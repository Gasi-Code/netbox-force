from netbox.plugins import PluginConfig, PluginMenuItem


# Module-level variable — NetBox's _load_resource imports this by dotted path
_menu_items = (
    PluginMenuItem(
        link='plugins:netbox_force:settings',
        link_text='Settings',
        permissions=['netbox_force.view_forcesettings'],
    ),
    PluginMenuItem(
        link='plugins:netbox_force:rule_list',
        link_text='Validation Rules',
        permissions=['netbox_force.view_validationrule'],
    ),
    PluginMenuItem(
        link='plugins:netbox_force:violation_list',
        link_text='Violations',
        permissions=['netbox_force.view_violation'],
    ),
    PluginMenuItem(
        link='plugins:netbox_force:dashboard',
        link_text='Dashboard',
        permissions=['netbox_force.view_forcesettings'],
    ),
    PluginMenuItem(
        link='plugins:netbox_force:import_template_list',
        link_text='Import Templates',
        permissions=[],
    ),
    PluginMenuItem(
        link='plugins:netbox_force:guide',
        link_text='Guide',
        permissions=[],
    ),
)


class NetboxForceConfig(PluginConfig):
    name = 'netbox_force'
    verbose_name = 'NetBox Force'
    description = 'Enforces changelog messages, validation policies, and compliance rules on object changes'
    version = '4.3.0'
    author = 'Gasi-Code'
    base_url = 'netbox-force'
    min_version = '4.0.0'

    middleware = [
        'netbox_force.middleware.RequestContextMiddleware',
    ]

    # String path: _load_resource constructs import_string("netbox_force.apps._menu_items")
    menu_items = '_menu_items'

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


config = NetboxForceConfig
