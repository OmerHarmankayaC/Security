**TED ÜNİVERSİTESİ**

**CMPE 399 — Yaz Stajı**

BOTAŞ Boru Hatları ile Petrol Taşıma A.Ş.

**VARDİYA ÇİZELGELEME KARAR DESTEK ARACI**

**Yazılım Gereksinim Belirtimi**

(Software Requirements Specification)

**Ömer HARMANKAYA**

Endüstri Mühendisliği / Bilgisayar Mühendisliği

05.08.2026

Sürüm 1.0

# Revizyon Geçmişi

| Ad | Tarih | Değişiklik Nedeni | Sürüm |
| --- | --- | --- | --- |
| Ömer HARMANKAYA | 05.08.2026 | İlk sürüm — alan modeli, kural kataloğu ve gereksinimler tanımlandı | 1.0 |
| Ömer HARMANKAYA | 05.08.2026 | Görev noktası boyutu eklendi (TD-10, TD-11); H1, H8, S1, S6 ve S8 yeniden yazıldı; uygulama alanı olarak güvenlik personeli tanımlandı (bölüm 3.3) | 1.1 |
| Ömer HARMANKAYA | 07.08.2026 | Görev noktaları tesis geneli üç noktaya indirildi ve planlama dönemi varsayılanı bir haftaya çekildi (bölüm 3.3); S4'ün hedefi kişisel sözleşme saatinden talebin orantılı payına çevrildi (hedef ulaşılamaz olduğunda ceza sabite dönüşüyor ve ayırt ediciliğini kaybediyordu); S6b'nin mevcut uygulama alanında etkisiz kaldığı belirtildi | 1.2 |
| Ömer HARMANKAYA | 07.08.2026 | NFR-1'in referans kadrosu otuzdan kırk personele çıkarıldı; Proje Tanım Dokümanı ve Yazılım Tasarım Dokümanı ile arasındaki üçlü tutarsızlık giderildi | 1.3 |



# 1. Giriş

## 1.1 Amaç

Bu doküman, Vardiya Çizelgeleme Karar Destek Aracı'nın fonksiyonel ve fonksiyonel olmayan gereksinimlerini tanımlar. Doküman, geliştirme sırasında referans alınacak; üretilen sistemin kabul değerlendirmesi buradaki gereksinimler üzerinden yapılacaktır. Hedef okuyucu kitlesi proje yürütücüsü, kurum mentörü ve akademik danışmandır.

## 1.2 Kapsam

Sistem, kesintisiz çalışan tesislerde dönemlik personel vardiya çizelgesi üreten web tabanlı bir karar destek aracıdır. Girdisi personel listesi, yetkinlikler, izin ve müsaitlik bilgileri, vardiya başına gereken personel sayısı ve çalışma kurallarıdır. Çıktısı, tüm zorunlu kuralları sağlayan, yükü dengeli dağıtan ve tercihleri gözeten bir çizelgedir.

Kapsam ilkesi, proje tanım dokümanında tanımlandığı gibidir: sistem, halihazırda o işi yapan vardiya yöneticisinin işini devralır, insan kaynaklarının işini değil. İzin talebi ve onay akışı, bordro, puantaj, vardiya takası, bildirim altyapısı ve kurum sistemlerine entegrasyon kapsam dışıdır.

## 1.3 Tanımlar ve Kısaltmalar

| Terim | Tanım |
| --- | --- |
| Dönem | Çizelgenin üretildiği takvim aralığı. Varsayılan uzunluk dört haftadır, kullanıcı değiştirebilir. |
| Vardiya tipi | Ad, başlangıç saati, bitiş saati ve süre ile tanımlanan çalışma dilimi (örn. gece 20:00–08:00). |
| Atama | Bir personelin belirli bir günde belirli bir vardiya tipine yerleştirilmesi. |
| Talep | Bir gün ve vardiya tipi için gereken personel sayısı ve yetkinlik dağılımı. |
| Zorunlu kısıt | İhlal edilmesi mümkün olmayan kural. Çözücü bu kuralları ihlal eden çözüm üretemez. |
| Esnek hedef | İhlal edildiğinde ceza puanı üreten kural. Çözücü toplam cezayı en aza indirmeye çalışır. |
| Isıtma penceresi | Önceki dönemin son günlerine ait, karar değişkeni olmayan sabit atamalar. |
| Kapsama açığı | Bir gün ve vardiya için talep edilen personel sayısının atanabilen sayıyı aşması. |
| CP-SAT | Kısıt programlama tabanlı çözücü (Google OR-Tools). |



## 1.4 Referanslar

- Vardiya Çizelgeleme Karar Destek Aracı — Proje Tanım Dokümanı, sürüm 1.0, 05.08.2026

- Google OR-Tools CP-SAT Solver dokümantasyonu

- 4857 sayılı İş Kanunu — çalışma süreleri ve gece çalışmasına ilişkin hükümler

## 1.5 Doküman Yapısı

Bölüm 2 sistemin genel tanımını, aktörleri ve varsayımları verir. Bölüm 3 alan modelini ve sistem genelinde geçerli temel tanımları içerir; bu bölümdeki tanımlar sonraki bölümlerin tamamı için bağlayıcıdır. Bölüm 4 kural kataloğunu biçimsel olarak tanımlar. Bölüm 5 fonksiyonel gereksinimleri, bölüm 6 kullanım senaryolarını, bölüm 7 arayüz gereksinimlerini, bölüm 8 fonksiyonel olmayan gereksinimleri, bölüm 9 izlenebilirlik matrisini verir.

# 2. Genel Tanım

## 2.1 Ürün Perspektifi

Sistem bağımsız bir web uygulamasıdır ve mevcut bir kurum sisteminin parçası değildir. İki katmandan oluşur. Yönetim katmanı, tanımların girildiği ve çizelgelerin görüntülendiği veritabanı ve arayüz katmanıdır; çözücüden bağımsız olarak da çalışabilir. Çözücü ve analiz katmanı, çizelgeyi üreten kısıt programlama modelini ve sonuç değerlendirmesini içerir.

## 2.2 Aktörler

| Aktör | Tanım | Temel Yetkileri |
| --- | --- | --- |
| Vardiya Yöneticisi | Çizelgeyi kuran ve uygulanmasından sorumlu kişi | Tüm tanımları yönetir, çözüm çalıştırır, çizelgeyi düzenler ve yayınlar, tercihleri onaylar |
| Personel | Çizelgeye tabi çalışan | Yalnızca kendi yayınlanmış çizelgesini görüntüler, tercih bildirir |
| Birim Yöneticisi | Çizelgeyi denetleyen kişi | Çizelgeleri ve analiz raporlarını görüntüler, değişiklik yapamaz |



## 2.3 İşletim Ortamı

- Sunucu tarafında kısıt programlama çözücüsünü barındıran bir uygulama servisi ve ilişkisel veritabanı

- İstemci tarafında güncel masaüstü tarayıcılar (yönetici arayüzü) ve mobil tarayıcılar (çalışan arayüzü)

## 2.4 Tasarım ve Uygulama Kısıtları

- Kural tanımları veri olarak saklanır, uygulama koduna gömülmez.

- Kurallar vardiya adına değil zaman bilgisine göre ifade edilir; vardiya yapısının değişmesi kod değişikliği gerektirmez.

- Çözücü modeli ile manuel düzenleme doğrulayıcısı aynı kural tanımından beslenir; kuralın iki ayrı yerde kodlanması yasaktır.

- Sistem gerçek kurum verisi olmadan çalışabilir olmalıdır.

## 2.5 Varsayımlar ve Bağımlılıklar

- İzin, rapor ve eğitim bilgileri sisteme yönetici tarafından elle veya dosyayla girilir; kurum sisteminden otomatik alınmaz.

