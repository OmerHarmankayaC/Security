# İlerleme Günlüğü

Her oturum sonunda buraya bir kayıt eklenir: tarih, tamamlanan, kalan/ertelenen,
sıradaki oturumun ilk işi. Yeni oturum bu dosyayı okuyarak başlar.

---

## 2026-08-06 — Sprint 0: İskelet Kurulumu

**Tamamlanan:**
- Dört referans doküman (Charter, SRS, Backlog, SDD) okundu.
- Depo yapısı kuruldu: `backend/`, `frontend/`, `docs/`, `scripts/`.
- Backend: FastAPI iskeleti (`app/main.py`), katmanlı klasör yapısı
  (`routers/`, `services/`, `repositories/`, `models/` — SDD 3.2'deki
  ayrışıma birebir), `/health` uç noktası, `pydantic-settings` ile ortam
  değişkeni tabanlı yapılandırma (SDD 3.4.5).
- SQLAlchemy `Base` + engine/session kurulumu (`app/db.py`), Alembic
  entegre edildi (`app/db.Base.metadata` autogenerate hedefi, DB URL
  `Ayarlar`'dan okunuyor), ilk boş göç oluşturuldu.
- Frontend: Vite + React + TypeScript strict mode (`strict`,
  `noUncheckedIndexedAccess` eklendi — varsayılan şablonda kapalıydı),
  vitrin içerikleri temizlendi, sade bir ana sayfa render ediliyor.
- `ruff.toml` (py312 hedefi, `alembic/versions` otomatik üretilen kod
  olduğu için lint kapsamı dışında bırakıldı), `pyproject.toml`
  (bağımlılık sürüm sabitleme, `ortools==9.14.6206` — 9.11.4210 bu
  makinedeki Python 3.13 için PyPI'de yoktu, en yakın uyumlu sürüme
  çıkıldı), `.env.example`, kapsamlı `.gitignore`.
- `VERSIONS.md`: Python/Node/PostgreSQL sürüm sabitleme dosyası (SDD
  3.4.1'de sözü edilen "sürüm dosyası").
- `scripts/kurulum.sh`: backend venv + bağımlılıklar + göç + lint + test,
  frontend install + tip kontrolü — tek komutla.
- `README.md` yazıldı.
- Uçtan uca doğrulama: geçici bir Docker PostgreSQL container'ı ile
  `scripts/kurulum.sh` baştan sona çalıştırıldı — `alembic upgrade head`
  hatasız tamamlandı, backend testleri (`pytest`) ve `ruff check/format`
  temiz geçti, `/health` gerçek sunucudan 200 döndürdü, frontend `tsc
  --noEmit` ve `vite build` temiz geçti. Container test sonrası silindi
  (kalıcı bir servis değil, yalnızca doğrulama amaçlıydı).
- `git init` yapıldı, ilk commit atılacak (bu dosyanın hemen ardından).

**Sapmalar / notlar (tasarımdan sapma değil, ortam notu):**
- Geliştirme makinesinde Python 3.12 yerine 3.13.11 mevcut; `pyproject.toml`
  `requires-python = ">=3.12"` olarak ayarlandı, bu ikisini de kapsıyor.
  Gösterim sunucusunda 3.12 kullanılabilir, sorun teşkil etmez.
- `ortools` sürümü plan/SDD'de belirtilmediği için PyPI'de bu ortamla
  (Python 3.13, macOS) uyumlu en güncel kararlı sürüm seçildi
  (9.14.6206). Sprint 2'de çözücü adaptörü yazılırken bu sürümün API'si
  ile SDD 5.3'teki sözde kod arasında uyumsuzluk çıkarsa burada not
  düşülecek.
- Yerel makinede PostgreSQL kurulu değil; doğrulama için geçici bir Docker
  container kullanıldı ve iş bitince silindi. Kalıcı geliştirme için
  kullanıcının ya yerel bir PostgreSQL 16 kurması ya da kalıcı bir
  container/Postgres.app ayağa kaldırması gerekiyor — bu, dağıtım
  tasarımını (SDD 3.4.1: konteynerleştirme kullanılmaz) etkilemez, yalnızca
  bu geliştirme makinesindeki günlük iş akışını ilgilendirir.

**Kalan / ertelenen:** Yok — Sprint 0 kapsamındaki tüm maddeler tamamlandı.

**Sıradaki oturumun ilk işi:** Sprint 1, Gün 1 — Veritabanı Şeması.
SDD 4.2'deki 15 tabloyu SQLAlchemy modeli olarak (Türkçe alan adlarıyla)
yaz, her tablo için Alembic göçü oluştur, `personel_yetkinlik` bileşik
anahtarını ve `atama` üzerindeki `(surum_id, personel_id, tarih)` benzersizlik
kısıtını uygula (SDD 4.2.4). Önce SDD Bölüm 4 (Veri Tasarımı / Veri
Sözlüğü) tam metnini oku — bu oturumda yalnızca girişi okundu, tablo
tanımlarının tamamı henüz çıkarılmadı.

---

## 2026-08-06 — Sprint 1, Gün 1: Veritabanı Şeması

**Tamamlanan:**
- SDD 4.2 (Veri Sözlüğü) tam metni okundu (4.2.1–4.2.4).
- SDD'de veri sözlüğünde fiilen **16 tablo** bulundu (plandaki "15 tablo"
  ifadesi muhtemelen `personel_yetkinlik` ilişki tablosunu ayrı saymıyor;
  aşağıda not düşüldü, tasarımdan sapma değil — dokümandaki her tablo
  birebir uygulandı).
- `app/models/` dört modüle bölündü (SDD 4.1'deki dört varlık kümesiyle
  birebir): `tanim.py` (personel, yetkinlik, personel_yetkinlik, bina,
  gorev_noktasi, vardiya_tipi, talep, ozel_gun), `girdi.py` (musaitlik,
  tercih), `kural.py` (kural), `sonuc.py` (donem, cizelge_surumu, atama,
  cozum_isi, kapsama_acigi). Ortak `olusturma_zamani`/`guncelleme_zamani`
  için `ortak.py`'de bir mixin (`ZamanDamgasiKarisimi`).
- Alan adları veri sözlüğüyle birebir (Türkçe). ENUM alanları Python
  `enum.StrEnum` + SQLAlchemy native Postgres ENUM olarak modellendi.
  `kural.parametreler`, `cozum_isi.ceza_dokumu` ve `kural_anlik_goruntu`
  `JSONB` (SDD 4.2.3/4.2.4'te açıkça istenen tip).
- `personel_yetkinlik`: bileşik birincil anahtar (`personel_id`,
  `yetkinlik_id`), ayrı `id` yok — SDD'deki "Birincil anahtar iki alanın
  birleşimidir" notuna birebir.
- `ozel_gun`: `tarih` alanı birincil anahtar (SDD'de ayrı bir kimlik alanı
  tanımlanmamış).
- `atama`: `(surum_id, personel_id, tarih)` üzerinde `UniqueConstraint`
  (SDD 4.2.4 — H1'in veritabanı seviyesinde güvencesi).
- `alembic revision --autogenerate` ile tek göç üretildi
  (`b413bb80a4bd_kural_katalogu_veri_modeli.py`), Sprint 0'daki boş göç
  silindi (henüz kimse üzerine göç zinciri kurmamıştı, tek commit'lik
  bir depoda güvenli bir işlemdi).
- **Düzeltme:** Alembic autogenerate, Postgres ENUM tiplerini
  `downgrade()`'de otomatik bırakmıyor (bilinen bir kısıt) — bu, gerçek
  bir `upgrade → downgrade → upgrade` denemesinde `type already exists`
  hatasıyla ortaya çıktı. Göç dosyasının `downgrade()` fonksiyonuna dokuz
  enum tipini (`kuraltipi`, `cizelgesurumudurumu`, `atamakaynagi`,
  `cozumisidurumu`, `musaitlikdilimi`, `musaitliktipi`, `tercihtipi`,
  `tercihdurumu`, `guntipi`) bırakan elle eklenmiş satırlar kondu. Bundan
  sonraki her ENUM içeren göçte aynı düzeltme gerekecek — bu bir örüntü,
  hatırlatma için burada not edildi.
- Doğrulama: geçici Docker PostgreSQL container'ında `upgrade head →
  downgrade base → upgrade head` döngüsü hatasız tamamlandı.
- `tests/test_veritabani_semasi.py`: iki test — (1) personel + yetkinlik
  + personel_yetkinlik INSERT/SELECT, (2) `atama` benzersizlik kısıtının
  aynı `(surum_id, personel_id, tarih)` için ikinci kaydı `IntegrityError`
  ile reddettiğini doğrulayan test. Testler canlı bir PostgreSQL
  gerektiriyor; bağlanılamazsa `pytest.skip` ile atlanıyor (CI'da veya bu
  makinede kalıcı bir Postgres yokken kırmızı görünmesin diye).
- `ruff check`, `ruff format --check`, `pytest -q` temiz (3 test geçti).
  Test container'ı doğrulama sonrası silindi.

**Sapmalar / notlar:**
- 15 vs 16 tablo notu yukarıda — kod, plan metnindeki sayıyı değil SDD veri
  sözlüğünü esas aldı.
- Modellerde şimdilik `relationship()` tanımlanmadı, yalnızca `ForeignKey`
  sütunları var. SDD 5.x'teki servis/depo katmanı yazılırken ihtiyaç
  çıkarsa (ör. ORM üzerinden gezinme) eklenecek; şu an için veri sözlüğü +
  FK'ler kabul kriterini karşılıyor ve gereksiz karmaşıklık eklemekten
  kaçınıldı.

**Kalan / ertelenen:** Yok — Gün 1 kapsamındaki tüm maddeler tamamlandı.

**Sıradaki oturumun ilk işi:** Sprint 1, Gün 2 — Kural Arayüzü ve Zorunlu
Kısıtlar (H1–H8). SDD 5.1'deki `Kural` temel sınıfını ve kural kayıt
defterini yaz, SDD Ek A'daki H2 örneğini şablon alarak H1–H8'i uygula
(bu aşamada `modele_ekle` CP-SAT model nesnesini henüz tam almayabilir,
ama imza ve `dogrula` metodu tam çalışır olmalı). Önce SDD 5.1 ve Ek A'yı,
SRS Bölüm 4.2 (H1–H8 tanımları, zaten bu oturumda okundu) ve
`app/models/kural.py`'deki `Kural` tablosunu tekrar gözden geçir.

---

## 2026-08-06 — Sprint 1, Gün 2: Kural Arayüzü ve Zorunlu Kısıtlar (H1–H8)

**Not:** Bu oturumdan itibaren git commit başlıkları ve açıklamaları
İngilizce yazılıyor (kullanıcı talebi); dokümantasyon, kod tanımlayıcıları
ve yorumlar Türkçe kalmaya devam ediyor.

**Tamamlanan:**
- SDD 5.1 (`kurallari_yukle` sözde kodu) ve Ek A (H2/S2 uygulama örnekleri)
  ile SRS 3.3.5'teki kural parametre varsayılanları okundu:
  H2 `asgari_dinlenme_saati=16`, H3 `azami_ardisik_gece=3`,
  H4 `azami_ardisik_calisma_gunu=6`, H5 `azami_haftalik_saat=45`,
  H6 `haftalik_asgari_izin_gunu=1`.
- Yeni paket `app/kurallar/` — ORM'den bağımsız, kural motoruna özgü:
  - `temel.py`: `Kural` ABC'si (`kimlik`, `tip`, `parametreler`, `agirlik`,
    `modele_ekle`, `dogrula`), `ZorunluKural`/`EsnekHedef` alt sınıfları
    (SDD 3.2.1, Ek A'daki `ZorunluKural`/`EsnekHedef` kalıbı), `Ihlal`
    dataclass'ı.
  - `kayit_defteri.py`: `@kayitli("H1")` sınıf dekoratörüyle kimlik→sınıf
    kaydı, `bul()`, ve SDD 5.1'deki `kurallari_yukle()` sözde kodunun
    birebir uygulaması (tanımsız kimlikte `ValueError`).
  - `baglam.py`: `Baglam` — vardiya süresi/gece bayrağı, görev noktası
    ön koşulu, personel yetkinlik/aktiflik, müsaitlik kayıtlarını taşıyan,
    veritabanından bağımsız hafif bir çalışma zamanı yapısı. `saat_farki`,
    `vardiya_araligi` (TD-1: gece yarısını aşan vardiya başlangıç gününe
    yazılır), `musait_mi` (TD-4: tam_gun/öğleden önce/öğleden sonra dilim
    kesişimi + personel aktiflik aralığı) ve `yetkin_mi` yardımcı
    metotları.
  - `yardimcilar.py`: H3/H4 için ortak "ardışık koşu" tarayıcısı,
    H5/H6 için ortak "kayan 7 günlük pencere" tarayıcısı (aynı algoritma
    iki kural çiftinde tekrar ettiği için ortak fonksiyona çıkarıldı).
  - `zorunlu.py`: H1–H8'in tamamı, her biri `@kayitli("Hx")` ile kayıtlı.
    `modele_ekle`, `ZorunluKural`'ın `NotImplementedError` fırlatan
    varsayılanını kullanıyor (Sprint 2 Gün 6'da CP-SAT ile
    tamamlanacak — plan buna açıkça izin veriyor); `dogrula` tamamı
    çalışır durumda.
- H6 formülasyon notu: SRS 4.2'de H6 "parametresizdir" deniyor ama
  SRS 3.3.5'teki parametre tablosu `haftalik_asgari_izin_gunu` adında bir
  parametre listeliyor (varsayılan 1, ki 7-1=6 ile SRS 4.2'deki `≤ 6`
  formülüyle örtüşüyor). İki kaynak arasındaki bu küçük tutarsızlığı,
  parametreyi kullanan ve varsayılanla aynı sonucu üreten yorumla
  çözdüm (tasarımdan sapma değil, doküman içi küçük bir isim
  tutarsızlığı).
- `tests/test_kurallar_zorunlu.py`: H1–H8'in her biri için en az bir
  ihlal-var ve bir ihlal-yok senaryosu, elle kurulan `Baglam`/`AtamaKaydi`
  örnekleriyle (23 test) — veritabanı gerektirmez. Ayrıca kayıt
  defterinin H1–H8'in tümünü içerdiğini, `kurallari_yukle`'nin doğru
  nesne ürettiğini ve tanımsız kimlikte hata verdiğini, `modele_ekle`'nin
  henüz `NotImplementedError` fırlattığını doğrulayan testler.
- `ruff check`, `ruff format --check`, `pytest -q` temiz (toplam 24 test
  geçti, 2 tanesi — Gün 1'den kalan DB testleri — canlı PostgreSQL
  olmadığı için atlandı, beklenen davranış).

**Sapmalar / notlar:**
- H6 parametre adı tutarsızlığı yukarıda not edildi.
- `modele_ekle` bu oturumda kasıtlı olarak `NotImplementedError` fırlatıyor
  (plan buna izin veriyor); Sprint 2 Gün 6'da CP-SAT model nesnesiyle
  gerçek kısıt ifadeleri eklenecek.

**Kalan / ertelenen:** Yok — Gün 2 kapsamındaki tüm maddeler tamamlandı.

**Sıradaki oturumun ilk işi:** Sprint 1, Gün 3 — Esnek Hedefler (S1–S8).
SDD Ek A'daki S2 örneğini şablon alarak `app/kurallar/esnek.py` içinde
S1–S8'i yaz (S1'in özel davranışına dikkat: SRS 4.3'te talep hem üst
sınır/zorunlu hem alt sınır/esnek olarak formüle ediliyor — bu oturumda
zaten okundu). Her esnek hedef için `dogrula`/ceza hesaplama birim testi
ekle. Önce SRS 4.3 (S1–S8 tanımları) ve SDD Ek A'daki S2 örneğini tekrar
gözden geçir; `EsnekHedef` taban sınıfı zaten `app/kurallar/temel.py`'de
hazır.

---

## 2026-08-06 — Sprint 1, Gün 3: Esnek Hedefler (S1–S8)

**Tamamlanan:**
- SRS 4.3 (S1–S8 tam formülasyonu) ve 4.4 (amaç fonksiyonu) okundu.
- `app/kurallar/esnek.py`: S1–S8'in tamamı, her biri `@kayitli("Sx")` ile
  kayıtlı, `dogrula` SDD Ek A'daki S2 örneğiyle tutarlı biçimde **ağırlıksız
  (ham) ceza büyüklüğü** döndürüyor (`w1..w8` ile çarpım, amaç fonksiyonu/
  ceza dökümü raporlaması gibi sonraki bir katmanın işi — Sprint 2 Gün 6 /
  Sprint 3 Gün 12).
- **`Ihlal` veri sınıfı genişletildi** (`app/kurallar/temel.py`):
  `personel_id`/`tarih` artık opsiyonel (varsayılan `None`) ve sınıf
  `kw_only=True` yapıldı. Gerekçe: SDD Ek A'daki `Ihlal('S2', ceza=acik)`
  örneği tek bir kişi/güne bağlı olmayan toplu ihlaller üretiyor (S1
  kapsama açığı, S2/S3 adalet sapması). H1–H8'deki tüm `Ihlal(...)`
  çağrıları (zorunlu.py + yardimcilar.py + testler) anahtar kelime
  argümanlarına çevrildi; pozisyonel imza kw_only ile artık geçersiz.
  Mevcut testler değişiklik sonrası tekrar çalıştırıldı, hepsi geçti.
- **`Baglam` genişletildi** (`app/kurallar/baglam.py`) S1–S8'in ihtiyaç
  duyduğu veriyle:
  - `talep: dict[(tarih, vardiya_tipi_id, nokta_id), gereken_sayi]` —
    istisna/genel talep satırı çözümlemesi (SDD 4.2.1) Baglam'ı kuran
    tarafın (repository/servis, Sprint 1 Gün 4+) sorumluluğu; Baglam
    zaten çözümlenmiş değeri alır.
  - `donem_baslangic`/`donem_bitis` + `donem_icinde()` — TD-6 (adalet
    ufku ısıtma penceresini kapsamaz).
  - `ozel_gunler` + `hafta_sonu_mu()` — TD-3.
  - `tercihler: list[TercihKaydi]` — yalnızca **onaylanmış** tercihler
    girer (filtreleme de yine Baglam'ı kuran tarafın işi, SRS S5).
  - `onceki_atamalar: list[AtamaKaydi] | None` — yalnızca yeniden çözüm
    doğrulamasında dolu (S8).
  - `GorevNoktasiBilgisi.bina_id`, `PersonelBilgisi.haftalik_hedef_saat`
    alanları eklendi (S6, S4 için gerekliydi; geriye dönük uyumlu —
    ikisi de sondan eklenen varsayılanlı alanlar).
- `tests/test_kurallar_esnek.py`: S1–S8'in her biri için en az bir
  ceza-üretir ve bir ceza-üretmez senaryosu (24 test), elle kurulan
  `Baglam`/`AtamaKaydi`/`TercihKaydi` örnekleriyle.
- `ruff check`, `ruff format --check`, `pytest -q` temiz: toplam 50 test
  (48 geçti, 2'si canlı PostgreSQL olmadığı için beklenen şekilde
  atlandı).

**Sapmalar / notlar (varsayım olarak işaretlendi, mentör onayı gerekebilir):**
- **S4 dönemlik hedef formülü:** SRS yalnızca "haftalık hedef saatinden
  türetilen dönemlik hedef" diyor, kesin formül vermiyor. Orantılama
  kullandım: `hedef_saat[p] = haftalik_hedef_saat[p] * (donem_gun_sayisi / 7)`.
  Mentör onayı bekleyen bir varsayım.
- **S6'nın iki ayrı ağırlığı (w6, w6b):** SRS formülü `w6·Σdegisim +
  w6b·Σbina_degisim` şeklinde iki ayrı ağırlık kullanıyor, ama `kural`
  tablosunda (SDD 4.2.3) her kural için tek bir `agirlik` sütunu var. Bu
  oturumda `dogrula` her iki ihlal türünü de (vardiya tipi değişimi,
  bina değişimi) ham `ceza=1` ile, aynı `S6` kimliğiyle, yalnızca
  `aciklama` metniyle ayrışan ayrı `Ihlal` kayıtları olarak döndürüyor —
  ağırlıklandırma bu katmanda yapılmıyor zaten (diğer tüm kurallarla
  tutarlı). Ancak Sprint 2 Gün 6'da amaç fonksiyonu kurulurken ya da
  Sprint 3 Gün 12'de ceza dökümü hesaplanırken w6/w6b ayrımı somut bir
  yer bulmalı; şema tek ağırlık sütunu içerdiği için bu noktada bir karar
  gerekecek (iki ayrı kural kaydı mı, yoksa `parametreler` JSONB alanında
  ikinci bir ağırlık mı). Şimdilik ilerlemeyi bloklamıyor, ama net.
  **Güncelleme (2026-08-06, Gün 4 başlangıcı): bu karar netleşti, bkz.
  aşağıdaki not.**
- Bu iki nokta dışında kalan tüm formüller SRS 4.3'ten birebir.

**Kalan / ertelenen:** Yok — Gün 3 kapsamındaki tüm maddeler tamamlandı.

---

## 2026-08-06 — Sprint 1 Gün 3 açık kararının çözümü: S6 → S6 + S6b

Kullanıcı, Gün 3'te not düşülen w6/w6b açık kararını netleştirdi: **S6 iki
ayrı kural kaydına bölünüyor**, `kural` tablosunun tek-ağırlık-sütunu
kısıtına uyacak şekilde.

- **S6 — Vardiya deseni tutarlılığı:** artık yalnızca ardışık günlerde
  vardiya tipi değişimini değerlendiriyor. `agirlik = 10`.
- **S6b — Bina tutarlılığı** (yeni kural): eskiden S6'nın içinde olan
  bina_degisim mantığı buraya taşındı, ayrı `@kayitli("S6b")` ile kayıtlı.
  `agirlik = 6`.
- İkisi de artık ortak bir `_ardisik_gun_ciftleri()` yardımcı
  fonksiyonundan (yeni, `app/kurallar/esnek.py`) beslenip kendi tek
  kontrolünü yapıyor — kod tekrarı yerine ortak "ardışık gün çifti"
  tarama mantığı paylaşılıyor.
- `tests/test_kurallar_esnek.py`: S6 testleri ikiye ayrıldı; her sınıf
  için ayrı ceza-üretir/ceza-üretmez senaryosu, artı S6'nın bina
  değişimini, S6b'nin vardiya tipi değişimini görmezden geldiğini
  doğrulayan iki çapraz test.
- `app/kurallar/kayit_defteri.py`'ye `tum_kimlikler()` eklendi (kayıtlı
  tüm kimliklerin sıralı listesi) ve kayıt defterinin tam olarak on yedi
  kimlik içerdiğini (H1–H8, S1–S8, S6b) doğrulayan bir test yazıldı.
- `ruff check`, `ruff format --check`, `pytest -q` temiz: 55 test (53
  geçti, 2'si DB gerektirdiği için beklenen şekilde atlandı).

**Kalan / ertelenen:** Yok.

**Sıradaki oturumun ilk işi:** Sprint 1, Gün 4 — Tanım Yönetimi CRUD
API'leri. SDD Ek B'deki uç noktalardan tanım yönetimi grubunu uygula:
`/api/personel`, `/api/yetkinlik`, `/api/bina`, `/api/nokta`,
`/api/vardiya-tipi`, `/api/talep`, `/api/kural`. SRS FR-1.1–FR-1.14'ü
karşıla, özellikle FR-1.9 (yük göstergesi hesaplaması — SDD 3.3.6'daki
formülü kullan). Depo katmanı (repository) deseni: SQL yalnızca bu
katmanda. Önce SDD Ek B (API özeti) ve SRS FR-1.x'i, ayrıca depo
katmanının kural kataloğuna nasıl bağlanacağını (`kurallari_yukle`'nin
beklediği `KuralSatiri` protokolü, `app/kurallar/kayit_defteri.py`) gözden
geçir.

---

## 2026-08-06 — Sprint 1, Gün 4: Tanım Yönetimi CRUD API'leri

**Not:** "SDD 3.3.6'daki formülü kullan" ifadesi plan metninde vardı, ama
SDD'de 3.3.6 diye bir bölüm yok — bu bölüm numarası SRS'e ait ("SRS
3.3.6 Kadro Büyüklüğü Analizi"). Muhtemelen plan yazılırken doküman
karışmış; SRS 3.3.6'yı kullandım (bkz. aşağıda).

**Tamamlanan:**
- SDD Ek B (API özeti tablosu) ve SRS 5.1 (FR-1.1–FR-1.14) tam metni
  okundu; SRS 3.3.6'nın (kadro büyüklüğü analizi) tüm sayısal örneği
  (144 kişi-vardiya, 1.152 saat, 29 kişilik asgari kadro) FR-1.9'un
  referans doğrulaması olarak kullanıldı.
- **Depo katmanı** (`app/repositories/`): `TabanDepo` — generic CRUD
  (`tumunu_getir`, `getir`, `olustur`, `guncelle`, `sil`); `tanim.py`
  (`YetkinlikDeposu`, `BinaDeposu`, `VardiyaTipiDeposu`,
  `GorevNoktasiDeposu`, `PersonelDeposu`, `TalepDeposu`); `kural.py`
  (`KuralDeposu`, `aktif_kurallari_getir()` — SDD 5.1'deki
  `kurallari_yukle()`'nin beklediği veri kaynağı).
- **Şema düzeyinde DELETE kararı:** Ek B tüm tanım kaynaklarında DELETE
  yöntemini listeliyor, ama veri sözlüğüne bakıldığında yalnızca
  `personel` (`aktif_bitis`) ve `gorev_noktasi` (`aktif`) alanlarında
  açık bir pasifleştirme alanı var (FR-1.1: "pasifleştirilmesine imkân
  vermelidir"). Bu ikisinde DELETE, satırı silmek yerine bu alanı
  güncelliyor (`PersonelDeposu.sil`, `GorevNoktasiDeposu.sil` override
  edildi). `yetkinlik`/`bina`/`vardiya_tipi`'de böyle bir alan
  tanımlanmadığı için DELETE gerçek satır silme; FK ile referans
  edildiğinde veritabanı bunu zaten engelliyor. Tasarımdan sapma değil,
  veri sözlüğündeki mevcut alanların doğal sonucu.
- **Model revizyonu:** `Personel.yetkinlikler` many-to-many
  `relationship` eklendi (`app/models/tanim.py`) — Sprint 1 Gün 1'de
  "henüz relationship tanımlanmadı" denmişti, bugün API yanıtlarında
  personelin yetkinlik kimliklerini döndürmek için gerekti. Şema
  değişikliği yok (yalnızca ORM navigasyonu), Alembic göçü gerekmedi;
  `alembic check` ile doğrulandı.
- **`app/db.py`:** `oturum_al()` artık istek başarıyla bitince
  `commit()`, hata halinde `rollback()` yapıyor (SDD 3.2: servis
  metodunun başlattığı işlem ya bütünüyle işlenir ya geri alınır).
  Önceden yalnızca `close()` yapıyordu; router'ların her yerde elle
  commit çağırmasını önlemek için bu katmana taşındı.
- **`app/services/vardiya_hesaplari.py`** (saf, DB'siz): `sure_saat_hesapla`
  (FR-1.3) ve `gece_mi_oner` (FR-1.4/TD-2: 20:00–06:00 penceresiyle
  kesişim ≥4 saatse öner). Not: TD-2'nin literal eşiği yüzünden akşam
  vardiyası (16:00–24:00) da tam 4 saat kesiştiği için "gece" olarak
  önerilebiliyor — SRS'in kendi örneğinde akşam gece sayılmıyor, ama bu
  yalnızca bir öneri ("nihai değeri kullanıcı belirler"); bug değil, TD-2
  formülünün doğal bir sınır durumu. Birim testinde not edildi.
- **`app/services/yuk_gostergesi.py`** (saf, DB'siz, FR-1.9): SRS
  3.3.6'nın yöntemini genelleştirdi — her talep hücresi gün tipinin
  haftalık tekrarıyla (hafta_ici×5, hafta_sonu×2, resmi_tatil hariç)
  çarpılıp haftalık kişi-vardiya/kişi-saate çevriliyor; asgari kadro,
  kişi başına azami haftalık vardiyanın (H5 saat tavanı VE H6 asgari
  izin günü kısıtlarından türetilip küçük olanı alınarak) toplam
  kişi-vardiyaya bölünüp yukarı yuvarlanmasıyla bulunuyor. Bu formül,
  SRS 3.3.6'nın 144/1.152/29 sayılarını **birebir** üretiyor
  (`tests/test_yuk_gostergesi.py`) — güçlü bir doğrulama.
- **`TanimServisi`** (`app/services/tanim_servisi.py`): repository +
  hesaplama katmanlarını birleştiriyor; personel oluşturma/güncellemede
  yetkinlik ataması, vardiya tipinde süre/gece_mi türetme, talep
  hücresi upsert + yük göstergesi, kural parametresi okuma (H5/H6
  varsayılanlarıyla, DB'de henüz satır yoksa SRS 3.3.5 varsayılanlarına
  düşüyor).
- **`app/routers/tanim.py`**: SDD 3.2'deki tek `tanim_router` — Ek
  B'deki tüm tanım yönetimi uç noktaları (`/api/personel`,
  `/api/yetkinlik`, `/api/bina`, `/api/nokta`, `/api/vardiya-tipi`
  tam CRUD; `/api/talep`, `/api/kural` yalnız GET/PUT, Ek B'yle birebir).
  Yönlendiriciler ince: şema doğrular, tek bir servis/depo metodunu
  çağırır.
- Pydantic şemaları (`app/schemas/tanim.py`, `app/schemas/kural.py`):
  her kaynak için Olustur/Guncelle/Oku üçlüsü.
- Testler:
  - `tests/test_vardiya_hesaplari.py` (5 test, DB'siz) — süre hesabı ve
    gece_mi önerisi.
  - `tests/test_yuk_gostergesi.py` (4 test, DB'siz) — SRS 3.3.6'nın
    tam güvenlik-personeli talep matrisi açılıp 144/1.152/29 sayılarının
    birebir üretildiği doğrulandı; tekil tarih istisnası ve resmi tatil
    satırlarının haftalık yüke girmediği ayrıca test edildi.
  - `tests/test_tanim_api.py` (8 test, canlı PostgreSQL gerektirir) —
    her kaynak için mutlu yol + personel/yetkinlik/görev noktası/talep
    zincirinin API üzerinden kurulabildiğini doğrulayan Gün 4 kabul
    testi + personel/nokta soft-delete + 404 senaryoları + kural PUT.
  - `tests/conftest.py` eklendi: `pg_yoksa_atla()` ortak DB-atlama
    yardımcısı; `test_veritabani_semasi.py` bunu kullanacak şekilde
    küçük bir refactor ile güncellendi (davranış değişmedi).
- Doğrulama: geçici Docker PostgreSQL container'ında `alembic upgrade
  head`, tüm test paketi (72 test, hepsi geçti) iki kez art arda
  (idempotentlik için testlerde `uuid` sonekli benzersiz değerler
  kullanıldı), `alembic check` (şema kayması yok), ve gerçek `curl`
  zinciriyle (yetkinlik→bina→nokta→vardiya tipi→personel→talep) elle
  doğrulama. Container silindi. DB'siz ortamda 62 geçti + 10 atlandı
  (beklenen).
- `ruff check`, `ruff format --check` temiz.

**Sapmalar / notlar (mentör onayı gerekebilecek varsayımlar):**
- FR-1.9 asgari kadro formülü SRS'te net bir matematiksel ifadeyle
  verilmiyor, yalnızca anlatı + tek bir sayısal örnek var. Yukarıdaki
  yöntemle bu örneği birebir ürettim, ama genel (farklı vardiya
  süreleri karışık) durumlarda "ortalama vardiya süresi" yaklaşıklığı
  kullanılıyor — SDD/SRS'te bu genellemeye dair açık bir talimat yok.
- TD-2'nin akşam vardiyasını da "gece" olarak önerebilmesi (yukarıda
  açıklandı) — muhtemelen mentör görüşmesinde netleşecek bir sınır
  durumu.

**Kalan / ertelenen:** Yok — Gün 4 kapsamındaki tüm maddeler tamamlandı.

**Sıradaki oturumun ilk işi:** Sprint 1, Gün 5 — Demo Veri Üreteci ve
Sprint 1 Checkpoint. SDD 3.3'teki güvenlik personeli senaryosunu (bu
oturumda `test_yuk_gostergesi.py` için zaten tam olarak modellendi —
oradaki `_guvenlik_personeli_talep_matrisi()` fonksiyonu yeniden
kullanılabilir bir başlangıç noktası) üreten bir betik yaz: ~44 personel,
üç yetkinlik dağılımı, SDD 3.3.4'teki talep matrisi. İki senaryo ("rahat"
ve "sıkışık"). Çözücü-doğrulayıcı uyum testinin iskeletini kur (elle
üretilmiş rastgele geçerli atamalarla, `app/kurallar` H1–H8/S1–S8
`dogrula` metotlarını kullanarak). Önce UYGULAMA_PLANI.md'deki Gün 5
maddesini ve Backlog'daki demo veri stratejisi notlarını gözden geçir.

---

## 2026-08-06 — Sprint 1, Gün 5: Demo Veri Üreteci ve Sprint 1 Checkpoint

**Not:** Plandaki "Backlog'daki demo veri stratejisi" referansı da (Gün 4'teki
"SDD 3.3.6" referansı gibi) doğrulanamadı — Backlog dokümanında "demo",
"senaryo", "rahat" veya "sıkışık" geçen tek bir satır yok; bu üçü de
yalnızca UYGULAMA_PLANI.md'nin kendi metninde tanımlı. SDD/SRS'te de
"3.3" numaralı bölüm SRS'e ait (SDD'nin 3.3'ü "Tasarım Gerekçesi"dir,
personel senaryosuyla ilgisizdir); SRS 3.3'ü kullandım.

**Tasarım kararı — "rahat" ve "sıkışık" nasıl ayrışıyor:** Plan metni
"'sıkışık' (izinler girince kapsama açığı doğuran)" diyor — bunu **aynı
personel havuzu ve aynı talep matrisi üzerinde, yalnızca müsaitlik/izin
kayıtlarının farklı olduğu iki ayrı dönem** olarak yorumladım (farklı
kadro büyüklükleri değil). Bu hem plan metnine hem de SRS 3.3.6'nın
kendi anlattığı kırılganlık mekanizmasına (5 kişilik vardiya şefi
havuzunda tek bir iznin kapatılamayan boşluk doğurması) birebir uyuyor.

**Tamamlanan:**
- `app/services/ornek_senaryo.py`: SRS 3.3'teki senaryonun DB'siz yapısal
  tanımı — `NOKTA_TANIMLARI` (3.3.3), `talep_satirlarini_olustur()`
  (3.3.4, Gün 4'te `test_yuk_gostergesi.py` içine gömülü olarak yazılmış
  mantığın buraya taşınmış hali), `PERSONEL_GRUPLARI` (3.3.6'daki "İzin
  Payıyla" havuz oranlarının ~44'e ölçeklenmesi: Vardiya Şefi 9, Müracaat
  Görevlisi 7, yalnız Güvenlik Görevi 28 — toplam 44). Hem
  `scripts/demo_veri_uret.py` hem `tests/test_yuk_gostergesi.py` artık bu
  tek kaynaktan besleniyor; `test_yuk_gostergesi.py` bunu kullanacak
  şekilde küçük bir refactor ile güncellendi (davranış/doğrulanan sayılar
  değişmedi — 144/1.152/29 hâlâ birebir üretiliyor).
- `scripts/demo_veri_uret.py`: tek komutla veritabanına yazıyor —
  3 yetkinlik, 2 bina, 6 görev noktası, 3 vardiya tipi (süre/gece_mi
  `vardiya_hesaplari` ile türetilmiş), tam talep matrisi, **17 kural**
  (H1–H8 SRS 3.3.5 varsayılan parametreleriyle; S1–S8+S6b — S1 ağırlığı
  1000, diğerlerinin toplamından [41] belirgin büyük, SRS S1
  gerekçesiyle tutarlı; S6/S6b sırasıyla 10/6, Gün 3/4 kararıyla
  tutarlı), 44 personel + yetkinlik atamaları, iki `donem` ("Rahat
  Dönem", "Sıkışık Dönem" — 28'er gün, örtüşmeyen tarih aralıkları).
  Sıkışık dönemde, 9 kişilik vardiya şefi havuzunun 5'i o dönemin ilk iki
  haftası için `yillik_izin`/`tam_gun` müsaitlik kaydıyla izinli
  gösteriliyor (kalan 4 kişi, haftada gereken 5 kişinin altında —
  SRS 3.3.6'daki mekanizmanın birebir tekrarı).
  - `--reset` bayrağı: mevcut demo verisini (yalnızca bu betiğin
    oluşturduğu türden satırları) FK bağımlılık sırasına göre silip
    yeniden üretir. Bayrak verilmeden zaten veri varken çalıştırılırsa
    açık bir hatayla durur (sessiz yinelenen kayıt yok).
- Doğrulama: geçici Docker PostgreSQL'de betik iki kez ardışık
  (`--reset` ile) çalıştırıldı, her ikisinde de "44 personel, 6 görev
  noktası, 17 kural, 2 dönem" çıktısı; `/api/talep` uç noktası üzerinden
  yük göstergesinin gerçekten 144/1.152/29 döndürdüğü curl ile doğrulandı
  (API + demo veri + FR-1.9 hesaplaması uçtan uca tutarlı).
- **Çözücü-doğrulayıcı uyum testi iskeleti**
  (`tests/test_cozucu_dogrulayici_uyumu.py`): henüz gerçek çözücü
  olmadığı için "çözülmüş" çizelge, H1–H8'in tamamını yapısal olarak
  sağlayan elle kurulmuş bir örnek (3 personel, 28 gün, her personel iki
  günde bir çalışıp SRS 3.3.5'teki ileri yönlü sırayla — gündüz→akşam→gece
  — dönüyor). Kayıt defterinden H1–H8 sınıfları çekilip hepsinin
  `dogrula`'sı çalıştırılıyor, sıfır ihlal bekleniyor. Bunun yanına, testin
  kendisinin de bir şey yakalayabildiğini kanıtlayan bir negatif kontrol
  eklendi: dinlenmeyi bilerek bozan bir atama H2 tarafından yakalanıyor.
  Sprint 2 Gün 6'da gerçek çözücü bağlanınca bu iskelet, rastgele üretilmiş
  örneklere ve gerçek çözücü çıktısına genişletilecek.
- `README.md`'ye demo veri betiğinin kullanımı eklendi.
- `ruff check`, `ruff format --check` temiz; DB'siz ortamda 64 test geçti
  + 10 atlandı (beklenen); canlı PostgreSQL'de tüm paket (74 test) geçti.

**Sprint 1 çıkış kabul kriteri (plan metninden):**
- ✅ Tanım yönetimi ekranından bağımsız olarak, API üzerinden tam bir
  personel/yetkinlik/nokta/talep kümesi kurulabiliyor (Gün 4'te
  `test_tanim_api.py` ile doğrulandı, bugün demo betiğiyle de aynı akış
  gerçek veriyle tekrar doğrulandı).
- ✅ Demo veri betiği tek komutla iki senaryoyu da veritabanına yazabiliyor.
- ✅ On yedi kuralın (plan "on altı" diyor — Gün 3/4'teki S6/S6b ayrımı
  sonrası on yediye çıktı) `dogrula` tarafı test kapsamında (H1–H8:
  `test_kurallar_zorunlu.py`; S1–S8+S6b: `test_kurallar_esnek.py`; ayrıca
  uyum testi iskeletinde H1–H8 birlikte de çalıştırılıyor).

**Sapmalar / notlar:**
- Plan metnindeki iki doküman referansı ("SDD 3.3.6", "Backlog'daki demo
  veri stratejisi") bu oturumda da (Gün 4'teki gibi) doğrulanamadı;
  yukarıda not edildi. Üçüncü kez aynı örüntü çıkarsa (belge referansları
  plan yazılırken karışmış olabilir) mentör görüşmesinde bir kez sorulup
  netleştirilmesi faydalı olur.
- "Rahat"/"sıkışık" ayrımının aynı roster üzerinde yalnızca izinle
  yapılması bir tasarım kararı (yukarıda gerekçelendirildi); alternatif
  yorum (farklı roster büyüklükleri) de mümkündü ama SRS'in kendi
  anlatısıyla daha az örtüşüyordu.

**Kalan / ertelenen:** Yok — Sprint 1 kapsamındaki tüm günler (1–5)
tamamlandı.

**Sıradaki oturumun ilk işi:** Sprint 2, Gün 6 — Çözücü Adaptörü ve Model
Kurma. SDD 5.3'teki `model_kur` sözde kodunu (karar değişkeni `x[p,g,v,n]`,
üç atlama koşulu, yardımcı değişken `y[p,g,v]`) birebir uygula;
`CozucuAdaptoru` (model kur, çöz, ara çözüm geri çağırma, sonuç döndür —
SDD 3.2'deki dar arayüz). H1–H8 ve S1–S8+S6b kurallarının `modele_ekle`
metotlarını (şu ana kadar hepsi `NotImplementedError` fırlatıyordu) gerçek
CP-SAT model nesnesiyle tamamla. Küçük bir örnek (5 personel, 3 gün)
uçtan uca çözülüp `atama` tablosuna yazılabilmeli. Önce SDD 5.3'ü, Ek
A'daki H2/S2 sözde kod örneklerini ve `app/kurallar/temel.py`'deki
`CezaTerimi`/`modele_ekle` imzasını tekrar gözden geçir. `ortools` sürüm
notunu (Sprint 0'da 9.14.6206'ya çıkılmıştı) hatırda tut — SDD 5.3'teki
sözde kodla bu sürümün gerçek Python API'si arasında fark çıkarsa not düş.

---

## 2026-08-06 — Sprint 2, Gün 6: Çözücü Adaptörü ve Model Kurma

**Önemli mimari netleştirme (SDD Ek A'nın iki farklı `Baglam` kullanım
biçimi):** Ek A'daki H2 örneği `baglam.saat_farki(g1, v1, g2, v2)`'yi dört
ham argümanla, S2 örneği `y[p,g,v]`'yi doğrudan (parametre olarak
geçirilmeden) kullanıyor. Bunu, `model_kur`'un kendi sözde kodundaki
`baglam ← Baglam(tanımlar, donem, zaman_ekseni, y)` satırıyla birleştirip
şöyle çözdüm: **tek bir `Baglam` sınıfı**, hem dogrula'nın (Sprint 1)
somut-atama-listesi üzerinde çalışan yüzeyini hem de model kurmanın karar-
değişkeni-üzerinde-enumerasyon yüzeyini taşıyor. `Baglam`'a eklenenler:
`zaman_ekseni`, `y` (yalnız model kurarken dolar), `donem_gunleri`,
`gece_vardiyalari`, `vardiya_ciftleri`, `gun_ciftleri`, `saat_farki_ham`,
`sure_dakika`. Bu, "iki yorumlayıcı da aynı kural nesnesinden beslenir"
ilkesini genişletilmiş biçimde koruyor — tasarımdan sapma değil, iki
kullanım biçimini tek yapıda birleştiren bir yorum.

**Tamamlanan:**
- SDD 5.3 (`model_kur` sözde kodu) ve 5.4'ün (çözüm işi durum makinesi,
  yalnızca sözlük/arayüz seviyesinde — tam iş orkestrasyonu Gün 8) ilgili
  kısımları okundu.
- `app/cozucu/model_kurucu.py`: `model_kur()`, SDD 5.3 ile birebir — üç
  atlama koşuluyla (talep sıfır / yetkinlik yok / müsait değil) `x[p,g,v,n]`
  BoolVar'ları, `y[p,g,v]` toplama ifadeleri, ısıtma penceresi
  atamalarının sabitlenmesi, kurallara sırayla `modele_ekle` çağrısı ve
  `kural.agirlik × terim` toplamının minimize edilmesi.
- `app/cozucu/adaptor.py`: `CozucuAdaptoru.coz()` — dar arayüz (SDD 3.2):
  zaman limiti, arama işçisi sayısı, ara çözüm geri çağırması
  (`CpSolverSolutionCallback` alt sınıfı), sonucu `CozumSonucu` (durum,
  atanan anahtarlar, toplam ceza, süre) olarak döndürür.
- **H1–H8'in tamamına `modele_ekle` eklendi:**
  - H1: günlük ≤1 atama (doğrudan toplam kısıtı).
  - H2: Ek A'daki H2 örneğiyle birebir (`vardiya_ciftleri` × `gun_ciftleri`
    taraması, `saat_farki_ham`).
  - H3/H4/H5/H6: ortak bir `kayan_pencere_kisiti_ekle()` yardımcısına
    (yeni, `yardimcilar.py`) çıkarıldı — dördü de "zaman ekseninin her
    N-günlük penceresinde ağırlıklı y toplamı bir üst sınırı aşamaz"
    örüntüsünün özel halleri. H5'in saat tavanı, CP-SAT'ın tamsayı katsayı
    zorunluluğu yüzünden dakika biriminde uygulanıyor (`sure_dakika`).
  - H7, H8: **bilerek boş** — SDD 5.3'ün kendi metni bunu açıkça söylüyor:
    "değişken oluşturmadaki üç atlama koşulu... H7 ve H8 kısıtlarının
    modele ayrıca eklenmesine gerek bırakmaz."
- **S1–S8+S6b'nin tamamına `modele_ekle` eklendi**, hepsi SRS 4.3/4.4'teki
  formüllerin doğrudan çevirisi:
  - S1: alt sınır (`eksik` IntVar) + üst sınır (kadro, doğrudan `model.add`)
    aynı metotta — SRS'in kendi formülasyonu böyle (zorunlu ve esnek
    bileşen tek kural içinde).
  - S2, S3: Ek A'daki S2 örneğiyle birebir (enb/enk aralık değişkenleri).
  - S4: `add_abs_equality` ile mutlak sapma; dakika biriminde (bkz. birim
    notu aşağıda).
  - S5: onaylanmış tercihler üzerinden doğrudan toplam.
  - S6, S6b: `gösterge ≥ y1 + y2 − 1` alt-sınırlama hilesiyle (amaç
    fonksiyonunda yalnızca pozitif katkılı bir değişken için üst sınır
    kısıtına gerek yok — çözücü onu zaten mümkün olduğunca düşük tutar).
    S6b, bina bilgisi nokta düzeyinde olduğu için `y` yerine `x` kullanıyor.
  - S7: aynı alt-sınırlama hilesiyle izole çalışma/izin göstergeleri.
  - S8: `Σ|x-x_önceki|`, önceki değer sabit (0/1) olduğu için doğrudan
    `x` veya `1-x` toplamına indirgeniyor.
- **Kural arayüzü sadeleşti:** `ZorunluKural`/`EsnekHedef`'in
  `NotImplementedError` fırlatan varsayılan `modele_ekle`'leri kaldırıldı
  — artık her somut kural kendi gerçek uygulamasını taşıyor, `Kural` yine
  tam soyut (ABC) kalıyor. Bu değişiklik iki eski testi bozdu
  (`..._modele_ekle_henuz_uygulanmadi`); onları gerçek CP-SAT davranışını
  doğrulayan testlere çevirdim (H1: iki değişkenin aynı anda 1 olması
  `INFEASIBLE` veriyor mu; S1: karşılanamayan talepte `eksik` değişkeni
  amaç fonksiyonunda doğru değere zorlanıyor mu).
- **Sprint 2 Gün 6 kabul testi**
  (`tests/test_cozucu_uctan_uca.py`): 5 personel, 3 gün, tek nokta —
  `model_kur` → `CozucuAdaptoru.coz` → sonucun H1–H8 `dogrula`'dan sıfır
  ihlalle geçtiği doğrulanıyor (Sprint 1 Gün 5'teki uyum testi iskeletinin
  gerçek çözücüyle genişletilmiş hali). İkinci bir test, aynı senaryoyu
  gerçek veritabanı kimlikleriyle kurup çözüp sonucu `atama` tablosuna
  yazıyor ve geri okuyarak doğruluyor (kabul kriterindeki "sonuç atama
  tablosuna yazılıyor" ifadesinin birebir karşılığı).
- Doğrulama: geçici Docker PostgreSQL'de tüm paket (76 test) iki kez
  ardışık geçti (idempotentlik için DB testinde `uuid` sonekli benzersiz
  değerler kullanıldı — kural satırları test kapsamında kullanılmadığı
  için o kısım testten çıkarıldı, ilk denemede tekrar çalıştırmada
  `kural.kimlik` benzersizlik ihlaline takılmıştı). DB'siz ortamda 65 geçti
  + 11 atlandı (beklenen).
- `ruff check`, `ruff format --check` temiz.

**Sapmalar / notlar:**
- **S4 birim tutarsızlığı:** `modele_ekle` dakika, `dogrula` saat
  biriminde ceza büyüklüğü üretiyor. Optimizasyon sonucunu etkilemiyor
  (60 ile sabit ölçekleme), yalnızca ham ceza büyüklüğünün raporlanan
  değeri iki tarafta farklı birimde. S-kuralları için henüz bir
  çözücü-doğrulayıcı uyum testi yok (yalnız H-kuralları için var); böyle
  bir test S-kurallarına genişletilirse bu birim farkı netleştirilmeli.
- `vardiya_ciftleri`/`gun_ciftleri` (H2) tam N² taraması yapıyor;
  küçük örneklerde sorun değil, Sprint 3 Gün 14'teki 40×28 referans
  performans testinde yavaş çıkarsa optimize edilmesi gerekebilir (not
  düşüldü, şimdilik dokunulmadı — doğruluk önce).
- S6/S6b ve S7'nin `modele_ekle`'si yalnızca `donem_gunleri` (ısıtma
  penceresini değil) kapsıyor; ısıtma penceresinden dönemin ilk gününe
  geçişteki olası desen kırılması bu haliyle değerlendirilmiyor. Bilinçli
  bir kapsam daraltması (zaman kısıtı), SDD'de bunun tersini söyleyen bir
  ifade yok.

**Kalan / ertelenen:** Yok — Gün 6 kapsamındaki tüm maddeler tamamlandı.

---

## 2026-08-06 — Gün 6 incelemesi ve UYGULAMA_PLANI.md düzeltmeleri

Kullanıcı Gün 6'yı onayladı. Ayrıca, Gün 4 ve Gün 5'te bu oturumlarda
tespit edilip doğrulanamayan iki doküman referansı UYGULAMA_PLANI.md'de
düzeltildi (kullanıcı tarafından, plan dosyasının kendisinde):

- Gün 4: "SDD 3.3.6" → "SRS 3.3.6" (tespitim doğruymuş).
- Gün 5: "Backlog'daki demo veri stratejisi" referansı kaldırıldı; strateji
  hiç yazılmamıştı. Şimdi UYGULAMA_PLANI.md'de doğrudan bir "Demo Veri
  Stratejisi" başlığı altında tanımlı (Gün 5'te bulduğum yorum — aynı
  roster, yalnızca izin farkı — doğrulandı ve kalıcı hale getirildi).

Bu düzeltmeler bu oturumda dosyaya işlendi.

Ayrıca üç not/karar:
1. **Yeni görev eklendi** (UYGULAMA_PLANI.md, Sprint 2 sonu, Gün 11'den
   sonra Gün 12'den önce): "S1–S8+S6b Uyum Testi Genişletmesi" —
   `test_cozucu_uctan_uca.py`'deki uyum testi şu an yalnızca H1–H8'i
   kapsıyor; S1–S8+S6b'nin çözücü çıktısı üzerinde `dogrula` ile
   `modele_ekle`'nin amaç fonksiyonu katkısının tutarlı olduğu da
   doğrulanmalı. Bu görev henüz yapılmadı, Gün 11'den sonra ele alınacak.
2. Bu genişletme sırasında Gün 6'da not düşülen **S4 birim tutarsızlığı**
   (`modele_ekle` dakika, `dogrula` saat) da düzeltilecek — henüz
   düzeltilmedi.
3. H2'nin `vardiya_ciftleri`/`gun_ciftleri` N² taraması şimdilik olduğu
   gibi bırakılacak; Gün 14'teki 40×28 referans performans testinde
   yavaş çıkarsa ilk bakılacak yer burası (henüz dokunulmadı).

---

## 2026-08-06 — Sprint 2, Gün 7: Ön Kontrol Alt Sistemi

**Önemli bulgu — sıkışık senaryo ön kontrolde hiç bulgu vermiyor:**
SDD 5.2'deki dört kontrolü (SDD 5.3'ün yanına, `app/services/on_kontrol.py`)
birebir uyguladıktan sonra Sprint 1 Gün 5'in demo verisiyle (rahat/sıkışık
dönemler) canlı bir API çağrısıyla test ettim. **Rahat da sıkışık da sıfır
bulgu üretti.** Sebebini araştırdım: dört kontrolün hiçbiri, "küçük bir
yetkinlik havuzunun yalnızca belirli bir haftada eşzamanlı izin yüzünden
yetersiz kalması" gibi zaman-pencereli/haftalık bir açığı yakalayacak
şekilde tasarlanmamış — Kontrol 1/2 dönem genelini topluyor (yerel
darboğaz, dönemin geri kalanındaki serbestlikle sayısal olarak örtülüyor),
Kontrol 3/4 ise yalnızca anlık (gün/vardiya bazlı) yeterliliğe bakıyor,
haftalık kümülatif yüke değil. SDD'nin kendi metni zaten bunu söylüyor
("zaman yapısına bağlı kısıtlar bu aritmetikle yakalanamaz") — yani bir
kodlama hatası değil, SDD 5.2'nin kasıtlı sınırının demo senaryosuyla
karşılaşması. Bunu bir `AskUserQuestion` ile kullanıcıya ilettim; üç
seçenek sundum (SDD'yi olduğu gibi bırakıp kabul kriterini gözden geçir /
demo senaryoyu değiştir / beşinci bir kontrol ekle). **Kullanıcı birinci
seçeneği onayladı.**

**Kullanıcının paralel doküman güncellemesi:** Aynı yanıtta kullanıcı,
`docs/SDD.docx` ve `docs/Backlog.docx`'un sürüm 1.2'ye güncellendiğini ve
`docs/UYGULAMA_PLANI.md` adında geçici bir senkronizasyon kopyası
bıraktığını bildirdi. Kontrol ettim: `docs/` klasöründeki dört referans
belge gerçekten güncellenmiş haldeydi (dosya zaman damgaları bunu
doğruluyordu). Değişiklikler:
- **SDD 5.2, Kontrol 2 (yetkinlik havuzu) düzeltildi:** artık Kontrol
  1'deki gibi kişi başına `MİN(musait_gun, azami_vardiya_sayisi)`
  topluyor (önceden bireysel izni hiç hesaba katmıyordu — bu, benim de
  bağımsız olarak fark ettiğim bir eksiklikti, kodda zaten "teorik;
  bireysel izin dikkate alınmaz" diye not düşmüştüm).
- **SDD 5.2'nin sonuna** bu sınırı somut örnekle (bizim sıkışık
  senaryomuzla birebir örtüşen) açıklayan bir paragraf eklendi.
- **Backlog'a B-14 eklendi:** "yetkinlik başına kayan haftalık pencere
  kontrolü" — ertelenmiş, şimdi yapılmıyor.
- **UYGULAMA_PLANI.md**: Gün 7'nin kabul kriteri "sıkışık senaryoda en az
  bir bulgu olmalı" yerine "kapsam içindeyse doğru raporlanır, değilse
  bulgusuzluk beklenen davranıştır" oldu; Gün 8'in kabul kriterine
  sıkışık senaryonun çözülüp `kapsama_acigi`'nde doğru raporlandığının
  doğrulanması eklendi. Ayrıca "Demo Veri Stratejisi" artık ayrı bir
  başlık (benim kendi yazdığım sürümden biraz farklı ama aynı özü
  taşıyan bir metinle).
- Bu içerikleri kök `UYGULAMA_PLANI.md`'ye birleştirdim (kendi eklediğim
  "Ek Görev — S1–S8+S6b Uyum Testi Genişletmesi" bölümünü koruyarak,
  kullanıcının yeni kopyasında bu bölüm yoktu ama silinmesi istenmedi).
  `docs/UYGULAMA_PLANI.md` staging kopyasını sildim — `docs/` yalnızca
  dört referans belgeyi barındırıyor.
- **Küçük gözlem (bloklamadı):** Kullanıcının yeni `UYGULAMA_PLANI.md`
  kopyasında Gün 5'teki "SDD 3.3" / "SDD 3.3.4" referansları hâlâ
  düzeltilmemiş (Gün 4'teki "SDD 3.3.6→SRS 3.3.6" düzeltmesiyle aynı
  örüntü). Üçüncü kez karşıma çıktığı için burada not ediyorum, ayrıca
  sormadım.

**Tamamlanan (kod):**
- **Gerçek bir hata buldum ve düzelttim:** `_azami_vardiya_donem`
  içinde `Decimal * float` çarpımı — yalnızca gerçek DB verisiyle
  (`VardiyaTipiBilgisi.sure_saat` orada `float`) test edince ortaya
  çıktı, saf birim testlerinde (hepsi `int` sure_saat kullanıyordu)
  görünmüyordu. Artık tutarlı biçimde `float` kullanılıyor.
- `app/services/kadro_hesaplari.py`: `kisi_basina_azami_haftalik_vardiya`
  — Gün 4'te `yuk_gostergesi.py` içine gömülü olan "H5/H6'dan kişi
  başına azami haftalık vardiya" formülü buraya çıkarıldı; hem
  `yuk_gostergesi.py` (asgari kadro) hem `on_kontrol.py`
  (`azami_vardiya_sayisi(donem)`) artık aynı fonksiyonu kullanıyor.
- `app/services/talep_cozucu.py`: SDD 4.2.1'deki istisna/genel talep
  satırı çözümlemesini (önce tarihe özgü istisna aranır, yoksa gün
  tipine göre genel satır kullanılır) somut bir gün listesi üzerinde
  yapan `talep_matrisini_coz()`.
- `app/services/baglam_kurucu.py`: bir `Donem` için veritabanından tam
  bir `Baglam` kuran `baglam_olustur()` — SDD 5.2'nin imzasına sadık
  kalarak (`on_kontrol(donem, tanimlar, musaitlikler)`, ısıtma penceresi
  almıyor) yalnızca dönem günleri için talep çözüyor; ısıtma penceresini
  de kapsayan `zaman_ekseni` Gün 8'de (gerçek çözüm işi) ayrıca
  kurulacak.
- `app/services/on_kontrol.py`: SDD 5.2'nin (sürüm 1.2) dört kontrolünün
  tamamı — `_donem_kapasitesi_kontrolu`, `_yetkinlik_havuzu_kontrolu`
  (artık ikisi de aynı önceden-hesaplanmış `musait_gun_by_personel`
  sözlüğünü paylaşıyor, kod tekrarı yok), `_gunluk_musaitlik_kontrolu`,
  `_nokta_musaitlik_kontrolu`. `Bulgu` veri sınıfı ve `BulguTipi` enum'u.
- `app/kurallar/baglam.py`'ye `gunde_musait_mi()` eklendi (gün bazlı,
  herhangi bir vardiya için müsaitlik — Kontrol 3/4'ün "p, g gününde
  müsait" ifadesinin karşılığı).
- `app/repositories/kural.py`'ye `parametre_getir()` eklendi (H5/H6
  parametrelerini okuyan, `TanimServisi` ve `OnKontrolServisi` arasında
  paylaşılan tek metot — önceden ikisinde de aynı kod tekrarlanıyordu).
- `app/repositories/sonuc.py` (yeni): `DonemDeposu`.
- `app/services/on_kontrol_servisi.py`: `donem_id` alıp `Baglam`'ı kurup
  `on_kontrol_yap`'ı çalıştıran servis katmanı.
- `app/routers/cizelge.py` (yeni, SDD 3.2'deki `cizelge_router`):
  `POST /api/on-kontrol`.
- Testler: `tests/test_on_kontrol.py` (6 test, DB'siz — dört kontrolün
  her biri için tetikleyen/tetiklemeyen senaryo, artı Kontrol 2'nin
  bireysel izni artık hesaba kattığını doğrulayan özel bir test);
  `tests/test_cizelge_api.py` (2 test, canlı DB — 404 ve kadro
  yeterliyken boş bulgu listesi).
- Doğrulama: geçici Docker PostgreSQL'de tüm paket (84 test) iki kez
  ardışık geçti; demo verisiyle gerçek `curl` çağrısı (rahat + sıkışık,
  ikisi de düzeltme sonrası hâlâ boş — beklenen).
- `ruff check`, `ruff format --check` temiz.

**Kalan / ertelenen:** Yok — Gün 7 kapsamındaki (kullanıcıyla birlikte
netleşen) tüm maddeler tamamlandı. Beşinci bir ön kontrol (B-14)
kasıtlı olarak yapılmadı.

**Sıradaki oturumun ilk işi:** Sprint 2, Gün 8 — Çözüm İşi ve Asenkron
Yürütme. SDD 5.4'teki durum makinesini (Şekil 5.1) uygula: kuyrukta →
on_kontrol → cozuluyor → tamamlandı/uyarılı/başarısız/iptal. Çözüm
işinin ayrı süreçte çalışması (basit `multiprocessing` yeterli, systemd
Sprint 3'te). `/api/cozum`, `/api/cozum/{id}`, `/api/cozum/{id}/iptal`.
Ara çözüm bildirimi: her iyileşen çözümde `en_iyi_ceza` güncellensin.
**Güncellenmiş kabul kriteri (bkz. UYGULAMA_PLANI.md, kullanıcıyla Gün
7'de netleşti):** çözüm isteği anında iş kimliği dönüyor, API bu sırada
yanıt vermeye devam ediyor; **ayrıca sıkışık senaryo çözülüp
`kapsama_acigi` tablosunda vardiya şefi havuzunun eksik kaldığı
gün/vardiyaların doğru raporlandığı doğrulanmalı** — Gün 7'de ön
kontrolün yakalayamadığı açığın gerçekten S1 esnek hedefiyle ortaya
çıktığını kanıtlayan asıl test budur. Önce SDD 5.4'ü, `CizelgeSurumu`/
`CozumIsi`/`KapsamaAcigi` modellerini (Sprint 1 Gün 1) ve
`app/services/baglam_kurucu.py`'nin ısıtma penceresini henüz
kurmadığını (bu oturumda bilerek ertelendi) hatırda tut — zaman_ekseni
(ısıtma + dönem) artık burada kurulmalı.

---

## 2026-08-06 — Sprint 2, Gün 8: Çözüm İşi ve Asenkron Yürütme

**Tamamlanan (kod):**
- `app/services/baglam_kurucu.py` genişletildi: `zaman_ekseni_olustur()`
  (ısıtma penceresi + dönem günleri birleşik liste) ve `baglam_olustur()`
  artık talebi tüm `zaman_ekseni` üzerinden çözüyor (önceden yalnızca
  dönem günleri) — `model_kur`'un değişken oluşturma döngüsü ısıtma
  penceresindeki günleri de gördüğü için gerekliydi.
- `app/kurallar/baglam.py`: `zaman_ekseni`, `y` (model kurarken dolan
  toplama ifadeleri), `kapsama_eksikleri` (S1'in `modele_ekle`'sinin
  doldurduğu, `(gün, vardiya_tipi_id, nokta_id) → eksik IntVar` sözlüğü)
  eklendi.
- `app/kurallar/esnek.py`: S1'in `modele_ekle`'si artık her talep
  hücresi için bir `eksik` IntVar'ı `baglam.kapsama_eksikleri`'ne
  yazıyor — Gün 8'in asıl kabul kriteri (kapsama açığının
  raporlanması) bu değişkenler üzerinden çalışıyor.
- `app/cozucu/model_kurucu.py`: `model_kur()` artık 4'lü demet
  döndürüyor (`model, x, baglam, ham_terimler`) — `ham_terimler`,
  kural kimliğine göre ağırlıksız ceza ifadeleri (ceza dökümü
  raporlaması için).
- `app/cozucu/adaptor.py`: `CozucuAdaptoru.coz()` artık
  `ceza_terimleri`/`kapsama_degiskenleri` alıyor, `CozumSonucu`'na
  `ceza_dokumu` (kural bazlı ağırlıksız ceza) ve `kapsama_eksikleri`
  (yalnızca >0 olan hücreler) ekliyor.
- `app/repositories/sonuc.py`: `CizelgeSurumuDeposu`
  (`donem_icin_sonraki_surum_no`), `CozumIsiDeposu`, `AtamaDeposu`,
  `KapsamaAcigiDeposu` eklendi.
- `app/services/cozum_servisi.py` (yeni): SDD 5.4'ün durum makinesinin
  birebir uygulaması. `CozumServisi.baslat()` işi `kuyrukta` durumunda
  oluşturup commit ettikten sonra `multiprocessing.Process` ile ayrı
  bir süreç başlatıp hemen dönüyor (SDD 3.4.4 — HTTP istek-yanit
  döngüsünden bağımsız gerçek süreç ayrımı; systemd entegrasyonu
  Sprint 3'te). `cozum_isini_calistir()` (ayrı süreçte, kendi DB
  oturumuyla çalışır): `kuyrukta → on_kontrol` (yapısal engel varsa
  `başarısız`, çözücüye hiç girmeden) `→ cozuluyor` (kurallar
  yüklenir, `zaman_ekseni_olustur` + `baglam_olustur` + `model_kur`,
  ara çözüm geri çağırmasıyla `en_iyi_ceza` her iyileşmede güncellenir)
  `→ tamamlandı` (kapsama açığı yok) / `uyarılı` (kapsama açığı var,
  `kapsama_acigi` tablosuna yazılır) / `başarısız` (çözücü zaman
  limitinde çözüm bulamadı). Atamalar ve kapsama açığı tek bir DB
  işleminde yazılıyor (SDD 5.4 — yarım kalmış bir çizelge yanıltıcı
  olmasın diye).
- `app/schemas/cozum.py` (yeni): `CozumBaslatIstek`, `CozumOku`.
- `app/routers/cizelge.py`: `POST /api/cozum`, `GET /api/cozum/{id}`,
  `POST /api/cozum/{id}/iptal` eklendi (iptal en iyi çaba — ayrı
  süreçte fiilen çalışan CP-SAT aramasını zorla durdurmuyor, yalnızca
  durumu işaretliyor; gerçek süreç izleme/sonlandırma Sprint 3'e
  bırakıldı).
- `tests/test_cozum_servisi.py` (yeni, 3 test, canlı DB gerektirir):
  kadro yeterliyken `tamamlandı`/`uyarılı` + atamaların yazıldığını
  doğrulayan test; ön kontrolde yapısal engel varsa (iki kişilik
  kapalı bir yetkinlik havuzunun tamamı aynı günde izinli) çözücüye
  hiç girmeden `başarısız` dönüp `hata_mesaji`'nin çakışma tarihini
  içerdiğini ve hiç `Atama` yazılmadığını doğrulayan test (bu test iki
  kez yeniden tasarlandı — ayrıntı aşağıda); bulunamayan dönemde
  `baslat()`'ın `None` döndüğünü doğrulayan test.
- Test geliştirirken ortaya çıkan iki gerçek (kod değil, test
  izolasyonu) sorun çözüldü: (1) paylaşılan Docker Postgres'te başka
  testlerin bıraktığı genel (tarihsiz) `Talep` satırları her hafta
  içi güne uygulandığı için (SDD 4.2.1 semantiğine göre doğru davranış)
  atama sayıları beklenenden fazla çıktı — düzeltme, test
  assertion'larını kendi `nokta_id`'siyle filtrelemek oldu, tabloyu
  boş varsaymamak. (2) "kesin kapsama açığı" senaryosu başta rastgele
  başka testlerin ilgisiz personeliyle dolduruluyordu — düzeltme,
  teste özel yeni bir `Yetkinlik` ile noktayı kapalı hale getirmek
  oldu. Sonrasında bu senaryo beklenenin aksine `uyarılı` değil
  `başarısız` döndü — kontrol edince bunun bir hata değil, tam olarak
  SDD 5.2 Kontrol 4'ün (nokta bazlı müsaitlik) yakalaması gereken bir
  durum olduğu anlaşıldı (tüm gün örtüşen izin = yapısal engel); test
  buna göre yeniden adlandırılıp `başarısız` bekleyecek şekilde
  düzeltildi.
- Doğrulama: geçici Docker PostgreSQL'de tüm paket (87 test) iki kez
  ardışık geçti.
- `ruff check`, `ruff format --check` temiz.

**Gün 8'in güncellenmiş kabul kriterinin manuel/uçtan uca doğrulaması
(temizlenmiş demo veriyle, gerçek `uvicorn` sunucusu + gerçek Docker
Postgres):**
- Demo verisi `--reset` ile yeniden üretildi (44 personel, 6 nokta, 17
  kural, 2 dönem — önceki test çalıştırmalarından kalan `kural`
  satırlarıyla ilk denemede benzersizlik ihlaline takıldı, DB
  `TRUNCATE ... CASCADE` ile temizlenip yeniden üretildi).
- Sıkışık Dönem (`donem_id=2`) için `POST /api/cozum` (zaman limiti 90
  sn) çağrıldı; iş anında `kuyrukta` durumuyla iş kimliği döndürdü.
- Çözüm ayrı süreçte sürerken `/health`'e beş kez art arda istek
  atıldı — hepsi ~30ms içinde `200 {"durum":"ok"}` döndürdü, aynı
  aralıkta iş durumu `çözülüyor`e geçip `en_iyi_ceza` art arda
  iyileşerek güncellendi (ara çözüm geri çağırması çalışıyor) — **API
  çözüm sürerken tamamen yanıt veriyor.**
- İş `uyarılı` durumuyla tamamlandı (`sure_saniye=90.06`, zaman
  limitine ulaşıldı — 4 haftalık/44 kişilik ölçekte beklenen).
  `kapsama_acigi` tablosu sorgulandı: **Vardiya Şefliği** noktasında,
  tam olarak izin haftalarına denk gelen 2026-03-06 ile 2026-03-13
  arasındaki 6 vardiya/gün hücresinde 1'er eksik raporlandı — **Gün
  7'de ön kontrolün yapısal olarak yakalayamadığı haftalık/yerel
  darboğaz, Gün 8'in çözücüsü tarafından S1'in `kapsama_eksikleri`
  mekanizmasıyla doğru tespit edildi.** Bu, Gün 7'de kullanıcıyla
  netleşen "asıl doğrulama Gün 8'e taşındı" kararının kanıtı.
- Doğrulama sonrası: `uvicorn` süreci durduruldu, test verileri
  `TRUNCATE` ile temizlendi, tüm paket (87 test) tekrar çalıştırılıp
  temiz DB üzerinde de geçtiği doğrulandı, Docker test container'ı
  (`vardiya-pg-test`) silindi (kalıcı bir servis değil).

**Sapmalar / notlar:** Yok — Gün 8, Gün 7'de netleşen güncellenmiş
kabul kriteriyle birebir tamamlandı.

**Kalan / ertelenen:** Yok — Gün 8 kapsamındaki tüm maddeler
tamamlandı. Ek Görev (S1–S8+S6b uyum testi genişletmesi + S4 birim
düzeltmesi) hâlâ Gün 11 sonrası için planlı, henüz yapılmadı.

**Kullanıcı notu (Gün 8 incelemesi sırasında, Sprint 3'e ertelenmiş bir
hatırlatma):** `/api/cozum/{id}/iptal` şu an gerçekten "en iyi çaba" —
ayrı süreçteki CP-SAT aramasını fiilen öldürmüyor, yalnızca DB'de
durumu `iptal` olarak işaretliyor. Bu, Gün 8'de bilinçli bir kapsam
kararıydı (gerçek süreç sonlandırma süreç izleme/PID takibi gerektirir,
Sprint 3'teki systemd entegrasyonuna bırakıldı — kod içindeki docstring
zaten bunu söylüyor). Kullanıcı, arayüzde bir "Durdur" butonu eklenirse
bunun kullanıcıya yanıltıcı bir his verebileceğini (buton basılsa da
arama süre limitine kadar arka planda çalışmaya devam eder) vurguladı.
Sprint 3'te gerçek sonlandırma (`process.terminate()` + zaman aşımlı
bekleme, ardından gerekirse `kill()`) eklenene kadar, Gün 10/13'teki
arayüz çalışmasında "Durdur" butonunun yanına bu sınırı açıklayan bir
not/tooltip eklenmesi düşünülmeli.

---

## 2026-08-06 — Sprint 2, Gün 9: Doğrulama Alt Sistemi

**Tasarım netleştirmesi (SDD 5.5 sürüm 1.3, kullanıcıyla birlikte
çözüldü):** SDD 5.5'in `degisikligi_dogrula` sözde kodu, değiştirilen
günün ±7 günlük penceresinden çekilen tek bir atama listesini hem
zorunlu (H1-H8) hem esnek (S1-S8) kurallara aynı şekilde veriyordu.
H1-H8'in `dogrula`'sı doğası gereği yerel olduğu için pencere sorunsuz
çalışıyor, ama S2/S3/S4 (dönem genelindeki en yüksek/en düşük değere
veya kişinin dönem toplamına bakan adalet/saat dengesi kuralları)
pencereyle sınırlanırsa yanlış (hatta yanlış YÖNDE) sonuç üretir —
bunu kullanıcıya `AskUserQuestion` ile ilettim. **Kullanıcı, docs/SDD.docx'i
sürüm 1.3'e güncelledi**: her kural sınıfına sabit bir `kapsam` alanı
eklendi (PENCERE veya DÖNEM_GENELİ); H1-H8 ile S1, S5, S6, S6b, S7, S8
PENCERE (S1/S8 dönem genelinde tanımlı olsa da tek hücrelik bir
değişikliğin etkisi yalnızca o hücreye bakılarak hesaplanabiliyor);
S2, S3, S4 DÖNEM_GENELİ. `degisikligi_dogrula` artık iki ayrı atama
kümesi çekiyor (pencere + tüm dönem) ve her kural kendi kapsamına göre
doğru kümeyle çağrılıyor; dönem geneli tarama tipik ölçekte (40
personel/28 gün, ~1200 satır) milisaniyeler sürüyor, performans
endişesi yok.

**Tamamlanan (kod):**
- `app/kurallar/temel.py`: `KuralKapsami` enum'u (PENCERE,
  DONEM_GENELI); `Kural` taban sınıfına `kapsam: ClassVar[KuralKapsami]
  = PENCERE` (varsayılan) eklendi.
- `app/kurallar/esnek.py`: S2, S3, S4 sınıflarına `kapsam =
  KuralKapsami.DONEM_GENELI` eklendi (gerekçe docstring'lerde).
- `app/repositories/sonuc.py`: `AtamaDeposu.surume_ve_araliga_gore_getir`
  (pencere sorgusu) ve `AtamaDeposu.tekil_getir` (upsert için) eklendi.
- `app/services/dogrulama_servisi.py` (yeni): `DogrulamaServisi` —
  SDD 5.5'in birebir uygulaması. `dogrula()`: sürüm bulunamazsa `None`
  (404), taslak değilse `SurumTaslakDegilError` (409, FR-7.3);
  pencere+dönem atama kümelerini çekip değişikliği her ikisine de
  uygular, zorunlu kurallar yalnızca SONRAKİ durumda değerlendirilir
  (kabul/red kararı için yeterli), esnek kurallar ÖNCESİ/SONRASI iki
  kez değerlendirilip ham ceza farkı toplanır (kural kendi `kapsam`ına
  göre pencere ya da dönem atamalarıyla çağrılır). `uygula()`: önce
  `dogrula()`, zorunlu ihlal yoksa `Atama` satırını upsert/siler
  (`kaynak=MANUEL`).
- `app/schemas/dogrulama.py` (yeni): `AtamaDegisikligiIstek` (hücre
  boşaltmak için vardiya_tipi_id/nokta_id ikisi birden `None`
  olabilir, tek biri olamaz — `model_validator` ile doğrulanıyor),
  `IhlalOku`, `DogrulamaSonucuOku`.
- `app/routers/cizelge.py`: `POST /api/atama/dogrula`, `PUT
  /api/atama` eklendi (409'da `DogrulamaSonucuOku` gövdesi ihlal
  detaylarıyla birlikte döner).
- `tests/test_dogrulama_servisi.py` (yeni, 7 test):
  - **DB gerektirmeyen, en önemli test:**
    `test_s2_pencereyle_sinirlanirsa_donem_genelindeki_yuku_yanlis_yonde_hesaplar`
    — personel 1'in değişiklik gününden (25) uzak on günde (1-10) zaten
    dönem geneli tavanının üzerinde gece yükü olduğu elle kurulmuş bir
    örnek: dönem geneli (doğru) atamalarla 11. geceyi eklemek cezayı
    **+1** artırırken, yalnızca pencereyle (yanlış) değerlendirilince
    aynı değişiklik cezayı **-1** azaltıyormuş gibi görünüyor — işaret
    bile ters çıkıyor. Bu, kapsam ayrımının neden zorunlu olduğunu
    doğrudan kanıtlıyor.
  - `test_kural_kapsamlari_sdd_5_5_ile_tutarli` (DB'siz): on yedi
    kuralın `kapsam` değerlerinin SDD 5.5'teki listeyle birebir
    eşleştiğini doğrular.
  - `test_dogrula_zorunlu_kisit_ihlalini_reddeder` (canlı DB): akşam
    (16-24) vardiyasından sonraki güne gündüz (08-16) ataması, 8 saatlik
    dinlenme bırakır (asgari 16 saatin altı) — H2 ihlali, `kabul_edilebilir
    False`, `uygula()` da reddediyor ve **hiçbir şey yazılmıyor**
    (canlı `curl` ile de doğrulandı, bkz. aşağıda).
  - `test_dogrula_yayinlanmis_surumde_409`, `test_dogrula_bulunamayan_surumde_none_doner`.
- Doğrulama: geçici Docker PostgreSQL'de tüm paket (92 test) iki kez
  ardışık geçti (87 + 5 yeni).
- **Gerçek `curl` ile manuel doğrulama** (Gün 9 kabul kriteri): H2
  ihlali üreten bir `POST /api/atama/dogrula` **43ms**'de yanıt verdi
  (kabul kriterinin "bir saniyenin altında" hedefinin çok altında);
  aynı istek `PUT /api/atama`'ya gönderilince **409** döndü ve DB'de
  hiçbir satır oluşmadığı doğrulandı; ardından zorunlu kısıtları
  bozmayan bir değişiklik `PUT /api/atama`'ya gönderildi, **200**
  döndü, `ceza_degisimi` esnek hedeflere etkiyi gösterdi (34ms) ve
  `atama` tablosunda `kaynak=MANUEL` olarak kalıcı biçimde yazıldığı
  doğrulandı.
- `ruff check`, `ruff format --check` temiz.

**Sapmalar / notlar:** Yok — SDD 5.5 sürüm 1.3'ün kendisi bu oturumda
kullanıcıyla birlikte netleşen tasarımın doğrudan karşılığı; kod ondan
sapmıyor.

**Kalan / ertelenen:** Yok — Gün 9 kapsamındaki tüm maddeler
tamamlandı. Ek Görev (S1–S8+S6b uyum testi genişletmesi + S4 birim
düzeltmesi) hâlâ Gün 11 sonrası için planlı.

**Sıradaki oturumun ilk işi:** Sprint 2, Gün 10 — Frontend: Çözüm ve
Çizelge Ekranları (temel görünüm). UYGULAMA_PLANI.md'deki Gün 10
maddesini takip et; SDD 6.3.2/6.3.3'teki nesneleri (çözüm başlatma,
ilerleme göstergesi, çizelge ızgarası, hücre düzenleme, ihlal
bildirimi, kilitleme, kapsama açığı işareti) uygula. Bu aşamada görsel
tasarım Figma mockup'larına göre değil işlevsel iskelet olarak
yapılıyor. Hücre düzenleme UI'ı `/api/atama/dogrula` ve `PUT
/api/atama`'yı (bu oturumda tamamlandı) kullanacak; "Durdur" butonu
eklenirse Gün 8'in sonunda not düşülen `/api/cozum/{id}/iptal`'in "en
iyi çaba" sınırını (ayrı süreçteki CP-SAT aramasını fiilen
öldürmüyor) kullanıcıya yansıtan bir not/tooltip eklenmesi
düşünülmeli.

---

## 2026-08-06 — Sprint 2, Gün 10: Frontend — Çözüm ve Çizelge Ekranları

**Tasarım kaynağı:** Kullanıcı bu oturumda `docs/tasarim/` klasörüne
`TASARIM_REFERANSI.md` (renk/tipografi/boşluk tokenleri, sayfa iskeleti,
bileşen tanımları) ve Figma'dan sekiz ekranın tam PNG dışa aktarımını
ekledi. Renk/boşluk/font değerleri doğrudan referans dokümanından
alındı; düzen/bileşen yerleşimi Çizelge ve Çözüm ekran görüntülerinden.
Kullanıcının özellikle vurguladığı iki nokta uygulandı: (1) bölüm
etiketleri `toLocaleUpperCase('tr-TR')` ile büyütülüyor (düz
`.toUpperCase()` değil — `lib/metin.ts`); (2) metne göre otomatik
genişleyen "Durum Rozeti" bileşenine sabit genişlik verildi (`Rozet`
bileşeni, `genislik` prop'u, varsayılan 96px).

**Kapsam:** Yalnızca Çizelge ve Çözüm ekranları işlevsel; kalan altı nav
öğesi (Özet, Tanımlar, Müsaitlik, Tercihler, Analiz, Sürümler) ortak
kabuk (sidebar/topbar) tutarlılığı için `PlaceholderEkrani` ile yer
tutucu — Sprint 3'te doldurulacak.

**Tamamlanan (backend — Gün 10'un ihtiyaç duyduğu, SDD Ek B'de zaten
tanımlı ama henüz kodlanmamış okuma uç noktaları):**
- `GET /api/donem`, `POST /api/donem`.
- `GET /api/surum?donem_id=` (dönem seçiciye göre sürüm listesi).
- `GET /api/surum/{id}/atama`, `GET /api/surum/{id}/kapsama-acigi`.
- `POST /api/atama/kilit` (FR-6.5): mevcut bir atamanın `kilitli`
  bayrağını değiştirir; kural doğrulaması gerektirmez (kilit atamanın
  kendisini değiştirmez). `DogrulamaServisi.kilit_ayarla()`.
- `app/repositories/sonuc.py`: `CizelgeSurumuDeposu.listele(donem_id=)`.
- `app/schemas/surum.py` (yeni): `DonemOku/Olustur`, `CizelgeSurumuOku`,
  `AtamaOku`, `KapsamaAcigiOku`, `AtamaKilitIstek`.

**Gerçek bir tasarım hatası bulundu ve düzeltildi (TD-8 ihlali):**
Gün 9'da yazılan `DogrulamaServisi.dogrula()`, düzenlemeye yalnızca
`taslak` durumundaki sürümlerde izin veriyordu. Ancak bir çözüm işi
bitince sürüm otomatik `cozuldu` durumuna geçiyor (`cozum_servisi.py`)
— ve SRS TD-8 açıkça yalnızca `yayinlandi` durumunun salt okunur
olduğunu söylüyor (`taslak` ve `cozuldu` ikisi de düzenlenebilir
olmalı). Bu, tarayıcıda gerçek bir çözüm çalıştırıp sonucu düzenlemeye
çalışırken ortaya çıktı ("Sürüm taslak durumunda değil" 409 hatası,
beklenmiyordu). **Düzeltme:** `_DUZENLENEBILIR_DURUMLAR = (TASLAK,
COZULDU)` sabiti eklendi, `dogrula()` ve `kilit_ayarla()` (ikincisi
zaten Gün 10'da doğru yazılmıştı) artık aynı kontrolü paylaşıyor.
Regresyon testi: `test_dogrula_cozuldu_surumde_duzenlenebilir`
(`tests/test_dogrulama_servisi.py`).

**Gerçek bir zaman damgası hatası bulundu ve düzeltildi:** Backend
`baslangic_zamani`/`guncelleme_zamani` gibi alanları UTC olarak yazıyor
(`datetime.now(UTC)`) ama DB sütunu saat dilimsiz olduğu için JSON'da
ofsetsiz dönüyor (örn. `"2026-08-06T16:54:11"`). Bunu doğrudan
`new Date(...)`'e vermek tarayıcıyı bunun YEREL saat olduğunu
sanmaya itiyor; "Geçen Süre" sayacında `180:03` gibi anlamsız
değerler olarak ortaya çıktı (tarayıcıda gerçek bir çözüm çalıştırınca
fark edildi). **Düzeltme:** `lib/tarih.ts`'e `utcTarihiAyristir()`
eklendi — ofset yoksa dizeye `Z` ekleyip UTC olduğunu açıkça belirtir;
`zamanBicimle` ve Çözüm ekranının geçen süre hesaplayıcısı artık bunu
kullanıyor. (Backend'i saat dilimli sütuna geçirmek daha büyük bir
göç gerektirir, bu oturumun kapsamı dışında bırakıldı — not düşüldü.)

**Tamamlanan (frontend):**
- `@fontsource/inter` (kendi barındırılan, CDN yok — kurumsal/iç
  dağıtımla tutarlı) + `src/index.css`: tüm renk/boşluk tokenleri CSS
  değişkeni olarak.
- `vite.config.ts`: dev sunucusunda `/api` → `http://127.0.0.1:8000`
  proxy'si (`localhost` yerine `127.0.0.1` — `localhost`'un IPv6'ya
  çözülmesi `uvicorn`'un yalnızca IPv4 dinlediği bu makinede "socket
  hang up" hatasına yol açıyordu, tarayıcıda fark edilip düzeltildi).
- `src/components/`: `AppShell` (sidebar + topbar, sekiz nav öğesi),
  `nav.ts`, `ui.tsx` (`Buton` üç varyant, `Kart`, `KartEtiketi`,
  `Rozet`, `BuyukRakam`) + karşılık gelen `.css` dosyaları — tamamı
  tasarım tokenlerinden besleniyor.
- `src/lib/metin.ts` (`buyukHarf`), `src/lib/tarih.ts` (gün listesi,
  "PZT 3" biçimi, UTC-güvenli zaman ayrıştırma/biçimleme).
- `src/api/types.ts` + `src/api/client.ts`: backend şemalarının TS
  karşılıkları, tek bir `api` nesnesi altında tüm çağrılar; 409
  gövdesini (`DogrulamaSonucuOku`) ayrıştıran `ApiHatasi`.
- `src/screens/CizelgeEkrani.tsx`: dönem/sürüm seçici, personel×gün
  ızgarası (yatay kaydırılabilir, `bos/dolu/eksik/kilitli` dört durum —
  `eksik`, atamanın (tarih, vardiya_tipi, nokta) anahtarı bir
  `kapsama_acigi` satırıyla eşleşince), hücre tıklanınca açılan "Atama
  Düzenle" paneli (`/api/atama/dogrula` önizleme + `PUT /api/atama`
  uygulama + `/api/atama/kilit` kilitleme, ihlal listesi ve ceza
  değişimi gösterimi), "Yeniden Çöz" (Çözüm ekranına dönemi taşıyarak
  geçer).
- `src/screens/CozumEkrani.tsx`: Ayarlar kartı (dönem, zaman limiti, Ön
  Kontrol, Çözümü Başlat), İlerleme kartı (yalnızca çalışırken —
  `accent-surface`, 1,5 saniyede bir `GET /api/cozum/{id}` anketi,
  canlı geçen süre/en iyi ceza; kapsama açığı sayısı yalnızca iş
  bitince hesaplanabildiği için çalışırken "—" gösteriliyor — dürüst
  bir sınır, backend'de canlı bir sayaç yok), Sonuç Özeti kartı (kural
  bazlı ceza dökümü, kapsama açığı özeti, "Çizelgeyi Görüntüle").
- `src/screens/PlaceholderEkrani.tsx`: kapsam dışı altı ekran için.
- `.claude/launch.json` (yeni): `frontend-dev` önizleme yapılandırması.

**Doğrulama (gerçek tarayıcı + gerçek backend + demo veri, uçtan uca):**
- `npx tsc -b`, `npx oxlint`, `npm run build` temiz.
- Backend: geçici Docker PostgreSQL'de tüm paket (93 test — 92 + Gün
  10'da eklenen regresyon testi) iki kez ardışık geçti; `ruff
  check`/`format` temiz.
- Demo veri (`--reset`) ile gerçek `uvicorn` + Vite dev sunucusu
  üzerinden: Ön Kontrol çalıştırıldı ("Yapısal bir engel bulunamadı"),
  15 saniyelik gerçek bir çözüm baştan sona izlendi (Geçen Süre doğru
  akıyor, iş "uyarılı tamamlandı" ile bitti, ceza dökümü + "231 kapsama
  açığı bulundu" doğru gösterildi), "Çizelgeyi Görüntüle" yeni sürümü
  (Sürüm 3) otomatik yükledi, ızgarada `eksik` hücreler doğru
  işaretlendi. Bir hücre seçilip Doğrula/Uygula ile hem **kabul edilen**
  (esnek ceza farkı gösterilen) hem **reddedilen** (H2 — "Onceki
  vardiyayla arada yalnizca 0.0 saat var" mesajıyla, hiçbir şey
  yazılmadığı DB'den doğrulandı) bir değişiklik uçtan uca test edildi.
  Kilitleme aç/kapa döngüsü DB'den doğrulandı.
- Doğrulama sonrası: Vite/uvicorn durduruldu, demo verisi `TRUNCATE`
  ile temizlendi, tüm paket tekrar çalıştırılıp temiz DB'de de geçtiği
  doğrulandı (93 test), Docker test container'ı silindi.

**Sapmalar / notlar:**
- Zaman damgası sütunlarının saat dilimsiz olması (yukarıda) bilinen
  bir sınır olarak not edildi; düzeltme şimdilik yalnızca frontend
  ayrıştırma katmanında (doğru ve yeterli, ama backend'in `TIMESTAMPTZ`
  sütununa geçmesi daha temiz olurdu — Sprint 3'te değerlendirilebilir).
- "Nokta Görünümü" butonu (Çizelge ekranı) kapsam dışı, devre dışı ve
  ipucu metniyle işaretli bırakıldı — tasarım referansında var ama
  UYGULAMA_PLANI'nda Gün 10 kapsamına girmiyor.

**Kalan / ertelenen:** Yok — Gün 10 kapsamındaki tüm maddeler
tamamlandı (kabul kriteri: "Bir çözüm baştan sona arayüzden
başlatılabiliyor, ilerleme görülüyor, sonuç ızgarada görüntüleniyor,
bir hücre elle değiştirilip doğrulama sonucu görülebiliyor" — hepsi
gerçek tarayıcıda doğrulandı).

**Sıradaki oturumun ilk işi:** Sprint 2, Gün 11 — Yeniden Çözme (S8) ve
Sprint 2 Checkpoint. UYGULAMA_PLANI.md'deki Gün 11 maddesini takip et:
SDD 5.6'daki `yeniden_coz` akışını uygula (taslak türetme, kilitli
atamaların sabitlenmesi, S8'in taban atamaları), sürüm durum
geçişlerini (taslak → çözüldü → yayınlandı → arşiv) tamamla (şu an
yalnızca `cozum_servisi.py` içinde taslak→çözüldü geçişi var;
yayınlama/arşivleme uç noktaları henüz yok). Ardından **Ek Görev**
(S1–S8+S6b uyum testi genişletmesi + S4 birim düzeltmesi, Gün 11'den
sonra Gün 12'den önce planlı) ele alınmalı — henüz yapılmadı, PROGRESS.md
ve UYGULAMA_PLANI.md'de not düşülü.

---

## 2026-08-07 — Ara oturum: Tasarım referansı sürüm 2 → shadcn/ui geçişi

Kullanıcı `docs/tasarim/TASARIM_REFERANSI.md`'yi sürüm 2'ye güncelledi
(üzerine yazarak): estetik "teknik rapor" görünümünden standart SaaS
admin paneline geçti — tuğla kırmızısı vurgu → mavi (`#2563EB`), sıfır
köşe yarıçapı → standart ölçek (kart 8px, buton/girdi 6px, rozet tam
yuvarlak), kenarlık-only ayraç → gölge (`shadow-sm`) + ikincil kenarlık,
Inter Light → Semibold/Medium/Regular. Aynı zamanda **elle CSS yerine
shadcn/ui + Tailwind** kullanılmasına karar verildi. Bu, Gün 10'da
tamamlanmış Çizelge/Çözüm ekranlarının **işlevselliğine dokunmayan, salt
görsel bir refactor**; API çağrıları, state yönetimi, doğrulama akışı
birebir korundu.

**Kurulum:**
- Tailwind v4 (`tailwindcss` + `@tailwindcss/vite`) — `npm install
  tailwindcss @tailwindcss/vite`, `vite.config.ts`'e `tailwindcss()`
  eklentisi + `@` path alias (`tsconfig.json`/`tsconfig.app.json`'a da
  `paths` eklendi; `baseUrl` TS 6'da kullanımdan kaldırıldığı için
  atlandı).
- `npx shadcn@latest init` bu ortamda **interaktif olmadan çalışmadı**
  (yeni CLI sürümü "Base color: Blue" yerine kürate edilmiş "preset"
  seçimi istiyor — `-p nova` ile geçildi, `-b radix` ile bileşen
  kütüphanesi seçildi). Sihirbazın ürettiği `src/index.css` kendi
  nötr/gri temasını (oklch tabanlı, Geist fontu) benim tokenlerimin
  üzerine yazdı — **elle tamamen yeniden yazıldı**: `--primary:
  #2563eb` dahil tüm shadcn CSS değişkenleri TASARIM_REFERANSI.md'deki
  hex değerleriyle birebir eşlendi, radius zinciri (`--radius-md/lg/xl`)
  Tailwind'in calc tabanlı hesaplamasına güvenmek yerine doğrudan
  sabitlendi (6px/6px/8px) çünkü Button/Input `rounded-lg`, Card
  `rounded-xl` kullanıyor — iki farklı token, iki farklı px hedefi.
  `npx shadcn@latest add button card badge input label` ile beş
  bileşen `src/components/ui/` altına kopyalandı (bunlar artık bizim
  kodumuz, elle düzenlenebilir/düzenlendi).
- `Card`'a `shadow-sm` + `border-border` eklendi (varsayılan `radix-nova`
  stili yalnızca `ring-1 ring-foreground/10` kullanıyordu, referans
  dokümanının "gölge birincil ayraç" ilkesiyle uyumlu değildi).

**Bileşen eşlemesi** (`src/components/app-ui.tsx`, yeni — eski
`components/ui.tsx`'in yerini alıyor): `Buton`/`Kart`/`KartEtiketi`/
`Rozet`/`BuyukRakam` **aynı Türkçe prop adlarıyla** korundu, böylece
`CizelgeEkrani.tsx`/`CozumEkrani.tsx`'in JSX'i değişmeden yalnızca
import satırı değişti (refactor, yeniden yazma değil — kullanıcının
talimatına birebir uyuldu). İçeride shadcn `Button`/`Card`/`Badge`
sarmalanıyor: `varyant="birincil"|"ikincil"|"hayalet"` →
`variant="default"|"outline"|"ghost"`. `Kart` iç boşluğu shadcn'in
varsayılanı (16px) yerine referans dokümanındaki 32px'e
(`[--card-spacing:--spacing(8)]`) sabitlendi. `Metin Girişi` → shadcn
`Input` (yalnızca Çözüm ekranının zaman limiti alanında; `<select>`
elemanları için hazır bir shadcn bileşeni önerilmediğinden — tabloda
yalnızca "Metin girişi → Input" var — native `<select>` Input'un görsel
diliyle eşleşen Tailwind sınıflarıyla elle stillendirildi). Nav öğesi
`nav.ts` yapısı korunarak `AppShell.tsx` içinde `rounded-md` + hover
durumlarıyla yeniden yazıldı.

**Sabit genişlik kuralı** (kullanıcının özellikle vurguladığı nokta):
`Rozet` bileşeni shadcn `Badge`'i sarmalarken `genislik` prop'unu
(varsayılan 96px, inline `style={{ width }}`) korudu — kütüphane
değişse de düzen kuralı aynen taşındı. Rozet şu an hiçbir ekranda
kullanılmıyor (Sürümler ekranı henüz yok) ama bileşen kütüphanesinde
hazır duruyor.

**Gerçek bir hata bulundu ve düzeltildi (tarayıcıda, bu geçiş
sırasında):** `KartEtiketi`/`Rozet`'in eski uygulaması
`buyukHarf(String(children))` kullanıyordu. JSX'te metin+ifade karışımı
(`sonuç özeti — {durum}` gibi) React'e **ayrı children** olarak gelir;
`String(['a', 'b'])` bunları virgülle birleştirir (`"a,b"`) —
tarayıcıda "SONUÇ ÖZETİ — ,UYARILI TAMAMLANDI" gibi sahte bir virgül
olarak ortaya çıktı. Bu, Gün 10'daki elle yazılmış `ui.tsx`'te de
**aynı şekilde mevcuttu** ama o oturumda bu spesifik çok-child
senaryosuyla (ekran başlığı + değişken) karşılaşılmamıştı — bu geçiş
sırasında gerçek bir çözüm çalıştırılıp Sonuç Özeti kartı görülünce
fark edildi. **Düzeltme:** `Children.toArray(children).join('')`
kullanan bir `duzMetneCevir()` yardımcı fonksiyonu eklendi.

**Doğrulama:** `npx tsc -b`, `npx oxlint` (yalnızca shadcn'in kendi
üretilmiş `button.tsx`/`badge.tsx` dosyalarında beklenen/standart iki
uyarı — `variants` sabitini bileşenle aynı dosyadan export etmekten
kaynaklanıyor, shadcn'in kendi kalıbı, dokunulmadı), `npm run build`
temiz. Gerçek tarayıcıda (1440×900) hem Çizelge (mavi aktif nav, 6px
buton/select köşeleri, `eksik` hücrelerin amber-100/amber-700 rengi,
`Yeniden Çöz`'ün mavi birincil buton stili) hem Çözüm (İlerleme
kartının artık mavi `accent`/`accent-surface` olması, Sonuç Özeti
tablosu) yeniden doğrulandı — sonuç görsel olarak referans
ekranlarındaki mavi/yuvarlak/gölgeli dile birebir uyuyor. Backend'e hiç
dokunulmadı; `pytest -q` (93 test) değişmeden geçti.

**Sapmalar / notlar:**
- `docs/tasarim/`'daki sekiz ekran PNG'si de kullanıcı tarafından
  yenilendi (muhtemelen v2 renk paletiyle yeniden dışa aktarıldı);
  yalnızca Çizelge/Çözüm görselleri bu oturumda referans alındı, diğer
  altısı henüz uygulanmadı (Sprint 3 kapsamı).
- Depoda bu oturumda `docs/BOTAS_Vardiya_Cizelgeleme_Backlog.docx`,
  `..._ProjectCharter.docx`, `..._SRS.docx` dosyalarının da yerel
  olarak değiştiği (`git status`) görüldü — bu oturumun kapsamıyla
  ilgisiz ve içeriği bu oturumda incelenmedi, bu yüzden commit'e dahil
  edilmedi. Kullanıcı bu değişiklikleri ayrıca ele almalı/bilgilendirmeli.

**Kalan / ertelenen:** Yok — bu ara oturumun kapsamı (görsel geçiş)
tamamlandı. Sıradaki iş Gün 11 (yukarıdaki not hâlâ geçerli, değişmedi).

---

## 2026-08-07 — Sprint 2, Gün 11: Yeniden Çözme (S8) ve Sprint 2 Checkpoint

**Tamamlanan (kod):**
- `app/cozucu/model_kurucu.py`: `model_kur()`'a `kilitli_atamalar` parametresi
  eklendi — ısıtma penceresiyle aynı mekanizmayı (x=1'e sabitleme)
  paylaşıyor ama kavramsal olarak ayrı tutuldu (ısıtma penceresi geçmiş
  bir zorunluluk, kilitli atama kullanıcı tercihi).
- `app/repositories/sonuc.py`: `CizelgeSurumuDeposu.taslak_turet()` (SDD
  5.6 — önceki sürüme bağlı yeni bir taslak satırı oluşturur, atamaları
  KOPYALAMAZ) ve `.yayinla()` (TD-8 — sürümü yayınlar, aynı dönemde daha
  önce yayınlanmış bir sürüm varsa arşive alır).
- `app/services/cozum_servisi.py`: `CozumServisi.baslat()` artık
  `onceki_surum_id` alabiliyor (SDD 5.6 `yeniden_coz`): verilirse
  `taslak_turet` ile taslak türetilir, `donem_id` yerine kullanılır.
  `cozum_isini_calistir()`, sürümün `onceki_surum_id`'si doluysa önceki
  sürümün atamalarını okuyup `baglam.onceki_atamalar`'a yazıyor (S8'in
  taban aldığı çizelge) ve kilitli olanları `model_kur`'a
  `kilitli_atamalar` olarak geçiriyor.
- `app/schemas/cozum.py`: `CozumBaslatIstek.donem_id` artık opsiyonel,
  `onceki_surum_id` eklendi; `model_validator` ile tam olarak birinin
  verilmesi zorunlu kılındı.
- `app/schemas/surum.py` + `app/routers/cizelge.py`: `POST /api/surum`
  (SDD Ek B — yalnız taslak türetir, çözüm başlatmaz; asıl yeniden çözme
  `POST /api/cozum` + `onceki_surum_id` ile tek adımda yapılır) ve `POST
  /api/surum/{id}/yayinla` (TD-8) eklendi.
- **"Değişen atama sayısı" (FR-7.4) nasıl raporlanıyor:** Yeni bir alan
  eklenmedi — S8'in `modele_ekle`'si zaten `Σ|x-x_önceki|` hesaplıyor
  (Gün 6'dan beri var) ve bu, `ceza_dokumu["S8"]` üzerinden `CozumOku`'da
  (Gün 8'den beri) zaten dışa açık. `baglam.onceki_atamalar` dolu
  olduğunda bu alan otomatik olarak anlamlı bir sayı taşıyor.
- `tests/test_yeniden_coz.py` (yeni, 5 test): taslak türetme + onceki
  sürüme bağlanma + kilitli atamanın yeniden çözümde aynen koruması (uçtan
  uca, gerçek bir çözüm + kilitleme + yayınlama + yeniden çözüm akışıyla),
  yayınlamanın önceki yayını arşive aldığı, bulunamayan sürümde `None`,
  `CozumBaslatIstek`'in doğrulama kuralı (ikisi de eksik / ikisi de dolu
  → hata).

**Gerçek bir performans/hijyen sorunu bulundu ve çözüldü (kod hatası
değil):** Tam paket testi bu oturumda tekrar tekrar (150 saniyeye kadar
zaman aşımı süresi denenerek) **istikrarlı biçimde** iki testte takılıyordu
— ikisi de birer `CozumServisi.baslat()` çağrısı içeren dosyalarının
İLK testleriydi. `pg_stat_activity` ve canlı `ps aux` ile araştırıldı:
çözücü süreci CPU'da %90+ ile gerçekten çalışıyordu (donmuş değildi),
ama `on_kontrol`/`cozuluyor` aşamalarında normalden çok daha uzun
sürüyordu. Kök neden: bu oturumda `pytest -q` tam paket testi **defalarca**
(shadcn geçişi + Gün 11 hata ayıklaması sırasında) hiç `TRUNCATE`
edilmeden çalıştırıldı; her çalıştırma benzersiz sonek'li (`on_ek`)
personel/talep/vardiya_tipi/görev_noktası satırları biriktirdiği için
(bkz. Gün 8'in test-izolasyon notu — bu satırlar KASITLI OLARAK silinmiyor,
yalnızca benzersiz isimlendirmeyle çakışmaları önlüyor) paylaşılan test
veritabanı 160 personel/108 vardiya_tipi/76 görev_noktası/4019 atamaya
kadar şişti. `baglam_olustur()`'un kapsam dışı (dönem bağımsız) sorguları
ve `model_kur`'un `personel × gün × vardiya × nokta` döngüsü bu şişkin
veriyle katlanarak büyüdü, gerçek testleri neredeyse durma noktasına
getirdi. **Düzeltme:** `TRUNCATE` ile veritabanı temizlendi, tam paket
tekrar 98 testi **6,9 saniyede** geçti (2 kez ardışık doğrulandı) — kod
tarafında hiçbir değişiklik gerekmedi. Küçük bir ek önlem olarak
`test_cozum_servisi.py` ve `test_yeniden_coz.py`'deki `_bekle_ve_getir`
zaman aşımı varsayılanı 45'ten 150 saniyeye çıkarıldı (çoklu-süreç
`multiprocessing.spawn` soğuk başlangıcının + olası gelecekteki hafif
şişkinliğin payını almak için — asıl neden veritabanı temizliği olsa da
bu ek bir güvenlik payı).
- **Öğrenilen ders (gelecek oturumlar için):** Uzun bir oturumda tam paket
  testini defalarca çalıştırırken ara sıra `TRUNCATE` yapılmalı; aksi
  halde biriken test verisi (kasıtlı olarak silinmeyen, yalnızca
  benzersiz sonekli satırlar) zamanla performans testi gibi davranmaya
  başlayıp yanlış "kod hatası" izlenimi verebiliyor.

**Doğrulama:**
- `ruff check`/`format` temiz.
- Geçici Docker PostgreSQL'de tüm paket (98 test — 93 + Gün 11'in 5 yeni
  testi) temiz veritabanında iki kez ardışık geçti (~7-40 saniye,
  makine yüküne göre).
- Gerçek `uvicorn` + demo veri (44 personel, 2 dönem) ile canlı `curl`
  zinciriyle tam SDD 5.6/TD-8 akışı uçtan uca doğrulandı: Sürüm 1
  çözüldü (`uyarılı`) → bir atama kilitlendi → Sürüm 1 yayınlandı →
  `POST /api/cozum` + `onceki_surum_id=1` ile yeniden çözüldü → Sürüm 2
  `onceki_surum_id=1` ile doğru bağlandı, kilitli hücre (personel 13,
  2026-02-13) birebir aynı kaldı (`vardiya_tipi_id=2, nokta_id=5`),
  `ceza_dokumu.S8=485` (S8'in gerçekten aktif olduğunu ve önceki
  çizelgeden sapmayı saydığını kanıtlıyor) → Sürüm 2 yayınlanınca Sürüm 1
  otomatik olarak `arsiv` durumuna geçti.

**Sapmalar / notlar:**
- FR-7.5 (iki sürümü yan yana karşılaştırma) bu günün kapsamına
  alınmadı — Ek B'de "Orta" öncelikli, Gün 11'in kendi madde listesinde
  yok; Sprint 3/Analiz'e bırakıldı, not düşüldü.
- `POST /api/surum` (yalnız taslak türetme, çözüm başlatmadan) Ek B'de
  ayrı bir satır olarak tanımlı olduğu için eklendi, ama Gün 11'in asıl
  kabul kriterinin sınadığı yol `POST /api/cozum` + `onceki_surum_id`
  (SDD 5.6'nın `yeniden_coz`'unu tek adımda birebir uyguluyor).

**Kalan / ertelenen:** Yok — Gün 11 kapsamındaki (Sprint 2 çıkış kabul
kriteri dahil) tüm maddeler tamamlandı. Ek Görev (S1–S8+S6b uyum testi
genişletmesi + S4 birim düzeltmesi) hâlâ yapılmadı — bu oturumun hemen
ardından kullanıcı ayrı bir görev (nokta/talep veri modeli değişikliği)
verdiği için Ek Görev'e henüz geçilmedi, sıradaki oturumda ele alınmalı.

**Sıradaki oturumun ilk işi:** Önce kullanıcının bu oturumun sonunda
verdiği ek görevi (bkz. bir sonraki PROGRESS.md kaydı — nokta/talep veri
modeli sadeleştirmesi) bitir, sonra Ek Görev'e (S1–S8+S6b uyum testi
genişletmesi) geç, ardından Sprint 3 Gün 12'ye (Analiz Servisi ve Ekranı).

---

## 2026-08-07 — Ek görev: Görev noktası/talep matrisi sadeleştirmesi

Kullanıcı `docs/` klasöründeki Charter/SRS/Backlog'u güncelledi (SDD'ye
dokunulmadı — şema değişmiyor, yalnızca demo/tanım verisi). Özet: Kapı ve
Kontrol Odası tek bir "Güvenlik" noktasında birleşti (kontrol odasındaki
personel zaten ayrı bir meslek grubu değil, aynı Güvenlik Görevi
yetkinliğine sahipti), bina ayrımı (Bina A/Bina B) tamamen kaldırıldı —
Müracaat da artık bina ayrımsız tek nokta. Yeni nokta listesi (üçe indi):
Vardiya Şefliği, Güvenlik, Müracaat — üçü de tesis geneli (`bina_id`
NULL). Yeni talep matrisi (SRS 3.3.4, tablo): hafta içi gündüz/akşam
Şef 1 + Güvenlik 7 + Müracaat 2 (toplam 10); gece/hafta sonu/tatil
Şef 1 + Güvenlik 3 + Müracaat 0 (toplam 4). **Kadro büyüklüğü sayıları
değişmedi** (36 kişi "İzin Payıyla" havuz: 7 şef, 6 müracaat, 23
güvenlik; haftalık 144 kişi-vardiya) — Kontrol Odası zaten ayrı bir
yetkinlik değildi. Ayrıca planlama dönemi varsayılan uzunluğu 28 günden
1 haftaya düştü (kısıt değil, yalnızca yeni dönem oluşturmanın başlangıç
değeri).

