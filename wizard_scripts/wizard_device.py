"""
wizard_device.py — Gerät anlegen
Generiert für: Meine Organisation
NetBox Custom Script | commit_default = False (Dry-Run Standard)
"""

from extras.scripts import Script, StringVar, ChoiceVar, ObjectVar
from django.utils.safestring import mark_safe
from dcim.models import Device, DeviceType, DeviceRole, Site
from tenancy.models import Tenant

name = "Netzwerk-Wizards"

STATUS_CHOICES_DEVICE = [
    ("active",           "Aktiv"),
    ("planned",          "Geplant"),
    ("staged",           "Staged"),
    ("failed",           "Defekt"),
    ("offline",          "Offline"),
    ("inventory",        "Inventar"),
    ("decommissioning",  "In Stilllegung"),
]


class GeraetAnlegen(Script):

    class Meta:
        name        = "Gerät anlegen"
        description = (
            "Legt ein neues Gerät (Device) in NetBox an. "
            "Standard: Dry-Run — Commit-Checkbox aktivieren um zu speichern."
        )
        commit_default = False

    device_name = StringVar(
        label       = "Gerätename (Hostname)",
        description = "Hostname des Geräts — keine Unterstriche, keine Leerzeichen",
        required    = True,
    )
    device_role = ObjectVar(
        label       = "Geräterolle",
        model       = DeviceRole,
        required    = True,
        description = "Funktionale Rolle des Geräts (z.B. Switch, Router, Server)",
    )
    device_type = ObjectVar(
        label       = "Gerätetyp",
        model       = DeviceType,
        required    = True,
        description = "Hersteller und Modell des Geräts",
    )
    site = ObjectVar(
        label       = "Standort",
        model       = Site,
        required    = True,
        description = "Standort des Geräts",
    )
    status = ChoiceVar(
        label   = "Status",
        choices = STATUS_CHOICES_DEVICE,
        default = "active",
    )
    tenant = ObjectVar(
        label       = "Mandant",
        model       = Tenant,
        required    = False,
        description = "Zugehöriger Mandant (optional)",
    )
    serial = StringVar(
        label       = "Seriennummer",
        description = "Seriennummer des Geräts (optional)",
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

        device_name = (data.get("device_name") or "").strip()

        # ── 2. Namenskonventionen ─────────────────────────────────────────────
        if "_" in device_name:
            self.log_failure(
                f"Gerätename '{device_name}' enthält Unterstriche. "
                "Unterstriche sind in Gerätenamen nicht erlaubt."
            )
            return

        if " " in device_name:
            self.log_failure(
                f"Gerätename '{device_name}' enthält Leerzeichen. "
                "Leerzeichen sind in Gerätenamen nicht erlaubt."
            )
            return

        # pattern=None → keine Regex-Prüfung
        # min_hyphens=0 → keine Mindestanzahl Bindestriche

        # ── 3. Duplikat-Check (Warnung, kein Abbruch) ─────────────────────────
        if Device.objects.filter(name=device_name).exists():
            self.log_warning(
                f"Ein Gerät mit dem Namen '{device_name}' existiert bereits in NetBox."
            )

        # ── 4. Objekt anlegen ─────────────────────────────────────────────────
        if commit:
            kwargs = {
                "name":        device_name,
                "device_role": data["device_role"],
                "device_type": data["device_type"],
                "site":        data["site"],
                "status":      data["status"],
            }
            if data.get("tenant"):
                kwargs["tenant"] = data["tenant"]
            if (data.get("serial") or "").strip():
                kwargs["serial"] = data["serial"].strip()

            device = Device(**kwargs)
            device.save()

            url = device.get_absolute_url()
            self.log_success(
                f"Gerät <a href='{url}'>{device.name}</a> erfolgreich angelegt."
            )
            self.log_info(
                "Nächste Schritte: Interfaces anlegen → IP-Adressen zuweisen"
            )
            return mark_safe(f'<a href="{url}">{device.name}</a>')

        else:
            self.log_info(
                f"Dry-Run — Gerät '{device_name}' würde angelegt werden. "
                "Aktiviere 'Commit' um die Änderung zu speichern."
            )
