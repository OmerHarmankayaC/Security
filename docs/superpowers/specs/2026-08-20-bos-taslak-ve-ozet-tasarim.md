# Boş taslak çizelge ve Özet ekranının zenginleştirilmesi

**Tarih:** 2026-08-20 · **Durum:** onay bekliyor · **Kapsam:** tek tur, üç parça

Bu belge `docs/` altındaki dört kanonik dokümanın (Charter, SRS, SDD, Backlog)
yerine geçmez; onların gerektirdiği değişiklikler turun sonunda
`PROGRESS_V2.md`'ye **DOKÜMAN BORCU** olarak yazılır.

## Neden

İki ihtiyaç var.

**Elle çizim.** Çözücü olmadan da çizelge üretilebilmeli: kullanıcı boş bir
taslak açıp vardiyaları kendi koyabilmeli, isterse çizimin bir kısmını
kilitleyip gerisini çözücüye bırakabilmeli. Elle çizme makinesi bugün zaten
tam çalışıyor (hücre seç → saat/nokta gir → Uygula, oturum birikir, geri
al/yeniden uygula, Kaydet tek istek, sunucu kuralları doğrular). Tek tıkanma
şu: ızgaranın satırları **atamalardan** türetiliyor, dolayısıyla ataması
olmayan personelin satırı yok ve boş bir taslakta tıklanacak hiçbir hücre
kalmıyor.

**Özet'in dolması.** Ekran bugün beş küçük kart, kapsama açıkları listesi ve
"yaklaşan müsaitlik kayıtları"ndan ibaret; ölçülerin çoğu Analiz'de duruyor.
Ayrıca kartlar sayının hangi aralığa ait olduğunu yazmıyor.

## Kararlar

| Konu | Karar |
|---|---|
| Çözücünün rolü | Hem tamamen elle hem "elle başla, çözücüye devret" desteklenir (kilit mekanizması zaten var) |
| Boş satırlar | Yalnız düzenlenebilir sürümlerde (taslak, çözüldü); yayınlanmış/arşivde bugünkü davranış |
| Giriş noktası | Çizelge ekranı; hiç sürümü olmayan dönemde de açılabilir |
| Ceza dökümü | Çözücü koşmamış ya da atamalar sonradan değişmişse kural motorundan hesaplanır |
| Özet'in kapsamı | Dönem seçici YOK; bugünü içeren dönem, aralık her blokta yazılı |
| Tazeleme | Ekran açıldığında ve sekmeye dönüldüğünde |

Boş taslak **ayrı bir kip değil, normal bir sürümdür** (`durum=taslak`,
ataması sıfır). Kaydet, doğrula, kilitle, yayınla, karşılaştır, dışa aktar ve
yazdır böylece kendiliğinden çalışır. Komşusu zaten var: `/kopyala` kaynağın
çizelgesini kopyalayarak taslak açıyor; bu onun boş kardeşi.

---

## Parça 1 — Boş taslak ve ızgara satırları

### Arka uç

`POST /api/surum` iki alandan **tam olarak birini** kabul eder:

```
SurumTaslakTuretIstek:
  onceki_surum_id: int | None    # bugünkü davranış, aynen kalır
  donem_id:        int | None    # yeni
```

İkisi birden ya da hiçbiri verilirse 422 (Pydantic model doğrulayıcısı).

`donem_id` verildiğinde `CizelgeSurumuDeposu.taslak_ac(donem_id)` çağrılır:

- dönemde sürüm varsa yenisi **en sonuncuya bağlanır** (`onceki_surum_id` dolar),
- hiç sürüm yoksa bağsız açılır (`onceki_surum_id = None`),
- `surum_no` her iki yolda da `donem_icin_sonraki_surum_no` ile belirlenir.

Bağlama zorunlu: S8 ("önceki sürümden sapma") ve Sürümler ekranının
karşılaştırması sürüm zincirine dayanır; kullanıcı boş taslak açtı diye zincir
kopmamalı.

`taslak_turet` olduğu gibi kalır — mevcut çağıranı değişmez.

Yetki: uç noktanın bugünkü kapısı korunur.

### Ön yüz

