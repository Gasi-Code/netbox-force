import logging

from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver

from utilities.exceptions import AbortRequest
from netbox.plugins import get_plugin_config

from .middleware import get_current_request
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

    # Core system objects (NetBox 4.x)
    'core.configrevision',
    'core.objecttype',
    'core.job',
    'core.managedfile',
    'core.datasource',
    'core.datasourcefile',
    'core.autosyncrecord',

    # Own settings model (singleton)
    'netbox_force.forcesettings',
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
    """Returns True if the user is exempt from changelog enforcement."""
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
    Aborts with AbortRequest if no changelog is present or blacklist match.
    """
    request = get_current_request()
    model_label = get_model_label(instance)

    if is_exempt_model(instance):
        logger.debug("pre_save: %s is exempt model, skipping", model_label)
        return
    if is_exempt_user(request):
        logger.debug("pre_save: %s exempt user, skipping", model_label)
        return
    if not request or request.method not in ENFORCE_ON_METHODS:
        logger.debug("pre_save: %s no request or method not enforced, skipping", model_label)
        return

    # New object? Check enforce_on_create setting
    if not instance.pk and not _get_setting('enforce_on_create', False):
        logger.debug("pre_save: %s new object, enforce_on_create=False, skipping", model_label)
        return

    if not has_real_changes(instance):
        logger.debug("pre_save: %s no real changes, skipping", model_label)
        return

    min_len = _get_setting('min_length', 2)
    comment = get_changelog_comment(request)
    username = getattr(getattr(request, 'user', None), 'username', 'unknown')

    # Changelog present and long enough?
    if not comment or len(comment) < min_len:
        logger.info("pre_save: %s changelog missing/too short (got %s, need %d), blocking user '%s'",
                     model_label, len(comment) if comment else 0, min_len, username)
        raise AbortRequest(build_error_message(instance, request))

    # Check blacklist
    matched = check_blacklist(comment)
    if matched:
        logger.info("pre_save: %s changelog matches blacklist %s, blocking user '%s'",
                     model_label, matched, username)
        raise AbortRequest(build_blacklist_message(instance, request, matched))


@receiver(pre_delete)
def enforce_changelog_on_delete(sender, instance, **kwargs):
    """
    Called before every model delete.
    Only active if enforce_on_delete is True.
    """
    if not _get_setting('enforce_on_delete', True):
        return

    request = get_current_request()
    model_label = get_model_label(instance)

    if is_exempt_model(instance):
        logger.debug("pre_delete: %s is exempt model, skipping", model_label)
        return
    if is_exempt_user(request):
        logger.debug("pre_delete: %s exempt user, skipping", model_label)
        return
    if not request or request.method not in ENFORCE_ON_DELETE_METHODS:
        logger.debug("pre_delete: %s no request or method not enforced, skipping", model_label)
        return

    min_len = _get_setting('min_length', 2)
    comment = get_changelog_comment(request)
    username = getattr(getattr(request, 'user', None), 'username', 'unknown')

    if not comment or len(comment) < min_len:
        logger.info("pre_delete: %s changelog missing/too short, blocking user '%s'",
                     model_label, username)
        raise AbortRequest(build_error_message(instance, request))

    matched = check_blacklist(comment)
    if matched:
        logger.info("pre_delete: %s changelog matches blacklist %s, blocking user '%s'",
                     model_label, matched, username)
        raise AbortRequest(build_blacklist_message(instance, request, matched))
