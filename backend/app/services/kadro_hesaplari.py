"""Asgari kadro buyuklugu: FR-1.9 (yuk_gostergesi) ve on_kontrol (SDD 5.2)
tarafindan paylasilan tek formul (SRS 3.3.6 yontemi)."""

from decimal import ROUND_CEILING, Decimal


def surdurulebilir_haftalik_saat(
    *,
    fazla_calisma_esigi: Decimal,
    azami_gunluk_saat: Decimal,
    haftalik_asgari_izin_gunu: int,
) -> Decimal:
    """Bir personelin haftada SURDURULEBILIR bicimde calisabilecegi saat.

    SRS 3.3.6 kadro gereksinimini fazla calisma esigi uzerinden hesaplar:
    1.152 saat / 45 saat ≈ 26 kisi. Esigin USTU yasak degildir (H5'in mutlak
    tavani 66'dir) ama o saatlerin tamami fazla calisma sayilir ve yillik
    kotayi (H10) hizla tuketir; surdurulebilir planlama esigin altinda
    kalmayi gerektirir.

    Ust sinir yine de H6 ve H9 ile sinirlidir: haftada en cok
    `7 − izin_gunu` gun, gunde en cok `azami_gunluk_saat` saat. Iki degerin
    KUCUGU alinir.

    Mutlak tavan (H5) bu hesaba GIRMEZ ve bu bilinclidir: 66 saatle bolmek
    kadroyu, hicbir zaman ulasilmamasi gereken bir calisma temposuna gore
    boyutlandirirdi.
    """
    gun_bazli = Decimal(max(0, 7 - haftalik_asgari_izin_gunu)) * azami_gunluk_saat
    if fazla_calisma_esigi <= 0:
        return gun_bazli
    return min(fazla_calisma_esigi, gun_bazli)


def asgari_kadro_hesapla(
    haftalik_kisi_saat: Decimal,
    *,
    fazla_calisma_esigi: Decimal,
    azami_gunluk_saat: Decimal,
    haftalik_asgari_izin_gunu: int,
) -> int:
    """Toplam haftalik kisi-saat yukunu tasiyabilecek asgari personel sayisi.

    Izin ve rapor payi HARICTIR (SRS 3.3.6: "payla birlikte 29"); pay
    kullanicinin karari, hesabin degil.
    """
    if haftalik_kisi_saat <= 0:
        return 0
    kisi_basina = surdurulebilir_haftalik_saat(
        fazla_calisma_esigi=fazla_calisma_esigi,
        azami_gunluk_saat=azami_gunluk_saat,
        haftalik_asgari_izin_gunu=haftalik_asgari_izin_gunu,
    )
    if kisi_basina <= 0:
        return 0
    # DECIMAL'DE `//` SIFIRA DOGRU KIRPAR, tam sayidaki gibi asagi
    # yuvarlamaz; `-(-a // b)` kalibi burada BIR EKSIK sonuc verir
    # (1.152 / 45 = 25,6 -> 25). ROUND_CEILING acikca istenir.
    return int((haftalik_kisi_saat / kisi_basina).to_integral_value(rounding=ROUND_CEILING))
