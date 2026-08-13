# Gerçek Saatlik Modele Geçiş — Tasarım Kararları

**Tarih:** 13.08.2026 · **Sürüm:** 2 (parametreler karara bağlandı; zaman ekseni düzeltildi)

Bu not, sistemin blok seçimine dayalı modelden **gerçek saatlik modele** geçişini
tasarlar. `SAATLIK_GECIS_KARARLARI.md`'nin devamıdır; oradaki K1 (çalışma bloğu)
ve K2 (blok kataloğu) kararlarını **geri alır**, kalan kararların çoğunu korur.

> Kanonik doküman değildir. Onaylanan her karar SRS, SDD ve Charter'a işlenir;
> Backlog'un karar günlüğüne gerekçesiyle yazılır.

---

## 0. Neden geri alınıyor

K1'de blok kataloğu yolunu seçtim ve gerekçem şuydu: "tek blok kuralı altında
sürekli zaman modeli aynı çözüm kümesini üretir, karşılığında bir şey vermeden
karmaşıklaştırır." Matematiksel olarak doğruydu; ürün olarak yanlıştı.

Katalog yolu, kullanıcının Tanımlar ekranında **vardiya tanımlamaya devam
etmesi** demekti. Ekranda hâlâ "hangi blokları kullanacağım" sorusu vardı ve
çizelge hâlâ o bloklardan oluşuyordu. İstenen, çizelgenin saatin kendisinden
kurulmasıydı: kimse blok tanımlamayacak, çözücü başlangıç ve süreye kendisi karar
verecek.

Bir de sayısal gerekçe var. İnce taneli bir katalog (her saatte başlayan, 4–11
saat arası her süre) 192 blok eder; 30 kişi × 7 gün × 3 nokta ile yaklaşık 121 bin
ikili değişken. Saat modeli aynı ölçekte 30 × 7 × 24 × 3 ≈ 15 bin değişken
kullanır. "Katalog daha ucuz" gerekçem yalnızca katalog kaba kaldığı sürece
geçerliydi — ki kaba katalog zaten istenen şey değildi.

---

## 1. Model

### M1 — Karar değişkeni mutlak saat eksenindedir

```
S = { 0, 1, …, 24·D−1 }   dönemin (ve ısıtma penceresinin) mutlak saat ekseni
z[p,s] ∈ {0,1}            p kişisi s saatinde çalışıyor
x[p,s,n] ∈ {0,1}          … ve n görev noktasında
```

`x` ile `z` arasında: `Σ_n x[p,s,n] = z[p,s]` — çalışılan her saat tam bir noktaya
aittir.

**Eksen gün başına sıfırlanmaz.** İlk taslakta `z[p,d,t]` (gün × saat) yazmıştım;
bu hatalıdır. Gece yarısını aşan bir çalışma — örneğin 20.00–08.00 — o kurguda
günün sonunda kesilip ertesi günün başında yeniden başlar ve kesintisizlik kısıtı
onu **iki ayrı blok** sayar. Kural, tam da izin verilmesi gereken çalışmayı
yasaklamış olurdu.

Mutlak eksende blok gün sınırını doğal olarak aşar; gün kavramı yalnızca sayım
için kullanılır.

Başlangıç saati ve süre artık **çıktıdır**, girdi değil. `vardiya_tipi` tablosu,
blok kataloğu ve Tanımlar > Vardiya Tipi sekmesi kalkar.

### M2 — Kesintisizlik: günde tek blok

Kullanıcının kuralı — "biri sabah dört saat çalışıp mola verip akşam beş saat daha
çalışmasın" — artık kısıt olarak yazılır:

```
bas[p,s] ≥ z[p,s] − z[p,s−1]            blok başlangıcı göstergesi
bas[p,s] ≤ z[p,s]
bas[p,s] ≤ 1 − z[p,s−1]
∀d :  Σ_{s ∈ gün d} bas[p,s] ≤ 1        günde en fazla bir başlangıç
```

Bir blok başladığı güne sayılır (TD-1 aynen korunur); ertesi güne taşan saatler
yeni bir blok başlangıcı üretmediği için kısıt onları ayrı saymaz. Adalet, H4 ve
H5 hesapları da bloğu başladığı güne yazar.

### M3 — Nokta değiştirme

**Karar (13.08.2026): nokta gün içinde değişmez.** Gerekçe ve reddedilen
alternatif:

- **Serbest:** aynı blok içinde saat saat farklı noktalarda çalışılabilir.
  Sahada anlamsız — kimse dört saat kapıda, dört saat şeflikte durmaz.
