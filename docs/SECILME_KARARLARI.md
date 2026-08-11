# Vardiya Çizelgeleme Karar Destek Aracı — Seçilme Kararları

Bu doküman, projenin teknoloji yığınını, mimari tercihlerini ve güvenlik tasarım
kararlarını gerekçeleriyle birlikte açıklar. Her bölüm üç soruyu yanıtlar: ne
seçildi, neden seçildi ve hangi alternatifler değerlendirilip neden reddedildi.

Doküman, proje tanım dokümanı (Charter), yazılım gereksinim belirtimi (SRS) ve
yazılım tasarım dokümanı (SDD) ile birlikte okunmalıdır. Buradaki kararlar
SDD bölüm 3.3'te özetlenmiştir; bu doküman o özetlerin genişletilmiş ve
bağımsız biçimde okunabilir hâlidir.

---

# 1. Çözücü: Google OR-Tools CP-SAT

## 1.1 Seçim

Çizelgeleme problemi, Google OR-Tools kütüphanesinin CP-SAT (Constraint
Programming — Satisfiability) çözücüsüyle modellenmektedir.

## 1.2 Gerekçe

Vardiya çizelgeleme, özünde bir kısıt eniyileme problemidir: bir dizi karar
değişkeni (kimin nerede ne zaman çalışacağı) üzerinde zorunlu kısıtlar
sağlanırken, esnek hedeflerin ürettiği ceza toplamı en aza indirilir. Bu
problem iki farklı paradigmayla modellenebilir.

**Matematiksel programlama (LP/MIP).** Gurobi, CPLEX, SCIP gibi çözücüler
doğrusal ve tamsayılı programlama modellerini çözer. Ticari olanları (Gurobi,
CPLEX) güçlüdür ancak lisans ücreti taşır ve akademik lisanslar dağıtım
kısıtlaması getirir. SCIP açık kaynaklıdır ancak Python arayüzü ve
dokümantasyonu CP-SAT kadar olgun değildir.

**Kısıt programlama (CP).** OR-Tools CP-SAT açık kaynaklıdır, ücretsizdir ve
Apache 2.0 lisansı ile dağıtılır. Çizelgeleme ve atama problemlerinde güçlü
performans gösterir; Google'ın kendi üretim sistemlerinde kullanılmaktadır.

CP-SAT'ın bu proje için belirleyici olan üç özelliği:

1. **Tek model, iki kural tipi.** Zorunlu kısıtlar (ihlal edilemez) ve esnek
   hedefler (ceza puanlı) aynı modelde ifade edilir. SRS bölüm 4'teki on altı
   kuralın hepsi tek bir CP-SAT modeline eklenir ve çözücü hem kısıtları
   sağlar hem cezayı en aza indirir.

2. **Paralel arama.** CP-SAT, birden fazla arama stratejisini eş zamanlı
   yürütür. Çözüm süresi çekirdek sayısıyla orantılı biçimde iyileşir; dört
   çekirdekli referans donanımda üç arama işçisi kullanılmaktadır (dördüncü
   çekirdek API sunucusuna ayrılır).

3. **Ara çözüm geri bildirimi.** CP-SAT, çözüm iyileştikçe geri çağırma
   (callback) yoluyla bildirim verir. Bu sayede kullanıcıya çözüm sürerken
   güncellenen ceza değeri ve kapsama açığı sayısı gösterilebilir; kullanıcı
   çözümün nereye yakınsadığını görerek erken durdurma kararı verebilir.

## 1.3 Reddedilen Alternatifler

| Alternatif | Reddedilme Nedeni |
|---|---|
| Gurobi / CPLEX | Ticari lisans gerektirir; akademik lisans dağıtım kısıtlaması getirir. Staj projesi için maliyet ve lisans karmaşıklığı gereksizdir. |
| SCIP | Açık kaynak MIP çözücüsü ancak Python arayüzü ve dokümantasyonu CP-SAT kadar olgun değildir. |
| Sezgisel algoritmalar (genetik, tavlama) | Optimallik garantisi vermez; zorunlu kısıtların her zaman sağlandığını kanıtlamak zorlaşır. CP-SAT, zorunlu kısıtları yapısal olarak garanti eder. |
| Elle çizelgeleme (çözücü yok) | Projenin temel amacı olan "karar destek aracı" kimliğiyle çelişir. |

---

# 2. Backend Dili: Python 3.12+

## 2.1 Seçim

Uygulama sunucusu Python 3.12 ile geliştirilmektedir (gösterim sunucusu
Python 3.14 çalıştırmaktadır).

## 2.2 Gerekçe

Dil seçimi çözücü seçiminden türemiştir. OR-Tools CP-SAT'ın birinci sınıf
desteklediği diller Python, C++, Java ve C# ile sınırlıdır. Bu kısıt,
alternatif çalışma zamanlarını (Go, Rust, Node.js gibi) değerlendirme dışı
bırakmıştır.

Kalan dört aday arasında Python, şu gerekçelerle seçilmiştir:

- **Geliştirme hızı.** Staj süresinde tek kişiyle geliştirilecek bir proje
  için C++'ın derleme süresi ve bellek yönetimi yükü gerçekçi değildir.
- **Kütüphane olgunluğu.** Web çatısı (FastAPI), ORM (SQLAlchemy), göç aracı
  (Alembic), parola özetleme (argon2-cffi) gibi ihtiyaçların tamamı Python
  ekosisteminde olgun, iyi belgelenmiş ve aktif bakım altındaki kütüphanelerle
  karşılanmaktadır.
- **Tip güvenliği.** Python 3.12, tip açıklamalarını (type hints) destekler.
  Projede her fonksiyonda tip açıklaması zorunludur ve `ruff` ile statik
  denetim yapılmaktadır. Bu, dinamik dilin başlıca dezavantajını önemli
  ölçüde azaltır.

## 2.3 Reddedilen Alternatifler

| Alternatif | Reddedilme Nedeni |
|---|---|
| C++ | OR-Tools'un ana dili ancak geliştirme hızı düşük, web çatısı seçenekleri sınırlı, bellek yönetimi yükü var. Staj süresine uygun değil. |
| Java | Olgun ekosistem ancak Python'a kıyasla daha fazla şablon kod (boilerplate) gerektirir. Spring Boot ile karşılaştırıldığında FastAPI daha ince bir katman sunar. |
| C# | .NET ekosistemi güçlü ancak gösterim sunucusu Linux üzerinde çalışıyor ve ekibin (tek kişi) deneyimi Python'da daha güçlü. |

---

# 3. Web Çatısı: FastAPI

## 3.1 Seçim

Uygulama sunucusu FastAPI 0.115.6 ile geliştirilmektedir. ASGI sunucusu
olarak uvicorn kullanılmaktadır.

## 3.2 Gerekçe

Sistemin sunucu tarafı, esas olarak çözücüyü saran ince bir katmandır. İki
tür iş yürütür: milisaniyeler mertebesinde tamamlanan istek-yanıt işleri
(tanım yönetimi, raporlama) ve dakikalar sürebilen çözüm işleri. Web
çatısının görevi birincisidir; ikincisi ayrı bir süreçte yürütülür.

FastAPI'nin bu proje için belirleyici üç özelliği:

1. **Şema tabanlı doğrulama.** İstek ve yanıt şemaları Python tip
   açıklamalarından (Pydantic modelleri) otomatik türetilir. Router katmanı
   yalnızca şema ile servisi birbirine bağlar; iş mantığı servis katmanında
   kalır.

2. **Bağımlılık enjeksiyonu.** Veritabanı oturumu, oturum doğrulama ve rol
   denetimi gibi kesişen sorumluluklar `Depends` mekanizmasıyla bildirimsel
   olarak ifade edilir. Bu, güvenlik kapılarının router imzasında görünür
   olmasını ve bir uç noktanın kapısız kalma riskinin azalmasını sağlar.

3. **Otomatik API belgelendirmesi.** FastAPI, OpenAPI şemasını otomatik
   üretir. Geliştirme sırasında `/docs` adresindeki Swagger arayüzü, uç
   noktaların elle test edilmesini kolaylaştırır.

## 3.3 Django ile Karşılaştırma

Django, bu proje için en güçlü alternatifti ve seçim SDD bölüm 3.3'te uzun
uzun tartışılmıştır.

**Django'nun avantajı:** Yerleşik yönetim arayüzü (Django Admin), SDD bölüm
3.1'de tanımlanan tanım yönetimi ekranlarının büyük bölümünü hazır sunardı.
Bu, gerçek bir zaman kazancı demekti.

**Reddedilme nedeni:** Tanım ekranları ürünün sunulan yüzeyinin parçasıdır ve
kendine özgü bir görsel dile sahip olması beklenmektedir. Django Admin'in kendi
arayüz kalıbı (tablo listeleri, basit formlar) bu beklentiyle uyuşmamakta;
üzerine özel bir görünüm inşa etmek ise sıfırdan yazmaktan farklı bir kazanç
sunmamaktadır. Django bu projede en güçlü olduğu noktada böylece devre dışı
kalmakta; geriye kalan ORM ve göç araçları ise FastAPI tarafında SQLAlchemy ve
Alembic ile eşdeğer biçimde karşılanmaktadır.

**Özet:** Seçim, bir çatının diğerinden üstün olmasından değil, sistemin CRUD
ağırlıklı bir iş uygulaması değil API ile hesaplama servisinin birleşimi
olmasından kaynaklanmıştır.

## 3.4 Reddedilen Diğer Alternatifler

| Alternatif | Reddedilme Nedeni |
|---|---|
| Django + DRF | Django Admin'in avantajı kullanılamadığında geriye kalan yapı FastAPI'den daha ağır; tam donanımlı bir çatının getireceği yapı bu ihtiyacın üzerindedir. |
| Flask | Minimalist ancak şema doğrulaması, bağımlılık enjeksiyonu ve tip desteği FastAPI kadar yerleşik değildir; üçüncü parti kütüphanelerle tamamlanması gerekir. |
| Litestar | FastAPI'ye benzer felsefede ancak ekosistemi daha küçük ve topluluk desteği daha sınırlı. |

