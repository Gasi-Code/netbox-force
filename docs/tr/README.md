# NetBox Force — Kılavuz (Türkçe)

[← Tüm diller](../README.md) · [Proje README](../../README.md) · [Değişiklik günlüğü](../../CHANGELOG.md)

---

## 1. Eklenti ne yapar

NetBox *neyin* değiştiğini kaydeder. NetBox Force ise *değişikliğe hiç izin verilip
verilmeyeceğine* karar verir ve geçmesine izin vermeden önce bir gerekçe isteyebilir.

Her kaydetme ve silme işlemi ile veritabanı arasında durur. Bir değişiklik
yazılmadan önce şunları denetleyebilir:

- bir günlük açıklaması verilmiş mi ve yeterince uzun mu
- açıklama yalnızca boş sözcüklerden mi oluşuyor
- açıklama bir kayıt numarası anıyor mu
- değişiklik onaylı bir zaman aralığında mı gerçekleşiyor
- alan değerleri bir adlandırma kalıbına uyuyor mu
- zorunlu alanlar gerçekten dolu mu

Yanında iki modül daha gelir:

- **Yama yönetimi** — her sanal makine veya fiziksel sunucu için yama durumu,
  işletim sistemi, sorumlular ve güncelleme geçmişi; istenirse CheckMK'dan beslenir.
- **Graylog** — denetim olaylarını dışarı gönderir ve günlük bilgilerini ait olduğu
  nesnenin yanına geri getirir.

Her şey isteğe bağlıdır. Kurulumdan sonra yalnızca açıklamanın varlığı denetlenir,
en az iki karakterle. Gerisi web arayüzünden açılır.

---

## 2. Gereksinimler

| Bileşen | Sürüm | Notlar |
|---|---|---|
| NetBox | 4.0.0 veya üzeri | |
| Python | 3.10 veya üzeri | |
| PostgreSQL | — | NetBox'ın kendisi ister |
| `cryptography` | herhangi | NetBox ile gelir. Yoksa CheckMK sırrı ve Graylog belirteci şifresiz saklanır ve eklenti bunu ayarlar sayfasında belirtir |
| `requests` | herhangi | NetBox ile gelir. CheckMK ve Graylog için gerekir |
| RQ süreci | — | Yalnızca zamanlanmış CheckMK eşitlemesi ve Graylog sorgulaması için. O olmadan da her ikisi istek üzerine çalışır ve sayfa bunu belirtir |

---

## 3. Kurulum

### 3.1 Paketi kurun

```bash
source /opt/netbox/venv/bin/activate
pip install git+https://github.com/Gasi-Code/netbox-force.git
```

### 3.2 Eklentiyi tanıtın

`configuration.py` içinde:

```python
PLUGINS = ['netbox_force']
```

### 3.3 Geçişleri çalıştırın

```bash
cd /opt/netbox/netbox
python manage.py migrate netbox_force
python manage.py collectstatic --no-input
```

### 3.4 NetBox'ı yeniden başlatın

```bash
sudo systemctl restart netbox netbox-rq
```

### 3.5 Docker

```bash
docker exec -it <kapsayıcı> pip install git+https://github.com/Gasi-Code/netbox-force.git
docker exec -it <kapsayıcı> /opt/netbox/netbox/manage.py migrate netbox_force
docker restart <kapsayıcı>
```

LinuxServer.io imajında kurulum için `custom-cont-init.d` betiklerini
**kullanmayın**. Bunlar NetBox'ın kendi başlangıç betiklerinden *sonra* çalışır ve
geçişlerin başarısız olmasına yol açabilir. Docker Mods onlardan önce çalışır.

Kapsayıcının dosya sistemine yapılan bir kurulum imaj güncellemesinden sağ çıkmaz.
Eklentiyi imajın kalıcı eklenti kurulum düzeneğine ekleyin, yoksa bir sonraki
pull'dan sonra kaybolur.

---

## 4. Güncelleme

```bash
source /opt/netbox/venv/bin/activate
pip install --force-reinstall --no-cache-dir git+https://github.com/Gasi-Code/netbox-force.git
```

