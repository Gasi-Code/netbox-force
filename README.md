# NetBox Force

> A comprehensive NetBox plugin that enforces changelog discipline, naming conventions, required fields, ticket references, change windows, and compliance auditing on every object change.

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE)
[![NetBox](https://img.shields.io/badge/NetBox-4.x-informational)](https://github.com/netbox-community/netbox)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)

---

## Overview

NetBox is a powerful source-of-truth platform, but out of the box it places no constraints on *how* changes are made. Teams often end up with a change history full of empty comments, cryptic one-liners like "fix" or "test", or device names that don't follow any convention — making audits, rollbacks, and root-cause analysis painful.

**NetBox Force** adds a configurable enforcement layer that sits between every save/delete operation and the database. Before any change goes through, the plugin can verify that:

- A meaningful changelog comment was provided
- The comment references a ticket number (JIRA, ServiceNow, GitHub, etc.)
- The change happens within an approved time window
- Field values conform to naming patterns
- Required fields are actually filled in

All features are **opt-in**. Out of the box, only the changelog presence check is active with a 2-character minimum. Everything else is enabled and configured through the plugin's web UI — no configuration file changes required after initial setup.

---

## Features

### Enforcement Controls

| Feature | Description |
|---|---|
| **Global enforcement toggle** | Master switch to pause all enforcement globally (e.g. during maintenance windows) |
| **Dry-run mode** | Log violations without actually blocking changes — ideal for rolling out rules incrementally |
| **Enforce on create** | Optionally require a changelog when *creating* new objects (default: off) |
| **Enforce on delete** | Require a changelog when *deleting* objects (default: on) |

### Changelog Enforcement

| Feature | Description |
|---|---|
| **Changelog requirement** | Blocks saves/deletes unless a changelog comment is provided |
| **Minimum length** | Configurable minimum character count for changelog entries (default: 2) |
| **Blocked phrases** | Reject changelog entries that contain only meaningless words (whole-word matching, e.g. "fix", "test", "update") |

### Ticket Reference

| Feature | Description |
|---|---|
| **Regex-based ticket requirement** | Require every changelog comment to reference a ticket number matching a configurable regex pattern |
| **Human-readable hint** | Show a custom example (e.g. `JIRA-1234`) instead of the raw regex in error messages |

**Built-in examples:**

| Pattern | Matches | Use Case |
|---|---|---|
| `JIRA-\d+` | JIRA-1234 | Jira |
| `[A-Z]+-\d+` | PROJ-123, OPS-42 | Generic Jira-style |
| `#\d+` | #123 | GitHub / GitLab |
| `INC\d{7}` | INC0012345 | ServiceNow Incident |
| `CHG\d{7}` | CHG0012345 | ServiceNow Change |
| `(INC\|CHG\|REQ)\d+` | INC123, CHG456 | ServiceNow (any type) |

### Validation Rules

| Feature | Description |
|---|---|
| **Naming convention rules** | Enforce that a field value matches a regex pattern (uses `re.fullmatch`) |
| **Required field rules** | Enforce that a field is not empty, null, or blank |
| **Per-model, per-field** | Each rule targets a specific model + field combination |
| **Custom error messages** | Show a human-readable hint when a rule fails |
| **Model dropdown** | Searchable dropdown of all installed models in the rule editor |

### Change Windows

| Feature | Description |
|---|---|
| **Time window** | Restrict changes to a defined start/end time (24-hour, timezone-aware) |
| **Weekday filter** | Limit changes to specific days of the week (ISO weekday numbers) |
| **Overnight windows** | Supports windows that cross midnight (e.g. 22:00–06:00) |

### Model Policies

| Feature | Description |
|---|---|
| **Per-model enforcement toggle** | Disable enforcement entirely for a specific model regardless of global settings |
| **Per-model min. length override** | Require longer (or shorter) changelog entries for specific models |
| **Per-model naming rule toggle** | Disable naming convention checks for a specific model |
| **Per-model required field toggle** | Disable required field checks for a specific model |

### Audit Scan

| Feature | Description |
|---|---|
| **Retroactive compliance scan** | Scan existing database objects against active validation rules — read-only, no changes made |
| **Per-model results** | Results grouped by model with violation count, object name, rule type, and error message |
| **500-object limit** | Scan is capped at 500 objects per model to avoid timeouts |

### Webhook Notifications

| Feature | Description |
|---|---|
| **Violation webhooks** | Send an HTTP POST to a configurable URL on every blocked change |
| **JSON payload** | Payload includes event type, username, model, object, action, reason, and error message |
| **HMAC-SHA256 signing** | Optional secret for payload signing — adds `X-NetBox-Force-Signature` header |
| **Fire-and-forget** | Webhook runs in a background thread — never blocks the NetBox response |

### Exemptions

| Feature | Description |
|---|---|
| **Exempt users** | Skip all enforcement for specific usernames (case-insensitive) — useful for automation accounts |
| **Exempt groups** | Skip all enforcement for all members of specific Django groups — no need to list every username |
| **Exempt models** | Skip enforcement for additional models beyond the built-in system exclusions |

### Audit Log (Violations)

| Feature | Description |
|---|---|
| **Violation logging** | Every blocked action is recorded with timestamp, user, model, object, action, reason, error message, and attempted changelog comment |
| **Filterable log** | Filter violations by reason, username, and date range |
| **Automatic retention** | Configurable automatic cleanup of old violation entries |
| **CSV export** | Export all violation data for external analysis |

### Dashboard

| Feature | Description |
|---|---|
| **Feature status overview** | See which enforcement features are currently enabled |
| **Violation statistics** | Total count, breakdown by reason with progress bars |
| **Top users** | Most frequently blocked users |
| **30-day trend** | Daily violation chart for the past month |

### Modules

| Feature | Description |
|---|---|
| **Import Templates** | Admins can create downloadable CSV templates for NetBox's built-in bulk import — with UTF-8 BOM for Excel compatibility |
| **User Guide** | Built-in WYSIWYG HTML guide page for end users — supports full standalone HTML pages or simple rich-text content |

### General

| Feature | Description |
|---|---|
| **Multilingual UI** | All labels, help texts, and error messages in German, English, and Spanish. Language switchable per-plugin settings |
| **API support** | Enforcement applies to both UI and API requests. API error messages are always in English |
| **Singleton settings** | All settings stored in the database — configurable through the web UI without editing configuration files |

---

## Requirements

| Component | Version |
|---|---|
| **NetBox** | 4.0.0 or later |
| **Python** | 3.11 or later |
| **Database** | PostgreSQL (required by NetBox) |

---

## Tested Environments

NetBox Force has been tested on:

- **Docker** — official NetBox Docker image and LinuxServer.io image
- **Linux VM** — Debian-based virtual machines (bare-metal and VMware)

Other deployment types (Kubernetes, other Linux distributions) should work but have not been explicitly verified.

---

## Installation

### 1. Install the plugin

Activate the NetBox virtual environment and install directly from GitHub:

```bash
source /opt/netbox/venv/bin/activate
pip install git+https://github.com/Gasi-Code/netbox-force.git
```

For Docker (official NetBox image), add to your `Dockerfile`:

```dockerfile
RUN pip install git+https://github.com/Gasi-Code/netbox-force.git
```

For **LinuxServer.io** Docker image, use Docker Mods (runs before NetBox init scripts):

```yaml
services:
  netbox:
    image: ghcr.io/linuxserver/netbox:latest
    environment:
      DOCKER_MODS: linuxserver/mods:universal-package-install
      INSTALL_PIP_PACKAGES: git+https://github.com/Gasi-Code/netbox-force.git
```

> **Note for LinuxServer.io:** Do not use `custom-cont-init.d` scripts for plugin installation — they run *after* NetBox's init scripts, which can cause migration failures. Docker Mods run before init scripts.

### 2. Register the plugin

Add `netbox_force` to the `PLUGINS` list in your NetBox `configuration.py`:

```python
PLUGINS = [
    'netbox_force',
]
```

### 3. Run database migrations

```bash
cd /opt/netbox/netbox
python manage.py migrate netbox_force
```

### 4. Restart NetBox services

```bash
sudo systemctl restart netbox netbox-rq
```

For Docker:

```bash
docker compose restart netbox
```

---

## Updating

To update to the latest version, reinstall with the `--force-reinstall` and `--no-cache-dir` flags (required because pip caches by version number):

```bash
source /opt/netbox/venv/bin/activate
pip install --force-reinstall --no-cache-dir git+https://github.com/Gasi-Code/netbox-force.git
```

Then run migrations and restart:

```bash
cd /opt/netbox/netbox
python manage.py migrate netbox_force
sudo systemctl restart netbox netbox-rq
```

---

## Configuration

`PLUGINS_CONFIG` in `configuration.py` sets the **initial defaults** only. After the first startup, all settings are managed through the plugin's web UI and stored in the database.

```python
PLUGINS_CONFIG = {
    'netbox_force': {
        'min_length': 2,
        'exempt_users': ['automation', 'monitoring', 'netbox'],
        'enforce_on_create': False,
        'enforce_on_delete': True,
        'extra_exempt_models': [],
    },
}
```

| Setting | Default | Description |
|---|---|---|
| `min_length` | `2` | Minimum number of characters required in a changelog entry |
| `exempt_users` | `['automation', 'monitoring', 'netbox']` | Usernames exempt from all enforcement checks (case-insensitive) |
| `enforce_on_create` | `False` | Whether to require a changelog when creating new objects |
| `enforce_on_delete` | `True` | Whether to require a changelog when deleting objects |
| `extra_exempt_models` | `[]` | Additional model labels to exempt (format: `app.model`) |

All other settings (ticket reference, change window, audit log, validation rules, etc.) are configured exclusively through the web UI.

---

## Usage

After installation, superusers will find **NetBox Force** in the sidebar navigation. All plugin views are restricted to superusers by default.

### Settings

The main configuration page. Organized into sections:

- **Global Enforcement** — master on/off switch for all enforcement
- **Enforcement Rules** — minimum length, create/delete behavior, dry-run mode
- **Blocked Phrases** — comma-separated words to reject
- **Ticket Reference** — regex pattern and human-readable hint
- **Change Window** — time range and weekday filter
- **Audit Log** — enable/disable logging and set retention period
- **Exemptions** — exempt users and exempt models
- **Modules** — enable/disable Import Templates and User Guide

### Validation Rules

Create and manage naming convention and required field rules. Each rule targets a specific model and field. Rules are cached for 30 seconds and take effect immediately after saving.

### Violations (Audit Log)

A paginated, filterable log of every blocked change. Filter by:
- **Reason** — why the change was blocked
- **Username** — who attempted the change
- **Date range** — when the attempt occurred

Violations can be exported as CSV for compliance reporting.

### Dashboard

A read-only statistics page showing enforcement activity. Includes feature status indicators, violation breakdowns, top blocked users, and a 30-day daily trend chart.

### Import Templates

*(Requires enabling in Settings → Modules)*

Admins can create CSV header templates that users can download as a starting point for NetBox's built-in bulk import. Templates are Excel-compatible (UTF-8 BOM + `sep=,` hint).

### User Guide

*(Requires enabling in Settings → Modules)*

An editable HTML page for documenting internal procedures, naming conventions, or usage guidelines. Supports both WYSIWYG editing and raw HTML mode (including full standalone HTML pages with embedded CSS/JS).

---

## Screenshots

> Screenshots will be added in a future release.

---

## How It Works

### Enforcement Flow

```
HTTP Request
    │
    ▼
RequestContextMiddleware ──── stores request in thread-local storage
    │
    ▼
Django View (NetBox)
    │
    ▼
Model.save() / Model.delete()
    │
    ▼
Signal Handler (pre_save / pre_delete)
    │
    ├── No HTTP request (migration/management command)? ──► skip
    ├── Model exempt? ──────────────────────────────────► skip
    ├── User exempt? ──────────────────────────────────► skip
    ├── Global enforcement disabled? ─────────────────► skip
    ├── Existing object with no real changes? ─────────► skip
    │
    ├── Change window check ───────────────────────────► AbortRequest (if outside window)
    ├── Naming convention check ───────────────────────► AbortRequest (if violated)
    ├── Required field check ──────────────────────────► AbortRequest (if empty)
    ├── Changelog present + long enough? ─────────────► AbortRequest (if missing/short)
    ├── Blocked phrases check ─────────────────────────► AbortRequest (if matched)
    └── Ticket reference check ────────────────────────► AbortRequest (if missing)
         │
         ▼
    All checks passed ──────────────────────────────────► save/delete proceeds
```

### API Support

Enforcement applies to both the NetBox UI and REST API. The plugin reads the changelog comment from:
- **UI requests:** the `comments` form field
- **API requests:** the `changelog_message` JSON body field

```bash
# Example: API PATCH with changelog message
curl -X PATCH https://netbox.example.com/api/dcim/devices/1/ \
  -H "Authorization: Token YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "new-hostname",
    "changelog_message": "Renamed per JIRA-1234"
  }'
```

API error messages are always in English regardless of the plugin's language setting.

### Automatic Exemptions

The plugin automatically bypasses enforcement for:

- All authentication and session models (`auth.*`, `users.*`, `sessions.*`)
- NetBox internal objects (`extras.objectchange`, `extras.journalentry`, `core.job`, `extras.dashboard`, etc.)
- Django migration recorder (`migrations.migration`)
- The plugin's own models (`netbox_force.*`)
- Unauthenticated requests and management commands

---

## Troubleshooting

### Plugin not appearing in the sidebar
- Verify installation: `pip show netbox-force`
- Verify `'netbox_force'` is listed in `PLUGINS` in `configuration.py`
- Check NetBox logs for migration errors
- Confirm you are logged in as a **superuser** (the menu is hidden for non-superusers)

### Enforcement not working
- Confirm the user is not in the exempt users list (Settings → Exemptions)
- Confirm the model is not in the exempt models list
- Check that `enforce_on_create` is enabled when testing with new objects
- Enable debug logging: add `'netbox.plugins.netbox_force': 'DEBUG'` to `LOGGING` in `configuration.py`

### Migration errors on startup
- Ensure the plugin is installed **before** NetBox runs its init process
- For LinuxServer.io Docker: use `DOCKER_MODS` — never `custom-cont-init.d`
- For official Docker: install in a `Dockerfile` layer, not at runtime

### pip installs old version after update
pip caches packages by version number. Use `--force-reinstall --no-cache-dir`:

```bash
pip install --force-reinstall --no-cache-dir git+https://github.com/Gasi-Code/netbox-force.git
```

---

## Contributing

Contributions are welcome. Please open an issue before submitting a pull request for larger changes so we can discuss the approach.

- **Bug reports:** Open an issue with reproduction steps and NetBox/plugin version
- **Feature requests:** Open an issue describing the use case
- **Pull requests:** Fork the repository, make your changes, and open a PR against `main`

Please keep pull requests focused — one feature or fix per PR.

---

## License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

See [LICENSE](LICENSE) for the full license text.

> The AGPL-3.0 requires that if you modify this software and run it as a network service, you must make the modified source code available to users of that service under the same license.

---

*Maintained by [Gasi-Code](https://github.com/Gasi-Code)*
