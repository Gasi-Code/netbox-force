# NetBox Force — Anleitung (Deutsch)

[← Alle Sprachen](../README.md) · [Projekt-README](../../README.md) · [Änderungsverlauf](../../CHANGELOG.md)

---

## 1. Was das Plugin macht

NetBox hält fest, *was* geändert wurde. NetBox Force entscheidet, *ob die Änderung
überhaupt zulässig ist*, und kann vorher eine Begründung verlangen.

Es sitzt zwischen jedem Speichern- und Löschvorgang und der Datenbank. Bevor eine
Änderung geschrieben wird, kann es prüfen:

- ob ein Changelog-Kommentar da ist und lang genug
- ob der Kommentar nicht nur aus Füllwörtern besteht
- ob er eine Ticketnummer nennt
- ob die Änderung in einem erlaubten Zeitfenster passiert
- ob Feldwerte einem Namensmuster entsprechen
- ob Pflichtfelder tatsächlich gefüllt sind

Zwei weitere Module gehören dazu:

- **Patchmanagement** — Patchstand, Betriebssystem, Zuständige und Update-Historie
  je virtueller Maschine oder physischem Server, wahlweise aus CheckMK gespeist.
- **Graylog** — sendet Audit-Ereignisse hinaus und holt Log-Informationen dorthin
  zurück, wo das Objekt steht.

Alles ist abschaltbar. Nach der Installation ist nur die Changelog-Prüfung aktiv,
mit zwei Zeichen Mindestlänge. Alles Weitere wird in der Oberfläche eingeschaltet.

---

## 2. Voraussetzungen

| Bestandteil | Version | Anmerkung |
|---|---|---|
| NetBox | 4.0.0 oder neuer | |
| Python | 3.10 oder neuer | |
| PostgreSQL | — | Von NetBox selbst vorausgesetzt |
| `cryptography` | beliebig | Liegt NetBox bei. Fehlt es, werden CheckMK-Geheimnis und Graylog-Token unverschlüsselt gespeichert — die Einstellungsseite sagt das |
| `requests` | beliebig | Liegt NetBox bei. Nötig für CheckMK und Graylog |
| RQ-Worker | — | Nur für den geplanten CheckMK-Abgleich und den Graylog-Abruf. Ohne Worker laufen beide weiterhin auf Knopfdruck, und die Seite sagt das |

---

## 3. Installation

### 3.1 Paket installieren

```bash
source /opt/netbox/venv/bin/activate
pip install git+https://github.com/Gasi-Code/netbox-force.git
```

### 3.2 Plugin eintragen

In der `configuration.py`:

```python
PLUGINS = ['netbox_force']
```

### 3.3 Migrationen ausführen

```bash
cd /opt/netbox/netbox
python manage.py migrate netbox_force
python manage.py collectstatic --no-input
```

### 3.4 NetBox neu starten

```bash
sudo systemctl restart netbox netbox-rq
```

### 3.5 Docker

```bash
docker exec -it <container> pip install git+https://github.com/Gasi-Code/netbox-force.git
docker exec -it <container> /opt/netbox/netbox/manage.py migrate netbox_force
docker restart <container>
```

Beim Image von LinuxServer.io **keine** `custom-cont-init.d`-Skripte für die
Installation verwenden. Die laufen *nach* den eigenen Init-Skripten von NetBox,
was zu fehlgeschlagenen Migrationen führen kann. Docker Mods laufen davor.

Eine Installation im Container-Dateisystem überlebt kein Image-Update. Das Plugin
gehört in die dauerhafte Plugin-Installationsliste des Images, sonst ist es nach
dem nächsten Pull weg.

---

## 4. Aktualisieren

```bash
source /opt/netbox/venv/bin/activate
pip install --force-reinstall --no-cache-dir git+https://github.com/Gasi-Code/netbox-force.git
```

`--force-reinstall --no-cache-dir` ist nötig, weil pip nach Versionsnummer
zwischenspeichert und sonst denselben Stand überspringen würde.

