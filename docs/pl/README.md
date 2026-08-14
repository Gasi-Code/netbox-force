# NetBox Force — Przewodnik (polski)

[← Wszystkie języki](../README.md) · [README projektu](../../README.md) · [Historia zmian](../../CHANGELOG.md)

---

## 1. Co robi wtyczka

NetBox zapisuje, *co* się zmieniło. NetBox Force rozstrzyga, *czy zmiana jest w
ogóle dopuszczalna*, i może wcześniej zażądać uzasadnienia.

Stoi pomiędzy każdą operacją zapisu lub usunięcia a bazą danych. Zanim zmiana
zostanie zapisana, potrafi sprawdzić:

- czy podano komentarz do dziennika i czy jest dostatecznie długi
- czy komentarz nie składa się wyłącznie z pustych słów
- czy komentarz przywołuje numer zgłoszenia
- czy zmiana zachodzi w zatwierdzonym oknie czasowym
- czy wartości pól odpowiadają wzorcowi nazewnictwa
- czy pola wymagane są faktycznie wypełnione

Towarzyszą jej dwa dalsze moduły:

- **Zarządzanie poprawkami** — stan poprawek, system operacyjny, osoby
  odpowiedzialne i historia aktualizacji dla każdej maszyny wirtualnej lub serwera
  fizycznego, opcjonalnie zasilane z CheckMK.
- **Graylog** — wysyła zdarzenia audytu na zewnątrz i sprowadza informacje z logów
  z powrotem obok obiektu, do którego należą.

Wszystko jest opcjonalne. Po instalacji działa wyłącznie kontrola obecności
komentarza, z minimum dwóch znaków. Reszta włączana jest w interfejsie webowym.

---

## 2. Wymagania

| Składnik | Wersja | Uwagi |
|---|---|---|
| NetBox | 4.0.0 lub nowszy | |
| Python | 3.10 lub nowszy | |
| PostgreSQL | — | Wymagany przez sam NetBox |
| `cryptography` | dowolna | Dostarczana z NetBoksem. Bez niej sekret CheckMK i token Grayloga zapisywane są bez szyfrowania, a wtyczka mówi o tym na stronie ustawień |
| `requests` | dowolna | Dostarczana z NetBoksem. Potrzebna do CheckMK i Grayloga |
| Proces RQ | — | Tylko do zaplanowanej synchronizacji CheckMK i odpytywania Grayloga. Bez niego obie nadal działają na żądanie, a strona to sygnalizuje |

---

## 3. Instalacja

### 3.1 Instalacja pakietu

```bash
source /opt/netbox/venv/bin/activate
pip install git+https://github.com/Gasi-Code/netbox-force.git
```

### 3.2 Zgłoszenie wtyczki

W `configuration.py`:

```python
PLUGINS = ['netbox_force']
```

### 3.3 Uruchomienie migracji

```bash
cd /opt/netbox/netbox
python manage.py migrate netbox_force
python manage.py collectstatic --no-input
```

### 3.4 Restart NetBoksa

```bash
sudo systemctl restart netbox netbox-rq
```

### 3.5 Docker

```bash
docker exec -it <kontener> pip install git+https://github.com/Gasi-Code/netbox-force.git
docker exec -it <kontener> /opt/netbox/netbox/manage.py migrate netbox_force
docker restart <kontener>
```

W obrazie LinuxServer.io **nie** używaj do instalacji skryptów
`custom-cont-init.d`. Uruchamiają się *po* własnych skryptach startowych NetBoksa,
co może spowodować niepowodzenie migracji. Docker Mods uruchamiają się przed nimi.

Instalacja wykonana w systemie plików kontenera nie przetrwa aktualizacji obrazu.
Dodaj wtyczkę do trwałego mechanizmu instalacji wtyczek obrazu, inaczej zniknie po
następnym pullu.

---

## 4. Aktualizacja

```bash
source /opt/netbox/venv/bin/activate
pip install --force-reinstall --no-cache-dir git+https://github.com/Gasi-Code/netbox-force.git
```

