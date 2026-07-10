from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_force', '0015_changelogging_fields'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='patchvm',
            options={
                'verbose_name': 'Patchmanagement',
                'verbose_name_plural': 'Patchmanagement VMs',
                'ordering': ['fqdn'],
            },
        ),
    ]