**Tamamlanan (kod):**
- `app/services/ornek_senaryo.py`: `NOKTA_TANIMLARI` altıdan üçe indi
  (hepsi `bina_adi=None`), `BINA_A`/`BINA_B` sabitleri kaldırıldı,
  `TALEP_DEGERLERI` yeni tabloyla değiştirildi ((1,1,1)/(7,7,3)/(2,2,0)) —
  sütun toplamları (10/10/4) eskisiyle birebir aynı olduğu için
  `PERSONEL_GRUPLARI` (7→9, 6→7, 23→28 ölçeklemesi) **değişmedi**.
- `scripts/demo_veri_uret.py`: `_binalari_olustur()` kaldırıldı (bu
  senaryoda artık hiç Bina satırı yazılmıyor — `Bina` tablosu
  `_her_seyi_temizle`'de temizlik için hâlâ referans alınıyor),
  `_noktalari_olustur()` artık `bina_id=None` sabit veriyor. Dönem
  uzunluğu iki ayrı sabite bölündü: `_RAHAT_DONEM_UZUNLUGU_GUN = 7`
  (yeni varsayılanla uyumlu) ve `_SIKISIK_DONEM_UZUNLUGU_GUN = 28`
  (bilerek korundu — bkz. aşağıdaki tasarım kararı).
- `tests/test_yuk_gostergesi.py`: eski `KAPI_A` sabiti (artık geçersiz
  bir yorum taşıyordu) `ORNEK_NOKTA_ID`'ye yeniden adlandırıldı.
- Frontend: `frontend/src/` içinde "Kapı"/"Kontrol Odası"/"Bina A/B"
  sabit metni aranıp **bulunamadı** — Çizelge ekranı nokta adlarını
  `/api/nokta`'dan dinamik okuyor (Gün 10), hiçbir değişiklik gerekmedi.

**Tasarım kararı (kullanıcıyla netleşti — bkz. AskUserQuestion):**
Sıkışık dönemi de 7 güne indirmek denendiğinde izin haftası dönemin
TAMAMINI kaplıyor, bu da Gün 7/8'de özenle kurulan senaryoyu bozuyordu:
dönem geneli toplam artık haftalık toplamla aynı olduğu için
`on_kontrol` (Kontrol 1/2) açığı doğrudan yakalayıp işi çözücü hiç
çalışmadan `başarısız` ile bitiriyordu — oysa senaryonun bütün amacı
tam tersiydi (bkz. Backlog B-14, SDD 5.2 sınır notu). **Karar:** Rahat
senaryo 7 güne indi; Sıkışık senaryo bilerek 28 gün / 2 haftalık izin
olarak kaldı (kodda bunun kasıtlı olduğunu açıklayan bir yorum var, ki
ileride "tutarsızlık" sanılıp "düzeltilmeye" çalışılmasın). Vardiya
Şefliği havuzunun 9 kişiden 5'i (kalan 4 < teorik asgari 5) hâlâ
donemin ilk iki haftası için izinli.

**Doğrulama:**
- `ruff check`/`format` temiz.
- Tüm paket (98 test) temiz veritabanında geçti; `test_yuk_gostergesi.py`
  hâlâ SRS 3.3.6'nın 144/1.152/29 sayılarını birebir üretiyor (sütun
  toplamları korunduğu için beklenen).