`--force-reinstall --no-cache-dir` jest potrzebne, ponieważ pip buforuje według
numeru wersji i w przeciwnym razie pominąłby przebudowę tej samej wersji.

**Sprawdź przed restartem.** Ten krok wczytuje wtyczkę, nie dotykając działającego
procesu. Jeśli zgłosi błąd, nie restartuj — działający NetBox ma w pamięci wciąż
stary kod i pracuje dalej:

```bash
cd /opt/netbox/netbox
python manage.py check
```

Następnie:

```bash
python manage.py migrate netbox_force
python manage.py collectstatic --no-input
sudo systemctl restart netbox netbox-rq
```

### Powrót do starszej wersji

```bash
pip install --force-reinstall --no-cache-dir \
  git+https://github.com/Gasi-Code/netbox-force.git@<commit>
sudo systemctl restart netbox netbox-rq
```

Migracji zwykle nie trzeba w tym celu cofać. Dodatkowe kolumny nie przeszkadzają
starszemu kodowi — po prostu ich nie zna. Mimo to przed aktualizacją wykonaj zrzut
bazy.

---

## 5. Plik konfiguracyjny

`PLUGINS_CONFIG` ustala **wyłącznie wartości początkowe**. Po pierwszym starcie
każde ustawienie zarządzane jest w interfejsie webowym i przechowywane w bazie.

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

| Ustawienie | Domyślnie | Znaczenie |
|---|---|---|
| `min_length` | `2` | Minimalna liczba znaków w komentarzu |
| `exempt_users` | patrz wyżej | Użytkownicy zwolnieni ze wszystkich kontroli, bez rozróżniania wielkości liter |
| `enforce_on_create` | `False` | Wymagać komentarza także przy tworzeniu |
| `enforce_on_delete` | `True` | Wymagać komentarza także przy usuwaniu |
| `extra_exempt_models` | `[]` | Dalsze zwolnione modele, format `app.model` |
| `checkmk_secret` | `''` | Opcjonalne. Trzyma sekret CheckMK całkowicie poza bazą; ma wtedy pierwszeństwo przed polem w interfejsie |

---

## 6. Strony

Superużytkownicy znajdą **NetBox Force** w panelu bocznym. Wszystkie strony są
zastrzeżone dla superużytkowników, o ile nie zaznaczono inaczej.

| Strona | Przeznaczenie |
|---|---|
| **Ustawienia** | Wszystkie reguły wymuszania, zwolnienia, moduły, webhook, CheckMK |
| **Reguły walidacji** | Wzorce nazw i pola wymagane, według modelu i pola |
| **Zasady modeli** | Odstępstwa od ustawień globalnych, według modelu |
| **Naruszenia** | Filtrowalny dziennik każdej zablokowanej zmiany, eksportowalny do CSV |
| **Graylog** | Wysyłanie i odczyt, patrz rozdziały 7 i 8 |
| **Pulpit** | Statystyki: które funkcje działają, zablokowane zmiany, najczęstsi użytkownicy, przebieg 30-dniowy |
| **Szablony importu** | Szablony CSV do pobrania dla importu masowego NetBoksa. Widoczne dla wszystkich zalogowanych użytkowników, gdy włączone |
| **Instrukcja** | Strona z dowolnym tekstem dla własnych użytkowników. Widoczna dla wszystkich zalogowanych użytkowników, gdy włączona |
| **Zarządzanie poprawkami** | Patrz rozdział 9 |

Dwa ustawienia zasługują na osobną wzmiankę:

- **Wyłącznik globalny** — wstrzymuje wszystkie kontrole, na przykład podczas okna
  serwisowego.
- **Tryb próbny (dry-run)** — rejestruje naruszenia, niczego nie blokując. Właściwy
  sposób wprowadzenia nowej reguły: widać, co *zostałoby* zablokowane, zanim ktoś
  naprawdę zostanie zatrzymany.

---

## 7. Graylog — wysyłanie

Wysyła zdarzenia audytu z NetBoksa do Grayloga przez GELF.

### Po co

