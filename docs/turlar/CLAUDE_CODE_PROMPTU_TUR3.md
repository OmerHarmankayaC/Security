# Claude Code — Sürüm 2, Tur 3: Saatlik Düzenin Veri Temeli

## Bağlam

BOTAŞ vardiya çizelgeleme karar destek aracının (VARDİS) ikinci geliştirme
aşamasındasın. Tur 1 ve Tur 2 tamamlandı. Bu tur, sistemin **vardiya tabanlı
düzenden saatlik düzene** geçişinin ilk adımıdır: veri temeli kurulur, kural
kataloğuna henüz dokunulmaz.

Bu, sürüm 2'nin ilk turudur. Üç şey değişti:

- **İlerleme kaydı artık `PROGRESS_V2.md`.** Birinci aşamanın `PROGRESS.md`'si
  kapandı ve okunmaz; arşivdir. Bu turda `PROGRESS_V2.md`'yi sen oluşturacaksın —
  ilk satırı bu turun kaydı olacak.
- **Yeni bir uygulama planı var:** `docs/UYGULAMA_PLANI_V2.md`. Turların tamamını
  ve aralarındaki sırayı gösterir.
- **Tasarım kararları ayrı bir notta:** `docs/SAATLIK_GECIS_KARARLARI.md`. Bu not
  kanonik değildir; kanonik dokümanlara işlenmiş kararların gerekçelerini ve henüz
  karara bağlanmamış maddeleri içerir.

### Doküman sürümleri — ilk işin bunları doğrulamak

| Doküman | Sürüm |
|---|---|
| `BOTAS_Vardiya_Cizelgeleme_SRS.md` | **1.15** |
| `BOTAS_Vardiya_Cizelgeleme_SDD.md` | **1.23** |
| `BOTAS_Vardiya_Cizelgeleme_Backlog.md` | **1.9** |
| `BOTAS_Vardiya_Cizelgeleme_ProjectCharter.md` | 1.2 (değişmedi) |

Taşımıyorlarsa dur ve bana söyle. Eski bir kopyayla çalışmak, tasarımı ikinci kez
üretmek demektir.

### Okunacaklar

- SRS **TD-13** (çalışma bloğu), **3.3.1** (blok kataloğu), **3.3.4** (talep
  aralıkları), **4.3 S1** (saat bazında kapsama), **FR-1.1, FR-1.3, FR-1.7,
  FR-1.8, FR-1.9**
- SRS **FR-5.1, FR-5.3, FR-5.5, FR-5.6, FR-8.1**
- SDD **4.2.1** (`vardiya_tipi` kısıtları, `personel` yeni alanları), **4.2.2**
  (`talep`), **4.2.4** (`kapsama_acigi`, `fazla_kadro`), **5.2** (ön kontrol),
  **5.3** (model kurma ve talebin saate açılımı), **5.7** (kapsama oranı)
- `docs/SAATLIK_GECIS_KARARLARI.md` — K1, K3, K7, K11, **K18, K19, K20**
- `docs/UYGULAMA_PLANI_V2.md` — Tur 3 maddesi

## Çalışma kuralları

- Dört kanonik dokümana (Charter, SRS, SDD, Backlog) **dokunmazsın**. Gereksinim
  veya tasarım etkisi doğuran bir şey çıkarsa `PROGRESS_V2.md`'ye "DOKÜMAN BORCU"
  başlığı altında yaz ve bana bildir; dokümanı ben işlerim.
- `PROGRESS_V2.md`, `DAGITIM.md` ve `README.md` senin dosyalarındır.
- Tasarımdan sapma gerekiyorsa **önce nedenini söyle**, sonra uygula.
- Şema değişikliği yalnızca Alembic göçüyle. Elle `ALTER TABLE` yasak.
- Git: `add`, `commit`, `tag` senin; `push` ve `remote` **asla**.
  `Co-Authored-By` trailer'ı yok.
- Backend'de tip açıklamaları zorunlu; `ruff check` ve `ruff format --check`
  temiz. Frontend'de TypeScript strict.
