from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_force', '0017_patchvm_permissions'),
    ]

    operations = [
        migrations.AddField(
            model_name='forcesettings',
            name='patch_editor_groups',
            field=models.TextField(
                blank=True,
                default='',
                verbose_name='Patch editor groups',
                help_text='Comma-separated NetBox group names. Members can add, edit, delete VMs, set patch status, and bulk-edit.',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='patch_import_groups',
            field=models.TextField(
                blank=True,
                default='',
                verbose_name='Patch import/admin groups',
                help_text='Comma-separated NetBox group names. Members have all editor rights plus VM import and contact sync.',
            ),
        ),
    ]
