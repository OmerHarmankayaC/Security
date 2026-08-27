"""Ortam beyaninin sozlesmesi (Demo Senaryosu 10).

Iki iddia var ve ikisi de serit icin hayati:

  1. Uc nokta YETKI ISTEMEZ. Serit giris ekraninda gorunmelidir; yetki
     istemesi, gosterim ortamina ilk bakan kisiye "bu veri gercek degil"
     demenin tek anini kacirirdi.
  2. Varsayilan KAPALIDIR. Ayari tasimayan her ortam - ozellikle gercek bir
     kurulum - kendini gosterim ortami ilan etmez.
"""

from fastapi.testclient import TestClient

from app.config import ayarlar
from app.main import app

istemci = TestClient(app)


def test_ortam_yetki_istemez() -> None:
    yanit = istemci.get("/api/ortam")

    assert yanit.status_code == 200
    assert "demo_kipi" in yanit.json()


def test_varsayilan_kapalidir() -> None:
    assert ayarlar.demo_kipi is False
    assert istemci.get("/api/ortam").json()["demo_kipi"] is False


def test_ayar_acikken_serit_beyan_edilir(monkeypatch) -> None:  # noqa: ANN001 - pytest fixture
    monkeypatch.setattr(ayarlar, "demo_kipi", True)

    assert istemci.get("/api/ortam").json()["demo_kipi"] is True
