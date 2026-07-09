from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_force', '0011_patchmanagement'),
    ]

    operations = [
        migrations.AddField(
            model_name='forcesettings',
            name='patchmanagement_enabled',
            field=models.BooleanField(
                default=True,
                help_text='If enabled, the Patch Management tab and views are accessible.',
                verbose_name='Enable Patch Management',
            ),
        ),
        migrations.AddField(
            model_name='patchupdateentry',
            name='version_before',
            field=models.CharField(
                blank=True, default='', max_length=200, verbose_name='Version Before',
            ),
        ),
        migrations.AddField(
            model_name='patchupdateentry',
            name='version_after',
            field=models.CharField(
                blank=True, default='', max_length=200, verbose_name='Version After',
            ),
        ),
    ]
