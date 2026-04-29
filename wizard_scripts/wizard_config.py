# wizard_config.py
# Automatisch generiert — zeigt die aktive Konfiguration der Wizard-Scripts.
# Änderungen hier haben keinen Effekt — CONFIG im Generator-Prompt anpassen.

ACTIVE_CONFIG = {

    # ── Organisation ──────────────────────────────────────────────────────────
    "org_name":    "Meine Organisation",
    "netbox_url":  "https://netbox.example.com",
    "script_path": "/opt/netbox/netbox/scripts/",

    # ── Changelog ─────────────────────────────────────────────────────────────
    "changelog_required":   True,
    "changelog_min_length": 5,

    # ── Namenskonventionen ────────────────────────────────────────────────────
    "naming": {
        "site": {
            "pattern":     None,   # kein Regex-Pattern aktiv
            "example":     "",
            "description": "Name des Standorts",
        },
        "device": {
            "pattern":          None,   # kein Regex-Pattern aktiv
            "example":          "",
            "description":      "Hostname des Geräts",
            "min_hyphens":      0,      # deaktiviert
            "forbid_underscore": True,  # AKTIV: Unterstriche verboten
            "forbid_spaces":     True,  # AKTIV: Leerzeichen verboten
        },
        "vlan": {
            "pattern":        None,    # kein Regex-Pattern aktiv
            "example":        "",
            "description":    "VLAN-Name",
            "require_hyphen": False,   # deaktiviert
        },
        "circuit": {
            "pattern":         None,   # kein Regex-Pattern aktiv
            "example":         "",
            "description":     "Circuit-Bezeichnung",
            "forbid_uppercase": False, # deaktiviert
        },
        "ip_dns": {
            "forbid_underscore": True,  # AKTIV: Unterstriche verboten
            "forbid_spaces":     True,  # AKTIV: Leerzeichen verboten
            "description":       "DNS-Name / Hostname",
        },
    },

    # ── Pflichtfelder ─────────────────────────────────────────────────────────
    "required_fields": {
        "ip": {
            "address":     True,   # Pflicht
            "status":      True,   # Pflicht
            "dns_name":    False,  # Optional
            "description": False,  # Optional
            "tenant":      False,  # Optional
            "role":        False,  # Optional
        },
        "prefix": {
            "prefix":  True,   # Pflicht
            "status":  True,   # Pflicht
            "role":    True,   # Pflicht
            "tenant":  False,  # Optional
            "site":    False,  # Optional
            "vlan":    False,  # Optional
        },
        "vlan": {
            "vid":    True,   # Pflicht
            "name":   True,   # Pflicht
            "group":  True,   # Pflicht
            "status": True,   # Pflicht
            "role":   True,   # Pflicht
            "tenant": False,  # Optional
        },
        "site": {
            "name":   True,   # Pflicht
            "status": True,   # Pflicht
            "tenant": True,   # Pflicht
            "region": False,  # Optional
            "group":  False,  # Optional
        },
        "device": {
            "name":        True,   # Pflicht
            "device_role": True,   # Pflicht
            "device_type": True,   # Pflicht
            "site":        True,   # Pflicht
            "status":      True,   # Pflicht
            "tenant":      False,  # Optional
            "serial":      False,  # Optional
        },
        "circuit": {
            "cid":                True,   # Pflicht
            "provider":           True,   # Pflicht
            "type":               True,   # Pflicht
            "status":             True,   # Pflicht
            "site_termination_a": True,   # Pflicht
            "description":        False,  # Optional
        },
    },

    # ── Sprache ───────────────────────────────────────────────────────────────
    "language": "de",

    # ── Berechtigungsdokumentation ────────────────────────────────────────────
    "generate_permission_docs": True,
}
