# Vardiya Çizelgeleme Karar Destek Aracı — Uygulama Planı

Bu doküman, projenin kodlama aşamasını gün gün Claude Code oturumlarına böler. Her gün bağımsız bir oturum olacak biçimde tasarlanmıştır: net bir hedefi, hangi doküman bölümüne dayandığını ve bittiğini nasıl anlayacağını (kabul testi) içerir.

Referans dokümanlar (hepsi `docs/` altına konmalı):
- `docs/charter.docx` — Proje Tanım Dokümanı (Sürüm 1.1)
- `docs/srs.docx` — Yazılım Gereksinim Belirtimi (Sürüm 1.1)
- `docs/backlog.docx` — Ürün Backlog'u ve Karar Günlüğü
- `docs/sdd.docx` — Yazılım Tasarım Dokümanı (Sürüm 1.1)

Bir görevde "SDD 5.3" gibi bir referans görürsen, o bölümdeki sözde kodu ve gerekçeyi birebir uygulama kaynağı olarak kullan. Tasarımdan sapman gerekiyorsa önce nedenini söyle, sonra uygula — sessizce sapma.

---

## 0. Genel Kurallar (proje boyunca geçerli)

### Kod stili ve araçlar
- Backend: Python 3.12, tip açıklamaları (type hints) her fonksiyonda zorunlu. `ruff` hem biçimlendirme hem statik denetim için; commit öncesi `ruff check` ve `ruff format` temiz olmalı.
- Frontend: TypeScript strict mode açık. `any` kullanımı yalnızca üçüncü parti tip tanımı eksikse ve yorum satırıyla gerekçelendirilmişse kabul edilir.
- Veritabanı: şema değişikliği yalnızca Alembic göçüyle yapılır. Elle `ALTER TABLE` veya veritabanını silip yeniden oluşturmak yasaktır — göç geçmişi projenin bir parçasıdır.
- Adlandırma: veritabanı ve Python tarafında Türkçe alan adları (SDD veri sözlüğüyle birebir), kod yapıları (sınıf, fonksiyon, dosya) için İngilizce teknik terimler kabul edilir; karışıklığı önlemek için SDD'deki alan adlarını değiştirmeden kullan.

### Git ve ilerleme takibi
- Her günün sonunda bir commit; conventional commits biçimi (`feat:`, `fix:`, `test:`, `docs:`, `refactor:`).
- Kök dizinde `PROGRESS.md` tutulur. Her oturum (Claude Code çalıştırması) sonunda şu satır eklenir: tarih, tamamlanan görev, kalan/ertelenen iş, bir sonraki oturumun ilk işi. Bir sonraki oturum bu dosyayı okuyarak başlar — bağlam böyle taşınır.
- Sprint sonlarında bir `git tag` (`sprint-1`, `sprint-2`, `sprint-3`) atılır.
- **GitHub'a yükleme her zaman elle yapılır.** Claude Code `git init`, `git add`, `git commit` ve `git tag` çalıştırır; `git push`, `git remote add`, GitHub üzerinde repo oluşturma veya herhangi bir kimlik doğrulama gerektiren işlem asla yapmaz. Görev, her günün sonunda çalışma dizinini "elle `git push` yapılmaya hazır" bırakmaktır — yükleme kararı ve zamanlaması tamamen kullanıcıya aittir.

### Her Günün Sonunda: GitHub'a Yüklemeye Hazırlık Kontrolü
Bir günün görevi "bitti" sayılmadan önce aşağıdakiler doğrulanır:
- [ ] `git status` temiz — commit edilmemiş değişiklik yok, izlenmeyen dosya yok (kasıtlı olanlar hariç)
- [ ] `.gitignore` güncel: `__pycache__/`, `.venv/`, `node_modules/`, `.env`, `*.db`, derleme çıktıları (`dist/`, `build/`) dahil
- [ ] Hiçbir sır (veritabanı şifresi, API anahtarı, `.env` dosyasının kendisi) commit geçmişinde yok — `git log -p` ile şüpheli dosya eklenmediği kontrol edilir
- [ ] Testler geçiyor (`pytest`, ilgiliyse `tsc --noEmit`)
- [ ] `ruff check` ve `ruff format --check` temiz
- [ ] Commit mesajı conventional commits biçiminde ve o günün işini doğru özetliyor
- [ ] `PROGRESS.md` güncellenmiş
- [ ] Depo kökünde, o ana kadarki `README.md` hâlâ doğru (kurulum adımları değiştiyse README de değişmiş olmalı)

