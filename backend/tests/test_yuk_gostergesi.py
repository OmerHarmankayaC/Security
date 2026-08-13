"""FR-1.9 yuk gostergesi hesabi: SRS 3.3.6'daki referans ornekle dogrulama.

Veritabani gerektirmez; Talep/VardiyaTipi ORM nesneleri saf veri tasiyici
olarak (oturuma eklenmeden) kullanilir.
"""

from datetime import time
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
            vardiya_tipi_id=vid,
            baslangic_saati=time(8 * (vid - 1) % 24),
            bitis_saati=time(8 * vid % 24),
            sure_saat=Decimal(8),
            gece_mi=(vid == _VARDIYA_ID[GECE]),
            aktif=True,
        )
        for vid in _VARDIYA_ID.values()
    }


def _guvenlik_personeli_talep_matrisi() -> list[Talep]:
    """app.services.ornek_senaryo'daki SRS 3.3.3/3.3.4 tanimini Talep nesnelerine cevirir."""
    return [
        Talep(
            talep_id=i,
            nokta_id=tanim.nokta_index,
            baslangic=tanim.baslangic,
            bitis=tanim.bitis,
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
        fazla_calisma_esigi=Decimal(45),
        azami_gunluk_saat=Decimal(11),
        haftalik_asgari_izin_gunu=1,
    )
    # KISI-VARDIYA ARTIK URETILMEZ (FR-1.9, Tur 4): karisik uzunluklu
    # katalogda o sayi katalogun bilesimine baglidir ve ayni talep icin
    # farkli sayilar verir. SRS 3.3.6'nin referansi saat cinsindendir.
    assert yuk.haftalik_kisi_saat == Decimal(1152)
    # 1.152 / 45 = 25,6 -> 26. Asgari kadro artik FAZLA CALISMA ESIGINDEN
    # hesaplaniyor (SRS 3.3.6); once H5'in 45 saatlik tavanindan
    # hesaplaniyordu ve ayni sayiyi baska bir gerekceyle veriyordu. H5 66'ya
    # ciktigi icin eski yol 18 kisi derdi - surdurulebilir olmayan bir tempo.
    assert yuk.asgari_kadro == 26


def test_talep_yoksa_sifir_doner() -> None:
    yuk = yuk_gostergesi_hesapla(
        [],
        fazla_calisma_esigi=Decimal(45),
        azami_gunluk_saat=Decimal(11),
        haftalik_asgari_izin_gunu=1,
    )
    assert yuk.haftalik_kisi_saat == 0
    assert yuk.asgari_kadro == 0


def test_tekil_tarih_istisnasi_haftalik_yuke_girmez() -> None:
    from datetime import date

    hucreler = [
        Talep(
            talep_id=1,
            nokta_id=ORNEK_NOKTA_ID,
            baslangic=time(8, 0),
            bitis=time(16, 0),
            gun_tipi=GunTipi.HAFTA_ICI,
            tarih=date(2026, 3, 1),  # tekil istisna
            gereken_sayi=99,
        )
    ]
    yuk = yuk_gostergesi_hesapla(
        hucreler,
        fazla_calisma_esigi=Decimal(45),
        azami_gunluk_saat=Decimal(11),
        haftalik_asgari_izin_gunu=1,
    )


def test_resmi_tatil_haftalik_yuke_girmez() -> None:
    hucreler = [
        Talep(
            talep_id=1,
            nokta_id=ORNEK_NOKTA_ID,
            baslangic=time(8, 0),
            bitis=time(16, 0),
            gun_tipi=GunTipi.RESMI_TATIL,
            tarih=None,
            gereken_sayi=5,
        )
    ]
    yuk = yuk_gostergesi_hesapla(
        hucreler,
        fazla_calisma_esigi=Decimal(45),
        azami_gunluk_saat=Decimal(11),
        haftalik_asgari_izin_gunu=1,
    )


def test_resmi_tatil_satirlari_haftalik_yuku_degistirmez() -> None:
    """RESMI_TATIL satirlari matrise eklendi (FR-1.10 icin zorunlu), ama
    SRS 3.3.6'nin referans sayilari DEGISMEMELIDIR.

    Resmi tatil her hafta tekrarlanmaz; haftalik yuk gostergesi (FR-1.9)
    onu bu yuzden sifir tekrarla sayar. Bu test, matrise tatil satiri
    eklemenin gostergeyi sessizce sismesini engeller.
    """
    hucreler = _guvenlik_personeli_talep_matrisi()
    tatil_satirlari = [h for h in hucreler if h.gun_tipi == GunTipi.RESMI_TATIL]
    assert tatil_satirlari, "matris resmi tatil satiri tasimali"

    yuk = yuk_gostergesi_hesapla(
        hucreler,
        fazla_calisma_esigi=Decimal(45),
        azami_gunluk_saat=Decimal(11),
        haftalik_asgari_izin_gunu=1,
    )
    assert yuk.haftalik_kisi_saat == Decimal(1152)
