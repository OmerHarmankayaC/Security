# Tasarım Referansı — "Kontrol Odası" (Sürüm 3)

Bu doküman **sürüm 3** ve önceki iki sürümün yerini tamamen alır. Sürüm 1
(laboratuvar defteri, tuğla kırmızısı) ve sürüm 2 (standart SaaS, mavi)
artık geçerli değildir — kodda o sürümlere ait renk, köşe yarıçapı ve
tipografi kalıntısı kalmamalıdır.

Kaynak: `https://www.figma.com/design/6Fc03g7QRQFQuQX1KmIVQj` →
"Prototip — Tüm Ekranlar" sayfası, `— Kontrol Odası` son ekli 14 ekran.
Aşağıdaki bütün değerler o dosyadan doğrudan okunmuştur.

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
| `chrome/ink` | `#E6EAE6` | Şasi üzerindeki ana metin |
| `chrome/ink-muted` | `#909BA6` | Şasi üzerindeki ikincil metin, grup başlıkları |

### Tuval (içerik alanı — açık)

| Token | Değer | Kullanım |
|---|---|---|
| `canvas` | `#EFF1EE` | Sayfa zemini (sıcak gri, mavi değil) |
| `surface` | `#FFFFFF` | Kart zemini |
| `sunken` | `#E4E7E1` | Gömük alanlar, tablo başlık şeridi |
| `rule` | `#D2D7CE` | Kart kenarlığı ve satır ayraçları |
| `rule-strong` | `#A9B1A3` | Vurgulu ayraç |
| `ink` | `#171B18` | Ana metin |
| `ink-muted` | `#5D655C` | Etiketler, ikincil metin |

### Anlam renkleri

| Token | Değer | Kullanım |
|---|---|---|
| `accent` | `#0F6E63` | Derin teal — birincil buton, seçim, etkileşim |
| `accent-soft` | `#DCE9E6` | Teal'in yumuşak zemini |
| `signal` | `#D2521E` | Turuncu — **yalnızca** dikkat gerektiren durum (kapsama açığı, uyarı) |
| `signal-soft` | `#F7E2D6` | Turuncunun yumuşak zemini |

**Kural:** teal kapsama durumu için kullanılmaz, turuncu da etkileşim için
kullanılmaz. İkisinin işi ayrıdır ve karıştırılmaz.

### Vardiya kodlaması (yalnızca Çizelge ızgarası)

| Token | Değer | Kullanım |
|---|---|---|
| `vardiya/gunduz` | `#FFFFFF` | Gündüz vardiyası hücresi |
| `vardiya/aksam` | `#C7CEC0` | Akşam vardiyası hücresi |
| `vardiya/gece` | `#2F3A38` | Gece vardiyası hücresi (koyu) |
| `vardiya/gece-ink` | `#E8EBE5` | Gece hücresi üzerindeki metin |
| `vardiya/gece-ink-muted` | `#99A29A` | Gece hücresi üzerindeki ikincil metin |

Vardiya tipi hücrenin **kendi dolgusudur**, kenarındaki ince bir bant
değil. Boş hücre düz beyazdır. Kapsama şeridinde karşılanan noktalar nötr
gri, yalnızca açık olanlar turuncudur — yani göz doğrudan soruna gider.

## Tipografi

Font ailesi: **IBM Plex** (Sans / Sans Condensed / Mono). Inter
kullanılmaz.

Figma'da tanımlı stiller ve birebir karşılıkları:

| Stil adı | Font | Boyut | Harf aralığı | Kullanım |
|---|---|---|---|---|
| `başlık/ekran` | IBM Plex Sans SemiBold | 18 | 0 | Üst çubuktaki ekran adı |
| `başlık/bölüm` | IBM Plex Sans SemiBold | 15 | 0 | Kart başlığı |
| `gövde/regular` | IBM Plex Sans Regular | 13 | 0 | Gövde metni |
| `gövde/medium` | IBM Plex Sans Medium | 13 | 0 | Vurgulu gövde |
| `gövde/semibold` | IBM Plex Sans SemiBold | 13 | 0 | Güçlü vurgu |
| `etiket/caps` | IBM Plex Sans Condensed Medium | 10 | %14 | KÜÇÜK HARF etiketler |
| `etiket/mono-caps` | IBM Plex Mono SemiBold | 11 | %6 | Tablo başlıkları |
| `veri/mono-küçük` | IBM Plex Mono Regular | 10 | 0 | Yoğun tablo verisi |
| `veri/mono` | IBM Plex Mono Regular | 12 | 0 | Normal veri |
| `sayı/orta` | IBM Plex Mono SemiBold | 14 | 0 | Metrik değeri |
| `sayı/büyük` | IBM Plex Mono SemiBold | 24 | 0 | Öne çıkan sayı |

