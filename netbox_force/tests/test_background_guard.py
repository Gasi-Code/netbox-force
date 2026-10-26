"""
Tests for the guard that refuses NetBox 4.7 background bulk writes.

Such a write runs in an RQ worker without an HTTP request, where every check in
signals.py returns early. The guard has to refuse it before it is queued.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import TestCase

from utilities.exceptions import AbortRequest

from netbox_force import backgroundguard, signals


def _model(app_label='ipam', model_name='vlan'):
    model = MagicMock()
    model._meta.app_label = app_label
    model._meta.model_name = model_name
    model._meta.verbose_name_plural = 'VLANs'
    return model


def _request(method='PATCH', background='true', data=None, username='alice'):
    return SimpleNamespace(
        method=method,
        query_params={'background': background} if background is not None else {},
        data=[{'id': 1}] if data is None else data,
        user=SimpleNamespace(username=username, is_superuser=False, is_authenticated=True),
        path_info='/api/ipam/vlans/',
    )


class BackgroundRequestedTest(TestCase):

    def test_a_list_body_with_the_flag_is_a_background_write(self):
        self.assertTrue(backgroundguard.background_requested(_request()))

    def test_the_flag_is_case_insensitive(self):
        self.assertTrue(backgroundguard.background_requested(_request(background='TRUE')))

    def test_no_flag_is_a_synchronous_write(self):
        self.assertFalse(backgroundguard.background_requested(_request(background=None)))
        self.assertFalse(backgroundguard.background_requested(_request(background='false')))

    def test_a_single_object_body_is_never_queued_by_netbox(self):
        self.assertFalse(backgroundguard.background_requested(_request(data={'id': 1})))

    def test_a_read_is_not_a_write(self):
        self.assertFalse(backgroundguard.background_requested(_request(method='GET')))


class BlockingMessageTest(TestCase):

    def _blocking(self, request=None, action='bulk_partial_update', *, settings=None,
                  values=None, exempt_model=False, exempt_user=False, maintenance=None):
        settings = settings or MagicMock(enforcement_enabled=True, dry_run=False)
        values = values or {}

        def setting(name, default=None):
            return values.get(name, default)

        violations = MagicMock()
        with patch.object(signals, '_get_settings', return_value=settings), \
             patch.object(signals, '_get_setting', side_effect=setting), \
             patch.object(signals, 'check_maintenance_mode', return_value=maintenance), \
             patch.object(signals, 'is_exempt_model', return_value=exempt_model), \
             patch.object(signals, 'is_exempt_user', return_value=exempt_user), \
             patch.object(signals, 'log_violation', violations), \
             patch('netbox_force.models.ModelPolicy.get_policy_for_model', return_value=None):
            message = backgroundguard.blocking_message(
                request or _request(), _model(), action)
        return message, violations

    def test_an_enforced_background_write_is_refused_and_recorded(self):
        message, violations = self._blocking()

        self.assertIn('background=true', message)
        violations.assert_called_once()
        self.assertEqual(violations.call_args.args[4], 'background_write')

    def test_nothing_is_refused_while_enforcement_is_off(self):
        settings = MagicMock(enforcement_enabled=False, dry_run=False)
        message, violations = self._blocking(settings=settings)

        self.assertIsNone(message)
        violations.assert_not_called()

    def test_an_exempt_user_may_write_in_the_background(self):
        self.assertIsNone(self._blocking(exempt_user=True)[0])

    def test_an_exempt_model_may_be_written_in_the_background(self):
        self.assertIsNone(self._blocking(exempt_model=True)[0])

    def test_a_bulk_delete_follows_the_delete_switch(self):
        values = {'enforce_on_delete': False}

        self.assertIsNone(self._blocking(action='bulk_destroy', values=values)[0])
        self.assertIsNotNone(self._blocking(action='bulk_partial_update', values=values)[0])

    def test_a_bulk_create_is_refused_because_naming_rules_apply_to_new_objects(self):
        self.assertIsNotNone(self._blocking(action='bulk_create')[0])

    def test_maintenance_mode_wins_over_every_exemption(self):
        message, violations = self._blocking(
            exempt_user=True, exempt_model=True, maintenance='maintenance text',
            settings=MagicMock(enforcement_enabled=False, dry_run=True))

        self.assertEqual(message, 'maintenance text')
        self.assertEqual(violations.call_args.args[4], 'maintenance_mode')

    def test_dry_run_records_the_violation_but_lets_the_write_through(self):
        settings = MagicMock(enforcement_enabled=True, dry_run=True)
        message, violations = self._blocking(settings=settings)

        self.assertIsNone(message)
        violations.assert_called_once()


class InstallBackgroundGuardTest(TestCase):

    def _fresh_mixin(self):
        def _handle_background_request(self, request, action, action_kwargs=None):
            return 'queued'
        return type('Mixin', (), {'_handle_background_request': _handle_background_request})

    def _install(self, mixin):
        with patch.object(backgroundguard, '_mixin_class', return_value=mixin):
            return backgroundguard.install_background_guard()

    def _viewset(self, mixin):
        viewset = mixin()
        viewset.queryset = SimpleNamespace(model=_model())
        return viewset

    def test_a_refused_request_never_reaches_the_queue(self):
        mixin = self._fresh_mixin()
        self.assertTrue(self._install(mixin))

        with patch.object(backgroundguard, 'blocking_message', return_value='refused'):
            with self.assertRaises(AbortRequest):
                self._viewset(mixin)._handle_background_request(
                    _request(), 'bulk_partial_update')

    def test_an_allowed_request_is_queued_as_before(self):
        mixin = self._fresh_mixin()
        self._install(mixin)

        with patch.object(backgroundguard, 'blocking_message', return_value=None):
            result = self._viewset(mixin)._handle_background_request(
                _request(), 'bulk_partial_update')

        self.assertEqual(result, 'queued')

    def test_a_synchronous_request_is_not_inspected(self):
        mixin = self._fresh_mixin()
        self._install(mixin)

        with patch.object(backgroundguard, 'blocking_message') as blocking:
            result = self._viewset(mixin)._handle_background_request(
                _request(background=None), 'bulk_partial_update')

        self.assertEqual(result, 'queued')
        blocking.assert_not_called()

    def test_installing_twice_wraps_only_once(self):
        mixin = self._fresh_mixin()

        self.assertTrue(self._install(mixin))
        self.assertFalse(self._install(mixin))

    def test_a_netbox_without_background_writes_needs_no_guard(self):
        with patch.object(backgroundguard, '_mixin_class', side_effect=ImportError):
            self.assertFalse(backgroundguard.install_background_guard())

    def test_a_renamed_method_is_reported_and_does_not_break_startup(self):
        with self.assertLogs('netbox.plugins.netbox_force', level='WARNING'):
            self.assertFalse(self._install(type('Mixin', (), {})))
