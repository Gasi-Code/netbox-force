import logging
import re

from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone

from utilities.exceptions import AbortRequest
from netbox.plugins import get_plugin_config

from .middleware import get_current_request, queue_pending_violation
from .messages import get_message, get_api_message

logger = logging.getLogger('netbox.plugins.netbox_force')


# =============================================================================
# CONFIGURATION
# =============================================================================

# Models that are never checked (NetBox internal system objects)
EXEMPT_MODELS = {
    # Auth & Sessions
    'auth.user', 'auth.group', 'auth.permission',
    'users.user', 'users.token', 'users.userconfig', 'users.objectpermission',
    'sessions.session',
    'contenttypes.contenttype',
    'admin.logentry',

    # Django migration recorder (must never trigger DB queries during migrate)
    'migrations.migration',

    # NetBox system objects (written internally/automatically)
    'extras.objectchange',
    'extras.journalentry',
    'extras.cachedvalue',
    'extras.notification',
    'extras.notificationgroup',
    'extras.subscription',
    'extras.bookmark',
    'extras.savedfilter',
    'extras.imageattachment',
    'extras.eventrule',
    'extras.customlink',
    'extras.exporttemplate',
    'extras.dashboard',

    # Core system objects (NetBox 4.x)
    'core.configrevision',
    'core.objecttype',
    'core.job',
    'core.managedfile',
    'core.datasource',
    'core.datasourcefile',
    'core.autosyncrecord',

    # Own plugin models
    'netbox_force.forcesettings',
    'netbox_force.validationrule',
    'netbox_force.violation',
    'netbox_force.importtemplate',
    'netbox_force.guidepage',
}

# HTTP methods that require a changelog (save)
ENFORCE_ON_METHODS = {'POST', 'PUT', 'PATCH'}

# HTTP methods that require a changelog (delete)
ENFORCE_ON_DELETE_METHODS = {'POST', 'DELETE'}

# Fields ignored during change comparison (timestamps etc.)
IGNORED_FIELDS = {
    'last_updated', 'created', 'modified',
    'last_login', 'date_joined', 'last_activity',
}

# Sentinel value: distinguishes "not yet checked" from "checked, nothing found"
_NOT_CHECKED = object()

# Weekday names for error messages
_WEEKDAY_NAMES = {
    'de': {1: 'Mo', 2: 'Di', 3: 'Mi', 4: 'Do', 5: 'Fr', 6: 'Sa', 7: 'So'},
    'en': {1: 'Mon', 2: 'Tue', 3: 'Wed', 4: 'Thu', 5: 'Fri', 6: 'Sat', 7: 'Sun'},
    'es': {1: 'Lun', 2: 'Mar', 3: 'Mié', 4: 'Jue', 5: 'Vie', 6: 'Sáb', 7: 'Dom'},
}

# Language-specific prefix for example hints in error messages
_EXAMPLE_PREFIX = {'de': 'Beispiel', 'en': 'Example', 'es': 'Ejemplo'}


def _format_hint(custom_msg, prefix=''):
    """
    Build a hint suffix from a rule's custom error_message.
    Returns '' if no custom message is set.
    When prefix is given: " Example: <msg>", otherwise: " <msg>".
    """
    if not custom_msg or not custom_msg.strip():
        return ''
    msg = custom_msg.strip()
    if prefix:
        return f" {prefix}: {msg}"
    return f" {msg}"


# =============================================================================
# SETTINGS ACCESS
# =============================================================================

def _get_settings():
    """
    Reads settings from the DB (ForceSettings model).
    Falls back to PLUGINS_CONFIG if the DB is unavailable.
    Returns a dict-like object or None.
    """
    try:
        from .models import ForceSettings
        settings = ForceSettings.get_settings()
        if settings is not None:
            return settings
    except Exception:
        pass
    return None


def _get_setting(name, default=None):
    """Reads a single setting — DB-first, config fallback."""
    settings = _get_settings()
    if settings is not None:
        return getattr(settings, name, default)
    # Fallback to PLUGINS_CONFIG
    val = get_plugin_config('netbox_force', name)
    return val if val is not None else default


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_model_label(instance):
    return f"{instance._meta.app_label}.{instance._meta.model_name}"


def is_exempt_model(instance):
    label = get_model_label(instance)
    if label in EXEMPT_MODELS:
        return True
    settings = _get_settings()
    if settings is not None:
        return label in settings.get_extra_exempt_models_list()
    extra = get_plugin_config('netbox_force', 'extra_exempt_models') or []
    return label in extra


