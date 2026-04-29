# NetBox Berechtigungskonzept — Netzwerk-Wizards

Anleitung zur Einrichtung der Berechtigungsgruppen für die Custom Scripts.

---

## Übersicht der Gruppen

| Gruppe | Beschreibung |
|--------|--------------|
| `wizard-only` | Darf Custom Scripts ausführen, keine direkten CRUD-Rechte auf NetBox-Objekte |
| `standard-user` | Scripts ausführen + eigene Objekte lesen und bearbeiten |
| `admin` | Vollzugriff auf alle NetBox-Funktionen |

---

## Gruppe: `wizard-only`

Für Benutzer die **ausschließlich** über die Wizard-Scripts arbeiten sollen
und keine direkten Berechtigungen in der NetBox-Oberfläche erhalten sollen.

### Benötigte Permissions

| App | Model | Aktionen | Hinweis |
|-----|-------|----------|---------|
| `extras` | `script` | `can_run` | Scripts ausführen |
| `dcim` | `site` | `view` | Standort-Auswahl im Formular |
| `dcim` | `device` | `view` | Gerät-Suche im Formular |
| `dcim` | `devicetype` | `view` | Gerätetyp-Auswahl |
| `dcim` | `devicerole` | `view` | Geräterolle-Auswahl |
| `dcim` | `region` | `view` | Regionen-Auswahl |
| `dcim` | `sitegroup` | `view` | Standortgruppen-Auswahl |
| `ipam` | `ipaddress` | `view` | IP-Duplikat-Check |
| `ipam` | `prefix` | `view` | Prefix-Auswahl + Überlappungscheck |
| `ipam` | `vlan` | `view` | VLAN-Auswahl + Duplikat-Check |
| `ipam` | `vlangroup` | `view` | VLAN-Gruppen-Auswahl |
| `ipam` | `role` | `view` | Rollen-Auswahl |
| `circuits` | `circuit` | `view` | Circuit-Duplikat-Check |
| `circuits` | `circuittype` | `view` | Circuit-Typ-Auswahl |
| `circuits` | `provider` | `view` | Provider-Auswahl |
| `tenancy` | `tenant` | `view` | Mandanten-Auswahl |

> **Hinweis:** `wizard-only` Benutzer können nur über Scripts anlegen —
> die Scripts laufen mit den Rechten des ausführenden Prozesses (netbox-user),
> nicht mit den Rechten des eingeloggten Benutzers.
> Für echte objektbasierte Rechte → Gruppe `standard-user` verwenden.

---

## Gruppe: `standard-user`

Für Benutzer die sowohl Scripts als auch die NetBox-Oberfläche nutzen.

### Benötigte Permissions

Alles aus `wizard-only` **plus**:

| App | Model | Aktionen | Hinweis |
|-----|-------|----------|---------|
| `dcim` | `site` | `add`, `change`, `view` | Standorte verwalten |
| `dcim` | `device` | `add`, `change`, `view` | Geräte verwalten |
| `ipam` | `ipaddress` | `add`, `change`, `view` | IPs verwalten |
| `ipam` | `prefix` | `add`, `change`, `view` | Prefixes verwalten |
| `ipam` | `vlan` | `add`, `change`, `view` | VLANs verwalten |
| `circuits` | `circuit` | `add`, `change`, `view` | Circuits verwalten |
| `circuits` | `circuittermination` | `add`, `change`, `view` | Terminierungen |
| `tenancy` | `tenant` | `view` | Mandanten lesen |

> **Löschen** (`delete`) sollte für Standard-User **nicht** vergeben werden.
> Löschvorgänge sollten nur durch Admins erfolgen.

---

## Gruppe: `admin`

Vollzugriff. Wird über den Django-Admin-Flag (`is_staff`) oder direkt über
NetBox-Berechtigungen mit `*` (alle Aktionen, alle Objekte) konfiguriert.

### Empfohlene Konfiguration

```
Alle Aktionen: add, change, delete, view
Für alle relevanten Apps: dcim, ipam, circuits, tenancy, extras
```

---

## Einrichtung in NetBox

### 1. Gruppe anlegen

**Admin → Authentication → Groups → Add**

- Name: `wizard-only` / `standard-user` / `admin`

### 2. Permissions vergeben

**Admin → Authentication → Permissions → Add**

- Name: z.B. `wizard-only: Script ausführen`
- Object type: `extras | script`
- Actions: `Can run script`
- Constraints: leer (gilt für alle Scripts)

Dann der Gruppe zuweisen: **Group → Permissions → ausgewählte Permissions hinzufügen**

### 3. Benutzer der Gruppe zuordnen

**Admin → Authentication → Users → [Benutzer] → Groups**

---

## NetBox Token-basierter API-Zugriff (optional)

Für Automationssysteme die Scripts per API ausführen:

```bash
# Script per API ausführen
curl -X POST https://netbox.example.com/api/extras/scripts/wizard_ip.IPAnlegen/ \
  -H "Authorization: Token DEIN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "address": "10.0.1.100/24",
      "status": "active",
      "changelog_message": "Automatisch angelegt via API"
    },
    "commit": true
  }'
```

---

## Sicherheitshinweise

1. **Principle of Least Privilege**: Jeder Benutzer erhält nur die Rechte die er benötigt
2. **Scripts laufen im NetBox-Kontext**: Alle Änderungen durch Scripts werden mit dem
   NetBox-Systembenutzer durchgeführt — nicht mit dem eingeloggten Benutzer
3. **Changelog-Pflicht**: Alle Wizard-Scripts erzwingen eine Changelog-Nachricht
   (mind. 5 Zeichen) — dies ergänzt das Berechtigungskonzept durch Nachvollziehbarkeit
4. **Dry-Run Standard**: Alle Scripts starten im Dry-Run-Modus (`commit_default = False`),
   Benutzer müssen explizit die Commit-Checkbox aktivieren
