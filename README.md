# NetBox Force

A comprehensive NetBox plugin that enforces changelog messages, naming conventions, required fields, ticket references, change windows, and compliance auditing on all object changes.

All features are **opt-in** — out of the box, only changelog enforcement is active. Everything else can be enabled and configured through the web UI.

## Compatibility

| Requirement | Version |
|---|---|
| **NetBox** | 4.0.0+ |
| **Python** | 3.10+ |

Works with all NetBox deployment types: Docker (official image, LinuxServer.io), bare-metal Linux, virtual machines, Kubernetes.

## Features

### Changelog Enforcement (always active)
Requires a meaningful changelog comment when creating, editing, or deleting objects.

- **Minimum length** — configurable minimum character count (default: 2)
- **Enforce on create** — optionally require changelog when creating new objects (default: off)
- **Enforce on delete** — require changelog when deleting objects (default: on)
- **Blocked phrases** — reject changelog entries containing specific words (whole-word matching)
- **Exempt users** — skip enforcement for automation accounts (case-insensitive)
- **Exempt models** — skip enforcement for specific models

### Ticket Reference Requirement (opt-in)
Requires every changelog comment to contain a ticket reference matching a regex pattern.

**Examples:**
| Pattern | Matches | Use Case |
|---|---|---|
| `JIRA-\d+` | JIRA-1234 | Jira |
| `[A-Z]+-\d+` | PROJ-123 | Generic Jira-style |
| `#\d+` | #123 | GitHub / GitLab |
| `INC\d{7}` | INC0012345 | ServiceNow Incident |
| `CHG\d{7}` | CHG0012345 | ServiceNow Change |
| `(INC\|CHG\|REQ)\d+` | INC/CHG/REQ + number | ServiceNow (any) |

**How to enable:** Settings → Ticket Reference → enter a regex pattern. Leave empty to disable.

### Naming Convention Enforcement (opt-in)
Enforces that field values on specific models match a regex pattern.

**Example:** Require all device names to follow the format `XX-YYYY-NNN`:
- Model: `dcim.device`
- Field: `name`
- Pattern: `^[A-Z]{2}-[A-Z]+-\d{3}$`
- Error message: `Device name must match format: XX-SITE-001`

The plugin provides a searchable dropdown of all installed models and their fields when creating rules.

**How to enable:** Validation Rules tab → Add Rule → select "Naming Convention".

### Required Fields Enforcement (opt-in)
Enforces that specific fields on specific models are not empty, null, or blank.

**Example:** Require every device to have a tenant assigned:
- Model: `dcim.device`
- Field: `tenant`

**How to enable:** Validation Rules tab → Add Rule → select "Required Field".

### Change Window Enforcement (opt-in)
Restricts changes to a defined time window (time of day + weekdays).

- **Start/end time** — e.g. 08:00 to 18:00
- **Allowed weekdays** — comma-separated ISO weekday numbers (1=Monday, 7=Sunday)
- **Overnight windows** — supports windows that cross midnight (e.g. 22:00 to 06:00)

Exempt users bypass the change window.

**How to enable:** Settings → Change Window → enable and configure times.

### Audit Log (opt-in)
Records every blocked change attempt for compliance tracking.

Each violation entry contains:
- Timestamp
- Username
- Model and object
- Action (create/edit/delete)
- Reason (missing changelog, too short, blacklisted phrase, missing ticket, naming violation, required field, change window)
- Error message shown to the user
- The attempted changelog comment

**Filterable** by reason, username, and date range. **Paginated** for large datasets.

**How to enable:** Settings → Audit Log → enable. Configure retention period in days.

### Dashboard
Read-only overview showing:
- **Feature status** — which features are enabled/disabled
- **Total violations** — lifetime count
- **Violations by reason** — breakdown with progress bars
- **Top 10 users** — most frequently blocked users
- **Last 30 days** — daily violation trend

### Multilingual UI (DE / EN / ES)
All labels, help texts, error messages, and section headers change dynamically based on the selected language. API error messages are always in English.

## Installation

### Method 1: pip install from GitHub

```bash
pip install https://github.com/Gasi-Code/netbox-force/archive/refs/heads/main.tar.gz
```

### Method 2: pip install from local clone

```bash
git clone https://github.com/Gasi-Code/netbox-force.git
pip install -e ./netbox-force/
```

### Method 3: Docker (official NetBox image)

Add to your `docker-compose.yml` or Dockerfile:

```dockerfile
RUN pip install https://github.com/Gasi-Code/netbox-force/archive/refs/heads/main.tar.gz
```

### Method 4: Docker (LinuxServer.io image)

Use Docker Mods for automatic installation before NetBox starts:

```yaml
services:
  netbox:
    image: ghcr.io/linuxserver/netbox:latest
    environment:
      DOCKER_MODS: linuxserver/mods:universal-package-install
      INSTALL_PIP_PACKAGES: https://github.com/Gasi-Code/netbox-force/archive/refs/heads/main.tar.gz
```

> **Important:** Do not use `custom-cont-init.d` scripts for plugin installation — they run after NetBox's init scripts, causing migration failures. Docker Mods run before init scripts.

### Method 5: Kubernetes / Helm

Add to your init container or custom image build:

```bash
pip install https://github.com/Gasi-Code/netbox-force/archive/refs/heads/main.tar.gz
```

