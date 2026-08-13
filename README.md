# Vardiya Çizelgeleme Karar Destek Aracı

BOTAŞ tesislerinin güvenlik personeli için, kısıt programlama (Google OR-Tools
CP-SAT) tabanlı bir vardiya çizelgeleme karar destek aracı. FastAPI + React +
PostgreSQL üzerine kurulu bir web uygulamasıdır.

Projenin kapsamı, mimarisi ve kural kataloğu için `docs/` altındaki dört
dokümana (Charter, SRS, Backlog, SDD) bakınız.

Geliştirme sürecinin planı iki dosyadadır: yürürlükteki plan
[`docs/turlar/UYGULAMA_PLANI_V2.md`](docs/turlar/UYGULAMA_PLANI_V2.md) (ikinci aşama, turlar
hâlinde), birinci aşamanın kapanmış günlük planı ise
[`docs/turlar/UYGULAMA_PLANI.md`](docs/turlar/UYGULAMA_PLANI.md).
İlerleme kaydı da ikiye ayrılır: yürürlükteki
[`PROGRESS_V2.md`](PROGRESS_V2.md), arşiv [`PROGRESS.md`](PROGRESS.md).

## Gereksinimler

Sürümler için [`VERSIONS.md`](VERSIONS.md) dosyasına bakınız. Özet:

- Python 3.12+
- Node.js 22.x
- PostgreSQL 16 (yerelde çalışır durumda, `.env` bu sunucuyu göstermeli)

## Kurulum

```bash
cp .env.example .env   # gerekirse degerleri duzenleyin
./scripts/kurulum.sh
```

Betik; backend sanal ortamını kurar, veritabanı göçlerini uygular, backend
testlerini/lint kontrollerini çalıştırır ve frontend bağımlılıklarını kurar.

## Geliştirme

Backend:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

`http://localhost:8000/health` 200 dönmelidir.

