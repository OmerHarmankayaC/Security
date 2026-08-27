"""Kural katalogu tohumunun sozlesmesi (Demo Senaryosu 4.6).

Katalog iki ortamda BIREBIR ayni olmak zorunda. Gecmiste ayrismisti ve
mekanizma sudur: goc zinciri katalogun bir bolumunu (H9, H10, S1f) yazar,
uretecin duz INSERT'i o satirlara carpar ya da onlari atlar. Uc iddia:

  1. Bos katalogda kurulum SRS bolum 4'un yirmi kimligini yazar.
  2. Gocun yazdigi kismi katalogun uzerine kurulum yinelenen satir
     uretmez ve kalan satirlari tamamlar.
  3. Kurulum iki kez kosturuldugunda katalog degismez (idempotent).
"""

import pytest
from sqlalchemy import select

from app.db import OturumYerel
from app.models.kural import Kural, KuralTipi
from app.services.kural_katalogu_tohumu import KURAL_TANIMLARI, katalogu_kur
from tests.conftest import pg_yoksa_atla


@pytest.fixture
def oturum():  # noqa: ANN201 - Session
    pg_yoksa_atla()
    oturum = OturumYerel()
    try:
        oturum.query(Kural).delete()
        oturum.flush()
        yield oturum
    finally:
        oturum.rollback()
        oturum.close()


def _katalogu_oku(oturum) -> dict[str, tuple]:  # noqa: ANN001 - Session
    return {
        kural.kimlik: (kural.tip, kural.parametreler, kural.agirlik, kural.aktif)
        for kural in oturum.execute(select(Kural)).scalars().all()
    }


def test_bos_katalogda_yirmi_kural_kurulur(oturum) -> None:  # noqa: ANN001
    katalogu_kur(oturum)

    katalog = _katalogu_oku(oturum)
    assert len(katalog) == 20
    assert set(katalog) == {tanim["kimlik"] for tanim in KURAL_TANIMLARI}
    # S6b katalogda KALIR ama pasiftir (SRS 4.3 notu); S1f aktiftir.
    assert katalog["S6b"][3] is False
    assert katalog["S1f"][3] is True


def test_gocun_yazdigi_kismi_katalogun_uzerine_kurulur(oturum) -> None:  # noqa: ANN001
    """Goc e7b2c4915d80 H9/H10/S1f yazar; kurulum bunlara carpmamali."""
    oturum.add_all(
        [
            Kural(
                kimlik="H9",
                tip=KuralTipi.ZORUNLU,
                parametreler={"azami_gunluk_saat": 11},
                agirlik=None,
            ),
            Kural(
                kimlik="H10",
                tip=KuralTipi.ZORUNLU,
                parametreler={"fazla_calisma_esigi": 45, "yillik_fazla_kotasi": 270},
                agirlik=None,
            ),
            Kural(kimlik="S1f", tip=KuralTipi.ESNEK, parametreler={}, agirlik=2),
        ]
    )
    oturum.flush()

    katalogu_kur(oturum)

    katalog = _katalogu_oku(oturum)
    assert len(katalog) == 20
    assert katalog["H9"][1] == {"azami_gunluk_saat": 11}


def test_kurulum_idempotenttir(oturum) -> None:  # noqa: ANN001
    katalogu_kur(oturum)
    ilk = _katalogu_oku(oturum)

    katalogu_kur(oturum)
    ikinci = _katalogu_oku(oturum)

    assert ilk == ikinci
