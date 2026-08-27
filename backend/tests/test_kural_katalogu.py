"""Kural katalogu ust verisi ve parametre dogrulamasi (madde 2).

Veritabani gerektirmez; kayit defteri ve sema uzerinde calisir.
"""

import pytest

from app.kurallar import kayit_defteri
from app.models.kural import KuralTipi
from app.services.tanim_servisi import KuralParametresiError, TanimServisi

# SRS bolum 4'teki kural katalogu. Arayuzde "H1" yerine bu adlar gosterilir.
_BEKLENEN_ADLAR = {
    # H1 yeniden tanimlandi (SRS 4.2, Tur 5): kural artik yalnizca "gunde
    # tek atama" demiyor - blok kesintisizdir, asgari sureden kisa olamaz
    # ve blok boyunca nokta degismez.
    "H1": "Günde tek ve kesintisiz çalışma",
    "H2": "Asgari dinlenme süresi",
    "H3": "Ardışık gece üst sınırı",
    "H4": "Ardışık çalışma günü üst sınırı",
    # Tur 4 (K6): kirk bes saat artik tavan degil, H10'un ESIGI. H5 dinlenme
    # amacli mutlak siniri korur ve varsayilani 66'ya cikti.
    "H5": "Kayan yedi günlük mutlak tavan",
    "H6": "Haftalık asgari izin günü",
    "H7": "Müsaitlik",
    "H8": "Ön koşul yetkinliği",
    # Tur 4: K7 ve K8.
    "H9": "Günlük azami çalışma süresi",
    "H10": "Yıllık fazla çalışma kotası",
    "S1": "Talep karşılama",
    # Tur 4 (K4): S1'in ust siniri esnedi; agirligi ayri oldugu icin kural
    # kaydi da ayri (S6/S6b ile ayni bolme).
    "S1f": "Fazla kadro",
    "S2": "Gece adaleti",
    "S3": "Hafta sonu adaleti",
    "S4": "Toplam saat dengesi",
    "S5": "Tercih karşılama",
    # Tur 4 (K13): olcu blok kimligi degil BASLANGIC SAATI kaymasi.
    "S6": "Çalışma deseni tutarlılığı",
    # 06.08.2026 karari: S6, S6 ve S6b olarak ikiye bolundu.
    "S6b": "Bina tutarlılığı",
    "S7": "İzole gün",
    "S8": "Değişim minimizasyonu",
}


def test_katalogdaki_her_kuralin_adi_srs_ile_ayni() -> None:
    assert {k: kayit_defteri.bul(k).ad for k in kayit_defteri.tum_kimlikler()} == _BEKLENEN_ADLAR


def test_her_kuralin_kisa_aciklamasi_var() -> None:
    """Arayuz kimligin yaninda ne ise yaradigini yazar; bos aciklama kalmamali."""
    for kimlik in kayit_defteri.tum_kimlikler():
        aciklama = kayit_defteri.bul(kimlik).aciklama
        assert aciklama, kimlik
        assert aciklama.endswith("."), f"{kimlik}: aciklama tam cumle olmali"


def test_parametre_okuyan_her_kural_o_parametreyi_tanimliyor() -> None:
    """`self.parametreler[...]` ile okunan her anahtarin arayuzde bir alani olmali.

    Tanimsiz birakilan bir parametre arayuzde gorunmez; kullanici degeri
    degistiremez ve neden degistiremedigini de anlamaz.
    """
    import inspect
    import re

    for kimlik in kayit_defteri.tum_kimlikler():
        sinif = kayit_defteri.bul(kimlik)
        kaynak = inspect.getsource(sinif)
        okunanlar = set(re.findall(r'self\.parametreler\[["\'](\w+)["\']\]', kaynak))
        tanimlananlar = {t.anahtar for t in sinif.parametre_tanimlari}
        assert (
            okunanlar <= tanimlananlar
        ), f"{kimlik}: kodda okunan ama tanimlanmayan parametre {okunanlar - tanimlananlar}"


def test_tanimlanan_her_parametrenin_etiketi_ve_siniri_var() -> None:
    for kimlik in kayit_defteri.tum_kimlikler():
        for tanim in kayit_defteri.bul(kimlik).parametre_tanimlari:
            assert tanim.etiket, f"{kimlik}.{tanim.anahtar}"
            assert tanim.anahtar not in tanim.etiket, "etiket alan adi olmamali (NFR-5)"
            assert (
                tanim.asgari is not None and tanim.azami is not None
            ), f"{kimlik}.{tanim.anahtar}: arayuzun sinir gosterebilmesi icin ikisi de gerekli"
            assert tanim.asgari < tanim.azami


def test_esnek_hedefler_agirlikli_zorunlu_kisitlar_degil() -> None:
    for kimlik in kayit_defteri.tum_kimlikler():
        sinif = kayit_defteri.bul(kimlik)
        beklenen = KuralTipi.ESNEK if kimlik.startswith("S") else KuralTipi.ZORUNLU
        assert sinif.tip == beklenen, kimlik


