import ipaddress
import json
import re

from django import forms
from django.apps import apps
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

from .models import (
    ForceSettings, ModelPolicy, ValidationRule, ImportTemplate, GuidePage,
    LANGUAGE_CHOICES, PatchVM, PatchVMContact, PatchUpdateEntry, PATCH_STATUS_CHOICES,
    AUTO_CHANGELOG_CORE_APPS,
)

# Valid model label pattern: app_label.model_name
_MODEL_LABEL_RE = re.compile(r'^[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*$')


def _app_config(app_label):
    """AppConfig for an app label, or None when the app is not installed."""
    try:
        return apps.get_app_config(app_label)
    except LookupError:
        return None


class ForceSettingsForm(forms.ModelForm):
    """Form for the plugin settings page."""

    class Meta:
        model = ForceSettings
        fields = [
            'language',
            'enforcement_enabled',
            'min_length',
            'enforce_on_create',
            'enforce_on_delete',
            'dry_run',
            'blacklist_enabled',
            'blacklisted_phrases',
            'ticket_enabled',
            'ticket_pattern',
            'ticket_pattern_hint',
            'change_window_enabled',
            'change_window_start',
            'change_window_end',
            'change_window_weekdays',
            'audit_log_enabled',
            'audit_log_retention_days',
            'dashboard_top_users_count',
            'webhook_enabled',
            'webhook_url',
            'webhook_secret',
            'exempt_users',
            'exempt_groups',
            'extra_exempt_models',
            'import_templates_enabled',
            'guide_enabled',
            'auto_changelog_enabled',
            'patchmanagement_enabled',
            'auto_add_vms_to_patch',
            'patch_overdue_days',
            'patch_editor_groups',
            'patch_import_groups',
            'checkmk_enabled',
            'checkmk_url',
            'checkmk_username',
            'checkmk_verify_ssl',
            'checkmk_timeout',
            'checkmk_service_pattern',
            'checkmk_sync_interval',
            'checkmk_escalation_days',
        ]
        widgets = {
            'language': forms.Select(attrs={'class': 'form-select'}),
            'min_length': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 500,
            }),
            'enforce_on_create': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'enforce_on_delete': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'exempt_users': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'automation\nmonitoring\nnetbox',
            }),
            'blacklisted_phrases': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'test\nasdf\nupdate\nfix',
            }),
            'extra_exempt_models': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'myplugin.mymodel',
            }),
            'ticket_pattern': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': r'ACME-  or  JIRA-\d+  or  #\d+',
            }),
            'ticket_pattern_hint': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'z.B. JIRA-1234 oder CHG0012345',
            }),
            'dry_run': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'blacklist_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'ticket_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'change_window_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'change_window_start': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
            }),
            'change_window_end': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
            }),
            'change_window_weekdays': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '1,2,3,4,5',
            }),
            'audit_log_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'audit_log_retention_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 3650,
            }),
            'dashboard_top_users_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 100,
            }),
            'enforcement_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'webhook_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'webhook_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://webhook.site/your-unique-url',
            }),
            'webhook_secret': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional HMAC secret',
            }),
            'exempt_groups': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'network-admins\nautomation-team',
            }),
            'import_templates_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'guide_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'auto_changelog_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'patchmanagement_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'auto_add_vms_to_patch': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'patch_overdue_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 3650,
                'style': 'width: 8rem;',
            }),
            'patch_editor_groups': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Patch-Editoren, Patch-Team',
            }),
            'patch_import_groups': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Patch-Admins',
            }),
            'checkmk_url': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://checkmk.example.com/mysite',
            }),
            'checkmk_username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'netbox_force',
                'autocomplete': 'off',
            }),
            'checkmk_service_pattern': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Updates?',
            }),
            'checkmk_timeout': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 300,
                'style': 'width: 8rem;',
            }),
            'checkmk_sync_interval': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 1440,
                'style': 'width: 8rem;',
            }),
            'checkmk_escalation_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 3650,
                'style': 'width: 8rem;',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # auto_changelog_scope is stored as newline-separated app labels but
        # edited as a checkbox group, so it is handled outside Meta.fields.
        self.fields['auto_changelog_scope_areas'] = forms.MultipleChoiceField(
            required=False,
            choices=self._area_choices(),
            widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            label='Auto-changelog areas',
        )
        if self.instance and self.instance.pk:
            self.initial['auto_changelog_scope_areas'] = \
                self.instance.get_auto_changelog_scope_list()

        # The CheckMK secret is never rendered back. An empty field means
        # 'keep the stored value', so the secret cannot be read out of the
        # settings page and cannot be wiped by an unrelated save.
        self.fields['checkmk_secret'] = forms.CharField(
            required=False,
            widget=forms.PasswordInput(attrs={
                'class': 'form-control',
                'autocomplete': 'new-password',
            }, render_value=False),
            label='Automation secret',
        )
        if self.instance and self.instance.checkmk_secret_is_from_config:
            self.fields['checkmk_secret'].disabled = True

    @staticmethod
    def _area_choices():
        """
        Selectable areas: NetBox core apps first, then every installed plugin.

        Plugins are discovered at runtime rather than hardcoded, so a newly
        installed plugin — including this one — becomes selectable without a
        code change.
        """
        labels = [
            label for label in AUTO_CHANGELOG_CORE_APPS
            if _app_config(label) is not None
        ]

        try:
            from netbox.plugins import PluginConfig
            plugin_labels = sorted(
                config.label for config in apps.get_app_configs()
                if isinstance(config, PluginConfig) and config.label not in labels
            )
            labels.extend(plugin_labels)
        except Exception:
            pass

        return [(label, str(_app_config(label).verbose_name)) for label in labels]

    def clean_auto_changelog_scope_areas(self):
        return '\n'.join(self.cleaned_data.get('auto_changelog_scope_areas', []))

    def clean_checkmk_url(self):
        """Accept a pasted browser URL and reduce it to the site base."""
        raw = (self.cleaned_data.get('checkmk_url') or '').strip()
        if not raw:
            return ''
        from .checkmk import CheckmkError, normalize_base_url
        try:
            return normalize_base_url(raw)
        except CheckmkError as exc:
            raise forms.ValidationError(
                {
                    'missing_site': 'The URL must include the CheckMK site, '
                                    'e.g. https://checkmk.example.com/mysite',
                    'bad_scheme': 'Only http:// and https:// are supported.',
                }.get(exc.code, 'This is not a valid CheckMK site URL.')
            )

    def clean_checkmk_service_pattern(self):
        import re
        pattern = (self.cleaned_data.get('checkmk_service_pattern') or '').strip()
        if not pattern:
            return 'Updates?'
        try:
            re.compile(pattern)
        except re.error as exc:
            raise forms.ValidationError(f'Invalid regular expression: {exc}')
        return pattern

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.auto_changelog_scope = self.cleaned_data.get('auto_changelog_scope_areas', '')

        secret = self.cleaned_data.get('checkmk_secret')
        if secret and not obj.checkmk_secret_is_from_config:
            obj.set_checkmk_secret(secret)

        # A changed URL, user or query form invalidates the probed flavor.
        if 'checkmk_url' in self.changed_data or 'checkmk_username' in self.changed_data:
            obj.checkmk_api_flavor = 'auto'

        if commit:
            obj.save()
        return obj

    def clean_extra_exempt_models(self):
        """Validate that each line matches the app.model format."""
        value = self.cleaned_data.get('extra_exempt_models', '')
        if not value or not value.strip():
            return value

        invalid_lines = []
        for line in value.splitlines():
            line = line.strip()
            if not line:
                continue
            if not _MODEL_LABEL_RE.match(line.lower()):
                invalid_lines.append(line)

        if invalid_lines:
            raise ValidationError(
                "Invalid model format: %(values)s. "
                "Use the format 'app.model' (e.g. 'myplugin.mymodel').",
                params={'values': ', '.join(f"'{l}'" for l in invalid_lines)},
                code='invalid_model_format',
            )
        return value

    def clean_ticket_pattern(self):
        """Validate that the ticket pattern is a valid regex."""
        value = self.cleaned_data.get('ticket_pattern', '')
        if not value or not value.strip():
            return value
        try:
            re.compile(value.strip())
        except re.error as e:
            raise ValidationError(
                "Invalid regex pattern: %(error)s",
                params={'error': str(e)},
                code='invalid_regex',
            )
        return value

    def clean_change_window_weekdays(self):
        """Validate comma-separated weekday numbers (1-7)."""
        value = self.cleaned_data.get('change_window_weekdays', '')
        if not value or not value.strip():
            return value

        invalid = []
        for part in value.split(','):
            part = part.strip()
            if not part:
                continue
            try:
                day = int(part)
                if day < 1 or day > 7:
                    invalid.append(part)
            except ValueError:
                invalid.append(part)

        if invalid:
            raise ValidationError(
                "Invalid weekday values: %(values)s. "
                "Use numbers 1-7 (1=Monday, 7=Sunday), separated by commas.",
                params={'values': ', '.join(f"'{v}'" for v in invalid)},
                code='invalid_weekdays',
            )
        return value

    def clean(self):
        """Cross-field validation for the change window and CheckMK block."""
        cleaned = super().clean()
        if cleaned.get('change_window_enabled'):
            if not cleaned.get('change_window_start'):
                self.add_error('change_window_start',
                               'Start time is required when the change window is enabled.')
            if not cleaned.get('change_window_end'):
                self.add_error('change_window_end',
                               'End time is required when the change window is enabled.')

        if cleaned.get('checkmk_enabled'):
            for name in ('checkmk_url', 'checkmk_username'):
                if not cleaned.get(name):
                    self.add_error(
                        name, 'Required when the CheckMK integration is enabled.')
            # A stored secret counts — the field stays empty on every reload.
            has_secret = bool(
                cleaned.get('checkmk_secret')
                or (self.instance.pk and self.instance.checkmk_has_secret)
            )
            if not has_secret:
                self.add_error('checkmk_secret',
                               'Required when the CheckMK integration is enabled.')
        return cleaned


