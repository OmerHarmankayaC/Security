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
