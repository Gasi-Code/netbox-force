import threading

_thread_locals = threading.local()


def get_current_request():
    """Gibt den aktuellen HTTP-Request aus dem Thread-Local-Storage zurück."""
    return getattr(_thread_locals, 'request', None)


def set_current_request(request):
    """Speichert den aktuellen HTTP-Request im Thread-Local-Storage."""
    _thread_locals.request = request


class RequestContextMiddleware:
    """
    Middleware die den aktuellen Request im Thread-Local-Storage hält,
    damit die Signal Handler darauf zugreifen können.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_current_request(request)
        try:
            response = self.get_response(request)
        finally:
            set_current_request(None)  # Immer aufräumen, auch bei Exceptions
        return response
