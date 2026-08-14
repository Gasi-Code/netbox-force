# NetBox Force — Guida (italiano)

[← Tutte le lingue](../README.md) · [README del progetto](../../README.md) · [Registro delle modifiche](../../CHANGELOG.md)

---

## 1. Che cosa fa il plugin

NetBox registra *che cosa* è cambiato. NetBox Force decide *se la modifica sia
ammessa*, e può pretendere una motivazione prima di lasciarla passare.

Si colloca fra ogni operazione di salvataggio o eliminazione e la banca dati.
Prima che una modifica venga scritta può verificare:

- che sia stato indicato un commento di registro e che sia abbastanza lungo
- che il commento non sia composto solo da parole vuote
- che il commento citi un numero di ticket
- che la modifica avvenga entro una finestra temporale approvata
- che i valori dei campi rispettino uno schema di denominazione
- che i campi obbligatori siano davvero compilati

Lo accompagnano altri due moduli:

- **Gestione patch** — stato delle patch, sistema operativo, responsabili e
  cronologia degli aggiornamenti per macchina virtuale o server fisico,
  facoltativamente alimentata da CheckMK.
- **Graylog** — invia gli eventi di audit verso l'esterno e riporta le
  informazioni di log accanto all'oggetto a cui appartengono.

Tutto è facoltativo. Dopo l'installazione è attivo solo il controllo di presenza
del commento, con un minimo di due caratteri. Il resto si attiva dall'interfaccia
web.

---

## 2. Requisiti

| Componente | Versione | Note |
|---|---|---|
| NetBox | 4.0.0 o successivo | |
| Python | 3.10 o successivo | |
| PostgreSQL | — | Richiesto da NetBox stesso |
| `cryptography` | qualsiasi | Incluso in NetBox. Senza di esso il segreto CheckMK e il token Graylog vengono salvati in chiaro, e il plugin lo dichiara nella pagina delle impostazioni |
| `requests` | qualsiasi | Incluso in NetBox. Necessario per CheckMK e Graylog |
| Processo RQ | — | Solo per la sincronizzazione CheckMK pianificata e l'interrogazione Graylog. Senza, entrambe funzionano comunque su richiesta, e la pagina lo dichiara |

---

## 3. Installazione

### 3.1 Installare il pacchetto

```bash
source /opt/netbox/venv/bin/activate
pip install git+https://github.com/Gasi-Code/netbox-force.git
```

### 3.2 Registrare il plugin

In `configuration.py`:

```python
PLUGINS = ['netbox_force']
```

### 3.3 Eseguire le migrazioni

```bash
cd /opt/netbox/netbox
python manage.py migrate netbox_force
python manage.py collectstatic --no-input
```

### 3.4 Riavviare NetBox

```bash
sudo systemctl restart netbox netbox-rq
```

### 3.5 Docker

```bash
docker exec -it <contenitore> pip install git+https://github.com/Gasi-Code/netbox-force.git
docker exec -it <contenitore> /opt/netbox/netbox/manage.py migrate netbox_force
docker restart <contenitore>
```

Sull'immagine di LinuxServer.io **non** usare script `custom-cont-init.d` per
l'installazione. Vengono eseguiti *dopo* gli script di avvio di NetBox, il che può
far fallire le migrazioni. I Docker Mods vengono eseguiti prima.

Un'installazione fatta nel filesystem del contenitore non sopravvive a un
aggiornamento dell'immagine. Aggiungere il plugin al meccanismo di installazione
persistente dell'immagine, altrimenti sparirà al prossimo pull.

---

## 4. Aggiornamento

```bash
source /opt/netbox/venv/bin/activate
pip install --force-reinstall --no-cache-dir git+https://github.com/Gasi-Code/netbox-force.git
```

`--force-reinstall --no-cache-dir` serve perché pip mette in cache per numero di
versione e altrimenti salterebbe la ricostruzione della stessa versione.

**Verificare prima di riavviare.** Questo passo importa il plugin senza toccare il
processo in esecuzione. Se segnala un errore, non riavviare: il NetBox attivo ha
ancora il codice precedente in memoria e continua a funzionare:

```bash
cd /opt/netbox/netbox
python manage.py check
```

Poi:

```bash
python manage.py migrate netbox_force
python manage.py collectstatic --no-input
sudo systemctl restart netbox netbox-rq
```

### Tornare indietro

```bash
pip install --force-reinstall --no-cache-dir \
  git+https://github.com/Gasi-Code/netbox-force.git@<commit>
sudo systemctl restart netbox netbox-rq
```

