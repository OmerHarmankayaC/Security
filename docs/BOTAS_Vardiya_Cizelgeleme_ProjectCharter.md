**TED ÜNİVERSİTESİ**

**CMPE 399 — Yaz Stajı**

BOTAŞ Boru Hatları ile Petrol Taşıma A.Ş.

**VARDİYA ÇİZELGELEME KARAR DESTEK ARACI**

Kısıt Programlama Tabanlı Personel Çizelgeleme Sistemi

**Proje Tanım Dokümanı (Project Charter)**

**Ömer HARMANKAYA**

Endüstri Mühendisliği / Bilgisayar Mühendisliği

05.08.2026

Kurum Mentörü: ____________________

# Revizyon Geçmişi

| Ad | Tarih | Değişiklik Nedeni | Sürüm |
| --- | --- | --- | --- |
| Ömer HARMANKAYA | 05.08.2026 | İlk sürüm — kapsam, hedefler ve ön plan tanımlandı | 1.0 |
| Ömer HARMANKAYA | 05.08.2026 | Uygulama alanı güvenlik personeline daraltıldı; görev noktası yapısı, yetkinlik tanımları ve talep matrisi eklendi | 1.1 |
| Ömer HARMANKAYA | 09.08.2026 | Kimlik doğrulama kapsama alındı: harici kimlik servisi maddesi kurumsal dizin entegrasyonu olarak yeniden yazıldı ve açık soru güncellendi | 1.2 |
| Ömer HARMANKAYA | 13.08.2026 | Gece adaleti kabul kriteri (K3) saatlik çalışma düzenine uyarlandı: ölçünün birimi vardiya sayısından gece saatine döndüğü için eşik bir gece bloğu uzunluğu olarak yeniden yazıldı | 1.3 |



# 1. Giriş

Vardiya Çizelgeleme Karar Destek Aracı, kesintisiz çalışan tesislerde vardiya planlamasını üstlenen web tabanlı bir sistemdir. Proje, CMPE 399 yaz stajı kapsamında BOTAŞ bünyesinde yürütülmektedir. Bugün büyük ölçüde elle ve elektronik tablolar üzerinde yapılan çizelgeleme işi, sistemde bir kısıt programlama problemi olarak modellenmekte; ihlal edilemeyecek kurallar zorunlu kısıt, adalet ve tercihler ise ceza puanı üreten esnek hedefler olarak tanımlanmaktadır.

Sistem genel amaçlı bir çizelgeleme aracı olarak tasarlanmakta, ilk uygulama alanı olarak BOTAŞ tesislerinin güvenlik personeli seçilmektedir. Bu daraltma modelin yapısını değiştirmemekte; yalnızca görev noktalarının, yetkinliklerin ve talep sayılarının somut değerlerini belirlemektedir. Söz konusu değerlerin tamamı sistem üzerinden düzenlenebilir veri olarak tutulduğundan, aracın başka bir personel grubuna uygulanması yapılandırma değişikliğinden ibarettir.

Proje, gereksinimlerin geliştirme sırasında netleşeceği varsayımıyla çevik bir yaklaşımla, üç sprint halinde yürütülecektir. Temel çıktılar bu proje tanım dokümanı, kural kataloğu, matematiksel model dokümanı, çalışan bir web uygulaması, deney raporu ve staj raporudur. Kilometre taşları, kural kataloğunun onaylanmasından çözücünün ilk geçerli çizelgeyi üretmesine ve son teknik sunuma kadar yazılım geliştirme yaşam döngüsü etrafında yapılandırılmıştır.

# 2. Proje Tanımı

## 2.1 Genel Bakış

BOTAŞ tesislerinde güvenlik hizmeti kesintisiz yürütülmekte; her vardiyada belirli görev noktalarında, belirli sayıda ve belirli niteliklerde personelin bulunması gerekmektedir. Bu ihtiyaç kâğıt üzerinde basit görünse de pratikte iç içe geçmiş kısıtlar üretmektedir. Gece vardiyasından çıkan personele ertesi sabah görev verilememekte, üst üste belirli sayıdan fazla gece tutulamamakta, haftalık çalışma saatlerinin yasal bir tavanı bulunmakta, izinler ve raporlar takvimden insan çıkarmakta, bazı görevler yalnızca belirli yetkinliğe sahip kişiler tarafından yapılabilmektedir. Bütün bunlar sağlandıktan sonra bir de adalet meselesi kalmakta; gece ve hafta sonu nöbetlerinin sürekli aynı kişilere düşmesi çizelgeyi teknik olarak geçerli ancak pratikte kabul edilemez kılmaktadır.

