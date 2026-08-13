# Claude Code — Sürüm 2, Tur 6: Saat Görünümleri ve Arayüz

## Bağlam

Tur 5 modeli saat düzeyine taşıdı: çalışma zamanı artık bir katalogdan seçilmiyor,
çözücü başlangıç ve süreye kendisi karar veriyor. Backend bitti, kabul ölçümü
koşuldu, dal `main`e alındı.

Arayüz o turda **yalnız kırık kalmayacak kadar** uyarlandı. Bu tur, çalışma
zamanını ekranda gerçekten saat çözünürlüğünde gösterir — projenin görünür
çıktısı bu tur.

### Doküman sürümleri — ilk işin bunları doğrulamak

| Doküman | Sürüm |
|---|---|
| `VARDIS_ProjectCharter.md` | 1.4 |
| `VARDIS_SRS.md` | **1.21** |
| `VARDIS_SDD.md` | 1.28 |
| `VARDIS_Backlog.md` | **1.18** |

Taşımıyorlarsa dur ve bana söyle.

### Okunacaklar

- SDD **6.3.3** (çizelge ekranı — iki görünüm, bu turun tanımı), **6.3.1**
  (tanımlar), **6.3.4** (analiz)
- SRS **TD-1, TD-13** (blok başladığı güne sayılır), **H1** (kesintisizlik,
  nokta sabitliği), **3.3.5** (parametreler)
- `docs/turlar/SAATLIK_MODEL_KARARLARI.md` — M6 (görünüm kararı)

## Çalışma kuralları

- Dört kanonik dokümana **dokunmazsın**. Etki doğuran bir şey çıkarsa
  `PROGRESS_V2.md`'ye "DOKÜMAN BORCU" başlığı altında yaz.
- Tasarımdan sapma gerekiyorsa **önce nedenini söyle**, sonra uygula.
- Git: `add`, `commit`, `tag` senin; `push` ve `remote` **asla**.
- `tsc -b` strict, `oxlint` temiz; her iş grubundan sonra commit.
- Bu tur backend'e neredeyse hiç dokunmaz. Dokunman gerekiyorsa önce söyle.

---

## İş 1 — Gün ızgarası (ana görünüm)

**Dayanak:** SDD 6.3.3.

Satırlarda personel, sütunlarda seçili günün yirmi dört saati. Bir personelin o
günkü bloğu, kapsadığı saat hücrelerinin **kesintisiz bir şeridi** olarak görünür;
şeridin üzerinde görev noktası kısaltması bulunur. Gün seçimi üstteki sekmelerle.

- Blok `baslangic_zamani`/`bitis_zamani`'ndan çizilir; `blok.ts` tek okuma yeri
  olarak kalsın — ikinci bir çözümleme yazma.
- **Gece yarısını aşan blok** iki güne yayılır ama tek bloktur. Başladığı günün
  ızgarasında sağ kenara kadar uzanır ve devam ettiği görünür; ertesi günün
  ızgarasında sol kenardan başlar ve **önceki günden geldiği belli olur**. İki
  ayrı blok gibi görünmemeli — bu, modelin tam da yasakladığı şeyin görüntüsü
  olurdu (SRS TD-13).
- Blok başladığı güne sayılır (TD-1); toplam saat göstergeleri bu güne yazar.

**Kabul:** 20.00'de başlayıp ertesi gün 06.00'da biten bir çalışma iki günün
ızgarasında da görünüyor, tek blok olduğu anlaşılıyor ve başladığı güne
sayılıyor.

---

## İş 2 — Hafta şeridi (ikincil görünüm)

Satırlarda personel, sütunlarda günler; her gün hücresi **yirmi dört dilimlik bir
mini şerit** ve dolu saatler boyalı. Bir gün hücresine tıklandığında o günün
ızgarasına geçilir.

**Performansa dikkat.** Otuz personel × yedi gün × yirmi dört dilim beş bin
elementten fazla eder; her dilimi ayrı bir DOM düğümü yapmak sayfayı boğar. Mini
şeridi tek bir öğeyle çiz — CSS gradient veya küçük bir SVG. Ölçümü
`PROGRESS_V2.md`'ye yaz.

**Kabul:** Yedi günlük bir dönem otuz personelle akıcı açılıyor; şeritten bir güne
geçiş çalışıyor.

---

## İş 3 — Renk saatin kendisinden

**Dayanak:** SDD 6.3.3.

Renk artık kategorik değil: gece saatleri koyu, gündüz açık, aradaki geçiş
sürekli. Sabit üç ton (gündüz/akşam/gece) kataloglu sürümlere aitti.

