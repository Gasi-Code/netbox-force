# NetBox Force — Handleiding (Nederlands)

[← Alle talen](../README.md) · [Project-README](../../README.md) · [Wijzigingslogboek](../../CHANGELOG.md)

---

## 1. Wat de plugin doet

NetBox legt vast *wat* er is gewijzigd. NetBox Force beslist *of de wijziging
überhaupt is toegestaan*, en kan er vooraf een reden voor eisen.

De plugin zit tussen elke bewaar- en verwijderactie en de database. Voordat een
wijziging wordt weggeschreven, kan hij controleren:

- of er een logboekopmerking is meegegeven en of die lang genoeg is
- of die opmerking niet alleen uit holle woorden bestaat
- of de opmerking een ticketnummer noemt
- of de wijziging binnen een goedgekeurd tijdvenster valt
- of veldwaarden aan een naamgevingspatroon voldoen
- of verplichte velden werkelijk zijn ingevuld

Er horen nog twee modules bij:

- **Patchbeheer** — patchstatus, besturingssysteem, verantwoordelijken en
  updategeschiedenis per virtuele machine of fysieke server, desgewenst gevoed
  vanuit CheckMK.
- **Graylog** — stuurt auditgebeurtenissen naar buiten en haalt loginformatie terug
  naar het object waar die bij hoort.

Alles is optioneel. Na de installatie is alleen de controle op aanwezigheid van de
opmerking actief, met een minimum van twee tekens. De rest wordt in de
webinterface ingeschakeld.

---

## 2. Vereisten

| Onderdeel | Versie | Opmerking |
|---|---|---|
| NetBox | 4.0.0 of nieuwer | |
| Python | 3.10 of nieuwer | |
| PostgreSQL | — | Vereist door NetBox zelf |
| `cryptography` | willekeurig | Zit bij NetBox. Ontbreekt het, dan worden het CheckMK-geheim en het Graylog-token onversleuteld opgeslagen; de instellingenpagina meldt dat |
| `requests` | willekeurig | Zit bij NetBox. Nodig voor CheckMK en Graylog |
| RQ-proces | — | Alleen voor de geplande CheckMK-synchronisatie en Graylog-ophaalronde. Zonder werken beide nog op verzoek, en de pagina meldt dat |

---

## 3. Installatie

### 3.1 Pakket installeren

```bash
source /opt/netbox/venv/bin/activate
pip install git+https://github.com/Gasi-Code/netbox-force.git
```

### 3.2 Plugin aanmelden

In `configuration.py`:

```python
PLUGINS = ['netbox_force']
```

### 3.3 Migraties uitvoeren

```bash
cd /opt/netbox/netbox
python manage.py migrate netbox_force
python manage.py collectstatic --no-input
```

### 3.4 NetBox herstarten

```bash
sudo systemctl restart netbox netbox-rq
```

### 3.5 Docker

```bash
docker exec -it <container> pip install git+https://github.com/Gasi-Code/netbox-force.git
docker exec -it <container> /opt/netbox/netbox/manage.py migrate netbox_force
docker restart <container>
```

Gebruik bij het LinuxServer.io-image **geen** `custom-cont-init.d`-scripts voor de
installatie. Die draaien *na* de eigen init-scripts van NetBox, wat migraties kan
laten mislukken. Docker Mods draaien ervoor.

Een installatie in het containerbestandssysteem overleeft geen image-update. Zet
de plugin in het blijvende installatiemechanisme van het image, anders is hij na
de volgende pull verdwenen.

---

## 4. Bijwerken

```bash
source /opt/netbox/venv/bin/activate
pip install --force-reinstall --no-cache-dir git+https://github.com/Gasi-Code/netbox-force.git
```

`--force-reinstall --no-cache-dir` is nodig omdat pip op versienummer cachet en
anders het opnieuw bouwen van dezelfde versie zou overslaan.

**Controleer vóór het herstarten.** Deze stap laadt de plugin zonder het lopende
proces aan te raken. Komt er een fout, herstart dan niet: het draaiende NetBox
heeft de oude code nog in het geheugen en werkt door:

```bash
cd /opt/netbox/netbox
python manage.py check
```

Daarna:

```bash
python manage.py migrate netbox_force
python manage.py collectstatic --no-input
sudo systemctl restart netbox netbox-rq
```

### Terug naar een oudere versie

```bash
pip install --force-reinstall --no-cache-dir \
  git+https://github.com/Gasi-Code/netbox-force.git@<commit>
sudo systemctl restart netbox netbox-rq
```

De migraties hoeven daarvoor doorgaans niet te worden teruggedraaid. Extra kolommen
storen oudere code niet — die kent ze eenvoudigweg niet. Maak vooraf toch een
database-dump.

