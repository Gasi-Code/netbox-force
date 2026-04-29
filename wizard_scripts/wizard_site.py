"""
wizard_site.py — Standort anlegen
Generiert für: Meine Organisation
NetBox Custom Script | commit_default = False (Dry-Run Standard)
"""

import re
from extras.scripts import Script, StringVar, ChoiceVar, ObjectVar
from django.utils.safestring import mark_safe
from dcim.models import Site, Region, SiteGroup
from tenancy.models import Tenant

name = "Netzwerk-Wizards"

STATUS_CHOICES_SITE = [
    ("active",           "Aktiv"),
    ("planned",          "Geplant"),
    ("staging",          "In Einrichtung"),
    ("decommissioning",  "In Stilllegung"),
    ("retired",          "Stillgelegt"),
]


class SiteAnlegen(Script):

    class Meta:
        name        = "Standort anlegen"
        description = (
            "Legt einen neuen Standort (Site) in NetBox an. "
            "Standard: Dry-Run — Commit-Checkbox aktivieren um zu speichern."
        )
        commit_default = False

    site_name = StringVar(
        label       = "Standort-Name",
        description = "Name des Standorts",
        required    = True,
    )
    status = ChoiceVar(
        label   = "Status",
        choices = STATUS_CHOICES_SITE,
        default = "active",
    )
    tenant = ObjectVar(
        label       = "Mandant",
        model       = Tenant,
        required    = True,
        description = "Zugehöriger Mandant",
    )
    region = ObjectVar(
        label       = "Region",
        model       = Region,
        required    = False,
        description = "Geografische Region (optional)",
    )
    group = ObjectVar(
        label       = "Standort-Gruppe",
        model       = SiteGroup,
        required    = False,
        description = "Standort-Gruppe (optional)",
    )
    physical_address = StringVar(
        label       = "Anschrift",
        description = "Physische Anschrift des Standorts (optional)",
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

        site_name = (data.get("site_name") or "").strip()

        # ── 2. Namenskonvention (kein Regex-Pattern konfiguriert) ─────────────
        # pattern=None → keine weiteren Konventionsprüfungen

        # ── 3. Duplikat-Check (Warnung, kein Abbruch) ─────────────────────────
        if Site.objects.filter(name=site_name).exists():
            self.log_warning(
                f"Ein Standort mit dem Namen '{site_name}' existiert bereits. "
                "Bitte prüfen, ob wirklich ein neuer Standort angelegt werden soll."
            )

        # ── 4. Slug auto-generieren ───────────────────────────────────────────
        slug = site_name.lower()
        slug = re.sub(r"[^\w-]", "-", slug)        # Sonderzeichen → Bindestrich
        slug = re.sub(r"-{2,}", "-", slug).strip("-")  # Doppelte -- entfernen
        slug = slug[:50]                             # Max. 50 Zeichen
        self.log_info(f"Generierter Slug: '{slug}'")

        # ── 5. Objekt anlegen ─────────────────────────────────────────────────
        if commit:
            kwargs = {
                "name":   site_name,
                "slug":   slug,
                "status": data["status"],
            }
            if data.get("tenant"):
                kwargs["tenant"] = data["tenant"]
            if data.get("region"):
                kwargs["region"] = data["region"]
            if data.get("group"):
                kwargs["group"] = data["group"]
            if data.get("physical_address", "").strip():
                kwargs["physical_address"] = data["physical_address"].strip()

            site = Site(**kwargs)
            site.save()

            url = site.get_absolute_url()
            self.log_success(
                f"Standort <a href='{url}'>{site.name}</a> erfolgreich angelegt."
            )
            return mark_safe(f'<a href="{url}">{site.name}</a>')

        else:
            self.log_info(
                f"Dry-Run — Standort '{site_name}' (Slug: '{slug}') würde angelegt werden. "
                "Aktiviere 'Commit' um die Änderung zu speichern."
            )