**Vor dem Neustart prüfen.** Dieser Schritt lädt das Plugin, ohne den laufenden
Prozess anzufassen. Kommt ein Fehler: nicht neu starten — das laufende NetBox hat
den alten Code im Speicher und arbeitet weiter:

```bash
cd /opt/netbox/netbox
python manage.py check
```

Danach:

```bash
python manage.py migrate netbox_force
python manage.py collectstatic --no-input
sudo systemctl restart netbox netbox-rq
```

### Zurück auf eine ältere Version

```bash
pip install --force-reinstall --no-cache-dir \
  git+https://github.com/Gasi-Code/netbox-force.git@<commit>
sudo systemctl restart netbox netbox-rq
```

Die Migrationen müssen dafür in der Regel nicht zurückgenommen werden.
Zusätzliche Spalten stören älteren Code nicht — er kennt sie schlicht nicht.
Trotzdem vorher einen Datenbank-Abzug ziehen.

---

## 5. Konfigurationsdatei

`PLUGINS_CONFIG` legt **nur die Startwerte** fest. Nach dem ersten Start wird
jede Einstellung in der Oberfläche verwaltet und in der Datenbank gehalten.

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

| Einstellung | Vorgabe | Bedeutung |
|---|---|---|
| `min_length` | `2` | Mindestzeichen im Changelog-Eintrag |
| `exempt_users` | siehe oben | Ausgenommene Benutzernamen, Groß-/Kleinschreibung egal |
| `enforce_on_create` | `False` | Changelog auch beim Anlegen verlangen |
| `enforce_on_delete` | `True` | Changelog auch beim Löschen verlangen |
| `extra_exempt_models` | `[]` | Weitere ausgenommene Modelle, Format `app.model` |
| `checkmk_secret` | `''` | Optional. Hält das CheckMK-Geheimnis vollständig aus der Datenbank heraus; hat dann Vorrang vor dem Feld in der Oberfläche |

---

## 6. Die Seiten

Superuser finden **NetBox Force** in der Seitenleiste. Alle Seiten sind auf
Superuser beschränkt, sofern nicht anders vermerkt.

| Seite | Zweck |
|---|---|
| **Einstellungen** | Sämtliche Erzwingungsregeln, Ausnahmen, Module, Webhook, CheckMK |
| **Validierungsregeln** | Namensmuster und Pflichtfelder, je Modell und Feld |
| **Modellrichtlinien** | Abweichungen von den globalen Regeln, je Modell |
| **Verstöße** | Filterbares Protokoll jeder blockierten Änderung, als CSV exportierbar |
| **Graylog** | Senden und Lesen, siehe Abschnitt 7 und 8 |
| **Dashboard** | Auswertung: welche Funktionen aktiv sind, blockierte Änderungen, Top-Benutzer, 30-Tage-Verlauf |
| **Importvorlagen** | Herunterladbare CSV-Vorlagen für den NetBox-Massenimport. Für alle angemeldeten Benutzer sichtbar, wenn aktiviert |
| **Anleitung** | Freie Textseite für die eigenen Benutzer. Für alle angemeldeten Benutzer sichtbar, wenn aktiviert |
| **Patchmanagement** | Siehe Abschnitt 9 |

Zwei Einstellungen verdienen eine eigene Erwähnung:

- **Globaler Schalter** — setzt alle Prüfungen aus, etwa während eines
  Wartungsfensters.
- **Dry-Run-Modus** — protokolliert Verstöße, blockiert aber nichts. Der richtige
  Weg, eine neue Regel einzuführen: man sieht, was blockiert *worden wäre*, bevor
  tatsächlich jemand aufgehalten wird.

---

## 7. Graylog — Senden

Sendet Audit-Ereignisse von NetBox an Graylog über GELF.

### Wozu

Drei Dinge stehen sonst nirgends in NetBox:

