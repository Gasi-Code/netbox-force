"""
wizard_vlan.py — VLAN anlegen
Generiert für: Meine Organisation
NetBox Custom Script | commit_default = False (Dry-Run Standard)
"""

from extras.scripts import Script, StringVar, IntegerVar, ChoiceVar, ObjectVar
from django.utils.safestring import mark_safe
from ipam.models import VLAN, VLANGroup, Role
from tenancy.models import Tenant

name = "Netzwerk-Wizards"

STATUS_CHOICES_VLAN = [
    ("active",     "Aktiv"),
    ("reserved",   "Reserviert"),
    ("deprecated", "Veraltet"),
]


class VLANAnlegen(Script):

    class Meta:
        name        = "VLAN anlegen"
        description = (
            "Legt ein neues VLAN in NetBox an. "
            "Standard: Dry-Run — Commit-Checkbox aktivieren um zu speichern."
        )
        commit_default = False

    vid = IntegerVar(
        label       = "VLAN-ID",
        description = "VLAN-ID (1–4094)",
        required    = True,
        min_value   = 1,
        max_value   = 4094,
    )
    vlan_name = StringVar(
        label       = "VLAN-Name",
        description = "Name des VLANs",
        required    = True,
    )
    group = ObjectVar(
        label       = "VLAN-Gruppe",
        model       = VLANGroup,
        required    = True,
        description = "VLAN-Gruppe der das VLAN angehört",
    )
    status = ChoiceVar(
        label   = "Status",
        choices = STATUS_CHOICES_VLAN,
        default = "active",
    )
    role = ObjectVar(
        label       = "Rolle",
        model       = Role,
        required    = True,
        description = "Funktionale Rolle des VLANs (z.B. Server, Client, Management)",
    )
    tenant = ObjectVar(
        label       = "Mandant",
        model       = Tenant,
        required    = False,
        description = "Zugehöriger Mandant (optional)",
    )
    description = StringVar(
        label       = "Beschreibung",
        description = "Beschreibung des VLANs",
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

        vid       = data["vid"]
        vlan_name = (data.get("vlan_name") or "").strip()
        group     = data.get("group")

        # ── 2. Namenskonvention VLAN (kein Regex-Pattern konfiguriert) ─────────
        # pattern=None → keine weiteren Konventionsprüfungen

        # ── 3. Duplikat-Check (VLAN-ID in Gruppe) ─────────────────────────────
        dup_qs = VLAN.objects.filter(vid=vid)
        if group:
            dup_qs = dup_qs.filter(group=group)
        if dup_qs.exists():
            existing = dup_qs.first()
            self.log_failure(
                f"VLAN-ID {vid} existiert bereits"
                + (f" in Gruppe '{group.name}'" if group else "")
                + f": '{existing.name}'"
            )
            return

        # ── 4. Objekt anlegen ─────────────────────────────────────────────────
        if commit:
            kwargs = {
                "vid":         vid,
                "name":        vlan_name,
                "status":      data["status"],
                "description": (data.get("description") or ""),
            }
            if group:
                kwargs["group"] = group
            if data.get("role"):
                kwargs["role"] = data["role"]
            if data.get("tenant"):
                kwargs["tenant"] = data["tenant"]

            vlan = VLAN(**kwargs)
            vlan.save()

            url = vlan.get_absolute_url()
            self.log_success(
                f"VLAN <a href='{url}'>{vlan.vid} – {vlan.name}</a> erfolgreich angelegt."
            )
            return mark_safe(f'<a href="{url}">VLAN {vlan.vid} – {vlan.name}</a>')

        else:
            self.log_info(
                f"Dry-Run — VLAN {vid} ('{vlan_name}') würde angelegt werden. "
                "Aktiviere 'Commit' um die Änderung zu speichern."
            )
