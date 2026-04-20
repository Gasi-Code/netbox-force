from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_force', '0003_v44_features'),
    ]

    operations = [
        # New explicit toggle for ticket reference check
        migrations.AddField(
            model_name='forcesettings',
            name='ticket_enabled',
            field=models.BooleanField(
                default=True,
                verbose_name='Enable ticket reference check',
            ),
        ),
        # New explicit toggle for blocked phrases check
        migrations.AddField(
            model_name='forcesettings',
            name='blacklist_enabled',
            field=models.BooleanField(
                default=True,
                verbose_name='Enable blocked phrases check',
            ),
        ),
        # Expand language choices to 16 languages; max_length 5 → 10 (for 'zh-hans')
        migrations.AlterField(
            model_name='forcesettings',
            name='language',
            field=models.CharField(
                choices=[
                    ('cs', 'Čeština'),
                    ('da', 'Dansk'),
                    ('de', 'Deutsch'),
                    ('en', 'English'),
                    ('es', 'Español'),
                    ('fr', 'Français'),
                    ('it', 'Italiano'),
                    ('ja', '日本語'),
                    ('lv', 'Latviešu'),
                    ('nl', 'Nederlands'),
                    ('pl', 'Polski'),
                    ('pt', 'Português'),
                    ('ru', 'Русский'),
                    ('tr', 'Türkçe'),
                    ('uk', 'Українська'),
                    ('zh-hans', '中文'),
                ],
                default='de',
                max_length=10,
                verbose_name='Language',
            ),
        ),
    ]