Çizelge ekranında, sürüm seçicinin yanında **"Boş taslak aç"**. Dönemde zaten
sürüm varsa onay metni ne olacağını yazar ("Dönemde 3 sürüm var; 4. sürüm boş
bir taslak olarak açılacak"), çünkü düğme sessizce sürüm sayısını artırır.
Açılan taslak doğrudan seçilir.

Satırlar: `surumDuzenlenebilir` (taslak/çözüldü) ise ızgara satırları
atamalardan değil **personel listesinden** türetilir. Personel, dönemde aktif
olanlarla sınırlanır:

```
aktif_baslangic ≤ dönem_bitişi  ve  (aktif_bitis boş  veya  aktif_bitis ≥ dönem_başlangıcı)
```

Gerekçe H7: bağlam, aktiflik penceresi dışındaki güne atamayı zaten reddediyor
(`baglam.musait_mi`). Süzgeç olmasa kullanıcı asla atama yapamayacağı bir satıra
tıklayıp sunucudan hata alırdı.

Bu, aktiflik penceresinin **ikinci kez okunduğu yerdir**. Kural değil görünürlük
süzgecidir ve ayrışırsa sonucu zararsız: atanamayan bir satır görünür, sunucu
gerekçesiyle reddeder. Yine de testi yazılır.

Yayınlanmış/arşiv sürümde bugünkü davranış aynen kalır; "Bu sürümde henüz atama
yok" metni yalnız o sürümlerde görünür.

### Sınama

- `donem_id` ile sıfır sürümlü dönemde taslak açılır, `onceki_surum_id` boş kalır.
- Sürümü olan dönemde yeni taslak sonuncuya bağlanır.
- İki alan birden / hiçbiri → 422.
- Düzenlenebilir sürümde ataması olmayan personel satır olur; yayınlanmışta olmaz.
- Aktiflik penceresi dışındaki personel hiçbir sürümde satır olmaz.

---

## Parça 2 — Elle çizilen sürümün cezası

### Hesap

Yeni formül yazılmaz. Doğrulama servisi her esnek kural için
`kural.dogrula(atamalar, baglam)` çağırıp ihlallerin `ceza` alanlarını topluyor;
orada iki durumun **farkı** alınıyor, burada tek durumun **mutlak** değeri:

```
ceza_dokumu = { kural.kimlik: Σ(ihlal.ceza) for kural in esnek_kurallar }
```

Çözücünün dökümüyle bu hesabın aynı sayıyı vermesi projenin zaten güvence
altına aldığı bir değişmezdir (SDD 3.2.1, `test_cozucu_dogrulayici_uyumu`):
çözücünün geçerli saydığı bir çizelgede doğrulayıcının farklı bir şey görmesi
yazılım hatası sayılır. İkinci bir gerçeklik kurulmuyor, var olan ikinci
okuyucu kullanılıyor.

### Kaynak seçimi

`AnalizOku`'ya alan eklenir:

```
ceza_kaynagi: "cozucu" | "kurallardan" | "yok"
```

- Çözüm işi var **ve** atamalar o işten sonra değişmemişse → çözücünün dökümü.
- Aksi hâlde → kurallardan hesap.
- Kural katalogunda esnek kural yoksa → "yok".

Tazelik ölçüsü: `max(atama.guncelleme_zamani) > cozum_isi.bitis_zamani`.

Bu, bugünkü bir kusuru kapatır: çözülmüş bir sürüm elle düzenlenip
kaydedildiğinde Analiz **çözücünün eski dökümünü** göstermeye devam ediyor —
çizelge değişmiş, ceza değişmemiş görünüyor.

### S8

Hesaplanan dökümde **yer almaz**. "Önceki sürümden sapma" yalnız
`baglam.onceki_atamalar` doluyken tanımlı ve analiz bağlamı onu kurmuyor
(`baglam_olustur`un böyle bir parametresi yok). Sıfır yazmak "sapma yok" derdi;
doğrusu "bu ölçü burada tanımsız", o yüzden kalem hiç üretilmez.

### Ekranlar

- Analiz'in ceza dökümü kartına kaynağı söyleyen dipnot ("kural motorundan
  hesaplandı — bu sürümde çözücü çalışmadı" / "çözüm işinin dökümü").
- Özet'in toplam ceza kartına aynı bilgi kısa hâlde.

### Sınama

- Çözücüsüz elle kurulmuş sürümde döküm dolu gelir; `ham × ağırlık = ağırlıklı`.
- Çözülmüş sürümde çözücünün dökümü kullanılır, `ceza_kaynagi = "cozucu"`.
- Çözülmüş sürüm elle düzenlendikten sonra kaynak `"kurallardan"`a döner.
- S8 hesaplanan dökümde bulunmaz.

---

## Parça 3 — Özet ekranı

Ekranın sorusu **"şu an ne oluyor"**. Dönem seçici eklenmez; dönem
`donemSec()` ile bugünden türetilir ve bugün ilerledikçe kendiliğinden kayar.
Veri, ekran açıldığında ve tarayıcı sekmesine geri dönüldüğünde tazelenir.

### Aralık her blokta yazılı

Bugün kartlarda "kapsama %97" yazıyor ve neyin kapsaması olduğu yalnız kenar
çubuğundaki dönemden çıkarılabiliyor.

| Blok | Aralık etiketi |
|---|---|
| Ölçü kartları şeridi | "<dönem aralığı> dönemi için" (ör. 17 – 23 Ağu 2026) |
| Kapsama kartı + günlük şerit | aynı dönem, başlıkta |
| Kişi başına saat | "bu dönemde görevli saat · <dönem aralığı>" |
| Bu dönem müsait olmayanlar | dönemle kesişen kayıtlar |
| Yaklaşan müsaitlik kayıtları | **bugünden itibaren** |

Yaklaşan müsaitlik kartı kalır. Tek aralık dışı blok odur ve artık bunu kendisi
söyler; iki müsaitlik kartı ancak ikisi de neye baktığını yazdığında karışmaz.

### A. Günlük açık şeridi

Kapsama açıkları kartının **içine** girer: dönemin her günü için bir çubuk, o
günün eksik kişi-saati. Açık yoksa çubuk boş ve gün soluk. Bir güne tıklanınca
altındaki ayrıntı listesi o güne süzülür, tekrar tıklanınca süzgeç kalkar.

Sayı sunucudan gelir; `AnalizOku`'ya eklenir:

```
gunluk_kapsama: [{ tarih, acik_aralik_sayisi, karsilanmayan_kisi_saat }]
```

İstemcide toplamak cazip — veri zaten ekranda — ama kişi-saat formülü
(`eksik_sayi × blok süresi`) analiz servisinde duruyor ve bu iki ölçü bu projede
bir kez karıştırılıp dışa aktarmada yanlış sayı basılmıştı. Şeridin toplamı
`karsilanmayan_kisi_saat`'e eşittir ve bu bir testtir.

### B. Kişi başına saat — kısa hâl

`analiz.saat_dagilimi` zaten yanıtta. Özet'te adil paydan **en çok sapan altı
kişi** (ad · toplam saat · fark) ve "tümünü Analiz'de görüntüle" bağlantısı. Tam
dağılım grafiği Analiz'de kalır; iki ekran birbirinin ikizi olmaz.

### C. Bu dönem müsait olmayanlar

Dönemle kesişen müsaitlik kayıtları: kişi, günler, tip. Veri zaten çekiliyor,
değişen süzgeç.

### Yerleşim

Ölçü kartları → kapsama kartı (şerit + süzülebilir liste) → kişi başına saat →
bu dönem müsait olmayanlar → yaklaşan müsaitlik kayıtları.

### D. "Ölçülebilir sürüm" ölçütü değişir

Özet bugün ölçüleri **taslak olmayan** en yeni sürümden okuyor
(`lib/donemSecimi.ts` → `olculebilirSurum`). O ölçüt "çözülmemiş taslağın
ataması yoktur" varsayımına dayanıyordu ve boş taslak özelliği bu varsayımı
geçersiz kılıyor: elle çizilmiş bir taslağın ataması vardır ve ölçülebilir.

Ölçüt **"ataması var"** olur. Bunun için `SurumOzetiOku`'ya `atama_sayisi: int`
eklenir (depo sorgusunda tek COUNT); `olculebilirSurum` duruma değil bu alana
bakar. Alan olmadan istemcinin elinde ayırt edecek bir şey yok — sürüm listesi
atama sayısını taşımıyor.

### Boş taslakta

**Hiç atama yokken** bugünkü davranış korunur: ölçüler yerine "bu dönemin son
sürümü henüz çözülmemiş bir taslak" uyarısı. Metin güncellenir, çünkü artık tek
yol çözücü değil: "…Çizelge ekranından elle çizebilir ya da Çözüm ekranını
kullanabilirsin."

**İlk vardiya konduğu anda** sürüm ölçülebilir hâle gelir: kapsama düşük, şerit
dolu, saat listesi herkesi payının altında gösterir. Bu doğru davranış — elle
çizdikçe şerit sönmeli.

### Sınama

- Günlük şeridin toplamı `karsilanmayan_kisi_saat`'e eşittir.
- Güne tıklamak listeyi süzer; açığı olmayan gün vurgulanmaz.
- Saat listesi en çok sapanı üstte verir.
- Müsaitlik kartı dönemle kesişmeyen kaydı göstermez.
- Her aralık-bağlı blok aralığını metin olarak taşır.
- Ekran dönem seçici sunmaz.
- Ataması olan bir TASLAK ölçülebilir sayılır; atamasız taslakta ölçü yerine
  durum metni çıkar.

---

## Kapsam dışı

- İzin belgeleri (görüntüleme/yükleme) bu turda ele alınmaz.
- Çoklu dönem karşılaştırması / kümülatif adalet eğrisi.
- Çizelge ekranında sürükle-bırak ile blok çizme; giriş yolu bugünkü hücre
  formudur.
- Özet'in düzenli aralıkla yoklaması.

## Riskler

- **Aktiflik penceresinin ikinci okuyucusu** (parça 1). Zararsız ayrışma, testli.
- **Hesaplanan ceza ile çözücünün dökümünün ayrışması** (parça 2). Zaten
  güvence altındaki bir değişmez; ayrışırsa yazılım hatasıdır ve öyle ele alınır.
- **Özet ile Analiz'in içerik olarak yakınsaması** (parça 3). Kısa hâl ve
  "tümünü Analiz'de gör" bağlantısı bunun panzehiri.
