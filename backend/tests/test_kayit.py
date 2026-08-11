"""Giris denemelerinin ve hesap yonetimi islemlerinin kaydi (SRS FR-10.9).

Testlerin yarisi kaydin ne YAZDIGINA, yarisi ne YAZMADIGINA bakar. Ikincisi
en az birincisi kadar onemli: gunlugu okuyabilen herkes oradaki her seyi
gorur, dolayisiyla oraya dusen bir parola ya da belirtec artik sir degildir.

Canli bir PostgreSQL gerektirir; baglanamiyorsa atlanir.
"""

import logging
import uuid

import pytest
from fastapi.testclient import TestClient

from app.db import OturumYerel
from app.kayit import _temizle
from app.main import app
from app.models.kimlik import Kullanici, Rol
from app.services.parola import ozetle
from app.veri_temizligi import HesapKapsami, hesaplari_temizle
from tests.conftest import oturumlu_istemci, pg_yoksa_atla

PAROLA = "kayit-testi-icin-uzun-parola"
KAYITCI = "vardiya.kimlik"


@pytest.fixture
def temiz() -> None:
    pg_yoksa_atla()
    oturum = OturumYerel()
    try:
        hesaplari_temizle(oturum, kapsam=HesapKapsami.HEPSI)
        oturum.commit()
    finally:
        oturum.close()


def _kullanici(kullanici_adi: str, *, aktif: bool = True) -> None:
    oturum = OturumYerel()
    try:
        oturum.add(
            Kullanici(
                kullanici_adi=kullanici_adi,
                parola_ozeti=ozetle(PAROLA),
                rol=Rol.YONETICI,
                aktif=aktif,
            )
        )
        oturum.commit()
    finally:
        oturum.close()


def _istemci() -> TestClient:
    return TestClient(app, base_url="https://testserver")


def _metin(caplog: pytest.LogCaptureFixture) -> str:
    return "\n".join(k.getMessage() for k in caplog.records)


# --- Giris denemeleri (FR-10.9) ---------------------------------------------


def test_basarili_giris_kaydedilir(temiz, caplog: pytest.LogCaptureFixture) -> None:  # noqa: ANN001
    _kullanici("kayit-basarili")
    istemci = _istemci()
    with caplog.at_level(logging.INFO, logger=KAYITCI):
        istemci.post("/api/giris", json={"kullanici_adi": "kayit-basarili", "parola": PAROLA})
    metin = _metin(caplog)
    assert "olay=giris_basarili" in metin
    assert "kullanici=kayit-basarili" in metin
    assert "rol=yonetici" in metin


