from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_force', '0008_wizard_config'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wizardconfig',
            name='wizard_type',
            field=models.CharField(
                choices=[
                    ('ip',       'IP Address'),
                    ('prefix',   'Prefix'),
                    ('vlan',     'VLAN'),
                    ('vrf',      'VRF'),
                    ('iprange',  'IP Range'),
                    ('site',     'Site'),
                    ('location', 'Location'),
                    ('rack',     'Rack'),
                    ('device',   'Device'),
                    ('vm',       'Virtual Machine'),
                    ('tenant',   'Tenant'),
                    ('circuit',  'Circuit'),
                ],
                max_length=20,
                unique=True,
                verbose_name='Wizard type',
            ),
        ),
    ]
