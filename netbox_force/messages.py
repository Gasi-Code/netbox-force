"""
Multilingual error messages for the NetBox Force plugin.
"""

MESSAGES = {
    'de': {
        'changelog_required': (
            "Changelog-Eintrag erforderlich! Beim {action} von '{model}' "
            "muss im Feld 'Änderungsgrund / Changelog' eine Begründung "
            "eingetragen werden (mind. {min_len} Zeichen)."
        ),
        'blacklisted': (
            "Unzulässiger Changelog-Eintrag! Der Text enthält gesperrte "
            "Begriffe: {words}"
        ),
        'action_create': 'Erstellen',
        'action_edit': 'Ändern',
        'action_delete': 'Löschen',
    },
    'en': {
        'changelog_required': (
            "Changelog entry required! When {action} '{model}', "
            "a reason must be provided in the 'Change reason / Changelog' "
            "field (min {min_len} characters)."
        ),
        'blacklisted': (
            "Invalid changelog entry! The text contains prohibited "
            "terms: {words}"
        ),
        'action_create': 'creating',
        'action_edit': 'modifying',
        'action_delete': 'deleting',
    },
    'es': {
        'changelog_required': (
            "Se requiere entrada en el registro de cambios. Al {action} "
            "'{model}', se debe proporcionar una razón en el campo "
            "'Motivo del cambio' (mín. {min_len} caracteres)."
        ),
        'blacklisted': (
            "Entrada de registro de cambios no válida. El texto contiene "
            "términos prohibidos: {words}"
        ),
        'action_create': 'crear',
        'action_edit': 'modificar',
        'action_delete': 'eliminar',
    },
}

# API messages are always in English
API_MESSAGES = {
    'changelog_required': (
        "Changelog entry required. When {action} '{model}', include a "
        "'changelog_message' field in the request body "
        "(min {min_len} characters)."
    ),
    'blacklisted': (
        "Invalid changelog entry. The text contains prohibited terms: {words}"
    ),
}


def get_message(key, language='de', **kwargs):
    """Returns a translated message for the given key and language."""
    lang_messages = MESSAGES.get(language, MESSAGES['en'])
    template = lang_messages.get(key, MESSAGES['en'].get(key, key))
    return template.format(**kwargs) if kwargs else template


def get_api_message(key, **kwargs):
    """Returns an API error message (always English)."""
    template = API_MESSAGES.get(key, key)
    return template.format(**kwargs) if kwargs else template
