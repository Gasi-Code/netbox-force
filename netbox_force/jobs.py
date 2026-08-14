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
GRAYLOG_JOB_NAME = 'Graylog Source Sync'

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

    class GraylogSyncJob(JobRunner):

        class Meta:
            name = GRAYLOG_JOB_NAME

        def run(self, *args, **kwargs):
            from .graylog_sync import GraylogSyncSkipped, run_sync

            try:
                run = run_sync(triggered_by='job')
            except GraylogSyncSkipped as exc:
                logger.info('Graylog sync skipped: %s', exc.code)
                return f'skipped: {exc.code}'

            if not run.success:
                logger.warning('Graylog sync failed: %s %s',
                               run.error_code, run.message)
                return f'failed: {run.error_code}'

            return (f'{run.sources_seen} sources, {run.sources_matched} matched, '
                    f'{run.sources_unmatched} unmatched')

    def _drop_stale_jobs(interval, job_name=JOB_NAME):
        """
        Remove scheduled job rows whose due time has long passed.

        The scheduled entry lives in Redis while the Job row lives in
        Postgres. A container restart can lose the former and keep the
        latter, and enqueue_once() then sees a job it believes is already
        scheduled and creates nothing — the sync stops for good, silently.

        Only rows overdue by more than twice the interval are removed, so a
        job that is merely due-but-not-yet-picked-up is left alone.
        """
        from datetime import timedelta

        from django.utils import timezone

        try:
            from core.models import Job
        except Exception:
            return 0

        cutoff = timezone.now() - timedelta(minutes=max(interval * 2, 5))
        try:
            stale = Job.objects.filter(
                name=job_name, status='scheduled', scheduled__lt=cutoff)
            count = stale.count()
            if count:
                logger.warning(
                    'netbox_force: discarding %s stale %s job(s) '
                    'overdue since before %s', count, job_name, cutoff)
                stale.delete()
            return count
        except Exception:
            logger.debug('stale job cleanup failed', exc_info=True)
            return 0

    def schedule():
        """
        (Re)register the recurring jobs using their configured intervals.

        Called from AppConfig.ready(); failures are logged and ignored so a
        missing scheduling API can never stop the plugin from loading.
        """
        from .models import ForceSettings

        settings_obj = ForceSettings.get_settings()
        if settings_obj is None:
            return

        interval = settings_obj.checkmk_sync_interval or 0
        if settings_obj.checkmk_enabled and interval > 0:
            _drop_stale_jobs(interval, JOB_NAME)
            try:
                CheckmkSyncJob.enqueue_once(interval=interval)
            except Exception:
                logger.debug('CheckMK sync job could not be scheduled',
                             exc_info=True)

        graylog_interval = getattr(settings_obj, 'graylog_poll_interval', 0) or 0
        if getattr(settings_obj, 'graylog_read_enabled', False) and graylog_interval > 0:
            _drop_stale_jobs(graylog_interval, GRAYLOG_JOB_NAME)
            try:
                GraylogSyncJob.enqueue_once(interval=graylog_interval)
            except Exception:
                logger.debug('Graylog sync job could not be scheduled',
                             exc_info=True)

    def sync_overdue():
        """
        True when the last successful sync is older than twice the interval.

        A stalled background job is the failure mode that hurts most: the
        page keeps showing a patch status, it is just quietly out of date.
        The UI asks this so it can say so out loud.
        """
        from datetime import timedelta

        from django.utils import timezone

        from .models import CheckmkSyncRun, ForceSettings

        settings_obj = ForceSettings.get_settings()
        if settings_obj is None or not settings_obj.checkmk_enabled:
            return False
        interval = settings_obj.checkmk_sync_interval or 0
        if interval <= 0:
            return False

        run = CheckmkSyncRun.objects.filter(success=True).order_by('-started').first()
        if run is None:
            return True
        return (timezone.now() - run.started) > timedelta(minutes=interval * 2)

else:

    CheckmkSyncJob = None
    GraylogSyncJob = None

    def schedule():
        return

    def sync_overdue():
        return False
