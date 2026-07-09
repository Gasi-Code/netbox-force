import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_force', '0012_patch_and_settings'),
    ]

    operations = [
        # PatchVM: drop old text fields
        migrations.RemoveField(model_name='patchvm', name='admins'),
        migrations.RemoveField(model_name='patchvm', name='verfahrensbetreuer'),
        # PatchVM: drop old ip CharField, add FK (db_constraint=False avoids ipam dependency)
        migrations.RemoveField(model_name='patchvm', name='ip_address'),
        migrations.AddField(
            model_name='patchvm',
            name='ip_address',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='patch_vms',
                to='ipam.ipaddress',
                verbose_name='IP Address',
                db_constraint=False,
            ),
        ),
        # New through model for contacts
        migrations.CreateModel(
            name='PatchVMContact',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contact_id', models.PositiveIntegerField(verbose_name='Contact')),
                ('role', models.CharField(
                    choices=[('admin', 'Administrator'), ('vb', 'Process Owner')],
                    max_length=5,
                    verbose_name='Role',
                )),
                ('patch_vm', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='vm_contacts',
                    to='netbox_force.patchvm',
                )),
            ],
            options={
                'verbose_name': 'VM Contact',
                'verbose_name_plural': 'VM Contacts',
                'ordering': ['role'],
                'unique_together': {('patch_vm', 'contact_id', 'role')},
            },
        ),
        # PatchUpdateEntry: drop CharField, add contact PK field
        migrations.RemoveField(model_name='patchupdateentry', name='updated_by'),
        migrations.AddField(
            model_name='patchupdateentry',
            name='updated_by_contact_id',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Updated By'),
        ),
    ]