Bu liste geçmeden gün "tamamlandı" işaretlenmez. Sprint sonlarında ayrıca `git tag` atılır ve tag'in doğru commit'i işaret ettiği teyit edilir.

### Test disiplini
- Her kural sınıfı (H1–H8, S1–S8) için: `modele_ekle` ve `dogrula` metotlarının ayrı ayrı birim testi.
- **Çözücü-doğrulayıcı uyum testi** (SDD 3.2.1'de söz verilen): rastgele üretilmiş çözülebilir örnekler çözülür, çıkan çizelge doğrulayıcıdan geçirilir, hiçbir zorunlu kısıt ihlali çıkmamalı. Bu test Sprint 1'in sonunda iskelet olarak, Sprint 2'de gerçek çözücüyle tam işler hâle gelir. Sürekli çalıştırılan bir test paketi olmalı — özellik değil, güvence.
- API uç noktaları için en az mutlu yol + bir hata yolu testi.
- Kabul kriterlerindeki sayısal hedefler (60 saniye, sıfır zorunlu kısıt ihlali, ≤1 gece sapması) Sprint 3'te otomatik bir test/betik olarak da yazılır; elle kontrol edilmez.

### Kural kataloğuna dokunurken
- Yeni bir kural asla tek başına eklenmez: sınıf + `modele_ekle` + `dogrula` + birim test + kural kayıt defterine kayıt aynı commit'te gider.
- Bir kural parametresi değiştirilecekse (örnek: dinlenme süresi) kod dokunulmaz, yalnızca veritabanındaki `kural` tablosu satırı güncellenir; bunu doğrulayan bir test yaz.

### Kapsam disiplini
- Backlog'daki K-01…K-07 (kalıcı kapsam dışı) ve B-01…B-13 (ertelenen) maddelerine dokunma. Bir görev sırasında bunlardan biri "aslında lazım" gibi görünürse, uygulama yerine `PROGRESS.md`'ye not düş ve devam et.
- SDD'de tanımlanmayan bir teknik karar (yeni kütüphane, yeni servis, yeni desen) alınacaksa önce sor.

### Oturum başlatma rutini
Her Claude Code oturumu şu sırayla başlamalı:
1. `PROGRESS.md`'yi oku.
2. O günün karşılık geldiği bu plandaki maddeyi oku.
3. İlgili SDD/SRS bölümünü oku.
4. Göreve başla; bitince testleri çalıştır, commit at, `PROGRESS.md`'yi güncelle.

---

## Sprint 0 — İskelet Kurulumu (yarım gün, Sprint 1'den önce)

**Hedef:** Boş ama çalışan bir iskelet; sonraki her gün doğrudan işlevsel koda başlayabilsin.

- [ ] Depo yapısı: `backend/`, `frontend/`, `docs/`, `scripts/`
- [ ] Backend: FastAPI projesi, `uvicorn` ile ayağa kalkan boş bir `/health` uç noktası
- [ ] SQLAlchemy + Alembic kurulumu, PostgreSQL'e ilk bağlantı, boş ilk göç
- [ ] Frontend: Vite + React + TypeScript iskeleti, boş ana sayfa
- [ ] `ruff.toml`, `pyproject.toml`, `.env.example`, `.gitignore`
- [ ] `requirements.txt` / `pyproject.toml` içinde sürüm sabitleme (SDD 3.4.1'deki "sürüm dosyası" burasıdır)
- [ ] `scripts/kurulum.sh` — geliştirme ortamını tek komutla ayağa kaldıran betik (SDD 3.4.1)
- [ ] `README.md` — projeyi tanıtan, kurulum adımlarını içeren kısa döküman
- [ ] `PROGRESS.md` oluştur, ilk satırı yaz
- [ ] `git init`, kapsamlı bir `.gitignore` (yukarıdaki "GitHub'a Yüklemeye Hazırlık Kontrolü" listesindeki maddeler dahil), ilk commit (`feat: proje iskeleti`)
- [ ] Uzak sunucu (`git remote add`) **eklenmez** — bu adım kullanıcı tarafından elle yapılacak

**Kabul:** `scripts/kurulum.sh` çalıştırıldığında backend `/health` 200 döner, frontend boş sayfayı render eder, `alembic upgrade head` hatasız çalışır; `git status` temiz ve `git log` en az bir commit gösteriyor.

---

## Sprint 1 (Gün 1–5): Kural Kataloğu → Veri Modeli → CRUD → Demo Veri

Bu sprintin riski en yüksek olanı: kural kataloğu burada yanlış kurulursa Sprint 2'de model yeniden yazılır (Charter bölüm "Riskler").

### Gün 1 — Veritabanı Şeması
- SDD 4.2'deki 15 tabloyu SQLAlchemy modeli olarak birebir yaz (Türkçe alan adları dahil).
- Her tablo için Alembic göçü.
- SDD 4.2'deki kısıtları uygula: `personel_yetkinlik` bileşik anahtar, `atama` üzerindeki (surum_id, personel_id, tarih) benzersizlik kısıtı (SDD 4.2.4).
- **Kabul:** `alembic upgrade head` sıfırdan çalışır, tüm tablolar ve yabancı anahtarlar oluşur; basit bir `INSERT`/`SELECT` testiyle doğrula.

### Gün 2 — Kural Arayüzü ve Zorunlu Kısıtlar (H1–H8)
- SDD 5.1'deki `Kural` temel sınıfını yaz (`modele_ekle`, `dogrula`, `kimlik`, `tip`, `parametreler`, `agirlik`).
- Kural kayıt defterini yaz (kimlik → sınıf eşlemesi).
- H1–H8'i SDD Ek A'daki H2 örneğini şablon alarak yaz. Bu aşamada `modele_ekle` metodu CP-SAT model nesnesini henüz almayabilir (Gün 6'da tam bağlanacak) — ama imza ve `dogrula` metodu tam çalışır olmalı.
- Her kural için `dogrula` birim testi (kural ihlal ediliyor mu / edilmiyor mu senaryosu).
- **Kabul:** Sekiz zorunlu kısıtın tamamı için `dogrula` metodu, elle kurulan örnek atama listelerinde doğru sonucu veriyor.

### Gün 3 — Esnek Hedefler (S1–S8)
- S1–S8'i SDD Ek A'daki S2 örneğini şablon alarak yaz.
- S1'in özel davranışını unutma: talep hem üst sınır (zorunlu) hem alt sınır (esnek) — SRS bölüm S1 formülasyonu.
- Her esnek hedef için `dogrula`/ceza hesaplama birim testi.
- **Kabul:** On altı kuralın (H1–H8, S1–S8) tamamı kayıt defterinde, hepsinin `dogrula` metodu test altında.

### Gün 4 — Tanım Yönetimi CRUD API'leri
- SDD Ek B'deki uç noktalardan tanım yönetimi grubu: `/api/personel`, `/api/yetkinlik`, `/api/bina`, `/api/nokta`, `/api/vardiya-tipi`, `/api/talep`, `/api/kural`.
- SRS FR-1.1–FR-1.14 gereksinimlerini karşıla; özellikle FR-1.9 (yük göstergesi hesaplaması — SDD 3.3.6'daki formülü kullan).
- Depo katmanı (repository) deseni: SQL yalnızca bu katmanda.
- **Kabul:** Her uç nokta için mutlu yol testi; Postman/HTTPie ile personel + yetkinlik + görev noktası + talep zinciri elle kurulabiliyor.

### Gün 5 — Demo Veri Üreteci ve Sprint 1 Checkpoint
- SDD 3.3'teki güvenlik personeli senaryosunu üreten bir betik: ~44 personel, üç yetkinlik dağılımı, SDD 3.3.4'teki talep matrisi.
- İki senaryo (Backlog'daki demo veri stratejisi): "rahat" (kadro yeterli) ve "sıkışık" (izinler girince kapsama açığı doğuran).
- Çözücü-doğrulayıcı uyum testinin iskeletini kur (henüz gerçek çözücü yok, elle üretilmiş rastgele geçerli atamalarla test et).
- **Kabul (Sprint 1 çıkışı):** Tanım yönetimi ekranından bağımsız olarak, API üzerinden tam bir personel/yetkinlik/nokta/talep kümesi kurulabiliyor; demo veri betiği tek komutla iki senaryoyu da veritabanına yazabiliyor; on altı kuralın `dogrula` tarafı test kapsamında.

---

## Sprint 2 (Gün 6–11): CP-SAT Modeli, Ön Kontrol, Çizelge Ekranı, Yeniden Çözme

### Gün 6 — Çözücü Adaptörü ve Model Kurma
- SDD 5.3'teki `model_kur` sözde kodunu birebir uygula: karar değişkeni `x[p,g,v,n]`, üç atlama koşulu (talep sıfır / yetkinlik yok / müsait değil), yardımcı değişken `y[p,g,v]`.
- `CozucuAdaptoru`: model kur, çöz, ara çözüm geri çağırma, sonucu döndür (SDD 3.2 — dar arayüz).
- Kuralların `modele_ekle` metotlarını gerçek CP-SAT model nesnesiyle tamamla (Gün 2–3'te iskelet kalmıştı).
- **Kabul:** Küçük bir örnek (5 personel, 3 gün) uçtan uca çözülüyor ve sonuç `atama` tablosuna yazılıyor.

### Gün 7 — Ön Kontrol Alt Sistemi
- SDD 5.2'deki dört kontrolü birebir uygula: dönem geneli kapasite, yetkinlik havuzu, gün bazlı, nokta bazlı.
- `/api/on-kontrol` uç noktası.
- Sıkışık senaryo üzerinde çalıştırıp gerçekten anlamlı bulgular ürettiğini doğrula.
- **Kabul:** Sıkışık senaryoda ön kontrol, çözücüyü çalıştırmadan en az bir yapısal engel buluyor; rahat senaryoda hiç bulgu vermiyor.

### Gün 8 — Çözüm İşi ve Asenkron Yürütme
- SDD 5.4'teki durum makinesini uygula (Şekil 5.1): kuyrukta → on_kontrol → cozuluyor → tamamlandı/uyarılı/başarısız/iptal.
- Çözüm işinin ayrı süreçte çalışması (SDD 3.4.4) — bu aşamada basit bir `multiprocessing` veya ayrı komutla tetiklenen süreç yeterli; systemd entegrasyonu Sprint 3'te.
- `/api/cozum`, `/api/cozum/{id}`, `/api/cozum/{id}/iptal` uç noktaları.
- Ara çözüm bildirimi: her iyileşen çözümde `en_iyi_ceza` güncellensin.
- **Kabul:** Çözüm isteği anında iş kimliği döndürüyor; API bu sırada başka isteklere yanıt vermeye devam ediyor (elle test et: çözüm sürerken `/health`'i çağır).

### Gün 9 — Doğrulama Alt Sistemi
- SDD 5.5'teki `degisikligi_dogrula` mantığını uygula: etkilenen pencere hesaplama (en geniş kapsamlı kural olan H5'in yedi günü), yalnızca o pencereyi değerlendirme.
- `/api/atama/dogrula` ve `/api/atama` (PUT) uç noktaları.
- Zorunlu ihlalde değişikliği reddet, esnek ihlalde ceza farkını bildir (SRS'teki "kararı devretmeme" ilkesi).
- **Kabul:** Bir saniyenin altında yanıt (elle zamanla); zorunlu kısıt bozan bir değişiklik reddediliyor, esnek hedefi bozan kabul edilip ceza farkı gösteriliyor.

### Gün 10 — Frontend: Çözüm ve Çizelge Ekranları (temel görünüm)
- SDD 6.3.2 ve 6.3.3'teki nesneleri uygula: çözüm başlatma, ilerleme göstergesi, çizelge ızgarası, hücre düzenleme, ihlal bildirimi, kilitleme, kapsama açığı işareti.
- Bu aşamada görsel tasarım Figma mockup'larına göre değil, işlevsel iskelet olarak yapılır — stil son sprintte veya mockup'lar hazır olunca uygulanır.
- **Kabul:** Bir çözüm baştan sona arayüzden başlatılabiliyor, ilerleme görülüyor, sonuç ızgarada görüntüleniyor, bir hücre elle değiştirilip doğrulama sonucu görülebiliyor.

### Gün 11 — Yeniden Çözme (S8) ve Sprint 2 Checkpoint
- SDD 5.6'daki `yeniden_coz` akışını uygula: taslak türetme, kilitli atamaların sabitlenmesi, S8'in taban atamaları.
- Sürüm durumu geçişleri (taslak → çözüldü → yayınlandı → arşiv, SRS TD-8).
- **Kabul (Sprint 2 çıkışı):** Rahat senaryo uçtan uca çözülüyor; sıkışık senaryo ön kontrolde doğru engelleri gösteriyor ve yine de bir çizelge üretip kapsama açığını raporluyor; yayınlanmış bir sürümden yeni izinle yeniden çözüm alınıp değişen atama sayısı görülebiliyor.

---

## Sprint 3 (Gün 12–15): Analiz, Çalışan Paneli, Deneyler, Dağıtım

### Gün 12 — Analiz Servisi ve Ekranı
- SDD 5.7'deki yedi metriği uygula.
- `/api/analiz/{surum_id}` uç noktası, SDD 6.3.4'teki analiz ekranı.
- CSV dışa aktarma.
- **Kabul:** Sıkışık senaryo üzerinde kapsama oranı, gece/hafta sonu adalet grafiği ve ceza dökümü doğru sayılarla görüntüleniyor.

### Gün 13 — Çalışan Paneli
- SDD 6.1'deki dört bölüm: Vardiyalarım, Dönem özetim, Tercih bildirimi, Tercihlerim.
- Backlog B-05 uyarınca kimlik doğrulama basit tutulur (kişiye özel bağlantı); kurumsal SSO kapsam dışı.
- **Kabul:** Bir personel kendi atamalarını görebiliyor, tercih bildirebiliyor; başka bir personelin verisine erişemiyor.

### Gün 14 — Uçtan Uca Deneyler ve Performans Ölçümü
- Charter'daki kabul kriterlerinin her biri için otomatik bir kontrol/betik yaz: 40 personel × 28 gün < 60 sn (SDD 3.4.2'deki referans donanımda ölç), zorunlu kısıt ihlali sıfır, kişi başı gece sapması ≤1, çelişkili örnekte eksik gösterimi, manuel düzenleme <1 sn.
- Çözücü-doğrulayıcı uyum testini büyük ölçekte (rastgele 20+ örnek) çalıştır.
- Sonuçları kısa bir performans notuna yaz (staj raporuna girecek).
- **Kabul:** Bütün kabul kriterleri otomatik betikle "geçti" sonucu veriyor; geçmiyorsa hangi kriterin ne kadar açıkta olduğu net.

### Gün 15 — Dağıtım ve Kapanış
- SDD 3.4'teki gösterim ortamını kur: systemd servisleri (`uygulama.service`, `cozum-isci.service`), Caddy, PostgreSQL sistem servisi.
- Sürümler ekranı (SDD 6.3.5).
- `docs/` klasöründeki dört dokümanla kodun tutarlı olduğunu son kez kontrol et; SDD'den sapılan yer varsa dokümana işle.
- `PROGRESS.md`'yi kapanış notuyla güncelle, `sprint-3` etiketini at.
- **Kabul:** Sistem, kendi sunucunda gerçek alan adı üzerinden erişilebilir durumda; mentöre gösterilecek uçtan uca senaryo (rahat + sıkışık) prova edilmiş.

---

## Mentör Görüşmesi Sonrası Güncelleme Protokolü

SRS ve Backlog'daki açık sorular mentörle netleştiğinde:
1. Önce ilgili dokümanı (Charter/SRS) güncelle — kod değil doküman önce değişir.
2. Değişiklik yalnızca veri ise (talep sayısı, kural parametresi gibi) kod dokunulmadan veritabanı üzerinden uygulanır.
3. Değişiklik yapısal ise (yeni görev noktası tipi, yeni yetkinlik davranışı gibi) önce bu plana etkisi değerlendirilir, sonra ilgili sprint gününe not düşülür.

## Kabul Kriterleri Kontrol Listesi (Charter'dan)

- [ ] 40 personel × 28 gün, referans donanımda (4 çekirdek / 8 GB) < 60 saniye
- [ ] Zorunlu kısıt ihlali sıfır (otomatik test)
- [ ] Kişi başı gece sapması ≤ 1
- [ ] Çelişkili örnekte eksik gün/vardiya/sayı gösteriliyor
- [ ] Manuel düzenleme doğrulaması < 1 saniye
