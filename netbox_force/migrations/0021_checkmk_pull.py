from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_force', '0020_escalation_and_changelog_scope'),
    ]

    operations = [
        # --- ForceSettings: CheckMK pull configuration ---
        migrations.AddField(
            model_name='forcesettings',
            name='checkmk_enabled',
            field=models.BooleanField(
                default=False,
                verbose_name='Enable CheckMK integration',
                help_text='Read patch status from CheckMK instead of maintaining it by hand.',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='checkmk_url',
            field=models.CharField(
                max_length=500, blank=True, default='',
                verbose_name='CheckMK URL',
                help_text='Site URL, e.g. https://checkmk.example.com/mysite',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='checkmk_username',
            field=models.CharField(
                max_length=150, blank=True, default='',
                verbose_name='Automation user',
                help_text='CheckMK user with an automation secret and read-only (guest) role.',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='checkmk_secret_encrypted',
            field=models.TextField(
                blank=True, default='',
                verbose_name='Automation secret',
                help_text='Stored encrypted. Never rendered back into the form.',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='checkmk_verify_ssl',
            field=models.BooleanField(default=True, verbose_name='Verify TLS certificate'),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='checkmk_timeout',
            field=models.PositiveIntegerField(default=10, verbose_name='Timeout (seconds)'),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='checkmk_service_pattern',
            field=models.CharField(
                max_length=200, default='Updates?',
                verbose_name='Service filter',
                help_text='Regular expression matched against CheckMK service names, e.g. Updates?',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='checkmk_sync_interval',
            field=models.PositiveIntegerField(
                default=15,
                verbose_name='Sync interval (minutes)',
                help_text='How often the background job pulls from CheckMK. Set 0 to sync only on demand.',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='checkmk_api_flavor',
            field=models.CharField(
                max_length=20, default='auto',
                verbose_name='API query form',
                help_text='Detected automatically. Reset to "auto" after a CheckMK upgrade.',
            ),
        ),
        # The inbound webhook was replaced by the pull integration; its secret
        # has no remaining consumer.
        migrations.RemoveField(
            model_name='forcesettings',
            name='checkmk_webhook_secret',
        ),

        # --- PatchVM: CheckMK provenance ---
        migrations.AddField(
            model_name='patchvm',
            name='checkmk_host_name',
            field=models.CharField(
                max_length=255, blank=True, default='', db_index=True,
                verbose_name='CheckMK host name',
                help_text='Exact host name in CheckMK. Filled by the sync; kept separate '
                          'from FQDN so renaming one does not break the other.',
            ),
        ),
        migrations.AddField(
            model_name='patchvm',
            name='checkmk_service',
            field=models.CharField(max_length=255, blank=True, default='',
                                   verbose_name='CheckMK service'),
        ),
        migrations.AddField(
            model_name='patchvm',
            name='checkmk_state',
            field=models.SmallIntegerField(
                null=True, blank=True,
                verbose_name='CheckMK raw state',
                help_text='0=OK, 1=WARN, 2=CRIT, 3=UNKNOWN',
            ),
        ),
        migrations.AddField(
            model_name='patchvm',
            name='checkmk_monitored',
            field=models.BooleanField(default=False, verbose_name='Monitored in CheckMK'),
        ),
        migrations.AddField(
            model_name='patchvm',
            name='checkmk_last_seen',
            field=models.DateTimeField(null=True, blank=True,
                                       verbose_name='Last seen in CheckMK'),
        ),
        migrations.AddField(
            model_name='patchvm',
            name='source',
            field=models.CharField(
                max_length=10, default='manual',
                choices=[('manual', 'Created manually'),
                         ('checkmk', 'Discovered in CheckMK')],
                verbose_name='Source',
            ),
        ),

        # --- Sync history ---
        migrations.CreateModel(
            name='CheckmkSyncRun',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('started', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('finished', models.DateTimeField(blank=True, null=True)),
                ('duration_ms', models.PositiveIntegerField(default=0)),
                ('triggered_by', models.CharField(
                    max_length=20, default='manual',
                    choices=[('manual', 'Manual'), ('job', 'Scheduled job'),
                             ('command', 'Management command')])),
                ('success', models.BooleanField(default=False)),
                ('error_code', models.CharField(blank=True, default='', max_length=50)),
                ('message', models.TextField(blank=True, default='')),
                ('checkmk_version', models.CharField(blank=True, default='', max_length=50)),
                ('api_flavor', models.CharField(blank=True, default='', max_length=20)),
                ('services_found', models.PositiveIntegerField(default=0)),
                ('hosts_seen', models.PositiveIntegerField(default=0)),
                ('hosts_created', models.PositiveIntegerField(default=0)),
                ('hosts_updated', models.PositiveIntegerField(default=0)),
                ('hosts_stale', models.PositiveIntegerField(default=0)),
                ('escalated', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'CheckMK Sync Run',
                'verbose_name_plural': 'CheckMK Sync Runs',
                'ordering': ['-started'],
            },
        ),
    ]
