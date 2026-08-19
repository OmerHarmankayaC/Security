"""Yetkilendirme: her uc nokta, yetkisiz roldan gelen DOGRUDAN istegi de
reddeder (SRS FR-10.4; SDD 5.1b).

Bu dosyanin varlik nedeni tek bir cumle: "Arayuzun bir islevi gizlemesi
yetkilendirme sayilmaz." Arayuz testleri butonun gorunmedigini gosterebilir;
burada olculen sey, butonu hic gormeden istegi kendisi kuran birinin de
reddedilmesidir.

Uc nokta LISTESI uygulamanin kendi yonlendirme tablosundan turetilir, elle
yazilmaz. Elle yazilsaydi yeni eklenen bir uc nokta listeye girmedigi icin
sessizce test disi kalirdi - yani tam da korunmasi gereken durumda test
hicbir sey soylemezdi.
"""

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.main import app
from app.models.kimlik import Rol
from tests.conftest import oturumlu_istemci, pg_yoksa_atla

# Kimlik dogrulama gerektirmeyen uc noktalar. Uzun bir liste degil ve uzun
# olmamalidir; her yeni satir bir karardir.
_ACIK_UC_NOKTALAR = {
    ("GET", "/health"),  # servis izleme; veri tasimaz
    ("POST", "/api/giris"),  # giris kapinin kendisidir
}

# Parola borcu varken de acik kalan uc noktalar (FR-10.7): borcun odenmesinin
# ve oturumdan cikilmasinin yolu.
_PAROLA_BORCUNA_ACIK = {
    ("GET", "/api/ben"),
    ("POST", "/api/cikis"),
    ("POST", "/api/parola-degistir"),
}

_CALISAN_ON_EKI = "/api/calisan"
_YONETIM_ON_EKI = "/api/kullanici"


def _uc_noktalar() -> list[tuple[str, str]]:
    cikti: list[tuple[str, str]] = []
    for rota in app.routes:
        if not isinstance(rota, APIRoute):
            continue
        for yontem in sorted(rota.methods - {"HEAD", "OPTIONS"}):
            cikti.append((yontem, rota.path))
    return sorted(set(cikti))


def _ornek_istek(istemci: TestClient, yontem: str, yol: str):
    """Yol parametrelerini doldurup istegi gonderir.

    Deger 0 secilir: hicbir kayda karsilik gelmeyen ama tipe uyan bir
    kimlik. Yetki kapisi kaydin varligindan ONCE calistigi icin, kapinin
    kapali oldugu durumda 404 degil 401/403 donmelidir - testin olctugu de
    tam olarak bu sira.
    """
    somut = yol
    for parca in yol.split("/"):
        if parca.startswith("{") and parca.endswith("}"):
            somut = somut.replace(parca, "0")
    return istemci.request(yontem, somut, json={})


@pytest.fixture(scope="module", autouse=True)
def _pg() -> None:
    pg_yoksa_atla()


# --- Kimlik dogrulama (FR-10.3) ---------------------------------------------


def test_hicbir_uc_nokta_oturumsuz_veri_vermez() -> None:
    """Acik uc noktalar disinda her sey 401 doner."""
    istemci = TestClient(app, base_url="https://testserver")
    kacaklar = []
    for yontem, yol in _uc_noktalar():
        if (yontem, yol) in _ACIK_UC_NOKTALAR:
            continue
        yanit = _ornek_istek(istemci, yontem, yol)
        if yanit.status_code != 401:
            kacaklar.append((yontem, yol, yanit.status_code))
    assert kacaklar == []


def test_acik_uc_noktalar_oturumsuz_calisir() -> None:
    istemci = TestClient(app, base_url="https://testserver")
    assert istemci.get("/health").status_code == 200
    # Giris uc noktasi oturum ISTEMEZ; kimlik bilgisi yanlis oldugu icin
    # 401 doner - kapinin kendisi degil, kimlik dogrulamasi reddediyor.
    assert (
        istemci.post(
            "/api/giris", json={"kullanici_adi": "yok", "parola": "yanlis-parola-uzun"}
        ).status_code
        == 401
    )


