# Claude Code — İkinci Aşama, Tur 1: Çözüm Akışı ve Kabuk

## Kim olduğun ve neyle çalıştığın

BOTAŞ vardiya çizelgeleme karar destek aracının ikinci geliştirme aşamasındasın.
Sistem canlıda çalışıyor (vardiya.omerharmankaya.com), altı kabul kriteri referans
donanımda 6/6 geçti, kimlik doğrulama ve üç rol (çalışan / yönetici / yönetim)
yayında. Bu tur bir hata düzeltme ve akış iyileştirme turudur; kural kataloğuna,
çözücü modeline ve veri modelinin çekirdeğine dokunmaz.

Depoda `docs/` altında dört kanonik doküman var. **Bu dokümanlar tek gerçek
kaynaktır ve sen onlara DOKUNMAZSIN.** Bu turun gerektirdiği güncellemeler zaten
yapıldı ve sana verildi:

- Yazılım Gereksinim Belirtimi — sürüm **1.12** (FR-4.9, FR-4.10, FR-4.11, NFR-14)
- Yazılım Tasarım Dokümanı — sürüm **1.19** (4.2.4, 5.4.1, 5.4.2, 6.1, 6.3.2, Ek B)
- Ürün Backlog'u — sürüm **1.5** (beş yeni karar; T-06 kapatıldı, T-02 kısmen)
- Proje Tanım Dokümanı — sürüm 1.2, bu turda değişmedi

**İlk işin:** `docs/` altındaki bu dosyaların yukarıdaki sürüm numaralarını taşıdığını
doğrula. Taşımıyorlarsa dur ve kullanıcıya söyle — eski bir kopyayla çalışmak,
tasarımı ikinci kez üretmek demektir.

Çalışmaya başlamadan önce oku: SDD 4.2.4 (`cozum_isi`), SDD 5.4 ve alt bölümleri
5.4.1–5.4.2, SDD 6.1'deki "Çalışan İş Göstergesi", SDD 6.3.2, SRS 5.4'teki
FR-4.9 – FR-4.11 ve NFR-14. Bu turun tamamı o bölümlerde tanımlıdır; sözde kodu ve
gerekçeyi birebir uygulama kaynağı olarak kullan.

## Çalışma kuralları

- **Tasarımdan sapma gerekiyorsa önce nedenini söyle, sonra uygula.** Sessizce sapma.
- **Gereksinim veya tasarım etkisi doğuran bir şey çıkarsa bana bildir**; dokümanı
  ben işlerim, sen `docs/` altındaki dosyaları değiştirmezsin.
- Şema değişikliği yalnızca Alembic göçüyle. Elle `ALTER TABLE` veya veritabanını
  silip yeniden kurmak yasak.
- Git: `add`, `commit`, `tag` senin; `push`, `remote add`, GitHub'da repo açma
  **asla**. Commit'lerde `Co-Authored-By` trailer'ı yok.
- Her oturum `PROGRESS.md` okumakla başlar, güncellemekle biter.
- Backend'de tip açıklamaları zorunlu, `ruff check` ve `ruff format --check` temiz.
  Frontend'de TypeScript strict; `any` yalnız gerekçeli yorumla.
- SDD'de tanımlı olmayan bir kütüphane veya desen ekleyeceksen **önce sor**.
- Sırları sohbete yazma.

## Bu projede tekrarlayan hata kalıpları

Bunlar geçmişte gerçekten bedeli ödenmiş kalıplardır; bu turdaki işler tam olarak
bu kalıpların bulunduğu yerlere dokunuyor.

1. **Aynı tanımın iki yerde durması.** Bir bilgi tek yerde durur, tüketiciler oradan
   alır. Bu turda iki yerde karşına çıkacak: (a) durdurulan işin sonucunu yazan blok,
   normal tamamlanma yolundaki yazma bloğunun aynısıdır — ikinci bir kopyasını
   çıkarma; (b) çalışan işin kimliği veritabanında zaten var, tarayıcıya ikinci bir
   kopyasını koyma.
