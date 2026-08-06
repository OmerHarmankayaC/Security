"""Kisi basina azami haftalik vardiya sayisi: FR-1.9 (yuk_gostergesi) ve on_kontrol
(SDD 5.2) tarafindan paylasilan tek formul (SRS 3.3.6 yontemi)."""

from decimal import Decimal


def kisi_basina_azami_haftalik_vardiya(
    ortalama_vardiya_suresi_saat: Decimal | float,
    *,
    azami_haftalik_saat: Decimal,
    haftalik_asgari_izin_gunu: int,
) -> int:
    """H5 (saat tavani) ve H6 (asgari izin gunu) kisitlarindan turetilen iki ayri
    ust siniri karsilastirip kucuk olanini dondurur (SRS 3.3.6 ornegiyle tutarli:
    45 saat tavan, 8 saatlik vardiya -> 5; 7-1=6; min(5,6)=5)."""
    gun_bazli_azami = 7 - haftalik_asgari_izin_gunu
    if ortalama_vardiya_suresi_saat > 0 and azami_haftalik_saat > 0:
        saat_bazli_azami = int(azami_haftalik_saat / Decimal(ortalama_vardiya_suresi_saat))
        return max(0, min(saat_bazli_azami, gun_bazli_azami))
    return max(0, gun_bazli_azami)
