"""Semanin gercek bir PostgreSQL'e karsi INSERT/SELECT ile dogrulanmasi (SDD 4.2).

Yerelde calisan bir PostgreSQL sunucusu ve gocleri uygulanmis bir veritabani
gerektirir (bkz. README "Kurulum"). `alembic upgrade head` onceden calismis olmalidir.
"""

from datetime import date, time

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import OturumYerel
from app.models import (
    Atama,
    AtamaKaynagi,
    CizelgeSurumu,
    Donem,
    GorevNoktasi,
    Personel,
    PersonelYetkinlik,
    VardiyaTipi,
    Yetkinlik,
)
from tests.conftest import pg_yoksa_atla


@pytest.fixture
def oturum() -> Session:
    pg_yoksa_atla()
    oturum = OturumYerel()
    try:
        yield oturum
    finally:
        oturum.rollback()
        oturum.close()


def test_personel_yetkinlik_ekle_ve_oku(oturum: Session) -> None:
    yetkinlik = Yetkinlik(ad="Test Yetkinligi")
    personel = Personel(
        ad_soyad="Test Personel",
        sicil_no="TST-0001",
        haftalik_hedef_saat=40,
        aktif_baslangic=date(2026, 1, 1),
    )
    oturum.add_all([yetkinlik, personel])
    oturum.flush()

    oturum.add(
        PersonelYetkinlik(personel_id=personel.personel_id, yetkinlik_id=yetkinlik.yetkinlik_id)
    )
    oturum.flush()

    sonuc = oturum.execute(
        select(PersonelYetkinlik).where(PersonelYetkinlik.personel_id == personel.personel_id)
    ).scalar_one()
    assert sonuc.yetkinlik_id == yetkinlik.yetkinlik_id


def test_atama_benzersizlik_kisiti_ayni_gune_ikinci_atamayi_reddeder(oturum: Session) -> None:
    personel = Personel(
        ad_soyad="Test Personel 2",
        sicil_no="TST-0002",
        haftalik_hedef_saat=40,
        aktif_baslangic=date(2026, 1, 1),
    )
    vardiya_tipi = VardiyaTipi(
        ad="Gunduz",
        baslangic_saati=time(8, 0),
        bitis_saati=time(16, 0),
        sure_saat=8,
        gece_mi=False,
    )
    nokta = GorevNoktasi(ad="Kapi")
    oturum.add_all([personel, vardiya_tipi, nokta])
    oturum.flush()

    donem = Donem(
        baslangic_tarihi=date(2026, 1, 1),
        bitis_tarihi=date(2026, 1, 28),
        tercih_son_tarihi=date(2025, 12, 25),
    )
    oturum.add(donem)
    oturum.flush()
    surum = CizelgeSurumu(donem_id=donem.donem_id, surum_no=1)
    oturum.add(surum)
    oturum.flush()

    ortak_alanlar = {
        "surum_id": surum.surum_id,
        "personel_id": personel.personel_id,
        "tarih": date(2026, 1, 5),
        "vardiya_tipi_id": vardiya_tipi.vardiya_tipi_id,
        "nokta_id": nokta.nokta_id,
        "kaynak": AtamaKaynagi.MANUEL,
    }
    oturum.add(Atama(**ortak_alanlar))
    oturum.flush()

    oturum.add(Atama(**ortak_alanlar))
    with pytest.raises(IntegrityError):
        oturum.flush()
