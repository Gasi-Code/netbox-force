# Changelog

All notable changes to NetBox Force.

This file is kept in English only. Version notes are read by operators comparing
what a release changed against what their installation does, and a translated
copy that drifts out of date is worse than one they have to read in English.
The user-facing documentation is translated — see [docs/](docs/).

Version numbers follow the plugin version reported in the NetBox UI and by
`pip show netbox-force`.

---

### v5.8.0 — Reading Graylog back into NetBox

- **Graylog information next to the object it belongs to.** Devices and virtual machines get a panel with the message, error and warning counts for that host, its recent messages on demand, and a link that opens the matching search in Graylog.
- **Source inventory.** Everything Graylog reports, with counters, filterable by assigned, unassigned, silent, never-seen and ignored.
- **Exact matching only** — manual assignment, then IP address, then host name, then host name after removing a configured domain suffix. First hit wins.
- **No fuzzy matching, deliberately.** `srv-web-01` and `srv-web-02` differ by one character, so any similarity score calls them a 96% match while they are two different machines. In a numbered naming scheme the most similar candidate is systematically the wrong one, and the logs would be filed under the neighbouring server unnoticed. Similarity now only orders the suggestions offered next to an unassigned source; it never assigns.
- **Silent hosts.** Mapped in NetBox, sending nothing to Graylog — dead, mis-configured, or a leftover record. Neither system can spot this alone.
- **Never seen in Graylog.** The other half of the cross-check: devices and VMs that never appeared under any recognised name.
- **Cluster status** with green/yellow/red lamps, indexer health, journal backlog, and each node linked to its NetBox VM.
- **One grouped query per poll**, not one query per device. A site with 800 devices costs three requests.
- **Graylog cannot write to NetBox.** Mappings live in the plugin's own table with a generic reference; removing the plugin removes the mapping and leaves NetBox untouched.
- **The message endpoint answers only for a source mapped to an object the caller may view.** Without that check any account could read any host's logs by guessing its name.
- **The API token is encrypted at rest** with a key derived from Django's `SECRET_KEY`. `secretstore` now takes a purpose, so the CheckMK secret keeps decoding under its original key.
- **On "read-only":** every call retrieves data or asks Graylog to run a search. The legacy search endpoint is a plain `GET`; the newer Views API needs a `POST` to register and execute a search, which returns results without storing anything. The search form can be pinned to `legacy` if only `GET` is acceptable. The real guarantee is the token — issue it for a read-only role.
- Migration `0028_graylog_readback`.

### v5.7.0 — Sending audit events to Graylog

- **Events NetBox otherwise keeps nowhere.** Failed logins are not recorded anywhere in NetBox; the changelog carries no client IP or user agent; and `ForceSettings` is a plain model the changelog does not cover, so switching enforcement off previously left no trace at all.
- **Selectable per event type** — object created, changed and deleted, login, logout, failed login, blocked change, and changes to the plugin settings — each with its own checkbox and syslog severity.
- **Object changes are read from NetBox's own change records** in the middleware pass that already runs after the view returns, rather than captured with a second set of signal handlers. That keeps the events post-commit and adds the two things those records lack: client IP and user agent.
- **A Graylog outage cannot slow down or fail a save.** Events go onto a bounded queue drained by a background thread. Once the queue is full, new events are dropped and counted, and the counter is shown on the settings page.
- **Transports:** GELF over UDP, TCP, TCP+TLS, HTTP and HTTPS. Oversized UDP datagrams are chunked per the GELF specification.
- **Bulk operations are summarised, not throttled.** A request changing more objects than a configurable threshold becomes one summary event. A queue that drains slower than it fills discards the newest events, which is the wrong half to lose.
- **Settings changes are reported from the state before the save.** Reading the current settings would suppress the very event that records Graylog output being switched off.
- **Message text is always English** regardless of the UI language. Graylog alert queries match on it, and translating it would silently break every alert the moment the language changed.
- **Business hours.** Every event carries an `outside_business_hours` field; events inside the window can optionally be suppressed entirely.
- Migration `0027_graylog_output`.

### v5.6.0 — Changelog enforcement on deletion

- **Deleting a single object now asks for a reason.** NetBox collects a changelog message on every form except the single-object delete dialog, so a deletion could previously be neither recorded with a reason nor enforced. The field is added to that dialog.
- **NetBox's own change record no longer satisfies the requirement.** The record NetBox writes for a deletion was being counted as the user's changelog entry, which made the check pass without anyone having typed anything.
- **The deleted object is named** in the recorded message, and field labels in generated messages follow the configured plugin language.
- **The requirement is decided from the submitted form, not from the model.** A form with no changelog field can no longer be blocked for not carrying one — that produced an error the user had no way to satisfy.

### v5.5.0 — Correctness fixes

- **Error messages name the limit that actually blocked**, and explain the difference between the two rule pages instead of leaving the user to guess which one applied.
- **The delete action is named correctly** in changelog error messages.
- **The plugin version is read from the app registry** rather than written into a template, so it can no longer drift from the installed package.
- **`0026_repair_nullability`** drops `NOT NULL` where the model allows `NULL`, derived from the model state rather than from a hardcoded list.

### v5.4.0

- **The scheduled sync no longer stalls silently.** The scheduled entry lives in Redis while the job row lives in Postgres; a container restart could lose the former and keep the latter, and `enqueue_once()` then saw a job it believed was already scheduled and created nothing. Rows overdue by more than twice the interval are now discarded and re-enqueued at startup.
- **A stalled sync is visible.** The dashboard states outright when the last successful sync is older than twice the configured interval, instead of showing a patch status that quietly stopped being true.
- **Dashboard covers Patch Management.** Patch status distribution with counts of auto-escalated entries, and an *Open gaps* panel listing entries without a NetBox object, CheckMK addresses missing from IPAM, and hosts CheckMK no longer reports.
- **Model Policies reachable from the sidebar.** The page, its views and its translations all existed; only the navigation entry was missing, so it could be found by typing the URL and no other way.

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


