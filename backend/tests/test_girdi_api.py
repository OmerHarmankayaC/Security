"""Musaitlik/Tercih CRUD uc noktalari icin mutlu yol + hata yolu testleri
(Sprint 3 Ara Is: SRS FR-2.x/FR-3.x, SDD Ek B).

Canli bir PostgreSQL gerektirir; baglanamiyorsa atlanir.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import (
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


def test_tercih_olustururken_ayni_gune_ikinci_kez_409_doner(istemci: TestClient) -> None:
    """Final review bulgu 4: `uq_tercih_personel_tarih` (goc c4f1a7d20b93)
    calisan yolunda 409'a cevriliyordu ama bu yonetici ucu (POST /api/tercih)
    dogrudan INSERT deniyordu -- kisit ihlali yakalanmamis bir
    IntegrityError olarak 500 uretirdi. Bu tur onceki davranisi (500)
    DEGISTIRMEDEN once bu test RED olurdu."""
    on_ek = _benzersiz("tercihcak")
    personel_id = _personel_olustur(istemci, on_ek)
    donem_id = _donem_olustur(istemci)
    govde = {
        "personel_id": personel_id,
        "donem_id": donem_id,
        "tarih": "2026-09-10",
        "tip": "calismama",
    }

    ilk = istemci.post("/api/tercih", json=govde)
    assert ilk.status_code == 201

    ikinci = istemci.post("/api/tercih", json=govde)
    assert ikinci.status_code == 409


def test_tercih_guncellerken_bulunamazsa_404_doner(istemci: TestClient) -> None:
    yanit = istemci.put("/api/tercih/999999999", json={"durum": "onaylandi"})
    assert yanit.status_code == 404


def test_tercih_zaman_araligi_tercihinde_araligi_tasir(istemci: TestClient) -> None:
    """SRS FR-3.2: tercih artik bir vardiya TIPI degil bir ZAMAN ARALIGI.

    Eski test `vardiya_tipi_id` alaninin tasindigini olcuyordu; alan blok
    katalogunun bir parcasiydi ve onunla birlikte kalkti (TD-13).
    """
    on_ek = _benzersiz("tercihvt")
    personel_id = _personel_olustur(istemci, on_ek)
    donem_id = _donem_olustur(istemci)

    yanit = istemci.post(
        "/api/tercih",
        json={
            "personel_id": personel_id,
            "donem_id": donem_id,
            "tarih": "2026-09-09",
            "tip": "zaman_araligi_tercihi",
            "tercih_baslangic": "08:00:00",
            "tercih_bitis": "16:00:00",
        },
    )
    assert yanit.status_code == 201
    assert yanit.json()["tercih_baslangic"] == "08:00:00"
    assert yanit.json()["tercih_bitis"] == "16:00:00"


# --- Izin belgesi (FR-2.x eki): yukleme, indirme, silme ---------------------

# Gecerli bir PNG'nin en kucuk hali: 1x1 piksel. Test icerigin ne oldugunu
# degil, YOLUN calistigini olcer; buyuk bir dosya uretmenin karsiligi yok.
_KUCUK_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000a49444154789c6360000002000100fdff03fd000000"
    "0049454e44ae426082"
)


def _izin_olustur(istemci: TestClient, on_ek: str) -> int:
    personel_id = _personel_olustur(istemci, on_ek)
    yanit = istemci.post(
        "/api/musaitlik",
        json={
            "personel_id": personel_id,
            "baslangic_tarihi": "2026-09-01",
            "bitis_tarihi": "2026-09-02",
            "dilim": "tam_gun",
            "tip": "rapor",
            "not_": None,
        },
    )
    assert yanit.status_code == 201
    return yanit.json()["musaitlik_id"]


def test_izin_belgesi_yuklenir_indirilir_silinir(istemci: TestClient) -> None:
    musaitlik_id = _izin_olustur(istemci, _benzersiz("belge"))

    # Belge yokken indirme 404; "belge yok" bir hata degil bir durumdur ama
    # indirilecek bir sey de yoktur.
    assert istemci.get(f"/api/musaitlik/{musaitlik_id}/belge").status_code == 404

    yanit = istemci.post(
        f"/api/musaitlik/{musaitlik_id}/belge",
        files={"dosya": ("rapor.png", _KUCUK_PNG, "image/png")},
    )
    assert yanit.status_code == 201, yanit.text
    assert yanit.json()["dosya_adi"] == "rapor.png"

    inen = istemci.get(f"/api/musaitlik/{musaitlik_id}/belge")
    assert inen.status_code == 200
    # ICERIK BIREBIR DONMELI: bozulmus bir belge, hic olmayandan kotudur.
    assert inen.content == _KUCUK_PNG
    assert inen.headers["content-type"] == "image/png"
    assert "rapor.png" in inen.headers.get("content-disposition", "")

    # Listede belgenin VARLIGI gorunur: arayuz dugmeyi buna gore cizer ve
    # her satir icin ayrica indirme denemesi yapmaz.
    kayit = next(
        m for m in istemci.get("/api/musaitlik").json() if m["musaitlik_id"] == musaitlik_id
    )
    assert kayit["belge_var"] is True

    assert istemci.delete(f"/api/musaitlik/{musaitlik_id}/belge").status_code == 204
    assert istemci.get(f"/api/musaitlik/{musaitlik_id}/belge").status_code == 404


def test_izin_belgesi_kabul_edilmeyen_tipi_reddeder(istemci: TestClient) -> None:
    """Yalniz goruntu ve PDF kabul edilir.

    Kabul edilen tip listesi olmadan, calisan panelinden yuklenen bir dosya
    sunucuda saklanip baska bir kullaniciya AYNI icerik tipiyle geri
    sunulurdu; tarayicida calisabilecek bir tip (html, svg) bu yolla
    depolanmis bir saldiri yuzeyine donusur.
    """
    musaitlik_id = _izin_olustur(istemci, _benzersiz("belge-tip"))

    yanit = istemci.post(
        f"/api/musaitlik/{musaitlik_id}/belge",
        files={"dosya": ("kotu.html", b"<script>alert(1)</script>", "text/html")},
    )
    assert yanit.status_code == 415


def test_izin_belgesi_ikinci_yukleme_oncekinin_yerine_gecer(istemci: TestClient) -> None:
    """Bir izin kaydinin EN FAZLA BIR belgesi olur (tablo kisiti).

    Ikinci yukleme hata vermek yerine ustune yazar: kullanici yanlis dosyayi
    sectiginde once silmek zorunda kalmasi icin bir sebep yok.
    """
    musaitlik_id = _izin_olustur(istemci, _benzersiz("belge-ust"))
    istemci.post(
        f"/api/musaitlik/{musaitlik_id}/belge",
        files={"dosya": ("ilk.png", _KUCUK_PNG, "image/png")},
    )
    yanit = istemci.post(
        f"/api/musaitlik/{musaitlik_id}/belge",
        files={"dosya": ("ikinci.png", _KUCUK_PNG, "image/png")},
    )
    assert yanit.status_code == 201
    assert yanit.json()["dosya_adi"] == "ikinci.png"
    assert istemci.get(f"/api/musaitlik/{musaitlik_id}/belge").status_code == 200


def test_izin_belgesi_olmayan_izne_yuklenemez(istemci: TestClient) -> None:
    yanit = istemci.post(
        "/api/musaitlik/99999999/belge",
        files={"dosya": ("rapor.png", _KUCUK_PNG, "image/png")},
    )
    assert yanit.status_code == 404