Sistemin girdisi personel listesi, yetkinlikler, izin ve müsaitlik bilgileri, her vardiya için gereken personel sayısı ve kurumun uymak zorunda olduğu çalışma kurallarından oluşmaktadır. Çıktısı ise bütün zorunlu kuralları sağlayan, yükü çalışanlar arasında olabildiğince dengeli dağıtan ve tercihleri mümkün olduğunca gözeten bir dönemlik çizelgedir.

Uygulama iki katmandan oluşmaktadır. Alt katmanda personel, vardiya tipleri, yetkinlikler, izinler ve kural tanımlarının yönetildiği veritabanı ve arayüz yer almakta; bu katman çözücüden bağımsız olarak da çalışan bir yönetim aracı niteliği taşımaktadır. Üst katmanda ise çizelgeyi üreten çözücü ve sonuçları değerlendiren analiz bileşeni bulunmaktadır.

Projenin kapsamı bilinçli olarak sınırlı tutulmuştur. Sistem, halihazırda o işi yapan vardiya yöneticisinin işini devralmayı hedeflemekte; insan kaynakları veya bordro işlevlerini kapsamamaktadır. Bir işlevin kapsama girip girmediği bu ölçütle belirlenmektedir. Sistem ayrıca kurumdan herhangi bir gerçek veriye ihtiyaç duymamakta; personel ve kural tanımları uygulama içinden oluşturulabildiği için ilk günden itibaren bağımsız olarak geliştirilebilmekte ve gösterilebilmektedir.

## 2.2 Hedefler

| Hedef | Hedefin Kısa Açıklaması |
| --- | --- |
| Tanım Yönetimi | Personel, yetkinlik, vardiya tipi, talep, izin ve kural tanımlarının sistem üzerinden yönetilmesi. |
| Çizelge Üretimi | Tanımlı kuralların tamamına uyan dönemlik vardiya çizelgesinin otomatik olarak üretilmesi. |
| Fizibilite Geri Bildirimi | Personelin yetersiz kaldığı durumlarda çözümü reddetmek yerine eksiğin nerede olduğunun gösterilmesi. |
| Manuel Müdahale ve Anlık Doğrulama | Yöneticinin çizelge üzerinde elle değişiklik yapabilmesi ve her değişiklikte bozulan kuralın anında bildirilmesi. |
| Değişim Odaklı Yeniden Çözme | Yeni bir izin bilgisi geldiğinde planın sıfırdan kurulması yerine en az sayıda değişiklikle güncellenmesi. |
| Yük Dengesi ve Adalet | Gece ve hafta sonu yükünün çalışanlar arasında dengeli dağıtılması ve bu dengenin ölçülmesi. |
| Tercih Yönetimi | Personel tercihlerinin toplanması, onaylanması ve modele esnek hedef olarak dahil edilmesi. |
| Analiz ve Raporlama | Kapsama, denge ve tercih karşılama ölçütlerinin ve ceza dökümünün raporlanması. |
| Çalışan Görünürlüğü | Personelin kendi çizelgesini görüntülemesi ve tercihlerini bildirmesi. |



### Tanım Yönetimi

**Üst Düzey Fonksiyonel Gereksinimler**

- Sistem, personel kayıtlarının yetkinlik, sözleşme tipi ve dönem içinde aktif olduğu tarih aralığı bilgileriyle tanımlanmasına imkân vermelidir.

- Sistem, vardiya tiplerinin ad, başlangıç saati, bitiş saati ve süre bilgileriyle tanımlanmasına imkân vermelidir.

- Sistem, her vardiya için gereken personel sayısının ve yetkinlik dağılımının gün tipine göre tanımlanmasına imkân vermelidir.

- Sistem, izin, rapor ve eğitim kayıtlarının elle veya toplu içe aktarma yoluyla girilmesine imkân vermelidir.

- Sistem, zorunlu kural parametrelerinin ve esnek hedef ağırlıklarının kullanıcı tarafından değiştirilmesine imkân vermelidir.

**Önemli Fonksiyonel Olmayan Gereksinimler**

- Kural tanımları veri olarak saklanmalı, uygulama koduna gömülmemelidir.

- Kurallar vardiya adına değil saate göre ifade edilmeli; vardiya yapısı değiştiğinde (3x8, 2x12) kod değişikliği gerekmemelidir.

### Çizelge Üretimi

**Üst Düzey Fonksiyonel Gereksinimler**

- Sistem, belirtilen dönem için kısıt programlama modeli kullanarak vardiya çizelgesi üretmelidir.

- Sistem, asgari dinlenme süresi, ardışık gece sınırı, ardışık çalışma günü sınırı, haftalık saat tavanı, haftalık asgari izin, müsaitlik ve yetkinlik eşleşmesi kısıtlarını ihlal etmeyen çizelge üretmelidir.

