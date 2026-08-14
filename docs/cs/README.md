# NetBox Force — Příručka (čeština)

[← Všechny jazyky](../README.md) · [README projektu](../../README.md) · [Seznam změn](../../CHANGELOG.md)

---

## 1. Co plugin dělá

NetBox zaznamenává, *co* se změnilo. NetBox Force rozhoduje, *zda je změna vůbec
přípustná*, a může předem vyžádat zdůvodnění.

Stojí mezi každou operací uložení či smazání a databází. Než se změna zapíše, umí
ověřit:

- zda byl uveden komentář do žurnálu a zda je dost dlouhý
- zda komentář netvoří jen prázdná slova
- zda komentář uvádí číslo tiketu
- zda změna probíhá ve schváleném časovém okně
- zda hodnoty polí odpovídají jmennému vzoru
- zda jsou povinná pole skutečně vyplněna

Doprovázejí jej další dva moduly:

- **Správa záplat** — stav záplatování, operační systém, odpovědné osoby a
  historie aktualizací pro každý virtuální stroj či fyzický server, volitelně
  plněné z CheckMK.
- **Graylog** — posílá auditní události ven a přináší informace z logů zpět k
  objektu, ke kterému patří.

Vše je volitelné. Po instalaci je aktivní pouze kontrola přítomnosti komentáře, s
minimem dvou znaků. Zbytek se zapíná ve webovém rozhraní.

---

## 2. Požadavky

| Součást | Verze | Poznámka |
|---|---|---|
| NetBox | 4.0.0 nebo novější | |
| Python | 3.10 nebo novější | |
| PostgreSQL | — | Vyžaduje sám NetBox |
| `cryptography` | libovolná | Součást NetBoxu. Bez něj se tajemství CheckMK a token Graylogu ukládají nešifrovaně a plugin to na stránce nastavení uvádí |
| `requests` | libovolná | Součást NetBoxu. Potřeba pro CheckMK a Graylog |
| Proces RQ | — | Jen pro plánovanou synchronizaci CheckMK a dotazování Graylogu. Bez něj obojí stále běží na vyžádání a stránka to uvádí |

---

## 3. Instalace

### 3.1 Instalace balíčku

```bash
source /opt/netbox/venv/bin/activate
pip install git+https://github.com/Gasi-Code/netbox-force.git
```

### 3.2 Zaregistrování pluginu

V `configuration.py`:

```python
PLUGINS = ['netbox_force']
```

### 3.3 Spuštění migrací

```bash
cd /opt/netbox/netbox
python manage.py migrate netbox_force
python manage.py collectstatic --no-input
```

### 3.4 Restart NetBoxu

```bash
sudo systemctl restart netbox netbox-rq
```

### 3.5 Docker

```bash
docker exec -it <kontejner> pip install git+https://github.com/Gasi-Code/netbox-force.git
docker exec -it <kontejner> /opt/netbox/netbox/manage.py migrate netbox_force
docker restart <kontejner>
```

U obrazu LinuxServer.io **nepoužívejte** k instalaci skripty `custom-cont-init.d`.
Běží *po* vlastních inicializačních skriptech NetBoxu, což může způsobit selhání
migrací. Docker Mods běží před nimi.

Instalace provedená v souborovém systému kontejneru nepřežije aktualizaci obrazu.
Přidejte plugin do trvalého instalačního mechanismu obrazu, jinak po dalším pullu
zmizí.

---

## 4. Aktualizace

```bash
source /opt/netbox/venv/bin/activate
pip install --force-reinstall --no-cache-dir git+https://github.com/Gasi-Code/netbox-force.git
```

`--force-reinstall --no-cache-dir` je nutné, protože pip ukládá do mezipaměti podle
čísla verze a jinak by přeskočil přestavbu téže verze.

**Před restartem ověřte.** Tento krok načte plugin, aniž by se dotkl běžícího
procesu. Pokud ohlásí chybu, nerestartujte — běžící NetBox má v paměti stále starý
kód a pracuje dál:

```bash
cd /opt/netbox/netbox
python manage.py check
```

Poté:

```bash
python manage.py migrate netbox_force
python manage.py collectstatic --no-input
sudo systemctl restart netbox netbox-rq
```

### Návrat zpět

```bash
pip install --force-reinstall --no-cache-dir \
  git+https://github.com/Gasi-Code/netbox-force.git@<commit>
sudo systemctl restart netbox netbox-rq
```

Migrace kvůli tomu obvykle vracet netřeba. Sloupce navíc staršímu kódu nevadí —
prostě o nich neví. Přesto si před aktualizací pořiďte zálohu databáze.

