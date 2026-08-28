**TED ÜNİVERSİTESİ**

**CMPE 399 — Yaz Stajı**

kurum Boru Hatları ile Petrol Taşıma A.Ş.

**VARDİYA ÇİZELGELEME KARAR DESTEK ARACI**

**Yazılım Gereksinim Belirtimi**

(Software Requirements Specification)

**Ömer HARMANKAYA**

Endüstri Mühendisliği / Bilgisayar Mühendisliği

05.08.2026

Sürüm 1.0

> **Not.** Bu doküman CMPE 399 yaz stajı kapsamında hazırlanmıştır. Sistem
> kurum bünyesinde kullanıma alınmamış, kurumdan gerçek veri kullanılmamıştır.
> Belgedeki kadro, görev noktası ve talep sayıları gösterim amaçlı
> varsayımlardır.

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
| Ömer HARMANKAYA | 13.08.2026 | Esnek hedeflerin ceza değişkenlerinin üst sınırla kısıtlanamayacağı 4.3'e yazıldı: S3'ün sapma değişkenine konan üst sınır, kadro yetersizken modeli çözülemez kılıyor ve FR-5.2'yi ihlal ediyordu | 1.18 |
| Ömer HARMANKAYA | 13.08.2026 | Model, önceden tanımlı çalışma bloklarının seçiminden gerçek saatlik karara geçirildi: karar değişkeni mutlak saat ekseninde tanımlandı (TD-13), blok kataloğu ve `gece_mi` bayrağı kaldırıldı (3.3.1, TD-2), H1 kesintisizlik kısıtına, H3 gece gününe, H9 günlük toplama, S6 fiilî başlangıç kaymasına dönüştürüldü, asgari blok süresi ve gece eşiği parametreleri eklendi (3.3.5). Müracaat görev noktası ve yetkinliği kaldırıldı; talebi Güvenlik'e taşındı (3.3.2, 3.3.3, 3.3.4) | 1.19 |
| Ömer HARMANKAYA | 13.08.2026 | S4'ün sapma ölçüsü, S2 ve S3'ün kullandığı taban/tavan yöntemine çevrildi; üç adalet hedefi artık aynı yöntemi kullanıyor | 1.20 |
| Ömer HARMANKAYA | 13.08.2026 | H1 ve H9'daki "gün d" ifadesi bloğun başlangıç gününe bağlandı; takvim günü sayımı gece yarısını aşan blokta günlük tavanı hiç tetiklemiyordu. 3.3.6'daki müracaat satırı ve blok sayısına dayalı toplam kaldırıldı | 1.21 |
| Ömer HARMANKAYA | 13.08.2026 | 7.2'deki çizelge dışa aktarma biçimi saat modeline göre yeniden yazıldı; vardiya tipi ve gece bayrağı alanları kaldırıldı, başlangıç ve bitiş ISO damgasına çevrildi | 1.22 |
| Ömer HARMANKAYA | 14.08.2026 | Manuel düzenleme taslak oturum modeline geçirildi (5.6): değişiklikler anında görünür ve geri alınabilir, sunucuya yalnızca kaydetmeyle yazılır; blok taşıma ve yayınlanmış sürümün salt okunurluğu gereksinim olarak yazıldı; TD-16 eklendi | 1.23 |
| Ömer HARMANKAYA | 14.08.2026 | Çizelgenin ve analizin Excel çıktısı gereksinim olarak tanımlandı (FR-8.5, FR-8.9); dosya yapısı ve biçimlendirme kuralları 7.2'ye yazıldı | 1.24 |
| Ömer HARMANKAYA | 14.08.2026 | Adalet ufkunun tanımı tamamlandı: geçmiş yükün ve hedefin birlikte ölçeklenmesi, ufuk içinde kısmen çalışabilir personel için payın orantılanması ve erişilebilirliğin bugünkü tanımdan alınması TD-6'ya yazıldı | 1.25 |
| Ömer HARMANKAYA | 18.08.2026 | Günde tek tercih kuralı FR-9.6'ya, çözücü zaman limitinin yeni varsayılanı FR-4.6'ya yazıldı; 7.2'deki çizelge dışa aktarma sütun listesiyle açıklama arasındaki çelişki giderildi | 1.26 |
| Ömer HARMANKAYA | 19.08.2026 | Rol yapısı dörde çıkarıldı (5.10): sistem yöneticisi, hesap yöneticisi, idare, çalışan; kendini kilitleme koruması FR-10.12, geçici parolanın tek seferlik gösterimi FR-10.13 ile tanımlandı. İzin belgesi eklendi (FR-2.7, FR-2.8) ve belgenin sağlık verisi olarak ele alınması TD-17'de yazıldı | 1.27 |



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
| Atama | Bir personelin belirli bir günde, belirli bir saat aralığında ve görev noktasında çalıştırılması. |
| Talep | Bir gün tipi ve zaman aralığı için bir görev noktasında gereken personel sayısı. |
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
| Bina | Ad, açıklama |
| Görev Noktası | Ad, bağlı olduğu bina (boş ise tesis geneli), ön koşul yetkinliği (boş olabilir), aktiflik |
| Gün Tipi | Hafta içi, hafta sonu, resmî tatil |
| Talep | Gün tipi veya tekil tarih, zaman aralığı, görev noktası, gereken personel sayısı |
| Müsaitlik Kaydı | Personel, başlangıç tarihi, bitiş tarihi, dilim (tam gün / öğleden önce / öğleden sonra), tip (yıllık izin, rapor, eğitim, mazeret) |
| Tercih | Personel, tarih veya tarih aralığı, tip (çalışmama, tercih edilen zaman aralığı), durum (beklemede, onaylandı, reddedildi), çalışanın isteğe bağlı notu, yöneticinin ret gerekçesi |
| Kural | Kimlik, tip (zorunlu / esnek), parametreler, ağırlık (esnekse), aktiflik |
| Dönem | Başlangıç tarihi, bitiş tarihi, tercih son bildirim tarihi |
| Çizelge Sürümü | Dönem, sürüm numarası, durum, oluşturma zamanı, çözüm süresi, ceza dökümü |
| Atama | Çizelge sürümü, personel, başlangıç zamanı, bitiş zamanı, görev noktası, kilitli_mi bayrağı, kaynak (çözücü / manuel) |



## 3.2 Temel Tanımlar ve Sayma Kuralları

Bu bölümdeki tanımlar sistemin tamamı için bağlayıcıdır. Bir kuralın nasıl değerlendirileceği, bir metriğin nasıl sayılacağı ve arayüzün neyi göstereceği bu tanımlara dayanır.

### TD-1 — Vardiyanın güne ilişkilendirilmesi

Bir vardiya, başladığı takvim gününe ilişkilendirilir. Gece yarısını aşan vardiyalar da başlangıç gününe yazılır. Bu kural atama, sayma, raporlama ve arayüz gösteriminin tamamında geçerlidir.

### TD-2 — Gece çalışması

Gece çalışması hesaplanır, işaretlenmez. Bir çalışmanın gece saati, o çalışmanın **20.00–06.00 aralığıyla kesişiminin uzunluğudur**.

Ölçü iki yerde kullanılır ve ikisinde de aynı tabandan gelir:

- **H3** — bir günün gece günü sayılıp sayılmadığı, o gün gece saatlerinde geçirilen sürenin `gece_esigi_saat` değerine ulaşıp ulaşmadığından belirlenir. Ergonomik yorum burada taşınır: iki saat gece çalışmak bir gece nöbeti değildir.
- **S2** — kişinin taşıdığı gece yükü, ufuk içindeki gece saatlerinin toplamıdır.