Çözüm işçisi (**ayrı bir terminalde, API'nin yanı sıra çalışmalı**):

```bash
cd backend
source .venv/bin/activate
python scripts/cozum_iscisi.py
```

Çözüm işi API sürecinde değil, ayrı bir serviste çalışır (SDD 3.4.4); iki
süreç yalnızca veritabanı üzerinden haberleşir. Bu işçi çalışmazsa çözüm
istekleri `kuyrukta` durumunda bekler ve hiçbir çizelge üretilmez.
Geliştirme ile sunucu böylece aynı yolu kullanır.

İlk yönetim hesabı (SRS FR-10.10 — arayüzde hesap açan bir uç nokta
**yoktur**, sistemin hesapsız anında hesap açmanın yolu budur):

```bash
cd backend && source .venv/bin/activate
python scripts/yonetim_hesabi_olustur.py
```

Parola argüman olarak verilemez; betik onu ekrana yazmadan sorar (komut
satırına yazılan parola kabuk geçmişine ve `ps` çıktısına düşerdi). Sonraki
hesaplar arayüzdeki Kullanıcılar ekranından açılır.

**Yerel geliştirmede `.env` içine `OTURUM_CEREZI_SECURE=false` yazın.**
Oturum çerezi üretimde `Secure` niteliği taşır ve tarayıcı onu düz
`http://localhost` adresine geri göndermez; ayar kapatılmazsa giriş hiçbir
hata göstermeden başarısız olur.

Gösterim amaçlı örnek veri (FR-1.14 — SRS 3.3'teki güvenlik personeli
senaryosu). Dönemler **üretildiği güne göre** yerleşir ve çizelgeler
**gerçek çözücüyle** üretilir; veri sabit tarihlere çakılı değildir:

| Dönem | Yeri | Durum | Ne gösterir |
|---|---|---|---|
| Geçen | önceki hafta | yayınlandı | Geçmiş çizelge; bir sonrakinin ısıtma penceresi (TD-5) |
| Bu Hafta | **bugünü içerir** | arşiv + yayınlandı | Dengeli dönem. Çalışan panelinin "Vardiyalarım" ve "sıradaki vardiya"sı; iki sürüm olduğu için "değişen günler" işareti de çalışır (FR-9.4) |
| Sıkışık | gelecek 4 hafta | çözüldü | Kapanamayan kapsama açığı (Backlog B-14). Çelişki **erişilebilirlik** üzerinden kurulur: vardiya şefliği havuzunun beşi izinde ve o noktaya başka kimse giremez (H8) — blok uzunluğundan bağımsız |
| Tatilli | ilk ulusal bayram haftası | sürüm yok | Resmî tatil azaltılmış kadroya düşer (FR-1.10, TD-3); **tercih penceresi açık** olan tek dönem |
| Fazla Çalışma | tatilliden bir hafta sonra | çözüldü | Güvenlik havuzunun üçte biri izinde; kalanların haftalık yükü eşiği (45 sa) aşar ve **kota tüketimi görünür** olur (H10) |
| Kota Sınırı | onu izleyen hafta | çözüldü | Devir bakiyesi yüksek personel. Kotası dolmuş kişi eşiğe kadar çalışmaya **devam eder**, üstüne çıkamaz; ön kontrol bunu uyarı olarak bildirir |

Ayrıca 30 personel (3 sabit vardiyalı, 1 pasifleştirilmiş), iki yıllık
resmî tatil takvimi, dört müsaitlik tipinin tamamı, yarım gün dilimler
(TD-4) ve tercihin üç durumu.

**Kadro talebe göre boyutlandırılmıştır** (SRS 3.3.6): 30 kişide kişi
başına haftalık yük 38,4 saat — fazla çalışma eşiğine yakın ama altında.
Önceki 44 kişilik kadroda yük 26 saate düşüyor, kimse eşiğe yaklaşmıyor ve
H10 hiçbir zaman tetiklenmiyordu; kuralların işlediğini gösteremeyen bir
gösterim verisi, kuralların yazılmamış olmasıyla aynı kapıya çıkar.

```bash
cd backend && source .venv/bin/activate
python scripts/demo_veri_uret.py           # ilk calistirma
python scripts/demo_veri_uret.py --reset   # var olan demo verisini silip yeniden uretir
python scripts/demo_veri_uret.py --reset --cozme   # cizelge uretmeden, yalnizca tanimlar
```

Çözüm birkaç on saniye sürer; yalnızca tanım ekranlarına bakacaksanız
`--cozme` ile atlayabilirsiniz.

## Giriş

Sistemde kayıt ekranı yoktur (FR-10.1); ilk hesap arayüz dışı bir betikle
açılır (FR-10.10). Varsayılan kullanıcı adı **`admin`**, rolü yönetim —
kullanıcı hesaplarını yönetebilen tek rol:

```bash
cd backend && source .venv/bin/activate
python scripts/yonetim_hesabi_olustur.py
```

Parola argüman olarak verilemez; betik onu ekrana yazmadan iki kez sorar
(en az 12 karakter). Sonraki hesaplar arayüzdeki Kullanıcılar ekranından
açılır.

Test takımı bu hesaba dokunmaz: testler ayrı bir veritabanında koşar
(bkz. "Testler ve Lint").

Frontend:

```bash
cd frontend
npm run dev
```

## Testler ve Lint

**Testler AYRI bir veritabanında koşar** (Ürün Backlog'u B-20). Takım,
bağlantı adresinde bir test veritabanı görmezse çalışmayı reddeder —
geliştirme verisini sessizce temizlemek yerine yüksek sesle durur.

İlk kurulumda bir kez:

```bash
createdb vardiya_test
cd backend
VERITABANI_URL=postgresql+psycopg://vardiya:<PAROLA>@localhost:5432/vardiya_test \
  .venv/bin/alembic upgrade head
```

Adresi `backend/.env` dosyasına yazın (`.env.example`'daki satır):

```
TEST_VERITABANI_URL=postgresql+psycopg://vardiya:<PAROLA>@localhost:5432/vardiya_test
```

Veritabanı adı `test` geçmelidir; kilit bunu arar. Şema göçle kurulur,
`create_all` ile değil — test veritabanı da geliştirme veritabanıyla aynı
göç zincirini izler, dolayısıyla göçlerin kendisi de her koşumda dolaylı
olarak sınanır. Yeni bir göç eklendiğinde ikisine de uygulanır.

```bash
cd backend && source .venv/bin/activate
ruff check . && ruff format --check .
python -m pytest -q
```

```bash
cd frontend
npx tsc --noEmit -p tsconfig.app.json
```

## Proje Yapısı

```
backend/    FastAPI uygulaması, SQLAlchemy modelleri, Alembic göçleri
frontend/   Vite + React + TypeScript (strict mode)
docs/       Charter, SRS, Backlog, SDD (kanonik dörtlü)
docs/turlar/ Planlar, tur promptları, devam yönergeleri — kaynak DEĞİL, kayıt
scripts/    Kurulum ve yardımcı betikler
```

## İlerleme Takibi

Oturumlar arası bağlam [`PROGRESS_V2.md`](PROGRESS_V2.md) dosyasında
tutulur; birinci aşamanın günlüğü [`PROGRESS.md`](PROGRESS.md) kapandı ve
yalnızca arşivdir.
