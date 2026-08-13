# Tur 4 — Devam Yönergesi

Kaldığın yerden sürdür.

## Neredesin

Yarım kural katmanı `git stash`ten çıkarıldı ve **`tur4-kural-katmani`** dalına
WIP commit'i olarak alındı (`36ba589` — 24 dosya, 1424 ekleme). `main` 327/327
yeşil ve dokunulmadı. Turun geri kalanını **bu dalda** sürdür; tur bittiğinde
`main`e alınır.

**Önemli:** o commit'e dokümanlar da girdi. `main`de SRS/SDD/Backlog hâlâ eski
sürümde (1.15 / 1.25 / 1.11); güncel sürümler yalnızca bu dalda. Yani sürüm
doğrulamasını **dalda** yap — `main`de yapılırsa haklı olarak başarısız olur.

Ekteki **Backlog 1.13**'ü dala koy (`w1f`'in ayrı kural kaydı olması kararı
işlendi). SRS 1.16 ve SDD 1.26 değişmedi.

İlk iş: `git status` temiz mi, dalda mısın, doküman sürümleri eşleşiyor mu —
üçünü doğrula, sonra testlere geç.

## Doğru yaptığın iki şey

**Sızıntıyı önce ölçtün.** `test_analiz_api` + `test_tanim_api` sırasını ters
çevirip düşen testi göstermek, hem hatanın gerçek olduğunu hem düzeltmenin işe
yaradığını kanıtladı. Ters dosya sırasında da 327/327 alınması B-22'nin gerçek
kabulü — "fikstür yazdım" demek yeterli olmazdı.

**Temizliği testten önce koydun, sonra değil.** Başarısız bir testin verisinin
incelenebilir kalması doğru tercih.

## `w1f` kararı kabul edildi

`w1f`'i S6b emsalinde ayrı bir kural kaydına bölmen doğru ve Backlog karar
günlüğüne işlendi. Gerekçe: ağırlık kullanıcı tarafından ayarlanabilir olmalı
(FR-1.11); S1'in içinde bir sabit olarak kalırsa Kural ekranında görünmez ve
değiştirilmesi kod değişikliği gerektirir.

## Testleri uyarlarken: iki ayrı iş

Elli testin hepsi mekanik değil. Ayır:

**Mekanik** — `Baglam(talep=…)` kalkması, `on_kontrol_yap` imzası, H5'in parametre
adı. Çağrı yeri düzeltmesi; beklenen değer değişmiyor. Ortak yardımcıyı
(`tests/conftest.py`'de blok eksenli test talebini saat eksenine açan kurucu)
yazdıktan sonra kalanı çoğunlukla arama-değiştirme.

**Gerekçeli** — S2 ve S3'ün birimi vardiya sayısından saate döndüğü için beklenen
değerler değişiyor. Bunlar "eski test silinmez, güncellenir" kuralına girer: her
değişen beklenen değerin yanına **neden** değiştiği yazılsın. Sekiz saatlik gece
bloğunda gece yükü 1'den 8'e çıkıyorsa bu bilinçli; testi sessizce yeni değere
çekmek, davranışın kazayla mı değiştiğini gizler.

Bir beklenen değer neden değiştiğini açıklayamıyorsan orada dur — kural
uygulamasında bir hata olabilir.

## Kalan işler

1. **İş 2–5'in testleri** — yukarıdaki ayrımla.
2. **İş 6** — katalog yedi bloğa (SRS 3.3.1) + dört senaryolu gösterim verisi +
   gerçekçi personel adları. Turun görünür çıktısı bu; kadro talebe göre
   boyutlanmazsa H10 hiçbir zaman tetiklenmez ve turun kabulü ölçülemez.
3. **İş 7** — çizelge hücresinde saat aralığı (`08–16 · GÜV`), renk başlangıç
   saati bandından.
4. **İş 8** — ön kontrole kota bulguları.
5. **Kabul ölçümü** — katalog yediye çıktığı için K1 artacak. Eşiğin (60 sn)
   yarısını aşarsa dur ve bana söyle.
6. `EK_B_UC_NOKTALAR.md`, `PROGRESS_V2.md`, dalın `main`e alınması.

## Değişmeyenler

- Ağırlıklara dokunma (kalibrasyon Tur 8). `w1f = 2` başlangıç değeri.
  S2/S3'ün birimi değiştiği için mevcut ağırlıklar ölçek olarak artık yanlış —
  bu **beklenen**, düzeltmesi Tur 8'de.
- `GecmisSayaclar` ve kümülatif adalet Tur 5. `devir[p]` bu turda yalnızca
  personel kaydındaki alandan okunur.
- Dört kanonik dokümana dokunma.
- Sunucuya dağıtım yok.
