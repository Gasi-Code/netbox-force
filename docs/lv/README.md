# NetBox Force — Rokasgrāmata (latviešu)

[← Visas valodas](../README.md) · [Projekta README](../../README.md) · [Izmaiņu žurnāls](../../CHANGELOG.md)

---

## 1. Ko spraudnis dara

NetBox pieraksta, *kas* ir mainījies. NetBox Force izlemj, *vai izmaiņa vispār ir
pieļaujama*, un var iepriekš pieprasīt pamatojumu.

Tas atrodas starp katru saglabāšanas un dzēšanas darbību un datubāzi. Pirms izmaiņa
tiek ierakstīta, tas var pārbaudīt:

- vai ir norādīts žurnāla komentārs un vai tas ir pietiekami garš
- vai komentārs nesastāv tikai no tukšiem vārdiem
- vai komentārā minēts pieteikuma numurs
- vai izmaiņa notiek apstiprinātā laika logā
- vai lauku vērtības atbilst nosaukumu paraugam
- vai obligātie lauki tiešām ir aizpildīti

Tam pievienojas vēl divi moduļi:

- **Ielāpu pārvaldība** — ielāpu stāvoklis, operētājsistēma, atbildīgie un
  atjauninājumu vēsture katrai virtuālajai mašīnai vai fiziskajam serverim, pēc
  izvēles baroti no CheckMK.
- **Graylog** — sūta audita notikumus uz āru un atnes žurnālu ziņas atpakaļ pie tā
  objekta, kuram tās pieder.

Viss ir pēc izvēles. Pēc uzstādīšanas darbojas tikai komentāra esamības pārbaude ar
vismaz diviem rakstzīmēm. Pārējais tiek ieslēgts tīmekļa saskarnē.

---

## 2. Priekšnosacījumi

| Sastāvdaļa | Versija | Piezīmes |
|---|---|---|
| NetBox | 4.0.0 vai jaunāks | |
| Python | 3.10 vai jaunāks | |
| PostgreSQL | — | Prasa pats NetBox |
| `cryptography` | jebkura | Nāk līdzi NetBox. Bez tās CheckMK noslēpums un Graylog pilnvara tiek glabāti nešifrēti, un spraudnis to pasaka iestatījumu lapā |
| `requests` | jebkura | Nāk līdzi NetBox. Nepieciešama CheckMK un Graylog |
| RQ process | — | Tikai plānotajai CheckMK sinhronizācijai un Graylog aptaujai. Bez tā abas joprojām darbojas pēc pieprasījuma, un lapa to pasaka |

---

## 3. Uzstādīšana

### 3.1 Uzstādīt paketi

```bash
source /opt/netbox/venv/bin/activate
pip install git+https://github.com/Gasi-Code/netbox-force.git
```

### 3.2 Pieteikt spraudni

Failā `configuration.py`:

```python
PLUGINS = ['netbox_force']
```

### 3.3 Izpildīt migrācijas

```bash
cd /opt/netbox/netbox
python manage.py migrate netbox_force
python manage.py collectstatic --no-input
```

### 3.4 Pārstartēt NetBox

```bash
sudo systemctl restart netbox netbox-rq
```

### 3.5 Docker

```bash
docker exec -it <konteiners> pip install git+https://github.com/Gasi-Code/netbox-force.git
docker exec -it <konteiners> /opt/netbox/netbox/manage.py migrate netbox_force
docker restart <konteiners>
```

LinuxServer.io attēlā uzstādīšanai **nelietojiet** `custom-cont-init.d` skriptus. Tie
darbojas *pēc* NetBox paša inicializācijas skriptiem, kas var izraisīt migrāciju
neizdošanos. Docker Mods darbojas pirms tiem.

Uzstādīšana konteinera failu sistēmā nepārdzīvo attēla atjaunināšanu. Pievienojiet
spraudni attēla pastāvīgajam spraudņu uzstādīšanas mehānismam, citādi pēc nākamā
pull tā vairs nebūs.

---

## 4. Atjaunināšana

```bash
source /opt/netbox/venv/bin/activate
pip install --force-reinstall --no-cache-dir git+https://github.com/Gasi-Code/netbox-force.git
```

