# Tasarım Referansı — "Kontrol Odası" (Sürüm 4)

Bu doküman **sürüm 4** ve önceki bütün sürümlerin yerini tamamen alır.
Sürüm 1 (laboratuvar defteri, tuğla kırmızısı), sürüm 2 (standart SaaS,
mavi) ve sürüm 3 (Kontrol Odası, IBM Plex) artık geçerli değildir —
kodda o sürümlere ait renk, köşe yarıçapı, **font** ve tipografi
kalıntısı kalmamalıdır.

Kaynak: `https://www.figma.com/design/1ynL8CUkC8tnIkbhRFMo6g` →
"Prototip — Tüm Ekranlar" sayfası, `v4` son ekli 20 ekran.
Aşağıdaki bütün değerler o dosyadan doğrudan okunmuştur.

> **Dosya notu.** Sürüm 3'ün kaynağı olan `6Fc03g7QRQFQuQX1KmIVQj`
> (BOTAS_deneme) dosyasındaki ekranlar hâlâ Plex tipografisi ve beyaz
> gündüz rengiyle duruyor. Kanonik kaynak artık yukarıdaki dosyadır;
> eski dosya yalnızca geçmiş kaydıdır.

## Sürüm 3 → 4 arasında ne değişti

Tasarımın **iskeleti, paleti ve fikri aynı kaldı.** Değişenler beştir:

1. **Tipografi tamamen değişti.** IBM Plex ailesi bırakıldı; yerine
   Public Sans (arayüz) + Azeret Mono (sayı) geldi. Gerekçe: Plex,
   Inter/Manrope/Space Grotesk gibi üretken araçların varsayılan
   repertuvarıyla aynı kümede okunuyordu. Public Sans kamu tasarım
   sistemi kökenli, hiçbir dönemde moda olmadı.
2. **Tip ölçeği bir kademe büyüdü.** Gövde 13 → 14, ekran başlığı
   18 → 21, mono veri 10 → 11,5.
3. **Yan menüye simgeler eklendi.** Sekiz gezinme öğesinin hepsinde.
4. **Gündüz vardiyası artık düz beyaz değil.** `#FFFFFF` → `#E9E7D9`.
5. **Binlik ayracı kaldırıldı.** Ne boşluk ne nokta: `8240`.

## Tasarım fikri

Bir vardiya çizelgeleme aracı, bir pazarlama sayfası değil bir **operasyon
konsoludur**. Yön buradan çıkıyor: koyu, sabit bir "şasi" (yan menü ve üst
çubuk) içinde açık renkli bir çalışma tuvali. Şasi bağlamı taşır ve göz
onu bir süre sonra görmez; tuval veriyi taşır ve tüm dikkat oradadır.

Renk hiçbir yerde dekorasyon değil, her zaman bir anlam taşır: teal
etkileşim ve seçim, turuncu yalnızca dikkat gerektiren durum, vardiya
tonları çizelge ızgarasında vardiya tipini kodlar.

## Renk Tokenleri

Değişken koleksiyonu adı: **Kontrol Odası**

### Şasi (yan menü, üst çubuk — koyu)

| Token | Değer | Kullanım |
|---|---|---|
| `chrome/base` | `#1A1F26` | Yan menü zemini |
| `chrome/raised` | `#2A323C` | Aktif menü öğesi zemini |
| `chrome/line` | `#39424E` | Şasi içi ayraçlar |
| `chrome/ink` | `#E6EAE6` | Şasi üzerindeki ana metin, **aktif menü simgesi** |
| `chrome/ink-muted` | `#909BA6` | Şasi üzerindeki ikincil metin, grup başlıkları, **pasif menü simgesi** |

### Tuval (içerik alanı — açık)

| Token | Değer | Kullanım |
|---|---|---|
| `canvas` | `#EFF1EE` | Sayfa zemini (sıcak gri, mavi değil) |
| `surface` | `#FFFFFF` | Kart zemini, **boş çizelge hücresi** |
| `sunken` | `#E4E7E1` | Gömük alanlar, tablo başlık şeridi |
| `rule` | `#D2D7CE` | Kart kenarlığı ve satır ayraçları |
| `rule-strong` | `#A9B1A3` | Vurgulu ayraç |
| `ink` | `#171B18` | Ana metin |
| `ink-muted` | `#5D655C` | Etiketler, ikincil metin |

