from django.db import migrations, models


class Migration(migrations.Migration):
    """
    v4.4.0: Group exemptions, webhook notifications, and per-model policies.
    """

    dependencies = [
        ('netbox_force', '0002_v43_features'),
    ]

    operations = [
        # --- ForceSettings: exempt_groups ---
        migrations.AddField(
            model_name='forcesettings',
            name='exempt_groups',
            field=models.TextField(
                blank=True,
                default='',
                verbose_name='Exempt groups',
                help_text='One group name per line. All members of these groups are exempt from enforcement.',
            ),
        ),

        # --- ForceSettings: webhook fields ---
        migrations.AddField(
            model_name='forcesettings',
            name='webhook_enabled',
            field=models.BooleanField(
                default=False,
                verbose_name='Enable webhook',
                help_text='Send an HTTP POST to the webhook URL on every violation.',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='webhook_url',
            field=models.CharField(
                max_length=500,
                blank=True,
                default='',
                verbose_name='Webhook URL',
                help_text='Endpoint to receive violation notifications (JSON POST).',
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='webhook_secret',
            field=models.CharField(
                max_length=255,
                blank=True,
                default='',
                verbose_name='Webhook secret',
                help_text='Optional HMAC-SHA256 secret. If set, adds an X-NetBox-Force-Signature header.',
            ),
        ),

        # --- ModelPolicy table ---
        migrations.CreateModel(
            name='ModelPolicy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('model_label', models.CharField(
                    max_length=100,
                    unique=True,
                    verbose_name='Model',
                    help_text='Format: app.model (e.g. dcim.device)',
                )),
                ('enforcement_enabled', models.BooleanField(
                    null=True,
                    blank=True,
                    default=None,
                    verbose_name='Enforcement enabled override',
                    help_text='Override enforcement for this model. Leave empty to inherit the global setting.',
                )),
                ('min_length_override', models.PositiveIntegerField(
                    null=True,
                    blank=True,
                    default=None,
                    verbose_name='Min. changelog length override',
                    help_text='Override minimum changelog length for this model. Leave empty to use the global setting.',
                )),
                ('check_naming_rules', models.BooleanField(
                    default=True,
                    verbose_name='Check naming convention rules',
                    help_text='If disabled, naming convention rules are not checked for this model.',
                )),
                ('check_required_fields_rules', models.BooleanField(
                    default=True,
                    verbose_name='Check required field rules',
                    help_text='If disabled, required field rules are not checked for this model.',
                )),
                ('enabled', models.BooleanField(
                    default=True,
                    verbose_name='Policy enabled',
                    help_text='If disabled, this policy is ignored (global settings apply).',
                )),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Model Policy',
                'verbose_name_plural': 'Model Policies',
                'ordering': ['model_label'],
            },
        ),
    ]
