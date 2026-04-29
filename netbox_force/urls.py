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
    path('import-templates/reorder/', views.ImportTemplateReorderView.as_view(), name='import_template_reorder'),
    path('import-templates/add/', views.ImportTemplateCreateView.as_view(), name='import_template_add'),
    path('import-templates/<int:pk>/edit/', views.ImportTemplateEditView.as_view(), name='import_template_edit'),
    path('import-templates/<int:pk>/delete/', views.ImportTemplateDeleteView.as_view(), name='import_template_delete'),
    path('import-templates/<int:pk>/download/', views.ImportTemplateDownloadView.as_view(), name='import_template_download'),

    # Guide
    path('guide/', views.GuideView.as_view(), name='guide'),
    path('guide/standalone/', views.GuideStandaloneView.as_view(), name='guide_standalone'),
    path('guide/edit/', views.GuideEditView.as_view(), name='guide_edit'),

    # Widget Images — order matters: specific patterns before the catch-all serve
    path('widget/images/', views.WidgetImagesView.as_view(), name='widget_image_list'),
    path('widget/images/<int:pk>/delete/', views.WidgetImageDeleteView.as_view(), name='widget_image_delete'),
    path('widget/images/<str:filename>', views.WidgetImageServeView.as_view(), name='widget_image_serve'),

    # Wizards
    path('wizards/', views.WizardListView.as_view(), name='wizard_list'),
    path('wizards/ip/', views.WizardIPView.as_view(), name='wizard_ip'),
    path('wizards/prefix/', views.WizardPrefixView.as_view(), name='wizard_prefix'),
    path('wizards/vlan/', views.WizardVLANView.as_view(), name='wizard_vlan'),
    path('wizards/vrf/', views.WizardVRFView.as_view(), name='wizard_vrf'),
    path('wizards/iprange/', views.WizardIPRangeView.as_view(), name='wizard_iprange'),
    path('wizards/site/', views.WizardSiteView.as_view(), name='wizard_site'),
    path('wizards/location/', views.WizardLocationView.as_view(), name='wizard_location'),
    path('wizards/rack/', views.WizardRackView.as_view(), name='wizard_rack'),
    path('wizards/device/', views.WizardDeviceView.as_view(), name='wizard_device'),
    path('wizards/vm/', views.WizardVMView.as_view(), name='wizard_vm'),
    path('wizards/tenant/', views.WizardTenantView.as_view(), name='wizard_tenant'),
    path('wizards/circuit/', views.WizardCircuitView.as_view(), name='wizard_circuit'),

    # Wizard Config (superuser only)
    path('wizards/config/', views.WizardConfigListView.as_view(), name='wizard_config_list'),
    path('wizards/config/<str:wizard_type>/toggle/', views.WizardConfigToggleView.as_view(), name='wizard_config_toggle'),
    path('wizards/config/<str:wizard_type>/edit/', views.WizardConfigEditView.as_view(), name='wizard_config_edit'),

    # JSON helper endpoints for dynamic dropdowns
    path('helpers/models/', views.ModelListAPIView.as_view(), name='api_models'),
    path('helpers/fields/<str:app_label>/<str:model_name>/',
         views.FieldListAPIView.as_view(), name='api_fields'),
    path('helpers/csv-headers/<str:app_label>/<str:model_name>/',
         views.CsvHeadersAPIView.as_view(), name='api_csv_headers'),
]