---

## 5. Configuratiebestand

`PLUGINS_CONFIG` legt **alleen de startwaarden** vast. Na de eerste start wordt
elke instelling in de webinterface beheerd en in de database bewaard.

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

| Instelling | Standaard | Betekenis |
|---|---|---|
| `min_length` | `2` | Minimaal aantal tekens in een logboekopmerking |
| `exempt_users` | zie boven | Gebruikers die van alle controles zijn vrijgesteld, hoofdletterongevoelig |
| `enforce_on_create` | `False` | Ook bij aanmaken een opmerking eisen |
| `enforce_on_delete` | `True` | Ook bij verwijderen een opmerking eisen |
| `extra_exempt_models` | `[]` | Verdere vrijgestelde modellen, formaat `app.model` |
| `checkmk_secret` | `''` | Optioneel. Houdt het CheckMK-geheim volledig buiten de database; het krijgt dan voorrang op het veld in de interface |

---

## 6. De pagina's

Superusers vinden **NetBox Force** in de zijbalk. Alle pagina's zijn tot superusers
beperkt tenzij anders vermeld.

| Pagina | Doel |
|---|---|
| **Instellingen** | Alle handhavingsregels, uitzonderingen, modules, webhook, CheckMK |
| **Validatieregels** | Naamgevingspatronen en verplichte velden, per model en veld |
| **Modelbeleid** | Afwijkingen van de globale instellingen, per model |
| **Overtredingen** | Filterbaar logboek van elke geblokkeerde wijziging, exporteerbaar als CSV |
| **Graylog** | Verzenden en lezen, zie paragraaf 7 en 8 |
| **Dashboard** | Statistiek: welke functies aanstaan, geblokkeerde wijzigingen, topgebruikers, verloop over 30 dagen |
| **Importsjablonen** | Downloadbare CSV-sjablonen voor de bulkimport van NetBox. Zichtbaar voor alle ingelogde gebruikers wanneer ingeschakeld |
| **Handleiding** | Vrije tekstpagina voor de eigen gebruikers. Zichtbaar voor alle ingelogde gebruikers wanneer ingeschakeld |
| **Patchbeheer** | Zie paragraaf 9 |

Twee instellingen verdienen aparte vermelding:

- **Globale schakelaar** — zet alle controles stil, bijvoorbeeld tijdens een
  onderhoudsvenster.
- **Proefmodus (dry-run)** — legt overtredingen vast zonder iets te blokkeren. De
  juiste manier om een nieuwe regel in te voeren: je ziet wat er geblokkeerd *zou
  zijn* voordat er werkelijk iemand wordt tegengehouden.

---

## 7. Graylog — verzenden

Stuurt auditgebeurtenissen van NetBox naar Graylog via GELF.

### Waarvoor

Drie dingen staan nergens anders in NetBox:

- **Mislukte aanmeldingen.** NetBox bewaart die helemaal niet.
- **Bron-IP en user agent** van een wijziging. Het wijzigingslogboek van NetBox
  draagt geen van beide.
- **Wijzigingen aan de instellingen van de plugin zelf.** Die vallen niet onder het
  NetBox-logboek — wie de handhaving uitzette, liet voorheen nergens een spoor na.

### Inrichten

Op de pagina **Graylog**, bovenste helft: host, poort, transport. Dan
*Testgebeurtenis versturen*.

Begin met **UDP**. Komt er niets aan, schakel dan over op **TCP**: UDP kan een
fout naar zijn aard niet melden, TCP wel. Dat onderscheidt "verkeerde poort" van
"bericht verworpen".

| Transport | Bevestigt aflevering | Versleuteld |
|---|---|---|
| UDP | nee | nee |
| TCP | ja | nee |
| TCP + TLS | ja | ja |
| HTTP | ja | nee |
| HTTPS | ja | ja |

UDP is juist binnen een lokaal netwerk en verkeerd over internet.

### Wat er wordt verstuurd

Eén regel per gebeurtenistype, elk met een vinkje en een syslog-ernst: object
aangemaakt, gewijzigd, verwijderd; aanmelding; afmelding; mislukte aanmelding;
geblokkeerde wijziging; plugin-instellingen gewijzigd.

### Hoeveelheid

Een verzoek dat meer objecten wijzigt dan de ingestelde drempel wordt als **één
samenvattende gebeurtenis** gemeld. Een import van 500 apparaten is één handeling —
500 bijna identieke regels maken die moeilijker zichtbaar, niet makkelijker.

Samenvatten in plaats van afknijpen is een bewuste keuze. Een wachtrij die
langzamer leegloopt dan hij volloopt, verwerpt de *nieuwste* gebeurtenissen, en dat
is precies de verkeerde helft.

