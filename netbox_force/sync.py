"""
CheckMK → Patch Management synchronisation.

Design constraints that shaped this module:

* Only the fields in CHECKMK_SYNC_FIELDS are ever written. Ticket numbers,
  comments, maintenance windows, contacts and the NetBox VM link are
  hand-maintained and must survive every run.
* Writes go through queryset .update(), which bypasses pre_save — the sync is
  an automated process and must not be blocked by changelog enforcement.
  auto_now does not fire on queryset updates, so 'updated' is set explicitly.
* A host that disappears from CheckMK is never deleted. It is flagged and its
  status frozen, because a missing host means missing information, not good
  news.
"""

import logging
import threading
import time
from datetime import timedelta

from django.utils import timezone

from .checkmk import STATE_MAP, CheckmkError, build_client
from .models import (
    CHECKMK_SYNC_FIELDS, CheckmkSyncRun, ForceSettings, PatchVM,
)

logger = logging.getLogger(__name__)

# Guards against two syncs running at once (job and manual button colliding).
_sync_lock = threading.Lock()


class SyncSkipped(Exception):
    """Raised when a sync cannot start — carries a reason code for the UI."""

    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _worst(rows):
    """
    Collapse several update services on one host into a single verdict.

    A host can report both 'System Updates' and 'APT Updates'. The most severe
    state wins, and the outputs are joined so the detail page shows why.
    """
    worst = max(rows, key=lambda r: (r['state'] == 3, r['state']))
    details = '\n'.join(
        f"{r['description']}: {r['plugin_output']}" for r in rows
    )
    services = ', '.join(sorted({r['description'] for r in rows}))
    return worst['state'], services, details


def _match_existing(host_name, by_checkmk, by_fqdn, by_vm_name):
    key = host_name.lower()
    return by_checkmk.get(key) or by_fqdn.get(key) or by_vm_name.get(key)


def _find_netbox_vm(host_name):
    """
    Best-effort link to a NetBox VirtualMachine, matched on name — with and
    without the domain part. Only ever used when creating a new entry, so an
    existing manual link is never overwritten.
    """
    try:
        from django.apps import apps
        VirtualMachine = apps.get_model('virtualization', 'VirtualMachine')
    except Exception:
        return None

    candidates = [host_name]
    if '.' in host_name:
        candidates.append(host_name.split('.', 1)[0])

    for name in candidates:
        try:
            vm = VirtualMachine.objects.filter(name__iexact=name).first()
        except Exception:
            return None
        if vm and not PatchVM.objects.filter(vm=vm).exists():
            return vm
    return None


def _resolve_status(state, existing, escalation_days, now):
    """
    Map a CheckMK state to (patch_status, first_warned).

    first_warned marks the start of an ongoing WARNING period. It survives
    repeated warnings so the clock keeps running, and is cleared by both OK
    and a genuine CRIT — a CRIT is its own reason for red and must not later
    be mistaken for an age-based escalation.
    """
    mapped = STATE_MAP.get(state, 'yellow')

    if mapped == 'green':
        return 'green', None
    if mapped == 'red':
        return 'red', None

    first_warned = (existing.first_warned if existing else None) or now
    if escalation_days > 0 and (now - first_warned) >= timedelta(days=escalation_days):
        return 'red', first_warned
    return 'yellow', first_warned


