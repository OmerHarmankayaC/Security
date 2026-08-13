# Tur 5 — Devam Yönergesi

Durman doğruydu; kuralın amacı tam olarak buydu.

## Önce: prototip tasarımı benim hatamdı

"Sadece S1 ekle, bu bir performans sondajı" dedim. Sondajın ölçtüğü şey gerçek
riski temsil etmiyordu: üç kuralla 5 saniye, on dokuz kuralla 45,6 saniye.
Maliyetin kümülatif olduğunu ölçebilecek bir sondaj tasarlamalıydım — en azından
S2, S3 ve S4'ü de içine koymalıydım. Bunu not düşüyorum ki bir dahaki sondajda
tekrarlanmasın: bir sondaj, ölçmek istediği riskin taşıyıcılarını içermelidir.

Bulduğun iki hata bunu fazlasıyla telafi etti. Özellikle **ısıtma penceresinin
hiç sabitlenmemesi** ciddi: çözücünün geçmiş çalışma icat edip H2, H3 ve H4'ü
beslemesi, o kuralların dönem başında fiilen devre dışı kalması demekti. Belirti
sessizdi — model çözülüyor, çizelge üretiliyor, kurallar sağlanmış görünüyordu.
İkisi de SDD 1.28'e ders olarak yazıldı.

## Karar: 1 ve 2 evet, 3 hayır

**Seçenek 1 — taşma göstergelerini günlük tavanla sınırla: uygula.** Bu bir tanım
değişikliği değil, doğru bir gözlem: bir blok `azami_gunluk_saat`ten uzun
olamayacağı için taşması da o kadar olabilir. Model aynı çözüm kümesini üretir.
"Eksen H9'a bağlanır" bedeli gerçek bir maliyet değil — model zaten her çözümde
yeniden kuruluyor. SDD 5.3'e yazıldı.

**Seçenek 2 — S4'ü taban/tavan yöntemine çevir: uygula.** Bunu **tutarlılık
gerekçesiyle** onaylıyorum, performans gerekçesiyle değil. S2 ve S3 zaten bu
yöntemi kullanıyor; S4'ün kesirli payı doğrudan kısıtlaması bir tutarsızlıktı.
Üç adalet hedefinin aynı biçimde ölçülmesi, birinin ayrı davranmasından daha
savunulabilir. Kayıp bandın içindeki bir saatlik fark — saat biriminde küçük.
SRS 1.20'ye yazıldı.

**Seçenek 3 — nokta sürekliliği: dokunma.** Blok içinde nokta değiştirmenin sahada
karşılığı yok ve bu bir ürün kararı. Ürün kararını çözüm süresi için bozmak son
çare olmalı; henüz oraya gelmedik. Ayrıca bu kısıtın **gerçekten uygulandığını**
doğrula — değişken eleme onu bir kez sessizce iptal etmişti.

## Sonra ölç, karar o zaman

1 ve 2 uygulandıktan sonra üç ölçüm istiyorum:

| Ölçek | Neden |
|---|---|
| 30 × 7 | **Gerçek kullanım.** Dönem varsayılanı bir hafta (Charter 2.5) |
| 30 × 28 | Karşılaştırma noktası — bugün 45,6 sn |
| 40 × 28 | K1'in stres ölçeği |

40 × 28 hâlâ 60 saniyeyi aşıyorsa **dur ve bildir**; K1 kararını o sayıya bakarak
vereceğim. Gerçek kullanım ölçeğinin nerede durduğunu bilmek, kriteri
gevşetmekle formülasyonu daha fazla değiştirmek arasında seçim yaparken
belirleyici olacak.

`test_agirlik_kalibrasyonu`'nun bu nedenle düştüğünü doğru teşhis etmişsin —
ağırlık dengesi değil süre. Ölçümden sonra hâlâ düşüyorsa söyle, testin kendisini
gözden geçiririz.

## Doküman sürümleri

| Doküman | Sürüm |
|---|---|
| `VARDIS_SRS.md` | **1.20** |
| `VARDIS_SDD.md` | **1.28** |
| `VARDIS_Backlog.md` | **1.17** |
| `VARDIS_ProjectCharter.md` | 1.4 (değişmedi) |

**Dosya adları değişti.** Kurum adı public depoda görünmesin diye kanonik
dokümanlar `BOTAS_Vardiya_Cizelgeleme_*` → `VARDIS_*` oldu. Depodaki dosyaları
yeniden adlandır ve referansları güncelle; tur promptlarındaki geçişler
düzeltilmiş hâlde geliyor.

## Kalan işler

1. Seçenek 1 ve 2'nin uygulanması
2. Üç ölçek ölçümü ve karar noktası
3. **İş 7** — arayüzün minimal uyarlaması. Frontend şu an derlenmiyor; API
   sözleşmesi değişti. Vardiya Tipi sekmesi ve Sabit Vardiya alanı kalkar,
   çizelge veri kaynağı `baslangic_zamani`/`bitis_zamani`'na uyarlanır, tercih
   formu zaman aralığına geçer. Gün ızgarası ve hafta şeridi **Tur 6'nın işi**.
4. `kabul_olcumu.py`'nin saat modeline uyarlanması; K1, K3, K4 ölçümü
   (Charter 1.4'ün yeni tanımlarıyla)
5. `EK_B_UC_NOKTALAR.md` yeniden üretimi
6. Dalın `main`e alınması

## Değişmeyenler

- Ağırlıklara dokunma (Tur 9 kalibrasyonu). T-07'deki kayma biliniyor.
- `GecmisSayaclar` ve kümülatif adalet Tur 7.
- Kanonik dokümanlara dokunma; borç çıkarsa `PROGRESS_V2.md`'ye yaz.
- Sunucuya dağıtım yok.
