from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ForceSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('language', models.CharField(
                    choices=[('de', 'Deutsch'), ('en', 'English'), ('es', 'Español')],
                    default='de', max_length=5, verbose_name='Sprache / Language',
                )),
                ('min_length', models.PositiveIntegerField(
                    default=2, verbose_name='Mindestlänge Changelog',
                )),
                ('enforce_on_create', models.BooleanField(
                    default=False, verbose_name='Beim Erstellen erzwingen',
                )),
                ('enforce_on_delete', models.BooleanField(
                    default=True, verbose_name='Beim Löschen erzwingen',
                )),
                ('exempt_users', models.TextField(
                    blank=True, default='',
                    help_text='Ein Benutzername pro Zeile',
                    verbose_name='Ausgenommene Benutzer',
                )),
                ('blacklisted_phrases', models.TextField(
                    blank=True, default='',
                    help_text='Ein Begriff pro Zeile. Changelog-Einträge die nur aus diesen Begriffen bestehen werden abgelehnt.',
                    verbose_name='Gesperrte Begriffe',
                )),
                ('extra_exempt_models', models.TextField(
                    blank=True, default='',
                    help_text='Ein Model pro Zeile (Format: app.model, z.B. myplugin.mymodel)',
                    verbose_name='Ausgenommene Modelle',
                )),
            ],
            options={
                'verbose_name': 'NetBox Force Einstellungen',
                'verbose_name_plural': 'NetBox Force Einstellungen',
            },
        ),
    ]
