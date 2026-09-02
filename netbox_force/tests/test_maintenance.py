"""
Tests for maintenance mode.

Written against the promise the switch makes rather than against its
implementation: nothing an administrator can configure lifts it, and turning it
on never locks anyone out of signing in. A refactor that routes the check back
through the ordinary exemption chain fails here.
"""
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from utilities.exceptions import AbortRequest

from netbox_force.middleware import (
    MaintenanceBannerMiddleware,
    set_current_request,
)
from netbox_force.signals import (
    MAINTENANCE_EXEMPT_MODELS,
    check_maintenance_mode,
    enforce_changelog_on_delete,
    enforce_changelog_on_save,
)


def _instance(app_label='dcim', model_name='device', pk=1):
    instance = MagicMock()
    instance._meta.app_label = app_label
    instance._meta.model_name = model_name
    instance._meta.verbose_name = model_name
    instance._meta.fields = []
    instance.pk = pk
    return instance


def _user(username='alice', superuser=False):
    user = MagicMock()
    user.username = username
    user.is_superuser = superuser
    user.is_authenticated = True
    return user


def _settings(**overrides):
    """A settings row shaped like ForceSettings, maintenance on by default."""
    settings = MagicMock()
    settings.maintenance_mode = True
    settings.language = 'en'
    settings.enforcement_enabled = True
    settings.dry_run = False
    settings.audit_log_enabled = False
    for key, value in overrides.items():
        setattr(settings, key, value)
    return settings


def _request(method='POST', path='/dcim/devices/1/edit/', user=None):
    factory = RequestFactory()
    request = getattr(factory, method.lower())(path)
    request.user = user if user is not None else _user()
    return request


class MaintenanceCheckTests(TestCase):
    """check_maintenance_mode() on its own."""

    def test_off_allows_everything(self):
        self.assertIsNone(check_maintenance_mode(
            _request(), _instance(), _settings(maintenance_mode=False)))

    def test_no_settings_row_allows_everything(self):
        with patch('netbox_force.signals._get_settings', return_value=None):
            self.assertIsNone(check_maintenance_mode(_request(), _instance()))

    def test_on_blocks_an_ordinary_user(self):
        message = check_maintenance_mode(_request(), _instance(), _settings())
        self.assertIsNotNone(message)
        self.assertIn('maintenance mode', message.lower())

    def test_superuser_passes(self):
        request = _request(user=_user('root', superuser=True))
        self.assertIsNone(
            check_maintenance_mode(request, _instance(), _settings()))

    def test_anonymous_is_not_exempt(self):
        """
        An installation with LOGIN_REQUIRED off would otherwise leave the one
        caller nobody authenticated able to write.
        """
        request = _request()
        request.user = AnonymousUser()
        self.assertIsNotNone(
            check_maintenance_mode(request, _instance(), _settings()))

    def test_api_gets_the_english_message(self):
        request = _request(path='/api/dcim/devices/1/')
        message = check_maintenance_mode(
            request, _instance(), _settings(language='de'))
        self.assertIsNotNone(message)
        self.assertIn('maintenance mode', message.lower())

    def test_language_is_honoured_in_the_ui(self):
        message = check_maintenance_mode(
            _request(), _instance(), _settings(language='de'))
        self.assertIn('Wartungsmodus', message)


