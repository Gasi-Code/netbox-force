import json
from datetime import timedelta

from django.apps import apps
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from .forms import ForceSettingsForm, ValidationRuleForm
from .models import ForceSettings, ValidationRule, Violation
from .ui_strings import get_all_ui_strings


# =============================================================================
# BASE MIXIN
# =============================================================================

class SuperuserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Requires the user to be logged in and a superuser."""

    def test_func(self):
        return self.request.user.is_superuser


def _get_ui_context(settings_obj=None):
    """Returns the UI strings dict based on the current language setting."""
    if settings_obj:
        language = getattr(settings_obj, 'language', 'de')
    else:
        s = ForceSettings.get_settings()
        language = getattr(s, 'language', 'de') if s else 'de'
    return get_all_ui_strings(language)


# =============================================================================
# COMMON PATTERN SUGGESTIONS
# =============================================================================

NAMING_PATTERN_SUGGESTIONS = [
    {
        'pattern': '^[A-Z]{2,3}-[A-Z0-9-]+$',
        'label': 'Uppercase code — DE-BERLIN, US-NYC-01',
        'example': 'DE-BERLIN',
    },
    {
        'pattern': '^[a-z][a-z0-9-]*$',
        'label': 'Lowercase with hyphens — my-device-01',
        'example': 'my-device-01',
    },
    {
        'pattern': '^[A-Z][A-Za-z0-9_ -]+$',
        'label': 'Starts with uppercase — Main Office',
        'example': 'Main Office',
    },
    {
        'pattern': '^(prod|staging|dev|test)-.*$',
        'label': 'Environment prefix — prod-web-01',
        'example': 'prod-web-01',
    },
    {
        'pattern': '^[A-Z0-9]{2,}-[A-Z0-9]{2,}-[A-Z0-9]+$',
        'label': 'Multi-segment code — DC01-RK01-U01',
        'example': 'DC01-RK01-U01',
    },
    {
        'pattern': '^[A-Za-z0-9._-]+$',
        'label': 'FQDN-safe characters — server01.example.com',
        'example': 'server01.example.com',
    },
    {
        'pattern': '^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}/\\d{1,2}$',
        'label': 'CIDR notation — 10.0.0.0/24',
        'example': '10.0.0.0/24',
    },
]

TICKET_PATTERN_SUGGESTIONS = [
    {
        'pattern': 'JIRA-\\d+',
        'label': 'Jira — JIRA-1234',
        'example': 'JIRA-1234',
    },
    {
        'pattern': '[A-Z]+-\\d+',
        'label': 'Generic Jira-style — PROJ-123',
        'example': 'PROJ-123',
    },
    {
        'pattern': '#\\d+',
        'label': 'GitHub / GitLab — #123',
        'example': '#123',
    },
    {
        'pattern': 'INC\\d{7}',
        'label': 'ServiceNow Incident — INC0012345',
        'example': 'INC0012345',
    },
    {
        'pattern': 'CHG\\d{7}',
        'label': 'ServiceNow Change — CHG0012345',
        'example': 'CHG0012345',
    },
    {
        'pattern': 'RITM\\d{7}',
        'label': 'ServiceNow Request — RITM0012345',
        'example': 'RITM0012345',
    },
    {
        'pattern': 'REQ\\d+',
        'label': 'Generic Request — REQ12345',
        'example': 'REQ12345',
    },
    {
        'pattern': '(INC|CHG|REQ)\\d+',
        'label': 'ServiceNow (any) — INC/CHG/REQ + number',
        'example': 'INC0012345',
    },
]


# =============================================================================
# HELPER API VIEWS (JSON endpoints for dynamic dropdowns)
# =============================================================================

class ModelListAPIView(SuperuserRequiredMixin, View):
    """Returns a JSON list of all available Django/NetBox models."""

    def get(self, request):
        models = []
        for model in apps.get_models():
            label = f"{model._meta.app_label}.{model._meta.model_name}"
            verbose = str(model._meta.verbose_name).title()
            models.append({'label': label, 'verbose': verbose})
        models.sort(key=lambda m: m['label'])
        return JsonResponse({'models': models})


class FieldListAPIView(SuperuserRequiredMixin, View):
    """Returns a JSON list of fields for a given model."""

    def get(self, request, app_label, model_name):
        try:
            model = apps.get_model(app_label, model_name)
        except LookupError:
            return JsonResponse({'fields': []})

        fields = []
        for field in model._meta.get_fields():
            if hasattr(field, 'column'):
                field_type = field.get_internal_type()
                verbose = str(getattr(field, 'verbose_name', field.name)).title()
                fields.append({
                    'name': field.name,
                    'type': field_type,
                    'verbose': verbose,
                })
        fields.sort(key=lambda f: f['name'])
        return JsonResponse({'fields': fields})


# =============================================================================
# SETTINGS VIEW
# =============================================================================

class ForceSettingsView(SuperuserRequiredMixin, View):
    """Settings page for the NetBox Force plugin."""

    def get(self, request):
        settings = ForceSettings.get_settings()
        if settings is None:
            settings = ForceSettings(pk=1)
        form = ForceSettingsForm(instance=settings)
        return render(request, 'netbox_force/settings.html', {
            'form': form,
            'settings': settings,
            'ui': _get_ui_context(settings),
            'active_tab': 'settings',
            'ticket_suggestions': json.dumps(TICKET_PATTERN_SUGGESTIONS),
        })

    def post(self, request):
        settings = ForceSettings.get_settings()
        if settings is None:
            settings = ForceSettings(pk=1)
        form = ForceSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            saved = form.save()
            messages.success(request, 'Settings saved successfully.')
            return redirect('plugins:netbox_force:settings')
        return render(request, 'netbox_force/settings.html', {
            'form': form,
            'settings': settings,
            'ui': _get_ui_context(settings),
            'active_tab': 'settings',
            'ticket_suggestions': json.dumps(TICKET_PATTERN_SUGGESTIONS),
        })


# =============================================================================
# VALIDATION RULE VIEWS
# =============================================================================

class ValidationRuleListView(SuperuserRequiredMixin, View):
    """Lists all validation rules."""

    def get(self, request):
        rules = ValidationRule.objects.all().order_by('model_label', 'field_name')
        return render(request, 'netbox_force/rules.html', {
            'rules': rules,
            'ui': _get_ui_context(),
            'active_tab': 'rules',
        })


class ValidationRuleCreateView(SuperuserRequiredMixin, View):
    """Create a new validation rule."""

    def get(self, request):
        form = ValidationRuleForm()
        return render(request, 'netbox_force/rule_form.html', {
            'form': form,
            'editing': False,
            'ui': _get_ui_context(),
            'active_tab': 'rules',
            'naming_suggestions': json.dumps(NAMING_PATTERN_SUGGESTIONS),
        })

    def post(self, request):
        form = ValidationRuleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Validation rule created successfully.')
            return redirect('plugins:netbox_force:rule_list')
        return render(request, 'netbox_force/rule_form.html', {
            'form': form,
            'editing': False,
            'ui': _get_ui_context(),
            'active_tab': 'rules',
            'naming_suggestions': json.dumps(NAMING_PATTERN_SUGGESTIONS),
        })


class ValidationRuleEditView(SuperuserRequiredMixin, View):
    """Edit an existing validation rule."""

    def get(self, request, pk):
        rule = get_object_or_404(ValidationRule, pk=pk)
        form = ValidationRuleForm(instance=rule)
        return render(request, 'netbox_force/rule_form.html', {
            'form': form,
            'rule': rule,
            'editing': True,
            'ui': _get_ui_context(),
            'active_tab': 'rules',
            'naming_suggestions': json.dumps(NAMING_PATTERN_SUGGESTIONS),
        })

    def post(self, request, pk):
        rule = get_object_or_404(ValidationRule, pk=pk)
        form = ValidationRuleForm(request.POST, instance=rule)
        if form.is_valid():
            form.save()
            messages.success(request, 'Validation rule updated successfully.')
            return redirect('plugins:netbox_force:rule_list')
        return render(request, 'netbox_force/rule_form.html', {
            'form': form,
            'rule': rule,
            'editing': True,
            'ui': _get_ui_context(),
            'active_tab': 'rules',
            'naming_suggestions': json.dumps(NAMING_PATTERN_SUGGESTIONS),
        })


class ValidationRuleDeleteView(SuperuserRequiredMixin, View):
    """Delete a validation rule."""

    def get(self, request, pk):
        rule = get_object_or_404(ValidationRule, pk=pk)
        return render(request, 'netbox_force/rule_delete.html', {
            'rule': rule,
            'ui': _get_ui_context(),
            'active_tab': 'rules',
        })

    def post(self, request, pk):
        rule = get_object_or_404(ValidationRule, pk=pk)
        rule.delete()
        messages.success(request, 'Validation rule deleted.')
        return redirect('plugins:netbox_force:rule_list')


# =============================================================================
# VIOLATIONS VIEW
# =============================================================================

class ViolationListView(SuperuserRequiredMixin, View):
    """Lists violation audit log entries with filtering and pagination."""

    def get(self, request):
        settings = ForceSettings.get_settings()
        qs = Violation.objects.all()

        # Apply filters
        reason = request.GET.get('reason', '')
        username = request.GET.get('username', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')

        if reason:
            qs = qs.filter(reason=reason)
        if username:
            qs = qs.filter(username__icontains=username)
        if date_from:
            qs = qs.filter(timestamp__date__gte=date_from)
        if date_to:
            qs = qs.filter(timestamp__date__lte=date_to)

        # Pagination
        paginator = Paginator(qs, 50)
        page = request.GET.get('page', 1)
        try:
            violations = paginator.page(page)
        except PageNotAnInteger:
            violations = paginator.page(1)
        except EmptyPage:
            violations = paginator.page(paginator.num_pages)

        # Reason choices for filter dropdown
        reason_choices = Violation.REASON_CHOICES

        return render(request, 'netbox_force/violations.html', {
            'violations': violations,
            'reason_choices': reason_choices,
            'filter_reason': reason,
            'filter_username': username,
            'filter_date_from': date_from,
            'filter_date_to': date_to,
            'audit_enabled': settings.audit_log_enabled if settings else False,
            'ui': _get_ui_context(settings),
            'active_tab': 'violations',
        })


# =============================================================================
# DASHBOARD VIEW
# =============================================================================

class DashboardView(SuperuserRequiredMixin, View):
    """Dashboard with violation statistics and feature status."""

    def get(self, request):
        settings = ForceSettings.get_settings()

        # Violation statistics
        total_violations = Violation.objects.count()

        violations_by_reason = (
            Violation.objects
            .values('reason')
            .annotate(count=Count('reason'))
            .order_by('-count')
        )

        # Map reason codes to display names
        reason_display = dict(Violation.REASON_CHOICES)
        for item in violations_by_reason:
            item['display'] = reason_display.get(item['reason'], item['reason'])

        violations_by_user = (
            Violation.objects
            .values('username')
            .annotate(count=Count('username'))
            .order_by('-count')[:10]
        )

        # Last 30 days trend
        thirty_days_ago = timezone.now() - timedelta(days=30)
        violations_over_time = (
            Violation.objects
            .filter(timestamp__gte=thirty_days_ago)
            .annotate(day=TruncDate('timestamp'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )

        # Find max count for bar scaling
        max_daily_count = 0
        for item in violations_over_time:
            if item['count'] > max_daily_count:
                max_daily_count = item['count']

        # Feature status
        active_rules_count = ValidationRule.objects.filter(enabled=True).count()

        return render(request, 'netbox_force/dashboard.html', {
            'settings': settings,
            'total_violations': total_violations,
            'violations_by_reason': violations_by_reason,
            'violations_by_user': violations_by_user,
            'violations_over_time': violations_over_time,
            'max_daily_count': max_daily_count,
            'active_rules_count': active_rules_count,
            'ui': _get_ui_context(settings),
            'active_tab': 'dashboard',
        })
