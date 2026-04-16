from netbox.plugins import PluginMenu, PluginMenuItem

menu = PluginMenu(
    label='NetBox Force',
    groups=(
        ('', (
            PluginMenuItem(
                link='plugins:netbox_force:settings',
                link_text='Einstellungen',
            ),
        )),
    ),
    icon_class='mdi mdi-shield-lock',
)