2. **Sessiz veri kaybı / sessiz sıfırlanma.** Hata vermeyen, yanlış çalışan davranış.
   Bu turun varlık nedeni tam olarak bu: durdurma bugün bulunmuş çözümü sessizce
   atıyor.
3. **Bir bilgiyi yalnız düzenleme anında göstermek.** İz kalmıyorsa o bilgi yokmuş
   gibidir.

## Yapılacak işler

Dördü de birbirinden bağımsızdır; ayrı commit'ler hâlinde git. Sıra önerilen sıradır.

---

### İş 1 — Durdurmanın gecikmesiz uygulanması (SDD 5.4.2)

Bugün durdurma isteği ara çözüm geri çağırması içinde okunuyor; geri çağırma yalnız
çözücü daha iyi bir çözüm bulunca tetikleniyor, dolayısıyla istek iki iyileşme
arasında dakikalarca bekleyebiliyor. İş 2 kullanıcıya bir karar ekranı açacağı için
bu gecikme artık kabul edilemez (SRS NFR-14).

- Çözüm çağrısını işçi sürecinde ayrı bir iş parçacığına al. Ana döngü iş kaydının
  durumunu düzenli aralıklarla veritabanından **taze** okusun
  (`oturum.refresh(is_kaydi, ["durum"])` — düz alan okuması oturum önbelleğini
  döndürür, bu tuzağa daha önce düşüldü) ve durdurma görünce çözücünün aramayı
  dışarıdan sonlandıran çağrısını tetiklesin.
- **Önce doğrula:** kurulu OR-Tools sürümünde bu çağrının, arama başka bir iş
  parçacığında yürürken beklendiği gibi davrandığını küçük bir deneyle kanıtla.
  Davranmıyorsa geri çağırma yolunu koru ve bana söyle. **İki yolu birlikte bırakma**
  — biri seçilir (SDD 5.4.2).
- Süreçler arası iletişim yine yalnız veritabanı üzerinden; eklenen iş parçacığı tek
  bir sürecin içinde kalır, mimariyi değiştirmez (SDD 3.4.4).

**Kabul:** Uzun süren bir çözüm başlat, hiçbir iyileşme olmayan bir anda durdur;
durum birkaç saniye içinde değişiyor. Ölçülen gecikmeyi `PROGRESS.md`'ye yaz.

---

### İş 2 — Durdurma → üç seçenekli karar (SDD 4.2.4, 5.4.1, 6.3.2)

Bugün "Durdur" işi iptal ediyor ve o ana kadar bulunmuş çözümü kaydetmeden atıyor.
Yeni davranış: arama sonlanır, çözüm saklanır, kullanıcı karar verir.

**Veri katmanı**

- `cozum_isi.durum` ENUM'una `durduruldu` değeri.
- `cozum_isi.gecici_sonuc` JSONB NULL — atama listesi, kapsama açıkları, fazla kadro
  ve ceza dökümü.
- `cozum_isi.devam_kaynagi_is_id` INT FK NULL (kendine).
- `cozum_isi.bitis_zamani` bu göçte TIMESTAMPTZ'ye çevrilsin — SDD 4.2.4 onu
  TIMESTAMPTZ olarak tanımlıyor, kodda TIMESTAMP kalmış olabilir; kontrol et.
  Mevcut naif veri UTC yorumlanır (`USING ... AT TIME ZONE 'UTC'`).

`gecici_sonuc` **hiçbir okuma yüzeyinin kaynağı değildir.** Çizelge ızgarası, analiz
servisi, sürüm karşılaştırması, dışa aktarma ve çalışan paneli atama tablosundan
beslenmeye devam eder. Alan yalnız iki yerde kullanılır: işçi bir kez yazar, karar
bir kez okuyup boşaltır. Bunu doğrulayan bir test yaz.