`--force-reinstall --no-cache-dir` gereklidir, çünkü pip sürüm numarasına göre
önbelleğe alır ve aksi hâlde aynı sürümün yeniden kurulmasını atlar.

**Yeniden başlatmadan önce denetleyin.** Bu adım çalışan sürece dokunmadan
eklentiyi yükler. Bir hata bildirirse yeniden başlatmayın — çalışan NetBox eski kodu
hâlâ bellekte tutar ve çalışmayı sürdürür:

```bash
cd /opt/netbox/netbox
python manage.py check
```

Ardından:

```bash
python manage.py migrate netbox_force
python manage.py collectstatic --no-input
sudo systemctl restart netbox netbox-rq
```

### Geri dönüş

```bash
pip install --force-reinstall --no-cache-dir \
  git+https://github.com/Gasi-Code/netbox-force.git@<commit>
sudo systemctl restart netbox netbox-rq
```

Geçişleri bunun için genelde geri almak gerekmez. Fazladan sütunlar eski kodu
rahatsız etmez — kod onları basitçe tanımaz. Yine de güncellemeden önce bir veritabanı
yedeği alın.

---

## 5. Yapılandırma dosyası

`PLUGINS_CONFIG` **yalnızca başlangıç değerlerini** belirler. İlk açılıştan sonra her
ayar web arayüzünde yönetilir ve veritabanında tutulur.

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

| Ayar | Varsayılan | Anlamı |
|---|---|---|
| `min_length` | `2` | Günlük açıklamasındaki en az karakter sayısı |
| `exempt_users` | yukarıya bakın | Tüm denetimlerden muaf kullanıcılar, büyük/küçük harf ayrımı yok |
| `enforce_on_create` | `False` | Oluştururken de açıklama iste |
| `enforce_on_delete` | `True` | Silerken de açıklama iste |
| `extra_exempt_models` | `[]` | Ek muaf modeller, biçim `app.model` |
| `checkmk_secret` | `''` | İsteğe bağlı. CheckMK sırrını tamamen veritabanının dışında tutar; o zaman arayüzdeki alana göre önceliklidir |

---

## 6. Sayfalar

Süper kullanıcılar **NetBox Force**'u kenar çubuğunda bulur. Aksi belirtilmedikçe tüm
sayfalar süper kullanıcılarla sınırlıdır.

| Sayfa | Amaç |
|---|---|
| **Ayarlar** | Tüm zorlama kuralları, muafiyetler, modüller, webhook, CheckMK |
| **Doğrulama kuralları** | Adlandırma kalıpları ve zorunlu alanlar, model ve alan bazında |
| **Model politikaları** | Genel ayarlardan sapmalar, model bazında |
| **İhlaller** | Engellenen her değişikliğin süzülebilir kaydı, CSV olarak dışa aktarılabilir |
| **Graylog** | Gönderme ve okuma, bkz. bölüm 7 ve 8 |
| **Gösterge paneli** | İstatistikler: hangi işlevler açık, engellenen değişiklikler, en sık kullanıcılar, 30 günlük eğilim |
| **İçe aktarma şablonları** | NetBox toplu içe aktarması için indirilebilir CSV şablonları. Açıkken tüm oturum açmış kullanıcılara görünür |
| **Kılavuz** | Kendi kullanıcılarınız için serbest metin sayfası. Açıkken tüm oturum açmış kullanıcılara görünür |
| **Yama yönetimi** | Bkz. bölüm 9 |

İki ayar ayrıca anılmayı hak eder:

- **Genel anahtar** — örneğin bir bakım penceresi sırasında tüm denetimleri duraklatır.
- **Deneme kipi (dry-run)** — ihlalleri kaydeder ama hiçbir şeyi engellemez. Yeni bir
  kuralı devreye almanın doğru yolu: gerçekten kimse durdurulmadan önce neyin
  engellenmiş *olacağı* görülür.

---

## 7. Graylog — gönderme

Denetim olaylarını NetBox'tan Graylog'a GELF üzerinden gönderir.

### Ne için

Üç şey NetBox'ta başka hiçbir yerde kayıtlı değildir:

- **Başarısız oturum açmalar.** NetBox bunları hiç saklamaz.
- **Bir değişikliğin kaynak IP'si ve tarayıcı bilgisi.** NetBox'ın değişiklik günlüğü
  ikisini de taşımaz.
- **Eklentinin kendi ayarlarındaki değişiklikler.** Bunlar NetBox'ın değişiklik
  günlüğüne girmez — zorlamayı kapatan kişi şimdiye kadar hiçbir iz bırakmıyordu.

### Kurulum

**Graylog** sayfasında, üst yarı: sunucu, bağlantı noktası, taşıma. Ardından *Test
olayı gönder*.

**UDP** ile başlayın. Hiçbir şey ulaşmazsa **TCP**'ye geçin — UDP yapısı gereği bir
hatayı bildiremez, TCP bildirebilir. Bu, "yanlış bağlantı noktası" ile "ileti
atıldı" arasını ayırır.

| Taşıma | Teslimi doğrular | Şifreli |
|---|---|---|
| UDP | hayır | hayır |
| TCP | evet | hayır |
| TCP + TLS | evet | evet |
| HTTP | evet | hayır |
| HTTPS | evet | evet |

UDP yerel ağ içinde doğru, internet üzerinden yanlıştır.

### Ne gönderilir

Olay türü başına bir satır; her biri onay kutusu ve syslog önem derecesiyle: nesne
oluşturuldu, değiştirildi, silindi; oturum açma; oturum kapatma; başarısız oturum
açma; engellenen değişiklik; eklenti ayarları değişti.

### Hacim

Ayarlanan eşikten daha çok nesne değiştiren bir istek **tek bir özet olayı** olarak
bildirilir. 500 cihazın içe aktarılması tek bir işlemdir — neredeyse aynı 500 satır
onu görmeyi kolaylaştırmaz, zorlaştırır.

Kısmak yerine özetlemek bilinçli bir seçimdir. Dolduğundan daha yavaş boşalan bir
kuyruk *en yeni* olayları atar, yani tam da yanlış yarıyı.

### Alan adları

Her olay aynı alanları taşır, böylece aramalar basit kalır:

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

`_request_id`, tek bir isteğin değiştirdiği her şeyi gruplar. Aynı anda düzenlenen
kırk cihaz tek bir işlemdir, kırk bilmece değil.

### Bilinmesi gereken üç şey

- **Bir Graylog kesintisi NetBox'taki bir kaydetmeyi ne yavaşlatabilir ne de
  başarısız kılabilir.** Olaylar, bir arka plan iş parçacığının boşalttığı sınırlı
  bir kuyruğa girer. Kuyruk dolduğunda yeni olaylar atılır ve sayılır; sayaç sayfada
  gösterilir.
- **İleti metni her zaman İngilizcedir**, arayüz dili ne olursa olsun. Graylog uyarı
  sorguları bu metne dayanır; çevirmek, biri dili değiştirdiği anda tüm uyarıları
  sessizce bozardı.
- **İstemci IP'si varsa `X-Forwarded-For`'dan okunur.** Bu başlık istemciden gelir ve
  NetBox önünde ters vekil sunucu olmadan erişilebiliyorsa sahtesi üretilebilir.

---

## 8. Graylog — okuma

Graylog bilgilerini NetBox'a getirir; böylece bir ana bilgisayar ikinci bir sekme
açmadan değerlendirilebilir.

### Kurulum

**Graylog** sayfasının alt yarısı: web adresi ve API belirteci, ardından *Bağlantıyı
test et*. Sonuç, Graylog sürümünü, saptanan arama API biçimini, en gürültülü
kaynakları ve mevcut akışları bildirir. *Şimdi sorgula* hemen bir sorgulama yapar.

**Belirteci yalnızca okuma rolüne sahip bir Graylog kullanıcısı için oluşturun.**
Graylog'un NetBox üzerinden değiştirilemeyeceğini garanti eden şey budur, bu
eklentinin kodu değil.

### Burada "yalnızca okuma" tam olarak ne demek

