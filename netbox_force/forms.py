import re

from django import forms
from django.apps import apps
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

from .models import ForceSettings, ModelPolicy, ValidationRule, ImportTemplate, GuidePage, LANGUAGE_CHOICES

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
                'placeholder': r'JIRA-\d+ or #\d+',
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


