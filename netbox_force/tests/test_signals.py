"""Tests für die Signal-Handler und Hilfsfunktionen."""
from unittest.mock import patch, MagicMock, PropertyMock

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError

from netbox_force.signals import (
    get_model_label,
    is_exempt_model,
    is_exempt_user,
    get_changelog_comment,
    has_real_changes,
    build_error_message,
    EXEMPT_MODELS,
)
from netbox_force.middleware import set_current_request


def _make_mock_instance(app_label='dcim', model_name='device', pk=1,
                        verbose_name='Device', fields=None):
    """Erstellt eine Mock-Model-Instance."""
    instance = MagicMock()
    instance._meta.app_label = app_label
    instance._meta.model_name = model_name
    instance._meta.verbose_name = verbose_name
    instance.pk = pk

    if fields:
        mock_fields = []
        for name, value in fields.items():
            field = MagicMock()
            field.name = name
            mock_fields.append(field)
            setattr(instance, name, value)
        instance._meta.fields = mock_fields
    else:
        instance._meta.fields = []

    return instance


def _make_request(method='POST', path='/', post_data=None, user=None,
                  data=None):
    """Erstellt einen Mock-Request."""
    factory = RequestFactory()
    if method == 'POST':
        request = factory.post(path, data=post_data or {})
    elif method == 'PATCH':
        request = factory.patch(path, data=post_data or {})
    elif method == 'PUT':
        request = factory.put(path, data=post_data or {})
    elif method == 'DELETE':
        request = factory.delete(path)
    else:
        request = factory.get(path)

    if user:
        request.user = user
    else:
        request.user = AnonymousUser()

    # DRF-style request.data simulieren
    if data is not None:
        request.data = data

    return request


class GetModelLabelTest(TestCase):

    def test_returns_app_dot_model(self):
        instance = _make_mock_instance(app_label='dcim', model_name='device')
        self.assertEqual(get_model_label(instance), 'dcim.device')

    def test_auth_user(self):
        instance = _make_mock_instance(app_label='auth', model_name='user')
        self.assertEqual(get_model_label(instance), 'auth.user')


class IsExemptModelTest(TestCase):

    @patch('netbox_force.signals.get_plugin_config', return_value=[])
    def test_builtin_exempt(self, mock_config):
        for label in ['extras.objectchange', 'auth.user', 'core.job']:
            app, model = label.split('.')
            instance = _make_mock_instance(app_label=app, model_name=model)
            self.assertTrue(is_exempt_model(instance),
                            f"{label} should be exempt")

    @patch('netbox_force.signals.get_plugin_config', return_value=[])
    def test_non_exempt_model(self, mock_config):
        instance = _make_mock_instance(app_label='dcim', model_name='device')
        self.assertFalse(is_exempt_model(instance))

    @patch('netbox_force.signals.get_plugin_config',
           return_value=['myplugin.mymodel'])
    def test_extra_exempt_from_config(self, mock_config):
        instance = _make_mock_instance(app_label='myplugin', model_name='mymodel')
        self.assertTrue(is_exempt_model(instance))


class IsExemptUserTest(TestCase):

    @patch('netbox_force.signals.get_plugin_config',
           return_value=['automation', 'netbox'])
    def test_no_request(self, mock_config):
        self.assertTrue(is_exempt_user(None))

    @patch('netbox_force.signals.get_plugin_config',
           return_value=['automation', 'netbox'])
    def test_unauthenticated(self, mock_config):
        request = _make_request()
        request.user = AnonymousUser()
        self.assertTrue(is_exempt_user(request))

    @patch('netbox_force.signals.get_plugin_config',
           return_value=['automation', 'netbox'])
    def test_exempt_username(self, mock_config):
        request = _make_request()
        user = MagicMock()
        user.is_authenticated = True
        user.username = 'automation'
        request.user = user
        self.assertTrue(is_exempt_user(request))

    @patch('netbox_force.signals.get_plugin_config',
           return_value=['automation', 'netbox'])
    def test_normal_user(self, mock_config):
        request = _make_request()
        user = MagicMock()
        user.is_authenticated = True
        user.username = 'admin'
        request.user = user
        self.assertFalse(is_exempt_user(request))


