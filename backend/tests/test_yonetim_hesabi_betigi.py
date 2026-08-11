"""Ilk yonetim hesabi betigi (SRS FR-10.10).

Betigin varlik nedeni, sistemin hesapsiz aninda kendi kendine hesap acan bir
UC NOKTA bulunmamasidir; testlerin bir kismi tam da bunu -- olmayan seyi --
sabitler.

Canli bir PostgreSQL gerektirir; baglanamiyorsa atlanir.
"""

import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.routing import APIRoute  # noqa: E402

from app.db import OturumYerel  # noqa: E402
from app.main import app  # noqa: E402
from app.models.kimlik import Kullanici, Rol  # noqa: E402
from app.services.parola import ASGARI_UZUNLUK, dogrula  # noqa: E402
from app.veri_temizligi import HesapKapsami, hesaplari_temizle
from scripts.yonetim_hesabi_olustur import (  # noqa: E402
    hesap_ac,
    main,
    yonetim_hesabi_var_mi,
)
from tests.conftest import pg_yoksa_atla

PAROLA = "kurulum-icin-uzun-parola"


@pytest.fixture
def oturum():  # noqa: ANN201 - Session
    pg_yoksa_atla()
    oturum = OturumYerel()
    try:
        hesaplari_temizle(oturum, kapsam=HesapKapsami.HEPSI)
        oturum.commit()
        yield oturum
    finally:
        oturum.rollback()
        oturum.close()


def _ad() -> str:
    return f"kurulum{uuid.uuid4().hex[:8]}"


# --- Parola komut satirindan ALINMAZ ----------------------------------------


def test_betik_parolayi_arguman_olarak_kabul_etmez() -> None:
    """Komut satirina yazilan parola kabuk gecmisine ve `ps` ciktisina duser.

    Test, ayristiricinin secenek listesini okuyarak bakar: bir gun
    "kolaylik olsun" diye eklenen --parola secenegi burada yakalanir.
    """
    import argparse
    from unittest.mock import patch

    yakalanan: list[argparse.ArgumentParser] = []

    def _yakala(self, *a, **k):  # noqa: ANN001, ANN202
        # Ayristiriciyi kurulmus hâliyle yakalar ve main'i orada durdurur;
        # betigin geri kalani (etkilesimli sorular, veritabani) calismaz.
        yakalanan.append(self)
        raise SystemExit(0)

    with patch.object(argparse.ArgumentParser, "parse_args", _yakala), pytest.raises(SystemExit):
        main()

    secenekler = {dize for eylem in yakalanan[0]._actions for dize in eylem.option_strings}
    for yasak in ("--parola", "--password", "-p"):
        assert yasak not in secenekler


# --- Hesap acma -------------------------------------------------------------


def test_hesap_yonetim_rolunde_acilir_ve_parola_ozetlenir(oturum) -> None:  # noqa: ANN001
    ad = _ad()
    kullanici = hesap_ac(oturum, ad, PAROLA)
    oturum.flush()

    assert kullanici.rol is Rol.YONETIM
    assert kullanici.aktif is True
    # Parola ozetlenmis: satirda duz metin YOK, ama dogrulama caliyor.
    assert PAROLA not in kullanici.parola_ozeti
    assert dogrula(kullanici.parola_ozeti, PAROLA)


def test_parolayi_yazan_kisi_hesabin_sahibiyse_borc_yuklenmez(oturum) -> None:  # noqa: ANN001
    """Betigi calistiran kisi parolayi kendi seciyor; ilk giriste yeniden
    sectirmenin karsiligi yok. Kurulumu baskasi yapiyorsa bayrakla borc
    korunur."""
    kendi = hesap_ac(oturum, _ad(), PAROLA)
    baskasi = hesap_ac(oturum, _ad(), PAROLA, ilk_giriste_degistir=True)
    oturum.flush()

    assert kendi.parola_degistirmeli is False
    assert baskasi.parola_degistirmeli is True


