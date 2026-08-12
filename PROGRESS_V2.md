# İlerleme Günlüğü — Sürüm 2

Birinci aşamanın günlüğü [`PROGRESS.md`](PROGRESS.md) dosyasında kapandı ve
arşivdir; okunmaz. Sürüm 2'nin kaydı buradan başlar.

Her oturum sonunda buraya bir kayıt eklenir: tarih, tamamlanan,
kalan/ertelenen, sıradaki oturumun ilk işi. Yeni oturum bu dosyayı okuyarak
başlar.

---

## 2026-08-12 — Tur 3: Saatlik Düzenin Veri Temeli — **SÜRÜYOR**

Kaynak: `docs/turlar/CLAUDE_CODE_PROMPTU_TUR3.md` ve `TUR3_DEVAM.md`. On
işlik bir tur. **Sekiz iş bitti, takım yeşil ve commit'lendi** (`374caa3`);
arayüz tarafında iki iş kaldı (aşağıda "KALANLAR").

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

### KALANLAR — sıradaki oturumun işi

1. **İş 7'nin arayüz tarafı.** Uç noktalar kayıt tabanlı hâle geldi
   (`GET, POST` + `PUT, DELETE /{id}`, çakışan aralık 409) ve testleri
   geçiyor; **Talep ekranı hâlâ eski matrisi çiziyor ve kırık.**
2. **İş 6** — blok kataloğu kısıtları: aynı `(baslangic_saati, sure_saat)`
   ikinci kez tanımlanamaz; süre günlük azami çalışma saatini (11) aşamaz.
   Değer kural kataloğundan okunacak bir parametre olarak tasarlanmalı
   (H9 Tur 4'te yazılacak, aynı değeri kullanacak).
3. **İş 5'in form tarafı** — devir bakiyesi alanları personel formunda.
4. Blok görünümü türevini kullanan her yere **tek uzunluklu katalog
   varsayımı** yorumu (TUR3_DEVAM'ın isteği; Tur 4'te türev kalkacak).
5. **Kabul ölçümü** (`scripts/kabul_olcumu.py`) — K1 süresi buraya
   yazılacak. Plan bunu her turun kabulüne dahil ediyor (K17); gruplama
   **sonrası** ölçülecek, önceki rakamlar teşhis kaydı.
6. `EK_B_UC_NOKTALAR.md`nin yeniden üretilmesi (talep uçları değişti:
   72 → 74) ve kalan commit'ler.

### Bekleyen göçler — dağıtım yapılmadı

Sunucuda **üç göç** birikmiş olacak: `b6e2f81d3c07`, `c9a4b7e21f38` (Tur 2)
ve `d1f83a6c40b2` (bu tur). Sonuncusu veri dönüştürüyor; dağıtımdan önce
yedek alınmalı. Dağıtım kararı proje yürütücüsünde.
