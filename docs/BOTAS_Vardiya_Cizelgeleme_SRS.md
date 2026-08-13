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
| Ömer HARMANKAYA | 07.08.2026 | Çalışan paneli boşlukları kapatıldı: tercih kaydına çalışan notu ve ret gerekçesi alanları eklendi (FR-3.4), karşılanma durumu TD-12 olarak türetilmiş ve üç değerli biçimde tanımlandı (FR-3.6, FR-9.6), FR-9.4'ün karşılaştırma tabanı ve değişim türleri netleştirildi, FR-9.3'teki aylık görünüm dönem görünümüne çevrildi | 1.4 |
| Ömer HARMANKAYA | 07.08.2026 | S2 ve S3'ün hedefi bütün personel yerine uygun havuz (P_gece, P_hs) üzerinden hesaplanacak biçimde düzeltildi; yetkinliği gereği gece veya hafta sonu talebi bulunan hiçbir noktada çalışamayan personel paydaya dahil edildiğinde hedef ulaşılamaz hâle geliyor ve ayırt ediciliğini kaybediyordu | 1.5 |
| Ömer HARMANKAYA | 09.08.2026 | Arayüz turunun gereksinim etkileri işlendi: FR-4.2'nin varsayılanı bir haftaya çekildi ve otuz bir günlük azami dönem tanımlandı; kapsama açığı dışa aktarımı (FR-8.7) ve yazdırılabilir görünüm (FR-8.8) eklendi; arşivlenmiş sürümden taslak türetme (FR-7.6) eklendi; 7.2'deki çizelge dışa aktarma biçimi görev noktası sütunu, noktalı virgül ayracı ve bayt sırası imi ile güncellendi | 1.6 |
| Ömer HARMANKAYA | 09.08.2026 | Kimlik doğrulama ve yetkilendirme gereksinimleri eklendi (5.10, FR-10.1 – FR-10.10); üç rol tanımlandı; FR-9.1'in kapsamı, gösterilecek personelin yalnızca oturumdan belirlenmesini içerecek biçimde zorunlu seviyeye çekildi | 1.7 |
| Ömer HARMANKAYA | 09.08.2026 | Uygulama sırasında ortaya çıkan üç sınır tanımlandı: kullanıcı adlarının ASCII kümesiyle sınırlanması (FR-10.11), personel başına tek hesap (FR-10.6) ve kilit/devre dışı bildirimlerinin yalnızca doğru parolada gösterilmesi (FR-10.8) | 1.8 |
| Ömer HARMANKAYA | 11.08.2026 | S1'in üst sınırının çözüm ile manuel düzenlemede farklı bağlayıcılıkta olduğu 4.3'e yazıldı: çözücüde zorunlu, manuel düzenlemede cezasız uyarı; uyarının sürüm raporunda kalıcı olması istendi | 1.9 |
| Ömer HARMANKAYA | 11.08.2026 | Kapsama açığı dışa aktarma biçimi fazla kadro kayıtlarını da taşıyacak biçimde genişletildi (tür sütunu, kisi_sayisi); uygulamada karşılığı bulunmayan sözleşme tipi alanı 3.1 ve FR-1.1'den çıkarıldı | 1.10 |
| Ömer HARMANKAYA | 11.08.2026 | Talep kayıtlarının gün tipi başına ayrı satırlar hâlinde tutulduğu ve resmî tatil satırlarının zorunluluğu 3.3.4'e yazıldı | 1.11 |
| Ömer HARMANKAYA | 11.08.2026 | Çözüm işinin durdurulması tek yönlü iptal olmaktan çıkarıldı: durdurma anında bulunmuş çözüm kullanıcının kararına sunulur (FR-4.9, FR-4.10). Çalışan işin ekran değişiminden bağımsız izlenebilirliği (FR-4.11) ve durdurmanın yanıt süresi (NFR-14) tanımlandı | 1.12 |
| Ömer HARMANKAYA | 11.08.2026 | FR-4.9'a, karar noktasının yalnızca arama başlamış işlerde doğduğu yazıldı; henüz kuyrukta veya ön kontrolde olan bir işin durdurulması doğrudan iptaldir | 1.13 |
| Ömer HARMANKAYA | 12.08.2026 | Saatlik çalışma düzenine geçişin veri temeli tanımlandı: çalışma bloğu kavramı TD-13 olarak eklendi, talep tanımı zaman aralığı kaydına çevrildi (3.3.4, FR-1.7, FR-1.8), S1'in kapsama kısıtı saat eksenine taşındı, blok kataloğu kısıtları FR-1.3'e yazıldı, personel kaydına devir bakiyesi alanı eklendi (FR-1.1) | 1.14 |
| Ömer HARMANKAYA | 12.08.2026 | FR-5.1'e ön kontrol bulgularının çözümü engellemediği, FR-5.3'e kapsama açığının saat aralığı düzeyinde raporlandığı, FR-8.1'e kapsama oranının atamalardan hesaplandığı yazıldı; FR-5.6 (bulgu metinlerinde ad kullanımı) eklendi | 1.15 |
| Ömer HARMANKAYA | 13.08.2026 | Kural kataloğu saatlik düzene taşındı: H5 mutlak tavana dönüştü, H9 (günlük azami saat) ve H10 (yıllık fazla çalışma kotası) eklendi, S1'in üst sınırı esnek hâle getirildi, S2 ve S3 saat birimine geçti, S6 başlangıç saati kaymasıyla yeniden tanımlandı; TD-2 ve TD-7 yeniden yazıldı, TD-14 eklendi; blok kataloğu genişletildi (3.3.1), parametre tablosu (3.3.5) ve kadro analizi (3.3.6) saat tabanına taşındı; amaç fonksiyonu (4.4) yeniden yazıldı | 1.16 |
| Ömer HARMANKAYA | 13.08.2026 | S2 ve S3'ün hedefi tek ortalamadan kişiye özel adil paya çevrildi: erişilebilirliği kısıtlı havuzlar için tek hedef ulaşılamaz kalıyor ve o havuz kalıcı olarak sapmalı görünüyordu | 1.17 |



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
| Personel | Ad, sicil, haftalık hedef saat, aktiflik başlangıç ve bitiş tarihi |
| Yetkinlik | Ad, açıklama |
| Personel-Yetkinlik | Personel, yetkinlik (seviyesiz çoktan-çoğa ilişki) |
| Vardiya Tipi | Ad, başlangıç saati, bitiş saati, süre (saat), gece_mi bayrağı |
| Bina | Ad, açıklama |
| Görev Noktası | Ad, bağlı olduğu bina (boş ise tesis geneli), ön koşul yetkinliği (boş olabilir), aktiflik |
| Gün Tipi | Hafta içi, hafta sonu, resmî tatil |
| Talep | Gün tipi veya tekil tarih, vardiya tipi, görev noktası, gereken personel sayısı |
| Müsaitlik Kaydı | Personel, başlangıç tarihi, bitiş tarihi, dilim (tam gün / öğleden önce / öğleden sonra), tip (yıllık izin, rapor, eğitim, mazeret) |
| Tercih | Personel, tarih veya tarih aralığı, tip (çalışmama, vardiya tipi tercihi), durum (beklemede, onaylandı, reddedildi), çalışanın isteğe bağlı notu, yöneticinin ret gerekçesi |
| Kural | Kimlik, tip (zorunlu / esnek), parametreler, ağırlık (esnekse), aktiflik |
| Dönem | Başlangıç tarihi, bitiş tarihi, tercih son bildirim tarihi |
| Çizelge Sürümü | Dönem, sürüm numarası, durum, oluşturma zamanı, çözüm süresi, ceza dökümü |
| Atama | Çizelge sürümü, personel, tarih, vardiya tipi, görev noktası, kilitli_mi bayrağı, kaynak (çözücü / manuel) |



## 3.2 Temel Tanımlar ve Sayma Kuralları

Bu bölümdeki tanımlar sistemin tamamı için bağlayıcıdır. Bir kuralın nasıl değerlendirileceği, bir metriğin nasıl sayılacağı ve arayüzün neyi göstereceği bu tanımlara dayanır.

