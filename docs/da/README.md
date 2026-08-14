# NetBox Force — Vejledning (dansk)

[← Alle sprog](../README.md) · [Projekt-README](../../README.md) · [Ændringslog](../../CHANGELOG.md)

---

## 1. Hvad pluginnet gør

NetBox registrerer, *hvad* der blev ændret. NetBox Force afgør, *om ændringen
overhovedet er tilladt*, og kan kræve en begrundelse, før den slipper igennem.

Det ligger mellem hver gemme- og slettehandling og databasen. Før en ændring
skrives, kan det kontrollere:

- om der er angivet en logbemærkning, og om den er lang nok
- om bemærkningen ikke kun består af tomme ord
- om bemærkningen nævner et sagsnummer
- om ændringen sker inden for et godkendt tidsvindue
- om feltværdier følger et navngivningsmønster
- om påkrævede felter faktisk er udfyldt

To yderligere moduler følger med:

- **Patchstyring** — patchstatus, styresystem, ansvarlige og opdateringshistorik
  pr. virtuel maskine eller fysisk server, valgfrit fodret fra CheckMK.
- **Graylog** — sender revisionshændelser ud og henter logoplysninger tilbage ved
  siden af det objekt, de hører til.

Alt er valgfrit. Efter installationen er kun kontrollen for tilstedeværelse af
bemærkningen aktiv, med mindst to tegn. Resten slås til i webfladen.

---

## 2. Forudsætninger

| Komponent | Version | Bemærkning |
|---|---|---|
| NetBox | 4.0.0 eller nyere | |
| Python | 3.10 eller nyere | |
| PostgreSQL | — | Krævet af NetBox selv |
| `cryptography` | vilkårlig | Følger med NetBox. Uden den gemmes CheckMK-hemmeligheden og Graylog-token ukrypteret, og pluginnet siger det på indstillingssiden |
| `requests` | vilkårlig | Følger med NetBox. Nødvendig til CheckMK og Graylog |
| RQ-proces | — | Kun til den planlagte CheckMK-synkronisering og Graylog-hentning. Uden kører begge stadig efter behov, og siden siger det |

---

## 3. Installation

### 3.1 Installér pakken

```bash
source /opt/netbox/venv/bin/activate
pip install git+https://github.com/Gasi-Code/netbox-force.git
```

### 3.2 Registrér pluginnet

I `configuration.py`:

```python
PLUGINS = ['netbox_force']
```

### 3.3 Kør migreringerne

```bash
cd /opt/netbox/netbox
python manage.py migrate netbox_force
python manage.py collectstatic --no-input
```

### 3.4 Genstart NetBox

```bash
sudo systemctl restart netbox netbox-rq
```

### 3.5 Docker

```bash
docker exec -it <container> pip install git+https://github.com/Gasi-Code/netbox-force.git
docker exec -it <container> /opt/netbox/netbox/manage.py migrate netbox_force
docker restart <container>
```

Brug **ikke** `custom-cont-init.d`-scripts til installationen på LinuxServer.io-
imaget. De kører *efter* NetBox' egne init-scripts, hvilket kan få migreringer til
at fejle. Docker Mods kører før dem.

En installation i containerens filsystem overlever ikke en image-opdatering. Læg
pluginnet ind i imagets varige installationsmekanisme, ellers er det væk efter næste
pull.

---

## 4. Opdatering

```bash
source /opt/netbox/venv/bin/activate
pip install --force-reinstall --no-cache-dir git+https://github.com/Gasi-Code/netbox-force.git
```

`--force-reinstall --no-cache-dir` er nødvendigt, fordi pip cacher efter
versionsnummer og ellers ville springe en genopbygning af samme version over.

**Kontrollér før genstart.** Dette trin indlæser pluginnet uden at røre den kørende
proces. Melder det en fejl, så lad være med at genstarte — det kørende NetBox har
stadig den gamle kode i hukommelsen og arbejder videre:

```bash
cd /opt/netbox/netbox
python manage.py check
```

Derefter:

```bash
python manage.py migrate netbox_force
python manage.py collectstatic --no-input
sudo systemctl restart netbox netbox-rq
```

### Tilbage til en ældre version

```bash
pip install --force-reinstall --no-cache-dir \
  git+https://github.com/Gasi-Code/netbox-force.git@<commit>
sudo systemctl restart netbox netbox-rq
```