- Sistem, esnek hedeflerin toplam ceza puanını en aza indiren çözümü aramalıdır.

- Sistem, planlama ufkunun kullanıcı tarafından seçilmesine imkân vermeli, varsayılan olarak dört haftalık dönem hesaplamalıdır.

**Önemli Fonksiyonel Olmayan Gereksinimler**

- Kırk personel ve yirmi sekiz günlük referans örnek (varsayılan bir haftalık dönemden büyük, kasıtlı bir stres testi ölçeği) altmış saniyenin altında çözülmelidir.

- Çözüm için üst zaman limiti tanımlanabilmelidir.

### Fizibilite Geri Bildirimi

**Üst Düzey Fonksiyonel Gereksinimler**

- Sistem, izin girişi sırasında ilgili günlerde kapsama açığı oluşacaksa kullanıcıyı uyarmalıdır.

- Sistem, personelin fiziken yetersiz olduğu durumda çözümü reddetmek yerine çizelgeyi üretmeli ve eksik kalan vardiyaları göstermelidir.

- Sistem, eksik kapsamayı gün, vardiya ve eksik kişi sayısı düzeyinde raporlamalıdır.

**Önemli Fonksiyonel Olmayan Gereksinimler**

- Uyarı ve hata mesajları teknik terim içermemeli, operasyon diliyle ifade edilmelidir.

### Manuel Müdahale ve Anlık Doğrulama

**Üst Düzey Fonksiyonel Gereksinimler**

- Sistem, üretilen çizelge üzerinde atamaların elle değiştirilmesine imkân vermelidir.

- Sistem, her manuel değişiklikte ihlal edilen kuralı ve ihlalin gerekçesini bildirmelidir.

- Sistem, belirli atamaların kilitlenerek yeniden çözümde korunmasına imkân vermelidir.

**Önemli Fonksiyonel Olmayan Gereksinimler**

- Kural ihlali bildirimi bir saniyenin altında görüntülenmelidir.

- Manuel doğrulama, çözücüyle aynı kural tanımından beslenmelidir.

### Değişim Odaklı Yeniden Çözme

**Üst Düzey Fonksiyonel Gereksinimler**

- Sistem, çizelge yayınlandıktan sonra değişiklik gerektiğinde önceki çizelgeden sapmayı cezalandırarak yeniden çözüm üretmelidir.

- Sistem, yeniden çözüm sonucunda değişen atama sayısını raporlamalıdır.

- Sistem, aynı döneme ait birden fazla çizelge sürümünü saklamalı ve karşılaştırmalıdır.

**Önemli Fonksiyonel Olmayan Gereksinimler**

- Yeniden çözüm süresi ilk çözüm süresini aşmamalıdır.

### Yük Dengesi ve Adalet

**Üst Düzey Fonksiyonel Gereksinimler**

- Sistem, kişi başına düşen gece ve hafta sonu vardiyası sayısının hedeften sapmasını cezalandırmalıdır.

- Sistem, kişi başına toplam çalışma saatinin ortalamadan sapmasını cezalandırmalıdır.

- Sistem, adalet hedeflerinin ağırlıklarının kullanıcı tarafından ayarlanmasına imkân vermelidir.

**Önemli Fonksiyonel Olmayan Gereksinimler**

- Kişi başına düşen gece yükü, kişiye düşen adil paydan en fazla bir gece bloğu kadar sapmalıdır.

- Sistem, hangi hedefin daha öncelikli olduğuna kendisi karar vermemeli; bu tercihi kullanıcıdan parametre olarak almalıdır.

### Tercih Yönetimi

**Üst Düzey Fonksiyonel Gereksinimler**

- Sistem, personelin belirli günlerde çalışmama veya belirli vardiya tipini tercih etme isteklerini kaydetmelidir.

- Sistem, tercihlerin yönetici tarafından onaylanmasına veya reddedilmesine imkân vermelidir.

- Sistem, onaylanmış tercihleri modele esnek hedef olarak dahil etmelidir.

- Sistem, onaylanan bir tercihin çizelgede karşılanıp karşılanmadığını onay durumundan ayrı olarak göstermelidir.

**Önemli Fonksiyonel Olmayan Gereksinimler**

- Tercih bildirimi için dönem bazlı son bildirim tarihi tanımlanabilmelidir.

### Analiz ve Raporlama

**Üst Düzey Fonksiyonel Gereksinimler**

- Sistem, kapsama oranını, kişi başına gece ve hafta sonu sayılarını, iş yükü dengesini ve tercih karşılama oranını raporlamalıdır.

