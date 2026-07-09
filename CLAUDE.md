# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**NetBox Force** (`netbox_force/`) is a NetBox plugin (Python/Django) that enforces changelog discipline, naming conventions, required fields, ticket references, change windows, and compliance auditing on every NetBox object change. It is installed into an external NetBox instance via `PLUGINS` in `configuration.py` — there is no standalone way to run or serve this repo.

This repo also contains unrelated legacy/auxiliary material — see "Non-Plugin Content" below before assuming a file belongs to the plugin.

## Commands

There is no build step — this is a pure Python/Django plugin package.

```bash
pip install -e .                     # editable install into a NetBox venv
python manage.py migrate netbox_force  # run from within NetBox's manage.py, after install
pytest                                # runs netbox_force/tests/ (per pyproject.toml), but requires
                                       # a configured NetBox/Django settings module — typically run
                                       # via NetBox's own test runner: manage.py test netbox_force
```

`pip install --force-reinstall --no-cache-dir git+...` is required for updates (pip caches by version number) — see README "Updating" section.

## Architecture

### Plugin Registration (`netbox_force/apps.py`)

`NetboxForceConfig` registers the plugin with NetBox. Key points:
- `middleware` registers `RequestContextMiddleware` (stores the current request in thread-local storage so signal handlers can access it).
- `menu = '_menu'` — NetBox resolves this as `import_string("netbox_force.apps._menu")`, a module-level `PluginMenu` instance (not a function call). `_menu` starts with English labels; `ready()` calls `_localize_menu()` to rebuild it from the DB language setting before the first request. **Sidebar labels only update on NetBox restart** — in-plugin tab labels update on every request via `ui_strings.py`.
- `ready()` imports `signals` (connects `pre_save`/`pre_delete` handlers) and `dashboards` (registers `@register_widget` dashboard widgets) as side effects.

### Settings & Caching Pattern

`ForceSettings` (`models.py`) is a singleton model (`pk=1` enforced in `save()`). All plugin configuration is read from the DB, not files, after first startup — `PLUGINS_CONFIG` in NetBox's `configuration.py` only seeds initial defaults via `_init_from_config()`.

`ForceSettings.get_settings()`, `ValidationRule.get_active_rules()`, and `ModelPolicy.get_all_policies()` all share the same pattern: a 30-second thread-safe in-memory cache, wrapped in a DB `SAVEPOINT` so a failed query (e.g. table not yet migrated) rolls back only the savepoint and not NetBox's outer transaction. When modifying caching behavior, preserve this savepoint pattern — without it, a failed settings lookup during migration can abort an unrelated PostgreSQL transaction.

### Enforcement Flow

```
HTTP Request → RequestContextMiddleware (thread-local request storage)
            → Model.save()/delete() → pre_save/pre_delete signal (signals.py)
            → exemption checks (model/user/group/global toggle/no real change)
            → change window → naming convention → required field
            → changelog presence/length → blocked phrases → ticket reference
            → AbortRequest raised on first failure, else save/delete proceeds
```

- Violations are not written inside the signal handler — `AbortRequest` triggers a DB rollback that would also roll back a `Violation.objects.create()` call made there. Instead, `middleware.queue_pending_violation()` buffers violation dicts in thread-local storage, and `RequestContextMiddleware._flush_pending_violations()` writes them (and fires webhooks) **after** the view returns, outside `transaction.atomic()`. Any new violation-reason code path must use this queue, not a direct `Violation.objects.create()`.
- Changelog comment is read from `comments` (UI form field) or `changelog_message` (API JSON body) — see `get_changelog_comment()` in `signals.py`.
- `EXEMPT_MODELS` in `signals.py` hardcodes system models (auth, sessions, NetBox internals, migration recorder) that must never be checked, independent of user-configured exemptions.

### i18n

Two parallel translation dicts, both keyed by language code (`cs`, `da`, `de`, `en`, `es`, `fr`, `it`, `ja`, `lv`, `nl`, `pl`, `pt`, `ru`, `tr`, `uk`, `zh-hans`):
- `messages.py` — user-facing `AbortRequest`/`ValidationError` text (enforcement-blocking messages). API responses always use English regardless of the configured language.
- `ui_strings.py` — labels/help text for plugin views and dashboard widgets, fetched via `get_all_ui_strings(lang)`.

Language is a per-installation DB setting (`ForceSettings.language`), not a per-request/per-user Django locale.

### Views & URLs

`views.py` is organized by feature area (Settings, Validation Rules, Model Policies, Audit Scan, Violations, Dashboard, Import Templates, Guide, Widget Images) matching the route groups in `urls.py`. Most views require `SuperuserRequiredMixin`; a few (Import Templates download, Guide) use `AuthenticatedRequiredMixin`. `_base_context()` / `_get_ui_context()` in `views.py` are the shared helpers every view uses to inject `ui` (translated strings) and `force_settings` into templates.

### Dashboards

`dashboards.py` registers NetBox home-dashboard widgets via `@register_widget`. Widget `description`/`default_title` use the `_LocalizedAttr` descriptor to read `ui_strings` at class-attribute access time (not `__init__`), since NetBox renders these without instantiating the widget per request in all code paths.

## Non-Plugin Content

This repo currently mixes the active plugin with leftover/unrelated material — don't assume every file is part of `netbox_force`:

- **`netbox_changelog_enforcer/`** and the root-level `__init__.py`, `apps.py`, `middleware.py`, `signals.py` — an earlier, simpler prototype plugin that `netbox_force` superseded and replaced (see commit history and `CLAUDE_CODE_HANDOFF.md`, itself a German-language handoff doc for that prototype, now superseded). These are untracked in git; treat as historical reference only, not live code.
- **`netbox_force/templates/netbox_force/wizard_*.html`** — leftover templates from a guided-wizard feature that was fully removed from the plugin (commit `5507ba4`, "remove: vollständige Entfernung des Wizard-Features"). No view or URL in `views.py`/`urls.py` references them anymore.
- **`wizard_scripts/`** — standalone NetBox *Custom Scripts* (`extras.scripts.Script` subclasses) for a specific organization's NetBox deployment, run via NetBox's own Custom Scripts feature. Unrelated to the `netbox_force` plugin and not packaged/installed with it. `wizard_scripts/PERMISSIONS.md` documents the permission groups for running these scripts.

When asked to work "on the plugin," scope changes to `netbox_force/` unless told otherwise.
