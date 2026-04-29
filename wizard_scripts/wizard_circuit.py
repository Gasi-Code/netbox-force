"""
wizard_circuit.py — Circuit anlegen
Generiert für: Meine Organisation
NetBox Custom Script | commit_default = False (Dry-Run Standard)
"""

from extras.scripts import Script, StringVar, ChoiceVar, ObjectVar
from django.utils.safestring import mark_safe
from circuits.models import Circuit, CircuitType, CircuitTermination, Provider
from dcim.models import Site

name = "Netzwerk-Wizards"

STATUS_CHOICES_CIRCUIT = [
    ("active",           "Aktiv"),
    ("planned",          "Geplant"),
    ("provisioning",     "In Einrichtung"),
    ("offline",          "Offline"),
    ("deprovisioning",   "In Kündigung"),
    ("decommissioned",   "Stillgelegt"),
]


class CircuitAnlegen(Script):

    class Meta:
        name        = "Circuit anlegen"
        description = (
            "Legt eine neue WAN/Circuit-Verbindung in NetBox an. "
            "Standard: Dry-Run — Commit-Checkbox aktivieren um zu speichern."
        )
        commit_default = False

    cid = StringVar(
        label       = "Circuit-ID",
        description = "Circuit-ID / Leitungsbezeichnung des Providers",
        required    = True,
    )
    provider = ObjectVar(
        label       = "Provider",
        model       = Provider,
        required    = True,
        description = "Leitungsanbieter / Provider",
    )
    circuit_type = ObjectVar(
        label       = "Circuit-Typ",
        model       = CircuitType,
        required    = True,
        description = "Art der Verbindung (z.B. MPLS, Internet, Dark Fiber)",
    )
    status = ChoiceVar(
        label   = "Status",
        choices = STATUS_CHOICES_CIRCUIT,
        default = "active",
    )
    site_termination_a = ObjectVar(
        label       = "Standort (Seite A)",
        model       = Site,
        required    = True,
        description = "Standort an dem die Leitung terminiert (A-Seite)",
    )
    description = StringVar(
        label       = "Beschreibung",
        description = "Beschreibung der Leitung (optional)",
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

        cid = (data.get("cid") or "").strip()

        # ── 2. Namenskonventionen (pattern=None, forbid_uppercase=False) ───────
        # Keine Regex- oder Großbuchstaben-Prüfung konfiguriert

        # ── 3. Duplikat-Check (Abbruch bei Duplikat) ──────────────────────────
        existing = Circuit.objects.filter(cid=cid).first()
        if existing:
            self.log_failure(
                f"Circuit-ID '{cid}' existiert bereits in NetBox "
                f"(Provider: {existing.provider}, "
                f"Status: {existing.get_status_display()})."
            )
            return

        # ── 4. Objekt anlegen ─────────────────────────────────────────────────
        if commit:
            kwargs = {
                "cid":         cid,
                "provider":    data["provider"],
                "type":        data["circuit_type"],
                "status":      data["status"],
                "description": (data.get("description") or ""),
            }

            circuit = Circuit(**kwargs)
            circuit.save()

            # Terminierung Seite A anlegen
            site_a = data.get("site_termination_a")
            if site_a:
                term_a = CircuitTermination(
                    circuit   = circuit,
                    term_side = "A",
                    site      = site_a,
                )
                term_a.save()
                self.log_info(
                    f"Terminierung Seite A angelegt: {site_a.name}"
                )

            url = circuit.get_absolute_url()
            self.log_success(
                f"Circuit <a href='{url}'>{circuit.cid}</a> erfolgreich angelegt."
            )
            self.log_info(
                "Nächste Schritte: Custom Fields befüllen, "
                "Bandbreite und Commit-Rate eintragen"
            )
            return mark_safe(f'<a href="{url}">{circuit.cid}</a>')

        else:
            self.log_info(
                f"Dry-Run — Circuit '{cid}' würde angelegt werden. "
                "Aktiviere 'Commit' um die Änderung zu speichern."
            )
