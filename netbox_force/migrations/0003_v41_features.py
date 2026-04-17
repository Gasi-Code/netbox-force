from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_force', '0002_v4_features'),
    ]

    operations = [
        migrations.AddField(
            model_name='forcesettings',
            name='ticket_pattern_hint',
            field=models.CharField(blank=True, default='', max_length=500),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='dashboard_top_users_count',
            field=models.PositiveIntegerField(default=10),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='dry_run',
            field=models.BooleanField(default=False),
        ),
    ]
