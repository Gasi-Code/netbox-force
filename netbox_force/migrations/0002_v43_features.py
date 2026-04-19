from django.db import migrations, models


class Migration(migrations.Migration):
    """
    v4.3.0: Global enforcement toggle (master switch).
    """

    dependencies = [
        ('netbox_force', '0001_initial'),
    ]

    operations = [
        # --- ForceSettings: Global enforcement toggle ---
        migrations.AddField(
            model_name='forcesettings',
            name='enforcement_enabled',
            field=models.BooleanField(
                default=True,
                verbose_name='Enforcement enabled',
                help_text='Disable to pause all enforcement globally (e.g. during maintenance windows).',
            ),
        ),
    ]
