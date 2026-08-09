**TED ÜNİVERSİTESİ**

**CMPE 399 — Yaz Stajı**

BOTAŞ Boru Hatları ile Petrol Taşıma A.Ş.

**VARDİYA ÇİZELGELEME KARAR DESTEK ARACI**

**Ürün Backlog'u ve Karar Günlüğü**

(Product Backlog and Decision Log)

**Ömer HARMANKAYA**

Endüstri Mühendisliği / Bilgisayar Mühendisliği

05.08.2026

Sürüm 1.0

# Revizyon Geçmişi

| Ad | Tarih | Değişiklik Nedeni | Sürüm |
| --- | --- | --- | --- |
| Ömer HARMANKAYA | 05.08.2026 | İlk sürüm — kapsam dışı maddeler, ertelenen özellikler ve karar günlüğü kayda alındı | 1.0 |
| Ömer HARMANKAYA | 08.08.2026 | T-06 (iptal gecikmesi) eklendi; dağıtım öncesi alınan kararlar karar günlüğüne işlendi | 1.1 |
| Ömer HARMANKAYA | 09.08.2026 | Arayüz turunda alınan beş karar (azami dönem, kural kaydı yetkisi, çoklu taslak, arşivden kopyalama, tanım pasifleştirme) karar günlüğüne işlendi | 1.2 |



# 1. Amaç ve Kullanım

Bu doküman, projenin ilk sürümüne alınmayan işlevleri ve alınmama gerekçelerini kayıt altına alır. Amacı iki yönlüdür. Birincisi kapsam korumasıdır: bir fikir reddedilmek yerine kaydedildiğinde, aynı tartışmanın geliştirme sırasında tekrar açılması ve kapsamın farkında olmadan genişlemesi engellenir. İkincisi izlenebilirliktir: staj sonunda hangi kararın hangi gerekçeyle alındığı bu dokümandan okunabilir.

Her maddede erteleme gerekçesinin yanında bir de gündeme gelme koşulu bulunur. Bir madde, koşulu gerçekleştiğinde otomatik olarak kapsama girmez; yalnızca yeniden değerlendirilmeye uygun hale gelir. Kapsam kararlarında Proje Tanım Dokümanı bölüm 4.1'deki ölçüt geçerlidir: bir iş bugün vardiya yöneticisi tarafından yapılıyorsa kapsam içindedir, insan kaynakları tarafından yapılıyorsa değildir.

Etki sütunu, maddenin hayata geçirilmesi durumunda sistemin kullanıcıya sağlayacağı faydayı; maliyet sütunu ise tahmini geliştirme yükünü ifade eder. İkisi birlikte önceliklendirme girdisi oluşturur.

# 2. Kalıcı Kapsam Dışı Maddeler

Aşağıdaki işlevler staj süresi boyunca gündeme alınmayacaktır. Bunlar ertelenmiş değil, projenin tanımı gereği dışarıda bırakılmış işlevlerdir.

| Kimlik | Madde | Gerekçe |
| --- | --- | --- |
| K-01 | İnsan kaynakları, bordro ve puantaj işlevleri | Vardiya yöneticisinin değil insan kaynaklarının işidir; kapsam ölçütünün dışında kalır |
| K-02 | İzin talebi ve onay iş akışı | İzinler sisteme veri olarak girilir; talep ve onay süreci insan kaynakları alanına aittir |
| K-03 | Vardiya takası ve değişim talebi iş akışı | Çizelge üretimi değil, yayınlanmış çizelge üzerinde çalışan-çalışan etkileşimidir |
| K-04 | Bildirim altyapısı (e-posta, anlık bildirim) | Çizelgeleme kararına katkısı yoktur; altyapı yükü faydasının üzerindedir |
| K-05 | Mobil uygulama geliştirme | Web arayüzü duyarlı tasarımla aynı ihtiyacı karşılar |
| K-06 | Kurum sistemlerine entegrasyon | Gerçek kurum verisine bağımlılık yaratır ve staj süresini aşar |
| K-07 | Gerçek kurum verisinin kullanımı | Proje bilinçli olarak veri bağımsız tasarlanmıştır; gösterim örnek veriyle yapılır |



# 3. Ertelenen İşlevsel Özellikler

Bu maddeler değerli bulunmuş ancak ilk sürüme alınmamıştır. Her biri, çekirdek işlev tamamlandıktan sonra sırasıyla değerlendirilebilir.