`--force-reinstall --no-cache-dir` ir vajadzīgs, jo pip kešo pēc versijas numura un
citādi izlaistu tās pašas versijas pārbūvi.

**Pārbaudiet pirms pārstartēšanas.** Šis solis ielādē spraudni, neaiztiekot strādājošo
procesu. Ja tas ziņo par kļūdu, nepārstartējiet — strādājošajam NetBox atmiņā vēl ir
vecais kods, un tas turpina darboties:

```bash
cd /opt/netbox/netbox
python manage.py check
```

Pēc tam:

```bash
python manage.py migrate netbox_force
python manage.py collectstatic --no-input
sudo systemctl restart netbox netbox-rq
```

### Atgriešanās pie vecākas versijas

```bash
pip install --force-reinstall --no-cache-dir \
  git+https://github.com/Gasi-Code/netbox-force.git@<commit>
sudo systemctl restart netbox netbox-rq
```

Migrācijas tam parasti nav jāatceļ. Papildu kolonnas vecākam kodam netraucē — tas
vienkārši par tām nezina. Tomēr pirms atjaunināšanas izveidojiet datubāzes kopiju.

---

## 5. Konfigurācijas fails

`PLUGINS_CONFIG` nosaka **tikai sākotnējās vērtības**. Pēc pirmās palaišanas katrs
iestatījums tiek pārvaldīts tīmekļa saskarnē un glabāts datubāzē.

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

| Iestatījums | Noklusējums | Nozīme |
|---|---|---|
| `min_length` | `2` | Mazākais rakstzīmju skaits komentārā |
| `exempt_users` | skat. augstāk | Lietotāji, kas atbrīvoti no visām pārbaudēm, neievērojot burtu reģistru |
| `enforce_on_create` | `False` | Prasīt komentāru arī izveidojot |
| `enforce_on_delete` | `True` | Prasīt komentāru arī dzēšot |
| `extra_exempt_models` | `[]` | Papildu atbrīvotie modeļi, formāts `app.model` |
| `checkmk_secret` | `''` | Nav obligāts. Notur CheckMK noslēpumu pilnībā ārpus datubāzes; tad tam ir priekšroka pār lauku saskarnē |

---

## 6. Lapas

Superlietotāji atrod **NetBox Force** sānu joslā. Visas lapas ir paredzētas tikai
superlietotājiem, ja vien nav norādīts citādi.

| Lapa | Nolūks |
|---|---|
| **Iestatījumi** | Visi piespiešanas noteikumi, izņēmumi, moduļi, webhook, CheckMK |
| **Validācijas noteikumi** | Nosaukumu paraugi un obligātie lauki pēc modeļa un lauka |
| **Modeļu politikas** | Atkāpes no globālajiem iestatījumiem pēc modeļa |
| **Pārkāpumi** | Filtrējams žurnāls par katru bloķēto izmaiņu, eksportējams CSV formātā |
| **Graylog** | Sūtīšana un lasīšana, skat. 7. un 8. nodaļu |
| **Kopsavilkums** | Statistika: kuras funkcijas ir ieslēgtas, bloķētās izmaiņas, biežākie lietotāji, 30 dienu tendence |
| **Importa veidnes** | Lejupielādējamas CSV veidnes NetBox masveida importam. Redzamas visiem pieteiktajiem lietotājiem, kad ieslēgtas |
| **Pamācība** | Brīva teksta lapa saviem lietotājiem. Redzama visiem pieteiktajiem lietotājiem, kad ieslēgta |
| **Ielāpu pārvaldība** | Skat. 9. nodaļu |

Divi iestatījumi pelna atsevišķu pieminējumu:

- **Globālais slēdzis** — aptur visas pārbaudes, piemēram, apkopes loga laikā.
- **Izmēģinājuma režīms (dry-run)** — reģistrē pārkāpumus, neko nebloķējot. Pareizais
  veids, kā ieviest jaunu noteikumu: redz, kas *būtu* bloķēts, pirms kāds patiešām
  tiek apturēts.

---

## 7. Graylog — sūtīšana

Sūta audita notikumus no NetBox uz Graylog, izmantojot GELF.

### Kāpēc

