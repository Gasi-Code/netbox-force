"""
Turns NetBox happenings into Graylog events.

Object changes are not captured with a second set of signal handlers. NetBox
already writes an ObjectChange row per change; reading those rows after the view
returns gives the same information, post-commit, with no risk of reporting a
change that was later rolled back. The one thing those rows lack — client IP and
user agent — is taken from the request that is still in scope at that point.

Every function here is written so that a failure can only cost the event, never
the request. Callers sit in a middleware `finally` block and in signal
receivers; an exception escaping from either would surface to the user as a
failed save.
"""

import logging

from django.contrib.auth.signals import (
    user_logged_in, user_logged_out, user_login_failed,
)
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

from .graylog import (
    LEVEL_ERROR, LEVEL_WARNING, LEVEL_NOTICE, LEVEL_INFO,
    build_config, build_gelf, get_sender, send_now,
)

logger = logging.getLogger('netbox.plugins.netbox_force')

CATEGORY_OBJECT = 'object_change'
CATEGORY_AUTH = 'auth'
CATEGORY_VIOLATION = 'violation'
CATEGORY_SETTINGS = 'settings'
CATEGORY_SYSTEM = 'system'

# Event type -> (ForceSettings toggle field, ForceSettings severity field)
EVENT_CONFIG = {
    'object_created':   ('graylog_ev_object_create', 'graylog_lvl_object_create'),
    'object_updated':   ('graylog_ev_object_update', 'graylog_lvl_object_update'),
    'object_deleted':   ('graylog_ev_object_delete', 'graylog_lvl_object_delete'),
    'bulk_change':      ('graylog_ev_object_update', 'graylog_lvl_object_update'),
    'login':            ('graylog_ev_login', 'graylog_lvl_login'),
    'logout':           ('graylog_ev_logout', 'graylog_lvl_logout'),
    'login_failed':     ('graylog_ev_login_failed', 'graylog_lvl_login_failed'),
    'violation':        ('graylog_ev_violation', 'graylog_lvl_violation'),
    'settings_changed': ('graylog_ev_settings_change', 'graylog_lvl_settings_change'),
}

DEFAULT_LEVELS = {
    'object_created': LEVEL_INFO,
    'object_updated': LEVEL_INFO,
    'object_deleted': LEVEL_NOTICE,
    'bulk_change': LEVEL_NOTICE,
    'login': LEVEL_INFO,
    'logout': LEVEL_INFO,
    'login_failed': LEVEL_WARNING,
    'violation': LEVEL_WARNING,
    'settings_changed': LEVEL_WARNING,
}

# ForceSettings fields whose old and new value are reported verbatim. Turning
# enforcement off is the change worth alerting on, so the numbers have to be in
# the message. Everything else is reported by field name only — the settings
# model holds exempt user lists and credentials that have no business in a log.
SETTINGS_VALUE_ALLOWLIST = {
    'enforcement_enabled', 'dry_run', 'enforce_on_create', 'enforce_on_delete',
    'min_length', 'audit_log_enabled', 'ticket_enabled', 'blacklist_enabled',
    'change_window_enabled', 'graylog_enabled', 'checkmk_enabled',
    'webhook_enabled', 'patchmanagement_enabled',
}

# Settings whose change is a security event rather than a routine adjustment.
SETTINGS_CRITICAL = {'enforcement_enabled', 'dry_run', 'graylog_enabled'}


def _settings():
    try:
        from .models import ForceSettings
        return ForceSettings.get_settings()
    except Exception:
        return None


def client_ip(request):
    """
    Best-effort client address.

    X-Forwarded-For is trusted only because NetBox behind a reverse proxy is the
    normal deployment. It is client-supplied and can be forged when NetBox is
    reachable directly; the settings page says so.
    """
    if request is None:
        return ''
    try:
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if forwarded:
            return forwarded.split(',')[0].strip()[:64]
        return (request.META.get('REMOTE_ADDR', '') or '')[:64]
    except Exception:
        return ''


