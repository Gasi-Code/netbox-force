from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_force', '0005_widget_images'),
    ]

    operations = [
        migrations.AddField(
            model_name='forcesettings',
            name='auto_changelog_enabled',
            field=models.BooleanField(
                default=False,
                verbose_name='Auto-generate changelog',
                help_text=(
                    'Automatically generate a changelog message from changed fields '
                    'when the user leaves the field empty. If the user provides a '
                    'message, it is always used as-is.'
                ),
            ),
        ),
    ]