### Veldnamen

Elke gebeurtenis draagt dezelfde velden, zodat zoeken eenvoudig blijft:

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

`_request_id` groepeert alles wat één verzoek heeft gewijzigd. Veertig tegelijk
bewerkte apparaten zijn één handeling, geen veertig raadsels.

### Drie dingen om te weten

- **Een storing bij Graylog kan een opslagactie in NetBox niet vertragen of laten
  mislukken.** Gebeurtenissen komen in een begrensde wachtrij die een
  achtergrondproces leegt. Is de wachtrij vol, dan worden nieuwe gebeurtenissen
  verworpen en geteld, en de teller staat op de pagina.
- **De berichttekst is altijd Engels**, ongeacht de taal van de interface.
  Graylog-alarmzoekopdrachten zoeken op die tekst; vertalen zou elk alarm stilletjes
  breken zodra iemand de taal wijzigde.
- **Het client-IP wordt uit `X-Forwarded-For` gelezen** als die aanwezig is. Die
  header komt van de client en kan vervalst worden als NetBox bereikbaar is zonder
  reverse proxy ervoor.

---

## 8. Graylog — lezen

Haalt Graylog-informatie naar NetBox, zodat een host beoordeeld kan worden zonder
een tweede tabblad te openen.

### Inrichten

Onderste helft van de pagina **Graylog**: webadres en API-token, dan *Verbinding
testen*. Het resultaat noemt de Graylog-versie, de herkende zoek-API, de
luidruchtigste bronnen en de beschikbare streams. *Nu ophalen* voert meteen een
ophaalronde uit.

**Geef het token uit voor een Graylog-gebruiker met een alleen-lezen rol.** Dat, en
niet de code van deze plugin, garandeert dat Graylog niet vanuit NetBox gewijzigd
kan worden.

### Wat "alleen lezen" hier precies betekent

Elke aanroep haalt gegevens op of laat Graylog een zoekopdracht uitvoeren. Het oude
zoekeindpunt is een gewone `GET`. De nieuwere Views-zoek-API niet: die heeft een
`POST` nodig om een zoekopdracht aan te melden en nog een om hem uit te voeren.
Daarbij ontstaat in Graylog een kortlevend zoekobject en komen resultaten terug;
opgeslagen gegevens worden niet gewijzigd. Is in uw omgeving alleen `GET`
aanvaardbaar, zet de zoek-API in de instellingen dan vast op `legacy`.

### Bronnen aan NetBox-objecten koppelen

Exact, in deze volgorde, de eerste treffer wint:

| | Regel |
|---|---|
| 1 | **Handmatige koppeling** — eenmaal gezet, gaat altijd voor |
| 2 | **IP-adres** — de bron tegen alle IP's van het object |
| 3 | **Hostnaam**, hoofdletterongevoelig |
| 4 | **Hostnaam na weglaten van een ingesteld domeinachtervoegsel** |

Al het overige blijft ongekoppeld en wordt als zodanig vermeld.

**Er is bewust geen benaderende koppeling.** `srv-web-01` en `srv-web-02`
verschillen één teken, dus elke gelijkenismaat noemt ze 96 % gelijk terwijl het
twee verschillende machines zijn. In een genummerd naamschema — dat wil zeggen in
elk NetBox dat die naam waard is — is de meest gelijkende kandidaat stelselmatig de
verkeerde. Logs zouden onder de buurserver belanden en niemand zou het merken.
Gelijkenis dient alleen om de suggesties naast een ongekoppelde bron te
**sorteren**; hij koppelt nooit zelf iets.

Staat er een centrale syslog-doorgever vóór Graylog, dan dragen alle berichten het
adres van die doorgever en levert regel 2 niets bruikbaars op. Het bronveld moet
dan de hostnaam dragen, en daarvoor zijn regel 3 en 4.

### De pagina's

- **Bronnen** — alles wat Graylog meldt, met tellers, filterbaar op gekoppeld,
  ongekoppeld, stil, nooit gezien en genegeerd.
- **Stil** — gekoppeld in NetBox maar stuurt niets meer. Dood, verkeerd
  geconfigureerd, of een overblijfsel. Geen van beide systemen ziet dit alleen.
- **Nooit in Graylog gezien** — de andere helft van de kruiscontrole.
- **Cluster** — knooppunten met groen/geel/rood lampje, gezondheid van de
  indexeerder, journaalachterstand, elk knooppunt gekoppeld aan zijn NetBox-VM.
- **Op het object** — apparaten en virtuele machines met een gekoppelde bron
  krijgen een Graylog-paneel met tellers, recente berichten op verzoek en een link
  naar Graylog.

