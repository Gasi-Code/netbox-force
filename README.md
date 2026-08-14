# NetBox Force

> A comprehensive NetBox plugin that enforces changelog discipline, naming conventions, required fields, ticket references, change windows, and compliance auditing on every object change — and adds a full Patch Management module for tracking VM patch status.

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE)
[![NetBox](https://img.shields.io/badge/NetBox-4.x-informational)](https://github.com/netbox-community/netbox)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-5.8.0-green)](https://github.com/Gasi-Code/netbox-force)

**Documentation in your language:**
[čeština](docs/cs/README.md) ·
[dansk](docs/da/README.md) ·
[Deutsch](docs/de/README.md) ·
[English](docs/en/README.md) ·
[español](docs/es/README.md) ·
[français](docs/fr/README.md) ·
[italiano](docs/it/README.md) ·
[日本語](docs/ja/README.md) ·
[latviešu](docs/lv/README.md) ·
[Nederlands](docs/nl/README.md) ·
[polski](docs/pl/README.md) ·
[português](docs/pt/README.md) ·
[русский](docs/ru/README.md) ·
[Türkçe](docs/tr/README.md) ·
[українська](docs/uk/README.md) ·
[简体中文](docs/zh-hans/README.md)

---

## Overview

NetBox is a powerful source-of-truth platform, but out of the box it places no constraints on *how* changes are made. Teams often end up with a change history full of empty comments, cryptic one-liners like "fix" or "test", or device names that don't follow any convention — making audits, rollbacks, and root-cause analysis painful.

**NetBox Force** adds a configurable enforcement layer that sits between every save/delete operation and the database. Before any change goes through, the plugin can verify that:

- A meaningful changelog comment was provided
- The comment references a ticket number (JIRA, ServiceNow, GitHub, etc.)
- The change happens within an approved time window
- Field values conform to naming patterns
- Required fields are actually filled in

In addition, NetBox Force includes a fully integrated **Patch Management** module that tracks the patch status, operating system, responsible contacts, and update history for every virtual machine in NetBox, and a two-way **Graylog** integration that sends audit events out and brings log information back next to the object it belongs to.

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

### Graylog Output

Sends audit events to Graylog over GELF. Read-only towards NetBox — nothing is read back, and Graylog never changes anything in NetBox.

| Feature | Description |
|---|---|
| **What it sends** | Object created/changed/deleted, login, logout, **failed login**, blocked changes, and changes to the plugin settings themselves |
| **Why it is worth it** | Failed logins are kept nowhere in NetBox; the changelog carries no client IP or user agent; and `ForceSettings` is not changelogged at all, so switching enforcement off otherwise leaves no trace |
| **Selectable** | Every event type has its own checkbox and syslog severity |
| **Transports** | GELF over UDP, TCP, TCP+TLS, HTTP or HTTPS. Oversized UDP datagrams are chunked per the GELF spec |
| **Never blocking** | Events go onto a bounded queue drained by a background thread. A Graylog outage cannot slow down or fail a save in NetBox |
| **Bulk summarising** | A request changing more objects than a configurable threshold is reported as a single summary event instead of hundreds of near-identical lines |
| **Business hours** | Configurable window; every event carries an `outside_business_hours` field, and events inside the window can optionally be suppressed entirely |
| **Stable field schema** | Same fields on every event (`_app`, `_category`, `_event`, `_username`, `_client_ip`, `_object_type`, `_action`, `_request_id`, `_netbox_url`, …). `_request_id` groups everything one request changed |
| **English messages** | Message text is always English regardless of the UI language — Graylog alert queries match on it, and translating it would silently break every alert |
| **Connection test** | One-click test event. UDP cannot confirm receipt, and the result says so instead of claiming success |

### Graylog Read-back

Brings Graylog information into NetBox so a host can be judged without opening a second tab. Strictly read-only towards Graylog.

| Feature | Description |
|---|---|
| **Panel on device and VM** | Message, error and warning counts for that host, plus its recent messages on demand and a link that opens the matching search in Graylog |
| **Source inventory** | Every source Graylog reports, with counters, filterable by assigned, unassigned, silent or ignored |
| **Exact matching only** | Manual assignment → IP address → host name → host name after removing a configured domain suffix. First hit wins |
| **No fuzzy matching** | `srv-web-01` and `srv-web-02` differ by one character; any similarity score calls them a 96% match. In a numbered naming scheme the most similar candidate is systematically the wrong machine, so similarity only *orders* suggestions and never assigns anything |
| **Silent hosts** | Mapped in NetBox, sending nothing to Graylog — dead, mis-configured, or a leftover record. Neither system can spot this alone |
| **Never seen in Graylog** | The other half of the cross-check: devices and VMs that never appeared under any recognised name |
| **Cluster status** | Node list with green/yellow/red lamps, indexer health, journal backlog, each node linked to its NetBox VM. Loaded after the page renders, so a dead Graylog cannot hang the settings page |
| **One query per poll** | Counters for every host come from a single grouped query, not one query per device. A site with 800 devices costs three requests |
| **Mapping stays in the plugin** | Graylog never writes to a NetBox core object. Removing the plugin removes the mapping and leaves NetBox untouched |
| **Token at rest** | Encrypted with a key derived from Django's `SECRET_KEY`, never rendered back into the form |
| **Access control** | The message endpoint only answers for a source mapped to an object the caller may view |
| **Dashboard widget** | Sources, unassigned, silent and the loudest hosts — rendered from the plugin's own tables, so Graylog is never in the critical path of the NetBox start page |

**On "read-only":** every call either retrieves data or asks Graylog to run a search. The legacy search endpoint is a plain `GET`. The newer Views search API requires a `POST` to register and execute a search — that creates a short-lived search object inside Graylog and returns results; it stores nothing. Pin the search form to `legacy` if only `GET` is acceptable. The real guarantee is the token: issue it for a Graylog user with a read-only role.

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

| Component | Version | Notes |
|---|---|---|
| **NetBox** | 4.0.0 or later | |
| **Python** | 3.10 or later | |
| **Database** | PostgreSQL | Required by NetBox itself |
| **cryptography** | any | Ships with NetBox. Without it the CheckMK secret and the Graylog token are stored unencrypted, and the plugin says so on the settings page |
| **requests** | any | Ships with NetBox. Needed for the CheckMK and Graylog integrations |
| **RQ worker** | — | Only needed for the scheduled CheckMK sync and Graylog poll. Without a worker both still run on demand, and the page says so |

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
| `checkmk_secret` | `''` | Optional. Setting it keeps the CheckMK automation secret out of the database entirely; it then takes precedence over the UI field, which is disabled and says so |

All other settings (ticket reference, change window, audit log, validation rules, patch management, Graylog, etc.) are configured exclusively through the web UI.

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

### Graylog

Reachable from the sidebar under **NetBox Force → Graylog**. The page has two halves that are configured and switched on independently.

**Sending (top of the page).** Enter host, port and transport, then press *Send test event*. Below that, a table with one row per event type: a checkbox for whether to send it and a dropdown for its syslog severity. Underneath, the volume controls and the business-hours window.

Start with UDP. If nothing arrives in Graylog, switch to TCP — UDP cannot report a failure by design, TCP can, which separates "wrong port" from "message discarded".

**Reading (bottom of the page).** Enter the Graylog web address and an API token, then press *Test connection*. The result reports the Graylog version, the detected search API form, the loudest sources and the available streams. *Poll now* runs one poll immediately.

Issue the token for a Graylog user with a **read-only role**. That is the actual guarantee that nothing can be changed in Graylog from NetBox — not the plugin code.

**Sources.** The *Sources* button opens the inventory: everything Graylog reports, with counters, filterable by assigned, unassigned, silent, never-seen and ignored. Unassigned sources come with ordered suggestions; assigning one is a single click and outranks every automatic rule from then on.

**On the object.** Devices and virtual machines that have a source mapped to them get a Graylog panel showing the counters, the recent messages on demand, and a link that opens the matching search in Graylog.

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

Enforcement applies to both the NetBox UI and REST API. The plugin reads the changelog comment from NetBox's own **Changelog message** field — `changelog_message` in the form body and in the API JSON body. NetBox writes it to `ObjectChange.message`, so the enforced text is what appears in the change log.

Where a request carries no such field, the plugin falls back to the object's `comments` field. That covers NetBox releases predating the native field. Once the native field is present it is the only source: `comments` is persisted object data, so text left there by an earlier edit would satisfy the rule on every later save without anyone writing anything.

A form that renders no changelog field at all — a quick-add modal, for example — cannot satisfy the rule by any input. Those requests get an auto-generated message instead of being blocked.

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

The full version history lives in [CHANGELOG.md](CHANGELOG.md).

**Latest releases**

| Version | Highlights |
|---|---|
| **5.8.0** | Reading Graylog back into NetBox — panel on device and VM, source inventory, exact-only matching, silent hosts, cluster status |
| **5.7.0** | Sending audit events to Graylog over GELF — failed logins, blocked changes, plugin settings changes, client IP and user agent |
| **5.6.0** | Changelog enforcement on deletion |
| **5.5.0** | Correctness fixes in error messages, version reporting and column nullability |

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