- Demo veri yeniden üretildi ("3 gorev noktasi" çıktısı doğrulandı),
  gerçek `uvicorn` ile uçtan uca: Rahat dönem artık 2026-02-02—02-08 (7
  gün); Sıkışık dönem 2026-03-02—03-29 (28 gün, değişmedi). Sıkışık
  dönemde `/api/on-kontrol` hâlâ boş bulgu döndürdü (açığı kaçırıyor,
  beklenen), gerçek bir çözüm (`uyarılı` sonuçlandı) `kapsama_acigi`'nde
  tam olarak Vardiya Şefliği (nokta_id=1) için, izin penceresi içindeki
  4 gün/vardiyada 1'er eksik raporladı — Gün 7/8'in "ön kontrol kaçırır,
  çözücü yakalar" anlatısı birebir korundu.

**Kalan / ertelenen:** Yok — bu ek görevin kapsamındaki tüm maddeler
tamamlandı.

**Sıradaki oturumun ilk işi:** Ek Görev — S1–S8+S6b Uyum Testi
Genişletmesi (Sprint 2 sonu, UYGULAMA_PLANI.md'de Gün 11'den sonra Gün
12'den önce planlı, henüz yapılmadı): `test_cozucu_uctan_uca.py`'deki
uyum testini S1–S8+S6b'yi de kapsayacak şekilde genişlet, bu sırada S4
birim tutarsızlığını (`modele_ekle` dakika, `dogrula` saat) düzelt.
Ardından Sprint 3 Gün 12'ye (Analiz Servisi ve Ekranı) geç.

---

## 2026-08-07 — Ek görev: S1–S8+S6b uyum testi + S4 birim + S2/S3/S7 formül düzeltmeleri

Bu oturum iki turdur ertelenen Ek Görev'i tamamladı. Kapsam, S4'ün
birim düzeltmesiyle sınırlı başlayıp, uyum testini gerçekten yazarken
iki ayrı önceden var olan formül hatası ortaya çıktı; ikisi de kullanıcıya
`AskUserQuestion` ile sorulup onaylandıktan sonra düzeltildi (SDD/SRS'ten
sessizce sapmama kuralı gereği).

**1. S4 birim düzeltmesi (asıl talep edilen madde):**
- `app/kurallar/esnek.py` `S4ToplamSaatDengesi.modele_ekle`: dakika
  yerine saat kullanacak şekilde değiştirildi (`sure_dakika`/`*60` →
  `round(sure_saat)`), `dogrula` ile aynı birim. Vardiya süreleri
  pratikte zaten tam saat olduğundan yuvarlama etkisiz; CP-SAT'ın
  tamsayı zorunluluğu için gerekli (H5'teki dakika yaklaşımıyla aynı
  gerekçe, ama artık dogrula ile aynı ölçekte).

**2. S2/S3'ün modele_ekle'si SRS'e uymuyordu (kullanıcı onayıyla düzeltildi):**
- Uyum testini yazarken S2/S3 için `ham_terim ≠ dogrula toplamı` çıktı.
  Araştırma: `modele_ekle` SDD Ek A'nın eski S2 örneğini birebir alıp
  aralık (`enb − enk`, dağılımın en yüksek/en düşük ucu) minimize
  ediyordu; `dogrula` ise SRS 4.3'ün normatif formülünü (`sapma[p] =
  max(sayı−taban, tavan−sayı, 0)`, kişi başına toplanır) uyguluyordu —
  ikisi cebirsel olarak eşit değil (karşı örnek: sayılar=[1,1,4],
  ortalama=2 → dogrula toplamı=4, aralık=3).
- Kullanıcı SRS'i otorite kabul edip SDD Ek A'nın örneğinin hatalı
  olduğunu belirtti; `docs/BOTAS_Vardiya_Cizelgeleme_SDD.docx` sürüm
  1.4'e kullanıcı tarafından bu oturumdan önce güncellenmişti (Ek A'daki
  S2 örneği artık SRS formülüyle uyumlu — revizyon notu dosyada mevcut).
  SRS docx'ten S2/S3 4.3 metni bağımsızca okunup doğrulandı.
- Düzeltme: `S2GeceAdaleti`/`S3HaftaSonuAdaleti.modele_ekle` artık
  `enb`/`enk` yerine SRS formülünü birebir uyguluyor — yeni ortak
  yardımcı `_adalet_sapmasi_terimi` (mevcut `_adalet_sapmasi_ihlalleri`
  ile aynı taban/tavan hesabı, CP-SAT tarafında kişi başına bir `sapma`
  IntVar'ı `sapma ≥ sayı−taban`, `sapma ≥ tavan−sayı` kısıtlarıyla).
  `dogrula`'ya dokunulmadı (zaten doğruydu).
- **Beklenen etki:** S2/S3 ceza büyüklükleri büyüdü (aralıktan toplam
  sapmaya geçiş) — bu doğru ve beklenen; ağırlıkların (w2=5, w3=5, demo
  kural tablosunda) bu yeni ölçekte hâlâ makul olup olmadığı aşağıdaki
  doğrulamada gözlemlendi, ayarlama ayrı bir konuşmaya bırakıldı.

**3. S7'de bağımsız, daha ciddi bir formül hatası bulundu (kullanıcı onayıyla düzeltildi):**
- Uyum testi S7 için ham=10, dogrula=2 üretti. `izole_calisma`
  göstergesinin alt sınır eşitsizliğinde fazladan bir `+1` vardı:
  `izole_calisma ≥ calisti[g] − calisti[onceki] − calisti[sonraki] + 1`.
  Üç literalin AND'i için doğru genel form `z ≥ a+b+c−2`; burada
  a=calisti[g], b=1−calisti[onceki], c=1−calisti[sonraki] olduğundan
  sabit **0** olmalı (+1 değil) — `izole_izin`'in eşitsizliği (ters
  işaretli literallerle sabiti −1) zaten doğruydu, S7 kendi içinde
  tutarsızdı.
- Etkisi sanılandan büyük: gerçekten izole bir çalışma gününde (g=1,
  komşular 0) hatalı sabit `izole_calisma ≥ 2` üretiyordu — bool
  değişken üst sınırı (1) aşıldığından bu kombinasyon modelde
  **imkânsız** hale geliyordu (yalnızca yanlış sayım değil, örtük bir
  zorunlu kısıt). Ayrıca tamamen boş bir günde veya bir çalışma
  bloğunun son gününde de (calisti[g]=0 durumları) sabit yine 1'e
  çıkıp gereksiz ceza üretiyordu — muhtemelen önceki oturumlarda
  gözlenen anormal büyük S7 değerlerinin kaynağı buydu.
- Düzeltme: fazladan `+1` kaldırıldı, doğru türetme kod içinde yorum
  olarak bırakıldı (ileride yanlış yeniden türetilmesini önlemek için).

**4. Uyum testi (`test_cozucu_uctan_uca.py::test_esnek_hedefler_cozucu_dogrulayici_uyumu`):**
- Yeni bir senaryo (`_esnek_uyum_baglami`): 4 personel, 2 nokta (ayrı
  binalarda, S6b için), tam 7 günlük dönem (S2/S3/S4'ün taban/tavan ve
  `donem_gun_sayisi/7` hesaplarının tam sayı kalması, dolayısıyla
  yuvarlama kaynaklı sahte uyuşmazlık riskinin sıfırlanması için
  bilerek 7 gün), onaylı tercihler (S5) ve önceki bir çizelge (S8).
  `model_kur` → `CozucuAdaptoru.coz(..., ceza_terimleri=ham_terimler)`
  ile çözülüyor, `durum == "optimal"` doğrulanıyor (gosterge/sapma gibi
  yalnızca alt sınırlı yardımcı değişkenlerin kendi minimuma
  zorlandığından emin olmak için — "uygun" ama optimal-olmayan bir
  çözümde bu garanti yok), sonra S1–S8+S6b'nin her biri için
  `sonuc.ceza_dokumu[kimlik] == dogrula(atamalar, baglam)`'daki
  `ceza` toplamı **birebir eşitlikle** karşılaştırılıyor (SDD 3.2.1'in
  "çözücü ile doğrulayıcı aynı kuralı ifade eder" güvencesinin esnek
  hedeflere genişletilmiş hali).
- İlk çalıştırmada S2/S3/S7 başarısız oldu (yukarıdaki bulgular);
  üçü de düzeltildikten sonra 9 kuralın tamamı (S1, S2, S3, S4, S5,
  S6, S6b, S7, S8) birebir eşitlikle geçiyor.

**Doğrulama:**
- `ruff check`/`format` temiz.
- Tam paket (99 test — 98 + yeni uyum testi) temiz veritabanında geçti
  (~6,6 saniye; DB test kirliliği bu oturumda da bir kez daha
  `TRUNCATE` ile giderildi — bkz. Gün 11'in aynı notu, hâlâ tekrarlayan
  bir bakım işi).
- Gerçek `uvicorn` + temiz demo veriyle (44 personel, 2 dönem) her iki
  dönem de baştan çözüldü. Rahat dönem (`optimal`, 13 sn):
  `S1=0, S2=90, S3=64, S4=608, S5=0, S6=0, S6b=0, S7=0, S8=0` — hepsi
  makul, karşılaştırılabilir büyüklükte (eski S4'ün 60 kata varan
  şişkinliği yok). Sıkışık dönem (`uyarılı`, 90 sn zaman limitinde
  durdu, beklenen — bkz. Gün 7/8): `S1=2, S2=97, S3=59, S4=2448, S5=0,
  S6=0, S6b=0, S7=29, S8=0`; S1=2 önceden bilinen Vardiya Şefliği
  açığıyla tutarlı.

**Sapmalar / notlar:**
- **Ağırlık ayarlaması bilerek bu oturuma alınmadı.** S2/S3'ün büyüklük
  ölçeği değişti (aralıktan toplam sapmaya), S4'ün ölçeği düzeldi (60
  kat küçüldü) — demo kural tablosundaki `w2=5, w3=5, w4=3` gibi
  ağırlıkların yeni ölçekte hâlâ isabetli olup olmadığı ayrıca
  değerlendirilmeli (kullanıcıyla bu oturumun sonunda ayrı konuşulacak
  dendi). Şimdilik hiçbir ağırlık değeri değiştirilmedi.
- `docs/BOTAS_Vardiya_Cizelgeleme_SDD.docx` bu oturumdan önce kullanıcı
  tarafından sürüm 1.4'e güncellenmişti (Ek A'daki S2 örneği düzeltildi);
  bu oturumda dosyaya dokunulmadı, yalnızca doğrulama amacıyla okundu.
  Henüz commit edilmemiş durumda (git status'ta `modified`) —
  kullanıcı elle commit edecek.
- `docs/BOTAS_Vardiya_Cizelgeleme_Charter/SRS/Backlog.docx` hijyen
  maddesi bu oturumdan önce zaten commit edilmişti (bkz. `2ec635d`),
  bu oturumda ayrıca yapılacak bir şey kalmamıştı.

**Kalan / ertelenen:**
- Ağırlık ayarlaması (S2/S3/S4'ün yeni ölçeğine göre `w2`/`w3`/`w4`
  gözden geçirmesi) — ayrı bir konuşma/oturum bekliyor.
- `docs/BOTAS_Vardiya_Cizelgeleme_SDD.docx`'in commit'i kullanıcının
  elle yapacağı bir iş (bu oturumda dokunulmadı, GİT kuralı gereği).

**Sıradaki oturumun ilk işi:** Ağırlık ayarlaması konuşulup karara
bağlanırsa onu uygula; sonra Sprint 3 Gün 12'ye (Analiz Servisi ve
Ekranı) geç.

---

## 2026-08-07 — Ek görev (devamı): dokümanlar .md'ye geçti, S4 yeniden tanımlandı, S6b pasif, ağırlık ölçümü

**Doküman formatı değişti.** Kullanıcı `docs/` altındaki dört `.docx`'i
sildi, yerine dört `.md` dosyası (Charter 1.1, SRS 1.2, SDD 1.4,
Backlog 1.0) ve `docs/diyagramlar/` altında beş şekil (f31/f32/f34/f41/
f51.png, SDD'nin img referanslarıyla eşleşiyor) koydu — sürüm 1.0'ın
son dört günün hiçbir düzeltmesini içermediği, bu yüzden bazı işlerin
güncel olmayan gereksinimlere göre yapılmış olabileceği uyarısıyla.
`git rm` (docx) + `git add` (md + diyagramlar/, flat png'ler taşınarak)
yapıldı, aşağıdaki kod değişiklikleriyle birlikte tek commit'te.

**Dört doküman da baştan sona okundu** (SRS 815 satır, SDD 982 satır,
Charter, Backlog) ve kodla karşılaştırıldı:

**1. S4 SRS v1.2'de yeniden tanımlandı — uygulandı:**
Eski formül (`hedef_saat[p] = haftalik_hedef_saat[p]·donem_gun_sayisi/7`)
gerçek bir kusur taşıyordu: H5 (45 saat tavan) + H6 (haftada 1 izin)
birlikte kişi başı azami 5 vardiya = tam 40 saat veriyor, yani kimse
kişisel hedefini aşamıyor; herkes hedefin eş ya da altında kalıyor ve
`Σsaat[p]` talep tarafından sabitlendiği için `Σ|saat[p]-hedef_saat[p]|`
dağılımdan bağımsız SABİT bir sayıya dönüşüyordu (ölçülen S4=608, tam
olarak `44×40 − 144×8` aritmetiğine eşit) — amaç fonksiyonuna ekleniyor
ama hiçbir optimizasyon sinyali üretmiyordu. Yeni formül (SRS 4.3 S4):
```
toplam_talep_saat = Σ sure[s]·talep[d,s,n]
pay[p] = (hedef_saat[p] / Σ_q hedef_saat[q]) · toplam_talep_saat
Ceza: w4 · Σ_p |saat[p] − pay[p]|
```
`app/kurallar/esnek.py`: yeni paylaşılan yardımcı `_s4_hedef_paylari`
(hem `modele_ekle` hem `dogrula` kullanıyor — pay CP-SAT'in tamsayı
kısıtı gereği en yakın saate yuvarlanıyor, `dogrula` da aynı yuvarlamayı
kullanıyor ki uyum testi birebir eşitlik korusun). `tests/test_kurallar_esnek.py`'deki
iki eski S4 birim testi (`test_s4_saat_sapmasi_ceza_uretir`,
`test_s4_hedefi_tutturunca_ceza_uretmez`) yeni formüle göre yeniden
yazıldı (artık `baglam.talep` dolduruyorlar, pay hesaba talep üzerinden
giriyor).

**2. S6b pasif edildi:**
SRS 4.3 S6 metnine not eklenmiş: nokta sadeleştirmesinden beri bütün
noktalar tesis geneli (`bina_id` NULL), bina değişimi fiziksel olarak
imkânsız, S6b modelde daima 0. `scripts/demo_veri_uret.py`'de S6b
satırına `"aktif": False` eklendi (kural katalogda kalıyor, yalnızca
gösterim verisinde pasif — `KuralDeposu.aktif_kurallari_getir()` zaten
her yerde (`cozum_servisi.py`, `dogrulama_servisi.py`) filtre noktası
olduğu için tek satırlık değişiklik yeterliydi). S1 ağırlığı yorumundaki
eski "digerlerinin toplami (...=41)" hesabı da güncel olmayan bir sayı
taşıdığından kaldırıldı, PROGRESS.md'deki ölçüme işaret eden bir nota
çevrildi.

**3. Genel tutarlılık taraması (madde c) — bulgular:**
- Nokta yapısı, talep matrisi (SRS 3.3.3/3.3.4), dönem varsayılanı (1
  hafta), SDD 5.5'teki kapsam ayrımı (S2/S3/S4 dönem geneli), SDD 5.2
  Kontrol 2 (bireysel izni hesaba katan `min(musait_gun, azami_vardiya_donem)`)
  — hepsi kodla **zaten tutarlı** (önceki oturumlarda uygulanmış).
  Değişiklik gerekmedi.
- Ek A'daki S2 örneğinin `dogrula` sözde kodu (`hedef ← TOPLA(sayilar.degerleri)/SAY(sayilar)`,
  yani GERÇEKLEŞEN atama sayısına göre hedef) kendi `modele_ekle`'siyle
  (`toplam ← TOPLA(talep[...])`, yani TALEP'e göre hedef) tutarsız —
  SRS 4.3'ün kendisi talep tabanlı hedefi tanımlıyor. **Kodda bu sorun
  yok**: `_adalet_sapmasi_ihlalleri`/`_adalet_sapmasi_terimi` ikisi de
  zaten talep tabanlı hedef kullanıyor (bu, kullanıcının bir önceki
  turda "SRS otorite" dediği ve o zaman düzelttiğim formülün ta
  kendisi). Yalnızca dokümandaki Ek A örneğinin `dogrula` yarısı kendi
  `modele_ekle`'siyle tutarsız kalmış — muhtemelen S1 kapsama açığı
  sıfırken fark etmiyor (talep=atanan), S1>0 olduğunda ayrışabilir. Kod
  değişikliği gerektirmiyor, yalnızca **doküman içi bir not** olarak
  burada kayıtlı; SDD'nin bir sonraki revizyonunda Ek A'nın `dogrula`
  satırının da talep tabanlı hedefe çevrilmesi önerilir.
- **NFR-1 sayısı üç yerde üç farklı biçimde:** SRS NFR-1 "Otuz personel",
  SDD 3.4.2 hâlâ "Kırk personel" (SDD bu noktada SRS 1.2'ye
  güncellenmemiş), Charter'ın KENDİ İÇİNDE bile tutarsız (§ölçülebilir
  hedefler "Otuz personel", §4.2 Varsayımlar "Kırk personel"). Şu an
  hiçbir kodda bu sayıya referans yok (Sprint 3 Gün 14'ün performans
  testi henüz yazılmadı), o yüzden kod etkisi yok — ama Gün 14'e
  geçilmeden önce üç dokümanın da aynı sayıda birleşmesi gerekiyor.
  **Karar kullanıcıya bırakıldı, tahmin yürütülmedi.**
- `UYGULAMA_PLANI.md`'nin başındaki referans listesi hâlâ
  `docs/*.docx` yollarını gösteriyor (artık `.md`) — küçük bir hijyen
  notu, bu oturumda dokunulmadı.

**Doğrulama:**
- `ruff check`/`format` temiz.
- Tam paket (99 test) temiz veritabanında 7,3 saniyede geçti.
- Test sırasında Docker'daki `vardiya-pg-test` konteynerinin durmuş
  olduğu görüldü (muhtemelen bir önceki oturumdan beri), `docker start`
  ile yeniden ayağa kaldırıldı. Ayrıca test paketinin biriktirdiği çok
  sayıda başıboş `donem` satırı (muhtemelen dönem-oluşturma testlerinin
  benzersiz sonek kullanmadığı bir yer) fark edildi — bu oturumda yalnız
  `TRUNCATE` ile temizlendi, kök neden araştırılmadı (ayrı bir konu).

**Ağırlık kalibrasyonu için ölçüm (karar verilmedi, yalnızca ölçüldü —
kullanıcının istediği tam biçimde):**

Gerçek `uvicorn` + temiz demo veriyle (44 personel) her iki dönem de
S4/S2/S3/S6b düzeltmeleri sonrası baştan çözüldü. Ağırlıklar: w1=1000,
w2=5, w3=5, w4=3, w5=2, w6=10, w7=2, w8=8 (S6b pasif, katkısı yok).

| Kural | Rahat: ham | Rahat: ham×ağırlık | Sıkışık: ham | Sıkışık: ham×ağırlık |
| --- | ---: | ---: | ---: | ---: |
| S1 | 0 | 0 | 4 | 4000 |
| S2 | 105 | 525 | 216 | 1080 |
| S3 | 62 | 310 | 106 | 530 |
| S4 | 1390 | 4170 | 2266 | 6798 |
| S5 | 0 | 0 | 0 | 0 |
| S6 | 0 | 0 | 0 | 0 |
| S7 | 10 | 20 | 21 | 42 |
| S8 | 0 | 0 | 0 | 0 |
| **Toplam** | | **5025** | | **12450** |
| **Toplam (S1 hariç)** | | **5025** | | **8450** |

(Ağırlıklı toplamlar her iki dönemde de `en_iyi_ceza` alanıyla birebir
eşleşti — 5025.00 ve 12450.00 — bu da ağırlıklandırma hesabında başka
bir hata olmadığının bağımsız bir doğrulaması.)

Rahat dönemde S1=0 olduğu için S1 hariç toplam zaten toplamın tamamı;
kalibrasyon sorusu asıl Sıkışık dönemde anlamlı: **S1 hariç ağırlıklı
toplam (8450), w1'in kendisinden (1000) sekiz kattan fazla büyük.**
Yani solver'ın önünde, tek bir kapsama açığı biriminden (1000 ceza)
vazgeçip diğer yedi hedefi topluca iyileştirerek 1000'den fazla kazanç
sağlayabileceği bir alan matematiksel olarak var — kullanıcının
"baskın ağırlık kâğıt üzerinde kalır" endişesi bu sayılarla somutlaşmış
durumda. En büyük tek katkı S4 (6798, toplamın %80'inden fazlası);
S4'ün formül düzeltmesi cezayı daha anlamlı hale getirdi ama aynı
zamanda büyüklüğünü de artırdı (608'den 2266'ya).

Ağırlıklara **hiç dokunulmadı** (kullanıcının açık talimatı). Karar
kullanıcıya bırakıldı.

**Kalan / ertelenen:**
- Ağırlık kalibrasyon kararı (yukarıdaki ölçüme dayanarak w1 ve/veya
  w4'ün yeniden ayarlanıp ayarlanmayacağı) — kullanıcıdan onay bekliyor.
- SDD Ek A'nın S2 `dogrula` örneğinin talep tabanlı hedefe çevrilmesi
  (doküman-içi tutarsızlık, kod etkilenmiyor) — küçük, ayrı bir revizyon.
- NFR-1'in üç dokümandaki üç farklı sayısının (otuz/kırk) birleştirilmesi
  — Sprint 3 Gün 14'ten önce, kullanıcı kararına bağlı.
- `UYGULAMA_PLANI.md`'nin `docs/*.docx` referanslarının `.md`'ye
  güncellenmesi — küçük hijyen.
- Test paketinin biriktirdiği başıboş `donem` satırlarının kök nedeni
  araştırılmadı.

**Sıradaki oturumun ilk işi:** Ağırlık kalibrasyon kararı netleşirse
uygula (yalnızca kod: `scripts/demo_veri_uret.py`'deki `_KURAL_TANIMLARI`
ağırlıkları — gerçek kullanımda `/api/kural` üzerinden değişecek);
sonra Sprint 3 Gün 12'ye (Analiz Servisi ve Ekranı) geç.

---

## 2026-08-07 — Ek görev (devamı 2): S4 ham cezası imkânsız büyüklükteydi — gerçek kök neden bulundu

Kullanıcı, bir önceki turdaki ölçüm tablosundan (S4 ham=1390, Rahat
dönem) matematiksel bir imkânsızlık çıkardı: 44 personel + 1152 saatlik
toplam talep + H5/H6'nın 40 saatlik kişisel tavanıyla mümkün olan azami
`Σ|saat−pay|` ≈ 774'tü, ama 1390 bunu aşıyordu. Kullanıcının hipotezi
(×10 ölçeklemenin geri çevrilmediği) **kısmen doğruydu ama asıl neden
değildi** — araştırma canlı `baglam` üzerinde doğrudan ölçümle yapıldı
(bkz. aşağıdaki doğrulama), tahmin yürütülmedi.

**Gerçek kök neden:** `_s4_hedef_paylari`, `toplam_talep_saat`'i
`baglam.talep`'in TAMAMI üzerinden topluyordu — ama `baglam.talep`,
`zaman_ekseni_olustur`'un ürettiği tam zaman ekseni (TD-5: ısıtma
penceresi + dönem) için çözülüyor. Isıtma penceresi dönemden hemen önceki
7 gün olduğundan (7'nin katı), aynı gün-tipi talep deseni ısıtma
penceresinde de tekrarlanıyor ve `baglam.talep` üzerinden filtresiz
toplam ~2 katına çıkıyor. Canlı ölçüm: Rahat dönem için `toplam gece
talep` (S2 için) filtresiz 172, dönem-içi (doğru) 86 — birebir 2 kat.
S4 için filtresiz `toplam_talep_saat` 2304, dönem-içi (doğru) 1152 —
yine birebir 2 kat. **Bu bug yalnızca S4'te değil, S2 ve S3'ün
`_adalet_sapmasi_terimi`/`_adalet_sapmasi_ihlalleri` yardımcılarında da
vardı** — üçü de aynı `baglam.talep.items()` filtresiz toplama
desenini paylaşıyordu. SDD Ek A'nın (sürüm 1.4) S2 örneği
(`TOPLA(talep[g,v,n]) HER (g,v,n) İÇİN baglam.donem`) zaten doğru
kapsamı (yalnızca `baglam.donem`, ısıtma penceresi hariç) gösteriyordu;
kod bunu tam uygulamıyordu.

**Düzeltme (`app/kurallar/esnek.py`):**
- `_adalet_sapmasi_terimi` ve `_adalet_sapmasi_ihlalleri`: `toplam_talep`
  hesabına `baglam.donem_icinde(anahtar[0])` filtresi eklendi (S2/S3'un
  hem `modele_ekle` hem `dogrula`'sı).
- `_s4_hedef_paylari` → `_s4_hedef_paylari_x10` olarak yeniden yazıldı:
  aynı `donem_icinde` filtresi + kullanıcının istediği SDD Ek A ölçekleme
  kuralı (aşağıda).

**SDD Ek A'nın yeni kuralı uygulandı — "Kesirli hedeflerin tamsayıya
ölçeklenmesi":** S4'ün `pay[p]`'i kesirli çıkabildiği ve doğrudan bir
mutlak sapma hesabına girdiği için (S2/S3'un taban/tavan hilesi burada
işlemez — pay doğrudan kıyaslanıyor), CP-SAT'in tamsayı kısıtı gereği
hem `pay` hem çalışma saati `_S4_OLCEK=10` (onda bir saat) ile
ölçeklenip tamsayıya çevriliyor. `modele_ekle` artık bütün hesabı
onda-bir-saat biriminde yapıyor, en sonda TEK bir
`model.add_division_equality` ile (yarım birimi yukarı yuvarlayan
`(toplam_x10 + 5) // 10` formülüyle) doğal birime (saat) geri
çevriliyor — döndürülen terim, hem ağırlıklandırma (`kural.agirlik *
terim`) hem `ceza_dokumu` raporlaması için kullanıldığından, bu
geri çevirme yalnızca raporlama değil gerçek optimizasyon davranışını
da düzeltiyor (SDD'nin uyardığı "ağırlığından bağımsız on kat önemli
görünme" tam olarak budur). `dogrula` da aynı ölçeği kullanıyor
(`sapma_x10/10`, kişi başına ondalık hassasiyetli) — ama kişi başına
YUVARLAMA yapmıyor, yalnızca modele_ekle'nin AGREGAT (kişi başına değil,
tüm toplam üzerinde tek seferlik) yuvarlamasıyla eşleşmesi gerekiyor.

**Uyum testi genişletildi (madde 2 — geri çevirmeyi kapsayacak
şekilde):** `test_cozucu_uctan_uca.py::_esnek_uyum_baglami`'deki
personel 4'ün hedef saati kasıtlı olarak farklı bırakıldı (20 vs
diğerlerinin 40'ı) — eşit hedeflerle `pay[p]` hep tam sayı çıkıyor ve
ölçekleme adımı hiç çalışmadan da (kazara) testten geçebilirdi. Kesirli
pay ile ilk çalıştırmada gerçekten yakalandı: ham=7, dogrula (yuvarlanmamış)
toplamı=6.7 — tam da SDD'nin tarif ettiği geri-çevirme adımı eksik
olsaydı ortaya çıkacak fark. Test artık S4 için dogrula toplamını
`_S4_OLCEK` ile yeniden tam sayıya çevirip aynı yarım-yukarı kuralıyla
yuvarlıyor, sonra `ham_terim`'le birebir karşılaştırıyor (diğer sekiz
kural hâlâ çıplak birebir eşitlik).

**Madde 3 (SDD Ek A'nın S2 `dogrula` örneği artık talep tabanlı) —
doğrulandı, kod zaten talep tabanlıydı (bir önceki turda kullanıcının
"SRS otorite" dediği düzeltmenin ta kendisi); değişiklik gerekmedi. Ama
doğrulama sırasında yukarıdaki dönem-kapsamı hatası bulundu ve
düzeltildi — kullanıcının "kapsama açığı olan dönemlerde ikisi ayrışır,
uyum testi bunu yakalamalı" uyarısı, farklı ama ilişkili bir hatayı
(kapsama açığı değil ısıtma penceresi kaynaklı ayrışma) gerçekten
yakalamış oldu.**

**Madde 4 (NFR-1):** SRS 1.3, SDD 1.5 ve Charter'ın kendi içindeki
tutarsız satırı "kırk personel"de birleşti; kodda bu sayıya referans
olmadığından (Sprint 3 Gün 14 performans testi henüz yok) ek bir
değişiklik gerekmedi.

**Doğrulama:**
- Kök nedeni doğrulamak için canlı `baglam_olustur()` çıktısı üzerinde
  doğrudan Python'da ölçüm yapıldı (yukarıdaki 172/86 ve 2304/1152
  rakamları) — koda dokunmadan önce.
- `ruff check`/`format` temiz.
- Tam paket (99 test) temiz veritabanında 7,6 saniyede geçti.
- Yeni uyum testi senaryosu (kesirli S4 payı) ilk çalıştırmada gerçekten
  başarısız oldu (7 ≠ 6.7), düzeltme sonrası geçti — testin genişletmeyi
  gerçekten sınadığının kanıtı.
- Gerçek `uvicorn` + temiz demo veriyle iki dönem de yeniden çözüldü;
  S4'ün canlı `pay[p]` örnekleri (Rahat dönem) `~26.2` saat çıktı —
  kullanıcının elle hesapladığı `26,18`'e birebir yakın (onda bir saat
  yuvarlamasıyla tutarlı).

**Ağırlık kalibrasyonu için ölçüm — TEKRARLANDI (yine karar verilmedi,
yalnızca ölçüldü):**

| Kural | Rahat: ham | Rahat: ham×ağırlık | Sıkışık: ham | Sıkışık: ham×ağırlık |
| --- | ---: | ---: | ---: | ---: |
| S1 | 0 | 0 | 4 | 4000 |
| S2 | 53 | 265 | 59 | 295 |
| S3 | 44 | 220 | 59 | 295 |
| S4 | 152 | 456 | 465 | 1395 |
| S5 | 0 | 0 | 0 | 0 |
| S6 | 0 | 0 | 5 | 50 |
| S7 | 11 | 22 | 36 | 72 |
| S8 | 0 | 0 | 0 | 0 |
| **Toplam** | | **963** | | **6107** |
| **Toplam (S1 hariç)** | | **963** | | **2107** |

(Yine `en_iyi_ceza` ile birebir eşleşti: 963.00 ve 6107.00.)

S4'ün düzeltilmesiyle ham değeri 1390'dan 152'ye (Rahat) ve muhtemelen
benzer oranda Sıkışık'ta düştü — teorik üst sınırın (~774) içinde,
artık gerçek bir dengesizlik ölçüsü. **Sıkışık dönemde S1 hariç
ağırlıklı toplam (2107), w1'in (1000) hâlâ üzerinde ama bir önceki
turdaki 8450'den çok daha yakın** — kalibrasyon sorusu hâlâ geçerli
(solver'ın önünde hâlâ matematiksel olarak 1 kapsama açığı biriminden
vazgeçip diğerlerini toplu iyileştirebileceği bir alan var) ama artık
gerçek bir S4 hatasının değil, yalnızca ağırlıkların kendisinin
sonucu. Ağırlıklara yine hiç dokunulmadı.

**Kalan / ertelenen:** Ağırlık kalibrasyon kararı hâlâ kullanıcıdan
bekliyor (bu turdaki düzeltilmiş ölçümle).

**Sıradaki oturumun ilk işi:** Ağırlık kalibrasyon kararı netleşirse
uygula; sonra Sprint 3 Gün 12'ye (Analiz Servisi ve Ekranı) geç.

---

## 2026-08-07 — Ek görev (devamı 3): ağırlık kalibrasyonu uygulandı

Kullanıcı iki karar verdi (bir önceki turun ölçümüne dayanarak):
1. w1: 1000 → 10000 (Sıkışık'ta S1-hariç ağırlıklı toplam 2107'ydi,
   1000 baskınlık garantisi vermiyordu).
2. Birim ölçeği düzeltmesi: S2/S3'ün ham birimi VARDİYA, S4'ünki SAAT
   (1 vardiya=8 saat) — eski `w2=5/w4=3` ile vardiya-eşdeğeri başına
   S4, S2'nin 5 katı önemli sayılıyordu. `w4 ≈ w2/8` hedefiyle yeni set:
   `S1=10000, S2=10, S3=8, S4=1, S5=12, S6=4, S7=6, S8=15` (S6b pasif,
   ağırlığı 6'da bırakıldı — modele hiç girmiyor).

**Uygulanan:** `scripts/demo_veri_uret.py`'deki `_KURAL_TANIMLARI`
ağırlıkları yukarıdaki sete güncellendi.

**Regresyon testi eklendi**
(`tests/test_agirlik_kalibrasyonu.py`,
`test_s1_agirligi_diger_hedeflerin_agirlikli_toplamindan_buyuk`):
gerçek demo senaryosunu (`scripts/demo_veri_uret.uret`) üretip
`CozumServisi.baslat` ile her iki dönemi de gerçekten çözüyor,
`Kural.agirlik` değerlerini DB'den okuyarak `w1 > Σ_{k≠S1}
ham[k]·agirlik[k]` iddiasını her iki dönem için ayrı ayrı doğruluyor.
Canlı PostgreSQL gerektirir (`pg_yoksa_atla`). İki teknik not:
- `test_cozum_servisi.py`'nin `temel_kurulum` fixture'ı, benzersiz
  sonek kullanmayan düz `H1..S8` kural satırları commit ediyor ve hiç
  temizlemiyor (bilinen bir test-izolasyon eksiği, bu turda kök nedeni
  araştırılmadı) — `demo_veri_uret.uret()` bu satırlarla çakışıp
  `UniqueViolation` veriyordu. Test artık `uret()` çağrısından önce
  `_her_seyi_temizle()`'yi koşulsuz çağırıyor (uret'in kendi "zaten
  var mı" kontrolü yalnızca "Güvenlik Görevi" yetkinliğine bakıyor,
  yalnız kural satırları kalmışsa bu kontrolü atlatıyordu).
- `CozumServisi.baslat` işi ayrı bir `multiprocessing.Process`'te
  çalıştırıyor (SDD 3.4.4); testin kendi `oturum`'u iş biterken hiç
  sorgu atmadığından SQLAlchemy'nin kimlik haritası `ceza_dokumu=None`
  durumundaki eski kopyayı önbellekte tutuyordu — `oturum.expire_all()`
  eklenerek düzeltildi.

**Doğrulama:** `ruff check`/`format` temiz, tam paket (100 test — 99 +
yeni regresyon testi) temiz veritabanında 145 saniyede geçti (yeni
testin kendisi ~90 saniye — iki gerçek çözümü içerdiği için beklenen).

**Gerçek `uvicorn` + temiz demo veriyle iki dönem de yeniden çözüldü
(kullanıcının istediği "dağılımın beklenene yakın çıktığını doğrula"
adımı):**

| Kural | Rahat: ham | ham×ağırlık | Sıkışık: ham | ham×ağırlık |
| --- | ---: | ---: | ---: | ---: |
| S1 | 0 | 0 | 3 | 30000 |
| S2 | 47 | 470 | 59 | 590 |
| S3 | 44 | 352 | 59 | 472 |
| S4 | 152 | 152 | 475 | 475 |
| S5 | 0 | 0 | 0 | 0 |
| S6 | 20 | 80 | 15 | 60 |
| S7 | 1 | 6 | 9 | 54 |
| S8 | 0 | 0 | 0 | 0 |
| **Toplam** | | **1060** | | **31651** |
| **Toplam (S1 hariç)** | | **1060** | | **1651** |

(Yine `en_iyi_ceza` ile birebir eşleşti.)

**S1 baskınlığı artık sağlam:** Sıkışık'ta S1-hariç toplam (1651),
w1'in (10000) çok altında — önceki turun 2107 > 1000 riski tamamen
kapandı, geniş bir pay var.

**Dağılım dengelendi ama kullanıcının elle hesapladığı beklenen
değerlerden SAPMA VAR — bildiriliyor, kendiliğinden düzeltilmedi:**
Kullanıcının "gece 590, hafta sonu 472, saat 465, izole 216, desen 20"
beklentisi, bir önceki turun HAM değerlerini (S2=59, S3=59, S4=465,
S6=5, S7=36) yeni ağırlıklarla çarparak türetilmiş görünüyor. Gece
(590) ve hafta sonu (472) birebir tutturuldu — ama **ham değerlerin
kendisi ağırlık değişince sabit kalmıyor**, çünkü çözücü artık FARKLI
bir ağırlıklı toplamı optimize ediyor ve dolayısıyla farklı bir çizelge
seçiyor:
- S7 (izole): ağırlığı 2'den 6'ya (3 kat) çıkınca çözücü izole
  günlerden gerçekten kaçındı — ham 36'dan 9'a düştü, ağırlıklı katkı
  216 beklenirken yalnızca 54 çıktı (beklenenin ~%25'i, İYİ yönde bir
  sapma — izole gün pratik olarak neredeyse ortadan kalktı).
- S6 (desen): ağırlığı 10'dan 4'e (2,5 kat) İNİNCE çözücü daha fazla
  vardiya-tipi değişimini göze aldı — ham 5'ten 15'e çıktı, ağırlıklı
  katkı 20 beklenirken 60 çıktı (beklenenin 3 katı).
- S4 (saat): ham 465 beklenirken 475 çıktı (yakın, muhtemelen 90
  saniyelik zaman limitinin optimal'i garanti etmemesinden kaynaklanan
  sıradan çözücü varyansı, "uyarılı" durumu — kanıtlanmış optimal
  değil).

Genel kalite hedefi (kullanıcının "tek bir hedef baskın değil" ifadesi)
**sağlandı**: S2/S3/S4 artık aynı büyüklük mertebesinde (352-590),
S1 hâlâ açık ara baskın, hiçbir tek hedef S1 dışında toplamın çoğunu
oluşturmuyor. Ama S6/S7'nin gerçek büyüklüğü, ağırlık kendisi
değiştiği için "eski ham × yeni ağırlık" tahmininden sapıyor — bu,
esnek hedeflerin birbirine bağımlı olmasının (bir kuralın ağırlığı
değişince çözücü TÜM çizelgeyi yeniden seçiyor, yalnızca o kuralın
kendi ihlalini değil) doğal bir sonucu, bir hata değil. Ağırlıklara
bu turda da dokunulmadı; karar kullanıcıya bırakıldı.

**Kalan / ertelenen:**
- S6/S7'nin sapması hakkında karar kullanıcıdan bekleniyor.
- `test_cozum_servisi.py`'nin `temel_kurulum` fixture'ının kural
  satırlarını temizlememesi — bilinen, kök nedeni araştırılmamış bir
  test-izolasyon eksiği (bu turda yalnızca yeni testte etrafından
  dolaşıldı, düzeltilmedi).

**Sıradaki oturumun ilk işi:** S6/S7 sapması hakkında kullanıcı kararı
netleşirse uygula; sonra Sprint 3 Gün 12'ye (Analiz Servisi ve Ekranı) geç.

---

## 2026-08-07 — Sprint 3 Ara İş: "Kontrol Odası" arayüz yenilemesi

Tasarım dili üçüncü ve son kez değişti (`docs/tasarim/TASARIM_REFERANSI.md`
sürüm 3 — koyu şasi, derin teal aksan, turuncu yalnız uyarı için, IBM
Plex, köşe 3-4px, gölge yok). `UYGULAMA_PLANI.md`'ye Sprint 3'ün başına
eklenen Ara İş maddesi uygulandı. Eski ekran görüntüleri
(`Vardiya Çizelgeleme — Admin Panel/`) silinip yenileri
(`Vardiya Çizelgeleme — Kontrol Odası/`) kondu.

**Kapsam netleştirmesi (oturum başında):** Plan "Müsaitlik ve Tercihler
için Gün 4'te hazırlanan uç noktalar var, yeni API gerekmiyor" diyordu —
kontrol ettiğimde bu yanlıştı: `backend/app/routers/`'da yalnızca
`tanim` (FR-1.x) ve `cizelge` router'ları vardı, `/api/musaitlik` ve
`/api/tercih` (FR-2.x/FR-3.x) hiç yazılmamıştı. Kullanıcıya soruldu;
"bu turda backend'i de genişlet, bu kapsam kayması değil SDD Ek B'de
zaten tanımlı iki eksik uç nokta" kararı verildi. `UYGULAMA_PLANI.md`
buna göre güncellendi.

**Backend — iki eksik router (`tanim.py`'deki CRUD örüntüsü izlenerek):**
- `app/repositories/girdi.py` (yeni): `MusaitlikDeposu`, `TercihDeposu`
  (ikisi de `TabanDepo`'nun düz alt sınıfı, özel mantık gerekmedi).
- `app/schemas/girdi.py` (yeni): `MusaitlikOlustur/Oku`,
  `TercihOlustur/Guncelle/Oku`.
- `TanimServisi`'ne `self.musaitlik`/`self.tercih` eklendi (SDD 3.1:
  müsaitlik/tercih zaten "Tanım Yönetimi Alt Sistemi"nin parçası —
  ayrı bir servis/router gerekmedi).
- `tanim.py` router'ına `GET/POST/DELETE /api/musaitlik` ve
  `GET/POST/PUT /api/tercih` eklendi (PUT yalnızca `durum` değiştirir —
  FR-3.4 onay/red).
- `tests/test_girdi_api.py` (yeni, 5 test): mutlu yol (oluştur/listele/
  sil, oluştur/listele/onayla/reddet, vardiya tipi tercihi) + hata yolu
  (var olmayan personel_id ile FK ihlali, var olmayan tercih_id ile 404).

**Frontend — tasarım sistemi:**
- `index.css` baştan yazıldı: sürüm 2'nin mavi/yuvarlak/gölgeli
  tokenlerinin hiçbir kalıntısı yok. Referans dokümanındaki YİRMİ token
  (chrome-*, canvas/surface/sunken/rule/ink, accent/signal ve
  yumuşakları, vardiya-*) `@theme inline` içinde birebir isimleriyle
  Tailwind rengi olarak tanımlandı; shadcn'in genel semantik
  değişkenleri (`--primary`, `--border` vb.) bunların takma adı yapıldı
  ki `components/ui/*.tsx` dosyalarına dokunmadan yeni palet
  devralınsın. **Not:** proje Tailwind v4 (CSS-first `@theme`)
  kullanıyor, `tailwind.config.js` diye bir dosya yok — talimat
  metnindeki dosya adı yerine bu projenin gerçek yapılandırma noktasına
  uygulandı, aynı ilke (token adları birebir, rastgele Tailwind rengi
  yok) korunarak.
- `@fontsource/inter` kaldırıldı, `@fontsource/ibm-plex-sans` +
  `-sans-condensed` + `-mono` eklendi.
- Köşe yarıçapı 3-4px'e sabitlendi, `card.tsx`'teki `shadow-sm` silindi.
- `app-ui.tsx`: `Buton/Kart/KartEtiketi/Rozet/BuyukRakam` yeni tokenlere
  taşındı; yeni `Sayi` bileşeni eklendi (`font-mono tabular-nums`) ve
  tüm sayı/tarih/saat gösterimlerinde kullanıldı (referans dokümanının
  "sayı her yerde Mono" uyarısı). `buyukHarf()` (zaten
  `toLocaleUpperCase('tr-TR')` kullanıyordu, bkz. Gün 10) ve `Rozet`'in
  sabit genişliği (zaten vardı, bkz. Gün 10) korundu — referans
  dokümanının diğer iki uyarısı bu ikisiydi, ikisi de daha önceki bir
  oturumda zaten doğru uygulanmıştı.

**Frontend — kabuk:**
- `AppShell.tsx` yeniden yazıldı: koyu şasi (`chrome-base`), üç başlıklı
  menü grupları (`nav.ts`'e `NAV_GRUPLARI` eklendi: VERİ/ÜRETİM/
  DEĞERLENDİRME), altta `altEylem` slotu (yalnızca Tanımlar alt
  sekmelerinde dolduruluyor) + Dönem bloğu (`/api/donem` ve
  `/api/vardiya-tipi`'den kendi çeker).
- **Bulunan ve düzeltilen bir düzen hatası:** `<aside>` başta
  `flex-col justify-between` ile normal akışta duruyordu; kök flex
  satırı `align-items: stretch` olduğundan, ana içerik (örn. 44 satırlı
  Personel tablosu) sayfayı uzatınca yan menü de AYNI yüksekliğe
  streç oluyor, alt gruptaki "Personel Ekle" butonu ve Dönem bloğu
  görünür alanın çok altına (y≈2100px) itiliyordu — tarayıcıda gerçekten
  test edilmeseydi (yalnızca kısa ekranlarda screenshot alınsaydı)
  fark edilmezdi. `<aside>` `sticky top-0 h-svh overflow-y-auto` yapılarak
  düzeltildi.

**Frontend — ekranlar:**
- Çizelge ve Çözüm yeni dile taşındı, **işlevsellik değişmedi** (aynı
  state/API çağrıları): vardiya kodlaması (gündüz beyaz/akşam sage/gece
  koyu — `VardiyaTipi`'de yalnızca `gece_mi` olduğundan akşam/gündüz
  ayrımı başlangıç saatinden yaklaştırıldı, ≥14:00 akşam sayıldı),
  kilitli hücreler teal `outline`, kapsama açığı `signal` zemin. Çözüm
  ekranındaki ceza dökümü artık referans mockup'taki gibi yatay çubuk
  grafiği.
- Özet, Tanımlar (7 sekme: Talep matrisi düzenlenebilir hücrelerle,
  Personel/Yetkinlik/Bina/Görev Noktası/Vardiya Tipi tablo+ekleme
  formu, Kural H1-H8/S1-S8+S6b tablosu ağırlık/aktiflik düzenlenebilir),
  Müsaitlik (kayıt tablosu + ekleme formu + basit çakışma uyarısı),
  Tercihler (Bekleyen/Onaylandı/Reddedildi sekmeleri + onayla/reddet)
  sıfırdan yazıldı — hepsi gerçek API verisiyle.
- Analiz ve Sürümler kapsam dışı bırakıldı (plan böyle diyor); ikisi de
  `PlaceholderEkrani` üzerinden ama artık yeni `AppShell`/`Kart` diliyle
  render ediliyor (eski mavi tema kalıntısı yok).

**Doğrulama:**
- `ruff check`/`format`, tam backend paketi (105 test) temiz veritabanında
  değişmeden geçti (~2,5 dk — sırf yeni testler eklendiği için, mevcut
  hiçbiri değişmedi).
- `tsc -b --noEmit`, `oxlint`, `npm run build` temiz.
- Gerçek `uvicorn` + `vite` dev sunucusuyla tarayıcıda uçtan uca
  gezildi (1440×900): demo veri (44 personel) + elle eklenen birkaç
  müsaitlik/tercih kaydıyla sekiz ekranın hepsi (Analiz/Sürümler dahil,
  onlar placeholder ama yeni dille) gerçekten açıldı; Çizelge'de gerçek
  bir sürümün ızgarası vardiya renkleriyle göründü; Çözüm'de gerçek bir
  çözüm çalıştırılıp tamamlandı; Tanımlar'ın yedi sekmesi de gerçek veri
  gösterdi (talep matrisi, kural ağırlıkları dahil — kalibre edilen
  S1=10000...S8=15 değerleri ekranda birebir görüldü); Müsaitlik'te
  yeni kayıt formu ve çakışma uyarısı denendi; Tercihler'de "Onayla"
  gerçekten `/api/tercih` PUT'unu tetikleyip durumu değiştirdi (API
  ile bağımsızca doğrulandı).

**Sapmalar / notlar:**
- Kapsam netleştirmesi (musaitlik/tercih router'ları) yukarıda
  açıklandı — kullanıcı onayıyla, kapsam kayması değil.
- `tailwind.config.js` yerine `index.css`'teki `@theme` bloğu
  kullanıldı (proje Tailwind v4) — yukarıda açıklandı.
- Akşam/gündüz vardiya renk ayrımı `VardiyaTipi.gece_mi`'nin
  kapsamadığı bir sezgiye (başlangıç saati ≥14:00) dayanıyor; veri
  modelinde bunu taşıyan bir alan yok, üç vardiyalı (08-16/16-24/00-08)
  mevcut senaryoda doğru çalışıyor ama farklı bir vardiya yapısında
  yanlış sınıflandırabilir. Küçük, bilinen bir sınır.
- Özet ekranının "Toplam Ceza" metriği (referans mockup'ta var)
  kasıtlı olarak eklenmedi: bu veri hiçbir mevcut uç noktadan
  gelmiyor (sürüm ↔ çözüm işi ilişkisini kuran bir endpoint yok),
  eklemek plan dışı üçüncü bir router demek olurdu. Dört dilim
  (Kapsama/Eksik Hücre/Bekleyen Tercih/Sürüm Durumu) gerçek veriyle
  dolduruldu, beşincisi eklenmedi — Gün 12'nin Analiz endpoint'i
  doğal olarak bunu da karşılayacak.
- Kapsama % hesaplaması (Özet) basitleştirilmiş bir yaklaşıklık:
  `atama_sayisi / (atama_sayisi + toplam_eksik)`. Gerçek "kapsama
  oranı" tanımı Gün 12'nin Analiz servisinin işi; bu, o güne kadar
  dürüst (uydurma olmayan) bir ara değer.

**Kalan / ertelenen:** Yok — Ara İş'in kapsamındaki tüm maddeler
tamamlandı (kabul kriteri: sekiz ekran yeni dille açılıyor, Çizelge/
Çözüm akışları bozulmadı, Müsaitlik/Tercihler gerçek veriyle çalışıyor,
iki yeni router'ın testleri var, çözücü/kural motoru/mevcut API
sözleşmesi değişmedi — hepsi sağlandı).

**Sıradaki oturumun ilk işi:** Sprint 3 Gün 12 — Analiz Servisi ve
Ekranı (SDD 5.7'deki yedi metrik; Özet ekranının eksik "Toplam Ceza"
dilimi ve basitleştirilmiş "Kapsama %" hesaplaması de o zaman gerçek
Analiz endpoint'ine bağlanabilir).

---

## 2026-08-07 — Sprint 3 Gün 12: Analiz Servisi ve Ekranı

SDD 5.7'deki yedi metrik uygulandı, dedike `analiz_router` (SDD 3.2'nin
öngördüğü dördüncü router — şimdiye kadar `tanim`/`cizelge` içine
sıkıştırılmıştı, bu artık ayrı). Ara İş'ten devreden not (Özet'in
"Toplam Ceza" kutusu) da bu turda kapatıldı.

**Backend:**
- `app/repositories/sonuc.py`: `CozumIsiDeposu.surume_gore_en_son(surum_id)`
  eklendi — bir sürümün (yeniden çözümle birden fazla olabilecek) çözüm
  işlerinden en sonuncusu, ceza dökümü/toplam ceza kaynağı.
- `app/schemas/analiz.py`, `app/services/analiz_servisi.py` (yeni):
  `AnalizServisi.hesapla(surum_id)` yedi metriği hesaplıyor:
  - **Kapsama oranı:** `baglam.talep`'in dönem içi toplamından (TD-6:
    ısıtma penceresi hariç — `baglam.talep` tam zaman ekseni için
    çözüldüğünden burada açıkça filtrelendi) kapsama açığı tablosundaki
    toplam eksiğin çıkarılmasıyla; SDD 5.7'nin "kapsama açığı
    tablosundan türetilir" ifadesiyle birebir.
  - **Kişi başına gece/hafta sonu sayısı, saat dağılımı:** dönem içi
    atamalar üzerinden `Baglam`'ın zaten var olan
    `gece_mi`/`hafta_sonu_mu`/`sure_saat` yardımcılarıyla. Saat
    dağılımının "kişisel hedef saat"i bilinçli olarak **S4'ün artık
    optimize ettiği talep-payı değil**, sözleşme (`haftalik_hedef_saat`)
    dönem uzunluğuna oranlı hali — Analiz, çözücünün neyi hedeflediğini
    değil personelin sözleşmesine göre nerede durduğunu gösterir (bkz.
    PROGRESS.md Ek Görev, S4 yeniden tanımı).
  - **En dengesiz personel:** saat dağılımındaki `|sapma|` en büyük kişi
    (dokümanda kesin tanım verilmemiş bir metrik; en doğal, saat
    dengesi tablosuyla tutarlı yorum seçildi).
  - **Bina değişim sayısı:** `S6bBinaTutarliligi.dogrula()`'nın
    doğrudan yeniden kullanımı — kural iki ayrı yerde kodlanmaz (SDD
    2.4). Mevcut senaryoda tüm noktalar tesis geneli olduğundan (bkz.
    Ek Görev) her zaman boş liste döner; bina'ya bağlı bir nokta
    tanımlanırsa kendiliğinden çalışır.
  - **Tercih karşılama oranı:** `baglam.tercihler` zaten yalnız o
    dönemin onaylanmış tercihlerini taşıyor (bkz. `baglam_kurucu.py`),
    ayrı bir sorgu gerekmedi.
  - **Ceza dökümü / toplam ceza:** `cozum_isi.surume_gore_en_son`
    üzerinden — Ara İş'te ertelenen kutu, plandaki notun dediği gibi
    ayrı bir router açılmadan buradan besleniyor.
- `app/routers/analiz.py` (yeni): `GET /api/analiz/{surum_id}`,
  `main.py`'ye kaydedildi.
- `tests/test_analiz_api.py` (yeni, 2 test): 404 yolu + elle kurulmuş
  küçük bir senaryoda (2 personel, 7 gün, 1 kapsama açığı, 1 karşılanmamış
  tercih) yedi metriğin tümü elle hesaplanıp doğrulandı. **Bulunan bir
  test-izolasyon deseni:** `baglam.talep` ve `personel_satirlari` sorguları
  tüm tabloyu tarar (Talep SDD 4.2.1 gereği dönem-agnostik bir tanım
  varlığı; saat_dagilimi/en_dengesiz de SDD 5.7 gereği TÜM personeli
  kapsar) — test ilk yazıldığında başka bir oturumdan kalan demo verisiyle
  yanlış toplamlar üretti, `tests/test_agirlik_kalibrasyonu.py`'deki
  aynı TRUNCATE deseniyle düzeltildi.

**Frontend:**
- `AnalizEkrani.tsx` (yeni): Dönem/Sürüm seçici + dört metrik dilimi
  (Dönem Kapsaması, Tercih Karşılama, En Dengesiz, Toplam Ceza), Gece
  ve Hafta Sonu Dağılımı (kişi başına yığılmış çubuk — gece koyu,
  hafta sonu teal, referans mockup'taki gibi), Saat Dengesi tablosu
  (yalnız sapması olanlar listelenir), Ceza Dökümü (Çözüm ekranındaki
  aynı yatay çubuk deseni), Bina Değişim Sayısı (yalnız değişim varsa
  gösterilir). "Dışa Aktar (CSV)" butonu SRS 7.2'deki birebir sütun
  sırasıyla (`sicil, ad, tarih, vardiya_tipi, gece_mi, hafta_sonu_mu,
  sure_saat`) tarayıcıda dosya indiriyor.
- `OzetEkrani.tsx`: eski `atama_sayisi/(atama_sayisi+eksik)` yaklaşıklığı
  kaldırıldı, gerçek `api.analizGetir()` kullanılıyor; beşinci dilim
  "Toplam Ceza" eklendi — mockup'taki beş dilimin (Kapsama/Eksik
  Hücre/Toplam Ceza/Bekleyen Tercih/Sürüm Durumu) tamamı artık gerçek.
- `App.tsx`'e `Analiz` case'i eklendi (Çizelge/Çözüm ile aynı
  donemId/donemIdSec paylaşımı).

**Doğrulama:**
- `ruff check`/`format`, tam backend paketi (107 test — 105 + yeni 2)
  temiz veritabanında geçti.
- `tsc -b --noEmit`, `oxlint`, `npm run build` temiz.
- Gerçek `uvicorn` + demo veriyle Rahat dönem çözüldü
  (`ceza_dokumu={S1:0,S2:46,S3:44,S4:152,S5:0,S6:22,S7:1,S8:0}`,
  `en_iyi_ceza=1058`); `/api/analiz/{surum_id}` doğrudan `curl` ile
  bu değerlerle birebir eşleşti. Tarayıcıda Analiz ekranı gezildi:
  metrik dilimleri, gece/hafta sonu çubukları, saat dengesi tablosu
  (44 personelin tamamı, hepsi hedefin altında — beklenen, Rahat
  dönem 44 kişiye 144 kişi-vardiyalık talep dağıtıyor), ceza dökümü
  hepsi gerçek veriyle doğru göründü; konsol hatası yok. Özet ekranı
  aynı sürüm için Kapsama %100 ve Toplam Ceza 1058 gösterdi.

**Sapmalar / notlar:**
- CSV dışa aktarmanın gerçek dosya indirmesi (Blob/URL.createObjectURL)
  headless tarayıcı ortamında otomatik doğrulanamadı; buton tıklamasının
  konsol hatası üretmediği ve `csvOlustur`'un birim mantığının doğru
  olduğu (SRS 7.2 sütunlarıyla birebir) kontrol edildi, dosya indirme
  akışının kendisi elle test edilmedi.
- "En dengesiz personel" tanımı SDD/SRS'te açıkça verilmemiş; en büyük
  mutlak saat sapması olarak yorumlandı (Saat Dengesi tablosuyla
  tutarlı). Başka bir tanım (ör. gece+hafta sonu toplamı) istenirse
  küçük bir değişiklik.

**Kalan / ertelenen:** Yok — Gün 12'nin kapsamındaki tüm maddeler
(yedi metrik, `/api/analiz/{surum_id}`, CSV dışa aktarma, Özet'in
Toplam Ceza kutusu) tamamlandı.

---

## 2026-08-07 — Sprint 3 Gün 13: Çalışan Paneli

**Tasarım görselleri:** Oturum başında `docs/tasarim/` altında Çalışan
Paneli PNG'leri bulunamadı (yalnızca Kontrol Odası ekranları vardı);
kullanıcıya soruldu, altı PNG (Vardiyalarım/Dönem Özetim/Tercihlerim ×
Masaüstü+Mobil) az sonra eklendi ve incelendi. `TASARIM_REFERANSI.md`
(sürüm 3) hâlâ yalnızca Kontrol Odası'nı kapsıyor — Çalışan Paneli için
ayrı bir referans dokümanı yok, kararlar doğrudan PNG'lerden ve
kullanıcının oturum başı talimatındaki yazılı kararlardan çıkarıldı.

**Doküman senkronizasyonu:** Kullanıcı SRS 1.4/SDD 1.6'nın TD-12 ve
güncellenmiş FR-9.3/SDD 6.1 içerdiğini belirtti, ama `docs/`'taki
kopyalar bunları içermiyordu (yeniden indirilecek bir kaynak URL'i
verilmemişti). Sessizce sapmak yerine dokümanlar bizzat güncellendi:
`SRS` TD-12 (karşılanma durumu, üç değerli) eklendi, FR-9.3 "aylık" ->
"dönem görünümü" oldu; `SDD` 6.1 dört bölümden üçe indirildi (Tercih
bildirimi artık ayrı sekme değil, Tercihlerim'in üstünde) ve tek
sütun/yan menüsüz/B-05 notları eklendi.

**Şema:** Alembic göçü `a1c3f7e9b2d4`: `tercih` tablosuna
`calisan_notu` (çalışanın gerekçesi) ve `ret_gerekcesi` (yöneticinin
ret gerekçesi, FR-3.4) — ayrı alanlar, farklı kişi farklı aşamada
yazıyor. `TercihOlustur`/`TercihGuncelle`/`TercihOku` şemaları buna
göre genişletildi; admin `PUT /api/tercih/{id}` artık `ret_gerekcesi`yi
aynı istekte kabul ediyor (`TercihlerEkrani.tsx`'e küçük bir "Ret
gerekçesi" girişi eklendi, reddet akışını test etmek için gerekliydi).

**Backend — `app/services/calisan_servisi.py` (yeni):**
- `vardiyalarim(personel_id)`: "güncel dönem" `DonemDeposu.
  guncel_donemi_bul` ile bulunuyor (bugünü kapsayan dönem; yoksa en
  yakın gelecek; o da yoksa en son geçmiş — personelden bağımsız, tek
  bir "aktif dönem" varsayımına dayanır). O dönemin YAYINLANDI
  sürümünden (FR-9.2, `CizelgeSurumuDeposu.yayinlanan_getir`) kişiye
  ait atamalar okunuyor.
- **Değişen günler (FR-9.4):** karşılaştırma tabanı aynı dönemdeki EN
  SON ARSIV sürümü (`en_son_arsivlenen_getir`, `yayin_zamani`'na göre).
  Üç tür: atama yalnız yeni sürümde -> `eklendi`; ikisinde de var ama
  vardiya tipi/nokta farklı -> `degisti`; aynıysa `null`. Karşılaştırma
  tabanı yoksa (dönemin ilk yayını) hiçbir gün işaretlenmez.
- **Dönem Özetim (FR-9.5):** `AnalizServisi.hesapla`nın (Gün 12)
  doğrudan yeniden kullanımı — yeniden yazılmadı. Ama servis
  `/api/analiz/{surum_id}` gibi TÜM personelin ad+sayılarını dışarı
  vermiyor: `CalisanServisi._donem_ozeti` yalnızca istenen personelin
  kendi değerini ve tek bir ekip ortalaması sayısını (`ekip_ortalama_*`)
  çıkarıp döndürüyor — SDD 6.1 kabul kriteri "başka bir personelin
  verisine erişemiyor" bunu gerektiriyordu, `/api/analiz` doğrudan
  reuse edilseydi (client'tan çağrılsaydı) her personelin gece/hafta
  sonu/saat kırılımı adıyla karşı tarafa görünür olurdu.
- **Karşılanma durumu (SRS TD-12):** `_karsilanma_durumu` — SAKLANMAZ,
  `tercihlerim` her çağrıldığında ilgili tercihin `donem_id`'sinin
  YAYINLANDI sürümünden (yoksa `henuz_belirsiz`) türetilir. Üç değer
  ayrıntısı için TD-12'ye bkz.
- `tercih_bildir`: SDD Ek B'nin `/api/calisan/tercih` POST'u.
  `donem_id` istemciden gelmiyor (çalışan ekranında dönem seçici yok,
  yalnızca "Gün" tarihi var) — `DonemDeposu.tarihi_iceren_donemi_bul`
  ile tarihten türetiliyor; tarih hiçbir dönemin içine düşmüyorsa veya
  o dönemin `tercih_son_tarihi` geçmişse `TercihDonemiBulunamadiError`
  (router 400'e çeviriyor).
- **"Kişiye özel bağlantı" (Backlog B-05, kimlik doğrulama yok):**
  `app/config.py`'de zaten tanımlı ama hiç kullanılmayan
  `calisan_paneli_baglanti_anahtari` ayarı fark edildi ve bu amaç için
  kullanıldı — üç `/api/calisan/*` uç noktası da `anahtar` sorgu
  parametresini bekliyor, uyuşmazsa 403. Bu GERÇEK bir yetkilendirme
  DEĞİLDİR (herkese aynı anahtar) — yalnızca personel_id'nin rastgele
  denenmesini zorlaştıran, giriş ekranı gerektirmeyen bir bağlantı
  parametresi. Kullanıcıya sorulmadı (talimat açıkça "giriş ekranı
  yapma" dedi, bu çözüm o kısıtı ihlal etmiyor ve zaten var olan bir
  ayarı hayata geçiriyor) ama PROGRESS'e not düşülüyor — istenirse
  kaldırılabilir.
- Yeni depo metotları: `DonemDeposu.guncel_donemi_bul/
  tarihi_iceren_donemi_bul/tercihe_acik_donemi_bul`,
  `CizelgeSurumuDeposu.yayinlanan_getir/en_son_arsivlenen_getir`,
  `AtamaDeposu.surume_ve_personele_gore_getir`,
  `TercihDeposu.personele_gore_getir`.
- `app/routers/calisan.py` (yeni): `GET /api/calisan/vardiyalarim`,
  `GET`+`POST /api/calisan/tercih`, `main.py`'ye kaydedildi.
- **Bulunan ve düzeltilen bir bağımsız hata:**
  `scripts/demo_veri_uret.py`'deki `_her_seyi_temizle` `Tercih`'i hiç
  silmiyordu ve `Donem`'i `Tercih`'ten ÖNCE siliyordu — FK ihlali
  riski, yalnızca bugüne kadar hiçbir test/betik aynı anda hem `Donem`
  hem `Tercih` satırı bırakmadığı için görünmüyordu. Bu oturumun testi
  (`test_calisan_api.py`) tam olarak bunu yaptığında `test_agirlik_
  kalibrasyonu.py` FK hatasıyla patladı; düzeltme: `Tercih` listeye
  eklendi, `Donem`'den önce siliniyor.

**Backend testleri:** `tests/test_calisan_api.py` (yeni, 6 test): 404/
403 yolları, değişen günlerin üç türe ayrıldığı elle kurulmuş bir
senaryo (+ Dönem Özetim'in ekip ortalamasının doğru hesabı),
yayınlanmamış sürümde boş liste, TD-12'nin üç karşılanma değeri
(henüz_belirsiz/karşılanmadı/karşılandı) elle kurulmuş iki-dönemli bir
senaryoda, tercih bildirme mutlu yol + dönem-dışı tarihte 400. Tam
paket 113 test (107 + 6), `ruff check`/`format` temiz.

**Frontend:**
- `src/CalisanApp.tsx` + `src/components/CalisanShell.tsx` (yeni): ayrı
  bir kabuk — Kontrol Odası'nın koyu yan menüsü yok, koyu üst çubuk +
  altında üç sekme, tek sütun (~720px, masaüstünde de ortalanmış).
  Router kütüphanesi eklenmedi (SDD'de tanımsız bir teknik karar
  olurdu); `main.tsx` `window.location.pathname`'i elle ayrıştırıyor:
  `/calisan/{personel_id}?anahtar=...` -> `CalisanApp`, aksi hâlde
  mevcut admin `App`.
- `src/screens/calisan/`: `VardiyalarimEkrani.tsx` (sıradaki vardiya
  kartı — kendi vardiya renginde, kontrast için metin rengi de vardiya
  tipine göre değişiyor; 7 sütunlu dönem görünümü ızgarası; vardiya
  listesi, değişen günler teal sol-kenarlıkla işaretli), `DonemOzetimEkrani.tsx`
  (üç metrik kartı, SEN/EKİP ORT. çubukları), `TercihlerimEkrani.tsx`
  (tercih bildirme formu + bildirilen tercihler listesi, karşılanma
  durumu nokta+etiketle, reddedilmişse gerekçe).
- `lib/tarih.ts`'e `tarihUzunBicim`/`gunEtiketi`/`gunFarki` eklendi;
  `lib/vardiyaRenk.ts` (yeni) — `CizelgeEkrani.tsx`'teki vardiya renk
  kodlama mantığının paylaşılan hali (gündüz/akşam/gece).
- `api/client.ts`+`api/types.ts`: `calisanVardiyalarim`/
  `calisanTercihlerim`/`calisanTercihBildir`; `Tercih` tipine
  `calisan_notu`/`ret_gerekcesi` eklendi; `tercihDurumGuncelle` artık
  isteğe bağlı `retGerekcesi` alıyor.

**Doğrulama:**
- `ruff check`/`format`, tam backend paketi (113 test) temiz veritabanında
  geçti; `tsc -b --noEmit`, `oxlint`, `npm run build` temiz.
- Gerçek `uvicorn`+`vite` ile (bu oturumdaki iki port zaten başka bir
  oturumun sunucularınca kullanıldığından, geçici olarak ayrı portlarda
  ikinci bir çift başlatıldı, doğrulama bitince kapatıldı) tarayıcıda
  uçtan uca gezildi: elle kurulmuş bir demo senaryosunda (H. Aydın,
  03-09 Ağu dönemi, bir ARŞİV + bir YAYINLANDI sürüm) Vardiyalarım
  ekranı sıradaki vardiyayı doğru vurguladı, 7 günlük ızgara ve vardiya
  listesi "eklendi" işaretlerini doğru gösterdi; Dönem Özetim üç
  metriği SEN/EKİP ORT. çubuklarıyla gösterdi; Tercihlerim'de mevcut
  üç tercihin karşılanma durumları (karşılandı/karşılanmadı/gerekçeli
  ret) mockup'la birebir eşleşti, yeni bir tercih gönderildi ve hem
  Tercihlerim listesinde hem admin'in Tercihler > Bekleyen sekmesinde
  gerçek zamanlı göründü. Demo/test verisi doğrulama sonunda temizlendi.

**Sapmalar / notlar:**
- Yukarıdaki doküman senkronizasyonu, "kişiye özel bağlantı" anahtarının
  kullanımı ve `demo_veri_uret.py` düzeltmesi kayda değer sapmalar/ek
  işler; hepsi yukarıda gerekçeleriyle not edildi.
- "Güncel dönem" tek bir dönem varsayımına dayanıyor (aynı anda
  birbiriyle çakışan iki dönem olmaz); gerçek kullanımda dönemler ardışık
  planlandığından bu makul, ama test verisinde (aynı anda "bugünü"
  kapsayan birden fazla dönem oluşabiliyor) bu varsayım ihlal edilirse
  `guncel_donemi_bul` hangi dönemi döndüreceğini garanti etmez —
  bilinen, küçük bir sınır.

**Kalan / ertelenen:** Yok — SDD 6.1'in üç bölümü (Vardiyalarım, Dönem
Özetim, Tercihlerim) ve kabul kriterindeki tüm maddeler (dönem+liste
görünümü, sıradaki vardiya, üç türde değişen gün, gece/hafta sonu/saat
karşılaştırması, tercih bildirme, onay+karşılanma durumu ayrı ayrı,
ret gerekçesi, personel izolasyonu) tamamlandı.

---

## 2026-08-07 — Sprint 3 Gün 13 Düzeltmeleri (gözden geçirme sonrası)

Gün 13 onaylandı; gözden geçirmede iki düzeltme istendi, kanonik
dokümanlar (SRS 1.4 / SDD 1.6) kaynaktan gelen sürümleriyle değiştirildi
ve bu sürümler bir üçüncü uyumsuzluğu ortaya çıkardı.

**0. Kanonik dokümanlar (ayrı commit).** Gün 13'te elle yazdığım TD-12 /
FR-9.3 / SDD 6.1 düzenlemeleri kaynaktan üretilmiş sürümlerle
değiştirildi (`docs: sync canonical SRS 1.4 and SDD 1.6`). **Bundan
sonra `docs/` altındaki dört doküman elle DÜZENLENMEMELİ** — kaynağı
kullanıcıda, elle düzenleme ayrışma doğurur. Değişmesi gereken bir şey
olursa koda değil, buraya not düşülüp kullanıcıya söylenecek.

**1. FR-9.4'ün üçüncü türü: "kaldırıldı".** Gün 13'te yalnız eklendi/
değişti vardı; vardiyası ALINAN çalışan hiçbir işaret görmüyordu.
- `KaldirilanGunOku` şeması **ayrı bir tip** olarak eklendi ve
  `VardiyalarimOku.kaldirilan_gunler` alanında taşınıyor —
  `vardiyalar` listesine karıştırılmadı, çünkü bu bir vardiya değil bir
  vardiyanın YOKLUĞU: o listeden beslenen her şey (vardiya sayısı,
  "sıradaki vardiyan", ızgaranın dolu hücreleri) çalışana artık sahip
  olmadığı bir vardiyayı varmış gibi gösterirdi. Alanlar `onceki_` ön
  ekli (taşıdıkları, elinden alınan vardiyanın bilgisi).
- `_vardiyalari_olustur` artık `(vardiyalar, kaldirilan_gunler)` ikilisi
  döndürüyor; kaldırılanlar "arşivde var, yayınlanmışta yok" farkından.
- **Doğrulandı:** "sıradaki" kaldırılan günü seçmiyor, Dönem Özetim
  sayıları (yalnız yayınlanmış sürümden) etkilenmiyor.
- Arayüz: ızgarada boş hücrenin altına ince teal işaret + listede üstü
  çizili, soluk, "KALDIRILDI" rozetli kendi satırı (tarih sırasına
  gerçek vardiyalarla birlikte yerleşiyor).
- **Ek tutarsızlık giderildi:** efsanede "Değişti" yazıyordu ama
  ızgarada hiçbir değişim türü işaretli değildi. Artık üç tür de
  ızgarada aynı ince işareti alıyor (hangisi olduğu listedeki rozetten
  okunuyor), efsane "Değişen gün" oldu.

**2. Bağlantı kapısı artık kişiye özel (FR-9.1).** Gün 13'teki tek
ortak anahtar, URL'deki `personel_id`'yi değiştiren herkese başkasının
çizelgesini açıyordu — kabul kriterinin "başka bir personelin verisine
erişemiyor" maddesi karşılanmıyordu.
- `app/services/calisan_baglantisi.py` (yeni):
  `anahtar = HMAC-SHA256(sunucu_sırrı, personel_id)`, ilk 32 onaltılık
  karakter. Ek tablo yok (anahtar saklanmıyor, her istekte yeniden
  türetiliyor), mevcut config sırrı korunuyor.
- Doğrulama `hmac.compare_digest` ile **sabit zamanda** — düz `==` ilk
  farklı karakterde döneceğinden anahtar zamanlama üzerinden karakter
  karakter tahmin edilebilirdi.
- Router'da anahtar doğrulaması personelin varlığına BAKILMADAN önce
  yapılıyor: 403/404 farkından geçerli personel kimlikleri sayılamasın.
- `scripts/calisan_baglantisi_uret.py` (yeni): türetilmiş anahtar elle
  hesaplanamayacağı için bağlantıyı dağıtmanın yolu bu betik.
- `.env.example`'a sırrın dağıtımda mutlaka değiştirilmesi ve
  değiştirilirse eski bağlantıların geçersizleşeceği uyarısı eklendi.
- **Hâlâ kimlik doğrulama DEĞİLDİR** (B-05 duruyor): bağlantı taşıyıcı
  belirteç gibi davranır, süresizdir, iptal edilemez, sunucu sırrı
  sızarsa bütün anahtarlar üretilebilir. Sınırlar modül docstring'ine
  yazıldı.

**3. TD-12 uyumsuzluğu (kanonik dokümandan çıktı).** Kanonik TD-12:
*"Türetme yalnızca onaylanmış tercihler için yapılır."* Gün 13'te
karşılanma her tercih için türetiliyordu; ekranda "REDDEDİLDİ +
KARŞILANMADI" yan yana çıkıyordu — yanıltıcı, çünkü reddedilen tercih
zaten modele girmez (FR-3.5), karşılanmaması bir sonuç değil tanım.
Artık `karsilanma` bekleyen/reddedilmiş tercihlerde `None` ve arayüz o
satırı hiç göstermiyor.

**4. Izgara dört haftalık dönemde bozuktu (bulunan hata).** Başlıklar
`gunler.map` ile üretiliyordu: 7 günlük dönemde doğru, ama 28 günlük
dönemde 28 başlık basıp SDD 6.1'in "dört haftalıkta dört satır"
kuralını bozuyordu. Başlıklar sabit yedi güne çevrildi, dönem
pazartesiden başlamıyorsa baştaki/sondaki boş hücreler eklendi.

**5. Liste mobilde kırpılıyordu (bulunan hata).** Satırlar tek satır ve
sabit genişlikliydi; 375px'te nokta adı ve rozet kesiliyordu (sayfa
yatay kaymıyordu, o yüzden Gün 13'te fark edilmemişti — `li` düzeyinde
ölçünce çıktı). Mobil mockup zaten iki satırlı bir düzen gösteriyordu;
satır tek bir duyarlı `ListeSatiri` bileşenine indirildi (mobilde
yığılır, `sm`'den itibaren tek satır). İki dal (vardiya/kaldırıldı)
arasındaki tekrar da böylece kalktı.

**Testler:** 121 test (113 + 8 yeni). Yeni: `test_calisan_baglantisi.py`
(6 test — anahtar kişiye özel, kararlı, sırra bağlı, yalnız kendi
anahtarını kabul ediyor, bağlantı biçimi `main.tsx`'in ayrıştırdığı
yola uyuyor) ve `test_calisan_api.py`'ye eklenen "bir personelin
anahtarı başkasının verisini açmaz" (üç uç nokta için de 403),
"kaldırıldı" senaryosu, "ilk yayında hiçbir gün işaretlenmez", TD-12'nin
beş durumu (henüz belirsiz / karşılandı / karşılanmadı / beklemede→null
/ reddedildi→null). `ruff` temiz, `tsc`/`oxlint`/`build` temiz.

**Doğrulama:** Gerçek uvicorn + vite ile, **dört haftalık** bir demo
dönemi (03-30 Ağu 2026, bir arşiv + bir yayınlanmış sürüm) üzerinde
tarayıcıda gezildi: ızgara 4×7 sarmalandı, altı değişen gün (1 değişti,
4 eklendi, 1 kaldırıldı) hem ızgarada işaretli hem listede doğru rozetli
göründü, kaldırılan gün üstü çizili kendi satırında ve kronolojik yerinde
durdu, "sıradaki" kaldırılan günü atladı, vardiya sayacı (9) kaldırılanı
saymadı, alt not "6 günün değişti" dedi. Tercihlerim'de dört tercihin
karşılanma satırı TD-12'ye göre çıktı/çıkmadı. İzolasyon `curl` ile
doğrulandı: başkasının kimliği + kendi anahtarı → 403, eski paylaşımlı
anahtar → 403. Mobilde (375px) taşan satır sayısı 10'dan 0'a düştü,
masaüstünde tek satır düzeni korundu; konsol hatası yok. Demo verisi
sonunda temizlendi.

**Sapmalar / notlar:**
- HMAC kapısı SDD'de tanımlı bir mekanizma değil; B-05'in "kişiye özel
  bağlantı" ifadesini gerçekleyen bir uygulama detayı olarak eklendi.
  Kanonik dokümanlara işlenmesi isteniyorsa **kaynak dokümanda**
  yapılmalı (bkz. madde 0) — ben `docs/`'u elle düzenlemedim.
- Bağlantıyı yönetici arayüzünden kopyalama alanı EKLENMEDİ; bu bir ürün
  kararı, sorulmadan eklenmedi. Şimdilik dağıtım yolu betik.
- "Güncel dönem" tek dönem varsayımı (Gün 13 notu) duruyor.

**Kalan / ertelenen:** Yok.

---

## 2026-08-07 — Sprint 3 Gün 14: Uçtan Uca Deneyler ve Performans Ölçümü

**Kapsam.** Planın Gün 14 maddesi Charter bölüm 5'teki altı kriterin
BEŞİNİ sayar; altıncısı ("yeniden çözümde değişen atama sayısı
raporlanır") ölçülmedi, çünkü raporlama yüzeyi Sürümler ekranının
karşılaştırma işlevi (SDD 6.3.5) ve o ekran Gün 15'in işi. Bu, plana
uyum; sessiz bir eksiltme değil (betiğin ve notun ikisinde de yazılı).

**`scripts/kabul_olcumu.py` (yeni).** Beş kriteri ölçüp eşik/ölçülen/
sonuç tablosu basan, hepsi geçerse 0 aksi hâlde 1 dönen betik.
Kendi referans verisini kurar (temizler → kurar → ölçer, `demo_veri_uret.py
--reset` ile aynı sözleşme). `--json` ile makine okunur çıktı verir.
- **Referans örnek (40×28):** demo senaryosunun 44 kişilik kadrosu 40'a
  YALNIZCA Güvenlik Görevi havuzu 28→24 çekilerek indirildi; kırılgan
  iki havuz (VŞ 9, Müracaat 7) SRS 3.3.6'daki izin paylı asgarilerin
  (7/6/23) üzerinde korundu.
- **Referans donanım (SDD 3.4.2/3.4.3):** ölçüm makinesi 10 çekirdek,
  referans 4. Arama işçisi sayısı referans değere (3) sabitlendi;
  böylece çözücünün PARALELLİĞİ referans donanımla aynı. Çekirdek
  BAŞINA hız farkı kalıyor — bu yüzden notta süreler "üst sınır değil
  gösterge" olarak nitelendi, kesin doğrulama Gün 15'te gösterim
  ortamında aynı betiğin çalıştırılmasına bırakıldı.

**Sonuç: 4/5 geçti.**
- **K1 (< 60 sn): 1,21 sn** — model kurma 0,51 + ilk uygun çözüm 0,70.
  "Çözülür"ün ne olduğu açıkça tanımlandı: CP-SAT eniyileme yaptığından
  60 sn'de eniyilik kanıtlanmıyor (durum *uygun*); kriterin işaret
  ettiği süre ilk KULLANILABİLİR çizelgeye ulaşma süresi (Charter
  bölüm 6: "limit dolduğunda o ana kadarki en iyi çözüm döndürülür").
- **K2 (sıfır zorunlu ihlal): 0** — H1–H8 doğrulayıcıdan temiz.
- **K3 (gece sapması ≤1): 4,60 → KALDI.** Aşağıda ayrıca.
- **K4 (çelişkili örnekte eksik gösterimi): 31 açık hücre**, her kayıt
  gün+vardiya+nokta+sayı taşıyor.
- **K5 (manuel düzenleme < 1 sn): 0,036 sn** (en kötü, 5 ölçüm).

**K3 — kalan kriter, tanım düzeyinde bir açık (uygulama hatası DEĞİL).**
Önce çözücü yetersizliği mi diye bakıldı: aynı örnek 5 kat süreyle
(300 sn) çözüldüğünde azami sapma DEĞİŞMEDİ (4,60). Betiğe eklenen
"ulaşılabilirlik teşhisi" nedeni otomatik gösteriyor:
- Müracaat görevlileri (7 kişi) yalnız Müracaat noktasında
  görevlendirilebilir (H8); o noktanın dönem boyu gece işaretli talebi
  40 kişi-vardiya → kişi başı tavan 5,71.
- Kriterin sağlanması için her birinin ≥ 8,60−1 = 7,60 gece alması,
  yani toplamda 7×7,60 = 53,2 > 40 olması gerekirdi. **Çelişki: hiçbir
  çizelge bu örnekte K3'ü sağlayamaz.**
- Kökeni iki tanımın birleşimi: (1) **TD-2** gece bayrağını "20:00–06:00
  ile kesişim ≥ 4 saat" diye önerir; Akşam (16:00–24:00) tam 4 saat
  kesiştiği için SINIRDA gece sayılır → üç vardiyanın ikisi gece, dönem
  içi gece talebi 344 (toplamın %60'ı). (2) **S2** (SRS 4.3) hedefi
  `gece talebi / |P|` ile BÜTÜN personele böler, gece çalışamayanlar da
  paydada.
- Akşam'ın bayrağı gündüze çevrilse bile kriter sağlanmıyor (hedef 2,80,
  Müracaat'ın gece sayısı 0 → sapma 2,80): asıl bağlayıcı (2).
- **Değiştirilmedi** — çözümü SRS'i etkiler. Üç seçenek notta gerekçe ve
  ölçülen etkileriyle yazıldı; karar mentör/paydaşın.

**`tests/test_cozucu_dogrulayici_uyumu_olcek.py` (yeni, 24 test).**
Gün 14'ün "rastgele 20+ örnek" maddesi: 24 rastgele örnek (5–9 personel,
5–10 gün, 1–2 nokta, değişken yetkinlik dağılımı) GERÇEK CP-SAT'la
çözülüp H1–H8 doğrulayıcısından geçiriliyor — SDD 3.2.1'in "çözücünün
geçerli saydığı çizelgede doğrulayıcının ihlal bulması bir yazılım
hatasıdır" sözünün otomatik güvencesi. 24/24 temiz. Sabit tohum
(20260814) ile başarısız bir örnek birebir yeniden üretilebilir.
Sprint 1'den kalan `test_cozucu_dogrulayici_uyumu.py` (elle kurulan
çizelgeler, çözücüsüz) yerinde bırakıldı; bu dosya onun yerine geçmiyor,
üzerine çözücüyü ekliyor.

**`docs/PERFORMANS_NOTU.md` (yeni).** Staj raporuna girecek not: ölçüm
ortamı ve referans donanıma göre konumu, referans örneğin tanımı, beş
kriterin sonuç tablosu, K3'ün kanıtı ve seçenekleri, uyum testi sonucu,
yeniden üretme komutları. **Bu dosya dört kanonik dokümandan biri
DEĞİL** — Gün 14'ün kendi çıktısı (kanonik dokümanlara elle
dokunulmadı, bkz. Gün 13 Düzeltmeleri madde 0).

**Doğrulama:** `ruff` temiz; tam paket **145 test** (121 + 24 yeni)
geçiyor. Kabul betiği üç kez çalıştırıldı; K1/K2/K5 sonuçları
değişmiyor, K3'ün sapması ve K4'ün açık hücre sayısı çalıştırmadan
çalıştırmaya değişiyor (CP-SAT paralel aramada belirlenimsiz) — bu da
notta yazıldı.

**Sapmalar / notlar:**
- K3 bilinçli olarak "kaldı" bırakıldı; Gün 14'ün kabul kriteri zaten
  "geçmiyorsa hangi kriterin ne kadar açıkta olduğu net" diyor.
- Ölçüm makinesi referans donanımdan güçlü; süreler gösterge
  niteliğinde. Gösterim ortamı kurulunca (Gün 15) betik orada
  yeniden çalıştırılmalı.

**Kalan / ertelenen:** K3'ün tanım kararı (mentör/paydaş); Charter'ın
altıncı kriteri Gün 15'te Sürümler ekranıyla ölçülebilir hâle gelecek.

---

## 2026-08-07 — Gün 14 Düzeltmeleri: K3 kapandı (5/5)

Kanonik dokümanlar SRS 1.5 / SDD 1.7'ye güncellendi (kaynaktan; `docs/`
elle düzenlenmedi). Gözden geçirmede üç düzeltme istendi; üçü de yapıldı
ve **K3 artık geçiyor**.

**1. VERİ HATASI — demo üreteci SRS 3.3.1'i eziyordu.** SRS 3.3.1'in
vardiya tipi tablosu Akşam'ı açıkça `gece_mi = Hayır` tanımlıyor; TD-2'nin
"20:00–06:00 ile kesişim ≥ 4 saat" kuralı ise bir ÖNERİ (TD-2: bayrak
"hesaplanan değil TANIMLANAN bir alandır"). `demo_veri_uret.py` ve
`kabul_olcumu.py` öneriyi otomatik uygulayıp tanımlı değeri eziyordu:
Akşam (16:00–24:00) pencereyle TAM 4 saat kesiştiği için eşiği sınırda
karşılayıp gece işaretleniyordu. İkisi de artık bayrakları SRS 3.3.1'den
birebir alıyor (`_VARDIYA_TANIMLARI`, üçlü: başlangıç, bitiş, gece_mi).
Dönem içi gece talebi **344 → 112** kişi-vardiya.
- Öneri kuralının API'deki kullanımı zaten doğruydu ve dokunulmadı:
  `VardiyaTipiOlustur.gece_mi` isteğe bağlı, verilirse kullanılıyor,
  verilmezse `gece_mi_oner` ön-dolduruyor — TD-2'nin "nihai değeri
  kullanıcı belirler" cümlesiyle uyumlu.

**2. FORMÜL HATASI — S2/S3'ün paydası (SRS 1.5).** Hedef artık uygun
havuza bölünüyor:
- `Baglam.uygun_havuz(talep_uygun_mu)` (yeni): ilgili talebi bulunan en
  az bir noktanın ön koşulunu (H8) karşılayan personel. **Tanım tek
  yerde**, çünkü dört tüketicisi var ve ayrışırlarsa iki farklı
  "ortalama" görünür: `modele_ekle`, `dogrula`, `AnalizServisi` ve
  `kabul_olcumu.py`.
- `_adalet_sapmasi_terimi` ve `_adalet_sapmasi_ihlalleri` ikisi de
  paydayı ve ceza toplamını havuza indirdi; uyum testi korundu (24
  rastgele örnek + `test_cozucu_uctan_uca.py`'deki sayısal eşitlik
  testi geçiyor).
- **Ölçüm betiğinin kendi K3 hesabı da eski paydayı kullanıyordu** —
  düzeltilmeseydi kod doğru olduğu hâlde kriter kalmaya devam ederdi.
  Betik artık `Baglam.uygun_havuz`'u çağırıyor, kendi tanımını
  uydurmuyor. Ulaşılabilirlik teşhisi de yalnız havuz içini gruplandırıyor
  (havuz dışını "ulaşılamaz" diye raporlamak yanlış alarm olurdu).

**3. ANALİZ METRİĞİ (SDD 1.7).**
- Saat dağılımının tabanı sözleşme saatinden **S4'teki adil paya**
  (`pay[p]`) çevrildi. Hesap S4'ün kendi fonksiyonundan geliyor — kural
  iki ayrı yerde kodlanmaz (SDD 2.4); `_S4_OLCEK`/`_s4_hedef_paylari_x10`
  bu yüzden `S4_OLCEK`/`s4_hedef_paylari_x10` olarak dışa açıldı.
  Kazanç `test_analiz_api.py`'de görünür hâle geldi: eski tabanda iki
  personel 0 ve −32 veriyordu (ikisi de ≤ 0, tablo "kim payından fazla
  aldı"yı yanıtlayamıyordu); yeni tabanda +12 ve −20, yani **iki yönlü**.
- Gece/hafta sonu metrikleri ve ortalamaları uygun havuz üzerinden
  hesaplanıyor; havuz dışındaki personel listelerden çıkarıldı.
- **Bulunan bir uç durum:** Çalışan Paneli'nin "Dönem Özetim"i ekip
  ortalamasını Analiz'den alıyor. Havuz dışındaki bir çalışan (Müracaat)
  kendi panelini açtığında kendi gecesi 0, ekip ortalaması 3,39
  görünüyordu — SDD 5.7'nin tam da kaçınmak istediği yanıltıcı çerçeve.
  `DonemOzetiOku`'ya `gece_havuzunda` / `hafta_sonu_havuzunda` eklendi;
  arayüz havuz dışındaki çalışana o karşılaştırmayı hiç göstermiyor,
  yerine nedenini yazan bir satır çıkıyor.

**K3 yeniden ölçüldü — sonuç 5/5:**

| | İlk ölçüm | Düzeltmeden sonra |
|---|---|---|
| Gece talebi | 344 | **112** |
| Payda | 40 (tüm personel) | **33 (P_gece)** |
| Hedef | 8,60 | **3,39** |
| Gözlenen aralık | 4–12 | **3–4** |
| Azami sapma | 4,60 ❌ | **0,61** ✅ |

K1 1,12 sn · K2 0 ihlal · K3 0,61 · K4 21 açık hücre · K5 0,038 sn.

**Testler:** 152 (145 + 7 yeni). `tests/test_uygun_havuz.py` (yeni, 7
test) havuz mantığını doğrudan kilitliyor: gece talebi olmayan noktanın
personeli havuz dışında; talebi olan noktanınki içeride; `gereken_sayi=0`
olan satır havuza sokmaz; dönem dışı (ısıtma penceresi) talep havuza
sokmaz (TD-6); hafta sonu havuzu aynı mantıkla; ön koşulsuz nokta
herkesi alır; hiç gece talebi yoksa havuz boş (bölme hatası yok).
İki mevcut test beklentileri meşru değiştiği için güncellendi
(`test_analiz_api` adil pay tabanı, `test_calisan_api` fikstürüne gerçek
talep eklendi — talep yoksa havuz boş kalıyor).

**Hata kalıbı notu.** Kullanıcının uyarısı kayda geçti: aynı kalıp dört
kez tekrarlandı (S4'ün ulaşılamaz sözleşme hedefi, Analiz'in saat
dağılımı, S2/S3'ün paydası, ve bu turda ölçüm betiğinin kendi paydası).
Belirti hep aynı: **metrik herkesi aynı yönde sapmış gösteriyor ve
hiçbir ayrım üretmiyor.** Bundan sonra bir adalet/denge metriği
eklerken ilk soru "bu hedefe herkes ulaşabilir mi" olacak.
`tests/test_uygun_havuz.py`'nin docstring'i bu kalıbı açıkça anlatıyor.

**Sapmalar / notlar:**
- **SDD Ek A'daki S2 sözde kodu hâlâ eski paydayı gösteriyor**
  (`hedef ← toplam / SAY(baglam.personel)`), oysa Ek A kendini "SRS
  bölüm 4'teki S2 formülasyonunun birebir karşılığı" diye tanımlıyor.
  SRS 1.5 normatif kabul edilip o uygulandı; `docs/` elle
  düzenlenmediği için kaynak dokümanda güncellenmesi gerekiyor.

**Kalan / ertelenen:** Yok (K3 kapandı). Charter'ın altıncı kriteri
Sürümler/Karşılaştır ekranıyla ölçülecek.

---

## 2026-08-08 — Sürümler Ekranı (SDD 6.3.5) ve Charter K6

Kanonik SDD 1.8 alındı: Ek A'daki S2 örneği artık uygun havuzu kullanıyor
(bildirdiğim tutarsızlık kapandı) ve havuz hesabının **tek yerde tutulup
bütün tüketicilerin oradan alması** artık dokümanda yazılı bir kural.
`Baglam.uygun_havuz` bu kuralı zaten karşılıyor, kod değişmedi.

**Backend — `app/services/surum_servisi.py` (yeni).** SDD 3.2
izlenebilirlik matrisi FR-7.x'i `SurumServisi`'ne bağlıyordu ama servis
yoktu (mantık depo + router'a dağılmıştı); iki işi burada topladım.
- `listele()`: SDD 6.3.5'in istediği liste satırı — numara, durum,
  oluşturma zamanı, **toplam ceza**, **kapsama açığı sayısı**. İki yeni
  toplu depo sorgusu (`surumlere_gore_en_son_ceza`,
  `surumlere_gore_eksik_toplami`) sürüm başına ayrı sorgu açmayı önlüyor.
  Toplam ceza sürümün EN SON çözüm işinden gelir (yeniden çalıştırmada
  birden fazla olabilir); kapsama açığı ise açık hücre sayısı değil
  **toplam eksik kişi** sayısıdır (bir hücrede birden fazla kişi eksik
  olabilir) — ikisi de testle sabitlendi.
- `karsilastir()`: iki sürüm arasındaki farklı atamalar, (personel, tarih)
  ekseninde ve **üç türde** (eklendi / kaldırıldı / değişti) — FR-9.4'ün
  çalışan panelinde kullandığı aynı sınıflandırma, burada yönetici
  tarafında. Karşılaştırma tabanı kullanıcının seçtiği iki sürümdür;
  çalışan panelindeki "en son arşiv" seçimi oraya özgü, buraya
  karıştırılmadı. Farklı dönemlerin sürümleri karşılaştırılamaz (409):
  atamalar farklı takvim günlerine düştüğü için "değişen gün" tanımsız.
- `GET /api/surum/karsilastir` eklendi. **Yol sırası önemli:**
  `/surum/{surum_id}` deseninden ÖNCE tanımlanmak zorunda, yoksa FastAPI
  "karsilastir" dizesini surum_id olarak ayrıştırmaya çalışır.

**Frontend — `SurumlerEkrani.tsx` (yeni).** Mockup'taki sürüm kartları
(durum rozeti, sürüm no, göreli zaman, toplam ceza, açık — açık>0 ise
turuncu), üst çubukta Karşılaştır, kart başına Yayınla / Taslak Türet.
Karşılaştırma paneli iki sürüm seçtirip fark tablosunu ve üç sayacı
gösteriyor. `lib/tarih.ts`'e `goreliZaman` eklendi ("bugün 07:10", "dün
09:04", "2 gün önce" — mockup böyle).
- **Yayınlama onayı (SDD 6.3.5 "Onay istenir"):** önce `window.confirm`
  yazmıştım; uygulamanın hiçbir yerinde modal deseni yok (tasarım
  referansında da yok) ve yerel diyalog hem dile yabancı hem
  otomasyonda kilitleniyor. Satır içi iki adımlı onaya çevirdim: Yayınla
  → sonucu adıyla söyleyen bir şerit ("Sürüm 2 yayınlanacak, Sürüm 1
  arşive alınacak … salt okunur olur") + Vazgeç / Onayla ve Yayınla.

**Bulunan ve düzeltilen bir betik hatası.** `demo_veri_uret.py --reset`
yalnızca `_mevcut_demo_verisi_var_mi()` doğruysa temizlik yapıyordu; oysa
`_her_seyi_temizle` zaten o tabloların TÜMÜNÜ siler. Sonuç: demo dışı
artık bulunan (test fikstürü, kabul ölçümü verisi) bir veritabanında
`--reset` sessizce hiçbir şey silmiyor, üreteç artıkların ÜSTÜNE
ekliyordu. Tam olarak bu yüzden ilk K6 ölçümüm test fikstürünün dönemiyle
demo personelinin karıştığı bir veri üzerinde çıktı. Temizlik artık
`--reset` verildiğinde koşulsuz.

**Charter K6 ölçüldü — 6/6.** Gerçek bir yeniden çözüm üzerinde: Rahat
Dönem çözülüp Sürüm 1 olarak yayınlandı (ceza 912) → GG-001 dönemin ilk
dört gününe izne çıkarıldı → Sürüm 1'den türetilen taslak yeniden çözüldü
(Sürüm 2, ceza 983) → Karşılaştır: **4 değişen atama** (2 kaldırıldı,
2 eklendi, 0 değişti). Sonuç yalnızca raporlamanın değil **S8'in de**
çalıştığını gösteriyor: izne çıkan kişinin iki vardiyası iki başka kişiye
verilmiş, dönemin geri kalanındaki ~140 atama korunmuş.

**Testler:** 157 (152 + 5 yeni). `tests/test_surum_api.py`: liste
satırının toplam ceza (en son çözüm işi) ve kapsama açığı (toplam eksik
kişi) taşıması, karşılaştırmanın üç türü doğru ayırıp sayması, aynı sürüm
kendisiyle karşılaştırılınca fark çıkmaması, bulunmayan sürümde 404,
farklı dönemlerin sürümlerinde 409. `ruff`/`tsc`/`oxlint`/`build` temiz.

**Doğrulama:** Gerçek uvicorn + vite ile tarayıcıda gezildi (1440×900):
sürüm kartları mockup'la örtüştü, Karşılaştır uçtan uca çalıştı (Sürüm 1 →
Sürüm 2, 4 değişen atama, KALDIRILDI turuncu / EKLENDİ teal), Yayınla'nın
onay şeridi doğru metni gösterdi, onaylayınca TD-8 gereği Sürüm 2
YAYINLANDI ve Sürüm 1 otomatik ARŞİV oldu, Taslak Türet Sürüm 3'ü üretti.
Konsol hatası yok. `docs/PERFORMANS_NOTU.md` 1.2'ye çıkarıldı (K6 bölümü
+ 6/6 tablosu).

**Sapmalar / notlar:**
- `GET /api/surum/karsilastir` **SDD Ek B'de listeli değil**. Ek B bir
  "özet" ve 6.3.5 karşılaştırma işlevini açıkça istiyor; uç nokta o işlevin
  doğal karşılığı. Kaynak dokümanda Ek B'ye eklenmesi gerekiyor
  (`docs/`'a elle dokunmuyorum).
- Sürüm listesi uç noktasının yanıtı zenginleşti (`CizelgeSurumuOku` →
  `SurumOzetiOku`); mevcut tüketiciler (Çizelge/Çözüm/Analiz) yalnız
  okudukları alanları kullandığı için etkilenmedi, TS tipi güncellendi.

**Kalan / ertelenen:** Yok. Altı kabul kriterinin tamamı ölçüldü ve geçti.

**Sıradaki oturumun ilk işi:** Dağıtım kullanıcı talimatıyla
BEKLETİLİYOR — her şey karara bağlandıktan sonra tek seferde sunucuya
çıkılacak. Dağıtım turunda yapılacaklar (UYGULAMA_PLANI Gün 15): systemd
servisleri (`uygulama.service`, `cozum-isci.service`), Caddy, PostgreSQL
sistem servisi; kabul ölçümünün gerçek gösterim donanımında yeniden
çalıştırılıp `docs/PERFORMANS_NOTU.md`'nin o sonuçlarla güncellenmesi;
dört dokümanla kodun son tutarlılık kontrolü; `sprint-3` etiketi.

---

## 2026-08-08 — Dağıtım Öncesi Maddeler: 4, 3, 1, 2

Kullanıcının verdiği sırayla. Maddeler 1 ve 2 önceki turlarda zaten
yapılmıştı; doğrulanıp aşağıda raporlandı.

### Madde 4 — Çözüm işçisi ayrı servis + Durdur (yeni)

SDD 3.4.4'ün tanımladığı mimariye geçildi: çözüm işi artık API sürecinin
çocuğu değil, **ayrı bir servis**. Yapılandırma anahtarı KONMADI (kullanıcı
uyarısı: iki kip bırakmak aynı davranışı iki yerde tanımlamaktır ve bu
projede üç kez soruna yol açan kalıbın kendisidir).

- `CozumServisi.baslat` süreç açmayı bıraktı; işi `kuyrukta` durumunda
  yazıp dönüyor. `multiprocessing` bağımlılığı ve `_disaridan_calistir`
  kalktı.
- `scripts/cozum_iscisi.py` (yeni): kuyruğu yoklayıp `cozum_isini_calistir`
  çağıran döngü. `siradaki_isi_isle()` tek adımı yapar (bir iş işler ya da
  None döner) — testlerin senkron çağırdığı giriş noktası.
- **Yarışa kapalı kapma:** `UPDATE cozum_isi SET durum='ON_KONTROL' WHERE
  is_id = (SELECT ... WHERE durum='KUYRUKTA' ... FOR UPDATE SKIP LOCKED)
  RETURNING is_id`. Durum değişikliği ile seçim tek ifadede olduğu için iki
  işçi aynı işi alamaz; ayrı bir sahiplik sütununa gerek kalmadı.
  Enum'ların veritabanında **isimle** saklandığı (`KUYUKTA` değil
  `KUYRUKTA`) ham SQL yazmadan önce doğrulandı.
- **SIGTERM:** bayrak kaldırılır, eldeki iş TAMAMLANIR, döngü ondan sonra
  çıkar. Yarım çizelge yazmak, kural ihlali içermeyen ama kapsaması eksik
  bir çizelgeden ayırt edilemeyeceği için yanıltıcı olurdu (SDD 5.4).
  Unit'teki `TimeoutStopSec=180s` bu yüzden çözücü limitinden geniş.
- **Durdur:** bayrak için ayrı sütun açılmadı — `durum=IPTAL` zaten SDD
  5.4'ün durum makinesinde var ve "veritabanına bir bayrak yazar" tam
  olarak bu. API durumu IPTAL'e çeker; işçi bunu CP-SAT geri çağırımında
  `oturum.refresh(is_kaydi, ["durum"])` ile **taze** okur (kimlik
  haritasındaki önbellek başka bağlantının değişikliğini görmez) ve
  `stop_search()` çağırır. Sonuç yazma bloğundan ÖNCE kontrol edilir, yarım
  sonuç yazılmaz (SDD 6.3.2).
- **Bilinen sınır (kodda ve DAGITIM.md'de yazılı):** geri çağırım yalnızca
  yeni ve daha iyi bir çözüm bulununca tetiklenir; iki iyileşme arasında
  uzun bir sessizlik varsa durdurma o sessizlik bitene ya da zaman limitine
  kadar etkisini göstermez. Ayrı servis mimarisinde süreç öldürmek mümkün
  olmadığı için bu kaçınılmaz.
- **5 mevcut test yeniden yazıldı:** `tests/conftest.py`'ye
  `isi_calistir_ve_bekle()` eklendi; işçinin tek adımını senkron sürüyor.
  Yoklama/zaman aşımı/yarış kalktı, testler belirlenimli oldu.
- `tests/test_cozum_iscisi.py` (yeni, 6 test): kuyruğa yazma, işi alıp
  çalıştırma, boş kuyruk, aynı işin iki kez kapılamaması, kuyruktayken
  iptal edilen işin hiç alınmaması, çözüm sırasında iptalde **hiçbir atama /
  kapsama açığı yazılmaması ve sürümün taslak kalması**.
- `deploy/cozum-isci.service` yazıldı, DAGITIM.md bölüm 7'deki açık madde
  kapatıldı. README'ye yerel geliştirmede işçinin ayrı çalıştırılması
  gerektiği eklendi.
- **Test yazarken bulunan bir tuzak:** fikstüre yalnız H1–H8 koyunca iş
  "tamamlandı" görünüp sıfır atama üretiyor — S1 olmadan kapsama kısıtı
  kurulmuyor, model boş amaç fonksiyonuyla çözülüyor. Fikstür S kurallarını
  da yükleyecek şekilde düzeltildi, nedeni yorumda yazılı.

**Gerçek servisle uçtan uca doğrulandı:** işçi ayrı süreçte işi aldı ve
tamamladı (`cozuluyor` → `tamamlandi`); 28 günlük bir iş sürerken Durdur
gönderildi, iş `iptal` oldu ve veritabanında **0 atama, 0 kapsama açığı,
sürüm `taslak`, ceza dökümü None** kaldı; iş sürerken SIGTERM gönderildi,
işçi eldeki işi bitirip (`tamamlandi`) temiz çıktı.

### Madde 3 — TIMESTAMPTZ göçü (yeni)

- Kapsam modellerden üretildi: **35 sütun, 16 tablo**; listesi göç
  dosyasının başına yorum olarak yazıldı. DATE sütunları (dönem/atama
  tarihleri) kapsam dışı — onlar bir takvim günü, bir zaman anı değil (TD-1).
- `ZamanDamgasi = DateTime(timezone=True)` `app/models/ortak.py`'de tek
  yerde tanımlandı; karışım ve üç açık sütun (`yayin_zamani`,
  `baslangic_zamani`, `bitis_zamani`) oradan alıyor.
- Göç `c8f2d1a45b73`: her sütun için açık
  `USING <kolon> AT TIME ZONE 'UTC'`. Bırakılsaydı PostgreSQL sunucunun
  saat dilimini varsayıp sessizce kaydırırdı.
- **Kayma olmadığı kanıtlandı:** oturum saat dilimi `Europe/Istanbul`
  yapılıp göç öncesi `12:00` naive değer yazıldı; göçten sonra UTC
  karşılığı **12:00 kaldı**, İstanbul'da `15:00+03` göründü. Downgrade →
  upgrade gidiş-dönüşü de çalıştırıldı.
- Göçten sonra API'nin gerçekte ne döndürdüğü ölçüldü:
  `'2026-08-08T06:14:14.058150Z'` — artık ofsetli.
- `utcTarihiAyristir` tek geçiş noktası olarak KALDI ama sağlamlaştı: eski
  regex (`/[zZ]|[+-]\d\d:\d\d$/`) `[zZ]`'yi sona bağlamıyordu ve `+0300`
  biçimini kaçırıyordu. Yeni hâli ofseti yalnız **zaman bölümünde** arıyor
  ('Z', '+03:00', '+0300', '+03'), tarih bölümündeki tireyi ofset sanmıyor.

### Maddeler 1 ve 2 — önceki turlarda yapılmıştı (doğrulandı)

- **Madde 1:** `app/services/calisan_baglantisi.py` — anahtar
  `HMAC-SHA256(secret, personel_id)`, doğrulama `hmac.compare_digest` ile
  sabit zamanlı, sır `.env`'den. `scripts/calisan_baglantisi_uret.py` yeni
  şemayı kullanıyor. Yönetici arayüzünde bağlantı gösteren/kopyalatan bir
  yer **yok**, o yüzden orada güncellenecek bir şey de yok. Testler:
  doğru anahtar 200, yanlış anahtar 403, **başka personelin geçerli
  anahtarı 403** (üç uç nokta için de).
- **Madde 2:** FR-9.4'ün üçüncü türü tamam. Kaldırılan günler
  `kaldirilan_gunler` alanında **ayrı** taşınıyor (bir vardiya değil,
  yokluğu); ızgarada boş hücreye ince işaret, listede üstü çizili
  "KALDIRILDI" satırı. Karşılaştırma tabanı çalışan panelinde
  `en_son_arsivlenen_getir` (aynı dönemdeki en son arşiv); Sürümler
  ekranının kullanıcı seçimli tabanıyla karıştırılmadı — iki ayrı kod yolu.

### Madde 6 — testler

**163 backend testi** geçiyor (157 + 6 yeni işçi testi). Ek olarak
**8 frontend testi** (`src/lib/tarih.test.ts`). `ruff`, `tsc`, `oxlint`,
`build` temiz.

**Sapmalar / notlar:**
- **Frontend'e `vitest` eklendi** (dev bağımlılığı + `npm test` betiği).
  Madde 3 `utcTarihiAyristir` için test istiyordu ve frontend'de hiç test
  koşucusu yoktu; Vite projesinin standart karşılığı bu. SDD'de tanımlı
  olmayan bir kütüphane kararı olduğu için burada not ediliyor.
- Dağıtım paketi hazır: `deploy/uygulama.service`,
  `deploy/cozum-isci.service`, `.env.example` (sırlar BOŞ),
  `deploy/DAGITIM.md`.

**Kalan / ertelenen:** Sunucuya dağıtım (madde 7) ve referans donanımda
kabul ölçümü (madde 8) — sunucu bilgileri/erişim henüz gelmedi.

**Sıradaki oturumun ilk işi:** Sunucu erişimi gelince madde 7 (bağımlılık
kurulumu, PostgreSQL, Alembic göçleri — TIMESTAMPTZ göçü dahil, frontend
derlemesi, systemd) ve ardından madde 8 (kabul ölçümünün sunucuda
tekrarı, PERFORMANS_NOTU'na İKİNCİ sütun olarak işlenmesi). Sırlar
kullanıcı tarafından doldurulacak; servisler ondan sonra başlatılacak.

---

## 2026-08-09 — Sunucuya Dağıtım (madde 7) ve Referans Donanımda Ölçüm (madde 8)

**Site yayında: https://vardiya.omerharmankaya.com — 6/6 kabul kriteri
referans donanımda geçti.**

### Madde 7 — dağıtım

Kullanıcının dört değişikliği uygulandı: port **8002** (8000 `vera-rag`,
8001 `energy-api`), servis adları **`vardiya-api`** / **`vardiya-cozucu`**,
frontend **yerelde** derlenip `dist/` yüklendi (sunucuda Node yok), Caddy'ye
`vardiya.omerharmankaya.com` bloğu eklendi (yedek alındı, `caddy validate`
→ *Valid configuration*, diğer bloklara dokunulmadı).

Port tek yerde: unit'in `--port` bayrağında. `.env.example`'a bir `API_PORT`
satırı eklemiştim, **geri aldım** — `config.py` onu okumuyor; uygulamanın
okumadığı ama otoriter görünen ikinci bir tanım olurdu.

**Python 3.14 dört sabit sürümü zorladı.** Ubuntu 26.04'ün deposunda tek
Python sürümü 3.14 ve aynı makinedeki diğer projeler de onu kullanıyor.
Kullanıcı `ortools` yükseltmesini onayladı; aynı sınıf sorun üç pakete daha
çıktı. Her biri, çalışan **en düşük** sürüme çekildi (en yenisine değil):

| Paket | Önce | Sonra | Belirti |
|---|---|---|---|
| `ortools` | 9.14.6206 | 9.15.6755 | 3.14 tekerleği yok |
| `psycopg[binary]` | 3.2.3 | 3.2.10 | `psycopg-binary` tekerleği yok |
| `pydantic` | 2.10.4 | 2.12.0 | `pydantic-core==2.27.2`'yi tam sabitler, onun tekerleği yok |
| `sqlalchemy` | 2.0.36 | 2.0.41 | **kuruluyor ama çalışma anında çöküyor** |

Son satır önemli bir ders: ilk üçünü `pip install --dry-run` ile taradım ve
SQLAlchemy'yi "OK" işaretledi — saf Python tekerleği var, kurulum sorunsuz.
Ama `typing.Union.__getitem__` 3.14'te değişmiş ve model tanımları içe
aktarılırken çöküyor. **Kurulabilirlik ≠ çalışabilirlik.** SQLAlchemy 3.14
sınıflandırıcısı da yayınlamadığı için asgari sürüm ampirik bulundu
(2.0.37/.39/.40 hata, 2.0.41 çalışıyor). Bundan sonra sunucuda **163/163**
test geçti; başka yükseltme gerekmedi.

**Sırlar:** üretmedim, yazmadım. `.env` sır satırları boş bırakılıp
kullanıcıya devredildi (`0640 root:vardiya`). İlk denemede `VERITABANI_URL`
satırına **yalnız parola** yazılmıştı (32 karakter; tam URL ~52+). Kendim
düzeltmedim — düzeltmek parolayı okuyup yeniden yazmak olurdu; kullanıcıya
tam şablonu ve değeri açmadan biçim kontrolü yapan tek satırlık komutu
verdim. Aynı hata daha önce yerel `.env`'de de olmuştu, o yüzden
`.env.example` ve DAGITIM.md bu hatayı bir daha davet etmeyecek biçimde
yeniden yazıldı (tam URL şablonu, URL kodlaması uyarısı, systemd
`EnvironmentFile`'ın `#` davranışı).

**Doğrulama:** iki servis de `active`; API `127.0.0.1:8002`; `/api/donem`
hem doğrudan hem HTTPS üzerinden 200; ana sayfa 200; **diğer üç site
(rag/loadcast/emlak) etkilenmedi** (üçü de 200). Uçtan uca çözüm: API
kuyruğa yazdı, **işçi ayrı serviste aldı**, `tamamlandı` (ceza 912 —
yereldekiyle aynı).

**Bir güvenlik kontrolü:** günlükte bir tarayıcı botun `/api/.env` denediğini
gördüm (404). `/.env` ise 200 dönüyor — ama gövdesi `index.html`, yani SPA
geri dönüşü; dosyanın kendisi değil. `.env` web kökünün dışında
(`/opt/vardiya/.env`, `0640`). Doğruladım, sızıntı yok; aynı davranış
`loadcast` bloğunda da var.

### Madde 8 — referans donanımda kabul ölçümü

Gerçek kullanım başlamadan, diğer uygulamalar boştayken (%0,2 CPU) alındı.

| Kriter | Eşik | Geliştirme | **Sunucu** |
|---|---|---|---|
| K1 40×28 < 60 sn | < 60 sn | 1,12 sn | **2,73 sn** |
| K2 zorunlu ihlal | 0 | 0 | **0** |
| K3 gece sapması | ≤ 1,0 | 0,61 | **0,61** |
| K4 eksik gösterimi | ≥1 açık | 21 hücre | **28–33 hücre** |
| K5 manuel düzenleme | < 1 sn | 0,038 sn | **0,116 sn** |
| K6 değişen atama | raporlanır | 4 | **4** |

Süreler beklendiği gibi arttı (K1 ~2,4×, K5 ~3×) ama eşiklerin çok altında
(K1 22 kat, K5 9 kat). **Kalite ölçütleri iki ortamda birebir aynı** — K2,
K3, K6 donanıma değil model ve kural tanımlarına bağlı olduğu için beklenen
sonuç bu. Sunucu ortamı paylaşımlı olduğundan süreler, izole bir makinenin
üst sınırı gibi okunmalı (SDD 3.4.1/3.4.2).

Ham çıktı sunucuda saklandı: `/opt/vardiya/olcum/kabul-20260809.json`.
`docs/PERFORMANS_NOTU.md` 2.0'a çıkarıldı — sunucu ölçümü **ikinci sütun**
olarak eklendi, geliştirme makinesi sütunu silinmedi.

**Sapmalar / notlar:**
- Dört sabit sürüm yükseltmesi yukarıda gerekçeleriyle yazılı; `ortools`
  kullanıcı onaylı, diğer üçü aynı gerekçenin (Python 3.14) doğrudan
  sonucu ve hepsi tam test paketiyle doğrulandı.
- `deploy/DAGITIM.md` artık tamamlanmış bir kayıt: her adım gerçekte
  çalıştırılan komutla, doğrulama tablosuyla ve bakım/güncelleme
  yordamıyla birlikte (bölüm 9).

**Kalan / ertelenen:** Yok. Dağıtım ve ölçüm tamamlandı.

**Sıradaki oturumun ilk işi:** Sprint 3 kapanışı — dört dokümanla kodun son
tutarlılık kontrolü ve `sprint-3` etiketi (UYGULAMA_PLANI Gün 15'in kalan
maddeleri). Ekrandaki doğrulamayı kullanıcı yapacak.
