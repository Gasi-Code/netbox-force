# netbox-force

NetBox-Plugin das Policies bei Objekt-Änderungen erzwingt.

**Aktuell enthaltene Features:**
- **Changelog Enforcer** — Erzwingt eine Begründung im Changelog-Feld bei jeder Erstellung, Bearbeitung oder Löschung von Objekten

## Kompatibilität

- **NetBox:** 4.0.0+
- **Python:** 3.10+

## Installation

```bash
# In der NetBox venv:
source /opt/netbox/venv/bin/activate

# Plugin installieren (editable mode für einfache Updates)
pip install -e /pfad/zu/netbox-force/

# Oder direkt aus dem Repository:
pip install git+https://github.com/Netbox-Force/netbox-force.git
```

## Konfiguration

In `/opt/netbox/netbox/netbox/configuration.py`:

```python
PLUGINS = [
    'netbox_force',
]

PLUGINS_CONFIG = {
    'netbox_force': {
        'min_length': 10,                # Mindestlänge der Changelog-Nachricht
        'exempt_users': [                # User die keine Changelog-Pflicht haben
            'automation',
            'monitoring',
            'netbox',
        ],
        'enforce_on_delete': True,       # Auch beim Löschen Changelog erzwingen
        'extra_exempt_models': [],       # Zusätzliche Modelle ausschließen (z.B. 'myplugin.mymodel')
    },
}
```

## Neustart

```bash
sudo systemctl restart netbox netbox-rq
```

## Funktionsweise

- **Middleware** speichert den HTTP-Request in Thread-Local-Storage
- **Signal Handler** (`pre_save`, `pre_delete`) prüfen bei jeder Änderung ob ein Changelog-Kommentar vorhanden ist
- Fehlt der Kommentar oder ist er zu kurz → `ValidationError` → NetBox zeigt Fehlermeldung
- Funktioniert sowohl für Browser-UI als auch REST-API (JSON-Body mit `changelog_message`)

### Ausnahmen

- Modelle in `EXEMPT_MODELS` (Auth, Sessions, NetBox-interne Objekte)
- Modelle in `extra_exempt_models` (konfigurierbar)
- User in `exempt_users` (z.B. Automation-Accounts)
- Nicht-authentifizierte Requests
- Management-Commands (kein HTTP-Kontext)
- Reine Timestamp-Änderungen (automatische Felder)

## Migration von der alten Lösung

Falls zuvor `custom_signals.py` direkt in NetBox eingepflegt war:

1. `/opt/netbox/netbox/netbox/custom_signals.py` löschen
2. In `settings.py` alle Referenzen auf `custom_signals` und die alte Middleware entfernen
3. Plugin wie oben beschrieben installieren und konfigurieren
4. `sudo systemctl restart netbox netbox-rq`
