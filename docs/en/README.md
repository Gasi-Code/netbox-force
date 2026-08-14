# NetBox Force — Guide (English)

[← All languages](../README.md) · [Project README](../../README.md) · [Changelog](../../CHANGELOG.md)

---

## 1. What the plugin does

NetBox records *what* changed. NetBox Force decides *whether the change is allowed
at all*, and can require a reason before it goes through.

It sits between every save and delete operation and the database. Before a change
is written it can check that:

- a changelog comment was supplied, and is long enough
- the comment does not consist only of meaningless words
- the comment references a ticket number
- the change happens inside an approved time window
- field values match a naming pattern
- required fields are actually filled in

Two further modules come with it:

- **Patch Management** — patch status, operating system, responsible contacts and
  update history per virtual machine or physical server, optionally fed from CheckMK.
- **Graylog** — sends audit events out, and brings log information back next to
  the object it belongs to.

Everything is opt-in. After installation only the changelog presence check is
active, with a two-character minimum. Everything else is switched on in the web
interface.

---

## 2. Requirements

| Component | Version | Notes |
|---|---|---|
| NetBox | 4.0.0 or later | |
| Python | 3.10 or later | |
| PostgreSQL | — | Required by NetBox itself |
| `cryptography` | any | Ships with NetBox. Without it the CheckMK secret and the Graylog token are stored unencrypted, and the plugin says so on the settings page |
| `requests` | any | Ships with NetBox. Needed for CheckMK and Graylog |
| RQ worker | — | Only for the scheduled CheckMK sync and Graylog poll. Without a worker both still run on demand, and the page says so |

---

## 3. Installation

### 3.1 Install the package

```bash
source /opt/netbox/venv/bin/activate
pip install git+https://github.com/Gasi-Code/netbox-force.git
```

### 3.2 Register the plugin

In `configuration.py`:

```python
PLUGINS = ['netbox_force']
```

### 3.3 Run the migrations

```bash
cd /opt/netbox/netbox
python manage.py migrate netbox_force
python manage.py collectstatic --no-input
```

### 3.4 Restart NetBox

```bash
sudo systemctl restart netbox netbox-rq
```

### 3.5 Docker

```bash
docker exec -it <container> pip install git+https://github.com/Gasi-Code/netbox-force.git
docker exec -it <container> /opt/netbox/netbox/manage.py migrate netbox_force
docker restart <container>
```

On the LinuxServer.io image, do **not** use `custom-cont-init.d` scripts for the
installation. They run *after* NetBox's own init scripts, which can cause
migration failures. Docker Mods run before them.

An installation made inside a container filesystem does not survive an image
update. Add the plugin to the image's persistent plugin installation mechanism,
or it will be gone after the next pull.

---

## 4. Updating

```bash
source /opt/netbox/venv/bin/activate
pip install --force-reinstall --no-cache-dir git+https://github.com/Gasi-Code/netbox-force.git
```

`--force-reinstall --no-cache-dir` is needed because pip caches by version number
and would otherwise skip a rebuild of the same version.

**Check before restarting.** This step imports the plugin without touching the
running process. If it reports an error, do not restart — the running NetBox
still has the old code in memory and keeps working:

```bash
cd /opt/netbox/netbox
python manage.py check
```

Then:

```bash
python manage.py migrate netbox_force
python manage.py collectstatic --no-input
sudo systemctl restart netbox netbox-rq
```

### Going back

```bash
pip install --force-reinstall --no-cache-dir \
  git+https://github.com/Gasi-Code/netbox-force.git@<commit>
sudo systemctl restart netbox netbox-rq
```

The migrations usually do not have to be reversed. Extra columns do not disturb
older code — it simply does not know about them. Take a database dump before
updating anyway.

---

## 5. Configuration file

`PLUGINS_CONFIG` sets the **initial defaults only**. After the first start every
setting is managed in the web interface and stored in the database.

```python
PLUGINS_CONFIG = {
    'netbox_force': {
        'min_length': 2,
        'exempt_users': ['automation', 'monitoring', 'netbox'],
        'enforce_on_create': False,
        'enforce_on_delete': True,
        'extra_exempt_models': [],
        'checkmk_secret': '',
    },
}
```

| Setting | Default | Meaning |
|---|---|---|
| `min_length` | `2` | Minimum characters in a changelog entry |
| `exempt_users` | see above | Usernames exempt from all checks, case-insensitive |
| `enforce_on_create` | `False` | Require a changelog when creating objects |
| `enforce_on_delete` | `True` | Require a changelog when deleting objects |
| `extra_exempt_models` | `[]` | Further exempt models, format `app.model` |
| `checkmk_secret` | `''` | Optional. Keeps the CheckMK secret out of the database entirely; it then takes precedence over the UI field |