### Anlam renkleri

| Token | Değer | Kullanım |
|---|---|---|
| `accent` | `#0F6E63` | Derin teal — birincil buton, seçim, etkileşim, **bugün işareti** |
| `accent-soft` | `#DCE9E6` | Teal'in yumuşak zemini |
| `signal` | `#D2521E` | Turuncu — **yalnızca** dikkat gerektiren durum (kapsama açığı, uyarı) |
| `signal-soft` | `#F7E2D6` | Turuncunun yumuşak zemini |

**Kural:** teal kapsama durumu için kullanılmaz, turuncu da etkileşim için
kullanılmaz. İkisinin işi ayrıdır ve karıştırılmaz.

### Vardiya kodlaması (Çizelge ızgarası + çalışan paneli takvimi)

| Token | Değer | Kullanım |
|---|---|---|
| `vardiya/gunduz` | `#E9E7D9` | Gündüz vardiyası hücresi (**sürüm 3'te beyazdı**) |
| `vardiya/aksam` | `#C7CEC0` | Akşam vardiyası hücresi |
| `vardiya/gece` | `#2F3A38` | Gece vardiyası hücresi (koyu) |
| `vardiya/gece-ink` | `#E8EBE5` | Gece hücresi üzerindeki metin |
| `vardiya/gece-ink-muted` | `#99A29A` | Gece hücresi üzerindeki ikincil metin |

Vardiya tipi hücrenin **kendi dolgusudur**, kenarındaki ince bir bant
değil. Dört basamaklı bir ramp kurulur ve basamaklar hem açıklık hem
sıcaklık ekseninde ayrışır:

```
boş #FFFFFF  →  gündüz #E9E7D9  →  akşam #C7CEC0  →  gece #2F3A38
   (beyaz)       (soluk sıcak)      (yeşile çalan)      (koyu)
```

Gündüzün beyazdan çıkarılmasının sebebi: beyaz gündüz hücresi boş
hücreden yalnızca içindeki yazıyla ayrılıyordu, yani renk hiçbir iş
yapmıyordu.

Kapsama şeridinde karşılanan noktalar nötr gri, yalnızca açık olanlar
turuncudur — yani göz doğrudan soruna gider.

## Tipografi

İki aile kullanılır:

- **Public Sans** — arayüz, gövde, başlık, etiket. ABD kamu tasarım
  sistemi (USWDS) için çizilmiş, Franklin Gothic kökenli kurumsal
  grotesk. Türkçe karakter desteği tam.
- **Azeret Mono** — bütün sayılar ve kod benzeri veri.

Ayrı bir display/başlık fontu **yoktur**; ekran başlığı da Public Sans
SemiBold'dur.

> **Condensed yok.** Sürüm 3'teki `IBM Plex Sans Condensed` rolünü
> Public Sans karşılamıyor, çünkü ailenin dar bir kesimi yok. BÜYÜK HARF
> etiketler bunun yerine **Public Sans Medium + %14 harf aralığı** ile
> yapılır; aynı işlevi görür, biraz daha geniş yer kaplar.

| Stil adı | Font | Boyut | Harf aralığı | Kullanım |
|---|---|---|---|---|
| `başlık/ekran` | Public Sans SemiBold | 21 | 0 | Üst çubuktaki ekran adı |
| `başlık/bölüm` | Public Sans SemiBold | 17 | 0 | Kart başlığı |
| `gövde/regular` | Public Sans Regular | 14 | 0 | Gövde metni |
| `gövde/medium` | Public Sans Medium | 14 | 0 | Vurgulu gövde |
| `gövde/semibold` | Public Sans SemiBold | 14 | 0 | Güçlü vurgu |
| `etiket/caps` | Public Sans Medium | 11,5 | %14 | BÜYÜK HARF etiketler |
| `etiket/mono-caps` | Azeret Mono SemiBold | 12,5 | %6 | Tablo başlıkları |
| `veri/mono-küçük` | Azeret Mono Regular | 11,5 | 0 | Yoğun tablo verisi |
| `veri/mono` | Azeret Mono Regular | 13 | 0 | Normal veri |
| `sayı/orta` | Azeret Mono SemiBold | 15 | 0 | Metrik değeri |
| `sayı/büyük` | Azeret Mono SemiBold | 26 | 0 | Öne çıkan sayı |

**Sayı her yerde Mono.** Tarih, saat, ceza puanı, sicil numarası,
personel sayısı — hepsi Azeret Mono ile yazılır, böylece rakamlar sütun
halinde hizalanır. Bu, bir tablo aracında okunabilirliğin en büyük tek
kazancıdır.

**Düz cümle asla Mono değildir.** Azeret Mono yalnızca sayı ve koda
ayrılmıştır; bir açıklama satırı sayı içeriyor diye Mono'ya geçmez.

**Azeret Mono geniş bir yüzdür.** Sürüm 3'ün Plex Mono'suna göre yaklaşık
%8 daha çok yer kaplar. Sabit genişlikli hücrelere yerleştirirken
ölçülmesi gerekir; mevcut 20 ekranda taşma olmadığı doğrulanmıştır.

Türkçe büyük harfe çevirirken **her zaman**
`toLocaleUpperCase('tr-TR')` — düz `toUpperCase()` "i" harfini noktasız
"I" yapar ve yanlıştır.

## Sayı biçimi

**Binlik ayracı kullanılmaz.** Ne boşluk, ne nokta, ne virgül:

```
doğru:  8240      10000     1152
yanlış: 8 240     8.240     10,000
```

Ondalık ayracı virgüldür (`3,39` · `0,61`), Türkçe kullanımına uyar.

## Köşe Yarıçapı ve Gölge

Bu tasarımda köşeler **çok az** yuvarlatılır ve **gölge yoktur**.

| Öğe | Yarıçap |
|---|---|
| Kart / panel | 4px |
| Buton, menü öğesi, sekme, hücre | 3px |
| Bugün işareti (daire) | tam yuvarlak |

Ayrım gölgeyle değil, 1px `rule` kenarlıkla yapılır. Sürüm 2'deki
`shadow-sm` tamamen kaldırılmalıdır.

## Sayfa İskeleti (yönetici arayüzü)

Toplam 1440×900. İki sütun: yan menü 260px sabit, ana alan kalan 1180px.

### Yan menü (koyu şasi)

- Zemin `chrome/base`, iç boşluk: üst 26, yan 18, alt 22
- İçerik `SPACE_BETWEEN` ile dağıtılır: üstte navigasyon, altta "Alt" grubu
- **Marka bloğu:** "VARDİYA ÇİZELGELEME" (`chrome/ink`) + altında
  "karar destek aracı" (`chrome/ink-muted`), aralarında 3px
- **Menü grupları** — düz bir liste değil, üç başlık altında toplanır:
  - (başlıksız) → Özet
  - **VERİ** → Tanımlar, Müsaitlik, Tercihler
  - **ÜRETİM** → Çizelge, Çözüm
  - **DEĞERLENDİRME** → Analiz, Sürümler
  - Grup başlıkları `etiket/caps`, `chrome/ink-muted`, üstünde 14px boşluk
  - Öğeler arası 2px, **öğe yüksekliği 40px**, yarıçap 3px
  - **Aktif öğe:** zemin `chrome/raised`, metin ve simge `chrome/ink`,
    solunda 2px `accent` işaret şeridi
  - **Pasif öğe:** zemin yok, metin ve simge `chrome/ink-muted`
- **Alt grubu** (en altta): **Dönem bloğu** — üstte 1px `chrome/line`
  ayraç, altında "PLANLAMA DÖNEMİ" (`etiket/caps`), tarih aralığı
  (`sayı/orta`, mono), "7 gün · 3×8 vardiya" (`veri/mono-küçük`)

  Blok, ekranda **seçili** olan dönemi gösterir. Dönem seçimi olmayan
  ekranlarda geçerli dönem kuralına düşer: bugünü içeren dönem, yoksa en
  yakın gelecek dönem, o da yoksa en son geçmiş dönem.

#### Menü simgeleri

Sekiz gezinme öğesinin hepsinde simge vardır. Kurallar:

- Boyut **17×17px**, kontur kalınlığı 2, dolgu yok — yalnızca kontur
- Simge ile etiket arası **11px**
- Renk metinle aynı: aktifse `chrome/ink`, pasifse `chrome/ink-muted`
- Biçim dili sade geometri; süslü, dolu veya çok detaylı simge yok

| Ekran | Simge |
|---|---|
| Özet | ev / gösterge |
| Tanımlar | veritabanı (yığılmış silindir) |
| Müsaitlik | takvim |
| Tercihler | yıldız |
| Çizelge | ızgara |
| Çözüm | oynat üçgeni |
| Analiz | dikey çubuklar |
| Sürümler | katman |

### Ana alan

- **Üst çubuk:** 64px yükseklik, yatay iç boşluk 28. Solda ekran adı
  (`başlık/ekran`). Sağda ekranın eylemleri, aralarında 8px.

  Tanımlar ekranında bu eylemler **Ekle · Değiştir · Sil** üçlüsüdür ve
  beş tanım sekmesinin (Personel, Yetkinlik, Bina, Görev Noktası, Vardiya
  Tipi) hepsinde aynı sırada, aynı konumda ve aynı görünümdedir. "Ekle"
  birincil (`accent` zemin), diğer ikisi ikincildir; "Değiştir" ve "Sil"
  listeden bir kayıt seçilene kadar pasiftir.

  Talep ve Kural sekmeleri bu üçlünün dışındadır: talep matrisinde
  eklenecek bağımsız bir kayıt yoktur (satırlar görev noktalarından
  türer, hücreler yerinde düzenlenir), kural kataloğunda ise H1–H8 ve
  S1–S8 kodda tanımlı sınıflarla eşleşir; eklenip silinemez, yalnızca
  pasifleştirilir.
- **İçerik:** iç boşluk 28 dikey / 32 yatay, kartlar arası 20px.
  Kart genişliği 1116px (içerik alanının tamamı).

### Kart anatomisi

```
Kart                     zemin surface, 1px rule kenarlık, yarıçap 4
├── kart başlığı         yükseklik 50, iç boşluk 18/24
├── ayraç                1px, rule
├── satır                yükseklik 47, iç boşluk 14/24
├── ayraç                1px, rule
└── satır                …
```

Satırlar arasındaki ayraç 1px `rule`. Kartın kendi içinde ek boşluk veya
gölge yoktur — ritim yalnızca ayraçlarla kurulur.

### Çizelge ızgarası

Büyüyen tipe göre yeniden ölçeklendi:

| Öğe | Sürüm 3 | Sürüm 4 |
|---|---|---|
| Başlık satırı yüksekliği | 46 | **54** |
| Kapsama şeridi yüksekliği | 40 | **46** |
| Personel satırı yüksekliği | 40 | **46** |
| Gösterilen personel satırı | 12 | **10** |
| Personel sütunu genişliği | 220 | 220 |
| Gün sütunu genişliği | 128 | 128 |

**Bugün işareti.** Geçerli günün tarihi, gün başlığında 28px'lik tam
yuvarlak `accent` daire içinde, `chrome/ink` metinle gösterilir.
Takvimlerden tanıdık bir işaret olduğu için açıklama gerektirmez.

### Sekme çubuğu (Tanımlar)

Sekmeler arası 2px, iç boşluk 10/16, yarıçap 3. Aktif sekme `accent-soft`
zemin + `accent` metin; pasif sekme zeminsiz + `ink-muted` metin.

## Çalışan paneli

Yönetici arayüzünden ayrı bir iskelet kullanır. **Yan menü yoktur.**

- **Mobil (birincil):** 390×844. Koyu üst çubuk 64px (ad + sicil + dönem),
  altında koyu sekme çubuğu 44px (üç sekme, aktif sekmede 2px `accent`
  alt çizgi), altında kaydırmalı içerik.
- **Masaüstü:** 1440×900 tuvalin ortasında **720px genişliğinde tek
  sütun** panel. Yatay dolduran bir düzen değildir; mobil düzenin
  genişletilmiş hâlidir.

Üç bölüm: **Vardiyalarım · Dönem Özetim · Tercihlerim**. Tercih formu ayrı
bir sekme değil, Tercihlerim'in üstündedir.

Dönem görünümü takvim gibi yedi sütuna sarmalar; hücre dolgusu aynı
vardiya kodlamasını kullanır. Değişen günlerde hücrenin üstünde 3px
`accent` şerit bulunur.

## Ekran envanteri

Yedi Tanımlar sekmesi tek bir ekran altında toplanır; yönetici tarafında
toplam sekiz ana ekran vardır.

| Ekran | İçerik |
|---|---|
| Özet | Ölçüm sırası (metrik şeridi) + Açık Uyarılar + Yaklaşan Müsaitlik |
| Tanımlar | Sekme çubuğu + seçili sekmenin içeriği |
| → Talep | Talep matrisi (3 nokta × gün tipi/vardiya) + yük göstergesi |
| → Personel | Personel tablosu |
| → Yetkinlik | Üç yetkinlik kartı |
| → Bina | İki bina kartı + açıklama notu |
| → Görev Noktası | Üç nokta kartı |
| → Vardiya Tipi | Üç vardiya tipi kartı |
| → Kural | H1–H8 tablosu + S1–S8/S6b tablosu |
| Müsaitlik | Kapsama riski uyarısı + kayıt tablosu |
| Tercihler | Durum sekmeleri + onayla/reddet listesi |
| Çizelge | Personel × gün ızgarası, vardiya renk kodlu + kapsama şeridi |
| Çözüm | Ayarlar + ilerleme + sonuç özeti (ceza dökümü çubukları) |
| Analiz | Ölçüm sırası + gece/hafta sonu adalet grafiği + saat dengesi tablosu |
| Sürümler | Sürüm kartları + karşılaştır / yayınla / taslak türet |
| **Vardiyalarım** | Sıradaki vardiya + dönem takvimi + liste görünümü |
| **Dönem Özetim** | Gece / hafta sonu / toplam saat, ekip ortalamasıyla eşli çubuk |
| **Tercihlerim** | Son tarih bandı + tercih formu + tercih listesi |

Çalışan panelinin üç ekranı hem mobil hem masaüstü olarak çizilmiştir.

> **Henüz tasarlanmamış.** SDD 6.3.6 (Giriş) ve 6.3.7 (Kullanıcılar)
> ekranları kimlik doğrulama fazıyla birlikte tanımlandı ama Figma'da
> karşılıkları yok. Çizildiklerinde bu dokümana eklenecekler.

## Uygulama notları

**Font yükleme.** Public Sans ve Azeret Mono ikisi de Google Fonts'ta.
Gereken kesimler: Public Sans 400/500/600, Azeret Mono 400/500/600.
Gövde metni için `font-feature-settings` gerekmiyor; Azeret Mono zaten
sabit genişlikli olduğundan `tabular-nums` da gerekmiyor.

**Tailwind eşlemesi.** Bu paletin hiçbiri Tailwind'in varsayılan
renklerine karşılık gelmez. Proje Tailwind v4 kullanıyor; tokenler
`tailwind.config.js` içinde değil, `index.css`'teki `@theme` bloğunda
tanımlanır. İsimleri yukarıdaki token adlarıyla birebir tutun
(`chrome-base`, `canvas`, `accent`, `signal`, `vardiya-gece` …).
Rastgele Tailwind rengi (`gray-800`, `teal-700` gibi) kullanmayın.
Aynı blokta font aileleri de tanımlanır — sürüm 3'ten geçerken
`--font-sans` ve `--font-mono` değerleri mutlaka güncellenmelidir.

**Genişleyen bileşenlere sabit genişlik.** Metnine göre büyüyen bir öğe
(durum rozeti gibi) bir satırdaki sonraki alanları kaydırır. Bu tasarımda
daha önce iki kez yaşandı. Yan yana hizalanması gereken alanlarda sabit
genişlik verin.

**Ekran yüksekliği.** Kural sekmesi ve Analiz ekranı 900px'i tam
doldurur. Gerçek üründe içerik alanı kaydırılabilir olmalı; tasarımdaki
sıkışıklık bir kısıt değil, o ekranın yoğunluğunun göstergesidir.

**Tip büyümesinin bedeli.** Sürüm 4'ün bir kademe büyük ölçeği, sabit
yükseklikli metin kutularını taşırır. Sürüm 3'ten geçerken satır
yükseklikleri ve sabit yükseklikli sarmalayıcılar tek tek gözden
geçirilmelidir; Figma'ya yayarken 30'dan fazla kutu bu yüzden büyütüldü.