**Servis ve uç noktalar**

- `POST /api/cozum/{is_id}/iptal` → `POST /api/cozum/{is_id}/durdur` olarak yeniden
  adlandır. Anlamı değişti: iptal değil, sonlandırma.
- `POST /api/cozum/{is_id}/karar` — gövde `{karar: kullan|at|devam,
  zaman_limiti_saniye?}`. SDD 5.4.1'deki `durdurma_karari_uygula` yordamını birebir
  uygula. Rol kapısı: yönetici + yönetim.
- `kullan` yolundaki yazma, normal tamamlanma yolunun kullandığı yazma bloğunun
  **aynısı** olmalı — ortak bir yordama çıkar, ikinci kopya yazma.
- `devam` yolunda yeni iş `gecici_sonuc`u çözücü ipucu (`AddHint`) olarak alır ve
  kullanıcının verdiği yeni zaman limitiyle başlar; `devam_kaynagi_is_id` dolar.
- Çözücü hiç çözüm bulamadan durdurulmuşsa `gecici_sonuc` boş kalır; `kullan`
  isteği hata döner. Boş bir sonucun sessizce boş çizelge olarak yazılması, kural
  ihlali içermeyen ama kapsaması sıfır olan bir sürüm üretir ve bu gerçekten
  çözülmüş bir çizelgeden ayırt edilemez.

**Arayüz (SDD 6.3.2)**

- "Durdur" artık karar panelini açar. Panel, çözüm tamamlanmış gibi tam ayrıntı
  gösterir: toplam ceza, hedef bazında döküm, kapsama açığı sayısı.
- Üç eylem: **Sonucu kullan** · **Sonucu at** (onay iste, geri alınamaz) · **Bu
  çözümden devam et** (yeni zaman limiti sorar).
- Çözüm bulunamadıysa "kullan" pasif ve nedeni panelde yazılı.
- **"Kaldığı yerden devam" yazma.** Devam, aramanın sürdürülmesi değil; bulunan
  çözümün ipucu verilerek yeni bir aramanın başlatılmasıdır. Ekranda yeni bir arama
  başladığı ve sürenin sıfırdan işlediği görünsün.

**Kabul:** Çözüm başlat, ilerlemeyi gör, durdur. Üç yolu da dene: (a) *kullan* →
atamalar yazılıyor, sürüm `cozuldu`, `gecici_sonuc` boş; (b) *at* → sürüm durdurma
öncesindeki hâliyle **birebir aynı**, hiçbir atama değişmemiş; (c) *devam* → yeni iş
başlıyor, sonucu eskisinden kötü değil, iki iş `devam_kaynagi_is_id` ile bağlı.

---

### İş 3 — Çalışan iş göstergesi kabukta (SDD 6.1, SRS FR-4.11)

Bugün çözüm sürerken başka bir ekrana geçilince iş durmuş gibi görünüyor. Backend
tarafında iş gerçekten sürüyor (ayrı serviste, iletişim veritabanı üzerinden);
sorun, yoklama döngüsünün Çözüm ekranı bileşeninde yaşayıp unmount'ta ölmesi ve iş
kimliğinin bileşen state'inde tutulması.

- **Önce teşhisi doğrula:** çözüm başlat, sayfayı tamamen yenile, `GET
  /api/cozum/{is_id}` hâlâ ilerliyor mu bak. İlerlemiyorsa teşhis değişir — dur ve
  bana söyle.
- `GET /api/cozum/aktif` — devam eden veya karar bekleyen işi döndürür, yoksa boş.
  Rol kapısı: yönetici + yönetim.
- Yoklamayı yönetici kabuğuna taşı. Gösterge üst çubukta: durum, geçen süre, o ana
  kadarki en iyi ceza; tıklanınca Çözüm ekranı açılır.
