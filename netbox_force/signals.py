import logging

from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver

from utilities.exceptions import AbortRequest
from netbox.plugins import get_plugin_config

from .middleware import get_current_request

logger = logging.getLogger('netbox.plugins.netbox_force')


# =============================================================================
# KONFIGURATION
# =============================================================================

# Modelle die niemals geprüft werden (NetBox-interne System-Objekte)
EXEMPT_MODELS = {
    # Auth & Sessions
    'auth.user', 'auth.group', 'auth.permission',
    'users.user', 'users.token', 'users.userconfig', 'users.objectpermission',
    'sessions.session',
    'contenttypes.contenttype',
    'admin.logentry',

    # NetBox System-Objekte (werden intern/automatisch geschrieben)
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

    # Core System-Objekte (NetBox 4.x)
    'core.configrevision',
    'core.objecttype',
    'core.job',
    'core.managedfile',
    'core.datasource',
    'core.datasourcefile',
    'core.autosyncrecord',
}

# HTTP-Methoden bei denen Changelog-Pflicht gilt (Save)
ENFORCE_ON_METHODS = {'POST', 'PUT', 'PATCH'}

# HTTP-Methoden bei denen Changelog-Pflicht gilt (Delete)
ENFORCE_ON_DELETE_METHODS = {'POST', 'DELETE'}

# Felder die bei Änderungsvergleich ignoriert werden (Timestamps etc.)
IGNORED_FIELDS = {
    'last_updated', 'created', 'modified',
    'last_login', 'date_joined', 'last_activity',
}

# Sentinel-Wert: unterscheidet "noch nicht geprüft" von "geprüft, nichts gefunden"
_NOT_CHECKED = object()


# =============================================================================
# HILFSFUNKTIONEN
# =============================================================================

def get_model_label(instance):
    return f"{instance._meta.app_label}.{instance._meta.model_name}"


def is_exempt_model(instance):
    label = get_model_label(instance)
    if label in EXEMPT_MODELS:
        return True
    extra = get_plugin_config('netbox_force', 'extra_exempt_models') or []
    return label in extra


def is_exempt_user(request):
    """Gibt True zurück wenn der User von der Prüfung ausgenommen ist."""
    if not request or not hasattr(request, 'user'):
        return True  # Kein Web-Request (z.B. Management-Commands) → ausgenommen
    if not request.user or not request.user.is_authenticated:
        return True
    exempt_users = get_plugin_config('netbox_force', 'exempt_users') or []
    return request.user.username in exempt_users


def get_changelog_comment(request):
    """
    Liest den Changelog-Kommentar aus dem Request.
    Prüft zuerst request.data (DRF, deckt JSON + Form ab),
    dann request.POST (Standard-Django-Views).
    """
    if not request:
        return None

    # Per-Request-Cache um bei Bulk-Operationen nicht wiederholt zu parsen
    cached = getattr(request, '_netbox_force_changelog_comment', _NOT_CHECKED)
    if cached is not _NOT_CHECKED:
        return cached

    field_names = ('changelog_message', 'comments', '_changelog_message')
    result = None

    # DRF parsed data (JSON + Form) — für REST-API-Requests
    if hasattr(request, 'data') and isinstance(request.data, dict):
        for field_name in field_names:
            val = request.data.get(field_name)
            if val and isinstance(val, str):
                val = val.strip()
                if val:
                    result = val
                    break

    # Fallback: Standard Django POST (Browser-Forms)
    if not result:
        for field_name in field_names:
            val = request.POST.get(field_name, '').strip()
            if val:
                result = val
                break

    request._netbox_force_changelog_comment = result  # None oder String
    return result


def has_real_changes(instance):
    """
    Prüft ob sich gegenüber dem gespeicherten Stand wirklich etwas geändert hat.
    Verhindert false-positives bei reinen Timestamp-Updates.
    """
    if not instance.pk:
        return True  # Neues Objekt → immer als Änderung werten

    try:
        old = instance.__class__.objects.get(pk=instance.pk)
    except instance.__class__.DoesNotExist:
        return True  # Objekt existiert noch nicht → Neuerstellung

    for field in instance._meta.fields:
        if field.name in IGNORED_FIELDS:
            continue
        if getattr(instance, field.name) != getattr(old, field.name):
            return True

    return False


def build_error_message(instance, request=None):
    """Baut die angezeigte Fehlermeldung auf — API-aware."""
    model_verbose = instance._meta.verbose_name.capitalize()
    min_len = get_plugin_config('netbox_force', 'min_length') or 2
    action_de = "Erstellen" if not instance.pk else "Ändern"
    action_en = "creating" if not instance.pk else "modifying"

    is_api = (request and hasattr(request, 'path_info')
              and request.path_info.startswith('/api/'))

    if is_api:
        return (
            f"Changelog entry required. When {action_en} '{model_verbose}', "
            f"include a 'changelog_message' field in the request body "
            f"(min {min_len} characters)."
        )

    return (
        f"Changelog-Eintrag erforderlich! Beim {action_de} von '{model_verbose}' "
        f"muss im Feld 'Änderungsgrund / Changelog' eine Begründung "
        f"eingetragen werden (mind. {min_len} Zeichen)."
    )


# =============================================================================
# SIGNAL HANDLER
# =============================================================================

@receiver(pre_save)
def enforce_changelog_on_save(sender, instance, **kwargs):
    """
    Wird vor jedem Model-Save aufgerufen.
    Bricht mit AbortRequest ab wenn kein Changelog vorhanden.
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
    if not instance.pk and not get_plugin_config('netbox_force', 'enforce_on_create'):
        logger.debug("pre_save: %s is new object, enforce_on_create=False, skipping", model_label)
        return
    if not has_real_changes(instance):
        logger.debug("pre_save: %s no real changes, skipping", model_label)
        return

    min_len = get_plugin_config('netbox_force', 'min_length') or 2
    comment = get_changelog_comment(request)

    if not comment or len(comment) < min_len:
        username = getattr(getattr(request, 'user', None), 'username', 'unknown')
        logger.info("pre_save: %s changelog missing/too short (got %s, need %d), blocking user '%s'",
                     model_label, len(comment) if comment else 0, min_len, username)
        raise AbortRequest(build_error_message(instance, request))


@receiver(pre_delete)
def enforce_changelog_on_delete(sender, instance, **kwargs):
    """
    Wird vor jedem Model-Delete aufgerufen.
    Nur aktiv wenn enforce_on_delete in der Plugin-Config True ist.
    """
    enforce_on_delete = get_plugin_config(
        'netbox_force', 'enforce_on_delete'
    )
    if not enforce_on_delete:
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

    min_len = get_plugin_config('netbox_force', 'min_length') or 2
    comment = get_changelog_comment(request)

    if not comment or len(comment) < min_len:
        username = getattr(getattr(request, 'user', None), 'username', 'unknown')
        logger.info("pre_delete: %s changelog missing/too short, blocking user '%s'",
                     model_label, username)
        raise AbortRequest(build_error_message(instance, request))
