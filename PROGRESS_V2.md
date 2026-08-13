# İlerleme Günlüğü — Sürüm 2

Birinci aşamanın günlüğü [`PROGRESS.md`](PROGRESS.md) dosyasında kapandı ve
arşivdir; okunmaz. Sürüm 2'nin kaydı buradan başlar.

Her oturum sonunda buraya bir kayıt eklenir: tarih, tamamlanan,
kalan/ertelenen, sıradaki oturumun ilk işi. Yeni oturum bu dosyayı okuyarak
başlar.

---

## 2026-08-13 — Tur 5: Gerçek Saatlik Model — **SÜRÜYOR**

Kaynak: `docs/turlar/CLAUDE_CODE_PROMPTU_TUR5.md`. Yedi iş. Çalışma
`tur5-saatlik-model` dalında yürüyor.

Doküman sürümleri turun başında doğrulandı: Charter **1.4**, SRS **1.19**,
SDD **1.27**, Backlog **1.16** — dördü de taşıyor.

### İş 1 — prototip ölçümü: **karar kuralı geçildi, devam**

Karar kuralı: 40 × 28 ölçeğinde ilk uygun çözüme ulaşma süresi 30 saniyeyi
aşarsa dur. **Aşmadı — 5,0 saniye.** Tam uygulamaya geçiliyor.

Sondaj `backend/scripts/saatlik_prototip.py`. Modelde yalnızca mutlak saat
ekseni, `bas` göstergesi, günde tek başlangıç, asgari süre, nokta sabitliği,
günlük tavan ve S1 var; başka kural yok. Talep SRS 3.3.4'ün Müracaat'sız
tablosudur ve kadroya göre `P/40` ile ölçeklenir — aksi hâlde on kişilik bir
kadro kırk kişilik talebi karşılamaya çalışır ve ölçülen şey çözüm süresi
değil kapsama açığı olurdu. Şef havuzu `max(3, 7·P/40)`: kesintisiz
doldurulan bir nokta haftada 168 kişi-saat ister, günlük tavan on bir
saattir, dolayısıyla üç kişinin altındaki bir havuz noktayı hiçbir çizelgeyle
kapatamaz.

Arama işçisi SDD 3.4.3 referansına sabit (3), makine macOS arm64 / 10
çekirdek — `kabul_olcumu.py` ile aynı sözleşme.

| Ölçek | Değişken | Kurma | **İlk uygun** | Optimale | Sonuç |
|---|---|---|---|---|---|
| 10 × 7 | 7.224 | 0,10 sn | **0,25 sn** | 0,45 sn | optimal, ceza 0 |
| 20 × 14 | 28.224 | 0,38 sn | **1,12 sn** | 4,63 sn | optimal, ceza 0 |
| 30 × 28 | 84.000 | 1,15 sn | **3,71 sn** | 28,63 sn | optimal, ceza 0 |
| 40 × 28 | 112.224 | 1,69 sn | **5,02 sn** | 56,03 sn | optimal, ceza 0 |

40 × 28 iki kez daha koşuldu: ilk uygun 4,93 ve 5,08 sn; optimale 44,6 ve
45,2 sn. İlk uygun süre kararlı.

**Ölçüm boşuna hızlı olmasın diye çıkan çizelge denetlendi** (`--denetle`).
Sondaj hızlı çözüyorsa iki açıklama vardır — formülasyon ucuzdur ya da kısıt
yanlış yazıldığı için model gerçekte kolaydır — ve ikisini ayırmanın tek yolu
sonuca bakmaktır. Dört ölçekte de: asgari süreden kısa blok yok, günlük
tavanı aşan blok yok, gün içinde ikinci blok yok, blok içinde nokta değişimi
yok. 40 × 28'de **96 blok gece yarısını aşıyor** — mutlak eksenin var oluş
nedeni tam olarak bu.

### İki sapma — nedenleri önce

**1. Günlük saat, duvar saatine değil bloğun başladığı güne yazılıyor.**
SRS H1 ve H9 günlük toplamı `Σ_{s ∈ gün d} z[p,s]` diye yazar; H9'un metni
ise aynı paragrafta "gece yarısını aşan bloğun saatleri başladığı güne
sayılır (TD-1); ertesi günün tavanı bu saatlerle dolmaz" der. İkisi aynı şey
değildir ve formülün duvar saati okunması **iki kuralı da bozar**:

- **H9 blok uzunluğunu sınırlayamaz.** 20.00–08.00 bloğu duvar saatinde
  4 + 8 saattir; ikisi de on bir tavanın altında kalır ve on iki saatlik blok
  geçer.
- **H1'in asgari süresi akşam başlangıçlarını yasaklar.** 21.00'de başlayan
  bir blok o güne yalnızca üç saat bırakır ve `≥ 4 · bas` kısıtı düşer —
  oysa gece kapsamasının ihtiyaç duyduğu bloklar tam olarak bunlardır.