Trīs lietas NetBox nav pierakstītas nekur citur:

- **Neveiksmīgas pieteikšanās.** NetBox tās vispār neuzglabā.
- **Izmaiņas avota IP un lietotāja aģents.** NetBox izmaiņu žurnāls nenes ne vienu,
  ne otru.
- **Izmaiņas paša spraudņa iestatījumos.** Tās neaptver NetBox izmaiņu žurnāls — tas,
  kurš izslēdza piespiešanu, līdz šim neatstāja nekādas pēdas.

### Iestatīšana

Lapā **Graylog**, augšējā puse: resursdators, ports, transports. Pēc tam *Sūtīt testa
notikumu*.

Sāciet ar **UDP**. Ja nekas nepienāk, pārslēdzieties uz **TCP** — UDP pēc būtības
nevar ziņot par kļūmi, TCP var. Tas nošķir “nepareizs ports” no “ziņojums atmests”.

| Transports | Apstiprina piegādi | Šifrēts |
|---|---|---|
| UDP | nē | nē |
| TCP | jā | nē |
| TCP + TLS | jā | jā |
| HTTP | jā | nē |
| HTTPS | jā | jā |

UDP ir pareizs vietējā tīklā un nepareizs caur internetu.

### Kas tiek sūtīts

Viena rinda uz notikuma veidu, katra ar izvēles rūtiņu un syslog nopietnību: objekts
izveidots, mainīts, dzēsts; pieteikšanās; atteikšanās; neveiksmīga pieteikšanās;
bloķēta izmaiņa; mainīti spraudņa iestatījumi.

### Apjoms

Pieprasījums, kas maina vairāk objektu nekā iestatītais slieksnis, tiek ziņots kā
**viens kopsavilkuma notikums**. 500 ierīču imports ir viena darbība — 500 gandrīz
vienādas rindas padara to grūtāk pamanāmu, nevis vieglāk.

Apkopot, nevis ierobežot plūsmu, ir apzināta izvēle. Rinda, kas iztukšojas lēnāk,
nekā piepildās, atmet *jaunākos* notikumus, tātad tieši nepareizo pusi.

### Lauku nosaukumi

Katrs notikums nes tos pašus laukus, tāpēc meklēšana paliek vienkārša:

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

`_request_id` apvieno visu, ko mainījis viens pieprasījums. Četrdesmit vienlaikus
rediģētas ierīces ir viena darbība, nevis četrdesmit mīklas.

### Trīs lietas, ko vērts zināt

- **Graylog atteice nevar ne palēnināt saglabāšanu NetBox, ne likt tai izgāzties.**
  Notikumi nonāk ierobežotā rindā, ko iztukšo fona pavediens. Kad rinda ir pilna,
  jaunie notikumi tiek atmesti un saskaitīti, un skaitītājs redzams lapā.
- **Ziņojuma teksts vienmēr ir angliski**, neatkarīgi no saskarnes valodas. Graylog
  brīdinājumu vaicājumi balstās uz šo tekstu; tulkojums klusi salauztu katru
  brīdinājumu brīdī, kad kāds nomainītu valodu.
- **Klienta IP tiek nolasīts no `X-Forwarded-For`**, ja tas ir. Šo galveni sūta
  klients, un to var viltot, ja NetBox ir sasniedzams bez apgrieztā starpniekservera
  priekšā.

---

## 8. Graylog — lasīšana

Atnes Graylog ziņas uz NetBox, lai resursdatoru varētu novērtēt, neatverot otru cilni.

### Iestatīšana

Lapas **Graylog** apakšējā puse: tīmekļa adrese un API pilnvara, pēc tam *Pārbaudīt
savienojumu*. Rezultāts norāda Graylog versiju, atklāto meklēšanas API veidu,
skaļākos avotus un pieejamās straumes. *Aptaujāt tagad* veic aptauju uzreiz.

**Izdodiet pilnvaru Graylog lietotājam ar tikai lasīšanas lomu.** Tieši tā, nevis šī
spraudņa kods, garantē, ka Graylog nevar mainīt no NetBox.

### Ko šeit precīzi nozīmē “tikai lasīšana”