Her çağrı ya veri alır ya da Graylog'dan bir arama çalıştırmasını ister. Eski arama
uç noktası düz bir `GET`'tir. Daha yeni Views arama API'si değildir: bir aramayı
kaydetmek için bir `POST`, çalıştırmak için bir tane daha ister. Bu, Graylog içinde
kısa ömürlü bir arama nesnesi oluşturur ve sonuç döndürür; saklanan veriyi
değiştirmez. Ortamınızda yalnızca `GET` kabul edilebilirse, ayarlarda arama biçimini
`legacy` olarak sabitleyin.

### Kaynakları NetBox nesneleriyle eşleştirme

Kesin olarak, bu sırayla, ilk eşleşme kazanır:

| | Kural |
|---|---|
| 1 | **Elle eşleştirme** — bir kez ayarlandığında her zaman geçerlidir |
| 2 | **IP adresi** — kaynak, nesnenin tüm IP'lerine karşı |
| 3 | **Ana bilgisayar adı**, büyük/küçük harf ayrımı olmadan |
| 4 | **Ayarlanmış bir alan adı soneki çıkarıldıktan sonraki ana bilgisayar adı** |

Geri kalan her şey eşleştirilmemiş kalır ve öyle listelenir.

**Bilinçli olarak yaklaşık eşleştirme yoktur.** `srv-web-01` ile `srv-web-02` tek
karakter farklıdır, bu yüzden herhangi bir benzerlik ölçüsü onları %96 eşleşme
sayar — oysa iki ayrı makinedir. Numaralandırılmış bir adlandırma şemasında — yani
adına layık her NetBox'ta — en benzer aday düzenli olarak yanlış olandır. Günlükler
komşu sunucunun altına dosyalanır ve kimse fark etmez. Benzerlik yalnızca
eşleştirilmemiş bir kaynağın yanındaki önerileri **sıralamak** için kullanılır; asla
kendiliğinden eşleştirme yapmaz.

Graylog'un önünde merkezî bir syslog aktarıcısı varsa, tüm iletiler aktarıcının
adresini taşır ve 2. kural işe yarar bir şey bulamaz. O zaman kaynak alanının ana
bilgisayar adını taşıması gerekir; 3. ve 4. kurallar bunun içindir.

### Sayfalar

- **Kaynaklar** — Graylog'un bildirdiği her şey, sayaçlarla birlikte; eşleştirilmiş,
  eşleştirilmemiş, sessiz, hiç görülmemiş ve yok sayılan olarak süzülebilir.
- **Sessiz** — NetBox'ta eşleştirilmiş ama artık hiçbir şey göndermiyor. Ölü, yanlış
  yapılandırılmış ya da bir kalıntı. Sistemlerin hiçbiri bunu tek başına fark edemez.
- **Graylog'da hiç görülmemiş** — çapraz denetimin öteki yarısı.
- **Küme** — yeşil/sarı/kırmızı lambalı düğümler, dizinleyici sağlığı, günlük
  birikimi; her düğüm kendi NetBox sanal makinesine bağlı.
- **Nesnenin üzerinde** — eşleştirilmiş kaynağı olan cihaz ve sanal makineler,
  sayaçlar, istek üzerine son iletiler ve Graylog'a bir bağlantı içeren bir Graylog
  paneli alır.

### Yük ve güvenlik

- Bir sorgulama, cihaz başına bir sorgu değil, **tüm ana bilgisayarlar için tek bir
  gruplanmış sorgudur**. 800 cihazlı bir yerleşke üç istek eder.
- Küme paneli ve ileti listesi sayfa çizildikten **sonra** yüklenir. Yavaş ya da ölü
  bir Graylog boş bir panel verir, asla donmuş bir NetBox sayfası değil.
- Eşleştirme eklentinin kendi tablosunda yaşar. **Graylog asla bir NetBox çekirdek
  nesnesine yazmaz** — eklentiyi kaldırmak eşleştirmeyi kaldırır ve NetBox'a
  dokunmaz.
- İleti uç noktası yalnızca, çağıranın görmeye yetkili olduğu bir nesneyle
  eşleştirilmiş bir kaynak için yanıt verir.

---

## 9. Yama yönetimi ve CheckMK

Her sanal makine veya fiziksel sunucu için yama durumunu, işletim sistemini,
sorumluları ve güncelleme geçmişini tutar.

