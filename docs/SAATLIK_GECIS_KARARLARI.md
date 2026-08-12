# Saatlik Çalışma Düzenine Geçiş — Tasarım Kararları

**Tarih:** 12.08.2026 · **Sürüm:** 2 (K2, K6, K10, K15 karara bağlandı; K18 ve K19 eklendi)

Bu not, sistemin vardiya tabanlı çalışma düzeninden saatlik düzene geçişini ve
dönem öncesi birikimin hesaba katılmasını tasarlar. Kararlar onaylandıktan sonra
SRS ve SDD'ye işlenecek, uygulama planı bunlara dayanacaktır.

> Bu dosya `docs/` altındaki dört kanonik dokümandan biri **değildir**; onların
> hazırlık girdisidir. Onaylanan her karar ilgili kanonik dokümana taşınır ve
> Ürün Backlog'unun karar günlüğüne gerekçesiyle yazılır.

İki iş birlikte tasarlanır çünkü aynı altyapıyı paylaşırlar: ikisi de planlama
döneminin dışına taşan bir birikim katmanı gerektirir. Ayrı ayrı yapılırsa aynı
hesap iki yerde durur — bu projede bedeli birkaç kez ödenmiş bir kalıptır.
Uygulamada önce saatlik düzen gelir; birikim katmanı hemen ardından.

---

## 1. Neyin değişmediği

Bu, kapsamı doğru çizmek için önce yazılmalıdır.

- **Karar değişkeninin yapısı.** `x[p, gün, blok, nokta]` aynen kalır. Sürekli
  zamana (başlangıç ve süre birer tamsayı değişken, aralık nesneleri ve
  çakışmama kısıtları) geçilmez.
- **`vardiya_tipi` tablosunun yapısı.** Tablo zaten `baslangic`, `bitis`,
  `sure_saat`, `gece_mi`, `aktif` alanlarını taşıyor. Değişen, satır sayısı.
- **H1, H2, H4, H6, H7, H8.** H2 zaten "vardiya adına değil zaman bilgisine göre"
  yazılmış (SRS 4.2); H7 kesişim üzerinden çalışıyor; H8 nokta bazlı. Hiçbiri
  vardiya tipi adına bağlı değil.
- **TD-1** (blok başladığı güne yazılır), **TD-3** (hafta sonu), **TD-4**
  (müsaitlik dilimleri), **TD-8…TD-12**.
- Sürüm yönetimi, manuel düzenleme, doğrulama, çalışan paneli, kimlik doğrulama.

**Neden sürekli zamana geçilmiyor:** kullanıcının koyduğu kural — bir kişi-gün tek
kesintisiz bloktur, parçalı çalışma yoktur — iki modeli denk hâle getirir. Tek
blok, `(başlangıç, süre)` çiftiyle tam tanımlıdır. Sürekli zaman aynı çözüm
kümesini üretir ama arama uzayını, doğrulayıcıyı ve manuel düzenleme yüzeyini
karşılığında hiçbir şey vermeden karmaşıklaştırır. 322 testin ve altı kabul
kriterinin dayandığı yapıyı korumak bedava kazançtır.

---

## 2. Kararlar

### K1 — Çalışma bloğu

Bir **çalışma bloğu**, `(başlangıç saati, süre)` çiftidir. Bir personelin bir
takvim günündeki çalışması en fazla bir bloktur ve blok kesintisizdir; gün içinde
bölünmüş çalışma (dört saat çalışıp ara verip beş saat daha) tanımlı değildir.

Blok, bugünkü "vardiya tipi"nin genelleştirilmiş hâlidir ve aynı tabloda tutulur.
Terim olarak SRS'te "vardiya tipi" yerine "çalışma bloğu" kullanılacak, veritabanı
alan adları (`vardiya_tipi_id`) geriye dönük uyumluluk için korunacaktır.

**Yeni tanım:** TD-13.

### K2 — Blok kataloğunun kaynağı

Katalog, kullanıcının Tanımlar ekranından girdiği bir **listedir**; parametrik
olarak üretilmez (her başlangıç saati × her süre kombinasyonu değil).

*Gerekçe:* gerçek bir tesisin kullandığı blok sayısı sınırlıdır. Her saat ×
4–11 saat arası her süre 192 blok eder ve K1 kabul kriterini (60 saniye) tehdit
eder. Listeyle kullanıcı arama uzayını doğrudan kontrol eder ve mevcut CRUD ekranı
olduğu gibi kullanılabilir.

