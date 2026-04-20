from netbox.plugins import PluginConfig, PluginMenu, PluginMenuItem


def _localize_menu():
    """
    Rebuilds navigation.menu with translated labels based on the DB language setting.
    Called once in ready(), before the first HTTP request.

    After changing the language in plugin settings the sidebar navigation labels
    update on the next NetBox restart. In-plugin tabs update immediately on every
    request without a restart.
    """
    try:
        from django.db import connection
        if 'netbox_force_forcesettings' not in connection.introspection.table_names():
            return  # Table not yet created (e.g. during first migration)
        from .models import ForceSettings
        from .ui_strings import get_all_ui_strings
        import netbox_force.navigation as nav

        settings = ForceSettings.get_settings()
        lang = getattr(settings, 'language', 'en') if settings else 'en'
        ui = get_all_ui_strings(lang)

        nav.menu = PluginMenu(
            label='NetBox Force',
            groups=(
                ('', (
                    PluginMenuItem(
                        link='plugins:netbox_force:settings',
                        link_text=ui.get('tab_settings', 'Settings'),
                        permissions=['netbox_force.view_forcesettings'],
                    ),
                    PluginMenuItem(
                        link='plugins:netbox_force:rule_list',
                        link_text=ui.get('tab_rules', 'Validation Rules'),
                        permissions=['netbox_force.view_validationrule'],
                    ),
                    PluginMenuItem(
                        link='plugins:netbox_force:violation_list',
                        link_text=ui.get('tab_violations', 'Violations'),
                        permissions=['netbox_force.view_violation'],
                    ),
                    PluginMenuItem(
                        link='plugins:netbox_force:dashboard',
                        link_text=ui.get('tab_dashboard', 'Dashboard'),
                        permissions=['netbox_force.view_forcesettings'],
                    ),
                    PluginMenuItem(
                        link='plugins:netbox_force:import_template_list',
                        link_text=ui.get('tab_import_templates', 'Import Templates'),
                        permissions=[],
                    ),
                    PluginMenuItem(
                        link='plugins:netbox_force:guide',
                        link_text=ui.get('tab_guide', 'Guide'),
                        permissions=[],
                    ),
                )),
            ),
            icon_class='mdi mdi-shield-check',
        )
    except Exception:
        pass  # Keep English defaults on any failure


class NetboxForceConfig(PluginConfig):
    name = 'netbox_force'
    verbose_name = 'NetBox Force'
    description = 'Enforces changelog messages, validation policies, and compliance rules on object changes'
    version = '4.5.0'
    author = 'Gasi-Code'
    base_url = 'netbox-force'
    min_version = '4.0.0'

    middleware = [
        'netbox_force.middleware.RequestContextMiddleware',
    ]

    # Standalone top-level nav section (like Slurp'it) instead of the shared
    # "Plugins" dropdown.  _localize_menu() rewrites navigation.menu at startup
    # with translated labels.
    menu = 'netbox_force.navigation.menu'

    default_settings = {
        'min_length': 2,
        'exempt_users': ['automation', 'monitoring', 'netbox'],
        'enforce_on_create': False,
        'enforce_on_delete': True,
        'extra_exempt_models': [],
    }

    def ready(self):
        super().ready()
        from . import signals  # noqa: F401
        from . import dashboards  # noqa: F401 — registers @register_widget
        _localize_menu()


config = NetboxForceConfig
