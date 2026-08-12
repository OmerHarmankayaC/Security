# Uygulama Planı — Sürüm 2

Bu doküman, projenin ikinci geliştirme aşamasını turlara böler. Her tur bağımsız
bir Claude Code oturumu olacak biçimde tasarlanmıştır: net bir hedefi, hangi
doküman bölümüne dayandığı ve bittiğini nasıl anlayacağı (kabul) yazılıdır.

Birinci aşamanın planı `docs/turlar/UYGULAMA_PLANI.md`'dir ve kapanmıştır. Bu
doküman onun yerine geçmez, devamıdır: bölüm 0'daki genel kurallar oradan aynen
geçerlidir ve aşağıda yalnızca **değişen veya eklenen** kurallar yazılmıştır.

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

- K16'daki genişletilmiş blok kataloğu (10 ve 12 saatlik bloklar) devreye girer.
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

## Tur 5 — Geçmiş Sayaçlar ve Kümülatif Adalet

**Hedef:** dönem öncesi birikim katmanı. Hem kotanın devri hem adalet ufku bu
katmandan beslenir.

**Dayanak:** K10, K11; SRS TD-6, TD-15; SDD yeni servis bölümü.

- `GecmisSayaclar` servisi: bir dönem ve bir ufuk verildiğinde her personel için
  gece saati, hafta sonu saati, toplam saat ve fazla çalışma saati döndürür.
  Yayınlanmış sürümlerin atamalarından **türetir**, saklamaz.
- Dört tüketici aynı servisten okur: çözücü, ön kontrol, analiz, kabul ölçümü.
  Beşinci bir hesap yeri açılmaz.
- Yasal ufuk ısıtma penceresini ve devir bakiyesini kapsar; adalet ufku
  yapılandırılabilir penceredir (K10).
- Ön kontrole yeni bulgu: devir bakiyesi kotayı aşmış personel (K8).

**Kabul:** Arka arkaya iki dönem çözüldüğünde ikinci dönemin adalet sayaçları
birincinin yükünü görüyor; aynı kişiye iki dönem üst üste ağır gece yükü
verilmiyor. Dönem sınırında bölünen takvim haftasının fazla çalışması tam
hesaplanıyor — bunu doğrudan gösteren bir test yazılır.

---

## Tur 6 — Arayüz

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

## Tur 7 — Demo Veri

**Hedef:** yeni düzeni gösterebilen, bugünkünden zengin bir gösterim verisi.

- Gerçekçi personel adları (madde 5).
- En az dört senaryo: rahat dönem · sıkışık dönem (mevcut kırılganlık mekanizması)
  · **fazla çalışma senaryosu** (12 saatlik bloklarla kota tüketen) · **kota sınırı
  senaryosu** (devir bakiyesi yüksek personel içeren).
- Isıtma penceresi ve kümülatif adaleti gösterebilmek için arka arkaya **en az iki
  yayınlanmış dönem**.
- Üreteç bayrakları SRS'ten birebir alır, öneri kurallarını uygulamaz (K5).

**Kabul:** `demo_veri_uret.py --reset` sonrası dört senaryo da arayüzden çözülüp
farklı davranışları gösteriyor; kota göstergesi en az bir personelde sınıra yakın.

---

## Tur 8 — Kalibrasyon, Ölçüm ve Kapanış

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

- **Tur 9** — Excel ve analiz dışa aktarma (madde 1, 9)
- **Tur 10** — Çizelge görünüm iyileştirmeleri ve sürükle-bırak (madde 3, 4)
- **Tur 11** — Özet ekranı (madde 12)
- **Tur 12** — Müsaitlik kaydına belge (madde 7)
- **Tur 13** — Kullanıcı hesaplarının düzenlenmesi (madde 6)

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
