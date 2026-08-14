from django.db import migrations, models


LEVEL_CHOICES = [
    ('3', 'Error'),
    ('4', 'Warning'),
    ('5', 'Notice'),
    ('6', 'Informational'),
    ('7', 'Debug'),
]


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_force', '0026_repair_nullability'),
    ]

    operations = [
        # --- Connection ---
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_enabled',
            field=models.BooleanField(
                default=False,
                verbose_name='Enable Graylog output',
                help_text='Send audit events to Graylog. Nothing is read from Graylog by this setting.',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_host',
            field=models.CharField(
                max_length=255, blank=True, default='',
                verbose_name='Graylog host',
                help_text='Hostname or IP of the Graylog input, e.g. graylog.example.com',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_port',
            field=models.PositiveIntegerField(
                default=12201,
                verbose_name='Port',
                help_text='Port of the GELF input. Graylog uses 12201 by default.',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_transport',
            field=models.CharField(
                max_length=10, default='udp',
                choices=[('udp', 'GELF UDP'), ('tcp', 'GELF TCP'),
                         ('tcp-tls', 'GELF TCP + TLS'), ('http', 'GELF HTTP'),
                         ('https', 'GELF HTTPS')],
                verbose_name='Transport',
                help_text='UDP never blocks and never confirms. TCP and HTTP confirm delivery '
                          'but cost a connection; use TLS whenever the path leaves the local network.',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_verify_ssl',
            field=models.BooleanField(
                default=True,
                verbose_name='Verify TLS certificate',
                help_text='Applies to the TLS and HTTPS transports only.',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_timeout',
            field=models.PositiveIntegerField(
                default=5,
                verbose_name='Timeout (seconds)',
                help_text='Applies to the background sender, never to a user request.',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_source_name',
            field=models.CharField(
                max_length=255, blank=True, default='',
                verbose_name='Source name',
                help_text='Value of the GELF host field. Leave empty to use the server hostname.',
            ),
        ),

        # --- Event selection ---
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_ev_object_create',
            field=models.BooleanField(default=True, verbose_name='Object created'),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_ev_object_update',
            field=models.BooleanField(default=True, verbose_name='Object changed'),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_ev_object_delete',
            field=models.BooleanField(default=True, verbose_name='Object deleted'),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_ev_login',
            field=models.BooleanField(default=True, verbose_name='Login'),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_ev_logout',
            field=models.BooleanField(default=False, verbose_name='Logout'),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_ev_login_failed',
            field=models.BooleanField(default=True, verbose_name='Failed login'),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_ev_violation',
            field=models.BooleanField(default=True, verbose_name='Blocked change'),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_ev_settings_change',
            field=models.BooleanField(default=True, verbose_name='Plugin settings changed'),
        ),

        # --- Severity per event type ---
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_lvl_object_create',
            field=models.CharField(max_length=1, default='6', choices=LEVEL_CHOICES,
                                   verbose_name='Severity: object created'),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_lvl_object_update',
            field=models.CharField(max_length=1, default='6', choices=LEVEL_CHOICES,
                                   verbose_name='Severity: object changed'),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_lvl_object_delete',
            field=models.CharField(max_length=1, default='5', choices=LEVEL_CHOICES,
                                   verbose_name='Severity: object deleted'),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_lvl_login',
            field=models.CharField(max_length=1, default='6', choices=LEVEL_CHOICES,
                                   verbose_name='Severity: login'),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_lvl_logout',
            field=models.CharField(max_length=1, default='6', choices=LEVEL_CHOICES,
                                   verbose_name='Severity: logout'),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_lvl_login_failed',
            field=models.CharField(max_length=1, default='4', choices=LEVEL_CHOICES,
                                   verbose_name='Severity: failed login'),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_lvl_violation',
            field=models.CharField(max_length=1, default='4', choices=LEVEL_CHOICES,
                                   verbose_name='Severity: blocked change'),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_lvl_settings_change',
            field=models.CharField(max_length=1, default='4', choices=LEVEL_CHOICES,
                                   verbose_name='Severity: plugin settings changed'),
        ),

        # --- Volume control ---
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_bulk_threshold',
            field=models.PositiveIntegerField(
                default=10,
                verbose_name='Summarise above',
                help_text='A request that changes more than this many objects is reported as '
                          'one summary event instead of one event per object. Set 0 to always '
                          'send every object individually.',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_max_events_per_request',
            field=models.PositiveIntegerField(
                default=100,
                verbose_name='Maximum events per request',
                help_text='Hard cap, applied when summarising is switched off.',
            ),
        ),

        # --- Business hours ---
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_only_outside_hours',
            field=models.BooleanField(
                default=False,
                verbose_name='Only outside business hours',
                help_text='Send events only outside the window below. Has no effect until '
                          'start and end time are set.',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_business_days',
            field=models.CharField(
                max_length=20, blank=True, default='1,2,3,4,5',
                verbose_name='Business days',
                help_text='Comma-separated ISO weekday numbers (1=Monday, 7=Sunday)',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_business_start',
            field=models.TimeField(null=True, blank=True, default=None,
                                   verbose_name='Business hours start'),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='graylog_business_end',
            field=models.TimeField(null=True, blank=True, default=None,
                                   verbose_name='Business hours end'),
        ),
    ]
