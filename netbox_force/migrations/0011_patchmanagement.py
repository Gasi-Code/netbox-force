import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_force', '0010_remove_wizards'),
    ]

    operations = [
        migrations.CreateModel(
            name='PatchVM',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fqdn', models.CharField(blank=True, default='', max_length=255, verbose_name='FQDN')),
                ('ip_address', models.CharField(blank=True, default='', max_length=50, verbose_name='IP Address')),
                ('admins', models.TextField(blank=True, default='', help_text='One per line', verbose_name='Administrators')),
                ('verfahrensbetreuer', models.TextField(blank=True, default='', help_text='One per line', verbose_name='Process Owners')),
                ('os_info', models.CharField(blank=True, default='', help_text='e.g. Ubuntu 22.04 LTS x64', max_length=200, verbose_name='OS')),
                ('maintenance_window', models.CharField(
                    choices=[
                        ('sun_0200_0600', 'Sunday 02:00–06:00'),
                        ('sat_2200_0200', 'Saturday 22:00–02:00'),
                        ('mon_0000_0600', 'Monday 00:00–06:00'),
                        ('fri_2200_0200', 'Friday 22:00–02:00'),
                        ('daily_0200_0400', 'Daily 02:00–04:00'),
                        ('none', 'No maintenance window'),
                        ('custom', 'Custom / on request'),
                    ],
                    default='none', max_length=30, verbose_name='Maintenance Window',
                )),
                ('update_installation', models.CharField(
                    choices=[
                        ('manual', 'Manual'),
                        ('automatic', 'Automatic'),
                        ('unknown', 'Not detected'),
                    ],
                    default='unknown', max_length=20, verbose_name='Update Installation',
                )),
                ('patch_status', models.CharField(
                    choices=[
                        ('green', 'Green / OK'),
                        ('yellow', 'Yellow / Warning'),
                        ('red', 'Red / Critical'),
                    ],
                    default='green', max_length=10, verbose_name='Patch Status',
                )),
                ('ticket_number', models.CharField(blank=True, default='', max_length=100, verbose_name='Ticket Number')),
                ('comment', models.TextField(blank=True, default='', verbose_name='Comment')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('vm', models.OneToOneField(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='patch_entry',
                    to='virtualization.virtualmachine',
                    verbose_name='NetBox VM',
                    db_constraint=False,
                )),
            ],
            options={
                'verbose_name': 'Patch Management VM',
                'verbose_name_plural': 'Patch Management VMs',
                'ordering': ['fqdn'],
            },
        ),
        migrations.CreateModel(
            name='PatchUpdateEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='Date')),
                ('updated_by', models.CharField(max_length=200, verbose_name='Updated By')),
                ('software', models.CharField(max_length=500, verbose_name='Software / Updates')),
                ('info', models.TextField(blank=True, default='', verbose_name='Notes')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('vm', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='update_entries',
                    to='netbox_force.patchvm',
                    verbose_name='VM',
                )),
            ],
            options={
                'verbose_name': 'Update Entry',
                'verbose_name_plural': 'Update Entries',
                'ordering': ['-date'],
            },
        ),
    ]