Trzech rzeczy nie ma nigdzie indziej w NetBoksie:

- **Nieudane logowania.** NetBox w ogóle ich nie przechowuje.
- **Adres IP źródła i user agent** zmiany. Dziennik zmian NetBoksa nie niesie
  żadnego z nich.
- **Zmiany ustawień samej wtyczki.** Nie obejmuje ich dziennik zmian NetBoksa — kto
  wyłączył wymuszanie, dotąd nie zostawiał żadnego śladu.

### Konfiguracja

Na stronie **Graylog**, górna połowa: host, port, transport. Następnie *Wyślij
zdarzenie testowe*.

Zacznij od **UDP**. Jeśli nic nie dotrze, przełącz na **TCP** — UDP z natury nie
umie zgłosić awarii, TCP umie. To odróżnia „zły port" od „wiadomość odrzucona".

| Transport | Potwierdza dostarczenie | Szyfrowany |
|---|---|---|
| UDP | nie | nie |
| TCP | tak | nie |
| TCP + TLS | tak | tak |
| HTTP | tak | nie |
| HTTPS | tak | tak |

UDP jest właściwe w sieci lokalnej i niewłaściwe przez internet.

### Co jest wysyłane

Jeden wiersz na typ zdarzenia, każdy z polem wyboru i wagą według sysloga: obiekt
utworzony, zmieniony, usunięty; logowanie; wylogowanie; nieudane logowanie;
zablokowana zmiana; zmienione ustawienia wtyczki.

### Ilość

Żądanie zmieniające więcej obiektów niż ustawiony próg zgłaszane jest jako **jedno
zdarzenie zbiorcze**. Import 500 urządzeń to jedna operacja — 500 niemal
identycznych wierszy utrudnia jej dostrzeżenie, a nie ułatwia.

Zbieranie w podsumowanie zamiast dławienia jest wyborem świadomym. Kolejka, która
opróżnia się wolniej, niż napełnia, odrzuca *najnowsze* zdarzenia, czyli akurat złą
połowę.

### Nazwy pól

Każde zdarzenie niesie te same pola, dzięki czemu wyszukiwanie pozostaje proste:

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

`_request_id` grupuje wszystko, co zmieniło jedno żądanie. Czterdzieści urządzeń
zmienionych naraz to jedna operacja, a nie czterdzieści zagadek.

### Trzy rzeczy, które warto wiedzieć

- **Awaria Grayloga nie może spowolnić ani przerwać zapisu w NetBoksie.** Zdarzenia
  trafiają do ograniczonej kolejki opróżnianej przez wątek w tle. Gdy kolejka jest
  pełna, nowe zdarzenia są odrzucane i liczone, a licznik pokazuje się na stronie.
- **Tekst komunikatu jest zawsze po angielsku**, niezależnie od języka interfejsu.
  Zapytania alarmowe Grayloga opierają się na tym tekście; tłumaczenie po cichu
  zepsułoby każdy alarm w chwili zmiany języka.
- **Adres IP klienta odczytywany jest z `X-Forwarded-For`**, jeśli jest obecny. Ten
  nagłówek pochodzi od klienta i można go sfałszować, gdy NetBox jest dostępny bez
  odwrotnego proxy przed nim.

---

## 8. Graylog — odczyt

Sprowadza informacje z Grayloga do NetBoksa, aby ocenić hosta bez otwierania drugiej
karty.

### Konfiguracja

Dolna połowa strony **Graylog**: adres webowy i token API, następnie *Testuj
połączenie*. Wynik podaje wersję Grayloga, wykrytą postać API wyszukiwania,
najgłośniejsze źródła i dostępne strumienie. *Odpytaj teraz* wykonuje odpytanie
natychmiast.

**Token wydaj dla użytkownika Grayloga z rolą tylko do odczytu.** To ona, a nie kod
tej wtyczki, gwarantuje, że Grayloga nie da się zmienić z poziomu NetBoksa.

### Co dokładnie znaczy tu „tylko do odczytu"

