"""
Periodic poll of Graylog.

The whole point of the design is in one line further down: the counters for
every host come from a *single* grouped query, not from one query per NetBox
device. A site with 800 devices costs three requests per poll, not 800.

Nothing here writes to Graylog, and nothing here writes to a NetBox core
object. Everything lands in the plugin's own GraylogSource table.
"""

import logging
import time

from django.utils import timezone

logger = logging.getLogger(__name__)


class GraylogSyncSkipped(Exception):
    """Raised when a poll is not attempted at all — not an error."""

    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _settings():
    from .models import ForceSettings
    return ForceSettings.get_settings()


def run_sync(triggered_by='manual', settings_obj=None):
    """
    Refresh the per-source counters and re-run the matching chain.

    Returns the GraylogSyncRun row. Raises GraylogSyncSkipped when reading is
    switched off or unconfigured; every other failure is recorded on the run.
    """
    from .graylog_api import GraylogApiError, build_client
    from .models import GraylogSource, GraylogSyncRun

    settings_obj = settings_obj or _settings()
    if settings_obj is None:
        raise GraylogSyncSkipped('no_settings')
    if not settings_obj.graylog_read_enabled:
        raise GraylogSyncSkipped('disabled')
    if not settings_obj.graylog_read_configured:
        raise GraylogSyncSkipped('not_configured')

    run = GraylogSyncRun.objects.create(triggered_by=triggered_by)
    started = time.monotonic()

    def finish(success, error_code='', message=''):
        run.success = success
        run.error_code = error_code
        run.message = message
        run.finished = timezone.now()
        run.duration_ms = int((time.monotonic() - started) * 1000)
        run.save()
        GraylogSyncRun.prune()
        return run

    try:
        client = build_client(settings_obj)
    except GraylogApiError as exc:
        return finish(False, exc.code, exc.detail[:500])

    try:
        version, _node_id, _cluster_id = client.get_version()
        run.graylog_version = version
    except GraylogApiError as exc:
        return finish(False, exc.code, exc.detail[:500])

    window_seconds = max(int(settings_obj.graylog_window_hours or 24), 1) * 3600
    limit = max(int(settings_obj.graylog_poll_batch_size or 1000), 1)

    try:
        counts = client.count_by_source(window_seconds, limit=limit)
    except GraylogApiError as exc:
        return finish(False, exc.code, exc.detail[:500])
    except Exception as exc:
        logger.exception('Graylog poll failed')
        return finish(False, 'internal', str(exc)[:500])

    run.api_flavor = client.detected_flavor or ''

    # Remember the detected search form so the next poll goes straight to it.
    if client.detected_flavor and settings_obj.graylog_search_flavor == 'auto':
        try:
            settings_obj.graylog_search_flavor = client.detected_flavor
            settings_obj.save()
        except Exception:
            logger.debug('could not persist detected Graylog search flavor',
                         exc_info=True)

    try:
        stats = _apply_counts(settings_obj, counts)
    except Exception as exc:
        logger.exception('Applying Graylog counts failed')
        return finish(False, 'internal', str(exc)[:500])

    run.sources_seen = stats['seen']
    run.sources_created = stats['created']
    run.sources_matched = stats['matched']
    run.sources_unmatched = stats['unmatched']
    return finish(True)


