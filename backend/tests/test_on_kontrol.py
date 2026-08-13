"""SDD 5.2 on_kontrol() testleri: dort kontrolun her biri icin elle kurulan
ornekler. Veritabani gerektirmez."""

from datetime import date, timedelta
from decimal import Decimal

from app.kurallar.baglam import (
    Baglam,
    GorevNoktasiBilgisi,
    MusaitlikKaydi,
    PersonelBilgisi,
)
from app.models.girdi import MusaitlikDilimi
from app.services.on_kontrol import (
    Bulgu,
    BulguTipi,
    kapsama_kurali_bulgusu,
    kesin_bulgular,
    on_kontrol_yap,
)
from tests.conftest import saatlik_talep

# Talep araliklari (blok degil, ZAMAN ARALIGI): (baslangic, bitis).
GECE, GUNDUZ, AKSAM = (0, 8), (8, 16), (16, 24)
KAPI, KONTROL_ODASI = 1, 2
GUVENLIK_GOREVI = 1

# Kapasite hesabi artik FAZLA CALISMA ESIGINDEN gecer (SRS 3.3.6): H5'in
# mutlak tavani (66) surdurulebilir tempo degil, asilamayan sinirdir.
_FAZLA_CALISMA_ESIGI = Decimal(45)
_AZAMI_GUNLUK_SAAT = Decimal(11)
_HAFTALIK_ASGARI_IZIN_GUNU = 1


def _gunler(n: int, baslangic: date = date(2026, 2, 2)) -> list[date]:
    return [baslangic + timedelta(days=i) for i in range(n)]


def _bos_baglam() -> Baglam:
    return Baglam(
        gorev_noktalari={KAPI: GorevNoktasiBilgisi(KAPI, onkosul_yetkinlik_id=GUVENLIK_GOREVI)},
        personel={},
        talep_saat={},
    )


def test_bulgu_yoksa_bos_liste_doner() -> None:
    gunler = _gunler(7)
    personel = {
        p: PersonelBilgisi(p, date(2026, 1, 1), None, frozenset({GUVENLIK_GOREVI}))
        for p in range(1, 6)
    }
    baglam = Baglam(
        gorev_noktalari={KAPI: GorevNoktasiBilgisi(KAPI, onkosul_yetkinlik_id=GUVENLIK_GOREVI)},
        personel=personel,
        talep_saat=saatlik_talep(gunler, [(*GUNDUZ, KAPI, 1)]),
    )
    bulgular = on_kontrol_yap(
        baglam,
        gunler,
        fazla_calisma_esigi=_FAZLA_CALISMA_ESIGI,
        azami_gunluk_saat=_AZAMI_GUNLUK_SAAT,
        haftalik_asgari_izin_gunu=_HAFTALIK_ASGARI_IZIN_GUNU,
    )
    assert bulgular == []


def test_donem_kapasitesi_yetersiz_talep_kadroyu_asinca() -> None:
    gunler = _gunler(7)
    # Tek personel, her gunun her vardiyasinda KAPI'da 1 kisi talebi: 21 vardiya/hafta
    # istiyor ama bir kisi haftada en fazla ~5 vardiya tutabiliyor.
    personel = {1: PersonelBilgisi(1, date(2026, 1, 1), None, frozenset({GUVENLIK_GOREVI}))}
    talep = saatlik_talep(gunler, [(0, 0, KAPI, 1)])  # gun boyu bir kisi
    baglam = Baglam(
        gorev_noktalari={KAPI: GorevNoktasiBilgisi(KAPI, onkosul_yetkinlik_id=GUVENLIK_GOREVI)},
        personel=personel,
        talep_saat=talep,
    )
    bulgular = on_kontrol_yap(
        baglam,
        gunler,
        fazla_calisma_esigi=_FAZLA_CALISMA_ESIGI,
        azami_gunluk_saat=_AZAMI_GUNLUK_SAAT,
        haftalik_asgari_izin_gunu=_HAFTALIK_ASGARI_IZIN_GUNU,
    )
    assert any(b.tip == BulguTipi.DONEM_KAPASITESI_YETERSIZ for b in bulgular)