- Aynı çizelge sürümü üzerinde aynı anda tek bir yönetici çalışır. Eş zamanlı düzenleme senaryosu kapsam dışıdır.

- Zorunlu kısıtlar yasal ve fiziksel niteliktedir; kendi aralarında çelişmeleri beklenmez.

- Kuruma özgü kural değerleri parametre olarak tanımlanmıştır; gerçek değerler öğrenildiğinde kod değişikliği gerekmez.

# 3. Alan Modeli ve Temel Tanımlar

## 3.1 Varlıklar

| Varlık | Temel Alanlar |
| --- | --- |
| Personel | Ad, sicil, sözleşme tipi, haftalık hedef saat, aktiflik başlangıç ve bitiş tarihi |
| Yetkinlik | Ad, açıklama |
| Personel-Yetkinlik | Personel, yetkinlik (seviyesiz çoktan-çoğa ilişki) |
| Vardiya Tipi | Ad, başlangıç saati, bitiş saati, süre (saat), gece_mi bayrağı |
| Bina | Ad, açıklama |
| Görev Noktası | Ad, bağlı olduğu bina (boş ise tesis geneli), ön koşul yetkinliği (boş olabilir), aktiflik |
| Gün Tipi | Hafta içi, hafta sonu, resmî tatil |
| Talep | Gün tipi veya tekil tarih, vardiya tipi, görev noktası, gereken personel sayısı |
| Müsaitlik Kaydı | Personel, başlangıç tarihi, bitiş tarihi, dilim (tam gün / öğleden önce / öğleden sonra), tip (yıllık izin, rapor, eğitim, mazeret) |
| Tercih | Personel, tarih veya tarih aralığı, tip (çalışmama, vardiya tipi tercihi), durum (beklemede, onaylandı, reddedildi) |
| Kural | Kimlik, tip (zorunlu / esnek), parametreler, ağırlık (esnekse), aktiflik |
| Dönem | Başlangıç tarihi, bitiş tarihi, tercih son bildirim tarihi |
| Çizelge Sürümü | Dönem, sürüm numarası, durum, oluşturma zamanı, çözüm süresi, ceza dökümü |
| Atama | Çizelge sürümü, personel, tarih, vardiya tipi, görev noktası, kilitli_mi bayrağı, kaynak (çözücü / manuel) |



## 3.2 Temel Tanımlar ve Sayma Kuralları

Bu bölümdeki tanımlar sistemin tamamı için bağlayıcıdır. Bir kuralın nasıl değerlendirileceği, bir metriğin nasıl sayılacağı ve arayüzün neyi göstereceği bu tanımlara dayanır.

### TD-1 — Vardiyanın güne ilişkilendirilmesi

Bir vardiya, başladığı takvim gününe ilişkilendirilir. Gece yarısını aşan vardiyalar da başlangıç gününe yazılır. Bu kural atama, sayma, raporlama ve arayüz gösteriminin tamamında geçerlidir.

### TD-2 — Gece vardiyası tanımı

Gece vardiyası, vardiya tipi üzerindeki gece_mi bayrağıyla belirlenir. Bayrak hesaplanan değil tanımlanan bir alandır. Yeni bir vardiya tipi oluşturulurken, tipin zaman aralığının 20:00–06:00 aralığıyla kesişimi dört saat veya daha fazlaysa bayrak otomatik olarak önerilir; nihai değeri kullanıcı belirler.

### TD-3 — Hafta sonu tanımı

Bir vardiya, başlangıç günü cumartesi veya pazar ise hafta sonu vardiyasıdır. TD-1 ile tutarlı olarak, cuma günü başlayıp cumartesi biten vardiya hafta sonu sayılmaz; pazar günü başlayıp pazartesi biten vardiya hafta sonu sayılır.

Resmî tatiller ayrı bir gün tipi bayrağıyla işaretlenir. Adalet hesaplarında resmî tatil vardiyaları varsayılan olarak hafta sonu vardiyalarıyla aynı sayaca eklenir; bu davranış yapılandırma ile kapatılabilir.

### TD-4 — Müsaitlik dilimleri

Müsaitlik kaydı bir zaman aralığı olarak modellenir: tam gün 00:00–24:00, öğleden önce 00:00–12:00, öğleden sonra 12:00–24:00. Kural tektir: bir personel, müsait olmadığı zaman aralığıyla kesişen hiçbir vardiyaya atanamaz.

Bu modelin sonucu olarak gece vardiyaları özel bir işlem gerektirmez. 20:00–08:00 vardiyası, başlangıç gününün öğleden sonrası ile ertesi günün öğleden öncesiyle kesişir; her iki dilimden birinde müsaitlik kaydı bulunması atamayı engeller.

### TD-5 — Isıtma penceresi ve dönem sınırı

Bir dönemin çizelgesi üretilirken, önceki yayınlanmış çizelgenin son yedi gününe ait atamalar modele sabit girdi olarak dahil edilir. Bu atamalar karar değişkeni değildir ve değiştirilemez.

Zaman penceresine dayanan tüm kurallar — asgari dinlenme, ardışık gece sınırı, ardışık çalışma günü sınırı ve kayan yedi günlük saat tavanı — ısıtma penceresi ile planlama döneminin birleştirildiği zaman ekseni üzerinde değerlendirilir. Böylece dönemin ilk gününde, önceki dönemin son gecesinden çıkan personele geçersiz atama yapılması engellenir.

Adalet sayaçları ısıtma penceresini içermez (bkz. TD-6). Önceki dönem bulunmadığında ısıtma penceresi boştur.

### TD-6 — Adalet ufku

Yük dengesi ve adalet hesapları yalnızca planlama dönemi içindeki atamaları kapsar. Geçmiş dönemlerden devreden kümülatif denge bu sürümde hesaba katılmaz.

### TD-7 — Haftalık saat penceresi

Haftalık saat tavanı, takvim haftası yerine kayan yedi günlük pencere üzerinde değerlendirilir. Bir vardiyanın süresi tamamıyla başlangıç gününe yazılır (TD-1). Bunun sonucu olarak, pencerenin son gününde başlayan bir vardiyanın ertesi güne taşan saatleri de o pencereye sayılır. Bu, bilinçli olarak kabul edilmiş bir yaklaşıklıktır; alternatifi vardiya süresini günlere bölmektir ve modeli gereksiz karmaşıklaştırır.

### TD-8 — Çizelge sürümü durum modeli

Bir çizelge sürümü şu durumlardan birindedir: taslak, çözüldü, yayınlandı, arşiv. Yayınlanmış bir sürüm salt okunurdur. Yayınlanmış çizelge üzerinde değişiklik gerektiğinde, sistem o sürümün kopyasından yeni bir taslak sürüm oluşturur; değişiklikler bu taslak üzerinde yapılır ve yayınlandığında önceki sürüm arşiv durumuna geçer.

Personele yalnızca yayınlanmış durumdaki sürüm gösterilir. Bu sayede yöneticinin üzerinde çalıştığı taslak ile çalışanın gördüğü çizelge hiçbir zaman karışmaz.

### TD-9 — Yetkinlik modeli

Yetkinlikler seviyesizdir. Bir personel bir yetkinliğe ya sahiptir ya değildir. Yetkinlik tek bir biçimde kullanılır: her görev noktasının en fazla bir ön koşul yetkinliği bulunur ve o noktaya atanacak personelin bu yetkinliğe sahip olması gerekir. Ön koşulu bulunmayan noktalara her personel atanabilir.

Bir yetkinliğin dışlayıcı davranışı, ayrı bir mekanizma yerine yetkinlik dağılımıyla ifade edilir. Bir personel grubunun yalnızca kendi noktasında çalışması isteniyorsa, o gruba diğer noktaların ön koşul yetkinliği verilmez. Bu sayede tek yönlü ve çift yönlü kısıtlama aynı modelle karşılanır ve kural kataloğuna yeni bir kural tipi eklemek gerekmez.

