"""
Dashboard widgets for the NetBox Force plugin.
Users can add these widgets to their NetBox home dashboard.
All visible text uses the plugin's language setting (DE/EN/ES).
"""
from django import forms
from django.urls import reverse
from django.utils.html import escape, format_html, mark_safe

from extras.dashboard.utils import register_widget
from extras.dashboard.widgets import DashboardWidget, WidgetConfigForm


class _LocalizedAttr:
    """Descriptor that reads a ui_strings key at access time so class-level
    widget attributes (description, default_title) are served in the active
    plugin language without requiring an instance."""

    def __init__(self, key, default):
        self.key = key
        self.default = default

    def __get__(self, obj, objtype=None):
        try:
            from .models import ForceSettings
            from .ui_strings import get_all_ui_strings
            settings = ForceSettings.get_settings()
            lang = getattr(settings, 'language', 'en') if settings else 'en'
            return get_all_ui_strings(lang).get(self.key, self.default)
        except Exception:
            return self.default


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
        show_model = forms.BooleanField(
            label='Show model column',
            required=False,
            initial=True,
        )
        max_items = forms.IntegerField(
            label='Max templates',
            required=False,
            initial=10,
            min_value=1,
            max_value=50,
            widget=forms.NumberInput(attrs={'style': 'width:5rem;'}),
        )

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            try:
                ui, _ = _get_widget_strings()
                self.fields['show_model'].label = ui.get(
                    'import_templates_show_model', 'Show model column')
                self.fields['show_model'].help_text = ui.get(
                    'import_templates_show_model_help',
                    'Show or hide the model column in the table.')
                self.fields['max_items'].label = ui.get(
                    'import_templates_max_items', 'Max templates')
                self.fields['max_items'].help_text = ui.get(
                    'import_templates_max_items_help',
                    'Maximum number of templates shown in the widget (1–50).')
            except Exception:
                pass

    def render(self, request):
        ui, settings = _get_widget_strings()
        enabled = settings.import_templates_enabled if settings else False

        # show_model defaults True — backward-compatible with existing widgets
        show_model = self.config.get('show_model', True)

        # max_items defaults 10 — backward-compatible with existing widgets
        try:
            max_items = max(1, int(self.config.get('max_items') or 10))
        except (TypeError, ValueError):
            max_items = 10

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
        import_tooltip = ui.get('import_templates_import_tooltip',
                                'Open NetBox import page for this model')
        btn_import = ui.get('import_templates_btn_import', 'Import')

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
            templates = list(ImportTemplate.objects.filter(enabled=True)[:max_items])
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

            # Description cell
            desc_cell = format_html(
                '<td class="small text-muted">{}</td>',
                tpl.description[:60] + '...' if len(tpl.description) > 60
                else tpl.description
            ) if tpl.description else '<td></td>'

            # Model cell (optional)
            model_cell = (
                format_html('<td><code class="small">{}</code></td>', tpl.model_label)
                if show_model else mark_safe('')
            )

            # Import button (only when a valid URL can be derived)
            import_url = tpl.netbox_import_url
            import_btn = (
                format_html(
                    '<a href="{url}" class="btn btn-sm btn-outline-secondary" '
                    'title="{tooltip}"><i class="mdi mdi-upload"></i></a>',
                    url=import_url,
                    tooltip=import_tooltip,
                )
                if import_url else mark_safe('')
            )

            rows.append(format_html(
                '<tr>'
                '<td>{name}</td>'
                '{model}'
                '{desc}'
                '<td class="text-end" style="white-space:nowrap;">'
                '<a href="{dl}" class="btn btn-sm btn-outline-primary me-1" '
                'title="Download"><i class="mdi mdi-download"></i></a>'
                '{import_btn}'
                '</td></tr>',
                name=tpl.display_name,
                model=model_cell,
                desc=mark_safe(desc_cell),
                dl=dl_url,
                import_btn=import_btn,
            ))

        # Build header based on show_model
        model_th = format_html('<th>{}</th>', col_model) if show_model else mark_safe('')

        table_rows = mark_safe(''.join(rows))
        return format_html(
            '<div class="table-responsive">'
            '<table class="table table-sm table-hover mb-0">'
            '<thead><tr>'
            '<th>{col_name}</th>{model_th}'
            '<th>{col_desc}</th><th></th>'
            '</tr></thead>'
            '<tbody>{rows}</tbody></table></div>'
            '<div class="text-center mt-2">'
            '<a href="{url}" class="small text-muted">'
            '{all_link} &rarr;</a></div>',
            col_name=col_name,
            model_th=model_th,
            col_desc=col_desc,
            rows=table_rows,
            url=list_url,
            all_link=all_link,
        )


# =============================================================================
# Quick Links Widget
# =============================================================================