**Karar (12.08.2026):** mentöre sorulmayacak, K16'daki katalog kullanılacak.
Katalog **veri**dir; gerçek saatler sonradan öğrenilirse satırlar değiştirilir,
kod değişmez.

### K3 — Talebin ekseni değişir

Talep bugün `(gün tipi × vardiya tipi × nokta)` kırılımındadır. Blok sayısı yirmiyi
aştığında bu kırılım hem anlamını hem kullanılabilirliğini kaybeder: "06:00–14:00
bloğunda 7 kişi" demek istenen şey değildir, istenen "08:00–16:00 arasında 7 kişi
bulunsun"dur.

Yeni tanım: talep kaydı bir **zaman aralığıdır** — `(nokta, gün tipi, başlangıç,
bitiş, gereken sayı)`. Çözücü bu kaydı içeride saate açar ve kapsama kısıtını saat
başına yazar:

```
∀d, ∀t (saat), ∀n :
    Σ_p Σ_{b: t ∈ b} x[p,d,b,n] + eksik[d,t,n] ≥ talep[d,t,n]
```

*Gerekçe:* talebi 24 hücrelik satırlar olarak girdirmek Talep ekranını
yaşanmaz kılar; aralık kaydı hem kullanıcının düşünme biçimine uygundur hem daha
ifadelidir. Açılım tek yerde (çözücü bağlamı) yapılır, tüketiciler oradan alır.

**Etkilenen:** SRS 3.3.4, S1, `talep` tablosu (göç), Talep ekranı, ön kontrol,
kapsama açığı raporlaması.

### K4 — Kapsama üst sınırı zorunlu olmaktan çıkar

Bugün talep sayısı **üst sınır olarak zorunlu**, alt sınır olarak esnektir (SRS
S1). Saatlik düzende üst sınırın zorunlu kalması modeli çözülemez hâle
getirebilir: blok sınırları talep aralıklarının sınırlarıyla hizalanmadığında,
bir saatte fazla kadro oluşması **yapısal olarak kaçınılmaz** olur. Bu çözücünün
tercihi değil, blok kataloğunun sonucudur.

Yeni tanım: üst sınır da esnektir, kendi ceza terimiyle.

```
∀d, t, n :  Σ_p Σ_{b: t ∈ b} x[p,d,b,n] − fazla[d,t,n] ≤ talep[d,t,n]
Ceza:  w1 · Σ eksik  +  w1f · Σ fazla        (w1f ≪ w1)
```

*Gerekçe:* fazla kadro gerçek bir maliyettir (boşa geçen kişi-saat) ama açık kadar
ağır değildir. Cezalandırılmazsa çözücü kayıtsız kalır ve gereksiz fazla üretir;
zorunlu tutulursa hizalanmayan taleplerde çözüm hiç bulunamaz. Küçük ağırlıklı bir
ceza ikisinin arasındadır.

**Dikkat:** bu, S1'in bugünkü "fazla kadro ceza üretmez" kararını (SRS 4.3)
değiştirir. O karar manuel düzenleme içindi ve orada geçerli kalır — vardiya
yöneticisi bilinçli olarak fazla yazabilir, ceza görmez. Değişen, çözücü
tarafıdır. İki tarafın farklı davranması dokümanda açıkça yazılmalıdır, yoksa aynı
çizelge için çözücü ile doğrulayıcı farklı toplam raporlar.

**Başlangıç değeri:** `w1f = 2` (kişi-saat başına). Kalibrasyonda (K14)
netleşecek; kesin olan `w1f ≪ w1` bağıntısıdır.

### K5 — Gece tanımı ikiye ayrılır

Bugün tek bir `gece_mi` bayrağı hem H3'ü (ardışık gece sınırı) hem S2'yi (gece
adaleti) besliyor. Saatlik düzende ikisinin ihtiyacı ayrışır:

- **H3 için bayrak kalır.** "Bu blok bir gece nöbeti midir?" ikili bir sorudur ve
  ergonomik bir eşiğe dayanır. Bayrak tanımlanan alan olmaya devam eder; TD-2'nin
  öneri kuralı yeni blok tanımlanırken alanı ön-doldurur ve **tanımlı bir değeri
  asla ezmez**. Bu kural bir kez çiğnendi ve K3 kabul kriterinin 4,60 ile
  kalmasının iki nedeninden biriydi.