- Sistem, toplam ceza puanını hedef bazında ayrıştırarak göstermelidir.

- Sistem, çizelgenin CSV veya Excel formatında dışa aktarılmasına imkân vermelidir.

**Önemli Fonksiyonel Olmayan Gereksinimler**

- Raporlar çözüm tamamlandıktan sonra ek işlem gerektirmeden görüntülenebilmelidir.

- Ceza dökümü, çözücünün neden bu çizelgeyi seçtiğini kullanıcıya açıklayacak ayrıntıda olmalıdır.

### Çalışan Görünürlüğü

**Üst Düzey Fonksiyonel Gereksinimler**

- Sistem, personelin yalnızca kendi çizelgesini görüntülemesine imkân vermelidir.

- Sistem, personele yalnızca yayınlanmış çizelge sürümünü göstermelidir.

- Sistem, yeni yayınlanan sürümde değişen günleri işaretlemelidir.

- Sistem, personelin dönem içindeki gece, hafta sonu ve toplam saat sayısını ekip ortalamasıyla birlikte göstermelidir.

**Önemli Fonksiyonel Olmayan Gereksinimler**

- Çalışan arayüzü mobil cihazlarda kullanılabilir olmalıdır.

## 2.3 Hedef Kullanıcılar

**Vardiya Yöneticisi (birincil kullanıcı):**

Çizelgeyi kuran ve uygulanmasından sorumlu olan kişidir. Sistemden beklentileri:

- Personel, yetkinlik, vardiya ve kural tanımlarını yönetmek

- Dönemlik çizelgeyi tek işlemle üretmek

- Personel yetersizliğini çizelge kurulmadan önce görmek

- Çizelge üzerinde elle değişiklik yapmak ve sonucunu anında doğrulamak

- Yeni bir izin bilgisi geldiğinde planı sınırlı değişiklikle güncellemek

- Yük dağılımının dengeli olduğunu sayısal olarak gösterebilmek

**Personel:**

Çizelgeye tabi olan çalışanlardır. Sistemden beklentileri:

- Kendi vardiyalarını güncel ve doğru biçimde görmek

- Yayın sonrası değişen günleri fark etmek

- Çalışmak istemediği günleri tercih olarak bildirmek

- Kendi yükünü ekip ortalamasıyla karşılaştırabilmek

**Birim / Operasyon Yöneticisi:**

Çizelgeyi kendisi kurmayan ancak sonucunu denetleyen kişidir. Sistemden beklentileri:

- Kapsama oranını ve eksik kalan vardiyaları görmek

- Yasal kurallara uyumun sağlandığını denetlemek

- Yük dağılımına ilişkin dönemlik raporlara erişmek

**Sistemin sunduğu hizmetler:**

- Tanım yönetimi: personel, yetkinlik, vardiya tipi, talep matrisi, izin ve kural tanımları

- Otomatik çizelge üretimi: kısıt programlama modeliyle dönemlik çizelge

- Fizibilite geri bildirimi: izin girişinde kapsama uyarısı ve eksik kapsama raporu

- Manuel düzenleme: atama değiştirme, kilitleme ve anlık kural doğrulaması

- Yeniden çözme: değişikliği en aza indirerek güncelleme ve sürüm karşılaştırma

- Analiz: kapsama, denge, tercih karşılama ölçütleri ve ceza dökümü

- Çalışan paneli: kişisel çizelge görüntüleme ve tercih bildirimi

- Dışa aktarım: çizelgenin CSV veya Excel formatında alınması

**Sistemin etkileşebileceği bileşenler:**

- İzin ve müsaitlik verisinin dosya yoluyla toplu içe aktarımı