class MaintenanceLockoutTests(TestCase):
    """
    Signing in writes a session row and stamps the user row. Blocking those
    would lock every account out, including the administrator who would have
    to turn the mode back off.
    """

    def test_session_writes_are_never_blocked(self):
        self.assertIsNone(check_maintenance_mode(
            _request(), _instance('sessions', 'session'), _settings()))

    def test_user_writes_are_never_blocked(self):
        for app_label, model_name in (('users', 'user'), ('auth', 'user'),
                                      ('users', 'userconfig')):
            with self.subTest(model=f'{app_label}.{model_name}'):
                self.assertIsNone(check_maintenance_mode(
                    _request(), _instance(app_label, model_name), _settings()))

    def test_the_settings_row_stays_writable(self):
        """Otherwise the switch could be turned on but never off."""
        self.assertIsNone(check_maintenance_mode(
            _request(), _instance('netbox_force', 'forcesettings'), _settings()))

    def test_the_violation_log_stays_writable(self):
        self.assertIsNone(check_maintenance_mode(
            _request(), _instance('netbox_force', 'violation'), _settings()))

    def test_change_records_are_never_blocked(self):
        self.assertIsNone(check_maintenance_mode(
            _request(), _instance('core', 'objectchange'), _settings()))

    def test_content_models_are_not_on_the_exempt_list(self):
        """
        The maintenance list is deliberately shorter than EXEMPT_MODELS: a
        journal entry and an image attachment are content, and a saved filter
        is configuration. All three are what the mode exists to stop.
        """
        for label in ('extras.journalentry', 'extras.imageattachment',
                      'extras.savedfilter', 'extras.exporttemplate',
                      'dcim.device', 'ipam.vlan'):
            with self.subTest(model=label):
                self.assertNotIn(label, MAINTENANCE_EXEMPT_MODELS)


class MaintenanceCannotBeConfiguredAwayTests(TestCase):
    """
    Each test here is a setting that must NOT let a write through. They go
    through the signal handler rather than check_maintenance_mode(), because
    the promise is about the order of the checks, not about one function.
    """

    def setUp(self):
        self.instance = _instance('ipam', 'vlan')
        self.request = _request()
        set_current_request(self.request)
        self.addCleanup(set_current_request, None)

        patcher = patch('netbox_force.signals.log_violation')
        self.log_violation = patcher.start()
        self.addCleanup(patcher.stop)

    def _save_with(self, settings):
        with patch('netbox_force.signals.get_current_request',
                   return_value=self.request), \
             patch('netbox_force.signals._get_settings', return_value=settings):
            with self.assertRaises(AbortRequest):
                enforce_changelog_on_save(sender=None, instance=self.instance)

    def test_master_switch_off_does_not_lift_it(self):
        self._save_with(_settings(enforcement_enabled=False))

    def test_dry_run_does_not_lift_it(self):
        """
        Dry-run exists so a new rule can be introduced without breaking
        anyone's work. Maintenance mode exists so nobody's work reaches the
        database. Routing one through the other would disable the switch on
        every installation that has dry-run on.
        """
        self._save_with(_settings(dry_run=True))

    def test_an_exempt_user_does_not_lift_it(self):
        settings = _settings()
        settings.get_exempt_users_list.return_value = ['alice']
        self._save_with(settings)

    def test_an_exempt_group_does_not_lift_it(self):
        settings = _settings()
        settings.get_exempt_users_list.return_value = []
        settings.get_exempt_groups_list.return_value = ['operators']
        self._save_with(settings)

    def test_an_exempt_model_entry_does_not_lift_it(self):
        settings = _settings()
        settings.get_extra_exempt_models_list.return_value = ['ipam.vlan']
        self._save_with(settings)

    def test_a_model_policy_does_not_lift_it(self):
        policy = MagicMock()
        policy.enforcement_enabled = False
        with patch('netbox_force.models.ModelPolicy.get_policy_for_model',
                   return_value=policy):
            self._save_with(_settings())

    def test_a_superuser_still_gets_through(self):
        request = _request(user=_user('root', superuser=True))
        settings = _settings(enforcement_enabled=False)
        with patch('netbox_force.signals.get_current_request',
                   return_value=request), \
             patch('netbox_force.signals._get_settings', return_value=settings):
            enforce_changelog_on_save(sender=None, instance=self.instance)
        self.log_violation.assert_not_called()

    def test_deletion_is_blocked_even_with_enforce_on_delete_off(self):
        settings = _settings(enforce_on_delete=False)
        with patch('netbox_force.signals.get_current_request',
                   return_value=self.request), \
             patch('netbox_force.signals._get_settings', return_value=settings):
            with self.assertRaises(AbortRequest):
                enforce_changelog_on_delete(sender=None, instance=self.instance)

    def test_the_block_is_recorded_as_its_own_reason(self):
        self._save_with(_settings())
        reason = self.log_violation.call_args[0][4]
        self.assertEqual(reason, 'maintenance_mode')


