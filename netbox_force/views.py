import csv
import importlib
import json
import re
from datetime import timedelta

from django.apps import apps
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from .forms import ForceSettingsForm, ModelPolicyForm, ValidationRuleForm, ImportTemplateForm, GuidePageForm, WidgetImageUploadForm
from .models import ForceSettings, ModelPolicy, ValidationRule, Violation, ImportTemplate, GuidePage, WidgetImage
from .signals import check_naming_conventions, check_required_fields
from .ui_strings import get_all_ui_strings


# =============================================================================
# BASE MIXINS
# =============================================================================

class SuperuserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Requires the user to be logged in and a superuser."""

    def test_func(self):
        return self.request.user.is_superuser


class AuthenticatedRequiredMixin(LoginRequiredMixin):
    """Requires the user to be logged in (any authenticated user)."""
    pass


# =============================================================================
# CONTEXT HELPERS
# =============================================================================

def _get_ui_context(settings_obj=None):
    """Returns the UI strings dict based on the current language setting."""
    if settings_obj:
        language = getattr(settings_obj, 'language', 'de')
    else:
        s = ForceSettings.get_settings()
        language = getattr(s, 'language', 'de') if s else 'de'
    return get_all_ui_strings(language)


def _base_context(settings_obj=None):
    """
    Returns a base context dict used by ALL views.
    Ensures `force_settings` and `ui` are always available for tab rendering.
    """
    if settings_obj is None:
        settings_obj = ForceSettings.get_settings()
    return {
        'ui': _get_ui_context(settings_obj),
        'force_settings': settings_obj,
    }


def _feature_disabled_response(request, settings_obj=None):
    """Renders the 'feature disabled' page."""
    ctx = _base_context(settings_obj)
    ctx['active_tab'] = ''
    return render(request, 'netbox_force/feature_disabled.html', ctx)


# =============================================================================
# COMMON PATTERN SUGGESTIONS
# =============================================================================

NAMING_PATTERN_SUGGESTIONS = [
    {
        'pattern': '^[A-ZÄÖÜ]{2,3}-[A-ZÄÖÜ0-9-]+$',
        'label': 'Uppercase code (mit Umlauten) — DE-BERLIN, DE-MÜNCHEN',
        'example': 'DE-MÜNCHEN',
    },
    {
        'pattern': '^[A-Z]{2,3}-[A-Z0-9-]+$',
        'label': 'Uppercase code (ASCII only) — DE-BERLIN, US-NYC-01',
        'example': 'DE-BERLIN',
    },
    {
        'pattern': '^[a-zäöüß][a-zäöüß0-9-]*$',
        'label': 'Lowercase mit Umlauten — münchen-sw-01',
        'example': 'münchen-sw-01',
    },
    {
        'pattern': '^[a-z][a-z0-9-]*$',
        'label': 'Lowercase (ASCII only) — my-device-01',
        'example': 'my-device-01',
    },
    {
        'pattern': '^[A-ZÄÖÜa-zäöüß][A-Za-zÄÖÜäöüß0-9_ -]+$',
        'label': 'Freitext mit Umlauten — Büro Südstadt',
        'example': 'Büro Südstadt',
    },
    {
        'pattern': '^[A-Z][A-Za-z0-9_ -]+$',
        'label': 'Starts with uppercase (ASCII) — Main Office',
        'example': 'Main Office',
    },
    {
        'pattern': '^(prod|staging|dev|test)-.*$',
        'label': 'Environment prefix — prod-web-01',
        'example': 'prod-web-01',
    },
    {
        'pattern': '^[A-Z0-9]{2,}-[A-Z0-9]{2,}-[A-ZÄÖÜ0-9]+$',
        'label': 'Multi-segment code — DC01-RK01-U01',
        'example': 'DC01-RK01-U01',
    },
    {
        'pattern': '^[A-Za-zÄÖÜäöüß0-9._-]+$',
        'label': 'FQDN-safe + Umlaute — server01.example.com',
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
        'pattern': 'ACME-',
        'label': 'Custom prefix (simple) — ACME-1234',
        'example': 'ACME-1234',
    },
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


class CsvHeadersAPIView(SuperuserRequiredMixin, View):
    """
    Returns CSV header names for a given model (JSON).
    Used by the import template form to auto-generate CSV content.

    Strategy 1 — look up the model's NetBox ImportForm (in
    ``<app>.forms.bulk_import``) and use its ``Meta.fields``.
    Strategy 2 — derive importable fields from ``model._meta.fields``
    (concrete local fields only, filtered).
    """

    _EXCLUDED_TYPES = {'AutoField', 'BigAutoField', 'SmallAutoField'}
    _EXCLUDED_NAMES = {'id', 'custom_field_data', 'local_context_data'}

    # ------------------------------------------------------------------
    # Strategy 1: ImportForm lookup
    # ------------------------------------------------------------------
    @staticmethod
    def _get_import_form_fields(app_label, model):
        """Return the field list from the model's ImportForm, or *None*."""
        try:
            module = importlib.import_module(f'{app_label}.forms.bulk_import')
            for attr_name in dir(module):
                try:
                    cls = getattr(module, attr_name)
                except Exception:
                    continue
                if (isinstance(cls, type)
                        and hasattr(cls, 'Meta')
                        and getattr(cls.Meta, 'model', None) is model
                        and hasattr(cls.Meta, 'fields')):
                    fields = cls.Meta.fields
                    if fields and fields != '__all__':
                        return list(fields)
        except Exception:
            pass
        return None

    # ------------------------------------------------------------------
    # Strategy 2: model._meta.fields introspection (reliable fallback)
    # ------------------------------------------------------------------
    @classmethod
    def _get_generic_fields(cls, model):
        """Derive importable fields from concrete model fields."""
        headers = []
        # model._meta.fields returns only local concrete fields (no M2M,
        # no reverse relations) — much safer than get_fields().
        for field in model._meta.fields:
            # Skip auto-generated primary keys
            type_name = field.get_internal_type()
            if type_name in cls._EXCLUDED_TYPES:
                continue

            # Skip auto_now / auto_now_add timestamp fields
            if getattr(field, 'auto_now', False) or getattr(field, 'auto_now_add', False):
                continue

            # Skip well-known internal fields
            if field.name in cls._EXCLUDED_NAMES:
                continue

            # Skip non-editable fields
            if not getattr(field, 'editable', True):
                continue

            headers.append(field.name)
        return headers

    # ------------------------------------------------------------------
    def get(self, request, app_label, model_name):
        try:
            model = apps.get_model(app_label, model_name)
        except LookupError:
            return JsonResponse({'headers': [], 'error': 'Model not found'}, status=404)

        # Strategy 1: ImportForm fields (exact match to NetBox bulk-import)
        headers = self._get_import_form_fields(app_label, model)

        # Strategy 2: generic field introspection
        if not headers:
            headers = self._get_generic_fields(model)

        return JsonResponse({'headers': headers})


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
        ctx = _base_context(settings)
        ctx.update({
            'form': form,
            'settings': settings,
            'active_tab': 'settings',
            'ticket_suggestions': json.dumps(TICKET_PATTERN_SUGGESTIONS),
        })
        return render(request, 'netbox_force/settings.html', ctx)

    def post(self, request):
        settings = ForceSettings.get_settings()
        if settings is None:
            settings = ForceSettings(pk=1)
        form = ForceSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings saved successfully.')
            return redirect('plugins:netbox_force:settings')
        ctx = _base_context(settings)
        ctx.update({
            'form': form,
            'settings': settings,
            'active_tab': 'settings',
            'ticket_suggestions': json.dumps(TICKET_PATTERN_SUGGESTIONS),
        })
        return render(request, 'netbox_force/settings.html', ctx)