---

## 5. Konfigurační soubor

`PLUGINS_CONFIG` určuje **pouze počáteční hodnoty**. Po prvním spuštění se každé
nastavení spravuje ve webovém rozhraní a ukládá do databáze.

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

| Nastavení | Výchozí | Význam |
|---|---|---|
| `min_length` | `2` | Minimální počet znaků v komentáři |
| `exempt_users` | viz výše | Uživatelé vyňatí ze všech kontrol, bez ohledu na velikost písmen |
| `enforce_on_create` | `False` | Vyžadovat komentář i při vytváření |
| `enforce_on_delete` | `True` | Vyžadovat komentář i při mazání |
| `extra_exempt_models` | `[]` | Další vyňaté modely, formát `app.model` |
| `checkmk_secret` | `''` | Volitelné. Udrží tajemství CheckMK zcela mimo databázi; má pak přednost před polem v rozhraní |

---

## 6. Stránky

Superuživatelé najdou **NetBox Force** v postranním panelu. Všechny stránky jsou
vyhrazeny superuživatelům, pokud není uvedeno jinak.

| Stránka | Účel |
|---|---|
| **Nastavení** | Všechna pravidla vynucování, výjimky, moduly, webhook, CheckMK |
| **Validační pravidla** | Jmenné vzory a povinná pole, podle modelu a pole |
| **Zásady modelů** | Odchylky od globálních nastavení, podle modelu |
| **Porušení** | Filtrovatelný záznam každé zablokované změny, exportovatelný do CSV |
| **Graylog** | Odesílání a čtení, viz oddíly 7 a 8 |
| **Přehled** | Statistiky: které funkce běží, zablokované změny, nejčastější uživatelé, trend za 30 dní |
| **Importní šablony** | Stažitelné CSV šablony pro hromadný import NetBoxu. Viditelné všem přihlášeným uživatelům, je-li zapnuto |
| **Návod** | Volná textová stránka pro vlastní uživatele. Viditelná všem přihlášeným uživatelům, je-li zapnuta |
| **Správa záplat** | Viz oddíl 9 |

Dvě nastavení si zaslouží zvláštní zmínku:

- **Globální vypínač** — pozastaví všechny kontroly, například během servisního
  okna.
- **Zkušební režim (dry-run)** — porušení zaznamenává, ale nic neblokuje. Správný
  způsob, jak zavést nové pravidlo: je vidět, co by *bylo* zablokováno, dřív než se
  někdo skutečně zastaví.

---

## 7. Graylog — odesílání

Posílá auditní události z NetBoxu do Graylogu přes GELF.

### K čemu

Tři věci nejsou v NetBoxu zaznamenány nikde jinde:

- **Neúspěšná přihlášení.** NetBox je vůbec neuchovává.
- **Zdrojová IP a user agent** změny. Záznam změn NetBoxu nenese ani jedno.
- **Změny nastavení samotného pluginu.** Nespadají do záznamu změn NetBoxu — kdo
  vypnul vynucování, dosud nezanechal žádnou stopu.

### Nastavení

Na stránce **Graylog**, horní polovina: host, port, přenos. Poté *Odeslat testovací
událost*.

Začněte s **UDP**. Pokud nic nedorazí, přepněte na **TCP** — UDP z podstaty nemůže
selhání ohlásit, TCP ano. To rozliší „špatný port" od „zpráva zahozena".

| Přenos | Potvrzuje doručení | Šifrovaný |
|---|---|---|
| UDP | ne | ne |
| TCP | ano | ne |
| TCP + TLS | ano | ano |
| HTTP | ano | ne |
| HTTPS | ano | ano |

UDP je správné uvnitř místní sítě a špatné přes internet.

### Co se odesílá

Jeden řádek na typ události, každý se zaškrtávacím políčkem a závažností podle
syslogu: objekt vytvořen, změněn, smazán; přihlášení; odhlášení; neúspěšné
přihlášení; zablokovaná změna; změněno nastavení pluginu.

### Objem

Požadavek, který změní více objektů než nastavená mez, se ohlásí jako **jediná
souhrnná událost**. Import 500 zařízení je jedna operace — 500 téměř shodných řádků
ji činí hůře viditelnou, ne lépe.

Shrnovat místo škrcení je záměrná volba. Fronta, která se vyprazdňuje pomaleji, než
se plní, zahazuje *nejnovější* události, tedy právě tu špatnou polovinu.

### Názvy polí

