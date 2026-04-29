#!/bin/bash
# deploy_wizards.sh
# Deployment-Skript für NetBox Wizard-Scripts
# Organisation: Meine Organisation
# Zielverzeichnis: /opt/netbox/netbox/scripts/
#
# Verwendung:
#   chmod +x deploy_wizards.sh
#   ./deploy_wizards.sh
#   ./deploy_wizards.sh --dry-run   # Nur anzeigen, nichts ausführen
#
# Voraussetzungen:
#   - Script wird auf dem NetBox-Server ausgeführt (oder script_path ist per NFS/SSHFS gemountet)
#   - Ausführungsrechte als root oder mit sudo

set -euo pipefail

# ── Konfiguration ──────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="/opt/netbox/netbox/scripts"
NETBOX_USER="netbox"
NETBOX_GROUP="netbox"
NETBOX_MANAGE="/opt/netbox/netbox/manage.py"
PYTHON_BIN="$(command -v python3 || echo /opt/netbox/venv/bin/python)"
FILE_MODE="644"

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "🔍 DRY-RUN Modus — keine Änderungen werden vorgenommen"
    echo ""
fi

# ── Hilfsfunktionen ────────────────────────────────────────────────────────────
log_info()    { echo "[INFO]  $*"; }
log_ok()      { echo "[OK]    $*"; }
log_warn()    { echo "[WARN]  $*"; }
log_error()   { echo "[ERROR] $*" >&2; }

run() {
    if $DRY_RUN; then
        echo "[DRY]   $*"
    else
        "$@"
    fi
}

# ── Prüfungen ──────────────────────────────────────────────────────────────────
log_info "Starte Deployment der Wizard-Scripts..."
echo ""

if [[ ! -d "$TARGET_DIR" ]]; then
    log_error "Zielverzeichnis '$TARGET_DIR' nicht gefunden."
    log_error "Bitte TARGET_DIR in diesem Skript anpassen."
    exit 1
fi

# ── Wizard-Dateien kopieren ────────────────────────────────────────────────────
WIZARD_FILES=(
    "wizard_ip.py"
    "wizard_prefix.py"
    "wizard_vlan.py"
    "wizard_site.py"
    "wizard_device.py"
    "wizard_circuit.py"
    "wizard_config.py"
)

echo "── Dateien kopieren ──────────────────────────────────────────────────────"
for f in "${WIZARD_FILES[@]}"; do
    src="$SCRIPT_DIR/$f"
    dst="$TARGET_DIR/$f"
    if [[ ! -f "$src" ]]; then
        log_warn "Quelldatei nicht gefunden: $src — übersprungen"
        continue
    fi
    run cp "$src" "$dst"
    run chown "$NETBOX_USER:$NETBOX_GROUP" "$dst"
    run chmod "$FILE_MODE" "$dst"
    log_ok "$f → $dst"
done
echo ""

# ── Syntax-Check ──────────────────────────────────────────────────────────────
echo "── Python Syntax-Check ───────────────────────────────────────────────────"
SYNTAX_OK=true
for f in "${WIZARD_FILES[@]}"; do
    src="$SCRIPT_DIR/$f"
    if [[ ! -f "$src" ]]; then continue; fi
    if $PYTHON_BIN -m py_compile "$src" 2>&1; then
        log_ok "$f — Syntax OK"
    else
        log_error "$f — Syntax-Fehler!"
        SYNTAX_OK=false
    fi
done

if ! $SYNTAX_OK; then
    log_error "Syntax-Fehler gefunden — Deployment abgebrochen."
    exit 1
fi
echo ""

# ── NetBox Script-Erkennung testen ────────────────────────────────────────────
echo "── NetBox Erkennung prüfen ───────────────────────────────────────────────"
if [[ -f "$NETBOX_MANAGE" ]]; then
    if $DRY_RUN; then
        log_info "[DRY] $PYTHON_BIN $NETBOX_MANAGE shell -c \"from extras.scripts import Script; print('Script-Import OK')\""
    else
        IMPORT_RESULT=$(
            $PYTHON_BIN "$NETBOX_MANAGE" shell -c \
                "from extras.scripts import Script; print('Script-Import OK')" \
                2>&1
        ) && log_ok "$IMPORT_RESULT" || log_warn "Import-Test fehlgeschlagen: $IMPORT_RESULT"
    fi
else
    log_warn "manage.py nicht gefunden unter '$NETBOX_MANAGE' — Test übersprungen"
fi
echo ""

# ── Dienste neu starten ───────────────────────────────────────────────────────
echo "── NetBox-Dienste neu starten ────────────────────────────────────────────"
for svc in netbox netbox-rq; do
    if systemctl is-active --quiet "$svc" 2>/dev/null || systemctl is-enabled --quiet "$svc" 2>/dev/null; then
        run systemctl restart "$svc"
        log_ok "systemctl restart $svc"
    else
        log_warn "Dienst '$svc' nicht gefunden oder nicht aktiv — übersprungen"
    fi
done
echo ""

# ── Zusammenfassung ───────────────────────────────────────────────────────────
echo "── Deployment abgeschlossen ──────────────────────────────────────────────"
echo ""
echo "  Scripts verfügbar unter: $TARGET_DIR"
echo "  NetBox URL:               https://netbox.example.com"
echo "  Scripts-Bereich:          https://netbox.example.com/extras/scripts/"
echo ""
echo "  Verfügbare Scripts:"
for f in "${WIZARD_FILES[@]}"; do
    if [[ "$f" != "wizard_config.py" ]]; then
        echo "    • ${f%.py}"
    fi
done
echo ""
if $DRY_RUN; then
    echo "  ℹ️  DRY-RUN: Keine Änderungen wurden vorgenommen."
    echo "     Ausführen ohne --dry-run um tatsächlich zu deployen."
fi
