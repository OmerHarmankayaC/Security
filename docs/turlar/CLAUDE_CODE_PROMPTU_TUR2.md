# Claude Code — İkinci Aşama, Tur 2: Doküman Borçları ve Test İzolasyonu

## Bağlam

BOTAŞ vardiya çizelgeleme karar destek aracının ikinci geliştirme aşamasındasın.
Tur 1 (durdurma akışı ve kabuk) tamamlandı; bu tur, o turun doğurduğu dört tasarım
borcunu koda yansıtır ve testleri geliştirme veritabanından ayırır. Kural
kataloğuna, çözücü modeline ve talep matrisine **dokunmaz**.

`docs/` altındaki dört kanonik doküman tek gerçek kaynaktır ve sen onlara
**dokunmazsın**. Bu turun gerektirdiği güncellemeler zaten yapıldı ve sana verildi:

- Yazılım Tasarım Dokümanı — sürüm **1.20** (4.2.4, 5.4.1, 6.3.2)
- Yazılım Gereksinim Belirtimi — sürüm **1.13** (FR-4.9)
- Ürün Backlog'u — sürüm **1.6** (üç yeni karar, B-20 eklendi)
- Proje Tanım Dokümanı — sürüm 1.2, değişmedi

**İlk işin:** bu sürüm numaralarını doğrula. Taşımıyorlarsa dur ve bana söyle.

Sonra oku: SDD 4.2.4 (`cozum_isi` tablosu ve altındaki iki paragraf), SDD 5.4.1'in
"Karar noktası yalnızca arama sürerken doğar" bölümü, SDD 6.3.2'deki karar paneli,
SRS FR-4.9, Backlog B-20.

Bu turda yaptığın işlerin üçü, tur 1'de senin bildirdiğin borçların karşılığıdır.
İkisinde tasarım senin uyguladığından farklı; farkın gerekçesi dokümanda yazılı.

## Çalışma kuralları

- Tasarımdan sapma gerekiyorsa **önce nedenini söyle**, sonra uygula.
- Gereksinim veya tasarım etkisi doğuran bir şey çıkarsa bana bildir; `docs/`
  altındaki dört kanonik dosyayı sen değiştirmezsin. `PROGRESS.md` ve `DAGITIM.md`
  senin dosyaların, onları güncelleyebilirsin.
- Şema değişikliği yalnızca Alembic göçüyle.
- Git: `add`, `commit`, `tag` senin; `push` ve `remote` **asla**.
  `Co-Authored-By` trailer'ı yok.
- Backend'de tip açıklamaları zorunlu, `ruff check` ve `ruff format --check` temiz.
  Frontend'de TypeScript strict.
- Sırları sohbete yazma.

## Hata kalıpları

Bu turun üç işi de doğrudan bu kalıpların üstünde:

1. **Aynı tanımın iki yerde durması** — iş 1 tam olarak bunun düzeltmesi.
2. **Sessiz veri kaybı / sessiz yanlış çalışma** — iş 1'deki boşaltma anı ve iş 3'ün
   tamamı bu yüzden.
3. **Metriğin veya durumun ayrım üretmemesi** — iş 2, anlamsız bir karar noktasını
   kaldırıyor.

---

## İş 1 — Çözücü ipucu ayrı sütuna (SDD 4.2.4)

Tur 1'de ipucu, yeni işin kendi `gecici_sonuc` alanında taşınıyor ve model kurulur
kurulmaz boşaltılıyordu. SDD 1.20 bunu değiştirdi.

- Alembic göçü: `cozum_isi.cozum_ipucu` JSONB NULL.
- `CozumServisi.baslat`'ın ipucu parametresi artık yeni işin `cozum_ipucu` alanına
  yazılır, `gecici_sonuc`a değil.
