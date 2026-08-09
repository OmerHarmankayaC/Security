"""Hesap yonetimi uc noktalari (SRS FR-10.5 - FR-10.7).

Rol kapisi burada degil tests/test_yetkilendirme.py'de olculur; bu dosya
kapidan gecildikten SONRAKI davranisa bakar.
"""

import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.db import OturumYerel
from app.models.kimlik import Kullanici, Rol
from app.models.tanim import Personel
from app.services.oturum_servisi import OturumServisi
from tests.conftest import oturumlu_istemci, pg_yoksa_atla

PAROLA = "yeterince-uzun-parola"


@pytest.fixture
def istemci() -> TestClient:
    pg_yoksa_atla()
    return oturumlu_istemci(Rol.YONETIM)


def _personel(ad: str = "Hesap Testi Personeli") -> int:
    oturum = OturumYerel()
    try:
        personel = Personel(
            ad_soyad=ad,
            sicil_no=f"HES-{uuid.uuid4().hex[:8]}",
            haftalik_hedef_saat=40,
            aktif_baslangic=date(2026, 1, 1),
        )
        oturum.add(personel)
        oturum.commit()
        return personel.personel_id
    finally:
        oturum.close()


def _olustur(istemci: TestClient, ad: str, **fazlasi):
    govde = {"kullanici_adi": ad, "parola": PAROLA, "rol": "yonetici", **fazlasi}
    return istemci.post("/api/kullanici", json=govde)


# --- Olusturma (FR-10.5 - FR-10.7) ------------------------------------------


def test_yeni_hesap_parola_degistirme_borcuyla_dogar(istemci: TestClient) -> None:
    """FR-10.7: yonetimin atadigi parola ilk giriste degistirilmek zorunda."""
    yanit = _olustur(istemci, "yeni-yonetici")
    assert yanit.status_code == 201
    assert yanit.json()["parola_degistirmeli"] is True
    assert yanit.json()["aktif"] is True


def test_calisan_hesabi_personelsiz_acilamaz(istemci: TestClient) -> None:
    """FR-10.6. Sema da ayni kurali tutar; burada olculen, kullanicinin 500
    yerine anlasilir bir 400 gormesi."""
    yanit = _olustur(istemci, "baglantisiz-calisan", rol="calisan")
    assert yanit.status_code == 400


def test_calisan_hesabi_personele_baglanir(istemci: TestClient) -> None:
    personel_id = _personel()
    yanit = _olustur(istemci, "bagli-calisan", rol="calisan", personel_id=personel_id)
    assert yanit.status_code == 201
    assert yanit.json()["personel_id"] == personel_id
    assert yanit.json()["ad_soyad"] == "Hesap Testi Personeli"


def test_bir_personelin_ikinci_hesabi_acilamaz(istemci: TestClient) -> None:
    """SRS bunu ayri bir madde olarak yazmaz; FR-10.6'nin kurdugu
    hesap-personel baglantisinin tek anlamli kalmasi icin gerekli. Iki hesap
    FR-9.1'i ihlal etmezdi ama parola sifirlandiginda hangisinin
    sifirlandigi belirsizlesirdi."""
    personel_id = _personel()
    assert _olustur(istemci, "ilk-hesap", rol="calisan", personel_id=personel_id).status_code == 201
    ikinci = _olustur(istemci, "ikinci-hesap", rol="calisan", personel_id=personel_id)
    assert ikinci.status_code == 400


def test_ayni_kullanici_adi_ikinci_kez_acilamaz(istemci: TestClient) -> None:
    assert _olustur(istemci, "tekrar-eden").status_code == 201
    assert _olustur(istemci, "tekrar-eden").status_code == 400
    # Buyuk harfli yazilis da ayni hesaptir.
    assert _olustur(istemci, "TEKRAR-EDEN").status_code == 400


def test_kullanici_adi_ascii_kumesiyle_sinirli(istemci: TestClient) -> None:
    """Turkce I/i cifti PostgreSQL ve Python'da FARKLI kucultulur; sinir
    olmasaydi hesap acilir ama sahibi giris yapamazdi."""
    for gecersiz in ("çalışan", "ad soyad", "a", "iki@nokta", "İSMAİL"):
        assert _olustur(istemci, gecersiz).status_code == 400, gecersiz


def test_kisa_parola_reddedilir(istemci: TestClient) -> None:
    assert _olustur(istemci, "kisa-parolali", parola="kisa").status_code == 400


# --- Guncelleme (FR-10.5) ---------------------------------------------------


def test_rol_atanabilir(istemci: TestClient) -> None:
    kullanici_id = _olustur(istemci, "rol-degisen").json()["kullanici_id"]
    yanit = istemci.put(f"/api/kullanici/{kullanici_id}", json={"rol": "yonetim"})
    assert yanit.status_code == 200
    assert yanit.json()["rol"] == "yonetim"


def test_calisan_rolune_gecis_personel_baglantisi_ister(istemci: TestClient) -> None:
    kullanici_id = _olustur(istemci, "rol-calisana").json()["kullanici_id"]
    assert istemci.put(f"/api/kullanici/{kullanici_id}", json={"rol": "calisan"}).status_code == 400
    personel_id = _personel()
    assert (
        istemci.put(
            f"/api/kullanici/{kullanici_id}",
            json={"rol": "calisan", "personel_id": personel_id},
        ).status_code
        == 200
    )


