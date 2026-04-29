import ipaddress
import re

from django import forms
from django.apps import apps
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

from .models import (
    ForceSettings, ModelPolicy, ValidationRule, ImportTemplate, GuidePage,
    WizardConfig, LANGUAGE_CHOICES, WIZARD_CONFIGURABLE_FIELDS,
)

# Valid model label pattern: app_label.model_name
_MODEL_LABEL_RE = re.compile(r'^[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*$')


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
            'wizards_enabled',
            'auto_changelog_enabled',
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
            'wizards_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'auto_changelog_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }

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
        """Cross-field validation: require start/end when change window is enabled."""
        cleaned = super().clean()
        if cleaned.get('change_window_enabled'):
            if not cleaned.get('change_window_start'):
                self.add_error('change_window_start',
                               'Start time is required when the change window is enabled.')
            if not cleaned.get('change_window_end'):
                self.add_error('change_window_end',
                               'End time is required when the change window is enabled.')
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
# WIZARD FORMS
# =============================================================================

_FC = 'form-control'
_FS = 'form-select'
_CI = 'form-check-input'

_CHANGELOG_FIELD = forms.CharField(
    label='Changelog-Nachricht',
    widget=forms.TextInput(attrs={
        'class': _FC,
        'placeholder': 'z.B. IP für Server-01 angelegt (Ticket-123)',
    }),
)

STATUS_IP = [
    ('active',      'Aktiv'),
    ('reserved',    'Reserviert'),
    ('deprecated',  'Abgekündigt'),
    ('dhcp',        'DHCP'),
    ('slaac',       'SLAAC'),
]

STATUS_PREFIX = [
    ('container',   'Container'),
    ('active',      'Aktiv'),
    ('reserved',    'Reserviert'),
    ('deprecated',  'Abgekündigt'),
]

STATUS_VLAN = [
    ('active',      'Aktiv'),
    ('reserved',    'Reserviert'),
    ('deprecated',  'Abgekündigt'),
]

STATUS_SITE = [
    ('active',          'Aktiv'),
    ('planned',         'Geplant'),
    ('staging',         'Staging'),
    ('decommissioning', 'In Stilllegung'),
    ('retired',         'Stillgelegt'),
]

STATUS_DEVICE = [
    ('active',          'Aktiv'),
    ('planned',         'Geplant'),
    ('staged',          'Staged'),
    ('failed',          'Defekt'),
    ('offline',         'Offline'),
    ('inventory',       'Inventar'),
    ('decommissioning', 'In Stilllegung'),
]

STATUS_CIRCUIT = [
    ('active',          'Aktiv'),
    ('planned',         'Geplant'),
    ('provisioning',    'In Einrichtung'),
    ('offline',         'Offline'),
    ('deprovisioning',  'In Kündigung'),
    ('decommissioned',  'Stillgelegt'),
]