Metin normatiftir, gösterim kısaltmadır: "gün d" bloğun sayıldığı gündür.
Gün başına saat bu yüzden devralınan saatler çıkarılıp taşan saatler
eklenerek hesaplanıyor (`devir[p,s]` göstergesi: "bu saat çalışılıyor ve
önceki günde başlamış bir bloğa ait"). Maliyeti ölçüme dahil — tam uygulama
da aynı yapıyı taşıyacak. Bu, aşağıdaki doküman borcunun birinci maddesidir.

**2. H9 sondaja dahil edildi.** Prompt "diğer kuralları ekleme" diyor;
günlük tavan olmadan çözücü günde yirmi dört saat çalıştırabilir, kapsama
bedelsiz kapanır ve ölçülen süre gerçek modelin süresi olmaz. H9 ayrıca
SRS 3.3.1'de asgari blok süresiyle **aynı üç parametreli çerçeve** içinde
tanımlı: alt sınır ve üst sınır birlikte bloğun çerçevesini çizer.

### K1 için erken uyarı — optimale ulaşma 45–56 sn

Karar kuralı ilk uygun çözümü ölçer ve rahat geçiyor. Ama **optimale ulaşma
süresi 40 × 28'de 45–56 saniye** ve K1'in eşiği 60 saniye. Tur 4'te aynı
kriter 1,01 saniyeydi (blok kataloğuyla). Saat modeli optimallik kanıtında
yaklaşık **elli kat** pahalı ve tam modelde on beş kural daha eklenecek.

Bu bir durdurma nedeni değil — K1 pratikte zaman limitli bir aramanın
sonucunu ölçer ve ilk uygun çözüm beş saniyede geliyor — ama turun kabul
ölçümünde K1'in **ne ölçtüğüne** dikkat edilecek: "60 saniyede optimal" ile
"60 saniyede kabul edilebilir çözüm" aynı şey değil ve saat modelinde ikisi
ilk kez ayrışıyor.

### DOKÜMAN BORCU — bir yeni madde

1. **SRS H1 / H9 — `Σ_{s ∈ gün d} z[p,s]` gösterimi belirsiz.** Sembol duvar
   saatini mi bloğun sayıldığı günü mü gösterdiğini söylemiyor; H9'un metni
   ikincisini söylüyor, formül birincisi gibi okunuyor. Uygulama metne
   uyuyor. Gösterimin (SRS 4.1) "gün d" tanımını açıkça bloğun başlangıç
   gününe bağlaması gerekiyor.

---

## 2026-08-13 — Tur 4: Kural Kataloğu — **BİTTİ**

Kaynak: `docs/turlar/CLAUDE_CODE_PROMPTU_TUR4.md`, `TUR4_DEVAM.md` ve
`TUR4_K3_KARARI.md`. Sekiz iş; hepsi bitti. Çalışma `tur4-kural-katmani`
dalında yürüdü — turun ilk yarısında yarım kalan kural katmanı `main`e
bulaşmasın diye.

Doküman sürümleri turun üç noktasında doğrulandı: başta SRS 1.16 / SDD
1.26 / Backlog 1.12 / Charter 1.2; devam yönergesiyle Backlog **1.13**;
K3 kararıyla Charter **1.3** / SRS **1.17** / Backlog **1.14**.

### İş 1 — testler arası veri sızıntısı (B-22)

Her testten **önce** çalışan bir fikstür tanım/girdi/sonuç tablolarını
uygulamanın kendi silme yolundan boşaltıyor. Temizlik testten önce, sonra
değil: başarısız bir testin verisi incelenebilsin.

**Sızıntı önce ölçüldü.** `test_analiz_api` + `test_tanim_api` normal
sırada 30/30 geçiyor, ters sırada bir test düşüyordu. Fikstürden sonra iki
sıra da geçiyor; tam takım ters dosya sırasında da **327/327** verdi.

### İş 2 — blok görünümü türevi kaldırıldı

`blok_gorunumu_uret` ve `Baglam.talep` yok. S2, S3 ve S4 talebi doğrudan
saat ekseninden okuyor; türevin tüketicisi kalmadı. Yük göstergesi de
kişi-vardiya sayısını bıraktı (FR-1.9): karışık uzunluklu katalogda o sayı
kataloğun bileşimine bağlıdır, talep değişmese bile değişir.

### İş 3 — H5 yeniden, H9 ve H10

45 saat artık tavan değil **eşik** (H10'un parametresi); H5 mutlak tavanı
66'ya çıktı — günlük 11 saat × altı çalışma günü, H6 ve H9'un zaten ima
ettiği sınır. H9 günü sınırlıyor ve blok kataloğu kısıtı **aynı
parametreyi** okuyor, Tur 3'teki geçici sabit silindi.

H10 fazla çalışmayı **ayrık takvim haftalarında** topluyor; hafta kümeleri
kayan pencere yardımcısından ayrı bir fonksiyonda üretiliyor (TD-14).
Karışmanın sonucu sessizdir: kayan pencerede aynı saat yedi pencereye
girer ve toplam yedi katına çıkar.

**Kural zorunlu ama modeli çözülemez yapmıyor** ve bunu söyleyen bir test
var: kotası dolmuş personel eşiğe kadar çalışmaya devam ediyor.

### İş 4 — S1'in üst sınırı esnek

Karışık uzunluklu katalogda fazla kadro **yapısaldır** — on saatlik blokla
kapatılan sekiz saatlik talep iki saat fazla üretir — dolayısıyla zorunlu
üst sınır modeli çözülemez yapardı. `fazla` değişkenleri `eksik` ile aynı
saat gruplamasından geçiyor.

`w1f` **ayrı bir kural kaydı** (S1f): kural tablosu kural başına tek
ağırlık sütunu taşıyor ve S1'in formülasyonunda iki ağırlık var —
S6/S6b'deki aynı bölme. Karar Backlog 1.13'e işlendi; gerekçe ağırlığın
Kural ekranından ayarlanabilir olması (FR-1.11).

Manuel düzenlemede fazla kadro **ceza üretmemeye devam ediyor**; iki
tarafın farklı davranması bilinçli (SRS 4.3).

### İş 5 — S2/S3 saat birimine, S6 kaymaya

`gece_saat[b] = |b ∩ [20:00, 06:00]|` tek yerde. `gece_mi` bayrağı tanımlı
alan olarak kaldı — öneri kuralı yalnızca yeni blok oluştururken
ön-dolduruyor. S6 dairesel başlangıç saati kaymasına geçti: 08.00–16.00 ile
08.00–20.00 farklı bloklar ama aynı saatte başlıyorlar ve ergonomik bir
kayma üretmiyorlar.

### K3 KARARI — eşik değil, hedef yanlıştı

Ölçüm iki ayrı sorun gösterdi ve ikincisi ağırdı: yedi kişilik Müracaat
havuzunun erişebildiği gece talebi kişi başına en fazla **22,86 saat**,
hedef 40. O havuz hedefe **hiçbir çizelgeyle** ulaşamıyordu; hangi eşik
konursa konsun kalıcı olarak sapmalı görünürdü.

**Hedef kişiye özel adil paya döndü** (SRS 1.17): her talep birimi ona
erişebilenler arasında eşit bölünüyor, kişinin hedefi kendi paylarının
toplamı. K3'ün ölçümü **34 → 1,15**'e indi ve ulaşılabilirlik teşhisi
artık "her havuz hedefe erişebiliyor" diyor.

**Eşik katalogdan türetiliyor** (Charter 1.3): katalogdaki en uzun gece
bloğunun süresi. Sabit bir saat değeri katalog her değiştiğinde elle
yeniden ölçekleme isterdi; oran ise hedef büyüdükçe gevşer, küçüldükçe
imkânsızlaşır.

Bu, aynı kalıbın **ikinci** görülüşü: önce hiç gece alamayan personel
paydada sayılıyordu, sonra kısıtlı erişimi olan havuz tek ortalamaya
vuruluyordu. İkisinde de ölçü, hiçbir çizelgeyle kapatılamayan bir sapma
raporluyordu.

### Uyum testinin yakaladığı gerçek hata

S3'ün sapma değişkeninin üst sınırı bir kişinin **fiilen taşıyabileceği**
azami yüktü; adil pay ise kadro yetersizken bunu aşabiliyor. O durumda
kısıt sınırı aşıyor ve model **çözülemez** dönüyordu — oysa kadro
yetersizliğinin doğru cevabı çizelgeyi üretip açığı göstermektir (FR-5.2).
24 rastgele örnekten biri buna denk geldi. Üst sınır artık payı da
kapsıyor; uyum testi **24/24** temiz.

### İş 6 — katalog yedi bloğa, gösterim verisi dört senaryoya

Katalog SRS 3.3.1'deki yedi blok. On iki saatlik bloklar haftalık eşiği
gerçekten aşabildiği için H10'un işlediğini gösterebilen tek yapı.

**Kadro 44'ten 30'a indi.** 44 kişide kişi başına haftalık yük 26 saatti;
kimse eşiğe yaklaşmıyor, H10 hiçbir zaman tetiklenmiyordu. 30 kişide yük
**38,4 saat** — eşiğe yakın ama altında.

| Senaryo | Açık | En yüksek hafta | Fazla çalışma | Uzun blok |
|---|---|---|---|---|
| Dengeli (Bu Hafta) | 0 | 50 sa | 32 sa (10 kişi) | 9 |
| Sıkışık | 56 | 54 sa | 149 sa (21 kişi) | 63 |
| Fazla çalışma | 17 | 54 sa | 79 sa (17 kişi) | 19 |
| Kota sınırı | 0 | 48 sa | 30 sa (10 kişi) | 9 |

Kota senaryosunda Ahmet Yılmaz'ın (devir 265, kalan 5) haftalık yükü **40
saat**: çalışmaya devam ediyor, eşiği aşamıyor. Ön kontrol bunu adıyla
bildiriyor.

**Sıkışık senaryonun çelişkisi erişilebilirliğe taşındı.** On iki saatlik
bloklar girince "kadroyu küçült" mekanizması çalışmaz oldu — kabul ölçümü
bunu sıfır açıkla yakaladı. Vardiya şefliği havuzunun beşini izne çıkarmak
blok uzunluğundan bağımsız çalışıyor: eksik olan saat değil, o noktadan
geçebilen **kişi** (H8).

Personel gerçekçi adlar taşıyor.

### İş 7 — çizelge hücresinde saat aralığı

Hücre `08–16 · GÜV` gösteriyor, renk **başlangıç saati bandından**
geliyor. Yedi bloklu katalogda "Gündüz" adını taşıyan iki blok aynı
kısaltmaya sıkışıyor ve ızgara iki farklı çizelgeyi aynı gösteriyordu.
06.00'da başlayan uzun blok gündüzden ayrı bir bantta — aynı renk olsalardı
06–16 ile 08–16 ayırt edilemezdi.

### İş 8 — ön kontrole kota bulguları

Devir kotayı aşmışsa **kesin bulgu** (H10 tek başına sağlanamaz; veri
hatası, kişinin adıyla), kalan kotası bir haftalık fazla çalışmaya
yetmiyorsa **uyarı**. İkisi de çözümü engellemiyor (K18).

### Kabul ölçümü — 5/5

| Kriter | Eşik | Tur 3 | **Tur 4** |
|---|---|---|---|
| K1 40×28 | < 60 sn | 1,01 sn | **3,36 sn** |
| K2 zorunlu ihlal | 0 | 0 | **0** |
| K3 gece adaleti | ≤ 1 gece bloğu (10 sa) | 0,61¹ | **2,85** |
| K4 eksik gösterimi | ≥1 açık | 13 aralık | **12 aralık (76 sa)** |
| K5 manuel düzenleme | < 1 sn | 0,035 sn | **0,051 sn** |

¹ Tur 3'te birim vardiya sayısıydı; sayılar doğrudan karşılaştırılamaz.

K1 üç katına çıktı (katalog ikiye katlandı) ama eşiğin yarısı olan 30
saniyenin çok altında — K17'nin "dur" koşulu oluşmadı.

### Bilinen sapma — dengeli dönemde bir miktar fazla çalışma

Dengeli dönemde on kişi toplam 32 saat fazla çalışma taşıyor; hedef "eşiğe
yakın ama altında"ydı. Ortalama 38,4 saat, en yüksek hafta 50. Sebep
**ağırlık ölçeği**: S2/S3'ün birimi saate döndüğü hâlde ağırlıkları
değişmedi, dolayısıyla S4'ün dengeleme baskısı görece zayıf. Bu
**beklenen** bir durum ve düzeltmesi Tur 8'in kalibrasyonu; bu turda
ağırlıklara dokunulmadı.

### DOKÜMAN BORCU — yok

Bu turda dört kanonik dokümana dokunulmadı; K3 kararının gerektirdiği
Charter 1.3, SRS 1.17 ve Backlog 1.13/1.14 güncellemeleri proje
yürütücüsü tarafından yapıldı ve dala alındı.

### Bekleyen göçler — dağıtım yapılmadı

Sunucu **`d1f83a6c40b2`** noktasında (Tur 3, 12.08.2026'da çıktı; Tur 2'nin
iki göçü ondan önce uygulanmıştı). Bekleyen tek göç bu turunki:
**`e7b2c4915d80`** — şemayı değiştirmez, yalnızca `kural` tablosunu
günceller: H5'in parametresini `azami_haftalik_saat` → `haftalik_mutlak_tavan`
olarak taşır ve değerini 66 yapar, H9/H10/S1f kayıtlarını ekler. Var olan
kayda dokunmaz (kullanıcının değiştirdiği bir ağırlığı geri almaz) ve iki
kez koşulabilir.

**Dağıtımda dikkat:** göç kural kayıtlarını değiştiriyor, kod ise yeni
parametre adını okuyor — ikisi birlikte gitmeli. Eski kod yeni parametreyle
`KeyError` verir, yeni kod eski parametreyle de. Dağıtım kararı proje
yürütücüsünde.


---

## 2026-08-12 — Tur 3: Saatlik Düzenin Veri Temeli — **BİTTİ**

Kaynak: `docs/turlar/CLAUDE_CODE_PROMPTU_TUR3.md`, `TUR3_DEVAM.md` ve
`TUR3_DEVAM_2.md`. On işlik bir tur; **onu da bitti.** İlk sekiz `374caa3`
ile, kalanlar turun sonunda commit'lendi.

Doküman sürümleri iki kez doğrulandı: turun başında SRS 1.15 / SDD 1.23 /
Backlog 1.9, devam yönergesinden sonra SRS **1.15** / SDD **1.24** /
Backlog **1.10** / Proje Tanım Dokümanı 1.2. Bildirilen dört doküman
borcunun tamamı kapatılmış olarak geldi.

### Uygulama planı

[`docs/turlar/UYGULAMA_PLANI_V2.md`](docs/turlar/UYGULAMA_PLANI_V2.md).
Bir süre `docs/` altında arayıp "eksik" diye kaydetmiştim; dosya o sırada
depo kökündeydi. Yerleşim kuralı artık planın kendisinde yazılı ve tek:
**kanonik dört doküman `docs/` altında, plan/prompt/yönerge dosyalarının
tamamı `docs/turlar/` altında**, depo kökünde plan veya prompt bulunmaz.

Plan Tur 3 için bu turda yapılanları birebir doğruluyor ve iki kural
ekliyor: **her turda kabul ölçümü koşulur** (K17 — blok kataloğu
büyüdükçe K1 riski artıyor, ölçüm sona bırakılmaz) ve **yeniden tanımlanan
bir kuralın eski testi silinmez, güncellenir** (davranışın bilinçli mi
kazayla mı değiştiği bilgisi kaybolmasın). İkincisi bu turda uygulandı:
S1'in birim değişikliğinde testler silinmedi, beklenen değerler
gerekçesiyle birlikte güncellendi.

### Biten ve ölçülen işler

#### İş 1 — Talep tablosu zaman aralığına (göç `d1f83a6c40b2`)

`talep.vardiya_tipi_id` yerine `baslangic` ve `bitis` (TIME). Dönüşüm göç
içinde yapılıyor ve **sayılarak** doğrulanıyor: satır sayısı ile toplam
kişi-saat yükü eşit değilse göç hata verip duruyor. Sessizce devam etmesi
hâlinde kaybolan bir talep satırı hiçbir yerde görünmezdi — talep düştüğü
için kapsama açığı da doğmaz.

**Ölçüldü (geliştirme veritabanı):** 27 satır → 27 satır, **384 kişi-saat →
384 kişi-saat.** Geri alma yazıldı; test veritabanında ileri → geri → ileri
denendi.

Aynı göç `kapsama_acigi` ve `fazla_kadro` tablolarını da aralığa çeviriyor,
`personel`e devir bakiyesi alanlarını (`devir_fazla_calisma_saat`,
`kota_yili`) ve `cozum_isi`ne `on_kontrol_bulgulari` alanını ekliyor.

**Açık/fazla kadro satırları dönüştürülmüyor, siliniyor.** Bu iki tablo bir
çözümün çıktısıdır, kullanıcının girdiği veri değil; blok eksenli bir açık
kaydını aralığa çevirmek o kaydın üretildiği andaki talebi yeniden kurmayı
gerektirir ve talep aynı göçte değişiyor. Satırlar sürüm yeniden
çözüldüğünde ya da elle düzenlendiğinde doğru biçimde yeniden yazılıyor.
Yanlış dönüşmüş bir açık kaydı, hiç olmamasından kötüdür: rapora doğru gibi
girer.

#### İş 2 — Talebin saate açılımı, tek yerde

`app/services/talep_cozucu.py` → `talebi_saate_ac`; aralık aritmetiğinin
kendisi `app/kurallar/zaman_araligi.py`de (ORM'den bağımsız, kural katmanı
da kullanabiliyor). Sınırlar başlangıçta kapalı, bitişte açık: `08.00–16.00`
→ 08…15, 16 dışarıda. Isıtma penceresi dahil (TD-5). Gece yarısını aşan
aralık ertesi günün duvar saatlerine taşıyor.

#### İş 3 — S1 saat ekseninde; **turun asıl kabulü geçti**

Göç öncesi taban (7 günlük dönem, tek arama işçisi, 120 s):
toplam **1096**, S1 0, S2 40, S3 40, S4 202, S6 18, S7 17, **144 atama, 0
açık**.

Göç sonrası aynı dönem: **S1 0, 144 atama, 0 açık**, toplam 1055. Kapsama
birebir aynı; toplam daha düşük çünkü çözücü daha iyi bir çözüm buldu (iki
koşum da optimalliği kanıtlamıyor, "uygun" durumunda bitiyor).

**Yolda bir tuzak çıktı — kaydı burada duruyor.** İlk uygulamada aynı dönem
120 saniyede **704 kişi-saat** açıkla çıkıyordu; 420 saniyede bile 536'ya
inebildi. Sebep yapıda değildi: hizalı katalogda bir bloğun sekiz saati
**aynı kısıtı** üretiyor ve sekiz **birbirinin yerine geçebilen** `eksik`
değişkeni doğuruyordu; çözücü zamanının çoğunu bu simetriyi kırmakla
harcıyordu. Aynı kısıtı üreten saatler tek değişkende toplandı ve amaç
fonksiyonundaki katsayı grubun saat sayısı yapıldı. **Anlam değişmedi** —
ceza saat başına birikmeye devam ediyor — ama arama eski hâline döndü.

#### İş 4 — Açık ve fazla kadro aralık olarak (kısmen)

Birleştirme `saatleri_araliklara_birlestir` ile **tek yerde**: ardışık ve
sayısı eşit saatler tek satıra iniyor (00…07'de 1 kişi eksik → tek
`00.00–08.00 / 1` kaydı). Hem çözücü yolu hem elle düzenleme yolu
(`sapmalari_yenile`) aynı yardımcıyı kullanıyor. Talep ile atamanın saat
bazında farkı `Baglam.sapma_saatleri`nde tek tanım; doğrulayıcının S1
bulguları da kalıcı sapma tabloları da oradan çıkıyor.

#### İş 8 ve İş 10 — servis tarafı

Ön kontrol bulguları artık **işi düşürmüyor**: `Bulgu.engel_mi` →
`kesin_mi` (anlamı "kesin bulgu mu, uyarı mı"), `engelleyenler` →
`kesin_bulgular`, ve çözüm işçisi bulguları `cozum_isi.on_kontrol_bulgulari`
alanına yazıp çözüme devam ediyor. Bulgu metinleri kimlik yerine ad
taşıyor (`Baglam.yetkinlik_adi/nokta_adi/vardiya_adi`).

### Tasarımdan sapmalar — ikisi de zorunluydu

1. **Gün sonu `24.00` yerine `00.00` ile yazılıyor.** SDD 4.2.2 `24.00`
   diyor. PostgreSQL bu değeri saklıyor fakat sürücü (psycopg) geri
   okuyamıyor — denendi: `DataError: can't parse time '24:00:00': hour must
   be in 0..23`. Python'un `time` tipi 24:00'ı taşımıyor. Bunun yerine
   `vardiya_tipi` tablosunun **zaten kullandığı** sözleşme uygulandı:
   `bitis <= baslangic` ise aralık gün sonuna kadar sürer, gece yarısını
   aşıyorsa ertesi güne taşar. Sütun tipi SDD'deki gibi TIME kaldı; değişen
   yalnızca 24.00'ın kodlanışı ve bu kural tek yerde (`zaman_araligi.py`)
   uygulanıyor.

2. **Blok eksenli talep görünümü korundu** — saat ekseninden türetilerek.
   S2, S3 ve S4 talebi hâlâ **vardiya biriminde** okuyor
   (`hedef_gece = Σ talep / |havuz|`, `Σ sure_saat × gereken`) ve bu turda
   kural kataloğuna dokunmak yasak. Talep doğrudan saate çevrilseydi
   S2/S3'ün hedefi sekiz katına çıkar ve "aynı toplam ceza" kabulü
   kırılırdı. İkinci bir **tanım** yazılmadı: tek kaynak `talep_saat`,
   `blok_gorunumu_uret` ondan tek yerde türetilen bir **türev** (bir bloğun
   gereken sayısı, kapsadığı saatlerdeki en büyük gereken). Hizalı
   katalogda eski tablonun birebir aynısını veriyor. Tur 4'te S2/S3 saate
   geçince türev kalkar.

### DOKÜMAN BORCU — **dördü de kapatıldı**

Aşağıdaki dört madde bildirildikleri hâlleriyle duruyor; **hepsi SDD 1.24
ve Backlog 1.10 ile karşılandı** (gün sonunun kodlanışı SDD 4.2.2'ye,
`on_kontrol_bulgulari` 4.2.4'e, talep uç noktaları Ek B'ye yazıldı;
FR-1.9'un kişi-vardiya türevi Backlog **B-21** olarak kaydedildi ve Tur
4'te saat tabanına taşınacak). Açık borç DEĞİLDİR; kayıt olarak duruyor.

1. **SDD 4.2.2 / 4.2.4 — gün sonunun kodlanışı.** "24.00 gün sonunu
   gösterir" ifadesi uygulanabilir değil (yukarıdaki 1. sapma).
   Dokümanda `bitis <= baslangic` sözleşmesinin yazılması gerekiyor.
2. **SDD 4.2.4 — `cozum_isi.on_kontrol_bulgulari`.** İş 8 bulguların
   "sürüm kaydında kalıcı" olmasını istiyor; SDD'de böyle bir alan tanımlı
   değil. Alan eklendi, dokümana işlenmeli.
3. **SDD Ek B — talep uç noktaları.** Talep artık hücre değil kayıt
   olduğundan `PUT /api/talep` yerine `POST /api/talep`,
   `PUT /api/talep/{id}` ve `DELETE /api/talep/{id}` var. Ek B yalnızca
   `GET, PUT` listeliyor; uç nokta sayısı 72 → 74.
4. **FR-1.9 — kişi-vardiya artık türev.** Talep blok taşımadığı için
   haftalık kişi-vardiya, kişi-saatin katalogdaki ortalama blok uzunluğuna
   bölünmesiyle bulunuyor (tek uzunluklu katalogda SRS 3.3.6'daki referans
   örneği birebir veriyor: 1.152 saat / 8 = 144, asgari kadro 29).
   Karışık uzunluklu katalogda bu bir yaklaşıktır; asgari kadro hesabının
   saat tabanına taşınması Tur 4'ün konusu olabilir.

### Test fikstürleri aralık şekline geçirildi — takım 320/322

Ondan fazla test dosyası ve iki betik (`demo_veri_uret.py`,
`kabul_olcumu.py`) eski `Talep(vardiya_tipi_id=…)` şeklini kuruyordu.
Ortak kaynak `ornek_senaryo.py` de SRS 3.3.4'ün yeni aralık tablosuna
geçirildi ve referans yükü koruyor: **haftalık 1.152 kişi-saat**, sekiz
saatlik katalogda 144 kişi-vardiya ve 29 kişilik asgari kadro (FR-1.9
testi birebir geçiyor).

Yol boyunca üç şey ortaya çıktı ve düzeltildi:

- **Göç dosyasını koştuktan sonra değiştirmiştim** (`on_kontrol_bulgulari`
  sonradan eklendi), bu yüzden iki veritabanı da göçün eski hâlindeydi ve
  geri alma da tutmuyordu. Göç yayınlanmadığı için ikisi de göç
  zincirinden sıfırdan kuruldu — elle `ALTER TABLE` yok.
- **`test_cizelge_api` sıra bağımlıydı:** ön kontrol bütün tanım verisine
  baktığı için başka bir testin bıraktığı nokta/talep bulgu üretiyordu.
  Fikstür artık senaryo verisini temizliyor.
- **`Bulgu.engel_mi` yalnızca serviste yeniden adlandırılmıştı**; API
  şeması ve arayüz hâlâ eski adı taşıyordu. Üçü de `kesin_mi` oldu.

S1'in birimi değiştiği için beklenen test güncellemeleri yapıldı: sekiz
saatlik blokta bir kişilik açık artık **8 kişi-saat** ceza üretiyor (eski
ölçüde 1 idi) ve bulgu metni blok adı yerine **aralık** taşıyor
(`2026-02-02 · 16.00–24.00 · Güvenlik`).

`test_cozum_on_kontrolde_yapisal_engel_varsa_cozmeden_basarisiz_doner`
adıyla birlikte tersine çevrildi: artık
`test_on_kontrol_bulgusu_cozumu_dusurmez_cizelge_yine_uretilir` ve
çizelgenin **üretildiğini**, bulgunun iş kaydında kaldığını, açığın
kapsama açığı olarak raporlandığını ölçüyor.

### İş 9 — kapsama oranı atamalardan (SDD 5.7, K19)

Oran artık `Σ min(atanan, talep) / Σ talep` ile **atama kayıtlarından**
hesaplanıyor; kapsama açığı tablosu bir raporlama detayı. `min(...)` şart:
bir saatteki fazla kadro başka bir saatteki açığı kapatmaz. Talep yoksa
oran **tanımsız** (`None`) — sıfır bölme yerine yüzde yüz varsaymak, boş
bir dönemi kusursuz bir çizelge gibi gösterirdi.

### Takım yeşil — ara commit atıldı

**322/322 geçiyor**, `ruff check` ve `ruff format --check` temiz. Buraya
kadarki iş `374caa3` ile commit'lendi (TUR3_DEVAM'ın istediği ara commit).

---

## Turun ikinci yarısı — kalan altı iş bitti

Kaynak: `docs/turlar/TUR3_DEVAM_2.md`. Tur **kapandı**.

### İş 7 — Talep ekranı aralık girişine

Ekran eski matrisi çiziyor ve kırıktı: hücrelere yazılan hiçbir sayı
kaydedilemiyordu, çünkü beslendiği `PUT /api/talep` ucu artık yok. Yerine
her satırı bir aralık olan liste geldi — nokta, gün tipi, tarih, aralık,
süre, gereken — ve Ekle/Değiştir/Sil üçlüsü diğer sekmelerle **aynı
konumda, aynı sırada** (SDD 6.3.1). Görsel geliştirme Tur 6'nın işi;
buradaki hedef işlevsellikti.

Üç karar kayda değer:

1. **Saatler açılır liste, serbest metin değil.** Aralıklar saat başında
   başlamak zorunda (kapsama kısıtı saat ekseninde yazılır); serbest bir
   alan 08.30 yazdırıp sunucudan hata almayı mümkün kılardı. Bitiş
   listesinde 00.00 **yoktur** — gün sonu 24.00'tır ve ikisi aynı değeri
   kodlar; iki ayrı seçenek görünmesi kullanıcıyı yanıltırdı.
2. **Tarih alanı forma girdi.** İş tanımı beş alan sayıyordu ama talep
   kayıtlarının tarihe özgü istisnaları var ve listede zaten görünüyorlar.
   Alan olmasaydı, istisna satırı genel satırın kopyası gibi durur ve
   kullanıcı farkı hiçbir yerden okuyamazdı.
3. **Yanıt alanı `hucreler` → `araliklar`.** Eski ad ekranın da matris
   çizmesine yol açmıştı; sözleşme değişirken adın kalması, sonraki
   okuyucuyu aynı yanlışa davet ederdi.

Ekranın sözleşmesi `TanimlarEkrani.test.tsx`te kilitli: 24.00 gösterimi,
POST/PUT/DELETE yolları ve 409'un anlaşılır hâle gelmesi.

### İş 6 — blok kataloğu kısıtları

İkisi de **girişte** reddediliyor: aynı `(baslangic_saati, sure_saat)`
ikinci kez tanımlanamaz (**409** — istek geçerli, mevcut veriyle çakışıyor)
ve süre günlük azami çalışmayı aşamaz (**400** — değerin kendisi geçersiz).
Ayrım korunuyor çünkü kullanıcının yapacağı şey farklı: biri başka bir saat
seçer, öbürü süreyi kısaltır.

**Pasif bloklar benzersizlik sayımında yok.** Sayılsalardı, kullanımda
olduğu için silinemeyip pasifleştirilmiş bir blok o saatlerde yeni blok
tanımlamayı **kalıcı olarak** imkânsız kılardı ve kullanıcının
düzeltebileceği bir yol kalmazdı.

**GEÇİCİ YAPILANDIRMA DEĞERİ — Tur 4'te silinmeli.** Azami süre
`kural.parametre_getir("H9", "azami_gunluk_calisma_saati", …)` ile **kural
kataloğundan** okunuyor; H9 henüz yok, o yüzden çağrı
`_GECICI_AZAMI_GUNLUK_CALISMA_SAATI = 11` varsayılanına düşüyor
(`app/services/tanim_servisi.py`). H9 yazıldığında kısıt kendiliğinden
onun değerini kullanmaya başlar ve **sabit silinmelidir** — iki yerde duran
bir sayı sessizce birbirinden ayrılır. Kısıt ile kuralın ayrı sayılar
taşıması, girişi geçen bir bloğun çözümde her gün ihlal üretmesi demekti.

**Test takımı bu kısıtla çelişiyordu ve bu bir bulgu.** Test veritabanı
koşumlar arasında sıfırlanmıyor; blok yaratan testler kayıtlarını
bırakıyordu, dolayısıyla katalogda üç tane 08.00/8sa blok birikmişti.
Kısıt gelince üç test kırıldı — kısıt yanlış olduğu için değil, testler
katalogda çöp biriktirdiği için. İki yardımcı eklendi
(`gecici_vardiya_tipi` blok açıp test bitince düşürür, `bos_vardiya_blogu`
saatleri testin konusu olmayan yerlere boş bir saat verir) ve birikmiş
kayıtlar uygulamanın kendi silme yolundan temizlendi — elle SQL yok.

### İş 5'in form tarafı — devir bakiyesi

`devir_fazla_calisma_saat` ve `kota_yili` şemalara, API'ye ve personel
formuna girdi. **Bu turda hiçbir kural bu alanları okumuyor**; toplanmalarının
nedeni Tur 4'ün kota hesabına hazır olmaları. Boş bırakılan devir **sıfır**
(sütun NOT NULL, "bilinmiyor" hâli tanımlı değil), kota yılı boş kalabilir.
Servis açıkça `null` gönderen bir istemciye karşı da korumalı.

### Blok görünümü türevine varsayım yorumu

`blok_gorunumu_uret`, kullanıcısı (`baglam_kurucu`) ve taşıyıcı alan
(`Baglam.talep`) — üçüne de aynı uyarı yazıldı: türev **tek uzunluklu ve
hizalı** bir katalog varsayar. Tur 4'te 10 ve 12 saatlik bloklar girdiğinde
"en büyük gereken" kuralı yanlışlaşır (06.00–18.00 bloğu gece 3 ve gündüz 7
kişilik talebi birlikte örter, türev 7 sayar) ve **hata vermez**. Yorum
düzeltmeyi değil **kaldırmayı** işaret ediyor: doğru çözüm S2/S3'ü saat
eksenine taşımaktır.

### Kabul ölçümü — K1 **1,01 sn** (eşik 60 sn)

Simetri gruplamasından **sonra**, bu makinede (macOS arm64, 10 çekirdek;
arama işçisi SDD 3.4.3 referansına sabit: 3):

| Kriter | Eşik | Tur öncesi | **Şimdi** |
|---|---|---|---|
| K1 40×28 | < 60 sn | 1,12 sn | **1,01 sn** |
| K2 zorunlu ihlal | 0 | 0 | **0** |
| K3 gece sapması | ≤ 1,0 | 0,61 | **0,61** |
| K4 eksik gösterimi | ≥1 açık | 21 hücre | **13 aralık (112 saat)** |
| K5 manuel düzenleme | < 1 sn | 0,038 sn | **0,035 sn** |

**5/5 geçti.** K1 artmadı — blok kataloğu bu turda büyümedi ve simetri
gruplaması aramayı göç öncesi hâline döndürdü.

**K4 ölçümün kendisi eskimişti ve önce kaldı.** Betik açık kayıtlarının
orta anahtarını hâlâ vardiya tipi kimliği sanıyor, saat numarasını
yazdırıyordu ("2026-06-06 / 0 / Vardiya Şefliği") ve "üç bilgi de dolu"
denetimi bu yüzden düşüyordu. Ölçülen şey bozulmamıştı; ölçü İş 4'ün
ardından güncellenmemişti. Betik saat eksenli eksikleri nokta içinde
aralığa birleştirip kullanıcıya gösterilen biçimi ölçüyor artık.

**Yol üstünde bir hata daha çıktı:** saat metnini yazan yardımcı **üç ayrı
modülde** kopyalanmıştı (`esnek.py`, `tanim_servisi.py`, `kabul_olcumu.py`)
ve üçü de aynı yanlışı yapıyordu — gün başında başlayan bir aralığı
"24.00–08.00" diye yazıyorlardı, çünkü 00.00'ı başlangıç mı bitiş mi
olduğuna bakmadan 24.00'a çeviriyorlardı. Okuyan kişi bunu gece yarısını
aşan bir aralık sanardı. Tanım `zaman_araligi.py`ye taşındı
(`saat_metni`/`aralik_metni`), üç kopya kaldırıldı.

### Ek B yeniden üretildi — 72 → 74

`PUT /api/talep` kalktı; `POST /api/talep`, `PUT /api/talep/{id}` ve
`DELETE /api/talep/{id}` geldi. Dosya "üretilmiştir" diyordu ama üreteci
yoktu; `backend/scripts/uc_noktalari_listele.py` eklendi. `--denetle`
uygulamanın yönlendirme tablosunu Ek B ile karşılaştırır ve fark varsa
sıfırdan farklı kodla çıkar — sayı artık elle sayılmıyor.

### S1'in ölçeği büyüdü — Tur 8'in kalibrasyonuna not

Sekiz saatlik blokta bir kişilik açık artık **1 yerine 8 birim** ceza
üretiyor (ceza saat başına birikiyor). `w1` değişmediği için S1'in diğer
hedefler karşısındaki **baskınlığı arttı**. Şu an sorun değil — baskınlık
zaten istenen şey — ama Tur 8'in ağırlık kalibrasyonunda hesaba katılacak
bir kayma. Bu turda ağırlıklara dokunulmadı.

### Yeni doküman borcu — üç madde

Öncekiler kapandı (yukarıdaki DOKÜMAN BORCU bölümü); bunlar **yeni** ve
**açık**:

1. **SRS FR-1.3 — blok kataloğu kısıtları.** Aynı `(baslangic_saati,
   sure_saat)` ikilisinin benzersizliği ve sürenin günlük azamiyi
   aşamayacağı SRS'te yazılı değil; kısıt kodda var.
2. **SDD 4.2.1 — `personel.devir_fazla_calisma_saat` / `kota_yili`.**
   Göçle geldiler (`d1f83a6c40b2`) ve artık API şemasında da varlar;
   SDD'nin alan listesi henüz taşımıyor.
3. **SDD Ek B — 74 uç nokta.** `docs/EK_B_UC_NOKTALAR.md` güncel; SDD'nin
   kendi Ek B'sine aktarılması bekliyor.

### Bekleyen göçler — dağıtım yapılmadı

Sunucuda **üç göç** birikmiş olacak: `b6e2f81d3c07`, `c9a4b7e21f38` (Tur 2)
ve `d1f83a6c40b2` (bu tur). Sonuncusu veri dönüştürüyor; dağıtımdan önce
yedek alınmalı. Dağıtım kararı proje yürütücüsünde.