def _parse_quicklink_lines(raw_text):
    """
    Parse the quick-links textarea.
    Supported formats per line (leading/trailing spaces stripped):
      logo-url | Name | https://url   — first column is a direct image URL (favicon etc.)
      Name | https://url              — no logo; default link icon is shown
      https://url                     — URL only, URL used as label
    Lines starting with # are treated as comments and skipped.
    Returns a list of dicts: {logo_url, name, url}
    """
    items = []
    for raw_line in (raw_text or '').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 3:
            logo_url = parts[0] if parts[0] else None
            name = parts[1]
            url = parts[2]
        elif len(parts) == 2:
            logo_url = None
            name = parts[0]
            url = parts[1]
        else:
            logo_url = None
            name = parts[0]
            url = parts[0]
        # Skip entries without a URL
        if not url:
            continue
        # Add https:// if url has no scheme
        if url and '://' not in url and not url.startswith('/'):
            url = 'https://' + url
        items.append({'logo_url': logo_url, 'name': name or url, 'url': url})
    return items


@register_widget
class QuickLinksWidget(DashboardWidget):
    default_title = 'Quick Links'
    description = _LocalizedAttr(
        'widget_quicklinks_description',
        'Configurable quick-links with logos and optional notice',
    )
    width = 4
    height = 3

    class ConfigForm(WidgetConfigForm):
        notice = forms.CharField(
            label='Notice text',
            widget=forms.Textarea(attrs={
                'rows': 3,
                'style': 'font-size: 13px;',
                'placeholder': 'e.g.: Please enter all devices in NetBox.',
            }),
            required=False,
            help_text='Optional text shown above the links.',
        )
        links = forms.CharField(
            label='Links',
            widget=forms.Textarea(attrs={
                'rows': 10,
                'style': 'font-family: monospace; font-size: 13px;',
                'placeholder': (
                    'https://github.com/favicon.ico | GitHub | https://github.com\n'
                    'https://example.com/logo.png | Wiki | https://wiki.example.com\n'
                    '# Lines starting with # are comments\n'
                    'Name without logo | https://example.com'
                ),
            }),
            required=False,
            help_text=(
                'One link per line. '
                'Format: <code>logo-URL | Name | target-URL</code> or <code>Name | URL</code>. '
                'The first column must be a direct image URL (e.g. a favicon: '
                '<code>https://github.com/favicon.ico</code>).'
            ),
        )

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            try:
                ui, _ = _get_widget_strings()
                # Note: 'title' and 'color' are rendered by NetBox's own
                # dashboard template, NOT in this ConfigForm — they cannot
                # be translated from a plugin.
                notice_lbl = ui.get('widget_quicklinks_notice_label', 'Notice text')
                notice_hlp = ui.get('widget_quicklinks_notice_help',
                                    'Optional text shown above the links.')
                links_lbl = ui.get('widget_quicklinks_links_label', 'Links')
                links_hlp = ui.get('widget_quicklinks_links_help', '')
                if notice_lbl:
                    self.fields['notice'].label = notice_lbl
                if notice_hlp:
                    self.fields['notice'].help_text = notice_hlp
                if links_lbl:
                    self.fields['links'].label = links_lbl
                if links_hlp:
                    self.fields['links'].help_text = links_hlp
            except Exception:
                pass

    def render(self, request):
        ui, _ = _get_widget_strings()
        notice_text = self.config.get('notice', '').strip()
        raw = self.config.get('links', '')
        items = _parse_quicklink_lines(raw)

        empty_msg = ui.get('widget_quicklinks_empty',
                           'No links configured. Click the ✎ button to add links.')

        # Build notice block
        notice_html = mark_safe('')
        if notice_text:
            lines_html = '<br>'.join(str(escape(ln)) for ln in notice_text.splitlines())
            notice_html = mark_safe(
                '<div class="px-3 py-2 small" '
                'style="border-left:3px solid #6ea8fe;margin:0 0 6px 0;'
                'border-radius:0 4px 4px 0;">'
                + lines_html + '</div>'
            )

        if not items:
            if notice_text:
                return format_html(
                    '{0}'
                    '<div class="text-center py-2 text-muted">'
                    '<p class="small mb-0">{1}</p>'
                    '</div>',
                    notice_html, empty_msg,
                )
            return format_html(
                '<div class="text-center py-3 text-muted">'
                '<p class="mb-2"><i class="mdi mdi-link-variant" '
                'style="font-size: 2rem;"></i></p>'
                '<p class="small mb-0">{}</p>'
                '</div>',
                empty_msg,
            )

        rows = []
        for item in items:
            if item['logo_url']:
                icon_html = format_html(
                    '<img src="{}" alt="" width="18" height="18" '
                    'style="object-fit:contain;border-radius:2px;flex-shrink:0;">',
                    item['logo_url'],
                )
            else:
                icon_html = mark_safe(
                    '<i class="mdi mdi-link-variant" '
                    'style="font-size:1.1rem;min-width:1.2rem;flex-shrink:0;"></i>'
                )
            rows.append(format_html(
                '<a href="{url}" target="_blank" rel="noopener noreferrer" '
                'class="list-group-item list-group-item-action '
                'd-flex align-items-center gap-2 py-2">'
                '{icon}<span>{name}</span></a>',
                url=item['url'],
                icon=icon_html,
                name=item['name'],
            ))

        return format_html(
            '{notice}<div class="list-group list-group-flush rounded">{links}</div>',
            notice=notice_html,
            links=mark_safe(''.join(str(r) for r in rows)),
        )


