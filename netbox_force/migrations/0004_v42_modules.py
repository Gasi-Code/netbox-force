from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_force', '0003_v41_features'),
    ]

    operations = [
        # New fields on ForceSettings
        migrations.AddField(
            model_name='forcesettings',
            name='import_templates_enabled',
            field=models.BooleanField(default=False, verbose_name='Enable import templates'),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='guide_enabled',
            field=models.BooleanField(default=False, verbose_name='Enable user guide'),
        ),

        # ImportTemplate model
        migrations.CreateModel(
            name='ImportTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('model_label', models.CharField(help_text='Format: app.model (e.g. dcim.device)', max_length=100, verbose_name='Model')),
                ('display_name', models.CharField(help_text='Human-readable name shown to users.', max_length=200, verbose_name='Display name')),
                ('description', models.TextField(blank=True, default='', verbose_name='Description')),
                ('csv_content', models.TextField(help_text='CSV header row (and optional example rows).', verbose_name='CSV content')),
                ('enabled', models.BooleanField(default=True, verbose_name='Enabled')),
                ('sort_order', models.PositiveIntegerField(default=0, verbose_name='Sort order')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Import Template',
                'verbose_name_plural': 'Import Templates',
                'ordering': ['sort_order', 'display_name'],
            },
        ),

        # GuidePage singleton model
        migrations.CreateModel(
            name='GuidePage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(blank=True, default='', help_text='HTML content for the user guide.', verbose_name='Guide content')),
                ('updated', models.DateTimeField(auto_now=True)),
                ('updated_by', models.CharField(blank=True, default='', max_length=150, verbose_name='Last updated by')),
            ],
            options={
                'verbose_name': 'Guide Page',
                'verbose_name_plural': 'Guide Pages',
            },
        ),
    ]
