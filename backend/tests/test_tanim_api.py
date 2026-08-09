"""Tanim yonetimi CRUD uc noktalari icin mutlu yol testleri (Sprint 1 Gun 4 kabul kriteri).

Canli bir PostgreSQL gerektirir (bkz. README "Kurulum"); bagilanamiyorsa atlanir.
Personel + yetkinlik + gorev noktasi + talep zincirinin elle (burada API
uzerinden) kurulabildigini dogrular.
"""

import uuid
from datetime import date, time
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from tests.conftest import pg_yoksa_atla, yetkili_istemci


@pytest.fixture
def istemci() -> TestClient:
    pg_yoksa_atla()
    return yetkili_istemci()


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


def test_kullanilmayan_tanim_gercekten_silinir(istemci: TestClient) -> None:
    """Madde 1: hicbir yerde kullanilmamis bir tanim gercekten silinebilir."""
    bina_id = istemci.post("/api/bina", json={"ad": _benzersiz("Bos Bina")}).json()["bina_id"]

    kullanim = istemci.get(f"/api/bina/{bina_id}/kullanim").json()
    assert kullanim == {"kullanimda_mi": False, "toplam": 0, "kalemler": []}

    assert istemci.delete(f"/api/bina/{bina_id}").status_code == 204
    assert all(b["bina_id"] != bina_id for b in istemci.get("/api/bina").json())
    assert istemci.get(f"/api/bina/{bina_id}/kullanim").status_code == 404


def test_kullanimdaki_tanim_silinmez_pasiflestirilir(istemci: TestClient) -> None:
    """Madde 1: kullanimda olan tanim satiri KALIR, yalnizca aktif=False olur.

    Gerekce SDD 4.1: gecmis cizelgeler tanim satirlarina referansla durur.
    """
    bina_id = istemci.post("/api/bina", json={"ad": _benzersiz("Dolu Bina")}).json()["bina_id"]
    nokta_id = istemci.post(
        "/api/nokta", json={"ad": _benzersiz("Nokta"), "bina_id": bina_id}
    ).json()["nokta_id"]

    kullanim = istemci.get(f"/api/bina/{bina_id}/kullanim").json()
    assert kullanim["kullanimda_mi"] is True
    assert kullanim["toplam"] == 1
    assert kullanim["kalemler"] == [{"kayit_turu": "görev noktası", "sayi": 1}]

    assert istemci.delete(f"/api/bina/{bina_id}").status_code == 204

    kalan = istemci.get("/api/bina").json()
    guncel = next(b for b in kalan if b["bina_id"] == bina_id)
    assert guncel["aktif"] is False, "kullanimdaki bina silinmemeli, pasiflesmeli"

    # Noktanin binaya referansi bozulmadi.
    nokta = next(n for n in istemci.get("/api/nokta").json() if n["nokta_id"] == nokta_id)
    assert nokta["bina_id"] == bina_id


def test_kullanim_sayimi_kayit_turu_kiriliminda(istemci: TestClient) -> None:
    """Onay kutusunun metni bu dokumden kurulur (FR-1.1, NFR-5)."""
    yetkinlik_id = istemci.post("/api/yetkinlik", json={"ad": _benzersiz("Yetkinlik")}).json()[
        "yetkinlik_id"
    ]
    istemci.post(
        "/api/nokta", json={"ad": _benzersiz("Nokta"), "onkosul_yetkinlik_id": yetkinlik_id}
    )
    for _ in range(2):
        istemci.post(
            "/api/personel",
            json={
                "ad_soyad": "Test Personel",
                "sicil_no": _benzersiz("KULL"),
                "haftalik_hedef_saat": 40,
                "aktif_baslangic": "2026-01-01",
                "yetkinlik_idleri": [yetkinlik_id],
            },
        )

    kullanim = istemci.get(f"/api/yetkinlik/{yetkinlik_id}/kullanim").json()
    assert kullanim["toplam"] == 3
    assert {k["kayit_turu"]: k["sayi"] for k in kullanim["kalemler"]} == {
        "personel yetkinliği": 2,
        "görev noktası ön koşulu": 1,
    }


def test_pasif_vardiya_tipi_listede_ayirt_edilebilir(istemci: TestClient) -> None:
    """Pasif tanimlar listeden dusmez; arayuz onlari isaretleyip filtreleyebilsin
    diye `aktif` alani yanitta tasinir."""
    vardiya_tipi_id = istemci.post(
        "/api/vardiya-tipi",
        json={"ad": _benzersiz("Pasif"), "baslangic_saati": "08:00:00", "bitis_saati": "16:00:00"},
    ).json()["vardiya_tipi_id"]

    guncel = istemci.put(f"/api/vardiya-tipi/{vardiya_tipi_id}", json={"aktif": False})
    assert guncel.status_code == 200
    assert guncel.json()["aktif"] is False

    listede = next(
        v
        for v in istemci.get("/api/vardiya-tipi").json()
        if v["vardiya_tipi_id"] == vardiya_tipi_id
    )
    assert listede["aktif"] is False


def test_pasif_tanim_yeni_cozume_girmez_mevcut_surumde_gorunur() -> None:
    """Madde 1'in ikinci yarisi: "yeni çözümlerde kullanılmaz, mevcut
    kayıtlarda görünmeye devam eder".

    Cozum/on kontrol yolu baglami `yalniz_aktif=True` ile kurar (pasif tanim
    dusuru); analiz/dogrulama yolu `False` ile kurar, cunku MEVCUT bir surumun
    atamalari pasiflestirmeden onceki tanimlara referans verebilir.
    """
    from app.db import OturumYerel
    from app.models.sonuc import Donem
    from app.models.tanim import VardiyaTipi
    from app.services.baglam_kurucu import baglam_olustur

    pg_yoksa_atla()
    oturum = OturumYerel()
    try:
        donem = Donem(
            baslangic_tarihi=date(2026, 3, 2),
            bitis_tarihi=date(2026, 3, 8),
            tercih_son_tarihi=date(2026, 2, 25),
        )
        pasif = VardiyaTipi(
            ad=_benzersiz("Pasif Vardiya"),
            baslangic_saati=time(8, 0),
            bitis_saati=time(16, 0),
            sure_saat=Decimal(8),
            gece_mi=False,
            aktif=False,
        )
        oturum.add_all([donem, pasif])
        oturum.flush()

        cozum_baglami = baglam_olustur(oturum, donem)
        okuma_baglami = baglam_olustur(oturum, donem, yalniz_aktif=False)

        assert pasif.vardiya_tipi_id not in cozum_baglami.vardiya_tipleri
        assert pasif.vardiya_tipi_id in okuma_baglami.vardiya_tipleri
    finally:
        oturum.rollback()
        oturum.close()


def test_kullanim_bulunamayanda_404(istemci: TestClient) -> None:
    for yol in ("yetkinlik", "bina", "nokta", "vardiya-tipi", "personel"):
        assert istemci.get(f"/api/{yol}/999999/kullanim").status_code == 404, yol


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