- **Sabit (seçilen):** bir blok boyunca nokta değişmez. Kısıt:
  `x[p,d,t,n] ≥ z[p,d,t] + x[p,d,t−1,n] − 1` — dün çalışıyorsa ve bugün de
  çalışıyorsa aynı noktada.

Sabit tutmak hem gerçekçi hem arama uzayını daraltır.

### M4 — Süre ve tavanlar

```
gunluk_saat[p,d] = Σ_t z[p,d,t]
H9:  gunluk_saat[p,d] ≤ azami_gunluk_saat          (11)
```

**Asgari blok süresi eklenir.** Saat modeli, kısıtlanmazsa tek saatlik bloklar
üretebilir; bu sahada anlamsızdır ve çizelgeyi okunamaz kılar. Yeni parametre:
`asgari_blok_saat` = **4** (karar 13.08.2026). Diğer bütün kural parametreleri gibi
Kural ekranından değiştirilebilir; koda gömülmez.

```
gunluk_saat[p,d] ≥ asgari_blok_saat · (o gün çalışıyor mu)
```

---

## 2. Kural kataloğunun durumu

### Korunanlar — formülasyonu değişmeden

H2 (asgari dinlenme), H5 (kayan yedi günlük mutlak tavan), H6 (haftalık izin),
H7 (müsaitlik), H8 (ön koşul yetkinliği), H10 (yıllık kota), S1 (kapsama),
S2/S3/S4 (adalet, kişiye özel adil pay), S5 (tercih), S7 (izole çalışma),
S8 (değişim minimizasyonu).

Bunlar zaten saat üzerinden yazılıydı ya da saat toplamına bağlıydı. Tur 3 ve
Tur 4'ün işi burada boşa gitmiyor.

### Yeniden yazılanlar

| Kural | Eski | Yeni |
|---|---|---|
| **H1** | Günde en fazla bir atama | M2'deki kesintisizlik kısıtı |
| **H3** | Ardışık gece *bloğu* ≤ 3 | Ardışık gece *günü* ≤ 3; bir gün, gece saati `gece_esigi_saat` = **4** değerine ulaşıyorsa gece sayılır (karar 13.08.2026, Kural ekranından değiştirilebilir) |
| **H4** | Ardışık çalışma günü ≤ 6 | Değişmez, `z`den türetilir |
| **S6** | Ardışık günlerde blok başlangıcı kayması | Ardışık günlerde **fiilî** başlangıç saati kayması — başlangıç artık değişken, `b[p,d,t]`den okunur |
| **H9** | Katalogdaki blok süresi ≤ 11 | M4'teki günlük toplam kısıtı |

### Kalkanlar

- **`gece_mi` bayrağı.** Blok kalmadığı için işaretlenecek bir şey yok. Gece
  saati hesaplanan tek tanım olarak kalır (`|blok ∩ [20:00, 06:00]|` yerine
  `Σ_{t ∈ gece} z[p,d,t]`).
- **Blok kataloğu, `vardiya_tipi` tablosu, TD-13, SRS 3.3.1.**
- **K16 (yedi bloklu katalog), K5'in bayrak yarısı, K2.**

---

## 3. Müracaat kaldırılıyor

### M5 — İki görev noktası kalır

Görev noktaları: **Vardiya Şefliği** ve **Güvenlik**. Müracaat noktası ve Müracaat
Görevlisi yetkinliği kalkar; o personel düz güvenlik görevlisi olur.

Talep, Müracaat'ın yükü Güvenlik'e eklenerek korunur — toplam iş yükü değişmez:

| Görev Noktası | Gün Tipi | Aralık | Gereken |
|---|---|---|---|
| Vardiya Şefliği | her gün tipi | 00.00 – 24.00 | 1 |
| Güvenlik | Hafta içi | 08.00 – 24.00 | 9 |
| Güvenlik | Hafta içi | 00.00 – 08.00 | 3 |
| Güvenlik | Hafta sonu / tatil | 00.00 – 24.00 | 3 |

Haftalık toplam yine **1.152 kişi-saat**.