Önceki sürümlerde çalışma zamanı bir katalogdan seçildiği için gece bilgisi vardiya tipi üzerinde `gece_mi` bayrağı olarak tanımlanıyordu ve bayrağın hesaplanan değil tanımlanan bir alan olması gerekiyordu. Blok kataloğu kaldırıldığı için işaretlenecek bir nesne kalmamıştır; bayrak da kalkmıştır. Bayrağın otomatik hesaplanan bir öneriyle ezilmesi bir kez yaşanmış ve K3 kabul kriterinin karşılanmamasının iki nedeninden biri olmuştu — o risk artık yapısal olarak yoktur, çünkü tek bir tanım vardır.

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

Bir dönemin birden çok yayınlanmış sürümü bulunabilir; sayım her dönem için **en son yayınlanan** sürümü kullanır. Ufuk bir dönemin ortasına düşerse o dönemin yalnızca pencereye giren günleri sayılır; blok başladığı güne yazılır (TD-1).

**Yük ile hedef birlikte ölçeklenir.** Adalet ölçüsü, ufuk boyunca taşınan yükü ufuk boyunca düşen payla karşılaştırır. Dönem içi yükü ufuk boyunca hesaplanmış bir payla karşılaştırmak, kişiyi hiç yapmadığı bir işin hesabını verirken göstermek olur:

```
gece_yuku[p]  = geçmiş_gece[p] + dönem içi gece saati
pay_gece[p]   = ( geçmiş gerçekleşen gece saati + dönem gece talebi )
                erişebilenler arasında bölünerek, p'nin payları toplamı
```

Geçmiş için talep değil **gerçekleşen** saat kullanılır: geçmiş dönemlerin talep tanımları o günden bu yana değişmiş olabilir ve sistemin elindeki kesin bilgi kimin ne kadar çalıştığıdır.

**Pay, çalışabilirlik oranıyla ölçeklenir.** Ufkun tamamında çalışabilir olmayan personel — arada işe başlamış, uzun izne ayrılmış veya aktifliği sona ermiş olan — tam pay ile ölçülemez. Böyle bir personel yükün tamamını taşıyamaz ve tam payla karşılaştırıldığında kalıcı olarak hedefin altında görünür; sapma hiçbir çizelgeyle kapatılamaz.

```
calisabilir_oran[p] = ufuk içinde p'nin çalışabilir olduğu gün / ufuk gün sayısı
pay[p] ← pay[p] · calisabilir_oran[p]
```

Çalışabilirlik, personelin aktiflik tarih aralığından ve tam gün kapsayan müsaitlik kayıtlarından hesaplanır.

Bu, aynı hatanın üçüncü biçimidir ve ilk ikisi bu projede yaşanmıştır: önce gece talebi bulunan hiçbir noktada çalışamayan personel paydada sayılıyordu, sonra erişilebilirliği kısıtlı havuz tek ortalamaya vuruluyordu. Üçünde de ölçü, hiçbir çizelgeyle kapatılamayan bir sapma raporlayarak ayırt ediciliğini kaybediyordu.

**Erişilebilirlik bugünkü tanımdan alınır.** Bir personelin geçmişte hangi noktalarda çalışabildiği kayıt altında değildir; yetkinlik tanımı o günden bu yana değişmiş olabilir. Sayım bu nedenle güncel yetkinlikleri kullanır. Yaklaşıklık bilinçlidir; alternatifi yetkinlik değişikliklerinin tarihçesini tutmaktır ve kazandıracağı kesinlik bu maliyeti karşılamaz.

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

Türetme yalnızca onaylanmış tercihler için yapılır ve tercihin tipine göre değişir. Çalışmama tercihi, ilgili günde o personele hiçbir atama yapılmamışsa karşılanmış sayılır. Zaman aralığı tercihi ise ilgili günde atama bulunması ve atanan bloğun tamamının tercih edilen aralığın içinde kalması hâlinde karşılanmış sayılır; bloğun bir kısmı aralığın dışına taşıyorsa tercih karşılanmamıştır.

Değer ikili değil üç durumludur. Dönem için yayınlanmış bir çizelge sürümü henüz yoksa sonuç "karşılanmadı" değil "henüz belirsiz"dir; bu ayrım kullanıcı arayüzünde de korunmalıdır, aksi hâlde çizelge üretilmeden önce bütün tercihler reddedilmiş gibi görünür.

### TD-13 — Çalışma zamanı ve kesintisizlik

Sistem, çalışma zamanını önceden tanımlanmış vardiya tiplerinin seçimi olarak değil, **saatin kendisi** üzerinden modeller. Karar değişkeni bir personelin belirli bir saatte çalışıp çalışmadığıdır; bloğun başlangıç saati ve süresi çözümün çıktısıdır, girdisi değil.

```
S = { 0, 1, …, 24·D−1 }   dönemin ve ısıtma penceresinin mutlak saat ekseni
z[p,s] ∈ {0,1}            p personeli s saatinde çalışıyor
x[p,s,n] ∈ {0,1}          … ve n görev noktasında
∀p, ∀s :  Σ_n x[p,s,n] = z[p,s]
```

**Zaman ekseni gün başına sıfırlanmaz.** Eksenin gün × saat biçiminde kurulması hâlinde gece yarısını aşan bir çalışma — örneğin 20.00–08.00 — günün sonunda kesilir, ertesi günün başında yeniden başlar ve kesintisizlik kuralı onu iki ayrı blok sayar; kural, tam da izin verilmesi gereken çalışmayı yasaklamış olur. Mutlak eksende blok gün sınırını doğal olarak aşar ve gün kavramı yalnızca sayım için kullanılır.

**Bir personelin bir gündeki çalışması tek ve kesintisizdir.** Gün içinde bölünmüş çalışma — dört saat çalışıp ara verip aynı gün beş saat daha çalışmak — tanımlı değildir. Kural, blok başlangıcı göstergesi üzerinden yazılır (H1).

Blok başladığı güne sayılır (TD-1); ertesi güne taşan saatler yeni bir başlangıç üretmediği için ayrı blok sayılmaz. Adalet, ardışıklık ve haftalık saat hesapları da bloğu başladığı güne yazar.

Önceki sürümler çalışma zamanını bir katalogdan seçilen blok olarak tanımlıyordu. Katalog yaklaşımı, kullanıcının vardiya tiplerini elle tanımlamaya devam etmesini gerektiriyor ve çizelgeyi o tiplerin dizilimi hâline getiriyordu. Yeterince ince taneli bir katalog (her saatte başlayan, her makul uzunlukta) ise saat modelinden yaklaşık sekiz kat fazla karar değişkeni üretmektedir; kataloğun sağladığı sadelik yalnızca katalog kaba kaldığı sürece geçerlidir.

## 3.3 Uygulama Alanı: Güvenlik Personeli

Bu bölüm, bölüm 3.1 ve 3.2'de tanımlanan yapının ilk uygulama alanına ait somut değerlerini içerir. Buradaki hiçbir değer koda gömülü değildir; tamamı bölüm 5.1'deki tanım yönetimi gereksinimleri aracılığıyla düzenlenebilen veridir. Değerler mevcut işleyişten alınmış varsayımlara dayanmakta olup mentör görüşmesinde teyit edilecektir.