def user_agent(request):
    if request is None:
        return ''
    try:
        return (request.META.get('HTTP_USER_AGENT', '') or '')[:256]
    except Exception:
        return ''


def username_of(request):
    if request is None:
        return ''
    try:
        user = getattr(request, 'user', None)
        if user is None or not getattr(user, 'is_authenticated', False):
            return ''
        return str(user)[:150]
    except Exception:
        return ''


def business_hours_configured(settings_obj):
    return bool(
        getattr(settings_obj, 'graylog_business_start', None)
        and getattr(settings_obj, 'graylog_business_end', None)
    )


def is_outside_business_hours(settings_obj, when=None):
    """
    None when business hours are not configured, so callers can tell "outside"
    apart from "unknown" instead of treating everything as a night-time change.
    """
    if not business_hours_configured(settings_obj):
        return None
    try:
        moment = timezone.localtime(when or timezone.now())
        weekdays = {
            int(part) for part in
            (getattr(settings_obj, 'graylog_business_days', '') or '').split(',')
            if part.strip().isdigit()
        }
        if weekdays and moment.isoweekday() not in weekdays:
            return True
        start = settings_obj.graylog_business_start
        end = settings_obj.graylog_business_end
        current = moment.time()
        if start <= end:
            return not (start <= current <= end)
        # Window crossing midnight.
        return not (current >= start or current <= end)
    except Exception:
        return None


def _level_for(settings_obj, event):
    _, level_field = EVENT_CONFIG.get(event, (None, None))
    raw = getattr(settings_obj, level_field, '') if level_field else ''
    try:
        return int(raw)
    except (TypeError, ValueError):
        return DEFAULT_LEVELS.get(event, LEVEL_INFO)


def _event_enabled(settings_obj, event):
    if event == 'bulk_change':
        # A summary stands in for creates, updates and deletes alike, so it is
        # sent as long as any of the three is wanted.
        return any(getattr(settings_obj, name, False) for name in (
            'graylog_ev_object_create', 'graylog_ev_object_update',
            'graylog_ev_object_delete'))
    toggle_field, _ = EVENT_CONFIG.get(event, (None, None))
    if toggle_field is None:
        return True
    return bool(getattr(settings_obj, toggle_field, False))


def emit(event, short_message, settings_obj=None, category=CATEGORY_SYSTEM,
         request=None, level=None, timestamp=None, **fields):
    """
    Central gate. Returns True when the event was queued.

    Never raises. Callers are in request-critical paths.
    """
    try:
        settings_obj = settings_obj or _settings()
        config = build_config(settings_obj)
        if config is None:
            return False
        if not _event_enabled(settings_obj, event):
            return False

        outside = is_outside_business_hours(settings_obj, timestamp)
        if getattr(settings_obj, 'graylog_only_outside_hours', False):
            # Unknown counts as inside — an unconfigured window must not turn
            # into "log everything".
            if outside is not True:
                return False

        payload = build_gelf(
            config['source'],
            short_message,
            level=level if level is not None else _level_for(settings_obj, event),
            timestamp=timestamp.timestamp() if hasattr(timestamp, 'timestamp') else None,
            app='netbox_force',
            category=category,
            event=event,
            outside_business_hours=outside,
            client_ip=fields.pop('client_ip', None) or client_ip(request),
            user_agent=fields.pop('user_agent', None) or user_agent(request),
            username=fields.pop('username', None) or username_of(request),
            **fields,
        )
        return get_sender().emit(config, payload)
    except Exception:
        logger.debug('netbox_force: building Graylog event failed', exc_info=True)
        return False


# =============================================================================
# OBJECT CHANGES
# =============================================================================

_ACTION_EVENTS = {
    'create': 'object_created',
    'update': 'object_updated',
    'delete': 'object_deleted',
}