class GraylogSettingsForm(forms.ModelForm):
    """
    Form for the Graylog page. Kept apart from ForceSettingsForm so the two
    pages cannot overwrite each other's fields when both are open.
    """

    _EVENT_FIELDS = [
        'graylog_ev_object_create', 'graylog_ev_object_update',
        'graylog_ev_object_delete', 'graylog_ev_login', 'graylog_ev_logout',
        'graylog_ev_login_failed', 'graylog_ev_violation',
        'graylog_ev_settings_change',
    ]
    _LEVEL_FIELDS = [
        'graylog_lvl_object_create', 'graylog_lvl_object_update',
        'graylog_lvl_object_delete', 'graylog_lvl_login', 'graylog_lvl_logout',
        'graylog_lvl_login_failed', 'graylog_lvl_violation',
        'graylog_lvl_settings_change',
    ]

    class Meta:
        model = ForceSettings
        fields = [
            'graylog_enabled',
            'graylog_host',
            'graylog_port',
            'graylog_transport',
            'graylog_verify_ssl',
            'graylog_timeout',
            'graylog_source_name',
            'graylog_ev_object_create', 'graylog_lvl_object_create',
            'graylog_ev_object_update', 'graylog_lvl_object_update',
            'graylog_ev_object_delete', 'graylog_lvl_object_delete',
            'graylog_ev_login', 'graylog_lvl_login',
            'graylog_ev_logout', 'graylog_lvl_logout',
            'graylog_ev_login_failed', 'graylog_lvl_login_failed',
            'graylog_ev_violation', 'graylog_lvl_violation',
            'graylog_ev_settings_change', 'graylog_lvl_settings_change',
            'graylog_bulk_threshold',
            'graylog_max_events_per_request',
            'graylog_only_outside_hours',
            'graylog_business_days',
            'graylog_business_start',
            'graylog_business_end',
            'graylog_read_enabled',
            'graylog_api_url',
            'graylog_api_verify_ssl',
            'graylog_api_timeout',
            'graylog_stream_id',
            'graylog_search_flavor',
            'graylog_poll_interval',
            'graylog_poll_batch_size',
            'graylog_window_hours',
            'graylog_message_limit',
            'graylog_domain_suffixes',
            'graylog_silent_after_hours',
        ]
        widgets = {
            'graylog_api_url': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://graylog.example.com',
            }),
            'graylog_api_timeout': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 1, 'max': 120,
            }),
            'graylog_stream_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '000000000000000000000001',
            }),
            'graylog_search_flavor': forms.Select(attrs={'class': 'form-select'}),
            'graylog_poll_interval': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 0, 'max': 1440,
            }),
            'graylog_poll_batch_size': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 1, 'max': 10000,
            }),
            'graylog_window_hours': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 1, 'max': 720,
            }),
            'graylog_message_limit': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 1, 'max': 200,
            }),
            'graylog_silent_after_hours': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 0, 'max': 8760,
            }),
            'graylog_domain_suffixes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'example.com\nintern.example.com',
            }),
            'graylog_host': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'graylog.example.com',
            }),
            'graylog_port': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 1, 'max': 65535,
            }),
            'graylog_transport': forms.Select(attrs={'class': 'form-select'}),
            'graylog_timeout': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 1, 'max': 60,
            }),
            'graylog_source_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'netbox',
            }),
            'graylog_bulk_threshold': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 0, 'max': 10000,
            }),
            'graylog_max_events_per_request': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 1, 'max': 10000,
            }),
            'graylog_business_days': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': '1,2,3,4,5',
            }),
            'graylog_business_start': forms.TimeInput(attrs={
                'class': 'form-control', 'type': 'time',
            }),
            'graylog_business_end': forms.TimeInput(attrs={
                'class': 'form-control', 'type': 'time',
            }),
        }

    _SEARCH_FLAVOR_CHOICES = [
        ('auto', 'Detect automatically'),
        ('legacy', 'Legacy search API (GET only)'),
        ('views', 'Views search API'),
    ]

    def __init__(self, *args, ui=None, stream_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = ui or {}
        for name in self._EVENT_FIELDS + ['graylog_enabled', 'graylog_verify_ssl',
                                          'graylog_only_outside_hours',
                                          'graylog_read_enabled',
                                          'graylog_api_verify_ssl']:
            self.fields[name].widget.attrs['class'] = 'form-check-input'
        for name in self._LEVEL_FIELDS:
            self.fields[name].widget.attrs['class'] = 'form-select form-select-sm'
        # Model verbose names are English by design; the page labels follow the
        # configured plugin language like every other view.
        for name in self._EVENT_FIELDS:
            translated = self.ui.get('graylog_event_' + name.replace('graylog_ev_', ''))
            if translated:
                self.fields[name].label = translated

        self.fields['graylog_search_flavor'] = forms.ChoiceField(
            required=False,
            choices=self._SEARCH_FLAVOR_CHOICES,
            initial=getattr(self.instance, 'graylog_search_flavor', 'auto') or 'auto',
            widget=forms.Select(attrs={'class': 'form-select'}),
            label=self.ui.get('graylog_label_flavor', 'Search API form'),
        )

        # The API token is never rendered back. An empty field means 'keep the
        # stored value', so the token cannot be read out of the settings page
        # and cannot be wiped by an unrelated save.
        self.fields['graylog_token'] = forms.CharField(
            required=False,
            widget=forms.PasswordInput(attrs={
                'class': 'form-control',
                'autocomplete': 'new-password',
            }, render_value=False),
            label=self.ui.get('graylog_label_token', 'API token'),
        )

        # Populated by the view once a connection exists; until then the stream
        # is entered by hand rather than picked from an empty dropdown.
        if stream_choices:
            self.fields['graylog_stream_id'] = forms.ChoiceField(
                required=False,
                choices=[('', self.ui.get('graylog_all_streams', 'All streams'))]
                        + list(stream_choices),
                initial=getattr(self.instance, 'graylog_stream_id', ''),
                widget=forms.Select(attrs={'class': 'form-select'}),
                label=self.ui.get('graylog_label_stream', 'Stream'),
            )

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.graylog_search_flavor = self.cleaned_data.get('graylog_search_flavor') or 'auto'
        token = self.cleaned_data.get('graylog_token')
        if token:
            obj.set_graylog_token(token)
        if commit:
            obj.save()
        return obj

    def event_rows(self):
        """Pairs the checkbox and its severity select for the template."""
        for toggle, level in zip(self._EVENT_FIELDS, self._LEVEL_FIELDS):
            yield {
                'key': toggle.replace('graylog_ev_', ''),
                'toggle': self[toggle],
                'level': self[level],
            }

    def clean_graylog_host(self):
        host = (self.cleaned_data.get('graylog_host') or '').strip()
        # A pasted browser URL is the obvious mistake here; strip it down rather
        # than rejecting it.
        for prefix in ('https://', 'http://'):
            if host.lower().startswith(prefix):
                host = host[len(prefix):]
        host = host.split('/', 1)[0]
        if ':' in host and not host.startswith('['):
            host = host.split(':', 1)[0]
        return host

    def clean_graylog_api_url(self):
        raw = (self.cleaned_data.get('graylog_api_url') or '').strip()
        if not raw:
            return ''
        from .graylog_api import GraylogApiError, normalize_api_url
        try:
            return normalize_api_url(raw)
        except GraylogApiError as exc:
            raise ValidationError(
                f'Could not read this as a Graylog address ({exc.code}).')

    def clean_graylog_business_days(self):
        raw = (self.cleaned_data.get('graylog_business_days') or '').strip()
        if not raw:
            return ''
        days = []
        for part in raw.split(','):
            part = part.strip()
            if not part:
                continue
            if not part.isdigit() or not 1 <= int(part) <= 7:
                raise ValidationError(
                    'Use ISO weekday numbers from 1 (Monday) to 7 (Sunday).')
            days.append(part)
        return ','.join(days)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('graylog_enabled') and not cleaned.get('graylog_host'):
            self.add_error('graylog_host',
                           'Required when Graylog output is enabled.')

        start = cleaned.get('graylog_business_start')
        end = cleaned.get('graylog_business_end')
        if cleaned.get('graylog_only_outside_hours') and not (start and end):
            self.add_error(
                'graylog_only_outside_hours',
                'Set a start and end time first — without a window this filter '
                'would suppress every event.')
        if bool(start) != bool(end):
            self.add_error('graylog_business_end' if start else 'graylog_business_start',
                           'Set both times or neither.')

        if cleaned.get('graylog_read_enabled'):
            if not cleaned.get('graylog_api_url'):
                self.add_error('graylog_api_url',
                               'Required when reading from Graylog is enabled.')
            # A stored token counts — the field stays empty on every reload.
            has_token = bool(
                cleaned.get('graylog_token')
                or (self.instance.pk and self.instance.graylog_has_token)
            )
            if not has_token:
                self.add_error('graylog_token',
                               'Required when reading from Graylog is enabled.')
        return cleaned


class ValidationRuleForm(forms.ModelForm):
    """Form for creating/editing validation rules."""

    class Meta:
        model = ValidationRule
        fields = [
            'rule_type',
            'model_label',
            'field_name',
            'regex_pattern',
            'error_message',
            'enabled',
        ]
        widgets = {
            'rule_type': forms.Select(attrs={'class': 'form-select'}),
            'model_label': forms.Select(attrs={
                'class': 'form-select',
            }),
            'field_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'name',
            }),
            'regex_pattern': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': r'^[A-Z]{3}-\d{3}$',
            }),
            'error_message': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Device name must match format: ABC-123',
            }),
            'enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate model_label choices from Django's app registry
        model_choices = [('', '---------')]
        for model in apps.get_models():
            label = f"{model._meta.app_label}.{model._meta.model_name}"
            verbose = str(model._meta.verbose_name).title()
            model_choices.append((label, f"{label} — {verbose}"))
        model_choices.sort(key=lambda c: c[0])
        self.fields['model_label'].widget.choices = model_choices

    def clean_model_label(self):
        """Validate that the model label matches the app.model format."""
        value = self.cleaned_data.get('model_label', '')
        if not value:
            raise ValidationError("Model label is required.")
        if not _MODEL_LABEL_RE.match(value.lower()):
            raise ValidationError(
                "Invalid model format: '%(value)s'. "
                "Use the format 'app.model' (e.g. 'dcim.device').",
                params={'value': value},
                code='invalid_model_format',
            )
        return value.lower()

    def clean_regex_pattern(self):
        """Validate regex pattern if provided."""
        value = self.cleaned_data.get('regex_pattern', '')
        if not value:
            return value
        try:
            re.compile(value)
        except re.error as e:
            raise ValidationError(
                "Invalid regex pattern: %(error)s",
                params={'error': str(e)},
                code='invalid_regex',
            )
        return value

    def clean(self):
        """Cross-field validation: naming rules require a regex pattern."""
        cleaned = super().clean()
        rule_type = cleaned.get('rule_type')
        regex_pattern = cleaned.get('regex_pattern', '')

        if rule_type == 'naming' and not regex_pattern:
            self.add_error('regex_pattern',
                           'A regex pattern is required for naming convention rules.')
        return cleaned