---

# 4. Veritabanı: PostgreSQL 16

## 4.1 Seçim

Veri katmanı PostgreSQL 16 ilişkisel veritabanı üzerine kuruludur.

## 4.2 Gerekçe

Veri modeli yoğun biçimde ilişkiseldir. Üç katmanlı bir ilişki ağı
bulunmaktadır:

- Personel ile yetkinlik arasında **çoktan çoğa** (personel_yetkinlik)
- Görev noktası ile bina ve yetkinlik arasında **çoktan bire**
- Atama ile personel, vardiya tipi ve görev noktası arasında **üçlü ilişki**

Bu yapıda ilişkisel model doğal karşılıktır. İlişkisel olmayan bir veritabanı
(MongoDB, DynamoDB gibi) bu ilişkileri gömülü belgelerle modellemeye çalışır;
bu da veri tutarsızlığı riskini artırır ve çapraz sorgulama ihtiyacını
karmaşıklaştırır.

PostgreSQL'in bu proje için belirleyici iki özelliği:

1. **JSONB desteği.** Kural parametreleri kurala göre farklı alanlara
   sahiptir: H2'nin `asgari_dinlenme_saati` parametresi varken H1'in hiç
   parametresi yoktur. Her kural tipi için ayrı sütun tanımlamak, on altı kural
   için büyük ölçüde boş kalan geniş bir tablo üretecektir. JSONB alanı bu
   sorunu çözer: her kural kendi parametre kümesini tek bir alanda taşır.
   Aynı yaklaşım ceza dökümü ve kural anlık görüntüsü için de kullanılır.

2. **Veritabanı düzeyinde güvenlik kısıtları.** Projedeki güvenlik
   önlemlerinin bir kısmı yalnızca uygulama katmanında değil, veritabanı
   düzeyinde de uygulanır:
   - `CHECK` kısıtı: çalışan hesabının personele bağlı olması zorunlu
   - `CHECK` kısıtı: kullanıcı adının küçük harfle saklanması zorunlu
   - `UNIQUE` kısıtı: aynı sürümde aynı personele aynı güne iki atama yazılamaz (H1)
   - `ENUM` tipleri: durum alanlarının geçerli değer kümesi veritabanında da korunur

## 4.3 Reddedilen Alternatifler

| Alternatif | Reddedilme Nedeni |
|---|---|
| SQLite | Geliştirme için pratik ancak eş zamanlı yazma desteği sınırlı, JSONB ve gelişmiş CHECK kısıtları yok. Ayrı süreçte çalışan çözüm işçisi ile API'nin aynı veritabanına yazması SQLite'ın kilitleme modeliyle iyi çalışmaz. |
| MySQL / MariaDB | İlişkisel ancak JSONB desteği PostgreSQL kadar olgun değil; CHECK kısıtları MySQL'de 8.0.16 öncesinde yok sayılıyordu. |
| MongoDB | İlişkisel olmayan model bu veri yapısına uygun değil; ilişkileri gömülü belgelerle modellemek tutarsızlık riski taşır. |

---

# 5. ORM ve Göç: SQLAlchemy + Alembic

## 5.1 Seçim

Veritabanı erişimi SQLAlchemy 2.0 ORM katmanıyla, şema değişiklikleri Alembic
göç aracıyla yönetilmektedir.

## 5.2 Gerekçe

**SQLAlchemy:** Python dünyasının en olgun ve en yaygın kullanılan ORM
kütüphanesidir. Modelleri Python sınıfları olarak tanımlar ve SQL'in depo
katmanının (repository) dışına sızmasını engeller. PostgreSQL'e özgü
özellikleri (JSONB, ENUM, CHECK kısıtları, mapped_column) doğrudan destekler.
2.0 sürümü modern Python tip açıklamalarıyla tam uyumludur.

**Alembic:** Şema değişikliği yalnızca göç dosyasıyla yapılır. Projede elle
`ALTER TABLE` çalıştırmak veya veritabanını silip yeniden oluşturmak yasaktır.
Göç geçmişi projenin bir parçasıdır ve versiyon kontrolünde tutulur. Bu
sayede:

- Geliştirme ile sunucu ortamı arasındaki şema tutarlılığı garanti altındadır
- Şema değişikliklerinin geriye dönük izlenebilirliği sağlanır
- `alembic upgrade head` komutuyla sıfırdan veritabanı kurulabilir

## 5.3 Reddedilen Alternatifler

| Alternatif | Reddedilme Nedeni |
|---|---|
| Django ORM | Django çatısına bağımlıdır; FastAPI seçildiğinde kullanılamaz. |
| Tortoise ORM | Asenkron odaklı ancak olgunluk ve topluluk desteği SQLAlchemy'nin çok gerisinde. |
| Peewee | Minimalist ve hafif ancak karmaşık sorgulamalar ve PostgreSQL'e özgü özellikler için yetersiz. |
| Ham SQL | Bakım zorluğu; SQL'in depolar dışına sızma riski; tip güvenliği yok. |