def flush_object_changes(request):
    """
    Emit one event per ObjectChange row written during this request.

    Runs from the middleware after the view returned. Above the configured
    threshold the rows are collapsed into a single summary event — a bulk import
    of five hundred objects is one operation, and five hundred near-identical
    log lines make it harder to see, not easier.
    """
    settings_obj = _settings()
    if build_config(settings_obj) is None:
        return

    request_id = getattr(request, 'id', None)
    if not request_id:
        return

    try:
        try:
            from core.models import ObjectChange
        except ImportError:
            from extras.models import ObjectChange

        changes = list(
            ObjectChange.objects.filter(request_id=request_id)
            .select_related('changed_object_type')[:1000]
        )
    except Exception:
        logger.debug('netbox_force: reading ObjectChange rows failed', exc_info=True)
        return

    if not changes:
        return

    threshold = int(getattr(settings_obj, 'graylog_bulk_threshold', 10) or 10)
    if threshold and len(changes) > threshold:
        _emit_bulk_summary(settings_obj, request, changes)
        return

    limit = int(getattr(settings_obj, 'graylog_max_events_per_request', 100) or 100)
    for change in changes[:limit]:
        _emit_single_change(settings_obj, request, change)


def _object_type_label(change):
    try:
        ct = change.changed_object_type
        return f'{ct.app_label}.{ct.model}' if ct else ''
    except Exception:
        return ''


def _object_url(request, change):
    try:
        obj = change.changed_object
        if obj is None:
            return ''
        return request.build_absolute_uri(obj.get_absolute_url())
    except Exception:
        return ''


def _emit_single_change(settings_obj, request, change):
    action = getattr(change, 'action', '') or ''
    event = _ACTION_EVENTS.get(action)
    if event is None:
        return

    changed_fields = ''
    try:
        pre = change.prechange_data or {}
        post = change.postchange_data or {}
        if action == 'update' and pre and post:
            changed_fields = ','.join(sorted(
                key for key in post
                if key not in ('last_updated',) and pre.get(key) != post.get(key)
            ))
    except Exception:
        pass

    object_type = _object_type_label(change)
    emit(
        event,
        f'{action} {object_type} {change.object_repr}'.strip(),
        settings_obj=settings_obj,
        category=CATEGORY_OBJECT,
        request=request,
        timestamp=getattr(change, 'time', None),
        username=str(getattr(change, 'user', '') or '') or username_of(request),
        action=action,
        object_type=object_type,
        object_id=getattr(change, 'changed_object_id', None),
        object_name=getattr(change, 'object_repr', ''),
        changed_fields=changed_fields,
        changelog_message=getattr(change, 'message', ''),
        request_id=str(getattr(change, 'request_id', '') or ''),
        netbox_url=_object_url(request, change),
    )


def _emit_bulk_summary(settings_obj, request, changes):
    actions = {}
    types = set()
    for change in changes:
        actions[change.action] = actions.get(change.action, 0) + 1
        label = _object_type_label(change)
        if label:
            types.add(label)

    breakdown = ', '.join(f'{count} {name}' for name, count in sorted(actions.items()))
    emit(
        'bulk_change',
        f'bulk change: {len(changes)} objects ({breakdown})',
        settings_obj=settings_obj,
        category=CATEGORY_OBJECT,
        request=request,
        count=len(changes),
        object_type=','.join(sorted(types))[:256],
        created=actions.get('create', 0),
        updated=actions.get('update', 0),
        deleted=actions.get('delete', 0),
        request_id=str(getattr(request, 'id', '') or ''),
        netbox_path=getattr(request, 'path', ''),
    )


# =============================================================================
# VIOLATIONS
# =============================================================================

