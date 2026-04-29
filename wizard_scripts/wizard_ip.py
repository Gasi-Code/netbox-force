"""
wizard_ip.py — IP-Adresse anlegen
Generiert für: Meine Organisation
NetBox Custom Script | commit_default = False (Dry-Run Standard)
"""

import netaddr
from extras.scripts import Script, StringVar, ChoiceVar, ObjectVar
from django.utils.safestring import mark_safe
from ipam.models import IPAddress, Prefix
from tenancy.models import Tenant

name = "Netzwerk-Wizards"

STATUS_CHOICES_IP = [
    ("active",     "Aktiv"),
    ("reserved",   "Reserviert"),
    ("deprecated", "Veraltet"),
    ("dhcp",       "DHCP"),
    ("slaac",      "SLAAC"),
]

ROLE_CHOICES_IP = [
    ("",          "keine"),
    ("loopback",  "Loopback"),
    ("secondary", "Secondary"),
    ("anycast",   "Anycast"),
    ("vip",       "VIP"),
    ("vrrp",      "VRRP"),
    ("hsrp",      "HSRP"),
    ("carp",      "CARP"),
    ("glbp",      "GLBP"),
]


class IPAnlegen(Script):

    class Meta:
        name        = "IP-Adresse anlegen"
        description = (
            "Legt eine neue IP-Adresse in NetBox an. "
            "Standard: Dry-Run — Commit-Checkbox aktivieren um zu speichern."
        )
        commit_default = False

    address = StringVar(
        label       = "IP-Adresse (CIDR)",
        description = "IP-Adresse mit Präfixlänge, z.B. 192.168.1.10/24 oder 2001:db8::1/64",
        required    = True,
    )
    dns_name = StringVar(
        label       = "DNS-Name",
        description = "Vollständiger Hostname / FQDN, z.B. server01.example.com",
        required    = False,
    )
    description = StringVar(
        label       = "Beschreibung",
        description = "Wofür wird diese IP verwendet?",
        required    = False,
    )
    status = ChoiceVar(
        label   = "Status",
        choices = STATUS_CHOICES_IP,
        default = "active",
    )
    role = ChoiceVar(
        label       = "Rolle",
        choices     = ROLE_CHOICES_IP,
        description = "Funktionale Rolle der IP-Adresse (optional)",
        required    = False,
        default     = "",
    )
    tenant = ObjectVar(
        label       = "Mandant",
        model       = Tenant,
        required    = False,
        description = "Zugehöriger Mandant (optional)",
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

        # ── 2. CIDR-Validierung ───────────────────────────────────────────────
        address_str = (data.get("address") or "").strip()
        if "/" not in address_str:
            self.log_failure(
                f"Bitte Präfixlänge angeben (CIDR-Format), z.B. {address_str}/24"
            )
            return
        try:
            netaddr.IPNetwork(address_str, implicit_prefix=False)
        except (netaddr.AddrFormatError, ValueError) as exc:
            self.log_failure(f"Ungültige IP-Adresse '{address_str}': {exc}")
            return

        # ── 3. DNS-Name Konvention ────────────────────────────────────────────
        dns_name = (data.get("dns_name") or "").strip()
        if dns_name:
            if "_" in dns_name:
                self.log_failure(
                    f"DNS-Name '{dns_name}' enthält Unterstriche — "
                    "DNS-Namen dürfen keine Unterstriche enthalten."
                )
                return
            if " " in dns_name:
                self.log_failure(
                    f"DNS-Name '{dns_name}' enthält Leerzeichen — "
                    "DNS-Namen dürfen keine Leerzeichen enthalten."
                )
                return

        # ── 4. Duplikat-Check ─────────────────────────────────────────────────
        if IPAddress.objects.filter(address=address_str).exists():
            self.log_failure(
                f"IP-Adresse {address_str} ist bereits in NetBox vorhanden."
            )
            return

        # ── 5. Parent-Prefix-Check ────────────────────────────────────────────
        parent = Prefix.objects.filter(
            prefix__net_contains_or_equals=address_str
        ).first()
        if parent:
            self.log_info(
                f"Übergeordnetes Prefix gefunden: {parent.prefix} "
                f"(Status: {parent.get_status_display()})"
            )
        else:
            self.log_warning(
                f"Kein übergeordnetes Prefix für {address_str} gefunden. "
                "Bitte sicherstellen, dass ein passendes Prefix existiert."
            )

        # ── 6. Objekt anlegen ─────────────────────────────────────────────────
        if commit:
            kwargs = {
                "address":     address_str,
                "status":      data["status"],
                "description": (data.get("description") or ""),
            }
            if data.get("role"):
                kwargs["role"] = data["role"]
            if data.get("tenant"):
                kwargs["tenant"] = data["tenant"]
            if dns_name:
                kwargs["dns_name"] = dns_name

            ip = IPAddress(**kwargs)
            ip.save()

            url = ip.get_absolute_url()
            self.log_success(
                f"IP-Adresse <a href='{url}'>{ip.address}</a> erfolgreich angelegt."
            )
            return mark_safe(f'<a href="{url}">{ip.address}</a>')

        else:
            self.log_info(
                f"Dry-Run — IP-Adresse {address_str} würde angelegt werden. "
                "Aktiviere 'Commit' um die Änderung zu speichern."
            )
