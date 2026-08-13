# Claude Code — Sürüm 2, Tur 5: Gerçek Saatlik Model

## Bağlam — bu tur bir yön değişikliği

Tur 3 ve Tur 4, çalışma zamanını **önceden tanımlı blokların seçimi** olarak
modelledi: kullanıcı Tanımlar ekranında vardiya tipleri tanımlıyor, çözücü onlar
arasından seçiyordu. Bu yaklaşım geri alınıyor.

Yeni model, çalışma zamanını **saatin kendisinden** kurar: karar değişkeni bir
personelin belirli bir saatte çalışıp çalışmadığıdır; bloğun başlangıç saati ve
süresi çözümün **çıktısıdır**. Blok kataloğu, `vardiya_tipi` tablosu ve `gece_mi`
bayrağı kalkar.

Ayrıca **Müracaat görev noktası ve yetkinliği kapsamdan çıkarılıyor**; iş yükü
Güvenlik talebine ekleniyor.

Tur 3 ve Tur 4'ün işinin çoğu ayakta kalıyor: talep ekseni, S1'in saat bazlı
kapsaması, kişiye özel adil pay, H10 kotası, takvim haftası ayrımı, geçmiş
sayaçlar — hepsi korunuyor. Kalkan şeyler yalnızca blok kavramına bağlı olanlar.

### Doküman sürümleri — ilk işin bunları doğrulamak

| Doküman | Sürüm |
|---|---|
| `BOTAS_Vardiya_Cizelgeleme_ProjectCharter.md` | **1.4** |
| `BOTAS_Vardiya_Cizelgeleme_SRS.md` | **1.19** |
| `BOTAS_Vardiya_Cizelgeleme_SDD.md` | **1.27** |
| `BOTAS_Vardiya_Cizelgeleme_Backlog.md` | **1.16** |

Taşımıyorlarsa dur ve bana söyle.

### Okunacaklar

- SRS **TD-1, TD-2, TD-13** (mutlak saat ekseni), **3.3.1** (çalışma zamanı),
  **3.3.2, 3.3.3, 3.3.4** (Müracaat'sız tanımlar), **3.3.5** (parametreler),
  **4.2** (H1, H3, H9), **4.3** (S2, S3, S6)
- SDD **4.2.1** (`atama`), **5.3** (model kurma), **6.3.3** (çizelge)
- `docs/turlar/SAATLIK_MODEL_KARARLARI.md` — M1…M7 ve bölüm 7

## Çalışma kuralları

- Dört kanonik dokümana **dokunmazsın**. Etki doğuran bir şey çıkarsa
  `PROGRESS_V2.md`'ye "DOKÜMAN BORCU" başlığı altında yaz.
- Tasarımdan sapma gerekiyorsa **önce nedenini söyle**, sonra uygula.
- Şema değişikliği yalnızca Alembic göçüyle.
- Git: `add`, `commit`, `tag` senin; `push` ve `remote` **asla**.
- Yeni bir kural asla tek başına eklenmez: sınıf + `modele_ekle` + `dogrula` +
  birim test + kural kayıt defterine kayıt aynı commit'te.
- Yeniden tanımlanan bir kuralın eski testi silinmez, güncellenir; her değişen
  beklenen değerin yanına **neden** değiştiği yazılır.
- Bu tur uzun. Her iş grubundan sonra commit at.

---

## İş 1 — Prototip ölçümü (turun ilk işi, tam uygulamadan önce)

**Bu iş bir karar noktasıdır, bir uygulama adımı değil.**

Saat modeli değişken sayısını düşürür (ince taneli katalogla karşılaştırıldığında
yaklaşık sekiz kat az) fakat **kısıt yapısı ağırdır**: kesintisizlik göstergesi ve
nokta sürekliliği CP-SAT için blok seçiminden zor problemlerdir. K1 kabul kriteri
(40 personel × 28 gün < 60 sn) risk altındadır ve bunu ölçmeden bilemeyiz.

- Modeli **küçük ölçekte** kur: 10 personel, 7 gün, 2 nokta.
- SRS TD-13 ve H1'deki formülasyonu birebir uygula (mutlak eksen, `bas`
  göstergesi, günde tek başlangıç, asgari süre, nokta sabitliği).
- Kapsama için S1'i ekle; diğer kuralları **ekleme** — bu bir performans sondajı,
  tam model değil.
- Süreyi ölç ve `PROGRESS_V2.md`'ye yaz. Sonra ölçeği kademeli büyüt:
  20 personel × 14 gün, 30 × 28, 40 × 28.

**Karar kuralı:** 40 × 28 ölçeğinde ilk uygun çözüme ulaşma süresi 30 saniyeyi
aşıyorsa **dur ve bana bildir**. Tam uygulamaya geçmeden formülasyonu gözden
geçirmemiz gerekir — özellikle nokta sürekliliği kısıtı, gevşetilebilecek ilk
yerdir.

Aşmıyorsa devam et; ölçümü kayıt olarak bırak.

