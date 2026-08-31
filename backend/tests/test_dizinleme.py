"""Arama motoru dizinlemesine kapali olma sozlesmesi.

Iki iddia:

  1. HER yanit `X-Robots-Tag: noindex` tasir - basarili da, hatali da.
     Hata sayfalarini disarida birakmak, dizine giren tek seyin uygulamanin
     hata mesajlari olmasi demekti.
  2. Baslik demo kipine BAGLI DEGILDIR. Kosula baglansaydi, ayarin kapali
     oldugu bir kurulumda uc noktalar dizine acilirdi ve bu bir ic kullanim
     araci icin de istenmez.
"""

import pytest
from fastapi.testclient import TestClient

from app.config import ayarlar
from app.main import app

istemci = TestClient(app)

_BEKLENEN = "noindex, nofollow"


@pytest.mark.parametrize(
    "yol",
    [
        "/health",
        "/api/ortam",
        "/api/demo/kimlik",  # kapali kipte 404 — o da baslik tasimali
        "/api/personel",  # oturumsuz 401
        "/api/boyle-bir-yol-yok",  # 404
    ],
)
def test_her_yanit_noindex_tasir(yol: str) -> None:
    yanit = istemci.get(yol)

    assert (
        yanit.headers.get("X-Robots-Tag") == _BEKLENEN
    ), f"{yol} ({yanit.status_code}) dizinlemeye acik dondu"


def test_baslik_demo_kipine_bagli_degil(monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.setattr(ayarlar, "demo_kipi", True)
    assert istemci.get("/health").headers.get("X-Robots-Tag") == _BEKLENEN

    monkeypatch.setattr(ayarlar, "demo_kipi", False)
    assert istemci.get("/health").headers.get("X-Robots-Tag") == _BEKLENEN


def test_yazma_reddi_de_baslik_tasir(monkeypatch) -> None:  # noqa: ANN001
    """Salt okunur kapisi yaniti ARA KATMANDA uretiyor; ikisinin sirasi
    yanlis olsaydi o yanit basliksiz cikardi."""
    monkeypatch.setattr(ayarlar, "demo_kipi", True)

    yanit = istemci.post("/api/personel", json={})

    assert yanit.status_code == 403
    assert yanit.headers.get("X-Robots-Tag") == _BEKLENEN