- Renk **tek başına bilgi taşımasın.** Renk körlüğü ve yazdırma nedeniyle şeridin
  üzerinde saat aralığı ya da erişilebilir bir etiket bulunmalı.
- Kilitli bloklar ve kapsama açığı işaretleri renk bandından **ayırt edilebilir**
  kalmalı; ikisi de bugün renkle gösteriliyor.

`docs/TASARIM_REFERANSI.md` (sürüm 4) vardiya renk rampasını üç sabit tip için
tanımlıyor ve artık geçersiz. Kanonik doküman değil, benim tarafımda güncellenmesi
gerekiyor — yeni bandı `PROGRESS_V2.md`'ye yaz, ben referansa işlerim.

---

## İş 4 — Hücre düzenleme

Bir personelin gün satırında **sürükleyerek** veya başlangıç ve bitiş saati
seçilerek blok tanımlanır. Görev noktası blok boyunca tektir (SRS H1).

- Sürükleme sırasında oluşacak blok önizlenir; bırakıldığında doğrulama isteği
  gönderilir.
- `asgari_blok_saat` (4) ve `azami_gunluk_saat` (11) sınırları **sürükleme
  sırasında** görünür olsun — kullanıcı geçersiz bir seçim yapıp sonra reddedilmek
  yerine sınırı hissetmeli. Değerler kural kataloğundan okunur, koda gömülmez.
- Mevcut bir bloğun kenarından tutup uzatma/kısaltma da çalışsın.

**Kabul:** Sürükleyerek blok oluşturuluyor, kenarından uzatılıyor; asgari süreden
kısa bir seçim anlaşılır biçimde engelleniyor.

---

## İş 5 — Yazdırma ve CSV

İkisi de hâlâ eski gösterimde. Saat eksenine geçsinler ve **ızgarayla aynı
biçimlendiriciyi** kullansınlar — üçüncü bir kopya çıkmasın (saat metni
biçimleyicisinin üç kopyası bir kez hataya yol açtı).

- Yazdırma: gün ızgarası yatay A4'e sığmalı. Uzun dönemlerde günler sayfaya
  bölünür, saat başlığı her sayfada tekrarlanır.
- CSV: makine okunur biçim korunur; blok başına bir satır, başlangıç ve bitiş
  ISO damgasıyla.

---

## İş 6 — Kural ekranı ve analiz

- Kural ekranı yeni parametreleri göstersin: `asgari_blok_saat`,
  `gece_esigi_saat`. İkisi de düzenlenebilir olmalı — kullanıcı bunları
  değiştirebilmeyi açıkça istedi.
- Analiz ekranındaki gece ve hafta sonu metrikleri saat biriminde; adalet grafiği
  referans çizgisi olarak **kişiye düşen adil payı** göstersin (SRS S2/S3), havuz
  ortalamasını değil.

---

## Turun bitiş kontrolü

- [ ] `tsc -b`, `oxlint` temiz; vitest geçiyor
- [ ] `pytest` tam takım geçiyor (backend'e dokunulmadıysa da koştur)
- [ ] Hafta şeridinin DOM maliyeti ölçülmüş ve `PROGRESS_V2.md`'de
- [ ] Yeni renk bandı `PROGRESS_V2.md`'ye yazılmış (tasarım referansına ben
      işleyeceğim)
- [ ] `git status` temiz, sır yok, `PROGRESS_V2.md` güncel

## Kullanıcının göreceği tur bu

Önceki turlarda ekranı tarayıcıda göremedin (5173 portu başka projede, ekran
girişin arkasında). Aynı durum sürerse:

- Bileşen testleriyle kanıtla ve **hangi davranışın test edilmediğini açıkça
  yaz** — özellikle sürükleyerek düzenleme ve gece yarısını aşan bloğun
  görünümü.
- Turun sonunda bana "şu üç ekranı kendi gözünle aç" diye net bir liste bırak.

Bu turdan sonra depo için ekran görüntüleri alınacak; ekranın gerçekten
kullanılabilir olması, testlerin geçmesinden daha önemli.

## Bu turda yapmayacakların

- **Sürükle-bırak ile atama taşıma** (bir personelden diğerine) — o madde 3 ve
  Tur 11'in işi. Bu turdaki sürükleme, blok tanımlamaktır.
- `GecmisSayaclar` ve kümülatif adalet (Tur 7).
- Ağırlık kalibrasyonu (Tur 9). T-07 ve T-08 biliniyor; ağırlıklara dokunma.
- Excel/analiz dışa aktarma (Tur 10), özet ekranı (Tur 12).
- Sunucuya dağıtım.