Planlama dönemi varsayılan olarak bir haftadır; yönetici bunu istediği bir uzunluğa çıkarabilir. Bu bir kısıt değil bir başlangıç değeridir — sistem daha uzun dönemleri de destekler ve NFR-1'in kırk personel/yirmi sekiz gün ölçeğindeki performans hedefi bu daha büyük dönemler için hâlâ geçerlidir (bkz. 3.3.6).

### 3.3.1 Çalışma Zamanı

Sistem çalışma zamanını saat düzeyinde belirler (TD-13); önceden tanımlanmış vardiya tipleri veya blok kataloğu bulunmaz. Çözücü, her personelin her gün için çalışıp çalışmayacağına, çalışacaksa hangi saatte başlayıp kaç saat süreceğine kendisi karar verir.

Kararın çerçevesini üç parametre çizer:

| Parametre | Değer | Etkisi |
| --- | --- | --- |
| asgari_blok_saat | 4 | Bir günlük çalışma bundan kısa olamaz |
| azami_gunluk_saat | 11 | Bir günlük çalışma bundan uzun olamaz (H9) |
| gece_esigi_saat | 4 | Bir gün, gece saati bu değere ulaşıyorsa gece günü sayılır (H3) |

Asgari blok süresi olmadan çözücü tek saatlik çalışmalar üretebilir; bu sahada karşılığı olmayan ve çizelgeyi okunamaz kılan bir sonuçtur. Değer, diğer bütün kural parametreleri gibi Kural ekranından değiştirilebilir.

Gece saati, çalışmanın 20.00–06.00 aralığıyla kesişimidir ve hesaplanır (TD-2); işaretlenen bir alan değildir.

### 3.3.2 Yetkinlikler

| Yetkinlik | Tanım |
| --- | --- |
| Güvenlik Görevi | Güvenlik noktasında (kapı ve kontrol odası görevlerini birlikte kapsar) görev alabilmenin ön koşuludur; kontrol odasında görevli personel ayrı bir meslek grubu değil, aynı noktanın bir parçasıdır. |
| Vardiya Şefi | Vardiya şefliği noktasının ön koşuludur. Bu yetkinliğe sahip personel Güvenlik Görevi yetkinliğini de taşır ve bütün noktalarda görevlendirilebilir. |



Önceki sürümlerde üçüncü bir yetkinlik (Müracaat Görevlisi) ve buna karşılık gelen bir görev noktası bulunuyordu. Müracaat noktası kaldırılmış, personeli güvenlik görevlisi olarak havuza katılmıştır (3.3.3).

### 3.3.3 Görev Noktaları

| Görev Noktası | Bina | Ön Koşul Yetkinliği |
| --- | --- | --- |
| Vardiya Şefliği | — (tesis geneli) | Vardiya Şefi |
| Güvenlik | — (tesis geneli) | Güvenlik Görevi |



Tesiste iki bina bulunmaktadır, ancak görev noktaları bina ayrımı yapılmadan tesis geneli tanımlanmıştır: kapı ve kontrol odası arasındaki ayrım kaldırılmış, ikisi tek bir "Güvenlik" noktasında birleştirilmiştir — kontrol odasında görevli personel zaten ayrı bir meslek grubu değil, aynı yetkinliğe sahip bir güvenlik görevlisiydi (bkz. 3.3.2), dolayısıyla atamanın hangi fiziksel noktaya yazıldığı modelin ihtiyaç duyduğu bir bilgi değildir; kim hangi kapıda veya kontrol odasında duracağını vardiya şefi o gün belirler. Devriye görevi bulunmamaktadır.

Müracaat noktası kaldırılmıştır. Noktanın iş yükü Güvenlik talebine eklenmiş, personeli güvenlik görevlisi olarak havuza katılmıştır; toplam iş yükü değişmemiştir (3.3.4). Kaldırma, modeli sadeleştirmenin yanında erişilebilirlik asimetrisini de büyük ölçüde ortadan kaldırır: tek noktaya kapalı bir personel havuzu kalmamıştır. Bir personel bir çalışma bloğu boyunca nokta değiştiremez; gün içinde iki farklı noktada görev almak tanımlı değildir.

### 3.3.4 Talep Matrisi

Talep bir **zaman aralığına** bağlanır. Bir talep kaydı `(görev noktası, gün tipi, başlangıç, bitiş, gereken sayı)` biçimindedir ve "bu noktada, bu saatler arasında şu kadar kişi bulunsun" anlamına gelir.

| Görev Noktası | Gün Tipi | Aralık | Gereken |
| --- | --- | --- | --- |
| Vardiya Şefliği | Hafta içi | 00.00 – 24.00 | 1 |
| Vardiya Şefliği | Hafta sonu / tatil | 00.00 – 24.00 | 1 |
| Güvenlik | Hafta içi | 00.00 – 08.00 | 3 |
| Güvenlik | Hafta içi | 08.00 – 24.00 | 9 |
| Güvenlik | Hafta sonu / tatil | 00.00 – 24.00 | 3 |



Haftalık toplam iş yükü **1.152 kişi-saattir**. Müracaat noktasının kaldırılması bu toplamı değiştirmemiştir: noktanın hafta içi gündüz ve akşam saatlerindeki iki kişilik talebi Güvenlik'in 08.00–24.00 aralığına eklenmiş, gereken sayı yediden dokuza çıkmıştır.

Kapsama, aralık kaydından türetilen saat ekseninde değerlendirilir (bölüm 4.3, S1). Açılım tek bir yerde yapılır; talep ekranı, ön kontrol, çözücü, analiz ve kapsama açığı raporlaması aynı açılımı kullanır.

Talep kayıtları gün tipi başına ayrı tutulur: hafta içi, hafta sonu ve resmî tatil için ayrı satırlar bulunur. Resmî tatil satırlarının eksik olması, o gün için hiçbir satır bulunamamasına ve talebin sessizce sıfıra düşmesine yol açar; talep sıfır olduğunda kapsama açığı da doğmayacağı için durum hiçbir raporda görünmez. Bu nedenle resmî tatil satırları, tatil tanımı yapılabilen her kurulumda bulunmak zorundadır.

### 3.3.5 Kural Parametreleri

| Kural | Parametre | Değer |
| --- | --- | --- |
| H2 | asgari_dinlenme_saati | 16 |
| H3 | azami_ardisik_gece | 3 |
| H4 | azami_ardisik_calisma_gunu | 6 |
| H5 | haftalik_mutlak_tavan | 66 |
| H6 | haftalik_asgari_izin_gunu | 1 |
| H1 | asgari_blok_saat | 4 |
| H3 | gece_esigi_saat | 4 |
| H9 | azami_gunluk_saat | 11 |
| H10 | fazla_calisma_esigi | 45 |
| H10 | yillik_fazla_kotasi | 270 |
| S6 | desen_toleransi_saat | 2 |
| S2, S3, S4 | adalet_ufku_gun | 90 |



Haftalık mutlak tavanın 66 saat olması, günlük azami on bir saat ile haftada en az bir izin gününün (H6) zaten ima ettiği üst sınırdır: altı çalışma günü × on bir saat. Değer bu nedenle tek başına ek bir kısıt getirmez; daha sıkı bir tavan istendiğinde parametre değiştirilir, kural yeniden yazılmaz. Kırk beş saat artık bir tavan değil, fazla çalışmanın başladığı eşiktir (H10).