Di norma le migrazioni non devono essere annullate. Le colonne aggiuntive non
disturbano il codice più vecchio: semplicemente non le conosce. Fare comunque una
copia della banca dati prima di aggiornare.

---

## 5. File di configurazione

`PLUGINS_CONFIG` stabilisce **solo i valori iniziali**. Dopo il primo avvio ogni
impostazione è gestita nell'interfaccia web e conservata nella banca dati.

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

| Impostazione | Predefinito | Significato |
|---|---|---|
| `min_length` | `2` | Caratteri minimi in un commento di registro |
| `exempt_users` | vedi sopra | Utenti esentati da ogni controllo, maiuscole indifferenti |
| `enforce_on_create` | `False` | Pretendere un commento anche alla creazione |
| `enforce_on_delete` | `True` | Pretendere un commento anche all'eliminazione |
| `extra_exempt_models` | `[]` | Altri modelli esentati, formato `app.model` |
| `checkmk_secret` | `''` | Facoltativo. Tiene il segreto CheckMK del tutto fuori dalla banca dati; ha allora la precedenza sul campo dell'interfaccia |

---

## 6. Le pagine

I superutenti trovano **NetBox Force** nella barra laterale. Tutte le pagine sono
riservate ai superutenti salvo diversa indicazione.

| Pagina | Scopo |
|---|---|
| **Impostazioni** | Tutte le regole di applicazione, esenzioni, moduli, webhook, CheckMK |
| **Regole di validazione** | Schemi di denominazione e campi obbligatori, per modello e campo |
| **Politiche per modello** | Deroghe alle impostazioni globali, per modello |
| **Violazioni** | Registro filtrabile di ogni modifica bloccata, esportabile in CSV |
| **Graylog** | Invio e lettura, vedi sezioni 7 e 8 |
| **Cruscotto** | Statistiche: quali funzioni sono attive, modifiche bloccate, utenti più frequenti, andamento a 30 giorni |
| **Modelli di importazione** | Modelli CSV scaricabili per l'importazione di massa di NetBox. Visibili a tutti gli utenti autenticati quando attivati |
| **Guida** | Pagina di testo libero per i propri utenti. Visibile a tutti gli utenti autenticati quando attivata |
| **Gestione patch** | Vedi sezione 9 |

Due impostazioni meritano una menzione a parte:

- **Interruttore globale** — sospende tutti i controlli, per esempio durante una
  finestra di manutenzione.
- **Modalità di prova (dry-run)** — registra le violazioni senza bloccare nulla.
  È il modo corretto di introdurre una nuova regola: si vede che cosa *sarebbe
  stato* bloccato prima di fermare davvero qualcuno.

---

## 7. Graylog — invio

Invia gli eventi di audit da NetBox a Graylog tramite GELF.

### A che serve

Tre cose non sono registrate da nessun'altra parte in NetBox:

- **Gli accessi falliti.** NetBox non li conserva affatto.
- **IP di origine e user agent** di una modifica. Il registro modifiche di NetBox
  non porta né l'uno né l'altro.
- **Le modifiche alle impostazioni del plugin stesso.** Non sono coperte dal
  registro di NetBox: chi disattivava l'applicazione delle regole non lasciava
  prima alcuna traccia.

### Configurazione

Nella pagina **Graylog**, metà superiore: host, porta, trasporto. Poi *Invia
evento di prova*.

Cominciare con **UDP**. Se non arriva nulla, passare a **TCP**: per costruzione
UDP non può segnalare un guasto, TCP sì. Questo distingue «porta sbagliata» da
«messaggio scartato».

| Trasporto | Conferma la consegna | Cifrato |
|---|---|---|
| UDP | no | no |
| TCP | sì | no |
| TCP + TLS | sì | sì |
| HTTP | sì | no |
| HTTPS | sì | sì |

UDP è corretto dentro una rete locale e sbagliato attraverso internet.

### Che cosa viene inviato

Una riga per tipo di evento, ciascuna con casella e gravità syslog: oggetto
creato, modificato, eliminato; accesso; disconnessione; accesso fallito; modifica
bloccata; impostazioni del plugin modificate.

### Volume

Una richiesta che modifica più oggetti della soglia impostata viene segnalata come
**un unico evento riepilogativo**. Importare 500 dispositivi è una operazione: 500
righe quasi identiche la rendono più difficile da vedere, non più facile.

Riepilogare anziché limitare il ritmo è una scelta deliberata. Una coda che si
svuota più lentamente di quanto si riempia scarta gli eventi *più recenti*, cioè
proprio la metà sbagliata.