Każde wywołanie albo pobiera dane, albo prosi Grayloga o wykonanie wyszukiwania.
Starszy punkt wyszukiwania to zwykłe `GET`. Nowsze API wyszukiwania Views już nie:
wymaga `POST` do zarejestrowania wyszukiwania i kolejnego do jego wykonania. Powstaje
przy tym w Graylogu krótkotrwały obiekt wyszukiwania i wracają wyniki; zapisane dane
nie są zmieniane. Jeśli w Państwa środowisku dopuszczalne jest wyłącznie `GET`,
ustaw w ustawieniach postać wyszukiwania na sztywno na `legacy`.

### Dopasowywanie źródeł do obiektów NetBoksa

Dokładnie, w tej kolejności, wygrywa pierwsze trafienie:

| | Reguła |
|---|---|
| 1 | **Przypisanie ręczne** — raz ustawione, zawsze ma pierwszeństwo |
| 2 | **Adres IP** — źródło wobec wszystkich adresów IP obiektu |
| 3 | **Nazwa hosta**, bez rozróżniania wielkości liter |
| 4 | **Nazwa hosta po odjęciu skonfigurowanego przyrostka domeny** |

Wszystko inne pozostaje nieprzypisane i tak też jest wykazywane.

**Świadomie nie ma dopasowania przybliżonego.** `srv-web-01` i `srv-web-02` różnią
się jednym znakiem, więc każda miara podobieństwa nazywa je zgodnymi w 96 %, choć są
to dwie różne maszyny. W numerowanym schemacie nazw — czyli w każdym NetBoksie
zasługującym na tę nazwę — najbardziej podobny kandydat jest systematycznie tym
niewłaściwym. Logi trafiałyby pod sąsiedni serwer i nikt by tego nie zauważył.
Podobieństwo służy wyłącznie do **sortowania** propozycji obok nieprzypisanego
źródła; samo nigdy niczego nie przypisuje.

Jeśli przed Graylogiem stoi centralny przekaźnik syslog, wszystkie komunikaty niosą
jego adres, a reguła 2 nie trafia w nic użytecznego. Pole źródła musi wtedy nieść
nazwę hosta, i po to są reguły 3 i 4.

### Strony

- **Źródła** — wszystko, co Graylog zgłasza, z licznikami, filtrowalne według
  przypisanych, nieprzypisanych, cichych, nigdy niewidzianych i ignorowanych.
- **Ciche** — przypisane w NetBoksie, ale nic już nie wysyłają. Martwe, źle
  skonfigurowane albo pozostałość. Żaden z systemów nie wykryje tego sam.
- **Nigdy niewidziane w Graylogu** — druga połowa kontroli krzyżowej.
- **Klaster** — węzły z kontrolką zieloną/żółtą/czerwoną, stan indeksera, zaległości
  dziennika, każdy węzeł powiązany ze swoją maszyną wirtualną w NetBoksie.
- **Przy obiekcie** — urządzenia i maszyny wirtualne z przypisanym źródłem
  otrzymują panel Grayloga z licznikami, ostatnimi komunikatami na żądanie i
  odnośnikiem do Grayloga.

### Obciążenie i bezpieczeństwo

- Jedno odpytanie to **jedno zgrupowane zapytanie o wszystkie hosty**, a nie
  zapytanie na każde urządzenie. Lokalizacja z 800 urządzeniami kosztuje trzy żądania.
- Panel klastra i lista komunikatów ładują się **po** wyrenderowaniu strony. Wolny
  albo martwy Graylog daje pusty panel, nigdy zawieszoną stronę NetBoksa.
- Przypisanie żyje we własnej tabeli wtyczki. **Graylog nigdy nie zapisuje do
  obiektu rdzenia NetBoksa** — usunięcie wtyczki usuwa przypisanie i pozostawia
  NetBoksa nietkniętego.
- Punkt komunikatów odpowiada wyłącznie dla źródła przypisanego do obiektu, który
  wywołujący ma prawo oglądać.

---

## 9. Zarządzanie poprawkami i CheckMK

