"""
Pull patch status from CheckMK from the command line.

Exists for two reasons: it is the fallback for installations without an RQ
worker (a cron entry calling this command), and it is the fastest way to see
what a sync actually does without going through the UI.
"""

from django.core.management.base import BaseCommand, CommandError

from netbox_force.sync import SyncSkipped, run_sync

_SKIP_HINTS = {
    'disabled': 'CheckMK integration is disabled in NetBox Force settings.',
    'not_configured': 'CheckMK URL, user or secret is missing.',
    'no_settings': 'Plugin settings could not be loaded.',
    'already_running': 'Another sync is currently running.',
}


class Command(BaseCommand):
    help = 'Synchronise Patch Management with CheckMK'

    def add_arguments(self, parser):
        parser.add_argument(
            '--quiet', action='store_true',
            help='Only print output on failure (useful for cron).',
        )

    def handle(self, *args, **options):
        quiet = options.get('quiet')

        try:
            run = run_sync(triggered_by='command')
        except SyncSkipped as exc:
            raise CommandError(_SKIP_HINTS.get(exc.code, exc.code))

        if not run.success:
            raise CommandError(
                f'Sync failed [{run.error_code}]: {run.message}'
            )

        if not quiet:
            self.stdout.write(self.style.SUCCESS(
                f'CheckMK {run.checkmk_version} · query form "{run.api_flavor}" · '
                f'{run.duration_ms} ms'
            ))
            self.stdout.write(
                f'  services matched : {run.services_found}\n'
                f'  hosts seen       : {run.hosts_seen}\n'
                f'  entries created  : {run.hosts_created}\n'
                f'  entries updated  : {run.hosts_updated}\n'
                f'  no longer in CMK : {run.hosts_stale}\n'
                f'  auto-escalated   : {run.escalated}'
            )