# =============================================================================
# VALIDATION RULE VIEWS
# =============================================================================

class ValidationRuleListView(SuperuserRequiredMixin, View):
    """Lists all validation rules."""

    def get(self, request):
        rules = ValidationRule.objects.all().order_by('model_label', 'field_name')
        ctx = _base_context()
        ctx.update({
            'rules': rules,
            'active_tab': 'rules',
        })
        return render(request, 'netbox_force/rules.html', ctx)


class ValidationRuleCreateView(SuperuserRequiredMixin, View):
    """Create a new validation rule."""

    def get(self, request):
        form = ValidationRuleForm()
        ctx = _base_context()
        ctx.update({
            'form': form,
            'editing': False,
            'active_tab': 'rules',
            'naming_suggestions': json.dumps(NAMING_PATTERN_SUGGESTIONS),
        })
        return render(request, 'netbox_force/rule_form.html', ctx)

    def post(self, request):
        form = ValidationRuleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Validation rule created successfully.')
            return redirect('plugins:netbox_force:rule_list')
        ctx = _base_context()
        ctx.update({
            'form': form,
            'editing': False,
            'active_tab': 'rules',
            'naming_suggestions': json.dumps(NAMING_PATTERN_SUGGESTIONS),
        })
        return render(request, 'netbox_force/rule_form.html', ctx)