# =============================================================================
# Wizards Widget
# =============================================================================

@register_widget
class WizardWidget(DashboardWidget):
    default_title = 'Wizards'
    description = 'Schnellzugriff auf die Netzwerk-Wizards'
    width = 6
    height = 4

    class ConfigForm(WidgetConfigForm):
        num_columns = forms.ChoiceField(
            label='Columns',
            choices=[('2', '2 columns'), ('3', '3 columns')],
            initial='3',
            widget=forms.Select(attrs={'style': 'width:8rem;'}),
        )
        show_descriptions = forms.BooleanField(
            label='Show descriptions',
            required=False,
            initial=True,
        )

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            try:
                ui, _ = _get_widget_strings()
                self.fields['num_columns'].label = ui.get(
                    'widget_wizards_columns_label', 'Columns')
                self.fields['show_descriptions'].label = ui.get(
                    'widget_wizards_show_desc_label', 'Show descriptions')
            except Exception:
                pass

    def render(self, request):
        ui, settings = _get_widget_strings()
        wizards_enabled = getattr(settings, 'wizards_enabled', False) if settings else False

        disabled_msg = ui.get('widget_wizards_disabled', 'Wizards sind deaktiviert.')
        empty_msg = ui.get('widget_wizards_empty', 'Keine Wizards konfiguriert.')

        if not wizards_enabled:
            return format_html(
                '<div class="text-center py-3 text-muted">'
                '<p class="mb-2"><i class="mdi mdi-lock-outline" '
                'style="font-size: 2rem;"></i></p>'
                '<p class="small mb-0">{}</p>'
                '</div>',
                disabled_msg,
            )

        try:
            from .models import WizardConfig
            configs = WizardConfig.get_enabled()
        except Exception:
            configs = []

        if not configs:
            return format_html(
                '<div class="text-center py-3 text-muted">'
                '<p class="mb-2"><i class="mdi mdi-auto-fix" '
                'style="font-size: 2rem;"></i></p>'
                '<p class="small mb-0">{}</p>'
                '</div>',
                empty_msg,
            )

        try:
            num_cols = int(self.config.get('num_columns') or 3)
            if num_cols not in (2, 3):
                num_cols = 3
        except (TypeError, ValueError):
            num_cols = 3

        show_descriptions = self.config.get('show_descriptions', True)
        col_class = 'col-6' if num_cols == 2 else 'col-4'

        cards = []
        for cfg in configs:
            try:
                url = reverse(f'plugins:netbox_force:{cfg.url_name}')
            except Exception:
                url = '#'

            desc_html = mark_safe('')
            if show_descriptions and cfg.description:
                desc = cfg.description[:80] + '…' if len(cfg.description) > 80 else cfg.description
                desc_html = format_html(
                    '<p class="small text-muted mb-2" style="line-height:1.3;">{}</p>',
                    desc,
                )

            cards.append(format_html(
                '<div class="{col_class} mb-3">'
                '<div class="card h-100 border-0 shadow-sm">'
                '<div class="card-body d-flex flex-column p-3">'
                '<div class="mb-2">'
                '<span class="fs-3 text-{color}">'
                '<i class="mdi {icon}"></i></span>'
                '</div>'
                '<h6 class="card-title mb-1" style="font-size:.85rem;line-height:1.2;">'
                '{label}</h6>'
                '{desc}'
                '<a href="{url}" class="btn btn-sm btn-{color} mt-auto">'
                '<i class="mdi mdi-arrow-right-circle"></i> Starten</a>'
                '</div></div></div>',
                col_class=col_class,
                color=cfg.color,
                icon=cfg.icon,
                label=cfg.label,
                desc=desc_html,
                url=url,
            ))

        rows_html = mark_safe(''.join(str(c) for c in cards))
        return format_html(
            '<div class="row g-2">{}</div>',
            rows_html,
        )


# Backwards-compatibility shim.
#
# NOT decorated with @register_widget — that would add a second "Quick Links"
# entry to the Add-widget picker.  NetBox loads widget classes for existing
# dashboard configs via import_string('netbox_force.dashboards.BookmarksWidget'),
# which finds this class by name in the module without it being in the registry.
# The proper __name__ ('BookmarksWidget', not 'QuickLinksWidget') is what makes
# the import_string lookup work correctly.
class BookmarksWidget(QuickLinksWidget):
    """Not registered — only here so import_string can resolve existing
    per-user dashboard configs saved under the old class name."""
    pass
