"""SDD 5.2 on_kontrol() testleri: dort kontrolun her biri icin elle kurulan
ornekler. Veritabani gerektirmez."""

from datetime import date, time, timedelta
from decimal import Decimal

from app.kurallar.baglam import (
    Baglam,
    GorevNoktasiBilgisi,
    MusaitlikKaydi,
    PersonelBilgisi,
    VardiyaTipiBilgisi,
)
from app.models.girdi import MusaitlikDilimi
from app.services.on_kontrol import (
    Bulgu,
    BulguTipi,
    kapsama_kurali_bulgusu,
    kesin_bulgular,
    on_kontrol_yap,
)
from tests.conftest import blok_talebini_saate_ac

GECE, GUNDUZ, AKSAM = 1, 2, 3
KAPI, KONTROL_ODASI = 1, 2
GUVENLIK_GOREVI = 1

# Kapasite hesabi artik FAZLA CALISMA ESIGINDEN gecer (SRS 3.3.6): H5'in
# mutlak tavani (66) surdurulebilir tempo degil, asilamayan sinirdir.
_FAZLA_CALISMA_ESIGI = Decimal(45)
_AZAMI_GUNLUK_SAAT = Decimal(11)
_HAFTALIK_ASGARI_IZIN_GUNU = 1


def _vardiya_tipleri() -> dict[int, VardiyaTipiBilgisi]:
    return {
        GECE: VardiyaTipiBilgisi(GECE, time(0, 0), time(8, 0), 8, True),
        GUNDUZ: VardiyaTipiBilgisi(GUNDUZ, time(8, 0), time(16, 0), 8, False),
        AKSAM: VardiyaTipiBilgisi(AKSAM, time(16, 0), time(0, 0), 8, False),
    }


def _gunler(n: int, baslangic: date = date(2026, 2, 2)) -> list[date]:
    return [baslangic + timedelta(days=i) for i in range(n)]


def _bos_baglam() -> Baglam:
    return Baglam(
        vardiya_tipleri=_vardiya_tipleri(),
        gorev_noktalari={KAPI: GorevNoktasiBilgisi(KAPI, onkosul_yetkinlik_id=GUVENLIK_GOREVI)},
        personel={},
        talep_saat=blok_talebini_saate_ac({}, _vardiya_tipleri()),
    )


def test_bulgu_yoksa_bos_liste_doner() -> None:
    gunler = _gunler(7)
    personel = {
        p: PersonelBilgisi(p, date(2026, 1, 1), None, frozenset({GUVENLIK_GOREVI}))
        for p in range(1, 6)
    }
    baglam = Baglam(
        vardiya_tipleri=_vardiya_tipleri(),
        gorev_noktalari={KAPI: GorevNoktasiBilgisi(KAPI, onkosul_yetkinlik_id=GUVENLIK_GOREVI)},
        personel=personel,
        talep_saat=blok_talebini_saate_ac(
            {(g, GUNDUZ, KAPI): 1 for g in gunler}, _vardiya_tipleri()
        ),
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
    talep = {(g, v, KAPI): 1 for g in gunler for v in (GECE, GUNDUZ, AKSAM)}
    baglam = Baglam(
        vardiya_tipleri=_vardiya_tipleri(),
        gorev_noktalari={KAPI: GorevNoktasiBilgisi(KAPI, onkosul_yetkinlik_id=GUVENLIK_GOREVI)},
        personel=personel,
        talep_saat=blok_talebini_saate_ac(talep, _vardiya_tipleri()),
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
    talep = {(g, GUNDUZ, KONTROL_ODASI): 1 for g in gunler}
    baglam = Baglam(
        vardiya_tipleri=_vardiya_tipleri(),
        gorev_noktalari={
            KONTROL_ODASI: GorevNoktasiBilgisi(KONTROL_ODASI, onkosul_yetkinlik_id=GUVENLIK_GOREVI)
        },
        personel=personel,
        talep_saat=blok_talebini_saate_ac(talep, _vardiya_tipleri()),
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
    talep = {(g, v, KAPI): 1 for g in gunler for v in (GECE, GUNDUZ, AKSAM)}
    baglam = Baglam(
        vardiya_tipleri=_vardiya_tipleri(),
        gorev_noktalari={KAPI: GorevNoktasiBilgisi(KAPI, onkosul_yetkinlik_id=GUVENLIK_GOREVI)},
        personel=personel,
        musaitlik=musaitlik,
        talep_saat=blok_talebini_saate_ac(talep, _vardiya_tipleri()),
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
    talep = {(gun, GUNDUZ, KAPI): 3}
    baglam = Baglam(
        vardiya_tipleri=_vardiya_tipleri(),
        gorev_noktalari={KAPI: GorevNoktasiBilgisi(KAPI, onkosul_yetkinlik_id=GUVENLIK_GOREVI)},
        personel=personel,
        musaitlik=musaitlik,
        talep_saat=blok_talebini_saate_ac(talep, _vardiya_tipleri()),
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
    talep = {(gun, GUNDUZ, KAPI): 1}
    baglam = Baglam(
        vardiya_tipleri=_vardiya_tipleri(),
        gorev_noktalari={KAPI: GorevNoktasiBilgisi(KAPI, onkosul_yetkinlik_id=GUVENLIK_GOREVI)},
        personel=personel,
        talep_saat=blok_talebini_saate_ac(talep, _vardiya_tipleri()),
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