class ValidationRuleEditView(SuperuserRequiredMixin, View):
    """Edit an existing validation rule."""

    def get(self, request, pk):
        rule = get_object_or_404(ValidationRule, pk=pk)
        form = ValidationRuleForm(instance=rule)
        ctx = _base_context()
        ctx.update({
            'form': form,
            'rule': rule,
            'editing': True,
            'active_tab': 'rules',
            'naming_suggestions': json.dumps(NAMING_PATTERN_SUGGESTIONS),
        })
        return render(request, 'netbox_force/rule_form.html', ctx)

    def post(self, request, pk):
        rule = get_object_or_404(ValidationRule, pk=pk)
        form = ValidationRuleForm(request.POST, instance=rule)
        if form.is_valid():
            form.save()
            messages.success(request, 'Validation rule updated successfully.')
            return redirect('plugins:netbox_force:rule_list')
        ctx = _base_context()
        ctx.update({
            'form': form,
            'rule': rule,
            'editing': True,
            'active_tab': 'rules',
            'naming_suggestions': json.dumps(NAMING_PATTERN_SUGGESTIONS),
        })
        return render(request, 'netbox_force/rule_form.html', ctx)


class ValidationRuleDeleteView(SuperuserRequiredMixin, View):
    """Delete a validation rule."""

    def get(self, request, pk):
        rule = get_object_or_404(ValidationRule, pk=pk)
        ctx = _base_context()
        ctx.update({
            'rule': rule,
            'active_tab': 'rules',
        })
        return render(request, 'netbox_force/rule_delete.html', ctx)

    def post(self, request, pk):
        rule = get_object_or_404(ValidationRule, pk=pk)
        rule.delete()
        messages.success(request, 'Validation rule deleted.')
        return redirect('plugins:netbox_force:rule_list')


class ValidationRuleToggleView(SuperuserRequiredMixin, View):
    """Toggle the enabled state of a validation rule (inline, no confirmation)."""

    def post(self, request, pk):
        rule = get_object_or_404(ValidationRule, pk=pk)
        rule.enabled = not rule.enabled
        rule.save()
        # Bust the 30-second rule cache immediately
        ValidationRule._rule_cache = None
        ValidationRule._rule_cache_timestamp = 0
        return redirect('plugins:netbox_force:rule_list')


# =============================================================================
# MODEL POLICY VIEWS
# =============================================================================

class ModelPolicyListView(SuperuserRequiredMixin, View):
    """Lists all per-model enforcement policies."""

    def get(self, request):
        policies = ModelPolicy.objects.all().order_by('model_label')
        ctx = _base_context()
        ctx.update({
            'policies': policies,
            'active_tab': 'policies',
        })
        return render(request, 'netbox_force/policy_list.html', ctx)


class ModelPolicyCreateView(SuperuserRequiredMixin, View):
    """Create a new model policy."""

    def get(self, request):
        form = ModelPolicyForm()
        ctx = _base_context()
        ctx.update({
            'form': form,
            'editing': False,
            'active_tab': 'policies',
        })
        return render(request, 'netbox_force/policy_form.html', ctx)

    def post(self, request):
        form = ModelPolicyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Model policy created successfully.')
            return redirect('plugins:netbox_force:policy_list')
        ctx = _base_context()
        ctx.update({
            'form': form,
            'editing': False,
            'active_tab': 'policies',
        })
        return render(request, 'netbox_force/policy_form.html', ctx)


class ModelPolicyEditView(SuperuserRequiredMixin, View):
    """Edit an existing model policy."""

    def get(self, request, pk):
        policy = get_object_or_404(ModelPolicy, pk=pk)
        form = ModelPolicyForm(instance=policy)
        ctx = _base_context()
        ctx.update({
            'form': form,
            'policy': policy,
            'editing': True,
            'active_tab': 'policies',
        })
        return render(request, 'netbox_force/policy_form.html', ctx)

    def post(self, request, pk):
        policy = get_object_or_404(ModelPolicy, pk=pk)
        form = ModelPolicyForm(request.POST, instance=policy)
        if form.is_valid():
            form.save()
            messages.success(request, 'Model policy updated successfully.')
            return redirect('plugins:netbox_force:policy_list')
        ctx = _base_context()
        ctx.update({
            'form': form,
            'policy': policy,
            'editing': True,
            'active_tab': 'policies',
        })
        return render(request, 'netbox_force/policy_form.html', ctx)