## Configuration

Add to your NetBox `configuration.py`:

```python
PLUGINS = [
    'netbox_force',
]

# Optional: override defaults (all values below are the defaults)
PLUGINS_CONFIG = {
    'netbox_force': {
        'min_length': 2,                 # Minimum changelog message length
        'exempt_users': [                # Users exempt from enforcement
            'automation',
            'monitoring',
            'netbox',
        ],
        'enforce_on_create': False,      # Require changelog on object creation
        'enforce_on_delete': True,       # Require changelog on object deletion
        'extra_exempt_models': [],       # Additional models to exempt (e.g. 'myplugin.mymodel')
    },
}
```

After installation, restart NetBox:

```bash
# Bare-metal
sudo systemctl restart netbox netbox-rq

# Docker
docker compose restart netbox

# Docker (full rebuild)
docker compose up -d --force-recreate netbox
```

The database migration runs automatically on startup.

## How It Works

### Architecture

```
HTTP Request
    |
    v
RequestContextMiddleware --> stores request in thread-local storage
    |
    v
Django View (NetBox)
    |
    v
Model.save() / Model.delete()
    |
    v
Signal Handler (pre_save / pre_delete)
    |
    |-- Is model exempt? --> skip
    |-- Is user exempt? --> skip
    |-- Is request method enforced? --> skip
    |-- New object + enforce_on_create=False? --> skip
    |-- No real changes? --> skip
    |
    |-- Change window check --> AbortRequest
    |-- Changelog present + long enough? --> AbortRequest
    |-- Blacklisted phrases? --> AbortRequest
    |-- Ticket reference present? --> AbortRequest
    |-- Naming convention valid? --> AbortRequest
    |-- Required fields filled? --> AbortRequest
    |
    +-- All checks passed --> save proceeds
```

### Enforcement Chain

Checks run in this order (first failure wins):

1. **Change Window** — blanket denial regardless of content
2. **Changelog Presence** — must exist and meet minimum length
3. **Blocked Phrases** — whole-word matching against blacklist
4. **Ticket Reference** — regex search in changelog comment
5. **Naming Convention** — `re.fullmatch()` against field value
6. **Required Fields** — field must not be empty/null/blank

### What Gets Skipped Automatically

The plugin automatically exempts:
- All authentication and session models (`auth.*`, `users.*`, `sessions.*`)
- NetBox internal objects (`extras.objectchange`, `extras.journalentry`, `core.job`, etc.)
- The plugin's own models (`netbox_force.forcesettings`, `netbox_force.validationrule`, `netbox_force.violation`)
- Unauthenticated requests
- Management commands (no HTTP context)
- Changes where only timestamp fields changed (e.g. `last_updated`)

### Settings Storage

Settings are stored in a singleton database row (ForceSettings, pk=1) with a 30-second in-memory cache. The cache uses `threading.Lock()` for thread safety. Changes made through the UI take effect immediately (cache is invalidated on save).

`PLUGINS_CONFIG` values are used as initial defaults when the database row is first created. After that, the UI settings override config file values.

### API Support

The plugin enforces rules on both UI and API requests:
- **UI:** Reads changelog from the `comments` form field
- **API:** Reads changelog from the `changelog_message` JSON body field

API error messages are always in English, regardless of the language setting.

```bash
# API request with changelog message
curl -X PATCH https://netbox.example.com/api/dcim/devices/1/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "new-name", "changelog_message": "Renamed device per JIRA-1234"}'
```

## Navigation

After installation, superusers see four menu items under **NetBox Force** in the sidebar:

| Tab | Description |
|---|---|
| **Settings** | General configuration, enforcement rules, ticket reference, change window, audit log, exemptions |
| **Validation Rules** | CRUD for naming convention and required field rules |
| **Violations** | Filterable audit log of blocked changes |
| **Dashboard** | Statistics overview with feature status |

Regular users do not see the plugin menu items.

## Upgrading

```bash
# Reinstall from GitHub (latest)
pip install --upgrade --force-reinstall \
  https://github.com/Gasi-Code/netbox-force/archive/refs/heads/main.tar.gz

# Restart NetBox (migrations run automatically)
sudo systemctl restart netbox netbox-rq
```

For Docker, redeploy the stack — the container will pull the latest version on startup.

## Troubleshooting

### Plugin not appearing in sidebar
- Verify the plugin is installed: `pip show netbox-force`
- Verify `'netbox_force'` is in `PLUGINS` in `configuration.py`
- Check container logs for migration errors
- Ensure you are logged in as a **superuser** (regular users don't see the menu)

### "You do not have permission to access this page"
- The plugin settings are restricted to superusers. Log in with an admin account.

### Changes not being enforced
- Check that the user is not in the exempt users list
- Check that the model is not in the exempt models list
- Check that `enforce_on_create` is enabled (if testing with new objects)
- Check the container logs for `netbox.plugins.netbox_force` debug messages

### Migration errors on startup
- Ensure the plugin is installed before NetBox runs migrations
- For LinuxServer.io Docker: use `DOCKER_MODS` (not `custom-cont-init.d`)
- For official Docker: install in Dockerfile (not at runtime)

## License

Apache License 2.0 — see [LICENSE](LICENSE).

## Author

[Gasi-Code](https://github.com/Gasi-Code)
