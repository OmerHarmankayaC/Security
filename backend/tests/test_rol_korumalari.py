"""FR-10.12 — hesap yonetiminin koruma kurallari.

UC AYRI KURAL, UC AYRI TEST. Uculu birlikte sinanirsa biri kaldirildiginda
digerlerinin hala gecmesi testi yesil tutar; kurallarin her biri tek basina
sistemi arayuzden onarilamaz hale getirmeye yeter.

  1. Sistem yoneticisi KENDINI kapatamaz/dusuremez  -> kazayi onler
  2. Son etkin sistem yoneticisi dusurulemez        -> iki kisinin birbirini
                                                       kapatmasini onler
  3. Hesap yoneticisi sistem yoneticisine dokunamaz -> yetki tirmanmasini
                                                       onler

Kurtarma yalnizca veritabanina dogrudan erisimle mumkun olacagi icin bu
kurallar "iyi olurdu" degil ZORUNLUdur.
"""

import uuid

import pytest

from app.db import OturumYerel
from app.models.kimlik import Kullanici, Rol
from app.services.kullanici_servisi import (
    HesapYonetmeYetkisiYokError,
    KendiHesabiError,
    KullaniciServisi,
    SistemYoneticisineDokunulamazError,
    SonSistemYoneticisiError,
)
from app.services.parola import ozetle
from tests.conftest import pg_yoksa_atla

PAROLA = "yeterince-uzun-parola"


def _hesap(oturum, rol: Rol, aktif: bool = True) -> Kullanici:  # noqa: ANN001
    kullanici = Kullanici(
        kullanici_adi=f"k-{uuid.uuid4().hex[:10]}",
        parola_ozeti=ozetle(PAROLA),
        rol=rol,
        aktif=aktif,
    )
    oturum.add(kullanici)
    oturum.flush()
    return kullanici


@pytest.fixture
def oturum():  # noqa: ANN201
    pg_yoksa_atla()
    o = OturumYerel()
    try:
        yield o
    finally:
        o.rollback()
        o.close()


def test_sistem_yoneticisi_kendi_rolunu_dusuremez(oturum) -> None:  # noqa: ANN001
    sistem = _hesap(oturum, Rol.SISTEM_YONETICISI)
    servis = KullaniciServisi(oturum)

    with pytest.raises(KendiHesabiError):
        servis.guncelle(sistem.kullanici_id, isteyen=sistem, rol=Rol.IDARE)


def test_sistem_yoneticisi_kendini_devre_disi_birakamaz(oturum) -> None:  # noqa: ANN001
    sistem = _hesap(oturum, Rol.SISTEM_YONETICISI)
    servis = KullaniciServisi(oturum)

    with pytest.raises(KendiHesabiError):
        servis.guncelle(sistem.kullanici_id, isteyen=sistem, aktif=False)


def test_son_etkin_sistem_yoneticisi_korumasi_sayimi_dogru_yapar(oturum) -> None:  # noqa: ANN001
    """Kural DOGRUDAN sinanir, `guncelle` uzerinden degil.

    ULASILABILIRLIK NOTU: mevcut kontrol sirasinda bu hata `guncelle`den
    ateslenemez —
      · aktor hesap yoneticisiyse `SistemYoneticisineDokunulamaz` once doner,
      · aktor sistem yoneticisi ve hedef baskasiysa aktor sayimda kalir,
      · aktor sistem yoneticisi ve hedef kendisiyse `KendiHesabi` once doner.
    Kural yine de DURUR ve durmalidir: ustteki uc korumadan biri ileride
    gevsetildiginde sistemi sifir yetkiliyle birakan yol acilir. Arka durak
    oldugu icin kaldirilmasi degil, ulasilamaz olmasi normaldir.
    """
    servis = KullaniciServisi(oturum)
    tek = _hesap(oturum, Rol.SISTEM_YONETICISI)

    # Tek etkin sistem yoneticisini dusurmek: sayim sifira iner -> yasak.
    with pytest.raises(SonSistemYoneticisiError):
        servis._son_sistem_yoneticisini_koru(tek, Rol.IDARE, True)
    with pytest.raises(SonSistemYoneticisiError):
        servis._son_sistem_yoneticisini_koru(tek, Rol.SISTEM_YONETICISI, False)

    # Ikinci bir etkin sistem yoneticisi varken serbest.
    _hesap(oturum, Rol.SISTEM_YONETICISI)
    servis._son_sistem_yoneticisini_koru(tek, Rol.IDARE, True)