def is_exempt_user(request):
    """Returns True if the user (or their groups) is exempt from changelog enforcement."""
    if not request or not hasattr(request, 'user'):
        return True
    if not request.user or not request.user.is_authenticated:
        return True

    username = request.user.username.lower()

    settings = _get_settings()
    if settings is not None:
        exempt_list = [u.lower() for u in settings.get_exempt_users_list()]
        return username in exempt_list

    exempt_users = get_plugin_config('netbox_force', 'exempt_users') or []
    return username in [u.lower() for u in exempt_users]


def get_changelog_comment(request):
    """
    Reads the changelog comment from the request.
    Checks request.data (DRF) first, then request.POST (Django forms).
    """
    if not request:
        return None

    cached = getattr(request, '_netbox_force_changelog_comment', _NOT_CHECKED)
    if cached is not _NOT_CHECKED:
        return cached

    field_names = ('changelog_message', 'comments', '_changelog_message')
    result = None

    if hasattr(request, 'data') and isinstance(request.data, dict):
        for field_name in field_names:
            val = request.data.get(field_name)
            if val and isinstance(val, str):
                val = val.strip()
                if val:
                    result = val
                    break

    if not result:
        for field_name in field_names:
            val = request.POST.get(field_name, '').strip()
            if val:
                result = val
                break

    request._netbox_force_changelog_comment = result
    return result


def has_real_changes(instance):
    """Checks whether the instance actually has changes compared to the DB."""
    if not instance.pk:
        return True

    try:
        old = instance.__class__.objects.get(pk=instance.pk)
    except instance.__class__.DoesNotExist:
        return True

    for field in instance._meta.fields:
        if field.name in IGNORED_FIELDS:
            continue
        if getattr(instance, field.name) != getattr(old, field.name):
            return True

    return False


def check_blacklist(comment):
    """
    Checks whether the comment contains blacklisted phrases.
    Matches whole words — e.g. blacklist "test" matches "test update"
    but not "testing".
    Returns a list of matched phrases (empty = OK).
    """
    if not comment:
        return []
    settings = _get_settings()
    if settings is None:
        return []
    blacklist = settings.get_blacklisted_phrases_list()
    if not blacklist:
        return []

    comment_lower = comment.strip().lower()
    comment_words = set(comment_lower.split())

    matched = [phrase for phrase in blacklist if phrase in comment_words]
    return matched


# =============================================================================
# NEW V4 CHECK FUNCTIONS
# =============================================================================

def check_change_window(settings):
    """
    Checks if changes are allowed in the current time window.
    Returns None if OK, or an error message string if outside the window.
    """
    if not settings or not settings.change_window_enabled:
        return None

    if not settings.change_window_start or not settings.change_window_end:
        return None

    now = timezone.localtime(timezone.now())
    current_time = now.time()
    current_weekday = now.isoweekday()  # 1=Monday, 7=Sunday

    # Check weekday
    allowed_weekdays = settings.get_allowed_weekdays()
    if allowed_weekdays and current_weekday not in allowed_weekdays:
        return _build_change_window_message(settings)

    # Check time — handle overnight windows (e.g. 22:00 to 06:00)
    start = settings.change_window_start
    end = settings.change_window_end

    if start <= end:
        # Normal window: e.g. 08:00 to 18:00
        if not (start <= current_time <= end):
            return _build_change_window_message(settings)
    else:
        # Overnight window: e.g. 22:00 to 06:00
        if not (current_time >= start or current_time <= end):
            return _build_change_window_message(settings)

    return None


def _build_change_window_message(settings):
    """Builds the change window error message."""
    language = getattr(settings, 'language', 'de')
    start_str = settings.change_window_start.strftime('%H:%M') if settings.change_window_start else '?'
    end_str = settings.change_window_end.strftime('%H:%M') if settings.change_window_end else '?'

    weekday_names = _WEEKDAY_NAMES.get(language, _WEEKDAY_NAMES['en'])
    allowed = settings.get_allowed_weekdays()
    weekdays_str = ', '.join(weekday_names.get(d, str(d)) for d in sorted(allowed)) if allowed else '?'

    return get_message('change_window', language,
                       start=start_str, end=end_str, weekdays=weekdays_str)