class _SahteKuralDeposu:
    """Parametre dogrulamasi icin veritabanina gitmeyen asgari sahte depo."""

    def __init__(self, mevcut: dict[str, object]) -> None:
        self._mevcut = mevcut

    def kimlige_gore_bul(self, kimlik: str) -> object:
        del kimlik
        return type("Satir", (), {"parametreler": self._mevcut})()


def _servis(mevcut: dict[str, object] | None = None) -> TanimServisi:
    servis = TanimServisi.__new__(TanimServisi)
    servis.kural = _SahteKuralDeposu(mevcut or {})  # type: ignore[assignment]
    return servis


def test_gecerli_parametre_kabul_edilir() -> None:
    assert _servis().kural_parametrelerini_dogrula("H2", {"asgari_dinlenme_saati": 16}) == {
        "asgari_dinlenme_saati": 16
    }


def test_tanimsiz_parametre_reddedilir() -> None:
    """JSONB alani sema dogrulamasi yapmaz; yanlis anahtar yazma aninda yakalanmali."""
    with pytest.raises(KuralParametresiError) as hata:
        _servis().kural_parametrelerini_dogrula("H2", {"asgari_dinlenmesaati": 16})
    assert "asgari_dinlenme_saati" in str(hata.value), "beklenen anahtar kullaniciya soylenmeli"


def test_sinir_disi_deger_reddedilir() -> None:
    with pytest.raises(KuralParametresiError) as alt:
        _servis().kural_parametrelerini_dogrula("H3", {"azami_ardisik_gece": 0})
    assert "en az" in str(alt.value)

    with pytest.raises(KuralParametresiError) as ust:
        _servis().kural_parametrelerini_dogrula("H5", {"haftalik_mutlak_tavan": 200})
    assert "en fazla" in str(ust.value)


def test_tam_sayi_olmayan_deger_reddedilir() -> None:
    for deger in ("16", 16.5, None, True):
        with pytest.raises(KuralParametresiError):
            _servis().kural_parametrelerini_dogrula("H2", {"asgari_dinlenme_saati": deger})


def test_kismi_guncelleme_diger_parametreleri_korur() -> None:
    """Arayuz tek bir alani gonderdiginde digerleri silinmemeli."""
    mevcut = {"asgari_dinlenme_saati": 11, "kullanilmayan": 3}
    sonuc = _servis(mevcut).kural_parametrelerini_dogrula("H2", {"asgari_dinlenme_saati": 16})
    assert sonuc == {"asgari_dinlenme_saati": 16, "kullanilmayan": 3}


def test_katalogda_olmayan_kimlik_reddedilir() -> None:
    with pytest.raises(KuralParametresiError):
        _servis().kural_parametrelerini_dogrula("H99", {})


# --- S1 pasif cikmasinin kaynagini kapatan kilitler -------------------------


def test_demo_ureteci_s1_i_aktif_uretir() -> None:
    """Canlida S1 pasif goruldu. Katalog tohumu suphelilerden biriydi; bu
    test onu kalici olarak eler.

    Ayni listede S6b'nin BILINCLI olarak pasif oldugu da sabitlenir (bina
    ayrimi kalktigindan modelde daima 0 katki verir, SRS S6b) — ikisi ayni
    listede yan yana durdugu icin bir gun biri digerinin yerine yazilabilir.
    """
    from app.services.kural_katalogu_tohumu import KURAL_TANIMLARI

    aktiflik = {t["kimlik"]: t.get("aktif", True) for t in KURAL_TANIMLARI}
    assert aktiflik["S1"] is True
    assert aktiflik["S6b"] is False
    pasifler = {kimlik for kimlik, aktif in aktiflik.items() if aktif is False}
    assert pasifler == {"S6b"}, f"uretecte beklenmeyen pasif kural: {pasifler - {'S6b'}}"


def test_demo_ureteci_katalogun_tamamini_uretir() -> None:
    """Tohumda eksik kalan bir kural, veritabaninda satiri olmadigi icin
    `aktif_kurallari_getir` tarafindan hic dondurulmez — pasif olmaktan
    ayirt edilemeyen bir sonuc verir."""
    from app.services.kural_katalogu_tohumu import KURAL_TANIMLARI

    assert {t["kimlik"] for t in KURAL_TANIMLARI} == set(kayit_defteri.tum_kimlikler())


def test_agirlik_guncellemesi_aktiflik_bayragina_dokunmaz() -> None:
    """Guncelleme kismidir: gonderilmeyen alan degismez.

    S1'in agirligini dusurmek tam da kullanicinin yapacagi sey (bkz. S1
    baskinlik uyarisi); bunun yan etkisiyle kuralin PASIFLESMESI, canlida
    gorulen duruma giden en olasi sessiz yol olurdu.
    """
    from app.schemas.kural import KuralGuncelle

    alanlar = KuralGuncelle(agirlik=5).model_dump(exclude_unset=True)
    assert alanlar == {"agirlik": 5}
    assert "aktif" not in alanlar


def test_parametre_guncellemesi_aktiflik_bayragina_dokunmaz() -> None:
    from app.schemas.kural import KuralGuncelle

    alanlar = KuralGuncelle(parametreler={"asgari_dinlenme_saati": 16}).model_dump(
        exclude_unset=True
    )
    assert set(alanlar) == {"parametreler"}
