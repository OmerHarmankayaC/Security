"""Semanin gercek bir PostgreSQL'e karsi INSERT/SELECT ile dogrulanmasi (SDD 4.2).

Yerelde calisan bir PostgreSQL sunucusu ve gocleri uygulanmis bir veritabani
gerektirir (bkz. README "Kurulum"). `alembic upgrade head` onceden calismis olmalidir.
"""

from datetime import date, datetime

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


def _surum_kur(oturum: Session, sicil: str) -> tuple[int, int, int]:
    personel = Personel(
        ad_soyad="Test Personel",
        sicil_no=sicil,
        haftalik_hedef_saat=40,
        aktif_baslangic=date(2026, 1, 1),
    )
    nokta = GorevNoktasi(ad="Güvenlik")
    oturum.add_all([personel, nokta])
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
    return surum.surum_id, personel.personel_id, nokta.nokta_id


def test_atama_benzersizlik_kisiti_ayni_baslangici_reddeder(oturum: Session) -> None:
    """Anahtar `(surum_id, personel_id, baslangic_zamani)` (SDD 4.2.1)."""
    surum_id, personel_id, nokta_id = _surum_kur(oturum, "TST-0002")
    ortak_alanlar = {
        "surum_id": surum_id,
        "personel_id": personel_id,
        "baslangic_zamani": datetime(2026, 1, 5, 8, 0),
        "bitis_zamani": datetime(2026, 1, 5, 16, 0),
        "nokta_id": nokta_id,
        "kaynak": AtamaKaynagi.MANUEL,
    }
    oturum.add(Atama(**ortak_alanlar))
    oturum.flush()

    oturum.add(Atama(**ortak_alanlar))
    with pytest.raises(IntegrityError):
        oturum.flush()


def test_ayni_gunde_farkli_saatte_ikinci_blogu_veritabani_yakalamaz(oturum: Session) -> None:
    """GUVENCE KAYBI BILINCLIDIR ve burada YAZILI (SDD 4.2.1).

    Eski anahtar `(surum_id, personel_id, tarih)` idi ve "gunde tek atama"yi
    veritabani duzeyinde zorluyordu. Yeni anahtar baslangic ZAMANINI tasidigi
    icin ayni gunde farkli saatte baslayan ikinci bir blok semaya takilmaz;
    kural artik yalnizca uygulama katmanindadir (H1) ve manuel duzenleme
    yolu onu denetlemek zorundadir (bkz. test_dogrulama_servisi).

    Test kaybi OLCER: yarin biri semaya guvenip uygulama katmanindaki
    denetimi kaldirirsa, bu testin adi ona ne oldugunu soyler.
    """
    surum_id, personel_id, nokta_id = _surum_kur(oturum, "TST-0003")
    ortak = {
        "surum_id": surum_id,
        "personel_id": personel_id,
        "nokta_id": nokta_id,
        "kaynak": AtamaKaynagi.MANUEL,
    }
    oturum.add(
        Atama(
            baslangic_zamani=datetime(2026, 1, 5, 8, 0),
            bitis_zamani=datetime(2026, 1, 5, 16, 0),
            **ortak,
        )
    )
    oturum.add(
        Atama(
            baslangic_zamani=datetime(2026, 1, 5, 18, 0),
            bitis_zamani=datetime(2026, 1, 5, 23, 0),
            **ortak,
        )
    )
    oturum.flush()  # sema itiraz etmez


def test_gece_yarisini_asan_blok_tek_kayitta_durur(oturum: Session) -> None:
    """SDD 4.2.1: `bitis_zamani` ertesi gune duser, kayit bolunmez."""
    surum_id, personel_id, nokta_id = _surum_kur(oturum, "TST-0004")
    oturum.add(
        Atama(
            surum_id=surum_id,
            personel_id=personel_id,
            nokta_id=nokta_id,
            kaynak=AtamaKaynagi.COZUCU,
            baslangic_zamani=datetime(2026, 1, 5, 20, 0),
            bitis_zamani=datetime(2026, 1, 6, 6, 0),
        )
    )
    oturum.flush()

    kayit = oturum.execute(
        select(Atama).where(Atama.surum_id == surum_id, Atama.personel_id == personel_id)
    ).scalar_one()
    assert kayit.baslangic_zamani.date() == date(2026, 1, 5)  # TD-1: blok bu gune sayilir
    assert kayit.bitis_zamani.date() == date(2026, 1, 6)


def test_vardiya_tipi_tablosu_semada_yok(oturum: Session) -> None:
    """Tur 5: blok katalogu kalkti (SRS TD-13)."""
    from sqlalchemy import text

    tablolar = {
        satir[0]
        for satir in oturum.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        )
    }
    assert "vardiya_tipi" not in tablolar