class ImportTemplateForm(forms.ModelForm):
    """Form for creating/editing import templates."""

    class Meta:
        model = ImportTemplate
        fields = [
            'model_label',
            'display_name',
            'description',
            'csv_content',
            'enabled',
            'sort_order',
        ]
        widgets = {
            'model_label': forms.Select(attrs={'class': 'form-select'}),
            'display_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Device Import Template',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Template for importing devices via CSV...',
            }),
            'csv_content': forms.Textarea(attrs={
                'class': 'form-control font-monospace',
                'rows': 10,
                'placeholder': 'name,site,device_type,role,status\nserver-01,main-dc,PowerEdge R640,server,active',
            }),
            'enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 9999,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate model_label choices from Django's app registry
        model_choices = [('', '---------')]
        for model in apps.get_models():
            label = f"{model._meta.app_label}.{model._meta.model_name}"
            verbose = str(model._meta.verbose_name).title()
            model_choices.append((label, f"{label} — {verbose}"))
        model_choices.sort(key=lambda c: c[0])
        self.fields['model_label'].widget.choices = model_choices

    def clean_model_label(self):
        """Validate that the model label matches the app.model format."""
        value = self.cleaned_data.get('model_label', '')
        if not value:
            raise ValidationError("Model label is required.")
        if not _MODEL_LABEL_RE.match(value.lower()):
            raise ValidationError(
                "Invalid model format: '%(value)s'. "
                "Use the format 'app.model' (e.g. 'dcim.device').",
                params={'value': value},
                code='invalid_model_format',
            )
        return value.lower()


