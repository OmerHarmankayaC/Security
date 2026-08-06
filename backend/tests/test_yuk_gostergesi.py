"""FR-1.9 yuk gostergesi hesabi: SRS 3.3.6'daki referans ornekle dogrulama.

Veritabani gerektirmez; Talep/VardiyaTipi ORM nesneleri saf veri tasiyici
olarak (oturuma eklenmeden) kullanilir.
"""

from decimal import Decimal

from app.models.tanim import GunTipi, Talep, VardiyaTipi
from app.services.yuk_gostergesi import yuk_gostergesi_hesapla

GECE, GUNDUZ, AKSAM = 1, 2, 3
VARDIYA_SEFLIGI, KONTROL_ODASI, KAPI_A, KAPI_B, MURACAAT_A, MURACAAT_B = range(1, 7)


def _vardiya_tipleri() -> dict[int, VardiyaTipi]:
    return {
        vid: VardiyaTipi(vardiya_tipi_id=vid, sure_saat=Decimal(8), gece_mi=(vid == GECE))
        for vid in (GECE, GUNDUZ, AKSAM)
    }


def _guvenlik_personeli_talep_matrisi() -> list[Talep]:
    """SRS 3.3.3/3.3.4'teki tabloyu tam acilmis talep satirlarina cevirir.

    'Gece / Hafta Sonu / Tatil' sutunu; hafta ici gece vardiyasina VE hafta
    sonu/resmi tatildeki her uc vardiyaya da ayni deger olarak uygulanir
    (SRS 3.3.4: 'Hafta sonu ve resmi tatillerde uc vardiyanin tamami
    azaltilmis kadroyla calisir').
    """
    # nokta_id -> (hafta_ici_gunduz, hafta_ici_aksam, gece_veya_hafta_sonu_veya_tatil)
    matris = {
        VARDIYA_SEFLIGI: (1, 1, 1),
        KONTROL_ODASI: (1, 1, 1),
        KAPI_A: (3, 3, 1),
        KAPI_B: (3, 3, 1),
        MURACAAT_A: (1, 1, 0),
        MURACAAT_B: (1, 1, 0),
    }
    satirlar: list[Talep] = []
    talep_id = 1
    for nokta_id, (hi_gunduz, hi_aksam, azaltilmis) in matris.items():
        satirlar.append(
            Talep(
                talep_id=talep_id,
                nokta_id=nokta_id,
                vardiya_tipi_id=GUNDUZ,
                gun_tipi=GunTipi.HAFTA_ICI,
                tarih=None,
                gereken_sayi=hi_gunduz,
            )
        )
        talep_id += 1
        satirlar.append(
            Talep(
                talep_id=talep_id,
                nokta_id=nokta_id,
                vardiya_tipi_id=AKSAM,
                gun_tipi=GunTipi.HAFTA_ICI,
                tarih=None,
                gereken_sayi=hi_aksam,
            )
        )
        talep_id += 1
        for vardiya_tipi_id, gun_tipi in (
            (GECE, GunTipi.HAFTA_ICI),
            (GUNDUZ, GunTipi.HAFTA_SONU),
            (AKSAM, GunTipi.HAFTA_SONU),
            (GECE, GunTipi.HAFTA_SONU),
        ):
            satirlar.append(
                Talep(
                    talep_id=talep_id,
                    nokta_id=nokta_id,
                    vardiya_tipi_id=vardiya_tipi_id,
                    gun_tipi=gun_tipi,
                    tarih=None,
                    gereken_sayi=azaltilmis,
                )
            )
            talep_id += 1
    return satirlar


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
            nokta_id=KAPI_A,
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
            nokta_id=KAPI_A,
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
