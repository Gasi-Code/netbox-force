import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_force', '0001_initial'),
    ]

    operations = [
        # --- Update ForceSettings verbose names (German → English) ---
        migrations.AlterModelOptions(
            name='forcesettings',
            options={
                'verbose_name': 'NetBox Force Settings',
                'verbose_name_plural': 'NetBox Force Settings',
            },
        ),

        # --- Add new fields to ForceSettings ---
        migrations.AddField(
            model_name='forcesettings',
            name='ticket_pattern',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Regex pattern for required ticket references (e.g. JIRA-\\d+ or #\\d+). Leave empty to disable.',
                max_length=255,
                verbose_name='Ticket pattern',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='change_window_enabled',
            field=models.BooleanField(
                default=False,
                verbose_name='Enable change window',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='change_window_start',
            field=models.TimeField(
                blank=True,
                default=None,
                null=True,
                verbose_name='Window start time',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='change_window_end',
            field=models.TimeField(
                blank=True,
                default=None,
                null=True,
                verbose_name='Window end time',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='change_window_weekdays',
            field=models.CharField(
                blank=True,
                default='1,2,3,4,5',
                help_text='Comma-separated ISO weekday numbers (1=Monday, 7=Sunday)',
                max_length=20,
                verbose_name='Allowed weekdays',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='audit_log_enabled',
            field=models.BooleanField(
                default=False,
                verbose_name='Enable audit log',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='audit_log_retention_days',
            field=models.PositiveIntegerField(
                default=90,
                verbose_name='Audit log retention (days)',
            ),
        ),

        # --- Create ValidationRule model ---
        migrations.CreateModel(
            name='ValidationRule',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID',
                )),
                ('rule_type', models.CharField(
                    choices=[('naming', 'Naming Convention'), ('required', 'Required Field')],
                    max_length=20,
                    verbose_name='Rule type',
                )),
                ('model_label', models.CharField(
                    help_text='Format: app.model (e.g. dcim.device)',
                    max_length=100,
                    verbose_name='Model',
                )),
                ('field_name', models.CharField(
                    help_text='The model field to validate (e.g. name, description, tenant)',
                    max_length=100,
                    verbose_name='Field name',
                )),
                ('regex_pattern', models.CharField(
                    blank=True,
                    default='',
                    help_text='Only for naming rules. The value must match this pattern.',
                    max_length=500,
                    verbose_name='Regex pattern',
                )),
                ('error_message', models.CharField(
                    blank=True,
                    default='',
                    help_text='Shown to the user when validation fails. Leave empty for default.',
                    max_length=500,
                    verbose_name='Custom error message',
                )),
                ('enabled', models.BooleanField(
                    default=True,
                    verbose_name='Enabled',
                )),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Validation Rule',
                'verbose_name_plural': 'Validation Rules',
                'ordering': ['model_label', 'field_name'],
                'unique_together': {('rule_type', 'model_label', 'field_name')},
            },
        ),

        # --- Create Violation model ---
        migrations.CreateModel(
            name='Violation',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID',
                )),
                ('timestamp', models.DateTimeField(
                    auto_now_add=True,
                    db_index=True,
                )),
                ('username', models.CharField(
                    db_index=True,
                    max_length=150,
                )),
                ('model_label', models.CharField(max_length=100)),
                ('object_repr', models.CharField(
                    blank=True,
                    default='',
                    max_length=200,
                )),
                ('action', models.CharField(
                    choices=[('create', 'Create'), ('edit', 'Edit'), ('delete', 'Delete')],
                    max_length=20,
                )),
                ('reason', models.CharField(
                    choices=[
                        ('missing_changelog', 'Missing Changelog'),
                        ('too_short', 'Changelog Too Short'),
                        ('blacklisted', 'Blacklisted Phrase'),
                        ('ticket_missing', 'Missing Ticket Reference'),
                        ('naming_violation', 'Naming Convention Violation'),
                        ('required_field', 'Required Field Missing'),
                        ('change_window', 'Outside Change Window'),
                    ],
                    db_index=True,
                    max_length=30,
                )),
                ('message', models.TextField(blank=True, default='')),
                ('attempted_comment', models.TextField(blank=True, default='')),
            ],
            options={
                'verbose_name': 'Violation',
                'verbose_name_plural': 'Violations',
                'ordering': ['-timestamp'],
            },
        ),
    ]