Každá událost nese stejná pole, aby hledání zůstalo jednoduché:

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

`_request_id` seskupuje vše, co jeden požadavek změnil. Čtyřicet naráz upravených
zařízení je jedna operace, ne čtyřicet hádanek.

### Tři věci, které je dobré vědět

- **Výpadek Graylogu nemůže uložení v NetBoxu zpomalit ani nechat selhat.**
  Události jdou do omezené fronty, kterou vyprazdňuje vlákno na pozadí. Je-li fronta
  plná, nové události se zahazují a počítají, a čítač je vidět na stránce.
- **Text zprávy je vždy anglicky**, ať je jazyk rozhraní jakýkoli. Výstražné dotazy
  v Graylogu na tomto textu stojí; překlad by tiše rozbil každou výstrahu ve chvíli,
  kdy by někdo změnil jazyk.
- **IP klienta se čte z `X-Forwarded-For`**, je-li přítomna. Tuto hlavičku posílá
  klient a lze ji zfalšovat, je-li NetBox dostupný bez reverzní proxy před ním.

---

## 8. Graylog — čtení

Přináší informace z Graylogu do NetBoxu, aby bylo možné posoudit hostitele bez
otevírání druhé karty.

### Nastavení

Dolní polovina stránky **Graylog**: webová adresa a API token, poté *Otestovat
spojení*. Výsledek uvádí verzi Graylogu, rozpoznanou podobu vyhledávacího API,
nejhlučnější zdroje a dostupné streamy. *Dotázat se nyní* provede dotázání ihned.

**Token vydejte pro uživatele Graylogu s rolí jen pro čtení.** Právě to, a nikoli
kód tohoto pluginu, zaručuje, že Graylog nelze z NetBoxu měnit.

### Co zde přesně znamená „pouze pro čtení"

Každé volání buď získává data, nebo žádá Graylog o provedení hledání. Starší
vyhledávací endpoint je prosté `GET`. Novější vyhledávací API Views nikoli:
vyžaduje `POST` pro zaregistrování hledání a další pro jeho provedení. Tím vzniká
uvnitř Graylogu krátkodobý vyhledávací objekt a vracejí se výsledky; uložená data se
nemění. Je-li ve vašem prostředí přijatelné pouze `GET`, nastavte v nastavení
podobu vyhledávání napevno na `legacy`.

### Párování zdrojů s objekty NetBoxu

Přesně, v tomto pořadí, vyhrává první shoda:

| | Pravidlo |
|---|---|
| 1 | **Ruční přiřazení** — jednou nastavené vždy platí |
| 2 | **IP adresa** — zdroj proti všem IP objektu |
| 3 | **Název hostitele**, bez ohledu na velikost písmen |
| 4 | **Název hostitele po odebrání nastavené doménové přípony** |

Vše ostatní zůstane nepřiřazeno a je tak i vypsáno.

**Přibližné párování zde záměrně není.** `srv-web-01` a `srv-web-02` se liší o jeden
znak, takže jakákoli míra podobnosti je označí za shodné na 96 %, ačkoli jde o dva
různé stroje. U číslovaného jmenného schématu — tedy v každém NetBoxu, který si to
jméno zaslouží — je nejpodobnější kandidát systematicky ten nesprávný. Logy by se
zařadily pod sousední server a nikdo by si toho nevšiml. Podobnost slouží pouze k
**seřazení** návrhů vedle nepřiřazeného zdroje; sama nikdy nic nepřiřadí.

Stojí-li před Graylogem centrální syslogový přeposílač, nesou všechny zprávy jeho
adresu a pravidlo 2 nenajde nic užitečného. Pole zdroje pak musí nést název
hostitele, k čemuž slouží pravidla 3 a 4.

### Stránky

- **Zdroje** — vše, co Graylog hlásí, s čítači, filtrovatelné podle přiřazených,
  nepřiřazených, tichých, nikdy neviděných a ignorovaných.
- **Tiché** — v NetBoxu přiřazené, ale už nic neposílají. Mrtvé, špatně
  nakonfigurované nebo pozůstatek. Ani jeden ze systémů to sám nepozná.
- **Nikdy neviděné v Graylogu** — druhá polovina křížové kontroly.
- **Cluster** — uzly se zelenou/žlutou/červenou kontrolkou, stav indexeru,
  nevyřízený žurnál, každý uzel propojený se svým virtuálním strojem v NetBoxu.
- **U objektu** — zařízení a virtuální stroje s přiřazeným zdrojem dostanou panel
  Graylogu s čítači, posledními zprávami na vyžádání a odkazem do Graylogu.

