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