- **S2 için gece saati hesaplanır.** `gece_saat[b] = |b ∩ [20:00, 06:00]|`. Adalet
  artık gece *sayısı* değil gece *saati* üzerinden ölçülür.

*Gerekçe:* bloklar farklı uzunlukta olduğunda 11 saatlik bir gece bloğu ile 8
saatlik bir gece bloğunu aynı saymak adaleti bozar. Saat, karışık uzunluklu
kataloğun doğru ölçüsüdür. İki tanım çelişmez; farklı sorulara cevap verirler ve
bu ayrım TD-2'de açıkça yazılacaktır.

### K6 — H5 ikiye bölünür: mutlak tavan ve fazla çalışma eşiği

Bugünkü H5, kayan yedi günlük pencerede 45 saatlik **zorunlu tavan**dır. Yeni
düzende 45 saat tavan değil, **fazla çalışmanın eşiğidir**. Üstü yasaktır demek
yanlış olur; üstü fazla çalışmadır ve yıllık kotaya yazılır.

- **H5 (yeniden tanımlı):** kayan yedi günlük pencerede toplam saat
  `haftalik_mutlak_tavan`ı aşamaz. Bu, dinlenme amaçlı üst sınırdır ve zorunlu
  kalır. Varsayılan değer K7 ile tutarlı olmalıdır.
- **45 saat** artık bir kural değil, H10'un içindeki bir eşik parametresidir.

**Karar (12.08.2026):** `haftalik_mutlak_tavan = 66` saat. Günlük 11 saat × altı
çalışma günü (H6 yedinci günü izin bırakır) teorik üst sınırıdır; yani bu değer
H6, H9 ve H4 ile zaten tutarlıdır ve tek başına ek bir sınır getirmez. Diğer bütün
kural parametreleri gibi arayüzden değiştirilebilir — daha sıkı bir tavan
istendiğinde kod değil veri değişir.

### K7 — H9: günlük azami çalışma süresi

```
∀p, ∀d :  Σ_b sure[b] · y[p,d,b] ≤ azami_gunluk_saat        (varsayılan 11)
```

H1 zaten günde tek blok verdiğinden bu kural pratikte "katalogdaki hiçbir blok 11
saati aşamaz" demeye gelir. Yine de ayrı bir kural olarak yazılır: yasal dayanağı
farklıdır ve H1'in gelecekte gevşetilmesi hâlinde (gün içinde ikinci blok, fazla
mesai modeli) tek başına geçerliliğini korumalıdır. H6'nın H4 karşısındaki
durumuyla aynı gerekçe.

Ek olarak: katalog CRUD'unda 11 saati aşan blok tanımlanması **engellenir**, kural
katmanına bırakılmaz. Geçersiz veriyi girişte durdurmak, çözüm anında keşfetmekten
ucuzdur.

### K8 — H10: yıllık fazla çalışma kotası

```
w ∈ W(dönem) : dönem içinde tam kapanan takvim haftaları
haftalik_saat[p,w] = Σ_{d ∈ w} Σ_b sure[b] · y[p,d,b]
fazla[p,w] ≥ haftalik_saat[p,w] − fazla_calisma_esigi        (45)
fazla[p,w] ≥ 0
∀p :  devir[p] + Σ_{w ∈ W} fazla[p,w] ≤ yillik_fazla_kotasi   (270)
```

`devir[p]`, personelin içinde bulunulan kota yılı içinde bu dönemden **önce**
biriktirdiği fazla çalışma saatidir (K11).

**Zorunlu kısıttır.** Bu, projenin "çözülemez deme, açığı göster" ilkesine aykırı
görünebilir; değildir. Kısıt yalnızca fazla çalışmayı sınırlar, çalışmayı değil:
kotası dolmuş bir personel haftada 45 saate kadar çalışmaya devam eder, yalnızca
üstüne çıkamaz. `fazla[p,w] = 0` her zaman uygulanabilir bir değerdir, dolayısıyla
kısıt tek başına modeli çözülemez yapmaz.