- İşçi, modeli kurarken `cozum_ipucu`'yu okuyup `AddHint` verir ve **alanı boşaltmaz**.
- Boşaltma, iş sonlandığında yapılır (`tamamlandi`, `uyarili`, `basarisiz`, `iptal`).
  Sonlanma tek bir yerden geçiyorsa oraya koy; birden çok yerden geçiyorsa önce tek
  yordama çıkar.

**Neden ayrı sütun:** `gecici_sonuc` durdurulmuş bir işin *çıktısı*, `cozum_ipucu`
yeni bir işin *girdisi*. Tek alanda taşınmaları hâlinde aynı değer bir işte
"kullanıcı kararı bekliyor", başka bir işte "modele verilecek ipucu" anlamına gelir;
alanın doluluğuna bakan bir sorgu henüz başlamamış bir işi karar bekliyor sanabilir.

**Bunu ayrıca kontrol et:** `GET /api/cozum/aktif` karar bekleyen işi neye göre
buluyor? Sorgu `gecici_sonuc IS NOT NULL` içeriyorsa `durum = DURDURULDU`'ya çevir.
Durum alanı bu bilgiyi zaten taşıyor.

**Neden boşaltma iş sonunda:** model kurulumunda silinirse, işçi yeniden başladığında
(servis yeniden başlatılır veya iş kuyruğa döner) iş ipucusuz devam eder — sonuç
sessizce kötüleşir ve bunu gösteren hiçbir iz kalmaz.

**Kabul:** "Devam et" ile başlatılan bir işte model kurulduktan sonra `cozum_ipucu`
hâlâ dolu; iş bitince boş. Test yaz.

---

## İş 2 — Arama başlamadan gelen durdurma doğrudan iptal (SDD 5.4.1, SRS FR-4.9)

Tur 1'de kuyrukta veya ön kontroldeki bir iş de `durduruldu` durumuna girip karar
bekliyordu. Artık girmeyecek.

- `POST /api/cozum/{is_id}/durdur`:
  - iş `kuyrukta` veya `on_kontrol` ise → durum doğrudan `iptal`, `gecici_sonuc`
    yazılmaz, karar sorulmaz.
  - iş `cozuluyor` ise → `durduruldu`, karar akışı tur 1'deki gibi.
  - iş başka bir durumdaysa → anlaşılır hata.
- **Durum geçişini koşullu tek bir UPDATE ile yap** (`WHERE durum = ...`) ve hangi
  satırın güncellendiğine göre yolu seç. Önce okuyup sonra yazarsan, tam o aralıkta
  işçi işi `on_kontrol`den `cozuluyor`a geçirmiş olabilir ve karar noktası doğması
  gereken bir iş sessizce iptal edilir.
- Arayüz: karar paneli yalnız `durduruldu`da açılır. Kuyruktaki iş durdurulduğunda
  panel hiç açılmaz, işin iptal edildiği bildirilir.

**Neden:** ortada saklanacak bir sonuç yokken karar paneli açmak, üç seçenekten
ikisini anlamsız kılıyor ("kullan" — sonuç yok) ve birini zaten var olan bir eylemin
uzun yoluna çeviriyor ("devam" — iptal edip yeniden başlatmak).

**Değişmeyen:** arama başlamış fakat ilk uygun çözüme ulaşamamışsa iş `durduruldu`
olur ve karar sorulur. Orada "devam" ipucusuz da olsa anlamlıdır — kullanıcı verdiği
sürenin yetmediğini görmüş, yeni bir limit veriyor olabilir.

**Kabul:** İş kuyruktayken durdur → iptal, panel yok. Çözücü çalışırken durdur →
`durduruldu`, panel var. İki yolu da test et.

---

## İş 3 — Testler ayrı veritabanına (Backlog B-20)

Testler şu anda geliştirme veritabanını kullanıyor. Bunun üç ayrı belirtisi çıktı ve
üçü de aynı kökten geliyor:

- Çözüm işçisi arka planda çalışırken test kuyruğundan iş kapıyor
  (`test_agirlik_kalibrasyonu` bu yüzden düştü).