---

# 6. Frontend: React + TypeScript + Vite

## 6.1 Seçim

Sunum katmanı React 19 ile TypeScript strict mode üzerinde geliştirilmektedir.
Derleme aracı olarak Vite 8 kullanılmaktadır.

## 6.2 React Gerekçesi

Sistemin arayüzü dokuz yönetici ekranı ve üç çalışan bölümünden oluşur.
Çizelge ızgarası (personel × gün matrisi), anlık doğrulama geri bildirimi ve
çoklu sekmeli tanım yönetimi gibi yapılar, bileşen tabanlı bir mimari
gerektirmektedir.

React'in bu proje için belirleyici özellikleri:

- **Bileşen yeniden kullanımı.** Çizelge ızgarasının hücreleri, talep matrisi
  tablosu, filtreleme bileşenleri gibi tekrarlı yapılar bağımsız bileşenler
  olarak yazılır ve farklı ekranlarda yeniden kullanılır.
- **Durum yönetimi.** Çözüm ilerlemesinin yoklanması (polling), çizelge
  hücrelerinin anlık doğrulanması ve ekranlar arası veri paylaşımı (dönem
  seçimi gibi) React'in durum yönetim modeli ile doğal biçimde ifade edilir.
- **Ekosistem genişliği.** Radix UI (erişilebilir bileşen ilkeleri), shadcn/ui
  (önceden tasarlanmış bileşenler), Lucide (ikon seti), TailwindCSS (stil
  sistemi) gibi araçlar geliştirme hızını artırır.

## 6.3 TypeScript Gerekçesi

TypeScript strict mode açıktır. `any` kullanımı yalnızca üçüncü parti tip
tanımı eksikse ve yorum satırıyla gerekçelendirilmişse kabul edilir.

Bu disiplinin sağladığı kazançlar:

- **API-arayüz sözleşmesi.** Backend'den gelen JSON yanıtları TypeScript
  arayüzleriyle (interface) tanımlanır. API şeması değiştiğinde derleme
  hatası oluşur ve uyumsuzluk çalışma zamanına ulaşmadan yakalanır.
- **Refactoring güvenliği.** Bir alan adı veya fonksiyon imzası değiştiğinde
  etkilenen tüm noktalar derleyici tarafından işaretlenir.
- **Editör desteği.** Otomatik tamamlama, tanıma gitme ve satır içi hata
  gösterimi geliştirme hızını artırır.

## 6.4 Vite Gerekçesi

Create React App (CRA) artık bakımsızdır ve React ekibi tarafından
önerilmemektedir. Vite, modern JavaScript geliştirme deneyiminin standartı
hâline gelmiştir:

- **Anlık sunucu başlatma.** Modül bazlı geliştirme sunucusu, proje
  büyüklüğünden bağımsız olarak milisaniyeler içinde başlar.
- **Hızlı HMR (Hot Module Replacement).** Kaynak dosya değiştiğinde yalnızca
  değişen modül güncellenir; sayfa yeniden yüklenmez.
- **Optimize üretim derlemesi.** Rollup tabanlı derleme, kod bölme (code
  splitting) ve ağaç silkeleme (tree shaking) ile küçük paketler üretir.

## 6.5 Stil Sistemi ve Bileşen Kütüphanesi

| Araç | Kullanım Amacı |
|---|---|
| **TailwindCSS 4** | Yardımcı sınıf (utility-first) tabanlı stil sistemi. Tasarım tokenleri (renk, tipografi, aralık) CSS değişkenleri olarak tanımlanır. |
| **shadcn/ui** | Kopyalanıp düzenlenebilir bileşen kütüphanesi. Radix UI ilkeleri üzerine kurulu, tam özelleştirilebilir. npm bağımlılığı değil, kaynak kodu projeye kopyalanır. |
| **Radix UI** | Erişilebilir (accessible), stilsiz UI ilkeleri. Diyalog, seçim kutusu, açılır menü gibi karmaşık etkileşim kalıplarını klavye navigasyonu ve ekran okuyucu desteğiyle sunar. |
| **IBM Plex** | Tipografi sistemi. Sans, Sans Condensed ve Mono üç varyant kullanılır. |
| **Lucide React** | Tutarlı, hafif ikon seti. |

## 6.6 Reddedilen Frontend Alternatifleri

| Alternatif | Reddedilme Nedeni |
|---|---|
| Vue.js | Güçlü alternatif ancak ekibin (tek kişi) React deneyimi daha güçlü; ekosistem genişliği ve bileşen kütüphanesi seçenekleri React'in gerisinde. |
| Angular | Tam donanımlı çatı ancak bu proje için fazla yapı ve şablon kodu (boilerplate) gerektirir. Öğrenme eğrisi daha dik. |
| Svelte | Performans avantajı var ancak ekosistemi küçük, bileşen kütüphanesi seçenekleri sınırlı. |
| Next.js | React üzerine kurulu tam yığın çatı. Sunucu tarafı render (SSR) ve dosya tabanlı yönlendirme sunar; ancak bu proje sunucu tarafını Python ile yönetiyor ve SSR'a ihtiyaç duymayan bir SPA. Ek karmaşıklık getirir, kazanç sunmaz. |
| Create React App | Bakımsız, React ekibi tarafından artık önerilmiyor. |

