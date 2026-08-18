# Claude Code — Sürüm 2, Tur 10: Analiz Ekranı, Kalibrasyon ve Kapanış Ölçümü

## Bağlam

Bu **kapanış turu**. Üç iş var ve sırası önemli: analiz ekranı yeniden yapılır,
ağırlıklar kalibre edilir, altı kabul kriteri referans donanımda ölçülür.

Sıra bilinçli: kalibrasyon ölçümden önce gelir, ölçüm de rapordan. Ters sırada
yapılırsa rapor kalibrasyondan önceki sayıları taşır.

### Doküman sürümleri — ilk işin bunları doğrulamak

| Doküman | Sürüm |
|---|---|
| `VARDIS_ProjectCharter.md` | **1.5** |
| `VARDIS_SRS.md` | 1.25 |
| `VARDIS_SDD.md` | **1.34** |
| `VARDIS_Backlog.md` | **1.24** |

Charter bu turda değişti — **K3'ün ölçüm ufku planlama dönemiyle sınırlandı.**
Ayrıntı aşağıda.

### Okunacaklar

- Charter **bölüm 5** (K3'ün yeni tanımı — bu turun kalibrasyon hedefini
  belirler)
- SDD **6.3.4** (analiz ekranı — bu turun tasarımı), **5.7** (analiz metrikleri),
  **5.9** (geçmiş sayaçlar)
- Backlog **T-07**, **T-08**, **B-25**

## Çalışma kuralları

- Dört kanonik dokümana **dokunmazsın**. Etki doğuran bir şey çıkarsa
  `PROGRESS_V2.md`'ye "DOKÜMAN BORCU" başlığı altında yaz.
- Tasarımdan sapma gerekiyorsa **önce nedenini söyle**, sonra uygula.
- Git: `add`, `commit`, `tag` senin; `push` ve `remote` **asla**.
- Başarısız bir test silinmez — `xfail` ile ve gerekçesiyle bırakılır.

---

## İş 1 — K3'ün ölçüm ufku değişti

**Dayanak:** Charter 1.5, bölüm 5.

Senin tespitin doğruydu: eşik ile ölçü aynı ufku kapsamıyordu ve 34 → 61,27
artışı gerileme değil, ufuk değişiminin aritmetik sonucuydu.

Karar: **K3 dönem içi dağılımı ölçer** — kişi başına gece yükünün, o döneme düşen
adil paydan sapması, en fazla sekiz gece saati.

Gerekçe: adalet hesapları doksan günlük ufku kapsar (SRS TD-6) fakat geçmiş,
sistemin o çalıştırmada değiştiremeyeceği bir girdidir. Önceki dönemlerde birikmiş
bir sapma tek dönemde kapatılamaz; kümülatif sapmanın büyüklüğünü kriter yapmak,
sistemi kendi denetimi dışındaki bir şeyden sorumlu tutmak olur.

- `kabul_olcumu.py`'nin K3 ölçümü dönem içi paya göre hesaplasın.
- Kümülatif sapma ayrıca raporlansın ama **kriter değil gösterge** olarak:
  kişi başına sapmanın önceki yayınlanmış döneme göre azalıp azalmadığı.

**Kabul:** K3 ölçümü dönem içi ufku kullanıyor ve iki ölçü raporda ayrı ayrı
görünüyor.

---

## İş 2 — B-25: kabul ölçümü otomatik koşuma girer

**Dayanak:** Backlog B-25.

`kabul_olcumu.py` iki tur boyunca sessizce kırık kaldı çünkü onu koşan hiçbir şey
yoktu. SDD 5.9 onu geçmiş sayaçların dört tüketicisinden biri sayıyor; denetleyen
bir şey olmadıkça "dört tüketici tek kaynaktan beslenir" sözleşmesi kâğıt üstünde
kalır.

En azından betiğin **çalıştığını** doğrulayan bir duman testi takıma alınsın —
küçük bir örnekle koşup çıktı üretmesi yeterli, altı kriterin geçmesi gerekmez.
Kriterlerin geçmesi ayrı bir ölçüm; buradaki amaç betiğin kırık olmadığını
sürekli bilmek.

Senin kendi dersin: *bir şeyin çalıştığını gösteren tek kanıt, onun düzenli olarak
koşuluyor olması.*

---

## İş 3 — Analiz ekranı yeniden yapılır

**Dayanak:** SDD 6.3.4 (yeniden yazıldı).

Ekran beş soruya yanıt verir ve sırası aciliyete göredir: bu çizelge kullanılabilir
mi, yük adil dağılmış mı, kimin kotası doluyor, sıkıntı nerede, önceki döneme göre
ne değişti.

- **Üst şerit:** kapsama oranı, karşılanmayan kişi-saat, toplam ceza. Karşılanmayan
  kişi-saat ile açık kayıt sayısı **ayrı ölçülerdir** ve ikisi de gösterilir —
  ardışık saatler tek kayıtta birleştiği için satır sayısı yükü anlatmaz. Bu
  karışıklık bir kez gerçekleşti ve dışa aktarma başlığında yanlış sayı çıktı.
- **Kapsama kartı:** açıklar gün / saat aralığı / nokta / eksik kişi; her satırda
  kişi-saat karşılığı ve toplam satırı.
- **Adalet kartı:** üç ölçü yan yana (gece, hafta sonu, toplam saat); kişi başına
  yük ve **kişiye düşen adil pay**; sapmaya göre sıralı, en uzaktakiler üstte.
  Havuz ortalaması gösterilmez.
