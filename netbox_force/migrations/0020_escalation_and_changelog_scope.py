from django.db import migrations, models


def clear_first_warned_on_critical(apps, schema_editor):
    """
    first_warned now means 'start of an ongoing WARNING period' and is cleared
    by a genuine CRIT report. The previous webhook version also set it on CRIT,
    which would make those rows look auto-escalated. Reset them.
    """
    PatchVM = apps.get_model('netbox_force', 'PatchVM')
    PatchVM.objects.filter(patch_status='red').update(first_warned=None)


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_force', '0019_checkmk_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='forcesettings',
            name='checkmk_escalation_days',
            field=models.PositiveIntegerField(
                default=30,
                verbose_name='CheckMK escalation threshold (days)',
                help_text=(
                    'A VM that stays in WARNING for this many days is automatically '
                    'escalated to CRITICAL. Set 0 to disable escalation.'
                ),
            ),
        ),
        migrations.AddField(
            model_name='forcesettings',
            name='auto_changelog_scope',
            field=models.TextField(
                blank=True,
                default='',
                verbose_name='Auto-changelog scope',
                help_text=(
                    'Restrict auto-generated changelog messages to these NetBox areas. '
                    'One app label per line. Leave empty to apply to all areas.'
                ),
            ),
        ),
        migrations.RunPython(
            clear_first_warned_on_critical,
            migrations.RunPython.noop,
        ),
    ]