| Kimlik | Madde ve Gerekçe | Gündeme Gelme Koşulu | Etki / Maliyet |
| --- | --- | --- | --- |
| B-01 | Kümülatif adalet. Adalet hesapları şu anda yalnızca planlama dönemini kapsar (TD-6). Dönemler arası devreden gece ve hafta sonu dengesi hesaba katılmaz. Ertelenmesinin nedeni, en az iki yayınlanmış dönem birikmeden anlamlı sonuç vermemesidir. | İkinci dönem çizelgesi yayınlandıktan sonra | Yüksek / Orta |
| B-02 | Otomatik çakışma teşhisi. Çelişkili kural kümelerinde hangi kısıt alt kümesinin çözümü imkânsız kıldığının otomatik olarak bulunması (unsat core analizi). İlk sürümde bu ihtiyaç, çözüm öncesi ön kontrol katmanı ve S1'in esnek tanımıyla karşılanmaktadır. | Ön kontrol katmanının yetersiz kaldığı somut bir örnekle karşılaşıldığında | Orta / Yüksek |
| B-03 | Eş zamanlı düzenleme. Birden fazla yöneticinin aynı çizelge sürümü üzerinde aynı anda çalışabilmesi. Tek kullanıcı varsayımı gösterim için yeterlidir. | Sistemin birden fazla vardiya yöneticisi tarafından kullanılacağı kesinleştiğinde | Düşük / Yüksek |
| B-04 | Senaryo karşılaştırma. Aynı veri üzerinde farklı ağırlık setleriyle üretilen çizelgelerin yan yana değerlendirilmesi. Ağırlık ayarlama işlevi ilk sürümde vardır; eksik olan yalnızca karşılaştırmalı görünümdür. | Ağırlık ayarlamanın gerçek kullanımda sık tekrarlandığı gözlendiğinde | Orta / Düşük |
| B-05 | Çalışan paneli kimlik doğrulaması. İlk sürümde panel, kişiye özel bağlantı üzerinden erişilir. Kurumsal kimlik doğrulama beklentisi mentör görüşmesinde netleşecektir. | Mentör kimlik doğrulama gereksinimi bildirdiğinde | Orta / Orta |
| B-06 | Görev noktası adaleti. Aynı personelin dönem boyunca sürekli aynı noktada (örneğin kontrol odasında) görevlendirilmemesi. İlk sürümde adalet yalnızca gece, hafta sonu ve toplam saat eksenlerinde ölçülür. | Yetkinlik havuzları, aynı kişiyi aynı noktaya zorlamayacak kadar genişlediğinde | Orta / Düşük |
| B-07 | Yetkinlik seviyeleri. Yetkinlikler şu anda seviyesizdir (TD-9); personel bir yetkinliğe ya sahiptir ya değildir. Kıdem veya sertifika derecesi ayrımı yapılmaz. | Aynı görevde farklı yetki derecelerinin belirleyici olduğu bir kural ortaya çıktığında | Düşük / Orta |
| B-08 | Saat bazlı müsaitlik. Müsaitlik şu anda tam gün, öğleden önce ve öğleden sonra dilimleriyle tanımlanır (TD-4). Serbest saat aralığı desteklenmez. | Yarım gün çözünürlüğünün yetersiz kaldığı bir izin tipi ortaya çıktığında | Düşük / Orta |
| B-09 | Fazla mesai modellemesi. Haftalık saat tavanı ilk sürümde katı üst sınırdır. Tavanın üzerine ücretli fazla mesaiyle çıkılabilmesi modellenmemiştir. | Kadro analizinde tavanın altında çözüm bulunamadığı doğrulandığında | Yüksek / Orta |
| B-10 | İzin kotası ve eş zamanlı izin sınırı. Aynı dönemde izne çıkabilecek azami personel sayısının sınırlanması. İzinler şu anda sabit girdi olduğundan model bu kararı vermez. | İzin planlamasının da sisteme devredilmesi istendiğinde | Orta / Orta |
| B-11 | Gezici görev noktaları. Devriye gibi vardiya içinde yer değiştiren görevlerin modellenmesi. Mevcut uygulama alanında devriye görevi bulunmamaktadır. | Devriye veya benzeri bir görev tanımlandığında | Düşük / Yüksek |
| B-12 | Çoklu tesis desteği. Sistem şu anda tek tesis ve o tesise bağlı binalar üzerinden çalışır. Farklı tesislerin ayrı personel havuzlarıyla yönetilmesi desteklenmez. | İkinci bir tesisin sisteme dahil edilmesi gündeme geldiğinde | Orta / Orta |
| B-13 | Talep tahmini. Ziyaretçi yoğunluğu gibi değişkenlere göre kadro sayısının önerilmesi. Talep ilk sürümde tamamen kullanıcı tarafından tanımlanır. | Talep değişkenliğini gösteren geçmiş veri erişilebilir olduğunda | Düşük / Yüksek |
| B-14 | Ön kontrole beşinci bir kontrol: yetkinlik başına kayan haftalık pencere kapasitesi. Mevcut dört kontrol (SDD 5.2) dönem geneli veya gün bazında bakar; küçük bir yetkinlik havuzunun belirli bir haftada (örneğin eş zamanlı izin nedeniyle) yetersiz kalması, dönemin geri kalanındaki serbestlikle sayısal olarak örtülüp yakalanamayabilir. Sprint 2 Gün 7'de gerçek demo senaryosuyla gözlemlendi. | Ön kontrolün kaçırdığı bir açık, çözücü çalıştırılmadan önce sık tekrar ediyorsa | Orta / Orta |



