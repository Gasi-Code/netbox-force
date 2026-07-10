from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_force', '0016_patchvm_verbose_name'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='patchvm',
            options={
                'verbose_name': 'Patchmanagement',
                'verbose_name_plural': 'Patchmanagement VMs',
                'ordering': ['fqdn'],
                'permissions': [
                    ('change_patch_status', 'Can change patch status and add update entries'),
                    ('bulk_edit_patchvm', 'Can bulk-edit patch VMs'),
                    ('import_patchvm', 'Can import patch VMs and sync contacts'),
                ],
            },
        ),
    ]