- **Ufuk anahtarı:** ölçüler ya planlama dönemi ya da doksan günlük adalet ufku
  için. Hangi ufkun seçili olduğu her zaman görünür — iki ufkun sayıları
  farklıdır ve belirsiz kalırsa tablo yanlış okunur.
- **Kota kartı:** kişi başına yıllık fazla çalışma ve kalan kota; **sınıra
  dayananlar üstte**. Kartın amacı listeyi göstermek değil, riski göstermek.
- **Ceza dökümü:** üç ayrı sütun — ham değer, ağırlık, ağırlıklı ceza. Hedefler
  kimlikleriyle değil adlarıyla listelenir; "S4" tek başına kimseye bir şey
  söylemez.
- **Kümülatif değişim:** kişi başına sapmanın önceki yayınlanmış döneme göre
  azalıp azalmadığı. K3'ün gösterge kısmı burada görünür.

Ekrandaki bütün sayılar `AnalizServisi`'nden gelir; ekran kendi hesabını yapmaz.
Aynı kural dışa aktarma için de geçerli (SDD 5.8).

**Kabul:** Ekrandaki her sayı Excel çıktısındakiyle birebir aynı. Ufuk anahtarı
değiştiğinde adalet tablosu değişiyor ve hangi ufkun seçili olduğu görünüyor.

---

## İş 4 — Ağırlık kalibrasyonu

**Dayanak:** Backlog T-07, T-08. **İş 1 ve İş 3 bittikten sonra yapılır.**

İki bilinen kayma var:

- **T-07:** S2 ve S3'ün birimi vardiya sayısından saate döndü (yaklaşık sekiz kat)
  ve ağırlıkları değişmedi; iki hedef S4'ü fiilen eziyor. Gözlenen: dengeli
  gösterim döneminde on kişi toplam 32 saat fazla çalışma taşıyor, oysa o
  senaryonun hedefi eşiğin altında kalmaktı.
- **T-08:** K3'ün sapması çözücü süresine bağlıydı (60 sn'de 30, 900 sn'de 7).
  Ufuk kararından sonra bu sayı yeniden ölçülmeli — kalibrasyon hedefi artık
  dönem içi sapma.

Kalibrasyonda korunacak tek şey **S1'in baskınlığıdır**: kapsama her zaman diğer
hedeflerin toplamını bastırmalı. Bunu koruyan regresyon testi var, güncelle ve
koru.

Ağırlıkları değiştirdikçe ölç; hangi değerin hangi sonucu verdiğini
`PROGRESS_V2.md`'ye yaz. Kalibrasyon bir arama sürecidir ve ara adımlar bir
sonraki kalibrasyonun girdisidir.

**Kabul:** Dengeli senaryoda fazla çalışma sıfıra yakın; K3 dönem içi ölçümde
eşiği geçiyor; S1 baskınlığı korunuyor.

---

## İş 5 — Kapanış ölçümü ve performans notu

**En son yapılır.** Kalibrasyon bitmeden ölçüm alınırsa rapor eski sayıları
taşır.

- Altı kabul kriteri **referans donanımda** (gösterim sunucusu) ölçülür.
- `PERFORMANS_NOTU.md` **sürüm 3** olarak yazılır: ölçüm ortamı, referans örnek,
  altı kriterin sonucu, yeniden üretme adımları. Sayılar elle yazılmaz, ölçümün
  çıktısından alınır.
- Sürüm 2'den bu yana değişenler ayrıca özetlenir: model saatlik düzene geçti,
  Müracaat kaldırıldı, adalet kümülatif ufka taşındı, K3'ün ölçüm ufku
  sınırlandı.

**Kabul:** Altı kriter referans donanımda ölçülmüş ve sonucu notta yazılı.
Geçmeyen varsa hangi kriterin ne kadar açıkta olduğu net.

---

## Turun bitiş kontrolü

- [ ] `pytest` tam takım geçiyor — ters dosya sırasında da
- [ ] `ruff`, `tsc -b`, `oxlint` temiz; frontend testleri geçiyor
- [ ] Uyum testi 24/24
- [ ] Kabul ölçümü betiği takımda ve geçiyor (B-25)
- [ ] Ekran ile Excel çıktısının aynı sayıyı verdiğini gösteren test
- [ ] `PERFORMANS_NOTU.md` sürüm 3 yazılmış, sayılar ölçümden alınmış
- [ ] `EK_B_UC_NOKTALAR.md` yeniden üretildi
- [ ] `git status` temiz, sır yok, `PROGRESS_V2.md` güncel

## Kullanıcı bu ekranı gözle görecek

Analiz ekranı bu turun görünür çıktısı. Tarayıcıda göremiyorsan hangi davranışın
test edilmediğini açıkça yaz ve turun sonunda "şu ekranları kendi gözünle aç"
listesi bırak — özellikle ufuk anahtarının çalışması ve kota kartının
sıralaması.

## Bu turdan sonra kalanlar

Bunlar bu turda **yapılmaz**; kapanış sırası ayrıca konuşulacak:

- Özet ekranı (madde 12) — henüz tanımlı değil
- Müsaitlik kaydına belge (madde 7)
- Kullanıcı hesaplarının düzenlenmesi (madde 6)
- Sunucuya dağıtım, ekran görüntüleri, README
- `docs/turlar/` temizliği ve dokümanların İngilizceye çevrilmesi
