"""SDD 4.2.1: talep icin gecerli deger onerilirken once tarihe ozgu istisna
satiri aranir, bulunamazsa gun tipine karsilik gelen genel satir kullanilir.
Bu modul, o cozumlemeyi somut bir gun listesi uzerinde yapar."""

from collections.abc import Sequence
from datetime import date

from app.models.tanim import GunTipi, Talep


def gun_tipi_belirle(tarih: date, ozel_gunler: frozenset[date]) -> GunTipi:
    """TD-3: ozel gun ise resmi tatil, cumartesi/pazar ise hafta sonu, aksi hafta ici."""
    if tarih in ozel_gunler:
        return GunTipi.RESMI_TATIL
    if tarih.weekday() >= 5:
        return GunTipi.HAFTA_SONU
    return GunTipi.HAFTA_ICI


def talep_matrisini_coz(
    talep_satirlari: Sequence[Talep],
    donem_gunleri: list[date],
    ozel_gunler: frozenset[date],
) -> dict[tuple[date, int, int], int]:
    """Genel (gun_tipi bazli) ve istisna (tarih bazli) talep satirlarini, donem
    gunleri icin somut (tarih, vardiya_tipi_id, nokta_id) -> gereken_sayi
    sozlugune cozer."""
    genel: dict[tuple[GunTipi, int, int], int] = {}
    istisna: dict[tuple[date, int, int], int] = {}
    for satir in talep_satirlari:
        if satir.tarih is not None:
            istisna[(satir.tarih, satir.vardiya_tipi_id, satir.nokta_id)] = satir.gereken_sayi
        else:
            genel[(satir.gun_tipi, satir.vardiya_tipi_id, satir.nokta_id)] = satir.gereken_sayi

    vardiya_nokta_ciftleri = {(v, n) for (_, v, n) in genel} | {(v, n) for (_, v, n) in istisna}

    cozulmus: dict[tuple[date, int, int], int] = {}
    for gun in donem_gunleri:
        gun_tipi = gun_tipi_belirle(gun, ozel_gunler)
        for v, n in vardiya_nokta_ciftleri:
            if (gun, v, n) in istisna:
                cozulmus[(gun, v, n)] = istisna[(gun, v, n)]
            elif (gun_tipi, v, n) in genel:
                cozulmus[(gun, v, n)] = genel[(gun_tipi, v, n)]
    return cozulmus
