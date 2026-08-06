# Tasarım Referansı — Figma'dan Frontend'e

Bu doküman, `https://www.figma.com/design/Ny6877QGaMQxsY0ENextV7` adresindeki
tasarımın React'e dökülürken ihtiyaç duyulacak kesin değerlerini içerir.
Görsel referans için aynı klasördeki PNG dışa aktarımlarına bakılmalı — bu
doküman onların tamamlayıcısı, yerine geçeni değil.

## Estetik yönelim

"Teknik rapor / laboratuvar defteri" — Inter Light başlıklar, ince ayraç
çizgileri, tuğla kırmızısı vurgu, sıfır köşe yarıçapı (hiçbir yerde
`border-radius` yok, tek istisna: Özet ekranındaki küçük durum noktaları,
onlar da yalnızca çok küçük bir görsel ayrıntı).

## Renk Tokenleri

| Token | Hex | Kullanım |
|---|---|---|
| `bg` | `#FAFAF8` | Sayfa arka planı |
| `surface` | `#FFFFFF` | Kart/panel arka planı |
| `ink` | `#1A1A18` | Ana metin |
| `ink-muted` | `#6B6B66` | İkincil metin, etiketler |
| `hairline` | `#DEDEDA` | Kenarlıklar, ayraç çizgileri (1px) |
| `accent` | `#B3462B` | Vurgu — aktif nav, birincil buton, kilitli rozet |
| `accent-surface` | `#F5E6E0` | Vurgu arka planı (aktif nav, ilerleme kartı) |
| `warn` | `#B38A2B` | Uyarı — eksik/gece rozeti |
| `warn-surface` | `#F5EFDD` | Uyarı arka planı |
| `ok` | `#3E6B4F` | Olumlu durum (dolu rozet metni) |

## Tipografi

Font ailesi: **Inter**. Kullanılan ağırlıklar: Light, Regular, Medium.

| Kullanım | Ağırlık | Boyut | Satır yüksekliği |
|---|---|---|---|
| Wordmark (sidebar üstü) | Light | 17px | — |
| Ekran başlığı (topbar h1) | Regular | 20px | %130 |
| Bölüm etiketi (kart başlıkları, KÜÇÜK HARF) | Medium | 11px | harf aralığı %3–6 |
| Gövde metni | Regular | 13px | %145 |
| Büyük rakam (istatistik kartları) | Light | 26–36px | — |

Bölüm etiketleri her zaman büyük harfle yazılır ve Türkçe'de
`toLocaleUpperCase('tr-TR')` ile büyütülmelidir — düz `.toUpperCase()`
kullanmayın, "İ"/"ı" harflerini yanlış çevirir (bu hata tasarım
dosyasında bir kez yaşandı ve düzeltildi).

## Boşluk Ölçeği

`4 / 8 / 16 / 24 / 40` px — bunun dışında değer kullanılmamalı.
Kart iç boşluğu (padding) genelde 32px, hücre/satır arası 16px.

## Sayfa İskeleti (tüm sekiz ekranda ortak)

- Toplam genişlik 1440px, yükseklik 900px (masaüstü referansı)
- Sol sidebar: 260px sabit genişlik, `surface` arka plan, sağında 1px `hairline` kenarlık
  - Üstte wordmark ("Vardiya Çizelgeleme"), altında 24px boşluk
  - Sekiz nav öğesi, dikey sıralı, 4px aralıkla: Özet, Tanımlar, Müsaitlik, Tercihler, Çizelge, Çözüm, Analiz, Sürümler
  - Aktif öğe: `accent-surface` arka plan + `accent` metin + Medium ağırlık
  - Pasif öğe: şeffaf arka plan + `ink-muted` metin + Regular ağırlık
- Üst çubuk (topbar): 88px yükseklik, `surface` arka plan, altında 1px `hairline`, 40px yatay padding
  - Sol: ekran başlığı (bazen alt satırda ikincil bilgi, örn. "Taslak · Son güncelleme...")
  - Sağ: varsa aksiyon butonları
- İçerik alanı: 40px yatay / 32px dikey padding, kartlar arası 24px boşluk

## Bileşenler

**Buton** — üç varyant, hepsi köşesiz, 10px dikey / 18px yatay padding, 13px Medium metin:
- `birincil`: `accent` arka plan, beyaz metin, kenarlıksız
- `ikincil`: şeffaf arka plan, `ink` metin, 1px `ink` kenarlık
- `hayalet`: şeffaf arka plan, `ink-muted` metin, 1px `hairline` kenarlık

**Durum Rozeti** — üç varyant, 3px dikey / 8px yatay padding, 11px Medium metin, %4 harf aralığı, KÜÇÜK HARF:
- `dolu`: `bg` arka plan, `ok` metin
- `eksik`: `warn-surface` arka plan, `warn` metin
- `kilitli`: `accent-surface` arka plan, `accent` metin

Not: Sürümler ekranında bu bileşen metne göre otomatik genişlediği için
farklı uzunluktaki etiketler (`TASLAK` / `YAYINLANDI` / `ARŞİV`) satırları
kaydırabilir — React'te bu rozete **sabit genişlik** (örn. 150px) vermek
gerekiyor, aksi halde yan yana gelen alanlar hizasız görünür.

**Tablo satırı** — sabit 32–40px yükseklik (yoğun tablolarda 28px), her
hücre sabit genişlik, dikey ortalanmış metin. Başlık satırı 11px Medium,
`ink-muted`, KÜÇÜK HARF; veri satırı 13–14px Regular/Medium, `ink`.

**Çizelge hücresi** — 96×44px, dört durum: `bos` (kenarlıksız), `dolu`
(`surface` arka plan + `hairline` kenarlık), `eksik` (`warn-surface` +
`warn` kenarlık), `kilitli` (`accent-surface` + `accent` kenarlık).

## Ekran başına notlar

- **Çizelge:** satırlar personel, sütunlar gün (kısaltma + tarih, örn.
  "PZT 3"). Hücreler yukarıdaki dört durumu kullanır.
- **Çözüm:** üç kart dikey sıralı — Ayarlar (dönem seçici + zaman limiti
  girişi + Ön Kontrol/Çözümü Başlat butonları), İlerleme (`accent-surface`
  arka plan, üç büyük rakam: geçen süre / en iyi ceza / kapsama açığı +
  Durdur butonu), Sonuç Özeti (kural bazlı ceza dökümü listesi).
- **Tanımlar:** yedi sekme (Personel, Yetkinlik, Bina, Görev Noktası,
  Vardiya Tipi, Talep, Kural). Talep sekmesinde ayrıca "Yük Göstergesi"
  kartı (`accent-surface` arka plan) — dört büyük rakam. Kural sekmesinde
  iki ayrı tablo (Zorunlu Kısıtlar H1-H8, Esnek Hedefler S1-S8+S6b),
  28px satır yüksekliği (diğer tablolardan daha sıkışık, on altı satır
  sığdırmak için).
- **Analiz:** üstte dört metrik kartı, altında çubuk grafikli ceza
  dökümü tablosu (çubuk: `hairline` kenarlıklı track + `accent` dolgu,
  genişlik yüzdeyle orantılı).
- **Sürümler:** her sürüm bir kart, yatay sıralı alanlar (rozet + Sürüm +
  Tarih + Toplam Ceza + Kapsama Açığı), her alan sabit genişlik
  (110/190/130/150px) — hizalama için zorunlu, yukarıdaki rozet notuna
  bakın.
