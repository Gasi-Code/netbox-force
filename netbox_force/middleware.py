import hashlib
import hmac
import json
import logging
import threading
from urllib.parse import urlsplit

_thread_locals = threading.local()

logger = logging.getLogger('netbox.plugins.netbox_force')


def get_current_request():
    """Returns the current HTTP request from thread-local storage."""
    return getattr(_thread_locals, 'request', None)


def set_current_request(request):
    """Stores the current HTTP request in thread-local storage."""
    _thread_locals.request = request


def queue_pending_changelog(data):
    """
    Queues an auto-generated changelog message to be written onto NetBox's own
    change record after the view completes.

    NetBox builds the ObjectChange for a deletion in its own pre_delete
    receiver, which the core app connects before any plugin, so a message set
    on the instance from this plugin's receiver arrives too late to be included.
    Rather than depend on receiver ordering, the message is applied afterwards
    to the change records belonging to this request.
    """
    pending = getattr(_thread_locals, 'pending_changelogs', None)
    if pending is None:
        _thread_locals.pending_changelogs = []
        pending = _thread_locals.pending_changelogs
    pending.append(data)


def queue_pending_violation(data):
    """
    Queues a violation dict for writing after the view completes.
    This exists because NetBox wraps form.save() in transaction.atomic().
    If we write the violation inside the signal handler, it gets rolled back
    together with the blocked save when AbortRequest is raised.
    """
    pending = getattr(_thread_locals, 'pending_violations', None)
    if pending is None:
        _thread_locals.pending_violations = []
        pending = _thread_locals.pending_violations
    pending.append(data)


class RequestContextMiddleware:
    """
    Middleware that keeps the current request in thread-local storage
    so that signal handlers can access it.

    Also flushes pending violation audit log entries after the view completes,
    ensuring they are written outside any transaction.atomic() block.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    # Requests that cannot have produced a change record. Checking this first
    # keeps the Graylog pass from costing a database query on every page view.
    _READ_ONLY_METHODS = frozenset(('GET', 'HEAD', 'OPTIONS'))

    def __call__(self, request):
        set_current_request(request)
        _thread_locals.pending_violations = []
        _thread_locals.pending_changelogs = []
        try:
            response = self.get_response(request)
        finally:
            self._flush_pending_changelogs()
            self._flush_pending_violations()
            self._flush_graylog_events(request)
            set_current_request(None)
        return response

    @classmethod
    def _flush_graylog_events(cls, request):
        """
        Reports the change records of this request to Graylog.

        Runs last, so the auto-generated changelog messages written above are
        already on the records. Failures are swallowed — a logging target that
        is down must not turn a successful save into an error page.
        """
        if request.method in cls._READ_ONLY_METHODS:
            return
        try:
            from .graylog_events import flush_object_changes
            flush_object_changes(request)
        except Exception:
            logger.debug('Graylog event flush failed', exc_info=True)

    @staticmethod
    def _flush_pending_changelogs():
        """
        Writes queued auto-generated messages onto the change records NetBox
        created during this request.

        Only records that are still empty are touched, so anything NetBox or the
        user already supplied always wins. Uses .update() so no signal fires and
        the plugin cannot trigger itself.
        """
        pending = getattr(_thread_locals, 'pending_changelogs', [])
        if not pending:
            return
        _thread_locals.pending_changelogs = []
        try:
            try:
                from core.models import ObjectChange
            except ImportError:
                from extras.models import ObjectChange

            for item in pending:
                request_id = item.get('request_id')
                if not request_id:
                    continue
                ObjectChange.objects.filter(
                    request_id=request_id,
                    changed_object_id=item['object_id'],
                    action=item['action'],
                    message='',
                ).update(message=item['message'][:200])
        except Exception:
            logger.debug('Could not apply auto-generated changelog messages',
                         exc_info=True)

    @staticmethod
    def _flush_pending_violations():
        """
        Writes queued violations to the database and fires webhook notifications.
        Runs AFTER the view returns, outside any transaction.atomic() block,
        so the writes are auto-committed and survive AbortRequest rollbacks.
        """
        pending = getattr(_thread_locals, 'pending_violations', [])
        if not pending:
            return
        try:
            from .models import Violation, ForceSettings
            settings = ForceSettings.get_settings()
            webhook_enabled = getattr(settings, 'webhook_enabled', False) if settings else False
            webhook_url = getattr(settings, 'webhook_url', '') if settings else ''
            webhook_secret = settings.get_webhook_secret() if settings else ''

            try:
                from .graylog_events import emit_violation
            except Exception:
                emit_violation = None

            for data in pending:
                try:
                    Violation.objects.create(**data)
                except Exception:
                    logger.error("Failed to write violation audit log entry", exc_info=True)

                if webhook_enabled and webhook_url:
                    _fire_webhook_async(data, webhook_url, webhook_secret)

                if emit_violation is not None:
                    emit_violation(settings, data)
        except Exception:
            logger.error("Failed to flush pending violations", exc_info=True)
        finally:
            _thread_locals.pending_violations = []


# Deliveries run on a small fixed pool, never on a thread per violation.
# Violations are user-triggered: a loop of blocked saves, or one bulk edit over
# many objects, would otherwise open unbounded threads against a webhook target
# that may be slow or gone — the plugin's own denial of service.
_WEBHOOK_WORKERS = 2
_WEBHOOK_QUEUE_LIMIT = 100
_webhook_pool = None
_webhook_pool_lock = threading.Lock()
_webhook_inflight = 0


def _get_webhook_pool():
    global _webhook_pool
    if _webhook_pool is None:
        with _webhook_pool_lock:
            if _webhook_pool is None:
                from concurrent.futures import ThreadPoolExecutor
                _webhook_pool = ThreadPoolExecutor(
                    max_workers=_WEBHOOK_WORKERS,
                    thread_name_prefix='netbox_force_webhook',
                )
    return _webhook_pool


def _allowed_webhook_url(url):
    """http and https only — urlopen would also open file:// and ftp://."""
    scheme = urlsplit(url).scheme.lower()
    return scheme in ('http', 'https')


