import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Physical servers belong in Patch Management just as much as VMs, but the
    only link available was a OneToOne to virtualization.VirtualMachine. A
    bare-metal host could therefore only ever be a standalone record.
    """

    dependencies = [
        ('dcim', '0001_initial'),
        ('netbox_force', '0024_repair_modelpolicy'),
    ]

    operations = [
        migrations.AddField(
            model_name='patchvm',
            name='device',
            field=models.ForeignKey(
                blank=True,
                null=True,
                db_constraint=False,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='patch_entries',
                to='dcim.device',
                verbose_name='NetBox Device',
                help_text='Physical server this entry belongs to. Use instead of NetBox VM.',
            ),
        ),
    ]