Katrs izsaukums vai nu iegūst datus, vai lūdz Graylog veikt meklēšanu. Vecākais
meklēšanas galapunkts ir vienkāršs `GET`. Jaunākais Views meklēšanas API nav: tam
nepieciešams `POST`, lai reģistrētu meklēšanu, un vēl viens, lai to izpildītu. Tā
Graylog iekšienē rodas īslaicīgs meklēšanas objekts un atgriežas rezultāti; saglabātie
dati netiek mainīti. Ja jūsu vidē pieņemams ir tikai `GET`, iestatījumos nofiksējiet
meklēšanas veidu uz `legacy`.

### Avotu saskaņošana ar NetBox objektiem

Precīzi, šādā secībā, uzvar pirmais atbilstības gadījums:

| | Noteikums |
|---|---|
| 1 | **Manuāla saistīšana** — reiz iestatīta, vienmēr noteicošā |
| 2 | **IP adrese** — avots pret visām objekta IP adresēm |
| 3 | **Resursdatora nosaukums**, neievērojot burtu reģistru |
| 4 | **Resursdatora nosaukums pēc iestatītas domēna galotnes noņemšanas** |

Viss pārējais paliek nesaistīts un tā arī tiek uzskaitīts.

**Aptuvenas saskaņošanas šeit apzināti nav.** `srv-web-01` un `srv-web-02` atšķiras
par vienu rakstzīmi, tāpēc jebkurš līdzības mērs tos nosauc par 96 % sakritīgiem,
lai gan tās ir divas dažādas mašīnas. Numurētā nosaukumu shēmā — tas ir, jebkurā
NetBox, kas šo vārdu ir pelnījis, — vislīdzīgākais kandidāts sistemātiski izrādās
nepareizais. Žurnāli nonāktu pie kaimiņservera, un neviens to nepamanītu. Līdzība
tiek izmantota tikai, lai **sakārtotu** ieteikumus blakus nesaistītam avotam; pati tā
nekad neko nesaista.

Ja Graylog priekšā ir centrāls syslog pārsūtītājs, visi ziņojumi nes tā adresi, un
2. noteikums neatrod neko noderīgu. Tad avota laukam jānes resursdatora nosaukums, un
tieši tam ir 3. un 4. noteikums.

### Lapas

- **Avoti** — viss, ko Graylog ziņo, ar skaitītājiem, filtrējams pēc saistītiem,
  nesaistītiem, klusiem, nekad neredzētiem un ignorētiem.
- **Klusie** — NetBox saistīti, bet vairs neko nesūta. Miruši, nepareizi konfigurēti
  vai palieka. Neviena no sistēmām to nepamana pati.
- **Nekad nav redzēti Graylog** — otra šķērspārbaudes puse.
- **Klasteris** — mezgli ar zaļu/dzeltenu/sarkanu spuldzīti, indeksētāja stāvoklis,
  žurnāla uzkrājums, katrs mezgls saistīts ar savu NetBox virtuālo mašīnu.
- **Pie objekta** — ierīces un virtuālās mašīnas ar saistītu avotu saņem Graylog
  paneli ar skaitītājiem, jaunākajiem ziņojumiem pēc pieprasījuma un saiti uz Graylog.

### Slodze un drošība

- Viena aptauja ir **viens grupēts vaicājums par visiem resursdatoriem**, nevis
  vaicājums par katru ierīci. Vietne ar 800 ierīcēm izmaksā trīs pieprasījumus.
- Klastera panelis un ziņojumu saraksts ielādējas **pēc** lapas attēlošanas. Lēns vai
  miris Graylog dod tukšu paneli, nekad — iestrēgušu NetBox lapu.
- Saistījums dzīvo spraudņa paša tabulā. **Graylog nekad neraksta NetBox pamatobjektā**
  — spraudņa noņemšana noņem saistījumu un atstāj NetBox neskartu.
- Ziņojumu galapunkts atbild tikai par avotu, kas saistīts ar objektu, kuru
  izsaucējam ir tiesības redzēt.

---

## 9. Ielāpu pārvaldība un CheckMK

Uztur ielāpu stāvokli, operētājsistēmu, atbildīgos un atjauninājumu vēsturi katrai
virtuālajai mašīnai vai fiziskajam serverim.