def test_kurallar_arayuzle_ayni_yerden_gelir(oturum) -> None:  # noqa: ANN001
    """Betikten acilan hesap, arayuzden acilanla AYNI kurallara tabi.
    Ayrisirlarsa bu ancak bir kullanici giris yapamadiginda fark edilirdi."""
    with pytest.raises(ValueError):
        hesap_ac(oturum, _ad(), "a" * (ASGARI_UZUNLUK - 1))
    oturum.rollback()

    with pytest.raises(ValueError):
        hesap_ac(oturum, "GEÇERSİZ AD", PAROLA)


def test_ikinci_calistirmada_var_olan_yonetim_hesabi_gorulur(oturum) -> None:  # noqa: ANN001
    assert yonetim_hesabi_var_mi(oturum) is False
    hesap_ac(oturum, _ad(), PAROLA)
    oturum.commit()
    assert yonetim_hesabi_var_mi(oturum) is True


def test_hepsi_devre_disi_birakilmis_sistemde_betik_yeniden_calisabilir(oturum) -> None:  # noqa: ANN001
    """Pasif hesaplar sayilmaz: butun hesaplarin kapali oldugu bir sistemde
    kimse giremez ve kurtulmanin tek yolu bu betiktir."""
    kullanici = hesap_ac(oturum, _ad(), PAROLA)
    oturum.commit()
    kullanici.aktif = False
    oturum.commit()
    assert yonetim_hesabi_var_mi(oturum) is False


# --- Arayuzde karsiligi olmamali (FR-10.10) ---------------------------------


def test_hesap_acan_uc_nokta_yalniz_yonetim_rolununkidir() -> None:
    """Hesap olusturan tek uc nokta /api/kullanici POST'udur ve o da yonetim
    rolune kapalidir (bkz. tests/test_yetkilendirme.py). "Hic hesap yoksa
    acilabilir" gibi kimlik dogrulamasiz bir kayit yolu BULUNMAMALIDIR;
    boyle bir uc nokta eklenirse bu test kirilir."""
    postlar = {
        rota.path for rota in app.routes if isinstance(rota, APIRoute) and "POST" in rota.methods
    }
    # Kayit benzeri hicbir yol YOK.
    assert [y for y in postlar if any(p in y for p in ("kayit", "register", "signup"))] == []
    # Hesap acan tek yol yonetim rolununki.
    assert "/api/kullanici" in postlar


def test_kullanicilar_arasinda_kurulum_hesabi_ayricalikli_degil(oturum) -> None:  # noqa: ANN001
    """Betikten acilan hesap, sonradan acilanlardan farkli bir alan
    tasimaz - "kurulum hesabi" diye silinemez/degistirilemez bir tur
    yoktur. Olsaydi, yetkilendirme mantiginin her yerinde ikinci bir
    durum daha olurdu."""
    ad = _ad()
    hesap_ac(oturum, ad, PAROLA)
    oturum.flush()
    kayit = oturum.query(Kullanici).filter(Kullanici.kullanici_adi == ad).one()
    sutunlar = {s.name for s in Kullanici.__table__.columns}
    assert "kurulum" not in " ".join(sutunlar)
    assert kayit.rol is Rol.YONETIM


def test_varsayilan_kullanici_adi_admin() -> None:
    """Sistem yoneticisinin varsayilan adi `admin`.

    Sabit ve Ingilizce: hesabi acan kisi ile sonradan giren kisi cogu zaman
    ayni degil ve "hangi adi vermistim" sorusu, parolasi bilinen ama adi
    hatirlanmayan bir hesap uretiyordu. Ad bir sir degildir - giris ekrani
    kullanici adinin varligini zaten ele vermez (SDD 5.1b).
    """
    from scripts.yonetim_hesabi_olustur import VARSAYILAN_KULLANICI_ADI

    assert VARSAYILAN_KULLANICI_ADI == "admin"
    # Ad, hesap acma yolundaki desene uymali; uymasaydi betik kendi
    # varsayilaniyla calismazdi.
    from app.services.kullanici_servisi import KullaniciServisi

    assert KullaniciServisi._adi_dogrula(VARSAYILAN_KULLANICI_ADI) == "admin"
