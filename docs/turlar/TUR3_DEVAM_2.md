# Tur 3 — Devam Yönergesi 2

Turu bitir. Kalan altı iş aşağıda; hiçbiri kural kataloğuna dokunmuyor.

## Önce: iki düzeltme

**1. Dosya yerleşimi kuralı yazıldı.** `UYGULAMA_PLANI_V2.md`'ye bir bölüm eklendi
ve kural artık tek:

```
docs/                    → kanonik dört doküman + SAATLIK_GECIS_KARARLARI.md
docs/turlar/             → planlar, tur promptları, devam yönergeleri, yapilacaklar
```

`UYGULAMA_PLANI_V2.md` de `docs/turlar/` altına taşınmalı — şu an depo kökünde.
`UYGULAMA_PLANI.md`'yi oraya taşımakla doğru yaptın; ikisi aynı yerde dursun.
Depo kökünde plan veya prompt dosyası kalmayacak. Güncellenmiş plan dosyası
ekte; eskisinin yerine koy.

**2. `PROGRESS_V2.md`'deki "DOKÜMAN BORCU" bölümü artık yanlış.** Dört maddenin
tamamı SDD 1.24 ve Backlog 1.10 ile kapatıldı, ama bölüm hâlâ açıkmış gibi
duruyor. Bölümü "kapatıldı" olarak işaretle veya kaldır — sonraki oturum bunu
açık borç sanarak ikinci kez çözmeye kalkar.

## Doğru yaptığın bir şey

Önceki oturumun kaydındaki İş 8 ve İş 10 maddelerini hatırlamadığın hâlde kabul
etmeyip **koda bakıp doğrulaman** doğru refleksti. Kayıt kendi başına kanıt
değildir; kanıt kodun kendisidir. Bundan sonra da böyle yap.

## Kalan işler

Sırayla:

1. **İş 7 — Talep ekranı.** Uç noktalar hazır ve testli, ekran hâlâ eski matrisi
   çiziyor ve kırık. Her satırı bir aralık olan liste: nokta, gün tipi, başlangıç,
   bitiş, gereken sayı; ekle / düzenle / sil; çakışan aralıkta anlaşılır hata
   (409). **Minimal uyarlama** — görsel geliştirme Tur 6'nın işi, şimdi işlevsel
   olması yeterli.

2. **İş 6 — Blok kataloğu kısıtları.** Aynı `(baslangic_saati, sure_saat)` ikinci
   kez tanımlanamaz; süre günlük azami çalışma saatini (11) aşamaz. İkisi de
   **girişte** reddedilir. Değeri kural kataloğundan okunacak bir parametre olarak
   tasarla — H9 Tur 4'te yazılacak ve aynı değeri kullanacak; parametre henüz
   yoksa geçici bir yapılandırma değeri kullan ve `PROGRESS_V2.md`'ye not düş.

3. **İş 5'in form tarafı.** `devir_fazla_calisma_saat` ve `kota_yili` personel
   formunda. Boş bırakıldığında 0. Bu turda hiçbir kural bu alanları okumaz.

4. **Blok görünümü türevine varsayım yorumu.** `blok_gorunumu_uret`'i kullanan her
   yere, tek uzunluklu katalog varsayımına dayandığını belirten bir yorum bırak.
   Tur 4'te 10 ve 12 saatlik bloklar girecek ve türev sessizce yanlış hesaplamaya
   başlayacak; yorumlar onu bulmayı kolaylaştırır.

5. **Kabul ölçümü** (`scripts/kabul_olcumu.py`). K1 süresini `PROGRESS_V2.md`'ye
   yaz. Simetri gruplamasından **sonraki** süre ölçülecek; gruplama öncesi
   rakamlar teşhis kaydı olarak kalsın, kabul ölçümü olarak değil. Blok kataloğu
   bu turda büyümediği için sürenin belirgin artmaması bekleniyor — arttıysa
   nedenini araştır.

6. **`EK_B_UC_NOKTALAR.md` yeniden üretilsin** (72 → 74) ve kalan işler
   commit'lensin.

## Bir not — S1'in ölçeği büyüdü

Sekiz saatlik blokta bir kişilik açık artık 1 yerine 8 birim ceza üretiyor. `w1`
değişmediği için S1'in diğer hedefler karşısındaki baskınlığı **arttı**. Bu şu an
sorun değil — baskınlık zaten istenen şey — ama Tur 8'in kalibrasyonunda dikkate
alınacak bir kayma. Bu turda ağırlıklara dokunma; `PROGRESS_V2.md`'ye bir satır
not düşmen yeterli.

## Turun bitiş kontrolü

- [ ] `pytest` tam takım geçiyor; `tsc -b` ve `oxlint` temiz
- [ ] Talep ekranı çalışıyor: aralık eklenip düzenlenebiliyor ve silinebiliyor
- [ ] Kabul ölçümü koşuldu, K1 süresi `PROGRESS_V2.md`'de
- [ ] `EK_B_UC_NOKTALAR.md` yeniden üretildi (74 uç nokta)
- [ ] `git status` temiz, sır yok
- [ ] `PROGRESS_V2.md` güncel; "DOKÜMAN BORCU" bölümü kapatılmış olarak işaretli
- [ ] Yeni doküman borcu varsa ayrı ve açık biçimde yazılı

## Değişmeyenler

- Kural kataloğuna dokunma (H5, H9, H10, S2, S3, S6 ve S1'in üst sınırı Tur 4).
- Blok kataloğunu büyütme — üç blok kalır.
- Ağırlıklara dokunma.
- Dört kanonik dokümana dokunma.
- Sunucuya dağıtım yok; üç göç bekliyor ve sonuncusu veri dönüştürüyor.
