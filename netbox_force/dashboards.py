"""
Dashboard widgets for the NetBox Force plugin.
Users can add these widgets to their NetBox home dashboard.
All visible text uses the plugin's language setting (DE/EN/ES).
"""
from django import forms
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


# =============================================================================
# Bookmarks Widget
# =============================================================================

def _parse_bookmark_lines(raw_text):
    """
    Parse the bookmarks textarea.
    Supported formats per line (leading/trailing spaces stripped):
      icon | Name | https://url      — icon is an MDI class name (e.g. mdi-github)
      Name | https://url             — uses default link icon
      https://url                    — URL only, uses the URL as label
    Lines starting with # are treated as comments and skipped.
    Returns a list of dicts: {icon, name, url}
    """
    items = []
    for raw_line in (raw_text or '').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 3:
            icon = parts[0] if parts[0] else 'mdi-link-variant'
            name = parts[1]
            url = parts[2]
        elif len(parts) == 2:
            icon = 'mdi-link-variant'
            name = parts[0]
            url = parts[1]
        elif len(parts) == 1:
            icon = 'mdi-link-variant'
            name = parts[0]
            url = parts[0]
        else:
            continue
        # Basic sanity: skip entries without a URL
        if not url:
            continue
        # Add https:// if url has no scheme
        if name and url and '://' not in url and not url.startswith('/'):
            url = 'https://' + url
        items.append({'icon': icon, 'name': name or url, 'url': url})
    return items


@register_widget
class BookmarksWidget(DashboardWidget):
    default_title = 'Bookmarks'
    description = 'Configurable quick-links / bookmarks with icons'
    width = 4
    height = 3

    class ConfigForm(WidgetConfigForm):
        links = forms.CharField(
            label='Links',
            widget=forms.Textarea(attrs={
                'rows': 10,
                'style': 'font-family: monospace; font-size: 13px;',
                'placeholder': (
                    'mdi-github | GitHub | https://github.com\n'
                    'mdi-book-open-variant | Wiki | https://wiki.example.com\n'
                    'mdi-ticket | Jira | https://jira.example.com\n'
                    '# Lines starting with # are comments\n'
                    'Name only | https://example.com'
                ),
            }),
            required=False,
            help_text=(
                'One link per line.  Format: <code>icon | Name | URL</code> '
                'or <code>Name | URL</code>.  '
                'Icons: any <a href="https://pictogrammers.com/library/mdi/" '
                'target="_blank">MDI icon</a> name, e.g. '
                '<code>mdi-github</code>, <code>mdi-server</code>.'
            ),
        )

    def render(self, request):
        ui, _ = _get_widget_strings()
        raw = self.config.get('links', '')
        items = _parse_bookmark_lines(raw)

        empty_msg = ui.get('widget_bookmarks_empty',
                           'No links configured. Click the ✎ button to add links.')

        if not items:
            return format_html(
                '<div class="text-center py-3 text-muted">'
                '<p class="mb-2"><i class="mdi mdi-bookmark-outline" '
                'style="font-size: 2rem;"></i></p>'
                '<p class="small mb-0">{}</p>'
                '</div>',
                empty_msg,
            )

        rows = []
        for item in items:
            icon_class = item['icon']
            # Normalise: strip leading 'mdi ' if user wrote 'mdi mdi-github'
            icon_class = icon_class.replace('mdi mdi-', 'mdi-').strip()
            # Always prefix with 'mdi ' for the final class
            full_icon = f'mdi {icon_class}' if not icon_class.startswith('mdi ') else icon_class
            rows.append(format_html(
                '<a href="{url}" target="_blank" rel="noopener noreferrer" '
                'class="list-group-item list-group-item-action d-flex align-items-center gap-2 py-2">'
                '<i class="{icon}" style="font-size:1.1rem; min-width:1.2rem;"></i>'
                '<span>{name}</span>'
                '</a>',
                url=item['url'],
                icon=full_icon,
                name=item['name'],
            ))

        return format_html(
            '<div class="list-group list-group-flush rounded">{}</div>',
            mark_safe(''.join(rows)),
        )
