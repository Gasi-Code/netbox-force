"""
Scheduled CheckMK sync via NetBox's job framework.

JobRunner with a system interval only exists in newer NetBox releases, and the
job only ever runs when an RQ worker is present. Both conditions are checked
at import time and reported through jobs_available() so the settings page can
tell the truth about whether automatic syncing is actually happening.
"""

import logging

logger = logging.getLogger(__name__)

JOB_NAME = 'CheckMK Patch Sync'

try:
    from netbox.jobs import JobRunner
    JOBRUNNER_AVAILABLE = True
except Exception:  # pragma: no cover - depends on NetBox version
    JobRunner = None
    JOBRUNNER_AVAILABLE = False


def worker_count():
    """Number of registered RQ workers, or 0 when that cannot be determined."""
    try:
        import django_rq
        from rq import Worker
        queue = django_rq.get_queue('default')
        return len(Worker.all(connection=queue.connection))
    except Exception:
        return 0


def jobs_available():
    return JOBRUNNER_AVAILABLE and worker_count() > 0


if JOBRUNNER_AVAILABLE:

    class CheckmkSyncJob(JobRunner):

        class Meta:
            name = JOB_NAME

        def run(self, *args, **kwargs):
            from .sync import SyncSkipped, run_sync

            try:
                run = run_sync(triggered_by='job')
            except SyncSkipped as exc:
                logger.info('CheckMK sync skipped: %s', exc.code)
                return f'skipped: {exc.code}'

            if not run.success:
                logger.warning('CheckMK sync failed: %s %s',
                               run.error_code, run.message)
                return f'failed: {run.error_code}'

            return (f'{run.hosts_seen} hosts, {run.hosts_created} created, '
                    f'{run.hosts_updated} updated, {run.hosts_stale} stale')

    def schedule():
        """
        (Re)register the recurring job using the configured interval.

        Called from AppConfig.ready(); failures are logged and ignored so a
        missing scheduling API can never stop the plugin from loading.
        """
        from .models import ForceSettings

        settings_obj = ForceSettings.get_settings()
        if settings_obj is None:
            return
        interval = settings_obj.checkmk_sync_interval or 0
        if not settings_obj.checkmk_enabled or interval <= 0:
            return

        try:
            CheckmkSyncJob.enqueue_once(interval=interval)
        except Exception:
            logger.debug('CheckMK sync job could not be scheduled', exc_info=True)

else:

    CheckmkSyncJob = None

    def schedule():
        return
