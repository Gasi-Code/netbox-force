"""
Dashboard widgets for the NetBox Force plugin.
Users can add these widgets to their NetBox home dashboard.
"""
from django.template.loader import render_to_string

from extras.dashboard.utils import register_widget
from extras.dashboard.widgets import DashboardWidget

from .models import ForceSettings, ImportTemplate


@register_widget
class GuideWidget(DashboardWidget):
    default_title = 'NetBox Force — Guide'
    description = 'Link to the NetBox Force user guide'
    width = 4
    height = 2

    def render(self, request):
        settings = ForceSettings.get_settings()
        enabled = settings.guide_enabled if settings else False
        return render_to_string('netbox_force/widgets/guide_widget.html', {
            'enabled': enabled,
        }, request=request)


@register_widget
class ImportTemplatesWidget(DashboardWidget):
    default_title = 'NetBox Force — Import Templates'
    description = 'Quick access to CSV import templates'
    width = 6
    height = 3

    def render(self, request):
        settings = ForceSettings.get_settings()
        enabled = settings.import_templates_enabled if settings else False
        templates = []
        if enabled:
            templates = list(ImportTemplate.objects.filter(enabled=True)[:10])
        return render_to_string('netbox_force/widgets/import_templates_widget.html', {
            'enabled': enabled,
            'templates': templates,
        }, request=request)
