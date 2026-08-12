# İlerleme Günlüğü — Sürüm 2

Birinci aşamanın günlüğü [`PROGRESS.md`](PROGRESS.md) dosyasında kapandı ve
arşivdir; okunmaz. Sürüm 2'nin kaydı buradan başlar.

Her oturum sonunda buraya bir kayıt eklenir: tarih, tamamlanan,
kalan/ertelenen, sıradaki oturumun ilk işi. Yeni oturum bu dosyayı okuyarak
başlar.

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
