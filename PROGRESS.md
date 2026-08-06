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