def check_ticket_reference(comment, settings, instance, request):
    """
    Checks if the changelog comment contains a required ticket reference.
    Returns None if OK, or an error message string if missing.
    """
    if not settings:
        return None

    pattern = getattr(settings, 'ticket_pattern', '')
    if not pattern or not pattern.strip():
        return None

    if not comment:
        return _build_ticket_message(settings, instance, request, pattern)

    try:
        if not re.search(pattern.strip(), comment):
            return _build_ticket_message(settings, instance, request, pattern)
    except re.error:
        logger.warning("Invalid ticket pattern regex: %s — skipping check", pattern)
        return None

    return None


def _build_ticket_message(settings, instance, request, pattern):
    """Builds the ticket reference error message with human-readable hint."""
    language = getattr(settings, 'language', 'de')
    # Use custom hint if set, otherwise fall back to raw regex
    custom_hint = getattr(settings, 'ticket_pattern_hint', '')
    if custom_hint and custom_hint.strip():
        hint = custom_hint.strip()
    else:
        hint = f"({pattern})"

    is_api = (request and hasattr(request, 'path_info')
              and request.path_info.startswith('/api/'))
    if is_api:
        return get_api_message('ticket_missing', hint=hint)
    return get_message('ticket_missing', language, hint=hint)


def check_naming_conventions(instance, model_label, request=None):
    """
    Checks naming convention rules for the given instance.
    Returns None if OK, or an error message string for the first violation.
    """
    try:
        from .models import ValidationRule
        rules = ValidationRule.get_rules_for_model(model_label, rule_type='naming')
    except Exception:
        return None

    if not rules:
        return None

    settings = _get_settings()
    language = getattr(settings, 'language', 'de') if settings else 'en'
    model_verbose = instance._meta.verbose_name.capitalize()

    is_api = (request and hasattr(request, 'path_info')
              and request.path_info.startswith('/api/'))

    for rule in rules:
        value = getattr(instance, rule.field_name, None)
        if value is None:
            logger.debug("Naming rule: field '%s' not found on %s, skipping",
                         rule.field_name, model_label)
            continue

        value_str = str(value)
        if not rule.regex_pattern:
            continue

        try:
            if not re.fullmatch(rule.regex_pattern, value_str):
                # Build language-aware hint from custom error_message
                prefix = 'Example' if is_api else _EXAMPLE_PREFIX.get(language, 'Example')
                hint = _format_hint(rule.error_message, prefix)
                if is_api:
                    return get_api_message('naming_violation',
                                           field=rule.field_name,
                                           model=model_verbose,
                                           hint=hint)
                return get_message('naming_violation', language,
                                   field=rule.field_name,
                                   model=model_verbose,
                                   hint=hint)
        except re.error:
            logger.warning("Invalid naming rule regex: %s — skipping rule",
                           rule.regex_pattern)
            continue

    return None


def check_required_fields(instance, model_label, request=None):
    """
    Checks required field rules for the given instance.
    Returns None if OK, or an error message string for the first violation.
    """
    try:
        from .models import ValidationRule
        rules = ValidationRule.get_rules_for_model(model_label, rule_type='required')
    except Exception:
        return None

    if not rules:
        return None

    settings = _get_settings()
    language = getattr(settings, 'language', 'de') if settings else 'en'
    model_verbose = instance._meta.verbose_name.capitalize()

    is_api = (request and hasattr(request, 'path_info')
              and request.path_info.startswith('/api/'))

    for rule in rules:
        if not hasattr(instance, rule.field_name):
            logger.debug("Required field rule: field '%s' not found on %s, skipping",
                         rule.field_name, model_label)
            continue

        value = getattr(instance, rule.field_name, None)

        # Check for empty: None, empty string, blank string
        is_empty = (value is None
                    or (isinstance(value, str) and not value.strip())
                    or value == '')

        if is_empty:
            # Custom error_message replaces the default message entirely
            if rule.error_message and rule.error_message.strip():
                return rule.error_message.strip()
            if is_api:
                return get_api_message('required_field',
                                       field=rule.field_name,
                                       model=model_verbose,
                                       hint='')
            return get_message('required_field', language,
                               field=rule.field_name,
                               model=model_verbose,
                               hint='')

    return None


