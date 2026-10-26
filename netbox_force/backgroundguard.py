"""
Refuse NetBox's background bulk writes while NetBox Force is enforcing.

NetBox 4.7 can run a REST bulk create, update or delete as a background job
when the request carries ?background=true. The job executes in an RQ worker,
where no HTTP request exists. Every check in signals.py starts by looking for
that request and returns when there is none, so a background write skips the
changelog, naming, required-field and change-window checks, and it skips
maintenance mode.

The checks cannot be moved into the worker: the request, and with it the
user's exemptions and the submitted changelog text, is not kept in the job.
What can be done is to refuse the request before it is queued, at the one point
where NetBox has authenticated the user and still holds the request. A client
that is turned away repeats the call without ?background=true, and that call is
enforced like any other.
"""

import logging
from functools import wraps

logger = logging.getLogger('netbox.plugins.netbox_force')

GUARD_MARK = '_netbox_force_background_guard'
WRITE_METHODS = frozenset(('POST', 'PUT', 'PATCH', 'DELETE'))


def _mixin_class():
    from netbox.api.viewsets.mixins import BackgroundOperationMixin
    return BackgroundOperationMixin


def background_requested(request):
    """True for a bulk write that NetBox would hand to a background job."""
    if getattr(request, 'method', None) not in WRITE_METHODS:
        return False
    query_params = getattr(request, 'query_params', None)
    if query_params is None or query_params.get('background', '').lower() != 'true':
        return False
    return isinstance(getattr(request, 'data', None), list)


def blocking_message(request, model, action):
    """
    Returns the error message when this background write must be refused,
    else None. Mirrors the order of the signal handlers: maintenance mode
    first and independent of every exemption, then the ordinary switches.
    """
    from . import signals
    from .messages import get_api_message

    settings = signals._get_settings()
    username = getattr(getattr(request, 'user', None), 'username', 'unknown')
    model_label = signals.get_model_label(model)
    target = str(model._meta.verbose_name_plural)

    maintenance_error = signals.check_maintenance_mode(request, model, settings)
    if maintenance_error:
        signals.log_violation(username, model_label, target, action,
                              'maintenance_mode', maintenance_error)
        return maintenance_error

    if settings and not getattr(settings, 'enforcement_enabled', True):
        return None
    if action == 'bulk_destroy' and not signals._get_setting('enforce_on_delete', True):
        return None
    if signals.is_exempt_model(model) or signals.is_exempt_user(request):
        return None

    try:
        from .models import ModelPolicy
        policy = ModelPolicy.get_policy_for_model(model_label)
    except Exception:
        policy = None
    if (policy is not None and policy.enforcement_enabled is not None
            and not policy.enforcement_enabled):
        return None

    message = get_api_message('background_not_allowed')
    signals.log_violation(username, model_label, target, action,
                          'background_write', message)
    if getattr(settings, 'dry_run', False):
        logger.warning("DRY-RUN: %s would refuse a background write by user '%s'",
                       model_label, username)
        return None
    return message


def install_background_guard():
    """
    Returns True when the guard was installed. Never raises — a NetBox release
    that renames or moves the mixin must not keep the plugin from loading.
    NetBox before 4.7 has no background writes and needs no guard.
    """
    try:
        mixin = _mixin_class()
    except ImportError:
        return False

    try:
        original = getattr(mixin, '_handle_background_request', None)
        if original is None:
            logger.warning(
                'netbox_force: NetBox offers background bulk writes but '
                '_handle_background_request was not found, so they cannot be '
                'refused and bypass changelog enforcement and maintenance mode')
            return False
        if getattr(original, GUARD_MARK, False):
            return False

        from utilities.exceptions import AbortRequest

        @wraps(original)
        def guarded(self, request, action, *args, **kwargs):
            if background_requested(request):
                model = getattr(getattr(self, 'queryset', None), 'model', None)
                if model is not None:
                    message = blocking_message(request, model, action)
                    if message:
                        raise AbortRequest(message)
            return original(self, request, action, *args, **kwargs)

        setattr(guarded, GUARD_MARK, True)
        mixin._handle_background_request = guarded
        logger.debug('netbox_force: guarding %s._handle_background_request',
                     mixin.__name__)
        return True

    except Exception as exc:
        logger.warning(
            'netbox_force: could not guard background bulk writes, they bypass '
            'changelog enforcement and maintenance mode: %s', exc)
        return False