def _fire_webhook_async(data, url, secret):
    """
    Sends a violation notification to a webhook URL on a bounded worker pool.
    Fire-and-forget: failures are logged but never propagate to the user.
    """
    global _webhook_inflight

    if not _allowed_webhook_url(url):
        logger.warning(
            "NetBox Force webhook URL rejected (only http/https): %s", url)
        return

    with _webhook_pool_lock:
        if _webhook_inflight >= _WEBHOOK_QUEUE_LIMIT:
            logger.warning(
                "NetBox Force webhook backlog full (%d queued) — notification dropped",
                _webhook_inflight)
            return
        _webhook_inflight += 1

    def _send():
        global _webhook_inflight
        try:
            payload = json.dumps({'event': 'violation', **data}).encode('utf-8')
            headers = {'Content-Type': 'application/json'}
            if secret:
                sig = hmac.new(secret.encode('utf-8'), payload, hashlib.sha256).hexdigest()
                headers['X-NetBox-Force-Signature'] = f'sha256={sig}'
            import requests
            requests.post(
                url,
                data=payload,
                headers=headers,
                timeout=5,
                # A redirect off the configured host would carry the payload,
                # and its signature, somewhere nobody agreed to.
                allow_redirects=False,
            )
            logger.debug("NetBox Force webhook delivered to %s", url)
        except Exception:
            logger.warning("NetBox Force webhook delivery failed to %s", url, exc_info=True)
        finally:
            with _webhook_pool_lock:
                _webhook_inflight -= 1

    try:
        _get_webhook_pool().submit(_send)
    except Exception:
        with _webhook_pool_lock:
            _webhook_inflight -= 1
        logger.warning("NetBox Force webhook could not be queued", exc_info=True)
