from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_force', '0022_checkmk_timeout_default'),
    ]

    operations = [
        migrations.AddField(
            model_name='patchvm',
            name='checkmk_ip',
            field=models.CharField(
                max_length=64, blank=True, default='',
                verbose_name='IP address in CheckMK',
                help_text='Address CheckMK monitors this host on. Read-only mirror — '
                          'the NetBox IP link is the authoritative one.',
            ),
        ),
        migrations.AddField(
            model_name='patchvm',
            name='checkmk_host_state',
            field=models.SmallIntegerField(
                null=True, blank=True,
                verbose_name='CheckMK host state',
                help_text='0=UP, 1=DOWN, 2=UNREACHABLE',
            ),
        ),
        migrations.AddField(
            model_name='checkmksyncrun',
            name='ips_linked',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