class ModelPolicyDeleteView(SuperuserRequiredMixin, View):
    """Delete a model policy."""

    def get(self, request, pk):
        policy = get_object_or_404(ModelPolicy, pk=pk)
        ctx = _base_context()
        ctx.update({
            'policy': policy,
            'active_tab': 'policies',
        })
        return render(request, 'netbox_force/policy_delete.html', ctx)

    def post(self, request, pk):
        policy = get_object_or_404(ModelPolicy, pk=pk)
        policy.delete()
        messages.success(request, 'Model policy deleted.')
        return redirect('plugins:netbox_force:policy_list')


class ModelPolicyToggleView(SuperuserRequiredMixin, View):
    """Toggle the enabled state of a model policy (inline, no confirmation)."""

    def post(self, request, pk):
        policy = get_object_or_404(ModelPolicy, pk=pk)
        policy.enabled = not policy.enabled
        policy.save()
        # Bust the 30-second policy cache immediately
        ModelPolicy._policy_cache = None
        ModelPolicy._policy_cache_timestamp = 0
        return redirect('plugins:netbox_force:policy_list')


# =============================================================================
# AUDIT SCAN VIEW
# =============================================================================

class AuditScanView(SuperuserRequiredMixin, View):
    """
    Retroactive compliance scan — checks existing DB objects against active
    ValidationRules. Read-only; no changes are made to the database.
    """

    SCAN_LIMIT = 500  # Max objects scanned per model

    def get(self, request):
        ctx = self._build_context(request, scan_results=None, scanned=False)
        return render(request, 'netbox_force/audit_scan.html', ctx)

    def post(self, request):
        scan_results = self._run_scan()
        ctx = self._build_context(request, scan_results=scan_results, scanned=True)
        return render(request, 'netbox_force/audit_scan.html', ctx)

    def _build_context(self, request, scan_results, scanned):
        # Determine which models have active rules
        rules_by_model = {}
        for rule in ValidationRule.get_active_rules():
            rules_by_model.setdefault(rule.model_label, []).append(rule)

        ctx = _base_context()
        ctx.update({
            'active_tab': 'audit_scan',
            'rules_by_model': rules_by_model,
            'scan_results': scan_results,
            'scanned': scanned,
            'scan_limit': self.SCAN_LIMIT,
        })
        return ctx

    def _run_scan(self):
        """
        Scans all models with active ValidationRules.
        Returns a list of result dicts, one per model.
        """
        results = []
        rules_by_model = {}
        for rule in ValidationRule.get_active_rules():
            rules_by_model.setdefault(rule.model_label, []).append(rule)

        if not rules_by_model:
            return results

        for model_label in sorted(rules_by_model.keys()):
            try:
                app_label, model_name = model_label.split('.', 1)
                ModelClass = apps.get_model(app_label, model_name)
                obj_list = list(ModelClass.objects.all()[:self.SCAN_LIMIT])
                total_scanned = len(obj_list)
                violations = []

                for obj in obj_list:
                    naming_err = check_naming_conventions(obj, model_label)
                    required_err = check_required_fields(obj, model_label)
                    if naming_err:
                        violations.append({
                            'obj': str(obj),
                            'pk': obj.pk,
                            'type': 'naming',
                            'type_label': 'Naming',
                            'message': naming_err,
                        })
                    if required_err:
                        violations.append({
                            'obj': str(obj),
                            'pk': obj.pk,
                            'type': 'required',
                            'type_label': 'Required Field',
                            'message': required_err,
                        })

                results.append({
                    'model_label': model_label,
                    'total_scanned': total_scanned,
                    'violations': violations,
                    'error': None,
                })
            except Exception as e:
                results.append({
                    'model_label': model_label,
                    'total_scanned': 0,
                    'violations': [],
                    'error': str(e),
                })

        return results


# =============================================================================
# VIOLATIONS VIEW
# =============================================================================

def _get_violation_queryset(request):
    """Builds the filtered violation queryset from request parameters."""
    qs = Violation.objects.all()

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

    return qs, reason, username, date_from, date_to