**Kabul:** Dört ölçekte süre ölçülmüş ve kaydedilmiş; karar kuralı uygulanmış.

---

## İş 2 — Göç: blok kavramının kaldırılması

**Dayanak:** SDD 4.2.1, SRS 3.3.2–3.3.4.

Tek bir Alembic göçünde:

- `atama` tablosu: `tarih` ve `vardiya_tipi_id` yerine `baslangic_zamani` ve
  `bitis_zamani` (TIMESTAMPTZ). **Mevcut atamalar dönüştürülür**: bağlı olduğu
  vardiya tipinin başlangıç ve bitiş saatleri, atamanın tarihiyle birleştirilir;
  gece yarısını aşan tiplerde bitiş ertesi güne düşer.
- Dönüşüm **sayılarak doğrulanır**: satır sayısı ve toplam kişi-saat, dönüşüm
  öncesi ve sonrası eşit olmalı. Eşit değilse göç hata verip durmalı.
- Benzersizlik kısıtı `(surum_id, personel_id, baslangic_zamani)` üçlüsüne geçer.
- `personel.sabit_vardiya_tipi_id` düşürülür.
- `vardiya_tipi` tablosu düşürülür (atama ve personel bağları koptuktan sonra).
- `tercih` tablosunda vardiya tipine bağlı alanlar zaman aralığına çevrilir
  (SRS FR-3.2, TD-12): tercih tipi artık "çalışmama" veya "tercih edilen zaman
  aralığı".
- Kural kayıtları: `asgari_blok_saat` = 4 ve `gece_esigi_saat` = 4 eklenir;
  blok kataloğu kısıtına bağlı kalıntılar temizlenir.

**Dikkat — H1'in güvencesi değişiyor.** Eski benzersizlik kısıtı
`(surum_id, personel_id, tarih)` idi ve "günde tek atama"yı veritabanı düzeyinde
zorluyordu. Yeni anahtar başlangıç zamanı içerdiği için aynı günde farklı saatte
başlayan ikinci bir blok veritabanı tarafından yakalanmaz; kural artık yalnızca
uygulama katmanındadır (SDD 4.2.1). Manuel düzenleme yolunun bunu kontrol
ettiğinden emin ol ve bir test yaz.

**Kabul:** Göç sıfırdan çalışır, geri alma yazılmış ve denenmiştir; mevcut demo
verisi dönüşümden sonra aynı toplam kişi-saati verir.

---

## İş 3 — Model kurma

**Dayanak:** SDD 5.3, SRS TD-13.

- Karar değişkenleri `z[p,s]` ve `x[p,s,n]`; `Σ_n x[p,s,n] = z[p,s]`.
- **Eksen mutlaktır**, gün başına sıfırlanmaz. Gün × saat kurgusunda gece yarısını
  aşan çalışma günün sonunda kesilir ve kesintisizlik kısıtı onu iki blok sayar —
  izin verilmesi gereken çalışmayı yasaklar.
- Değişken eleme: müsait olmayan saat, ön koşulu taşımayan nokta, talebin sıfır
  olduğu saat-nokta çifti için **değişken hiç oluşturulmaz**. Oluşturup sıfıra
  sabitlemek aynı sonucu verir ama modeli gereksiz büyütür.
- `bas[p,s]` başlangıç göstergesi ve günde tek başlangıç kısıtı.
- Isıtma penceresi saatleri sabitlenir (TD-5).
- **Saat gruplaması korunur.** Tur 3'te eklenen "aynı kısıtı üreten ardışık
  saatler tek `eksik` değişkeni üretir" optimizasyonu S1 tarafında geçerliliğini
  sürdürür; kaldırma.

**Kabul:** Küçük bir senaryoda çözüm üretiliyor ve çıkan bloklar kesintisiz,
asgari süreye uyuyor, gün içinde nokta değiştirmiyor.

---

## İş 4 — Çözücü çıktısının bloklara toplanması

**Dayanak:** SDD 4.2.1.

Çözücü saat düzeyinde sonuç verir; `atama` blok başına kayıt tutar. Ardışık
çalışma saatleri yazma anında tek bloğa toplanır.

- Toplama, kapsama açığı kayıtlarında kullanılan birleştirme yardımcısından
  geçsin — ikinci bir kopya yazma.
- Gece yarısını aşan blok tek kayıtta durur; `bitis_zamani` ertesi güne düşer.
- Bloğun hangi güne sayıldığı (TD-1) `baslangic_zamani`'ndan türetilir, ayrı
  alanda saklanmaz.

**Kabul:** 20.00'de başlayıp ertesi gün 06.00'da biten bir çalışma tek atama
kaydı olarak yazılıyor ve o gün tek blok sayılıyor.

---

## İş 5 — Kuralların saat modeline uyarlanması

**Yeniden yazılanlar** (SRS 4.2, 4.3):