- **İş kimliğini tarayıcıya yazma** — ne state'e, ne localStorage'a (artifact
  kısıtından bağımsız olarak, bu bir tasarım kararı). Kabuk sunucuya sorar, kimlik
  yanıtın içinden gelir. Aynı bilginin ikinci kopyası, sayfa yenilendiğinde veya
  başka cihazdan girildiğinde ayrışır; bu hatanın nedeni tam olarak buydu.
- Karar bekleyen iş de göstergede görünmeli — kullanıcı başka ekrandayken durdurup
  unutursa, iş sessizce askıda kalmasın.

**Kabul:** Çözüm başlat, Tanımlar'a geç, Analiz'e geç, sayfayı yenile — gösterge her
ekranda ve yenilemeden sonra da duruyor, ilerleme akıyor. Çözüm bitince gösterge
sonucu bildiriyor.

---

### İş 4 — Yan menü kaydırma davranışı

Yan menü sayfayla birlikte aşağı inip çıkıyor; sabit kalması gerekiyor. Ana içerik
alanı kendi içinde kaydırılabilir olmalı, yan menü ekranda sabit dursun.

Bu bölgede daha önce bir hata yaşandı: `align-items: stretch` Dönem bloğunu görünür
alanın 2000px altına itmişti. Düzeltirken alt gruptaki Dönem bloğunun konumunu
kontrol et; yan menü `SPACE_BETWEEN` ile dağıtılıyor (üstte navigasyon, altta Dönem
bloğu — TASARIM_REFERANSI sürüm 4).

Kural sekmesi ve Analiz ekranı içerik yüksekliğini tam doldurur; bu ekranlarda
kaydırmanın gerçekten çalıştığını ayrıca doğrula.

**Kabul:** Uzun içerikli ekranlarda (Kural sekmesi, Analiz, Çizelge) sayfa
kaydırılırken yan menü yerinde kalıyor, Dönem bloğu görünür durumda.

---

## Turun bitiş kontrolü

- [ ] Dört iş de ayrı commit, conventional commits biçiminde
- [ ] `pytest` ve frontend testleri geçiyor; yeni davranışların testleri yazılmış
      (özellikle: geçici sonucun okuma yüzeylerine sızmadığı, "at" kararının sürümü
      değiştirmediği, `/api/cozum/aktif`in rol kapısı)
- [ ] `tests/test_yetkilendirme.py` yeni uç noktaları görüyor ve
      `EK_B_UC_NOKTALAR.md` yeniden üretilmiş (uç nokta sayısı değişti: `/iptal`
      gitti, `/durdur`, `/karar`, `/aktif` geldi)
- [ ] `ruff check` ve `ruff format --check` temiz
- [ ] `git status` temiz, sır yok, `PROGRESS.md` güncel
- [ ] Doküman etkisi doğuran bir şey çıktıysa `PROGRESS.md`'ye "DOKÜMAN BORCU"
      başlığı altında yazılmış (dosyaları sen değiştirmiyorsun)

## Bu turda yapmayacakların

Aşağıdakiler biliniyor ve sırada; bu turda **dokunma**:

- Saatlik sisteme geçiş (günlük 11 saat tavanı, yıllık 270 saat fazla çalışma
  kotası). Kural kataloğuna, talep matrisine ve `vardiya_tipi` tablosuna bu turda
  dokunulmaz — bir sonraki tur bunları baştan tanımlayacak.
- Önceki dönemlerin hesaba katılması (kümülatif adalet, B-01).
- Excel ve analiz dışa aktarma, çizelge görünümü, sürükle-bırak, özet ekranı,
  demo veri ve isimleri, müsaitlik kaydına belge ekleme.
- Tasarım sürüm 4'ün koda geçirilmesi (`@theme` font ve renk tokenleri).

Bunlardan biri yolda "aslında lazım" gibi görünürse uygulama; `PROGRESS.md`'ye not
düş ve devam et.
