from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_force', '0007_wizards_enabled'),
    ]

    operations = [
        migrations.CreateModel(
            name='WizardConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wizard_type', models.CharField(
                    choices=[
                        ('ip',      'IP-Adresse anlegen'),
                        ('prefix',  'Prefix anlegen'),
                        ('vlan',    'VLAN anlegen'),
                        ('site',    'Standort anlegen'),
                        ('device',  'Gerät anlegen'),
                        ('circuit', 'Circuit anlegen'),
                    ],
                    max_length=20,
                    unique=True,
                    verbose_name='Wizard type',
                )),
                ('enabled', models.BooleanField(
                    default=True,
                    verbose_name='Enabled',
                    help_text='If disabled, this wizard is hidden from the landing page and widget.',
                )),
                ('custom_label', models.CharField(
                    blank=True,
                    default='',
                    max_length=100,
                    verbose_name='Custom label',
                    help_text='Leave empty to use the default label.',
                )),
                ('custom_description', models.TextField(
                    blank=True,
                    default='',
                    verbose_name='Custom description',
                    help_text='Leave empty to use the default description.',
                )),
                ('sort_order', models.PositiveIntegerField(
                    default=0,
                    verbose_name='Sort order',
                    help_text='Lower numbers appear first.',
                )),
                ('field_config', models.JSONField(
                    blank=True,
                    default=dict,
                    verbose_name='Field configuration',
                    help_text='Per-field visibility: "required", "optional", or "hidden".',
                )),
            ],
            options={
                'verbose_name': 'Wizard Configuration',
                'verbose_name_plural': 'Wizard Configurations',
                'ordering': ['sort_order', 'wizard_type'],
            },
        ),
    ]
