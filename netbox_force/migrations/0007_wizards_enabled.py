from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_force', '0006_auto_changelog'),
    ]

    operations = [
        migrations.AddField(
            model_name='forcesettings',
            name='wizards_enabled',
            field=models.BooleanField(
                default=False,
                verbose_name='Enable wizards',
                help_text='Enable guided creation wizards for IP addresses, prefixes, VLANs, sites, devices, and circuits.',
            ),
        ),
    ]
