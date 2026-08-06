"""Tanim yonetimi CRUD uc noktalari icin mutlu yol testleri (Sprint 1 Gun 4 kabul kriteri).

Canli bir PostgreSQL gerektirir (bkz. README "Kurulum"); bagilanamiyorsa atlanir.
Personel + yetkinlik + gorev noktasi + talep zincirinin elle (burada API
uzerinden) kurulabildigini dogrular.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import pg_yoksa_atla


@pytest.fixture
def istemci() -> TestClient:
    pg_yoksa_atla()
    return TestClient(app)


def _benzersiz(on_ek: str) -> str:
    """Testler yeniden calistirildiginda benzersizlik kisitlarina takilmamak icin."""
    return f"{on_ek}-{uuid.uuid4().hex[:8]}"


def test_yetkinlik_olustur_listele_guncelle_sil(istemci: TestClient) -> None:
    yanit = istemci.post("/api/yetkinlik", json={"ad": _benzersiz("Test Yetkinligi FR12")})
    assert yanit.status_code == 201
    yetkinlik_id = yanit.json()["yetkinlik_id"]

    yanit = istemci.get("/api/yetkinlik")
    assert yanit.status_code == 200
    assert any(y["yetkinlik_id"] == yetkinlik_id for y in yanit.json())

    yanit = istemci.put(f"/api/yetkinlik/{yetkinlik_id}", json={"aciklama": "guncellendi"})
    assert yanit.status_code == 200
    assert yanit.json()["aciklama"] == "guncellendi"

    yanit = istemci.delete(f"/api/yetkinlik/{yetkinlik_id}")
    assert yanit.status_code == 204

    yanit = istemci.put(f"/api/yetkinlik/{yetkinlik_id}", json={"aciklama": "x"})
    assert yanit.status_code == 404


def test_bina_crud(istemci: TestClient) -> None:
    yanit = istemci.post("/api/bina", json={"ad": "Test Bina FR15"})
    assert yanit.status_code == 201
    bina_id = yanit.json()["bina_id"]

    yanit = istemci.put(f"/api/bina/{bina_id}", json={"ad": "Test Bina FR15 Guncel"})
    assert yanit.status_code == 200
    assert yanit.json()["ad"] == "Test Bina FR15 Guncel"

    assert istemci.delete(f"/api/bina/{bina_id}").status_code == 204


def test_vardiya_tipi_olustururken_gece_mi_onerilir(istemci: TestClient) -> None:
    yanit = istemci.post(
        "/api/vardiya-tipi",
        json={"ad": "Test Gece FR14", "baslangic_saati": "00:00:00", "bitis_saati": "08:00:00"},
    )
    assert yanit.status_code == 201
    govde = yanit.json()
    assert govde["gece_mi"] is True
    assert float(govde["sure_saat"]) == 8.0


def test_vardiya_tipi_gece_mi_elle_belirtilebilir(istemci: TestClient) -> None:
    yanit = istemci.post(
        "/api/vardiya-tipi",
        json={
            "ad": "Test Aksam FR14",
            "baslangic_saati": "16:00:00",
            "bitis_saati": "00:00:00",
            "gece_mi": False,
        },
    )
    assert yanit.status_code == 201
    assert yanit.json()["gece_mi"] is False


def test_personel_yetkinlik_nokta_talep_zinciri(istemci: TestClient) -> None:
    """Gun 4 kabul kriteri: personel+yetkinlik+gorev noktasi+talep zinciri API'den kurulur."""
    yetkinlik_yaniti = istemci.post(
        "/api/yetkinlik", json={"ad": _benzersiz("Guvenlik Gorevi FR-zincir")}
    )
    yetkinlik_id = yetkinlik_yaniti.json()["yetkinlik_id"]
    bina_id = istemci.post("/api/bina", json={"ad": "Bina A FR-zincir"}).json()["bina_id"]
    nokta_id = istemci.post(
        "/api/nokta",
        json={"ad": "Kapi FR-zincir", "bina_id": bina_id, "onkosul_yetkinlik_id": yetkinlik_id},
    ).json()["nokta_id"]
    vardiya_tipi_id = istemci.post(
        "/api/vardiya-tipi",
        json={"ad": "Gunduz FR-zincir", "baslangic_saati": "08:00:00", "bitis_saati": "16:00:00"},
    ).json()["vardiya_tipi_id"]

    yanit = istemci.post(
        "/api/personel",
        json={
            "ad_soyad": "Test Personel FR-zincir",
            "sicil_no": _benzersiz("ZNCR"),
            "haftalik_hedef_saat": 40,
            "aktif_baslangic": "2026-01-01",
            "yetkinlik_idleri": [yetkinlik_id],
        },
    )
    assert yanit.status_code == 201
    govde = yanit.json()
    personel_id = govde["personel_id"]
    assert govde["yetkinlik_idleri"] == [yetkinlik_id]

    yanit = istemci.put(
        "/api/talep",
        json={
            "nokta_id": nokta_id,
            "vardiya_tipi_id": vardiya_tipi_id,
            "gun_tipi": "hafta_ici",
            "gereken_sayi": 3,
        },
    )
    assert yanit.status_code == 200
    govde = yanit.json()
    assert any(h["nokta_id"] == nokta_id and h["gereken_sayi"] == 3 for h in govde["hucreler"])
    assert govde["yuk_gostergesi"]["haftalik_kisi_vardiya"] >= 15  # 3 kisi x 5 gun

    yanit = istemci.get("/api/talep")
    assert yanit.status_code == 200
    assert any(h["nokta_id"] == nokta_id for h in yanit.json()["hucreler"])

    # DELETE personel icin pasiflestirmedir; kayit silinmez, aktif_bitis dolar.
    assert istemci.delete(f"/api/personel/{personel_id}").status_code == 204
    kalan = istemci.get("/api/personel").json()
    guncel = next(p for p in kalan if p["personel_id"] == personel_id)
    assert guncel["aktif_bitis"] is not None

    # DELETE gorev noktasi icin de pasiflestirmedir (aktif=False).
    assert istemci.delete(f"/api/nokta/{nokta_id}").status_code == 204
    kalan_noktalar = istemci.get("/api/nokta").json()
    guncel_nokta = next(n for n in kalan_noktalar if n["nokta_id"] == nokta_id)
    assert guncel_nokta["aktif"] is False


def test_personel_bulunamayanda_404(istemci: TestClient) -> None:
    assert istemci.put("/api/personel/999999", json={"ad_soyad": "yok"}).status_code == 404
    assert istemci.delete("/api/personel/999999").status_code == 404


def test_kural_bulunamayanda_404(istemci: TestClient) -> None:
    yanit = istemci.put("/api/kural/TANIMSIZ-KIMLIK", json={"agirlik": 5})
    assert yanit.status_code == 404


def test_kural_guncelle(istemci: TestClient) -> None:
    from app.db import OturumYerel
    from app.models.kural import Kural, KuralTipi

    kimlik = _benzersiz("TEST-KURAL-FR11")
    oturum = OturumYerel()
    try:
        oturum.add(Kural(kimlik=kimlik, tip=KuralTipi.ESNEK, parametreler={}, agirlik=1))
        oturum.commit()
    finally:
        oturum.close()

    yanit = istemci.put(f"/api/kural/{kimlik}", json={"agirlik": 7, "aktif": False})
    assert yanit.status_code == 200
    govde = yanit.json()
    assert govde["agirlik"] == 7
    assert govde["aktif"] is False
