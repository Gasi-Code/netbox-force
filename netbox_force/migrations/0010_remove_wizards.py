from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_force', '0009_wizard_type_choices'),
    ]

    operations = [
        migrations.DeleteModel(
            name='WizardConfig',
        ),
        migrations.RemoveField(
            model_name='forcesettings',
            name='wizards_enabled',
        ),
    ]