Migreringerne skal som regel ikke rulles tilbage. Ekstra kolonner generer ikke
ældre kode — den kender dem ganske enkelt ikke. Tag alligevel en databasekopi før
opdateringen.

---

## 5. Konfigurationsfil

`PLUGINS_CONFIG` fastsætter **kun startværdierne**. Efter første opstart styres hver
indstilling i webfladen og gemmes i databasen.

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

| Indstilling | Standard | Betydning |
|---|---|---|
| `min_length` | `2` | Mindste antal tegn i en logbemærkning |
| `exempt_users` | se ovenfor | Brugere fritaget for alle kontroller, uden hensyn til store og små bogstaver |
| `enforce_on_create` | `False` | Kræv også bemærkning ved oprettelse |
| `enforce_on_delete` | `True` | Kræv også bemærkning ved sletning |
| `extra_exempt_models` | `[]` | Flere fritagne modeller, formatet `app.model` |
| `checkmk_secret` | `''` | Valgfrit. Holder CheckMK-hemmeligheden helt uden for databasen; den får så forrang frem for feltet i fladen |

---

## 6. Siderne

Superbrugere finder **NetBox Force** i sidepanelet. Alle sider er forbeholdt
superbrugere, medmindre andet er anført.

| Side | Formål |
|---|---|
| **Indstillinger** | Alle håndhævelsesregler, fritagelser, moduler, webhook, CheckMK |
| **Valideringsregler** | Navnemønstre og påkrævede felter, pr. model og felt |
| **Modelpolitikker** | Afvigelser fra de globale indstillinger, pr. model |
| **Overtrædelser** | Filtrerbar log over hver blokeret ændring, kan eksporteres som CSV |
| **Graylog** | Afsendelse og læsning, se afsnit 7 og 8 |
| **Oversigt** | Statistik: hvilke funktioner er slået til, blokerede ændringer, hyppigste brugere, 30-dages forløb |
| **Importskabeloner** | CSV-skabeloner til download til NetBox' masseimport. Synlige for alle indloggede brugere, når slået til |
| **Vejledning** | Fritekstside til egne brugere. Synlig for alle indloggede brugere, når slået til |
| **Patchstyring** | Se afsnit 9 |

To indstillinger fortjener en særlig omtale:

- **Global kontakt** — sætter alle kontroller på pause, for eksempel under et
  servicevindue.
- **Prøvetilstand (dry-run)** — registrerer overtrædelser uden at blokere noget. Den
  rigtige måde at indføre en ny regel på: man ser, hvad der *ville være* blevet
  blokeret, før nogen faktisk standses.

---

## 7. Graylog — afsendelse

Sender revisionshændelser fra NetBox til Graylog via GELF.

### Hvorfor

Tre ting er ikke registreret noget andet sted i NetBox:

- **Mislykkede logins.** NetBox gemmer dem slet ikke.
- **Kilde-IP og user agent** for en ændring. NetBox' ændringslog bærer ingen af
  delene.
- **Ændringer af pluginnets egne indstillinger.** De er ikke omfattet af NetBox'
  ændringslog — den, der slog håndhævelsen fra, efterlod hidtil ingen spor.

### Opsætning

På siden **Graylog**, øverste halvdel: vært, port, transport. Derefter *Send
testhændelse*.

Begynd med **UDP**. Kommer der intet frem, så skift til **TCP** — UDP kan af natur
ikke melde en fejl, det kan TCP. Det skelner "forkert port" fra "besked kasseret".

| Transport | Bekræfter levering | Krypteret |
|---|---|---|
| UDP | nej | nej |
| TCP | ja | nej |
| TCP + TLS | ja | ja |
| HTTP | ja | nej |
| HTTPS | ja | ja |

UDP er rigtigt inden for et lokalt net og forkert over internettet.

### Hvad der sendes

Én række pr. hændelsestype, hver med et flueben og en syslog-alvorlighed: objekt
oprettet, ændret, slettet; login; logud; mislykket login; blokeret ændring;
plugin-indstillinger ændret.

### Mængde

En forespørgsel, der ændrer flere objekter end den indstillede tærskel, meldes som
**én samlet hændelse**. En import af 500 enheder er én handling — 500 næsten ens
linjer gør den sværere at få øje på, ikke lettere.

At sammenfatte frem for at strube er et bevidst valg. En kø, der tømmes langsommere,
end den fyldes, kasserer de *nyeste* hændelser, altså netop den forkerte halvdel.

