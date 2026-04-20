from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_force', '0004_v45_features'),
    ]

    operations = [
        migrations.CreateModel(
            name='WidgetImage',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID',
                )),
                ('name', models.CharField(
                    help_text='Filename as used in the widget URL (e.g. company-logo.png)',
                    max_length=255, unique=True, verbose_name='Filename',
                )),
                ('file', models.FileField(
                    upload_to='netbox_force/widget_images/', verbose_name='File',
                )),
                ('file_size', models.PositiveIntegerField(
                    default=0, verbose_name='File size (bytes)',
                )),
                ('content_type', models.CharField(
                    blank=True, default='', max_length=100, verbose_name='Content type',
                )),
                ('uploaded_by', models.CharField(
                    blank=True, default='', max_length=150, verbose_name='Uploaded by',
                )),
                ('uploaded_at', models.DateTimeField(
                    auto_now_add=True, verbose_name='Uploaded at',
                )),
            ],
            options={
                'verbose_name': 'Widget Image',
                'verbose_name_plural': 'Widget Images',
                'ordering': ['name'],
            },
        ),
    ]
