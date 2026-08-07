# Tasarım Referansı — Figma'dan Frontend'e (Sürüm 2)

Bu doküman **sürüm 2** — önceki "teknik rapor / laboratuvar defteri"
estetiğinden (tuğla kırmızısı, sıfır köşe yarıçapı, ince ayraçlar)
**standart SaaS admin paneli** estetiğine geçildi (mavi vurgu, yuvarlak
köşeler, yumuşak gölgeler). Gün 10'da kurulan Çizelge ve Çözüm ekranları
bu referansa göre yeniden temalandırılmalı.

Kaynak: `https://www.figma.com/design/Ny6877QGaMQxsY0ENextV7`

## Renk Tokenleri (değişti)

| Token | Eski | Yeni | Kullanım |
|---|---|---|---|
| `bg` | `#FAFAF8` | `#F9FAFB` | Sayfa arka planı |
| `surface` | `#FFFFFF` | `#FFFFFF` | Kart/panel arka planı (değişmedi) |
| `ink` | `#1A1A18` | `#111827` | Ana metin |
| `ink-muted` | `#6B6B66` | `#6B7280` | İkincil metin, etiketler |
| `hairline` | `#DEDEDA` | `#E5E7EB` | Kenarlıklar (artık gölgeyle birlikte kullanılıyor, tek başına değil) |
| `accent` | `#B3462B` (tuğla kırmızısı) | **`#2563EB`** (mavi) | Vurgu — aktif nav, birincil buton, kilitli rozet |
| `accent-surface` | `#F5E6E0` | `#EFF6FF` | Vurgu arka planı |
| `warn` | `#B38A2B` | `#B45309` | Uyarı — eksik/gece rozeti |
| `warn-surface` | `#F5EFDD` | `#FEF3C7` | Uyarı arka planı |
| `ok` | `#3E6B4F` | `#15803D` | Olumlu durum |

Bu değerler standart Tailwind renk paletine (`blue-600`, `gray-50/200/500/900`,
`amber-700/100`, `green-700`) karşılık gelecek şekilde seçildi — Tailwind
kurulumunda doğrudan bu isimlerle eşleştirilebilir.

## Köşe Yarıçapı (yeni)

Artık sıfır değil — standart ölçek kullanılır:

| Bileşen | Yarıçap |
|---|---|
| Kartlar/paneller | 8px |
| Buton, girdi, nav öğesi, çizelge hücresi | 6px |
| Durum rozeti | tam yuvarlak (pill, `border-radius: 9999px`) |

## Gölge (yeni)

Kartlar artık yalnızca 1px kenarlıkla değil, hafif bir gölgeyle ayrılıyor:

```css
box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
```

shadcn/ui'daki `shadow-sm` ile birebir aynı. Kenarlık (`hairline`) hâlâ
var ama artık ikincil — gölge birincil ayraç.

## Tipografi

Font ailesi hâlâ **Inter**, ama **Light ağırlığı bırakıldı** — standart
SaaS panellerinde "Light" başlıklar nadir görülür, kararsız/kırılgan
hissettirir. Bunun yerine:

| Kullanım | Ağırlık | Boyut |
|---|---|---|
| Wordmark (sidebar üstü) | Semibold | 16px |
| Ekran başlığı (topbar h1) | Semibold | 18–20px |
| Bölüm etiketi (kart başlıkları) | Medium | 11–12px, KÜÇÜK HARF, hafif harf aralığı |
| Gövde metni | Regular | 13–14px |
| Büyük rakam (istatistik kartları) | Semibold | 24–32px (Light değil — daha vurgulu, standart dashboard hissi) |

Bölüm etiketleri Türkçe büyütülürken hâlâ `toLocaleUpperCase('tr-TR')`
kullanılmalı — bu kural değişmedi.

## Bileşen Kütüphanesi: shadcn/ui + Tailwind

Bundan sonra elle CSS yazmak yerine **shadcn/ui** kullanılacak. Kurulum:

```
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
npx shadcn@latest init
```

`tailwind.config.js`'te yukarıdaki renk tokenleri CSS değişkeni olarak
tanımlanmalı (shadcn'in kendi `init` sihirbazı bunu zaten soruyor —
"Base color: Blue" seçilmeli).

Kullanılacak shadcn bileşenleri (mevcut elle yazılmış karşılıkları):

| Elle yazılmış (Gün 10) | shadcn karşılığı |
|---|---|
| `Buton` (üç varyant) | `Button` (`variant="default"`, `"outline"`, `"ghost"`) |
| `Kart` | `Card`, `CardHeader`, `CardContent` |
| `KartEtiketi` | `CardTitle` (uppercase + tracking için `className` override) |
| `Rozet` | `Badge` (`variant="default"`, `"secondary"`, `"outline"` — renk eşlemesi için `className` override gerekebilir) |
| `BuyukRakam` | Hazır bileşen yok, `<span className="text-3xl font-semibold">` yeterli |
| Metin girişi | `Input` |
| Nav öğesi | shadcn'in hazır bir nav bileşeni yok; mevcut `nav.ts` yapısı korunabilir, yalnızca sınıflar (rounded-md, hover state) shadcn diline uyarlanır |

**Sabit genişlik notu hâlâ geçerli:** Sürümler ekranındaki `Rozet`
bileşeni (veya shadcn `Badge`) metne göre otomatik genişliyor; yan yana
gelen alanları kaydırmaması için hâlâ sabit genişlik (`w-[150px]` gibi)
verilmesi gerekiyor — bu, kütüphane değişse de geçerliliğini koruyan bir
düzen kuralıdır.

## Sayfa İskeleti

Genel yapı (sidebar 260px + topbar 88px + içerik) değişmedi. Değişen:
kartlar artık `rounded-lg shadow-sm` (veya shadcn `Card`'ın varsayılanı),
kenarlık artık `border-gray-200` (ince, ikincil).

## Ekran başına notlar (değişmeyenler)

Çizelge hücresi dört durumu (`bos/dolu/eksik/kilitli`), Çözüm'ün üç
kartı, Tanımlar'ın yedi sekmesi, Analiz'in çubuk grafiği — yapısal
düzenleri aynı kaldı, yalnızca görsel dil değişti. Önceki sürümdeki
"Ekran başına notlar" bölümü hâlâ geçerli, yalnızca renk/köşe/gölge
değerlerini bu dokümandaki yeni tokenlerle değiştirin.
