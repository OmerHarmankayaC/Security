"""Donem basina acik surum siniri ve yayinlanmamis surumun silinmesi.

Ikisi ayni turde bir sorunu iki uctan kavriyor: her cozum denemesi bir surum
aciyor, hicbiri kendiliginden kapanmiyor. Sinir birikmeyi durdurur, silme
birikeni temizler; biri olmadan digeri yetmez - yalnizca sinir, kullaniciyi
cikisi olmayan bir duvara dayardi.

Silmenin UC RETTI ayri ayri sinaniyor cunku ucu de farkli bir sey koruyor:
yayinlanmis surumu calisan paneli okur, arsiv surum "degisen gunler"
isaretinin tabanidir, zincire bagli surum S8'in dayanagidir.
"""

from datetime import date, timedelta

import pytest
from sqlalchemy import select

from app.db import OturumYerel
from app.models.sonuc import Atama, CizelgeSurumu, CizelgeSurumuDurumu, Donem
from app.repositories.sonuc import (
    DONEM_BASINA_AZAMI_ACIK_SURUM,
    CizelgeSurumuDeposu,
    SurumSilinemezError,
    TaslakSiniriAsildiError,
)
from tests.conftest import pg_yoksa_atla


@pytest.fixture
def oturum():  # noqa: ANN201 - Session
    pg_yoksa_atla()
    oturum = OturumYerel()
    try:
        yield oturum
    finally:
        oturum.rollback()
        oturum.close()


def _donem(oturum, gun_kaydir: int = 0) -> Donem:  # noqa: ANN001
    bas = date(2026, 3, 2) + timedelta(days=gun_kaydir)
    donem = Donem(
        baslangic_tarihi=bas,
        bitis_tarihi=bas + timedelta(days=6),
        tercih_son_tarihi=bas - timedelta(days=1),
    )
    oturum.add(donem)
    oturum.flush()
    return donem


def _surum(depo: CizelgeSurumuDeposu, donem: Donem, **alanlar) -> CizelgeSurumu:  # noqa: ANN003
    return depo.olustur(
        donem_id=donem.donem_id,
        surum_no=depo.donem_icin_sonraki_surum_no(donem.donem_id),
        **alanlar,
    )


# --- Sinir ------------------------------------------------------------------


def test_sinira_kadar_surum_acilir(oturum) -> None:  # noqa: ANN001
    depo = CizelgeSurumuDeposu(oturum)
    donem = _donem(oturum)

    for _ in range(DONEM_BASINA_AZAMI_ACIK_SURUM):
        _surum(depo, donem)

    assert depo.acik_surum_sayisi(donem.donem_id) == DONEM_BASINA_AZAMI_ACIK_SURUM


def test_sinirin_ustunde_surum_acilmaz(oturum) -> None:  # noqa: ANN001
    depo = CizelgeSurumuDeposu(oturum)
    donem = _donem(oturum)
    for _ in range(DONEM_BASINA_AZAMI_ACIK_SURUM):
        _surum(depo, donem)

    with pytest.raises(TaslakSiniriAsildiError):
        _surum(depo, donem)


def test_sinir_donem_basinadir(oturum) -> None:  # noqa: ANN001
    """Dolan bir donem, baska bir donemde surum acmayi engellemez."""
    depo = CizelgeSurumuDeposu(oturum)
    dolu, bos = _donem(oturum), _donem(oturum, gun_kaydir=7)
    for _ in range(DONEM_BASINA_AZAMI_ACIK_SURUM):
        _surum(depo, dolu)

    _surum(depo, bos)  # yukselmemeli

    assert depo.acik_surum_sayisi(bos.donem_id) == 1


def test_yayinlanmis_ve_arsiv_surumler_sinira_sayilmaz(oturum) -> None:  # noqa: ANN001
    """Sayim kaydi kapsasaydi, yeterince duzeltilmis bir donem bir daha
    YAYINLANAMAZDI - sinir tam da duzeltmeyi engellerdi."""
    depo = CizelgeSurumuDeposu(oturum)
    donem = _donem(oturum)
    for _ in range(DONEM_BASINA_AZAMI_ACIK_SURUM):
        _surum(depo, donem, durum=CizelgeSurumuDurumu.YAYINLANDI)
    for _ in range(DONEM_BASINA_AZAMI_ACIK_SURUM):
        _surum(depo, donem, durum=CizelgeSurumuDurumu.ARSIV)

    _surum(depo, donem)  # yukselmemeli

    assert depo.acik_surum_sayisi(donem.donem_id) == 1