**Sayı her yerde Mono.** Tarih, saat, ceza puanı, personel sayısı — hepsi
IBM Plex Mono ile yazılır, böylece rakamlar sütun halinde hizalanır. Bu,
bir tablo aracında okunabilirliğin en büyük tek kazancıdır.

Türkçe büyük harfe çevirirken **her zaman**
`toLocaleUpperCase('tr-TR')` — düz `toUpperCase()` "i" harfini noktasız
"I" yapar ve yanlıştır.

## Köşe Yarıçapı ve Gölge

Bu tasarımda köşeler **çok az** yuvarlatılır ve **gölge yoktur**.

| Öğe | Yarıçap |
|---|---|
| Kart / panel | 4px |
| Buton, menü öğesi, sekme, hücre | 3px |

Ayrım gölgeyle değil, 1px `rule` kenarlıkla yapılır. Sürüm 2'deki
`shadow-sm` tamamen kaldırılmalıdır.

## Sayfa İskeleti

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
  - Öğeler arası 2px, öğe yüksekliği 34px, yarıçap 3px
  - **Aktif öğe:** zemin `chrome/raised`, metin `chrome/ink`
  - **Pasif öğe:** zemin yok, metin `chrome/ink-muted`
- **Alt grubu** (en altta): **Dönem bloğu** — üstte 1px `chrome/line`
  ayraç, altında "PLANLAMA DÖNEMİ" (`etiket/caps`), tarih aralığı
  (`sayı/orta`, mono), "7 gün · 3×8 vardiya" (`veri/mono-küçük`)

  Blok, ekranda **seçili** olan dönemi gösterir. Dönem seçimi olmayan
  ekranlarda geçerli dönem kuralına düşer: bugünü içeren dönem, yoksa en
  yakın gelecek dönem, o da yoksa en son geçmiş dönem.

> **Değişiklik (arayüz turu).** Tanımlar sekmelerinin eylem butonu artık
> yan menünün altında **değil**, üst çubuğun sağındadır — bkz. "Ana alan
> → Üst çubuk". Neden: buton yalnızca bazı sekmelerde vardı ve
> "Değiştir"/"Sil" eklenince üçlü, üzerinde işlem yaptığı listeden iki
> sütun uzakta kalıyordu. Yan menü bağlam taşır, eylem taşımaz.

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

### Sekme çubuğu (Tanımlar)

Sekmeler arası 2px, iç boşluk 10/16, yarıçap 3. Aktif sekme `accent-soft`
zemin + `accent` metin; pasif sekme zeminsiz + `ink-muted` metin.

## Ekran envanteri

Yedi Tanımlar sekmesi tek bir ekran altında toplanır; toplam sekiz ana
ekran vardır.

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

## Uygulama notları

**Tailwind eşlemesi.** Bu paletin hiçbiri Tailwind'in varsayılan
renklerine karşılık gelmez. Proje Tailwind v4 kullanıyor; tokenler
`tailwind.config.js` içinde değil, `index.css`'teki `@theme` bloğunda
tanımlanır. İsimleri yukarıdaki token adlarıyla birebir tutun
(`chrome-base`, `canvas`, `accent`, `signal`, `vardiya-gece` …).
Rastgele Tailwind rengi (`gray-800`, `teal-700` gibi) kullanmayın.

**Genişleyen bileşenlere sabit genişlik.** Metnine göre büyüyen bir öğe
(durum rozeti gibi) bir satırdaki sonraki alanları kaydırır. Bu tasarımda
daha önce iki kez yaşandı. Yan yana hizalanması gereken alanlarda sabit
genişlik verin.

**Ekran yüksekliği.** Kural sekmesi ve Analiz ekranı 900px'i tam
doldurur. Gerçek üründe içerik alanı kaydırılabilir olmalı; tasarımdaki
sıkışıklık bir kısıt değil, o ekranın yoğunluğunun göstergesidir.