- **Stāvoklis** zaļš / dzeltens / sarkans, uzturēts ar roku vai lasīts no CheckMK.
- **Nokavējuma slieksnis** — ieraksti bez ielāpa N dienu laikā tiek atzīmēti kā
  nokavēti.
- **Eskalācija** — ieraksts, kas N dienas stāv *dzeltenā*, pats kļūst *sarkans*.
- **Kontakti** — administrators un procesa atbildīgais no NetBox kontaktu objektiem.
- **Atjauninājumu vēsture** — viens ieraksts par katru ielāpu reizi, ar pieteikuma
  numuru un piezīmi.
- **Piekļuve** tiek piešķirta pēc NetBox grupas nosaukuma spraudņa iestatījumos, nevis
  ar Django atļaujām.

### CheckMK

Integrācija ir **pull**: NetBox lasa no CheckMK. CheckMK nekas netiek rakstīts, tāpēc
pietiek ar automatizācijas lietotāju tikai lasīšanai.

Konfigurē iestatījumu lapā: vietnes URL, automatizācijas lietotājs, noslēpums,
pakalpojumu filtrs un sinhronizācijas intervāls. Noslēpums tiek glabāts šifrēts un
vairs netiek rādīts.

Apstājusies sinhronizācija ir kļūme, kas sāp visvairāk, jo lapa turpina rādīt ielāpu
stāvokli, kas klusi vairs nav patiess. Tāpēc kopsavilkums tieši pasaka, kad pēdējā
veiksmīgā sinhronizācija ir vecāka par divkāršu iestatīto intervālu.

---

## 10. Traucējummeklēšana

**Spraudnis neparādās sānu joslā.**
Vai `PLUGINS` ir iestatīts `configuration.py`? Vai migrācijas ir izpildītas? Vai
NetBox ir pārstartēts? Uzraksti sānu joslā atjaunojas tikai pārstartējot; cilnes
spraudņa iekšienē — uzreiz.

**Izmaiņas netiek bloķētas.**
Pārbaudiet šādā secībā: globālo slēdzi, izmēģinājuma režīmu, vai lietotājs nav starp
atbrīvotajiem lietotājiem vai grupām, un vai modeļa politika neizslēdz piespiešanu
šim modelim.

**Lapa ziņo par trūkstošu kolonnu.**
Migrācijas nav izpildītas vai izpildītas tikai daļēji.
`python manage.py migrate netbox_force`.

**“Nedarbojas neviens fona process.”**
`netbox-rq` nedarbojas. CheckMK sinhronizācija un Graylog aptauja tad notiek tikai,
nospiežot pogu.

**Uz Graylog nekas nepienāk.**
Pārslēdziet transportu no UDP uz TCP. UDP nevar ziņot par kļūmi; TCP var, un tā kļūdas
ziņojums pasaka, vai ports ir nepareizs, vai ziņojums tika noraidīts.

**Graylog panelis pie ierīces paliek tukšs.**
Ierīcei nav saistīta avota. Atveriet *Avoti → Nesaistītie* un saistiet to vai
pievienojiet savu domēna galotni iestatījumos, lai FQDN varētu saīsināt.

**Pēc `SECRET_KEY` maiņas CheckMK noslēpums vai Graylog pilnvara vairs nedarbojas.**
Abi ir šifrēti ar atslēgu, kas atvasināta no `SECRET_KEY`. Tie jāievada no jauna.

---

## 11. Valodas maiņa

Valoda ir iestatījums **uz uzstādīšanu**, nevis uz lietotāju. To maina iestatījumu
lapā.

Cilnes un lapas spraudņa iekšienē pārslēdzas uzreiz. Uzraksti sānu joslā tiek
izveidoti vienreiz startējot un mainās tikai pēc NetBox pārstartēšanas.

Ziņojumi, ko lietotāji redz bloķēšanas brīdī, seko šim iestatījumam. API kļūdu
ziņojumi un uz Graylog sūtītie ziņojumi paliek angliski — skat. piezīmi
[dokumentācijas rādītājā](../README.md).

---

## 12. Licence

AGPL-3.0. Skat. [LICENSE](../../LICENSE).