- **Fehlgeschlagene Anmeldungen.** NetBox speichert sie überhaupt nicht.
- **Quell-IP und User-Agent** einer Änderung. Das NetBox-Changelog trägt beides nicht.
- **Änderungen an den Plugin-Einstellungen selbst.** Sie stehen nicht im
  NetBox-Changelog — wer die Erzwingung abschaltete, hinterließ bisher keine Spur.

### Einrichten

Auf der Seite **Graylog**, obere Hälfte: Host, Port, Transport. Dann
*Testereignis senden*.

Mit **UDP** anfangen. Kommt nichts an, auf **TCP** umstellen — UDP kann einen
Fehler bauartbedingt nicht melden, TCP schon. Das unterscheidet „falscher Port"
von „Meldung verworfen".

| Transport | Bestätigt Zustellung | Verschlüsselt |
|---|---|---|
| UDP | nein | nein |
| TCP | ja | nein |
| TCP + TLS | ja | ja |
| HTTP | ja | nein |
| HTTPS | ja | ja |

UDP ist im lokalen Netz richtig und über das Internet falsch.

### Was gesendet wird

Eine Zeile je Ereignisart, jeweils mit Häkchen und Schweregrad: Objekt angelegt,
geändert, gelöscht; Anmeldung; Abmeldung; fehlgeschlagene Anmeldung; blockierte
Änderung; Plugin-Einstellungen geändert.

### Menge

Eine Anfrage, die mehr Objekte ändert als der eingestellte Schwellwert, wird als
**eine einzige Sammelmeldung** gemeldet. Ein Import von 500 Geräten ist ein
Vorgang — 500 fast identische Zeilen machen ihn schwerer erkennbar, nicht leichter.

Zusammenfassen statt Drosseln ist bewusst gewählt. Eine Warteschlange, die
langsamer leert als sie sich füllt, verwirft die *neuesten* Ereignisse — also
genau die falsche Hälfte.

### Feldnamen

Jedes Ereignis trägt dieselben Felder, damit Suchen einfach bleiben:

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

`_request_id` fasst alles zusammen, was eine Anfrage geändert hat. Vierzig
gleichzeitig bearbeitete Geräte sind ein Vorgang und nicht vierzig Rätsel.

### Drei Dinge, die man wissen sollte

- **Ein Graylog-Ausfall kann eine Speicherung in NetBox weder verlangsamen noch
  scheitern lassen.** Ereignisse kommen in eine begrenzte Warteschlange, die ein
  Hintergrundprozess leert. Ist sie voll, werden neue Ereignisse verworfen und
  gezählt; der Zähler steht auf der Seite.
- **Der Meldungstext ist immer englisch**, unabhängig von der Oberflächensprache.
  Graylog-Alarme suchen auf diesem Text; eine Übersetzung würde jeden Alarm still
  zerstören, sobald jemand die Sprache umstellt.
- **Die Client-IP wird aus `X-Forwarded-For` gelesen**, sofern vorhanden. Dieser
  Kopf kommt vom Client und lässt sich fälschen, wenn NetBox ohne vorgelagerten
  Reverse Proxy erreichbar ist.

---

## 8. Graylog — Lesen

Holt Graylog-Informationen nach NetBox, damit man einen Host beurteilen kann,
ohne einen zweiten Tab zu öffnen.

### Einrichten

Untere Hälfte der Seite **Graylog**: Adresse und API-Token, dann *Verbindung
testen*. Das Ergebnis nennt die Graylog-Version, die erkannte Such-API, die
lautesten Quellen und die vorhandenen Streams. *Jetzt abrufen* führt einen Abruf
sofort aus.

**Den Token für einen Graylog-Benutzer mit reiner Leserolle ausstellen.** Das —
und nicht der Code dieses Plugins — ist die eigentliche Garantie, dass sich
Graylog von NetBox aus nicht verändern lässt.

### Was „nur lesend" hier genau heißt