# 4. Teknik İyileştirmeler

Bu maddeler kullanıcıya doğrudan yeni bir işlev sunmaz; çözüm kalitesini, performansı veya sürdürülebilirliği iyileştirir.

| Kimlik | Madde | Gündeme Gelme Koşulu |
| --- | --- | --- |
| T-01 | Simetri kırma kısıtları. Birbirinin yerine geçebilen personel arasındaki eşdeğer çözümlerin elenmesiyle arama uzayının daraltılması. | Çözüm süresi kabul kriterine yaklaştığında |
| T-02 | Sıcak başlangıç. Önceki çözümün çözücüye başlangıç ipucu olarak verilmesi; özellikle yeniden çözme senaryosunda süreyi kısaltır. | Yeniden çözme süresi ilk çözümü aştığında |
| T-03 | Çoklu çözüm sunumu. Aynı ceza seviyesinde birden fazla alternatif çizelgenin üretilip kullanıcıya seçtirilmesi. | Çözüm süresi tek çözüm için kriterin belirgin altında kaldığında |
| T-04 | Ağırlık kalibrasyon önerisi. Kullanıcının seçtiği ağırlıkların sonuç üzerindeki etkisinin duyarlılık analiziyle raporlanması. | Ağırlık ayarlamanın deneme yanılmaya dönüştüğü gözlendiğinde |
| T-05 | Kural kataloğu şema doğrulaması. Katalog verisinin biçimsel şemayla doğrulanması ve hatalı tanımların çözücüye ulaşmadan yakalanması. | Kataloğa üçüncü bir yorumlayıcı eklendiğinde |
| T-06 | İptal gecikmesinin giderilmesi. İptal isteği şu anda ara çözüm geri çağırması içinde okunur; geri çağırma yalnızca daha iyi bir çözüm bulunduğunda tetiklendiğinden istek iki iyileşme arasında bekleyebilir (SDD 5.4). Öneri: çözüm çağrısı işçi içinde ayrı bir iş parçacığında yürütülür, ana döngü iş durumunu düzenli aralıklarla yoklar ve çözücünün aramayı dışarıdan sonlandıran çağrısını kullanır. Kütüphane sürümünde bu çağrının davranışı önce doğrulanmalıdır. | Kullanıcı iptalin geç yanıt verdiğini gerçek kullanımda bildirdiğinde |



# 5. Karar Günlüğü

Aşağıdaki tablo, tasarım sürecinde alınan ve sonradan değiştirilen kararları gerekçeleriyle birlikte kaydeder. Bir kararın değişmiş olması hata anlamına gelmez; bilginin netleşmesiyle tasarımın güncellenmesi beklenen bir davranıştır.

