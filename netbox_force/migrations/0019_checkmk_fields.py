from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_force', '0018_patch_group_settings'),
    ]

    operations = [
        migrations.AddField(
            model_name='forcesettings',
            name='checkmk_webhook_secret',
            field=models.CharField(
                blank=True,
                default='',
                max_length=255,
                verbose_name='CheckMK webhook secret',
                help_text='Secret token for validating incoming CheckMK webhooks (Authorization: Bearer <secret>).',
            ),
        ),
        migrations.AddField(
            model_name='patchvm',
            name='last_checked',
            field=models.DateTimeField(
                null=True,
                blank=True,
                verbose_name='Last CheckMK check',
            ),
        ),
        migrations.AddField(
            model_name='patchvm',
            name='first_warned',
            field=models.DateTimeField(
                null=True,
                blank=True,
                verbose_name='First warned (CheckMK)',
            ),
        ),
        migrations.AddField(
            model_name='patchvm',
            name='update_details',
            field=models.TextField(
                blank=True,
                default='',
                verbose_name='Update details (CheckMK)',
            ),
        ),
    ]
