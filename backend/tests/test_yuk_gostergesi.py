"""FR-1.9 yuk gostergesi hesabi: SRS 3.3.6'daki referans ornekle dogrulama.

Veritabani gerektirmez; Talep/VardiyaTipi ORM nesneleri saf veri tasiyici
olarak (oturuma eklenmeden) kullanilir.
"""

from decimal import Decimal

from app.models.tanim import GunTipi, Talep, VardiyaTipi
from app.services.ornek_senaryo import AKSAM, GECE, GUNDUZ, talep_satirlarini_olustur
from app.services.yuk_gostergesi import yuk_gostergesi_hesapla

_VARDIYA_ID = {GECE: 1, GUNDUZ: 2, AKSAM: 3}
ORNEK_NOKTA_ID = (
    2  # NOKTA_TANIMLARI[2] (0-tabanli index) = Muracaat -- bkz. app/services/ornek_senaryo.py
)


def _vardiya_tipleri() -> dict[int, VardiyaTipi]:
    return {
        vid: VardiyaTipi(
            vardiya_tipi_id=vid, sure_saat=Decimal(8), gece_mi=(vid == _VARDIYA_ID[GECE])
        )
        for vid in _VARDIYA_ID.values()
    }


def _guvenlik_personeli_talep_matrisi() -> list[Talep]:
    """app.services.ornek_senaryo'daki SRS 3.3.3/3.3.4 tanimini Talep nesnelerine cevirir."""
    return [
        Talep(
            talep_id=i,
            nokta_id=tanim.nokta_index,
            vardiya_tipi_id=_VARDIYA_ID[tanim.vardiya_tipi],
            gun_tipi=tanim.gun_tipi,
            tarih=None,
            gereken_sayi=tanim.gereken_sayi,
        )
        for i, tanim in enumerate(talep_satirlarini_olustur(), start=1)
    ]


def test_srs_3_3_6_referans_ornegi_birebir_uretilir() -> None:
    hucreler = _guvenlik_personeli_talep_matrisi()
    yuk = yuk_gostergesi_hesapla(
        hucreler,
        _vardiya_tipleri(),
        azami_haftalik_saat=Decimal(45),
        haftalik_asgari_izin_gunu=1,
    )
    assert yuk.haftalik_kisi_vardiya == 144
    assert yuk.haftalik_kisi_saat == Decimal(1152)
    assert yuk.asgari_kadro == 29


def test_talep_yoksa_sifir_doner() -> None:
    yuk = yuk_gostergesi_hesapla(
        [], _vardiya_tipleri(), azami_haftalik_saat=Decimal(45), haftalik_asgari_izin_gunu=1
    )
    assert yuk.haftalik_kisi_vardiya == 0
    assert yuk.haftalik_kisi_saat == 0
    assert yuk.asgari_kadro == 0


def test_tekil_tarih_istisnasi_haftalik_yuke_girmez() -> None:
    from datetime import date

    hucreler = [
        Talep(
            talep_id=1,
            nokta_id=ORNEK_NOKTA_ID,
            vardiya_tipi_id=GUNDUZ,
            gun_tipi=GunTipi.HAFTA_ICI,
            tarih=date(2026, 3, 1),  # tekil istisna
            gereken_sayi=99,
        )
    ]
    yuk = yuk_gostergesi_hesapla(
        hucreler, _vardiya_tipleri(), azami_haftalik_saat=Decimal(45), haftalik_asgari_izin_gunu=1
    )
    assert yuk.haftalik_kisi_vardiya == 0


def test_resmi_tatil_haftalik_yuke_girmez() -> None:
    hucreler = [
        Talep(
            talep_id=1,
            nokta_id=ORNEK_NOKTA_ID,
            vardiya_tipi_id=GUNDUZ,
            gun_tipi=GunTipi.RESMI_TATIL,
            tarih=None,
            gereken_sayi=5,
        )
    ]
    yuk = yuk_gostergesi_hesapla(
        hucreler, _vardiya_tipleri(), azami_haftalik_saat=Decimal(45), haftalik_asgari_izin_gunu=1
    )
    assert yuk.haftalik_kisi_vardiya == 0