### TD-10 — Görev noktası modeli

Atamanın birimi vardiya değil, vardiya içindeki görev noktasıdır. Bir görev noktası, personelin fiilen bulunacağı yeri ve orada üstlendiği rolü birlikte temsil eder. Talep, ön koşul yetkinliği ve kapsama açığı raporlaması bu birim üzerinden tanımlanır.

Görev noktası isteğe bağlı olarak bir binaya bağlanır. Binaya bağlı olmayan noktalar tesis geneli olarak değerlendirilir ve tek bir kadroyla bütün binalara hizmet eder. Bina bilgisi zorunlu kısıtlarda kullanılmaz; raporlamada ve S6 kapsamındaki bina tutarlılığı hedefinde kullanılır.

Bu tanımın gerekçesi eşleme ile sayma arasındaki farktır. Yetkinlik gereksinimi vardiya düzeyinde sayılırsa, birden fazla yetkinlik taşıyan bir personel tek atamayla birden çok gereksinimi karşılamış görünür; oysa aynı anda tek bir noktada bulunabilir. Nokta boyutu bu tutarsızlığı modelin yapısında ortadan kaldırır.

### TD-11 — Personelin binaya bağlılığı

Personel belirli bir binaya bağlı değildir; tek havuz olarak değerlendirilir ve tesisteki bütün noktalara atanabilir. Aynı personelin gün aşırı bina değiştirmesi zorunlu kısıtla engellenmez, S6 kapsamında esnek biçimde cezalandırılır. Bu tercihin nedeni, kadronun daraldığı dönemlerde bina değişiminin kapsama açığını kapatan tek hamle olabilmesidir.

## 3.3 Uygulama Alanı: Güvenlik Personeli

Bu bölüm, bölüm 3.1 ve 3.2'de tanımlanan yapının ilk uygulama alanına ait somut değerlerini içerir. Buradaki hiçbir değer koda gömülü değildir; tamamı bölüm 5.1'deki tanım yönetimi gereksinimleri aracılığıyla düzenlenebilen veridir. Değerler mevcut işleyişten alınmış varsayımlara dayanmakta olup mentör görüşmesinde teyit edilecektir.

Planlama dönemi varsayılan olarak bir haftadır; yönetici bunu istediği bir uzunluğa çıkarabilir. Bu bir kısıt değil bir başlangıç değeridir — sistem daha uzun dönemleri de destekler ve NFR-1'in kırk personel/yirmi sekiz gün ölçeğindeki performans hedefi bu daha büyük dönemler için hâlâ geçerlidir (bkz. 3.3.6).

### 3.3.1 Vardiya Tipleri

| Vardiya Tipi | Saat Aralığı | Süre | gece_mi |
| --- | --- | --- | --- |
| Gece | 00.00 – 08.00 | 8 saat | Evet |
| Gündüz | 08.00 – 16.00 | 8 saat | Hayır |
| Akşam | 16.00 – 24.00 | 8 saat | Hayır |



### 3.3.2 Yetkinlikler

| Yetkinlik | Tanım |
| --- | --- |
| Güvenlik Görevi | Güvenlik noktasında (kapı ve kontrol odası görevlerini birlikte kapsar) görev alabilmenin ön koşuludur; kontrol odasında görevli personel ayrı bir meslek grubu değil, aynı noktanın bir parçasıdır. |
| Vardiya Şefi | Vardiya şefliği noktasının ön koşuludur. Bu yetkinliğe sahip personel Güvenlik Görevi yetkinliğini de taşır ve müracaat dışındaki bütün noktalarda görevlendirilebilir. |
| Müracaat Görevlisi | Müracaat noktasının ön koşuludur. Bu yetkinliğe sahip personel Güvenlik Görevi yetkinliğini taşımaz; dolayısıyla başka bir noktaya atanamaz. Aynı biçimde müracaat noktası da bu yetkinliği taşımayan personele kapalıdır. |



Müracaat görevlilerinin çift yönlü dışlayıcılığı, TD-9'da tanımlandığı üzere ayrı bir kural tipiyle değil yetkinlik dağılımıyla sağlanmaktadır.

### 3.3.3 Görev Noktaları

| Görev Noktası | Bina | Ön Koşul Yetkinliği |
| --- | --- | --- |
| Vardiya Şefliği | — (tesis geneli) | Vardiya Şefi |
| Güvenlik | — (tesis geneli) | Güvenlik Görevi |
| Müracaat | — (tesis geneli) | Müracaat Görevlisi |



Tesiste iki bina bulunmaktadır, ancak görev noktaları bina ayrımı yapılmadan tesis geneli tanımlanmıştır: kapı ve kontrol odası arasındaki ayrım kaldırılmış, ikisi tek bir "Güvenlik" noktasında birleştirilmiştir — kontrol odasında görevli personel zaten ayrı bir meslek grubu değil, aynı yetkinliğe sahip bir güvenlik görevlisiydi (bkz. 3.3.2), dolayısıyla atamanın hangi fiziksel noktaya yazıldığı modelin ihtiyaç duyduğu bir bilgi değildir; kim hangi kapıda veya kontrol odasında duracağını vardiya şefi o gün belirler. Aynı gerekçeyle müracaat noktası da bina ayrımı olmadan tanımlanmıştır. Devriye görevi bulunmamaktadır.

### 3.3.4 Talep Matrisi

| Görev Noktası | Hafta İçi Gündüz | Hafta İçi Akşam | Gece / Hafta Sonu / Tatil |
| --- | --- | --- | --- |
| Vardiya Şefliği | 1 | 1 | 1 |
| Güvenlik | 7 | 7 | 3 |
| Müracaat | 2 | 2 | 0 |
| Toplam | 10 | 10 | 4 |



Hafta sonu ve resmî tatillerde üç vardiyanın tamamı azaltılmış kadroyla çalışır. Müracaat noktası yalnızca hafta içi gündüz ve akşam vardiyalarında açıktır. Güvenlik talebi, önceki sürümde ayrı satırlar olan kapı ve kontrol odası taleplerinin toplamıdır; toplam kişi sayısı değişmemiştir, yalnızca noktanın kendisi birleşmiştir.

### 3.3.5 Kural Parametreleri

| Kural | Parametre | Değer |
| --- | --- | --- |
| H2 | asgari_dinlenme_saati | 16 |
| H3 | azami_ardisik_gece | 3 |
| H4 | azami_ardisik_calisma_gunu | 6 |
| H5 | azami_haftalik_saat | 45 |
| H6 | haftalik_asgari_izin_gunu | 1 |



Asgari dinlenme süresinin 16 saat olarak belirlenmesi, üçlü sekiz saatlik düzende iki çalışılan vardiya arasında en az iki boş vardiya bulunması gereksiniminin saat cinsinden karşılığıdır. Kuralın saat üzerinden yazılması, vardiya yapısı değiştiğinde yeniden tanımlanmasını gereksiz kılar (bkz. H2). Bu değer altında yalnızca ileri yönlü vardiya geçişleri mümkün kalır; gece, gündüz ve akşam sırası korunur, geri yönlü geçişler için araya en az bir izin günü girmesi gerekir.

### 3.3.6 Kadro Büyüklüğü Analizi

Talep matrisi, haftada 144 kişi-vardiyalık bir iş yükü üretmektedir: hafta içi beş gün için günde 24, hafta sonu iki gün için günde 12 kişi-vardiya. Sekiz saatlik vardiya süresiyle bu, haftalık 1.152 saate karşılık gelmektedir.

