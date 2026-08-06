"""FR-1.3 (sure hesabi) ve FR-1.4/TD-2 (gece_mi onerisi) testleri."""

from datetime import time
from decimal import Decimal

from app.services.vardiya_hesaplari import gece_mi_oner, sure_saat_hesapla


def test_sure_hesapla_gun_icinde_biten_vardiya() -> None:
    assert sure_saat_hesapla(time(8, 0), time(16, 0)) == Decimal(8)


def test_sure_hesapla_gece_yarisini_asan_vardiya() -> None:
    assert sure_saat_hesapla(time(16, 0), time(0, 0)) == Decimal(8)
    assert sure_saat_hesapla(time(20, 0), time(8, 0)) == Decimal(12)


def test_gece_oneri_00_08_vardiyasi_gece_onerir() -> None:
    assert gece_mi_oner(time(0, 0), time(8, 0)) is True


def test_gece_oneri_08_16_vardiyasi_gece_onermez() -> None:
    assert gece_mi_oner(time(8, 0), time(16, 0)) is False


def test_gece_oneri_esik_altinda_kesisim_gece_onermez() -> None:
    # 22:00-24:00 araligi gece penceresiyle yalnizca 2 saat kesisir (< 4 saat esigi).
    assert gece_mi_oner(time(22, 0), time(0, 0)) is False
