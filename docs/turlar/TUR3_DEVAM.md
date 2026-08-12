# Tur 3 — Devam Yönergesi

Kaldığın yerden sürdür. Aşağıdakiler bu turda alınan kararlar ve önceliğin.

## Önce: iki dosya

1. **`docs/UYGULAMA_PLANI_V2.md` eklendi** — eksikti, haklıydın. Turlar arası sıra
   orada.
2. **Dokümanlar güncellendi:** SDD **1.24**, Backlog **1.10**. SRS 1.15 ve
   Charter 1.2 değişmedi. Bildirdiğin dört doküman borcunun tamamı kapatıldı;
   sürümleri doğrula.

## Doküman borçlarının karşılığı

| Borç | Karar |
|---|---|
| Gün sonunun kodlanışı | Sapman **kabul edildi ve dokümana yazıldı**. SDD 4.2.2: `bitis = 00.00` gün sonu, `bitis < baslangic` gece yarısını aşan aralık. Gerekçesi `vardiya_tipi`nin zaten aynı sözleşmeyi kullanması |
| `cozum_isi.on_kontrol_bulgulari` | SDD 4.2.4'e eklendi |
| Ek B talep uç noktaları | SDD Ek B kayıt tabanlı hâle getirildi (`GET, POST` + `PUT, DELETE /{id}`) |
| FR-1.9 kişi-vardiya türevi | **Backlog B-21** olarak kaydedildi. Şimdilik türev kalabilir; Tur 4'te karışık uzunluklu katalog geldiğinde saat tabanına taşınacak. Ekranda gösterilirken tek uzunluklu katalog varsayımına dayandığı belli olmalı |

## Simetri bulgusu SDD'ye işlendi

Bulduğun şey turun en değerli çıktısıydı ve artık SDD 5.3'te ölçüleriyle birlikte
yazılı (704 → 536 → 0). Gerekçesi olmadan bu gruplama ileride "gereksiz
optimizasyon" diye geri alınabilirdi.

## Blok görünümü türevi — Tur 4'te kalkacak

İkinci sapman doğruydu ve Backlog karar günlüğüne **geçici** olarak kaydedildi.
Bir uyarı: `blok_gorunumu_uret` bir bloğun gereken sayısını "kapsadığı saatlerdeki
en büyük gereken" olarak alıyor. Bu yalnızca **hizalı katalogda** doğru. Tur 4'te
10 ve 12 saatlik bloklar devreye girecek ve türev sessizce yanlış hesaplamaya
başlayacak.

Bu turda yapman gereken: türevi kullanan her yere, tek uzunluklu katalog
varsayımına dayandığını belirten bir yorum bırak. Tur 4'ün ilk işlerinden biri
onu kaldırmak olacak.

## Sıra

`PROGRESS_V2.md`'de yazdığın sırayla devam et:

1. Test fikstürlerini aralık şekline geçir, takımı yeşile çek
2. İş 6 — blok kataloğu kısıtları
3. İş 9 — kapsama oranı atamalardan
4. İş 7 — Talep ekranı (şu an kırık)
5. İş 5'in form tarafı, `kabul_olcumu.py`, `demo_veri_uret.py`
6. Kabul ölçümü koşumu, `EK_B_UC_NOKTALAR.md`, commit'ler

**Commit konusunda:** şu an hiçbir şey commit edilmemiş ve çalışma ağacında bir
göç uygulanmış durumda. Takımı yeşile çeker çekmez ara bir commit at; turun geri
kalanını ondan sonra sürdür. Yarım günlük bir işin tek bir sepette durması
gereksiz risk.

## Kabul ölçümü

Blok kataloğu bu turda büyümediği için K1 süresinin belirgin artmaması bekleniyor.
Simetri gruplamasından **sonraki** süreyi ölç ve `PROGRESS_V2.md`'ye yaz — gruplama
öncesi rakamlar teşhis kaydı olarak kalsın, kabul ölçümü olarak değil.

## Değişmeyenler

- Kural kataloğuna dokunma (H5, H9, H10, S2, S3, S6 ve S1'in üst sınırı Tur 4).
- Blok kataloğunu büyütme — üç blok kalır.
- Dört kanonik dokümana dokunma; yeni borç çıkarsa `PROGRESS_V2.md`'ye yaz.
- Sunucuya dağıtım yok.
