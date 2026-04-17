import re

from django import forms
from django.core.exceptions import ValidationError

from .models import ForceSettings, ValidationRule, LANGUAGE_CHOICES

# Valid model label pattern: app_label.model_name
_MODEL_LABEL_RE = re.compile(r'^[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*$')


class ForceSettingsForm(forms.ModelForm):
    """Form for the plugin settings page."""

    class Meta:
        model = ForceSettings
        fields = [
            'language',
            'min_length',
            'enforce_on_create',
            'enforce_on_delete',
            'dry_run',
            'exempt_users',
            'blacklisted_phrases',
            'extra_exempt_models',
            'ticket_pattern',
            'ticket_pattern_hint',
            'change_window_enabled',
            'change_window_start',
            'change_window_end',
            'change_window_weekdays',
            'audit_log_enabled',
            'audit_log_retention_days',
            'dashboard_top_users_count',
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
            'model_label': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'dcim.device',
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