class ModelPolicyForm(forms.ModelForm):
    """Form for creating/editing per-model enforcement policies."""

    class Meta:
        model = ModelPolicy
        fields = [
            'model_label',
            'enforcement_enabled',
            'min_length_override',
            'check_naming_rules',
            'check_required_fields_rules',
            'enabled',
        ]
        widgets = {
            'model_label': forms.Select(attrs={'class': 'form-select'}),
            'enforcement_enabled': forms.NullBooleanSelect(attrs={'class': 'form-select'}),
            'min_length_override': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 500,
                'placeholder': 'Leave empty to use global setting',
            }),
            'check_naming_rules': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'check_required_fields_rules': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate model_label choices from Django's app registry
        model_choices = [('', '---------')]
        for model in apps.get_models():
            label = f"{model._meta.app_label}.{model._meta.model_name}"
            verbose = str(model._meta.verbose_name).title()
            model_choices.append((label, f"{label} — {verbose}"))
        model_choices.sort(key=lambda c: c[0])
        self.fields['model_label'].widget.choices = model_choices
        # Make min_length_override not required
        self.fields['min_length_override'].required = False

    def clean_model_label(self):
        """Validate that the model label matches the app.model format."""
        value = self.cleaned_data.get('model_label', '')
        if not value:
            raise ValidationError("Model label is required.")
        if not _MODEL_LABEL_RE.match(value.lower()):
            raise ValidationError(
                "Invalid model format: '%(value)s'. "
                "Use the format 'app.model' (e.g. 'dcim.device').",
                params={'value': value},
                code='invalid_model_format',
            )
        return value.lower()