| Kural | Yeni tanım |
|---|---|
| **H1** | Kesintisizlik + günde tek başlangıç + asgari süre + nokta sabitliği |
| **H3** | Ardışık gece **günü** ≤ N; bir gün, gece saati `gece_esigi_saat`e ulaşıyorsa gece günü |
| **H9** | Günlük toplam saat ≤ `azami_gunluk_saat` |
| **S2** | Gece yükü = ufuk içindeki gece saatlerinin toplamı (`z` üzerinden) |
| **S3** | Hafta sonu yükü = hafta sonu günlerindeki toplam saat |
| **S6** | Ardışık günlerde **fiilî** başlangıç saati kayması (dairesel, tolerans 2 sa) |

**Korunanlar — dokunma:** H2, H4, H5, H6, H7, H8, H10, S1, S4, S5, S7, S8. Bunlar
zaten saat toplamına veya zaman bilgisine bağlıydı.

**`gece_mi` bayrağı tümüyle kalkar.** Gece saati tek bir hesaplanan tanımdır
(SRS TD-2); H3 ile S2 aynı tabandan besleniyor. Bayrağın öneriyle ezilmesi bir kez
yaşanmış ve K3'ün kalmasının nedenlerinden biri olmuştu — o risk artık yapısal
olarak yok, çünkü tek tanım var.

**Kabul:** Çözücü–doğrulayıcı uyum testi 24/24 temiz. Gece yarısını aşan blok
içeren bir senaryoda H3 ve S2 doğru sayıyor.

---

## İş 6 — Müracaat'ın kaldırılması ve gösterim verisi

**Dayanak:** SRS 3.3.2–3.3.4, Charter 1.4.

- Görev noktaları: Vardiya Şefliği, Güvenlik. Yetkinlikler: Güvenlik Görevi
  (taban), Vardiya Şefi.
- Talep SRS 3.3.4'teki tabloya göre: Güvenlik hafta içi 08.00–24.00 arası **9**
  (7 + Müracaat'tan gelen 2). Haftalık toplam 1.152 kişi-saat değişmez.
- Gösterim verisi Müracaat'sız yeniden üretilir; Tur 4'teki senaryolar korunur
  (dengeli, sıkışık, fazla çalışma, kota sınırı) ve **saat modeline göre yeniden
  ayarlanır** — blok uzunlukları artık çözümün çıktısı olduğu için senaryoların
  davranışı değişecektir.
- **K4'ün çelişkili senaryosu şef havuzu üzerinden kurulur**: Vardiya Şefliği
  noktasına yalnız şefler erişebildiğinden, o havuzun bir kısmının izinli olması
  blok uzunluğundan bağımsız olarak açık üretir.

**Kabul:** Dört senaryo da çözülüyor ve farklı davranıyor; çelişkili senaryo
gerçekten açık veriyor.

---

## İş 7 — Arayüzün minimal uyarlaması

**Bu turda yalnız kırık kalmaması sağlanır**; yeni görünümler Tur 6'nın işi.

- Tanımlar'dan **Vardiya Tipi sekmesi** kaldırılır; Personel formundan **Sabit
  Vardiya alanı** kaldırılır.
- Çizelge ızgarası bugün zaten saat aralığı gösteriyor (Tur 4); atama modeli
  değiştiği için veri kaynağı `baslangic_zamani`/`bitis_zamani`'na uyarlanır,
  gösterim aynı kalır.
- Tercih formu zaman aralığı seçimine geçer.
- Analiz ekranındaki gece ve hafta sonu metrikleri saat birimindedir.

**Tur 6'da gelecek (şimdi yapma):** gün ızgarası (24 saat sütunlu ana görünüm),
hafta şeridi (24 dilimlik mini şeritler), saatten hesaplanan renk bandı,
yazdırma ve CSV'nin saat ızgarasına geçmesi.

---

## Turun bitiş kontrolü

- [ ] Prototip ölçümü yapılmış, dört ölçek `PROGRESS_V2.md`'de
- [ ] `pytest` tam takım geçiyor — ters dosya sırasında da
- [ ] `tsc -b`, `oxlint`, `ruff` temiz
- [ ] Uyum testi 24/24
- [ ] **Kabul ölçümü koşuldu**; K1 süresi kaydedildi. K3 ve K4'ün yeni
      tanımlarıyla ölçüldü (Charter 1.4)
- [ ] `vardiya_tipi` kod tabanında ve şemada yok
- [ ] `EK_B_UC_NOKTALAR.md` yeniden üretildi (vardiya tipi uçları düştü)
- [ ] `git status` temiz, sır yok, `PROGRESS_V2.md` güncel

## Bu turda yapmayacakların

- Gün ızgarası ve hafta şeridi görünümleri (Tur 6).
- `GecmisSayaclar` servisi ve kümülatif adalet — `devir[p]` hâlâ personel
  kaydındaki alandan okunuyor.
- Ağırlık kalibrasyonu (Tur 8). T-07'deki kayma biliniyor; ağırlıklara dokunma.
- Excel/analiz dışa aktarma, sürükle-bırak, özet ekranı, belge, hesaplar.
- Sunucuya dağıtım. Bekleyen göçler birikmeye devam ediyor.
