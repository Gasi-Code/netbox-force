from django.db import migrations, models


class Migration(migrations.Migration):
    """
    v4.3.0 features:
    - ForceSettings: enforcement_enabled, exempt_groups, webhook_*,
    - New ModelPolicy model for per-model enforcement overrides
    """

    dependencies = [
        ('netbox_force', '0001_initial'),
    ]

    operations = [
        # --- ForceSettings: Global enforcement toggle ---
        migrations.AddField(
            model_name='forcesettings',
            name='enforcement_enabled',
            field=models.BooleanField(
                default=True,
                verbose_name='Enforcement enabled',
                help_text='Disable to pause all enforcement globally (e.g. during maintenance windows).',
            ),
        ),
        # --- ForceSettings: Group exemptions ---
        migrations.AddField(
            model_name='forcesettings',
            name='exempt_groups',
            field=models.TextField(
                blank=True,
                default='',
                verbose_name='Exempt groups',
                help_text='One group name per line. All members bypass enforcement entirely.',
            ),
        ),
        # --- ForceSettings: Webhook ---
        migrations.AddField(
            model_name='forcesettings',
            name='webhook_enabled',
            field=models.BooleanField(
                default=False,
                verbose_name='Enable webhook',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='webhook_url',
            field=models.CharField(
                blank=True,
                default='',
                max_length=500,
                verbose_name='Webhook URL',
                help_text='HTTP POST endpoint for violation notifications.',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='webhook_secret',
            field=models.CharField(
                blank=True,
                default='',
                max_length=255,
                verbose_name='Webhook secret',
                help_text='Optional HMAC-SHA256 secret.',
            ),
        ),
        # --- New ModelPolicy model ---
        migrations.CreateModel(
            name='ModelPolicy',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID',
                )),
                ('model_label', models.CharField(
                    max_length=100, unique=True,
                    verbose_name='Model',
                    help_text='Format: app.model (e.g. dcim.device)',
                )),
                ('enforcement_enabled', models.BooleanField(
                    default=True,
                    verbose_name='Enforcement enabled',
                    help_text='If disabled, all enforcement is skipped for this model.',
                )),
                ('min_length_override', models.PositiveIntegerField(
                    null=True, blank=True,
                    verbose_name='Min. changelog length',
                    help_text='Overrides global minimum. Leave empty to use global.',
                )),
                ('require_ticket', models.BooleanField(
                    null=True, blank=True,
                    verbose_name='Require ticket reference',
                    help_text='True=always require, False=never, empty=use global.',
                )),
                ('enforce_change_window', models.BooleanField(
                    null=True, blank=True,
                    verbose_name='Enforce change window',
                    help_text='True=enforce, False=skip, empty=use global.',
                )),
                ('check_naming_rules', models.BooleanField(
                    default=True,
                    verbose_name='Check naming rules',
                )),
                ('check_required_fields', models.BooleanField(
                    default=True,
                    verbose_name='Check required fields',
                )),
                ('notes', models.TextField(
                    blank=True, default='',
                    verbose_name='Notes',
                )),
            ],
            options={
                'verbose_name': 'Model Policy',
                'verbose_name_plural': 'Model Policies',
                'ordering': ['model_label'],
            },
        ),
    ]
