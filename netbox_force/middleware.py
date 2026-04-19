import hashlib
import hmac
import json
import logging
import threading
from urllib.request import Request, urlopen

_thread_locals = threading.local()

logger = logging.getLogger('netbox.plugins.netbox_force')


def get_current_request():
    """Returns the current HTTP request from thread-local storage."""
    return getattr(_thread_locals, 'request', None)


def set_current_request(request):
    """Stores the current HTTP request in thread-local storage."""
    _thread_locals.request = request


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

    def __call__(self, request):
        set_current_request(request)
        _thread_locals.pending_violations = []
        try:
            response = self.get_response(request)
        finally:
            self._flush_pending_violations()
            set_current_request(None)
        return response

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
            webhook_secret = getattr(settings, 'webhook_secret', '') if settings else ''

            for data in pending:
                try:
                    Violation.objects.create(**data)
                except Exception:
                    logger.error("Failed to write violation audit log entry", exc_info=True)

                if webhook_enabled and webhook_url:
                    _fire_webhook_async(data, webhook_url, webhook_secret)
        except Exception:
            logger.error("Failed to flush pending violations", exc_info=True)
        finally:
            _thread_locals.pending_violations = []


def _fire_webhook_async(data, url, secret):
    """
    Sends a violation notification to a webhook URL in a background daemon thread.
    Fire-and-forget: failures are logged but never propagate to the user.
    """
    def _send():
        try:
            payload = json.dumps({'event': 'violation', **data}).encode('utf-8')
            headers = {'Content-Type': 'application/json'}
            if secret:
                sig = hmac.new(secret.encode('utf-8'), payload, hashlib.sha256).hexdigest()
                headers['X-NetBox-Force-Signature'] = f'sha256={sig}'
            req = Request(url, data=payload, headers=headers, method='POST')
            urlopen(req, timeout=5)
            logger.debug("NetBox Force webhook delivered to %s", url)
        except Exception:
            logger.warning("NetBox Force webhook delivery failed to %s", url, exc_info=True)

    t = threading.Thread(target=_send, daemon=True)
    t.start()