def test_hesap_silinmez_devre_disi_birakilir(istemci: TestClient) -> None:
    """FR-10.5. DELETE diye bir uc nokta YOKTUR; kayit durur, `aktif` doner."""
    kullanici_id = _olustur(istemci, "devre-disi-kalan").json()["kullanici_id"]

    assert istemci.delete(f"/api/kullanici/{kullanici_id}").status_code == 405

    yanit = istemci.put(f"/api/kullanici/{kullanici_id}", json={"aktif": False})
    assert yanit.status_code == 200
    assert yanit.json()["aktif"] is False

    oturum = OturumYerel()
    try:
        assert oturum.get(Kullanici, kullanici_id) is not None
    finally:
        oturum.close()


def test_devre_disi_birakma_acik_oturumlari_kapatir(istemci: TestClient) -> None:
    """Oturum tablosunun varlik nedeni (SDD 4.2.1). Yalniz bayragi cevirmek,
    elindeki cerezle calisan birinin oturum suresi dolana kadar icerde
    kalmasi demekti."""
    kullanici_id = _olustur(istemci, "oturumu-kapanan").json()["kullanici_id"]

    oturum = OturumYerel()
    try:
        OturumServisi(oturum).olustur(kullanici_id)
        oturum.commit()
        assert OturumServisi(oturum).kullanicinin_oturum_sayisi(kullanici_id) == 1
    finally:
        oturum.close()

    istemci.put(f"/api/kullanici/{kullanici_id}", json={"aktif": False})

    oturum = OturumYerel()
    try:
        assert OturumServisi(oturum).kullanicinin_oturum_sayisi(kullanici_id) == 0
    finally:
        oturum.close()


def test_yonetim_kendi_hesabini_kapatamaz_ve_rolunu_dusuremez(istemci: TestClient) -> None:
    """Aksi halde sistemde hic yonetim hesabi kalmadigi durum tek tikla
    uretilebilir; oradan cikisin arayuzden yolu yoktur (FR-10.10 geregi
    hesap acan bir uc nokta bulunmaz)."""
    kendi_id = istemci.get("/api/ben").json()
    oturum = OturumYerel()
    try:
        kullanici = (
            oturum.query(Kullanici)
            .filter(Kullanici.kullanici_adi == kendi_id["kullanici_adi"])
            .one()
        )
        id_ = kullanici.kullanici_id
    finally:
        oturum.close()

    assert istemci.put(f"/api/kullanici/{id_}", json={"aktif": False}).status_code == 400
    assert istemci.put(f"/api/kullanici/{id_}", json={"rol": "yonetici"}).status_code == 400
    # Kendi hesabinda baska bir degisiklik yasak degil.
    assert istemci.put(f"/api/kullanici/{id_}", json={"rol": "yonetim"}).status_code == 200


def test_bulunmayan_kullanici_404(istemci: TestClient) -> None:
    assert istemci.put("/api/kullanici/99999999", json={"aktif": False}).status_code == 404


# --- Parola sifirlama (FR-10.5, FR-10.7) ------------------------------------


def test_parola_sifirlama_borc_yukler_ve_oturumlari_kapatir(istemci: TestClient) -> None:
    """Sifirlamanin nedeni cogu zaman hesabin ele gecmis olmasidir; acik
    oturumlar ayakta kalirsa sifirlama hicbir sey cozmezdi."""
    kullanici_id = _olustur(istemci, "sifirlanan").json()["kullanici_id"]

    oturum = OturumYerel()
    try:
        kullanici = oturum.get(Kullanici, kullanici_id)
        assert kullanici is not None
        kullanici.parola_degistirmeli = False
        OturumServisi(oturum).olustur(kullanici_id)
        oturum.commit()
    finally:
        oturum.close()

    yanit = istemci.post(
        f"/api/kullanici/{kullanici_id}/parola-sifirla",
        json={"yeni_parola": "sifirlanmis-uzun-parola"},
    )
    assert yanit.status_code == 200
    assert yanit.json()["parola_degistirmeli"] is True

    oturum = OturumYerel()
    try:
        assert OturumServisi(oturum).kullanicinin_oturum_sayisi(kullanici_id) == 0
    finally:
        oturum.close()


def test_parola_sifirlama_kilidi_de_kaldirir(istemci: TestClient) -> None:
    kullanici_id = _olustur(istemci, "kilidi-acilan").json()["kullanici_id"]
    oturum = OturumYerel()
    try:
        kullanici = oturum.get(Kullanici, kullanici_id)
        assert kullanici is not None
        kullanici.basarisiz_deneme = 4
        oturum.commit()
    finally:
        oturum.close()

    istemci.post(
        f"/api/kullanici/{kullanici_id}/parola-sifirla",
        json={"yeni_parola": "sifirlanmis-uzun-parola"},
    )

    oturum = OturumYerel()
    try:
        kullanici = oturum.get(Kullanici, kullanici_id)
        assert kullanici is not None
        assert kullanici.basarisiz_deneme == 0
        assert kullanici.kilit_bitis is None
    finally:
        oturum.close()


def test_parola_sifirlama_kurali_uygular(istemci: TestClient) -> None:
    kullanici_id = _olustur(istemci, "kural-sifirlama").json()["kullanici_id"]
    yanit = istemci.post(
        f"/api/kullanici/{kullanici_id}/parola-sifirla", json={"yeni_parola": "kisa"}
    )
    assert yanit.status_code == 400


# --- Listeleme --------------------------------------------------------------


def test_listede_parola_ozeti_donmez(istemci: TestClient) -> None:
    _olustur(istemci, "listedeki")
    govde = istemci.get("/api/kullanici").json()
    assert len(govde) >= 1
    for satir in govde:
        assert "parola_ozeti" not in satir
        assert "parola" not in satir
