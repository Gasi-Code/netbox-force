"""
Dashboard widgets for the NetBox Force plugin.
Users can add these widgets to their NetBox home dashboard.
All visible text uses the plugin's language setting (DE/EN/ES).
"""
from django.urls import reverse
from django.utils.html import format_html, mark_safe

from extras.dashboard.utils import register_widget
from extras.dashboard.widgets import DashboardWidget, WidgetConfigForm


def _get_widget_strings():
    """Load UI strings based on the plugin's current language setting."""
    try:
        from .models import ForceSettings
        from .ui_strings import get_all_ui_strings
        settings = ForceSettings.get_settings()
        language = getattr(settings, 'language', 'de') if settings else 'de'
        return get_all_ui_strings(language), settings
    except Exception:
        return {}, None


@register_widget
class GuideWidget(DashboardWidget):
    default_title = 'Guide'
    description = 'Link zur NetBox Force Benutzer-Anleitung'
    width = 4
    height = 2

    class ConfigForm(WidgetConfigForm):
        pass

    def render(self, request):
        ui, settings = _get_widget_strings()
        enabled = settings.guide_enabled if settings else False

        try:
            url = reverse('plugins:netbox_force:guide_standalone')
        except Exception:
            url = '/plugins/netbox-force/guide/standalone/'

        btn_label = ui.get('widget_guide_btn', 'Guide')
        disabled_msg = ui.get('widget_guide_disabled', 'Guide ist deaktiviert.')

        if enabled:
            return format_html(
                '<div class="text-center py-3">'
                '<p class="mb-2"><i class="mdi mdi-book-open-variant" '
                'style="font-size: 2rem;"></i></p>'
                '<a href="{}" target="_blank" rel="noopener" '
                'class="btn btn-sm btn-primary">'
                '<i class="mdi mdi-arrow-right"></i> {}</a>'
                '</div>',
                url, btn_label
            )
        return format_html(
            '<div class="text-center py-3 text-muted">'
            '<p class="mb-2"><i class="mdi mdi-lock-outline" '
            'style="font-size: 2rem;"></i></p>'
            '<p class="small mb-0">{}</p>'
            '</div>',
            disabled_msg
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
        ui, settings = _get_widget_strings()
        enabled = settings.import_templates_enabled if settings else False

        try:
            list_url = reverse('plugins:netbox_force:import_template_list')
        except Exception:
            list_url = '/plugins/netbox-force/import-templates/'

        disabled_msg = ui.get('widget_templates_disabled',
                              'Import-Vorlagen sind deaktiviert.')
        col_name = ui.get('import_templates_col_name', 'Name')
        col_model = ui.get('import_templates_col_model', 'Model')
        col_desc = ui.get('import_templates_col_description', 'Description')
        empty_msg = ui.get('import_templates_empty',
                           'Keine Vorlagen vorhanden.')
        all_link = ui.get('widget_templates_all', 'Alle Vorlagen')

        if not enabled:
            return format_html(
                '<div class="text-center py-3 text-muted">'
                '<p class="mb-2"><i class="mdi mdi-lock-outline" '
                'style="font-size: 2rem;"></i></p>'
                '<p class="small mb-0">{}</p>'
                '</div>',
                disabled_msg
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
                '<p class="small">{}</p>'
                '<a href="{}" class="small">{} &rarr;</a>'
                '</div>',
                empty_msg, list_url, all_link
            )

        rows = []
        for tpl in templates:
            try:
                dl_url = reverse('plugins:netbox_force:import_template_download',
                                 args=[tpl.pk])
            except Exception:
                dl_url = '#'
            desc_cell = format_html(
                '<td class="small text-muted">{}</td>',
                tpl.description[:60] + '...' if len(tpl.description) > 60
                else tpl.description
            ) if tpl.description else '<td></td>'
            rows.append(format_html(
                '<tr>'
                '<td>{name}</td>'
                '<td><code class="small">{model}</code></td>'
                '{desc}'
                '<td class="text-end">'
                '<a href="{dl}" class="btn btn-sm btn-outline-primary" '
                'title="Download"><i class="mdi mdi-download"></i></a>'
                '</td></tr>',
                name=tpl.display_name,
                model=tpl.model_label,
                desc=mark_safe(desc_cell),
                dl=dl_url,
            ))

        table_rows = mark_safe(''.join(rows))
        return format_html(
            '<div class="table-responsive">'
            '<table class="table table-sm table-hover mb-0">'
            '<thead><tr>'
            '<th>{col_name}</th><th>{col_model}</th>'
            '<th>{col_desc}</th><th></th>'
            '</tr></thead>'
            '<tbody>{rows}</tbody></table></div>'
            '<div class="text-center mt-2">'
            '<a href="{url}" class="small text-muted">'
            '{all_link} &rarr;</a></div>',
            col_name=col_name,
            col_model=col_model,
            col_desc=col_desc,
            rows=table_rows,
            url=list_url,
            all_link=all_link,
        )