def test_yetkinlik_havuzu_yetersiz_havuz_kucukken() -> None:
    gunler = _gunler(7)
    # Kontrol Odasi'nin onkosulu var ama hicbir personel bu yetkinlige sahip degil.
    personel = {1: PersonelBilgisi(1, date(2026, 1, 1), None, frozenset())}
    talep = saatlik_talep(gunler, [(*GUNDUZ, KONTROL_ODASI, 1)])
    baglam = Baglam(
        gorev_noktalari={
            KONTROL_ODASI: GorevNoktasiBilgisi(KONTROL_ODASI, onkosul_yetkinlik_id=GUVENLIK_GOREVI)
        },
        personel=personel,
        talep_saat=talep,
    )
    bulgular = on_kontrol_yap(
        baglam,
        gunler,
        fazla_calisma_esigi=_FAZLA_CALISMA_ESIGI,
        azami_gunluk_saat=_AZAMI_GUNLUK_SAAT,
        haftalik_asgari_izin_gunu=_HAFTALIK_ASGARI_IZIN_GUNU,
    )
    ilgili = [b for b in bulgular if b.tip == BulguTipi.YETKINLIK_HAVUZU_YETERSIZ]
    assert len(ilgili) == 1
    assert ilgili[0].yetkinlik_id == GUVENLIK_GOREVI


def test_yetkinlik_havuzu_kontrolu_bireysel_izni_hesaba_katar() -> None:
    """SDD 5.2 surum 1.2: havuz teorik olarak yeterli gorunse de, izinli kisilerin
    musait_gun'u dusuruldugunde acik ortaya cikmali (Kontrol 1'deki gibi)."""
    gunler = _gunler(7)
    # 2 kisilik havuz; biri butun donem boyunca izinli.
    personel = {
        1: PersonelBilgisi(1, date(2026, 1, 1), None, frozenset({GUVENLIK_GOREVI})),
        2: PersonelBilgisi(2, date(2026, 1, 1), None, frozenset({GUVENLIK_GOREVI})),
    }
    musaitlik = [MusaitlikKaydi(2, gunler[0], gunler[-1], MusaitlikDilimi.TAM_GUN)]
    # Talep, tek kisinin haftalik kapasitesinin (azami_haftalik_saat/vardiya suresi ~5) acikca
    # ustunde: her gun uc vardiyada da KAPI'da 1 kisi - haftada 21 vardiya.
    talep = saatlik_talep(gunler, [(0, 0, KAPI, 1)])  # gun boyu bir kisi
    baglam = Baglam(
        gorev_noktalari={KAPI: GorevNoktasiBilgisi(KAPI, onkosul_yetkinlik_id=GUVENLIK_GOREVI)},
        personel=personel,
        musaitlik=musaitlik,
        talep_saat=talep,
    )
    bulgular = on_kontrol_yap(
        baglam,
        gunler,
        fazla_calisma_esigi=_FAZLA_CALISMA_ESIGI,
        azami_gunluk_saat=_AZAMI_GUNLUK_SAAT,
        haftalik_asgari_izin_gunu=_HAFTALIK_ASGARI_IZIN_GUNU,
    )
    ilgili = [b for b in bulgular if b.tip == BulguTipi.YETKINLIK_HAVUZU_YETERSIZ]
    assert len(ilgili) == 1
    assert ilgili[0].yetkinlik_id == GUVENLIK_GOREVI


def test_gunluk_personel_yetersiz_coğu_izinliyken() -> None:
    gunler = _gunler(1)
    gun = gunler[0]
    # 3 personel, ama ikisi o gun tam gun izinli; talep gunde 3 kisi.
    personel = {
        p: PersonelBilgisi(p, date(2026, 1, 1), None, frozenset({GUVENLIK_GOREVI}))
        for p in (1, 2, 3)
    }
    musaitlik = [
        MusaitlikKaydi(1, gun, gun, MusaitlikDilimi.TAM_GUN),
        MusaitlikKaydi(2, gun, gun, MusaitlikDilimi.TAM_GUN),
    ]
    talep = saatlik_talep([gun], [(*GUNDUZ, KAPI, 3)])
    baglam = Baglam(
        gorev_noktalari={KAPI: GorevNoktasiBilgisi(KAPI, onkosul_yetkinlik_id=GUVENLIK_GOREVI)},
        personel=personel,
        musaitlik=musaitlik,
        talep_saat=talep,
    )
    bulgular = on_kontrol_yap(
        baglam,
        gunler,
        fazla_calisma_esigi=_FAZLA_CALISMA_ESIGI,
        azami_gunluk_saat=_AZAMI_GUNLUK_SAAT,
        haftalik_asgari_izin_gunu=_HAFTALIK_ASGARI_IZIN_GUNU,
    )
    ilgili = [b for b in bulgular if b.tip == BulguTipi.GUNLUK_PERSONEL_YETERSIZ]
    assert len(ilgili) == 1
    assert ilgili[0].tarih == gun
    assert ilgili[0].eksik == 2