---

## 6. The pages

Superusers find **NetBox Force** in the sidebar. All pages are restricted to
superusers unless stated otherwise.

| Page | Purpose |
|---|---|
| **Settings** | Every enforcement setting, exemptions, modules, webhook, CheckMK |
| **Validation Rules** | Naming patterns and required fields, per model and field |
| **Model Policies** | Per-model overrides of the global enforcement settings |
| **Violations** | Filterable log of every blocked change, exportable as CSV |
| **Graylog** | Sending and reading, see sections 7 and 8 |
| **Dashboard** | Statistics: which features are on, blocked changes, top users, 30-day trend |
| **Import Templates** | Downloadable CSV templates for NetBox's bulk import. Visible to all logged-in users when enabled |
| **Guide** | A free-text page for your own users. Visible to all logged-in users when enabled |
| **Patch Management** | See section 9 |

Two settings deserve their own mention:

- **Global enforcement toggle** — pauses all checks, for example during a
  maintenance window.
- **Dry-run mode** — records violations without blocking anything. The right way
  to introduce a new rule: you see what *would* have been blocked before anybody
  is actually stopped.

---

## 7. Graylog — sending

Sends audit events from NetBox to Graylog over GELF.

### Why

Three things are recorded nowhere else in NetBox:

- **Failed logins.** NetBox does not keep them at all.
- **Client IP and user agent** on a change. The NetBox changelog carries neither.
- **Changes to the plugin's own settings.** These are not covered by the NetBox
  changelog, so switching enforcement off previously left no trace anywhere.

### Setting it up

On the **Graylog** page, upper half: host, port, transport. Then *Send test event*.

Start with **UDP**. If nothing arrives, switch to **TCP** — UDP cannot report a
failure by design, TCP can. That distinguishes "wrong port" from "message
discarded".

| Transport | Confirms delivery | Encrypted |
|---|---|---|
| UDP | no | no |
| TCP | yes | no |
| TCP + TLS | yes | yes |
| HTTP | yes | no |
| HTTPS | yes | yes |

UDP is right inside a local network and wrong across the internet.

### What is sent

One row per event type, each with a checkbox and a syslog severity: object
created, changed, deleted; login; logout; failed login; blocked change; plugin
settings changed.

### Volume

A request that changes more objects than the configured threshold is reported as
a **single summary event**. An import of 500 devices is one operation — 500
near-identical log lines make it harder to see, not easier.

Summarising rather than throttling is deliberate. A queue that drains slower than
it fills discards the *newest* events, which is the wrong half to lose.

### Field names

Every event carries the same fields, so searches stay simple:

```
_app          netbox_force
_category     object_change | auth | violation | settings
_event        object_created, login_failed, …
_username
_client_ip
_user_agent
_object_type  dcim.device
_object_id
_object_name
_action       create | update | delete
_changed_fields
_request_id
_netbox_url
_outside_business_hours
```

`_request_id` groups everything one request changed. Forty devices edited at once
is one operation, not forty riddles.

### Two things to know

- **A Graylog outage cannot slow down or fail a save in NetBox.** Events go onto a
  bounded queue drained by a background thread. When the queue is full, new events
  are dropped and counted, and the counter is shown on the page.
- **Message text is always English**, whatever the interface language. Graylog
  alert queries match on that text; translating it would silently break every
  alert the moment somebody changed the language.
- **The client IP is read from `X-Forwarded-For`** when present. That header comes
  from the client and can be forged if NetBox is reachable without a reverse proxy
  in front of it.

---

## 8. Graylog — reading

Brings Graylog information into NetBox so a host can be judged without opening a
second tab.

### Setting it up

Lower half of the **Graylog** page: web address and API token, then *Test
connection*. The result reports the Graylog version, the detected search API
form, the loudest sources and the available streams. *Poll now* runs one poll.

**Issue the token for a Graylog user with a read-only role.** That, and not this
plugin's code, is what guarantees Graylog cannot be altered from NetBox.

### What "read-only" means here, precisely

Every call either retrieves data or asks Graylog to run a search. The legacy
search endpoint is a plain `GET`. The newer Views search API is not: it requires a
`POST` to register a search and another to execute it. That creates a short-lived
search object inside Graylog and returns results — it does not change stored
data. If only `GET` is acceptable in your environment, pin the search form to
`legacy` in the settings.

### Matching sources to NetBox objects

Exact, in this order, first hit wins:

| | Rule |
|---|---|
| 1 | **Manual assignment** — once set, always wins |
| 2 | **IP address** — the source against every IP of the object |
| 3 | **Host name**, case-insensitive |
| 4 | **Host name after removing a configured domain suffix** |

Everything else stays unassigned and is listed as such.

**There is deliberately no fuzzy matching.** `srv-web-01` and `srv-web-02` differ
by one character, so any similarity measure calls them a 96% match — while being
two different machines. In a numbered naming scheme, which is to say in every
NetBox worth the name, the most similar candidate is systematically the wrong one.
Logs would be filed under the neighbouring server and nobody would notice.
Similarity is used only to *order* the suggestions next to an unassigned source;
it never assigns anything.

If a central syslog relay sits in front of Graylog, every message carries the
relay's address and rule 2 matches nothing useful. The source field then has to
carry the host name, which is what rules 3 and 4 are for.

### The pages

- **Sources** — everything Graylog reports, with counters, filterable by
  assigned, unassigned, silent, never-seen and ignored.
- **Silent** — mapped in NetBox, sending nothing. Dead, mis-configured, or a
  leftover record. Neither system can spot this alone.
- **Never seen in Graylog** — the other half of the cross-check.
- **Cluster** — nodes with green/yellow/red lamps, indexer health, journal
  backlog, each node linked to its NetBox VM.
- **On the object** — devices and VMs with a mapped source get a Graylog panel
  showing counters, recent messages on demand, and a link into Graylog.

### Load and safety

- One poll is a **single grouped query for all hosts**, not one query per device.
  A site with 800 devices costs three requests.
- The cluster panel and the message list load **after** the page has rendered. A
  slow or dead Graylog yields an empty panel, never a hung NetBox page.
- The mapping lives in the plugin's own table. **Graylog never writes to a NetBox
  core object** — removing the plugin removes the mapping and leaves NetBox
  untouched.
- The message endpoint only answers for a source mapped to an object the caller is
  allowed to view.

---

## 9. Patch Management and CheckMK

Tracks patch status, operating system, responsible contacts and update history per
virtual machine or physical server.

- **Status** green / yellow / red, either maintained by hand or read from CheckMK.
- **Overdue threshold** — entries not patched within N days are marked overdue.
- **Escalation** — an entry left in *yellow* for N days becomes *red* on its own.
- **Contacts** — administrator and process owner from NetBox's contact objects.
- **Update history** — one entry per patch run, with ticket number and note.
- **Access** is granted by NetBox group name in the plugin settings, not through
  Django permissions.

### CheckMK

The integration is a **pull**: NetBox reads from CheckMK. Nothing is written to
CheckMK, so a read-only automation user is sufficient.

Configured on the settings page: site URL, automation user, secret, service filter
and sync interval. The secret is stored encrypted and never shown again.

A stalled sync is the failure mode that hurts most, because the page keeps showing
a patch status that quietly stopped being true. The dashboard therefore states
outright when the last successful sync is older than twice the configured interval.

---

## 10. Troubleshooting

**The plugin does not appear in the sidebar.**
`PLUGINS` set in `configuration.py`? Migrations run? NetBox restarted? Sidebar
labels only update on restart — the tabs inside the plugin update immediately.

**Changes are not being blocked.**
Check, in this order: the global enforcement toggle, dry-run mode, whether your
user is in the exempt users or exempt groups, and whether a Model Policy disables
enforcement for that model.

**A page reports a missing column.**
Migrations have not been run, or only partly. `python manage.py migrate netbox_force`.

**"No background worker is running."**
`netbox-rq` is not running. The CheckMK sync and the Graylog poll then only run
when you press the button.

**Nothing arrives in Graylog.**
Switch the transport from UDP to TCP. UDP cannot report a failure; TCP can, and
its error message says whether the port is wrong or the message was rejected.

**The Graylog panel on a device stays empty.**
The device has no mapped source. Open *Sources → Unassigned* and assign it, or add
your domain suffix to the settings so the FQDN can be shortened.

**After changing `SECRET_KEY`, the CheckMK secret or the Graylog token no longer works.**
Both are encrypted with a key derived from `SECRET_KEY`. They have to be entered
again.

---

## 11. Changing the language

The language is a **per-installation** setting, not a per-user one. It is changed
on the settings page.

Tabs and pages inside the plugin change over immediately. The sidebar labels are
built once at startup and only change after NetBox is restarted.

Enforcement messages shown to users follow this setting. API error messages and
messages sent to Graylog stay English — see the note in the
[documentation index](../README.md).

---

## 12. License

AGPL-3.0. See [LICENSE](../../LICENSE).