### Zátěž a bezpečnost

- Jedno dotázání je **jediný seskupený dotaz na všechny hostitele**, ne dotaz na
  každé zařízení. Lokalita s 800 zařízeními stojí tři požadavky.
- Panel clusteru a seznam zpráv se načítají **až po** vykreslení stránky. Pomalý
  nebo mrtvý Graylog dá prázdný panel, nikdy zaseknutou stránku NetBoxu.
- Přiřazení žije ve vlastní tabulce pluginu. **Graylog nikdy nezapisuje do
  jádrového objektu NetBoxu** — odstranění pluginu odstraní přiřazení a NetBox
  zůstane nedotčen.
- Endpoint zpráv odpovídá pouze pro zdroj přiřazený k objektu, který volající smí
  vidět.

---

## 9. Správa záplat a CheckMK

Vede stav záplatování, operační systém, odpovědné osoby a historii aktualizací pro
každý virtuální stroj či fyzický server.

- **Stav** zelená / žlutá / červená, buď vedený ručně, nebo čtený z CheckMK.
- **Práh prodlení** — položky bez záplaty po N dnech se označí jako opožděné.
- **Eskalace** — položka, která zůstane N dnů na *žluté*, se sama změní na
  *červenou*.
- **Kontakty** — administrátor a garant procesu z kontaktních objektů NetBoxu.
- **Historie aktualizací** — jeden záznam na každý průchod záplatování, s číslem
  tiketu a poznámkou.
- **Přístup** se uděluje podle názvu skupiny v NetBoxu v nastavení pluginu, nikoli
  přes oprávnění Djanga.

### CheckMK

Napojení je **pull**: NetBox čte z CheckMK. Do CheckMK se nic nezapisuje, takže
stačí automatizační uživatel pouze pro čtení.

Nastavuje se na stránce nastavení: URL webu, automatizační uživatel, tajemství,
filtr služeb a interval synchronizace. Tajemství se ukládá zašifrované a už se nikdy
nezobrazí.

Zaseknutá synchronizace je porucha, která bolí nejvíc, protože stránka dál ukazuje
stav záplatování, který tiše přestal platit. Přehled proto výslovně uvádí, když je
poslední úspěšná synchronizace starší než dvojnásobek nastaveného intervalu.

---

## 10. Řešení potíží

**Plugin se neobjevuje v postranním panelu.**
Je `PLUGINS` v `configuration.py`? Proběhly migrace? Byl NetBox restartován? Popisky
v postranním panelu se aktualizují až při restartu; karty uvnitř pluginu ihned.

**Změny se neblokují.**
Ověřte v tomto pořadí: globální vypínač, zkušební režim, zda uživatel není mezi
vyňatými uživateli či skupinami, a zda zásada modelu nevypíná vynucování pro daný
model.

**Stránka hlásí chybějící sloupec.**
Migrace neproběhly, nebo jen zčásti. `python manage.py migrate netbox_force`.

**„Neběží žádný proces na pozadí."**
`netbox-rq` neběží. Synchronizace CheckMK a dotazování Graylogu pak proběhnou jen
po stisku tlačítka.

**Do Graylogu nic nedorazí.**
Přepněte přenos z UDP na TCP. UDP nemůže selhání ohlásit; TCP ano a jeho chybové
hlášení řekne, zda je špatný port, nebo byla zpráva odmítnuta.

**Panel Graylogu u zařízení zůstává prázdný.**
Zařízení nemá přiřazený zdroj. Otevřete *Zdroje → Nepřiřazené* a přiřaďte jej, nebo
doplňte v nastavení vlastní doménovou příponu, aby bylo možné FQDN zkrátit.

**Po změně `SECRET_KEY` přestane fungovat tajemství CheckMK nebo token Graylogu.**
Obojí je šifrováno klíčem odvozeným ze `SECRET_KEY`. Je nutné je zadat znovu.

---

## 11. Změna jazyka

Jazyk je nastavení **na instalaci**, nikoli na uživatele. Mění se na stránce
nastavení.

Karty a stránky uvnitř pluginu se přepnou okamžitě. Popisky v postranním panelu se
sestavují jednou při startu a změní se až po restartu NetBoxu.

Zprávy zobrazované uživatelům při zablokování se řídí tímto nastavením. Chybová
hlášení API a zprávy posílané do Graylogu zůstávají anglicky — viz poznámku v
[rozcestníku dokumentace](../README.md).

---

## 12. Licence

AGPL-3.0. Viz [LICENSE](../../LICENSE).
