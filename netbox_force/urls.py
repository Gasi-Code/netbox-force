from django.urls import path

from . import views

app_name = 'netbox_force'

urlpatterns = [
    path('settings/', views.ForceSettingsView.as_view(), name='settings'),
    path('rules/', views.ValidationRuleListView.as_view(), name='rule_list'),
    path('rules/add/', views.ValidationRuleCreateView.as_view(), name='rule_add'),
    path('rules/<int:pk>/edit/', views.ValidationRuleEditView.as_view(), name='rule_edit'),
    path('rules/<int:pk>/delete/', views.ValidationRuleDeleteView.as_view(), name='rule_delete'),
    path('rules/<int:pk>/toggle/', views.ValidationRuleToggleView.as_view(), name='rule_toggle'),

    # Model Policies
    path('policies/', views.ModelPolicyListView.as_view(), name='policy_list'),
    path('policies/add/', views.ModelPolicyCreateView.as_view(), name='policy_add'),
    path('policies/<int:pk>/edit/', views.ModelPolicyEditView.as_view(), name='policy_edit'),
    path('policies/<int:pk>/delete/', views.ModelPolicyDeleteView.as_view(), name='policy_delete'),
    path('policies/<int:pk>/toggle/', views.ModelPolicyToggleView.as_view(), name='policy_toggle'),

    # Audit Scan
    path('audit-scan/', views.AuditScanView.as_view(), name='audit_scan'),

    path('violations/', views.ViolationListView.as_view(), name='violation_list'),
    path('violations/export/', views.ViolationExportCSVView.as_view(), name='violation_export_csv'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard/reset/', views.DashboardResetView.as_view(), name='dashboard_reset'),
    path('dashboard/export/', views.DashboardExportView.as_view(), name='dashboard_export'),

    # Import Templates
    path('import-templates/', views.ImportTemplateListView.as_view(), name='import_template_list'),
    path('import-templates/admin/', views.ImportTemplateAdminListView.as_view(), name='import_template_admin'),
    path('import-templates/add/', views.ImportTemplateCreateView.as_view(), name='import_template_add'),
    path('import-templates/<int:pk>/edit/', views.ImportTemplateEditView.as_view(), name='import_template_edit'),
    path('import-templates/<int:pk>/delete/', views.ImportTemplateDeleteView.as_view(), name='import_template_delete'),
    path('import-templates/<int:pk>/download/', views.ImportTemplateDownloadView.as_view(), name='import_template_download'),

    # Guide
    path('guide/', views.GuideView.as_view(), name='guide'),
    path('guide/standalone/', views.GuideStandaloneView.as_view(), name='guide_standalone'),
    path('guide/edit/', views.GuideEditView.as_view(), name='guide_edit'),

    # JSON helper endpoints for dynamic dropdowns
    path('helpers/models/', views.ModelListAPIView.as_view(), name='api_models'),
    path('helpers/fields/<str:app_label>/<str:model_name>/',
         views.FieldListAPIView.as_view(), name='api_fields'),
    path('helpers/csv-headers/<str:app_label>/<str:model_name>/',
         views.CsvHeadersAPIView.as_view(), name='api_csv_headers'),
]
