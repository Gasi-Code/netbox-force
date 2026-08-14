"""
Matching Graylog sources to NetBox devices and virtual machines.

Deliberately not fuzzy.

A similarity score looks helpful and is dangerous here. Real host names are
numbered by design: srv-web-01 and srv-web-02 differ by one character, so any
edit-distance measure calls them a 96% match while they are two different
machines. In a naming scheme — which is to say, in every NetBox worth the name
— the most similar candidate is systematically the wrong one. Logs would be
filed under the neighbouring server and nobody would notice.

So the chain below is exact at every step, first hit wins:

    1. manual    an assignment made by a human, which always stands
    2. ip        the source parses as an IP that NetBox knows
    3. hostname  exact name match, case-insensitive
    4. fqdn      exact match after removing a configured domain suffix

Anything else stays unassigned and is listed as such. Similarity is used only
to order the suggestions offered next to an unassigned source; it never assigns
anything by itself.

One caveat that decides how well rule 2 works in a given installation: with a
central syslog relay in front of Graylog, every message carries the relay
address, and the IP rule matches nothing useful. The source field then has to
carry the host name, which is what rules 3 and 4 are for.
"""

import logging
import re

logger = logging.getLogger(__name__)

_IPV4_RE = re.compile(r'^\d{1,3}(\.\d{1,3}){3}$')


def _looks_like_ip(value):
    if _IPV4_RE.match(value):
        return True
    return ':' in value and not value.startswith('[')


def short_name(value, suffixes):
    """
    Reduce an FQDN to its short name using the configured suffixes only.

    Blindly cutting at the first dot would be wrong: a host legitimately named
    'db.prod' in NetBox would never match again.
    """
    lowered = value.lower().rstrip('.')
    for suffix in suffixes:
        if lowered.endswith('.' + suffix):
            return lowered[:-(len(suffix) + 1)]
    return lowered


class MatchIndex:
    """
    Lookup tables built once per poll.

    Building these costs three queries. Matching a thousand sources against
    them afterwards costs nothing, which is what keeps the poll cheap.
    """

    def __init__(self, suffixes=None):
        self.suffixes = suffixes or []
        self.by_ip = {}
        self.by_name = {}
        self._ambiguous_names = set()
        self._ambiguous_ips = set()
        self.build()

    # -- construction ----------------------------------------------------

    def build(self):
        self._add_objects('dcim', 'Device')
        self._add_objects('virtualization', 'VirtualMachine')
        self._add_ips()

    def _add_objects(self, app_label, model_name):
        from django.apps import apps

        try:
            model = apps.get_model(app_label, model_name)
        except Exception:
            return

        try:
            rows = model.objects.filter(name__isnull=False).only('id', 'name')
            for obj in rows.iterator(chunk_size=2000):
                name = (obj.name or '').strip().lower()
                if not name:
                    continue
                self._register_name(name, model, obj.pk)
                trimmed = short_name(name, self.suffixes)
                if trimmed != name:
                    self._register_name(trimmed, model, obj.pk)
        except Exception:
            logger.debug('netbox_force: indexing %s.%s failed',
                         app_label, model_name, exc_info=True)

    def _register_name(self, name, model, pk):
        existing = self.by_name.get(name)
        if existing is not None and existing != (model, pk):
            # Two NetBox objects answer to the same name. Assigning either one
            # would be a coin flip, so neither is assigned.
            self._ambiguous_names.add(name)
            return
        self.by_name[name] = (model, pk)

    def _add_ips(self):
        from django.apps import apps

        try:
            IPAddress = apps.get_model('ipam', 'IPAddress')
        except Exception:
            return

        try:
            # Deliberately no .only() here: the generic relation needs both the
            # type and the id, and combining only() with select_related on the
            # same field is fragile across Django versions.
            rows = (IPAddress.objects
                    .filter(assigned_object_id__isnull=False)
                    .select_related('assigned_object_type'))
            for ip in rows.iterator(chunk_size=2000):
                owner = self._ip_owner(ip)
                if owner is None:
                    continue
                address = str(ip.address).split('/')[0].strip().lower()
                if not address:
                    continue
                existing = self.by_ip.get(address)
                if existing is not None and existing != owner:
                    self._ambiguous_ips.add(address)
                    continue
                self.by_ip[address] = owner
        except Exception:
            logger.debug('netbox_force: indexing IP addresses failed',
                         exc_info=True)

    @staticmethod
    def _ip_owner(ip):
        """
        Resolve an IPAddress to the device or VM behind it.

        An address is assigned to an Interface or VMInterface, not to the
        device directly, so one hop is needed.
        """
        from django.apps import apps

        try:
            iface = ip.assigned_object
        except Exception:
            return None
        if iface is None:
            return None

        device = getattr(iface, 'device', None)
        if device is not None:
            try:
                return apps.get_model('dcim', 'Device'), device.pk
            except Exception:
                return None

        vm = getattr(iface, 'virtual_machine', None)
        if vm is not None:
            try:
                return apps.get_model('virtualization', 'VirtualMachine'), vm.pk
            except Exception:
                return None
        return None

    # -- matching --------------------------------------------------------

    def match(self, source_name):
        """
        Returns (model, pk, method) or (None, None, 'none').

        Never raises and never guesses.
        """
        value = (source_name or '').strip().lower().rstrip('.')
        if not value:
            return None, None, 'none'

        if _looks_like_ip(value):
            if value in self._ambiguous_ips:
                return None, None, 'none'
            hit = self.by_ip.get(value)
            if hit:
                return hit[0], hit[1], 'ip'
            return None, None, 'none'

        if value in self._ambiguous_names:
            return None, None, 'none'

        hit = self.by_name.get(value)
        if hit:
            return hit[0], hit[1], 'hostname'

        trimmed = short_name(value, self.suffixes)
        if trimmed != value and trimmed not in self._ambiguous_names:
            hit = self.by_name.get(trimmed)
            if hit:
                return hit[0], hit[1], 'fqdn'

        return None, None, 'none'


