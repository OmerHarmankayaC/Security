# Vardiya Çizelgeleme Karar Destek Aracı

BOTAŞ tesislerinin güvenlik personeli için, kısıt programlama (Google OR-Tools
CP-SAT) tabanlı bir vardiya çizelgeleme karar destek aracı. FastAPI + React +
PostgreSQL üzerine kurulu bir web uygulamasıdır.

Projenin kapsamı, mimarisi ve kural kataloğu için `docs/` altındaki dört
dokümana (Charter, SRS, Backlog, SDD) ve geliştirme sürecinin gün gün
planlandığı [`UYGULAMA_PLANI.md`](UYGULAMA_PLANI.md) dosyasına bakınız.

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
senaryosu: 44 personel, 6 görev noktası, talep matrisi, 17 kural; "rahat"
ve "sıkışık" iki dönem):

```bash
cd backend && source .venv/bin/activate
python scripts/demo_veri_uret.py           # ilk calistirma
python scripts/demo_veri_uret.py --reset   # var olan demo verisini silip yeniden uretir
```

Frontend:

```bash
cd frontend
npm run dev
```

## Testler ve Lint

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
docs/       Charter, SRS, Backlog, SDD
scripts/    Kurulum ve yardımcı betikler
```

## İlerleme Takibi

Oturumlar arası bağlam [`PROGRESS.md`](PROGRESS.md) dosyasında tutulur.
