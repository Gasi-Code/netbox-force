"""
Dynamic UI translations for the NetBox Force plugin.
Used by views to provide language-dependent labels in templates.
"""

UI_STRINGS = {
    'de': {
        # Tabs
        'tab_settings': 'Einstellungen',
        'tab_rules': 'Validierungsregeln',
        'tab_violations': 'Verstöße',
        'tab_dashboard': 'Dashboard',

        # Section headers
        'section_language': 'Sprache',
        'section_enforcement': 'Erzwingungsregeln',
        'section_blocked_phrases': 'Gesperrte Begriffe',
        'section_exemptions': 'Ausnahmen',
        'section_ticket': 'Ticket-Referenz',
        'section_change_window': 'Änderungsfenster',
        'section_audit_log': 'Audit-Log',

        # Field labels
        'label_language': 'Sprache',
        'label_min_length': 'Mindestlänge Changelog',
        'label_enforce_on_create': 'Beim Erstellen erzwingen',
        'label_enforce_on_delete': 'Beim Löschen erzwingen',
        'label_exempt_users': 'Ausgenommene Benutzer',
        'label_blacklisted_phrases': 'Gesperrte Begriffe',
        'label_extra_exempt_models': 'Ausgenommene Modelle',
        'label_ticket_pattern': 'Ticket-Muster (Regex)',
        'label_ticket_pattern_hint': 'Ticket-Beispiel (Fehlermeldung)',
        'label_change_window_enabled': 'Änderungsfenster aktivieren',
        'label_change_window_start': 'Startzeit',
        'label_change_window_end': 'Endzeit',
        'label_change_window_weekdays': 'Erlaubte Wochentage',
        'label_audit_log_enabled': 'Audit-Log aktivieren',
        'label_audit_log_retention_days': 'Aufbewahrungsdauer (Tage)',
        'label_dashboard_top_users_count': 'Top-Benutzer im Dashboard',
        'label_dry_run': 'Dry-Run-Modus',

        # Help texts
        'help_language': 'Sprache für Fehlermeldungen in der NetBox-UI. API-Nachrichten sind immer auf Englisch.',
        'help_min_length': 'Mindestanzahl an Zeichen für einen Changelog-Eintrag.',
        'help_enforce_on_create': 'Wenn aktiviert, wird auch beim Erstellen neuer Objekte ein Changelog-Eintrag verlangt.',
        'help_enforce_on_delete': 'Wenn aktiviert, wird auch beim Löschen von Objekten ein Changelog-Eintrag verlangt.',
        'help_exempt_users': 'Ein Benutzername pro Zeile.',
        'help_blacklisted_phrases': 'Ein Begriff pro Zeile. Changelog-Einträge die diese Begriffe (als ganze Wörter) enthalten, werden abgelehnt.',
        'help_extra_exempt_models': 'Ein Model pro Zeile (Format: app.model, z.B. myplugin.mymodel).',
        'help_ticket_pattern': 'Regex-Muster für erforderliche Ticket-Referenzen (z.B. JIRA-\\d+ oder #\\d+). Leer lassen zum Deaktivieren.',
        'help_ticket_pattern_hint': 'Verständliches Beispiel, das dem Benutzer in der Fehlermeldung angezeigt wird (z.B. "JIRA-1234 oder CHG0012345"). Wenn leer, wird das Regex-Muster angezeigt.',
        'help_change_window_enabled': 'Wenn aktiviert, sind Änderungen nur innerhalb des definierten Zeitfensters erlaubt.',
        'help_change_window_start': 'Beginn des erlaubten Änderungszeitraums.',
        'help_change_window_end': 'Ende des erlaubten Änderungszeitraums.',
        'help_change_window_weekdays': 'Kommagetrennte ISO-Wochentage (1=Montag, 7=Sonntag).',
        'help_audit_log_enabled': 'Wenn aktiviert, werden alle abgelehnten Änderungen protokolliert.',
        'help_audit_log_retention_days': 'Anzahl der Tage, die Audit-Einträge aufbewahrt werden. Ältere Einträge werden automatisch gelöscht.',
        'help_dashboard_top_users_count': 'Anzahl der Benutzer in der Top-Liste im Dashboard.',
        'help_dry_run': 'Wenn aktiviert, werden Verstöße nur protokolliert, aber Änderungen nicht blockiert. Nützlich zum schrittweisen Einführen neuer Regeln.',

        # Buttons
        'btn_save': 'Speichern',
        'btn_add_rule': 'Regel hinzufügen',
        'btn_edit': 'Bearbeiten',
        'btn_delete': 'Löschen',
        'btn_cancel': 'Abbrechen',
        'btn_confirm_delete': 'Löschen bestätigen',
        'btn_apply_filter': 'Filter anwenden',
        'btn_clear_filter': 'Filter zurücksetzen',

        # Rules page
        'rules_title': 'Validierungsregeln',
        'rules_empty': 'Keine Validierungsregeln definiert.',
        'rules_col_type': 'Typ',
        'rules_col_model': 'Model',
        'rules_col_field': 'Feld',
        'rules_col_pattern': 'Muster',
        'rules_col_message': 'Fehlermeldung',
        'rules_col_enabled': 'Aktiv',
        'rules_col_actions': 'Aktionen',
        'rule_add_title': 'Regel hinzufügen',
        'rule_edit_title': 'Regel bearbeiten',
        'rule_delete_title': 'Regel löschen',
        'rule_delete_confirm': 'Soll diese Regel wirklich gelöscht werden?',
        'rule_type_naming': 'Namenskonvention',
        'rule_type_required': 'Pflichtfeld',
        'rule_help_title': 'Hilfe',
        'rule_help_naming_desc': 'Stellt sicher, dass ein Feldwert einem Regex-Muster entspricht. Verwendet Pythons re.fullmatch(), d.h. der gesamte Wert muss übereinstimmen.',
        'rule_help_naming_examples': 'Beispiele:',
        'rule_help_naming_ex1': 'entspricht ABC-123',
        'rule_help_naming_ex2': 'muss mit Präfix beginnen',
        'rule_help_required_desc': 'Stellt sicher, dass ein Feld nicht leer, null oder blank ist. Nützlich für Felder, die in NetBox optional sind, aber in Ihrer Organisation Pflicht.',
        'rule_help_common_models': 'Häufige Modelle:',
        'rule_help_type_naming_desc': 'Feldwert muss einem Regex-Muster entsprechen.',
        'rule_help_type_required_desc': 'Feld muss einen nicht-leeren Wert haben.',
        'rule_help_model_format': 'Format: app.model (z.B. dcim.device, ipam.ipaddress)',
        'rule_help_field_desc': 'Das zu validierende Modellfeld (z.B. name, description, tenant)',
        'rule_help_pattern_desc': 'Nur für Namenskonventionen. Der Feldwert muss vollständig diesem Regex-Muster entsprechen. Hinweis: Umlaute (ÄÖÜäöüß) müssen explizit im Pattern stehen, z.B. [A-ZÄÖÜ] statt nur [A-Z].',
        'rule_help_error_msg_desc': 'Wird dem Benutzer bei fehlgeschlagener Validierung angezeigt. Leer lassen für Standardmeldung.',
        'rule_test_placeholder': 'Testwert eingeben...',
        'dashboard_col_count': 'Anzahl',

        # Violations page
        'violations_title': 'Verstöße',
        'violations_empty': 'Keine Verstöße erfasst.',
        'violations_disabled_warning': 'Das Audit-Log ist deaktiviert. Verstöße werden nicht aufgezeichnet.',
        'violations_col_timestamp': 'Zeitstempel',
        'violations_col_username': 'Benutzer',
        'violations_col_model': 'Model',
        'violations_col_object': 'Objekt',
        'violations_col_action': 'Aktion',
        'violations_col_reason': 'Grund',
        'violations_col_message': 'Nachricht',
        'filter_reason': 'Grund',
        'filter_username': 'Benutzer',
        'filter_date_from': 'Von',
        'filter_date_to': 'Bis',
        'filter_all': 'Alle',

        # Dashboard
        'dashboard_title': 'Dashboard',
        'dashboard_feature_status': 'Feature-Status',
        'dashboard_total_violations': 'Verstöße gesamt',
        'dashboard_by_reason': 'Verstöße nach Grund',
        'dashboard_top_users': 'Top {count} Benutzer',
        'dashboard_over_time': 'Verstöße (letzte 30 Tage)',
        'dashboard_active_rules': 'Aktive Regeln',
        'dashboard_enabled': 'Aktiviert',
        'dashboard_disabled': 'Deaktiviert',
        'dashboard_changelog_enforcement': 'Changelog-Erzwingung',
        'dashboard_ticket_reference': 'Ticket-Referenz',
        'dashboard_change_window': 'Änderungsfenster',
        'dashboard_audit_log': 'Audit-Log',
        'dashboard_no_data': 'Keine Daten vorhanden.',
        'dashboard_dry_run': 'Dry-Run-Modus',

        # Violations page extras
        'btn_export_csv': 'CSV-Export',

        # Dashboard buttons
        'btn_reset_violations': 'Verstöße zurücksetzen',
        'btn_export_dashboard': 'Statistiken exportieren',
        'dashboard_reset_confirm': 'Sollen wirklich ALLE Verstöße gelöscht werden? Diese Aktion kann nicht rückgängig gemacht werden.',

        # Info sidebar
        'info_title': 'Info',
        'info_plugin': 'Plugin',
        'info_version': 'Version',
        'info_author': 'Autor',
        'info_note': 'Änderungen werden sofort wirksam. Diese Einstellungen überschreiben Werte aus configuration.py.',

        # Modules section (settings)
        'section_modules': 'Module',
        'label_import_templates_enabled': 'Import-Vorlagen aktivieren',
        'label_guide_enabled': 'Benutzer-Anleitung aktivieren',
        'help_import_templates_enabled': 'Wenn aktiviert, können CSV-Import-Vorlagen für alle Benutzer bereitgestellt werden.',
        'help_guide_enabled': 'Wenn aktiviert, wird eine bearbeitbare Benutzer-Anleitung im Plugin angezeigt.',

        # Tabs (new)
        'tab_import_templates': 'Import-Vorlagen',
        'tab_guide': 'Anleitung',

        # Import Templates
        'import_templates_title': 'Import-Vorlagen',
        'import_templates_empty': 'Keine Import-Vorlagen vorhanden.',
        'import_templates_admin_title': 'Import-Vorlagen verwalten',
        'import_template_add_title': 'Vorlage hinzufügen',
        'import_template_edit_title': 'Vorlage bearbeiten',
        'import_template_delete_title': 'Vorlage löschen',
        'import_template_delete_confirm': 'Soll diese Vorlage wirklich gelöscht werden?',
        'import_templates_col_name': 'Name',
        'import_templates_col_model': 'Model',
        'import_templates_col_enabled': 'Aktiv',
        'import_templates_col_actions': 'Aktionen',
        'import_templates_col_description': 'Beschreibung',
        'btn_add_template': 'Vorlage hinzufügen',
        'btn_download': 'Herunterladen',
        'btn_auto_generate': 'CSV-Header generieren',
        'btn_manage_templates': 'Vorlagen verwalten',

        # Guide
        'guide_title': 'Anleitung',
        'guide_empty': 'Noch keine Anleitung erstellt.',
        'guide_edit_title': 'Anleitung bearbeiten',
        'guide_last_updated': 'Zuletzt aktualisiert',
        'guide_updated_by': 'von',
        'btn_edit_guide': 'Anleitung bearbeiten',
        'guide_editor_hint': 'WYSIWYG-Modus für einfache Inhalte oder HTML-Code-Modus für vollständige HTML-Seiten (mit eigenem CSS/JS). Vollständige HTML-Seiten werden in einem isolierten Frame dargestellt.',
        'guide_preview_label': 'Vorschau',
        'guide_confirm_switch': 'Der HTML-Inhalt ist eine vollständige Seite mit eigenem CSS/JS. Im WYSIWYG-Modus geht die Formatierung verloren. Trotzdem wechseln?',

        # Feature disabled
        'feature_disabled_title': 'Funktion deaktiviert',
        'feature_disabled_message': 'Diese Funktion ist derzeit deaktiviert. Ein Administrator kann sie in den Plugin-Einstellungen aktivieren.',

        # Dashboard (new)
        'dashboard_import_templates': 'Import-Vorlagen',
        'dashboard_guide': 'Benutzer-Anleitung',

        # Widget text (dashboard widgets)
        'widget_guide_btn': 'Anleitung',
        'widget_guide_disabled': 'Guide ist deaktiviert.',
        'widget_templates_disabled': 'Import-Vorlagen sind deaktiviert.',
        'widget_templates_all': 'Alle Vorlagen',

        # Widget setup hints
        'widget_hint_title': 'Dashboard-Widget einrichten',
        'widget_hint_guide_text': 'Um einen Schnellzugriff auf die Anleitung im NetBox-Dashboard zu erstellen: Home \u2192 Widget hinzuf\u00fcgen \u2192 "Note" w\u00e4hlen \u2192 folgenden Markdown-Inhalt einf\u00fcgen:',
        'widget_hint_guide_markdown': '### \U0001f4d6 Anleitung\n\nHier findest du die interne Anleitung:\n\n[\u2192 Zur Anleitung](/plugins/netbox-force/guide/)',
        'widget_hint_import_text': 'Um einen Schnellzugriff auf die Import-Vorlagen im NetBox-Dashboard zu erstellen: Home \u2192 Widget hinzuf\u00fcgen \u2192 "Note" w\u00e4hlen \u2192 folgenden Markdown-Inhalt einf\u00fcgen:',
        'widget_hint_import_markdown': '### \U0001f4e5 Import-Vorlagen\n\nCSV-Vorlagen f\u00fcr den Bulk-Import:\n\n[\u2192 Zu den Import-Vorlagen](/plugins/netbox-force/import-templates/)',

        # Settings sections (v4.3.0)
        'section_enforcement_toggle': 'Globale Erzwingung',

        # Settings fields (v4.3.0)
        'label_enforcement_enabled': 'Erzwingung aktiviert',
        'help_enforcement_enabled': 'Hauptschalter. Deaktivieren pausiert alle Enforcement-Pr\u00fcfungen global (z.B. w\u00e4hrend Wartungsfenstern). Dry-Run-Modus ist eine sanftere Alternative.',
    },

    'en': {
        # Tabs
        'tab_settings': 'Settings',
        'tab_rules': 'Validation Rules',
        'tab_violations': 'Violations',
        'tab_dashboard': 'Dashboard',

        # Section headers
        'section_language': 'Language',
        'section_enforcement': 'Enforcement Rules',
        'section_blocked_phrases': 'Blocked Phrases',
        'section_exemptions': 'Exemptions',
        'section_ticket': 'Ticket Reference',
        'section_change_window': 'Change Window',
        'section_audit_log': 'Audit Log',

        # Field labels
        'label_language': 'Language',
        'label_min_length': 'Minimum changelog length',
        'label_enforce_on_create': 'Enforce on create',
        'label_enforce_on_delete': 'Enforce on delete',
        'label_exempt_users': 'Exempt users',
        'label_blacklisted_phrases': 'Blocked phrases',
        'label_extra_exempt_models': 'Exempt models',
        'label_ticket_pattern': 'Ticket pattern (Regex)',
        'label_ticket_pattern_hint': 'Ticket example (error message)',
        'label_change_window_enabled': 'Enable change window',
        'label_change_window_start': 'Start time',
        'label_change_window_end': 'End time',
        'label_change_window_weekdays': 'Allowed weekdays',
        'label_audit_log_enabled': 'Enable audit log',
        'label_audit_log_retention_days': 'Retention period (days)',
        'label_dashboard_top_users_count': 'Top users in dashboard',
        'label_dry_run': 'Dry-run mode',

        # Help texts
        'help_language': 'Language for error messages in the NetBox UI. API messages are always in English.',
        'help_min_length': 'Minimum number of characters required for a changelog entry.',
        'help_enforce_on_create': 'If enabled, a changelog entry is also required when creating new objects.',
        'help_enforce_on_delete': 'If enabled, a changelog entry is also required when deleting objects.',
        'help_exempt_users': 'One username per line.',
        'help_blacklisted_phrases': 'One phrase per line. Changelog entries containing any of these phrases (as whole words) will be rejected.',
        'help_extra_exempt_models': 'One model per line (format: app.model, e.g. myplugin.mymodel).',
        'help_ticket_pattern': 'Regex pattern for required ticket references (e.g. JIRA-\\d+ or #\\d+). Leave empty to disable.',
        'help_ticket_pattern_hint': 'Human-readable example shown to users in error messages (e.g. "JIRA-1234 or CHG0012345"). If empty, the raw regex pattern is shown.',
        'help_change_window_enabled': 'If enabled, changes are only allowed within the defined time window.',
        'help_change_window_start': 'Start of the allowed change period.',
        'help_change_window_end': 'End of the allowed change period.',
        'help_change_window_weekdays': 'Comma-separated ISO weekday numbers (1=Monday, 7=Sunday).',
        'help_audit_log_enabled': 'If enabled, all rejected changes are logged for compliance tracking.',
        'help_audit_log_retention_days': 'Number of days to retain audit log entries. Older entries are automatically deleted.',
        'help_dashboard_top_users_count': 'Number of users shown in the dashboard top list.',
        'help_dry_run': 'If enabled, violations are logged but changes are not blocked. Useful for gradually rolling out new rules.',

        # Buttons
        'btn_save': 'Save',
        'btn_add_rule': 'Add Rule',
        'btn_edit': 'Edit',
        'btn_delete': 'Delete',
        'btn_cancel': 'Cancel',
        'btn_confirm_delete': 'Confirm Delete',
        'btn_apply_filter': 'Apply Filter',
        'btn_clear_filter': 'Clear Filter',

        # Rules page
        'rules_title': 'Validation Rules',
        'rules_empty': 'No validation rules defined.',
        'rules_col_type': 'Type',
        'rules_col_model': 'Model',
        'rules_col_field': 'Field',
        'rules_col_pattern': 'Pattern',
        'rules_col_message': 'Error Message',
        'rules_col_enabled': 'Enabled',
        'rules_col_actions': 'Actions',
        'rule_add_title': 'Add Rule',
        'rule_edit_title': 'Edit Rule',
        'rule_delete_title': 'Delete Rule',
        'rule_delete_confirm': 'Are you sure you want to delete this rule?',
        'rule_type_naming': 'Naming Convention',
        'rule_type_required': 'Required Field',
        'rule_help_title': 'Help',
        'rule_help_naming_desc': 'Ensures that a field value matches a regex pattern. Uses Python\'s re.fullmatch(), so the entire value must match.',
        'rule_help_naming_examples': 'Examples:',
        'rule_help_naming_ex1': 'matches ABC-123',
        'rule_help_naming_ex2': 'must start with prefix',
        'rule_help_required_desc': 'Ensures that a field is not empty, null, or blank. Useful for fields that are optional in NetBox by default but required by your organization.',
        'rule_help_common_models': 'Common models:',
        'rule_help_type_naming_desc': 'Field value must match a regex pattern.',
        'rule_help_type_required_desc': 'Field must have a non-empty value.',
        'rule_help_model_format': 'Format: app.model (e.g. dcim.device, ipam.ipaddress)',
        'rule_help_field_desc': 'The model field to validate (e.g. name, description, tenant)',
        'rule_help_pattern_desc': 'Only for naming rules. The field value must fully match this regex pattern. Note: Umlauts (ÄÖÜäöüß) must be explicitly included in patterns, e.g. [A-ZÄÖÜ] instead of just [A-Z].',
        'rule_help_error_msg_desc': 'Shown to the user when validation fails. Leave empty for default message.',
        'rule_test_placeholder': 'Enter test value...',
        'dashboard_col_count': 'Count',

        # Violations page
        'violations_title': 'Violations',
        'violations_empty': 'No violations recorded.',
        'violations_disabled_warning': 'Audit logging is disabled. Violations are not being recorded.',
        'violations_col_timestamp': 'Timestamp',
        'violations_col_username': 'User',
        'violations_col_model': 'Model',
        'violations_col_object': 'Object',
        'violations_col_action': 'Action',
        'violations_col_reason': 'Reason',
        'violations_col_message': 'Message',
        'filter_reason': 'Reason',
        'filter_username': 'User',
        'filter_date_from': 'From',
        'filter_date_to': 'To',
        'filter_all': 'All',

        # Dashboard
        'dashboard_title': 'Dashboard',
        'dashboard_feature_status': 'Feature Status',
        'dashboard_total_violations': 'Total Violations',
        'dashboard_by_reason': 'Violations by Reason',
        'dashboard_top_users': 'Top {count} Users',
        'dashboard_over_time': 'Violations (Last 30 Days)',
        'dashboard_active_rules': 'Active Rules',
        'dashboard_enabled': 'Enabled',
        'dashboard_disabled': 'Disabled',
        'dashboard_changelog_enforcement': 'Changelog Enforcement',
        'dashboard_ticket_reference': 'Ticket Reference',
        'dashboard_change_window': 'Change Window',
        'dashboard_audit_log': 'Audit Log',
        'dashboard_no_data': 'No data available.',
        'dashboard_dry_run': 'Dry-Run Mode',

        # Violations page extras
        'btn_export_csv': 'CSV Export',

        # Dashboard buttons
        'btn_reset_violations': 'Reset Violations',
        'btn_export_dashboard': 'Export Statistics',
        'dashboard_reset_confirm': 'Are you sure you want to delete ALL violation records? This action cannot be undone.',

        # Info sidebar
        'info_title': 'Info',
        'info_plugin': 'Plugin',
        'info_version': 'Version',
        'info_author': 'Author',
        'info_note': 'Changes take effect immediately. These settings override values from configuration.py.',

        # Modules section (settings)
        'section_modules': 'Modules',
        'label_import_templates_enabled': 'Enable import templates',
        'label_guide_enabled': 'Enable user guide',
        'help_import_templates_enabled': 'If enabled, CSV import templates can be provided for all users.',
        'help_guide_enabled': 'If enabled, an editable user guide is shown in the plugin.',

        # Tabs (new)
        'tab_import_templates': 'Import Templates',
        'tab_guide': 'Guide',

        # Import Templates
        'import_templates_title': 'Import Templates',
        'import_templates_empty': 'No import templates available.',
        'import_templates_admin_title': 'Manage Import Templates',
        'import_template_add_title': 'Add Template',
        'import_template_edit_title': 'Edit Template',
        'import_template_delete_title': 'Delete Template',
        'import_template_delete_confirm': 'Are you sure you want to delete this template?',
        'import_templates_col_name': 'Name',
        'import_templates_col_model': 'Model',
        'import_templates_col_enabled': 'Enabled',
        'import_templates_col_actions': 'Actions',
        'import_templates_col_description': 'Description',
        'btn_add_template': 'Add Template',
        'btn_download': 'Download',
        'btn_auto_generate': 'Generate CSV Headers',
        'btn_manage_templates': 'Manage Templates',

        # Guide
        'guide_title': 'Guide',
        'guide_empty': 'No guide has been created yet.',
        'guide_edit_title': 'Edit Guide',
        'guide_last_updated': 'Last updated',
        'guide_updated_by': 'by',
        'btn_edit_guide': 'Edit Guide',
        'guide_editor_hint': 'Use WYSIWYG mode for simple content or HTML-Code mode for full HTML pages (with own CSS/JS). Full HTML pages are rendered in an isolated frame.',
        'guide_preview_label': 'Preview',
        'guide_confirm_switch': 'The HTML content is a full page with its own CSS/JS. Switching to WYSIWYG mode will lose formatting. Switch anyway?',

        # Feature disabled
        'feature_disabled_title': 'Feature Disabled',
        'feature_disabled_message': 'This feature is currently disabled. An administrator can enable it in the plugin settings.',

        # Dashboard (new)
        'dashboard_import_templates': 'Import Templates',
        'dashboard_guide': 'User Guide',

        # Widget text (dashboard widgets)
        'widget_guide_btn': 'Guide',
        'widget_guide_disabled': 'Guide is disabled.',
        'widget_templates_disabled': 'Import templates are disabled.',
        'widget_templates_all': 'All templates',

        # Widget setup hints
        'widget_hint_title': 'Set up dashboard widget',
        'widget_hint_guide_text': 'To add a quick link to the guide on the NetBox dashboard: Home \u2192 Add Widget \u2192 select "Note" \u2192 paste the following Markdown content:',
        'widget_hint_guide_markdown': '### \U0001f4d6 Guide\n\nAccess the internal guide:\n\n[\u2192 Open Guide](/plugins/netbox-force/guide/)',
        'widget_hint_import_text': 'To add a quick link to import templates on the NetBox dashboard: Home \u2192 Add Widget \u2192 select "Note" \u2192 paste the following Markdown content:',
        'widget_hint_import_markdown': '### \U0001f4e5 Import Templates\n\nCSV templates for bulk import:\n\n[\u2192 Open Import Templates](/plugins/netbox-force/import-templates/)',

        # Settings sections (v4.3.0)
        'section_enforcement_toggle': 'Global Enforcement',

        # Settings fields (v4.3.0)
        'label_enforcement_enabled': 'Enforcement enabled',
        'help_enforcement_enabled': 'Master switch. Disable to pause all enforcement globally (e.g. during maintenance). Dry-run mode is a softer alternative.',
    },

    'es': {
        # Tabs
        'tab_settings': 'Configuración',
        'tab_rules': 'Reglas de Validación',
        'tab_violations': 'Infracciones',
        'tab_dashboard': 'Panel',

        # Section headers
        'section_language': 'Idioma',
        'section_enforcement': 'Reglas de Aplicación',
        'section_blocked_phrases': 'Frases Bloqueadas',
        'section_exemptions': 'Exenciones',
        'section_ticket': 'Referencia de Ticket',
        'section_change_window': 'Ventana de Cambios',
        'section_audit_log': 'Registro de Auditoría',

        # Field labels
        'label_language': 'Idioma',
        'label_min_length': 'Longitud mínima del changelog',
        'label_enforce_on_create': 'Aplicar al crear',
        'label_enforce_on_delete': 'Aplicar al eliminar',
        'label_exempt_users': 'Usuarios exentos',
        'label_blacklisted_phrases': 'Frases bloqueadas',
        'label_extra_exempt_models': 'Modelos exentos',
        'label_ticket_pattern': 'Patrón de ticket (Regex)',
        'label_ticket_pattern_hint': 'Ejemplo de ticket (mensaje de error)',
        'label_change_window_enabled': 'Activar ventana de cambios',
        'label_change_window_start': 'Hora de inicio',
        'label_change_window_end': 'Hora de fin',
        'label_change_window_weekdays': 'Días permitidos',
        'label_audit_log_enabled': 'Activar registro de auditoría',
        'label_audit_log_retention_days': 'Retención (días)',
        'label_dashboard_top_users_count': 'Usuarios principales en el panel',
        'label_dry_run': 'Modo de prueba',

        # Help texts
        'help_language': 'Idioma para mensajes de error en la UI de NetBox. Los mensajes de API siempre son en inglés.',
        'help_min_length': 'Número mínimo de caracteres requeridos para una entrada de changelog.',
        'help_enforce_on_create': 'Si está activado, también se requiere una entrada de changelog al crear nuevos objetos.',
        'help_enforce_on_delete': 'Si está activado, también se requiere una entrada de changelog al eliminar objetos.',
        'help_exempt_users': 'Un nombre de usuario por línea.',
        'help_blacklisted_phrases': 'Una frase por línea. Las entradas de changelog que contengan estas frases (como palabras completas) serán rechazadas.',
        'help_extra_exempt_models': 'Un modelo por línea (formato: app.model, ej. myplugin.mymodel).',
        'help_ticket_pattern': 'Patrón regex para referencias de tickets requeridas (ej. JIRA-\\d+ o #\\d+). Dejar vacío para desactivar.',
        'help_ticket_pattern_hint': 'Ejemplo legible mostrado en los mensajes de error (ej. "JIRA-1234 o CHG0012345"). Si está vacío, se muestra el patrón regex.',
        'help_change_window_enabled': 'Si está activado, los cambios solo se permiten dentro de la ventana de tiempo definida.',
        'help_change_window_start': 'Inicio del período de cambios permitido.',
        'help_change_window_end': 'Fin del período de cambios permitido.',
        'help_change_window_weekdays': 'Números de días ISO separados por comas (1=Lunes, 7=Domingo).',
        'help_audit_log_enabled': 'Si está activado, todos los cambios rechazados se registran para seguimiento de cumplimiento.',
        'help_audit_log_retention_days': 'Número de días para retener las entradas del registro de auditoría. Las entradas más antiguas se eliminan automáticamente.',
        'help_dashboard_top_users_count': 'Número de usuarios en la lista principal del panel.',
        'help_dry_run': 'Si está activado, las infracciones se registran pero los cambios no se bloquean. Útil para implementar nuevas reglas gradualmente.',

        # Buttons
        'btn_save': 'Guardar',
        'btn_add_rule': 'Agregar Regla',
        'btn_edit': 'Editar',
        'btn_delete': 'Eliminar',
        'btn_cancel': 'Cancelar',
        'btn_confirm_delete': 'Confirmar Eliminación',
        'btn_apply_filter': 'Aplicar Filtro',
        'btn_clear_filter': 'Limpiar Filtro',

        # Rules page
        'rules_title': 'Reglas de Validación',
        'rules_empty': 'No hay reglas de validación definidas.',
        'rules_col_type': 'Tipo',
        'rules_col_model': 'Modelo',
        'rules_col_field': 'Campo',
        'rules_col_pattern': 'Patrón',
        'rules_col_message': 'Mensaje de Error',
        'rules_col_enabled': 'Activo',
        'rules_col_actions': 'Acciones',
        'rule_add_title': 'Agregar Regla',
        'rule_edit_title': 'Editar Regla',
        'rule_delete_title': 'Eliminar Regla',
        'rule_delete_confirm': '¿Está seguro de que desea eliminar esta regla?',
        'rule_type_naming': 'Convención de Nombres',
        'rule_type_required': 'Campo Obligatorio',
        'rule_help_title': 'Ayuda',
        'rule_help_naming_desc': 'Asegura que el valor de un campo coincida con un patrón regex. Usa re.fullmatch() de Python, por lo que el valor completo debe coincidir.',
        'rule_help_naming_examples': 'Ejemplos:',
        'rule_help_naming_ex1': 'coincide con ABC-123',
        'rule_help_naming_ex2': 'debe comenzar con prefijo',
        'rule_help_required_desc': 'Asegura que un campo no esté vacío, nulo o en blanco. Útil para campos que son opcionales en NetBox por defecto pero obligatorios en su organización.',
        'rule_help_common_models': 'Modelos comunes:',
        'rule_help_type_naming_desc': 'El valor del campo debe coincidir con un patrón regex.',
        'rule_help_type_required_desc': 'El campo debe tener un valor no vacío.',
        'rule_help_model_format': 'Formato: app.model (ej. dcim.device, ipam.ipaddress)',
        'rule_help_field_desc': 'El campo del modelo a validar (ej. name, description, tenant)',
        'rule_help_pattern_desc': 'Solo para reglas de nombres. El valor del campo debe coincidir completamente con este patrón regex. Nota: Los caracteres especiales (ÄÖÜäöüß) deben incluirse explícitamente, p.ej. [A-ZÄÖÜ] en vez de solo [A-Z].',
        'rule_help_error_msg_desc': 'Se muestra al usuario cuando falla la validación. Dejar vacío para mensaje predeterminado.',
        'rule_test_placeholder': 'Ingrese valor de prueba...',
        'dashboard_col_count': 'Cantidad',

        # Violations page
        'violations_title': 'Infracciones',
        'violations_empty': 'No se registraron infracciones.',
        'violations_disabled_warning': 'El registro de auditoría está desactivado. Las infracciones no se están registrando.',
        'violations_col_timestamp': 'Marca de Tiempo',
        'violations_col_username': 'Usuario',
        'violations_col_model': 'Modelo',
        'violations_col_object': 'Objeto',
        'violations_col_action': 'Acción',
        'violations_col_reason': 'Razón',
        'violations_col_message': 'Mensaje',
        'filter_reason': 'Razón',
        'filter_username': 'Usuario',
        'filter_date_from': 'Desde',
        'filter_date_to': 'Hasta',
        'filter_all': 'Todos',

        # Dashboard
        'dashboard_title': 'Panel',
        'dashboard_feature_status': 'Estado de Funciones',
        'dashboard_total_violations': 'Infracciones Totales',
        'dashboard_by_reason': 'Infracciones por Razón',
        'dashboard_top_users': 'Top {count} Usuarios',
        'dashboard_over_time': 'Infracciones (Últimos 30 Días)',
        'dashboard_active_rules': 'Reglas Activas',
        'dashboard_enabled': 'Activado',
        'dashboard_disabled': 'Desactivado',
        'dashboard_changelog_enforcement': 'Aplicación de Changelog',
        'dashboard_ticket_reference': 'Referencia de Ticket',
        'dashboard_change_window': 'Ventana de Cambios',
        'dashboard_audit_log': 'Registro de Auditoría',
        'dashboard_no_data': 'No hay datos disponibles.',
        'dashboard_dry_run': 'Modo de Prueba',

        # Violations page extras
        'btn_export_csv': 'Exportar CSV',

        # Dashboard buttons
        'btn_reset_violations': 'Restablecer Infracciones',
        'btn_export_dashboard': 'Exportar Estadísticas',
        'dashboard_reset_confirm': '¿Está seguro de que desea eliminar TODOS los registros de infracciones? Esta acción no se puede deshacer.',

        # Info sidebar
        'info_title': 'Info',
        'info_plugin': 'Plugin',
        'info_version': 'Versión',
        'info_author': 'Autor',
        'info_note': 'Los cambios surten efecto inmediatamente. Estas configuraciones anulan los valores de configuration.py.',

        # Modules section (settings)
        'section_modules': 'Módulos',
        'label_import_templates_enabled': 'Activar plantillas de importación',
        'label_guide_enabled': 'Activar guía de usuario',
        'help_import_templates_enabled': 'Si está activado, se pueden proporcionar plantillas de importación CSV para todos los usuarios.',
        'help_guide_enabled': 'Si está activado, se muestra una guía de usuario editable en el plugin.',

        # Tabs (new)
        'tab_import_templates': 'Plantillas de Importación',
        'tab_guide': 'Guía',

        # Import Templates
        'import_templates_title': 'Plantillas de Importación',
        'import_templates_empty': 'No hay plantillas de importación disponibles.',
        'import_templates_admin_title': 'Gestionar Plantillas de Importación',
        'import_template_add_title': 'Agregar Plantilla',
        'import_template_edit_title': 'Editar Plantilla',
        'import_template_delete_title': 'Eliminar Plantilla',
        'import_template_delete_confirm': '¿Está seguro de que desea eliminar esta plantilla?',
        'import_templates_col_name': 'Nombre',
        'import_templates_col_model': 'Modelo',
        'import_templates_col_enabled': 'Activo',
        'import_templates_col_actions': 'Acciones',
        'import_templates_col_description': 'Descripción',
        'btn_add_template': 'Agregar Plantilla',
        'btn_download': 'Descargar',
        'btn_auto_generate': 'Generar Encabezados CSV',
        'btn_manage_templates': 'Gestionar Plantillas',

        # Guide
        'guide_title': 'Guía',
        'guide_empty': 'Aún no se ha creado una guía.',
        'guide_edit_title': 'Editar Guía',
        'guide_last_updated': 'Última actualización',
        'guide_updated_by': 'por',
        'btn_edit_guide': 'Editar Guía',
        'guide_editor_hint': 'Use el modo WYSIWYG para contenido simple o el modo HTML-Code para páginas HTML completas (con CSS/JS propio). Las páginas HTML completas se muestran en un marco aislado.',
        'guide_preview_label': 'Vista previa',
        'guide_confirm_switch': 'El contenido HTML es una página completa con su propio CSS/JS. Cambiar al modo WYSIWYG perderá el formato. ¿Cambiar de todos modos?',

        # Feature disabled
        'feature_disabled_title': 'Función Desactivada',
        'feature_disabled_message': 'Esta función está actualmente desactivada. Un administrador puede activarla en la configuración del plugin.',

        # Dashboard (new)
        'dashboard_import_templates': 'Plantillas de Importaci\u00f3n',
        'dashboard_guide': 'Gu\u00eda de Usuario',

        # Widget text (dashboard widgets)
        'widget_guide_btn': 'Gu\u00eda',
        'widget_guide_disabled': 'La gu\u00eda est\u00e1 desactivada.',
        'widget_templates_disabled': 'Las plantillas de importaci\u00f3n est\u00e1n desactivadas.',
        'widget_templates_all': 'Todas las plantillas',

        # Widget setup hints
        'widget_hint_title': 'Configurar widget del panel',
        'widget_hint_guide_text': 'Para a\u00f1adir un acceso r\u00e1pido a la gu\u00eda en el panel de NetBox: Inicio \u2192 A\u00f1adir Widget \u2192 seleccionar "Note" \u2192 pegar el siguiente contenido Markdown:',
        'widget_hint_guide_markdown': '### \U0001f4d6 Gu\u00eda\n\nAccede a la gu\u00eda interna:\n\n[\u2192 Abrir Gu\u00eda](/plugins/netbox-force/guide/)',
        'widget_hint_import_text': 'Para a\u00f1adir un acceso r\u00e1pido a las plantillas en el panel de NetBox: Inicio \u2192 A\u00f1adir Widget \u2192 seleccionar "Note" \u2192 pegar el siguiente contenido Markdown:',
        'widget_hint_import_markdown': '### \U0001f4e5 Plantillas de Importaci\u00f3n\n\nPlantillas CSV para importaci\u00f3n masiva:\n\n[\u2192 Abrir Plantillas](/plugins/netbox-force/import-templates/)',

        # Settings sections (v4.3.0)
        'section_enforcement_toggle': 'Aplicaci\u00f3n Global',

        # Settings fields (v4.3.0)
        'label_enforcement_enabled': 'Aplicaci\u00f3n activada',
        'help_enforcement_enabled': 'Interruptor principal. Desactivar pausa toda la aplicaci\u00f3n globalmente (p. ej. durante mantenimiento). El modo simulaci\u00f3n es una alternativa m\u00e1s suave.',
    },
}


def get_ui_string(key, language='de'):
    """Returns a single translated UI string for the given key and language."""
    lang_strings = UI_STRINGS.get(language, UI_STRINGS['en'])
    return lang_strings.get(key, UI_STRINGS['en'].get(key, key))


def get_all_ui_strings(language='de'):
    """Returns the full UI strings dict for a language, falling back to English."""
    base = dict(UI_STRINGS['en'])
    base.update(UI_STRINGS.get(language, {}))
    return base