H5 ve H6 birlikte değerlendirildiğinde bir personelin haftada en fazla beş vardiya tutabildiği görülmektedir; altı vardiya 48 saat ederek haftalık tavanı aşmaktadır. Buradan, izin ve rapor payı hariç asgari 29 kişilik bir kadro gereksinimi çıkmaktadır.

Yetkinlik havuzları ayrı ayrı değerlendirildiğinde tablo aşağıdaki gibidir.

| Yetkinlik Havuzu | Haftalık Kişi-Vardiya | Teorik Asgari | İzin Payıyla |
| --- | --- | --- | --- |
| Vardiya Şefi | 21 | 5 | 7 |
| Müracaat Görevlisi | 20 | 4 | 6 |
| Güvenlik Görevi | 103 | 21 | 23 |
| Toplam | 144 | 29 | 36 |



Vardiya şefliği havuzu sistemin en kırılgan bileşenidir. Kesintisiz doldurulan tek bir görev noktası haftada 21 vardiya gerektirmekte; beş kişilik bir havuzda tek bir personelin izne ayrılması, kalan dört kişinin haftalık tavanı aşmadan bu yükü karşılayamaması nedeniyle kapatılamayan bir boşluk doğurmaktadır. Müracaat havuzunda aynı durum dört kişilik kadroda ortaya çıkmaktadır.

Bu analiz, bölüm 5.5'te tanımlanan fizibilite geri bildirimi işlevinin neden zorunlu kısıt yerine esnek hedef üzerine kurulduğunu göstermektedir. Kadro daraldığında doğru davranış çözümü reddetmek değil, açığın hangi gün, vardiya ve noktada oluştuğunu göstermektir.

# 4. Kural Kataloğu

## 4.1 Gösterim

Aşağıdaki gösterim bölüm 4.2 ve 4.3'te kullanılmaktadır.

```
P   : personel kümesi
D   : planlama dönemi günleri (ısıtma penceresi dahil zaman ekseni)
S   : vardiya tipleri kümesi
K   : yetkinlikler kümesi
N   : görev noktaları kümesi
x[p,d,s,n] ∈ {0,1} : p personeli d gününde s vardiyasında n noktasına atandı
y[p,d,s] = Σ_n x[p,d,s,n] : p personeli d gününde s vardiyasında görevli
sure[s]     : s vardiyasının süresi (saat)
gece[s]     : s vardiyası gece ise 1
hs[d]       : d günü hafta sonu veya resmî tatil ise 1
talep[d,s,n]: d gününde s vardiyasında n noktası için gereken personel
onkosul[n]  : n noktasının gerektirdiği yetkinlik (boş olabilir)
bina[n]     : n noktasının bağlı olduğu bina (tesis geneli ise boş)
musait[p,d,s] : p personeli d gününde s vardiyasına atanabiliyorsa 1
yetkin[p,k]  : p personeli k yetkinliğine sahipse 1
```

Yardımcı değişken y, nokta ayrımının önemsiz olduğu kurallarda gösterimi sadeleştirmek için tanımlanmıştır. Dinlenme, ardışıklık, saat tavanı ve adalet kuralları personelin hangi noktada görevlendirildiğinden bağımsız olduğu için y üzerinden yazılır; talep ve yetkinlik kuralları ise x üzerinden yazılır.

Isıtma penceresine düşen günler için x değişkenleri sabittir ve önceki yayınlanmış çizelgeden alınır (TD-5).

## 4.2 Zorunlu Kısıtlar

### H1 — Günde en fazla bir vardiya

Bir personel bir takvim gününde en fazla bir vardiyaya ve o vardiya içinde en fazla bir görev noktasına atanabilir. Kısıt, bütün vardiya tipleri ve bütün görev noktaları üzerinden birlikte yazılır; böylece aynı personelin aynı anda iki noktada sayılması yapısal olarak imkânsız hale gelir.

```
∀p, ∀d :  Σ_s Σ_n x[p,d,s,n] ≤ 1
```

Parametresizdir. Vardiyalar başlangıç gününe yazıldığından (TD-1) gece yarısını aşan vardiyalar bu kuralı bozmaz.

### H2 — Asgari dinlenme süresi

Ardışık iki atama arasındaki boşluk, tanımlı asgari dinlenme süresinden az olamaz. Kural, vardiya adına değil zaman bilgisine göre değerlendirilir.

```
Her (p, d, s, d', s') çifti için, s vardiyasının d günündeki bitiş zamanı
ile s' vardiyasının d' günündeki başlangıç zamanı arasındaki fark
asgari_dinlenme_saati değerinden küçükse:
y[p,d,s] + y[p,d',s'] ≤ 1
```

Parametre: asgari_dinlenme_saati (varsayılan 16; bkz. bölüm 3.3.5). Bu kural, gece vardiyasından çıkan personele ertesi sabah görev verilmesini engelleyen kuralın genel biçimidir; vardiya yapısı değiştiğinde yeniden yazılması gerekmez.

### H3 — Ardışık gece üst sınırı

Bir personel, üst üste tanımlı sayıdan fazla gece vardiyası tutamaz.

```
N = azami_ardisik_gece
∀p, ∀d :  Σ_{i=0..N} Σ_{s: gece[s]=1} y[p,d+i,s] ≤ N
```

Parametre: azami_ardisik_gece. Pencere, ısıtma penceresini de kapsayacak şekilde değerlendirilir.

### H4 — Ardışık çalışma günü üst sınırı

Bir personel, üst üste tanımlı sayıdan fazla gün çalışamaz.

```
M = azami_ardisik_gun
∀p, ∀d :  Σ_{i=0..M} Σ_s y[p,d+i,s] ≤ M
```

Parametre: azami_ardisik_gun.

### H5 — Kayan yedi günlük saat tavanı

Herhangi bir yedi günlük pencerede toplam çalışma saati tavanı aşamaz.

```
∀p, ∀d :  Σ_{i=0..6} Σ_s sure[s] · y[p,d+i,s] ≤ azami_haftalik_saat
```

Parametre: azami_haftalik_saat. Saatlerin güne yazılma biçimi TD-7'de tanımlanmıştır.

### H6 — Haftalık asgari izin günü

Herhangi bir yedi günlük pencerede en az bir tam gün çalışılmamalıdır.

```
∀p, ∀d :  Σ_{i=0..6} Σ_s y[p,d+i,s] ≤ 6
```

Parametresizdir. azami_ardisik_gun değeri 7'den küçük tanımlandığında bu kural H4 tarafından zaten sağlanır; yine de ayrı kural olarak tutulur, çünkü yasal dayanağı farklıdır ve H4 devre dışı bırakıldığında geçerliliğini korumalıdır.

### H7 — Müsaitlik

Personel, müsait olmadığı zaman aralığıyla kesişen bir vardiyaya atanamaz.

```
∀p, d, s :  y[p,d,s] ≤ musait[p,d,s]
```

musait değeri, müsaitlik kayıtlarının zaman aralıklarıyla vardiyanın zaman aralığının kesişimine bakılarak hesaplanır (TD-4). Personelin aktiflik tarih aralığı dışındaki günler de müsait olmayan gün olarak değerlendirilir.

### H8 — Ön koşul yetkinliği

Ön koşul yetkinliği vardiya tipine değil görev noktasına bağlıdır. Bir noktaya atanan personelin, o noktanın gerektirdiği yetkinliğe sahip olması zorunludur. Ön koşulu bulunmayan noktalara her personel atanabilir.

```
∀p, d, s, n, ∀k ∈ onkosul[n] :  x[p,d,s,n] ≤ yetkin[p,k]
```

Bu tanım, yetkinlik gereksinimini sayma yerine eşleme problemine dönüştürür. Yetkinliklerin örtüştüğü durumlarda — örneğin bir personelin iki farklı noktanın ön koşulunu birden taşıması — sayma tabanlı bir formülasyon aynı kişiyi iki gereksinim için birden sayabilir ve sahada karşılığı olmayan bir çizelge üretir. Nokta boyutu bu hatayı yapısal olarak ortadan kaldırır.