def test_nokta_icin_uygun_personel_yok_yetkinlik_eksikken() -> None:
    gunler = _gunler(1)
    gun = gunler[0]
    personel = {1: PersonelBilgisi(1, date(2026, 1, 1), None, frozenset())}  # yetkinliksiz
    talep = saatlik_talep([gun], [(*GUNDUZ, KAPI, 1)])
    baglam = Baglam(
        gorev_noktalari={KAPI: GorevNoktasiBilgisi(KAPI, onkosul_yetkinlik_id=GUVENLIK_GOREVI)},
        personel=personel,
        talep_saat=talep,
    )
    bulgular = on_kontrol_yap(
        baglam,
        gunler,
        fazla_calisma_esigi=_FAZLA_CALISMA_ESIGI,
        azami_gunluk_saat=_AZAMI_GUNLUK_SAAT,
        haftalik_asgari_izin_gunu=_HAFTALIK_ASGARI_IZIN_GUNU,
    )
    ilgili = [b for b in bulgular if b.tip == BulguTipi.NOKTA_ICIN_UYGUN_PERSONEL_YOK]
    assert len(ilgili) == 1
    assert ilgili[0].tarih == gun
    assert ilgili[0].nokta_id == KAPI


# --- S1 pasifken uyari (madde: aktiflik anahtarinin sessiz kalmamasi) -------


def test_s1_aktifken_yapilandirma_uyarisi_yok() -> None:
    assert kapsama_kurali_bulgusu(frozenset({"S1", "S2"})) is None


def test_s1_pasifken_uyari_uretilir() -> None:
    bulgu = kapsama_kurali_bulgusu(frozenset({"S2", "S3"}))
    assert bulgu is not None
    assert bulgu.tip is BulguTipi.KAPSAMA_KURALI_PASIF


def test_s1_uyarisi_cozumu_durdurmaz() -> None:
    """Pasiflestirme kullanicinin bilincli ayari olabilir; sistem onun yerine
    karar vermez. Yapisal engellerden ayiran alan bu."""
    bulgu = kapsama_kurali_bulgusu(frozenset())
    assert bulgu is not None
    assert bulgu.kesin_mi is False
    assert kesin_bulgular([bulgu]) == []


def test_yapisal_engeller_cozumu_durdurmaya_devam_eder() -> None:
    engel = Bulgu(tip=BulguTipi.DONEM_KAPASITESI_YETERSIZ, aciklama="x", eksik=3)
    assert engel.kesin_mi is True
    assert kesin_bulgular([engel, kapsama_kurali_bulgusu(frozenset())]) == [engel]


def test_s1_uyarisi_uc_sonucu_da_soyler() -> None:
    """Metin kullaniciya dogrudan gosterilir. Uc sonucun ucu de yazili olmali;
    ozellikle ucuncusu, cunku digerleri cizelgeye bakinca gorulur ama o
    sistemin KENDI raporunu yanlislastirir."""
    metin = kapsama_kurali_bulgusu(frozenset()).aciklama
    assert "boş" in metin, "bos cizelge ihtimali yazilmali"
    assert "üzerinde personel" in metin, "ust sinirin kalkmasi yazilmali"
    assert "0 açık" in metin, "kapsama raporunun yanlislasmasi yazilmali"
    # Ne yapilacagi da soylenmeli, yalnizca sorun degil (NFR-5).
    assert "S1'i etkinleştirin" in metin


def test_donem_gunu_yokken_de_uyari_kaybolmaz() -> None:
    """Erken cikis yolu uyariyi yutmamali."""
    bulgular = on_kontrol_yap(
        _bos_baglam(),
        [],
        fazla_calisma_esigi=Decimal(45),
        azami_gunluk_saat=Decimal(11),
        haftalik_asgari_izin_gunu=1,
        aktif_kural_kimlikleri=frozenset(),
    )
    assert [b.tip for b in bulgular] == [BulguTipi.KAPSAMA_KURALI_PASIF]


