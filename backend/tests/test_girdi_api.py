"""Musaitlik/Tercih CRUD uc noktalari icin mutlu yol + hata yolu testleri
(Sprint 3 Ara Is: SRS FR-2.x/FR-3.x, SDD Ek B).

Canli bir PostgreSQL gerektirir; baglanamiyorsa atlanir.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import (
    bos_vardiya_blogu,
    gecici_vardiya_tipi,
    pg_yoksa_atla,
    yetkili_istemci,
)


@pytest.fixture
def istemci() -> TestClient:
    pg_yoksa_atla()
    return yetkili_istemci()


def _benzersiz(on_ek: str) -> str:
    return f"{on_ek}-{uuid.uuid4().hex[:8]}"


def _personel_olustur(istemci: TestClient, on_ek: str) -> int:
    yanit = istemci.post(
        "/api/personel",
        json={
            "ad_soyad": f"Test Personel {on_ek}",
            "sicil_no": _benzersiz(f"GRD-{on_ek}"),
            "haftalik_hedef_saat": 40,
            "aktif_baslangic": "2026-01-01",
        },
    )
    assert yanit.status_code == 201
    return yanit.json()["personel_id"]


def _donem_olustur(istemci: TestClient) -> int:
    yanit = istemci.post(
        "/api/donem",
        json={
            "baslangic_tarihi": "2026-09-07",
            "bitis_tarihi": "2026-09-13",
            "tercih_son_tarihi": "2026-08-31",
        },
    )
    assert yanit.status_code == 201
    return yanit.json()["donem_id"]


def test_musaitlik_olustur_listele_sil(istemci: TestClient) -> None:
    on_ek = _benzersiz("musaitlik")
    personel_id = _personel_olustur(istemci, on_ek)

    yanit = istemci.post(
        "/api/musaitlik",
        json={
            "personel_id": personel_id,
            "baslangic_tarihi": "2026-08-06",
            "bitis_tarihi": "2026-08-08",
            "dilim": "tam_gun",
            "tip": "yillik_izin",
            "not_": "Test kaydi",
        },
    )
    assert yanit.status_code == 201
    govde = yanit.json()
    musaitlik_id = govde["musaitlik_id"]
    assert govde["personel_id"] == personel_id
    assert govde["not_"] == "Test kaydi"

    yanit = istemci.get("/api/musaitlik")
    assert yanit.status_code == 200
    assert any(m["musaitlik_id"] == musaitlik_id for m in yanit.json())

    assert istemci.delete(f"/api/musaitlik/{musaitlik_id}").status_code == 204
    assert istemci.delete(f"/api/musaitlik/{musaitlik_id}").status_code == 404


def test_musaitlik_olustururken_personel_bulunamazsa_hata_doner() -> None:
    """FK ihlali (bilinmeyen personel_id) yakalanmis bir HTTPException degil,
    veritabani kisitidir - bu yuzden TestClient burada sunucu istisnasini
    (500) yeniden firlatmayacak sekilde kuruluyor; asil iddia, istegin
    sessizce 2xx ile basarili sayilmadigidir."""
    pg_yoksa_atla()
    istemci = TestClient(app, raise_server_exceptions=False)
    yanit = istemci.post(
        "/api/musaitlik",
        json={
            "personel_id": 999999999,
            "baslangic_tarihi": "2026-08-06",
            "bitis_tarihi": "2026-08-08",
            "dilim": "tam_gun",
            "tip": "yillik_izin",
        },
    )
    assert yanit.status_code >= 400


def test_tercih_olustur_listele_onayla_reddet(istemci: TestClient) -> None:
    on_ek = _benzersiz("tercih")
    personel_id = _personel_olustur(istemci, on_ek)
    donem_id = _donem_olustur(istemci)

    yanit = istemci.post(
        "/api/tercih",
        json={
            "personel_id": personel_id,
            "donem_id": donem_id,
            "tarih": "2026-09-08",
            "tip": "calismama",
        },
    )
    assert yanit.status_code == 201
    govde = yanit.json()
    tercih_id = govde["tercih_id"]
    assert govde["durum"] == "beklemede"

    yanit = istemci.get("/api/tercih")
    assert yanit.status_code == 200
    assert any(t["tercih_id"] == tercih_id for t in yanit.json())

    yanit = istemci.put(f"/api/tercih/{tercih_id}", json={"durum": "onaylandi"})
    assert yanit.status_code == 200
    assert yanit.json()["durum"] == "onaylandi"

    yanit = istemci.put(f"/api/tercih/{tercih_id}", json={"durum": "reddedildi"})
    assert yanit.status_code == 200
    assert yanit.json()["durum"] == "reddedildi"


def test_tercih_guncellerken_bulunamazsa_404_doner(istemci: TestClient) -> None:
    yanit = istemci.put("/api/tercih/999999999", json={"durum": "onaylandi"})
    assert yanit.status_code == 404


def test_tercih_vardiya_tipi_tercihinde_vardiya_tipi_id_tasir(istemci: TestClient) -> None:
    on_ek = _benzersiz("tercihvt")
    personel_id = _personel_olustur(istemci, on_ek)
    donem_id = _donem_olustur(istemci)

    istek = {"ad": _benzersiz("Gunduz-tercih"), **bos_vardiya_blogu(istemci)}
    with gecici_vardiya_tipi(istemci, istek) as vardiya:
        vardiya_tipi_id = vardiya["vardiya_tipi_id"]
        yanit = istemci.post(
            "/api/tercih",
            json={
                "personel_id": personel_id,
                "donem_id": donem_id,
                "tarih": "2026-09-09",
                "tip": "vardiya_tipi_tercihi",
                "vardiya_tipi_id": vardiya_tipi_id,
            },
        )
        assert yanit.status_code == 201
        assert yanit.json()["vardiya_tipi_id"] == vardiya_tipi_id