def test_silmek_sinirda_yer_acar(oturum) -> None:  # noqa: ANN001
    """Sinir ile silmenin birlikte calismasi: cikisi olmayan bir duvar degil."""
    depo = CizelgeSurumuDeposu(oturum)
    donem = _donem(oturum)
    surumler = [_surum(depo, donem) for _ in range(DONEM_BASINA_AZAMI_ACIK_SURUM)]

    depo.sil(surumler[0].surum_id)

    _surum(depo, donem)  # yukselmemeli
    assert depo.acik_surum_sayisi(donem.donem_id) == DONEM_BASINA_AZAMI_ACIK_SURUM


# --- Silme ------------------------------------------------------------------


def test_taslak_silinir_ve_atamalari_gider(oturum) -> None:  # noqa: ANN001
    depo = CizelgeSurumuDeposu(oturum)
    donem = _donem(oturum)
    surum = _surum(depo, donem)
    oturum.add(
        Atama(
            surum_id=surum.surum_id,
            personel_id=_personel(oturum),
            baslangic_zamani=f"{donem.baslangic_tarihi} 08:00",
            bitis_zamani=f"{donem.baslangic_tarihi} 16:00",
            nokta_id=_nokta(oturum),
            kilitli=False,
            kaynak="COZUCU",
        )
    )
    oturum.flush()

    assert depo.sil(surum.surum_id) is True

    kalan = oturum.execute(select(Atama).where(Atama.surum_id == surum.surum_id)).scalars().all()
    assert kalan == []
    assert depo.getir(surum.surum_id) is None


def test_olmayan_surum_false_doner(oturum) -> None:  # noqa: ANN001
    assert CizelgeSurumuDeposu(oturum).sil(10**8) is False


def test_yayinlanmis_surum_silinmez(oturum) -> None:  # noqa: ANN001
    depo = CizelgeSurumuDeposu(oturum)
    surum = _surum(depo, _donem(oturum), durum=CizelgeSurumuDurumu.YAYINLANDI)

    with pytest.raises(SurumSilinemezError, match="Yayınlanmış"):
        depo.sil(surum.surum_id)


def test_arsiv_surum_silinmez(oturum) -> None:  # noqa: ANN001
    depo = CizelgeSurumuDeposu(oturum)
    surum = _surum(depo, _donem(oturum), durum=CizelgeSurumuDurumu.ARSIV)

    with pytest.raises(SurumSilinemezError, match="Arşivlenmiş"):
        depo.sil(surum.surum_id)


def test_zincire_bagli_surum_silinmez(oturum) -> None:  # noqa: ANN001
    """Ortadan bir halka cikarmak S8'in ve karsilastirmanin dayanagini koparir."""
    depo = CizelgeSurumuDeposu(oturum)
    donem = _donem(oturum)
    onceki = _surum(depo, donem)
    _surum(depo, donem, onceki_surum_id=onceki.surum_id)

    with pytest.raises(SurumSilinemezError, match="türetilmiş"):
        depo.sil(onceki.surum_id)


def test_zincirin_ucu_silinince_taban_silinebilir(oturum) -> None:  # noqa: ANN001
    depo = CizelgeSurumuDeposu(oturum)
    donem = _donem(oturum)
    onceki = _surum(depo, donem)
    sonraki = _surum(depo, donem, onceki_surum_id=onceki.surum_id)

    depo.sil(sonraki.surum_id)

    assert depo.sil(onceki.surum_id) is True


# --- Yardimcilar ------------------------------------------------------------


def _personel(oturum) -> int:  # noqa: ANN001
    from app.models.tanim import Personel

    kisi = Personel(
        ad_soyad="Sınır Testi",
        sicil_no=f"SNR-{id(oturum) % 100000}",
        haftalik_hedef_saat=40,
        aktif_baslangic=date(2026, 1, 1),
    )
    oturum.add(kisi)
    oturum.flush()
    return kisi.personel_id


def _nokta(oturum) -> int:  # noqa: ANN001
    from app.models.tanim import GorevNoktasi

    nokta = GorevNoktasi(ad=f"Sınır Noktası {id(oturum) % 100000}")
    oturum.add(nokta)
    oturum.flush()
    return nokta.nokta_id