Prowadzi stan poprawek, system operacyjny, osoby odpowiedzialne i historię
aktualizacji dla każdej maszyny wirtualnej lub serwera fizycznego.

- **Stan** zielony / żółty / czerwony, prowadzony ręcznie albo czytany z CheckMK.
- **Próg zaległości** — wpisy bez poprawki w ciągu N dni oznaczane są jako zaległe.
- **Eskalacja** — wpis pozostający N dni na *żółtym* sam przechodzi na *czerwony*.
- **Kontakty** — administrator i opiekun procesu z obiektów kontaktów NetBoksa.
- **Historia aktualizacji** — jeden wpis na przebieg poprawek, z numerem zgłoszenia
  i notatką.
- **Dostęp** przyznaje się po nazwie grupy NetBoksa w ustawieniach wtyczki, a nie
  przez uprawnienia Django.

### CheckMK

Integracja to **pull**: NetBox czyta z CheckMK. Do CheckMK nic nie jest zapisywane,
więc wystarczy użytkownik automatyzacji z prawem tylko do odczytu.

Konfigurowane na stronie ustawień: URL witryny, użytkownik automatyzacji, sekret,
filtr usług i interwał synchronizacji. Sekret przechowywany jest zaszyfrowany i nie
jest już nigdy pokazywany.

Zatrzymana synchronizacja to awaria boląca najbardziej, bo strona dalej pokazuje
stan poprawek, który po cichu przestał być prawdziwy. Pulpit mówi więc wprost, gdy
ostatnia udana synchronizacja jest starsza niż dwukrotność ustawionego interwału.

---

## 10. Rozwiązywanie problemów

**Wtyczka nie pojawia się w panelu bocznym.**
Czy `PLUGINS` jest ustawione w `configuration.py`? Czy migracje zostały wykonane?
Czy NetBox zrestartowano? Etykiety w panelu bocznym odświeżają się dopiero przy
restarcie; karty wewnątrz wtyczki natychmiast.

**Zmiany nie są blokowane.**
Sprawdź w tej kolejności: wyłącznik globalny, tryb próbny, czy użytkownik nie jest
wśród zwolnionych użytkowników lub grup, i czy zasada modelu nie wyłącza wymuszania
dla tego modelu.

**Strona zgłasza brakującą kolumnę.**
Migracje nie zostały wykonane albo tylko częściowo.
`python manage.py migrate netbox_force`.

**„Nie działa żaden proces w tle."**
`netbox-rq` nie działa. Synchronizacja CheckMK i odpytywanie Grayloga wykonują się
wtedy tylko po naciśnięciu przycisku.

**Do Grayloga nic nie dociera.**
Przełącz transport z UDP na TCP. UDP nie umie zgłosić awarii; TCP umie, a jego
komunikat błędu mówi, czy port jest zły, czy komunikat został odrzucony.

**Panel Grayloga przy urządzeniu pozostaje pusty.**
Urządzenie nie ma przypisanego źródła. Otwórz *Źródła → Nieprzypisane* i przypisz je
albo dodaj swój przyrostek domeny w ustawieniach, aby FQDN mógł zostać skrócony.

**Po zmianie `SECRET_KEY` sekret CheckMK albo token Grayloga przestał działać.**
Oba są zaszyfrowane kluczem wyprowadzonym z `SECRET_KEY`. Trzeba je wprowadzić
ponownie.

---

## 11. Zmiana języka

Język jest ustawieniem **na instalację**, nie na użytkownika. Zmienia się go na
stronie ustawień.

Karty i strony wewnątrz wtyczki przełączają się natychmiast. Etykiety w panelu
bocznym budowane są raz przy starcie i zmieniają się dopiero po restarcie NetBoksa.

Komunikaty pokazywane użytkownikom przy blokadzie idą za tym ustawieniem.
Komunikaty błędów API oraz komunikaty wysyłane do Grayloga pozostają po angielsku —
patrz uwaga w [spisie dokumentacji](../README.md).

---

## 12. Licencja

AGPL-3.0. Patrz [LICENSE](../../LICENSE).