- Kurumsal kimlik sağlayıcı (LDAP, Active Directory veya tek oturum açma). Sistem kendi kullanıcı hesaplarını ve oturumlarını yönetir; kurum dizinine bağlanma kapsam dışıdır (Ürün Backlog'u B-15)

## 2.4 Değer Önerisi

Projenin amacı, kesintisiz çalışan tesislerde vardiya planlamasının yarattığı karmaşıklığa uygulanabilir bir çözüm getirmektir. Bugün elektronik tablolar üzerinde saatler süren bu iş, sistemde dakikalar mertebesinde tamamlanmaktadır. Kazanılan süre, vardiya yöneticisinin asıl işine ayırabileceği zamana dönüşmektedir.

Uyum açısından sistem, üretilen çizelgenin yasal ve operasyonel kuralları ihlal etmediğini garanti etmektedir. Asgari dinlenme süresi, ardışık gece sınırı ve haftalık saat tavanı gibi kurallar modele zorunlu kısıt olarak girdiği için ihlal içeren bir çizelge üretilmesi mümkün değildir. Ayrıca hangi kuralın nasıl sağlandığı raporlanabildiğinden, çizelge denetlenebilir bir belge niteliği kazanmaktadır.

Operasyonel açıdan en belirgin kazanım, değişime dayanıklılıktır. Mevcut uygulamada tek bir izin bilgisi bütün planın yeniden kurulmasını gerektirebilmektedir. Sistem, önceki çizelgeden sapmayı cezalandırarak yeniden çözüm ürettiği için değişiklik yalnızca gerekli olan birkaç atamayla sınırlı kalmakta; çalışanlar planlarını baştan öğrenmek zorunda kalmamaktadır.

İnsan kaynağı açısından sistem, adalet iddiasını ölçülebilir hale getirmektedir. Gece ve hafta sonu yükünün dağılımı kişi bazında raporlanmakta, çalışan kendi yükünü ekip ortalamasıyla karşılaştırabilmektedir. Bu şeffaflık, çizelgeye ilişkin itirazların algı düzeyinden veri düzeyine taşınmasını sağlamaktadır.

Nihayetinde araç, neyin daha önemli olduğuna kendisi karar vermemektedir. Adalet ile tercih arasındaki dengeyi kullanıcıdan ağırlık parametreleri olarak almakta ve bu tercihin sonucunu hesaplamaktadır. Böylece kararı devralan değil, kararı veren kişiyi destekleyen bir konumda kalmaktadır.

## 2.5 Uygulama Alanı: Güvenlik Personeli

Sistemin ilk uygulama alanı BOTAŞ tesislerinin güvenlik personelidir. Aşağıda tanımlanan yapı, mentör görüşmesi sonrasında kesinleşmek üzere mevcut işleyişten alınmış varsayımlara dayanmaktadır. Bu değerlerin tamamı sistem içinden düzenlenebildiği için, gerçek değerlerin farklı çıkması durumunda yazılım değişikliği gerekmemektedir.

Tesiste iki bina bulunmakta ve güvenlik hizmeti günde üç vardiya halinde (00.00–08.00, 08.00–16.00, 16.00–24.00) kesintisiz yürütülmektedir. Devriye görevi bulunmamakta; personel güvenlik ve müracaat noktalarında görevlendirilmektedir. Görev noktaları bina ayrımı yapılmadan tesis geneli tanımlanmıştır: kapı ve kontrol odası arasındaki ayrım kaldırılmış, tek bir "Güvenlik" noktasında birleştirilmiştir — kontrol odasında görevli personel zaten ayrı bir meslek grubu değil aynı yetkinliğe sahip bir güvenlik görevlisiydi, dolayısıyla atamanın hangi fiziksel noktaya yazıldığı modelin ihtiyaç duyduğu bir bilgi değildir; kim hangi kapıda veya kontrol odasında duracağını vardiya şefi o gün belirler. Aynı gerekçeyle müracaat noktası da bina ayrımı olmadan tanımlanmıştır.

Görev noktaları ve her noktanın gerektirdiği yetkinlik aşağıdaki gibidir.

| Görev Noktası | Konum | Gerekli Yetkinlik |
| --- | --- | --- |
| Vardiya Şefliği | Tesis geneli | Vardiya Şefi |
| Güvenlik | Tesis geneli | Güvenlik Görevi |
| Müracaat | Tesis geneli | Müracaat Görevlisi |



Yetkinlik yapısı üç tanımdan oluşmaktadır. Güvenlik Görevi yetkinliği, güvenlik noktasında (kapı ve kontrol odası görevlerini birlikte kapsar) görev alabilmenin ön koşuludur. Vardiya Şefi yetkinliğine sahip personel aynı zamanda Güvenlik Görevi yetkinliğini de taşımakta, dolayısıyla müracaat dışındaki tüm noktalarda görevlendirilebilmektedir. Müracaat Görevlisi ise yalnızca müracaat noktasında çalışmakta; bu personel Güvenlik Görevi yetkinliğini taşımadığı için başka bir noktaya atanamamakta, aynı şekilde müracaat noktası da bu yetkinliğe sahip olmayan personele açılmamaktadır.

Görev noktası başına gereken personel sayısı gün tipine ve vardiyaya göre değişmektedir. Hafta içi gündüz ve akşam vardiyaları tam kadro çalışmakta; gece vardiyası ile hafta sonu ve resmî tatillerin tüm vardiyaları azaltılmış kadroyla yürütülmektedir.

| Görev Noktası | Hafta İçi Gündüz / Akşam | Gece, Hafta Sonu ve Tatil |
| --- | --- | --- |
| Vardiya Şefliği | 1 | 1 |
| Güvenlik | 7 | 3 |
| Müracaat | 2 | — |
| Toplam | 10 | 4 |



Bu talep yapısı haftada 144 kişi-vardiyalık, bir başka deyişle 1.152 saatlik bir iş yükü oluşturmaktadır. Haftalık saat tavanı ve haftada bir tam izin günü kuralları birlikte değerlendirildiğinde bir personelin haftada en fazla beş vardiya tutabildiği görülmekte; buradan izin ve rapor payı hariç en az yirmi dokuz kişilik bir kadro gereksinimi çıkmaktadır. Yetkinlik havuzları ayrı ayrı incelendiğinde vardiya şefliği havuzunun en kırılgan bileşen olduğu ortaya çıkmaktadır: tek bir görev noktası kesintisiz doldurulduğu için haftada yirmi bir vardiya gerektirmekte, bu da beş kişilik bir havuzda tek bir iznin dahi kapanamayan boşluk doğurması anlamına gelmektedir. Sistemin bu tür kırılganlıkları sayısal olarak görünür kılması, projenin doğrudan katkılarından biridir.

Bu bölümdeki bütün sayılar birer parametredir. Görev noktası eklenmesi, vardiya sayısının değiştirilmesi veya kadro sayılarının güncellenmesi yönetim arayüzünden yapılabilmekte, çözücü modeli bu değişiklikleri kendiliğinden dikkate almaktadır.

Planlama dönemi varsayılan olarak bir haftadır; yönetici bunu istediği bir uzunluğa çıkarabilir. Aşağıdaki 4.2 bölümündeki performans kabul kriteri, bu varsayılanın üzerinde kasıtlı bir stres testi ölçeğidir.

# 3. Ön Plan

## 3.1 Planlanan Çıktılar

Projenin yaşam döngüsü boyunca üretilecek çıktılar ve ait oldukları aşamalar aşağıda tanımlanmıştır.

- Proje Tanım Dokümanı: Başlangıç planlama aşamasının çıktısıdır; projenin hedeflerini, kapsamını ve fizibilitesini tanımlar.

- Kural Kataloğu: Gereksinim analizi aşamasının çıktısıdır. Her kuralın kimliği, tipi (zorunlu veya esnek), parametreleri ve ihlal ölçüsü tanımlanır. Hem çözücü modelinin hem de manuel doğrulayıcının kaynağıdır.

- Veri Modeli ve Matematiksel Model Dokümanı: Tasarım aşamasının çıktısıdır. Veritabanı şeması ile karar değişkenlerini, kısıtları ve amaç fonksiyonunu matematiksel gösterimle içerir.

- Web Uygulaması ve Demo Veri Seti: Geliştirme aşamasının çıktısıdır. Yönetim arayüzü, çözücü, analiz paneli ve çalışan panelini kapsar.

- Deney Raporu: Doğrulama aşamasının çıktısıdır. Farklı ölçeklerde çözüm süreleri, ceza dağılımları ve elle kurulan çizelgeyle karşılaştırma sonuçlarını içerir.

- Kullanım Kılavuzu: Teslim aşamasının çıktısıdır; sistemin kurulumu ve kullanımını kısa biçimde açıklar.

- Staj Raporu ve Kapanış Sunumu: Projenin bulgularını, karşılaşılan teknik zorlukları ve sistemin canlı gösterimini içeren son çıktıdır.

## 3.2 Çalışma Planı

### Proje Aşamaları ve Çalışma Modeli

Proje çevik bir yaklaşımla, üç sprint halinde yürütülecektir. Her sprint çalışır durumda bir artım üretmeyi hedefler; böylece gereksinimlerdeki değişiklikler ve mentör görüşmelerinden çıkan yeni bilgiler plana esneklik kaybı olmadan yansıtılabilir.

| Sprint | Gün | İçerik |
| --- | --- | --- |
| Sprint 1 | 1–5 | Kural kataloğunun çıkarılması, veri modelinin tasarımı, tanım yönetimi arayüzü, demo veri üreteci |
| Sprint 2 | 6–11 | Kısıt programlama modeli, kapsama uyarıları, çizelge ekranı, değişim odaklı yeniden çözme |
| Sprint 3 | 12–15 | Analiz paneli, manuel düzenleme doğrulaması, çalışan paneli (koşullu), deneyler ve dokümantasyon |



### Kaynaklar ve Eğitim

Proje tek kişilik bir ekiple yürütülmektedir. Gerekli kaynaklar geliştirme ortamı, kısıt programlama çözücüsü ve barındırma altyapısından ibarettir. Kısıt programlama alanında ön bilgi mevcut olmakla birlikte, çözücünün ileri özellikleri (varsayım tabanlı çelişki teşhisi, çözüm ipucu verme) gerektiğinde çalışılacaktır. Kurumdan gerçek veri talep edilmediği için veri erişim izni gerektiren bir bağımlılık bulunmamaktadır.

### İşbirliği ve Toplantılar

Kurum mentörüyle düzenli görüşmeler yapılacak, her sprint sonunda ilerleme gösterilecektir. Kuruma özgü kural değerleri ve vardiya yapısı gibi açık sorular bu görüşmelerde netleştirilecektir. Toplantı tipleri şunlardır:

- Sprint Planlama: İlgili sprintte üretilecek artımın ve görevlerin belirlenmesi.

- Mentör Görüşmesi: İlerlemenin gösterilmesi, açık soruların netleştirilmesi ve geri bildirim alınması.

- Sprint Değerlendirme: Üretilen artımın kabul kriterleri karşısında değerlendirilmesi.

- Sprint Retrospektifi: Sonraki sprint için çalışma biçiminin gözden geçirilmesi.

### Kilometre Taşları

- Kilometre Taşı 1: Proje tanım dokümanının mentör tarafından onaylanması.

- Kilometre Taşı 2: Kural kataloğunun ve veri modelinin kesinleşmesi.

- Kilometre Taşı 3: Çözücünün tüm zorunlu kısıtları sağlayan ilk geçerli çizelgeyi üretmesi.

- Kilometre Taşı 4: Manuel düzenleme, yeniden çözme ve analiz panelinin tamamlanması.

- Kilometre Taşı 5: Deneylerin tamamlanması, dokümantasyon ve kapanış sunumu.

## 3.3 Roller ve Sorumluluklar

| Kişi | Projedeki Rolü |
| --- | --- |
| Ömer HARMANKAYA | Proje Yürütücüsü — Sistem Analisti / Geliştirici |
| Kurum Mentörü | Alan Uzmanı ve Onay Mercii |
| Akademik Danışman | Akademik Değerlendirme |



**Ömer HARMANKAYA — Proje Yürütücüsü**

Gereksinimlerin çıkarılması, kural kataloğunun oluşturulması, veri modelinin ve kısıt programlama modelinin tasarımı, uygulamanın geliştirilmesi, deneylerin yürütülmesi ve dokümantasyonun hazırlanmasından sorumludur.

**Kurum Mentörü — Alan Uzmanı**

Kuruma özgü çalışma kurallarının, vardiya yapısının ve yetkinlik ayrımlarının doğrulanmasından; üretilen çıktıların operasyonel gerçeklikle uyumunun değerlendirilmesinden sorumludur.

**Akademik Danışman**

Staj sürecinin ve nihai raporun akademik gereklilikler açısından değerlendirilmesinden sorumludur.

# 4. Kapsam Sınırları ve Varsayımlar

## 4.1 Kapsam Dışı

Aşağıdaki işlevler bilinçli olarak kapsam dışında bırakılmıştır. Kapsam kararlarında kullanılan ölçüt şudur: bir iş bugün vardiya yöneticisi tarafından yapılıyorsa kapsam içindedir, insan kaynakları tarafından yapılıyorsa değildir.

- İnsan kaynakları ve bordro işlevleri; puantaj hesabı

- İzin talebi ve onay iş akışı (izinler sisteme veri olarak girilir)

- Vardiya takası ve değişim talebi iş akışı

- Personel bildirimleri (e-posta, anlık bildirim)

- Mobil uygulama geliştirme

- Kurum sistemlerine entegrasyon

- Gerçek kurum verisinin kullanımı

## 4.2 Varsayımlar

- Personel, yetkinlik ve kural tanımları uygulama içinden oluşturulabildiği için proje gerçek kurum verisine bağımlı değildir.

- İzin ve rapor bilgileri sisteme yönetici tarafından elle veya toplu içe aktarma yoluyla girilir.

- Kuruma özgü kural değerleri (ardışık gece sınırı, haftalık saat tavanı vb.) parametre olarak tanımlanmıştır; gerçek değerler öğrenildiğinde kod değişikliği gerekmez.

- Zorunlu kısıtlar yasal ve fiziksel niteliktedir; birbirleriyle çelişmeleri beklenmemektedir.

- Bölüm 2.5'te tanımlanan görev noktası, yetkinlik ve kadro değerleri mevcut işleyişten alınmış varsayımlardır; mentör görüşmesinde teyit edilecektir.

- Personel belirli bir binaya bağlı değildir; tek havuz olarak değerlendirilmekte ve her iki binada da görevlendirilebilmektedir.

- Tüm güvenlik personeli silahlı görevlidir; bu nedenle silah durumu ayırt edici bir yetkinlik olarak modellenmemiştir.

- Mevcut kadro, hâlihazırda işleyen çizelgeyi karşılayacak düzeydedir; dolayısıyla gerçek veriyle çalışıldığında çözülebilir bir problem beklenmektedir.

# 5. Kabul Kriterleri

- Kırk personel ve yirmi sekiz günlük referans örnek (varsayılan bir haftalık dönemden büyük, kasıtlı bir stres testi ölçeği) altmış saniyenin altında çözülür.

- Üretilen çizelgede zorunlu kısıt ihlali bulunmaz; bu durum otomatik testlerle doğrulanır.

- Kişi başına düşen gece yükü, kişiye düşen adil paydan en fazla bir gece bloğu kadar sapar. Ölçünün birimi gece saatidir; eşik, çalışma bloğu kataloğundaki en uzun gece bloğunun süresidir ve katalog değiştiğinde kendiliğinden güncellenir.

- Kasten çelişkili kurulan örnekte sistem hangi gün, hangi saat aralığı ve hangi görev noktasında kaç kişi eksik kaldığını gösterir.

- Manuel düzenlemede kural ihlali bir saniyenin altında bildirilir.

- Yeniden çözümde değişen atama sayısı raporlanır.

# 6. Riskler

| Risk | Etki | Önlem |
| --- | --- | --- |
| Kural kataloğu Sprint 1'de hatalı tasarlanırsa çözücü modeli defalarca yeniden yazılır | Yüksek | İlk somut iş kural kataloğudur; veri modeli ondan sonra gelir ve katalog mentör onayından geçer |
| Kapsam, çalışan paneli ve ek özelliklerle genişler | Orta | Çalışan paneli koşullu iş olarak işaretlenmiştir; kapsam kararlarında bölüm 4.1'deki ölçüt uygulanır |
| Kurumun gerçek kuralları bilinmediği için model varsayımlarla kurulur | Düşük | Tüm kurallar parametre olarak tanımlanmıştır; gerçek değerler öğrenildiğinde yalnızca veri değişir |
| Çözüm süresi büyük örneklerde kabul edilebilir sınırın üstüne çıkar | Orta | Zaman limiti tanımlanır ve limit dolduğunda o ana kadarki en iyi çözüm döndürülür |



# 7. Mentöre Yöneltilecek Açık Sorular

- Güvenlik hizmetinde 3x8 düzeni mi uygulanmaktadır, yoksa 12/24 gibi bir düzen mi kullanılmaktadır?

- Ardışık gece sınırı, asgari dinlenme süresi ve haftalık saat tavanı için kurumda uygulanan gerçek değerler nelerdir?

- Bölüm 2.5'teki kadro sayıları mevcut işleyişle örtüşmekte midir; özellikle gece ve hafta sonu kadrolarında azaltma bu şekilde mi yapılmaktadır?

- Vardiya şefliği gerçekten iki bina için ortak tek bir görev midir, yoksa bina başına ayrı şef bulunmakta mıdır?

- Kontrol odası yalnızca bir binada mı bulunmaktadır?

- Müracaat personeli güvenlik görevlerinde hiç görevlendirilmemekte midir?

- Vardiya şefi kadrosu kaç kişiden oluşmaktadır? Bu havuz, tek görev noktasının kesintisiz doldurulması nedeniyle izin dönemlerinde kritik hale gelmektedir.

- Personel sabit vardiyada mı çalışmaktadır, yoksa vardiyalar arasında rotasyon uygulanmakta mıdır?

- Çizelgeler hangi dönem uzunluğunda hazırlanmaktadır?

- Kullanıcı hesaplarının kurum dizininden mi yönetilmesi beklenmektedir, yoksa sistemin kendi hesap yönetimi yeterli midir? (Çalışan panelinin kimlik doğrulaması kapsama alınmış ve kullanıcı adı–parola ile çözülmüştür.)

# 8. Gelecek Çalışma

- Çelişen kısıtlarda varsayım tabanlı otomatik çakışma teşhisi

- Senaryo karşılaştırma: aynı veri üzerinde farklı ağırlık setlerinin yan yana değerlendirilmesi

- Vardiya takası iş akışı

- Bildirim altyapısı

# Kaynaklar

Google. (2026). OR-Tools CP-SAT Solver [Yazılım kütüphanesi]. https://developers.google.com/optimization/cp

T.C. Resmî Gazete. (2003). 4857 sayılı İş Kanunu.

TED Üniversitesi. (2026). CMPE 399 Yaz Stajı — ders materyalleri [Öğrenme yönetim sistemi]. https://lms.tedu.edu.tr/
