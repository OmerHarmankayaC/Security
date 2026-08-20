"""CizelgeSurumuDeposu.taslak_ac testleri (Tur 13, Gorev 1).

Canli PostgreSQL gerektirir; senaryo `senaryo_verisini_temizle` ile izole
edilir (bkz. tests/conftest.py).
"""

import uuid
from datetime import date, timedelta

from app.db import OturumYerel
from app.models.sonuc import CizelgeSurumuDurumu, Donem
from app.repositories.sonuc import AtamaDeposu, CizelgeSurumuDeposu
from tests.conftest import pg_yoksa_atla, senaryo_verisini_temizle


def _donem_olustur(oturum: OturumYerel) -> int:
    on_ek = uuid.uuid4().hex[:8]
    baslangic = date(2026, 9, 7)  # Pazartesi
    donem = Donem(
        baslangic_tarihi=baslangic,
        bitis_tarihi=baslangic + timedelta(days=6),
        tercih_son_tarihi=baslangic - timedelta(days=7),
    )
    oturum.add(donem)
    oturum.commit()
    _ = on_ek  # senaryo icin benzersizlik gerekmiyor, temizlik zaten tum donemleri siler
    return donem.donem_id


def test_taslak_ac_bos_donemde_bagsiz_acar() -> None:
    pg_yoksa_atla()
    oturum = OturumYerel()
    try:
        senaryo_verisini_temizle(oturum)
        donem_id = _donem_olustur(oturum)

        depo = CizelgeSurumuDeposu(oturum)
        yeni = depo.taslak_ac(donem_id)
        oturum.commit()

        assert yeni.surum_no == 1
        assert yeni.onceki_surum_id is None
        assert yeni.durum == CizelgeSurumuDurumu.TASLAK
        assert AtamaDeposu(oturum).surume_gore_getir(yeni.surum_id) == []
    finally:
        oturum.close()


def test_taslak_ac_mevcut_surume_baglanir() -> None:
    pg_yoksa_atla()
    oturum = OturumYerel()
    try:
        senaryo_verisini_temizle(oturum)
        donem_id = _donem_olustur(oturum)

        depo = CizelgeSurumuDeposu(oturum)
        v1 = depo.olustur(donem_id=donem_id, surum_no=1, durum=CizelgeSurumuDurumu.YAYINLANDI)
        v2 = depo.olustur(donem_id=donem_id, surum_no=2, durum=CizelgeSurumuDurumu.ARSIV)
        oturum.commit()
        v2_id = v2.surum_id
        _ = v1

        yeni = depo.taslak_ac(donem_id)
        oturum.commit()

        assert yeni.surum_no == 3
        assert yeni.onceki_surum_id == v2_id
        assert yeni.durum == CizelgeSurumuDurumu.TASLAK
    finally:
        oturum.close()