def test_devre_disi_sistem_yoneticisi_sayima_girmez(oturum) -> None:  # noqa: ANN001
    """Sayim ETKIN hesaplari sayar. Devre disi bir sistem yoneticisi sisteme
    giremez; onu "var" saymak, son etkin hesabin dusurulmesine izin verirdi."""
    servis = KullaniciServisi(oturum)
    _hesap(oturum, Rol.SISTEM_YONETICISI, aktif=False)
    etkin = _hesap(oturum, Rol.SISTEM_YONETICISI)

    with pytest.raises(SonSistemYoneticisiError):
        servis._son_sistem_yoneticisini_koru(etkin, Rol.SISTEM_YONETICISI, False)


def test_sistem_yoneticisi_baska_bir_sistem_yoneticisini_dusurebilir(oturum) -> None:  # noqa: ANN001
    """Kural "hic dokunulamaz" degil "sonuncusuna dokunulamaz"dir."""
    birinci = _hesap(oturum, Rol.SISTEM_YONETICISI)
    ikinci = _hesap(oturum, Rol.SISTEM_YONETICISI)
    servis = KullaniciServisi(oturum)

    guncellenen = servis.guncelle(ikinci.kullanici_id, isteyen=birinci, rol=Rol.IDARE)
    assert guncellenen.rol is Rol.IDARE


def test_hesap_yoneticisi_sistem_yoneticisine_dokunamaz(oturum) -> None:  # noqa: ANN001
    sistem = _hesap(oturum, Rol.SISTEM_YONETICISI)
    _hesap(oturum, Rol.SISTEM_YONETICISI)  # sayim kurali devreye girmesin
    hesapci = _hesap(oturum, Rol.HESAP_YONETICISI)
    servis = KullaniciServisi(oturum)

    with pytest.raises(SistemYoneticisineDokunulamazError):
        servis.guncelle(sistem.kullanici_id, isteyen=hesapci, rol=Rol.IDARE)
    with pytest.raises(SistemYoneticisineDokunulamazError):
        servis.parola_sifirla(sistem.kullanici_id, PAROLA, isteyen=hesapci)


def test_hesap_yoneticisi_sistem_yoneticisi_hesabi_acamaz(oturum) -> None:  # noqa: ANN001
    """Rol atamasi da bir dokunustur: hesap yoneticisi kendi ustunde bir
    hesap acabilseydi, yetki tirmanmasi tek adimda yapilirdi."""
    hesapci = _hesap(oturum, Rol.HESAP_YONETICISI)
    servis = KullaniciServisi(oturum)

    with pytest.raises(SistemYoneticisineDokunulamazError):
        servis.olustur(f"y-{uuid.uuid4().hex[:8]}", PAROLA, Rol.SISTEM_YONETICISI, isteyen=hesapci)


def test_idare_hesap_islemlerine_servis_duzeyinde_de_giremez(oturum) -> None:  # noqa: ANN001
    """Uc noktadaki rol kapisi tek katman degildir.

    Kapi yalnizca yonlendiricide olsaydi, sonradan eklenen bir uc nokta
    kapiyi yazmayi unuttugunda idare sessizce hesap yonetebilirdi. SRS
    5.10'un en kritik ayrimi budur ve iki katmanda birden durur.
    """
    idare = _hesap(oturum, Rol.IDARE)
    hedef = _hesap(oturum, Rol.CALISAN if False else Rol.IDARE)
    servis = KullaniciServisi(oturum)

    with pytest.raises(HesapYonetmeYetkisiYokError):
        servis.guncelle(hedef.kullanici_id, isteyen=idare, aktif=False)
    with pytest.raises(HesapYonetmeYetkisiYokError):
        servis.parola_sifirla(hedef.kullanici_id, PAROLA, isteyen=idare)
    with pytest.raises(HesapYonetmeYetkisiYokError):
        servis.olustur(f"x-{uuid.uuid4().hex[:8]}", PAROLA, Rol.IDARE, isteyen=idare)
