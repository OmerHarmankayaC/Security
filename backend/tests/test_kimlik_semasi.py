"""kullanici ve oturum tablolarinin gercek PostgreSQL'e karsi dogrulanmasi
(SDD 4.2.1; SRS FR-10.2, FR-10.5, FR-10.6).

Yerelde calisan bir PostgreSQL ve `alembic upgrade head` gerektirir.
"""

from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import OturumYerel
from app.models import Kullanici, OturumKaydi, Personel, Rol
from app.services.parola import ozetle
from tests.conftest import pg_yoksa_atla

_PAROLA = "cok-uzun-bir-parola"


@pytest.fixture
def oturum() -> Session:
    pg_yoksa_atla()
    oturum = OturumYerel()
    try:
        yield oturum
    finally:
        oturum.rollback()
        oturum.close()


def _personel(oturum: Session, sicil: str) -> Personel:
    personel = Personel(
        ad_soyad=f"Kimlik Test {sicil}",
        sicil_no=sicil,
        haftalik_hedef_saat=40,
        aktif_baslangic=date(2026, 1, 1),
    )
    oturum.add(personel)
    oturum.flush()
    return personel


def test_calisan_hesabi_personelsiz_acilamaz(oturum: Session) -> None:
    """FR-10.6. Kisit veritabaninda: elle SQL'den ya da bir betikten acilan
    hesap da bu kapiya carpar, yalniz servis katmanindan gecen degil."""
    oturum.add(
        Kullanici(
            kullanici_adi="kimlik-baglantisiz",
            parola_ozeti=ozetle(_PAROLA),
            rol=Rol.CALISAN,
            personel_id=None,
        )
    )
    with pytest.raises(IntegrityError):
        oturum.flush()


def test_calisan_hesabi_personele_bagliyken_acilir(oturum: Session) -> None:
    personel = _personel(oturum, "KMLK-0001")
    oturum.add(
        Kullanici(
            kullanici_adi="kimlik-bagli",
            parola_ozeti=ozetle(_PAROLA),
            rol=Rol.CALISAN,
            personel_id=personel.personel_id,
        )
    )
    oturum.flush()


def test_yonetim_hesabi_personelsiz_acilabilir(oturum: Session) -> None:
    """Kisit YALNIZ calisan rolunu baglar; yonetici ve yonetim rollerinin
    personel kaydi olmayabilir (SDD 4.2.1)."""
    oturum.add(
        Kullanici(
            kullanici_adi="kimlik-yonetim",
            parola_ozeti=ozetle(_PAROLA),
            rol=Rol.HESAP_YONETICISI,
        )
    )
    oturum.flush()


def test_kullanici_adi_benzersizdir(oturum: Session) -> None:
    for _ in range(2):
        oturum.add(
            Kullanici(
                kullanici_adi="kimlik-tekrar",
                parola_ozeti=ozetle(_PAROLA),
                rol=Rol.IDARE,
            )
        )
    with pytest.raises(IntegrityError):
        oturum.flush()


def test_varsayilanlar_hesabi_acik_ve_kilitsiz_dogurur(oturum: Session) -> None:
    """Sunucu varsayilanlari: yeni hesap aktif, sayaci sifir, parola
    degistirme zorunlulugu YOK. Zorunluluk, hesabi acan yolun (yonetim
    ekrani ve kurulum betigi) bilincli olarak yazdigi bir degerdir - burada
    varsayilan olsaydi, kendi parolasini degistiren kullanici da yeniden
    degistirmeye zorlanirdi."""
    kullanici = Kullanici(
        kullanici_adi="kimlik-varsayilan",
        parola_ozeti=ozetle(_PAROLA),
        rol=Rol.IDARE,
    )
    oturum.add(kullanici)
    oturum.flush()
    oturum.refresh(kullanici)

    assert kullanici.aktif is True
    assert kullanici.parola_degistirmeli is False
    assert kullanici.basarisiz_deneme == 0
    assert kullanici.kilit_bitis is None


def test_oturum_kayit_edilir_ve_kullaniciya_baglidir(oturum: Session) -> None:
    kullanici = Kullanici(
        kullanici_adi="kimlik-oturumlu",
        parola_ozeti=ozetle(_PAROLA),
        rol=Rol.IDARE,
    )
    oturum.add(kullanici)
    oturum.flush()

    simdi = datetime.now(UTC)
    oturum.add(
        OturumKaydi(
            oturum_id="a" * 64,
            kullanici_id=kullanici.kullanici_id,
            olusturma=simdi,
            son_erisim=simdi,
            gecerlilik_bitis=simdi + timedelta(hours=12),
        )
    )
    oturum.flush()

    kayit = oturum.execute(
        select(OturumKaydi).where(OturumKaydi.kullanici_id == kullanici.kullanici_id)
    ).scalar_one()
    # Zaman damgalari saat dilimi TASIR (SDD 4.2, `timestamptz` karari):
    # dilimsiz okunursa hareketsizlik ve mutlak bitis hesabi sunucunun yerel
    # dilimine gore kayar.
    assert kayit.gecerlilik_bitis.tzinfo is not None
    assert kayit.gecerlilik_bitis > kayit.son_erisim