- Testler ayrı veritabanında koşar (Tur 2'de kuruldu). Bu kural altyapıdadır.
- Sırları sohbete yazma.

## Bu turun ilkesi: davranış değişmemeli

Bu turda **blok kataloğu büyümüyor.** Üç blok (00–08, 08–16, 16–24) olduğu gibi
kalıyor. Değişen yalnızca tablo yapıları ve talebin ekseni.

Bunun nedeni kabul kriterini ölçülebilir kılmaktır: aynı girdiyle çözülen bir
dönem, göçten sonra **aynı sonucu** vermelidir. Sonuç değişirse göç ya da açılım
hatalıdır ve bunu bir sonraki turda kural değişiklikleriyle birlikte teşhis etmek
çok daha zor olur.

Yeni bloklar (10 ve 12 saatlik) ve yeni kurallar Tur 4'te birlikte gelecek.

## Bu projede tekrarlayan hata kalıpları

1. **Aynı tanımın iki yerde durması.** Bu turun merkezinde: talebin saate açılımı
   **tek bir fonksiyonda** yapılır, beş tüketici oradan alır.
2. **Metriğin ayrım üretmemesi.** Kapsama oranı hesabının birimi değişiyor
   (kişi-vardiya → kişi-saat); paydayı bir yerde değiştirip başka yerde unutmak bu
   kalıbın tam örneğidir.
3. **Isıtma penceresini hesaba katmamak** (TD-5). İki kez oldu. Açılım zaman
   eksenini ısıtma penceresiyle birlikte kapsamalı.
4. **Sessiz veri kaybı.** Göç mevcut talep satırlarını dönüştürüyor; dönüşen bir
   satırın kaybolması hata vermez, yalnızca talebi düşürür ve kapsama açığı da
   doğmadığı için hiçbir raporda görünmez.

---

## İş 1 — Talep tablosu zaman aralığına geçer

**Dayanak:** SDD 4.2.2, SRS 3.3.4.

- Alembic göçü: `talep.vardiya_tipi_id` yerine `baslangic` (TIME) ve `bitis`
  (TIME).
- **Veri dönüşümü göç içinde yapılır.** Her mevcut satır, bağlı olduğu vardiya
  tipinin başlangıç ve bitiş saatlerini alır. Gün sonu `24.00` ile gösterilir.
- Dönüşümün doğruluğu göç içinde **sayılarak** doğrulanır: dönüşüm öncesi ve
  sonrası satır sayısı ile toplam kişi-saat yükü eşit olmalıdır. Eşit değilse göç
  hata vermeli, sessizce devam etmemelidir.
- Aynı nokta ve gün tipi için **çakışan aralıklar** reddedilir (uygulama
  katmanında). Çakışan iki kayıt aynı saat için iki farklı gereken sayı üretir ve
  hangisinin geçerli olduğu tanımsız kalır.
- Tarihe özgü istisna satırlarının davranışı: bir tarih için istisna varsa o günün
  talebi **yalnızca** istisna satırlarından oluşur; genel satırlarla karışım
  yapılmaz (SDD 4.2.2).

**Kabul:** Göç sıfırdan çalışır; mevcut demo verisi dönüşümden sonra aynı toplam
kişi-saat yükünü verir. Geri alma (`downgrade`) yazılmış ve denenmiştir.

---

## İş 2 — Talebin saate açılımı

**Dayanak:** SDD 5.3.

- `talebi_saate_ac(talepler, zaman_ekseni)` → `talep_saat[gün, saat, nokta]`.
  **Tek yer burasıdır.**
- Beş tüketici bu fonksiyonu çağırır: model kurucu, ön kontrol, doğrulayıcı,
  analiz servisi, kabul ölçüm betiği. Hiçbiri kendi açılımını yazmaz.
- **Aralık sınırları:** başlangıçta kapalı, bitişte açık. `08.00–16.00` aralığı
  08, 09, … 15 saatlerini kapsar, 16'yı kapsamaz. Böylece `08.00–16.00` ve
  `16.00–24.00` çakışmadan bitişir.
- Zaman ekseni **ısıtma penceresini de kapsar** (TD-5).
- Gece yarısını aşan bloklar ertesi günün saatlerine taşar; taşan kısım TD-1
  uyarınca başlangıç gününe ait sayılmaya devam eder.

**Kabul:** Birim testi, üç bloklu katalogda 08.00–24.00 / 7 kişilik bir talep
kaydının 08–23 saatlerinin her birine 7 yazdığını ve 24.00'ün dışarıda kaldığını
doğruluyor. Bitişik iki aralığın hiçbir saatte çakışmadığı ayrıca test ediliyor.

---

## İş 3 — S1 saat eksenine taşınır

**Dayanak:** SRS 4.3 (S1).

- Kapsama kısıtı `(gün, vardiya tipi, nokta)` yerine `(gün, saat, nokta)`
  üzerinden yazılır. Bir personel, bir saati kapsayan bloğa atanmışsa o saatte
  sayılır.
- Alt sınır esnek (`eksik`), üst sınır **bu turda zorunlu kalır**. Üç blok talep
  aralıklarıyla hizalı olduğu için sorun çıkarmaz. Üst sınırın esnetilmesi (K4)
  Tur 4'ün işidir — bu turda uygulama.
- Ceza saat başına birikir: iki saat bir kişi eksik = bir saat iki kişi eksik.

**Kabul:** Aynı dönem, göç öncesiyle **aynı toplam cezayı ve aynı kapsama açığı
miktarını** veriyor. Bu turun asıl kabulü budur; bir farkla karşılaşırsan durup
nedenini bul, üstünü örtme.

---

## İş 4 — Kapsama açığı ve fazla kadro aralık olarak tutulur

**Dayanak:** SDD 4.2.4.

- Göç: `kapsama_acigi` ve `fazla_kadro` tablolarında `vardiya_tipi_id` yerine
  `baslangic` ve `bitis` (TIME).
- **Birleştirme yazma anında yapılır.** Ardışık ve eksik sayısı eşit olan saatler
  tek satırda toplanır: 00, 01, … 07 saatlerinde 1 kişi eksikse tek bir
  `00.00–08.00 / 1 kişi` kaydı yazılır, sekiz satır değil.
- Birleştirme mantığı **tek yerde**; iki tablo aynı geçişte yazıldığı için aynı
  yardımcıyı kullanır.
- Dışa aktarma ve raporlama yüzeyleri aralık gösterir.

**Kabul:** Çelişkili senaryoda (SRS 3.3.6 kırılganlık mekanizması) açık kayıtları
aralık olarak yazılıyor; kayıt sayısı saat sayısından belirgin biçimde az.
Raporlanan toplam eksik kişi-saat, birleştirme öncesiyle aynı.

---

## İş 5 — Personel kaydına devir bakiyesi

**Dayanak:** SDD 4.2.1, SRS FR-1.1, karar notu K11.

- Göç: `personel.devir_fazla_calisma_saat` (NUMERIC, varsayılan 0) ve
  `personel.kota_yili` (INT).
- Personel formuna ve API şemasına eklenir.
- **Bu turda hiçbir kural bu alanı okumaz.** Alan Tur 5'te (`GecmisSayaclar`)
  kullanılacak; şimdi yalnızca veri girilebilir hâle geliyor.

**Kabul:** Alan arayüzden girilip okunabiliyor; boş bırakıldığında 0 kabul
ediliyor.

---

## İş 6 — Blok kataloğu kısıtları

**Dayanak:** SDD 4.2.1, SRS FR-1.3.

- Aynı `(baslangic_saati, sure_saat)` ikilisi iki kez tanımlanamaz.
- `sure_saat`, günlük azami çalışma saatini (11) aşamaz. Bu değer şimdilik bir
  sabit olarak değil, kural kataloğundan okunacak bir parametre olarak
  tasarlanmalı — H9 Tur 4'te yazılacak ve aynı değeri kullanacak. Parametre henüz
  yoksa geçici bir yapılandırma değeri kullan ve `PROGRESS_V2.md`'ye not düş.
- İkisi de **girişte** reddedilir, çözüm anına bırakılmaz.

**Kabul:** Çakışan blok ve 11 saati aşan blok tanımlama denemeleri anlaşılır bir
hatayla reddediliyor; mevcut üç blok etkilenmiyor.

---

## İş 7 — Talep ekranının aralık girişine uyarlanması

Talep ekranı bugün gün tipi × vardiya tipi matrisidir ve bu turdan sonra çalışmaz
hâle gelir. **Kırık ekran bırakılmaz.**

- Ekran, her satırı bir aralık olan bir listeye dönüşür: nokta, gün tipi,
  başlangıç, bitiş, gereken sayı. Ekleme, düzenleme, silme.
- Çakışan aralık girildiğinde anlaşılır hata.
- Bu **minimal bir uyarlamadır**, tasarım işi değil. Ekranın görsel olarak
  geliştirilmesi Tur 6'nın konusudur; şimdi işlevsel olması yeterli.

**Kabul:** Arayüzden bir talep aralığı eklenip düzenlenebiliyor ve silinebiliyor;
kapsama uyarısı (FR-1.9 kişi-saat yükü) doğru sayıyı gösteriyor.

---

## İş 8 — Ön kontrol bulguları çözümü engellemeyecek

**Dayanak:** SDD 5.2, SRS FR-5.1, FR-5.2, FR-5.5; karar notu K18.

**Bu bir hata düzeltmesidir ve bu turun en önemli işidir.** Bugün ön kontrol
yapısal bir bulgu ürettiğinde çözüm işi hiç başlatılmıyor; sürüm "başarısız"
damgasıyla, tek bir atama olmadan kalıyor. Gözlenen ekran çıktısı:

```
ENGEL: 18 nolu yetkinlik havuzunda 16 vardiyalık açık var
SONUÇ ÖZETİ — BAŞARISIZ
Çizelge: "Bu sürümde henüz atama yok."
```

Bu davranış **SRS FR-5.2'yi doğrudan ihlal ediyor**: "Sistem, personel yetersizliği
durumunda çözümü reddetmek yerine çizelgeyi üretmeli ve kapsama açıklarını
göstermelidir." S1'in zorunlu kısıt değil baskın ağırlıklı esnek hedef olarak
tasarlanmasının tek nedeni budur; işi düşürmek o tasarımı işlevsiz bırakıyor.

Yapılacak:

- Hiçbir ön kontrol bulgusu çözüm işini düşürmesin. `Bulgu.engel_mi` alanı
  **silinmez** — anlamı değişir: artık "kesin bulgu mu, uyarı mı" ayrımını taşır,
  "işi düşürür mü" ayrımını değil. Alan adı bu yeni anlamı yansıtmalı.
- Bulgular çözüm sonucuyla **birlikte** gösterilsin ve sürüm kaydında kalıcı
  olsun. Yalnızca çözüm anında görünüp kaybolan bir bilgi, yayınlanmış çizelgeye
  sonradan bakan kişi için hiç var olmamıştır.
- İşin `basarisiz` olmasının tek meşru nedeni çözücünün modeli **çözülemez**
  bulmasıdır (zorunlu kısıt çelişkisi). Bu, kapsama açığından ayırt edilebilir
  biçimde bildirilmeli (FR-5.5).
- S1 pasifken de çözüm çalışsın; "kapsama raporlanmıyor" damgası sürümün
  raporunda kalıcı olsun.

**Kabul:** Ekrandaki senaryo (02–08 Şubat 2026 dönemi, vardiya şefi havuzunda
açık) çözüldüğünde çizelge **üretiliyor**, atamalar görünüyor ve kapsama açığı
gün/saat/nokta düzeyinde raporlanıyor. Ön kontrol bulgusu kaybolmuyor, sonucun
yanında duruyor.

---

## İş 9 — Kapsama oranı atamalardan hesaplanacak

**Dayanak:** SDD 5.7, SRS FR-8.1; karar notu K19.

**Bu da bir hata düzeltmesidir.** Hiç ataması olmayan bir sürümde kapsama **%100**,
açık **0** gösteriliyor. Sebebi SDD 5.7'nin eski hâliydi: oran kapsama açığı
tablosundan türetiliyordu ve o tabloda kayıt bulunmayınca eksik sıfır sayılıyordu.
Sistem "açık kaydı yok" ile "açık yok"u karıştırıyor.

```
karsilanan = Σ_{d,t,n} min( atanan[d,t,n], talep[d,t,n] )
toplam     = Σ_{d,t,n} talep[d,t,n]
kapsama    = karsilanan / toplam
```

- Oranın **tek kaynağı atama kayıtlarıdır**; kapsama açığı tablosu bir raporlama
  detayıdır. Oranı iki yoldan türetilebilir bırakma.
- `min(...)` zorunludur: bir saatteki fazla kadro, başka bir saatteki açığı
  kapatmaz.
- Atama yoksa oran **%0**. Talep de yoksa oran **tanımsız** — tire göster, sıfır
  bölmede %100 varsayma.
- Bu hesap Analiz ekranında, Çizelge başlığındaki göstergede ve Özet ekranında
  aynı yerden gelsin.

**Kabul:** Boş bir sürümde kapsama %0 ve açık sayısı doğru; kısmen dolu bir
sürümde oran elle hesaplananla birebir aynı. Bunu doğrulayan bir test yaz.

---

## İş 10 — Bulgu metinlerinde ad göster

**Dayanak:** SRS FR-5.6; karar notu K20.

Bulgu metni bugün *"18 nolu yetkinlik havuzunda"* diyor. Kullanıcı 18 numaralı
yetkinliğin hangisi olduğunu bilmiyor ve ekranın hiçbir yerinde bu eşleme yok.
Ön kontrol bulgularında ve hata metinlerinde veritabanı kimliği yerine tanım adı
kullanılsın: *"Vardiya Şefi yetkinlik havuzunda"*.

**Kabul:** Aynı senaryoda bulgu metni yetkinlik adını taşıyor.

---

## Turun bitiş kontrolü

- [ ] On iş, mantıklı gruplarda commit'lenmiş (conventional commits)
- [ ] `pytest` tam takım geçiyor; `tsc -b` ve `oxlint` temiz
- [ ] **Kabul ölçümü koşuldu** (`scripts/kabul_olcumu.py`) ve K1 süresi
      `PROGRESS_V2.md`'ye yazıldı. Blok kataloğu bu turda büyümediği için sürenin
      belirgin biçimde artmaması beklenir; arttıysa nedenini araştır.
- [ ] Göç öncesi ve sonrası aynı dönem aynı toplam cezayı veriyor (İş 3 kabulü)
- [ ] `EK_B_UC_NOKTALAR.md` yeniden üretildi (uç nokta değişmemiş olsa bile
      doğrulanmış olur)
- [ ] `git status` temiz, sır yok
- [ ] **`PROGRESS_V2.md` oluşturuldu** ve bu turun kaydını içeriyor
- [ ] Doküman borcu varsa `PROGRESS_V2.md`'de "DOKÜMAN BORCU" başlığı altında

## Bu turda yapmayacakların

- **Kural kataloğuna dokunma.** H5'in yeniden tanımı, H9, H10, S2/S3'ün saat
  birimine geçişi, S6'nın yeniden yazımı ve S1'in üst sınırının esnetilmesi Tur
  4'ün işidir.
- **Blok kataloğunu büyütme.** Üç blok kalır.
- Geçmiş sayaçlar / kümülatif adalet (Tur 5).
- Çizelge ızgarasının değişken uzunluklu blok gösterimi, Analiz ekranı, Kural
  ekranı (Tur 6).
- Demo verinin zenginleştirilmesi ve gerçek isimler (Tur 7).
- Ağırlık kalibrasyonu (Tur 8).
- Excel/analiz dışa aktarma, sürükle-bırak, özet ekranı, belge ekleme, kullanıcı
  hesapları.
- Tasarım sürüm 4'ün koda geçirilmesi.
- **Sunucuya dağıtım.** Sunucuda zaten iki göç bekliyor; bu turunkiler de
  eklenecek. Dağıtım kararı bende.

Bunlardan biri yolda "aslında lazım" gibi görünürse uygulama; `PROGRESS_V2.md`'ye
not düş ve devam et.

## Kararlar

Karar notundaki açık maddelerin tamamı bağlandı: blok kataloğu K16'daki yedi blok
(Tur 4'te devreye girecek), haftalık mutlak tavan 66 saat, adalet ufku kayan 90
gün, gece çalışması 7,5 saat kuralı kataloğa alınmayacak, `w1f` başlangıç değeri 2.
Hiçbiri bu turu doğrudan etkilemiyor. Yine de bir varsayım yapman gerektiğini
hissedersen yapma — sor.
