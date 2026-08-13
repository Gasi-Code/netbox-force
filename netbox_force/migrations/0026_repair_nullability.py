"""
Drop NOT NULL constraints the models no longer ask for.

Same root cause as 0024: on installations that ran both migration generations,
tables were created by the early set and the later CreateModel was recorded as
applied without changing the existing columns. 0024 repaired the columns it
listed by hand and missed netbox_force_modelpolicy.enforcement_enabled, which
the model declares null=True — saving a policy with "inherit global" then
failed with an IntegrityError.

This migration derives the column list from model state instead of naming
columns, so a mismatch on any other field is repaired in the same pass.

Only ever relaxes: a NOT NULL is dropped where the model allows NULL. It never
adds a constraint, so it cannot reject existing rows. Idempotent — on a healthy
installation it makes no changes.
"""

from django.db import migrations


def repair(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return

    models = [m for m in apps.get_models()
              if m._meta.app_label == 'netbox_force']

    with schema_editor.connection.cursor() as cursor:
        for model in models:
            table = model._meta.db_table

            cursor.execute("SELECT to_regclass(%s) IS NOT NULL",
                           [f'public.{table}'])
            if not cursor.fetchone()[0]:
                continue  # table not created yet

            cursor.execute(
                "SELECT column_name, is_nullable FROM information_schema.columns "
                "WHERE table_name = %s", [table]
            )
            is_nullable = {row[0]: row[1] for row in cursor.fetchall()}

            for field in model._meta.concrete_fields:
                if not field.null:
                    continue
                column = field.column
                if is_nullable.get(column) == 'NO':
                    cursor.execute(
                        f'ALTER TABLE "{table}" ALTER COLUMN "{column}" DROP NOT NULL'
                    )
                    print(f'  netbox_force: {table}.{column} NOT NULL entfernt')


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_force', '0025_patchvm_device'),
    ]

    operations = [
        migrations.RunPython(repair, migrations.RunPython.noop),
    ]