Tek istisna: `devir[p]` zaten kotayı aşmışsa model çözülemez hâle gelir. Bu bir
veri hatasıdır ve **ön kontrolde** yakalanır (yeni bulgu tipi), çözüm anında
değil.

### K9 — İki farklı "hafta" bir arada yaşar

Bu, geçişin en kolay gözden kaçan noktasıdır ve açıkça yazılmadığı takdirde
karışacaktır.

| | Kapsam | Kullanan |
|---|---|---|
| **Kayan yedi günlük pencere** | herhangi bir yedi ardışık gün | H5 (mutlak tavan), H6 (asgari izin), H4 |
| **Takvim haftası (Pzt–Paz)** | ayrık, örtüşmeyen haftalar | H10 (fazla çalışma kotası) |

*Gerekçe:* kota "haftalık 45 saatin üstünde çalışılan saatlerin toplamı" olarak
tanımlıdır ve bir toplam ancak **ayrık** pencerelerde anlamlıdır. Kayan pencerede
aynı saat yedi farklı pencereye girer; toplamı yedi katına çıkarır. Dinlenme
kuralları ise tersine kayan olmak zorundadır — takvim haftasına dayanan bir
dinlenme kuralı, pazar–pazartesi sınırında yan yana iki yoğun haftayı serbest
bırakır.

**Yeni tanım:** TD-14. TD-7 bu ayrımı gösterecek biçimde güncellenir.

### K10 — Adalet ufku ile yasal ufuk ayrılır

Bugünkü TD-6 tek cümledir: adalet hesapları yalnızca planlama dönemini kapsar,
ısıtma penceresi dahil edilmez. Bu iki ayrı ufka bölünür:

- **Yasal sayaçlar (H10).** Isıtma penceresini **ve** devir bakiyesini kapsar.
  Kapsamazsa dönem sınırında bölünen takvim haftası eksik hesaplanır ve kota
  sessizce aşılır — bu, kuralın hiç olmamasıyla aynı sonucu verir. Isıtma penceresi
  (TD-5) zaten önceki yedi günü sabit girdi olarak modele koyuyor; bölünen haftanın
  önceki kısmı tam olarak oradan okunur.