### TD-1 — Vardiyanın güne ilişkilendirilmesi

Bir vardiya, başladığı takvim gününe ilişkilendirilir. Gece yarısını aşan vardiyalar da başlangıç gününe yazılır. Bu kural atama, sayma, raporlama ve arayüz gösteriminin tamamında geçerlidir.

### TD-2 — Gece çalışması: bayrak ve saat

Gece çalışması iki ayrı soruya karşılık gelir ve sistem ikisini ayrı ayrı yanıtlar.

**"Bu blok bir gece nöbeti midir?"** — ikili bir sorudur ve ergonomik bir eşiğe dayanır. Yanıtı çalışma bloğu üzerindeki `gece_mi` bayrağıdır. Bayrak **hesaplanan değil tanımlanan** bir alandır. Yeni bir blok oluşturulurken, bloğun zaman aralığının 20:00–06:00 aralığıyla kesişimi dört saat veya daha fazlaysa bayrak otomatik olarak önerilir; nihai değeri kullanıcı belirler ve öneri kuralı **tanımlı bir değeri asla ezmez**. H3 (ardışık gece sınırı) bu bayrağı kullanır.

**"Bu kişi ne kadar gece saati taşıdı?"** — sürekli bir ölçüdür ve adalet hesabına girer. Yanıtı hesaplanır: bir bloğun gece saati, bloğun 20:00–06:00 aralığıyla kesişiminin uzunluğudur. S2 (gece adaleti) bu ölçüyü kullanır.

Ayrım, blokların farklı uzunluklarda tanımlanabilmesinin sonucudur. On bir saatlik bir gece bloğu ile sekiz saatlik bir gece bloğunu adalet hesabında aynı saymak, uzun bloğu alan personelin yükünü görünmez kılar. Buna karşılık ardışık gece sınırı bir sayım kuralıdır ve saat üzerinden yazılamaz.

İki tanım çelişmez; farklı sorulara yanıt verirler. Bayrağın hesaplanan değere dönüştürülmesi denenmemelidir: öneri kuralının tanımlı değeri ezmesi bir kez yaşanmış ve K3 kabul kriterinin kalmasının iki nedeninden biri olmuştur.

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

### TD-6 — Ölçüm ufukları

Dönem öncesi birikimin hesaba katılması iki ayrı ufuk gerektirir ve bunlar birbirinin yerine geçmez.

**Yasal ufuk (H10).** Kota hesabı, ısıtma penceresini (TD-5) ve personel kaydındaki devir bakiyesini kapsar. Kapsamaması hâlinde dönem sınırında bölünen takvim haftası eksik ölçülür ve kota sessizce aşılır.

**Adalet ufku (S2, S3, S4).** Sayaçlar, dönemin başlangıcından geriye doğru `adalet_ufku_gun` (varsayılan 90) günlük kayan bir pencereyi kapsar. Pencere içindeki yayınlanmış sürümlerin atamaları, planlama dönemindeki atamalarla birlikte sayılır.

Ufkun "son N dönem" olarak tanımlanmaması bilinçlidir: dönem uzunluğu değişkendir (bir hafta ile bir ay arasında) ve aynı sayı farklı kurulumlarda farklı uzunlukta pencereler üretirdi. "Kota yılının başından bugüne" tanımı ise ufku ocak ayında sıfırlayıp aralıkta on iki aya çıkarır; yıl başında ağır gece yükü alan bir personelin bu yükü şubatta hiç görünmez.

**Birikim türetilir, saklanmaz.** İki ufkun de kaynağı yayınlanmış sürümlerin atamalarıdır; ayrı bir sayaç tablosunda tutulmaz. Saklanan sayaç, bir dönem yeniden çözüldüğünde veya bir sürüm arşive alındığında bayatlar. Tek istisna personel kaydındaki devir bakiyesidir: sistemin kota yılının başından beri her şeyi bilmediği durumu karşılar ve türetilen değere eklenir.

### TD-7 — Haftalık saat penceresi

Haftalık mutlak saat tavanı (H5), takvim haftası yerine kayan yedi günlük pencere üzerinde değerlendirilir. Bir bloğun süresi tamamıyla başlangıç gününe yazılır (TD-1). Bunun sonucu olarak, pencerenin son gününde başlayan bir bloğun ertesi güne taşan saatleri de o pencereye sayılır. Bu, bilinçli olarak kabul edilmiş bir yaklaşıklıktır; alternatifi blok süresini günlere bölmektir ve modeli gereksiz karmaşıklaştırır.

Yıllık fazla çalışma kotası (H10) bu pencereyi **kullanamaz**; gerekçesi TD-14'te yazılıdır.

### TD-14 — İki hafta kavramı bir arada yaşar

Sistem iki farklı "hafta" tanımı taşır ve bunlar birbirinin yerine geçmez.

| | Kapsam | Kullanan |
| --- | --- | --- |
| Kayan yedi günlük pencere | herhangi yedi ardışık gün | H4, H5, H6 |
| Takvim haftası (pazartesi–pazar) | ayrık, örtüşmeyen haftalar | H10 |

Dinlenme kuralları kayan olmak zorundadır: takvim haftasına dayanan bir dinlenme kuralı, pazar–pazartesi sınırında yan yana iki yoğun haftayı serbest bırakır ve kişi on dört günün on ikisinde çalışabilir.

Fazla çalışma kotası ise ayrık pencere gerektirir. Kota, "haftalık eşiğin üstünde çalışılan saatlerin yıllık toplamı" olarak tanımlıdır ve bir toplam ancak örtüşmeyen pencerelerde anlamlıdır. Kayan pencerede aynı saat yedi ayrı pencereye girer ve toplam yedi katına çıkar.

İki kavramın tek bir yardımcıda birleştirilmemesi bilinçlidir; birleştirildiklerinde hangi kuralın hangi pencereyi kullandığı çağrı yerine bakılarak anlaşılır hâle gelir.

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

### TD-12 — Tercihin karşılanma durumu

Bir tercihin karşılanıp karşılanmadığı, onay durumundan ayrı bir bilgidir (FR-3.6) ve saklanmaz; okuma anında yayınlanmış çizelgeden türetilir. Saklanması hâlinde çizelge yeniden çözüldüğünde değer bayatlar ve iki kaynak arasında tutarsızlık doğar.

Türetme yalnızca onaylanmış tercihler için yapılır ve tercihin tipine göre değişir. Çalışmama tercihi, ilgili günde o personele hiçbir atama yapılmamışsa karşılanmış sayılır. Vardiya tipi tercihi ise ilgili günde atama bulunması ve atanan vardiya tipinin istenen tiple aynı olması hâlinde karşılanmış sayılır.

Değer ikili değil üç durumludur. Dönem için yayınlanmış bir çizelge sürümü henüz yoksa sonuç "karşılanmadı" değil "henüz belirsiz"dir; bu ayrım kullanıcı arayüzünde de korunmalıdır, aksi hâlde çizelge üretilmeden önce bütün tercihler reddedilmiş gibi görünür.

### TD-13 — Çalışma bloğu

Bir personelin bir takvim günündeki çalışması **en fazla bir bloktur** ve blok kesintisizdir. Gün içinde bölünmüş çalışma — dört saat çalışıp ara verip aynı gün beş saat daha çalışmak — tanımlı değildir.

Bu kuralın sonucu olarak bir kişi-gün, `(başlangıç saati, süre)` çiftiyle tam olarak tanımlanır. Sistem bu nedenle çalışma zamanını sürekli bir karar değişkeni olarak değil, önceden tanımlanmış blokların seçimi olarak modeller: karar değişkeni `x[personel, gün, blok, nokta]` biçimini korur. Süre ve başlangıç saatinin ayrı tamsayı değişkenler olduğu sürekli zaman modeli, tek blok kuralı altında aynı çözüm kümesini üretir; karşılığında arama uzayını, doğrulayıcıyı ve manuel düzenleme yüzeyini karmaşıklaştırdığı için tercih edilmemiştir.

