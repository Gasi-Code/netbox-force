# NetBox Force

> A comprehensive NetBox plugin that enforces changelog discipline, naming conventions, required fields, ticket references, change windows, and compliance auditing on every object change — and adds a full Patch Management module for tracking VM patch status.

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE)
[![NetBox](https://img.shields.io/badge/NetBox-4.x-informational)](https://github.com/netbox-community/netbox)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-5.3.0-green)](https://github.com/Gasi-Code/netbox-force)

---

## Overview

NetBox is a powerful source-of-truth platform, but out of the box it places no constraints on *how* changes are made. Teams often end up with a change history full of empty comments, cryptic one-liners like "fix" or "test", or device names that don't follow any convention — making audits, rollbacks, and root-cause analysis painful.

**NetBox Force** adds a configurable enforcement layer that sits between every save/delete operation and the database. Before any change goes through, the plugin can verify that:

- A meaningful changelog comment was provided
- The comment references a ticket number (JIRA, ServiceNow, GitHub, etc.)
- The change happens within an approved time window
- Field values conform to naming patterns
- Required fields are actually filled in

In addition, **NetBox Force 4.6** includes a fully integrated **Patch Management** module that tracks the patch status, operating system, responsible contacts, and update history for every virtual machine in NetBox.

All features are **opt-in** and can be individually toggled. Out of the box, only the changelog presence check is active with a 2-character minimum. Everything else is enabled and configured through the plugin's web UI — no configuration file changes required after initial setup.

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
| **Blocked phrases** | Reject changelog entries that contain only meaningless words (whole-word matching, e.g. "fix", "test", "update"). Has an explicit enable/disable toggle |
| **Auto-changelog** | Automatically generate a human-readable diff comment when none is provided (optional). Lists every changed field in the configured language |

### Ticket Reference

| Feature | Description |
|---|---|
| **Explicit toggle** | Enable or disable the ticket reference check independently with a dedicated toggle |
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
| **Inline enable/disable** | Toggle rules on/off from the list view without opening the edit form |

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
| **Inline enable/disable** | Toggle policies on/off from the list view without opening the edit form |

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
| **Patch Management widget** | Overview of VM patch status (green/yellow/red) directly on the NetBox home dashboard |

### Modules

| Feature | Description |
|---|---|
| **Import Templates** | Admins can create downloadable CSV templates for NetBox's built-in bulk import — with UTF-8 BOM for Excel compatibility |
| **User Guide** | Built-in WYSIWYG HTML guide page for end users — supports full standalone HTML pages or simple rich-text content |

### General

| Feature | Description |
|---|---|
| **Multilingual UI** | All labels, help texts, and error messages available in 16 languages. Language switchable in plugin settings |
| **Sidebar localization** | Sidebar navigation labels follow the configured language (updated on NetBox restart) |
| **API support** | Enforcement applies to both UI and API requests. API error messages are always in English |
| **Singleton settings** | All settings stored in the database — configurable through the web UI without editing configuration files |

**Supported languages:**

| Code | Language |
|---|---|
| `cs` | Čeština (Czech) |
| `da` | Dansk (Danish) |
| `de` | Deutsch (German) |
| `en` | English |
| `es` | Español (Spanish) |
| `fr` | Français (French) |
| `it` | Italiano (Italian) |
| `ja` | 日本語 (Japanese) |
| `lv` | Latviešu (Latvian) |
| `nl` | Nederlands (Dutch) |
| `pl` | Polski (Polish) |
| `pt` | Português (Portuguese) |
| `ru` | Русский (Russian) |
| `tr` | Türkçe (Turkish) |
| `uk` | Українська (Ukrainian) |
| `zh-hans` | 中文 (Chinese Simplified) |

---

## Patch Management Module

The Patch Management module (introduced in v4.5.0, significantly expanded in v4.6.0) tracks the patch status and maintenance history of virtual machines directly within NetBox.

### What it tracks

Each virtual machine in Patch Management has the following fields:

| Field | Description |
|---|---|
| **VM** | Link to the NetBox VirtualMachine object |
| **FQDN** | Fully qualified domain name of the VM |
| **IP Address** | Link to a NetBox IPAddress object |
| **Operating System** | Free-text OS name — automatically synced with `VirtualMachine.platform` (bidirectional) |
| **Patch Status** | Color-coded status: Green (up-to-date), Yellow (patches pending), Red (critically overdue) |
| **Maintenance Window** | When this VM may be patched: None, Business Hours, Non-Business Hours, or Weekend |
| **Update Installation** | How updates are applied: Unknown, Automatic, or Manual |
| **Ticket Number** | Internal ticket reference for the last patch cycle |
| **Comment** | Free-text notes |
| **Administrators** | One or more NetBox Contacts responsible for this VM (role: Patch-Admin) |
| **Process Owners** | One or more NetBox Contacts as process owners (role: Patch-VB) |
| **Overdue warning** | Configurable threshold in days — VMs are flagged as overdue if not patched within this period |

### Update History

Each VM in Patch Management can have multiple update entries:

| Field | Description |
|---|---|
| **Date** | Date the patch was applied |
| **Version Before** | Software version before patching |
| **Version After** | Software version after patching |
| **Software** | Name of the patched software or OS |
| **Info** | Additional notes |
| **Updated By** | NetBox Contact who performed the patch |

### Contact Integration

Contacts in Patch Management are standard NetBox Contacts (from the Tenancy app). The plugin automatically creates two ContactRole objects on startup:

- **Patch-Admin** (`patch-admin`) — for Administrators
- **Patch-VB** (`patch-vb`) — for Process Owners (Verfahrensbetreuer)

Contact assignments are **bidirectional**: adding a contact in the Patch Management form also adds a ContactAssignment on the VM in NetBox's native Contacts tab, and vice versa. Removing a contact does the same.

### Operating System Sync

The `Operating System` field in Patch Management is kept in sync with `VirtualMachine.platform` in NetBox:

- When you set or change `VirtualMachine.platform` in NetBox → the Patch Management OS field updates automatically
- When you set or change the OS in the Patch Management form → NetBox creates or finds the matching `Platform` object and sets it on the VM
- When a new VM is auto-added to Patch Management → its current platform is copied as the initial OS value
- Platform objects are created with a URL-safe slug if they don't already exist

### Auto-Add VMs

When the **Auto-Add VMs** setting is enabled, every newly created VirtualMachine is automatically added to Patch Management with:
- `patch_status = green`
- `fqdn` = VM name
- `os_info` = current platform name (if set)

### Changelog Integration

All Patch Management changes appear in NetBox's native Changelog (ObjectChange), including:

- Field changes (OS, patch status, IP, maintenance window, etc.) — auto-generated "Nachricht" describing each changed field
- Contact additions and removals — "Nachricht" lists the contact names: `Admin hinzugefügt: John Doe; VB entfernt: Jane Smith`
- The ObjectChange type shows **Patchmanagement** (not the internal model name)

### Dashboard Widget

A Patch Management dashboard widget can be added to the NetBox home screen. It shows:
- Count of VMs per patch status (green/yellow/red)
- Overdue VM count (if threshold is configured)

### Patch Management Settings

| Setting | Description |
|---|---|
| **Overdue threshold (days)** | Number of days after the last patch date before a VM is flagged as overdue. Set to 0 to disable |
| **Auto-Add new VMs** | Automatically add every new VirtualMachine to Patch Management |

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

All other settings (ticket reference, change window, audit log, validation rules, patch management, etc.) are configured exclusively through the web UI.

---

## Usage

After installation, superusers will find **NetBox Force** in the sidebar navigation. All plugin views are restricted to superusers by default.

### Settings

The main configuration page. Organized into sections:

- **Global Enforcement** — master on/off switch for all enforcement
- **Enforcement Rules** — minimum length, create/delete behavior, dry-run mode
- **Blocked Phrases** — enable/disable toggle + list of phrases to reject (whole-word match)
- **Ticket Reference** — enable/disable toggle + regex pattern and human-readable hint
- **Change Window** — time range and weekday filter
- **Audit Log** — enable/disable logging and set retention period
- **Webhook** — enable/disable + endpoint URL and optional HMAC signing secret
- **Exemptions** — exempt users, groups, and models
- **Modules** — enable/disable Import Templates and User Guide
- **Patch Management** — overdue threshold, auto-add VMs toggle

### Validation Rules

Create and manage naming convention and required field rules. Each rule targets a specific model and field. Rules are cached for 30 seconds and take effect immediately after saving. Rules can be toggled on/off from the list view using inline buttons.

### Model Policies

Override enforcement behavior for specific models without touching global settings. Model policies allow you to exempt a single model, set a longer minimum changelog length, or selectively disable naming/required-field checks. Policies can be toggled on/off from the list view using inline buttons.

### Violations (Audit Log)

A paginated, filterable log of every blocked change. Filter by:
- **Reason** — why the change was blocked
- **Username** — who attempted the change
- **Date range** — when the attempt occurred

Violations can be exported as CSV for compliance reporting.

### Dashboard

A read-only statistics page showing enforcement activity. Includes feature status indicators, violation breakdowns, top blocked users, and a 30-day daily trend chart.

### Patch Management

The Patch Management section is accessible from the sidebar under **NetBox Force → Patchmanagement**.

#### VM List

The main list view shows all VMs currently tracked in Patch Management with:
- FQDN and IP address
- Operating system
- Patch status (color-coded badge)
- Last patch date
- Overdue flag (if threshold exceeded)
- Administrators and Process Owners

#### Adding a VM Manually

Click **Add VM** to create a new Patch Management entry. Select the NetBox VirtualMachine, set the FQDN, IP, OS, patch status, maintenance window, and assign contacts.

#### VM Detail View

The detail view for a single VM shows all fields plus the full update history. From here you can:
- Edit the VM record
- Add a new update entry
- View the overdue status
- See linked contacts

#### Recording a Patch

In the VM detail view, click **Add Update** to record a new patch event. Fill in the date, software version before and after, and optional notes.

#### Search and Filter

The list view supports:
- Free-text search (FQDN, OS)
- Filter by patch status
- Filter by maintenance window
- Filter by overdue status
- Filter by contact

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
    ├── User exempt (by username or group)? ───────────► skip
    ├── Global enforcement disabled? ─────────────────► skip
    ├── Existing object with no real changes? ─────────► skip
    │
    ├── Change window check ───────────────────────────► AbortRequest (if outside window)
    ├── Naming convention check ───────────────────────► AbortRequest (if violated)
    ├── Required field check ──────────────────────────► AbortRequest (if empty)
    ├── Changelog present + long enough? ─────────────► AbortRequest (if missing/short)
    ├── Blocked phrases check (if enabled) ────────────► AbortRequest (if matched)
    └── Ticket reference check (if enabled) ───────────► AbortRequest (if missing)
         │
         ▼
    All checks passed ──────────────────────────────────► save/delete proceeds
```

### OS Sync Flow (Patch Management)

```
VM.platform changes (NetBox UI/API)
    │
    ▼
post_save signal on VirtualMachine
    │
    ▼
Find linked PatchVM → compare os_info
    │
    ├── os_info already matches? ───────────────────────► skip (no loop)
    └── os_info differs? ───────────────────────────────► PatchVM.os_info = platform.name
                                                          PatchVM.save() → ObjectChange created

PatchVM.os_info changes (Patch Management form)
    │
    ▼
post_save signal on PatchVM
    │
    ▼
Find linked VirtualMachine → compare platform.name
    │
    ├── already matches? ───────────────────────────────► skip (no loop)
    └── differs? ──────────────────────────────────────► Platform.get_or_create(name=os_info)
                                                          VM.platform = platform
                                                          VM.save() → ObjectChange created
```

### Violation Queue

Violations are not written during the signal handler itself (a DB rollback would also roll back the violation record). Instead, violations are buffered in thread-local storage and written **after** the view returns, outside the transaction.

### Language & Sidebar Localization

The plugin's UI language is set in **Settings → Language**. In-plugin tabs, labels, help texts, and error messages update immediately on every request. Sidebar navigation labels (in NetBox's left nav) are read at startup — they update after the next **NetBox restart**.

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
- Internal sync saves (OS bidirectional sync between VM and Patch Management)

---

## Changelog

### v5.3.0

- **Physical servers can be linked.** Patch Management entries had only a link to `virtualization.VirtualMachine`, so a bare-metal host could never be more than a standalone record. A `device` link to `dcim.Device` was added, and the CheckMK sync fills whichever of the two matches the host name.
- **One-click creation of the missing object.** An entry tied to no NetBox object now offers *As device* / *As VM* buttons that open the corresponding NetBox form with the name prefilled. Both are offered because a host name does not say whether it is metal or virtual — and the site, role, device type or cluster are decisions the plugin has no basis to make.
- **Repairs `netbox_force_modelpolicy`** on installations that applied both migration generations (`0002_v4_features…` and `0002_v43_features…`). The table was created with the old column layout and the later `CreateModel` never corrected it, so the Model Policies page failed with *column check_required_fields_rules does not exist*. The repair is idempotent and does nothing on a healthy database. Obsolete columns are made nullable rather than dropped, so no data is lost.

### v5.2.0

- **Relative times no longer mix languages.** Django's `timesince` renders in NetBox's locale while every other label comes from the plugin's own language setting, which produced output like *"5 Minuten ago"*. A `force_age` filter now reads the plugin language and uses a compact unit form (`5 Min.`, `2 Std.`, `3 T`) that needs no preposition or plural rule in any of the sixteen languages.
- **Create missing IP addresses in one click.** Where CheckMK reports an address NetBox does not know, the patch list offers a button straight into NetBox's IPAM form, prefilled with the address and the host name as DNS name.
- **The mask is derived, not guessed** — it comes from the most specific NetBox prefix containing the address. Only when no prefix matches is a host mask prefilled, and the button says so instead of pretending to know.
- Removed the leftover `wizard_*.html` templates of the withdrawn wizard feature.

### v5.1.0

- **Host data from CheckMK** — each sync now also reads the monitored IP address and the host's up/down state from the CheckMK monitoring API. A host CheckMK cannot reach is flagged in the patch list, because its patch status is by definition stale.
- **IP linking without double maintenance** — when CheckMK reports an address that already exists in NetBox IPAM and the Patch Management entry has no IP linked yet, the link is created automatically. An existing link is never changed or removed; if CheckMK monitors a different address, that is shown as a warning rather than silently corrected.
- **Addresses NetBox does not know** are marked *not in NetBox* instead of being created. A monitoring system is not the source of truth for IPAM — the gap is surfaced so a person decides what it should become.
- **Discovery no longer depends on auto-changelog** — creating a Patch Management entry during a sync went through the plugin's own enforcement and only succeeded because auto-changelog happened to be enabled. It now uses the internal sync bypass.
- **Complete translations** — eleven keys reachable from the patch list and the patch dashboard widget existed only in English and German. `Warning` and `Critical` were untranslated even in German.

### v5.0.0 — CheckMK integration rebuilt as a pull

**Breaking:** the inbound webhook receiver (`/api/plugins/netbox-force/webhook-receiver/`) is gone, and with it the `checkmk_webhook_secret` setting. Existing CheckMK notification rules pointing at that URL will start returning 404 and can be deleted once the sync is verified.

- **NetBox now reads from CheckMK instead of waiting to be told.** Configure the site URL, an automation user and its secret once; Patch Management is populated and kept current from the CheckMK service data. Nothing is ever written back to CheckMK.
- **No unauthenticated endpoint.** The plugin only makes outbound calls, which removes the entire attack surface the webhook had.
- **Read-only by design.** Only the monitoring API is used, never the Setup/WATO configuration API — a CheckMK user with the `guest` role is enough.
- **Hosts are discovered automatically.** Every CheckMK host with a service matching the configurable filter (default `Updates?`, matching *System Updates*, *APT Updates*, *Windows Updates*) gets an entry, linked to a NetBox VirtualMachine when the name matches.
- **Hand-maintained fields are protected.** The sync writes only status, timestamps and CheckMK provenance. Ticket number, comment, maintenance window, contacts and the VM link survive every run.
- **Hosts that vanish are flagged, not deleted.** An entry that CheckMK stops reporting is marked *No longer monitored in CheckMK* in red, its status frozen at the last known value, and it is excluded from age-based escalation.
- **Version-tolerant API access.** The service query is probed across several forms and the working one is remembered, so the plugin does not need updating for each CheckMK release. Verified against 2.3.0p48 Raw Edition.
- **Secret stored encrypted**, with `PLUGINS_CONFIG['netbox_force']['checkmk_secret']` taking precedence when set, so the secret can be kept out of the database entirely.
- **Test connection / Sync now** buttons on the settings page report in plain language, plus a history of the last 50 sync runs.
- **Three ways to run it:** the button, `manage.py checkmk_sync` (for cron), and a recurring background job when an RQ worker is available. The settings page states which one is actually active.

### v4.7.0

- **CheckMK escalation now actually fires** — CheckMK notifications only trigger on state *transitions*, so a host that stayed in WARNING never sent a second webhook and was never escalated. A sweep (`PatchVM.escalate_overdue()`) now runs from the patch list and dashboard widget, so the stored status, the status counters and the `?status=red` filter all agree.
- **Escalation no longer undone** — a repeated WARN report used to reset `first_warned`, dropping an already-escalated VM back to yellow. `first_warned` now marks the start of an ongoing WARNING period and survives repeated WARN reports.
- **Configurable escalation threshold** — Settings → CheckMK Integration → *Escalation threshold (days)*, default 30, `0` disables escalation.
- **Webhook fails closed** — with no `checkmk_webhook_secret` configured the endpoint returned `200` and accepted writes from anyone. It now returns `503` until a secret is set. Secret comparison also tolerates non-ASCII values instead of raising a `500`.
- **CheckMK data on the VM detail page** — last check, warning age, auto-escalation badge and the raw CheckMK output.
- **Auto-changelog scope** — Settings → *Areas*: restrict auto-generated changelog messages to selected NetBox areas (DCIM, IPAM, Virtualization, …). Selecting nothing keeps the previous behaviour of applying everywhere.

### v4.6.0

- **Bidirectional OS sync** — `VirtualMachine.platform` and the Patch Management OS field are kept in sync automatically. Changing either one updates the other. Platform objects are created on demand if they don't exist yet. New VMs are auto-added with the current platform as initial OS.
- **Contact changelog messages** — Adding or removing a contact in the Patch Management form now creates an ObjectChange entry with a human-readable "Nachricht": `Admin hinzugefügt: John Doe; VB entfernt: Jane Smith`. Contact changes via NetBox's native ContactAssignment UI are also captured.
- **Correct ObjectChange field** — Changelog messages are now stored in the `message` field on `ObjectChange` (NetBox 4.x), which maps to the "Nachricht" column in the changelog UI.
- **_netbox_force_sync_save bypass** — Internal sync saves (OS sync, contact sync) are now correctly exempt from enforcement to prevent false violations.
- **ContactAssignment bidirectional sync** — Contacts added/removed via NetBox's native Contacts tab on a VM are mirrored to Patch Management and vice versa.

### v4.5.0

- **Patch Management module** — Full VM patch tracking: status (green/yellow/red), OS, administrators, process owners, update history, overdue warning, maintenance window, ticket reference.
- **Auto-Add VMs** — Automatically add newly created VirtualMachines to Patch Management.
- **Patch Management dashboard widget** — Home screen widget showing VM counts per status.
- **ContactRole auto-creation** — Plugin creates the required `Patch-Admin` and `Patch-VB` ContactRole objects on startup.
- **Patchmanagement i18n** — All Patch Management UI strings translated across all 16 supported languages.
- **Explicit feature toggles** — Blocked Phrases and Ticket Reference now each have a dedicated enable/disable checkbox.
- **16 languages** — Added Czech, Danish, French, Italian, Japanese, Latvian, Dutch, Polish, Portuguese, Russian, Turkish, Ukrainian, and Chinese Simplified.
- **Sidebar localization** — Plugin sidebar navigation labels now follow the configured language (requires NetBox restart after language change).

### v4.4.0

- **Model Policies** — Per-model enforcement overrides: enable/disable enforcement, set a custom minimum changelog length, and toggle naming/required-field checks per model.
- **Audit Scan** — Retroactive compliance scan that checks existing database objects against active validation rules without making any changes.
- **Webhook Notifications** — HTTP POST notifications on every blocked change, with optional HMAC-SHA256 payload signing.
- **Group Exemptions** — Exempt all members of a Django group from enforcement without listing individual usernames.
- **Inline Toggle Buttons** — Enable/disable Validation Rules and Model Policies directly from the list view.

### v4.3.x and earlier

- Initial release with changelog enforcement, ticket reference, blocked phrases, change windows, validation rules, audit log, dashboard, import templates, and user guide.

---

## Troubleshooting

### Plugin not appearing in the sidebar

- Verify installation: `pip show netbox-force`
- Verify `'netbox_force'` is listed in `PLUGINS` in `configuration.py`
- Check NetBox logs for migration errors
- Confirm you are logged in as a **superuser** (the menu is hidden for non-superusers)

### Enforcement not working

- Confirm the user is not in the exempt users list (Settings → Exemptions)
- Confirm the user is not a member of an exempt group
- Confirm the model is not in the exempt models list
- Check that `enforce_on_create` is enabled when testing with new objects
- Verify that the relevant feature toggle (Blocked Phrases, Ticket Reference) is enabled in Settings
- Enable debug logging: add `'netbox.plugins.netbox_force': 'DEBUG'` to `LOGGING` in `configuration.py`

### Patch Management OS not syncing

- Confirm the VM has a linked PatchVM entry (check via Patchmanagement list)
- Confirm the Platform exists in NetBox (Devices → Platforms)
- Check that the OS name in Patch Management matches the Platform name exactly (case-sensitive)
- Check NetBox logs: `sudo docker logs Netbox 2>&1 | grep sync_vm_platform`

### Patch Management contact changes not showing Nachricht

- Ensure you are on NetBox Force 4.6.0 or later
- Reinstall with `--force-reinstall --no-cache-dir` and restart NetBox
- The "Nachricht" field in the changelog uses the `message` field on `ObjectChange` (NetBox 4.x)

### Sidebar labels still in English after changing language

The sidebar navigation is read once at NetBox startup. After changing the language in Settings, restart NetBox for the sidebar labels to update. In-plugin tabs and all UI strings update immediately without a restart.

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