class ViolationListView(SuperuserRequiredMixin, View):
    """Lists violation audit log entries with filtering and pagination."""

    def get(self, request):
        settings = ForceSettings.get_settings()
        qs, reason, username, date_from, date_to = _get_violation_queryset(request)

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

        ctx = _base_context(settings)
        ctx.update({
            'violations': violations,
            'reason_choices': reason_choices,
            'filter_reason': reason,
            'filter_username': username,
            'filter_date_from': date_from,
            'filter_date_to': date_to,
            'audit_enabled': settings.audit_log_enabled if settings else False,
            'active_tab': 'violations',
        })
        return render(request, 'netbox_force/violations.html', ctx)


class ViolationExportCSVView(SuperuserRequiredMixin, View):
    """Exports filtered violations as CSV."""

    def get(self, request):
        qs, *_ = _get_violation_queryset(request)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="netbox_force_violations.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Timestamp', 'Username', 'Model', 'Object', 'Action',
            'Reason', 'Message', 'Attempted Comment',
        ])

        for v in qs.iterator():
            writer.writerow([
                v.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                v.username,
                v.model_label,
                v.object_repr,
                v.get_action_display(),
                v.get_reason_display(),
                v.message,
                v.attempted_comment,
            ])

        return response


# =============================================================================
# DASHBOARD VIEW
# =============================================================================