class GuidePageForm(forms.ModelForm):
    """Form for editing the user guide content."""

    class Meta:
        model = GuidePage
        fields = ['content']
        widgets = {
            'content': forms.HiddenInput(),  # Quill populates this via JS
        }


class WidgetImageUploadForm(forms.Form):
    """Form for uploading widget images."""

    _MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
    _ALLOWED_EXTENSIONS = ['svg', 'png', 'jpg', 'jpeg', 'gif']

    file = forms.FileField(
        label='Image file',
        validators=[
            FileExtensionValidator(allowed_extensions=_ALLOWED_EXTENSIONS),
        ],
        help_text='Allowed formats: SVG, PNG, JPG, JPEG, GIF. Max size: 5 MB.',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.svg,.png,.jpg,.jpeg,.gif',
        }),
    )

    def clean_file(self):
        f = self.cleaned_data.get('file')
        if f and f.size > self._MAX_SIZE_BYTES:
            raise ValidationError(
                'File too large. Maximum allowed size is 5 MB '
                f'(uploaded: {f.size / 1024 / 1024:.1f} MB).'
            )
        return f


# =============================================================================
# PATCH MANAGEMENT FORMS
# =============================================================================

def _get_contact_choices(empty_label='— not selected —'):
    """Returns list of (pk, name) tuples from tenancy.Contact."""
    try:
        from django.apps import apps
        Contact = apps.get_model('tenancy', 'Contact')
        choices = [(c.pk, c.name) for c in Contact.objects.order_by('name')]
    except Exception:
        choices = []
    if empty_label is not None:
        choices = [('', empty_label)] + choices
    return choices


