"""
Regression tests for the security fixes.

Each test here stands for a hole that was open once. They are written against
the behaviour that closed it, not against the implementation, so a refactor
that reopens the hole still fails.
"""
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, TestCase

from netbox_force.middleware import _allowed_webhook_url
from netbox_force.signals import changelog_input_available
from netbox_force.views import _csv_safe


def _mock_instance(fields=('name', 'comments')):
    """A model instance whose _meta.fields carries the given names."""
    instance = MagicMock()
    instance._meta.app_label = 'dcim'
    instance._meta.model_name = 'device'
    instance._meta.fields = [MagicMock(name=n) for n in fields]
    for field, name in zip(instance._meta.fields, fields):
        field.name = name
    return instance


class ChangelogEnforcementBypassTests(TestCase):
    """
    F1: dropping the changelog field from the POST body used to disable the
    whole changelog, blocklist and ticket chain for that request.
    """

    def setUp(self):
        self.factory = RequestFactory()

    def test_missing_field_still_enforces_on_modern_netbox(self):
        """A POST without any changelog key must not switch enforcement off."""
        request = self.factory.post('/dcim/devices/1/edit/', {'name': 'sw-01'})
        instance = _mock_instance()

        with patch('netbox_force.signals.netbox_offers_changelog_field',
                   return_value=True):
            self.assertTrue(changelog_input_available(request, instance))

    def test_missing_field_still_enforces_when_model_has_comments(self):
        """Older NetBox: the model's own comments field is input enough."""
        request = self.factory.post('/dcim/devices/1/edit/', {'name': 'sw-01'})
        instance = _mock_instance(fields=('name', 'comments'))

        with patch('netbox_force.signals.netbox_offers_changelog_field',
                   return_value=False):
            self.assertTrue(changelog_input_available(request, instance))

    def test_model_without_any_field_is_exempt(self):
        """The one honest 'no way to type it' case still reports False."""
        request = self.factory.post('/dcim/devices/1/edit/', {'name': 'sw-01'})
        instance = _mock_instance(fields=('name',))

        with patch('netbox_force.signals.netbox_offers_changelog_field',
                   return_value=False):
            self.assertFalse(changelog_input_available(request, instance))

    def test_api_requests_are_always_enforced(self):
        request = self.factory.post('/api/dcim/devices/1/', {})
        self.assertTrue(changelog_input_available(request, _mock_instance()))


class ObjectPermissionTests(TestCase):
    """
    F5: the Graylog message endpoint must ask about the object, not the model.

    The recursion test exists because the first attempt at this fix replaced
    the wrong one of two identical code blocks: the helper ended up calling
    itself instead of falling back, which nothing noticed because every NetBox
    core model takes the other branch.
    """

    def test_helper_does_not_recurse_without_restrict(self):
        from netbox_force.views import _may_view_object

        class _PlainManager:
            """A manager with no restrict(), like a non-NetBox model."""

        obj = MagicMock()
        obj.__class__ = MagicMock()
        obj.__class__.objects = _PlainManager()
        obj._meta.app_label = 'someapp'
        obj._meta.model_name = 'somemodel'

        user = MagicMock()
        user.is_superuser = False
        user.has_perm.return_value = False

        # Must return, not blow the stack.
        self.assertFalse(_may_view_object(user, obj))
        user.has_perm.assert_called_once_with('someapp.view_somemodel')

    def test_superuser_always_passes(self):
        from netbox_force.views import _may_view_object

        user = MagicMock()
        user.is_superuser = True
        self.assertTrue(_may_view_object(user, MagicMock()))

    def test_graylog_view_delegates_to_the_object_check(self):
        import inspect

        from netbox_force.views import GraylogMessagesView

        source = inspect.getsource(GraylogMessagesView._may_view)
        self.assertIn('_may_view_object', source)
        self.assertNotIn('has_perm', source)


class CsvInjectionTests(TestCase):
    """F3: violation exports carry text an attacker chose."""

    def test_formula_prefixes_are_neutralised(self):
        for payload in ('=1+1', '+1', '-1', '@SUM(A1)', '\tcmd', '\rcmd'):
            with self.subTest(payload=payload):
                self.assertTrue(_csv_safe(payload).startswith("'"))

    def test_ordinary_text_is_untouched(self):
        for value in ('sw-01', 'Ticket-4711', 'a=b', ''):
            with self.subTest(value=value):
                self.assertEqual(_csv_safe(value), value)

    def test_none_becomes_empty(self):
        self.assertEqual(_csv_safe(None), '')