Asgari dinlenme süresinin 16 saat olarak belirlenmesi, üçlü sekiz saatlik düzende iki çalışılan vardiya arasında en az iki boş vardiya bulunması gereksiniminin saat cinsinden karşılığıdır. Kuralın saat üzerinden yazılması, vardiya yapısı değiştiğinde yeniden tanımlanmasını gereksiz kılar (bkz. H2). Bu değer altında yalnızca ileri yönlü vardiya geçişleri mümkün kalır; gece, gündüz ve akşam sırası korunur, geri yönlü geçişler için araya en az bir izin günü girmesi gerekir.

### 3.3.6 Kadro Büyüklüğü Analizi

Talep, haftada **1.152 kişi-saatlik** bir iş yükü üretmektedir: hafta içi beş gün için günde 192, hafta sonu iki gün için günde 96 kişi-saat. Ölçü kişi-saattir; blok süreleri çözümün çıktısı olduğundan vardiya sayısı üzerinden bir hesap tanımlı değildir.

Kadro gereksinimi fazla çalışma eşiği üzerinden hesaplanır: 1.152 saat / 45 saat ≈ 26 kişi. H6 (haftada en az bir izin günü) ile birlikte bir personel haftada en çok altı gün çalışabilir; on bir saatlik günlük tavan (H9) teorik olarak 66 saate izin verse de bu saatlerin tamamı fazla çalışma sayılır ve yıllık kotayı hızla tüketir. Sürdürülebilir planlama eşiğin altında kalmayı gerektirir. İzin ve rapor payı hariç asgari **26 kişilik** bir kadro gereksinimi çıkmaktadır; payla birlikte 29.

**Kadronun asgarinin belirgin biçimde üzerinde olması, adalet hedeflerini dar bir banda sıkıştırır.** Kırk dört kişilik bir kadroda kişi başına haftalık yük 26 saate düşer ve hiç kimse fazla çalışma eşiğine yaklaşmaz; H10 hiçbir zaman tetiklenmez, S4 dar bir aralıkta çalışır. Gösterim verisi bu nedenle kadroyu talebe göre boyutlandırmalıdır — aksi hâlde kuralların işlediği gösterilemez.

Yetkinlik havuzları ayrı ayrı değerlendirildiğinde tablo aşağıdaki gibidir.

| Yetkinlik Havuzu | Haftalık Kişi-Saat | Teorik Asgari | İzin Payıyla |
| --- | --- | --- | --- |
| Vardiya Şefi | 168 | 4 | 6 |
| Güvenlik Görevi | 984 | 22 | 25 |
| Toplam | 1.152 | 26 | 31 |

Vardiya Şefliği noktası haftanın her günü kesintisiz bir kişi gerektirir: 7 × 24 = 168 kişi-saat. Kalan yük güvenlik noktasınındır. Şef yetkinliğine sahip personel güvenlik noktasında da çalışabildiği için iki havuzun asgarileri toplandığında bir miktar fazlalık oluşur; tabloda havuzlar bağımsız hesaplanmıştır.

**Vardiya Şefi havuzu yapısal olarak kırılgandır.** Tek bir noktanın kesintisiz doldurulması gerekir ve o noktanın ön koşulunu yalnızca bu havuz karşılar. Havuzun bir kısmının aynı dönemde izinli olması, kadro büyüklüğünden ve çalışma sürelerinin uzunluğundan bağımsız olarak kapsama açığı üretir; kırılganlık senaryosu (Charter bölüm 5, K4) bu mekanizmayı kullanır.



Vardiya şefliği havuzu sistemin en kırılgan bileşenidir. Kesintisiz doldurulan tek bir görev noktası haftada 168 kişi-saat gerektirmekte; küçük bir havuzda tek bir personelin izne ayrılması, kalanların fazla çalışma eşiğini aşmadan bu yükü karşılayamaması nedeniyle kapatılamayan bir boşluk doğurmaktadır. Kırılganlık kadro büyüklüğünden değil erişilebilirlikten gelir: noktanın ön koşulunu yalnızca bu havuz karşılar, dolayısıyla açık çalışma sürelerinin uzunluğundan bağımsızdır.

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

### H1 — Günde tek ve kesintisiz çalışma

Bir personelin bir takvim gününde en fazla bir çalışma bloğu bulunur; blok kesintisizdir ve süresi asgari blok süresinden kısa olamaz.

```
bas[p,s] ≥ z[p,s] − z[p,s−1]              blok başlangıcı göstergesi
bas[p,s] ≤ z[p,s]
bas[p,s] ≤ 1 − z[p,s−1]
∀p, ∀d :  Σ_{s ∈ gün d} bas[p,s] ≤ 1
∀p, ∀d :  Σ_{s ∈ G(p,d)} z[p,s] ≥ asgari_blok_saat · Σ_{s ∈ gün d} bas[p,s]
          G(p,d) : d gününde başlayan bloğa ait saatler (H9)
```

Parametre: asgari_blok_saat. Kuralın son satırı, bir gün çalışma başlamışsa o günün toplam çalışma süresinin asgari blok süresine ulaşmasını zorunlu kılar; hiç çalışılmayan günde her iki taraf da sıfırdır.

Gün içinde bölünmüş çalışma bu kuralla dışlanır: ikinci bir aralık ikinci bir başlangıç göstergesi üretir ve toplam bir sınırını aşar. Gece yarısını aşan bloklar kuralı bozmaz — taşan saatler yeni bir başlangıç üretmez ve blok başladığı güne sayılır (TD-1, TD-13).

Nokta ataması blok boyunca sabittir:

```
∀p, ∀s, ∀n :  x[p,s,n] ≥ z[p,s] + x[p,s−1,n] − 1
```

Bir personel çalışmaya devam ettiği sürece görev noktası değişmez. Gün içinde nokta değiştirmenin sahada karşılığı yoktur ve serbest bırakılması arama uzayını gereksiz genişletir.

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

Bir personel, üst üste tanımlı sayıdan fazla gece günü çalışamaz.

```
gece_saat[p,d] = Σ_{s ∈ gün d, s gece saati} z[p,s]
gece_gunu[p,d] = 1  eğer gece_saat[p,d] ≥ gece_esigi_saat
N = azami_ardisik_gece
∀p, ∀d :  Σ_{i=0..N} gece_gunu[p,d+i] ≤ N
```

Parametreler: azami_ardisik_gece, gece_esigi_saat. Pencere, ısıtma penceresini de kapsayacak şekilde değerlendirilir.