## 4.3 Esnek Hedefler

Esnek hedefler ihlal edildiğinde ceza puanı üretir. Her hedefin ağırlığı kullanıcı tarafından ayarlanabilir. Amaç fonksiyonu, ağırlıklı ceza toplamını en aza indirir.

### S1 — Talep karşılama

Talep karşılama zorunlu kısıt değil, baskın ağırlıklı esnek hedeftir. Bu tasarım kararı sayesinde personel fiziken yetersiz olduğunda sistem çözümü reddetmek yerine çizelgeyi üretir ve eksiğin nerede olduğunu gösterir.

```
Nokta bazında kapsama (alt sınır, esnek):
∀d, s, n :  Σ_p x[p,d,s,n] + eksik[d,s,n] ≥ talep[d,s,n],  eksik[d,s,n] ≥ 0
Nokta bazında kadro (üst sınır, zorunlu):
∀d, s, n :  Σ_p x[p,d,s,n] ≤ talep[d,s,n]
Ceza:  w1 · Σ_{d,s,n} eksik[d,s,n]
```

Talep sayısı üst sınır olarak zorunlu, alt sınır olarak esnektir. Personel yeterli olduğunda iki kısıt birlikte eşitliği zorlar; yetersiz olduğunda çözücü açığı eksik değişkenine yazar ve çizelgeyi yine de üretir. Fazla personel atanması ise her koşulda engellenir.

Ağırlık w1, diğer tüm ağırlıkların toplamından belirgin biçimde büyük seçilir; böylece çözücü hiçbir zaman başka bir hedefi iyileştirmek için kapsama açığı bırakmaz. Fizibilite geri bildirimi (bölüm 5.5) eksik değişkenlerinin sıfırdan büyük olduğu gün, vardiya ve nokta üçlülerini doğrudan bu formülasyondan okur.

### S2 — Gece adaleti

Kişi başına düşen gece vardiyası sayısının hedeften sapması cezalandırılır.

```
gece_sayisi[p] = Σ_{d ∈ dönem} Σ_{s: gece[s]=1} y[p,d,s]
hedef_gece = ( Σ_{d,s: gece[s]=1} talep[d,s] ) / |P|
sapma[p] ≥ gece_sayisi[p] − ⌊hedef_gece⌋
sapma[p] ≥ ⌈hedef_gece⌉ − gece_sayisi[p]
Ceza:  w2 · Σ_p sapma[p]
```

Sayım yalnızca planlama dönemini kapsar; ısıtma penceresi dahil edilmez (TD-6).

### S3 — Hafta sonu adaleti

Kişi başına düşen hafta sonu ve resmî tatil vardiyası sayısının hedeften sapması cezalandırılır. Formülasyon S2 ile aynıdır; gece[s] yerine hs[d] kullanılır (TD-3).

```
hs_sayisi[p] = Σ_{d: hs[d]=1} Σ_s y[p,d,s]
Ceza:  w3 · Σ_p sapma_hs[p]
```

### S4 — Toplam saat dengesi

Kişi başına toplam çalışma saatinin, o personele düşen adil paydan sapması cezalandırılır. Adil pay, dönemdeki toplam talep saatinin personel arasında haftalık hedef saatleri oranında bölüştürülmesiyle bulunur.

```
saat[p] = Σ_{d ∈ dönem} Σ_s sure[s] · y[p,d,s]
toplam_talep_saat = Σ_{d,s,n} sure[s] · talep[d,s,n]
pay[p] = ( hedef_saat[p] / Σ_q hedef_saat[q] ) · toplam_talep_saat
Ceza:  w4 · Σ_p |saat[p] − pay[p]|
```

Sözleşme tipleri farklı olan personel için haftalık hedef saat farklılaşabildiğinden, pay eşit bölüşüm değil hedef saatle orantılı bölüşümdür; kırk saatlik sözleşmeli bir personel, otuz saatlik sözleşmeli bir personelden orantılı olarak daha fazla pay alır.

Sapmanın kişisel sözleşme saatine değil bu paya göre hesaplanmasının nedeni, sözleşme saatinin ulaşılabilir bir hedef olmamasıdır. Haftalık saat tavanı ve asgari izin günü kuralları birlikte kişi başına azami vardiya sayısını sınırlar; kadro asgari gereksinimin üzerinde olduğunda hiçbir personel sözleşme saatine ulaşamaz. Bu durumda bütün sapmalar aynı yönde olur ve toplamları, çalışılan toplam saat talep tarafından sabitlendiği için dağılımdan bağımsız bir sabite dönüşür — hedef, ayırt edici olma özelliğini tamamen kaybeder. Paya göre hesaplanan sapma ise iki yönlü olabildiğinden dengesizliği gerçekten ölçer.

### S5 — Tercih karşılama

Onaylanmış her tercih için, tercihin ihlal edilip edilmediğini gösteren bir gösterge değişken tanımlanır.

```
Çalışmama tercihi (p, d):  ihlal[p,d] = Σ_s y[p,d,s]
Vardiya tipi tercihi (p, d, s*):  ihlal = Σ_{s ≠ s*} y[p,d,s]
Ceza:  w5 · Σ ihlal
```

Yalnızca yönetici tarafından onaylanmış tercihler modele dahil edilir. Reddedilen veya bekleyen tercihler ceza üretmez.

### S6 — Vardiya deseni tutarlılığı

Ardışık günlerde vardiya tipi değiştirmek ergonomik olarak istenmeyen bir durumdur ve cezalandırılır. Aynı gerekçeyle, ardışık günlerde farklı binalarda görevlendirilmek de ayrı bir ceza bileşeni üretir.

```
degisim[p,d] = 1  eğer p, d ve d+1 günlerinde çalışıyor ve
                  vardiya tipleri farklıysa
bina_degisim[p,d] = 1  eğer p, d ve d+1 günlerinde çalışıyor ve
                       atandığı noktaların binaları farklıysa
Ceza:  w6 · Σ degisim[p,d]  +  w6b · Σ bina_degisim[p,d]
```

Tesis geneli noktalar (bina bilgisi boş olanlar) bina değişimi hesabına girmez. Bölüm 3.3.3'te tanımlanan mevcut uygulama alanında bütün görev noktaları tesis geneli olduğundan, S6b bileşeni şu anda hiçbir ceza üretmemekte ve etkisiz kalmaktadır; kural, binaya bağlı nokta tanımlanması durumunda kendiliğinden devreye girmek üzere katalogda tutulmaktadır. Gösterim verisinde pasif bırakılması, amaç fonksiyonunu gereksiz terimden arındırır.

### S7 — İzole gün

Tek günlük çalışma blokları ve tek günlük izinler cezalandırılır; her ikisi de pratikte istenmeyen desenlerdir.

```
izole_calisma[p,d] = 1  eğer d günü çalışıyor, d−1 ve d+1 boşsa
izole_izin[p,d]    = 1  eğer d günü boş, d−1 ve d+1 doluysa
Ceza:  w7 · Σ ( izole_calisma + izole_izin )
```

### S8 — Değişim minimizasyonu

Mevcut bir çizelge üzerinden yeniden çözüm yapıldığında, önceki çizelgeden sapan her atama cezalandırılır. Bu hedef yalnızca yeniden çözüm işlemlerinde etkindir.

```
Ceza:  w8 · Σ_{p,d,s,n} | x[p,d,s,n] − x_onceki[p,d,s,n] |
```

Kilitli atamalar bu hedefin dışındadır; onlar sabit değer olarak modele girer ve değişmeleri mümkün değildir.

## 4.4 Amaç Fonksiyonu

