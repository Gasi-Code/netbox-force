# NetBox Force — Documentation

The plugin interface is available in sixteen languages. This directory holds one
complete guide per language, covering installation, updating, configuration, and
every feature.

Language directories are named after the code used in the plugin's language
setting and are sorted alphabetically by that code.

| Code | Language | Guide |
|---|---|---|
| `cs` | čeština | [docs/cs/README.md](cs/README.md) |
| `da` | dansk | [docs/da/README.md](da/README.md) |
| `de` | Deutsch | [docs/de/README.md](de/README.md) |
| `en` | English | [docs/en/README.md](en/README.md) |
| `es` | español | [docs/es/README.md](es/README.md) |
| `fr` | français | [docs/fr/README.md](fr/README.md) |
| `it` | italiano | [docs/it/README.md](it/README.md) |
| `ja` | 日本語 | [docs/ja/README.md](ja/README.md) |
| `lv` | latviešu | [docs/lv/README.md](lv/README.md) |
| `nl` | Nederlands | [docs/nl/README.md](nl/README.md) |
| `pl` | polski | [docs/pl/README.md](pl/README.md) |
| `pt` | português | [docs/pt/README.md](pt/README.md) |
| `ru` | русский | [docs/ru/README.md](ru/README.md) |
| `tr` | Türkçe | [docs/tr/README.md](tr/README.md) |
| `uk` | українська | [docs/uk/README.md](uk/README.md) |
| `zh-hans` | 简体中文 | [docs/zh-hans/README.md](zh-hans/README.md) |

## How these files are organised

Every guide uses the same numbered sections in the same order, so a section can
be compared across languages without reading both in full:

1. What the plugin does
2. Requirements
3. Installation
4. Updating
5. Configuration file
6. The pages
7. Graylog — sending
8. Graylog — reading
9. Patch Management and CheckMK
10. Troubleshooting
11. Changing the language
12. License

## What is not translated

- **[CHANGELOG.md](../CHANGELOG.md)** — English only. Release notes are read by
  operators comparing what a release changed against what their installation
  does; a translated copy that drifts out of date is worse than one they have to
  read in English.
- **Messages sent to Graylog** — always English, regardless of the configured
  language. Graylog alert queries match on that text, and translating it would
  silently break every alert the moment somebody changed the UI language.
- **API error messages** — always English, so that scripts consuming the API do
  not have to cope with a server-side language setting.

The plugin interface itself *is* translated, and follows the language configured
in the plugin settings.

## Keeping them in sync

The interface strings live in `netbox_force/ui_strings.py` and are versioned with
the code. These guides are separate documents and will drift if a feature changes
and only one language is updated. When you change behaviour, either update every
guide or none — a half-updated set is harder to trust than an openly stale one.
The shared section numbering exists to make that check quick.
