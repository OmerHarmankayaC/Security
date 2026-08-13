# Tur 4 — K3 Kararı ve Kalan Sıra

## K3: eşik değil, hedef yanlıştı

Sorduğun üç seçenekten hiçbiri tek başına yeterli değil, çünkü ölçüm **iki ayrı
sorunu** gösteriyor ve ikincisi daha ağır.

Müracaat bulgusu belirleyici: yedi kişilik havuzun erişebildiği gece talebi kişi
başına en fazla 22,86 saat, hedef 40. O havuz hedefe **hiçbir çizelgeyle**
ulaşamıyor. Hangi eşiği koyarsak koyalım o yedi kişi kalıcı olarak sapmalı
görünür — ölçü ayırt ediciliğini kaybeder. Eşiği ölçeklemek bunu düzeltmez,
gizler.

Bu, bu projede ikinci kez görülen bir kalıp. Önce hiç gece alamayan personel
paydada sayılıyordu (düzeltildi: uygun havuz). Şimdi kısıtlı erişimi olan havuz
tek ortalamaya vuruluyor.

### Karar 1 — Hedef kişiye özel adil paya döner (SRS 1.17)

```
erisebilen(n) = { q ∈ P : q, n noktasının ön koşulunu karşılıyor }
pay_gece[p]   = Σ_{d, t ∈ gece, n : p ∈ erisebilen(n)}
                    talep[d,t,n] / |erisebilen(n)|
P_gece = { p ∈ P : pay_gece[p] > 0 }
∀p ∈ P_gece :
    sapma[p] ≥ gece_yuku[p] − pay_gece[p]
    sapma[p] ≥ pay_gece[p] − gece_yuku[p]
```

Her talep birimi ona erişebilenler arasında eşit bölünür; kişinin hedefi kendi
paylarının toplamıdır. Müracaat görevlisinin hedefi düşük olur çünkü payı
düşüktür — sapma yapısal olmaktan çıkar.

S3 için aynısı `pay_hs[p]` ile. Bu, **S4'ün zaten kullandığı mantıktır**; üç
adalet hedefi de artık kişiye düşen payı ölçer.

`erisebilen(n)` hesabı ön koşul yetkinliğine dayanır (H8), müsaitliğe değil —
müsaitlik dönem içinde değişir, yetkinlik yapısaldır.

### Karar 2 — K3'ün eşiği bir gece bloğu (Charter 1.3)

> Kişi başına düşen gece yükü, kişiye düşen adil paydan **en fazla bir gece
> bloğu kadar** sapar. Ölçünün birimi gece saatidir; eşik, katalogdaki en uzun
> gece bloğunun süresidir ve katalog değiştiğinde kendiliğinden güncellenir.

Sabit bir saat değeri yazmak (8 gibi) katalog her değiştiğinde kriteri elle
yeniden ölçeklemeyi gerektirirdi — bu, önerdiğin 1. seçeneğin zayıf yanı. Oran
(2. seçenek) ise hedef büyüdükçe gevşer, küçüldükçe imkânsızlaşır: 40 saatlik
hedefte %20 sekiz saat, 3 saatlik hedefte 0,6 saat.

Bir gece bloğu, ölçünün doğal tanesidir: bir kişinin bir nöbet fazla veya eksik
alması kabul edilebilir.

### Karar 3 — Ulaşılabilirlik teşhisi kalıcı

Ölçüm betiğinin "her havuz hedefe erişebiliyor mu" teşhisi kalsın ve raporda
görünsün. Bu teşhis bu sorunu iki kez yakaladı; kaldırılırsa üçüncüsünü
yakalayamayız.

## K4: senaryo artık çelişkili değil

Doğru teşhis. On iki saatlik bloklar girince aynı kadro talebi kapatabiliyor —
kırılganlık mekanizması (SRS 3.3.6) blok uzunluğu varsayımına dayanıyordu.

Çelişkiyi kadro üzerinden değil, **erişilebilirlik üzerinden** yeniden kur: tek
noktaya kapalı bir havuzun izne çıkması, blok uzunluğundan bağımsız olarak açık
üretir. Charter'daki K4 ifadesi de saat aralığına güncellendi (1.3).

## Sıra: önce kural düzeltmesi, sonra gösterim verisi

Sorduğun sıraya cevap: **İş 7 ve İş 8'e devam et**, ikisi de bağımsız ve kural
katmanına dokunmuyor. Ama gösterim verisini **kural düzeltmesinden sonra** yap.

Gerekçe: senaryolar kuralların davranışına göre ayarlanacak. Bugünkü hedefle
kurulan bir "dengeli dönem", pay tanımı değiştiğinde dengeli olmaktan çıkabilir
ve iki kez ayarlamak zorunda kalırsın.

Önerilen sıra:

1. İş 7 (çizelge hücresi) ve İş 8 (kota bulguları) — şimdi
2. S2/S3'ün pay tanımı (SRS 1.17) — kural katmanı
3. İş 6'nın gösterim verisi — dört senaryo, gerçekçi adlar, K4 için erişilebilirlik
   tabanlı çelişki
4. Kabul ölçümü — K3 ve K4 bu noktada geçmeli
5. Ek B, `PROGRESS_V2.md`, dalın `main`e alınması

## Doküman sürümleri

| Doküman | Sürüm |
|---|---|
| `BOTAS_Vardiya_Cizelgeleme_ProjectCharter.md` | **1.3** |
| `BOTAS_Vardiya_Cizelgeleme_SRS.md` | **1.17** |
| `BOTAS_Vardiya_Cizelgeleme_SDD.md` | 1.26 (değişmedi) |
| `BOTAS_Vardiya_Cizelgeleme_Backlog.md` | **1.14** |

Charter ilk kez bu aşamada değişiyor — kabul kriterinin kendisi değiştiği için.

## K1 hakkında

1,01 → 3,42 sn beklenen bir artış ve eşiğin çok altında. Ölçümü kayıt için
`PROGRESS_V2.md`'de tut; katalog bir daha büyürse karşılaştırma noktası olacak.