```
min   w1·(Σ eksik + Σ eksikK)
    + w2·Σ sapma_gece  + w3·Σ sapma_hs
    + w4·Σ sapma_saat  + w5·Σ tercih_ihlal
    + w6·Σ degisim     + w7·Σ izole
    + w8·Σ onceki_sapma
```

Ağırlıkların tamamı kullanıcı tarafından ayarlanabilir. Sistem hangi hedefin daha öncelikli olduğuna kendisi karar vermez; bu tercihi parametre olarak alır ve sonucunu hesaplar.

# 5. Fonksiyonel Gereksinimler

Öncelikler şu şekilde tanımlanmıştır: Zorunlu (sistem bu gereksinim olmadan kabul edilemez), Yüksek (temel işlevin bir parçası), Orta (zaman kalırsa gerçekleştirilir).

## 5.1 Tanım Yönetimi

| Kimlik | Gereksinim | Öncelik |
| --- | --- | --- |
| FR-1.1 | Sistem, personel kayıtlarının oluşturulmasına, güncellenmesine ve pasifleştirilmesine imkân vermelidir. Personel kaydı sözleşme tipi, haftalık hedef saat ve aktiflik tarih aralığı içerir. | Zorunlu |
| FR-1.2 | Sistem, yetkinlik tanımlarının oluşturulmasına ve personele seviyesiz olarak atanmasına imkân vermelidir. | Zorunlu |
| FR-1.3 | Sistem, vardiya tiplerinin ad, başlangıç saati ve bitiş saatiyle tanımlanmasına imkân vermelidir. Süre, başlangıç ve bitiş saatinden hesaplanır. | Zorunlu |
| FR-1.4 | Sistem, vardiya tipi oluşturulurken gece_mi bayrağını TD-2'ye göre önermeli, kullanıcının bu öneriyi değiştirmesine imkân vermelidir. | Yüksek |
| FR-1.5 | Sistem, bina tanımlarının oluşturulmasına ve güncellenmesine imkân vermelidir. | Zorunlu |
| FR-1.6 | Sistem, görev noktalarının ad, bağlı olduğu bina ve ön koşul yetkinliğiyle tanımlanmasına imkân vermelidir. Bina alanı boş bırakıldığında nokta tesis geneli olarak değerlendirilir. | Zorunlu |
| FR-1.7 | Sistem, talep tanımının görev noktası, vardiya tipi ve gün tipi kırılımında yapılmasına ve tekil tarihler için istisna tanımlanmasına imkân vermelidir. | Zorunlu |
| FR-1.8 | Sistem, talep matrisini gün tipi ve vardiya tipi eksenlerinde tablo halinde göstermeli, hücrelerin doğrudan düzenlenmesine imkân vermelidir. | Yüksek |
| FR-1.9 | Sistem, tanımlı talep matrisinden haftalık toplam kişi-vardiya yükünü ve kural parametreleri altındaki asgari kadro büyüklüğünü hesaplayarak göstermelidir. | Orta |
| FR-1.10 | Sistem, resmî tatillerin takvimde işaretlenmesine imkân vermelidir. | Yüksek |
| FR-1.11 | Sistem, zorunlu kural parametrelerinin görüntülenmesine ve değiştirilmesine imkân vermelidir. | Zorunlu |
| FR-1.12 | Sistem, esnek hedef ağırlıklarının görüntülenmesine ve değiştirilmesine imkân vermelidir. | Zorunlu |
| FR-1.13 | Sistem, bir kuralın geçici olarak devre dışı bırakılmasına imkân vermelidir. | Orta |
| FR-1.14 | Sistem, gösterim amaçlı örnek veri seti üretebilmelidir. | Yüksek |



## 5.2 Müsaitlik Yönetimi

| Kimlik | Gereksinim | Öncelik |
| --- | --- | --- |
| FR-2.1 | Sistem, müsaitlik kayıtlarının personel, tarih aralığı, dilim ve tip bilgisiyle girilmesine imkân vermelidir. | Zorunlu |
| FR-2.2 | Sistem, müsaitlik diliminin tam gün, öğleden önce veya öğleden sonra olarak seçilmesine imkân vermelidir. | Zorunlu |
| FR-2.3 | Sistem, müsaitlik kayıtlarını dosya yoluyla toplu olarak içe aktarabilmelidir. | Yüksek |
| FR-2.4 | Sistem, bir müsaitlik kaydı girilirken ilgili günlerde kapsama açığı oluşacaksa kullanıcıyı uyarmalı; uyarı gün, vardiya ve eksik kişi sayısını içermelidir. | Yüksek |
| FR-2.5 | Sistem, müsaitlik takvimini aylık görünümde sunmalıdır. | Yüksek |
| FR-2.6 | Sistem, yayınlanmış bir çizelgeyi etkileyen müsaitlik değişikliğinde kullanıcıyı bilgilendirmeli ve yeniden çözüm önermelidir. | Yüksek |



## 5.3 Tercih Yönetimi

| Kimlik | Gereksinim | Öncelik |
| --- | --- | --- |
| FR-3.1 | Sistem, personelin belirli bir günde çalışmama tercihini kaydetmesine imkân vermelidir. | Yüksek |
| FR-3.2 | Sistem, personelin belirli bir vardiya tipine yönelik tercihini kaydetmesine imkân vermelidir. | Orta |
| FR-3.3 | Sistem, dönem bazında tercih son bildirim tarihi tanımlanmasına imkân vermeli ve bu tarihten sonra yeni tercih kabul etmemelidir. | Yüksek |
| FR-3.4 | Sistem, yöneticinin tercihleri onaylamasına veya gerekçeyle reddetmesine imkân vermelidir. | Yüksek |
| FR-3.5 | Sistem, yalnızca onaylanmış tercihleri çözücü modeline dahil etmelidir. | Zorunlu |
| FR-3.6 | Sistem, onaylanmış bir tercihin çizelgede karşılanıp karşılanmadığını onay durumundan ayrı bir bilgi olarak göstermelidir. | Yüksek |



## 5.4 Çizelge Üretimi

| Kimlik | Gereksinim | Öncelik |
| --- | --- | --- |
| FR-4.1 | Sistem, seçilen dönem için kısıt programlama modeli kullanarak çizelge üretmelidir. | Zorunlu |
| FR-4.2 | Sistem, planlama ufkunun kullanıcı tarafından seçilmesine imkân vermeli, varsayılan olarak dört haftalık dönem önermelidir. | Zorunlu |
| FR-4.3 | Sistem, bölüm 4.2'deki zorunlu kısıtların tamamını sağlayan çizelge üretmelidir. | Zorunlu |
| FR-4.4 | Sistem, bölüm 4.4'teki amaç fonksiyonunu en aza indiren çözümü aramalıdır. | Zorunlu |
| FR-4.5 | Sistem, önceki yayınlanmış çizelgenin son yedi gününü ısıtma penceresi olarak modele dahil etmelidir (TD-5). | Zorunlu |
| FR-4.6 | Sistem, çözüm için üst zaman limiti tanımlanmasına imkân vermeli; limit dolduğunda o ana kadar bulunan en iyi çözümü döndürmelidir. | Yüksek |
| FR-4.7 | Sistem, çözüm tamamlandığında çözüm süresini, çözüm durumunu ve toplam ceza puanını raporlamalıdır. | Zorunlu |
| FR-4.8 | Sistem, toplam ceza puanını esnek hedef bazında ayrıştırarak göstermelidir. | Yüksek |



## 5.5 Fizibilite Geri Bildirimi