class WebhookUrlSchemeTests(TestCase):
    """F9: the delivery client also speaks file:// and ftp://."""

    def test_http_and_https_allowed(self):
        self.assertTrue(_allowed_webhook_url('http://example.test/hook'))
        self.assertTrue(_allowed_webhook_url('https://example.test/hook'))

    def test_other_schemes_rejected(self):
        for url in ('file:///etc/passwd', 'ftp://example.test/x',
                    'gopher://example.test', 'data:text/plain,x'):
            with self.subTest(url=url):
                self.assertFalse(_allowed_webhook_url(url))


class WidgetImageContentTypeTests(TestCase):
    """F2: the served type must come from a fixed table, never from guessing."""

    def test_svg_is_not_served_as_svg(self):
        from netbox_force.models import WidgetImage
        self.assertEqual(
            WidgetImage.content_type_for('payload.svg'),
            'application/octet-stream',
        )

    def test_html_is_not_served_as_html(self):
        from netbox_force.models import WidgetImage
        self.assertEqual(
            WidgetImage.content_type_for('payload.html'),
            'application/octet-stream',
        )

    def test_known_raster_types(self):
        from netbox_force.models import WidgetImage
        self.assertEqual(WidgetImage.content_type_for('logo.png'), 'image/png')
        self.assertEqual(WidgetImage.content_type_for('logo.JPG'), 'image/jpeg')


class UploadValidationTests(TestCase):
    """F2: extension whitelist plus a content check."""

    def test_svg_extension_rejected(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from netbox_force.forms import WidgetImageUploadForm

        upload = SimpleUploadedFile(
            'payload.svg',
            b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
            content_type='image/svg+xml',
        )
        form = WidgetImageUploadForm({}, {'file': upload})
        self.assertFalse(form.is_valid())
        self.assertIn('file', form.errors)

    def test_renamed_file_rejected(self):
        """A script that calls itself .png is not a png."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from netbox_force.forms import WidgetImageUploadForm

        upload = SimpleUploadedFile(
            'payload.png', b'<html><script>alert(1)</script></html>',
            content_type='image/png',
        )
        form = WidgetImageUploadForm({}, {'file': upload})
        self.assertFalse(form.is_valid())

    def test_real_png_accepted(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from netbox_force.forms import WidgetImageUploadForm

        png = (b'\x89PNG\r\n\x1a\n' + b'\x00' * 32)
        upload = SimpleUploadedFile('logo.png', png, content_type='image/png')
        form = WidgetImageUploadForm({}, {'file': upload})
        self.assertTrue(form.is_valid(), form.errors)


class RegexRuleValidationTests(TestCase):
    """F10: a nested quantifier hands every user a way to hang a worker."""

    def test_nested_quantifier_rejected(self):
        from netbox_force.forms import ValidationRuleForm

        for pattern in ('(a+)+$', r'(\w+\s?)*$', '(.*)+'):
            with self.subTest(pattern=pattern):
                form = ValidationRuleForm()
                form.cleaned_data = {'regex_pattern': pattern}
                with self.assertRaises(Exception):
                    form.clean_regex_pattern()

    def test_ordinary_pattern_accepted(self):
        from netbox_force.forms import ValidationRuleForm

        form = ValidationRuleForm()
        form.cleaned_data = {'regex_pattern': r'^sw-[a-z0-9]{2,8}$'}
        self.assertEqual(form.clean_regex_pattern(), r'^sw-[a-z0-9]{2,8}$')


class RegexSubjectBoundTests(TestCase):
    """F10: the value a pattern is applied to is bounded."""

    def test_subject_limit_is_modest(self):
        from netbox_force.signals import _MAX_REGEX_SUBJECT
        self.assertLessEqual(_MAX_REGEX_SUBJECT, 1024)


class CheckmkInputBoundTests(TestCase):
    """F13/F15: a monitored host writes its own output and its own name."""

    def test_plugin_output_is_capped(self):
        from netbox_force.sync import MAX_UPDATE_DETAILS, _worst

        rows = [{'state': 1, 'description': 'Updates',
                 'plugin_output': 'A' * 50000}]
        _state, _services, details = _worst(rows)
        self.assertLessEqual(len(details), MAX_UPDATE_DETAILS)

    def test_host_name_cap_matches_the_column(self):
        from netbox_force.sync import MAX_HOST_NAME
        self.assertLessEqual(MAX_HOST_NAME, 255)
