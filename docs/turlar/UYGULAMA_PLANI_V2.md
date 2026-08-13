# Uygulama Planı — Sürüm 2

Bu doküman, projenin ikinci geliştirme aşamasını turlara böler. Her tur bağımsız
bir Claude Code oturumu olacak biçimde tasarlanmıştır: net bir hedefi, hangi
doküman bölümüne dayandığı ve bittiğini nasıl anlayacağı (kabul) yazılıdır.

Birinci aşamanın planı `docs/turlar/UYGULAMA_PLANI.md`'dir ve kapanmıştır. Bu
doküman onun yerine geçmez, devamıdır: bölüm 0'daki genel kurallar oradan aynen
geçerlidir ve aşağıda yalnızca **değişen veya eklenen** kurallar yazılmıştır.

**Dosya yerleşimi.** Karışıklığı önlemek için kural tektir:

```
docs/
  BOTAS_..._ProjectCharter.md      kanonik
  BOTAS_..._SRS.md                 kanonik
  BOTAS_..._SDD.md                 kanonik
  BOTAS_..._Backlog.md             kanonik
  SAATLIK_GECIS_KARARLARI.md       hazırlık girdisi (kanonik değil)
  turlar/
    UYGULAMA_PLANI.md              birinci aşama planı (kapandı)
    UYGULAMA_PLANI_V2.md           bu dosya
    CLAUDE_CODE_PROMPTU_TUR*.md    tur promptları
    TUR*_DEVAM*.md                 tur içi yönergeler
    yapilacaklar.md
```

Kanonik dört doküman `docs/` altındadır ve Claude Code onlara dokunmaz. Diğer
her şey `docs/turlar/` altındadır; depo kökünde plan veya prompt dosyası
bulunmaz.

Referans dokümanlar (`docs/` altında):
- `BOTAS_Vardiya_Cizelgeleme_ProjectCharter.md` — Proje Tanım Dokümanı
- `BOTAS_Vardiya_Cizelgeleme_SRS.md` — Yazılım Gereksinim Belirtimi
- `BOTAS_Vardiya_Cizelgeleme_SDD.md` — Yazılım Tasarım Dokümanı
- `BOTAS_Vardiya_Cizelgeleme_Backlog.md` — Ürün Backlog'u ve Karar Günlüğü

Hazırlık girdisi (kanonik değil): `docs/SAATLIK_GECIS_KARARLARI.md`.

---

## 0. Bu aşamada değişen kurallar

- **İlerleme kaydı `PROGRESS_V2.md`'dir.** Birinci aşamanın `PROGRESS.md`'si
  kapanmıştır ve okunmaz; yalnızca arşivdir. Her oturum `PROGRESS_V2.md` okuyarak
  başlar, güncelleyerek biter.
- **Tur numaraları devam eder.** Tur 1 ve Tur 2 tamamlandı; bu plan Tur 3'ten
  başlar.
- **Tur promptları `docs/turlar/` altındadır** ve kanonik doküman değildir.
- **Her turda kabul ölçümü koşulur.** Blok kataloğu büyüdükçe K1 kabul kriteri
  (40×28 < 60 sn) risk altındadır; ölçüm sona bırakılmaz, her turun kabulüne
  dahildir (K17).
