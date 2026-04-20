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
            "entspricht nicht dem erforderlichen Muster.{hint}"
        ),
        'required_field': (
            "Pflichtfeld fehlt! Das Feld '{field}' bei '{model}' "
            "darf nicht leer sein.{hint}"
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
            "does not match the required pattern.{hint}"
        ),
        'required_field': (
            "Required field missing! The field '{field}' on '{model}' "
            "must not be empty.{hint}"
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
            "no coincide con el patrón requerido.{hint}"
        ),
        'required_field': (
            "Campo obligatorio faltante. El campo '{field}' en '{model}' "
            "no debe estar vacío.{hint}"
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
    'cs': {
        'changelog_required': (
            "Požadován záznam changelogu! Při {action} '{model}' "
            "musí být v poli 'Důvod změny / Changelog' uveden důvod "
            "(min. {min_len} znaků)."
        ),
        'blacklisted': (
            "Neplatný záznam changelogu! Text obsahuje zakázané "
            "výrazy: {words}"
        ),
        'ticket_missing': (
            "Požadován odkaz na ticket! Záznam changelogu musí obsahovat "
            "odkaz na ticket. {hint}"
        ),
        'naming_violation': (
            "Porušena konvence pojmenování! Pole '{field}' u '{model}' "
            "neodpovídá požadovanému vzoru.{hint}"
        ),
        'required_field': (
            "Chybí povinné pole! Pole '{field}' u '{model}' "
            "nesmí být prázdné.{hint}"
        ),
        'change_window': (
            "Změny nejsou povoleny mimo okno změn "
            "({start} - {end}, {weekdays})."
        ),
        'dry_run_prefix': '[DRY-RUN] ',
        'action_create': 'vytvoření',
        'action_edit': 'úpravě',
        'action_delete': 'odstranění',
    },
    'da': {
        'changelog_required': (
            "Changelogpost påkrævet! Ved {action} af '{model}' "
            "skal der angives en årsag i feltet 'Ændringsårsag / Changelog' "
            "(min. {min_len} tegn)."
        ),
        'blacklisted': (
            "Ugyldig changelogpost! Teksten indeholder forbudte "
            "udtryk: {words}"
        ),
        'ticket_missing': (
            "Ticketreference påkrævet! Changelogposten skal indeholde "
            "en ticketreference. {hint}"
        ),
        'naming_violation': (
            "Navnekonvention overtrådt! Feltet '{field}' på '{model}' "
            "matcher ikke det påkrævede mønster.{hint}"
        ),
        'required_field': (
            "Påkrævet felt mangler! Feltet '{field}' på '{model}' "
            "må ikke være tomt.{hint}"
        ),
        'change_window': (
            "Ændringer er ikke tilladt uden for ændringsvinduet "
            "({start} - {end}, {weekdays})."
        ),
        'dry_run_prefix': '[DRY-RUN] ',
        'action_create': 'oprettelse',
        'action_edit': 'ændring',
        'action_delete': 'sletning',
    },
    'fr': {
        'changelog_required': (
            "Entrée de journal requise ! Lors de {action} de '{model}', "
            "une raison doit être fournie dans le champ "
            "'Raison de modification / Journal' (min. {min_len} caractères)."
        ),
        'blacklisted': (
            "Entrée de journal invalide ! Le texte contient des "
            "termes interdits : {words}"
        ),
        'ticket_missing': (
            "Référence de ticket requise ! L'entrée du journal doit "
            "contenir une référence de ticket. {hint}"
        ),
        'naming_violation': (
            "Convention de nommage violée ! Le champ '{field}' pour '{model}' "
            "ne correspond pas au modèle requis.{hint}"
        ),
        'required_field': (
            "Champ obligatoire manquant ! Le champ '{field}' pour '{model}' "
            "ne doit pas être vide.{hint}"
        ),
        'change_window': (
            "Les modifications ne sont pas autorisées en dehors de la "
            "fenêtre de modification ({start} - {end}, {weekdays})."
        ),
        'dry_run_prefix': '[DRY-RUN] ',
        'action_create': 'la création',
        'action_edit': 'la modification',
        'action_delete': 'la suppression',
    },
    'it': {
        'changelog_required': (
            "Voce del registro richiesta! Durante {action} di '{model}', "
            "è necessario fornire una motivazione nel campo "
            "'Motivo della modifica / Registro' (min. {min_len} caratteri)."
        ),
        'blacklisted': (
            "Voce del registro non valida! Il testo contiene "
            "termini vietati: {words}"
        ),
        'ticket_missing': (
            "Riferimento ticket richiesto! La voce del registro deve "
            "contenere un riferimento al ticket. {hint}"
        ),
        'naming_violation': (
            "Convenzione di denominazione violata! Il campo '{field}' "
            "su '{model}' non corrisponde al pattern richiesto.{hint}"
        ),
        'required_field': (
            "Campo obbligatorio mancante! Il campo '{field}' su '{model}' "
            "non deve essere vuoto.{hint}"
        ),
        'change_window': (
            "Le modifiche non sono consentite al di fuori della finestra "
            "di modifica ({start} - {end}, {weekdays})."
        ),
        'dry_run_prefix': '[DRY-RUN] ',
        'action_create': 'creazione',
        'action_edit': 'modifica',
        'action_delete': 'eliminazione',
    },
    'ja': {
        'changelog_required': (
            "変更ログの記録が必要です！ '{model}' の{action}時には、"
            "'変更理由 / 変更ログ' フィールドに理由を入力してください "
            "（最低 {min_len} 文字）。"
        ),
        'blacklisted': (
            "変更ログの記録が無効です！ テキストに禁止された "
            "語句が含まれています: {words}"
        ),
        'ticket_missing': (
            "チケット参照が必要です！ 変更ログにはチケット参照を "
            "含める必要があります。 {hint}"
        ),
        'naming_violation': (
            "命名規則違反！ '{model}' のフィールド '{field}' が "
            "必要なパターンに一致しません。{hint}"
        ),
        'required_field': (
            "必須フィールドが空です！ '{model}' のフィールド '{field}' "
            "は空にできません。{hint}"
        ),
        'change_window': (
            "変更ウィンドウ外での変更は許可されていません "
            "（{start} - {end}、{weekdays}）。"
        ),
        'dry_run_prefix': '[DRY-RUN] ',
        'action_create': '作成',
        'action_edit': '編集',
        'action_delete': '削除',
    },
    'lv': {
        'changelog_required': (
            "Nepieciešams izmaiņu žurnāla ieraksts! Veicot {action} '{model}', "
            "laukā 'Izmaiņu iemesls / Žurnāls' jānorāda iemesls "
            "(min. {min_len} rakstzīmes)."
        ),
        'blacklisted': (
            "Nederīgs izmaiņu žurnāla ieraksts! Teksts satur aizliegtus "
            "vārdus: {words}"
        ),
        'ticket_missing': (
            "Nepieciešama biļetes atsauce! Izmaiņu žurnāla ierakstam "
            "jāsatur biļetes atsauce. {hint}"
        ),
        'naming_violation': (
            "Nosaukumu konvencijas pārkāpums! '{model}' lauks '{field}' "
            "neatbilst nepieciešamajam paraugam.{hint}"
        ),
        'required_field': (
            "Trūkst obligātā lauka! '{model}' lauks '{field}' "
            "nedrīkst būt tukšs.{hint}"
        ),
        'change_window': (
            "Izmaiņas nav atļautas ārpus izmaiņu loga "
            "({start} - {end}, {weekdays})."
        ),
        'dry_run_prefix': '[DRY-RUN] ',
        'action_create': 'izveidošana',
        'action_edit': 'rediģēšana',
        'action_delete': 'dzēšana',
    },
    'nl': {
        'changelog_required': (
            "Changelog-vermelding vereist! Bij het {action} van '{model}' "
            "moet een reden worden opgegeven in het veld "
            "'Wijzigingsreden / Changelog' (min. {min_len} tekens)."
        ),
        'blacklisted': (
            "Ongeldige changelog-vermelding! De tekst bevat verboden "
            "termen: {words}"
        ),
        'ticket_missing': (
            "Ticketreferentie vereist! De changelog-vermelding moet "
            "een ticketreferentie bevatten. {hint}"
        ),
        'naming_violation': (
            "Naamgevingsconventie geschonden! Het veld '{field}' bij '{model}' "
            "komt niet overeen met het vereiste patroon.{hint}"
        ),
        'required_field': (
            "Verplicht veld ontbreekt! Het veld '{field}' bij '{model}' "
            "mag niet leeg zijn.{hint}"
        ),
        'change_window': (
            "Wijzigingen zijn niet toegestaan buiten het wijzigingsvenster "
            "({start} - {end}, {weekdays})."
        ),
        'dry_run_prefix': '[DRY-RUN] ',
        'action_create': 'aanmaken',
        'action_edit': 'wijzigen',
        'action_delete': 'verwijderen',
    },
    'pl': {
        'changelog_required': (
            "Wymagana pozycja dziennika zmian! Podczas {action} '{model}', "
            "w polu 'Powód zmiany / Dziennik' należy podać uzasadnienie "
            "(min. {min_len} znaków)."
        ),
        'blacklisted': (
            "Nieprawidłowa pozycja dziennika zmian! Tekst zawiera "
            "zakazane wyrazy: {words}"
        ),
        'ticket_missing': (
            "Wymagane odniesienie do zgłoszenia! Pozycja dziennika zmian "
            "musi zawierać odniesienie do zgłoszenia. {hint}"
        ),
        'naming_violation': (
            "Naruszono konwencję nazewnictwa! Pole '{field}' dla '{model}' "
            "nie pasuje do wymaganego wzorca.{hint}"
        ),
        'required_field': (
            "Brakuje wymaganego pola! Pole '{field}' dla '{model}' "
            "nie może być puste.{hint}"
        ),
        'change_window': (
            "Zmiany nie są dozwolone poza oknem zmian "
            "({start} - {end}, {weekdays})."
        ),
        'dry_run_prefix': '[DRY-RUN] ',
        'action_create': 'tworzenia',
        'action_edit': 'edycji',
        'action_delete': 'usuwania',
    },
    'pt': {
        'changelog_required': (
            "Entrada no registro de alterações obrigatória! Ao {action} "
            "'{model}', é necessário fornecer um motivo no campo "
            "'Motivo da alteração / Registro' (mín. {min_len} caracteres)."
        ),
        'blacklisted': (
            "Entrada inválida no registro de alterações! O texto contém "
            "termos proibidos: {words}"
        ),
        'ticket_missing': (
            "Referência de ticket obrigatória! A entrada do registro de "
            "alterações deve conter uma referência de ticket. {hint}"
        ),
        'naming_violation': (
            "Convenção de nomenclatura violada! O campo '{field}' em '{model}' "
            "não corresponde ao padrão necessário.{hint}"
        ),
        'required_field': (
            "Campo obrigatório em falta! O campo '{field}' em '{model}' "
            "não pode estar vazio.{hint}"
        ),
        'change_window': (
            "As alterações não são permitidas fora da janela de alterações "
            "({start} - {end}, {weekdays})."
        ),
        'dry_run_prefix': '[DRY-RUN] ',
        'action_create': 'criar',
        'action_edit': 'modificar',
        'action_delete': 'eliminar',
    },
    'ru': {
        'changelog_required': (
            "Требуется запись в журнале изменений! При {action} '{model}' "
            "необходимо указать причину в поле "
            "'Причина изменения / Журнал' (мин. {min_len} символов)."
        ),
        'blacklisted': (
            "Недопустимая запись в журнале изменений! Текст содержит "
            "запрещённые слова: {words}"
        ),
        'ticket_missing': (
            "Требуется ссылка на тикет! Запись в журнале изменений "
            "должна содержать ссылку на тикет. {hint}"
        ),
        'naming_violation': (
            "Нарушение соглашения об именовании! Поле '{field}' у '{model}' "
            "не соответствует требуемому шаблону.{hint}"
        ),
        'required_field': (
            "Отсутствует обязательное поле! Поле '{field}' у '{model}' "
            "не должно быть пустым.{hint}"
        ),
        'change_window': (
            "Изменения не разрешены вне окна изменений "
            "({start} - {end}, {weekdays})."
        ),
        'dry_run_prefix': '[DRY-RUN] ',
        'action_create': 'создании',
        'action_edit': 'изменении',
        'action_delete': 'удалении',
    },
    'tr': {
        'changelog_required': (
            "Değişiklik günlüğü girişi gerekli! '{model}' öğesini {action} "
            "sırasında, 'Değişiklik nedeni / Günlük' alanına bir gerekçe "
            "girilmelidir (min. {min_len} karakter)."
        ),
        'blacklisted': (
            "Geçersiz değişiklik günlüğü girişi! Metin yasaklı "
            "terimler içeriyor: {words}"
        ),
        'ticket_missing': (
            "Bilet referansı gerekli! Değişiklik günlüğü girişi "
            "bir bilet referansı içermelidir. {hint}"
        ),
        'naming_violation': (
            "Adlandırma kuralı ihlali! '{model}' üzerindeki '{field}' alanı "
            "gerekli kalıba uymamaktadır.{hint}"
        ),
        'required_field': (
            "Zorunlu alan eksik! '{model}' üzerindeki '{field}' alanı "
            "boş bırakılamaz.{hint}"
        ),
        'change_window': (
            "Değişikliklere değişiklik penceresi dışında izin "
            "verilmemektedir ({start} - {end}, {weekdays})."
        ),
        'dry_run_prefix': '[DRY-RUN] ',
        'action_create': 'oluşturma',
        'action_edit': 'düzenleme',
        'action_delete': 'silme',
    },
    'uk': {
        'changelog_required': (
            "Потрібний запис у журналі змін! Під час {action} '{model}' "
            "необхідно вказати причину в полі "
            "'Причина зміни / Журнал' (мін. {min_len} символів)."
        ),
        'blacklisted': (
            "Недопустимий запис у журналі змін! Текст містить "
            "заборонені слова: {words}"
        ),
        'ticket_missing': (
            "Потрібне посилання на тікет! Запис у журналі змін "
            "повинен містити посилання на тікет. {hint}"
        ),
        'naming_violation': (
            "Порушення угоди про іменування! Поле '{field}' у '{model}' "
            "не відповідає потрібному шаблону.{hint}"
        ),
        'required_field': (
            "Відсутнє обов'язкове поле! Поле '{field}' у '{model}' "
            "не повинно бути порожнім.{hint}"
        ),
        'change_window': (
            "Зміни не дозволені за межами вікна змін "
            "({start} - {end}, {weekdays})."
        ),
        'dry_run_prefix': '[DRY-RUN] ',
        'action_create': 'створенні',
        'action_edit': 'зміні',
        'action_delete': 'видаленні',
    },
    'zh-hans': {
        'changelog_required': (
            "需要变更日志条目！在{action}'{model}'时，"
            "必须在'变更原因 / 变更日志'字段中提供原因 "
            "（最少 {min_len} 个字符）。"
        ),
        'blacklisted': (
            "变更日志条目无效！文本包含禁止的 "
            "词语：{words}"
        ),
        'ticket_missing': (
            "需要工单参考！变更日志条目必须包含 "
            "工单参考。{hint}"
        ),
        'naming_violation': (
            "命名规范违规！'{model}'上的字段'{field}' "
            "不符合所需模式。{hint}"
        ),
        'required_field': (
            "缺少必填字段！'{model}'上的字段'{field}' "
            "不得为空。{hint}"
        ),
        'change_window': (
            "变更窗口之外不允许进行更改 "
            "（{start} - {end}，{weekdays}）。"
        ),
        'dry_run_prefix': '[DRY-RUN] ',
        'action_create': '创建',
        'action_edit': '修改',
        'action_delete': '删除',
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
        "does not match the required pattern.{hint}"
    ),
    'required_field': (
        "Required field missing. The field '{field}' on '{model}' "
        "must not be empty.{hint}"
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