### Nomi dei campi

Ogni evento porta gli stessi campi, così le ricerche restano semplici:

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

`_request_id` raggruppa tutto ciò che una richiesta ha modificato. Quaranta
dispositivi modificati insieme sono una operazione, non quaranta enigmi.

### Tre cose da sapere

- **Un guasto di Graylog non può rallentare né far fallire un salvataggio in
  NetBox.** Gli eventi finiscono in una coda limitata svuotata da un thread in
  background. Quando la coda è piena, i nuovi eventi vengono scartati e contati, e
  il contatore è mostrato nella pagina.
- **Il testo del messaggio è sempre in inglese**, qualunque sia la lingua
  dell'interfaccia. Le query di allarme di Graylog si basano su quel testo;
  tradurlo romperebbe in silenzio ogni allarme non appena qualcuno cambiasse
  lingua.
- **L'IP del client viene letto da `X-Forwarded-For`** quando presente. Quella
  intestazione arriva dal client e può essere falsificata se NetBox è raggiungibile
  senza un reverse proxy davanti.

---

## 8. Graylog — lettura

Porta le informazioni di Graylog dentro NetBox, così da poter giudicare un host
senza aprire una seconda scheda.

### Configurazione

Metà inferiore della pagina **Graylog**: indirizzo web e token API, poi *Prova
connessione*. Il risultato indica la versione di Graylog, la forma di API di
ricerca rilevata, le sorgenti più rumorose e gli stream disponibili. *Interroga
ora* esegue subito una interrogazione.

**Emettere il token per un utente Graylog con ruolo di sola lettura.** È questo, e
non il codice di questo plugin, a garantire che Graylog non possa essere alterato
da NetBox.

### Che cosa significa qui «sola lettura», con precisione

Ogni chiamata recupera dati oppure chiede a Graylog di eseguire una ricerca. Il
vecchio endpoint di ricerca è un semplice `GET`. La più recente API di ricerca
Views no: richiede un `POST` per registrare una ricerca e un altro per eseguirla.
Questo crea un oggetto di ricerca effimero dentro Graylog e restituisce risultati;
i dati memorizzati non vengono modificati. Se nel vostro ambiente è accettabile
solo `GET`, fissare la forma di ricerca su `legacy` nelle impostazioni.

### Abbinare le sorgenti agli oggetti NetBox

Esatto, in questo ordine, vince il primo riscontro:

| | Regola |
|---|---|
| 1 | **Abbinamento manuale** — una volta impostato, prevale sempre |
| 2 | **Indirizzo IP** — la sorgente contro tutti gli IP dell'oggetto |
| 3 | **Nome host**, maiuscole indifferenti |
| 4 | **Nome host dopo aver tolto un suffisso di dominio configurato** |

Tutto il resto resta non abbinato ed è elencato come tale.

**Non esiste, deliberatamente, alcun abbinamento approssimativo.** `srv-web-01` e
`srv-web-02` differiscono di un carattere: qualsiasi misura di somiglianza li
dichiara simili al 96 % pur essendo due macchine diverse. In uno schema di nomi
numerato — cioè in qualunque NetBox degno di questo nome — il candidato più simile
è sistematicamente quello sbagliato. I log finirebbero archiviati sotto il server
vicino e nessuno se ne accorgerebbe. La somiglianza serve solo a **ordinare** i
suggerimenti accanto a una sorgente non abbinata; non abbina mai nulla.

Se davanti a Graylog c'è un relè syslog centrale, tutti i messaggi portano
l'indirizzo del relè e la regola 2 non trova nulla di utile. Il campo sorgente deve
allora portare il nome host, ed è a questo che servono le regole 3 e 4.

### Le pagine

- **Sorgenti** — tutto ciò che Graylog riporta, con contatori, filtrabile per
  abbinate, non abbinate, silenziose, mai viste e ignorate.
- **Silenziose** — abbinate in NetBox ma non inviano più nulla. Morte, mal
  configurate o residuo. Nessuno dei due sistemi se ne accorge da solo.
- **Mai viste in Graylog** — l'altra metà del riscontro incrociato.
- **Cluster** — nodi con spia verde/gialla/rossa, salute dell'indicizzatore,
  arretrato del journal, ogni nodo collegato alla sua macchina virtuale in NetBox.
- **Sull'oggetto** — dispositivi e macchine virtuali con una sorgente abbinata
  ricevono un riquadro Graylog con contatori, messaggi recenti su richiesta e un
  collegamento a Graylog.

### Carico e sicurezza