| Tarih | Karar | Gerekçe |
| --- | --- | --- |
| 05.08.2026 | Talep karşılama zorunlu kısıt değil, baskın ağırlıklı esnek hedef olarak tanımlandı | Personel yetersiz olduğunda çözümü reddetmek yerine açığı göstermek, aracın temel ayırt edici işlevidir |
| 05.08.2026 | Uygulama alanı tüm istasyon personelinden güvenlik personeline daraltıldı | Mentör yönlendirmesi. Model yapısı değişmedi; yalnızca alan sözlüğü ve talep değerleri belirlendi |
| 05.08.2026 | Silahlı görevlilik ayrı bir yetkinlik olmaktan çıkarıldı | Tüm güvenlik personeli silahlı olduğundan ayırt edici değeri yoktur; modelde ölü ağırlık oluşturur |
| 05.08.2026 | Kontrol odası operatörlüğü ayrı bir yetkinlik olmaktan çıkarıldı | Kontrol odasında görevli personel ayrı bir meslek grubu değil, farklı bir noktada bulunan güvenlik görevlisidir |
| 05.08.2026 | Görev noktası, karar değişkenine ayrı bir boyut olarak eklendi | Yetkinlik gereksiniminin vardiya düzeyinde sayılması, çoklu yetkinlik taşıyan personelin tek atamayla birden çok gereksinimi karşılıyor görünmesine yol açıyordu |
| 05.08.2026 | Bina, karar değişkeninin boyutu olmaktan çıkarılıp görev noktasının niteliği haline getirildi | Vardiya şefliğinin iki bina için ortak, kontrol odasının ise tek binada olması bina eksenini simetrik olmaktan çıkardı |
| 05.08.2026 | Asgari dinlenme süresi 11 saatten 16 saate çıkarıldı | İki çalışılan vardiya arasında en az iki boş vardiya bulunması gereksiniminin saat cinsinden karşılığıdır |
| 05.08.2026 | Talep sayıları üst sınır olarak zorunlu, alt sınır olarak esnek tanımlandı | Fazla personel atanmasını engellerken kapsama açığının raporlanabilmesini korur |
| 05.08.2026 | Vardiya rotasyonu genel bir anahtar yerine personel bazlı isteğe bağlı alan olarak tasarlandı | Gerçek kullanımda çoğu personelin döndüğü, bir bölümünün sabit vardiyada çalıştığı karma düzen yaygındır; tek anahtar bunu ifade edemez |
| 06.08.2026 | S6, S6 (vardiya deseni tutarlılığı, ağırlık 10) ve S6b (bina tutarlılığı, ağırlık 6) olarak ikiye bölündü | SRS formülü w6 ve w6b olmak üzere iki ayrı ağırlık kullanıyordu; kural tablosunda kural başına tek ağırlık sütunu var, iki ayrı kayıt şemaya dokunmadan çözer |
| 06.08.2026 | SDD 5.2 Kontrol 2 (yetkinlik havuzu) sözde kodu bireysel izni hesaba katacak şekilde düzeltildi | Orijinal sözde kod Kontrol 1'in aksine musait_gun'u hiç çıkarmıyordu; gerçek demo senaryosuyla test edilirken fark edildi. Düzeltme bile bu senaryodaki zaman-pencereli (haftalık) açığı yakalamıyor — bkz. B-14 ve SDD 5.2'deki yeni sınır açıklaması |
| 07.08.2026 | Kapı ve kontrol odası görev noktaları tek bir "Güvenlik" noktasında birleştirildi, bina ayrımı kaldırıldı; müracaat noktası da bina ayrımı olmadan tanımlandı | Kontrol odası zaten ayrı bir yetkinlik değildi (aynı Güvenlik Görevi havuzu); atamanın hangi fiziksel noktaya yazıldığı modelin ihtiyaç duyduğu bir bilgi değil, kim nerede duracağını vardiya şefi belirliyor. Altı nokta üçe indi, toplam kadro sayıları (36 kişi, 7/6/23 havuz) değişmedi |
| 07.08.2026 | Planlama dönemi varsayılanı yirmi sekiz günden bir haftaya düşürüldü, kullanıcı manuel büyütebilir | Gerçek kullanımda haftalık planlama daha tipik; yirmi sekiz günlük ölçek performans kabul kriterinde kasıtlı bir stres testi olarak korundu, sistemin daha büyük dönemleri desteklemesi gerekliliği değişmedi |
| 08.08.2026 | S2 ve S3'ün paydası uygun havuza çevrildi; havuz hesabı tek bir yerde tutuluyor ve dört tüketici (model kurma, doğrulama, analiz servisi, ölçüm betiği) oradan alıyor | Yetkinliği gereği gece talebi bulunan hiçbir noktada çalışamayan personel paydaya girdiğinde hedef ulaşılamaz hâle geliyordu. Tanımın tüketicilerde tekrarlanması hâlinde ölçüm aracı, doğruladığı ölçütün tanımını kendisi taşıdığı için sessizce yanlış bir sonuç üretebilir |
| 08.08.2026 | Çözüm işi, uygulama sürecinden açılan çocuk süreç olmaktan çıkarılıp bağımsız bir sistem servisine taşındı | Sprint 2'deki çocuk süreç çözümü bilinçli bir ara adımdı; SDD 3.4.4 çözüm işinin ayrı bir servis olmasını ve süreçler arası iletişimin yalnızca veritabanı üzerinden kurulmasını tanımlıyor |
| 08.08.2026 | Yürütme kipi için yapılandırma anahtarı (gömülü / servis) konmadı; tek yol bırakıldı ve eski davranışa dayanan testler işçinin tek adımını doğrudan çağıracak biçimde yeniden yazıldı | İki yürütme kipi, aynı davranışın iki yerde tanımlanması demektir; bu proje aynı kalıptan daha önce birkaç kez zarar görmüştür. Ayrıca yerel geliştirmenin gösterim ortamıyla aynı yolu kullanması sürüm eşliğini güçlendirir |
| 08.08.2026 | Çözümün durdurulması ayrı bir bayrak alanı yerine iş kaydının `iptal` durumu üzerinden yürütüldü | Durum alanı bu bilgiyi zaten taşıyor; ikinci bir alan aynı bilginin iki kaynağa ayrışması riskini doğururdu |
| 08.08.2026 | Zaman damgası sütunları saat dilimli tipe geçirildi; mevcut veri UTC olarak yorumlandı | Uygulama zaten UTC yazıyordu ve arayüz bunu elle telafi ediyordu. Dönüşümde saat dilimi açıkça belirtilmezse veritabanı sunucunun yerel dilimini varsayar ve veriyi sessizce kaydırır |
| 09.08.2026 | Azami planlama dönemi otuz bir gün olarak sınırlandı | Çözüm süresi dönem uzunluğuyla hızla büyür; sınır konmadığında kullanıcı hiçbir uyarı almadan saatlerce sürecek bir iş başlatabilir. Otuz bir gün, yirmi sekiz günlük kabul kriteri ölçeğini kapsar |
| 09.08.2026 | Kullanıcının arayüzden kural kaydı oluşturması ve silmesi kapsam dışı bırakıldı; yetkisi parametre, ağırlık ve aktiflikle sınırlandı | Kural tablosundaki her satır kayıt defterindeki bir sınıfla eşleşmek zorundadır (SDD 3.2.1); sınıfı olmayan bir satır zaten yüklenemez. Kullanıcının ekleyebileceği bir kural bu mimaride oluşamaz, dolayısıyla ekleme ve silme arayüzü var olmayan bir yetkiyi vaat ederdi |
| 09.08.2026 | Aynı dönemde birden fazla taslağın bir arada bulunmasına izin verildi | TD-8'deki sürüm durum makinesi taslak sayısına sınır koymaz ve her çözüm başlatma zaten yeni bir taslak açar; sınır getirmek mevcut davranışı bozardı |
| 09.08.2026 | Arşivlenmiş sürüm geri döndürülmek yerine yeni taslağa kopyalanır | Yayınlanmış ve arşivlenmiş sürüm tarihsel kayıttır. Durumunun geri alınması, çalışan panelindeki "en son arşiv" karşılaştırma tabanını ve iki sürüm arasındaki karşılaştırmayı dayanaksız bırakır |
| 09.08.2026 | Kullanımda olan bir tanım silinmez, pasifleştirilir | Atamalarda kullanılan bir tanımın gerçekten silinmesi geçmiş çizelgeleri okunamaz hâle getirir. Hiçbir yerde kullanılmayan tanım için gerçek silme korunmuştur |



# 6. Mentör Görüşmesine Bağlı Maddeler

Aşağıdaki maddeler backlog'da değil, karar bekleyen konumdadır. Mentör görüşmesi sonrasında ya kapsama alınacak ya backlog'a taşınacaktır.

- Vardiya yapısının 3x8 mi yoksa 12/24 gibi bir düzen mi olduğu

- Ardışık gece sınırı, asgari dinlenme süresi ve haftalık saat tavanının kurumda uygulanan gerçek değerleri

- Vardiya şefi havuzunun büyüklüğü ve izin dönemlerinde nasıl yönetildiği

- Gece ve hafta sonu kadro azaltmasının tanımlanan biçimde yapılıp yapılmadığı

- Personelin sabit vardiyada mı çalıştığı yoksa rotasyon mu uygulandığı

- Planlama döneminin bir haftalık varsayılanı yeterli mi, yoksa kurumda tipik olarak daha uzun bir ufuk mu kullanılıyor

- Çalışan paneli için kimlik doğrulama beklentisi