- **Testler ayrı veritabanında koşar** (B-20, Tur 2'de kapatıldı). Bu kural artık
  altyapıdadır, her turda geçerlidir.

### Kural kataloğuna dokunurken

Birinci aşamanın kuralı aynen geçerli: yeni bir kural asla tek başına eklenmez —
sınıf + `modele_ekle` + `dogrula` + birim test + kural kayıt defterine kayıt aynı
commit'te gider. Bu aşamada bir madde daha eklenir:

- **Bir kural yeniden tanımlandığında eski testi silinmez, güncellenir.** H5 ve S6
  yeniden yazılıyor; eski davranışın testini silip yenisini yazmak, davranışın
  bilinçli olarak mı değiştiği yoksa kazayla mı bozulduğu bilgisini kaybettirir.

---

## Tur 3 — Veri Modeli ve Blok Kataloğu

**Hedef:** saatlik düzenin veri temeli. Kural kataloğuna henüz dokunulmaz.

**Dayanak:** SAATLIK_GECIS_KARARLARI K1, K2, K3, K7 (katalog kısıtı), K16;
SRS 3.3.1, 3.3.4; SDD 4.2.

**Bu turda blok kataloğu büyümez.** Üç blok (00–08, 08–16, 16–24) olduğu gibi
kalır; değişen yalnızca tablo yapıları ve talebin eksenidir. Bunun nedeni kabulü
ölçülebilir kılmaktır: aynı girdiyle çözülen bir dönem, göçten sonra aynı sonucu
vermelidir. Yeni bloklar Tur 4'te, yeni kurallarla birlikte gelir — sonuç o zaman
değişecektir ve değişimin nedeni bilinecektir.

- Blok kataloğu: `vardiya_tipi` tablosunun yapısı değişmez, kısıtları eklenir —
  süre ≤ günlük azami çalışma saati, aynı `(baslangic, sure)` çifti iki kez
  tanımlanamaz.
- `talep` tablosu aralık kaydına geçer: `vardiya_tipi_id` yerine `baslangic`,
  `bitis`. Göç mevcut veriyi dönüştürür ve dönüşümü satır sayısı ile toplam
  kişi-saat yükünü karşılaştırarak doğrular.
- `kapsama_acigi` ve `fazla_kadro` aralık kaydına geçer; birleştirme yazma anında
  ve tek yerde yapılır.
- S1'in kapsama kısıtı saat eksenine taşınır. Üst sınır bu turda zorunlu kalır
  (K4 Tur 4'ün işidir) — üç blok talep aralıklarıyla hizalı olduğu için sorun
  çıkarmaz.
- `personel.devir_fazla_calisma_saat` ve `personel.kota_yili` eklenir (K11); bu
  turda hiçbir kural bu alanları okumaz.
- Talep aralıklarının saate açılımı **tek bir yerde** yazılır; model kurucu, ön
  kontrol, doğrulayıcı, analiz ve kabul ölçümü aynı fonksiyonu çağırır.
- Talep ekranı aralık girişine minimal olarak uyarlanır — kırık ekran bırakılmaz;
  görsel geliştirme Tur 6'dadır.

**Kabul:** `alembic upgrade head` sıfırdan çalışır; aynı dönem göç öncesiyle
**aynı toplam cezayı ve aynı kapsama açığı miktarını** verir. Bu, göçün ve
açılımın doğruluğunun kanıtıdır. Kabul ölçümü koşulur ve K1 süresi kaydedilir.

---

## Tur 4 — Kural Kataloğu

**Hedef:** H5'in yeniden tanımı, H9 ve H10'un eklenmesi, S1/S2/S3/S6'nın yeniden
yazılması.

**Dayanak:** K4, K5, K6, K7, K8, K9, K12, K13; SRS 4.2, 4.3, 4.4 (güncellenmiş
hâlleri).

- **İlk iş B-22** — testler arası veri sızıntısı; bu tur çok sayıda yeni tanım
  testi getiriyor.
- `blok_gorunumu_uret` türevi kaldırılır (Tur 3'ün geçici köprüsü; karışık
  katalogda sessizce yanlış hesaplar).
- K16'daki genişletilmiş blok kataloğu (10 ve 12 saatlik bloklar) devreye girer.
- **Gösterim verisi kadrosu talebe göre boyutlandırılır** ve dört senaryoya çıkar;
  gerçekçi personel adları bu turda gelir. Planın önceki hâlinde bu iş Tur 7'deydi
  — kuralların işlediğini gösteremeyen bir gösterim verisiyle turun kabulü
  ölçülemez, bu nedenle öne alındı. Tur 5'e kalan kısım: arka arkaya iki
  yayınlanmış dönem ve devir bakiyesi senaryosu (`GecmisSayaclar`'a bağlı).
- Çizelge hücresi blok adı yerine saat aralığı gösterir.
- H5 → kayan yedi günlük mutlak tavan; 45 saat H10'un eşik parametresine taşınır.
- H9 (günlük azami saat) ve H10 (yıllık fazla çalışma kotası) yazılır. H10'un
  takvim haftası kümeleri, kayan pencerelerden **ayrı** bir yardımcıda hesaplanır
  (K9) — iki hafta kavramı tek bir fonksiyonda karışmamalıdır.
- S1'e fazla kadro terimi (`w1f`) eklenir; üst sınır zorunlu olmaktan çıkar.
- S2/S3 saat birimine geçer, uygun havuz mantığı korunur.
- S6 dairesel kayma tanımına geçer.
- `gece_saat[b]` hesabı tek yerde; `gece_mi` bayrağı tanımlı alan olarak kalır ve
  öneri kuralı tanımlı değeri asla ezmez (K5 — bu kural bir kez çiğnendi).
- Her kural için `modele_ekle` ve `dogrula` birim testi; yeniden tanımlananların
  eski testleri güncellenir, silinmez.

**Kabul:** Çözücü–doğrulayıcı uyum testi yeni katalogla 24/24 temiz geçer. 12
saatlik blok içeren bir senaryoda fazla çalışma saatleri doğru hesaplanır; kotası
dolmuş bir personel 45 saatin üstüne çıkmaz ama çalışmaya devam eder. Referans
ölçekte kabul ölçümü koşulur ve K1 süresi kaydedilir.

---

## Tur 5 — Gerçek Saatlik Model

**Hedef:** çalışma zamanının blok seçiminden saat düzeyinde karara geçirilmesi ve
Müracaat noktasının kapsamdan çıkarılması.

**Dayanak:** `docs/turlar/SAATLIK_MODEL_KARARLARI.md`; SRS 1.19, SDD 1.27,
Charter 1.4.

Bu tur, Tur 3 ve Tur 4'ün blok kataloğu kararını geri alır. Kalkanlar:
`vardiya_tipi` tablosu, `gece_mi` bayrağı, blok kataloğu, Müracaat noktası ve
yetkinliği. Korunanlar: talep ekseni, S1'in saat bazlı kapsaması, kişiye özel adil
pay, H10 kotası, takvim haftası ayrımı, saat gruplaması.

- **İlk iş prototip ölçümüdür.** Saat modeli değişken sayısını düşürür fakat kısıt
  yapısı ağırdır; K1 riski ölçülmeden tam uygulamaya geçilmez. 40 × 28 ölçeğinde
  ilk uygun çözüm 30 saniyeyi aşarsa durulur ve formülasyon gözden geçirilir.
- Göç: atama blok kaydına (`baslangic_zamani`, `bitis_zamani`), `vardiya_tipi`
  düşürülür, tercih zaman aralığına çevrilir, iki yeni kural parametresi eklenir.
- Model kurma mutlak saat ekseninde yeniden yazılır.
- H1, H3, H9, S2, S3, S6 yeniden tanımlanır; kalan kurallara dokunulmaz.
- Gösterim verisi Müracaat'sız yeniden üretilir; K4'ün çelişkisi şef havuzu
  üzerinden kurulur.
- Arayüz yalnız kırık kalmayacak kadar uyarlanır.

**Kabul:** Prototip ölçümü kayıtlı; uyum testi 24/24; kabul ölçümü Charter 1.4'ün
yeni K3 ve K4 tanımlarıyla koşulmuş.

## Tur 6 — Saat Görünümleri ve Arayüz

**Hedef:** çalışma zamanının ekranda saat çözünürlüğünde görünmesi.

- Gün ızgarası: satırlarda personel, sütunlarda seçili günün yirmi dört saati.
  Blok, kapsadığı saat hücrelerinin kesintisiz şeridi olarak görünür.
- Hafta şeridi: her gün hücresi yirmi dört dilimlik mini şerit; tıklanınca gün
  ızgarasına geçilir.
- Renk saatin kendisinden hesaplanır — gece koyu, gündüz açık, geçiş sürekli.
- Yazdırma ve CSV saat ızgarasına geçer.
- Kural ekranı yeni parametreleri gösterir; Analiz saat birimine hizalanır.

**Kabul:** Bir dönem baştan sona arayüzden kurulup çözülebiliyor ve çizelge saat
düzeyinde okunabiliyor.

## Tur 7 — Geçmiş Sayaçlar ve Kümülatif Adalet

**Hedef:** saatlik düzenin ekranlara yansıması.

**Dayanak:** SDD 6.3; TASARIM_REFERANSI 4.

- Talep ekranı: aralık girişi (başlangıç–bitiş–sayı), gün tipi başına satırlar.
- Çizelge ızgarası: değişken uzunluklu blok gösterimi. Hücre artık sabit üç renkten
  biri değil; renk başlangıç saati bandından hesaplanır. TASARIM_REFERANSI'ndaki
  vardiya renk rampası bu turda yeniden tanımlanır.
- Kural ekranı: yeni parametreler (günlük tavan, fazla çalışma eşiği, yıllık kota,
  desen toleransı, adalet ufku).
- Analiz: saat birimine hizalanmış metrikler + kişi başı fazla çalışma ve kalan
  kota göstergesi.
- Personel ekranı: devir bakiyesi alanı.

**Kabul:** Bir dönem baştan sona arayüzden kurulup çözülebiliyor: bloklar
tanımlanıyor, talep aralık olarak giriliyor, çizelge okunabilir biçimde
görüntüleniyor, analiz ekranında kota göstergesi doğru sayıları veriyor.

---

## Tur 8 — Gösterim Verisinin Tamamlanması

**Hedef:** Tur 4 ve Tur 5'te kurulan senaryoların üzerine, kümülatif davranışı
gösteren tarihsel derinlik.

Gösterim verisinin büyük kısmı Tur 4'te (dört senaryo, gerçekçi adlar, kadro
dengesi) ve Tur 5'te (devir bakiyesi senaryosu) gelir. Bu tura kalan:

- Arka arkaya **en az üç yayınlanmış dönem**, adalet ufkunun (90 gün) gerçekten
  dolduğu bir geçmiş.
- Isıtma penceresinin dönem sınırında görünür etkisini gösteren bir kurgu.
- Tercih, izin ve manuel düzenleme izlerinin gerçekçi dağılımı.

**Kabul:** Üçüncü dönem çözüldüğünde adalet sayaçları önceki iki dönemin yükünü
görüyor ve bu Analiz ekranında okunabiliyor.

---

## Tur 9 — Kalibrasyon, Ölçüm ve Kapanış

**Hedef:** ağırlıkların yeniden kalibrasyonu ve altı kabul kriterinin yeniden
ölçülmesi.

**Dayanak:** K14, K17; Charter bölüm 5.

- Ağırlık kalibrasyonu: `w1` baskınlığı korunarak `w1f`, `w2`, `w3`, `w4`, `w6`
  yeniden belirlenir. S2/S3/S4 artık aynı birimde olduğu için oranlar doğrudan
  karşılaştırılabilir (K12).
- Altı kabul kriteri referans donanımda yeniden ölçülür; `PERFORMANS_NOTU`
  sürüm 3 yazılır.
- K3 kriterinin (gece adaleti) birimi saate döndüğü için eşiği yeniden
  yorumlanmalıdır — Charter'daki "en fazla 1 sapar" ifadesi vardiya sayısına
  göreydi. Bu bir Charter değişikliğidir ve karar günlüğüne yazılır.

**Kabul:** 6/6 kriter geçiyor; geçmeyen varsa hangi kriterin ne kadar açıkta
olduğu net.

---

## Sonraki turlar (saatlik geçişten bağımsız)

Bunlar saatlik düzenin üstüne oturur ve sırayla ele alınır:

- **Tur 10** — Excel ve analiz dışa aktarma (madde 1, 9)
- **Tur 11** — Sürükle-bırak (madde 3)
- **Tur 12** — Özet ekranı (madde 12)
- **Tur 13** — Müsaitlik kaydına belge (madde 7)
- **Tur 14** — Kullanıcı hesaplarının düzenlenmesi (madde 6)

Madde 1, 4, 9 ve 12 henüz prompta dönüşecek kadar tanımlı değildir; sıra gelmeden
önce somut belirtileri yazılmalıdır.

---

## Aşama kabul kriterleri

- [ ] Saatlik düzende bir dönem uçtan uca çözülüyor ve yayınlanabiliyor
- [ ] Günlük 11 saat tavanı hiçbir çizelgede aşılmıyor
- [ ] Yıllık 270 saat kotası aşılmıyor; kotası dolmuş personel çalışmaya devam
      ediyor, yalnızca fazla çalışamıyor
- [ ] Dönem sınırında bölünen takvim haftasının fazla çalışması tam hesaplanıyor
- [ ] Arka arkaya iki dönemde adalet sayaçları birikimi görüyor
- [ ] Altı kabul kriteri referans donanımda geçiyor
- [ ] Dört kanonik doküman kodla tutarlı; sapılan yer varsa dokümana işlenmiş