Blok, önceki sürümlerdeki "vardiya tipi" kavramının genelleştirilmiş hâlidir ve aynı tanım tablosunda tutulur. Fark, kataloğun sabit üç satırla sınırlı olmaması ve blokların farklı uzunluklarda tanımlanabilmesidir. Veritabanı alan adlarında `vardiya_tipi` ifadesi geriye dönük uyumluluk için korunur.

## 3.3 Uygulama Alanı: Güvenlik Personeli

Bu bölüm, bölüm 3.1 ve 3.2'de tanımlanan yapının ilk uygulama alanına ait somut değerlerini içerir. Buradaki hiçbir değer koda gömülü değildir; tamamı bölüm 5.1'deki tanım yönetimi gereksinimleri aracılığıyla düzenlenebilen veridir. Değerler mevcut işleyişten alınmış varsayımlara dayanmakta olup mentör görüşmesinde teyit edilecektir.

Planlama dönemi varsayılan olarak bir haftadır; yönetici bunu istediği bir uzunluğa çıkarabilir. Bu bir kısıt değil bir başlangıç değeridir — sistem daha uzun dönemleri de destekler ve NFR-1'in kırk personel/yirmi sekiz gün ölçeğindeki performans hedefi bu daha büyük dönemler için hâlâ geçerlidir (bkz. 3.3.6).

### 3.3.1 Çalışma Blokları

| Blok | Saat Aralığı | Süre | gece_mi |
| --- | --- | --- | --- |
| Gece | 00.00 – 08.00 | 8 saat | Evet |
| Gündüz | 08.00 – 16.00 | 8 saat | Hayır |
| Akşam | 16.00 – 24.00 | 8 saat | Hayır |
| Uzun gece | 20.00 – 08.00 | 12 saat | Evet |
| Uzun gündüz | 08.00 – 20.00 | 12 saat | Hayır |
| Erken uzun | 06.00 – 16.00 | 10 saat | Hayır |
| Geç uzun | 14.00 – 24.00 | 10 saat | Hayır |



İlk üç blok mevcut işleyişteki üçlü sekiz saatlik düzenin karşılığıdır; kalan dördü on ve on iki saatlik seçeneklerdir. On iki saatlik bloklar haftalık fazla çalışma eşiğini gerçekten aşabildiği için kotanın (H10) işlediğini gösterebilen tek yapıdır: yalnızca sekiz saatlik bloklarla haftada altı gün çalışan bir personel 48 saate ulaşır ve eşiği ancak üç saat aşar.

Katalog kullanıcı tarafından tanımlanan bir listedir (FR-1.3) ve bu tablo bir başlangıç hâlidir; gerçek işleyişteki saatler öğrenildiğinde satırlar değiştirilir. Değişiklik veridir, kod değildir. Katalog kullanıcı tarafından tanımlanan bir listedir (FR-1.3): farklı başlangıç saatleri ve farklı uzunluklar eklenebilir. Bloklar parametrik olarak üretilmez — her başlangıç saatinin her süreyle çarpımı yüzlerce satır eder ve NFR-1'deki çözüm süresi hedefini tehdit eder; gerçek bir tesisin kullandığı blok sayısı ise sınırlıdır.



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

Talep, bir çalışma bloğuna değil bir **zaman aralığına** bağlanır. Bir talep kaydı `(görev noktası, gün tipi, başlangıç, bitiş, gereken sayı)` biçimindedir ve "bu noktada, bu saatler arasında şu kadar kişi bulunsun" anlamına gelir.

| Görev Noktası | Gün Tipi | Aralık | Gereken |
| --- | --- | --- | --- |
| Vardiya Şefliği | Hafta içi | 00.00 – 24.00 | 1 |
| Vardiya Şefliği | Hafta sonu / tatil | 00.00 – 24.00 | 1 |
| Güvenlik | Hafta içi | 08.00 – 24.00 | 7 |
| Güvenlik | Hafta içi | 00.00 – 08.00 | 3 |
| Güvenlik | Hafta sonu / tatil | 00.00 – 24.00 | 3 |
| Müracaat | Hafta içi | 08.00 – 24.00 | 2 |



Bu tablo, önceki sürümdeki vardiya tipi eksenli matrisin birebir karşılığıdır: hafta içi gündüz ve akşam vardiyalarındaki 7 kişilik güvenlik talebi tek bir 08.00–24.00 aralığına, gece vardiyasındaki 3 kişilik talep 00.00–08.00 aralığına karşılık gelir. Toplam iş yükü değişmemiştir.

Talebin bloktan ayrılmasının nedeni, kataloğun genişlemesiyle blok ekseninin hem anlamını hem kullanılabilirliğini kaybetmesidir. Yirmi bloklu bir katalogda "06.00–14.00 bloğunda yedi kişi" ifadesi kullanıcının söylemek istediği şey değildir; söylemek istediği "sabah sekizden akşam on ikiye kadar yedi kişi bulunsun"dur. Hangi blokların bu aralığı hangi bileşimle kapatacağı çözücünün kararıdır.

Kapsama, aralık kaydından türetilen saat ekseninde değerlendirilir (bölüm 4.3, S1). Açılım tek bir yerde yapılır; talep ekranı, ön kontrol, çözücü, analiz ve kapsama açığı raporlaması aynı açılımı kullanır.

Talep kayıtları gün tipi başına ayrı tutulur: hafta içi, hafta sonu ve resmî tatil için ayrı satırlar bulunur. Resmî tatil satırlarının eksik olması, o gün için hiçbir satır bulunamamasına ve talebin sessizce sıfıra düşmesine yol açar; talep sıfır olduğunda kapsama açığı da doğmayacağı için durum hiçbir raporda görünmez. Bu nedenle resmî tatil satırları, tatil tanımı yapılabilen her kurulumda bulunmak zorundadır. Müracaat noktası yalnızca hafta içi gündüz saatlerinde açıktır.

### 3.3.5 Kural Parametreleri

| Kural | Parametre | Değer |
| --- | --- | --- |
| H2 | asgari_dinlenme_saati | 16 |
| H3 | azami_ardisik_gece | 3 |
| H4 | azami_ardisik_calisma_gunu | 6 |
| H5 | haftalik_mutlak_tavan | 66 |
| H6 | haftalik_asgari_izin_gunu | 1 |
| H9 | azami_gunluk_saat | 11 |
| H10 | fazla_calisma_esigi | 45 |
| H10 | yillik_fazla_kotasi | 270 |
| S6 | desen_toleransi_saat | 2 |
| S2, S3, S4 | adalet_ufku_gun | 90 |



Haftalık mutlak tavanın 66 saat olması, günlük azami on bir saat ile haftada en az bir izin gününün (H6) zaten ima ettiği üst sınırdır: altı çalışma günü × on bir saat. Değer bu nedenle tek başına ek bir kısıt getirmez; daha sıkı bir tavan istendiğinde parametre değiştirilir, kural yeniden yazılmaz. Kırk beş saat artık bir tavan değil, fazla çalışmanın başladığı eşiktir (H10).

Asgari dinlenme süresinin 16 saat olarak belirlenmesi, üçlü sekiz saatlik düzende iki çalışılan vardiya arasında en az iki boş vardiya bulunması gereksiniminin saat cinsinden karşılığıdır. Kuralın saat üzerinden yazılması, vardiya yapısı değiştiğinde yeniden tanımlanmasını gereksiz kılar (bkz. H2). Bu değer altında yalnızca ileri yönlü vardiya geçişleri mümkün kalır; gece, gündüz ve akşam sırası korunur, geri yönlü geçişler için araya en az bir izin günü girmesi gerekir.

### 3.3.6 Kadro Büyüklüğü Analizi

Talep, haftada **1.152 kişi-saatlik** bir iş yükü üretmektedir: hafta içi beş gün için günde 192, hafta sonu iki gün için günde 96 kişi-saat. Sekiz saatlik blokların kullanıldığı bir katalogda bu 144 kişi-vardiyaya karşılık gelir, fakat asıl ölçü saattir; katalog karışık uzunluklu olduğunda vardiya sayısı kataloğun bileşimine göre değişir, saat yükü değişmez.