### Belasting en veiligheid

- Eén ophaalronde is **één gegroepeerde query voor alle hosts**, geen query per
  apparaat. Een locatie met 800 apparaten kost drie verzoeken.
- Het clusterpaneel en de berichtenlijst laden **na** het opbouwen van de pagina.
  Een traag of dood Graylog levert een leeg paneel op, nooit een vastgelopen
  NetBox-pagina.
- De koppeling staat in de eigen tabel van de plugin. **Graylog schrijft nooit in
  een NetBox-kernobject** — de plugin verwijderen verwijdert de koppeling en laat
  NetBox onaangeroerd.
- Het berichteneindpunt antwoordt alleen voor een bron die gekoppeld is aan een
  object dat de aanroeper mag zien.

---

## 9. Patchbeheer en CheckMK

Houdt patchstatus, besturingssysteem, verantwoordelijken en updategeschiedenis bij
per virtuele machine of fysieke server.

- **Status** groen / geel / rood, met de hand bijgehouden of uit CheckMK gelezen.
- **Achterstanddrempel** — items die binnen N dagen niet gepatcht zijn, worden als
  achterstallig gemarkeerd.
- **Escalatie** — een item dat N dagen op *geel* staat, wordt vanzelf *rood*.
- **Contacten** — beheerder en proceseigenaar uit de contactobjecten van NetBox.
- **Updategeschiedenis** — één regel per patchronde, met ticketnummer en notitie.
- **Toegang** wordt geregeld via NetBox-groepsnamen in de plugin-instellingen, niet
  via Django-rechten.

### CheckMK

De koppeling is een **pull**: NetBox leest uit CheckMK. Er wordt niets naar CheckMK
geschreven, dus een automatiseringsgebruiker met alleen leesrecht volstaat.

Ingesteld op de instellingenpagina: site-URL, automatiseringsgebruiker, geheim,
servicefilter en synchronisatie-interval. Het geheim wordt versleuteld bewaard en
nooit meer getoond.

Een vastgelopen synchronisatie is de storing die het meest pijn doet, omdat de
pagina een patchstatus blijft tonen die stilletjes ophield te kloppen. Het
dashboard meldt daarom uitdrukkelijk wanneer de laatste geslaagde synchronisatie
ouder is dan tweemaal het ingestelde interval.

---

## 10. Problemen oplossen

**De plugin verschijnt niet in de zijbalk.**
Staat `PLUGINS` in `configuration.py`? Zijn de migraties uitgevoerd? Is NetBox
herstart? De labels in de zijbalk werken alleen bij een herstart bij; de tabbladen
binnen de plugin meteen.

**Wijzigingen worden niet geblokkeerd.**
Controleer in deze volgorde: de globale schakelaar, de proefmodus, of de gebruiker
bij de vrijgestelde gebruikers of groepen staat, en of een modelbeleid de handhaving
voor dat model uitschakelt.

**Een pagina meldt een ontbrekende kolom.**
De migraties zijn niet of maar deels uitgevoerd.
`python manage.py migrate netbox_force`.

**"Er draait geen achtergrondproces."**
`netbox-rq` draait niet. De CheckMK-synchronisatie en de Graylog-ophaalronde lopen
dan alleen op knopdruk.

**Er komt niets aan in Graylog.**
Zet het transport van UDP op TCP. UDP kan een fout niet melden; TCP wel, en de
foutmelding daarvan zegt of de poort verkeerd is of het bericht is geweigerd.

**Het Graylog-paneel bij een apparaat blijft leeg.**
Aan het apparaat is geen bron gekoppeld. Open *Bronnen → Niet gekoppeld* en koppel
hem, of voeg uw domeinachtervoegsel toe in de instellingen zodat de FQDN kan worden
ingekort.

**Na het wijzigen van `SECRET_KEY` werkt het CheckMK-geheim of het Graylog-token niet meer.**
Beide zijn versleuteld met een sleutel die van `SECRET_KEY` is afgeleid. Ze moeten
opnieuw worden ingevoerd.

---

## 11. Taal wijzigen

De taal is een instelling **per installatie**, niet per gebruiker. Ze wordt op de
instellingenpagina gewijzigd.

Tabbladen en pagina's binnen de plugin schakelen meteen om. De labels in de zijbalk
worden eenmalig bij het opstarten opgebouwd en veranderen pas na een herstart van
NetBox.

De meldingen die gebruikers bij een blokkade zien, volgen deze instelling.
API-foutmeldingen en de berichten naar Graylog blijven Engels — zie de opmerking in
de [documentatie-index](../README.md).

---

## 12. Licentie

AGPL-3.0. Zie [LICENSE](../../LICENSE).
