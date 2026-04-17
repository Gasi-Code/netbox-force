"""
Dashboard widgets for the NetBox Force plugin.
Users can add these widgets to their NetBox home dashboard.
"""
from django.urls import reverse
from django.utils.html import format_html, mark_safe

from extras.dashboard.utils import register_widget
from extras.dashboard.widgets import DashboardWidget, WidgetConfigForm


@register_widget
class GuideWidget(DashboardWidget):
    default_title = 'Guide'
    description = 'Link zur NetBox Force Benutzer-Anleitung'
    width = 4
    height = 2

    class ConfigForm(WidgetConfigForm):
        pass

    def render(self, request):
        try:
            from .models import ForceSettings
            settings = ForceSettings.get_settings()
            enabled = settings.guide_enabled if settings else False
        except Exception:
            enabled = False

        try:
            url = reverse('plugins:netbox_force:guide')
        except Exception:
            url = '/plugins/netbox-force/guide/'

        if enabled:
            return format_html(
                '<div class="text-center py-3">'
                '<p class="mb-2"><i class="mdi mdi-book-open-variant" '
                'style="font-size: 2rem;"></i></p>'
                '<a href="{}" target="_blank" rel="noopener" '
                'class="btn btn-sm btn-primary">'
                '<i class="mdi mdi-arrow-right"></i> Anleitung</a>'
                '</div>',
                url
            )
        return mark_safe(
            '<div class="text-center py-3 text-muted">'
            '<p class="mb-2"><i class="mdi mdi-lock-outline" '
            'style="font-size: 2rem;"></i></p>'
            '<p class="small mb-0">Guide ist deaktiviert.</p>'
            '</div>'
        )


@register_widget
class ImportTemplatesWidget(DashboardWidget):
    default_title = 'Import-Vorlagen'
    description = 'CSV Import-Vorlagen herunterladen'
    width = 6
    height = 3

    class ConfigForm(WidgetConfigForm):
        pass

    def render(self, request):
        try:
            from .models import ForceSettings
            settings = ForceSettings.get_settings()
            enabled = settings.import_templates_enabled if settings else False
        except Exception:
            enabled = False

        try:
            list_url = reverse('plugins:netbox_force:import_template_list')
        except Exception:
            list_url = '/plugins/netbox-force/import-templates/'

        if not enabled:
            return mark_safe(
                '<div class="text-center py-3 text-muted">'
                '<p class="mb-2"><i class="mdi mdi-lock-outline" '
                'style="font-size: 2rem;"></i></p>'
                '<p class="small mb-0">Import-Vorlagen sind deaktiviert.</p>'
                '</div>'
            )

        try:
            from .models import ImportTemplate
            templates = list(ImportTemplate.objects.filter(enabled=True)[:10])
        except Exception:
            templates = []

        if not templates:
            return format_html(
                '<div class="text-center py-3 text-muted">'
                '<p class="mb-2"><i class="mdi mdi-file-document-outline" '
                'style="font-size: 2rem;"></i></p>'
                '<p class="small">Keine Vorlagen vorhanden.</p>'
                '<a href="{}" class="small">Alle Vorlagen &rarr;</a>'
                '</div>',
                list_url
            )

        rows = []
        for tpl in templates:
            try:
                dl_url = reverse('plugins:netbox_force:import_template_download',
                                 args=[tpl.pk])
            except Exception:
                dl_url = '#'
            rows.append(format_html(
                '<tr>'
                '<td>{}</td>'
                '<td><code class="small">{}</code></td>'
                '<td class="text-end">'
                '<a href="{}" class="btn btn-sm btn-outline-primary" '
                'title="Download"><i class="mdi mdi-download"></i></a>'
                '</td></tr>',
                tpl.display_name, tpl.model_label, dl_url
            ))

        table_rows = mark_safe(''.join(rows))
        return format_html(
            '<div class="table-responsive">'
            '<table class="table table-sm table-hover mb-0">'
            '<thead><tr><th>Vorlage</th><th>Model</th><th></th></tr></thead>'
            '<tbody>{}</tbody></table></div>'
            '<div class="text-center mt-2">'
            '<a href="{}" class="small text-muted">'
            'Alle Vorlagen &rarr;</a></div>',
            table_rows, list_url
        )
