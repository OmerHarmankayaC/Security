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