class WizardIPForm(forms.Form):
    address = forms.CharField(
        label='IP-Adresse / CIDR',
        widget=forms.TextInput(attrs={'class': _FC, 'placeholder': '10.0.1.100/24'}),
    )
    status = forms.ChoiceField(
        label='Status',
        choices=STATUS_IP,
        initial='active',
        widget=forms.Select(attrs={'class': _FS}),
    )
    dns_name = forms.CharField(
        label='DNS-Name',
        required=False,
        widget=forms.TextInput(attrs={'class': _FC, 'placeholder': 'server-01.example.com'}),
    )
    description = forms.CharField(
        label='Beschreibung',
        required=False,
        widget=forms.TextInput(attrs={'class': _FC}),
    )
    tenant = forms.ModelChoiceField(
        label='Mandant',
        queryset=None,
        required=False,
        empty_label='— kein Mandant —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    role = forms.ModelChoiceField(
        label='Rolle',
        queryset=None,
        required=False,
        empty_label='— keine Rolle —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    changelog_message = forms.CharField(
        label='Changelog-Nachricht',
        widget=forms.TextInput(attrs={
            'class': _FC,
            'placeholder': 'z.B. IP für Server-01 angelegt',
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from tenancy.models import Tenant
            from ipam.models import Role
            self.fields['tenant'].queryset = Tenant.objects.all().order_by('name')
            self.fields['role'].queryset = Role.objects.all().order_by('name')
        except Exception:
            self.fields['tenant'].queryset = forms.ModelChoiceField(queryset=None).queryset
            self.fields['role'].queryset = forms.ModelChoiceField(queryset=None).queryset

    def clean_address(self):
        value = self.cleaned_data.get('address', '').strip()
        try:
            ipaddress.ip_interface(value)
        except ValueError:
            raise ValidationError(
                'Ungültige IP-Adresse / CIDR-Notation (z.B. 10.0.1.100/24 oder 2001:db8::1/64).'
            )
        if '/' not in value:
            raise ValidationError(
                'Bitte Präfixlänge angeben (z.B. 10.0.1.100/24).'
            )
        return value

    def clean_dns_name(self):
        value = (self.cleaned_data.get('dns_name') or '').strip()
        if value and '_' in value:
            raise ValidationError('DNS-Name darf keine Unterstriche enthalten.')
        if value and ' ' in value:
            raise ValidationError('DNS-Name darf keine Leerzeichen enthalten.')
        return value


class WizardPrefixForm(forms.Form):
    prefix = forms.CharField(
        label='Prefix (CIDR)',
        widget=forms.TextInput(attrs={'class': _FC, 'placeholder': '10.0.0.0/24'}),
    )
    status = forms.ChoiceField(
        label='Status',
        choices=STATUS_PREFIX,
        initial='active',
        widget=forms.Select(attrs={'class': _FS}),
    )
    role = forms.ModelChoiceField(
        label='Rolle',
        queryset=None,
        required=True,
        empty_label='— Rolle auswählen —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    tenant = forms.ModelChoiceField(
        label='Mandant',
        queryset=None,
        required=False,
        empty_label='— kein Mandant —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    site = forms.ModelChoiceField(
        label='Standort',
        queryset=None,
        required=False,
        empty_label='— kein Standort —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    vlan = forms.ModelChoiceField(
        label='VLAN',
        queryset=None,
        required=False,
        empty_label='— kein VLAN —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    description = forms.CharField(
        label='Beschreibung',
        required=False,
        widget=forms.TextInput(attrs={'class': _FC}),
    )
    changelog_message = forms.CharField(
        label='Changelog-Nachricht',
        widget=forms.TextInput(attrs={
            'class': _FC,
            'placeholder': 'z.B. Produktionsnetz Standort Berlin angelegt',
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from ipam.models import Role, VLAN
            from tenancy.models import Tenant
            from dcim.models import Site
            self.fields['role'].queryset = Role.objects.all().order_by('name')
            self.fields['tenant'].queryset = Tenant.objects.all().order_by('name')
            self.fields['site'].queryset = Site.objects.all().order_by('name')
            self.fields['vlan'].queryset = VLAN.objects.all().order_by('group', 'vid')
        except Exception:
            pass

    def clean_prefix(self):
        value = self.cleaned_data.get('prefix', '').strip()
        try:
            ipaddress.ip_network(value, strict=False)
        except ValueError:
            raise ValidationError(
                'Ungültige Netzwerkadresse (z.B. 10.0.0.0/24 oder 2001:db8::/48).'
            )
        if '/' not in value:
            raise ValidationError('Bitte Präfixlänge angeben (z.B. 10.0.0.0/24).')
        return value


class WizardVLANForm(forms.Form):
    vid = forms.IntegerField(
        label='VLAN-ID',
        min_value=1,
        max_value=4094,
        widget=forms.NumberInput(attrs={'class': _FC, 'placeholder': '100'}),
    )
    name = forms.CharField(
        label='VLAN-Name',
        widget=forms.TextInput(attrs={'class': _FC, 'placeholder': 'VLAN-Produktion'}),
    )
    group = forms.ModelChoiceField(
        label='VLAN-Gruppe',
        queryset=None,
        required=True,
        empty_label='— Gruppe auswählen —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    status = forms.ChoiceField(
        label='Status',
        choices=STATUS_VLAN,
        initial='active',
        widget=forms.Select(attrs={'class': _FS}),
    )
    role = forms.ModelChoiceField(
        label='Rolle',
        queryset=None,
        required=True,
        empty_label='— Rolle auswählen —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    tenant = forms.ModelChoiceField(
        label='Mandant',
        queryset=None,
        required=False,
        empty_label='— kein Mandant —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    changelog_message = forms.CharField(
        label='Changelog-Nachricht',
        widget=forms.TextInput(attrs={
            'class': _FC,
            'placeholder': 'z.B. VLAN für Produktionsnetz angelegt',
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from ipam.models import VLANGroup, Role
            from tenancy.models import Tenant
            self.fields['group'].queryset = VLANGroup.objects.all().order_by('name')
            self.fields['role'].queryset = Role.objects.all().order_by('name')
            self.fields['tenant'].queryset = Tenant.objects.all().order_by('name')
        except Exception:
            pass


class WizardSiteForm(forms.Form):
    name = forms.CharField(
        label='Standortname',
        widget=forms.TextInput(attrs={'class': _FC, 'placeholder': 'Frankfurt-DC1'}),
    )
    status = forms.ChoiceField(
        label='Status',
        choices=STATUS_SITE,
        initial='active',
        widget=forms.Select(attrs={'class': _FS}),
    )
    tenant = forms.ModelChoiceField(
        label='Mandant',
        queryset=None,
        required=True,
        empty_label='— Mandant auswählen —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    region = forms.ModelChoiceField(
        label='Region',
        queryset=None,
        required=False,
        empty_label='— keine Region —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    group = forms.ModelChoiceField(
        label='Standortgruppe',
        queryset=None,
        required=False,
        empty_label='— keine Gruppe —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    description = forms.CharField(
        label='Beschreibung',
        required=False,
        widget=forms.TextInput(attrs={'class': _FC}),
    )
    changelog_message = forms.CharField(
        label='Changelog-Nachricht',
        widget=forms.TextInput(attrs={
            'class': _FC,
            'placeholder': 'z.B. Neues Rechenzentrum Frankfurt angelegt',
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from tenancy.models import Tenant
            from dcim.models import Region, SiteGroup
            self.fields['tenant'].queryset = Tenant.objects.all().order_by('name')
            self.fields['region'].queryset = Region.objects.all().order_by('name')
            self.fields['group'].queryset = SiteGroup.objects.all().order_by('name')
        except Exception:
            pass


class WizardDeviceForm(forms.Form):
    name = forms.CharField(
        label='Gerätename (Hostname)',
        widget=forms.TextInput(attrs={
            'class': _FC,
            'placeholder': 'sw-berlin-01',
        }),
    )
    device_role = forms.ModelChoiceField(
        label='Geräterolle',
        queryset=None,
        required=True,
        empty_label='— Rolle auswählen —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    device_type = forms.ModelChoiceField(
        label='Gerätetyp',
        queryset=None,
        required=True,
        empty_label='— Typ auswählen —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    site = forms.ModelChoiceField(
        label='Standort',
        queryset=None,
        required=True,
        empty_label='— Standort auswählen —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    status = forms.ChoiceField(
        label='Status',
        choices=STATUS_DEVICE,
        initial='active',
        widget=forms.Select(attrs={'class': _FS}),
    )
    tenant = forms.ModelChoiceField(
        label='Mandant',
        queryset=None,
        required=False,
        empty_label='— kein Mandant —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    serial = forms.CharField(
        label='Seriennummer',
        required=False,
        widget=forms.TextInput(attrs={'class': _FC, 'placeholder': 'Optional'}),
    )
    changelog_message = forms.CharField(
        label='Changelog-Nachricht',
        widget=forms.TextInput(attrs={
            'class': _FC,
            'placeholder': 'z.B. Neuen Switch in Berlin angelegt',
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from dcim.models import DeviceRole, DeviceType, Site
            from tenancy.models import Tenant
            self.fields['device_role'].queryset = DeviceRole.objects.all().order_by('name')
            self.fields['device_type'].queryset = DeviceType.objects.all().order_by('manufacturer__name', 'model')
            self.fields['site'].queryset = Site.objects.all().order_by('name')
            self.fields['tenant'].queryset = Tenant.objects.all().order_by('name')
        except Exception:
            pass

    def clean_name(self):
        value = (self.cleaned_data.get('name') or '').strip()
        if '_' in value:
            raise ValidationError(
                'Gerätename darf keine Unterstriche enthalten.'
            )
        if ' ' in value:
            raise ValidationError(
                'Gerätename darf keine Leerzeichen enthalten.'
            )
        return value


class WizardCircuitForm(forms.Form):
    cid = forms.CharField(
        label='Circuit-ID',
        widget=forms.TextInput(attrs={'class': _FC, 'placeholder': 'LEITUNG-2024-001'}),
    )
    provider = forms.ModelChoiceField(
        label='Provider',
        queryset=None,
        required=True,
        empty_label='— Provider auswählen —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    circuit_type = forms.ModelChoiceField(
        label='Circuit-Typ',
        queryset=None,
        required=True,
        empty_label='— Typ auswählen —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    status = forms.ChoiceField(
        label='Status',
        choices=STATUS_CIRCUIT,
        initial='active',
        widget=forms.Select(attrs={'class': _FS}),
    )
    site_termination_a = forms.ModelChoiceField(
        label='Standort (Seite A)',
        queryset=None,
        required=True,
        empty_label='— Standort auswählen —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    description = forms.CharField(
        label='Beschreibung',
        required=False,
        widget=forms.TextInput(attrs={'class': _FC}),
    )
    changelog_message = forms.CharField(
        label='Changelog-Nachricht',
        widget=forms.TextInput(attrs={
            'class': _FC,
            'placeholder': 'z.B. Neue Internetleitung Berlin angelegt',
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from circuits.models import Provider, CircuitType
            from dcim.models import Site
            self.fields['provider'].queryset = Provider.objects.all().order_by('name')
            self.fields['circuit_type'].queryset = CircuitType.objects.all().order_by('name')
            self.fields['site_termination_a'].queryset = Site.objects.all().order_by('name')
        except Exception:
            pass


class WizardVRFForm(forms.Form):
    name = forms.CharField(
        label='VRF Name',
        widget=forms.TextInput(attrs={'class': _FC, 'placeholder': 'VRF-Produktion'}),
    )
    rd = forms.CharField(
        label='Route Distinguisher',
        required=False,
        widget=forms.TextInput(attrs={'class': _FC, 'placeholder': '65000:100'}),
    )
    tenant = forms.ModelChoiceField(
        label='Tenant',
        queryset=None,
        required=False,
        empty_label='— no tenant —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    description = forms.CharField(
        label='Description',
        required=False,
        widget=forms.TextInput(attrs={'class': _FC}),
    )
    changelog_message = forms.CharField(
        label='Changelog Message',
        widget=forms.TextInput(attrs={'class': _FC, 'placeholder': 'e.g. Production VRF created'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from tenancy.models import Tenant
            self.fields['tenant'].queryset = Tenant.objects.all().order_by('name')
        except Exception:
            pass


class WizardIPRangeForm(forms.Form):
    start_address = forms.CharField(
        label='Start Address',
        widget=forms.TextInput(attrs={'class': _FC, 'placeholder': '10.0.0.1/24'}),
    )
    end_address = forms.CharField(
        label='End Address',
        widget=forms.TextInput(attrs={'class': _FC, 'placeholder': '10.0.0.254/24'}),
    )
    status = forms.ChoiceField(
        label='Status',
        choices=STATUS_IP,
        initial='active',
        widget=forms.Select(attrs={'class': _FS}),
    )
    role = forms.ModelChoiceField(
        label='Role',
        queryset=None,
        required=False,
        empty_label='— no role —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    tenant = forms.ModelChoiceField(
        label='Tenant',
        queryset=None,
        required=False,
        empty_label='— no tenant —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    description = forms.CharField(
        label='Description',
        required=False,
        widget=forms.TextInput(attrs={'class': _FC}),
    )
    changelog_message = forms.CharField(
        label='Changelog Message',
        widget=forms.TextInput(attrs={'class': _FC, 'placeholder': 'e.g. DHCP pool range created'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from ipam.models import Role
            from tenancy.models import Tenant
            self.fields['role'].queryset = Role.objects.all().order_by('name')
            self.fields['tenant'].queryset = Tenant.objects.all().order_by('name')
        except Exception:
            pass

    def clean_start_address(self):
        value = self.cleaned_data.get('start_address', '').strip()
        try:
            ipaddress.ip_interface(value)
        except ValueError:
            raise ValidationError('Invalid IP address / CIDR notation (e.g. 10.0.0.1/24).')
        if '/' not in value:
            raise ValidationError('Please include prefix length (e.g. 10.0.0.1/24).')
        return value

    def clean_end_address(self):
        value = self.cleaned_data.get('end_address', '').strip()
        try:
            ipaddress.ip_interface(value)
        except ValueError:
            raise ValidationError('Invalid IP address / CIDR notation (e.g. 10.0.0.254/24).')
        if '/' not in value:
            raise ValidationError('Please include prefix length (e.g. 10.0.0.254/24).')
        return value


STATUS_RACK = [
    ('active',           'Active'),
    ('planned',          'Planned'),
    ('staged',           'Staged'),
    ('failed',           'Failed'),
    ('decommissioning',  'Decommissioning'),
]

STATUS_VM = [
    ('active',           'Active'),
    ('offline',          'Offline'),
    ('planned',          'Planned'),
    ('staged',           'Staged'),
    ('failed',           'Failed'),
    ('decommissioning',  'Decommissioning'),
]

STATUS_LOCATION = [
    ('active',           'Active'),
    ('planned',          'Planned'),
    ('staged',           'Staged'),
    ('decommissioning',  'Decommissioning'),
]


class WizardRackForm(forms.Form):
    name = forms.CharField(
        label='Rack Name',
        widget=forms.TextInput(attrs={'class': _FC, 'placeholder': 'Rack-01'}),
    )
    site = forms.ModelChoiceField(
        label='Site',
        queryset=None,
        required=True,
        empty_label='— select site —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    location = forms.ModelChoiceField(
        label='Location',
        queryset=None,
        required=False,
        empty_label='— no location —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    status = forms.ChoiceField(
        label='Status',
        choices=STATUS_RACK,
        initial='active',
        widget=forms.Select(attrs={'class': _FS}),
    )
    u_height = forms.IntegerField(
        label='Height (U)',
        required=False,
        initial=42,
        min_value=1,
        max_value=100,
        widget=forms.NumberInput(attrs={'class': _FC}),
    )
    role = forms.ModelChoiceField(
        label='Role',
        queryset=None,
        required=False,
        empty_label='— no role —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    tenant = forms.ModelChoiceField(
        label='Tenant',
        queryset=None,
        required=False,
        empty_label='— no tenant —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    changelog_message = forms.CharField(
        label='Changelog Message',
        widget=forms.TextInput(attrs={'class': _FC, 'placeholder': 'e.g. New rack in server room A'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from dcim.models import Site, Location, RackRole
            from tenancy.models import Tenant
            self.fields['site'].queryset = Site.objects.all().order_by('name')
            self.fields['location'].queryset = Location.objects.all().order_by('site__name', 'name')
            self.fields['role'].queryset = RackRole.objects.all().order_by('name')
            self.fields['tenant'].queryset = Tenant.objects.all().order_by('name')
        except Exception:
            pass


class WizardVMForm(forms.Form):
    name = forms.CharField(
        label='VM Name',
        widget=forms.TextInput(attrs={'class': _FC, 'placeholder': 'vm-web-01'}),
    )
    status = forms.ChoiceField(
        label='Status',
        choices=STATUS_VM,
        initial='active',
        widget=forms.Select(attrs={'class': _FS}),
    )
    cluster = forms.ModelChoiceField(
        label='Cluster',
        queryset=None,
        required=True,
        empty_label='— select cluster —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    role = forms.ModelChoiceField(
        label='Role',
        queryset=None,
        required=False,
        empty_label='— no role —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    tenant = forms.ModelChoiceField(
        label='Tenant',
        queryset=None,
        required=False,
        empty_label='— no tenant —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    platform = forms.ModelChoiceField(
        label='Platform',
        queryset=None,
        required=False,
        empty_label='— no platform —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    changelog_message = forms.CharField(
        label='Changelog Message',
        widget=forms.TextInput(attrs={'class': _FC, 'placeholder': 'e.g. New web server VM created'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from virtualization.models import Cluster
            from dcim.models import DeviceRole, Platform
            from tenancy.models import Tenant
            self.fields['cluster'].queryset = Cluster.objects.all().order_by('name')
            self.fields['role'].queryset = DeviceRole.objects.all().order_by('name')
            self.fields['tenant'].queryset = Tenant.objects.all().order_by('name')
            self.fields['platform'].queryset = Platform.objects.all().order_by('name')
        except Exception:
            pass

    def clean_name(self):
        value = (self.cleaned_data.get('name') or '').strip()
        if '_' in value:
            raise ValidationError('VM name must not contain underscores.')
        if ' ' in value:
            raise ValidationError('VM name must not contain spaces.')
        return value


class WizardTenantForm(forms.Form):
    name = forms.CharField(
        label='Tenant Name',
        widget=forms.TextInput(attrs={'class': _FC, 'placeholder': 'ACME Corp'}),
    )
    group = forms.ModelChoiceField(
        label='Tenant Group',
        queryset=None,
        required=False,
        empty_label='— no group —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    description = forms.CharField(
        label='Description',
        required=False,
        widget=forms.TextInput(attrs={'class': _FC}),
    )
    changelog_message = forms.CharField(
        label='Changelog Message',
        widget=forms.TextInput(attrs={'class': _FC, 'placeholder': 'e.g. New customer tenant created'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from tenancy.models import TenantGroup
            self.fields['group'].queryset = TenantGroup.objects.all().order_by('name')
        except Exception:
            pass


class WizardLocationForm(forms.Form):
    name = forms.CharField(
        label='Location Name',
        widget=forms.TextInput(attrs={'class': _FC, 'placeholder': 'Server Room A'}),
    )
    site = forms.ModelChoiceField(
        label='Site',
        queryset=None,
        required=True,
        empty_label='— select site —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    status = forms.ChoiceField(
        label='Status',
        choices=STATUS_LOCATION,
        initial='active',
        widget=forms.Select(attrs={'class': _FS}),
    )
    parent = forms.ModelChoiceField(
        label='Parent Location',
        queryset=None,
        required=False,
        empty_label='— no parent —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    tenant = forms.ModelChoiceField(
        label='Tenant',
        queryset=None,
        required=False,
        empty_label='— no tenant —',
        widget=forms.Select(attrs={'class': _FS}),
    )
    description = forms.CharField(
        label='Description',
        required=False,
        widget=forms.TextInput(attrs={'class': _FC}),
    )
    changelog_message = forms.CharField(
        label='Changelog Message',
        widget=forms.TextInput(attrs={'class': _FC, 'placeholder': 'e.g. New server room location created'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from dcim.models import Site, Location
            from tenancy.models import Tenant
            self.fields['site'].queryset = Site.objects.all().order_by('name')
            self.fields['parent'].queryset = Location.objects.all().order_by('site__name', 'name')
            self.fields['tenant'].queryset = Tenant.objects.all().order_by('name')
        except Exception:
            pass


# =============================================================================
# WIZARD CONFIGURATION FORM
# =============================================================================

_FIELD_VISIBILITY_CHOICES = [
    ('optional', 'Optional'),
    ('required', 'Required'),
    ('hidden',   'Hidden'),
]

# Human-readable field names for the config UI
_FIELD_LABELS = {
    'dns_name':           'DNS Name',
    'description':        'Description',
    'tenant':             'Tenant',
    'role':               'Role',
    'site':               'Site',
    'vlan':               'VLAN',
    'region':             'Region',
    'group':              'Group / Site Group / Tenant Group',
    'serial':             'Serial Number',
    'rd':                 'Route Distinguisher',
    'u_height':           'Height (U)',
    'location':           'Location',
    'platform':           'Platform',
    'parent':             'Parent Location',
}


class WizardConfigForm(forms.ModelForm):
    """Form for editing a single WizardConfig entry."""

    class Meta:
        model = WizardConfig
        fields = ['enabled', 'custom_label', 'custom_description', 'sort_order']
        widgets = {
            'enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'custom_label': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Leer lassen für Standard-Label',
            }),
            'custom_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Leer lassen für Standard-Beschreibung',
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 9999,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically add one ChoiceField per configurable field for this wizard type
        if self.instance and self.instance.wizard_type:
            configurable = WIZARD_CONFIGURABLE_FIELDS.get(self.instance.wizard_type, [])
            current_config = self.instance.field_config or {}
            for field_name in configurable:
                self.fields[f'field_{field_name}'] = forms.ChoiceField(
                    label=_FIELD_LABELS.get(field_name, field_name),
                    choices=_FIELD_VISIBILITY_CHOICES,
                    initial=current_config.get(field_name, 'optional'),
                    widget=forms.Select(attrs={'class': 'form-select'}),
                    required=False,
                )

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Collect field_config from dynamic fields
        configurable = WIZARD_CONFIGURABLE_FIELDS.get(instance.wizard_type, [])
        field_config = {}
        for field_name in configurable:
            value = self.cleaned_data.get(f'field_{field_name}', 'optional')
            if value in ('required', 'optional', 'hidden'):
                field_config[field_name] = value
        instance.field_config = field_config
        if commit:
            instance.save()
        return instance


def localize_wizard_form(form):
    """
    Translates form field labels to the current plugin language.
    Keys follow the pattern wizard_field_<field_name> in ui_strings.py.
    Call this after apply_wizard_config() in each wizard view.
    """
    try:
        from .models import ForceSettings
        from .ui_strings import get_all_ui_strings
        s = ForceSettings.get_settings()
        lang = getattr(s, 'language', 'de') if s else 'de'
        ui = get_all_ui_strings(lang)
        for field_name in list(form.fields.keys()):
            key = f'wizard_field_{field_name}'
            translated = ui.get(key)
            if translated:
                form.fields[field_name].label = translated
    except Exception:
        pass


def apply_wizard_config(form, wizard_type):
    """
    Reads WizardConfig for wizard_type and adjusts form field required/hidden status.
    Call this after form instantiation in both GET and POST handlers.
    """
    try:
        config = WizardConfig.objects.filter(wizard_type=wizard_type).first()
        if not config or not config.field_config:
            return
        for field_name, setting in config.field_config.items():
            if field_name not in form.fields:
                continue
            if setting == 'required':
                form.fields[field_name].required = True
            elif setting == 'optional':
                form.fields[field_name].required = False
            elif setting == 'hidden':
                del form.fields[field_name]
    except Exception:
        pass