- Una interrogazione è **una sola query raggruppata per tutti gli host**, non una
  query per dispositivo. Una sede con 800 dispositivi costa tre richieste.
- Il riquadro del cluster e l'elenco dei messaggi si caricano **dopo** il
  rendering della pagina. Un Graylog lento o morto produce un riquadro vuoto, mai
  una pagina NetBox bloccata.
- L'abbinamento vive nella tabella propria del plugin. **Graylog non scrive mai in
  un oggetto centrale di NetBox**: rimuovendo il plugin sparisce l'abbinamento e
  NetBox resta intatto.
- L'endpoint dei messaggi risponde solo per una sorgente abbinata a un oggetto che
  il chiamante è autorizzato a vedere.

---

## 9. Gestione patch e CheckMK

Tiene traccia di stato delle patch, sistema operativo, responsabili e cronologia
degli aggiornamenti per macchina virtuale o server fisico.

- **Stato** verde / giallo / rosso, mantenuto a mano oppure letto da CheckMK.
- **Soglia di ritardo** — le voci non aggiornate entro N giorni sono segnate in
  ritardo.
- **Escalation** — una voce rimasta N giorni in *giallo* passa da sola a *rosso*.
- **Contatti** — amministratore e responsabile di processo dagli oggetti contatto
  di NetBox.
- **Cronologia aggiornamenti** — una voce per passaggio di patch, con numero di
  ticket e nota.
- **L'accesso** si concede per nome di gruppo NetBox nelle impostazioni del
  plugin, non tramite i permessi di Django.

### CheckMK

L'integrazione è un **pull**: NetBox legge da CheckMK. In CheckMK non viene
scritto nulla, quindi basta un utente di automazione in sola lettura.

Si configura nella pagina delle impostazioni: URL del sito, utente di automazione,
segreto, filtro dei servizi e intervallo di sincronizzazione. Il segreto è
conservato cifrato e non viene più mostrato.

Una sincronizzazione ferma è il guasto che fa più male, perché la pagina continua
a mostrare uno stato delle patch che ha smesso in silenzio di essere vero. Il
cruscotto dichiara perciò apertamente quando l'ultima sincronizzazione riuscita è
più vecchia del doppio dell'intervallo impostato.

---

## 10. Risoluzione dei problemi

**Il plugin non compare nella barra laterale.**
`PLUGINS` è impostato in `configuration.py`? Le migrazioni sono state eseguite?
NetBox è stato riavviato? Le etichette della barra laterale si aggiornano solo al
riavvio; le schede dentro il plugin subito.

**Le modifiche non vengono bloccate.**
Controllare, in quest'ordine: l'interruttore globale, la modalità di prova, se
l'utente è fra gli utenti o i gruppi esentati, e se una politica per modello
disattiva l'applicazione per quel modello.

**Una pagina segnala una colonna mancante.**
Le migrazioni non sono state eseguite, o solo in parte.
`python manage.py migrate netbox_force`.

**«Non è in esecuzione alcun processo in background».**
`netbox-rq` non è avviato. La sincronizzazione CheckMK e l'interrogazione Graylog
vengono allora eseguite solo premendo il pulsante.

**In Graylog non arriva nulla.**
Cambiare il trasporto da UDP a TCP. UDP non può segnalare un guasto; TCP sì, e il
suo messaggio di errore dice se la porta è sbagliata o se il messaggio è stato
rifiutato.

**Il riquadro Graylog su un dispositivo resta vuoto.**
Al dispositivo non è abbinata alcuna sorgente. Aprire *Sorgenti → Non abbinate* e
abbinarla, oppure aggiungere il proprio suffisso di dominio nelle impostazioni
perché l'FQDN possa essere accorciato.

**Dopo aver cambiato `SECRET_KEY` il segreto CheckMK o il token Graylog non funziona più.**
Entrambi sono cifrati con una chiave derivata da `SECRET_KEY`. Vanno inseriti di
nuovo.

---

## 11. Cambiare lingua

La lingua è un'impostazione **per installazione**, non per utente. Si cambia nella
pagina delle impostazioni.

Le schede e le pagine dentro il plugin passano subito alla nuova lingua. Le
etichette della barra laterale sono costruite una volta all'avvio e cambiano solo
dopo un riavvio di NetBox.

I messaggi mostrati agli utenti in caso di blocco seguono questa impostazione. I
messaggi di errore delle API e quelli inviati a Graylog restano in inglese: vedi la
nota nell'[indice della documentazione](../README.md).

---

## 12. Licenza

AGPL-3.0. Vedi [LICENSE](../../LICENSE).