def test_basarisiz_giris_nedeniyle_birlikte_kaydedilir(
    temiz,  # noqa: ANN001
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Yanit kullanicinin var olup olmadigini ele vermez (SDD 5.1b) ama KAYIT
    ayirir. Fark bilincli: yanitin okuyucusu saldirgan olabilir, gunlugun
    okuyucusu sunucuya girebilen kisidir ve tam da bu ayrimi gormek ister."""
    _kullanici("kayit-basarisiz")
    istemci = _istemci()
    with caplog.at_level(logging.INFO, logger=KAYITCI):
        istemci.post(
            "/api/giris", json={"kullanici_adi": "kayit-basarisiz", "parola": "yanlis-parola-uzun"}
        )
        istemci.post(
            "/api/giris", json={"kullanici_adi": "hic-yok-boyle-biri", "parola": "yanlis-parola"}
        )
    metin = _metin(caplog)
    assert "neden=parola_hatali" in metin
    assert "neden=kullanici_yok" in metin


def test_devre_disi_hesaba_giris_denemesi_kaydedilir(
    temiz,  # noqa: ANN001
    caplog: pytest.LogCaptureFixture,
) -> None:
    _kullanici("kayit-pasif", aktif=False)
    istemci = _istemci()
    with caplog.at_level(logging.INFO, logger=KAYITCI):
        istemci.post("/api/giris", json={"kullanici_adi": "kayit-pasif", "parola": PAROLA})
    assert "neden=hesap_pasif" in _metin(caplog)


def test_cikis_kaydedilir(temiz, caplog: pytest.LogCaptureFixture) -> None:  # noqa: ANN001
    _kullanici("kayit-cikis")
    istemci = _istemci()
    istemci.post("/api/giris", json={"kullanici_adi": "kayit-cikis", "parola": PAROLA})
    with caplog.at_level(logging.INFO, logger=KAYITCI):
        istemci.post("/api/cikis")
    assert "olay=cikis kullanici=kayit-cikis" in _metin(caplog)


# --- Hesap yonetimi (FR-10.9) -----------------------------------------------


def test_hesap_yonetimi_islemleri_yapaniyla_birlikte_kaydedilir(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """ "Kim yapti" olmadan bir hesap yonetimi kaydi yarim kalirdi: neyin
    degistigi bilinir ama sorumlusu bilinmezdi."""
    pg_yoksa_atla()
    istemci = oturumlu_istemci(Rol.YONETIM)
    ad = f"kayit{uuid.uuid4().hex[:8]}"

    with caplog.at_level(logging.INFO, logger=KAYITCI):
        yanit = istemci.post(
            "/api/kullanici",
            json={"kullanici_adi": ad, "parola": PAROLA, "rol": "yonetici"},
        )
        assert yanit.status_code == 201
        kullanici_id = yanit.json()["kullanici_id"]

        istemci.put(f"/api/kullanici/{kullanici_id}", json={"rol": "yonetim"})
        istemci.put(f"/api/kullanici/{kullanici_id}", json={"aktif": False})
        istemci.post(
            f"/api/kullanici/{kullanici_id}/parola-sifirla",
            json={"yeni_parola": "sifirlanmis-uzun-parola"},
        )

    metin = _metin(caplog)
    for beklenen in (
        "olay=hesap_olusturuldu",
        "olay=rol_degistirildi",
        "olay=hesap_devre_disi_birakildi",
        "olay=parola_sifirlandi",
    ):
        assert beklenen in metin, beklenen
    # Her satirda islemi yapan var.
    for satir in metin.splitlines():
        if satir.startswith("olay=hesap") or satir.startswith("olay=rol"):
            assert "yapan=" in satir, satir


# --- Kaydedilmeyenler --------------------------------------------------------


def test_parola_ve_ozeti_hicbir_yola_kaydedilmez(
    temiz,  # noqa: ANN001
    caplog: pytest.LogCaptureFixture,
) -> None:
    _kullanici("kayit-sizinti")
    istemci = _istemci()
    with caplog.at_level(logging.INFO, logger=KAYITCI):
        # Basarili, basarisiz ve parola degistirme yollarinin hepsi.
        istemci.post("/api/giris", json={"kullanici_adi": "kayit-sizinti", "parola": "yanlis-uzun"})
        istemci.post("/api/giris", json={"kullanici_adi": "kayit-sizinti", "parola": PAROLA})
        istemci.post(
            "/api/parola-degistir",
            json={"mevcut_parola": PAROLA, "yeni_parola": "bambaska-uzun-parola"},
        )
    metin = _metin(caplog)
    assert PAROLA not in metin
    assert "bambaska-uzun-parola" not in metin
    assert "$argon2" not in metin
    assert "olay=parola_degistirildi" in metin


def test_oturum_belirteci_kaydedilmez(temiz, caplog: pytest.LogCaptureFixture) -> None:  # noqa: ANN001
    """Gunlugu okuyan biri belirteci bulursa oturumu devralabilirdi."""
    from app.services.oturum_servisi import CEREZ_ADI

    _kullanici("kayit-belirtec")
    istemci = _istemci()
    with caplog.at_level(logging.INFO, logger=KAYITCI):
        istemci.post("/api/giris", json={"kullanici_adi": "kayit-belirtec", "parola": PAROLA})
    belirtec = istemci.cookies[CEREZ_ADI]
    metin = _metin(caplog)
    assert belirtec not in metin
    # Ozeti de yok: kayda deger bir bilgi tasimiyor, riski ise var.
    assert len([p for p in metin.split() if len(p) == 64]) == 0


# --- Kayit enjeksiyonu -------------------------------------------------------


def test_kullanici_adi_gunluge_sahte_satir_yazamaz() -> None:
    """Basarisiz giristeki kullanici adi SALDIRGANIN yazdigi metindir.

    Temizlenmezse icine satir sonu koyup gunluge "olay=giris_basarili ..."
    diye bir satir uydurabilir ve kaydi okuyani yaniltabilirdi.
    """
    kotu = "kurban\nolay=giris_basarili kullanici=yonetim"
    temiz_hali = _temizle(kotu)
    assert "\n" not in temiz_hali
    assert " " not in temiz_hali

    # Cok uzun bir ad gunlugu sisirmesin.
    assert len(_temizle("a" * 500)) < 100
