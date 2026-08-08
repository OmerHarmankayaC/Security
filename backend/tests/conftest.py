"""Testler arasi paylasilan yardimcilar: canli PostgreSQL gerektiren testler icin
atlama ve cozum iscisinin senkron calistirilmasi."""

import sys
from pathlib import Path

import pytest
from sqlalchemy.exc import OperationalError

from app.db import OturumYerel, engine
from app.models.sonuc import CozumIsiDurumu
from app.repositories.sonuc import CozumIsiDeposu

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.cozum_iscisi import siradaki_isi_isle  # noqa: E402

SONUCLANMIS_DURUMLAR = (
    CozumIsiDurumu.TAMAMLANDI,
    CozumIsiDurumu.UYARILI,
    CozumIsiDurumu.BASARISIZ,
    CozumIsiDurumu.IPTAL,
)


def pg_yoksa_atla() -> None:
    """Yerel PostgreSQL'e baglanilamiyorsa testi atlar (bkz. README "Kurulum")."""
    try:
        with engine.connect():
            pass
    except OperationalError:
        pytest.skip("Yerel PostgreSQL sunucusuna baglanilamadi")


def isi_calistir_ve_bekle(is_id: int, *, azami_adim: int = 5) -> CozumIsiDurumu:
    """Cozum iscisinin TEK ADIMINI senkron cagirir; hedef is sonuclanana
    kadar kuyruktan is isler ve isin son durumunu dondurur.

    `CozumServisi.baslat` artik surec ACMAZ (SDD 3.4.4: cozum ayri bir
    servistir), o yuzden testler isciyi kendileri surer. Surec acilmadigi
    icin davranis belirlenimlidir: yoklama, zaman asimi ve yaris yoktur.

    azami_adim, birden fazla is kuyruga alinmis testler icindir (hedef is
    kuyrukta ikinci sirada olabilir); sonsuz donguye karsi da sinirdir.
    """
    for _ in range(azami_adim):
        durum = _durumu_oku(is_id)
        if durum in SONUCLANMIS_DURUMLAR:
            return durum
        oturum = OturumYerel()
        try:
            if siradaki_isi_isle(oturum) is None:
                break  # kuyruk bos; hedef is sonuclanmamissa asagida hata verilir
        finally:
            oturum.close()

    durum = _durumu_oku(is_id)
    if durum not in SONUCLANMIS_DURUMLAR:
        pytest.fail(f"Cozum isi {is_id} {azami_adim} isci adiminda sonuclanmadi (durum: {durum})")
    return durum


def _durumu_oku(is_id: int) -> CozumIsiDurumu | None:
    oturum = OturumYerel()
    try:
        is_kaydi = CozumIsiDeposu(oturum).getir(is_id)
        return is_kaydi.durum if is_kaydi is not None else None
    finally:
        oturum.close()