Yetkinlikler ikiye iner: **Güvenlik Görevi** (taban) ve **Vardiya Şefi** (Güvenlik
Görevi'ni de taşır, iki noktada da çalışabilir).

**Kazanç:** erişilebilirlik asimetrisi büyük ölçüde kalkar. Tek noktaya kapalı bir
havuz kalmadığı için K3'te uğraştığımız yapısal sapma kaynağı ortadan kalkar.

**Kayıp:** K4'ün çelişkili senaryosu erişilebilirlik üzerinden kurulmuştu (Tur 4).
Şef havuzu hâlâ ayrıcalıklı — Vardiya Şefliği noktasına yalnız şefler
erişebiliyor — dolayısıyla çelişki şef havuzunun izne çıkmasıyla kurulabilir.
Senaryo yeniden ayarlanacak.

**Not:** kişiye özel adil pay tanımı (SRS 1.17) **kalır**. Müracaat kalkınca sorun
görünmez olur ama tanım doğru olduğu için geri alınmaz; şef havuzu iki noktaya,
düz güvenlik bir noktaya eriştiği için paylar hâlâ farklıdır.

---

## 4. Görünüm

### M6 — Gün seçici + 24 saatlik ızgara

Yedi gün × 24 saat = 168 sütun ekrana sığmaz. İki görünüm birlikte çalışır:

**Ana görünüm — gün ızgarası.** Satırlarda personel, sütunlarda o günün 24 saati.
Dolu saatler renkli, blok tek parça görünür. Üstte gün sekmeleri. İstenen "saat
saat" görünüm budur.

**İkincil — hafta şeridi.** Mevcut haftalık yapı korunur, her gün hücresi 24
dilimlik minik bir şerit olur; dolu saatler renkli. Yedi gün aynı anda görünür,
saat okunurluğu düşük ama genel dağılım görünür. Bir güne tıklayınca ana görünüme
geçilir.

Renk artık blok tipinden değil **saatin kendisinden** gelir: gece saatleri koyu,
gündüz açık, akşam ara ton. Süreklilik bandı, ayrık üç kategori değil.

Yazdırma ve CSV de saat ızgarasına geçer.

---

## 5. Kabul kriterleri

| Kriter | Durum |
|---|---|
| K1 (60 sn) | **Risk altında.** Kısıt yapısı blok seçiminden ağır; değişken sayısı düşük ama kesintisizlik ve nokta sürekliliği CP-SAT için zor. Ölçmeden söz verilemez |
| K2 (sıfır ihlal) | Değişmez |
| K3 (gece adaleti) | Eşik "bir gece bloğu" idi; blok kalmadı. Yeni eşik: **8 gece saati** (karar 13.08.2026). Charter yeniden yazılacak |
| K4 (çelişkili örnek) | Senaryo yeniden ayarlanacak (şef havuzu üzerinden) |
| K5, K6 | Değişmez |

### M7 — Önce prototip, sonra tam uygulama

K1 riski nedeniyle model **önce küçük ölçekte** kurulup ölçülür: 10 personel,
7 gün, 2 nokta. Süre kabul edilebilirse tam uygulamaya geçilir; değilse kısıt
formülasyonu (özellikle nokta sürekliliği) gözden geçirilir.

Bu, tur planına yeni bir adım ekler ve tam uygulamadan önce gelir.

---

## 6. Karara bağlananlar (13.08.2026)

| # | Konu | Karar |
|---|---|---|
| M4 | `asgari_blok_saat` | **4** — kural parametresi, değiştirilebilir |
| H3 | `gece_esigi_saat` | **4** — kural parametresi, değiştirilebilir |
| K3 | Gece adaleti eşiği | **8 gece saati** — Charter yeniden yazılacak |
| M3 | Nokta değiştirme | **Yasak** — blok boyunca nokta sabit |

Açık kalan yok; SRS, SDD ve Charter yazılabilir.

## 7. Atama kaydının biçimi

`atama` tablosu bugün `vardiya_tipi_id` taşıyor; o tablo kalkıyor. İki seçenek
vardı:

- **Saat başına satır** — `(surum_id, personel_id, tarih, saat, nokta_id)`.
  Çözücü çıktısına birebir uyar fakat 30 personel × 7 gün × 8 saat ≈ 1.680 satır
  eder ve her okuma yüzeyi satırları yeniden bloklara toplamak zorunda kalır.
- **Blok başına satır (seçilen)** — `(surum_id, personel_id, baslangic_zamani,
  bitis_zamani, nokta_id, kilitli)`. Yaklaşık 210 satır; manuel düzenleme, sürüm
  karşılaştırması ve dışa aktarma bugünkü yapılarını korur.

Çözücü çıktısı saat düzeyindedir ve yazma anında bloklara toplanır — kapsama
açığı kayıtlarında uygulanan birleştirmenin aynısı, aynı yardımcıyla.

Tarih alanı yerine `baslangic_zamani` kullanılması, gece yarısını aşan bloğun tek
kayıtta durmasını sağlar. Bloğun hangi güne sayıldığı (TD-1) başlangıç zamanından
türetilir, ayrı bir alanda saklanmaz.
