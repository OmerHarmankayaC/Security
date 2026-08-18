"""Resmi tatil takvimi (SRS FR-1.10, app/services/tatil_takvimi.py).

Bu testlerin kilitledigi sey, kutuphaneye gecmenin GEREKCESIDIR: dini
bayramlarin tarihi hicri takvime baglidir ve her yil kayar. Sabit tarihli
bir liste onlari ya hic uretmez ya da yanlis uretir; ikisi de talep
matrisinin RESMI_TATIL satirlarini yanlis gunlere baglar.

Tarihler teste GOMULMEZ - hangi gun oldugu kutuphanenin bilgisidir ve
surum yukseltmesiyle duzelebilir. Sinanan sey takvimin OZELLIKLERIDIR.
"""

from datetime import date

from app.services.tatil_takvimi import resmi_tatiller, yil_araligi


def test_sabit_tarihli_ulusal_bayramlarin_tamami_bulunur() -> None:
    tarihler = {t for t, _ in resmi_tatiller([2026])}
    for ay, gun in ((1, 1), (4, 23), (5, 1), (5, 19), (7, 15), (8, 30), (10, 29)):
        assert date(2026, ay, gun) in tarihler, f"{gun:02d}.{ay:02d} takvimde yok"


def test_dini_bayramlar_uretilir_ve_yildan_yila_kayar() -> None:
    """Sabit tarihli bir listenin YAPAMADIGI sey."""

    def ramazan(yil: int) -> list[date]:
        return [t for t, ad in resmi_tatiller([yil]) if "Ramazan" in ad]

    iki_bin_yirmi_alti = ramazan(2026)
    iki_bin_yirmi_yedi = ramazan(2027)
    assert iki_bin_yirmi_alti, "Ramazan Bayrami uretilmedi"
    assert iki_bin_yirmi_yedi, "Ramazan Bayrami uretilmedi"
    # Hicri yil miladi yildan yaklasik on bir gun kisadir; bayram her yil
    # YIL ICINDE geriye kayar. Kiyas gun-of-year uzerinden yapilir - tam
    # tarihler zaten farkli yillarda.
    assert iki_bin_yirmi_yedi[0].timetuple().tm_yday < iki_bin_yirmi_alti[0].timetuple().tm_yday


def test_cok_gunlu_bayram_gun_gun_dondurulur() -> None:
    """Talep matrisi ve adalet sayaclari gun bazinda calisir, aralik bazinda degil."""
    kurban = [t for t, ad in resmi_tatiller([2026]) if "Kurban" in ad]
    assert len(kurban) >= 3
    # Ardisik gunler olmali - aralik tek satira toplanmamis.
    assert kurban == sorted(kurban)
    assert (kurban[-1] - kurban[0]).days == len(kurban) - 1


def test_adlar_turkce() -> None:
    adlar = {ad for _, ad in resmi_tatiller([2026])}
    assert "Cumhuriyet Bayramı" in adlar
    # Ingilizce adlar Ozel Gun ekraninda dogrudan kullaniciya gorunurdu.
    assert not any("Republic" in ad for ad in adlar)


def test_tarihe_gore_sirali() -> None:
    tarihler = [t for t, _ in resmi_tatiller([2026, 2027])]
    assert tarihler == sorted(tarihler)


def test_ayni_gun_iki_kez_dondurulmez() -> None:
    """`ozel_gun` tablosunun anahtari TARIHTIR (SDD 4.2.1); yinelenen bir
    gun ekleme aninda kisit hatasi verirdi."""
    tarihler = [t for t, _ in resmi_tatiller([2026, 2027])]
    assert len(tarihler) == len(set(tarihler))


def test_birden_fazla_yil_birlestirilir() -> None:
    tek = resmi_tatiller([2026])
    cift = resmi_tatiller([2026, 2027])
    assert len(cift) > len(tek)


def test_yil_araligi_yil_sinirini_asan_donemi_kapsar() -> None:
    assert yil_araligi(date(2026, 12, 28), date(2027, 1, 3)) == [2026, 2027]
    assert yil_araligi(date(2026, 3, 1), date(2026, 3, 31)) == [2026]