### Feltnavne

Hver hændelse bærer de samme felter, så søgninger forbliver enkle:

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

`_request_id` samler alt, hvad én forespørgsel har ændret. Fyrre enheder redigeret
på én gang er én handling, ikke fyrre gåder.

### Tre ting at vide

- **Et Graylog-nedbrud kan hverken forsinke eller vælte en gemmehandling i NetBox.**
  Hændelser lægges i en begrænset kø, som en baggrundstråd tømmer. Er køen fuld,
  kasseres nye hændelser og tælles, og tælleren vises på siden.
- **Beskedteksten er altid engelsk**, uanset fladens sprog. Graylogs alarmsøgninger
  bygger på den tekst; en oversættelse ville lydløst ødelægge hver alarm, så snart
  nogen skiftede sprog.
- **Klientens IP læses fra `X-Forwarded-For`**, når den er til stede. Den header
  kommer fra klienten og kan forfalskes, hvis NetBox kan nås uden en omvendt proxy
  foran.

---

## 8. Graylog — læsning

Henter Graylog-oplysninger ind i NetBox, så en vært kan bedømmes uden at åbne en
ekstra fane.

### Opsætning

Nederste halvdel af siden **Graylog**: webadresse og API-token, derefter *Test
forbindelsen*. Resultatet angiver Graylog-versionen, den fundne søge-API-form, de
mest støjende kilder og de tilgængelige streams. *Hent nu* udfører en hentning
straks.

**Udsted token til en Graylog-bruger med en skrivebeskyttet rolle.** Det, og ikke
dette plugins kode, er dét, der garanterer, at Graylog ikke kan ændres fra NetBox.

### Hvad "kun læsning" præcist betyder her

Hvert kald henter data eller beder Graylog om at køre en søgning. Det gamle
søgeendepunkt er et almindeligt `GET`. Den nyere Views-søge-API er det ikke: den
kræver et `POST` for at registrere en søgning og endnu et for at køre den. Det
skaber et kortlivet søgeobjekt inde i Graylog og returnerer resultater; gemte data
ændres ikke. Er kun `GET` acceptabelt i jeres miljø, så lås søgeformen til `legacy`
i indstillingerne.

### At sammenkoble kilder med NetBox-objekter

Præcist, i denne rækkefølge, første træffer vinder:

| | Regel |
|---|---|
| 1 | **Manuel tilknytning** — når den først er sat, gælder den altid |
| 2 | **IP-adresse** — kilden mod alle objektets IP-adresser |
| 3 | **Værtsnavn**, uden hensyn til store og små bogstaver |
| 4 | **Værtsnavn efter fjernelse af et indstillet domænesuffiks** |

Alt andet forbliver uden tilknytning og opføres som sådan.

**Der er bevidst ingen tilnærmet sammenkobling.** `srv-web-01` og `srv-web-02` er
forskellige med ét tegn, så ethvert lighedsmål kalder dem 96 % ens, skønt de er to
forskellige maskiner. I et nummereret navneskema — det vil sige i ethvert NetBox,
der er navnet værd — er den mest lignende kandidat systematisk den forkerte. Logfiler
ville blive arkiveret under naboserveren, og ingen ville opdage det. Lighed bruges
udelukkende til at **sortere** forslagene ved siden af en kilde uden tilknytning;
den tilknytter aldrig selv noget.

Står der et centralt syslog-relæ foran Graylog, bærer alle beskeder relæets adresse,
og regel 2 rammer intet brugbart. Kildefeltet må da bære værtsnavnet, og det er
regel 3 og 4 til.

### Siderne

- **Kilder** — alt, hvad Graylog melder, med tællere, kan filtreres på tilknyttede,
  ikke-tilknyttede, tavse, aldrig set og ignorerede.
- **Tavse** — tilknyttet i NetBox, men sender intet mere. Død, forkert konfigureret
  eller en rest. Ingen af systemerne opdager det alene.
- **Aldrig set i Graylog** — den anden halvdel af krydstjekket.
- **Klynge** — knuder med grøn/gul/rød lampe, indekserens tilstand, journalefterslæb,
  hver knude linket til sin NetBox-VM.
- **På objektet** — enheder og virtuelle maskiner med en tilknyttet kilde får et
  Graylog-panel med tællere, seneste beskeder efter behov og et link til Graylog.

### Belastning og sikkerhed

