"""
wizard_prefix.py — Prefix anlegen
Generiert für: Meine Organisation
NetBox Custom Script | commit_default = False (Dry-Run Standard)
"""

import netaddr
from extras.scripts import Script, StringVar, ChoiceVar, ObjectVar
from django.utils.safestring import mark_safe
from ipam.models import Prefix, Role, VLAN
from dcim.models import Site
from tenancy.models import Tenant

name = "Netzwerk-Wizards"

STATUS_CHOICES_PREFIX = [
    ("active",      "Aktiv"),
    ("container",   "Container (Aggregat)"),
    ("reserved",    "Reserviert"),
    ("deprecated",  "Veraltet"),
]


class PrefixAnlegen(Script):

    class Meta:
        name        = "Prefix anlegen"
        description = (
            "Legt ein neues IP-Prefix (Subnetz) in NetBox an. "
            "Standard: Dry-Run — Commit-Checkbox aktivieren um zu speichern."
        )
        commit_default = False

    prefix = StringVar(
        label       = "Prefix (CIDR)",
        description = "Netzadresse mit Präfixlänge, z.B. 192.168.10.0/24 oder 10.0.0.0/8",
        required    = True,
    )
    status = ChoiceVar(
        label   = "Status",
        choices = STATUS_CHOICES_PREFIX,
        default = "active",
    )
    role = ObjectVar(
        label       = "Rolle",
        model       = Role,
        required    = True,
        description = "Funktionale Rolle des Prefixes (z.B. Server, Management, DMZ)",
    )
    tenant = ObjectVar(
        label       = "Mandant",
        model       = Tenant,
        required    = False,
        description = "Zugehöriger Mandant (optional)",
    )
    site = ObjectVar(
        label       = "Standort",
        model       = Site,
        required    = False,
        description = "Standort dem dieses Prefix zugeordnet ist (optional)",
    )
    vlan = ObjectVar(
        label       = "VLAN",
        model       = VLAN,
        required    = False,
        description = "Zugehöriges VLAN (optional)",
    )
    description = StringVar(
        label       = "Beschreibung",
        description = "Beschreibung des Prefixes",
        required    = False,
    )
    changelog_message = StringVar(
        label       = "Changelog-Nachricht",
        description = "Pflichtfeld: Änderungsgrund (mind. 5 Zeichen)",
        required    = True,
    )

    def run(self, data, commit):
        # ── 1. Changelog-Prüfung ──────────────────────────────────────────────
        changelog = (data.get("changelog_message") or "").strip()
        if len(changelog) < 5:
            self.log_failure(
                "Changelog-Nachricht muss mindestens 5 Zeichen lang sein."
            )
            return

        # ── 2. CIDR-Validierung + Normalisierung ──────────────────────────────
        prefix_str = (data.get("prefix") or "").strip()
        if "/" not in prefix_str:
            self.log_failure(
                f"Bitte Präfixlänge angeben (CIDR-Format), z.B. {prefix_str}/24"
            )
            return
        try:
            network = netaddr.IPNetwork(prefix_str, implicit_prefix=False)
            normalized = str(network.cidr)
            if prefix_str != normalized:
                self.log_info(
                    f"Prefix normalisiert: {prefix_str} → {normalized} "
                    "(Host-Bits auf 0 gesetzt)"
                )
            prefix_str = normalized
        except (netaddr.AddrFormatError, ValueError) as exc:
            self.log_failure(f"Ungültiges Prefix '{data['prefix']}': {exc}")
            return

        # ── 3. Überlappungsprüfung (Warnung, kein Abbruch) ────────────────────
        overlapping = Prefix.objects.filter(prefix__net_overlaps=prefix_str)
        if overlapping.exists():
            overlap_str = ", ".join(str(p.prefix) for p in overlapping[:10])
            extra = f" (+{overlapping.count() - 10} weitere)" if overlapping.count() > 10 else ""
            self.log_warning(
                f"Überlappende Prefixes gefunden: {overlap_str}{extra}"
            )

        # ── 4. Parent-Container-Check ─────────────────────────────────────────
        parent = (
            Prefix.objects
            .filter(prefix__net_contains=prefix_str, status="container")
            .order_by("-prefix__net_mask_length")
            .first()
        )
        if parent:
            self.log_info(f"Übergeordneter Container: {parent.prefix}")
        else:
            parent_any = (
                Prefix.objects
                .filter(prefix__net_contains=prefix_str)
                .order_by("-prefix__net_mask_length")
                .first()
            )
            if parent_any:
                self.log_info(f"Übergeordnetes Prefix: {parent_any.prefix}")

        # ── 5. Objekt anlegen ─────────────────────────────────────────────────
        if commit:
            kwargs = {
                "prefix":      prefix_str,
                "status":      data["status"],
                "description": (data.get("description") or ""),
            }
            if data.get("role"):
                kwargs["role"] = data["role"]
            if data.get("tenant"):
                kwargs["tenant"] = data["tenant"]
            if data.get("site"):
                kwargs["site"] = data["site"]
            if data.get("vlan"):
                kwargs["vlan"] = data["vlan"]

            p = Prefix(**kwargs)
            p.save()

            url = p.get_absolute_url()
            self.log_success(
                f"Prefix <a href='{url}'>{p.prefix}</a> erfolgreich angelegt."
            )
            return mark_safe(f'<a href="{url}">{p.prefix}</a>')

        else:
            self.log_info(
                f"Dry-Run — Prefix {prefix_str} würde angelegt werden. "
                "Aktiviere 'Commit' um die Änderung zu speichern."
            )