def _apply_counts(settings_obj, counts):
    """Upsert the source rows and rerun matching. Returns counters."""
    from .graylog_match import MatchIndex
    from .models import GraylogSource

    now = timezone.now()
    index = MatchIndex(settings_obj.get_graylog_domain_suffixes())

    existing = {row.name: row for row in GraylogSource.objects.all()}
    created = 0
    seen = 0

    for name, values in counts.items():
        name = (name or '').strip()
        if not name:
            continue
        seen += 1
        row = existing.get(name)
        if row is None:
            row = GraylogSource(name=name)
            created += 1
            existing[name] = row

        row.total_count = values.get('total', 0)
        row.error_count = values.get('errors', 0)
        row.warning_count = values.get('warnings', 0)
        row.last_seen = now
        if row.total_count:
            row.last_message_at = now

    # Sources Graylog did not report in this window have gone quiet. The
    # counters are zeroed; last_message_at is deliberately left alone, because
    # it is the only thing that says how long the silence has lasted.
    for name, row in existing.items():
        if name not in counts:
            row.total_count = 0
            row.error_count = 0
            row.warning_count = 0

    matched = 0
    for row in existing.values():
        # A mapped object that has since been deleted must not keep a dangling
        # reference — including a manual one.
        if row.is_matched and row.matched_object is None:
            row.clear_match()

        if row.match_method != 'manual':
            model, pk, method = index.match(row.name)
            if model is not None:
                _assign(row, model, pk, method)
            elif row.is_matched:
                row.clear_match()

        if row.is_matched:
            matched += 1

        try:
            row.save()
        except Exception:
            logger.debug('could not save Graylog source %s', row.name,
                         exc_info=True)

    return {
        'seen': seen,
        'created': created,
        'matched': matched,
        'unmatched': len(existing) - matched,
    }


def _assign(row, model, pk, method):
    from django.contrib.contenttypes.models import ContentType

    try:
        row.matched_type = ContentType.objects.get_for_model(model)
        row.matched_id = pk
        row.match_method = method
    except Exception:
        logger.debug('could not assign Graylog source %s', row.name,
                     exc_info=True)


# =============================================================================
# QUERIES FOR THE UI
# =============================================================================

def unmatched_sources(limit=None):
    from .models import GraylogSource

    queryset = GraylogSource.objects.filter(
        matched_id__isnull=True, ignored=False).order_by('-total_count', 'name')
    return list(queryset[:limit]) if limit else list(queryset)


def silent_sources(settings_obj=None):
    """
    Sources mapped to a NetBox object that have stopped sending.

    This is the cross-check neither system can do alone: NetBox says the host
    exists, Graylog says it has not spoken. Either it is dead, its logging is
    broken, or the NetBox entry is a leftover.
    """
    from .models import GraylogSource

    settings_obj = settings_obj or _settings()
    if settings_obj is None:
        return []
    threshold = int(getattr(settings_obj, 'graylog_silent_after_hours', 0) or 0)
    if threshold <= 0:
        return []

    rows = GraylogSource.objects.filter(
        matched_id__isnull=False).order_by('last_message_at', 'name')
    return [row for row in rows if row.is_silent(threshold)]


def undocumented_objects(limit=200):
    """
    Devices and VMs with no Graylog source mapped to them at all.

    The other half of the cross-check: these never showed up in Graylog under
    any name the matching chain recognises.
    """
    from django.apps import apps

    from .models import GraylogSource

    mapped = {}
    for source in GraylogSource.objects.filter(matched_id__isnull=False) \
            .values_list('matched_type_id', 'matched_id'):
        mapped.setdefault(source[0], set()).add(source[1])

    out = []
    from django.contrib.contenttypes.models import ContentType

    for app_label, model_name in (('dcim', 'Device'),
                                  ('virtualization', 'VirtualMachine')):
        try:
            model = apps.get_model(app_label, model_name)
            content_type = ContentType.objects.get_for_model(model)
        except Exception:
            continue
        known = mapped.get(content_type.id, set())
        try:
            queryset = model.objects.exclude(pk__in=known).only('id', 'name')
            for obj in queryset[:limit]:
                out.append(obj)
        except Exception:
            logger.debug('listing unmapped %s failed', model_name, exc_info=True)
    return out[:limit]


def sync_overdue():
    """
    True when the last successful poll is older than twice the interval.

    A stalled poll is the failure that hurts most: the page keeps showing
    counters, they are just quietly out of date.
    """
    from datetime import timedelta

    from .models import GraylogSyncRun

    settings_obj = _settings()
    if settings_obj is None or not settings_obj.graylog_read_enabled:
        return False
    interval = int(getattr(settings_obj, 'graylog_poll_interval', 0) or 0)
    if interval <= 0:
        return False

    run = GraylogSyncRun.objects.filter(success=True).order_by('-started').first()
    if run is None:
        return True
    return (timezone.now() - run.started) > timedelta(minutes=interval * 2)