- **Adalet sayaçları (S2, S3, S4).** Bugün dönem içidir. Madde 8 ("önceki
  dönemlerin göz önünde bulundurulması") bunu değiştirir: sayaçlar yapılandırılabilir
  bir **adalet ufkunu** kapsar.

**Karar (12.08.2026):** adalet ufku **kayan 90 gündür** ve parametredir. Dönem
uzunluğu değişken olduğu için "son N dönem" tutarsız pencereler üretirdi; "yıl
başından bugüne" ise ufku ocakta sıfırlayıp aralıkta on iki aya çıkarırdı — aynı
kişi yıl başında ağır gece yükü alsa bile şubatta bunun izi kalmazdı.

**Yeni tanım:** TD-6 yeniden yazılır, TD-15 eklenir.

### K11 — Birikim tek kaynaktan türetilir, saklanmaz

Dönem öncesi birikim — hem kota hem adalet için — **yayınlanmış sürümlerin
atamalarından türetilir**. Sayaç tablosunda saklanmaz.

*Gerekçe:* saklanan sayaç, bir dönem yeniden çözüldüğünde veya bir sürüm arşive
alındığında bayatlar; TD-12'nin tercih karşılanma durumu için verdiği kararla aynı
gerekçe. Türetme tek bir serviste toplanır (`GecmisSayaclar`); çözücü, ön kontrol,
analiz ve kabul ölçümü aynı tabandan okur. Havuz tanımının `Baglam.uygun_havuz`'a
taşınmasıyla aynı desen.

Tek istisna **devir bakiyesidir**: sistem kota yılının başından beri her şeyi
bilmiyor olabilir (canlıya alınmadan önceki aylar). Personel kaydına
`devir_fazla_calisma_saat` alanı eklenir; sistemin bildiği dönemlerin fazla
çalışması buna **eklenerek** hesaplanır, onun yerine geçmez.

### K12 — S2 ve S3'ün birimi saate döner

S2 gece *sayısı* yerine gece *saati*, S3 hafta sonu *vardiyası* yerine hafta sonu
*saati* üzerinden ölçülür. S4 zaten saat üzerindedir.

*Sonuç:* üç adalet hedefi de aynı birimdedir ve `w2`, `w3`, `w4` doğrudan
karşılaştırılabilir hâle gelir. Bugünkü `w4 ≈ w2/8` düzeltmesi (bir vardiya = 8
saat) gereksizleşir — bu düzeltme zaten karışık uzunluklu katalogda yanlış
olurdu.

Uygun havuz mantığı (`P_gece`, `P_hs`) aynen korunur.

### K13 — S6 yeniden tanımlanır

"Aynı vardiya tipi" kavramı kalmadığı için S6'nın bugünkü tanımı uygulanamaz.

```
kayma[p,d] = dairesel_fark( baslangic[b_{d+1}], baslangic[b_d] )
           = min( |Δ|, 24 − |Δ| )
degisim[p,d] = 1  eğer p, d ve d+1 günlerinde çalışıyor ve
                  kayma > desen_toleransi_saat
Ceza:  w6 · Σ degisim[p,d]
```

Dairesel fark zorunludur: 22:00 ile 02:00 arasındaki kayma dört saattir, yirmi
saat değil. Tolerans parametredir (öneri: 2 saat) — bir saatlik kaymayı
cezalandırmak, kataloğun ince taneli olmasının anlamını yok eder.

S6b (bina tutarlılığı) değişmez; bütün noktalar tesis geneli olduğu için hâlâ
etkisizdir.

### K14 — Ağırlıklar yeniden kalibre edilir

S2/S3'ün birimi değiştiği, S1'e yeni bir terim (`w1f`) eklendiği ve S6'nın tanımı
değiştiği için mevcut ağırlık seti (S1=10000, S2=10, S3=8, S4=1, S5=12, S6=8, S7=6,
S8=15) geçersizdir. Kalibrasyon, kural kataloğu ve çözücü bittikten sonra ayrı bir
adım olarak yapılır.

`w1` baskınlığını koruyan regresyon testi güncellenir ve korunur.

### K15 — Gece çalışması süresi

4857 sayılı kanunun 69. maddesi gece dönemine denk gelen çalışmayı 7,5 saatle
sınırlar. Bugünkü 8 saatlik gece vardiyası bunu zaten aşmaktadır; saatlik düzende
bu kural ilk kez temsil edilebilir hâle gelir.

**Karar (12.08.2026):** bu kural **kataloğa girmeyecek.** Güvenlik hizmeti
kesintisiz yürütülen bir iştir ve mevcut işleyişte gece vardiyası sekiz saattir;
kuralın eklenmesi bugünkü düzeni tek başına kural dışı gösterirdi. Karar bilinçli
olarak alınmıştır ve burada kayıtlıdır — sessizce atlanmamıştır. İleride
gerekirse H11 olarak eklenebilir; kural kataloğunun yapısı buna hazırdır.

### K16 — Blok kataloğu

Kullanılacak katalog (K2 uyarınca kesinleşti) — **veridir**, kod değildir:

| Blok | Başlangıç | Süre | gece_mi |
|---|---|---|---|
| 08:00–16:00 | 08:00 | 8 | Hayır |
| 16:00–24:00 | 16:00 | 8 | Hayır |
| 00:00–08:00 | 00:00 | 8 | Evet |
| 08:00–20:00 | 08:00 | 12 | Hayır |
| 20:00–08:00 | 20:00 | 12 | Evet |
| 06:00–16:00 | 06:00 | 10 | Hayır |
| 14:00–24:00 | 14:00 | 10 | Hayır |

Yedi blok — bugünkünün iki katından biraz fazla, K1'i tehdit etmeyecek ölçekte.
Mevcut üç vardiya korunmuş, üstüne 12 ve 10 saatlik seçenekler eklenmiştir; 12
saatlik bloklar fazla çalışma eşiğini gerçekten tetikler ve kotanın test
edilebilmesini sağlar.

### K17 — Performans tavanı

Değişken sayısı blok kataloğunun büyüklüğüyle doğrudan çarpılır. K1 kabul kriteri
(40 personel × 28 gün < 60 saniye, referans donanımda) risk altındadır.

Uygulama sırasında blok sayısı arttıkça ölçüm alınır. Referans ölçekte süre eşiğin
yarısını aşarsa katalog kırpılır veya çözücüye simetri kırma ipucu verilir. Ölçüm
`kabul_olcumu.py` ile yapılır ve her turda tekrarlanır — sona bırakılmaz.

### K18 — Ön kontrol bulguları çözümü engellemez

**Gözlenen hata (12.08.2026).** Ön kontrol yapısal bir bulgu ürettiğinde çözüm işi
hiç başlatılmıyor; sürüm "başarısız" damgasıyla, tek bir atama olmadan kalıyor.
Ekranda görülen: *"18 nolu yetkinlik havuzunda 16 vardiyalık açık var"* → sonuç
özeti başarısız → çizelgede "bu sürümde henüz atama yok".

Bu davranış, SRS **FR-5.2'nin doğrudan ihlalidir**: "Sistem, personel yetersizliği
durumunda çözümü reddetmek yerine çizelgeyi üretmeli ve kapsama açıklarını
göstermelidir." Aynı zamanda projeyi ödevden ayıran iki özellikten birincisini
işlevsiz bırakır — S1'in zorunlu kısıt değil baskın ağırlıklı esnek hedef olarak
tasarlanmasının tek nedeni budur.

Ön kontrolün söyleyebildiği ile çözücünün söyleyebildiği aynı şey değildir. Ön
kontrol "on altı vardiyalık açık var" der; hangi gün, hangi saat, hangi noktada
olduğunu **söyleyemez**, çünkü kadro aritmetiğine bakar, çizelgeye değil. Kullanıcının
ihtiyacı olan bilgi ikincisidir: açığı kapatmak için nereye personel bulacağını
ancak o zaman bilir. Çözümü engellemek, kullanıcıyı elindeki tek teşhis
aracından mahrum bırakır.

**Yeni tanım.** Ön kontrol bulguları hiçbir zaman çözüm işini düşürmez. İki
seviye ayrımı korunur ama anlamı değişir:

| Seviye | Anlamı | Davranış |
|---|---|---|
| Kesin bulgu | "Bu açık kesinlikle oluşacak" | Çözüm çalışır; bulgu sonuçla birlikte gösterilir |
| Uyarı | "Sonucu şu koşulla oku" | Çözüm çalışır; bulgu sonuçla birlikte gösterilir |

Ayrım okuma amaçlıdır: kesin bulgu, çıkan açığın kadro yetersizliğinden
kaynaklandığını **önceden** doğrular ve kullanıcı çizelgeyi buna göre okur.

İşin düşmesinin tek meşru nedeni, çözücünün modeli çözülemez bulmasıdır — yani
zorunlu kısıtların birbiriyle çeliştiği durum. Bu, kapsama açığından ayrı bir
şeydir ve SRS FR-5.5 bunu zaten ayrı bildirilmesi gereken bir durum olarak
tanımlar.

**S1 pasifken.** S1 pasifleştirilmişse kapsama açığı değişkenleri hiç oluşmaz ve
sistem "açık yok" raporlar (SDD 5.2). Bu tehlikelidir ama çözümü engellemek de
doğru cevap değildir; kullanıcı S1'i bilinçli olarak kapatmış olabilir. Doğru
davranış, çizelgeyi üretmek ve **kapsama raporlanmıyor** damgasını sürüm kaydında
kalıcı kılmaktır — yalnızca çözüm anındaki bir uyarı olarak değil, sürümün
raporunda da görünür biçimde.

### K19 — Kapsama oranı atamalardan hesaplanır

**Gözlenen hata (12.08.2026).** Hiç ataması olmayan bir sürümde kapsama **%100**,
açık **0** gösteriliyor.

Sebebi SDD 5.7'de yazılıdır: kapsama oranı "kapsama açığı tablosundan türetilir".
Çözüm hiç çalışmadığında o tabloda kayıt bulunmaz, dolayısıyla eksik sıfır sayılır
ve oran %100 çıkar. Sistem "açık kaydı yok" ile "açık yok"u karıştırmaktadır.

**Yeni tanım.** Kapsama oranı, **karşılanan kişi-saatin toplam talep kişi-saatine
oranıdır** ve atama kayıtlarından hesaplanır:

```
karsilanan = Σ_{d,t,n} min( atanan[d,t,n], talep[d,t,n] )
toplam     = Σ_{d,t,n} talep[d,t,n]
kapsama    = karsilanan / toplam          (toplam = 0 ise tanımsız, "—" gösterilir)
```

Kapsama açığı tablosu bir **raporlama detayıdır**, oranın kaynağı değildir. Aynı
bilginin iki türetme yolu bulunması bu projede tekrarlayan bir hata kalıbıdır ve
burada iki yol ayrışmıştır: biri "açık kaydı yok" der, diğeri "hiç atama yok".

`min(...)` kullanılması, fazla kadronun kapsama oranını şişirmesini engeller: bir
saatte talebin üzerine çıkmak, başka bir saatteki açığı kapatmaz.

Atama yokken oran **%0**'dır. Talep de yoksa oran tanımsızdır ve tire ile
gösterilir; sıfır bölme yerine yüzde yüz varsaymak, boş bir dönemi mükemmel bir
çizelge gibi gösterir.

### K20 — Bulgu metinleri kimliği değil adı gösterir

Ekrandaki bulgu *"18 nolu yetkinlik havuzunda"* diyor. Kullanıcı 18 numaralı
yetkinliğin hangisi olduğunu bilmez; ekranın hiçbir yerinde bu eşleme yoktur.
Bulgu metinleri veritabanı kimliği değil ad taşır: "Vardiya Şefi yetkinlik
havuzunda". Kimlik gerekiyorsa bağlantı olarak verilir, metnin kendisinde değil.

---

## 3. Doküman etkisi

| Doküman | Bölüm | Değişiklik |
|---|---|---|
| SRS | 3.2 | TD-2, TD-6, TD-7 yeniden yazılır; TD-13, TD-14, TD-15 eklenir |
| SRS | 3.3 | 3.3.1 blok kataloğu, 3.3.4 talep aralıkları, 3.3.5 yeni parametreler, 3.3.6 kadro analizi yeniden hesaplanır |
| SRS | 4.2 | H5 yeniden yazılır; H9, H10 eklenir; (H11 karar bekliyor) |
| SRS | 4.3 | S1 (üst sınır esnek), S2, S3 (saat birimi), S6 (kayma) yeniden yazılır |
| SRS | 4.4 | Amaç fonksiyonu yeniden yazılır — `w1f` eklenir, tanımsız `eksikK` terimi kaldırılır, eksik `w6b` yazılır |
| SRS | 5.1, 5.4, 5.5 | Blok kataloğu CRUD kuralları, talep aralığı girişi, ön kontrolün yeni bulgu tipleri |
| SDD | 4.2 | `talep` tablosu (aralık), `personel.devir_fazla_calisma_saat`, blok kataloğu kısıtları |
| SDD | 5.2 | Ön kontrole kota ve hizalama bulguları; bulguların işi düşürmemesi (K18) |
| SDD | 5.7 | Kapsama oranının atamalardan hesaplanması (K19) |
| SDD | 5.3 | Model kurma — saate açılım, takvim haftası kümeleri, geçmiş sayaçların modele girişi |
| SDD | 5.7 | Analiz metrikleri saat birimine hizalanır, kota göstergesi eklenir |
| SDD | 6.3 | Talep ekranı (aralık girişi), Çizelge ızgarası (değişken uzunluklu blok gösterimi), Kural ekranı, Analiz |
| SDD | yeni | `GecmisSayaclar` servisi |
| Backlog | karar günlüğü | Bu notta onaylanan her karar |
| Backlog | B-01 | Kümülatif adalet — kapsama alınıyor |
| TASARIM_REFERANSI | vardiya renk rampası | Üç sabit tip yerine başlangıç saati bandından hesaplanan renk |

---

## 4. Karar bekleyenler — özet

| # | Konu | Durum |
|---|---|---|
| K2 | Başlangıç saatleri ve süreler | **Karara bağlandı** — K16'daki katalog |
| K4 | `w1f` başlangıç değeri | Başlangıç 2; kalibrasyonda (K14) netleşecek |
| K6 | `haftalik_mutlak_tavan` | **Karara bağlandı** — 66 saat, parametre |
| K10 | Adalet ufku | **Karara bağlandı** — kayan 90 gün, parametre |
| K15 | Gece çalışması 7,5 saat | **Karara bağlandı** — kataloğa girmeyecek |

Açık karar kalmamıştır; kural kataloğu bölümü yazılabilir. Bütün bu değerler kural
parametresidir ve arayüzden değiştirilebilir — hiçbiri koda gömülmez.
