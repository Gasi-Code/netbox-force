"""
Repair netbox_force_modelpolicy on installations that ran both migration
generations.

Two sets of migrations exist for the same models: 0002_v4_features /
0003_v41_features / 0004_v42_modules, and the later 0002_v43_features /
0003_v44_features / 0004_v45_features. On an installation that applied the
early set first, the ModelPolicy table was created with the old column
layout, and the later CreateModel never corrected it — Django considers the
migration applied, so the mismatch persists silently until the page is opened
and Postgres reports the missing column.

This migration touches the database only, never the migration state: the
fields already exist in state from the CreateModel. It is idempotent, so on a
healthy installation it does nothing at all.

Obsolete columns are made nullable rather than dropped. They hold data from a
feature that no longer exists; dropping them would destroy it, while a NOT
NULL constraint on a column the model does not know about breaks every
insert. Making them nullable resolves the conflict without losing anything.
"""

from django.db import migrations

TABLE = 'netbox_force_modelpolicy'

# Columns the current model needs, with the SQL to create them if absent.
EXPECTED = {
    'check_required_fields_rules': 'boolean NOT NULL DEFAULT true',
    'enabled': 'boolean NOT NULL DEFAULT true',
    'created': 'timestamp with time zone NOT NULL DEFAULT now()',
}

# Left over from the earlier generation of this model.
OBSOLETE = ('require_ticket', 'enforce_change_window', 'check_required_fields', 'notes')


def _columns(cursor):
    cursor.execute(
        "SELECT column_name, is_nullable FROM information_schema.columns "
        "WHERE table_name = %s", [TABLE]
    )
    return {row[0]: row[1] for row in cursor.fetchall()}


def repair(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "SELECT to_regclass(%s) IS NOT NULL", [f'public.{TABLE}'])
        if not cursor.fetchone()[0]:
            return  # table does not exist yet; nothing to repair

        present = _columns(cursor)

        for name, ddl in EXPECTED.items():
            if name not in present:
                cursor.execute(f'ALTER TABLE {TABLE} ADD COLUMN "{name}" {ddl}')

        # The old column carried the same meaning under a different name.
        if ('check_required_fields' in present
                and 'check_required_fields_rules' not in present):
            cursor.execute(
                f'UPDATE {TABLE} SET check_required_fields_rules = check_required_fields'
            )

        for name in OBSOLETE:
            if present.get(name) == 'NO':
                cursor.execute(f'ALTER TABLE {TABLE} ALTER COLUMN "{name}" DROP NOT NULL')


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_force', '0023_checkmk_host_data'),
    ]

    operations = [
        migrations.RunPython(repair, migrations.RunPython.noop),
    ]