class GetChangelogCommentTest(TestCase):

    def test_none_request(self):
        self.assertIsNone(get_changelog_comment(None))

    def test_from_post_data(self):
        request = _make_request(method='POST',
                                post_data={'comments': 'Test changelog entry'})
        self.assertEqual(get_changelog_comment(request), 'Test changelog entry')

    def test_from_drf_data(self):
        request = _make_request(method='POST',
                                data={'changelog_message': 'API changelog'})
        self.assertEqual(get_changelog_comment(request), 'API changelog')

    def test_drf_data_preferred_over_post(self):
        request = _make_request(method='POST',
                                post_data={'comments': 'from form'},
                                data={'changelog_message': 'from api'})
        self.assertEqual(get_changelog_comment(request), 'from api')

    def test_empty_comment(self):
        request = _make_request(method='POST', post_data={'comments': '   '})
        self.assertIsNone(get_changelog_comment(request))

    def test_no_comment_fields(self):
        request = _make_request(method='POST', post_data={'name': 'test'})
        self.assertIsNone(get_changelog_comment(request))

    def test_caching(self):
        """Wiederholte Aufrufe sollten gecachtes Ergebnis nutzen."""
        request = _make_request(method='POST',
                                post_data={'comments': 'cached entry'})
        result1 = get_changelog_comment(request)
        result2 = get_changelog_comment(request)
        self.assertEqual(result1, result2)
        self.assertEqual(result1, 'cached entry')
        self.assertTrue(hasattr(request, '_netbox_force_changelog_comment'))


class BuildErrorMessageTest(TestCase):

    @patch('netbox_force.signals.get_plugin_config', return_value=10)
    def test_browser_message(self, mock_config):
        instance = _make_mock_instance(verbose_name='Device')
        request = _make_request(path='/dcim/devices/1/edit/')
        msg = build_error_message(instance, request)
        self.assertIn('Changelog-Eintrag erforderlich', msg)
        self.assertIn('mind. 10 Zeichen', msg)

    @patch('netbox_force.signals.get_plugin_config', return_value=10)
    def test_api_message(self, mock_config):
        instance = _make_mock_instance(verbose_name='Device')
        request = _make_request(path='/api/dcim/devices/1/')
        msg = build_error_message(instance, request)
        self.assertIn('Changelog entry required', msg)
        self.assertIn('changelog_message', msg)
        self.assertIn('min 10 characters', msg)

    @patch('netbox_force.signals.get_plugin_config', return_value=10)
    def test_no_request_gives_browser_message(self, mock_config):
        instance = _make_mock_instance(verbose_name='Device')
        msg = build_error_message(instance)
        self.assertIn('Changelog-Eintrag erforderlich', msg)


class HasRealChangesTest(TestCase):

    def test_new_object(self):
        instance = _make_mock_instance(pk=None)
        self.assertTrue(has_real_changes(instance))

    def test_object_not_found(self):
        instance = _make_mock_instance(pk=999)
        instance.__class__.objects.get.side_effect = instance.__class__.DoesNotExist
        self.assertTrue(has_real_changes(instance))

    def test_no_changes(self):
        instance = _make_mock_instance(
            pk=1, fields={'name': 'same', 'last_updated': 'new_ts'}
        )
        old_instance = MagicMock()
        old_instance.name = 'same'
        old_instance.last_updated = 'old_ts'
        instance.__class__.objects.get.return_value = old_instance
        self.assertFalse(has_real_changes(instance))

    def test_real_change(self):
        instance = _make_mock_instance(
            pk=1, fields={'name': 'new_name', 'last_updated': 'new_ts'}
        )
        old_instance = MagicMock()
        old_instance.name = 'old_name'
        old_instance.last_updated = 'old_ts'
        instance.__class__.objects.get.return_value = old_instance
        self.assertTrue(has_real_changes(instance))