Kadro gereksinimi fazla çalışma eşiği üzerinden hesaplanır: 1.152 saat / 45 saat ≈ 26 kişi. H6 (haftada en az bir izin günü) ile birlikte bir personel haftada en çok altı gün çalışabilir; on bir saatlik günlük tavan (H9) teorik olarak 66 saate izin verse de bu saatlerin tamamı fazla çalışma sayılır ve yıllık kotayı hızla tüketir. Sürdürülebilir planlama eşiğin altında kalmayı gerektirir. İzin ve rapor payı hariç asgari **26 kişilik** bir kadro gereksinimi çıkmaktadır; payla birlikte 29.

**Kadronun asgarinin belirgin biçimde üzerinde olması, adalet hedeflerini dar bir banda sıkıştırır.** Kırk dört kişilik bir kadroda kişi başına haftalık yük 26 saate düşer ve hiç kimse fazla çalışma eşiğine yaklaşmaz; H10 hiçbir zaman tetiklenmez, S4 dar bir aralıkta çalışır. Gösterim verisi bu nedenle kadroyu talebe göre boyutlandırmalıdır — aksi hâlde kuralların işlediği gösterilemez.

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

### H5 — Kayan yedi günlük mutlak tavan

Herhangi bir yedi günlük pencerede toplam çalışma saati mutlak tavanı aşamaz.

```
∀p, ∀d :  Σ_{i=0..6} Σ_b sure[b] · y[p,d+i,b] ≤ haftalik_mutlak_tavan
```

Parametre: haftalik_mutlak_tavan (varsayılan 66). Saatlerin güne yazılma biçimi TD-7'de tanımlanmıştır.

Bu kural önceki sürümlerde kırk beş saatlik bir tavandı. Kırk beş saat artık bir tavan değil, fazla çalışmanın başladığı **eşiktir** ve H10'un parametresidir: haftalık kırk beş saatin üzerinde çalışmak yasak değildir, yıllık kotaya yazılır. H5 ise dinlenme amaçlı, aşılamayan üst sınırı korur.

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

### H9 — Günlük azami çalışma süresi

Bir personelin bir takvim günündeki çalışma süresi günlük tavanı aşamaz.

```
∀p, ∀d :  Σ_b sure[b] · y[p,d,b] ≤ azami_gunluk_saat
```

Parametre: azami_gunluk_saat (varsayılan 11).

H1 bir günde en fazla bir blok verdiğinden bu kural pratikte "katalogdaki hiçbir blok günlük tavanı aşamaz" demeye gelir ve aynı sınır blok tanımlanırken de uygulanır (FR-1.3) — geçersiz veriyi girişte durdurmak, dakikalar süren bir çözümün sonunda keşfetmekten ucuzdur. Kural yine de ayrı yazılır: yasal dayanağı H1'den bağımsızdır ve H1'in gelecekte gevşetilmesi hâlinde tek başına geçerliliğini korumalıdır. Gerekçe H6'nın H4 karşısındaki durumuyla aynıdır.

Blok kataloğu kısıtı ile bu kural aynı parametreyi okur; iki ayrı değer tanımlanmaz.

### H10 — Yıllık fazla çalışma kotası

Haftalık eşiğin üzerinde çalışılan saatlerin kota yılı içindeki toplamı, yıllık kotayı aşamaz.

```
W       : dönemin dokunduğu takvim haftaları (pazartesi–pazar, TD-14)
saat[p,w] = Σ_{d ∈ w} Σ_b sure[b] · y[p,d,b]
fazla[p,w] ≥ saat[p,w] − fazla_calisma_esigi
fazla[p,w] ≥ 0
∀p :  devir[p] + Σ_{w ∈ W} fazla[p,w] ≤ yillik_fazla_kotasi
```

Parametreler: fazla_calisma_esigi (varsayılan 45), yillik_fazla_kotasi (varsayılan 270).

`devir[p]`, personelin içinde bulunulan kota yılında bu dönemden önce biriktirdiği fazla çalışma saatidir. Kaynağı iki parçalıdır: sistemin bildiği yayınlanmış sürümlerden türetilen toplam ile personel kaydındaki devir alanı. İkincisi, sistemin kota yılının başından beri her şeyi bilmediği durumu karşılar; türetilen değerin yerine geçmez, ona eklenir.

**Takvim haftası dönem sınırını aştığında**, haftanın dönem dışında kalan günleri sabit girdi olarak hesaba katılır: ısıtma penceresinden (TD-5) veya yayınlanmış sürümlerden okunur, ikisi de yoksa sıfır sayılır. Hesaba katılmaması hâlinde dönem sınırındaki hafta eksik ölçülür ve kota sessizce aşılır — kuralın hiç bulunmamasıyla aynı sonucu verir.

**Kural zorunludur ve modeli çözülemez yapmaz.** Yalnızca fazla çalışmayı sınırlar, çalışmayı değil: kotası dolmuş bir personel haftalık eşiğe kadar çalışmaya devam eder, yalnızca üstüne çıkamaz. `fazla[p,w] = 0` her zaman uygulanabilir bir değer olduğundan kısıt tek başına çelişki üretmez. Tek istisna `devir[p]`in kotayı zaten aşmış olmasıdır; bu bir veri hatasıdır ve ön kontrolde bildirilir (FR-5.1), çözüm anında değil.

## 4.3 Esnek Hedefler

Esnek hedefler ihlal edildiğinde ceza puanı üretir. Her hedefin ağırlığı kullanıcı tarafından ayarlanabilir. Amaç fonksiyonu, ağırlıklı ceza toplamını en aza indirir.

### S1 — Talep karşılama

Talep karşılama zorunlu kısıt değil, baskın ağırlıklı esnek hedeftir. Bu tasarım kararı sayesinde personel fiziken yetersiz olduğunda sistem çözümü reddetmek yerine çizelgeyi üretir ve eksiğin nerede olduğunu gösterir.

```
T(d)   : d gününün saat dilimleri
b ∋ t  : b bloğu t saatini kapsıyor
talep[d,t,n] : d gününde t saatinde n noktası için gereken personel
               (aralık kayıtlarından açılarak elde edilir, 3.3.4)

Saat bazında kapsama (alt sınır, esnek):
∀d, t, n :  Σ_p Σ_{b ∋ t} x[p,d,b,n] + eksik[d,t,n] ≥ talep[d,t,n],  eksik ≥ 0
Saat bazında kadro (üst sınır, esnek):
∀d, t, n :  Σ_p Σ_{b ∋ t} x[p,d,b,n] − fazla[d,t,n] ≤ talep[d,t,n],  fazla ≥ 0
Ceza:  w1 · Σ eksik[d,t,n]  +  w1f · Σ fazla[d,t,n]        (w1f ≪ w1)
```

**Üst sınır da esnektir.** Önceki sürümde talep sayısı aşılamayan bir tavandı. Karışık uzunluklu bir katalogda bu, modeli çözülemez hâle getirebilir: blok sınırları talep aralıklarının sınırlarıyla hizalanmadığında bir saatte fazla kadro oluşması yapısal olarak kaçınılmazdır. Örneğin 08.00–16.00 arasında dört kişi isteyen bir talep, on saatlik bir blokla kapatıldığında 16.00–18.00 saatlerinde de kadro üretir. Bu çözücünün tercihi değil, kataloğun sonucudur.

Fazla kadro gerçek bir maliyettir — boşa geçen kişi-saat — fakat açık kadar ağır değildir. Cezalandırılmazsa çözücü kayıtsız kalır ve gereksiz fazla üretir; zorunlu tutulursa hizalanmayan taleplerde çözüm hiç bulunamaz. Küçük ağırlıklı ceza ikisinin arasındadır.

