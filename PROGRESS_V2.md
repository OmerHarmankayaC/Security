# İlerleme Günlüğü — Sürüm 2

Birinci aşamanın günlüğü [`PROGRESS.md`](PROGRESS.md) dosyasında kapandı ve
arşivdir; okunmaz. Sürüm 2'nin kaydı buradan başlar.

Her oturum sonunda buraya bir kayıt eklenir: tarih, tamamlanan,
kalan/ertelenen, sıradaki oturumun ilk işi. Yeni oturum bu dosyayı okuyarak
başlar.

---

## 2026-08-14 — Tur 7: Düzenleme Sistemi — **BİTTİ**

Kaynak: bu turun promptu. **Altı iş de bitti.** Çalışma
`tur7-duzenleme-sistemi` dalında yürüdü.

Doküman sürümleri turun başında doğrulandı: Charter **1.4**, SRS **1.23**,
SDD **1.30**, Backlog **1.20** — dördü de taşıyor.

> **İSİM ÇAKIŞMASI.** Bu dosyada bir alttaki kayıt da "Tur 7" adını
> taşıyordu (gösterim verisi ve tatil takvimi). O iş bir tur promptundan
> değil doğrudan istekten doğdu; karışmasın diye **"Ara iş"** olarak
> yeniden adlandırıldı. Numaralı Tur 7 budur.

### İş 5 — yazdırma yalnızca ilk günü basıyordu · **BİTTİ**

Teşhis doğrulandı, tahmin edilenden başkaydı. Önizleme `position: fixed` +
`overflow: auto` bir kabın içinde duruyor, baskı CSS'i de yazdırma alanına
`position: absolute` veriyordu. Üçü de öğeyi normal akıştan çıkarır ve **akış
dışı içerik sayfalanmaz** — tarayıcı ilk sayfayı çizip durur. Tek tablolu
çıktıda görünmüyordu (zaten bir sayfaya sığıyordu); Tur 6'da gün başına ayrı
ızgaraya geçilince yedi günlük dönem tek sayfa basmaya başladı.

Önizleme artık `document.body`'ye **portal** ile bağlanıyor, yani `#root`un
kardeşi; baskıda `#root` tümüyle gizleniyor. Uygulama yerleşimden düştüğü
için konumlandıracak bir şey kalmadı ve görünürlük hilesi de mutlak
konumlandırma da kaldırıldı.

jsdom sayfalama yapmaz, **"yedi sayfa çıktı" TEST EDİLEMEZ.** Test asıl
bozulan şeyi kilitliyor: önizleme gövdenin çocuğu olmalı, çünkü baskı kuralı
`#root`u gizleyerek çalışıyor.

### İş 6 — haftalık görünüm okunmuyordu · **BİTTİ**

Hücre artık saat aralığını **metin** olarak yazıyor ("08–16 GÜV"), altındaki
üç piksellik **düz** çubuk bloğun günün neresinde durduğunu gösteriyor.