# =============================================================================
# SUGGESTIONS FOR UNASSIGNED SOURCES
# =============================================================================

def _similarity(left, right):
    """
    Ratio in 0..1, used exclusively to order suggestions.

    Never call this to decide an assignment. See the module docstring.
    """
    from difflib import SequenceMatcher
    return SequenceMatcher(None, left, right).ratio()


def suggest_candidates(source_name, limit=5):
    """
    Candidates for an unassigned source, each with the reason it is a
    candidate.

    The reason is the point. "Shares the first two name segments" is something
    a human can check in a second; "87%" is not.
    """
    value = (source_name or '').strip().lower().rstrip('.')
    if not value:
        return []

    from django.apps import apps

    candidates = []
    prefix = _prefix(value)

    for app_label, model_name in (('dcim', 'Device'),
                                  ('virtualization', 'VirtualMachine')):
        try:
            model = apps.get_model(app_label, model_name)
        except Exception:
            continue
        try:
            queryset = model.objects.filter(name__isnull=False)
            if prefix:
                queryset = queryset.filter(name__istartswith=prefix)
            else:
                queryset = queryset.filter(name__icontains=value[:6])
            for obj in queryset.only('id', 'name')[:50]:
                name = (obj.name or '').strip()
                if not name:
                    continue
                candidates.append({
                    'model': model,
                    'pk': obj.pk,
                    'name': name,
                    'label': f'{app_label}.{model_name.lower()}',
                    'reason': 'prefix' if prefix else 'contains',
                    'score': _similarity(value, name.lower()),
                })
        except Exception:
            logger.debug('netbox_force: suggesting from %s failed',
                         model_name, exc_info=True)

    candidates.sort(key=lambda item: item['score'], reverse=True)
    return candidates[:limit]


def _prefix(value):
    """
    The stable part of a host name: everything up to the last separator.

    'srv-web-01' yields 'srv-web-', which finds the siblings without pretending
    to know which sibling is right.
    """
    for separator in ('-', '_', '.'):
        if separator in value:
            head = value.rsplit(separator, 1)[0]
            if len(head) >= 3:
                return head + separator
    return ''