| Kimlik | Gereksinim | Öncelik |
| --- | --- | --- |
| FR-5.1 | Sistem, çözüm başlatılmadan önce talep ve mevcut personel sayısını karşılaştıran ön kontrol yapmalı, karşılanamayacak gün ve vardiyaları listelemelidir. | Yüksek |
| FR-5.2 | Sistem, personel yetersizliği durumunda çözümü reddetmek yerine çizelgeyi üretmeli ve kapsama açıklarını göstermelidir. | Zorunlu |
| FR-5.3 | Sistem, kapsama açığını gün, vardiya tipi, gereken sayı, atanan sayı ve eksik sayı düzeyinde raporlamalıdır. | Zorunlu |
| FR-5.4 | Sistem, yetkinlik bazlı kapsama açıklarını toplam açıktan ayrı olarak göstermelidir. | Yüksek |
| FR-5.5 | Sistem, zorunlu kısıtların çelişmesi nedeniyle çözüm bulunamadığında bunu kapsama açığından ayırt edilebilir biçimde bildirmelidir. | Yüksek |



## 5.6 Manuel Düzenleme ve Doğrulama

| Kimlik | Gereksinim | Öncelik |
| --- | --- | --- |
| FR-6.1 | Sistem, taslak durumdaki bir çizelge üzerinde atamaların elle değiştirilmesine imkân vermelidir. | Zorunlu |
| FR-6.2 | Sistem, her manuel değişiklikten sonra tüm zorunlu kısıtları yeniden değerlendirmeli ve ihlal edilen kuralları listelemelidir. | Zorunlu |
| FR-6.3 | Sistem, ihlal bildiriminde kuralın kimliğini, ilgili personeli, tarihi ve ihlalin gerekçesini anlaşılır bir cümleyle vermelidir. | Zorunlu |
| FR-6.4 | Sistem, manuel değişikliğin esnek hedef cezalarına etkisini de göstermelidir. | Yüksek |
| FR-6.5 | Sistem, belirli atamaların kilitlenmesine imkân vermeli; kilitli atamalar yeniden çözümde değiştirilmemelidir. | Zorunlu |
| FR-6.6 | Manuel doğrulama, çözücü modeliyle aynı kural tanımından beslenmelidir. | Zorunlu |



## 5.7 Sürüm ve Yayın Yönetimi

| Kimlik | Gereksinim | Öncelik |
| --- | --- | --- |
| FR-7.1 | Sistem, bir dönem için birden fazla çizelge sürümü saklayabilmelidir. | Zorunlu |
| FR-7.2 | Sistem, çizelge sürümlerini taslak, çözüldü, yayınlandı ve arşiv durumlarında yönetmelidir (TD-8). | Zorunlu |
| FR-7.3 | Sistem, yayınlanmış bir sürümün doğrudan düzenlenmesini engellemeli; düzenleme talebinde kopyadan yeni bir taslak sürüm oluşturmalıdır. | Zorunlu |
| FR-7.4 | Sistem, yeniden çözümde önceki sürümden sapmayı cezalandırmalı ve değişen atama sayısını raporlamalıdır. | Zorunlu |
| FR-7.5 | Sistem, iki çizelge sürümünü yan yana karşılaştırarak farkları göstermelidir. | Orta |



## 5.8 Analiz ve Raporlama

| Kimlik | Gereksinim | Öncelik |
| --- | --- | --- |
| FR-8.1 | Sistem, dönem için kapsama oranını raporlamalıdır. | Zorunlu |
| FR-8.2 | Sistem, kişi başına gece, hafta sonu ve toplam saat sayılarını tablo halinde raporlamalıdır. | Zorunlu |
| FR-8.3 | Sistem, iş yükü dağılımını en yüklü ve en az yüklü personel arasındaki fark üzerinden ölçmelidir. | Yüksek |
| FR-8.4 | Sistem, onaylanmış tercihlerin karşılanma oranını raporlamalıdır. | Yüksek |
| FR-8.5 | Sistem, çizelgeyi CSV veya Excel formatında dışa aktarabilmelidir. | Zorunlu |
| FR-8.6 | Sistem, kural bazlı ihlal ve ceza dökümünü raporlamalıdır. | Yüksek |



## 5.9 Çalışan Paneli

| Kimlik | Gereksinim | Öncelik |
| --- | --- | --- |
| FR-9.1 | Sistem, personelin yalnızca kendi çizelgesini görüntülemesine imkân vermelidir. | Yüksek |
| FR-9.2 | Sistem, personele yalnızca yayınlanmış durumdaki çizelge sürümünü göstermelidir. | Zorunlu |
| FR-9.3 | Sistem, personelin çizelgesini aylık ve liste görünümünde sunmalı, sıradaki vardiyayı öne çıkarmalıdır. | Yüksek |
| FR-9.4 | Sistem, yeni yayınlanan sürümde önceki sürüme göre değişen günleri işaretlemelidir. | Yüksek |
| FR-9.5 | Sistem, personelin dönem içindeki gece, hafta sonu ve toplam saat sayısını ekip ortalamasıyla birlikte göstermelidir. | Orta |
| FR-9.6 | Sistem, personelin tercih bildirmesine ve bildirdiği tercihlerin durumunu görmesine imkân vermelidir. | Yüksek |



# 6. Kullanım Senaryoları

### KS-1 — Dönem çizelgesinin üretilmesi

Aktör: Vardiya Yöneticisi

Ön koşul: Personel, yetkinlik, vardiya tipi ve talep tanımları girilmiştir.

**Akış:**

- Yönetici yeni bir dönem oluşturur ve tarih aralığını belirler.

- Sistem ön kontrol yapar ve karşılanamayacak gün-vardiya çiftlerini listeler.

- Yönetici ağırlıkları ve zaman limitini gözden geçirir, çözümü başlatır.

- Sistem önceki dönemin son yedi gününü ısıtma penceresi olarak modele dahil eder ve çözümü üretir.

- Sistem çizelgeyi, çözüm süresini ve hedef bazlı ceza dökümünü gösterir.

- Yönetici sonucu inceler ve çizelgeyi yayınlar.

Sonuç: Dönem için yayınlanmış bir çizelge sürümü oluşur ve personele görünür hale gelir.

### KS-2 — Yeni izin bilgisi sonrası yeniden çözme

Aktör: Vardiya Yöneticisi

Ön koşul: Dönem için yayınlanmış bir çizelge sürümü mevcuttur.

**Akış:**

- Yönetici bir personel için müsaitlik kaydı girer.

- Sistem, ilgili günlerde kapsama açığı oluşup oluşmayacağını kontrol eder ve gerekiyorsa uyarır.

- Sistem, yayınlanmış çizelgenin etkilendiğini bildirir ve yeniden çözüm önerir.

- Sistem yayınlanmış sürümün kopyasından yeni bir taslak sürüm oluşturur.

- Yönetici korunmasını istediği atamaları kilitler ve yeniden çözümü başlatır.

- Sistem, önceki çizelgeden sapmayı cezalandırarak yeni çözümü üretir ve değişen atama sayısını raporlar.

- Yönetici değişiklikleri inceleyip yeni sürümü yayınlar.

Sonuç: Önceki sürüm arşiv durumuna geçer; personel panelinde yalnızca değişen günler işaretli olarak yeni çizelge görünür.

### KS-3 — Çizelgenin elle düzenlenmesi

Aktör: Vardiya Yöneticisi

Ön koşul: Taslak durumda bir çizelge sürümü mevcuttur.

**Akış:**

- Yönetici çizelge ızgarasında bir atamayı değiştirir.

- Sistem tüm zorunlu kısıtları yeniden değerlendirir.

- İhlal varsa sistem kuralın kimliğini, ilgili personeli, tarihi ve gerekçeyi bildirir.

- Sistem, değişikliğin esnek hedef cezalarına etkisini gösterir.

- Yönetici değişikliği geri alır veya kabul eder.

Sonuç: Çizelge güncellenir; ihlal içeren bir çizelgenin yayınlanması engellenir.