Jeder Aufruf holt entweder Daten oder lässt Graylog eine Suche ausführen. Der
alte Such-Endpunkt ist ein reines `GET`. Die neuere Views-Such-API nicht: sie
braucht ein `POST`, um eine Suche anzumelden, und ein weiteres, um sie
auszuführen. Dabei entsteht in Graylog ein kurzlebiges Suchobjekt und es kommen
Ergebnisse zurück — gespeicherte Daten werden nicht verändert. Ist in Ihrer
Umgebung nur `GET` akzeptabel, die Such-API in den Einstellungen auf `legacy`
festnageln.

### Zuordnung von Quellen zu NetBox-Objekten

Exakt, in dieser Reihenfolge, erster Treffer gewinnt:

| | Regel |
|---|---|
| 1 | **Manuelle Zuordnung** — einmal gesetzt, gilt immer |
| 2 | **IP-Adresse** — die Quelle gegen alle IPs des Objekts |
| 3 | **Hostname**, Groß-/Kleinschreibung egal |
| 4 | **Hostname nach Abschneiden einer konfigurierten Domänen-Endung** |

Alles andere bleibt nicht zugeordnet und wird als solches aufgeführt.

**Es gibt bewusst keine unscharfe Zuordnung.** `srv-web-01` und `srv-web-02`
unterscheiden sich um ein Zeichen — jede Ähnlichkeitsrechnung sagt „96 %
Übereinstimmung", dabei sind es zwei verschiedene Maschinen. Bei durchnummerierten
Namensschemata, also überall in einem ernstzunehmenden NetBox, liegt der
ähnlichste Kandidat systematisch daneben. Logs würden dem Nachbarserver zugeordnet
und niemand würde es merken. Die Ähnlichkeit wird ausschließlich zum **Sortieren**
der Vorschläge neben einer nicht zugeordneten Quelle benutzt; sie ordnet nie selbst
zu.

Steht ein zentraler Syslog-Weiterleiter vor Graylog, tragen alle Meldungen dessen
Adresse und Regel 2 trifft nichts Brauchbares. Dann muss das Quellfeld den
Hostnamen tragen — dafür sind Regel 3 und 4 da.

### Die Seiten

- **Quellen** — alles, was Graylog meldet, mit Zählern, filterbar nach zugeordnet,
  nicht zugeordnet, still, nie gesehen und ignoriert.
- **Still** — in NetBox zugeordnet, sendet aber nichts mehr. Tot, falsch
  konfiguriert oder Karteileiche. Keins der beiden Systeme erkennt das allein.
- **Nie in Graylog gesehen** — die andere Hälfte des Abgleichs.
- **Cluster** — Knoten mit Ampel grün/gelb/rot, Indexer-Zustand, Journal-Rückstau,
  jeder Knoten verlinkt auf seine NetBox-VM.
- **Am Objekt** — Geräte und VMs mit zugeordneter Quelle bekommen eine
  Graylog-Kachel mit Zählern, letzten Meldungen auf Knopfdruck und einem Link nach
  Graylog.

### Last und Sicherheit

- Ein Abruf ist eine **einzige gruppierte Abfrage für alle Hosts**, nicht eine
  Abfrage pro Gerät. Ein Standort mit 800 Geräten kostet drei Anfragen.
- Cluster-Kachel und Meldungsliste laden **nach** dem Seitenaufbau. Ein langsames
  oder totes Graylog liefert eine leere Kachel, niemals eine hängende
  NetBox-Seite.
- Die Zuordnung liegt in einer plugin-eigenen Tabelle. **Graylog schreibt nie in
  ein NetBox-Kernobjekt** — löscht man das Plugin, ist die Zuordnung weg und
  NetBox unberührt.
- Der Meldungs-Endpunkt antwortet nur für eine Quelle, die einem Objekt zugeordnet
  ist, das der Aufrufer sehen darf.

---

## 9. Patchmanagement und CheckMK

Führt Patchstand, Betriebssystem, Zuständige und Update-Historie je virtueller
Maschine oder physischem Server.

- **Status** grün / gelb / rot, entweder von Hand gepflegt oder aus CheckMK gelesen.
- **Überfälligkeitsschwelle** — Einträge ohne Patch innerhalb von N Tagen gelten
  als überfällig.