- **Durum** yeşil / sarı / kırmızı; elle tutulur ya da CheckMK'dan okunur.
- **Gecikme eşiği** — N gün içinde yamalanmayan kayıtlar geciken olarak işaretlenir.
- **Yükseltme** — N gün *sarı*da kalan bir kayıt kendiliğinden *kırmızı* olur.
- **Kişiler** — NetBox iletişim nesnelerinden yönetici ve süreç sorumlusu.
- **Güncelleme geçmişi** — her yama turu için bir kayıt, kayıt numarası ve notla.
- **Erişim**, Django izinleriyle değil, eklenti ayarlarındaki NetBox grup adlarıyla
  verilir.

### CheckMK

Bütünleşme bir **pull**'dur: NetBox CheckMK'dan okur. CheckMK'ya hiçbir şey
yazılmaz, bu yüzden yalnızca okuma yetkili bir otomasyon kullanıcısı yeter.

Ayarlar sayfasında yapılandırılır: site adresi, otomasyon kullanıcısı, sır, hizmet
süzgeci ve eşitleme aralığı. Sır şifrelenmiş olarak saklanır ve bir daha gösterilmez.

Takılmış bir eşitleme en çok canı yakan arızadır, çünkü sayfa sessizce doğru olmaktan
çıkmış bir yama durumunu göstermeye devam eder. Bu yüzden gösterge paneli, son
başarılı eşitleme ayarlanan aralığın iki katından eskiyse bunu açıkça söyler.

---

## 10. Sorun giderme

**Eklenti kenar çubuğunda görünmüyor.**
`configuration.py` içinde `PLUGINS` ayarlı mı? Geçişler çalıştırıldı mı? NetBox
yeniden başlatıldı mı? Kenar çubuğundaki etiketler yalnızca yeniden başlatmada
güncellenir; eklenti içindeki sekmeler hemen.

**Değişiklikler engellenmiyor.**
Şu sırayla denetleyin: genel anahtar, deneme kipi, kullanıcının muaf kullanıcılar ya
da gruplar arasında olup olmadığı ve bir model politikasının o model için zorlamayı
kapatıp kapatmadığı.

**Bir sayfa eksik sütun bildiriyor.**
Geçişler çalıştırılmamış ya da yalnızca kısmen çalıştırılmış.
`python manage.py migrate netbox_force`.

**"Arka planda hiçbir işlem çalışmıyor."**
`netbox-rq` çalışmıyor. CheckMK eşitlemesi ve Graylog sorgulaması o zaman yalnızca
düğmeye basıldığında çalışır.

**Graylog'a hiçbir şey ulaşmıyor.**
Taşımayı UDP'den TCP'ye çevirin. UDP bir hatayı bildiremez; TCP bildirebilir ve hata
iletisi bağlantı noktasının mı yanlış olduğunu yoksa iletinin mi reddedildiğini
söyler.

**Bir cihazdaki Graylog paneli boş kalıyor.**
Cihazın eşleştirilmiş kaynağı yok. *Kaynaklar → Eşleştirilmemiş* sayfasını açıp
eşleştirin ya da FQDN'in kısaltılabilmesi için ayarlara kendi alan adı sonekinizi
ekleyin.

**`SECRET_KEY` değiştikten sonra CheckMK sırrı veya Graylog belirteci artık çalışmıyor.**
Her ikisi de `SECRET_KEY`'den türetilen bir anahtarla şifrelenir. Yeniden girilmeleri
gerekir.

---

## 11. Dili değiştirme

Dil, kullanıcı başına değil, **kurulum başına** bir ayardır. Ayarlar sayfasından
değiştirilir.

Eklenti içindeki sekmeler ve sayfalar hemen değişir. Kenar çubuğundaki etiketler
başlangıçta bir kez kurulur ve ancak NetBox yeniden başlatıldıktan sonra değişir.

Engelleme sırasında kullanıcılara gösterilen iletiler bu ayarı izler. API hata
iletileri ve Graylog'a gönderilen iletiler İngilizce kalır — bkz.
[belgelendirme dizini](../README.md)'ndeki not.

---

## 12. Lisans

AGPL-3.0. Bkz. [LICENSE](../../LICENSE).
