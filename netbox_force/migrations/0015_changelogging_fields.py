from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_force', '0014_patch_settings'),
    ]

    operations = [
        migrations.AddField(
            model_name='patchvm',
            name='last_updated',
            field=models.DateTimeField(auto_now=True, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='patchupdateentry',
            name='last_updated',
            field=models.DateTimeField(auto_now=True, blank=True, null=True),
        ),
    ]