def run_sync(triggered_by='manual'):
    """
    Pull once from CheckMK and reconcile Patch Management.

    Always returns a persisted CheckmkSyncRun — failures are recorded, not
    swallowed, so the UI can show what went wrong and when.
    """
    if not _sync_lock.acquire(blocking=False):
        raise SyncSkipped('already_running')

    started = time.monotonic()
    run = CheckmkSyncRun(triggered_by=triggered_by)

    try:
        settings_obj = ForceSettings.get_settings()
        if settings_obj is None:
            raise SyncSkipped('no_settings')
        if not settings_obj.checkmk_enabled:
            raise SyncSkipped('disabled')
        if not settings_obj.checkmk_configured:
            raise SyncSkipped('not_configured')

        try:
            _perform(settings_obj, run)
            run.success = True
        except CheckmkError as exc:
            run.success = False
            run.error_code = exc.code
            run.message = str(exc.detail)[:2000]
            logger.warning('CheckMK sync failed: %s', exc)
        except Exception as exc:
            run.success = False
            run.error_code = 'internal'
            run.message = str(exc)[:2000]
            logger.exception('CheckMK sync crashed')

        run.finished = timezone.now()
        run.duration_ms = int((time.monotonic() - started) * 1000)
        run.save()
        CheckmkSyncRun.prune()
        return run
    finally:
        _sync_lock.release()


def _perform(settings_obj, run):
    client = build_client(settings_obj)

    version, edition = client.get_version()
    run.checkmk_version = f'{version} ({edition})'[:50]

    rows = client.fetch_update_services(settings_obj.checkmk_service_pattern)
    run.api_flavor = client.detected_flavor or ''
    run.services_found = len(rows)

    # Remember the working query form so later runs skip the probe. Written
    # with a queryset update to avoid the enforcement signal, then the cached
    # settings instance is invalidated so the next reader sees it.
    if client.detected_flavor and settings_obj.checkmk_api_flavor != client.detected_flavor:
        ForceSettings.objects.filter(pk=1).update(
            checkmk_api_flavor=client.detected_flavor)
        settings_obj.checkmk_api_flavor = client.detected_flavor
        with ForceSettings._cache_lock:
            ForceSettings._cached_instance = None
            ForceSettings._cache_timestamp = 0

    by_host = {}
    for row in rows:
        by_host.setdefault(row['host_name'], []).append(row)
    run.hosts_seen = len(by_host)

    existing = list(PatchVM.objects.all().select_related('vm'))
    by_checkmk = {p.checkmk_host_name.lower(): p for p in existing if p.checkmk_host_name}
    by_fqdn = {p.fqdn.lower(): p for p in existing if p.fqdn}
    by_vm_name = {p.vm.name.lower(): p for p in existing if p.vm_id and p.vm}

    now = timezone.now()
    escalation_days = settings_obj.checkmk_escalation_days or 0
    seen_pks = set()

    for host_name, host_rows in by_host.items():
        state, services, details = _worst(host_rows)
        pvm = _match_existing(host_name, by_checkmk, by_fqdn, by_vm_name)
        status, first_warned = _resolve_status(state, pvm, escalation_days, now)

        values = {
            'patch_status': status,
            'first_warned': first_warned,
            'last_checked': now,
            'update_details': details,
            'checkmk_host_name': host_name,
            'checkmk_service': services[:255],
            'checkmk_state': state,
            'checkmk_monitored': True,
            'checkmk_last_seen': now,
            'updated': now,
        }
        # Belt and braces: the whitelist is the contract, enforce it here too.
        values = {k: v for k, v in values.items() if k in CHECKMK_SYNC_FIELDS}

        if pvm is None:
            pvm = PatchVM.objects.create(
                fqdn=host_name,
                vm=_find_netbox_vm(host_name),
                source='checkmk',
                **values,
            )
            by_checkmk[host_name.lower()] = pvm
            run.hosts_created += 1
        else:
            PatchVM.objects.filter(pk=pvm.pk).update(**values)
            run.hosts_updated += 1

        seen_pks.add(pvm.pk)

    # Entries CheckMK used to report and no longer does. Status is left as it
    # was; only the monitoring flag changes.
    run.hosts_stale = (
        PatchVM.objects
        .exclude(pk__in=seen_pks)
        .exclude(checkmk_host_name='')
        .filter(checkmk_monitored=True)
        .update(checkmk_monitored=False, updated=now)
    )

    run.escalated = PatchVM.escalate_overdue()