class MaintenanceBannerTests(TestCase):
    """The banner is added to finished HTML; every condition is a refusal."""

    def setUp(self):
        self.factory = RequestFactory()

    def _run(self, request, response, maintenance=True):
        settings = _settings(maintenance_mode=maintenance)
        with patch('netbox_force.models.ForceSettings.get_settings',
                   return_value=settings):
            middleware = MaintenanceBannerMiddleware(lambda r: response)
            return middleware(request)

    @staticmethod
    def _page(body=b'<!doctype html><html><head></head><body class="x">Hi</body></html>'):
        response = HttpResponse(body, content_type='text/html; charset=utf-8')
        return response

    def _get(self, path='/dcim/devices/', user=None, **headers):
        request = self.factory.get(path, **headers)
        request.user = user if user is not None else _user()
        return request

    def test_banner_is_added_for_a_signed_in_user(self):
        response = self._run(self._get(), self._page())
        self.assertIn(b'data-netbox-force-maintenance', response.content)
        self.assertIn('maintenance mode'.encode(), response.content.lower())

    def test_banner_lands_directly_after_the_body_tag(self):
        response = self._run(self._get(), self._page())
        body = response.content
        self.assertLess(body.index(b'<body'), body.index(b'data-netbox-force-maintenance'))
        self.assertLess(body.index(b'data-netbox-force-maintenance'), body.index(b'Hi'))

    def test_a_compressed_body_is_left_alone(self):
        """Inserting bytes into a gzipped body would corrupt the page."""
        response = self._page()
        response['Content-Encoding'] = 'gzip'
        before = response.content
        result = self._run(self._get(), response)
        self.assertEqual(result.content, before)

    def test_superuser_is_told_they_can_still_write(self):
        request = self._get(user=_user('root', superuser=True))
        response = self._run(request, self._page())
        self.assertIn(b'superuser', response.content.lower())

    def test_nothing_is_added_when_the_mode_is_off(self):
        original = self._page()
        before = original.content
        response = self._run(self._get(), original, maintenance=False)
        self.assertEqual(response.content, before)

    def test_anonymous_visitors_are_not_told(self):
        request = self._get()
        request.user = AnonymousUser()
        response = self._run(request, self._page())
        self.assertNotIn(b'data-netbox-force-maintenance', response.content)

    def test_htmx_fragments_are_left_alone(self):
        """Otherwise every modal and table refresh carries its own banner."""
        request = self._get(HTTP_HX_REQUEST='true')
        response = self._run(request, self._page())
        self.assertNotIn(b'data-netbox-force-maintenance', response.content)

    def test_the_api_is_left_alone(self):
        request = self._get(path='/api/dcim/devices/')
        response = self._run(request, self._page())
        self.assertNotIn(b'data-netbox-force-maintenance', response.content)

    def test_non_html_is_left_alone(self):
        response = HttpResponse(b'{"count": 0}', content_type='application/json')
        result = self._run(self._get(), response)
        self.assertEqual(result.content, b'{"count": 0}')

    def test_error_pages_are_left_alone(self):
        response = self._page()
        response.status_code = 500
        result = self._run(self._get(), response)
        self.assertNotIn(b'data-netbox-force-maintenance', result.content)

    def test_a_document_without_a_body_tag_is_left_alone(self):
        response = HttpResponse(b'<div>fragment</div>', content_type='text/html')
        result = self._run(self._get(), response)
        self.assertEqual(result.content, b'<div>fragment</div>')

    def test_the_banner_is_never_added_twice(self):
        response = self._run(self._get(), self._page())
        once = response.content
        again = self._run(self._get(), response)
        self.assertEqual(again.content, once)

    def test_a_failure_never_breaks_the_page(self):
        original = self._page()
        before = original.content
        with patch('netbox_force.models.ForceSettings.get_settings',
                   side_effect=RuntimeError('database gone')):
            middleware = MaintenanceBannerMiddleware(lambda r: original)
            response = middleware(self._get())
        self.assertEqual(response.content, before)
