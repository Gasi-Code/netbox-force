from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Squashed migration: combines 0001_initial + 0002_v4_features +
    0003_v41_features + 0004_v42_modules into a single initial migration.

    This ensures all tables and columns are created in one atomic step,
    preventing signal handlers from querying columns that do not yet exist.
    """

    initial = True

    dependencies = []

    operations = [
        # =================================================================
        # ForceSettings — singleton plugin settings (all fields)
        # =================================================================
        migrations.CreateModel(
            name='ForceSettings',
            fields=[
                ('id', models.AutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID',
                )),
                # --- General ---
                ('language', models.CharField(
                    choices=[('de', 'Deutsch'), ('en', 'English'), ('es', 'Español')],
                    default='de', max_length=5, verbose_name='Language',
                )),
                ('min_length', models.PositiveIntegerField(
                    default=2, verbose_name='Minimum changelog length',
                )),
                ('enforce_on_create', models.BooleanField(
                    default=False, verbose_name='Enforce on create',
                )),
                ('enforce_on_delete', models.BooleanField(
                    default=True, verbose_name='Enforce on delete',
                )),
                ('exempt_users', models.TextField(
                    blank=True, default='',
                    help_text='One username per line',
                    verbose_name='Exempt users',
                )),
                ('blacklisted_phrases', models.TextField(
                    blank=True, default='',
                    help_text=(
                        'One phrase per line. Changelog entries containing any of '
                        'these phrases (as whole words) will be rejected.'
                    ),
                    verbose_name='Blocked phrases',
                )),
                ('extra_exempt_models', models.TextField(
                    blank=True, default='',
                    help_text='One model per line (format: app.model, e.g. myplugin.mymodel)',
                    verbose_name='Exempt models',
                )),
                # --- Ticket Reference ---
                ('ticket_pattern', models.CharField(
                    blank=True, default='', max_length=255,
                    help_text='Regex pattern for required ticket references (e.g. JIRA-\\d+ or #\\d+). Leave empty to disable.',
                    verbose_name='Ticket pattern',
                )),
                ('ticket_pattern_hint', models.CharField(
                    blank=True, default='', max_length=500,
                    help_text='Human-readable example shown in error messages (e.g. "JIRA-1234 or CHG0012345").',
                    verbose_name='Ticket pattern hint',
                )),
                # --- Change Window ---
                ('change_window_enabled', models.BooleanField(
                    default=False, verbose_name='Enable change window',
                )),
                ('change_window_start', models.TimeField(
                    blank=True, default=None, null=True,
                    verbose_name='Window start time',
                )),
                ('change_window_end', models.TimeField(
                    blank=True, default=None, null=True,
                    verbose_name='Window end time',
                )),
                ('change_window_weekdays', models.CharField(
                    blank=True, default='1,2,3,4,5', max_length=20,
                    help_text='Comma-separated ISO weekday numbers (1=Monday, 7=Sunday)',
                    verbose_name='Allowed weekdays',
                )),
                # --- Audit Log ---
                ('audit_log_enabled', models.BooleanField(
                    default=False, verbose_name='Enable audit log',
                )),
                ('audit_log_retention_days', models.PositiveIntegerField(
                    default=90, verbose_name='Audit log retention (days)',
                )),
                # --- Dashboard ---
                ('dashboard_top_users_count', models.PositiveIntegerField(
                    default=10, verbose_name='Dashboard top users count',
                )),
                # --- Dry Run ---
                ('dry_run', models.BooleanField(
                    default=False, verbose_name='Dry run mode',
                    help_text='Log violations but do not block changes.',
                )),
                # --- Modules ---
                ('import_templates_enabled', models.BooleanField(
                    default=False, verbose_name='Enable import templates',
                )),
                ('guide_enabled', models.BooleanField(
                    default=False, verbose_name='Enable user guide',
                )),
            ],
            options={
                'verbose_name': 'NetBox Force Settings',
                'verbose_name_plural': 'NetBox Force Settings',
            },
        ),

        # =================================================================
        # ValidationRule — configurable naming/required-field rules
        # =================================================================
        migrations.CreateModel(
            name='ValidationRule',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID',
                )),
                ('rule_type', models.CharField(
                    choices=[('naming', 'Naming Convention'), ('required', 'Required Field')],
                    max_length=20, verbose_name='Rule type',
                )),
                ('model_label', models.CharField(
                    help_text='Format: app.model (e.g. dcim.device)',
                    max_length=100, verbose_name='Model',
                )),
                ('field_name', models.CharField(
                    help_text='The model field to validate (e.g. name, description, tenant)',
                    max_length=100, verbose_name='Field name',
                )),
                ('regex_pattern', models.CharField(
                    blank=True, default='',
                    help_text='Only for naming rules. The value must match this pattern.',
                    max_length=500, verbose_name='Regex pattern',
                )),
                ('error_message', models.CharField(
                    blank=True, default='',
                    help_text='Shown to the user when validation fails. Leave empty for default.',
                    max_length=500, verbose_name='Custom error message',
                )),
                ('enabled', models.BooleanField(
                    default=True, verbose_name='Enabled',
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

        # =================================================================
        # Violation — audit log for blocked changes
        # =================================================================
        migrations.CreateModel(
            name='Violation',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID',
                )),
                ('timestamp', models.DateTimeField(
                    auto_now_add=True, db_index=True,
                )),
                ('username', models.CharField(
                    db_index=True, max_length=150,
                )),
                ('model_label', models.CharField(max_length=100)),
                ('object_repr', models.CharField(
                    blank=True, default='', max_length=200,
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
                    db_index=True, max_length=30,
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

        # =================================================================
        # ImportTemplate — CSV templates for bulk import
        # =================================================================
        migrations.CreateModel(
            name='ImportTemplate',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID',
                )),
                ('model_label', models.CharField(
                    help_text='Format: app.model (e.g. dcim.device)',
                    max_length=100, verbose_name='Model',
                )),
                ('display_name', models.CharField(
                    help_text='Human-readable name shown to users.',
                    max_length=200, verbose_name='Display name',
                )),
                ('description', models.TextField(
                    blank=True, default='', verbose_name='Description',
                )),
                ('csv_content', models.TextField(
                    help_text='CSV header row (and optional example rows).',
                    verbose_name='CSV content',
                )),
                ('enabled', models.BooleanField(
                    default=True, verbose_name='Enabled',
                )),
                ('sort_order', models.PositiveIntegerField(
                    default=0, verbose_name='Sort order',
                )),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Import Template',
                'verbose_name_plural': 'Import Templates',
                'ordering': ['sort_order', 'display_name'],
            },
        ),

        # =================================================================
        # GuidePage — singleton user guide (WYSIWYG HTML)
        # =================================================================
        migrations.CreateModel(
            name='GuidePage',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID',
                )),
                ('content', models.TextField(
                    blank=True, default='',
                    help_text='HTML content for the user guide.',
                    verbose_name='Guide content',
                )),
                ('updated', models.DateTimeField(auto_now=True)),
                ('updated_by', models.CharField(
                    blank=True, default='', max_length=150,
                    verbose_name='Last updated by',
                )),
            ],
            options={
                'verbose_name': 'Guide Page',
                'verbose_name_plural': 'Guide Pages',
            },
        ),
    ]
