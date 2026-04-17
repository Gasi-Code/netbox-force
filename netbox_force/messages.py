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
        'ticket_missing': (
            "Ticket-Referenz erforderlich! Der Changelog-Eintrag muss eine "
            "Ticket-Referenz enthalten. {hint}"
        ),
        'naming_violation': (
            "Namenskonvention verletzt! Das Feld '{field}' bei '{model}' "
            "entspricht nicht dem erforderlichen Muster. {hint}"
        ),
        'required_field': (
            "Pflichtfeld fehlt! Das Feld '{field}' bei '{model}' "
            "darf nicht leer sein."
        ),
        'change_window': (
            "Änderungen sind außerhalb des Änderungsfensters nicht erlaubt "
            "({start} - {end}, {weekdays})."
        ),
        'dry_run_prefix': '[DRY-RUN] ',
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
        'ticket_missing': (
            "Ticket reference required! The changelog entry must contain "
            "a ticket reference. {hint}"
        ),
        'naming_violation': (
            "Naming convention violated! The field '{field}' on '{model}' "
            "does not match the required pattern. {hint}"
        ),
        'required_field': (
            "Required field missing! The field '{field}' on '{model}' "
            "must not be empty."
        ),
        'change_window': (
            "Changes are not allowed outside the change window "
            "({start} - {end}, {weekdays})."
        ),
        'dry_run_prefix': '[DRY-RUN] ',
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
        'ticket_missing': (
            "Se requiere referencia de ticket. La entrada del registro de "
            "cambios debe contener una referencia de ticket. {hint}"
        ),
        'naming_violation': (
            "Convención de nombres violada. El campo '{field}' en '{model}' "
            "no coincide con el patrón requerido. {hint}"
        ),
        'required_field': (
            "Campo obligatorio faltante. El campo '{field}' en '{model}' "
            "no debe estar vacío."
        ),
        'change_window': (
            "No se permiten cambios fuera de la ventana de cambios "
            "({start} - {end}, {weekdays})."
        ),
        'dry_run_prefix': '[DRY-RUN] ',
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
    'ticket_missing': (
        "Ticket reference required. The changelog entry must contain a "
        "ticket reference. {hint}"
    ),
    'naming_violation': (
        "Naming convention violated. The field '{field}' on '{model}' "
        "does not match the required pattern. {hint}"
    ),
    'required_field': (
        "Required field missing. The field '{field}' on '{model}' "
        "must not be empty."
    ),
    'change_window': (
        "Changes are not allowed outside the change window "
        "({start} - {end}, {weekdays})."
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