def log_violation(username, model_label, instance, action, reason, message,
                  comment=None):
    """
    Queues a Violation audit log entry for writing after the view completes
    (only if audit_log_enabled).

    Violations are NOT written directly because NetBox wraps form.save()
    in transaction.atomic(). A direct write would be rolled back when
    AbortRequest is raised. Instead, the violation data is buffered in
    thread-local storage and flushed by the middleware after the response.

    Also fires a webhook notification if configured.

    Never raises — logging failures must not block enforcement.
    """
    settings = _get_settings()

    if settings and getattr(settings, 'audit_log_enabled', False):
        try:
            queue_pending_violation({
                'username': username,
                'model_label': model_label,
                'object_repr': str(instance)[:200],
                'action': action,
                'reason': reason,
                'message': message,
                'attempted_comment': comment or '',
            })
        except Exception:
            logger.error("Failed to queue violation audit log entry", exc_info=True)


# =============================================================================
# ERROR MESSAGE BUILDERS (existing)
# =============================================================================

def build_error_message(instance, request=None, reason='changelog_required'):
    """Builds the error message — multilingual and API-aware."""
    model_verbose = instance._meta.verbose_name.capitalize()
    min_len = _get_setting('min_length', 2)
    language = _get_setting('language', 'de')

    is_new = not instance.pk
    is_api = (request and hasattr(request, 'path_info')
              and request.path_info.startswith('/api/'))

    if is_api:
        action = 'creating' if is_new else 'modifying'
        return get_api_message(reason, action=action, model=model_verbose,
                               min_len=min_len, words='')

    action_key = 'action_create' if is_new else 'action_edit'
    action = get_message(action_key, language)
    return get_message(reason, language, action=action, model=model_verbose,
                       min_len=min_len, words='')


def build_blacklist_message(instance, request, matched_words):
    """Builds the blacklist error message."""
    language = _get_setting('language', 'de')
    words_str = ', '.join(f"'{w}'" for w in matched_words)

    is_api = (request and hasattr(request, 'path_info')
              and request.path_info.startswith('/api/'))

    if is_api:
        return get_api_message('blacklisted', words=words_str)
    return get_message('blacklisted', language, words=words_str)


# =============================================================================
# SIGNAL HANDLERS
# =============================================================================

@receiver(pre_save)
def enforce_changelog_on_save(sender, instance, **kwargs):
    """
    Called before every model save.
    Runs the full enforcement chain:
    1. Request context check (bail out during migrations/management commands)
    2. Exemption checks (model, user)
    3. Real changes check (existing objects only)
    4. Change window check (ALWAYS — regardless of enforce_on_create)
    5. Naming convention check (ALWAYS — regardless of enforce_on_create)
    6. Required field check (ALWAYS — regardless of enforce_on_create)
    7. Changelog presence + length (gated by enforce_on_create for new objects)
    8. Blacklist check (gated by enforce_on_create for new objects)
    9. Ticket reference check (gated by enforce_on_create for new objects)
    """
    # --- Request context check FIRST (no DB access!) ---
    # During migrations, management commands, and background tasks there is
    # no HTTP request.  Bail out immediately to avoid querying plugin tables
    # whose schema may not yet be complete.
    request = get_current_request()
    if not request or request.method not in ENFORCE_ON_METHODS:
        return

    model_label = get_model_label(instance)

    # --- Global enforcement master switch ---
    settings = _get_settings()
    if settings and not getattr(settings, 'enforcement_enabled', True):
        return

    # --- Exemption checks ---
    if is_exempt_model(instance):
        logger.debug("pre_save: %s is exempt model, skipping", model_label)
        return
    if is_exempt_user(request):
        logger.debug("pre_save: %s exempt user, skipping", model_label)
        return

    # Determine if this is a new object
    is_new = not instance.pk

    # For existing objects, check if there are real changes
    if not is_new and not has_real_changes(instance):
        logger.debug("pre_save: %s no real changes, skipping", model_label)
        return

    username = getattr(getattr(request, 'user', None), 'username', 'unknown')
    action = 'create' if is_new else 'edit'
    dry_run = getattr(settings, 'dry_run', False) if settings else False

    def _enforce(reason, error_msg, comment=None):
        """Log violation and raise AbortRequest (or just log in dry-run mode)."""
        log_violation(username, model_label, instance, action, reason, error_msg, comment)
        if dry_run:
            logger.warning("DRY-RUN: %s would block user '%s' (%s): %s",
                           model_label, username, reason, error_msg)
        else:
            raise AbortRequest(error_msg)

    # --- Change window check ---
    window_error = check_change_window(settings)
    if window_error:
        logger.info("pre_save: %s outside change window, blocking user '%s'",
                     model_label, username)
        _enforce('change_window', window_error)

    # --- Naming convention check ---
    naming_error = check_naming_conventions(instance, model_label, request)
    if naming_error:
        logger.info("pre_save: %s naming convention violation, blocking user '%s'",
                     model_label, username)
        _enforce('naming_violation', naming_error)

    # --- Required field check ---
    required_error = check_required_fields(instance, model_label, request)
    if required_error:
        logger.info("pre_save: %s required field missing, blocking user '%s'",
                     model_label, username)
        _enforce('required_field', required_error)

    # --- Changelog-related checks ---
    changelog_required = not is_new or _get_setting('enforce_on_create', False)

    if not changelog_required:
        logger.debug("pre_save: %s new object, enforce_on_create=False, skipping changelog checks",
                      model_label)
        return

    # --- Changelog presence + length ---
    min_len = _get_setting('min_length', 2)
    comment = get_changelog_comment(request)

    if not comment or len(comment) < min_len:
        reason = 'too_short' if comment else 'missing_changelog'
        error_msg = build_error_message(instance, request)
        logger.info("pre_save: %s changelog missing/too short (got %s, need %d), blocking user '%s'",
                     model_label, len(comment) if comment else 0, min_len, username)
        _enforce(reason, error_msg, comment)

    # --- Blacklist check ---
    matched = check_blacklist(comment)
    if matched:
        error_msg = build_blacklist_message(instance, request, matched)
        logger.info("pre_save: %s changelog matches blacklist %s, blocking user '%s'",
                     model_label, matched, username)
        _enforce('blacklisted', error_msg, comment)

    # --- Ticket reference check ---
    ticket_error = check_ticket_reference(comment, settings, instance, request)
    if ticket_error:
        logger.info("pre_save: %s missing ticket reference, blocking user '%s'",
                     model_label, username)
        _enforce('ticket_missing', ticket_error, comment)


