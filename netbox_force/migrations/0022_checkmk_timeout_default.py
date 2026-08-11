from django.db import migrations, models


def raise_short_timeouts(apps, schema_editor):
    """
    Ten seconds turned out to be too tight against a real CheckMK site — the
    service query alone can take eight. Installations still on the old default
    are moved up; anything deliberately configured higher is left alone.
    """
    ForceSettings = apps.get_model('netbox_force', 'ForceSettings')
    ForceSettings.objects.filter(checkmk_timeout__lte=10).update(checkmk_timeout=30)


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_force', '0021_checkmk_pull'),
    ]

    operations = [
        migrations.AlterField(
            model_name='forcesettings',
            name='checkmk_timeout',
            field=models.PositiveIntegerField(
                default=30,
                verbose_name='Timeout (seconds)',
                help_text='A CheckMK site with many services can take well over ten '
                          'seconds to answer the service query.',
            ),
        ),
        migrations.RunPython(raise_short_timeouts, migrations.RunPython.noop),
    ]