### KS-4 — Tercih bildirimi

Aktör: Personel

Ön koşul: Dönem tanımlanmış ve tercih son bildirim tarihi geçmemiştir.

**Akış:**

- Personel çalışan panelinde tercih formunu açar.

- Personel çalışmak istemediği günü seçer ve isteğe bağlı gerekçe girer.

- Sistem tercihi beklemede durumuyla kaydeder.

- Yönetici tercihi onaylar veya gerekçeyle reddeder.

- Onaylanan tercih bir sonraki çözümde esnek hedef olarak modele dahil edilir.

- Çözüm sonrası sistem, tercihin karşılanıp karşılanmadığını personele gösterir.

Sonuç: Tercih kayıt altına alınır; onay durumu ve karşılanma durumu ayrı ayrı izlenebilir.

# 7. Arayüz Gereksinimleri

## 7.1 Kullanıcı Arayüzleri

| Panel | Ekran | Temel İçerik |
| --- | --- | --- |
| Yönetici | Özet | Kapsama oranı, eksik hücre sayısı, toplam ceza, bekleyen tercih sayısı, yaklaşan müsaitlik kayıtları |
| Yönetici | Tanımlar | Personel, yetkinlik, vardiya tipi, talep matrisi, takvim, kural parametreleri, ağırlıklar |
| Yönetici | Müsaitlik | Aylık takvim, kayıt girişi, toplu içe aktarma, kapsama uyarısı |
| Yönetici | Tercihler | Bekleyen ve karara bağlanmış tercih listesi, onay ve red işlemleri |
| Yönetici | Çizelge | Personel × gün ızgarası, hücre düzenleme, ihlal göstergesi, kilitleme, günlük kapsama satırı, filtreler |
| Yönetici | Çözüm | Ufuk ve ağırlık seçimi, zaman limiti, çalıştırma, çözüm durumu ve ceza dökümü |
| Yönetici | Analiz | Kişi başına dağılım tabloları, denge ölçütleri, tercih karşılama, kural bazlı ihlal dökümü |
| Yönetici | Sürümler | Sürüm listesi, durum yönetimi, yayınlama, karşılaştırma |
| Çalışan | Vardiyalarım | Aylık ve liste görünümü, sıradaki vardiya, değişen günlerin işaretlenmesi |
| Çalışan | Dönem özetim | Gece, hafta sonu ve toplam saat sayıları, ekip ortalaması karşılaştırması |
| Çalışan | Tercihlerim | Tercih bildirimi formu, onay durumu ve karşılanma durumu |



## 7.2 Veri Değişim Formatları

**Müsaitlik içe aktarma (CSV):**

```
sicil, baslangic_tarihi, bitis_tarihi, dilim, tip
Dilim değerleri: TAM, OO (öğleden önce), OS (öğleden sonra)
```

**Çizelge dışa aktarma (CSV):**

```
sicil, ad, tarih, vardiya_tipi, gece_mi, hafta_sonu_mu, sure_saat
```

Dosya karakter kodlaması UTF-8 olmalı; tarih biçimi ISO 8601 (YYYY-AA-GG) kullanılmalıdır.

# 8. Fonksiyonel Olmayan Gereksinimler

| Kimlik | Kategori | Gereksinim |
| --- | --- | --- |
| NFR-1 | Performans | Kırk personel ve yirmi sekiz günlük referans örnek (varsayılan bir haftalık dönemden büyük, kasıtlı bir stres testi ölçeği) altmış saniyenin altında çözülmelidir. |
| NFR-2 | Performans | Manuel düzenleme sonrası kural doğrulaması bir saniyenin altında tamamlanmalıdır. |
| NFR-3 | Performans | Yeniden çözüm süresi ilk çözüm süresini aşmamalıdır. |
| NFR-4 | Performans | Çizelge ızgarası ve analiz raporları ek işlem gerektirmeden görüntülenebilmelidir. |
| NFR-5 | Kullanılabilirlik | Uyarı ve hata mesajları teknik terim içermemeli, operasyon diliyle ifade edilmelidir. |
| NFR-6 | Kullanılabilirlik | Ceza dökümü, çözücünün neden bu çizelgeyi seçtiğini kullanıcıya açıklayacak ayrıntıda olmalıdır. |
| NFR-7 | Kullanılabilirlik | Çalışan arayüzü mobil cihazlarda kullanılabilir olmalıdır. |
| NFR-8 | Doğruluk | Yayınlanan hiçbir çizelge zorunlu kısıt ihlali içermemelidir. Bu, otomatik testlerle doğrulanır. |
| NFR-9 | Doğruluk | Kişi başına düşen gece sayısı hedeften en fazla bir birim sapmalıdır. |
| NFR-10 | Sürdürülebilirlik | Yeni bir kural eklemek, kural tanımına bir kayıt eklemek ve iki yorumlayıcıyı genişletmek dışında değişiklik gerektirmemelidir. |
| NFR-11 | Sürdürülebilirlik | Vardiya yapısının değişmesi (3x8, 2x12 veya başka bir düzen) kod değişikliği gerektirmemelidir. |
| NFR-12 | Taşınabilirlik | Sistem gerçek kurum verisi olmadan, uygulama içinden üretilen örnek veriyle çalıştırılabilmelidir. |
| NFR-13 | İzlenebilirlik | Her atamanın çözücü tarafından mı yoksa manuel olarak mı oluşturulduğu kayıt altında tutulmalıdır. |



# 9. İzlenebilirlik Matrisi

Aşağıdaki tablo, proje tanım dokümanındaki hedefleri bu dokümandaki gereksinimlerle ve kabul kriterleriyle ilişkilendirir.

| Hedef | Gereksinimler | Kabul Kriteri |
| --- | --- | --- |
| Tanım Yönetimi | FR-1.1 – FR-1.14 | Tüm tanımlar arayüzden oluşturulabilir; örnek veri seti üretilebilir |
| Çizelge Üretimi | FR-4.1 – FR-4.8, H1–H8 | Referans örnek 60 saniyenin altında çözülür; zorunlu kısıt ihlali yoktur (NFR-1, NFR-8) |
| Fizibilite Geri Bildirimi | FR-2.4, FR-5.1 – FR-5.5, S1 | Çelişkili örnekte hangi gün ve vardiyada kaç kişi eksik kaldığı gösterilir |
| Manuel Müdahale | FR-6.1 – FR-6.6 | İhlal bildirimi bir saniyenin altında görüntülenir (NFR-2) |
| Değişim Odaklı Yeniden Çözme | FR-7.1 – FR-7.5, S8 | Yeniden çözümde değişen atama sayısı raporlanır |
| Yük Dengesi ve Adalet | S2, S3, S4, FR-8.2, FR-8.3 | Kişi başına gece sayısı hedeften en fazla bir sapar (NFR-9) |
| Tercih Yönetimi | FR-3.1 – FR-3.6, S5 | Onay durumu ve karşılanma durumu ayrı ayrı gösterilir |
| Analiz ve Raporlama | FR-8.1 – FR-8.6, FR-4.8 | Ceza dökümü hedef bazında ayrıştırılır |
| Çalışan Görünürlüğü | FR-9.1 – FR-9.6 | Yalnızca yayınlanmış sürüm görünür; değişen günler işaretlenir |



## 9.1 Kapsam Dışı Gereksinimler

Aşağıdaki işlevler bu sürümün kapsamı dışındadır ve gereksinim olarak tanımlanmamıştır: izin talebi ve onay iş akışı, bordro ve puantaj, vardiya takası, personel bildirimleri, mobil uygulama, kurum sistemlerine entegrasyon, eş zamanlı düzenleme, geçmiş dönemlerden devreden kümülatif adalet, çelişen zorunlu kısıtlarda otomatik çakışma teşhisi.
