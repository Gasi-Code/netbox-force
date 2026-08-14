from django.db import migrations, models
import django.db.models.deletion


MATCH_CHOICES = [
    ('manual', 'Assigned by hand'),
    ('ip', 'IP address'),
    ('hostname', 'Host name'),
    ('fqdn', 'Host name after removing the domain'),
    ('none', 'Not assigned'),
]

TRIGGER_CHOICES = [
    ('manual', 'Manual'),
    ('job', 'Scheduled job'),
    ('command', 'Management command'),
]


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('netbox_force', '0027_graylog_output'),
    ]

    operations = [
        # --- ForceSettings: read-back configuration ---
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_read_enabled',
            field=models.BooleanField(
                default=False,
                verbose_name='Enable reading from Graylog',
                help_text='Show Graylog information inside NetBox. Read-only — nothing in Graylog is modified.',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_api_url',
            field=models.CharField(
                max_length=500, blank=True, default='',
                verbose_name='Graylog web address',
                help_text='Address of the Graylog web interface, e.g. https://graylog.example.com. '
                          'Pasting a full search URL works — it is shortened automatically.',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_token_encrypted',
            field=models.TextField(
                blank=True, default='',
                verbose_name='API token',
                help_text='Stored encrypted. Never rendered back into the form.',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_api_verify_ssl',
            field=models.BooleanField(default=True, verbose_name='Verify TLS certificate'),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_api_timeout',
            field=models.PositiveIntegerField(
                default=10,
                verbose_name='Timeout (seconds)',
                help_text='Applies to the background poll and to the panels. A slow answer '
                          'yields an empty panel, never a broken page.',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_stream_id',
            field=models.CharField(
                max_length=64, blank=True, default='',
                verbose_name='Stream',
                help_text='Restrict every query to one Graylog stream. Leave empty to search everything.',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_search_flavor',
            field=models.CharField(
                max_length=20, default='auto',
                verbose_name='Search API form',
                help_text='Detected automatically. Reset to "auto" after a Graylog upgrade. '
                          'Pin to "legacy" to keep the plugin on plain GET requests.',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_poll_interval',
            field=models.PositiveIntegerField(
                default=5,
                verbose_name='Poll interval (minutes)',
                help_text='How often the background job refreshes the per-source counters. '
                          'Set 0 to refresh only on demand.',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_poll_batch_size',
            field=models.PositiveIntegerField(
                default=1000,
                verbose_name='Sources per poll',
                help_text='Upper bound on how many distinct sources one poll asks for. '
                          'The poll is a single grouped query, not one query per device.',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_window_hours',
            field=models.PositiveIntegerField(
                default=24,
                verbose_name='Counting window (hours)',
                help_text='Period the error and warning counters cover.',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_message_limit',
            field=models.PositiveIntegerField(
                default=25,
                verbose_name='Messages per panel',
                help_text='How many recent messages the panel on a device or VM shows.',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_domain_suffixes',
            field=models.TextField(
                blank=True, default='',
                verbose_name='Domain suffixes',
                help_text='One per line, e.g. example.com. Used to reduce an FQDN from Graylog '
                          'to a short name before matching. Nothing is guessed beyond this.',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_silent_after_hours',
            field=models.PositiveIntegerField(
                default=24,
                verbose_name='Silent after (hours)',
                help_text='A device or VM that is mapped to a Graylog source but has sent nothing '
                          'for this long is listed as silent. Set 0 to disable the check.',
            ),
        ),

        # --- Source inventory and mapping ---
        migrations.CreateModel(
            name='GraylogSource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('name', models.CharField(
                    max_length=255, unique=True, db_index=True,
                    verbose_name='Source',
                    help_text='Value of the Graylog source field.')),
                ('first_seen', models.DateTimeField(auto_now_add=True)),
                ('last_seen', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('last_message_at', models.DateTimeField(blank=True, null=True,
                                                         verbose_name='Last message')),
                ('total_count', models.PositiveIntegerField(default=0, verbose_name='Messages')),
                ('error_count', models.PositiveIntegerField(default=0, verbose_name='Errors')),
                ('warning_count', models.PositiveIntegerField(default=0, verbose_name='Warnings')),
                ('matched_id', models.PositiveBigIntegerField(blank=True, null=True)),
                ('match_method', models.CharField(
                    max_length=10, default='none', choices=MATCH_CHOICES,
                    db_index=True, verbose_name='Matched by')),
                ('ignored', models.BooleanField(
                    default=False, verbose_name='Ignored',
                    help_text='Keeps a source out of the unassigned list without assigning it.')),
                ('matched_type', models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='+', to='contenttypes.contenttype')),
            ],
            options={
                'verbose_name': 'Graylog Source',
                'verbose_name_plural': 'Graylog Sources',
                'ordering': ['name'],
            },
        ),
        migrations.AddIndex(
            model_name='graylogsource',
            index=models.Index(fields=['matched_type', 'matched_id'],
                               name='nbf_glsrc_matched_idx'),
        ),

        # --- Poll history ---
        migrations.CreateModel(
            name='GraylogSyncRun',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('started', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('finished', models.DateTimeField(blank=True, null=True)),
                ('duration_ms', models.PositiveIntegerField(default=0)),
                ('triggered_by', models.CharField(max_length=20, default='manual',
                                                  choices=TRIGGER_CHOICES)),
                ('success', models.BooleanField(default=False)),
                ('error_code', models.CharField(blank=True, default='', max_length=50)),
                ('message', models.TextField(blank=True, default='')),
                ('graylog_version', models.CharField(blank=True, default='', max_length=50)),
                ('api_flavor', models.CharField(blank=True, default='', max_length=20)),
                ('sources_seen', models.PositiveIntegerField(default=0)),
                ('sources_created', models.PositiveIntegerField(default=0)),
                ('sources_matched', models.PositiveIntegerField(default=0)),
                ('sources_unmatched', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Graylog Sync Run',
                'verbose_name_plural': 'Graylog Sync Runs',
                'ordering': ['-started'],
            },
        ),
    ]