# --- Rol ayrimi (FR-10.4) ---------------------------------------------------


def test_calisan_rolu_yonetici_uc_noktalarina_erisemez() -> None:
    """SRS 5.10: calisan rolu tanim, cozum ve yayin islevlerine erisemez."""
    import uuid
    from datetime import date

    from app.db import OturumYerel
    from app.models.tanim import Personel

    oturum = OturumYerel()
    try:
        personel = Personel(
            ad_soyad="Yetki Testi Calisani",
            sicil_no=f"YET-{uuid.uuid4().hex[:8]}",
            haftalik_hedef_saat=40,
            aktif_baslangic=date(2026, 1, 1),
        )
        oturum.add(personel)
        oturum.commit()
        personel_id = personel.personel_id
    finally:
        oturum.close()

    istemci = oturumlu_istemci(Rol.CALISAN, personel_id=personel_id)
    kacaklar = []
    for yontem, yol in _uc_noktalar():
        if (yontem, yol) in _ACIK_UC_NOKTALAR or (yontem, yol) in _PAROLA_BORCUNA_ACIK:
            continue
        if yol.startswith(_CALISAN_ON_EKI):
            continue  # calisanin kendi yuzeyi
        if _ornek_istek(istemci, yontem, yol).status_code != 403:
            kacaklar.append((yontem, yol))
    assert kacaklar == []


def test_yonetici_rolu_hesap_yonetimine_erisemez() -> None:
    """SRS 5.10: yonetici "kullanici hesaplarini yonetemez". Arayuzun
    Kullanicilar ekranini hic gostermemesi bunun yerine gecmez."""
    istemci = oturumlu_istemci(Rol.IDARE)
    kacaklar = []
    for yontem, yol in _uc_noktalar():
        if not yol.startswith(_YONETIM_ON_EKI):
            continue
        if _ornek_istek(istemci, yontem, yol).status_code != 403:
            kacaklar.append((yontem, yol))
    assert kacaklar == []


def test_yonetici_rolu_kendi_islevlerine_erisir() -> None:
    """Kapinin gereginden dar olmadigi da olculur: yonetici, hesap yonetimi
    disindaki her seye girebilmelidir (SRS 5.10)."""
    istemci = oturumlu_istemci(Rol.IDARE)
    for yol in ("/api/personel", "/api/yetkinlik", "/api/donem", "/api/kural"):
        assert istemci.get(yol).status_code == 200, yol


def test_yonetim_rolu_yoneticinin_yetkilerini_de_tasir() -> None:
    """Roller kapsayicidir (SRS 5.10): yonetim, yoneticinin yetkilerini
    icerir. Yalniz hesap yonetimine erisip tanimlara erisememek, dokumanin
    tersini soylerdi."""
    istemci = oturumlu_istemci(Rol.HESAP_YONETICISI)
    assert istemci.get("/api/personel").status_code == 200
    assert istemci.get("/api/kullanici").status_code == 200


# --- Parola borcu (FR-10.7) -------------------------------------------------


def test_parola_borclu_kullanici_yalniz_borcunu_odeyebilir() -> None:
    """Borc odenene kadar DIGER uc noktalar kapali; kalan uclar borcun
    odenmesinin ve cikisin yoludur."""
    from app.db import OturumYerel
    from app.models.kimlik import Kullanici

    istemci = oturumlu_istemci(Rol.HESAP_YONETICISI)
    oturum = OturumYerel()
    try:
        kullanici = oturum.query(Kullanici).one()
        kullanici.parola_degistirmeli = True
        oturum.commit()
    finally:
        oturum.close()

    assert istemci.get("/api/ben").status_code == 200
    assert istemci.get("/api/personel").status_code == 403
    assert istemci.get("/api/kullanici").status_code == 403