class DashboardView(SuperuserRequiredMixin, View):
    """Dashboard with violation statistics and feature status."""

    def get(self, request):
        settings = ForceSettings.get_settings()

        # Run retention cleanup on dashboard access
        try:
            Violation.cleanup_expired()
        except Exception:
            pass

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

        # Configurable top N users
        top_count = getattr(settings, 'dashboard_top_users_count', 10) if settings else 10

        violations_by_user = (
            Violation.objects
            .values('username')
            .annotate(count=Count('username'))
            .order_by('-count')[:top_count]
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

        # Build top-users label with count
        ctx = _base_context(settings)
        top_users_label = ctx['ui'].get('dashboard_top_users', 'Top {count} Users').format(count=top_count)

        ctx.update({
            'settings': settings,
            'total_violations': total_violations,
            'violations_by_reason': violations_by_reason,
            'violations_by_user': violations_by_user,
            'violations_over_time': violations_over_time,
            'max_daily_count': max_daily_count,
            'active_rules_count': active_rules_count,
            'top_users_label': top_users_label,
            'active_tab': 'dashboard',
        })
        return render(request, 'netbox_force/dashboard.html', ctx)


class DashboardResetView(SuperuserRequiredMixin, View):
    """Deletes all violation records (superuser only)."""

    def post(self, request):
        count, _ = Violation.objects.all().delete()
        messages.success(request, f'{count} violation(s) deleted.')
        return redirect('plugins:netbox_force:dashboard')


class DashboardExportView(SuperuserRequiredMixin, View):
    """Exports dashboard statistics and all violations as CSV."""

    def get(self, request):
        settings = ForceSettings.get_settings()
        top_count = getattr(settings, 'dashboard_top_users_count', 10) if settings else 10
        now = timezone.localtime(timezone.now())

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = (
            f'attachment; filename="netbox_force_report_{now:%Y%m%d_%H%M}.csv"'
        )

        writer = csv.writer(response)
        reason_display = dict(Violation.REASON_CHOICES)
        total = Violation.objects.count()

        # ── Header ──
        writer.writerow(['NetBox Force — Compliance Report'])
        writer.writerow(['Generated', now.strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow([])

        # ── Section 1: Summary ──
        writer.writerow(['SUMMARY'])
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Total Violations', total])

        # Date range of recorded violations
        if total > 0:
            first = Violation.objects.order_by('timestamp').first()
            last = Violation.objects.order_by('-timestamp').first()
            writer.writerow(['First Violation', first.timestamp.strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow(['Last Violation', last.timestamp.strftime('%Y-%m-%d %H:%M:%S')])

        writer.writerow([])

        # ── Section 2: Violations by Reason ──
        writer.writerow(['VIOLATIONS BY REASON'])
        writer.writerow(['Reason', 'Count', '% of Total'])
        by_reason = (
            Violation.objects
            .values('reason')
            .annotate(count=Count('reason'))
            .order_by('-count')
        )
        for item in by_reason:
            pct = f"{item['count'] / total * 100:.1f}%" if total else '0%'
            writer.writerow([
                reason_display.get(item['reason'], item['reason']),
                item['count'],
                pct,
            ])
        writer.writerow([])

        # ── Section 3: Violations by Model ──
        writer.writerow(['VIOLATIONS BY MODEL'])
        writer.writerow(['Model', 'Count', '% of Total'])
        by_model = (
            Violation.objects
            .values('model_label')
            .annotate(count=Count('model_label'))
            .order_by('-count')
        )
        for item in by_model:
            pct = f"{item['count'] / total * 100:.1f}%" if total else '0%'
            writer.writerow([item['model_label'], item['count'], pct])
        writer.writerow([])

        # ── Section 4: Violations by Action ──
        writer.writerow(['VIOLATIONS BY ACTION'])
        writer.writerow(['Action', 'Count'])
        action_display = dict(Violation.ACTION_CHOICES)
        by_action = (
            Violation.objects
            .values('action')
            .annotate(count=Count('action'))
            .order_by('-count')
        )
        for item in by_action:
            writer.writerow([
                action_display.get(item['action'], item['action']),
                item['count'],
            ])
        writer.writerow([])

        # ── Section 5: Top N Users ──
        writer.writerow([f'TOP {top_count} USERS'])
        writer.writerow(['#', 'Username', 'Count', '% of Total'])
        by_user = (
            Violation.objects
            .values('username')
            .annotate(count=Count('username'))
            .order_by('-count')[:top_count]
        )
        for rank, item in enumerate(by_user, 1):
            pct = f"{item['count'] / total * 100:.1f}%" if total else '0%'
            writer.writerow([rank, item['username'], item['count'], pct])
        writer.writerow([])

        # ── Section 6: 30-Day Trend ──
        writer.writerow(['30-DAY TREND'])
        writer.writerow(['Date', 'Count'])
        thirty_days_ago = timezone.now() - timedelta(days=30)
        over_time = (
            Violation.objects
            .filter(timestamp__gte=thirty_days_ago)
            .annotate(day=TruncDate('timestamp'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )
        for item in over_time:
            writer.writerow([item['day'].strftime('%Y-%m-%d'), item['count']])
        writer.writerow([])

        # ── Section 7: All Violation Records ──
        writer.writerow(['ALL VIOLATION RECORDS'])
        writer.writerow([
            'Timestamp', 'Username', 'Model', 'Object', 'Action',
            'Reason', 'Message', 'Attempted Comment',
        ])
        for v in Violation.objects.all().iterator():
            writer.writerow([
                v.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                v.username,
                v.model_label,
                v.object_repr,
                action_display.get(v.action, v.action),
                reason_display.get(v.reason, v.reason),
                v.message,
                v.attempted_comment,
            ])

        return response


# =============================================================================
# IMPORT TEMPLATE VIEWS
# =============================================================================

class ImportTemplateListView(AuthenticatedRequiredMixin, View):
    """Lists enabled import templates for all authenticated users."""

    def get(self, request):
        settings = ForceSettings.get_settings()
        if not settings or not settings.import_templates_enabled:
            return _feature_disabled_response(request, settings)

        templates = ImportTemplate.objects.filter(enabled=True)
        ctx = _base_context(settings)
        ctx.update({
            'templates': templates,
            'active_tab': 'import_templates',
        })
        return render(request, 'netbox_force/import_templates.html', ctx)


class ImportTemplateAdminListView(SuperuserRequiredMixin, View):
    """Admin list of all import templates (enabled and disabled)."""

    def get(self, request):
        settings = ForceSettings.get_settings()
        templates = ImportTemplate.objects.all()
        ctx = _base_context(settings)
        ctx.update({
            'templates': templates,
            'active_tab': 'import_templates',
        })
        return render(request, 'netbox_force/import_template_admin_list.html', ctx)


class ImportTemplateCreateView(SuperuserRequiredMixin, View):
    """Create a new import template."""

    def get(self, request):
        form = ImportTemplateForm()
        ctx = _base_context()
        ctx.update({
            'form': form,
            'editing': False,
            'active_tab': 'import_templates',
        })
        return render(request, 'netbox_force/import_template_form.html', ctx)

    def post(self, request):
        form = ImportTemplateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Import template created successfully.')
            return redirect('plugins:netbox_force:import_template_admin')
        ctx = _base_context()
        ctx.update({
            'form': form,
            'editing': False,
            'active_tab': 'import_templates',
        })
        return render(request, 'netbox_force/import_template_form.html', ctx)


class ImportTemplateEditView(SuperuserRequiredMixin, View):
    """Edit an existing import template."""

    def get(self, request, pk):
        template = get_object_or_404(ImportTemplate, pk=pk)
        form = ImportTemplateForm(instance=template)
        ctx = _base_context()
        ctx.update({
            'form': form,
            'template': template,
            'editing': True,
            'active_tab': 'import_templates',
        })
        return render(request, 'netbox_force/import_template_form.html', ctx)

    def post(self, request, pk):
        template = get_object_or_404(ImportTemplate, pk=pk)
        form = ImportTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, 'Import template updated successfully.')
            return redirect('plugins:netbox_force:import_template_admin')
        ctx = _base_context()
        ctx.update({
            'form': form,
            'template': template,
            'editing': True,
            'active_tab': 'import_templates',
        })
        return render(request, 'netbox_force/import_template_form.html', ctx)


class ImportTemplateDeleteView(SuperuserRequiredMixin, View):
    """Delete an import template."""

    def get(self, request, pk):
        template = get_object_or_404(ImportTemplate, pk=pk)
        ctx = _base_context()
        ctx.update({
            'template': template,
            'active_tab': 'import_templates',
        })
        return render(request, 'netbox_force/import_template_delete.html', ctx)

    def post(self, request, pk):
        template = get_object_or_404(ImportTemplate, pk=pk)
        template.delete()
        messages.success(request, 'Import template deleted.')
        return redirect('plugins:netbox_force:import_template_admin')


class ImportTemplateReorderView(SuperuserRequiredMixin, View):
    """AJAX endpoint: save drag-drop sort order for import templates.
    Expects POST body: {"order": [pk1, pk2, pk3, ...]}
    """

    def post(self, request):
        try:
            data = json.loads(request.body)
            order = data.get('order', [])
            for position, pk in enumerate(order):
                ImportTemplate.objects.filter(pk=int(pk)).update(sort_order=position)
            return JsonResponse({'status': 'ok'})
        except Exception as exc:
            return JsonResponse({'status': 'error', 'message': str(exc)}, status=400)


class ImportTemplateDownloadView(AuthenticatedRequiredMixin, View):
    """Downloads a single import template as CSV file."""

    def get(self, request, pk):
        settings = ForceSettings.get_settings()
        if not settings or not settings.import_templates_enabled:
            return _feature_disabled_response(request, settings)

        template = get_object_or_404(ImportTemplate, pk=pk, enabled=True)

        response = HttpResponse(content_type='text/csv; charset=utf-8')
        safe_name = template.display_name.replace(' ', '_').replace('/', '-')
        response['Content-Disposition'] = f'attachment; filename="{safe_name}.csv"'
        # UTF-8 BOM + sep=, hint so Excel opens with correct column separation
        # regardless of locale (German Excel defaults to semicolons otherwise)
        response.write('\ufeff' + 'sep=,\r\n' + template.csv_content)
        return response


# =============================================================================
# GUIDE VIEWS
# =============================================================================

_FULL_HTML_RE = re.compile(r'^\s*<!DOCTYPE|^\s*<html', re.IGNORECASE)


class GuideView(AuthenticatedRequiredMixin, View):
    """Displays the user guide page (read-only for all users)."""

    def get(self, request):
        settings = ForceSettings.get_settings()
        if not settings or not settings.guide_enabled:
            return _feature_disabled_response(request, settings)

        guide = GuidePage.get_guide()
        content = guide.content if guide else ''
        is_full_html = bool(_FULL_HTML_RE.search(content))

        ctx = _base_context(settings)
        ctx.update({
            'guide': guide,
            'guide_is_full_html': is_full_html,
            'active_tab': 'guide',
        })
        return render(request, 'netbox_force/guide.html', ctx)


class GuideStandaloneView(AuthenticatedRequiredMixin, View):
    """
    Serves the guide HTML content as a standalone page (no NetBox layout).
    Used by the dashboard widget to open the guide in a new browser tab.
    """

    def get(self, request):
        settings = ForceSettings.get_settings()
        if not settings or not settings.guide_enabled:
            return HttpResponse(
                '<html><body><p>Guide is disabled.</p></body></html>',
                content_type='text/html',
            )

        guide = GuidePage.get_guide()
        content = guide.content if guide else ''

        if not content.strip():
            return HttpResponse(
                '<html><body><p>No guide content.</p></body></html>',
                content_type='text/html',
            )

        # If full HTML page, serve as-is; otherwise wrap in minimal page
        if _FULL_HTML_RE.search(content):
            return HttpResponse(content, content_type='text/html')

        wrapped = (
            '<!DOCTYPE html><html><head>'
            '<meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<style>body{font-family:system-ui,sans-serif;max-width:960px;'
            'margin:40px auto;padding:0 20px;line-height:1.6;}</style>'
            '</head><body>' + content + '</body></html>'
        )
        return HttpResponse(wrapped, content_type='text/html')


class GuideEditView(SuperuserRequiredMixin, View):
    """WYSIWYG editor for the guide page (superuser only)."""

    def get(self, request):
        guide = GuidePage.get_guide()
        if guide is None:
            guide = GuidePage(pk=1)
        form = GuidePageForm(instance=guide)
        ctx = _base_context()
        ctx.update({
            'form': form,
            'guide': guide,
            'active_tab': 'guide',
        })
        return render(request, 'netbox_force/guide_edit.html', ctx)

    def post(self, request):
        guide = GuidePage.get_guide()
        if guide is None:
            guide = GuidePage(pk=1)
        form = GuidePageForm(request.POST, instance=guide)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.updated_by = request.user.username
            obj.save()
            messages.success(request, 'Guide updated successfully.')
            return redirect('plugins:netbox_force:guide')
        ctx = _base_context()
        ctx.update({
            'form': form,
            'guide': guide,
            'active_tab': 'guide',
        })
        return render(request, 'netbox_force/guide_edit.html', ctx)


# =============================================================================
# WIDGET IMAGES
# =============================================================================

def _get_widget_strings():
    """Load UI strings based on the plugin language."""
    try:
        from .ui_strings import get_all_ui_strings
        settings = ForceSettings.get_settings()
        language = getattr(settings, 'language', 'en') if settings else 'en'
        return get_all_ui_strings(language), settings
    except Exception:
        return {}, None


class WidgetImagesView(SuperuserRequiredMixin, View):
    """
    List and upload widget images (superuser only).
    GET  — show upload form + table of existing images
    POST — handle file upload
    """

    def _render(self, request, form, images=None):
        if images is None:
            images = WidgetImage.objects.all()
        ctx = _base_context()
        ctx.update({
            'active_tab': 'widget_images',
            'form': form,
            'images': images,
            # Absolute base URL so the template can display copy-ready URLs
            'base_url': request.build_absolute_uri('/').rstrip('/'),
        })
        return render(request, 'netbox_force/widget_images.html', ctx)

    def get(self, request):
        return self._render(request, WidgetImageUploadForm())

    def post(self, request):
        import mimetypes
        import re as _re
        import unicodedata

        form = WidgetImageUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            return self._render(request, form)

        uploaded = request.FILES['file']

        # Sanitize filename: normalize unicode, replace non-safe chars with '_'
        raw_name = uploaded.name
        raw_name = unicodedata.normalize('NFKD', raw_name)
        safe_name = _re.sub(r'[^\w.\-]', '_', raw_name)
        safe_name = safe_name.lstrip('.')  # No leading dots

        # Detect MIME type
        import mimetypes as _mimetypes
        content_type, _ = _mimetypes.guess_type(safe_name)
        if not content_type:
            content_type = 'application/octet-stream'

        # If a file with this name already exists, delete the old one first
        existing = WidgetImage.objects.filter(name=safe_name).first()
        if existing:
            existing.delete()

        img = WidgetImage(
            name=safe_name,
            file_size=uploaded.size,
            content_type=content_type,
            uploaded_by=request.user.username,
        )
        img.file.save(safe_name, uploaded, save=True)

        ui, _ = _get_widget_strings()
        msg = ui.get('widget_images_upload_success', 'Image "{name}" uploaded successfully.')
        messages.success(request, msg.replace('{name}', safe_name))
        return redirect('plugins:netbox_force:widget_image_list')


class WidgetImageDeleteView(SuperuserRequiredMixin, View):
    """Delete a widget image record + its file (superuser only, POST only)."""

    def post(self, request, pk):
        img = get_object_or_404(WidgetImage, pk=pk)
        name = img.name
        img.delete()
        ui, _ = _get_widget_strings()
        msg = ui.get('widget_images_delete_success', 'Image "{name}" deleted.')
        messages.success(request, msg.replace('{name}', name))
        return redirect('plugins:netbox_force:widget_image_list')


class WidgetImageServeView(AuthenticatedRequiredMixin, View):
    """
    Serve an uploaded widget image file.
    Only authenticated users can access (authentication via LoginRequiredMixin).
    """

    def get(self, request, filename):
        from django.http import Http404
        img = get_object_or_404(WidgetImage, name=filename)
        try:
            f = img.file.open('rb')
            response = FileResponse(
                f,
                content_type=img.content_type or 'application/octet-stream',
            )
            return response
        except (FileNotFoundError, OSError):
            raise Http404('Image file not found on disk.')
