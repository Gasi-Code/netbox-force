from django.urls import path

from . import views

app_name = 'netbox_force'

urlpatterns = [
    path('settings/', views.ForceSettingsView.as_view(), name='settings'),
    path('rules/', views.ValidationRuleListView.as_view(), name='rule_list'),
    path('rules/add/', views.ValidationRuleCreateView.as_view(), name='rule_add'),
    path('rules/<int:pk>/edit/', views.ValidationRuleEditView.as_view(), name='rule_edit'),
    path('rules/<int:pk>/delete/', views.ValidationRuleDeleteView.as_view(), name='rule_delete'),
    path('violations/', views.ViolationListView.as_view(), name='violation_list'),
    path('violations/export/', views.ViolationExportCSVView.as_view(), name='violation_export_csv'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard/reset/', views.DashboardResetView.as_view(), name='dashboard_reset'),
    path('dashboard/export/', views.DashboardExportView.as_view(), name='dashboard_export'),

    # JSON helper endpoints for dynamic dropdowns
    path('helpers/models/', views.ModelListAPIView.as_view(), name='api_models'),
    path('helpers/fields/<str:app_label>/<str:model_name>/',
         views.FieldListAPIView.as_view(), name='api_fields'),
]
