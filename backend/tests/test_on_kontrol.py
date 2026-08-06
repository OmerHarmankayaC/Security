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
from app.services.on_kontrol import BulguTipi, on_kontrol_yap

GECE, GUNDUZ, AKSAM = 1, 2, 3
KAPI, KONTROL_ODASI = 1, 2
GUVENLIK_GOREVI = 1

_AZAMI_HAFTALIK_SAAT = Decimal(45)
_HAFTALIK_ASGARI_IZIN_GUNU = 1


def _vardiya_tipleri() -> dict[int, VardiyaTipiBilgisi]:
    return {
        GECE: VardiyaTipiBilgisi(GECE, time(0, 0), time(8, 0), 8, True),
        GUNDUZ: VardiyaTipiBilgisi(GUNDUZ, time(8, 0), time(16, 0), 8, False),
        AKSAM: VardiyaTipiBilgisi(AKSAM, time(16, 0), time(0, 0), 8, False),
    }


def _gunler(n: int, baslangic: date = date(2026, 2, 2)) -> list[date]:
    return [baslangic + timedelta(days=i) for i in range(n)]


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
        talep={(g, GUNDUZ, KAPI): 1 for g in gunler},
    )
    bulgular = on_kontrol_yap(
        baglam,
        gunler,
        azami_haftalik_saat=_AZAMI_HAFTALIK_SAAT,
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
        talep=talep,
    )
    bulgular = on_kontrol_yap(
        baglam,
        gunler,
        azami_haftalik_saat=_AZAMI_HAFTALIK_SAAT,
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
        talep=talep,
    )
    bulgular = on_kontrol_yap(
        baglam,
        gunler,
        azami_haftalik_saat=_AZAMI_HAFTALIK_SAAT,
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
        talep=talep,
    )
    bulgular = on_kontrol_yap(
        baglam,
        gunler,
        azami_haftalik_saat=_AZAMI_HAFTALIK_SAAT,
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
        talep=talep,
    )
    bulgular = on_kontrol_yap(
        baglam,
        gunler,
        azami_haftalik_saat=_AZAMI_HAFTALIK_SAAT,
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
        talep=talep,
    )
    bulgular = on_kontrol_yap(
        baglam,
        gunler,
        azami_haftalik_saat=_AZAMI_HAFTALIK_SAAT,
        haftalik_asgari_izin_gunu=_HAFTALIK_ASGARI_IZIN_GUNU,
    )
    ilgili = [b for b in bulgular if b.tip == BulguTipi.NOKTA_ICIN_UYGUN_PERSONEL_YOK]
    assert len(ilgili) == 1
    assert ilgili[0].tarih == gun
    assert ilgili[0].nokta_id == KAPI
