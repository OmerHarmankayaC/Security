# Tasarım Referansı — Çizelge Renk Bandı (sürüm 5 için)

> Bu metin `docs/tasarim/TASARIM_REFERANSI.md` içindeki **vardiya renk rampası**
> bölümünün yerine geçer. Sürüm 4'teki üç sabit ton (gündüz / akşam / gece)
> çalışma zamanının kataloglu olduğu sürümlere aitti ve artık geçersizdir.

## Neden değişti

Çalışma zamanı artık bir katalogdan seçilmiyor; çözücü başlangıç ve süreye kendisi
karar veriyor (SRS TD-13). Kategorik renk, kategorinin kendisi kalktığı için
tanımsız kaldı: 06.00–16.00 ile 08.00–20.00 arasında "hangi vardiya" sorusunun
yanıtı yok, ama "günün hangi saatinde" sorusunun yanıtı var.

## Band

Renk, hücrenin temsil ettiği saatin gün içindeki konumundan hesaplanır:

```
aydinlik(s) = ( 1 − cos( 2π · (s − 1) / 24 ) ) / 2        s ∈ [0, 24)
```

- Dip **01.00** — günün en koyu noktası
- Tepe **13.00** — günün en açık noktası
- Uçlar mevcut paletten: `#2F3A38` (koyu) → `#E9E7D9` (açık)

Kosinüs eğrisi seçilmesi, geçişin gün başında ve sonunda yumuşamasını sağlar;
doğrusal bir band gece yarısında sert bir kesme üretir ve gece yarısını aşan
blokları ikiye bölünmüş gibi gösterir.

## Bandın taşımadığı bilgi

Renk **tek başına bilgi taşımaz**. Üç şey bandın dışında kalır:

| Bilgi | Gösterim |
|---|---|
| Saat aralığı | Şeridin üzerinde metin — her zaman görünür |
| Kilitli blok | Eğik tarama dokusu (renk değil) |
| Kapsama açığı | ▲ simgesi ve eksik kişi sayısı |

Gerekçe iki katlı: renk körlüğü, ve arka plan basımı kapalıyken yazdırılan
çizelgede bandın tümüyle kaybolması. Yazdırılan bir çizelge, ekrandaki kadar
okunabilir olmak zorundadır — o çizelge vardiya odasının duvarına asılır.

## Uygulama notu

Band `blok.ts` üzerinden okunur; ızgara, hafta şeridi ve yazdırma aynı kaynağı
kullanır. Hafta şeridindeki yirmi dört dilimlik mini gösterim ayrı elementlerle
değil tek bir CSS gradient ile çizilir — otuz personelin yedi günü beş binden
fazla düğüm ederdi.