Kural önceki sürümlerde vardiya tipi üzerindeki gece bayrağına dayanıyordu. Blok kataloğu kaldırıldığı için işaretlenecek bir nesne kalmamıştır; bir günün gece günü sayılıp sayılmadığı, o gün gece saatlerinde geçirilen sürenin eşiğe ulaşıp ulaşmadığından hesaplanır. Eşik, ergonomik yorumu taşır: iki saat gece çalışmak bir gece nöbeti değildir.

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
G(p,d) = { s : p'nin d gününde başlayan bloğuna ait saatler }
         gece yarısını aşan blokta ertesi güne taşan saatler dahildir
∀p, ∀d :  Σ_{s ∈ G(p,d)} z[p,s] ≤ azami_gunluk_saat
```

Parametre: azami_gunluk_saat (varsayılan 11).

**"Gün d" takvim günü değil, bloğun başlangıç günüdür.** Sayım takvim günü üzerinden yapılsaydı gece yarısını aşan bir blok ikiye bölünür ve tavan hiç tetiklenmezdi: 20.00–08.00 arası on iki saatlik bir çalışma, takvim günü sayımında dört ve sekiz saat olarak görünür; ikisi de on bir saatin altında kalır ve on bir saatlik tavanı aşan blok sessizce geçer. Aynı bağ H1'in günde tek başlangıç kısıtı için de geçerlidir ve TD-1'in doğrudan sonucudur.

Kural, H1'in asgari süre koşuluyla birlikte çalışma bloğunun alt ve üst sınırını çizer: bir günlük çalışma dört saatten kısa, on bir saatten uzun olamaz.

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

**Ceza değişkenlerine üst sınır konulmaz.** Bir esnek hedefin sapma veya eksik değişkeni yukarıdan sınırlandığında, o hedef fiilen zorunlu kısıta dönüşür: sınırın yetmediği bir girdide model çözülemez döner. Bu, esnek hedef tanımının tam tersidir ve FR-5.2'yi ihlal eder — sistem çizelgeyi üretip açığı göstermek yerine reddetmiş olur.

Sınır makul göründüğünde bile konmaz. Bir sapma değişkeninin üst sınırının "bir kişinin fiilen taşıyabileceği yük" olarak belirlenmesi doğru görünür, fakat adil pay kadro yetersizken bu değeri aşabilir; o anda sapma tanımlanamaz hâle gelir ve çözücü çelişki bildirir. Bu hata bir kez yaşanmış ve çözücü–doğrulayıcı uyum testinin rastgele örneklerinden biri tarafından yakalanmıştır.

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
gece_yuku[p]  = Σ_{s ∈ ufuk, s gece saati} z[p,s]
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

Ölçünün birimi **saattir**. Blok süreleri çözümün çıktısı olduğundan sayıma dayalı bir ölçü tanımsızdır: on iki saat gece çalışan personel ile altı saat çalışan aynı sayılamaz. Gece saati, çalışmanın 20.00–06.00 aralığıyla kesişimidir (TD-2).

Aynı değişiklik S3 ve S4 için de geçerlidir; üç adalet hedefi de saat biriminde olduğundan `w2`, `w3` ve `w4` doğrudan karşılaştırılabilir. Önceki sürümde `w4`'ün diğerlerinin sekizde biri ölçeğinde tutulması gereğini doğuran birim farkı ortadan kalkmıştır.

Adalet, yükü paylaşabilecekler arasında paylaştırmaktır; paylaşamayan personel ölçümün dışındadır ve **kısmen paylaşabilen personel kendi payı kadar ölçülür.** Bu ayrım iki kez bedeli ödenmiş bir hatanın karşılığıdır: önce hiç gece alamayan personel paydada sayılıyordu, sonra kısıtlı erişimi olan havuz tek ortalamaya vuruluyordu. İkisinde de ölçü, hiçbir çizelgeyle kapatılamayan bir sapma raporluyor ve ayırt ediciliğini kaybediyordu.

Ölçüm ufku TD-6'da tanımlıdır.

### S3 — Hafta sonu adaleti

Kişi başına düşen hafta sonu ve resmî tatil **saatinin** hedeften sapması cezalandırılır. Formülasyon S2 ile aynıdır; gece saati yerine hafta sonu günlerindeki toplam süre kullanılır (TD-3) ve uygun havuz aynı mantıkla belirlenir.

```
hs_yuku[p] = Σ_{d: hs[d]=1} Σ_{s ∈ gün d} z[p,s]
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

**Sapma ölçüsü taban/tavan yöntemiyle kurulur.** Adil pay kesirli bir değerdir; sapma, payın tabanı ile tavanı arasındaki bant dışına çıkıldığında birikir:

```
∀p :  sapma[p] ≥ toplam_saat[p] − ⌊pay[p]⌋
      sapma[p] ≥ ⌈pay[p]⌉ − toplam_saat[p]
```

Bandın içindeki fark cezasızdır. Bu, S2 ve S3'ün zaten kullandığı yöntemdir; üç adalet hedefinin aynı biçimde ölçülmesi, birinin kesirli payı doğrudan kısıtlaması ve diğer ikisinin bant kullanmasından daha tutarlıdır. Kesirli payın modelde bölme kısıtı olarak kurulması ayrıca çözüm süresini belirgin biçimde artırmaktadır.

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
bas_saati[p,d] = blok başlangıcının gün içindeki saati (bas[p,s] = 1 olan s)
kayma[p,d] = dairesel_fark( bas_saati[p,d+1], bas_saati[p,d] )
           = min( |Δ|, 24 − |Δ| )
degisim[p,d] = 1  eğer p, d ve d+1 günlerinde çalışıyor ve
                  kayma[p,d] > desen_toleransi_saat
bina_degisim[p,d] = 1  eğer p, d ve d+1 günlerinde çalışıyor ve
                       atandığı noktaların binaları farklıysa
Ceza:  w6 · Σ degisim[p,d]  +  w6b · Σ bina_degisim[p,d]
```

Kural önceki sürümlerde "aynı vardiya tipi" üzerinden yazılıydı. Blok kataloğu kaldırıldığı için karşılaştırılacak bir tip kalmamıştır; ölçü, çözümün ürettiği **fiilî başlangıç saatidir**. Sekizde başlayıp on altıda biten bir gün ile sekizde başlayıp yirmide biten bir gün arasında kayma yoktur — ergonomik olarak da yoktur, kişi aynı saatte kalkar.

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
| FR-1.5 | Sistem, bina tanımlarının oluşturulmasına ve güncellenmesine imkân vermelidir. | Zorunlu |
| FR-1.6 | Sistem, görev noktalarının ad, bağlı olduğu bina ve ön koşul yetkinliğiyle tanımlanmasına imkân vermelidir. Bina alanı boş bırakıldığında nokta tesis geneli olarak değerlendirilir. | Zorunlu |
| FR-1.7 | Sistem, talep tanımının görev noktası, zaman aralığı ve gün tipi kırılımında yapılmasına ve tekil tarihler için istisna tanımlanmasına imkân vermelidir. | Zorunlu |
| FR-1.8 | Sistem, talep tanımlarını görev noktası ve gün tipi kırılımında, her kayıt bir zaman aralığı olacak biçimde göstermeli; aralıkların ve gereken sayıların doğrudan düzenlenmesine imkân vermelidir. Aynı nokta ve gün tipi için çakışan aralıklar tanımlanamaz. | Yüksek |
| FR-1.9 | Sistem, tanımlı talepten haftalık toplam kişi-saat yükünü ve kural parametreleri altındaki asgari kadro büyüklüğünü hesaplayarak göstermelidir. Hesap saat tabanlıdır; blok süreleri çözümün çıktısı olduğundan vardiya sayısı üzerinden bir karşılık gösterilmez. | Orta |
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
| FR-2.7 | Sistem, bir müsaitlik kaydına dayanak belge (rapor, izin yazısı) eklenmesine imkân vermelidir. Kayıtta belge bulunduğu listede görünür ve belge tek tıkla açılır. | Yüksek |
| FR-2.8 | Belgeye erişim, müsaitlik kaydını görebilen rollerle sınırlıdır ve her erişim kayda geçer. Çalışan yalnızca kendi kaydının belgesine erişebilir. | Zorunlu |



## 5.3 Tercih Yönetimi

| Kimlik | Gereksinim | Öncelik |
| --- | --- | --- |
| FR-3.1 | Sistem, personelin belirli bir günde çalışmama tercihini kaydetmesine imkân vermelidir. | Yüksek |
| FR-3.2 | Sistem, personelin tercih ettiği çalışma saati aralığını kaydetmesine imkân vermelidir. | Orta |
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
| FR-4.6 | Sistem, çözüm için üst zaman limiti tanımlanmasına imkân vermeli; limit dolduğunda o ana kadar bulunan en iyi çözümü döndürmelidir. Varsayılan değer **300 saniyedir**. | Yüksek |
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
| FR-6.1 | Sistem, taslak durumdaki bir çizelge üzerinde çalışma bloklarının doğrudan çizelge üzerinde oluşturulmasına, süresinin değiştirilmesine, kaldırılmasına ve başka bir personele taşınmasına imkân vermelidir. | Zorunlu |
| FR-6.2 | Sistem, her değişiklikten sonra tüm zorunlu kısıtları yeniden değerlendirmeli ve ihlal edilen kuralları listelemelidir. Değerlendirme, o ana kadar biriken bütün değişikliklerin birlikte uygulandığı durum üzerinden yapılır. | Zorunlu |
| FR-6.3 | Sistem, ihlal bildiriminde kuralın kimliğini, ilgili personeli, tarihi ve ihlalin gerekçesini anlaşılır bir cümleyle vermelidir. | Zorunlu |
| FR-6.4 | Sistem, değişikliğin sonucunu önce gündelik dille bildirmeli, sayısal ceza dökümünü isteğe bağlı ayrıntı olarak sunmalıdır. | Yüksek |
| FR-6.5 | Sistem, belirli blokların kilitlenmesine imkân vermeli; kilitli bloklar yeniden çözümde değiştirilmemelidir. | Zorunlu |
| FR-6.6 | Manuel doğrulama, çözücü modeliyle aynı kural tanımından beslenmelidir. | Zorunlu |
| FR-6.7 | Sistem, yapılan değişikliklerin sırayla geri alınmasına ve yeniden uygulanmasına imkân vermelidir. | Zorunlu |
| FR-6.8 | Değişiklikler çizelge sürümüne yalnızca kullanıcı kaydettiğinde yazılmalıdır. Kaydedilmeden bırakılan bir düzenleme oturumu sürümü değiştirmez; kullanıcı kaydedilmemiş değişikliklerle ekrandan ayrılmadan önce uyarılır. | Zorunlu |
| FR-6.9 | Yayınlanmış bir çizelge sürümü üzerinde değişiklik yapılamaz. Değişiklik gerektiğinde yayınlanmış sürümden yeni bir taslak türetilir (FR-7.3). | Zorunlu |

**Düzenleme çizelgenin üzerinde yapılır.** Blok, ızgarada sürükleyerek oluşturulur; kenarından tutularak uzatılır veya kısaltılır, gövdesinden tutularak gün içinde kaydırılır ya da başka bir personelin satırına taşınır. Ayrı bir form üzerinden saat girişi, tam değer yazmak isteyen kullanıcı için ikincil bir yol olarak bulunur; birincil yol değildir.

Değişiklik bırakıldığı anda ızgarada görünür. Zorunlu kısıt ihlali doğuran bir değişiklik **uygulanmaz**: blok eski hâline döner ve hangi kuralın neden bozulduğu bloğun yanında bildirilir. Esnek hedef etkisi değişikliği engellemez.

**Blok taşıma**, hedef personelin görev noktasının ön koşulunu taşımasını (H8) ve o saatlerde müsait olmasını (H7) gerektirir; taşıma bu iki kuralın ihlaline yol açıyorsa uygulanmaz.

### TD-16 — Taslak düzenleme oturumu

Düzenleme, sürüme her değişiklikte yazan bir işlem dizisi değil, **kaydedilene kadar biriken bir oturumdur**.

Değişiklikler istemcide tutulur ve ızgarada anında görünür; geri alma ve yeniden uygulama bu birikimi ileri geri sürer. Sunucuya yazma tek bir noktada olur: kullanıcı kaydettiğinde, biriken bütün değişiklikler tek işlemde uygulanır. Kaydedilmeden kapatılan bir oturum sürümü hiç değiştirmez.

**Doğrulama yine sunucuda kalır.** Her değişiklikte sunucuya bir doğrulama isteği gider ve istek, o ana kadar biriken değişikliklerin tamamını taşır; sunucu bunları sürümün üzerine düşünsel olarak uygular ve sonucu döndürür, hiçbir şey yazmaz. Kural değerlendirmesinin istemciye taşınması, kuralın ikinci bir yerde tanımlanması anlamına gelirdi — bu projede birkaç kez bedeli ödenmiş bir kalıptır (FR-6.6).

Değerlendirmenin biriken değişikliklerin **tamamı** üzerinden yapılması zorunludur. Tek tek değişiklikler ayrı ayrı geçerli olsa da birlikte bir kuralı bozabilirler: iki ayrı gün için yapılan iki değişiklik, tek başına haftalık tavanı aşmazken birlikte aşar.

Kaydetme, sürümün kullanıcı düzenlemeye başladığından beri değişmediğini doğrular. Değişmişse kayıt reddedilir ve kullanıcıya durum bildirilir; sessizce üzerine yazmak, başka bir kullanıcının işini iz bırakmadan yok eder.

### TD-17 — İzin belgesi sağlık verisidir

Müsaitlik kaydına eklenen belge çoğu zaman bir doktor raporudur. Bu, sıradan bir
ek dosya değil **özel nitelikli kişisel veridir**; tasarımı kolaylık değil erişim
sorusu belirler.

**Kim görür.** Belgeye erişim, müsaitlik kaydını zaten görebilen rollerle
sınırlıdır: idare ve üstü, bir de kaydın sahibi olan çalışan. Çalışan başkasının
belgesine erişemez. Erişim yetkisi hem uç noktada hem indirme yolunda denetlenir;
belgenin adresini bilmek erişim hakkı vermez.

**Her erişim kayda geçer.** Kimin hangi belgeye ne zaman eriştiği yazılır. Sağlık
verisinde "kim gördü" sorusunun yanıtsız kalması, verinin korunmadığı anlamına
gelir.

**Belge veritabanında saklanır**, dosya sisteminde değil. Gerekçe yedektir: sistem
yedeği veritabanı yedeğidir (SDD 3.4.5) ve dosyalar dışarıda tutulursa yedeğe
girmez, bir gün sessizce kaybolurlar. Kayıt silindiğinde belge de aynı işlemde
gider; yetim dosya kalmaz. Ölçek buna elverir — birkaç yüz belge, her biri birkaç
yüz kilobayt.

**Sınırlar.** Kayıt başına tek dosya, boyut tavanı ve tip beyaz listesi (PDF ve
yaygın görsel biçimleri). Sınırsız bırakılan bir yükleme yüzeyi, paylaşımlı
sunucuda diski dolduran ilk şeydir.

**Belge zorunlu değildir.** Müsaitlik kaydı belgesiz de girilebilir; belge bir
dayanaktır, ön koşul değil. Zorunlu tutulması, acil durumda kaydı girmeyi
engellerdi.

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
| FR-8.5 | Sistem, çizelgeyi hem makine okunur (CSV) hem insan okunur (Excel) biçimde dışa aktarabilmelidir. Excel çıktısı çizelgenin kendisini taşır: personel × gün düzeninde, hücrede çalışma saatleri ve görev noktası, saatin gün içindeki konumunu gösteren biçimlendirmeyle. | Zorunlu |
| FR-8.6 | Sistem, kural bazlı ihlal ve ceza dökümünü raporlamalıdır. | Yüksek |
| FR-8.7 | Sistem, çizelgenin kapsama açıklarını ayrı bir dosya olarak dışa aktarabilmelidir. Talep karşılama esnek hedef olarak tanımlandığından (S1) açıkları içermeyen bir çıktı çizelgeyi olduğundan tam gösterir. | Zorunlu |
| FR-8.8 | Sistem, çizelgenin yazdırılabilir bir görünümünü üretebilmelidir. Görünüm personel × gün matrisi biçiminde olmalı, başlığında dönem, sürüm ve üretim tarihi bulunmalı, kapsama açıkları tablonun altında listelenmelidir. | Yüksek |
| FR-8.9 | Sistem, analiz sonuçlarını tek bir dosyada dışa aktarabilmelidir. Dosya hem okunmaya hazır bir özet (tablolar ve grafikler) hem de üzerinde çalışılabilir ham veri içermelidir. | Yüksek |



## 5.9 Çalışan Paneli

| Kimlik | Gereksinim | Öncelik |
| --- | --- | --- |
| FR-9.1 | Sistem, personelin yalnızca kendi çizelgesini görüntülemesine imkân vermelidir. Hangi personelin verisinin gösterileceği yalnızca oturumdan belirlenir; istek içindeki hiçbir alan bu seçimi değiştiremez. | Zorunlu |
| FR-9.2 | Sistem, personele yalnızca yayınlanmış durumdaki çizelge sürümünü göstermelidir. | Zorunlu |
| FR-9.3 | Sistem, personelin çizelgesini dönem görünümünde (dönem uzunluğu ne ise o kadar) ve liste görünümünde sunmalı, sıradaki vardiyayı öne çıkarmalıdır. | Yüksek |
| FR-9.4 | Sistem, yayınlanmış çizelgede, aynı dönemde en son arşive alınmış sürüme göre değişen günleri işaretlemelidir. Değişim üç biçimde ayrışır: eklendi, kaldırıldı, değişti (çalışma saatleri veya görev noktası farklı). Dönemin ilk yayınında karşılaştırma tabanı bulunmadığından hiçbir gün işaretlenmez. | Yüksek |
| FR-9.5 | Sistem, personelin dönem içindeki gece, hafta sonu ve toplam saat sayısını ekip ortalamasıyla birlikte göstermelidir. | Orta |
| FR-9.6 | Sistem, personelin tercih bildirmesine ve bildirdiği tercihlerin durumunu görmesine imkân vermelidir. Bir personel bir gün için **tek tercih** bildirir: aynı güne ikinci bir bildirim, mevcut kayıt beklemedeyse onun üzerine yazar; kayıt onaylanmış veya reddedilmişse bildirim reddedilir ve kullanıcıya nedeni gösterilir. | Yüksek |

Günde tek tercih kuralı veritabanı düzeyinde de zorlanır; uygulama katmanındaki denetim tek başına bırakılmaz, çünkü iki yazma yolu vardır — çalışanın kendi bildirimi ve yöneticinin çalışan adına girişi. İkisi de aynı kısıta çarpar ve aynı yanıtı üretir.

Kararlanmış bir tercihin üzerine yazılmaması bilinçlidir: onay veya ret bir yöneticinin verdiği karardır ve çalışanın yeni bir bildirimiyle sessizce geçersizleşmesi, kararın hiç verilmemiş olmasıyla aynı sonucu doğurur.



## 5.10 Kimlik Doğrulama ve Yetkilendirme

Sistem bir kurum içi araçtır; kullanıcılar kendi kendilerine kayıt olmaz, hesapları yönetim tarafından oluşturulur. Bu nedenle sistemde kayıt ekranı bulunmaz, yalnızca giriş ekranı vardır.

**Dört** kullanıcı rolü tanımlıdır:

| Rol | Kapsam |
| --- | --- |
| Çalışan | Yalnızca kendi çizelgesini, dönem özetini ve tercihlerini görür ve yönetir (5.9). Tanım, çözüm ve yayın işlevlerine erişemez. |
| İdare | Vardiya yöneticisinin bütün işlevlerine erişir: tanımlar, talep, kural, çözüm, manuel düzenleme, sürüm yönetimi, analiz, müsaitlik ve dışa aktarma. **Kullanıcı hesaplarına erişemez** — hesap ekranı bu rol için hiç görünmez. |
| Hesap yöneticisi | İdarenin bütün yetkilerine ek olarak kullanıcı hesaplarını oluşturur, rolünü değiştirir, parolasını sıfırlar ve hesabı devre dışı bırakır. Sistem yöneticisi hesaplarına dokunamaz. |
| Sistem yöneticisi | Bütün yetkileri taşır; hesap yöneticisi hesaplarını da yönetir. **Kendi hesabını devre dışı bırakamaz veya rolünü düşüremez**, ve sistemde en az bir etkin sistem yöneticisi kalmak zorundadır. |

Roller kapsayıcıdır: sistem yöneticisi hesap yöneticisinin, hesap yöneticisi idarenin yetkilerini içerir. Çalışan rolü diğerlerinin alt kümesi değildir; kendi verisine erişim, personel kaydına bağlı ayrı bir yetkidir.

**İdare ile hesap yöneticisinin ayrılması** bilinçlidir. Vardiya planlamak ile hesap açmak farklı işlerdir ve farklı kişiler yapar: çizelgeyi kuran kişinin kullanıcı parolası sıfırlayabilmesi için bir neden yoktur. Önceki sürümlerde iki iş tek rolde birleşikti ve yönetici rolü, ihtiyaç duymadığı bir yetkiyi taşıyordu.

**Sistem yöneticisinin kendini kilitleyememesi** de bilinçlidir: son yetkili hesabın kapanması sistemi arayüzden onarılamaz hâle getirir ve kurtarma yalnızca veritabanına doğrudan erişimle mümkün olur. Kısıt, kendi hesabına ve son etkin sistem yöneticisine ayrı ayrı uygulanır — birincisi kazayı, ikincisi iki kişinin birbirini kapatmasını önler.

| Kimlik | Gereksinim | Öncelik |
| --- | --- | --- |
| FR-10.1 | Sistem, kullanıcı adı ve parola ile giriş yapılan tek bir giriş ekranı sunmalı, kayıt ekranı içermemelidir. | Zorunlu |
| FR-10.2 | Sistem, parolaları yalnızca özet (hash) biçiminde saklamalı, geri çevrilebilir hiçbir biçimde tutmamalıdır. | Zorunlu |
| FR-10.3 | Sistem, giriş yapan kullanıcı için sunucu tarafında bir oturum kaydı oluşturmalı; oturumun süresi dolduğunda veya çıkış yapıldığında oturum geçersiz hâle gelmelidir. | Zorunlu |
| FR-10.4 | Sistem, her isteğin yetkisini oturumdaki role göre sunucu tarafında denetlemelidir. Arayüzün bir işlevi gizlemesi yetkilendirme sayılmaz. | Zorunlu |
| FR-10.5 | Sistem, hesap yöneticisi ve sistem yöneticisi rollerindeki kullanıcının hesap oluşturmasına, rol atamasına, parola sıfırlamasına ve hesabı devre dışı bırakmasına imkân vermelidir. Hesap silme yerine devre dışı bırakma kullanılır. İdare rolü bu işlevlere erişemez. | Zorunlu |
| FR-10.12 | Sistem yöneticisi kendi hesabını devre dışı bırakamaz, silemez ve rolünü düşüremez; sistemde her zaman en az bir etkin sistem yöneticisi bulunmalıdır. Hesap yöneticisi, sistem yöneticisi rolündeki hesapları değiştiremez. | Zorunlu |
| FR-10.6 | Sistem, çalışan rolündeki her hesabı bir personel kaydına bağlamalıdır; bağlantısı olmayan bir çalışan hesabı oluşturulamaz. İdare, hesap yöneticisi ve sistem yöneticisi rolleri için personel bağlantısı isteğe bağlıdır — bu roller bir personel kaydına karşılık gelmeyebilir. Bir personelin birden fazla hesabı bulunamaz: iki hesap da yalnızca kendi verisini göreceğinden erişim açısından sakınca doğmaz, ancak parola sıfırlandığında hangi hesabın sıfırlandığı belirsizleşir. | Zorunlu |
| FR-10.7 | Sistem, hesap yönetimi tarafından oluşturulan veya sıfırlanan parolanın ilk girişte değiştirilmesini zorunlu tutmalıdır. | Zorunlu |
| FR-10.13 | Sistem, bir hesap oluşturulduğunda veya parolası sıfırlandığında geçici parolayı **yalnızca o anda ve bir kez** göstermelidir. Parola hiçbir yerde saklanmaz, listelenmez ve yeniden gösterilemez; kaybedilmesi hâlinde yeniden sıfırlanır. | Zorunlu |
| FR-10.8 | Sistem, ardışık başarısız giriş denemelerinde hesabı geçici olarak kilitlemeli ve kilit süresini bildirmelidir. Kilit bildirimi ile hesabın devre dışı olduğu bildirimi yalnızca parola doğru girildiğinde gösterilir; parolayı bilmeyen bir kullanıcı bu metinleri hiçbir kullanıcı adı için göremez. Aksi hâlde bildirim, hesabın var olup olmadığını ele veren bir sinyale dönüşür. | Yüksek |
| FR-10.9 | Sistem, başarılı ve başarısız giriş denemeleri ile hesap yönetimi işlemlerini zaman damgasıyla kaydetmelidir. | Orta |
| FR-10.10 | Sistem, ilk yönetim hesabının arayüz dışı bir kurulum adımıyla oluşturulmasına imkân vermelidir. | Zorunlu |
| FR-10.11 | Kullanıcı adları ASCII karakter kümesiyle sınırlandırılmalıdır. Türkçe karakterlerin küçültülmesi veritabanı ile uygulama katmanında farklı sonuç verebildiğinden, sınır olmadan açılan bir hesabın sahibi doğru parolayla dahi giriş yapamayabilir. | Zorunlu |



# 6. Kullanım Senaryoları

### KS-1 — Dönem çizelgesinin üretilmesi

Aktör: Vardiya Yöneticisi

Ön koşul: Personel, yetkinlik, görev noktası ve talep tanımları girilmiştir.

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
| Yönetici | Tanımlar | Personel, yetkinlik, görev noktası, talep tanımları, takvim, kural parametreleri, ağırlıklar |
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
sicil; ad; baslangic; bitis; gorev_noktasi; gece_saat; hafta_sonu_mu; sure_saat
```

Başlangıç ve bitiş tam ISO zaman damgasıdır, tarih ve saat metni değil. Gece
yarısını aşan bir bloğun bitişi ertesi güne düşer; ayrı bir tarih sütunuyla saat
metni bunu makineye söyleyemez ve blok iki gün arasında kaybolur. Bloğun hangi
güne sayıldığı (TD-1) başlangıç damgasından türetilir.

`gece_saat`, bloğun 20.00–06.00 aralığıyla kesişiminin uzunluğudur (TD-2); önceki
sürümlerdeki `gece_mi` bayrağının yerini alır ve çalışma zamanı saat düzeyinde
belirlendiği için ikili bir değer taşımaz.

Görev noktası sütunu, atamanın görev noktası kırılımında tutulmasından gelir (Yazılım Tasarım Dokümanı 4.2.4); noktası olmayan bir satır kaydın yalnızca bir bölümünü taşır.

Ayrı bir tarih sütunu **bulunmaz**; önceki sürümlerde satırların gün ekseninde okunmasını kolaylaştırmak için başa alınmıştı. Çalışma zamanı saat düzeyine geçtiğinde bu sütun bir belirsizlik kaynağına dönüştü: gece yarısını aşan bir blokta tarih hangi günü gösterirdi? Gün bilgisi artık başlangıç damgasından türetilir ve tek kaynaktan gelir.

**Kapsama açığı dışa aktarma (CSV):**

```
baslangic; bitis; gorev_noktasi; tur; kisi_sayisi
```

Başlangıç ve bitiş burada da tam ISO zaman damgasıdır. Kapsama açığı kaydı bugün
veritabanında tarih ve ofsetsiz saat olarak tutulmaktadır (SDD 4.2.4); bu
gösterimden ISO damgası kurmak, saklanmayan bir ofseti uydurmak anlamına gelir ve
gece yarısını aşan bir açık aralığı dosyada okunamaz kalır. Kaydın atama tablosuyla
aynı biçime (zaman damgası) taşınması gerekmektedir; Ürün Backlog'unda kayıtlıdır.

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

**Çizelge dışa aktarma (Excel):**

CSV makine okunur çıktıdır ve olduğu gibi kalır; Excel çıktısı insan okunur
olandır. İkisi birbirinin yerine geçmez — biri başka bir sisteme veri taşır,
diğeri masaya konur ve bakılır.

Dosya üç sayfa taşır:

| Sayfa | İçerik |
| --- | --- |
| Çizelge | Personel × gün. Hücrede çalışma saatleri ve görev noktası kısaltması; hücre dolgusu saatin gün içindeki konumunu gösterir (gece koyu, gündüz açık). Kapsama açığı bulunan günler işaretlidir |
| Özet | Personel başına toplam saat, gece saati, hafta sonu saati, fazla çalışma saati ve kalan yıllık kota |
| Ham veri | Blok başına bir satır, başlangıç ve bitiş tam ISO zaman damgasıyla — CSV çıktısının aynısı |

Başlık bölümünde dönem, sürüm numarası, üretim tarihi, kapsama oranı ve toplam
açık bulunur. Renklendirme tek başına bilgi taşımaz: saat aralığı hücrede metin
olarak da yazılıdır ve bir açıklama satırı dolgunun ne anlama geldiğini söyler.
Çıktının renksiz yazdırılması bilgi kaybettirmez.

**Analiz dışa aktarma (Excel):**

| Sayfa | İçerik |
| --- | --- |
| Özet | Kapsama oranı, toplam ceza ve hedef bazında ceza dökümü |
| Adalet | Personel başına gece saati, hafta sonu saati ve toplam saat; her biri için kişiye düşen adil pay ve sapma. Grafikler bu sayfada yer alır |
| Kapsama açıkları | Gün, saat aralığı, görev noktası, eksik kişi sayısı |
| Ham veri | Yukarıdaki tabloların biçimlendirilmemiş hâli |

Grafiklerin referans çizgisi kişiye düşen adil paydır, havuz ortalaması değil
(bölüm 4.3, S2). İki ölçü karışık uzunluklu bir çizelgede farklı sonuç verir ve
ortalamayı göstermek S2'nin açıkça reddettiği ölçüyü ekrana taşımak olur.