Çubuk gradient değil: okunması gereken şey tam olarak **sınırdır**, gradient
sürekli olduğu için onu belirsizleştirir — sürekliliğin bant için erdem
olduğu yerde burada kusur. Çubuk saat rengini de taşımıyor; gündüz tonu
(#E9E7D9) hücre zemininden (#E4E7E1) ayırt edilemiyor ve üç piksellik bir
çubukta o fark tümüyle kayboluyor. "Gece mi gündüz mü" bilgisi zaten metinde.

Düğüm sayısı hücre başına sabit kaldı; performans testinin sınırı 1.000'den
**2.000**'e çıkarıldı (30 × 7 ölçümü ~1.400). Testin koruduğu şey bugünkü
sayı değil, sayının **dilim sayısından bağımsız** kalmasıdır.

### İş 2a + İş 3'ün sunucu tarafı — taslak oturum · **BİTTİ**

`dogrula(surum_id, degisiklikler)` oturumun **tamamını** alıp aday çizelgeyi
bellekte kuruyor ve **hiçbir şey yazmıyor** — işlem açmıyor, sapma
tablolarına dokunmuyor.

`kaydet(surum_id, degisiklikler, damga)` tek işlemde: `SELECT … FOR UPDATE`
→ durum → damga → **yeniden doğrula** → uygula → sapmaları tazele → yeni
damga. Kısmi kayıt yok; istemcinin "geçerliydi" bilgisine güvenilmiyor.

`PUT /api/atama` kalktı, `POST /api/atama/kaydet` geldi.
`EK_B_UC_NOKTALAR.md` yeniden üretildi — **68 uç nokta, denetim temiz.**

**Göç `a3f5d81c7e42`** — `cizelge_surumu.damga`. Şema değişikliği, veri
dönüştürmez, geri alınabilir. Var olan satırlara `gen_random_uuid()` ile
**satır başına farklı** değer yazılır; tek adımda `server_default` verilseydi
hepsi aynı değeri alır ve damga hiçbir şey ayırt etmezdi.

**On bir yeni test** (`test_duzenleme_oturumu.py`) — turun istediği dördü:
kaydetmeden çıkınca sürüm değişmiyor, damga çakışması ikinci kaydı
reddediyor, yayınlanmış sürüm hem yordamda hem uç noktada korunuyor, ve
**biriken değişikliklerin birlikte doğrulandığı** test.

### Tasarımdan iki sapma — ikisi de gerekçeli

1. **±7 günlük doğrulama penceresi kalktı.** O kısayol TEK değişiklik
   varsayımına dayanıyordu; birden fazla değişiklikte kuralların göreceği
   küme yanlış çıkardı. SDD 5.5'in kendi sözde kodu zaten dönem geneli
   atamalar üzerinde çalışıyor.
2. **Damga `guncelleme_zamani` değil ayrı bir sütun.** O alan satırın her
   dokunuluşunda değişir (yayınlama, arşivleme) ve mikrosaniye duyarlılığıyla
   JSON üzerinden gidip gelir; eşitlik karşılaştırması biçimlendirmeye
   bağımlı hale gelirdi.

### DOKÜMAN BORCU — **bir madde**

**SDD 4.2.4 — `cizelge_surumu.damga`.** 5.5.1 `surum.damga`'dan ve
`YENİ_DAMGA()`'dan söz ediyor, ama 4.2.4'teki alan listesinde böyle bir
sütun yok. Sütun eklendi (göç `a3f5d81c7e42`), dokümana işlenmeli.

### Yol boyunca iki tuzak

**Test veritabanı göç görmemişti.** İlk koşumdaki 41 başarısızlığın tamamı
bundandı. Şema bilinçli olarak `create_all` ile değil **göçle** kuruluyor
(göçlerin kendisi de sınansın diye, conftest bunu belgeliyor); yeni bir göç
eklendiğinde `VERITABANI_URL=$TEST_VERITABANI_URL alembic upgrade head` de
koşturulmalı.

**Kendi fikstürüm test kirliliği üretti ve yanlış teşhise yol açtı.** Yeni
fikstür bütün kuralları global pasifleştirip commit ediyordu; `kural` tablosu
bütün testlerce paylaşıldığı için sonraki testler kuralsız katalogla kalıyor
ve **başarısızlık kümesi koşumdan koşuma değişiyordu**. Bu kirlilik varken
`test_kimlik_api` ve `test_calisan_api` tek başlarına koşturulduğunda dokuz
test düşüyordu ve bu, "önceden var olan bir sıra bağımlılığı" diye
kaydedilmeye çok yakındı. Fikstür düzeltildikten sonra **ikisi de izolasyonda
geçiyor** — böyle bir bağımlılık yok. Ders: paylaşılan tabloyu değiştiren bir
fikstür, ölçtüğü şeyi de bozar.

### Turun bitiş kontrolü — sunucu tarafı

- [x] `pytest` tam takım **360 test geçiyor** — **ters dosya sırasında da**
      (`ls tests/test_*.py | sort -r`), aynı 360. Sıra bağımlılığı yok
- [x] `ruff check` ve `ruff format` temiz
- [x] Taslak oturumun dört testi de yerinde
- [x] Biriken değişikliklerin **birlikte** doğrulandığı test yazıldı
- [x] `EK_B_UC_NOKTALAR.md` yeniden üretildi
- [ ] Frontend testleri ve `tsc`/`oxlint` — arayüz işi yapılmadı

### İş 1 — düzenleme ızgaranın üzerine taşındı · **BİTTİ**

Boş satırda sürükle → blok; kenardan tut → uzat/kısalt; gövdeden tut → gün
içinde kaydır **ya da başka personelin satırına bırak**; tıkla → menü (görev
noktası, kilitle, sil).

**SÜRÜKLEME SINIRA DAYANINCA DURUR.** Aralık artık uyarıyla işaretlenmiyor,
**kırpılıyor**: asgarinin altına inen sürükleme asgaride, azaminin üstüne
çıkan azamide duruyor. Değerler kural kataloğundan; kural pasifse kırpma da
yok. Kullanıcı geçersiz bir seçimi tamamlayıp sonradan reddedilmiyor.

**Silme menüde ve görünür.** Eski ekranda bir açılır listenin "— Boşalt —"
seçeneğinin içine saklıydı; bir işlemi başka bir işlemin seçeneği yapmak onu
bulunmaz kılar.

Form paneli **ikincil yol** olarak yanda kaldı (SRS 5.6): tam saat değeri
yazmak isteyen için, ızgaranın altında değil yanında.

### İş 2b — oturum arayüzü · **BİTTİ**

Değişiklikler istemcide birikiyor ve ızgarada anında görünüyor; her adımdan
sonra sunucuya **oturumun tamamı** doğrulatılıyor ve sunucu hiçbir şey
yazmıyor. Geri al / yinele birikimi ileri geri sürüyor. Kaydet tek istek
gönderiyor ve damgayı taşıyor; yanıttaki yeni damga saklanıyor.

Kirli oturumda **dönem ve sürüm seçicileri, Yeniden Çöz düğmesi kilitli** ve
sekme kapatma `beforeunload` ile uyarılıyor (FR-6.8).

**Kilit bilinçli olarak oturumun DIŞINDA** ve anında yazılıyor: kilit atamayı
değiştirmez, yalnızca yeniden çözümde sabit girdi sayılıp sayılmayacağını
belirler (FR-6.5). Oturuma alınsaydı kaydedilmemiş bir kilit "bu blok
korunuyor" diye görünür ama yeniden çözüm onu görmezdi.

### İş 3'ün arayüz tarafı · **BİTTİ**

Yayınlanmış/arşiv sürümde ızgara salt okunur, düzenleme araçları çalışmıyor
ve ekranın başında **nedenini söyleyen** bir şerit duruyor: yeni taslak
türetilmesi gerektiği (FR-7.3). Sunucu tarafı zaten reddediyordu; araçların
gizlenmesi tek başına yeterli değil, ama kullanıcının NEDEN
düzenleyemediğini okuması gerekiyor — yoksa ızgaranın tepkisizliği hataya
benziyor.

### İş 4 — sonuç dili · **BİTTİ**

Şerit önce cümleyi yazıyor: "Kapsama açığı 1 kişi azaldı; toplam saat dengesi
1 saat bozuldu." Sayısal ceza dökümü **ayrıntı bağlantısının arkasında**.

**Zorunlu ihlal varken başka hiçbir şey gösterilmiyor** — değişiklik
uygulanmadığı için ceza dökümü gerçekleşmemiş bir durumu anlatır ve ikisini
birlikte göstermek kullanıcıya iki farklı gerçeklik sunardı. "Kabul
edilebilir" ile kırmızı uyarı artık aynı anda görünemiyor.

### Bir dayanıklılık açığı — testte yakalandı

Gövde sürüklemesinde imlecin hangi saatin üzerinde olduğu, şeridin kabına
göre oranla bulunuyor. Kap **sıfır genişlikteyken** bölme `NaN` üretiyordu ve
`NaN === NaN` **false** olduğu için "kıpırdamadı" kontrolü sessizce çöküyor,
tek tık taşımaya dönüşüyordu. jsdom düzen hesaplamadığı için test bunu ilk
denemede gösterdi; tarayıcıda da henüz yerleşmemiş bir kapta aynı şey olurdu.

### Testte OLMAYAN davranışlar — gözle bakılmalı

jsdom düzen (layout) hesaplamaz. Aşağıdakiler **test edilmedi**:

- **Sürükleme akıcılığı.** Testler hücrelere doğrudan olay göndererek jestin
  mantığını doğruluyor; imlecin gerçekten o hücrenin üzerinde olup olmadığını
  doğrulamıyor.
- **Taşımada tutulan saatin korunması.** Şeridin neresinden tutulduğu oranla
  hesaplanıyor ve jsdom'da o oran hep sıfır; testler yalnızca SATIR
  değişikliğini ölçüyor.
- **Menünün konumu.** Şeridin altında açılıyor; dar sütunda ya da ızgaranın
  sağ kenarında ekrandan taşabilir.

### Turun bitiş kontrolü

- [x] `pytest` tam takım **360 test geçiyor** — **ters dosya sırasında da**
      (`ls tests/test_*.py | sort -r`), aynı 360. Sıra bağımlılığı yok
- [x] `ruff check` ve `ruff format` temiz
- [x] `tsc -b` ve `oxlint` temiz (4 uyarı, turdan önce de vardı)
- [x] **284 frontend testi** geçiyor — karışık sırada da (`--sequence.shuffle`)
- [x] Taslak oturumun dört testi de yerinde
- [x] Biriken değişikliklerin **birlikte** doğrulandığı test yazıldı
- [x] `EK_B_UC_NOKTALAR.md` yeniden üretildi
- [ ] `git status` temiz — dört kanonik doküman proje yürütücüsünde açık

### Sen ne göreceksin — şu üç ekranı kendi gözünle aç

1. **Çizelge → Gün, boş bir satırda sürükle.** Asgariye dayandığında
   sürüklemenin durduğunu hisset; önizleme "Asgari blok 4 saat (H1)" yazmalı.
2. **Bir bloğu gövdesinden tutup başka personelin satırına bırak.** Kaynak
   şerit sürükleme boyunca soluklaşıyor, önizleme hedef satırda çiziliyor.
   Tuttuğun saatin korunup korunmadığına bak — bu testte ölçülemedi.
3. **Bloğa tıkla.** Menü şeridin altında açılmalı; dar sütunda ya da
   ızgaranın sağ kenarında ekrandan taşıyorsa söyle.

Ayrıca **kaydetmeden dönem değiştirmeyi dene**: seçici kilitli olmalı ve
"Önce değişiklikleri kaydedin ya da vazgeçin" demeli.

---

## 2026-08-14 — Ara iş: Gösterim Verisi ve Tatil Takvimi — **BİTTİ, DAĞITILDI**

Sunucudaki demo verisi Tur 4 öncesindendi ("Demo Personel GG-001", 44 kişi,
Müracaat noktası); göç onu olduğu gibi taşımıştı. İstenen yenileme sırasında
üretecin kendisi de gözden geçirildi.

### Önce tespit: istenenlerin çoğu zaten yazılıydı

Gerçekçi adlar, izin ve talep demo verisi, resmi tatil üretimi, üretilmiş
çizelgeler, pasif personel, devir bakiyeleri ve Özel Gün ekranındaki
Ekle/Değiştir/Sil üçlüsü Tur 4/5'te yapılmıştı. Sunucu bunları hiç görmemişti.
Gerçek eksik üç maddeydi ve üçü de karar gerektirdi.

### Üç karar

1. **Müracaat kapsam dışı kalır.** SRS 1.19 noktayı ve yetkinliği kaldırmış,
   yükünü Güvenlik'e taşımıştı (3.3.3: "tek noktaya kapalı bir personel havuzu
   kalmamıştır"). Geri getirmek SRS 3.3.2/3.3.3/3.3.4 ve Charter kadro
   analizini değiştirirdi. **Doküman borcu doğmadı.**
2. **Beş haftalık geçmiş, senaryo dönemlerinin YERİNE geçer.**
3. **Dini bayramlar kütüphaneden gelir.**

### Yeni dönem takvimi — geçmişe bakar

Eskiden ileriye bakıyordu (dört haftalık sıkışık dönem, sonraki bayram
haftası) ve ürün çoğunlukla yaşanmamış bir takvim gösteriyordu. Artık bugünü
içeren hafta + önceki dördü, hepsi gerçek çözücüyle **60 sn** limitle
çözülüyor. Yerel koşumun sonucu (bugün 14.08.2026):

| Hafta | Tarih | Durum | Atama | Eksik kişi |
|---|---|---|---|---|
| H-4 | 13–19 Tem | yayınlandı | 151 | 0 |
| H-3 | 20–26 Tem | **çözüldü** (yayınlanmadı) | 137 | **12** |
| H-2 | 27 Tem–2 Ağu | yayınlandı | 163 | 0 |
| H-1 | 3–9 Ağu | yayınlandı | 158 | 0 |
| H-0 | 10–16 Ağu | arşiv + yayınlandı | 163 | 0 |

**Kaldırılan senaryolardan ikisi bedelsiz korundu.** Kapsama açığı senaryosu
dar haftaya (H-3) taşındı: yedi şeften beşi izinde, nokta kesintisiz dolu ve
haftada 168 kişi-saat istiyor; kalan iki kişi günlük tavan ve haftalık izin
günü altında en çok 132 verebiliyor. Eksik olan **saat değil kişi** — hiçbir
blok uzunluğu kapatamaz (SRS TD-13). Ölçülen açık **12 kişi, tamamı Vardiya
Şefliği'nde**. TD-8'in "çözüldü" durumu da o haftanın yayınlanmamasından
geliyor. Kota senaryosu personel kaydındaki devir bakiyelerinde duruyor.

**Kaybedilen:** fazla çalışma ve kota dönemleri ayrı dönem olarak yok; resmi
tatilin çözüme etkisi artık üretim gününe bağlı (bugün 15 Temmuz H-4'e
düşüyor, başka bir gün hiçbir haftaya düşmeyebilir).

**Tercih penceresi.** Beş dönemin hepsi bugün veya geçmiş olunca açık pencere
kalmıyordu ve Tercihler ekranı boş açılacaktı. Bugünü içeren haftanın
penceresi açık bırakıldı (son tarih 16 Ağu). Devam eden bir hafta için tercih
toplamak alışıldık değil; alternatifi özelliği hiç gösterememekti.

### Resmi tatil takvimi — `holidays` kütüphanesi

`app/services/tatil_takvimi.py` tek kaynak; `holidays==0.102` bağımlılık
olarak eklendi. Üretilen: **27 gün / iki yıl**, Ramazan (3 gün) ve Kurban
(4 gün) dahil, Türkçe adlarla.

Eski üreteç dini bayramları bilinçli dışarıda bırakıyordu ve gerekçesi
yazılıydı: "tahmini bir tarih yazmak, doğru sanılan yanlış bir veri
üretirdi". İtiraz doğruydu, çözümü eksikti — tarihleri **elle yazmamak** ile
**hiç yazmamak** aynı şey değil.

Sekiz test kilitliyor. Tarihler teste GÖMÜLMEDİ (kütüphanenin bilgisi, sürümle
düzelebilir); sınanan şey takvimin özellikleri: dini bayramın yıl içinde
geriye kayması, çok günlü bayramın gün gün dönmesi, adların Türkçe olması,
aynı günün iki kez dönmemesi (`ozel_gun` anahtarı tarihtir).

### Üretecin sabit tarihleri kalktı

`aktif_baslangic` 1 Ocak 2026'ya, pasif personelin kapanışı 31 Ocak 2026'ya
sabitti. İkisi de bugüne göre hesaplanıyor — dosyanın zaten uyguladığı
"BUGUNE GORE, sabit tarihlerle DEGIL" ilkesi bu iki satırda atlanmıştı.

### Baskı çıktısındaki kırpma kusuru düzeltildi

Tur 6'nın çıktısı gerçek kâğıtta denendi (PDF). Dar şeritlerde etiket
kırpılıyordu — "22.00–05.00 G…" — ve gece yarısını aşan bloğun `›` işareti
tam o kırpmanın içinde kayboluyordu. Ekranda ipucu metni kaybı telafi eder,
kâğıtta edecek bir şey yok. Dört saatten dar şeritlerin etiketi artık şeridin
yanına, gün sonuna dayananlarda soluna yazılıyor. Dört test eklendi.

### Dağıtım — **YAPILDI** (14.08.2026, kesinti ~14 dk)

Yedek: `/opt/vardiya/yedek/vardiya-20260814-0620-demo-oncesi.dump` (88K,
155 nesne). Sıra: yedek → servisleri durdur → rsync → `chown` →
`pip install -e .` → üreteç → başlat. Göç yok, şema değişmedi.

**`VERI_TEMIZLIGINE_IZIN` `.env`'e HİÇ yazılmadı.** Değer tek seferlik
komutun önüne konuldu (`app/veri_temizligi.py`'nin belgelediği kalıp), yani
açılıp kapatılan bir kilit olmadı; sunucu bir sonraki kazara çalıştırmaya
karşı korumasını hiçbir an kaybetmedi. `.env`'de satır yok, doğrulandı.

Sunucudaki sonuç (yerel koşumla aynı yapı, çözücü sayıları farklı — 60 sn
limitte arama belirlenimci değil):

| Hafta | Durum | Atama | Eksik |
|---|---|---|---|
| H-4 13–19 Tem | yayınlandı | 159 | 0 |
| H-3 20–26 Tem | **çözüldü** | 139 | **8** (yerelde 12) |
| H-2 27 Tem–2 Ağu | yayınlandı | 165 | 0 |
| H-1 3–9 Ağu | yayınlandı | 161 | 0 |
| H-0 10–16 Ağu | arşiv + yayınlandı | 164 | 0 |

Açığın tamamı yine Vardiya Şefliği'nde. 30 personel, 4 tercih, 12 izin,
27 resmi tatil (13'ü Ramazan/Kurban), 343 gece yarısını aşan blok.
Beş servis `active`, `journalctl`'de 0 hata, `/api/ben` kimliksiz 401.

**Bir tuzak yakalandı.** İlk rsync frontend'de **0 dosya** aktardı: `dist/`
baskı düzeltmesinden önce derlenmişti ve sunucudakiyle aynıydı. Yeniden
derlenip gönderildi (`index-D5cG4Hsi.js`); yakalanmasaydı eski arayüz
sessizce kalacaktı. Ders: `npm run build` ile rsync arasına başka bir
kaynak değişikliği girerse rsync "değişiklik yok" der ve HAKLIDIR — yanlış
olan derlemenin eskiliğidir.

**Yönetim hesabı silinmedi**, doğrulandı: `omerharmankaya` (YONETIM),
`yonetici1`, `yonetim1` üçü de aktif. DAGITIM.md'deki "demo yenilenirse
yönetim hesabı yeniden kurulmalı" notu `HesapKapsami.PERSONELE_BAGLI`
davranışından eskidir.

### Açık kalan — çalışan paneli için hesap yok

Temizlik **personel kaydına bağlı 1 hesabı** (1 açık oturumla) sildi; bu
beklenen davranıştır (o hesap silinen personele bağlıydı). Sonuç: şu anda
çalışan rolünde hiçbir hesap yok ve **çalışan paneli gösterilemez** —
"Vardiyalarım", "sıradaki vardiya", tercih bildirimi ve FR-9.4'ün değişen
gün işareti ancak çalışan hesabıyla görülür. Yeni personelden birine
Kullanıcılar ekranından hesap açılmalı; parola belirlemek proje
yürütücüsünün işi.

---

## 2026-08-13 — Dağıtım: Tur 1–6 birikimi — **TAMAMLANDI**

Gösterim sunucusuna (46.225.109.40) çıkıldı. Kesinti penceresi
**19:26–19:31 (~5 dk)**; `vera-rag`, `energy-api` ve ortak PostgreSQL'e
dokunulmadı, üçü de boyunca ayakta kaldı.

### Runbook'un üç varsayımı tutmadı — sıra buna göre düzeltildi

**1. Sunucu kodu git ile çekmiyor.** `/opt/vardiya` bir git deposu değil
(hiçbir alt dizininde `.git` yok), `frontend/` dizini yok (derlenmiş arayüz
`web/` altında) ve sunucuda **Node kurulu değil**. Yani "git fetch + merge
--ff-only" ve "sunucuda npm run build" adımları koşamazdı. Yürürlükteki
yordam `deploy/DAGITIM.md`'de kayıtlı ve altı dağıtımdır aynı: **yerelde
derle, `rsync` ile gönder, sonra `chown -R vardiya:vardiya`**. Bu, "dağıtım
sunucunun çektiği koddan yapılır" cümlesini tersine çevirir — dağıtılan şey
yerel çalışma ağacıdır, o yüzden önce `HEAD == origin/main == 4d8b5d7` ve
`git status` boş olduğu doğrulandı.

**2. Göç durumu farklıydı.** `alembic current` = `e7b2c4915d80`, yani:

| Göç | Runbook | Gerçek |
|---|---|---|
| `d1f83a6c40b2` (talep → aralık) | bekliyor | zaten uygulanmış (12.08) |
| `e7b2c4915d80` (kural parametre adları) | bekliyor, kodla gitmeli | zaten uygulanmış; sunucudaki kod da o dönemin koduydu, tutarlıydı |
| `f2a8c561d94b` (atama → blok, `vardiya_tipi` düşer) | — | **bekleyen tek göç** |

Dolayısıyla "eski kod / yeni parametre" `KeyError` penceresi bu dağıtımda
hiç oluşmadı; risk yalnızca veri dönüşümü ve tablo düşürmedeydi.

**3. `pg_dump "$VERITABANI_URL"` düşerdi.** Değer `postgresql+psycopg://`
ile başlıyor — SQLAlchemy'nin biçimi, libpq'nun değil. `DAGITIM.md` bunu
bir kez yaşanmış tuzak olarak kaydetmiş ("pg_dump düştü, alembic devam
etti"). Kullanılan biçim:
`PGURL=$(printf %s "$VERITABANI_URL" | sed 's|+psycopg||')`.
Yedek dizini de `/root` değil `/opt/vardiya/yedek/`.

Ayrıca runbook'un girişi "durdur → yedek", numaralı adımları "yedek →
durdur" diyordu; girişteki sıra izlendi (çalışan servis yedeğin ortasında
yazabilir).

### Uygulanan sıra

1. Yerelde `npm run build` + **231 vitest** + **341 pytest** (10 dk 28 sn)
2. Bitmemiş çözüm işi kontrolü (yok) → `systemctl stop vardiya-cozucu`, `vardiya-api`
3. **Parola rotasyonu** (aşağıda) — proje yürütücüsü koştu
4. Yedek: `/opt/vardiya/yedek/vardiya-20260813-1928-tur6oncesi.dump`,
   **85K**, `pg_restore -l` ile denetlendi: 165 nesne, 20 tablo verisi
5. `rsync`: `frontend/dist/` → `web/` (35 dosya), `backend/` → `backend/`
   (66 dosya). `--delete` yalnız iki dosya sildi: Tur 5'te kaldırılan
   `app/services/vardiya_hesaplari.py` ve testi. `.env`, `.venv`,
   `__pycache__` hariç tutuldu. Ardından `chown -R vardiya:vardiya`.
6. `pip install -e .` → çıkış 0
7. `alembic upgrade head` → tek göç koştu, çıkış 0

### `alembic current` — önce / sonra

```
önce : e7b2c4915d80
sonra: f2a8c561d94b (head)
```

### Göç doğrulaması — sayarak

| Ölçü | Önce | Sonra |
|---|---|---|
| `atama` satırı | 3.051 | **3.051** |
| toplam kişi-saat | 24.408,00 | **24.408,00** |
| `talep` / `tercih` / `kural` | 21 / 4 / 20 | 21 / 4 / 20 |
| `personel` / `cizelge_surumu` | 44 / 26 | 44 / 26 |
| `vardiya_tipi` tablosu | var (3 satır) | **düştü** |

`atama` sütunları `vardiya_tipi_id, tarih` yerine artık
`baslangic_zamani, bitis_zamani`. **1.171 blok gece yarısını aşıyor** —
mutlak eksenin var oluş nedeni sunucudaki gerçek veride de görünüyor.
Kural parametreleri yerinde: `H1.asgari_blok_saat=4`,
`H3.gece_esigi_saat=4`, `H9.azami_gunluk_saat=11`.

### Doğrulama

- `systemctl is-active`: vardiya-api, vardiya-cozucu, vera-rag,
  energy-api, postgresql → **beşi de active**
- `http://127.0.0.1:8002/health` → `{"durum":"ok"}`
- `https://vardiya.omerharmankaya.com/` → yeni paket sunuluyor
  (`index-DdDLnrHO.js` 200); `web/assets` içinde eski paket kalmadı
- `GET /api/ben` kimliksiz → **401** (API Caddy üzerinden erişilebilir,
  yetkilendirme çalışıyor)
- `journalctl` (başlatmadan beri): **0 hata satırı**
- Kural kataloğu salt okunur sınandı: 20 kural satırı → 20 kural nesnesi
  kuruldu, parametre okuma hatası yok

**Runbook'ta yanlış olan bir kontrol:** `curl https://.../health` API'ye
gitmiyor. Caddy yalnızca `/api/*`'i vekilliyor, `/health` SPA'ya düşüyor ve
`index.html` dönüyor. API'nin sağlık ucu kök altında (`/health`), yani
dışarıdan erişilebilir değil. Doğru kontrol ya yerelden `127.0.0.1:8002`
ya da `/api/ben` → 401.

### Parola rotasyonu

Dağıtım sırasında `vardiya` veritabanı kullanıcısının parolası değiştirildi.
Nedeni: bu oturumda koşulan bir şema kontrolü psycopg hatası verdi ve hata
mesajı bağlantı dizesinin tamamını, parolayı da içerecek biçimde bastı.
Rotasyonu proje yürütücüsü koştu (`\password`, komut satırına yazılmadı);
`.env` güncellendi, eski parolanın kopyasını taşıyan `/opt/vardiya/.env.yedek`
silindi. Yeni parola, göçten ÖNCE `alembic current` ve `pg_dump` ile
doğrulandı — yedeğin başarısı aynı zamanda rotasyonun sınavı oldu.

Bundan sonra sunucuya gönderilen her komutun çıktısı
`sed -E 's#://[^@]*@#://***@#g'` süzgecinden geçirildi.

### Açık kalan — `S6.desen_toleransi_saat` kural kaydında yok

Kural kataloğu sınandığında tek eksik bu çıktı. **Arıza değil:** kod
`self.parametreler.get("desen_toleransi_saat", varsayılan)` ile okuyor,
yani çözücü varsayılanla çalışır. Etkisi yalnızca Kural ekranında: bu
parametre okuma kipinde `—`, düzenleme kipinde boş kutu görünür. Kalıcı
çözüm ya ekrandan bir değer kaydetmek ya da kaydı ekleyen küçük bir göç.
Tur 5'in göçü `H1` ve `H3` için bu satırları yazmıştı, `S6` atlanmış.

### `.env` — yasaklı iki değişken yok

`TEST_VERITABANI_URL` ve `VERI_TEMIZLIGINE_IZIN` sunucuda tanımlı değil,
doğrulandı. Gösterim verisi yenileme (`demo_veri_uret.py --reset`) bu
dağıtımın parçası DEĞİLDİR ve yapılmadı — ayrı karar olarak bekliyor.
Sunucudaki veri hâlâ eski senaryo: **44 kişilik kadro**, göçle blok
kaydına çevrilmiş 3.051 atama. Tur 4/5'in 30 kişilik senaryoları yalnızca
üreteçten gelir.

### Geri dönüş kullanılmadı

Hiçbir adımda geri alınmadı. Gerekseydi: `alembic downgrade e7b2c4915d80`
(geri alma yazılı ve denenmiş), tutmazsa
`pg_restore -c -d "$PGURL" /opt/vardiya/yedek/vardiya-20260813-1928-tur6oncesi.dump`.

---

## 2026-08-13 — Tur 6: Saat Görünümleri ve Arayüz — **BİTTİ**

Kaynak: `docs/turlar/CLAUDE_CODE_PROMPTU_TUR6.md`. Altı iş, hepsi bitti.
Çalışma `tur6-saat-gorunumleri` dalında yürüdü.

Doküman sürümleri turun başında doğrulandı: Charter **1.4**, SRS **1.21**,
SDD **1.28**, Backlog **1.18** — dördü de taşıyor. (SDD'nin revizyon
tablosunda satır SIRASI bozuk: ... 1.24, 1.25, **1.27**, **1.28**, **1.26**.
İçerik eksik değil, yalnızca son üç satır sıra dışı; en yüksek sürüm 1.28.)

### İş 1 — Gün ızgarası

Satırlarda personel, sütunlarda seçili günün yirmi dört saati
(`components/GunIzgarasi.tsx`). Blok, saat hücrelerinin ÜZERİNDE tek parça
bir şerit olarak durur — hücreler yalnızca ızgara çizgisi ve sürükleme
hedefi. Ayrım görsel değil anlamsal: blok tek bir karardır (SRS TD-13) ve
yirmi dört ayrı boyalı kutu, kataloglu sürümün "vardiya dizilimi"
görüntüsünü geri getirirdi.

**Gece yarısını aşan blok** başladığı günde sağ kenara dayanır (köşe açık,
kenarlık yok, `›` işareti), ertesi gün sol kenardan başlar (`‹`). İki günde
de etiket bloğun TAMAMINI yazar ("20.00–06.00"). "20.00–24.00" ve
"00.00–06.00" yazmak, modelin tam olarak yasakladığı iki-blok görüntüsünü
ekranda üretmek olurdu. Gün toplamı bloğun BAŞLADIĞI güne yazılır (TD-1);
ertesi günün satırında altı saat görünür ama toplamına girmez.

Geometri `lib/blok.ts`te tek yerde: `gunParcasi` / `gununParcalari`. Gün
ızgarası, hafta şeridi ve yazdırma üçü de oradan okur; ikinci bir çözümleme
yazılmadı.

### İş 2 — Hafta şeridi ve **DOM ÖLÇÜMÜ**

`components/HaftaSeridi.tsx`. Her gün hücresi yirmi dört dilimlik mini
şerittir ve **tek öğeyle** çizilir: dilimler bir CSS gradientinin sert
duraklarıdır (`lib/saatRengi.ts`, `saatGradyani`).

**Ölçüm — otuz personel × yedi gün (210 hücre), jsdom, tam ağaç:**

| Çizim yolu | DOM düğümü |
|---|---|
| Bugünkü hâli (gradient, hücre başına 1 düğüm) | **574** |
| Dilim başına ayrı düğüm olsaydı | ~5.400 (yalnız dilimler 210 × 24 = 5.040) |

Ölçüm testle kilitlendi (`HaftaSeridi.test.tsx`: düğüm sayısı < 1.000 ve
210 şerit gerçekten çizilmiş). Dilimler ayrı öğelere bölünürse test düşer.

### İş 3 — Renk saatin kendisinden · **YENİ RENK BANDI**

Kategorik üç ton kalktı. `lib/vardiyaRenk.ts` silindi; yerine
`lib/saatRengi.ts` geldi.

**Bandın tanımı** (`docs/tasarim/TASARIM_REFERANSI.md` sürüm 4'ün vardiya
rampasının yerine geçer — kanonik doküman değil, proje yürütücüsü
işleyecek):

```
aydinlik(saat) = (1 − cos(2π · (saat − 1) / 24)) / 2      → 0…1
renk(saat)     = lerp(#2F3A38, #E9E7D9, aydinlik(saat))
```

- Uçlar mevcut paletten: en koyu gece `--vardiya-gece` **#2F3A38**, en açık
  gündüz `--vardiya-gunduz` **#E9E7D9**. Yeni bir palet uydurulmadı.
- Dip nokta **01.00**, tepe **13.00**. Dip, gece penceresinin (20.00–06.00,
  TD-2) ORTASINA konuldu; kenarına konsaydı 20.00 ile 05.00 farklı koyulukta
  çıkardı, oysa ikisi de gecenin kenarıdır.
- `--vardiya-aksam` (#C7CEC0) artık kullanılmıyor — bandın 16.00 civarındaki
  değeri onun yerini tutuyor.
- Bandın 24 basamağı modül yüklenirken bir kez hesaplanır; beş binden fazla
  renk sorgusunda kosinüs tekrar çalışmaz.

Örnek basamaklar: `00 #323d3b` · `01 #2f3a38` · `06 #747a74` · `08 #a4a79d`
· `12 #e6e4d6` · `13 #e9e7d9` · `16 #cecec1` · `20 #747a74` · `23 #3b4643`.

**Renk tek başına bilgi taşımıyor.** Şeridin üzerinde saat aralığı metni
durur (`blokErisilebilirEtiket`, aynı metin `aria-label`de). Kilitli blok
RENKLE değil **eğik tarama** + aksan dış çizgiyle işaretlenir
(`KILIT_DOKUSU`); kapsama açığı **▲ + sayı** ile — şekil, renk körlüğünde ve
siyah-beyaz yazdırmada da ayrışır. Şerit metni kendi yarı saydam zeminini
taşır (`ETIKET_ZEMINI`): aynı şerit hem #2F3A38 hem #E9E7D9 taşıyabildiği
için tek bir mürekkep rengi baştan sona okunmuyor.

Çalışan paneli de aynı banda taşındı — "Gündüz / Akşam / Gece" rozeti ve üç
kutulu lejant kalktı. Aynı vardiyanın yöneticide ve çalışanda farklı
okunmaması için renk iki panelde de aynı fonksiyondan geliyor.

### İş 4 — Sürükleyerek blok tanımlama

Gün satırında sürükleme bloğu tanımlar; var olan bloğun iki kenarından da
uzatma/kısaltma çalışır. Bırakıldığında panel doldurulur ve **doğrulama
isteği** gönderilir — değişiklik uygulanmaz, "Uygula" arada durur.

`asgari_blok_saat` (H1) ve `azami_gunluk_saat` (H9) **kural kataloğundan**
okunur (`lib/kuralParametre.ts`), koda gömülmez; kullanıcı parametreyi
değiştirdiğinde ızgara yeni sınırı gösterir. **Pasif kural sınır koymaz.**
Sınır sürükleme SIRASINDA görünür: önizleme kırmızıya döner ve nedenini
yazar ("Asgari blok 4 saat (H1)").

Tek tık blok tanımlamaz, yalnızca satırı seçer — bir saatlik blok üretip
ardından "asgari dört saat" diye reddetmek, kullanıcının yapmadığı bir
işlemi ona geri okumak olurdu.

### İş 5 — Yazdırma ve CSV

Yazdırılabilir görünüm artık **gün ızgarası**: her gün kendi sayfasında
başlar (`.yazdirma-sayfa-basi`), bir günün personeli sayfaya sığmadığında
tablo bölünür ve **saat başlığı `thead`de olduğu için her sayfada yeniden
basılır**. Şeridin üzerinde saat aralığı ve nokta kısaltması METİN olarak
durur: tarayıcı arka plan basmayabilir, kâğıtta kalan tek şey odur.

CSV'de `baslangic`/`bitis` saat metninden **tam ISO damgasına** çevrildi.
Dosyanın okuyucusu makinedir ve `tarih` sütununun yanında "20.00; 06.00"
gören bir okuyucu bitişin ertesi güne düştüğünü çıkaramaz — gece yarısını
aşan blok tam da bu dosyada görünmez oluyordu.

Üçüncü kopya çıkmadı: `saatEtiketi`in `talepAraligi.ts`teki ikinci tanımı
`blok.ts`e katlandı, yazdırma ızgaranın biçimlendiricilerini çağırıyor.

### İş 6 — Kural ekranı ve analiz

**Kural ekranına kod eklenmedi** ve gerekmedi: ekran parametreleri
katalogdan genel olarak çiziyor, `asgari_blok_saat` ve `gece_esigi_saat` de
göçle (`f2a8c561d94b`) kural kayıtlarına eklenmişti. Varsayım teste
çevrildi (`TanimlarEkrani.test.tsx`): ikisi de görünüyor, düzenlenebiliyor
ve onay kutusundan geçerek kaydediliyor.

**Adalet grafiğinin referansı havuz ortalamasından kişiye düşen ADİL PAYA
geçti** (SRS S2/S3). Gece ve hafta sonu artık ayrı iki grafik: havuzları da
hedefleri de farklı, iki hedefi tek yığılmış çubuktan okumak mümkün değil.
Gösterilen sapma çözücünün kendi formülü — `max(saat − ⌊pay⌋, ⌈pay⌉ − saat,
0)` — böylece ceza dökümü ile grafik aynı çizelge için farklı sayı söylemez.

Saat dengesi tablosunun "HEDEF" sütunu **"ADİL PAY"** olarak adlandırıldı;
o sütun Analiz servisi yazıldığından beri S4'ün adil payıydı ve "hedef"
demek onu sözleşme saati gibi okutuyordu.

### Backend'e dokunuldu — tek yer, ek alan

Tur backend'e neredeyse hiç dokunmamayı istiyordu. Bir yerde gerekti ve
nedeni şu: adalet grafiğinin referansı için gereken `pay_gece[p]` /
`pay_hs[p]` sunucuda **zaten hesaplanıyor ama atılıyordu** —
`Baglam.uygun_havuz` payları hesaplayıp yalnızca "payı sıfırdan büyük
olanlar" kümesini döndürüyor. Arayüz elinde sayılarla kalınca referans
olarak havuz ortalamasını çizmek zorundaydı, yani S2'nin açıkça reddettiği
ölçüyü.

Değişiklik ikisi: `KisiSayisiOku`ya `pay: float | None = None` alanı
eklendi (var olan tüketiciler için kırıcı değil), Analiz servisi
`uygun_havuz` yerine `adil_paylar`ı doğrudan çağırıp payı da yazıyor. Tanım
yine `Baglam.adil_paylar`da tek yerde; ikinci bir geçiş de yapılmıyor.
**Göç yok, şema değişikliği yok.**

### Tasarımdan sapma — Çizelge ekranındaki nokta EKSENİ kaldırıldı

Ekranda "Personel / Nokta" görünüm anahtarı vardı; yerini "Gün / Hafta"
aldı. Gerekçe: SDD 6.3.3 (sürüm 1.28) ekranın iki görünümünü ÇÖZÜNÜRLÜK
üzerinden tanımlıyor ve listesinde Görünüm Anahtarı yok. Nokta ekseni,
satırların nokta × vardiya TİPİ olduğu kataloglu sürümden kalmaydı ve Tur
5'te zaten yarısını kaybetmişti (satır doğrudan noktaya inmişti).

Kayıp telafi edildi: gün ızgarasına **nokta süzgeci** eklendi. "Bu noktada
bugün kim var" sorusu artık orada yanıtlanıyor ve yanıt saat çözünürlüğünde
— eski eksenin veremediği bilgiyle birlikte. Nokta eksenini geri
istiyorsanız söyleyin; gün ızgarasında nokta satırları alt satırlara
yığılarak çizilebilir.

### DOKÜMAN BORCU — **üçü de açık**

1. **SRS 7.2 — çizelge dışa aktarma sütunları.** Doküman hâlâ
   `vardiya_tipi` ve `gece_mi` yazıyor; kod Tur 5'ten beri
   `baslangic`/`bitis` + `gece_saat` üretiyor. Bu turda ikisi daha
   değişti: `baslangic`/`bitis` artık saat metni değil **tam ISO damgası**.
   Kapsama açığı dosyasının sütunları da `vardiya_tipi` yerine
   `baslangic`/`bitis` + `tur`/`kisi_sayisi`.
2. **SDD 6.3.3 — kaldırılan Görünüm Anahtarı ve eklenen nokta süzgeci.**
   Yukarıdaki sapma. Ayrıca gün ızgarasının kapsama satırının saat
   düzeyinde olduğu ve işaretin şekil taşıdığı yazılı değil.
3. **Ek B — `KisiSayisi` yanıtına `pay` alanı eklendi.** Uç nokta sayısı
   değişmedi, `GET /api/analiz/{surum_id}` yanıtının şekli değişti.

### Bilinen sınır — kapsama açığı dosyasında gece yarısı

Çizelge CSV'si ISO damgasına geçti; **talep sapması dosyası** hâlâ `tarih` +
saat metni taşıyor (`00.00`, `08.00`). Kapsama açığı kaydı sunucuda TIME
sütunlarında duruyor ve saat dilimi ofseti taşımıyor; ondan bir ISO damgası
kurmak ofseti uydurmak olurdu. Gece yarısını aşan bir açık aralığı bu
dosyada hâlâ okunamaz. Düzeltmenin yeri sunucu tarafı (aralığa bitiş tarihi
ya da ofset eklemek) ve bu tur backend'e dokunmama kuralının içinde
kalmadı.

### Sen ne göreceksin — **şu üç ekranı kendi gözünle aç**

Ekranı tarayıcıda yine göremedim (5173 portu başka projede, ekran girişin
arkasında). Testler kanıt yerine geçiyor ama **jest değil**: aşağıdakiler
test edilmedi ve gözle bakılmalı.

1. **Çizelge → Gün.** Sürükleyerek blok tanımla ve kenarından uzat.
   jsdom düzen (layout) hesaplamadığı için imlecin gerçekten hangi saatin
   üzerinde olduğu test edilemiyor; test hücrelere doğrudan olay göndererek
   jestin MANTIĞINI doğruluyor. Bakılacak: sürükleme akıcı mı, önizleme
   doğru hücrelerde mi, kenar tutamakları 6px genişlikte tutulabiliyor mu.
2. **Çizelge → Gün, gece yarısını aşan bir blok.** Şeridin iki günde de
   tek blok gibi okunduğu ancak gözle doğrulanabilir: köşe açıklığı,
   `‹ ›` işaretleri ve etiketin sığması. Dar sütunda etiket kırpılıyorsa
   söyle.
3. **Çizelge → Yazdır.** Yatay A4 önizlemesi. Gün ızgarası sayfaya sığıyor
   mu, saat başlığı ikinci sayfada tekrarlanıyor mu, arka plan basımı kapalı
   olduğunda şeritler hâlâ okunuyor mu — üçü de yalnızca gerçek baskı
   önizlemesinde görülür.

Ayrıca **Analiz** ekranındaki iki yeni adalet grafiğine bakmanı öneririm:
referans çizgisi (dikey ince çizgi) çubukların arasında kaybolabiliyor mu?

### Turun bitiş kontrolü

- [x] `tsc -b` temiz, `oxlint` temiz (4 uyarı, hepsi turdan önce vardı ve
      `react/only-export-components` — dosya başına bir bileşen kuralı)
- [x] `vitest` **231 test geçiyor** (turdan önce 162; 69 yeni test).
      Ters/karışık sırada da geçiyor (`--sequence.shuffle`)
- [x] `pytest` tam takım **341 test geçiyor** (10 dk 26 sn)
- [x] `ruff check` ve `ruff format --check` temiz
- [x] Hafta şeridinin DOM maliyeti ölçüldü ve yukarıda
- [x] Yeni renk bandı yukarıda (tasarım referansına proje yürütücüsü işleyecek)
- [ ] `git status` temiz — dal `main`e alınmayı bekliyor

### Bekleyen göçler — dağıtım yapılmadı

Bu tur göç üretmedi. Tur 5'in göçü (`f2a8c561d94b`) hâlâ bekliyor; durumu
değişmedi.

---

## 2026-08-13 — Tur 5: Gerçek Saatlik Model — **BİTTİ**

Kaynak: `docs/turlar/CLAUDE_CODE_PROMPTU_TUR5.md` ve devamı
`docs/turlar/TUR5_DEVAM.md`. Yedi iş. Çalışma `tur5-saatlik-model` dalında
yürüdü, sonunda `main`e alındı.

Tur ortasında bir kez **durdu**: İş 1'in sondajı yanıltıcı çıkmıştı ve karar
istendi. Devam belgesi üç seçenekten ikisini onayladı, ölçüm yeniden koşuldu
ve tur tamamlandı. Aşağıda önce turun ilk yarısı, sonra "Durma noktası ve
sonrası" başlığı altında devamı yazılı.

Doküman sürümleri turun başında doğrulandı: Charter **1.4**, SRS **1.19**,
SDD **1.27**, Backlog **1.16** — dördü de taşıyor.

### İş 1 — prototip ölçümü: **karar kuralı geçildi, devam**

Karar kuralı: 40 × 28 ölçeğinde ilk uygun çözüme ulaşma süresi 30 saniyeyi
aşarsa dur. **Aşmadı — 5,0 saniye.** Tam uygulamaya geçiliyor.

Sondaj `backend/scripts/saatlik_prototip.py`. Modelde yalnızca mutlak saat
ekseni, `bas` göstergesi, günde tek başlangıç, asgari süre, nokta sabitliği,
günlük tavan ve S1 var; başka kural yok. Talep SRS 3.3.4'ün Müracaat'sız
tablosudur ve kadroya göre `P/40` ile ölçeklenir — aksi hâlde on kişilik bir
kadro kırk kişilik talebi karşılamaya çalışır ve ölçülen şey çözüm süresi
değil kapsama açığı olurdu. Şef havuzu `max(3, 7·P/40)`: kesintisiz
doldurulan bir nokta haftada 168 kişi-saat ister, günlük tavan on bir
saattir, dolayısıyla üç kişinin altındaki bir havuz noktayı hiçbir çizelgeyle
kapatamaz.

Arama işçisi SDD 3.4.3 referansına sabit (3), makine macOS arm64 / 10
çekirdek — `kabul_olcumu.py` ile aynı sözleşme.

| Ölçek | Değişken | Kurma | **İlk uygun** | Optimale | Sonuç |
|---|---|---|---|---|---|
| 10 × 7 | 7.224 | 0,10 sn | **0,25 sn** | 0,45 sn | optimal, ceza 0 |
| 20 × 14 | 28.224 | 0,38 sn | **1,12 sn** | 4,63 sn | optimal, ceza 0 |
| 30 × 28 | 84.000 | 1,15 sn | **3,71 sn** | 28,63 sn | optimal, ceza 0 |
| 40 × 28 | 112.224 | 1,69 sn | **5,02 sn** | 56,03 sn | optimal, ceza 0 |

40 × 28 iki kez daha koşuldu: ilk uygun 4,93 ve 5,08 sn; optimale 44,6 ve
45,2 sn. İlk uygun süre kararlı.

**Ölçüm boşuna hızlı olmasın diye çıkan çizelge denetlendi** (`--denetle`).
Sondaj hızlı çözüyorsa iki açıklama vardır — formülasyon ucuzdur ya da kısıt
yanlış yazıldığı için model gerçekte kolaydır — ve ikisini ayırmanın tek yolu
sonuca bakmaktır. Dört ölçekte de: asgari süreden kısa blok yok, günlük
tavanı aşan blok yok, gün içinde ikinci blok yok, blok içinde nokta değişimi
yok. 40 × 28'de **96 blok gece yarısını aşıyor** — mutlak eksenin var oluş
nedeni tam olarak bu.

### İki sapma — nedenleri önce

**1. Günlük saat, duvar saatine değil bloğun başladığı güne yazılıyor.**
SRS H1 ve H9 günlük toplamı `Σ_{s ∈ gün d} z[p,s]` diye yazar; H9'un metni
ise aynı paragrafta "gece yarısını aşan bloğun saatleri başladığı güne
sayılır (TD-1); ertesi günün tavanı bu saatlerle dolmaz" der. İkisi aynı şey
değildir ve formülün duvar saati okunması **iki kuralı da bozar**:

- **H9 blok uzunluğunu sınırlayamaz.** 20.00–08.00 bloğu duvar saatinde
  4 + 8 saattir; ikisi de on bir tavanın altında kalır ve on iki saatlik blok
  geçer.
- **H1'in asgari süresi akşam başlangıçlarını yasaklar.** 21.00'de başlayan
  bir blok o güne yalnızca üç saat bırakır ve `≥ 4 · bas` kısıtı düşer —
  oysa gece kapsamasının ihtiyaç duyduğu bloklar tam olarak bunlardır.

Metin normatiftir, gösterim kısaltmadır: "gün d" bloğun sayıldığı gündür.
Gün başına saat bu yüzden devralınan saatler çıkarılıp taşan saatler
eklenerek hesaplanıyor (`devir[p,s]` göstergesi: "bu saat çalışılıyor ve
önceki günde başlamış bir bloğa ait"). Maliyeti ölçüme dahil — tam uygulama
da aynı yapıyı taşıyacak. Bu, aşağıdaki doküman borcunun birinci maddesidir.

**2. H9 sondaja dahil edildi.** Prompt "diğer kuralları ekleme" diyor;
günlük tavan olmadan çözücü günde yirmi dört saat çalıştırabilir, kapsama
bedelsiz kapanır ve ölçülen süre gerçek modelin süresi olmaz. H9 ayrıca
SRS 3.3.1'de asgari blok süresiyle **aynı üç parametreli çerçeve** içinde
tanımlı: alt sınır ve üst sınır birlikte bloğun çerçevesini çizer.

### K1 için erken uyarı — optimale ulaşma 45–56 sn

Karar kuralı ilk uygun çözümü ölçer ve rahat geçiyor. Ama **optimale ulaşma
süresi 40 × 28'de 45–56 saniye** ve K1'in eşiği 60 saniye. Tur 4'te aynı
kriter 1,01 saniyeydi (blok kataloğuyla). Saat modeli optimallik kanıtında
yaklaşık **elli kat** pahalı ve tam modelde on beş kural daha eklenecek.

Bu bir durdurma nedeni değil — K1 pratikte zaman limitli bir aramanın
sonucunu ölçer ve ilk uygun çözüm beş saniyede geliyor — ama turun kabul
ölçümünde K1'in **ne ölçtüğüne** dikkat edilecek: "60 saniyede optimal" ile
"60 saniyede kabul edilebilir çözüm" aynı şey değil ve saat modelinde ikisi
ilk kez ayrışıyor.

### İş 2 — göç: blok kavramı kalktı

Tek göç (`f2a8c561d94b`). `atama` blok kaydına geçti
(`baslangic_zamani`/`bitis_zamani`), `vardiya_tipi` tablosu ve
`personel.sabit_vardiya_tipi_id` düştü, tercih zaman aralığına çevrildi,
`asgari_blok_saat` = 4 ve `gece_esigi_saat` = 4 kural kayıtlarına eklendi.

**Dönüşüm sayılarak doğrulandı** ve göç eşitliği bozulursa hata verip
duruyor. Geliştirme veritabanında: önce 604 satır / 5.032 kişi-saat, sonra
604 satır / 5.032 kişi-saat. Geri alma yazıldı ve **denendi**: katalog
veriden yeniden türetiliyor (atamalarda fiilen geçen aralıklar), aynı 604
satır ve 5.032 kişi-saat geri geliyor. Sıfırdan da koşuyor (`downgrade base`
→ `upgrade head` temiz).

**H1'in güvencesi değişti ve bu bir testle kilitlendi.** Yeni benzersizlik
anahtarı `(surum_id, personel_id, baslangic_zamani)`; aynı günde farklı
saatte başlayan ikinci bir bloğu veritabanı **yakalamıyor**.
`test_ayni_gunde_farkli_saatte_ikinci_blogu_veritabani_yakalamaz` kaybı
ölçüyor; manuel düzenleme yolu o günün bloklarını silip tek blok yazarak
kuralı yapısal olarak taşıyor.

### İş 3, 4, 5, 6 — model, toplama, kurallar, gösterim verisi

Model `z[p,s]` / `x[p,s,n]` üzerine kuruldu; `bas` başlangıç göstergesi ve
`devir` devralma göstergesi eksenin parçası. Çözücü çıktısı yazma anında
bloklara toplanıyor ve toplama **kapsama açığı kayıtlarının kullandığı aynı
yardımcıdan** geçiyor (`ardisik_saatleri_grupla`); tek fark
`gun_sinirinda_kes` parametresi — gece yarısını aşan blok tek kayıtta duruyor.

Müracaat kalktı: iki nokta, iki yetkinlik, Güvenlik hafta içi 08.00–24.00
talebi 9. Haftalık toplam 1.152 kişi-saat **değişmedi** ve bunu
`test_yuk_gostergesi` kilitliyor.

**Çözücü–doğrulayıcı uyum testi 24/24 temiz** ve yol üstünde iki gerçek hata
yakaladı:

1. **Değişken eleme H1'in nokta sabitliğini deliyordu.** Kısıt geriye dönük
   yazılıyor ve `x[p,s,n]` bulunamadığında atlanıyordu; talebi biten bir
   noktanın değişkeni elendiği için kısıt hiç kurulmuyor ve personel
   **çalışmayı kesmeden** nokta değiştirebiliyordu. Çözücü bunu buldu:
   14.00–16.00 bir noktada, 16.00–24.00 başka noktada, tek kesintisiz
   çalışma. Kısıt ileri yönlü kuruldu ve eksik değişken sıfır sayılıyor.
2. **Isıtma penceresi tümüyle sabit değildi.** Atanmış saatler 1'e
   çekiliyordu ama boş saatler **serbest** kalıyordu; çözücü geçmiş bir
   haftada olmayan çalışma uydurabiliyor ve o uydurma H2/H3/H4
   pencerelerini dönemin ilk günlerinde yanlış besliyordu. TD-5 açık: o
   atamalar karar değişkeni değildir.

### Durma noktası — İş 1'in sondajı yanıltıcı çıktı

**Turun asıl bulgusu bu ve karar burada istendi.**

İş 1'in sondajı üç kuralla (H1, H9, S1) ölçtü ve 40 × 28'de ilk uygun çözümü
**5,0 saniyede** buldu. Tam model **on dokuz kural** taşıyor ve ölçüm
tamamen başka:

| Ölçek | Değişken | Kısıt | İlk uygun | 300 sn'de |
|---|---|---|---|---|
| 30 × 28 (sıkışık senaryo) | 106.603 | 229.138 | **45,6 sn** | optimal değil |

Ara ölçümler, iyileştirmelerin sırasıyla ne kazandırdığını gösteriyor:

| Durum | İlk uygun (30 × 28) |
|---|---|
| İlk hâl | 60 sn'de **bulunamadı** |
| Gün başına türev tek değişkene bağlandıktan sonra | 128 sn |
| Isıtma penceresi tümüyle sabitlendikten sonra | **45,6 sn** |

Kural bazında sondaj (taban = H1+H9+S1, 30 × 28): hiçbir kural tek başına
patlatmıyor, **S4** en pahalısı (3,8 sn → 19,6 sn), gerisi 4–7 sn arası.
Yük **birikimli**.

**İki iyileştirme yapıldı ve ikisi de tesadüfi değil, yapısal:**

1. **Gün başına türetilmiş büyüklükler tek değişkene bağlandı.**
   `blok_saati` 48 terimli bir ifade ve **altı kural** onu okuyor; her
   çağrıda yeniden açıldığında aynı bilgi modele yüz binlerce kez
   kopyalanıyordu.
2. **Isıtma penceresi sabitlendi** (yukarıdaki 2 numaralı hata). Arama
   uzayının beşte biri.

Bu noktada 40 × 28 ölçeğinde K1 ölçümü **koşulmamıştı**; 30 × 28'de ilk uygun
çözüm 45,6 saniye olduğuna göre 40 × 28'in 60 saniyenin altında kalması
muhtemel görünmüyordu. **Karar istendi.** Formülasyonda gevşetilebilecek üç
yer sıralandı, maliyeti artan sırayla:

- **`devir` göstergesinin penceresi.** Bugün her saat için üretiliyor
  (22.680 ikili değişken). Bir blok günlük tavanı (11 saat) aşamadığına
  göre ertesi güne en fazla on saat taşabilir; gösterge yalnızca günün ilk
  on bir saati için gerekli. Kazanç ~%55 daha az `devir` değişkeni.
  **Bedeli:** eksen H9'un parametresine bağlanır.
- **S4'ün bölme kısıtı.** `add_division_equality` ceza dökümünü doğal
  birimde raporlamak için var; S2/S3'ün taban/tavan yöntemine geçirilirse
  bölme kalkar. **Bedeli:** S4'ün cezası kesirli payların arasında sıfıra
  düşer — SRS'in S4 tanımını değiştirir.
- **Nokta sürekliliği** (M3'ün ve SAATLIK_MODEL_KARARLARI'nın "ilk
  gevşetilecek yer" dediği kısıt). Kaldırılırsa blok içinde nokta
  değişebilir; sahada anlamsız ama model belirgin biçimde ucuzlar.

Ölçmeden hangisinin ne kazandıracağı söylenemezdi ve ikisi tanımı
değiştiriyordu; bu yüzden denenmeden karar istendi.

---

### Devam kararı ve uygulanan iki seçenek

`docs/turlar/TUR5_DEVAM.md`: **1 ve 2 uygulanacak, 3'e dokunulmayacak.**

**Seçenek 1 — `devir` göstergesinin penceresi daraltıldı.** Gösterge artık
günün yalnızca ilk `azami_gunluk_saat` saati için üretiliyor. Bu bir tanım
değişikliği değil: bir blok H9'un tavanını aşamadığına göre ertesi güne o
tavandan fazla taşamaz, dolayısıyla eksik bırakılan göstergeler zaten her
çözümde sıfırdır — **çözüm kümesi aynı**. Eşik kuralın kendi parametresinden
okunuyor (`_azami_gunluk_saat`), sabit yazılmadı; H9 kapalıysa 24'e düşüyor,
yani gevşetme kuralın varlığına bağlı. SDD 5.3'e işlendi.

**Seçenek 2 — S4 taban/tavan yöntemine geçti.** `add_division_equality` ve
`S4_OLCEK` kalktı; sapma artık `sapma ≥ toplam − ⌊pay⌋` ve
`sapma ≥ ⌈pay⌉ − toplam` ile kuruluyor, S2/S3 ile **aynı yöntem**. Onay
başarım gerekçesiyle değil **tutarlılık** gerekçesiyle verildi: kesirli
payların arasında ceza sıfıra düşer, bu S4'ün tanımını değiştirir ve
değişiklik SRS 1.20'ye yazıldı. `s4_hedef_paylari_x10` → `s4_hedef_paylari`
(doğal saat birimi).

**Seçenek 3 — nokta sürekliliği: dokunulmadı.** Ürün kararı. Devam belgesi
ayrıca kısıtın *gerçekten uygulandığının* doğrulanmasını istedi — değişken
eleme onu bir kez sessizce iptal etmişti (yukarıdaki 1 numaralı hata). İki
test bunu kilitliyor: biri talebi dönem ortasında biten bir nokta kurup
değişkenin elendiği yerde kısıtın hâlâ kurulduğunu, diğeri ısıtma
penceresinin boş saatlerinin sıfıra sabitlendiğini ölçüyor.

### Ölçüm — devam belgesinin istediği üç ölçek

Arama işçisi 3 (SDD 3.4.3), macOS arm64, 180 sn limit:

| Ölçek | Değişken | Kısıt | **İlk uygun** | Not |
|---|---|---|---|---|
| **30 × 7** | 39.622 | 84.130 | **1,0 sn** | Gerçek kullanım — dönem varsayılanı bir hafta (Charter 2.5) |
| **30 × 28** | 94.284 | 192.278 | **5,0 sn** | Karşılaştırma noktası — durma anında 45,6 sn |
| **40 × 28** | 126.674 | 260.808 | **16,3 sn** | K1'in stres ölçeği |

Durdurma eşiği 60 saniyeydi; **aşılmadı**, tur devam etti. Asıl kullanım
ölçeğinde (30 × 7) çözüm bir saniyede geliyor.

### Kabul ölçümü — `scripts/kabul_olcumu.py` saat modelinde

Betik yeniden yazıldı. K3'ün eşiği artık katalogdan türetilmiyor,
**Charter 1.4'ün sekiz gece saati** doğrudan yazılı; referans havuzlar
Müracaat'sız kadroya göre 9 şef + 31 güvenlik.

| Çözücü limiti | K1 | K2 | K3 | K4 | K5 | Sonuç |
|---|---|---|---|---|---|---|
| 60 sn | 8,68 sn ✔ | 0 ✔ | **30,00** ✘ | 167 açık ✔ | 0,099 sn ✔ | 4/5 |
| 300 sn | 8,33 sn ✔ | 0 ✔ | **12,00** ✘ | 49 açık ✔ | 0,064 sn ✔ | 4/5 |
| **900 sn** | 8,72 sn ✔ | 0 ✔ | **7,00** ✔ | 47 açık ✔ | 0,070 sn ✔ | **5/5** |

**K1 limitten bağımsız geçiyor** — kendi ölçtüğü şey ilk uygun çözüme ulaşma
süresi ve o üç koşuda da 8–9 saniye. Limit yalnızca çözümün **kalitesini**
etkiliyor, ki K3 tam olarak kalite ölçüyor.

**K3 yakınsama sınırlı, yapısal değil.** 30 → 12 → 7: sapma çözücü süresiyle
tekdüze düşüyor ve 900 saniyede eşiğin altına iniyor. Betiğin ulaşılabilirlik
teşhisi de bunu söylüyor — her havuz hedefine erişebiliyor (31 kişilik havuz
kişi başı 42,6 gece saatine kadar, 9 kişilik havuz 177,8'e kadar), yani engel
kadro değil arama. Bu, **Tur 9'un ağırlık kalibrasyonuna** giden bir gözlem:
S3'ün ağırlığı gece dengesini daha erken sıkıştırırsa 60 saniyede de inebilir.
Ağırlıklara bu turda dokunulmadı (devam belgesinin açık talimatı).

**K4 senaryosu düzeltildi.** Saat modelinde beş şefin izinli olması açık
üretmiyordu — çözücü blokları uzatarak kapatıyordu. Senaryo dokuz şefin
**yedisini** izne çıkarıyor ve aritmetiği docstring'e yazılı: nokta haftada
168 kişi-saat istiyor, kalan iki kişi H5/H6 altında en çok 132 saat verebiliyor,
yani açık **kaçınılmaz**.

### İş 7 — arayüz

`frontend/src/lib/blok.ts` tek okuma yeri: blok ISO damgasından okunuyor,
`new Date` kullanılmıyor — tarayıcının saat dilimi ızgarayı kaydıramaz.
Çizelge ızgarası `baslangic_zamani`/`bitis_zamani` okuyor, düzenleme formunda
vardiya tipi seçicisi yerine **başlangıç ve bitiş saati** seçicileri var,
nokta görünümünde vardiya tipi ekseni kalktı. Tanımlar ekranından Vardiya
Tipi sekmesi ve Sabit Vardiya alanı silindi.

`EK_B_UC_NOKTALAR.md` yeniden üretildi: altı `vardiya-tipi` ucu düştü,
**74 → 68**; `uc_noktalari_listele.py --denetle` 68 = 68 diyor.

### Turun kapanış durumu

- Backend **341 test geçiyor** (316 + 24 örnekli uyum testi + ağırlık
  kalibrasyonu). `test_agirlik_kalibrasyonu`'nun çözücü limitleri geçici
  olarak 90/180'e çıkarılmıştı, **60/90'a geri alındı** ve o hâliyle geçiyor.
- Frontend `tsc -b` temiz, **162/162** vitest, oxlint'te yalnızca önceden
  var olan uyarılar.
- Uyum testi (SDD 3.2.1) `optimal` yerine `optimal | uygun` kabul ediyor:
  test **mutabakat** ölçüyor, optimallik değil, ve saat modelinde optimallik
  kanıtı belirgin biçimde pahalı.
- Kanonik belgeler `BOTAS_Vardiya_Cizelgeleme_*` → **`VARDIS_*`** olarak
  `git mv` ile yeniden adlandırıldı, atıflar güncellendi.
- Sunucuya dağıtım **yok**; `push`/`remote` **çalıştırılmadı**.

### DOKÜMAN BORCU — iki madde

1. **SRS H1 / H9 — `Σ_{s ∈ gün d} z[p,s]` gösterimi belirsiz.** Sembol duvar
   saatini mi bloğun sayıldığı günü mü gösterdiğini söylemiyor; H9'un metni
   ikincisini söylüyor, formül birincisi gibi okunuyor. Uygulama metne
   uyuyor. Gösterimin (SRS 4.1) "gün d" tanımını açıkça bloğun başlangıç
   gününe bağlaması gerekiyor.
2. **SRS 3.3.6 — kadro tablosu Müracaat satırını taşıyor.** Yetkinlik
   havuzları tablosunda "Müracaat Görevlisi" hâlâ duruyor; 3.3.2 ve 3.3.3
   noktayı kaldırdı. Toplam satırı da (144 kişi-vardiya / 29 kişi) blok
   sayısına dayanıyor ve blok kavramı kalktı.

---

## 2026-08-13 — Tur 4: Kural Kataloğu — **BİTTİ**

Kaynak: `docs/turlar/CLAUDE_CODE_PROMPTU_TUR4.md`, `TUR4_DEVAM.md` ve
`TUR4_K3_KARARI.md`. Sekiz iş; hepsi bitti. Çalışma `tur4-kural-katmani`
dalında yürüdü — turun ilk yarısında yarım kalan kural katmanı `main`e
bulaşmasın diye.

Doküman sürümleri turun üç noktasında doğrulandı: başta SRS 1.16 / SDD
1.26 / Backlog 1.12 / Charter 1.2; devam yönergesiyle Backlog **1.13**;
K3 kararıyla Charter **1.3** / SRS **1.17** / Backlog **1.14**.

### İş 1 — testler arası veri sızıntısı (B-22)

Her testten **önce** çalışan bir fikstür tanım/girdi/sonuç tablolarını
uygulamanın kendi silme yolundan boşaltıyor. Temizlik testten önce, sonra
değil: başarısız bir testin verisi incelenebilsin.

**Sızıntı önce ölçüldü.** `test_analiz_api` + `test_tanim_api` normal
sırada 30/30 geçiyor, ters sırada bir test düşüyordu. Fikstürden sonra iki
sıra da geçiyor; tam takım ters dosya sırasında da **327/327** verdi.

### İş 2 — blok görünümü türevi kaldırıldı

`blok_gorunumu_uret` ve `Baglam.talep` yok. S2, S3 ve S4 talebi doğrudan
saat ekseninden okuyor; türevin tüketicisi kalmadı. Yük göstergesi de
kişi-vardiya sayısını bıraktı (FR-1.9): karışık uzunluklu katalogda o sayı
kataloğun bileşimine bağlıdır, talep değişmese bile değişir.

### İş 3 — H5 yeniden, H9 ve H10

45 saat artık tavan değil **eşik** (H10'un parametresi); H5 mutlak tavanı
66'ya çıktı — günlük 11 saat × altı çalışma günü, H6 ve H9'un zaten ima
ettiği sınır. H9 günü sınırlıyor ve blok kataloğu kısıtı **aynı
parametreyi** okuyor, Tur 3'teki geçici sabit silindi.

H10 fazla çalışmayı **ayrık takvim haftalarında** topluyor; hafta kümeleri
kayan pencere yardımcısından ayrı bir fonksiyonda üretiliyor (TD-14).
Karışmanın sonucu sessizdir: kayan pencerede aynı saat yedi pencereye
girer ve toplam yedi katına çıkar.

**Kural zorunlu ama modeli çözülemez yapmıyor** ve bunu söyleyen bir test
var: kotası dolmuş personel eşiğe kadar çalışmaya devam ediyor.

### İş 4 — S1'in üst sınırı esnek

Karışık uzunluklu katalogda fazla kadro **yapısaldır** — on saatlik blokla
kapatılan sekiz saatlik talep iki saat fazla üretir — dolayısıyla zorunlu
üst sınır modeli çözülemez yapardı. `fazla` değişkenleri `eksik` ile aynı
saat gruplamasından geçiyor.

`w1f` **ayrı bir kural kaydı** (S1f): kural tablosu kural başına tek
ağırlık sütunu taşıyor ve S1'in formülasyonunda iki ağırlık var —
S6/S6b'deki aynı bölme. Karar Backlog 1.13'e işlendi; gerekçe ağırlığın
Kural ekranından ayarlanabilir olması (FR-1.11).

Manuel düzenlemede fazla kadro **ceza üretmemeye devam ediyor**; iki
tarafın farklı davranması bilinçli (SRS 4.3).

### İş 5 — S2/S3 saat birimine, S6 kaymaya

`gece_saat[b] = |b ∩ [20:00, 06:00]|` tek yerde. `gece_mi` bayrağı tanımlı
alan olarak kaldı — öneri kuralı yalnızca yeni blok oluştururken
ön-dolduruyor. S6 dairesel başlangıç saati kaymasına geçti: 08.00–16.00 ile
08.00–20.00 farklı bloklar ama aynı saatte başlıyorlar ve ergonomik bir
kayma üretmiyorlar.

### K3 KARARI — eşik değil, hedef yanlıştı

Ölçüm iki ayrı sorun gösterdi ve ikincisi ağırdı: yedi kişilik Müracaat
havuzunun erişebildiği gece talebi kişi başına en fazla **22,86 saat**,
hedef 40. O havuz hedefe **hiçbir çizelgeyle** ulaşamıyordu; hangi eşik
konursa konsun kalıcı olarak sapmalı görünürdü.

**Hedef kişiye özel adil paya döndü** (SRS 1.17): her talep birimi ona
erişebilenler arasında eşit bölünüyor, kişinin hedefi kendi paylarının
toplamı. K3'ün ölçümü **34 → 1,15**'e indi ve ulaşılabilirlik teşhisi
artık "her havuz hedefe erişebiliyor" diyor.

**Eşik katalogdan türetiliyor** (Charter 1.3): katalogdaki en uzun gece
bloğunun süresi. Sabit bir saat değeri katalog her değiştiğinde elle
yeniden ölçekleme isterdi; oran ise hedef büyüdükçe gevşer, küçüldükçe
imkânsızlaşır.

Bu, aynı kalıbın **ikinci** görülüşü: önce hiç gece alamayan personel
paydada sayılıyordu, sonra kısıtlı erişimi olan havuz tek ortalamaya
vuruluyordu. İkisinde de ölçü, hiçbir çizelgeyle kapatılamayan bir sapma
raporluyordu.

### Uyum testinin yakaladığı gerçek hata

S3'ün sapma değişkeninin üst sınırı bir kişinin **fiilen taşıyabileceği**
azami yüktü; adil pay ise kadro yetersizken bunu aşabiliyor. O durumda
kısıt sınırı aşıyor ve model **çözülemez** dönüyordu — oysa kadro
yetersizliğinin doğru cevabı çizelgeyi üretip açığı göstermektir (FR-5.2).
24 rastgele örnekten biri buna denk geldi. Üst sınır artık payı da
kapsıyor; uyum testi **24/24** temiz.

### İş 6 — katalog yedi bloğa, gösterim verisi dört senaryoya

Katalog SRS 3.3.1'deki yedi blok. On iki saatlik bloklar haftalık eşiği
gerçekten aşabildiği için H10'un işlediğini gösterebilen tek yapı.

**Kadro 44'ten 30'a indi.** 44 kişide kişi başına haftalık yük 26 saatti;
kimse eşiğe yaklaşmıyor, H10 hiçbir zaman tetiklenmiyordu. 30 kişide yük
**38,4 saat** — eşiğe yakın ama altında.

| Senaryo | Açık | En yüksek hafta | Fazla çalışma | Uzun blok |
|---|---|---|---|---|
| Dengeli (Bu Hafta) | 0 | 50 sa | 32 sa (10 kişi) | 9 |
| Sıkışık | 56 | 54 sa | 149 sa (21 kişi) | 63 |
| Fazla çalışma | 17 | 54 sa | 79 sa (17 kişi) | 19 |
| Kota sınırı | 0 | 48 sa | 30 sa (10 kişi) | 9 |

Kota senaryosunda Ahmet Yılmaz'ın (devir 265, kalan 5) haftalık yükü **40
saat**: çalışmaya devam ediyor, eşiği aşamıyor. Ön kontrol bunu adıyla
bildiriyor.

**Sıkışık senaryonun çelişkisi erişilebilirliğe taşındı.** On iki saatlik
bloklar girince "kadroyu küçült" mekanizması çalışmaz oldu — kabul ölçümü
bunu sıfır açıkla yakaladı. Vardiya şefliği havuzunun beşini izne çıkarmak
blok uzunluğundan bağımsız çalışıyor: eksik olan saat değil, o noktadan
geçebilen **kişi** (H8).

Personel gerçekçi adlar taşıyor.

### İş 7 — çizelge hücresinde saat aralığı

Hücre `08–16 · GÜV` gösteriyor, renk **başlangıç saati bandından**
geliyor. Yedi bloklu katalogda "Gündüz" adını taşıyan iki blok aynı
kısaltmaya sıkışıyor ve ızgara iki farklı çizelgeyi aynı gösteriyordu.
06.00'da başlayan uzun blok gündüzden ayrı bir bantta — aynı renk olsalardı
06–16 ile 08–16 ayırt edilemezdi.

### İş 8 — ön kontrole kota bulguları

Devir kotayı aşmışsa **kesin bulgu** (H10 tek başına sağlanamaz; veri
hatası, kişinin adıyla), kalan kotası bir haftalık fazla çalışmaya
yetmiyorsa **uyarı**. İkisi de çözümü engellemiyor (K18).

### Kabul ölçümü — 5/5

| Kriter | Eşik | Tur 3 | **Tur 4** |
|---|---|---|---|
| K1 40×28 | < 60 sn | 1,01 sn | **3,36 sn** |
| K2 zorunlu ihlal | 0 | 0 | **0** |
| K3 gece adaleti | ≤ 1 gece bloğu (10 sa) | 0,61¹ | **2,85** |
| K4 eksik gösterimi | ≥1 açık | 13 aralık | **12 aralık (76 sa)** |
| K5 manuel düzenleme | < 1 sn | 0,035 sn | **0,051 sn** |

¹ Tur 3'te birim vardiya sayısıydı; sayılar doğrudan karşılaştırılamaz.

K1 üç katına çıktı (katalog ikiye katlandı) ama eşiğin yarısı olan 30
saniyenin çok altında — K17'nin "dur" koşulu oluşmadı.

### Bilinen sapma — dengeli dönemde bir miktar fazla çalışma

Dengeli dönemde on kişi toplam 32 saat fazla çalışma taşıyor; hedef "eşiğe
yakın ama altında"ydı. Ortalama 38,4 saat, en yüksek hafta 50. Sebep
**ağırlık ölçeği**: S2/S3'ün birimi saate döndüğü hâlde ağırlıkları
değişmedi, dolayısıyla S4'ün dengeleme baskısı görece zayıf. Bu
**beklenen** bir durum ve düzeltmesi Tur 8'in kalibrasyonu; bu turda
ağırlıklara dokunulmadı.

### DOKÜMAN BORCU — yok

Bu turda dört kanonik dokümana dokunulmadı; K3 kararının gerektirdiği
Charter 1.3, SRS 1.17 ve Backlog 1.13/1.14 güncellemeleri proje
yürütücüsü tarafından yapıldı ve dala alındı.

### Bekleyen göçler — dağıtım yapılmadı

Sunucu **`d1f83a6c40b2`** noktasında (Tur 3, 12.08.2026'da çıktı; Tur 2'nin
iki göçü ondan önce uygulanmıştı). Bekleyen tek göç bu turunki:
**`e7b2c4915d80`** — şemayı değiştirmez, yalnızca `kural` tablosunu
günceller: H5'in parametresini `azami_haftalik_saat` → `haftalik_mutlak_tavan`
olarak taşır ve değerini 66 yapar, H9/H10/S1f kayıtlarını ekler. Var olan
kayda dokunmaz (kullanıcının değiştirdiği bir ağırlığı geri almaz) ve iki
kez koşulabilir.

**Dağıtımda dikkat:** göç kural kayıtlarını değiştiriyor, kod ise yeni
parametre adını okuyor — ikisi birlikte gitmeli. Eski kod yeni parametreyle
`KeyError` verir, yeni kod eski parametreyle de. Dağıtım kararı proje
yürütücüsünde.


---

## 2026-08-12 — Tur 3: Saatlik Düzenin Veri Temeli — **BİTTİ**

Kaynak: `docs/turlar/CLAUDE_CODE_PROMPTU_TUR3.md`, `TUR3_DEVAM.md` ve
`TUR3_DEVAM_2.md`. On işlik bir tur; **onu da bitti.** İlk sekiz `374caa3`
ile, kalanlar turun sonunda commit'lendi.

Doküman sürümleri iki kez doğrulandı: turun başında SRS 1.15 / SDD 1.23 /
Backlog 1.9, devam yönergesinden sonra SRS **1.15** / SDD **1.24** /
Backlog **1.10** / Proje Tanım Dokümanı 1.2. Bildirilen dört doküman
borcunun tamamı kapatılmış olarak geldi.

### Uygulama planı

[`docs/turlar/UYGULAMA_PLANI_V2.md`](docs/turlar/UYGULAMA_PLANI_V2.md).
Bir süre `docs/` altında arayıp "eksik" diye kaydetmiştim; dosya o sırada
depo kökündeydi. Yerleşim kuralı artık planın kendisinde yazılı ve tek:
**kanonik dört doküman `docs/` altında, plan/prompt/yönerge dosyalarının
tamamı `docs/turlar/` altında**, depo kökünde plan veya prompt bulunmaz.

Plan Tur 3 için bu turda yapılanları birebir doğruluyor ve iki kural
ekliyor: **her turda kabul ölçümü koşulur** (K17 — blok kataloğu
büyüdükçe K1 riski artıyor, ölçüm sona bırakılmaz) ve **yeniden tanımlanan
bir kuralın eski testi silinmez, güncellenir** (davranışın bilinçli mi
kazayla mı değiştiği bilgisi kaybolmasın). İkincisi bu turda uygulandı:
S1'in birim değişikliğinde testler silinmedi, beklenen değerler
gerekçesiyle birlikte güncellendi.

### Biten ve ölçülen işler

#### İş 1 — Talep tablosu zaman aralığına (göç `d1f83a6c40b2`)

`talep.vardiya_tipi_id` yerine `baslangic` ve `bitis` (TIME). Dönüşüm göç
içinde yapılıyor ve **sayılarak** doğrulanıyor: satır sayısı ile toplam
kişi-saat yükü eşit değilse göç hata verip duruyor. Sessizce devam etmesi
hâlinde kaybolan bir talep satırı hiçbir yerde görünmezdi — talep düştüğü
için kapsama açığı da doğmaz.

**Ölçüldü (geliştirme veritabanı):** 27 satır → 27 satır, **384 kişi-saat →
384 kişi-saat.** Geri alma yazıldı; test veritabanında ileri → geri → ileri
denendi.

Aynı göç `kapsama_acigi` ve `fazla_kadro` tablolarını da aralığa çeviriyor,
`personel`e devir bakiyesi alanlarını (`devir_fazla_calisma_saat`,
`kota_yili`) ve `cozum_isi`ne `on_kontrol_bulgulari` alanını ekliyor.

**Açık/fazla kadro satırları dönüştürülmüyor, siliniyor.** Bu iki tablo bir
çözümün çıktısıdır, kullanıcının girdiği veri değil; blok eksenli bir açık
kaydını aralığa çevirmek o kaydın üretildiği andaki talebi yeniden kurmayı
gerektirir ve talep aynı göçte değişiyor. Satırlar sürüm yeniden
çözüldüğünde ya da elle düzenlendiğinde doğru biçimde yeniden yazılıyor.
Yanlış dönüşmüş bir açık kaydı, hiç olmamasından kötüdür: rapora doğru gibi
girer.

#### İş 2 — Talebin saate açılımı, tek yerde

`app/services/talep_cozucu.py` → `talebi_saate_ac`; aralık aritmetiğinin
kendisi `app/kurallar/zaman_araligi.py`de (ORM'den bağımsız, kural katmanı
da kullanabiliyor). Sınırlar başlangıçta kapalı, bitişte açık: `08.00–16.00`
→ 08…15, 16 dışarıda. Isıtma penceresi dahil (TD-5). Gece yarısını aşan
aralık ertesi günün duvar saatlerine taşıyor.

#### İş 3 — S1 saat ekseninde; **turun asıl kabulü geçti**

Göç öncesi taban (7 günlük dönem, tek arama işçisi, 120 s):
toplam **1096**, S1 0, S2 40, S3 40, S4 202, S6 18, S7 17, **144 atama, 0
açık**.

Göç sonrası aynı dönem: **S1 0, 144 atama, 0 açık**, toplam 1055. Kapsama
birebir aynı; toplam daha düşük çünkü çözücü daha iyi bir çözüm buldu (iki
koşum da optimalliği kanıtlamıyor, "uygun" durumunda bitiyor).

**Yolda bir tuzak çıktı — kaydı burada duruyor.** İlk uygulamada aynı dönem
120 saniyede **704 kişi-saat** açıkla çıkıyordu; 420 saniyede bile 536'ya
inebildi. Sebep yapıda değildi: hizalı katalogda bir bloğun sekiz saati
**aynı kısıtı** üretiyor ve sekiz **birbirinin yerine geçebilen** `eksik`
değişkeni doğuruyordu; çözücü zamanının çoğunu bu simetriyi kırmakla
harcıyordu. Aynı kısıtı üreten saatler tek değişkende toplandı ve amaç
fonksiyonundaki katsayı grubun saat sayısı yapıldı. **Anlam değişmedi** —
ceza saat başına birikmeye devam ediyor — ama arama eski hâline döndü.

#### İş 4 — Açık ve fazla kadro aralık olarak (kısmen)

Birleştirme `saatleri_araliklara_birlestir` ile **tek yerde**: ardışık ve
sayısı eşit saatler tek satıra iniyor (00…07'de 1 kişi eksik → tek
`00.00–08.00 / 1` kaydı). Hem çözücü yolu hem elle düzenleme yolu
(`sapmalari_yenile`) aynı yardımcıyı kullanıyor. Talep ile atamanın saat
bazında farkı `Baglam.sapma_saatleri`nde tek tanım; doğrulayıcının S1
bulguları da kalıcı sapma tabloları da oradan çıkıyor.

#### İş 8 ve İş 10 — servis tarafı

Ön kontrol bulguları artık **işi düşürmüyor**: `Bulgu.engel_mi` →
`kesin_mi` (anlamı "kesin bulgu mu, uyarı mı"), `engelleyenler` →
`kesin_bulgular`, ve çözüm işçisi bulguları `cozum_isi.on_kontrol_bulgulari`
alanına yazıp çözüme devam ediyor. Bulgu metinleri kimlik yerine ad
taşıyor (`Baglam.yetkinlik_adi/nokta_adi/vardiya_adi`).

### Tasarımdan sapmalar — ikisi de zorunluydu

1. **Gün sonu `24.00` yerine `00.00` ile yazılıyor.** SDD 4.2.2 `24.00`
   diyor. PostgreSQL bu değeri saklıyor fakat sürücü (psycopg) geri
   okuyamıyor — denendi: `DataError: can't parse time '24:00:00': hour must
   be in 0..23`. Python'un `time` tipi 24:00'ı taşımıyor. Bunun yerine
   `vardiya_tipi` tablosunun **zaten kullandığı** sözleşme uygulandı:
   `bitis <= baslangic` ise aralık gün sonuna kadar sürer, gece yarısını
   aşıyorsa ertesi güne taşar. Sütun tipi SDD'deki gibi TIME kaldı; değişen
   yalnızca 24.00'ın kodlanışı ve bu kural tek yerde (`zaman_araligi.py`)
   uygulanıyor.

2. **Blok eksenli talep görünümü korundu** — saat ekseninden türetilerek.
   S2, S3 ve S4 talebi hâlâ **vardiya biriminde** okuyor
   (`hedef_gece = Σ talep / |havuz|`, `Σ sure_saat × gereken`) ve bu turda
   kural kataloğuna dokunmak yasak. Talep doğrudan saate çevrilseydi
   S2/S3'ün hedefi sekiz katına çıkar ve "aynı toplam ceza" kabulü
   kırılırdı. İkinci bir **tanım** yazılmadı: tek kaynak `talep_saat`,
   `blok_gorunumu_uret` ondan tek yerde türetilen bir **türev** (bir bloğun
   gereken sayısı, kapsadığı saatlerdeki en büyük gereken). Hizalı
   katalogda eski tablonun birebir aynısını veriyor. Tur 4'te S2/S3 saate
   geçince türev kalkar.

### DOKÜMAN BORCU — **dördü de kapatıldı**

Aşağıdaki dört madde bildirildikleri hâlleriyle duruyor; **hepsi SDD 1.24
ve Backlog 1.10 ile karşılandı** (gün sonunun kodlanışı SDD 4.2.2'ye,
`on_kontrol_bulgulari` 4.2.4'e, talep uç noktaları Ek B'ye yazıldı;
FR-1.9'un kişi-vardiya türevi Backlog **B-21** olarak kaydedildi ve Tur
4'te saat tabanına taşınacak). Açık borç DEĞİLDİR; kayıt olarak duruyor.

1. **SDD 4.2.2 / 4.2.4 — gün sonunun kodlanışı.** "24.00 gün sonunu
   gösterir" ifadesi uygulanabilir değil (yukarıdaki 1. sapma).
   Dokümanda `bitis <= baslangic` sözleşmesinin yazılması gerekiyor.
2. **SDD 4.2.4 — `cozum_isi.on_kontrol_bulgulari`.** İş 8 bulguların
   "sürüm kaydında kalıcı" olmasını istiyor; SDD'de böyle bir alan tanımlı
   değil. Alan eklendi, dokümana işlenmeli.
3. **SDD Ek B — talep uç noktaları.** Talep artık hücre değil kayıt
   olduğundan `PUT /api/talep` yerine `POST /api/talep`,
   `PUT /api/talep/{id}` ve `DELETE /api/talep/{id}` var. Ek B yalnızca
   `GET, PUT` listeliyor; uç nokta sayısı 72 → 74.
4. **FR-1.9 — kişi-vardiya artık türev.** Talep blok taşımadığı için
   haftalık kişi-vardiya, kişi-saatin katalogdaki ortalama blok uzunluğuna
   bölünmesiyle bulunuyor (tek uzunluklu katalogda SRS 3.3.6'daki referans
   örneği birebir veriyor: 1.152 saat / 8 = 144, asgari kadro 29).
   Karışık uzunluklu katalogda bu bir yaklaşıktır; asgari kadro hesabının
   saat tabanına taşınması Tur 4'ün konusu olabilir.

### Test fikstürleri aralık şekline geçirildi — takım 320/322

Ondan fazla test dosyası ve iki betik (`demo_veri_uret.py`,
`kabul_olcumu.py`) eski `Talep(vardiya_tipi_id=…)` şeklini kuruyordu.
Ortak kaynak `ornek_senaryo.py` de SRS 3.3.4'ün yeni aralık tablosuna
geçirildi ve referans yükü koruyor: **haftalık 1.152 kişi-saat**, sekiz
saatlik katalogda 144 kişi-vardiya ve 29 kişilik asgari kadro (FR-1.9
testi birebir geçiyor).

Yol boyunca üç şey ortaya çıktı ve düzeltildi:

- **Göç dosyasını koştuktan sonra değiştirmiştim** (`on_kontrol_bulgulari`
  sonradan eklendi), bu yüzden iki veritabanı da göçün eski hâlindeydi ve
  geri alma da tutmuyordu. Göç yayınlanmadığı için ikisi de göç
  zincirinden sıfırdan kuruldu — elle `ALTER TABLE` yok.
- **`test_cizelge_api` sıra bağımlıydı:** ön kontrol bütün tanım verisine
  baktığı için başka bir testin bıraktığı nokta/talep bulgu üretiyordu.
  Fikstür artık senaryo verisini temizliyor.
- **`Bulgu.engel_mi` yalnızca serviste yeniden adlandırılmıştı**; API
  şeması ve arayüz hâlâ eski adı taşıyordu. Üçü de `kesin_mi` oldu.

S1'in birimi değiştiği için beklenen test güncellemeleri yapıldı: sekiz
saatlik blokta bir kişilik açık artık **8 kişi-saat** ceza üretiyor (eski
ölçüde 1 idi) ve bulgu metni blok adı yerine **aralık** taşıyor
(`2026-02-02 · 16.00–24.00 · Güvenlik`).

`test_cozum_on_kontrolde_yapisal_engel_varsa_cozmeden_basarisiz_doner`
adıyla birlikte tersine çevrildi: artık
`test_on_kontrol_bulgusu_cozumu_dusurmez_cizelge_yine_uretilir` ve
çizelgenin **üretildiğini**, bulgunun iş kaydında kaldığını, açığın
kapsama açığı olarak raporlandığını ölçüyor.

### İş 9 — kapsama oranı atamalardan (SDD 5.7, K19)

Oran artık `Σ min(atanan, talep) / Σ talep` ile **atama kayıtlarından**
hesaplanıyor; kapsama açığı tablosu bir raporlama detayı. `min(...)` şart:
bir saatteki fazla kadro başka bir saatteki açığı kapatmaz. Talep yoksa
oran **tanımsız** (`None`) — sıfır bölme yerine yüzde yüz varsaymak, boş
bir dönemi kusursuz bir çizelge gibi gösterirdi.

### Takım yeşil — ara commit atıldı

**322/322 geçiyor**, `ruff check` ve `ruff format --check` temiz. Buraya
kadarki iş `374caa3` ile commit'lendi (TUR3_DEVAM'ın istediği ara commit).

---

## Turun ikinci yarısı — kalan altı iş bitti

Kaynak: `docs/turlar/TUR3_DEVAM_2.md`. Tur **kapandı**.

### İş 7 — Talep ekranı aralık girişine

Ekran eski matrisi çiziyor ve kırıktı: hücrelere yazılan hiçbir sayı
kaydedilemiyordu, çünkü beslendiği `PUT /api/talep` ucu artık yok. Yerine
her satırı bir aralık olan liste geldi — nokta, gün tipi, tarih, aralık,
süre, gereken — ve Ekle/Değiştir/Sil üçlüsü diğer sekmelerle **aynı
konumda, aynı sırada** (SDD 6.3.1). Görsel geliştirme Tur 6'nın işi;
buradaki hedef işlevsellikti.

Üç karar kayda değer:

1. **Saatler açılır liste, serbest metin değil.** Aralıklar saat başında
   başlamak zorunda (kapsama kısıtı saat ekseninde yazılır); serbest bir
   alan 08.30 yazdırıp sunucudan hata almayı mümkün kılardı. Bitiş
   listesinde 00.00 **yoktur** — gün sonu 24.00'tır ve ikisi aynı değeri
   kodlar; iki ayrı seçenek görünmesi kullanıcıyı yanıltırdı.
2. **Tarih alanı forma girdi.** İş tanımı beş alan sayıyordu ama talep
   kayıtlarının tarihe özgü istisnaları var ve listede zaten görünüyorlar.
   Alan olmasaydı, istisna satırı genel satırın kopyası gibi durur ve
   kullanıcı farkı hiçbir yerden okuyamazdı.
3. **Yanıt alanı `hucreler` → `araliklar`.** Eski ad ekranın da matris
   çizmesine yol açmıştı; sözleşme değişirken adın kalması, sonraki
   okuyucuyu aynı yanlışa davet ederdi.

Ekranın sözleşmesi `TanimlarEkrani.test.tsx`te kilitli: 24.00 gösterimi,
POST/PUT/DELETE yolları ve 409'un anlaşılır hâle gelmesi.

### İş 6 — blok kataloğu kısıtları

İkisi de **girişte** reddediliyor: aynı `(baslangic_saati, sure_saat)`
ikinci kez tanımlanamaz (**409** — istek geçerli, mevcut veriyle çakışıyor)
ve süre günlük azami çalışmayı aşamaz (**400** — değerin kendisi geçersiz).
Ayrım korunuyor çünkü kullanıcının yapacağı şey farklı: biri başka bir saat
seçer, öbürü süreyi kısaltır.

**Pasif bloklar benzersizlik sayımında yok.** Sayılsalardı, kullanımda
olduğu için silinemeyip pasifleştirilmiş bir blok o saatlerde yeni blok
tanımlamayı **kalıcı olarak** imkânsız kılardı ve kullanıcının
düzeltebileceği bir yol kalmazdı.

**GEÇİCİ YAPILANDIRMA DEĞERİ — Tur 4'te silinmeli.** Azami süre
`kural.parametre_getir("H9", "azami_gunluk_calisma_saati", …)` ile **kural
kataloğundan** okunuyor; H9 henüz yok, o yüzden çağrı
`_GECICI_AZAMI_GUNLUK_CALISMA_SAATI = 11` varsayılanına düşüyor
(`app/services/tanim_servisi.py`). H9 yazıldığında kısıt kendiliğinden
onun değerini kullanmaya başlar ve **sabit silinmelidir** — iki yerde duran
bir sayı sessizce birbirinden ayrılır. Kısıt ile kuralın ayrı sayılar
taşıması, girişi geçen bir bloğun çözümde her gün ihlal üretmesi demekti.

**Test takımı bu kısıtla çelişiyordu ve bu bir bulgu.** Test veritabanı
koşumlar arasında sıfırlanmıyor; blok yaratan testler kayıtlarını
bırakıyordu, dolayısıyla katalogda üç tane 08.00/8sa blok birikmişti.
Kısıt gelince üç test kırıldı — kısıt yanlış olduğu için değil, testler
katalogda çöp biriktirdiği için. İki yardımcı eklendi
(`gecici_vardiya_tipi` blok açıp test bitince düşürür, `bos_vardiya_blogu`
saatleri testin konusu olmayan yerlere boş bir saat verir) ve birikmiş
kayıtlar uygulamanın kendi silme yolundan temizlendi — elle SQL yok.

### İş 5'in form tarafı — devir bakiyesi

`devir_fazla_calisma_saat` ve `kota_yili` şemalara, API'ye ve personel
formuna girdi. **Bu turda hiçbir kural bu alanları okumuyor**; toplanmalarının
nedeni Tur 4'ün kota hesabına hazır olmaları. Boş bırakılan devir **sıfır**
(sütun NOT NULL, "bilinmiyor" hâli tanımlı değil), kota yılı boş kalabilir.
Servis açıkça `null` gönderen bir istemciye karşı da korumalı.

### Blok görünümü türevine varsayım yorumu

`blok_gorunumu_uret`, kullanıcısı (`baglam_kurucu`) ve taşıyıcı alan
(`Baglam.talep`) — üçüne de aynı uyarı yazıldı: türev **tek uzunluklu ve
hizalı** bir katalog varsayar. Tur 4'te 10 ve 12 saatlik bloklar girdiğinde
"en büyük gereken" kuralı yanlışlaşır (06.00–18.00 bloğu gece 3 ve gündüz 7
kişilik talebi birlikte örter, türev 7 sayar) ve **hata vermez**. Yorum
düzeltmeyi değil **kaldırmayı** işaret ediyor: doğru çözüm S2/S3'ü saat
eksenine taşımaktır.

### Kabul ölçümü — K1 **1,01 sn** (eşik 60 sn)

Simetri gruplamasından **sonra**, bu makinede (macOS arm64, 10 çekirdek;
arama işçisi SDD 3.4.3 referansına sabit: 3):

| Kriter | Eşik | Tur öncesi | **Şimdi** |
|---|---|---|---|
| K1 40×28 | < 60 sn | 1,12 sn | **1,01 sn** |
| K2 zorunlu ihlal | 0 | 0 | **0** |
| K3 gece sapması | ≤ 1,0 | 0,61 | **0,61** |
| K4 eksik gösterimi | ≥1 açık | 21 hücre | **13 aralık (112 saat)** |
| K5 manuel düzenleme | < 1 sn | 0,038 sn | **0,035 sn** |

**5/5 geçti.** K1 artmadı — blok kataloğu bu turda büyümedi ve simetri
gruplaması aramayı göç öncesi hâline döndürdü.

**K4 ölçümün kendisi eskimişti ve önce kaldı.** Betik açık kayıtlarının
orta anahtarını hâlâ vardiya tipi kimliği sanıyor, saat numarasını
yazdırıyordu ("2026-06-06 / 0 / Vardiya Şefliği") ve "üç bilgi de dolu"
denetimi bu yüzden düşüyordu. Ölçülen şey bozulmamıştı; ölçü İş 4'ün
ardından güncellenmemişti. Betik saat eksenli eksikleri nokta içinde
aralığa birleştirip kullanıcıya gösterilen biçimi ölçüyor artık.

**Yol üstünde bir hata daha çıktı:** saat metnini yazan yardımcı **üç ayrı
modülde** kopyalanmıştı (`esnek.py`, `tanim_servisi.py`, `kabul_olcumu.py`)
ve üçü de aynı yanlışı yapıyordu — gün başında başlayan bir aralığı
"24.00–08.00" diye yazıyorlardı, çünkü 00.00'ı başlangıç mı bitiş mi
olduğuna bakmadan 24.00'a çeviriyorlardı. Okuyan kişi bunu gece yarısını
aşan bir aralık sanardı. Tanım `zaman_araligi.py`ye taşındı
(`saat_metni`/`aralik_metni`), üç kopya kaldırıldı.

### Ek B yeniden üretildi — 72 → 74

`PUT /api/talep` kalktı; `POST /api/talep`, `PUT /api/talep/{id}` ve
`DELETE /api/talep/{id}` geldi. Dosya "üretilmiştir" diyordu ama üreteci
yoktu; `backend/scripts/uc_noktalari_listele.py` eklendi. `--denetle`
uygulamanın yönlendirme tablosunu Ek B ile karşılaştırır ve fark varsa
sıfırdan farklı kodla çıkar — sayı artık elle sayılmıyor.

### S1'in ölçeği büyüdü — Tur 8'in kalibrasyonuna not

Sekiz saatlik blokta bir kişilik açık artık **1 yerine 8 birim** ceza
üretiyor (ceza saat başına birikiyor). `w1` değişmediği için S1'in diğer
hedefler karşısındaki **baskınlığı arttı**. Şu an sorun değil — baskınlık
zaten istenen şey — ama Tur 8'in ağırlık kalibrasyonunda hesaba katılacak
bir kayma. Bu turda ağırlıklara dokunulmadı.

### Yeni doküman borcu — üç madde

Öncekiler kapandı (yukarıdaki DOKÜMAN BORCU bölümü); bunlar **yeni** ve
**açık**:

1. **SRS FR-1.3 — blok kataloğu kısıtları.** Aynı `(baslangic_saati,
   sure_saat)` ikilisinin benzersizliği ve sürenin günlük azamiyi
   aşamayacağı SRS'te yazılı değil; kısıt kodda var.
2. **SDD 4.2.1 — `personel.devir_fazla_calisma_saat` / `kota_yili`.**
   Göçle geldiler (`d1f83a6c40b2`) ve artık API şemasında da varlar;
   SDD'nin alan listesi henüz taşımıyor.
3. **SDD Ek B — 74 uç nokta.** `docs/EK_B_UC_NOKTALAR.md` güncel; SDD'nin
   kendi Ek B'sine aktarılması bekliyor.

### Bekleyen göçler — dağıtım yapılmadı

Sunucuda **üç göç** birikmiş olacak: `b6e2f81d3c07`, `c9a4b7e21f38` (Tur 2)
ve `d1f83a6c40b2` (bu tur). Sonuncusu veri dönüştürüyor; dağıtımdan önce
yedek alınmalı. Dağıtım kararı proje yürütücüsünde.