- Én hentning er **én samlet forespørgsel for alle værter**, ikke én forespørgsel pr.
  enhed. En lokation med 800 enheder koster tre kald.
- Klyngepanelet og beskedlisten indlæses **efter**, at siden er tegnet. Et langsomt
  eller dødt Graylog giver et tomt panel, aldrig en hængende NetBox-side.
- Tilknytningen ligger i pluginnets egen tabel. **Graylog skriver aldrig i et
  NetBox-kerneobjekt** — fjernes pluginnet, forsvinder tilknytningen, og NetBox står
  urørt.
- Beskedendepunktet svarer kun for en kilde, der er tilknyttet et objekt, som den
  kaldende må se.

---

## 9. Patchstyring og CheckMK

Følger patchstatus, styresystem, ansvarlige og opdateringshistorik pr. virtuel
maskine eller fysisk server.

- **Status** grøn / gul / rød, enten vedligeholdt i hånden eller læst fra CheckMK.
- **Forsinkelsestærskel** — poster uden patch inden for N dage markeres som forsinkede.
- **Eskalering** — en post, der står N dage på *gul*, bliver af sig selv *rød*.
- **Kontakter** — administrator og procesansvarlig fra NetBox' kontaktobjekter.
- **Opdateringshistorik** — én post pr. patchkørsel, med sagsnummer og note.
- **Adgang** gives via NetBox-gruppenavne i plugin-indstillingerne, ikke via
  Django-rettigheder.

### CheckMK

Integrationen er et **pull**: NetBox læser fra CheckMK. Der skrives intet til
CheckMK, så en automatiseringsbruger med kun læseadgang er nok.

Konfigureres på indstillingssiden: site-URL, automatiseringsbruger, hemmelighed,
servicefilter og synkroniseringsinterval. Hemmeligheden gemmes krypteret og vises
aldrig igen.

En gået i stå synkronisering er den fejl, der gør mest ondt, fordi siden bliver ved
med at vise en patchstatus, der lydløst holdt op med at passe. Oversigten siger
derfor direkte, når den seneste vellykkede synkronisering er ældre end det dobbelte
af det indstillede interval.

---

## 10. Fejlsøgning

**Pluginnet dukker ikke op i sidepanelet.**
Er `PLUGINS` sat i `configuration.py`? Er migreringerne kørt? Er NetBox genstartet?
Etiketterne i sidepanelet opdateres først ved genstart; fanerne inde i pluginnet
straks.

**Ændringer bliver ikke blokeret.**
Kontrollér i denne rækkefølge: den globale kontakt, prøvetilstanden, om brugeren står
blandt de fritagne brugere eller grupper, og om en modelpolitik slår håndhævelsen fra
for netop den model.

**En side melder en manglende kolonne.**
Migreringerne er ikke kørt, eller kun delvist.
`python manage.py migrate netbox_force`.

**"Der kører ingen baggrundsproces."**
`netbox-rq` kører ikke. CheckMK-synkroniseringen og Graylog-hentningen kører da kun
ved tryk på knappen.

**Der kommer intet frem i Graylog.**
Skift transporten fra UDP til TCP. UDP kan ikke melde en fejl; det kan TCP, og dens
fejlbesked siger, om porten er forkert, eller beskeden blev afvist.

**Graylog-panelet på en enhed forbliver tomt.**
Enheden har ingen tilknyttet kilde. Åbn *Kilder → Ikke tilknyttede* og tilknyt den,
eller tilføj jeres domænesuffiks i indstillingerne, så FQDN kan forkortes.

**Efter ændring af `SECRET_KEY` virker CheckMK-hemmeligheden eller Graylog-token ikke længere.**
Begge er krypteret med en nøgle afledt af `SECRET_KEY`. De skal indtastes igen.

---

## 11. Skift sprog

Sproget er en indstilling **pr. installation**, ikke pr. bruger. Det ændres på
indstillingssiden.

Faner og sider inde i pluginnet skifter straks. Etiketterne i sidepanelet bygges én
gang ved opstart og ændrer sig først efter en genstart af NetBox.

De beskeder, brugerne ser ved en blokering, følger denne indstilling.
API-fejlbeskeder og beskederne til Graylog forbliver engelske — se bemærkningen i
[dokumentationsoversigten](../README.md).

---

## 12. Licens

AGPL-3.0. Se [LICENSE](../../LICENSE).
