#!/usr/bin/env bash
# Gelistirme ortamini tek komutla ayaga kaldirir (SDD 3.4.1).
# Onkosul: PostgreSQL calisir durumda olmali ve .env dosyasindaki VERITABANI_URL
# bu sunucuyu gostermeli (bkz. .env.example).

set -euo pipefail

KOK_DIZIN="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "== Backend kuruluyor =="
cd "$KOK_DIZIN/backend"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -e ".[dev]"

if [ ! -f ".env" ] && [ -f "$KOK_DIZIN/.env.example" ]; then
    cp "$KOK_DIZIN/.env.example" .env
    echo ".env, .env.example'dan olusturuldu; degerleri kendi ortaminiza gore duzenleyin."
fi

echo "== Veritabani gocleri uygulaniyor =="
alembic upgrade head

# Test takimi AYRI bir veritabaninda kosar (Urun Backlog'u B-20) ve ayni goc
# zincirini izler. Adres .env'deki TEST_VERITABANI_URL'den okunur; yoksa
# testler zaten anlasilir bir hatayla durur (backend/conftest.py).
TEST_URL="$(python - <<'PY'
from app.config import ayarlar
print(ayarlar.test_veritabani_url or "")
PY
)"
if [ -n "$TEST_URL" ]; then
    echo "== Test veritabani gocleri uygulaniyor =="
    VERITABANI_URL="$TEST_URL" alembic upgrade head
else
    echo "UYARI: TEST_VERITABANI_URL tanimli degil; testler calismayacak."
    echo "       Kurulum icin bkz. README, 'Testler ve Lint'."
fi

echo "== Backend testleri calistiriliyor =="
ruff check .
ruff format --check .
python -m pytest -q

echo "== Frontend kuruluyor =="
cd "$KOK_DIZIN/frontend"
npm install
npx tsc --noEmit -p tsconfig.app.json

echo "== Kurulum tamamlandi =="
echo "Backend'i baslatmak icin: cd backend && source .venv/bin/activate && uvicorn app.main:app --reload"
echo "Frontend'i baslatmak icin: cd frontend && npm run dev"
