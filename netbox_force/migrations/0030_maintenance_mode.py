"""
Maintenance mode.

One switch on the settings singleton and one new reason on the violation log.

The switch defaults to off, so an upgrade changes nothing until an
administrator turns it on. The reason is only a widening of the choice list —
Django records it in the schema but PostgreSQL stores the column unchanged, so
the operation is instant on a large violation table.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_force', '0029_security_hardening'),
    ]

    operations = [
        migrations.AddField(
            model_name='forcesettings',
            name='maintenance_mode',
            field=models.BooleanField(
                default=False,
                verbose_name='Maintenance mode',
                help_text='While enabled, only superusers can create, change '
                          'or delete objects. Everyone else sees a banner and '
                          'is blocked. Takes up to 30 seconds to reach every '
                          'worker process.'),
        ),
        migrations.AlterField(
            model_name='violation',
            name='reason',
            field=models.CharField(
                max_length=30, db_index=True,
                choices=[
                    ('missing_changelog', 'Missing Changelog'),
                    ('too_short', 'Changelog Too Short'),
                    ('blacklisted', 'Blacklisted Phrase'),
                    ('ticket_missing', 'Missing Ticket Reference'),
                    ('naming_violation', 'Naming Convention Violation'),
                    ('required_field', 'Required Field Missing'),
                    ('change_window', 'Outside Change Window'),
                    ('maintenance_mode', 'Maintenance Mode'),
                ]),
        ),
    ]