- **Eskalation** — ein Eintrag, der N Tage auf *gelb* steht, wird von selbst *rot*.
- **Kontakte** — Administrator und Verfahrensbetreuer aus den NetBox-Kontakten.
- **Update-Historie** — ein Eintrag je Patchlauf, mit Ticketnummer und Notiz.
- **Zugriff** wird über NetBox-Gruppennamen in den Plugin-Einstellungen geregelt,
  nicht über Django-Berechtigungen.

### CheckMK

Die Anbindung ist ein **Pull**: NetBox liest aus CheckMK. Es wird nichts nach
CheckMK geschrieben, ein Automationsbenutzer mit reinem Leserecht genügt.

Auf der Einstellungsseite konfiguriert: Site-URL, Automationsbenutzer,
Geheimnis, Servicefilter und Abgleichintervall. Das Geheimnis wird verschlüsselt
gespeichert und nie wieder angezeigt.

Ein stehengebliebener Abgleich ist die Störung, die am meisten weh tut, weil die
Seite weiter einen Patchstand zeigt, der still aufgehört hat zu stimmen. Das
Dashboard sagt deshalb ausdrücklich, wenn der letzte erfolgreiche Abgleich älter
ist als das doppelte Intervall.

---

## 10. Störungssuche

**Das Plugin taucht nicht in der Seitenleiste auf.**
`PLUGINS` in der `configuration.py` gesetzt? Migrationen gelaufen? NetBox neu
gestartet? Die Beschriftungen in der Seitenleiste ändern sich erst beim Neustart —
die Reiter innerhalb des Plugins sofort.

**Änderungen werden nicht blockiert.**
In dieser Reihenfolge prüfen: globaler Schalter, Dry-Run-Modus, ob der Benutzer in
den ausgenommenen Benutzern oder Gruppen steht, und ob eine Modellrichtlinie die
Erzwingung für dieses Modell abschaltet.

**Eine Seite meldet eine fehlende Spalte.**
Die Migrationen wurden nicht oder nur teilweise ausgeführt.
`python manage.py migrate netbox_force`.

**„Es läuft kein Hintergrundprozess."**
`netbox-rq` läuft nicht. CheckMK-Abgleich und Graylog-Abruf laufen dann nur auf
Knopfdruck.

**In Graylog kommt nichts an.**
Transport von UDP auf TCP umstellen. UDP kann einen Fehler nicht melden, TCP
schon — und dessen Fehlermeldung sagt, ob der Port falsch ist oder die Meldung
abgelehnt wurde.

**Die Graylog-Kachel am Gerät bleibt leer.**
Dem Gerät ist keine Quelle zugeordnet. Unter *Quellen → Nicht zugeordnet*
zuordnen, oder die eigene Domänen-Endung in den Einstellungen eintragen, damit
der FQDN gekürzt werden kann.

**Nach einer Änderung von `SECRET_KEY` funktionieren CheckMK-Geheimnis oder Graylog-Token nicht mehr.**
Beide sind mit einem aus `SECRET_KEY` abgeleiteten Schlüssel verschlüsselt. Sie
müssen neu eingegeben werden.

---

## 11. Sprache umstellen

Die Sprache ist eine Einstellung **je Installation**, nicht je Benutzer. Sie wird
auf der Einstellungsseite geändert.

Reiter und Seiten innerhalb des Plugins stellen sich sofort um. Die Beschriftungen
in der Seitenleiste werden einmal beim Start aufgebaut und ändern sich erst nach
einem Neustart von NetBox.

Die Meldungen, die Benutzern beim Blockieren angezeigt werden, folgen dieser
Einstellung. API-Fehlermeldungen und die an Graylog gesendeten Meldungen bleiben
englisch — siehe die Anmerkung im [Dokumentationsverzeichnis](../README.md).

---

## 12. Lizenz

AGPL-3.0. Siehe [LICENSE](../../LICENSE).
