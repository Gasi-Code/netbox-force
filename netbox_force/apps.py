from netbox.plugins import PluginConfig


class NetboxForceConfig(PluginConfig):
    name = 'netbox_force'
    verbose_name = 'NetBox Force'
    description = 'Erzwingt Changelog-Messages und weitere Policies bei Objekt-Änderungen'
    version = '2.1.0'
    author = 'hannIT AöR'
    base_url = 'netbox-force'
    min_version = '4.0.0'

    middleware = [
        'netbox_force.middleware.RequestContextMiddleware',
    ]

    default_settings = {
        'min_length': 10,
        'exempt_users': ['automation', 'monitoring', 'netbox'],
        'enforce_on_delete': True,
        'extra_exempt_models': [],
    }

    def ready(self):
        from . import signals  # noqa: F401 – registriert alle Signal Handler


config = NetboxForceConfig
