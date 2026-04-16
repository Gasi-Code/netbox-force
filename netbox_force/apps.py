from netbox.plugins import PluginConfig


class NetboxForceConfig(PluginConfig):
    name = 'netbox_force'
    verbose_name = 'NetBox Force'
    description = 'Enforces changelog messages, validation policies, and compliance rules on object changes'
    version = '3.0.0'
    author = 'Gasi-Code'
    base_url = 'netbox-force'
    min_version = '4.0.0'

    middleware = [
        'netbox_force.middleware.RequestContextMiddleware',
    ]

    default_settings = {
        'min_length': 2,
        'exempt_users': ['automation', 'monitoring', 'netbox'],
        'enforce_on_create': False,
        'enforce_on_delete': True,
        'extra_exempt_models': [],
    }

    def ready(self):
        from . import signals  # noqa: F401


config = NetboxForceConfig