- Test takımı kullanıcı hesaplarını siliyor (`kullanici.personel_id` personel
  tablosuna bağlı, `TRUNCATE CASCADE` hesapları da götürüyor).
- Kabul ölçümü ile testler birbirinin verisini bozuyor.

Yapılacak:

- Test takımı ayrı bir veritabanına bağlansın (ör. `vardiya_test`), ayrı bir ortam
  değişkeninden okusun.
- `conftest.py`, bağlantı adresinde test veritabanını görmezse **anlaşılır bir
  hatayla dursun**. Mevcut `VERI_TEMIZLIGINE_IZIN` kilidi kalkmaz; bu ikinci bir
  kapı. Sessizce geliştirme verisini temizlemek yerine yüksek sesle reddetmek esas.
- `DAGITIM.md`'ye ve varsa yerel kurulum adımlarına test veritabanının nasıl
  oluşturulacağı yazılsın.
- `scripts/kabul_olcumu.py` bu turda kapsam dışı — kendi kilidiyle kalır. Onu da
  değiştirmeye kalkma, ayrı bir karar gerektirir.

**Kabul:** Çözüm işçisi arka planda çalışırken tam takım geçiyor. Test koşumundan
sonra geliştirme veritabanındaki yönetim hesabı ve demo verisi yerinde.

---

## İş 4 — İzlenmeyen dosyaların depoya alınması

`git status`'ta duran üç yol commit'lensin:

- `docs/CLAUDE_CODE_PROMPTU_TUR1.md` ve bu dosya → `docs/turlar/` altına taşı, ki
  kanonik dört dokümanla karışmasınlar.
- `docs/yapilacaklar.md` → `docs/turlar/` altına.
- `docs/tasarim/logolar/` → olduğu yerde commit.

Bunlar neden öyle yapıldığının kaydı; depoda durmazlarsa iz kalmaz.

---

## Turun bitiş kontrolü

- [ ] Dört iş, ayrı commit'ler
- [ ] `pytest` tam takım geçiyor — **çözüm işçisi arka planda çalışırken de**
- [ ] Yeni testler: ipucunun model kurulumundan sonra yerinde durması ve iş bitince
      boşalması, kuyruktaki işin durdurulmasının iptal olması, çözülürken
      durdurmanın karar noktası doğurması
- [ ] `ruff check`, `ruff format --check`, `tsc -b`, `oxlint` temiz
- [ ] `git status` temiz, sır yok, `PROGRESS.md` güncel
- [ ] Doküman etkisi doğuran bir şey çıktıysa `PROGRESS.md`'de "DOKÜMAN BORCU"
      başlığı altında
- [ ] **Sunucuya dağıtım YAPILMAZ.** Bu turdan sonra iki göç birikmiş olacak
      (`b6e2f81d3c07` ve bu turdaki yeni göç). `PROGRESS.md`'ye ikisini de yaz;
      dağıtım kararı bende.

## Bu turda yapmayacakların

- Saatlik sisteme geçiş (günlük 11 saat tavanı, yıllık 270 saat fazla çalışma
  kotası). Kural kataloğuna, talep matrisine ve `vardiya_tipi` tablosuna
  dokunulmaz — bir sonraki tur bunları baştan tanımlayacak.
- Önceki dönemlerin hesaba katılması (kümülatif adalet, B-01).
- Excel ve analiz dışa aktarma, çizelge görünümü, sürükle-bırak, özet ekranı,
  demo veri ve isimleri, müsaitlik kaydına belge ekleme.
- Tasarım sürüm 4'ün koda geçirilmesi (`@theme` font ve renk tokenleri).
- `scripts/kabul_olcumu.py`'nin veritabanı davranışı.

Bunlardan biri yolda "aslında lazım" gibi görünürse uygulama; `PROGRESS.md`'ye not
düş ve devam et.
