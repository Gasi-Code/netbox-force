from netbox.plugins import PluginMenu, PluginMenuItem

# Initial values are English; _localize_menu() in apps.py overwrites this
# at startup based on the stored language setting.
# After changing the plugin language, a NetBox restart is required for
# the sidebar labels to update (in-plugin tabs update immediately).
menu = PluginMenu(
    label='NetBox Force',
    groups=(
        ('', (
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
        )),
    ),
    icon_class='mdi mdi-shield-check',
)
