# Security Policy

## Reporting a vulnerability

Report privately, not as a public issue.

Use GitHub's **[Report a vulnerability](https://github.com/Gasi-Code/netbox-force/security/advisories/new)**
form, which opens a private advisory visible only to the maintainers.

Please include the plugin version, the NetBox version, what an attacker gains,
and the steps to reproduce it. A proof of concept helps but is not required —
a clear description of the flaw is enough to start.

Expect a first response within seven days. Fixed issues are credited in the
changelog unless you ask otherwise.

## Supported versions

The latest release is the only one that receives fixes. This is a single-file
plugin installed with `pip install --force-reinstall`; upgrading is the
remediation path.

## Security model

Knowing what the plugin does and does not defend against saves everyone time.

### What the plugin protects

- **Changelog, blocklist and ticket enforcement** is decided from server-side
  facts only. A request cannot switch enforcement off by omitting a field.
- **Plugin administration pages** (settings, rules, policies, violations,
  Graylog configuration, widget images) require a superuser.
- **NetBox core data read on a user's behalf** — IP addresses, contacts,
  Graylog messages tied to an object — passes through NetBox's object
  permissions, so a user sees only what NetBox would show them.
- **Secrets at rest** — CheckMK automation secret, Graylog API token, webhook
  HMAC secret — are encrypted with a key derived from Django's `SECRET_KEY` and
  never rendered back into a form. A database dump alone does not expose them.
- **Uploaded widget images** are stored in the database, restricted to raster
  formats, checked against their own magic bytes, and served with a fixed
  Content-Type, `nosniff` and a sandbox policy.
- **Violation exports** neutralise spreadsheet formula prefixes, so text an
  attacker typed cannot execute when an administrator opens the CSV.

### What the plugin does not protect against

- **A NetBox superuser.** Superusers can run Custom Scripts, which is arbitrary
  code execution on the NetBox host. Plugin settings that reach outward — the
  webhook URL, the CheckMK and Graylog endpoints, validation-rule patterns, the
  guide page — are superuser-only by design and are not treated as a boundary.
- **The guide page's HTML.** Full HTML pages render inside a sandboxed iframe
  with no same-origin access; shorter content is filtered when `nh3` or
  `bleach` is installed. Neither is a NetBox requirement — where both are
  absent, inline guide content renders unfiltered and a warning is logged.
- **Reading patch data.** By default every logged-in NetBox user may read the
  patch pages. Set `patch_viewer_groups` in the plugin settings to restrict it;
  the list of servers, their OS versions and their maintenance windows is
  otherwise readable by any account.
- **A compromised CheckMK or Graylog.** Data pulled from them is length-bounded
  and HTML-escaped before display, but it is written into NetBox as fact.
- **Anything with TLS verification switched off.** `checkmk_verify_ssl`,
  `graylog_verify_ssl` and `graylog_api_verify_ssl` exist for self-signed
  labs. Off means the credentials for that service travel unauthenticated.

### Deployment notes

- Give the CheckMK automation user the built-in **guest** role. The plugin only
  reads, and never touches the Setup/WATO API.
- Keep `cryptography` installed. Without it, secrets fall back to plaintext
  storage and the settings page says so.
- The diagnostic probe (`NETBOX_FORCE_PROBE`) writes only to a regular file
  owned by the NetBox user and refuses to follow symlinks, but it still logs
  request field names. Remove the file when you are done with it.
