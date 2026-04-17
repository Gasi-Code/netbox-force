import logging
import threading

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
        Writes queued violations to the database.
        Runs AFTER the view returns, outside any transaction.atomic() block,
        so the writes are auto-committed and survive AbortRequest rollbacks.
        """
        pending = getattr(_thread_locals, 'pending_violations', [])
        if not pending:
            return
        try:
            from .models import Violation
            for data in pending:
                Violation.objects.create(**data)
        except Exception:
            logger.error("Failed to flush pending violations", exc_info=True)
        finally:
            _thread_locals.pending_violations = []