class PatchVMForm(forms.ModelForm):
    admin_contact_ids = forms.MultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '6'}),
        label='Administrators',
    )
    vb_contact_ids = forms.MultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '6'}),
        label='Process Owners',
    )

    class Meta:
        model = PatchVM
        fields = [
            'vm', 'device', 'fqdn', 'ip_address',
            'os_info', 'maintenance_window', 'update_installation',
            'patch_status', 'ticket_number', 'comment',
        ]
        widgets = {
            'vm': forms.Select(attrs={'class': 'form-select'}),
            'device': forms.Select(attrs={'class': 'form-select'}),
            'fqdn': forms.TextInput(attrs={'class': 'form-control'}),
            'ip_address': forms.Select(attrs={'class': 'form-select'}),
            'os_info': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'z.B. Ubuntu 24.04 LTS',
                'list': 'platform-datalist',
                'autocomplete': 'off',
            }),
            'maintenance_window': forms.Select(attrs={'class': 'form-select'}),
            'update_installation': forms.Select(attrs={'class': 'form-select'}),
            'patch_status': forms.Select(attrs={'class': 'form-select'}),
            'ticket_number': forms.TextInput(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # IP address: set queryset + label showing IP and DNS name
        try:
            IPAddress = apps.get_model('ipam', 'IPAddress')
            self.fields['ip_address'].queryset = IPAddress.objects.order_by('address')
            self.fields['ip_address'].empty_label = '— no IP selected —'
            self.fields['ip_address'].label_from_instance = (
                lambda obj: (
                    f"{str(obj.address).split('/')[0]}  —  {obj.dns_name}"
                    if obj.dns_name
                    else str(obj.address).split('/')[0]
                )
            )
        except Exception:
            pass
        # Platform names for OS datalist autocomplete
        try:
            Platform = apps.get_model('dcim', 'Platform')
            self.platform_names = list(Platform.objects.order_by('name').values_list('name', flat=True))
        except Exception:
            self.platform_names = []
        # Contact choices
        contact_choices = _get_contact_choices(empty_label=None)
        self.fields['admin_contact_ids'].choices = contact_choices
        self.fields['vb_contact_ids'].choices = contact_choices
        # Contact data for JS search widget (list of {pk, name} dicts)
        self.contact_data = [{'pk': pk, 'name': name} for pk, name in contact_choices]
        # Pre-selected contacts — from POST (bound) or DB (unbound)
        if self.is_bound:
            self.selected_admin_data = [int(x) for x in self.data.getlist('admin_contact_ids') if x]
            self.selected_vb_data = [int(x) for x in self.data.getlist('vb_contact_ids') if x]
        elif self.instance and self.instance.pk:
            admin_pks = list(self.instance.vm_contacts.filter(role='admin').values_list('contact_id', flat=True))
            vb_pks = list(self.instance.vm_contacts.filter(role='vb').values_list('contact_id', flat=True))
            self.selected_admin_data = admin_pks
            self.selected_vb_data = vb_pks
            self.fields['admin_contact_ids'].initial = [str(p) for p in admin_pks]
            self.fields['vb_contact_ids'].initial = [str(p) for p in vb_pks]
        else:
            self.selected_admin_data = []
            self.selected_vb_data = []

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            # Sync admin contacts
            instance.vm_contacts.filter(role='admin').delete()
            for pk in self.cleaned_data.get('admin_contact_ids', []):
                PatchVMContact.objects.get_or_create(
                    patch_vm=instance, contact_id=int(pk), role='admin'
                )
            # Sync vb contacts
            instance.vm_contacts.filter(role='vb').delete()
            for pk in self.cleaned_data.get('vb_contact_ids', []):
                PatchVMContact.objects.get_or_create(
                    patch_vm=instance, contact_id=int(pk), role='vb'
                )
            self.save_m2m()
        return instance


class PatchVMBulkEditForm(forms.Form):
    """Bulk-edit form for PatchVM — only fields with apply_X checked are written."""
    apply_os_info = forms.BooleanField(required=False)
    os_info = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'list': 'platform-datalist',
            'autocomplete': 'off',
            'placeholder': 'z.B. Ubuntu 24.04 LTS',
        }),
    )
    apply_admin_contacts = forms.BooleanField(required=False)
    admin_contact_ids = forms.MultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'}),
        label='Administrators',
    )
    apply_vb_contacts = forms.BooleanField(required=False)
    vb_contact_ids = forms.MultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'}),
        label='Process Owners',
    )
    apply_ticket_number = forms.BooleanField(required=False)
    ticket_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    apply_comment = forms.BooleanField(required=False)
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        contact_choices = _get_contact_choices(empty_label=None)
        self.fields['admin_contact_ids'].choices = contact_choices
        self.fields['vb_contact_ids'].choices = contact_choices
        self.contact_data = [{'pk': pk, 'name': name} for pk, name in contact_choices]
        try:
            Platform = apps.get_model('dcim', 'Platform')
            self.platform_names = list(Platform.objects.order_by('name').values_list('name', flat=True))
        except Exception:
            self.platform_names = []
        if self.is_bound:
            self.selected_admin_data = [int(x) for x in self.data.getlist('admin_contact_ids') if x]
            self.selected_vb_data = [int(x) for x in self.data.getlist('vb_contact_ids') if x]
        else:
            self.selected_admin_data = []
            self.selected_vb_data = []


class PatchUpdateEntryForm(forms.ModelForm):
    updated_by_contact = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Updated By',
    )

    class Meta:
        model = PatchUpdateEntry
        fields = ['date', 'version_before', 'version_after', 'software', 'info']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'version_before': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1.2.3'}),
            'version_after': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1.2.4'}),
            'software': forms.TextInput(attrs={'class': 'form-control'}),
            'info': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['updated_by_contact'].choices = _get_contact_choices()
        if self.instance and self.instance.pk and self.instance.updated_by_contact_id:
            self.fields['updated_by_contact'].initial = str(self.instance.updated_by_contact_id)

    def save(self, commit=True):
        instance = super().save(commit=False)
        pk_str = self.cleaned_data.get('updated_by_contact')
        instance.updated_by_contact_id = int(pk_str) if pk_str else None
        if commit:
            instance.save()
        return instance


class PatchStatusForm(forms.Form):
    patch_status = forms.ChoiceField(
        choices=PATCH_STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
    )