def test_varsayilan_cagri_yapilandirma_uyarisi_uretmez() -> None:
    """Kadro aritmetigini elle kuran cagiranlar (testler) kural katalogundan
    habersizdir; varsayilan onlari uyarmamali."""
    bulgular = on_kontrol_yap(
        _bos_baglam(),
        [],
        fazla_calisma_esigi=Decimal(45),
        azami_gunluk_saat=Decimal(11),
        haftalik_asgari_izin_gunu=1,
    )
    assert bulgular == []


# --- Kota bulgulari (SDD 5.2, Tur 4 Is 8) -----------------------------------


def _kota_baglami(devir: float) -> Baglam:
    """Tek personelli, talebi karsilanabilir bir baglam.

    Kota bulgulari kadro aritmetigine bakmaz; digerlerinin susmasi icin
    talep bilincli olarak kucuk tutuldu.
    """
    gunler = _gunler(7)
    return Baglam(
        gorev_noktalari={KAPI: GorevNoktasiBilgisi(KAPI, onkosul_yetkinlik_id=None)},
        personel={
            1: PersonelBilgisi(
                1,
                date(2026, 1, 1),
                None,
                frozenset(),
                devir_fazla_calisma_saat=devir,
            )
        },
        personel_adlari={1: "Ayşe Yılmaz"},
        talep_saat=saatlik_talep([gunler[0]], [(*GUNDUZ, KAPI, 1)]),
        donem_baslangic=gunler[0],
        donem_bitis=gunler[-1],
    )


def _kota_bulgulari(devir: float) -> list:
    return [
        b
        for b in on_kontrol_yap(
            _kota_baglami(devir),
            _gunler(7),
            fazla_calisma_esigi=_FAZLA_CALISMA_ESIGI,
            azami_gunluk_saat=_AZAMI_GUNLUK_SAAT,
            haftalik_asgari_izin_gunu=_HAFTALIK_ASGARI_IZIN_GUNU,
            yillik_fazla_kotasi=Decimal(270),
        )
        if b.tip in (BulguTipi.DEVIR_KOTAYI_ASMIS, BulguTipi.KOTASI_DOLMUS_PERSONEL)
    ]


def test_devir_kotayi_asmissa_veri_hatasi_bildirilir() -> None:
    """`devir[p] > yillik_fazla_kotasi` H10'u TEK BASINA cozulemez kilar.

    Kisit `devir + Σ fazla <= kota` ve `fazla >= 0`; devir kotayi asmissa
    hicbir atama bunu saglayamaz. Cozucunun "model cozulemez" demesi
    kullaniciya HANGI personelin hangi alaninin yanlis oldugunu soylemez -
    bu yuzden on kontrolde bildirilir (FR-5.1).
    """
    bulgular = _kota_bulgulari(devir=300.0)
    assert [b.tip for b in bulgular] == [BulguTipi.DEVIR_KOTAYI_ASMIS]
    assert bulgular[0].personel_id == 1
    # K20: metin kimlik degil AD tasir.
    assert "Ayşe Yılmaz" in bulgular[0].aciklama
    assert bulgular[0].eksik == 30


def test_kotasi_dolmus_personel_uyari_uretir() -> None:
    """Kalan kotasi bir haftalik fazla calismaya yetmeyen personel fazla
    calismaya atanamaz; kadro hesabi bunu bilmeden yapildiginda acigin
    NEDENI gorunmez kalir."""
    bulgular = _kota_bulgulari(devir=260.0)
    assert [b.tip for b in bulgular] == [BulguTipi.KOTASI_DOLMUS_PERSONEL]
    assert bulgular[0].kesin_mi is False  # uyari, kesin bulgu degil
    assert "10 saat kaldı" in bulgular[0].aciklama


def test_kotasi_bol_personel_bulgu_uretmez() -> None:
    assert _kota_bulgulari(devir=0.0) == []


def test_kota_bulgulari_cozumu_engellemez() -> None:
    """K18: hicbir bulgu isi dusurmez; ikisi de TESHIS uretir, karar vermez."""
    from app.services.on_kontrol import kesin_bulgular

    bulgular = _kota_bulgulari(devir=300.0)
    # Kesin bulgu olmasi "cozum baslamasin" demek DEGILDIR - ayrimin tek
    # anlami kullaniciya nasil gosterildigidir (SDD 5.2).
    assert kesin_bulgular(bulgular) == bulgular