---

# 7. Parola Güvenliği: Argon2id

## 7.1 Seçim

Parolalar Argon2id algoritmasıyla özetlenmektedir (argon2-cffi kütüphanesi,
RFC 9106 varsayılan parametreleri).

## 7.2 Gerekçe

Parola özetleme (hashing), kullanıcı parolalarının veritabanında düz metin
yerine geri çevrilemez biçimde saklanmasını sağlar. Veritabanı sızdığında
saldırganın parolaları elde edebilmesi, özetleme algoritmasının saldırı
maliyetine bağlıdır.

Üç nesil parola özetleme algoritması ve güvenlik profilleri:

| Nesil | Algoritma | Güvenlik Profili |
|---|---|---|
| 1. | MD5, SHA-256 | **Güvensiz.** Çok hızlı — modern GPU ile saniyede milyarlarca deneme. Tuz (salt) bile yeterli değil; hız sorunun kendisi. |
| 2. | bcrypt, scrypt | **İyi.** Kasıtlı olarak yavaş; bcrypt CPU yoğun, scrypt hem CPU hem bellek yoğun. Ancak bcrypt'in bellek kullanımı düşük olduğundan özelleştirilmiş donanım (ASIC/GPU) ile hızlandırılabilir. |
| 3. | **Argon2id** | **Güncel standart.** RFC 9106 ile standartlaştırılmış. Hem CPU yoğun hem bellek yoğun (64 MiB varsayılan). GPU/ASIC tabanlı kaba kuvvet saldırılarına karşı tasarlanmış. OWASP tarafından birinci tercih olarak önerilir. |

Argon2id'nin ek avantajları:

- **Özet dizesi kendi kendini tanımlar.** Tuz, algoritma parametreleri
  (bellek, geçiş sayısı, kol sayısı) özetin içinde saklanır. Ayrı bir tuz
  sütunu gerekmez.
- **İleriye uyumlu.** Kütüphane güncellendiğinde varsayılan parametreler
  otomatik yükselir. Eski özetler, parametreleri özetin içinden okuyarak
  doğrulanmaya devam eder; kullanıcının yeni parametrelerle özetlenmesi
  ancak bir sonraki giriş veya parola değişikliğinde yapılır.

## 7.3 Reddedilen Alternatifler

| Alternatif | Reddedilme Nedeni |
|---|---|
| bcrypt | İyi bir algoritma ancak bellek kullanımı düşük; GPU tabanlı saldırılara Argon2id kadar dayanıklı değil. Güncel standart artık Argon2id. |
| scrypt | Bellek yoğun ancak standartlaştırılmamış; parametre ayarlaması daha karmaşık. |
| SHA-256 + tuz | Çok hızlı; parola özetleme için güvensiz. |
| PBKDF2 | NIST tarafından hâlâ kabul ediliyor ancak yalnızca CPU yoğun; bellek boyutu yok, GPU saldırılarına açık. |

---

# 8. Oturum Yönetimi: Sunucu Tarafı Oturum

## 8.1 Seçim

Kimlik doğrulama, JWT (JSON Web Token) yerine sunucu tarafında veritabanında
tutulan oturum kayıtlarıyla yönetilmektedir. Oturum belirteci (token) rastgele
üretilir ve yalnızca çerezde saklanır; veritabanında belirtecin SHA-256 özeti
tutulur.

## 8.2 Gerekçe

JWT'nin temel avantajı durumsuzluktur: sunucuda kayıt tutmaya gerek yoktur
ve belirteç kendi kendini doğrular. Ancak bu avantaj, bu projenin gereksinimi
olan **anlık geri alınabilirlik** ile doğrudan çelişir.

Anlık geri alınabilirliğin gerektiği üç senaryo:

1. **Hesap devre dışı bırakma (SRS FR-10.5).** Bir hesap devre dışı
   bırakıldığında, o hesaba ait tüm açık oturumların anında geçersiz
   kılınması gerekir. JWT'de bu, belirtecin süresinin dolmasını beklemeyi
   veya ayrı bir kara liste altyapısı kurmayı gerektirir.

2. **Parola sıfırlama.** Yönetim bir hesabın parolasını sıfırladığında veya
   kullanıcı parolasını değiştirdiğinde, eski parola ile açılmış oturumlar
   kapatılmalıdır. Aksi hâlde çalınmış bir belirteç parola değişikliğinden
   sonra da geçerli kalır.

3. **Zorunlu parola değiştirme (SRS FR-10.7).** Yönetim tarafından atanan
   parolanın ilk girişte değiştirilmesi zorunludur. Bu zorunluluk, oturumun
   sunucu tarafında hangi kullanıcıya ait olduğunun bilinmesini gerektirir.

