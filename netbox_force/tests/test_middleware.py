"""Tests für die RequestContext Middleware."""
from django.test import TestCase, RequestFactory

from netbox_force.middleware import (
    RequestContextMiddleware,
    get_current_request,
    set_current_request,
)


class ThreadLocalStorageTest(TestCase):
    """Tests für get_current_request / set_current_request."""

    def test_default_is_none(self):
        set_current_request(None)
        self.assertIsNone(get_current_request())

    def test_set_and_get(self):
        factory = RequestFactory()
        request = factory.get('/test/')
        set_current_request(request)
        self.assertEqual(get_current_request(), request)
        set_current_request(None)

    def test_cleanup(self):
        factory = RequestFactory()
        request = factory.get('/test/')
        set_current_request(request)
        self.assertIsNotNone(get_current_request())
        set_current_request(None)
        self.assertIsNone(get_current_request())


class MiddlewareTest(TestCase):
    """Tests für RequestContextMiddleware."""

    def setUp(self):
        self.factory = RequestFactory()
        set_current_request(None)

    def test_request_stored_during_processing(self):
        """Request muss während der Verarbeitung verfügbar sein."""
        captured = {}

        def fake_get_response(request):
            captured['request'] = get_current_request()

            class FakeResponse:
                status_code = 200
            return FakeResponse()

        middleware = RequestContextMiddleware(fake_get_response)
        request = self.factory.get('/test/')
        middleware(request)

        self.assertEqual(captured['request'], request)

    def test_request_cleared_after_processing(self):
        """Request muss nach Verarbeitung aufgeräumt werden."""
        def fake_get_response(request):
            class FakeResponse:
                status_code = 200
            return FakeResponse()

        middleware = RequestContextMiddleware(fake_get_response)
        request = self.factory.get('/test/')
        middleware(request)

        self.assertIsNone(get_current_request())

    def test_request_cleared_on_exception(self):
        """Request muss auch bei Exception aufgeräumt werden."""
        def fake_get_response(request):
            raise RuntimeError("Test error")

        middleware = RequestContextMiddleware(fake_get_response)
        request = self.factory.get('/test/')

        with self.assertRaises(RuntimeError):
            middleware(request)

        self.assertIsNone(get_current_request())