def emit_violation(settings_obj, data):
    """Called from the middleware once a queued violation has been written."""
    from .middleware import get_current_request
    emit(
        'violation',
        'change blocked ({}): {} {}'.format(
            data.get('reason', ''), data.get('model_label', ''),
            data.get('object_repr', '')).strip(),
        settings_obj=settings_obj,
        category=CATEGORY_VIOLATION,
        request=get_current_request(),
        username=data.get('username', ''),
        action=data.get('action', ''),
        object_type=data.get('model_label', ''),
        object_name=data.get('object_repr', ''),
        reason=data.get('reason', ''),
        detail=data.get('message', ''),
        attempted_comment=data.get('attempted_comment', ''),
    )


# =============================================================================
# AUTHENTICATION
# =============================================================================

@receiver(user_logged_in)
def _on_login(sender, request=None, user=None, **kwargs):
    emit('login', f'login succeeded: {user}', category=CATEGORY_AUTH,
         request=request, username=str(user) if user else '')


@receiver(user_logged_out)
def _on_logout(sender, request=None, user=None, **kwargs):
    emit('logout', f'logout: {user}', category=CATEGORY_AUTH,
         request=request, username=str(user) if user else '')


@receiver(user_login_failed)
def _on_login_failed(sender, credentials=None, request=None, **kwargs):
    # Only the username is read out of `credentials`. The dict also carries the
    # submitted password.
    attempted = ''
    try:
        attempted = str((credentials or {}).get('username', ''))[:150]
    except Exception:
        pass
    emit('login_failed', f'login failed: {attempted or "unknown"}',
         category=CATEGORY_AUTH, request=request, username=attempted)


# =============================================================================
# SETTINGS CHANGES
# =============================================================================

@receiver(pre_save, sender='netbox_force.ForceSettings')
def _on_settings_save(sender, instance=None, **kwargs):
    """
    Report changes to the plugin's own settings.

    ForceSettings is a plain model and therefore not covered by NetBox's
    changelog. Without this, switching enforcement off leaves no trace anywhere.

    The event is built from the state *before* the save. The settings page edits
    the cached instance in place, so reading the current settings here would
    already show the new values — and switching Graylog output off would then
    suppress the very event that records it.
    """
    try:
        from .models import ForceSettings
        if instance is None or not instance.pk:
            return

        try:
            previous = ForceSettings.objects.get(pk=instance.pk)
        except ForceSettings.DoesNotExist:
            return

        settings_obj = previous
        if build_config(settings_obj) is None:
            return

        changed = []
        details = {}
        critical = False
        for field in ForceSettings._meta.fields:
            name = field.name
            if name == 'id':
                continue
            old = getattr(previous, name, None)
            new = getattr(instance, name, None)
            if old == new:
                continue
            changed.append(name)
            if name in SETTINGS_VALUE_ALLOWLIST:
                details[name] = f'{old} -> {new}'
            if name in SETTINGS_CRITICAL:
                critical = True

        if not changed:
            return

        from .middleware import get_current_request
        emit(
            'settings_changed',
            'NetBox Force settings changed: ' + ','.join(changed),
            settings_obj=settings_obj,
            category=CATEGORY_SETTINGS,
            request=get_current_request(),
            level=LEVEL_ERROR if critical else None,
            changed_fields=','.join(changed),
            changed_values='; '.join(f'{k}={v}' for k, v in sorted(details.items())),
        )
    except Exception:
        logger.debug('netbox_force: settings change event failed', exc_info=True)


# =============================================================================
# TEST
# =============================================================================

def send_test_event(settings_obj, username=''):
    """
    Synchronous delivery for the settings page. Raises GraylogError on failure.
    """
    config = build_config(settings_obj)
    if config is None:
        from .graylog import GraylogError
        raise GraylogError('not_configured')

    payload = build_gelf(
        config['source'],
        'NetBox Force connection test',
        level=LEVEL_NOTICE,
        app='netbox_force',
        category=CATEGORY_SYSTEM,
        event='test',
        username=username,
    )
    send_now(config, payload)
    return config