Bu, çözücü tarafının davranışıdır. Manuel düzenlemede fazla kadro ceza üretmez (bölüm 4.3'ün sonundaki not): vardiya yöneticisi bilinçli olarak talebin üzerine çıkabilir ve sistem bunu bir hata gibi göstermez. İki tarafın farklı davranması bilinçlidir; çözücü kendi ürettiği fazlayı en aza indirmeye çalışır, kullanıcının bilerek yazdığını sorgulamaz.

Kısıt saat ekseninde yazılır çünkü talep bir bloğa değil bir zaman aralığına bağlıdır (3.3.4, TD-13). Bir personel bir saatte, o saati kapsayan bloğa atanmışsa sayılır; blokların uzunlukları farklı olabildiğinden aynı saati farklı bloklardan gelen personel birlikte doldurabilir.

Ceza saat başına değil, açığın süresiyle orantılı olarak birikir: iki saat boyunca bir kişi eksik kalmak, bir saat boyunca iki kişi eksik kalmakla aynı cezayı üretir. Bu bilinçlidir — ikisi de aynı miktarda karşılanmamış kişi-saattir.

Raporlamada ardışık ve eşit büyüklükteki saat açıkları tek bir aralık kaydı olarak birleştirilir; kullanıcıya saat saat liste değil, "02.06.2026, 00.00–08.00, Vardiya Şefliği: 1 kişi eksik" biçiminde aralık gösterilir.

Talep sayısı üst sınır olarak zorunlu, alt sınır olarak esnektir. Personel yeterli olduğunda iki kısıt birlikte eşitliği zorlar; yetersiz olduğunda çözücü açığı eksik değişkenine yazar ve çizelgeyi yine de üretir.

Üst sınırın bağlayıcılığı çözüm ile manuel düzenlemede farklı işler. Çözücü fazla personel atanmasını her koşulda engeller; üretilen hiçbir çizelgede talepten fazla kadro bulunmaz. Manuel düzenlemede ise vardiya yöneticisinin bir noktaya talebin üzerinde personel yazması engellenmez, uyarıyla bildirilir — devir, eğitim veya geçici takviye gibi durumlarda bu bilinçli bir tercih olabilir ve sistemin karar veren kişinin yerine geçmemesi ilkesi burada da geçerlidir (Proje Tanım Dokümanı bölüm 2). Fazla kadro bir ceza üretmez: amaç fonksiyonunda karşılığı olan bir terim yoktur ve uydurulacak bir sayı, aynı çizelge için çözücü ile doğrulayıcının farklı toplam raporlamasına yol açardı.

Bu tercihin bedeli, yayımlanmış bir çizelgenin talebin üzerinde kadro taşıyabilmesidir. Bu nedenle uyarı yalnızca düzenleme anında gösterilmekle kalmaz; sürümün raporunda da görünür kalır.

Ağırlık w1, diğer tüm ağırlıkların toplamından belirgin biçimde büyük seçilir; böylece çözücü hiçbir zaman başka bir hedefi iyileştirmek için kapsama açığı bırakmaz. Fizibilite geri bildirimi (bölüm 5.5) eksik değişkenlerinin sıfırdan büyük olduğu gün, vardiya ve nokta üçlülerini doğrudan bu formülasyondan okur.

### S2 — Gece adaleti

Gece çalışma yükü, bu yükü üstlenebilecek personel arasında dengeli dağıtılır. Kişi başına düşen **gece saatinin** hedeften sapması cezalandırılır.

```
gece_saat[b]  = | b ∩ [20:00, 06:00] |          (TD-2)
gece_yuku[p]  = Σ_{d ∈ ufuk} Σ_{b,n} gece_saat[b] · x[p,d,b,n]
erisebilen(n) = { q ∈ P : q, n noktasının ön koşulunu karşılıyor }
pay_gece[p]   = Σ_{d, t ∈ gece, n : p ∈ erisebilen(n)}
                    talep[d,t,n] / |erisebilen(n)|
P_gece = { p ∈ P : pay_gece[p] > 0 }
∀p ∈ P_gece :
    sapma[p] ≥ gece_yuku[p] − pay_gece[p]
    sapma[p] ≥ pay_gece[p] − gece_yuku[p]
Ceza:  w2 · Σ_{p ∈ P_gece} sapma[p]
```

**Hedef kişiye özeldir, havuz ortalaması değildir.** Her talep birimi, ona
erişebilenler arasında eşit bölünür; kişinin hedefi kendi erişebildiği
taleplerden gelen payların toplamıdır. Tek bir ortalama kullanıldığında,
erişilebilirliği kısıtlı bir havuz kalıcı olarak hedefin altında görünür: yalnızca
tek bir noktada çalışabilen bir personel, o noktanın gece talebi düşükse hedefe
hiçbir çizelgeyle ulaşamaz. Bu bir adaletsizlik değil yapısal bir sınırdır ve
ölçünün onu sapma olarak raporlaması, ölçüyü ayırt edici olmaktan çıkarır.

Bu, S4'ün adil pay tanımıyla aynı mantıktır; üç adalet hedefi de kişiye düşen
payı ölçer. Payı sıfır olan personel ölçünün dışındadır — hedefe ulaşması
imkânsız olan kimse ölçülmez.

Ölçünün birimi **saattir**, vardiya sayısı değil. Katalog farklı uzunlukta bloklar taşıdığında sayım adaleti bozar: on iki saatlik bir gece bloğu ile sekiz saatlik bir gece bloğu aynı sayılırsa, uzun bloğu alan personelin dört saatlik fazla yükü ölçüye hiç girmez. Saat, karışık uzunluklu kataloğun tek doğru ölçüsüdür.

Aynı değişiklik S3 ve S4 için de geçerlidir; üç adalet hedefi de saat biriminde olduğundan `w2`, `w3` ve `w4` doğrudan karşılaştırılabilir. Önceki sürümde `w4`'ün diğerlerinin sekizde biri ölçeğinde tutulması gereğini doğuran birim farkı ortadan kalkmıştır.

Adalet, yükü paylaşabilecekler arasında paylaştırmaktır; paylaşamayan personel ölçümün dışındadır ve **kısmen paylaşabilen personel kendi payı kadar ölçülür.** Bu ayrım iki kez bedeli ödenmiş bir hatanın karşılığıdır: önce hiç gece alamayan personel paydada sayılıyordu, sonra kısıtlı erişimi olan havuz tek ortalamaya vuruluyordu. İkisinde de ölçü, hiçbir çizelgeyle kapatılamayan bir sapma raporluyor ve ayırt ediciliğini kaybediyordu.

Ölçüm ufku TD-6'da tanımlıdır.

### S3 — Hafta sonu adaleti

Kişi başına düşen hafta sonu ve resmî tatil **saatinin** hedeften sapması cezalandırılır. Formülasyon S2 ile aynıdır; gece saati yerine hafta sonu günlerindeki toplam süre kullanılır (TD-3) ve uygun havuz aynı mantıkla belirlenir.

```
hs_yuku[p] = Σ_{d: hs[d]=1} Σ_{b,n} sure[b] · x[p,d,b,n]
pay_hs[p]  = Σ_{d: hs[d]=1, t, n : p ∈ erisebilen(n)}
                 talep[d,t,n] / |erisebilen(n)|
P_hs = { p ∈ P : pay_hs[p] > 0 }
Ceza:  w3 · Σ_{p ∈ P_hs} sapma_hs[p]
```

Hedef S2'deki gibi kişiye özel paydır.

Uygun havuz kısıtlaması burada da geçerlidir ve aynı gerekçeye dayanır: yalnızca hafta içi talebi bulunan bir noktada çalışabilen personel, hafta sonu adaleti ölçümünün dışındadır.

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

### S6 — Çalışma deseni tutarlılığı

Ardışık günlerde çalışma saatlerini kaydırmak ergonomik olarak istenmeyen bir durumdur ve cezalandırılır. Aynı gerekçeyle, ardışık günlerde farklı binalarda görevlendirilmek de ayrı bir ceza bileşeni üretir.

```
kayma[p,d] = dairesel_fark( baslangic[b_{d+1}], baslangic[b_d] )
           = min( |Δ|, 24 − |Δ| )
degisim[p,d] = 1  eğer p, d ve d+1 günlerinde çalışıyor ve
                  kayma[p,d] > desen_toleransi_saat
bina_degisim[p,d] = 1  eğer p, d ve d+1 günlerinde çalışıyor ve
                       atandığı noktaların binaları farklıysa
Ceza:  w6 · Σ degisim[p,d]  +  w6b · Σ bina_degisim[p,d]
```

Kural önceki sürümde "aynı vardiya tipi" üzerinden yazılıydı; katalog genişlediğinde bu tanım anlamını yitirir, çünkü 08.00–16.00 ile 08.00–20.00 farklı bloklardır fakat aynı saatte başlarlar ve ergonomik olarak bir kayma üretmezler. Ölçü bu nedenle blok kimliği değil **başlangıç saatidir**.

Farkın dairesel alınması zorunludur: 22.00 ile 02.00 arasındaki kayma dört saattir, yirmi saat değil. Tolerans parametredir (varsayılan 2 saat); bir saatlik kaymayı cezalandırmak, kataloğun ince taneli olmasının anlamını ortadan kaldırır.

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
min   w1·Σ eksik      + w1f·Σ fazla
    + w2·Σ sapma_gece + w3·Σ sapma_hs
    + w4·Σ sapma_saat + w5·Σ tercih_ihlal
    + w6·Σ degisim    + w6b·Σ bina_degisim
    + w7·Σ izole      + w8·Σ onceki_sapma
```

Önceki sürümdeki `eksikK` terimi kaldırılmıştır: yetkinlik bazlı eksik değişkeni, nokta boyutunun eklenmesiyle (H8) tanımsız kalmıştı ve amaç fonksiyonunda karşılığı bulunmayan bir sembol olarak duruyordu. `w1f` ve `w6b` terimleri ise kural kataloğunda tanımlı oldukları hâlde bu listede eksikti.

Ağırlıkların tamamı kullanıcı tarafından ayarlanabilir. Sistem hangi hedefin daha öncelikli olduğuna kendisi karar vermez; bu tercihi parametre olarak alır ve sonucunu hesaplar.

# 5. Fonksiyonel Gereksinimler

Öncelikler şu şekilde tanımlanmıştır: Zorunlu (sistem bu gereksinim olmadan kabul edilemez), Yüksek (temel işlevin bir parçası), Orta (zaman kalırsa gerçekleştirilir).

## 5.1 Tanım Yönetimi

| Kimlik | Gereksinim | Öncelik |
| --- | --- | --- |
| FR-1.1 | Sistem, personel kayıtlarının oluşturulmasına, güncellenmesine ve pasifleştirilmesine imkân vermelidir. Personel kaydı haftalık hedef saat, aktiflik tarih aralığı ve içinde bulunulan kota yılına ait devir fazla çalışma saatini içerir. | Zorunlu |
| FR-1.2 | Sistem, yetkinlik tanımlarının oluşturulmasına ve personele seviyesiz olarak atanmasına imkân vermelidir. | Zorunlu |
| FR-1.3 | Sistem, çalışma bloklarının ad, başlangıç saati ve bitiş saatiyle tanımlanmasına imkân vermelidir. Süre, başlangıç ve bitiş saatinden hesaplanır. Aynı başlangıç ve süre ikilisi iki kez tanımlanamaz; süresi günlük azami çalışma saatini aşan blok tanımlanamaz. | Zorunlu |
| FR-1.4 | Sistem, vardiya tipi oluşturulurken gece_mi bayrağını TD-2'ye göre önermeli, kullanıcının bu öneriyi değiştirmesine imkân vermelidir. | Yüksek |
| FR-1.5 | Sistem, bina tanımlarının oluşturulmasına ve güncellenmesine imkân vermelidir. | Zorunlu |
| FR-1.6 | Sistem, görev noktalarının ad, bağlı olduğu bina ve ön koşul yetkinliğiyle tanımlanmasına imkân vermelidir. Bina alanı boş bırakıldığında nokta tesis geneli olarak değerlendirilir. | Zorunlu |
| FR-1.7 | Sistem, talep tanımının görev noktası, zaman aralığı ve gün tipi kırılımında yapılmasına ve tekil tarihler için istisna tanımlanmasına imkân vermelidir. | Zorunlu |
| FR-1.8 | Sistem, talep tanımlarını görev noktası ve gün tipi kırılımında, her kayıt bir zaman aralığı olacak biçimde göstermeli; aralıkların ve gereken sayıların doğrudan düzenlenmesine imkân vermelidir. Aynı nokta ve gün tipi için çakışan aralıklar tanımlanamaz. | Yüksek |
| FR-1.9 | Sistem, tanımlı talepten haftalık toplam kişi-saat yükünü ve kural parametreleri altındaki asgari kadro büyüklüğünü hesaplayarak göstermelidir. Hesap saat tabanlıdır; kişi-vardiya karşılığı gösterilmez, çünkü karışık uzunluklu katalogda bu sayı kataloğun bileşimine bağlıdır. | Orta |
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
| FR-3.4 | Sistem, yöneticinin tercihleri onaylamasına veya gerekçeyle reddetmesine imkân vermelidir; ret gerekçesi tercih kaydında saklanır ve çalışana gösterilir. | Yüksek |
| FR-3.5 | Sistem, yalnızca onaylanmış tercihleri çözücü modeline dahil etmelidir. | Zorunlu |
| FR-3.6 | Sistem, onaylanmış bir tercihin çizelgede karşılanıp karşılanmadığını onay durumundan ayrı bir bilgi olarak göstermelidir. | Yüksek |



## 5.4 Çizelge Üretimi

| Kimlik | Gereksinim | Öncelik |
| --- | --- | --- |
| FR-4.1 | Sistem, seçilen dönem için kısıt programlama modeli kullanarak çizelge üretmelidir. | Zorunlu |
| FR-4.2 | Sistem, planlama ufkunun kullanıcı tarafından takvim üzerinden seçilmesine imkân vermeli, varsayılan olarak bir haftalık dönem önermelidir. Seçilebilecek azami dönem uzunluğu otuz bir gündür; bu sınır aşıldığında sistem çözümü başlatmamalı ve nedenini bildirmelidir. | Zorunlu |
| FR-4.3 | Sistem, bölüm 4.2'deki zorunlu kısıtların tamamını sağlayan çizelge üretmelidir. | Zorunlu |
| FR-4.4 | Sistem, bölüm 4.4'teki amaç fonksiyonunu en aza indiren çözümü aramalıdır. | Zorunlu |
| FR-4.5 | Sistem, önceki yayınlanmış çizelgenin son yedi gününü ısıtma penceresi olarak modele dahil etmelidir (TD-5). | Zorunlu |
| FR-4.6 | Sistem, çözüm için üst zaman limiti tanımlanmasına imkân vermeli; limit dolduğunda o ana kadar bulunan en iyi çözümü döndürmelidir. | Yüksek |
| FR-4.7 | Sistem, çözüm tamamlandığında çözüm süresini, çözüm durumunu ve toplam ceza puanını raporlamalıdır. | Zorunlu |
| FR-4.8 | Sistem, toplam ceza puanını esnek hedef bazında ayrıştırarak göstermelidir. | Yüksek |
| FR-4.9 | Sistem, çalışan bir çözüm işinin kullanıcı tarafından durdurulmasına imkân vermelidir. Durdurma anında bulunmuş en iyi çözüm atılmaz; karar verilene kadar saklanır ve kullanıcıya sunulur. Arama henüz başlamamışsa (iş kuyrukta veya ön kontroldeyse) durdurma doğrudan iptaldir ve karar sorulmaz. | Zorunlu |
| FR-4.10 | Sistem, durdurulan bir işte kullanıcıya üç seçenek sunmalıdır: sonucu kullanmak, sonucu atmak ve bulunan çözümden devam etmek. Karar verilene kadar çizelge sürümü değişmez. Çözücü henüz hiçbir çözüm bulmamışsa "kullan" seçeneği sunulmaz ve bunun nedeni yazılır. | Zorunlu |
| FR-4.11 | Sistem, çalışan veya karar bekleyen bir çözüm işini kullanıcının hangi ekranda olduğundan bağımsız olarak izlenebilir kılmalıdır. Ekran değiştirmek, sayfayı yenilemek veya oturumu başka bir cihazdan açmak işi durdurmaz ve ilerleme görünürlüğünü kaybettirmez. | Zorunlu |



Durdurmanın tek yönlü bir iptal olarak tanımlanması, çözücünün dakikalarca çalışıp
ürettiği kullanılabilir bir çizelgenin kullanıcı ona hiç bakmadan atılması anlamına
gelir. Bu, sistemin karar veren kişiyi desteklemesi ilkesiyle bağdaşmaz: durdurma
kararı "bu çözümü istemiyorum" değil, "aramanın devam etmesini istemiyorum"
demektir. İkisi ayrı sorulardır ve ikincisinin yanıtı birincisini belirlemez.

FR-4.10'daki üçüncü seçeneğin adı "devam et" olmakla birlikte, aramanın kaldığı
yerden sürdürülmesi değildir; çözücü sonlandırıldıktan sonra iç durumu geri
yüklenemez. Seçenek, bulunan çözümün başlangıç ipucu olarak verilmesiyle yeni bir
çözüm işinin başlatılmasıdır. Sonuç bulunmuş çözümden daha kötü olmaz, ancak süre
sayacı sıfırdan başlar ve çözücü aynı arama yolunu izlemeyebilir. Bu nedenle
seçenek kullanıcıya yeni bir zaman limiti sorularak sunulur ve arayüzde
"kaldığı yerden devam" ifadesi kullanılmaz.

## 5.5 Fizibilite Geri Bildirimi

| Kimlik | Gereksinim | Öncelik |
| --- | --- | --- |
| FR-5.1 | Sistem, çözüm başlatılmadan önce talep ve mevcut personel sayısını karşılaştıran ön kontrol yapmalı, karşılanamayacak gün ve saatleri listelemelidir. Ön kontrol bulguları teşhis niteliğindedir ve çözüm işini engellemez; bulgular sonuçla birlikte gösterilir ve sürüm kaydında kalıcı olur. | Yüksek |
| FR-5.2 | Sistem, personel yetersizliği durumunda çözümü reddetmek yerine çizelgeyi üretmeli ve kapsama açıklarını göstermelidir. | Zorunlu |
| FR-5.3 | Sistem, kapsama açığını gün, saat aralığı, görev noktası, gereken sayı, atanan sayı ve eksik sayı düzeyinde raporlamalıdır. | Zorunlu |
| FR-5.4 | Sistem, yetkinlik bazlı kapsama açıklarını toplam açıktan ayrı olarak göstermelidir. | Yüksek |
| FR-5.5 | Sistem, zorunlu kısıtların çelişmesi nedeniyle çözüm bulunamadığında bunu kapsama açığından ayırt edilebilir biçimde bildirmelidir. Çözüm işinin sonuçsuz kalmasının tek meşru nedeni budur; kadro yetersizliği çözümü engellemez. | Yüksek |
| FR-5.6 | Sistem, ön kontrol bulgularında ve hata metinlerinde veritabanı kimliği yerine tanım adını göstermelidir. | Orta |



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
| FR-7.6 | Sistem, arşivlenmiş bir sürümün atamalarıyla birlikte yeni bir taslak sürüme kopyalanmasına imkân vermelidir. Kaynak sürüm bu işlemden etkilenmez ve arşivde kalır. | Orta |



## 5.8 Analiz ve Raporlama

| Kimlik | Gereksinim | Öncelik |
| --- | --- | --- |
| FR-8.1 | Sistem, dönem için kapsama oranını raporlamalıdır. Oran, karşılanan kişi-saatin toplam talep kişi-saatine bölünmesiyle atama kayıtlarından hesaplanır; ataması bulunmayan bir sürümde oran sıfırdır. | Zorunlu |
| FR-8.2 | Sistem, kişi başına gece, hafta sonu ve toplam saat sayılarını tablo halinde raporlamalıdır. | Zorunlu |
| FR-8.3 | Sistem, iş yükü dağılımını en yüklü ve en az yüklü personel arasındaki fark üzerinden ölçmelidir. | Yüksek |
| FR-8.4 | Sistem, onaylanmış tercihlerin karşılanma oranını raporlamalıdır. | Yüksek |
| FR-8.5 | Sistem, çizelgeyi CSV veya Excel formatında dışa aktarabilmelidir. | Zorunlu |
| FR-8.6 | Sistem, kural bazlı ihlal ve ceza dökümünü raporlamalıdır. | Yüksek |
| FR-8.7 | Sistem, çizelgenin kapsama açıklarını ayrı bir dosya olarak dışa aktarabilmelidir. Talep karşılama esnek hedef olarak tanımlandığından (S1) açıkları içermeyen bir çıktı çizelgeyi olduğundan tam gösterir. | Zorunlu |
| FR-8.8 | Sistem, çizelgenin yazdırılabilir bir görünümünü üretebilmelidir. Görünüm personel × gün matrisi biçiminde olmalı, başlığında dönem, sürüm ve üretim tarihi bulunmalı, kapsama açıkları tablonun altında listelenmelidir. | Yüksek |



## 5.9 Çalışan Paneli

| Kimlik | Gereksinim | Öncelik |
| --- | --- | --- |
| FR-9.1 | Sistem, personelin yalnızca kendi çizelgesini görüntülemesine imkân vermelidir. Hangi personelin verisinin gösterileceği yalnızca oturumdan belirlenir; istek içindeki hiçbir alan bu seçimi değiştiremez. | Zorunlu |
| FR-9.2 | Sistem, personele yalnızca yayınlanmış durumdaki çizelge sürümünü göstermelidir. | Zorunlu |
| FR-9.3 | Sistem, personelin çizelgesini dönem görünümünde (dönem uzunluğu ne ise o kadar) ve liste görünümünde sunmalı, sıradaki vardiyayı öne çıkarmalıdır. | Yüksek |
| FR-9.4 | Sistem, yayınlanmış çizelgede, aynı dönemde en son arşive alınmış sürüme göre değişen günleri işaretlemelidir. Değişim üç biçimde ayrışır: eklendi, kaldırıldı, değişti (vardiya tipi veya görev noktası farklı). Dönemin ilk yayınında karşılaştırma tabanı bulunmadığından hiçbir gün işaretlenmez. | Yüksek |
| FR-9.5 | Sistem, personelin dönem içindeki gece, hafta sonu ve toplam saat sayısını ekip ortalamasıyla birlikte göstermelidir. | Orta |
| FR-9.6 | Sistem, personelin tercih bildirmesine ve bildirdiği tercihlerin durumunu görmesine imkân vermelidir. | Yüksek |



## 5.10 Kimlik Doğrulama ve Yetkilendirme

Sistem bir kurum içi araçtır; kullanıcılar kendi kendilerine kayıt olmaz, hesapları yönetim tarafından oluşturulur. Bu nedenle sistemde kayıt ekranı bulunmaz, yalnızca giriş ekranı vardır.

Üç kullanıcı rolü tanımlıdır:

| Rol | Kapsam |
| --- | --- |
| Çalışan | Yalnızca kendi çizelgesini, dönem özetini ve tercihlerini görür ve yönetir (5.9). Tanım, çözüm ve yayın işlevlerine erişemez. |
| Yönetici | Vardiya yöneticisinin bütün işlevlerine erişir: tanımlar, talep, kural, çözüm, manuel düzenleme, sürüm yönetimi, analiz ve dışa aktarma. Kullanıcı hesaplarını yönetemez. |
| Yönetim (admin) | Yöneticinin bütün yetkilerine ek olarak kullanıcı hesaplarını oluşturur, rolünü değiştirir, parolasını sıfırlar ve hesabı devre dışı bırakır. |

Roller kapsayıcıdır: yönetim rolü, yönetici rolünün yetkilerini içerir. Çalışan rolü diğerlerinin alt kümesi değildir; kendi verisine erişim, personel kaydına bağlı ayrı bir yetkidir.

| Kimlik | Gereksinim | Öncelik |
| --- | --- | --- |
| FR-10.1 | Sistem, kullanıcı adı ve parola ile giriş yapılan tek bir giriş ekranı sunmalı, kayıt ekranı içermemelidir. | Zorunlu |
| FR-10.2 | Sistem, parolaları yalnızca özet (hash) biçiminde saklamalı, geri çevrilebilir hiçbir biçimde tutmamalıdır. | Zorunlu |
| FR-10.3 | Sistem, giriş yapan kullanıcı için sunucu tarafında bir oturum kaydı oluşturmalı; oturumun süresi dolduğunda veya çıkış yapıldığında oturum geçersiz hâle gelmelidir. | Zorunlu |
| FR-10.4 | Sistem, her isteğin yetkisini oturumdaki role göre sunucu tarafında denetlemelidir. Arayüzün bir işlevi gizlemesi yetkilendirme sayılmaz. | Zorunlu |
| FR-10.5 | Sistem, yönetim rolündeki kullanıcının hesap oluşturmasına, rol atamasına, parola sıfırlamasına ve hesabı devre dışı bırakmasına imkân vermelidir. Hesap silme yerine devre dışı bırakma kullanılır. | Zorunlu |
| FR-10.6 | Sistem, çalışan rolündeki her hesabı bir personel kaydına bağlamalıdır; bağlantısı olmayan bir çalışan hesabı oluşturulamaz. Bir personelin birden fazla hesabı bulunamaz: iki hesap da yalnızca kendi verisini göreceğinden erişim açısından sakınca doğmaz, ancak parola sıfırlandığında hangi hesabın sıfırlandığı belirsizleşir. | Zorunlu |
| FR-10.7 | Sistem, yönetim tarafından oluşturulan veya sıfırlanan parolanın ilk girişte değiştirilmesini zorunlu tutmalıdır. | Yüksek |
| FR-10.8 | Sistem, ardışık başarısız giriş denemelerinde hesabı geçici olarak kilitlemeli ve kilit süresini bildirmelidir. Kilit bildirimi ile hesabın devre dışı olduğu bildirimi yalnızca parola doğru girildiğinde gösterilir; parolayı bilmeyen bir kullanıcı bu metinleri hiçbir kullanıcı adı için göremez. Aksi hâlde bildirim, hesabın var olup olmadığını ele veren bir sinyale dönüşür. | Yüksek |
| FR-10.9 | Sistem, başarılı ve başarısız giriş denemeleri ile hesap yönetimi işlemlerini zaman damgasıyla kaydetmelidir. | Orta |
| FR-10.10 | Sistem, ilk yönetim hesabının arayüz dışı bir kurulum adımıyla oluşturulmasına imkân vermelidir. | Zorunlu |
| FR-10.11 | Kullanıcı adları ASCII karakter kümesiyle sınırlandırılmalıdır. Türkçe karakterlerin küçültülmesi veritabanı ile uygulama katmanında farklı sonuç verebildiğinden, sınır olmadan açılan bir hesabın sahibi doğru parolayla dahi giriş yapamayabilir. | Zorunlu |



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
tarih; sicil; ad; vardiya_tipi; gorev_noktasi; gece_mi; hafta_sonu_mu; sure_saat
```

Görev noktası sütunu, atamanın görev noktası kırılımında tutulmasından gelir (Yazılım Tasarım Dokümanı 4.2.4); noktası olmayan bir satır kaydın yalnızca bir bölümünü taşır. Tarih sütunu, satırların gün ekseninde okunmasını kolaylaştırmak üzere başa alınmıştır.

**Kapsama açığı dışa aktarma (CSV):**

```
tarih; vardiya_tipi; gorev_noktasi; tur; kisi_sayisi
```

Bu dosya iki tür sapmayı birlikte taşır: talebin altında kalan kapsama açıkları ve manuel düzenlemeyle talebin üzerine çıkılan fazla kadro kayıtları. Tür sütunu hangisinin söz konusu olduğunu belirtir; kişi sayısı her iki türde de pozitif yazılır, yönü tür bildirir. İkisinin aynı dosyada bulunması, satır şekillerinin aynı olmasından kaynaklanır — ayrı dosya gerekçesi, farklı sütun kümelerinin tek dosyaya sıkıştırılmasına karşıdır, aynı şekildeki satırların ayrılmasını gerektirmez.

Kapsama açıkları çizelge dosyasının içinde bir bölüm olarak değil, ayrı bir dosya olarak verilir. Tek dosyada iki başlık bloğu bulunması, uzun biçimin varlık nedeni olan makine okunabilirliğini ortadan kaldırır; hiçbir tablo programı böyle bir dosyayı tek tablo olarak açamaz. Açık bulunmayan bir sürümde dosya yalnızca başlık satırıyla üretilir; sıfır satır, açık bulunmadığı anlamına gelir ve dosya hiçbir durumda üretilmeden bırakılmaz.

Dosya karakter kodlaması UTF-8 olmalı ve bayt sırası imi (BOM) içermelidir; tarih biçimi ISO 8601 (YYYY-AA-GG) kullanılmalıdır. Alan ayracı noktalı virgüldür. Bu iki tercih Türkçe yerelli elektronik tablo programlarından kaynaklanır: bayt sırası imi bulunmadığında Türkçe karakterler bozuk görüntülenir, virgül ayracı ise ondalık ayracı olarak yorumlanıp bütün satırı tek sütuna yığar.

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
| NFR-14 | Performans | Durdurma isteği, çözücünün yeni bir ara çözüm bulmasını beklemeden birkaç saniye içinde etkili olmalıdır. Kullanıcı durdurmanın ardından bir karar ekranı beklediğinden, isteğin iki iyileşme arasında sessizce beklemesi kabul edilemez. |



# 9. İzlenebilirlik Matrisi

Aşağıdaki tablo, proje tanım dokümanındaki hedefleri bu dokümandaki gereksinimlerle ve kabul kriterleriyle ilişkilendirir.

| Hedef | Gereksinimler | Kabul Kriteri |
| --- | --- | --- |
| Tanım Yönetimi | FR-1.1 – FR-1.14 | Tüm tanımlar arayüzden oluşturulabilir; örnek veri seti üretilebilir |
| Çizelge Üretimi | FR-4.1 – FR-4.8, H1–H8 | Referans örnek 60 saniyenin altında çözülür; zorunlu kısıt ihlali yoktur (NFR-1, NFR-8) |
| Fizibilite Geri Bildirimi | FR-2.4, FR-5.1 – FR-5.5, S1 | Çelişkili örnekte hangi gün ve vardiyada kaç kişi eksik kaldığı gösterilir |
| Manuel Müdahale | FR-6.1 – FR-6.6 | İhlal bildirimi bir saniyenin altında görüntülenir (NFR-2) |
| Değişim Odaklı Yeniden Çözme | FR-7.1 – FR-7.6, S8 | Yeniden çözümde değişen atama sayısı raporlanır |
| Yük Dengesi ve Adalet | S2, S3, S4, FR-8.2, FR-8.3 | Kişi başına gece sayısı hedeften en fazla bir sapar (NFR-9) |
| Tercih Yönetimi | FR-3.1 – FR-3.6, S5 | Onay durumu ve karşılanma durumu ayrı ayrı gösterilir |
| Analiz ve Raporlama | FR-8.1 – FR-8.8, FR-4.8 | Ceza dökümü hedef bazında ayrıştırılır |
| Çalışan Görünürlüğü | FR-9.1 – FR-9.6 | Yalnızca yayınlanmış sürüm görünür; değişen günler işaretlenir |
| Kimlik Doğrulama ve Yetkilendirme | FR-10.1 – FR-10.11 | Yetkisiz rol, yetkisi dışındaki uç noktalardan veri alamaz |



## 9.1 Kapsam Dışı Gereksinimler

Aşağıdaki işlevler bu sürümün kapsamı dışındadır ve gereksinim olarak tanımlanmamıştır: izin talebi ve onay iş akışı, bordro ve puantaj, vardiya takası, personel bildirimleri, mobil uygulama, kurum sistemlerine entegrasyon, eş zamanlı düzenleme, geçmiş dönemlerden devreden kümülatif adalet, çelişen zorunlu kısıtlarda otomatik çakışma teşhisi.