@receiver(pre_delete)
def enforce_changelog_on_delete(sender, instance, **kwargs):
    """
    Called before every model delete.
    Only active if enforce_on_delete is True.
    Runs: exemption checks, change window, changelog, blacklist, ticket reference.
    (Naming and required field checks are skipped on deletion.)
    """
    # --- Request context check FIRST (no DB access!) ---
    request = get_current_request()
    if not request or request.method not in ENFORCE_ON_DELETE_METHODS:
        return

    # --- Global enforcement master switch ---
    settings = _get_settings()
    if settings and not getattr(settings, 'enforcement_enabled', True):
        return

    if not _get_setting('enforce_on_delete', True):
        return

    model_label = get_model_label(instance)

    if is_exempt_model(instance):
        logger.debug("pre_delete: %s is exempt model, skipping", model_label)
        return
    if is_exempt_user(request):
        logger.debug("pre_delete: %s exempt user, skipping", model_label)
        return

    username = getattr(getattr(request, 'user', None), 'username', 'unknown')
    dry_run = getattr(settings, 'dry_run', False) if settings else False

    def _enforce(reason, error_msg, comment=None):
        log_violation(username, model_label, instance, 'delete', reason, error_msg, comment)
        if dry_run:
            logger.warning("DRY-RUN: %s would block user '%s' (%s): %s",
                           model_label, username, reason, error_msg)
        else:
            raise AbortRequest(error_msg)

    # --- Change window check ---
    window_error = check_change_window(settings)
    if window_error:
        logger.info("pre_delete: %s outside change window, blocking user '%s'",
                     model_label, username)
        _enforce('change_window', window_error)

    # --- Changelog presence + length ---
    min_len = _get_setting('min_length', 2)
    comment = get_changelog_comment(request)

    if not comment or len(comment) < min_len:
        reason = 'too_short' if comment else 'missing_changelog'
        error_msg = build_error_message(instance, request)
        logger.info("pre_delete: %s changelog missing/too short, blocking user '%s'",
                     model_label, username)
        _enforce(reason, error_msg, comment)

    # --- Blacklist check ---
    matched = check_blacklist(comment)
    if matched:
        error_msg = build_blacklist_message(instance, request, matched)
        logger.info("pre_delete: %s changelog matches blacklist %s, blocking user '%s'",
                     model_label, matched, username)
        _enforce('blacklisted', error_msg, comment)

    # --- Ticket reference check ---
    ticket_error = check_ticket_reference(comment, settings, instance, request)
    if ticket_error:
        logger.info("pre_delete: %s missing ticket reference, blocking user '%s'",
                     model_label, username)
        _enforce('ticket_missing', ticket_error, comment)