Sunucu tarafı oturumun bu projede ek bir maliyet getirmemesinin nedeni:
**sistemde zaten bir veritabanı var.** JWT'nin durumsuzluk avantajı, genellikle
ayrı bir Redis veya oturum deposu kurma ihtiyacını ortadan kaldırmasıdır.
Bu projede PostgreSQL zaten çalışmakta olduğundan, ek bir parça gerekmez.

### Belirteç Güvenliği

Oturum belirteci 256 bit rastgele üretilir (`secrets.token_urlsafe(32)`) ve
veritabanında yalnızca SHA-256 özeti saklanır. Bu tasarımın anlamı:
veritabanını okuyan bir saldırgan, mevcut oturumları ele geçiremez — çünkü
özetten belirteç üretilemez.

SHA-256'nın burada (parola özetlemede olduğu gibi Argon2id yerine)
kullanılmasının nedeni: belirteç insan tarafından seçilmiş bir parola değil,
256 bit rastgele bir değerdir. Sözlük saldırısı mümkün değildir; yavaş bir
özet burada yalnızca gereksiz gecikme olurdu.

## 8.3 Reddedilen Alternatifler

| Alternatif | Reddedilme Nedeni |
|---|---|
| JWT | Anlık geri alınamaz; kara liste altyapısı (Redis) kurmak, zaten veritabanı olan bir sistemde gereksiz karmaşıklık. |
| JWT + Redis kara listesi | İki ek parça (JWT doğrulama + Redis); sunucu tarafı oturumun tek parça ile verdiği işlevselliği daha fazla bileşenle karşılar. |
| Çerez tabanlı oturum (sunucu imzalı) | Flask'ın varsayılanı. Oturum verisi çerezde taşınır; boyut sınırı var ve sunucu tarafında iptal mekanizması yok. |

---

# 9. Çerez Güvenliği

## 9.1 Seçim

Oturum belirteci tarayıcıda yalnızca çerezde, üç güvenlik niteliği ile
saklanır: `HttpOnly`, `Secure`, `SameSite=Lax`.

## 9.2 Her Niteliğin Gerekçesi

| Nitelik | Koruma | Açıklama |
|---|---|---|
| `HttpOnly` | XSS (Cross-Site Scripting) | JavaScript, çereze erişemez. Sayfada bir XSS açığı bulunsa bile saldırgan belirteci çalıp kendi bilgisayarından giriş yapamaz. |
| `Secure` | Ağ dinlemesi | Çerez yalnızca HTTPS üzerinden gönderilir. Düz HTTP'de iletilmez, ağı dinleyen biri belirteci ele geçiremez. Yerel geliştirmede `.env` ile kapatılır (`http://localhost` HTTPS değildir). |
| `SameSite=Lax` | CSRF (Cross-Site Request Forgery) | Başka sitelerden gelen POST isteklerine çerez eklenmez. Saldırgan kendi sitesinden kullanıcının adına istek gönderemez. GET'lerde çerez gider, normal gezinme bozulmaz. |

## 9.3 Ek: Çereze Süre Yazılmaması

Çerezde `Max-Age` veya `Expires` değeri **ayarlanmaz**. Oturumun geçerliliği
yalnızca sunucudaki veritabanı kaydından okunur. Çereze bir süre yazmak, iki
kaynağın (tarayıcı ve veritabanı) ayrışabildiği ikinci bir gerçek üretirdi:
çerez tarayıcıda hâlâ geçerliyken sunucuda süresi dolmuş olabilir veya tam
tersi.

---

# 10. Asenkron Çözüm Mimarisi

## 10.1 Seçim

Çözüm işi API sürecinde değil, ayrı bir sistem servisi olarak ayrı bir
süreçte çalışır. İki süreç arasında doğrudan iletişim kurulmaz; iş durumu,
ilerleme bilgisi ve sonuç yalnızca veritabanı üzerinden aktarılır.

## 10.2 Gerekçe

Kabul kriteri, kırk personel ve yirmi sekiz günlük referans örneğin altmış
saniyenin altında çözülmesini öngörmektedir. Bu süre bir HTTP isteğinin
makul yanıt süresinin çok üzerindedir. Çözümün istek-yanıt döngüsü içinde
yürütülmesi iki nedenle uygulanabilir değildir:

1. **Zaman aşımı.** Ara sunucular (reverse proxy) ve tarayıcılar, uzun süre
   açık kalan bağlantıları kesebilir.
2. **API blokajı.** CP-SAT işlemciyi kesintisiz kullanır. Aynı süreçteki
   olay döngüsünde çalışırsa, işin sürdüğü boyunca tüm istekler bekletilir —
   çözüm durumunu sorgulayan istekler de yanıtsız kalır ve asenkron tasarımın
   kazancı ortadan kalkar.

İki sürecin yalnızca veritabanı üzerinden haberleşmesinin iki kazancı:

1. **Hata izolasyonu.** Çözüm sürecinin beklenmedik biçimde sonlanması API
   sunucusunu etkilemez. İş kaydı veritabanında kaldığı için durum tespit
   edilebilir ve systemd süreci otomatik olarak yeniden başlatır.
2. **Gelecek esnekliği.** Çözüm işçisinin ayrı bir makineye taşınması,
   aradaki sözleşme zaten veritabanı olduğu için mimari değişiklik
   gerektirmez.

## 10.3 Celery + Redis Kullanılmaması

Kuyruk altyapısı bilinçli olarak dışarıda bırakılmıştır. Sistemde tek bir
vardiya yöneticisi varsayılmakta ve eş zamanlı çözüm ihtiyacı
bulunmamaktadır. Uygulama sürecinin kendi arka plan görevi ile işin durumunu
tutan bir veritabanı tablosu bu ihtiyacı karşılamaktadır.

Celery + Redis eklenmesi:

- İki ek bağımlılık (Celery, Redis) ve bunların yapılandırması
- Redis sunucusunun kurulumu ve bakımı
- Celery worker'ın ayrıca yönetilmesi

Bu ek karmaşıklık, tek kullanıcılı ve tek tesisli bir kullanımda karşılığı
olmayan bir işletim yükü getirecektir. Çok kullanıcılı kullanım gündeme
geldiğinde bu karar Ürün Backlog'u T-02 kapsamında yeniden değerlendirilecektir.

---

# 11. Dağıtım: systemd + Caddy, Docker Yok

## 11.1 Seçim

Sistem, konteynerleştirme kullanılmadan doğrudan işletim sistemi üzerine
kurulur. API ve çözüm işçisi systemd servisleri olarak, ters vekil (reverse
proxy) olarak Caddy çalıştırılır.

## 11.2 Docker Kullanılmaması

Konteynerleştirme bilinçli olarak dışarıda bırakılmıştır. Docker'ın çözdüğü
üç temel sorun ve bu projede karşılıkları:

| Docker'ın Çözdüğü Sorun | Bu Projede Durum |
|---|---|
| **İzolasyon** | Tek sunucu, tek uygulama grubu; izolasyon sorunu yok. |
| **Taşınabilirlik** | İki ortam (geliştirme + gösterim); sürüm dosyası ve tek kurulum betiği ile sağlanıyor. |
| **Ölçekleme** | Tek kullanıcılı sistemde ölçekleme ihtiyacı yok. |

Docker kullanmamanın kazancı: doğrudan kurulum, gösterim öncesi hata ayıklamayı
ve sunucudaki günlük kayıtlarına erişimi basitleştirir. Konteyner katmanı,
bu ölçekte kazanımı olmayan bir soyutlama eklerdi.

## 11.3 systemd Gerekçesi

systemd, Docker'ın sağladığı iki pratik faydayı konteyner katmanı olmadan
verir:

1. **Süreç çöktüğünde otomatik yeniden başlatma** (`Restart=on-failure`)
2. **Sunucu yeniden başladığında otomatik ayağa kalkma** (`WantedBy=multi-user.target`)

## 11.4 Caddy Gerekçesi

| Özellik | Caddy | Nginx |
|---|---|---|
| Otomatik TLS | Let's Encrypt ile otomatik, yapılandırma gerektirmez | certbot ile ayrıca yapılandırılır |
| Yapılandırma | ~10 satır Caddyfile | Daha fazla yapılandırma satırı |
| Sunucu durumu | Gösterim sunucusunda zaten kurulu | Ek kurulum gerekir |

---

# 12. Kural Kataloğunun Kod-Veri Ayrımı

## 12.1 Seçim

Kural kataloğu iki parçadan oluşur: kodda tanımlı kural sınıfları ve
veritabanında tutulan kural verisi. Kural tipleri (H1–H8, S1–S8) kodda,
kural değerleri (parametreler, ağırlıklar, aktiflik) veritabanındadır.

## 12.2 Gerekçe

Kuralların tamamen veri olarak tanımlanması — yani veritabanında saklanan bir
kural dilinin çalışma zamanında yorumlanması — değerlendirilmiş ve
reddedilmiştir. Bu yaklaşım yeni kural tiplerinin kod değişikliği olmadan
eklenebilmesini sağlardı; ancak:

- Dilin kendisinin tasarlanması, ayrıştırılması ve doğrulanması bağımsız bir
  iş kalemidir ve projenin kabul kriterlerine katkı sağlamaz.
- Pratikte değişen şey kural **değeri**dir (örn. dinlenme süresi 16 → 12
  saat), kural **tipi** değil. Değer değişikliği arayüzden yapılır, kod
  değişmez.
- Yeni bir kural tipi eklemek, her durumda hem CP-SAT modeline ekleme
  mantığının hem de doğrulama mantığının yazılmasını gerektirir; bunlar bir
  yorumlama diliyle ifade edilemeyecek kadar karmaşıktır.

Seçilen yapının sonuçları:

| İhtiyaç | Çözüm |
|---|---|
| Ardışık gece sınırını 3'ten 4'e çıkarmak | Arayüzden parametre değişikliği, kod değişmez |
| Bir hedefin ağırlığını ayarlamak | Arayüzden ağırlık değişikliği, kod değişmez |
| Bir kuralı geçici olarak devre dışı bırakmak | Arayüzden aktiflik değişikliği, kod değişmez |
| Yeni bir kural tipi eklemek | Yeni bir Python sınıfı yazılır (geliştirici işi) |

---

# 13. Yıkıcı İşlem Koruması: Üretim Kilidi

## 13.1 Seçim

Veritabanını boşaltan üç komut (testler, kabul ölçümü, demo veri üreteci)
`VERI_TEMIZLIGINE_IZIN=true` ortam değişkeni olmadan çalışmayı reddeder.

## 13.2 Gerekçe

Bu tasarımın felsefesi: **kilit, ayarın yokluğunda devrededir.** Varsayılan
değer `false`'tur; dolayısıyla ayarı taşımayan her ortam — özellikle gösterim
sunucusu — otomatik olarak korunur.

- Geliştirme makinesinde `backend/.env` içinde `true`dur.
- Sunucuda bu dosya **bulunmaz** (dağıtımda rsync ile dışlanır).
- Sunucuda gerçekten çalıştırılması gerekirse değişken tek seferlik komutun
  önüne yazılır: `VERI_TEMIZLIGINE_IZIN=true python scripts/kabul_olcumu.py`

Bu yapı, veritabanı adı kontrolünden bilinçli olarak farklıdır: geliştirme
ve gösterim veritabanlarının ikisi de `vardiya` adını taşımakta olduğundan,
ad hiçbir şey ayırt edemezdi.

---

# 14. Denetim Kaydı Tasarımı

## 14.1 Seçim

Giriş denemeleri ve hesap yönetimi işlemleri, Python `logging` modülü ile
yapılandırılmış biçimde kaydedilir. Harici bir günlük toplama altyapısı
(ELK, Splunk) kullanılmaz.

## 14.2 Gerekçe

### Ne kaydedilir
Olayın türü, ilgili kullanıcı adı, rol, işlemi yapan kişi ve zaman damgası.
`journalctl -u vardiya-api | grep olay=giris_basarisiz` gibi komutlarla
süzülebilecek `anahtar=değer` çiftleri biçiminde.

### Ne kaydedilmez
Parola, parola özeti, oturum belirteci ve belirtecin özeti. Kayıtlar sistem
günlüğüne yazılır ve günlüğü okuyabilen herkes onları görür; oraya yazılan
bir sır artık sır değildir.

### Girdi temizleme
Giriş denemesindeki kullanıcı adı saldırganın yazdığı metindir. İçine satır
sonu koyup günlüğe sahte bir satır uydurabilirdi (log injection). Bu nedenle
güvenli karakter kümesi dışındaki her karakter noktaya çevrilir ve uzunluk
sınırlandırılır.

### Harici altyapı kullanılmaması
Bu ölçekte (tek sunucu, düşük istek hacmi) ayrı bir günlük toplama altyapısı
taşıdığından fazla parça olurdu. systemd günlüğü (journald) yeterlidir.

---

# Özet Tablo

| Karar | Seçilen | Ana Gerekçe | Reddedilen Başlıca Alternatif |
|---|---|---|---|
| Çözücü | OR-Tools CP-SAT | Açık kaynak, kısıt + eniyileme tek modelde | Gurobi (lisans), sezgisel (garanti yok) |
| Dil | Python 3.12+ | Çözücü desteği + geliştirme hızı | C++ (yavaş geliştirme), Java (fazla şablon) |
| Web çatısı | FastAPI | İnce katman, şema doğrulama, bağımlılık enjeksiyonu | Django (admin kullanılamıyor) |
| Veritabanı | PostgreSQL 16 | İlişkisel model + JSONB + CHECK kısıtları | SQLite (eş zamanlılık), MongoDB (ilişkisel değil) |
| ORM | SQLAlchemy + Alembic | Olgunluk + göç yönetimi | Django ORM (Django'ya bağımlı) |
| Frontend | React + TypeScript | Bileşen mimarisi + tip güvenliği | Vue (daha az deneyim), Angular (fazla yapı) |
| Derleme | Vite | Hızlı geliştirme deneyimi | CRA (bakımsız) |
| Parola | Argon2id | RFC 9106 standardı, GPU dayanıklı | bcrypt (GPU'ya açık), SHA-256 (güvensiz) |
| Oturum | Sunucu tarafı (DB) | Anlık geri alınabilirlik | JWT (geri alınamaz) |
| Kuyruk | Yok (DB yoklama) | Tek kullanıcı, basitlik | Celery+Redis (gereksiz karmaşıklık) |
| Konteyner | Yok (systemd) | Bu ölçekte gereksiz | Docker (kazanımsız katman) |
| Ters vekil | Caddy | Otomatik TLS, basit yapılandırma | Nginx (elle TLS) |
