from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_force', '0013_patch_contacts_and_ip_fk'),
    ]

    operations = [
        migrations.AddField(
            model_name='forcesettings',
            name='auto_add_vms_to_patch',
            field=models.BooleanField(
                default=False,
                verbose_name='Auto-add new VMs to Patch Management',
                help_text='When enabled, new NetBox VMs are automatically added to Patch Management on creation.',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='patch_overdue_days',
            field=models.PositiveIntegerField(
                default=0,
                verbose_name='Overdue threshold (days)',
                help_text='VMs not patched within this many days are marked overdue. Set 0 to disable.',
            ),
        ),
    ]
