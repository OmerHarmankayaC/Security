"""H1-H10 dogrula testleri: elle kurulan ornek blok listeleriyle.

Bu testler veritabani gerektirmez; Baglam ve AtamaKaydi elle olusturulur.

TUR 5'TE BEKLENEN DEGERLER NEDEN DEGISTI. Calisma zamani artik bir
katalogdan secilmiyor; blok bir ZAMAN ARALIGIDIR ve testler "GUNDUZ blogu"
yerine "08.00'de baslayan sekiz saatlik blok" der. Uc kural yeniden
tanimlandi ve bekledikleri sey degisti:

  - **H1** artik yalnizca "gunde tek atama" demiyor: blok kesintisizdir ve
    asgari sureden kisa olamaz. Eski testler korundu, yanlarina asgari sure
    testi eklendi.
  - **H3** gece BLOGU degil gece GUNU sayiyor; bir gun, gece saati
    `gece_esigi_saat` degerine ulasiyorsa gece gunudur (SRS TD-2).
  - **H9** gunluk tavani BLOGA uyguluyor. Duvar saati okumasi 20.00–08.00
    blogunu 4 + 8 saat diye gorur ve on iki saatlik blok tavani asmadan
    gecerdi.
"""

from datetime import date, datetime, time, timedelta

import pytest

from app.kurallar import (
    Baglam,
    GorevNoktasiBilgisi,
    Ihlal,
    MusaitlikKaydi,
    PersonelBilgisi,
    bul,
    kurallari_yukle,
)
from app.kurallar.zorunlu import (
    H1GundeTekKesintisizCalisma,
    H2AsgariDinlenme,
    H3ArdisikGeceUstSiniri,
    H4ArdisikCalismaGunuUstSiniri,
    H5KayanHaftalikSaatTavani,
    H6HaftalikAsgariIzinGunu,
    H7Musaitlik,
    H8OnkosulYetkinligi,
    H9GunlukAzamiSaat,
    H10YillikFazlaCalismaKotasi,
)
from app.models.girdi import MusaitlikDilimi
from tests.conftest import blok

GUVENLIK = 1
SEFLIK = 2

GUVENLIK_GOREVI = 1
VARDIYA_SEFI = 2

_PZT = date(2026, 2, 2)  # pazartesi
_BIR_GUN = date(2026, 1, 5)


@pytest.fixture
def baglam() -> Baglam:
    gorev_noktalari = {
        GUVENLIK: GorevNoktasiBilgisi(GUVENLIK, onkosul_yetkinlik_id=None),
        SEFLIK: GorevNoktasiBilgisi(SEFLIK, onkosul_yetkinlik_id=VARDIYA_SEFI),
    }
    personel = {
        1: PersonelBilgisi(1, date(2026, 1, 1), None, frozenset({GUVENLIK_GOREVI, VARDIYA_SEFI})),
        2: PersonelBilgisi(2, date(2026, 1, 1), None, frozenset({GUVENLIK_GOREVI})),
    }
    return Baglam(gorev_noktalari=gorev_noktalari, personel=personel)


# --- H1 --------------------------------------------------------------------


def test_h1_ayni_gune_iki_blok_ihlal_verir(baglam: Baglam) -> None:
    kural = H1GundeTekKesintisizCalisma(parametreler={"asgari_blok_saat": 4})
    atamalar = [
        blok(1, _BIR_GUN, 8, 8, GUVENLIK),
        blok(1, _BIR_GUN, 16, 8, GUVENLIK),
    ]
    ihlaller = kural.dogrula(atamalar, baglam)
    assert [i.kural_kimlik for i in ihlaller] == ["H1"]
    assert "2 blok" in ihlaller[0].aciklama


def test_h1_farkli_gunlerde_blok_ihlal_vermez(baglam: Baglam) -> None:
    kural = H1GundeTekKesintisizCalisma(parametreler={"asgari_blok_saat": 4})
    atamalar = [
        blok(1, _BIR_GUN, 8, 8, GUVENLIK),
        blok(1, _BIR_GUN + timedelta(days=1), 8, 8, GUVENLIK),
    ]
    assert kural.dogrula(atamalar, baglam) == []


def test_h1_asgari_sureden_kisa_blok_ihlal_verir(baglam: Baglam) -> None:
    """Kuralin YENI yarisi: saat modeli kisitlanmazsa tek saatlik bloklar
    uretebilir ve bunun sahada karsiligi yoktur (SRS 3.3.1)."""
    kural = H1GundeTekKesintisizCalisma(parametreler={"asgari_blok_saat": 4})
    ihlaller = kural.dogrula([blok(1, _BIR_GUN, 8, 2, GUVENLIK)], baglam)
    assert [i.kural_kimlik for i in ihlaller] == ["H1"]
    assert "asgari 4 saat" in ihlaller[0].aciklama


def test_h1_gece_yarisini_asan_blok_tek_blok_sayilir(baglam: Baglam) -> None:
    """TD-1: tasan saatler yeni bir baslangic uretmez, blok basladigi gune yazilir."""
    kural = H1GundeTekKesintisizCalisma(parametreler={"asgari_blok_saat": 4})
    assert kural.dogrula([blok(1, _BIR_GUN, 20, 10, GUVENLIK)], baglam) == []


# --- H2 --------------------------------------------------------------------


def test_h2_yetersiz_dinlenme_ihlal_verir(baglam: Baglam) -> None:
    kural = H2AsgariDinlenme(parametreler={"asgari_dinlenme_saati": 16})
    atamalar = [
        blok(1, _BIR_GUN, 16, 8, GUVENLIK),  # biter: ertesi gun 00.00
        blok(1, _BIR_GUN + timedelta(days=1), 8, 8, GUVENLIK),  # 8 saat ara
    ]
    ihlaller = kural.dogrula(atamalar, baglam)
    assert [i.kural_kimlik for i in ihlaller] == ["H2"]


def test_h2_yeterli_dinlenme_ihlal_vermez(baglam: Baglam) -> None:
    kural = H2AsgariDinlenme(parametreler={"asgari_dinlenme_saati": 16})
    atamalar = [
        blok(1, _BIR_GUN, 0, 8, GUVENLIK),  # biter: 05 08.00
        blok(1, _BIR_GUN + timedelta(days=1), 16, 8, GUVENLIK),  # baslar: 06 16.00
    ]
    assert kural.dogrula(atamalar, baglam) == []


# --- H3 --------------------------------------------------------------------


def test_h3_dort_ardisik_gece_gunu_ihlal_verir(baglam: Baglam) -> None:
    kural = H3ArdisikGeceUstSiniri(parametreler={"azami_ardisik_gece": 3, "gece_esigi_saat": 4})
    # 00.00–08.00: sekiz saatin altisi gece penceresinde (00–06).
    atamalar = [blok(1, _BIR_GUN + timedelta(days=i), 0, 8, GUVENLIK) for i in range(4)]
    ihlaller = kural.dogrula(atamalar, baglam)
    assert [i.kural_kimlik for i in ihlaller] == ["H3"]
    assert ihlaller[0].tarih == _BIR_GUN + timedelta(days=3)


def test_h3_uc_ardisik_gece_gunu_ihlal_vermez(baglam: Baglam) -> None:
    kural = H3ArdisikGeceUstSiniri(parametreler={"azami_ardisik_gece": 3, "gece_esigi_saat": 4})
    atamalar = [blok(1, _BIR_GUN + timedelta(days=i), 0, 8, GUVENLIK) for i in range(3)]
    assert kural.dogrula(atamalar, baglam) == []


def test_h3_esigin_altinda_gece_saati_gece_gunu_saymaz(baglam: Baglam) -> None:
    """SRS TD-2'nin ergonomik yorumu: iki saat gece calismak bir gece nobeti degildir.

    04.00–12.00 blogunun yalnizca iki saati (04, 05) gece penceresindedir;
    esik dort saat oldugu icin bu gunler gece gunu SAYILMAZ ve dort ardisik
    gun bile ihlal uretmez. Eski kural gece BAYRAGINA bakiyordu ve bayrak
    blok tanimlanirken elle isaretlendigi icin bu ayrimi yapamiyordu.
    """
    kural = H3ArdisikGeceUstSiniri(parametreler={"azami_ardisik_gece": 3, "gece_esigi_saat": 4})
    atamalar = [blok(1, _BIR_GUN + timedelta(days=i), 4, 8, GUVENLIK) for i in range(4)]
    assert kural.dogrula(atamalar, baglam) == []


def test_h3_gece_saati_blogun_basladigi_gune_yazilir(baglam: Baglam) -> None:
    """TD-1: 20.00–06.00 blogunun on gece saatinin TAMAMI baslangic gunundedir.

    Duvar saatine yazilsaydi ayni blok iki ayri gunu gece gunu yapar ve iki
    ardisik gece blogu dort gece gunu gibi gorunurdu.
    """
    kural = H3ArdisikGeceUstSiniri(parametreler={"azami_ardisik_gece": 3, "gece_esigi_saat": 4})
    atamalar = [blok(1, _BIR_GUN + timedelta(days=i), 20, 10, GUVENLIK) for i in range(3)]
    assert kural.dogrula(atamalar, baglam) == []


# --- H4, H5, H6 ------------------------------------------------------------


def test_h4_yedi_ardisik_gun_ihlal_verir(baglam: Baglam) -> None:
    kural = H4ArdisikCalismaGunuUstSiniri(parametreler={"azami_ardisik_calisma_gunu": 6})
    atamalar = [blok(1, _BIR_GUN + timedelta(days=i), 8, 8, GUVENLIK) for i in range(7)]
    ihlaller = kural.dogrula(atamalar, baglam)
    assert [i.kural_kimlik for i in ihlaller] == ["H4"]


def test_h4_alti_ardisik_gun_ihlal_vermez(baglam: Baglam) -> None:
    kural = H4ArdisikCalismaGunuUstSiniri(parametreler={"azami_ardisik_calisma_gunu": 6})
    atamalar = [blok(1, _BIR_GUN + timedelta(days=i), 8, 8, GUVENLIK) for i in range(6)]
    assert kural.dogrula(atamalar, baglam) == []


def test_h5_haftalik_saat_tavani_asilinca_ihlal_verir(baglam: Baglam) -> None:
    kural = H5KayanHaftalikSaatTavani(parametreler={"haftalik_mutlak_tavan": 45})
    # 6 gun x 8 saat = 48 saat, 7 gunluk pencerede tavani (45) asar.
    atamalar = [blok(1, _BIR_GUN + timedelta(days=i), 8, 8, GUVENLIK) for i in range(6)]
    ihlaller = kural.dogrula(atamalar, baglam)
    assert [i.kural_kimlik for i in ihlaller] == ["H5"]


def test_h5_tavan_altinda_ihlal_vermez(baglam: Baglam) -> None:
    kural = H5KayanHaftalikSaatTavani(parametreler={"haftalik_mutlak_tavan": 45})
    atamalar = [blok(1, _BIR_GUN + timedelta(days=i), 8, 8, GUVENLIK) for i in range(5)]
    assert kural.dogrula(atamalar, baglam) == []


def test_h6_yedi_gun_ust_uste_calisinca_ihlal_verir(baglam: Baglam) -> None:
    kural = H6HaftalikAsgariIzinGunu(parametreler={"haftalik_asgari_izin_gunu": 1})
    atamalar = [blok(1, _BIR_GUN + timedelta(days=i), 8, 8, GUVENLIK) for i in range(7)]
    ihlaller = kural.dogrula(atamalar, baglam)
    assert [i.kural_kimlik for i in ihlaller] == ["H6"]


def test_h6_haftada_bir_izin_gunuyle_ihlal_vermez(baglam: Baglam) -> None:
    kural = H6HaftalikAsgariIzinGunu(parametreler={"haftalik_asgari_izin_gunu": 1})
    atamalar = [blok(1, _BIR_GUN + timedelta(days=i), 8, 8, GUVENLIK) for i in range(7) if i != 5]
    assert kural.dogrula(atamalar, baglam) == []


# --- H7, H8 ----------------------------------------------------------------


def test_h7_izinli_gunde_atama_ihlal_verir(baglam: Baglam) -> None:
    kural = H7Musaitlik(parametreler={})
    baglam.musaitlik.append(MusaitlikKaydi(1, _BIR_GUN, _BIR_GUN, MusaitlikDilimi.TAM_GUN))
    ihlaller = kural.dogrula([blok(1, _BIR_GUN, 8, 8, GUVENLIK)], baglam)
    assert [i.kural_kimlik for i in ihlaller] == ["H7"]


def test_h7_ogleden_once_izinli_personel_aksam_calisabilir(baglam: Baglam) -> None:
    """Musaitlik artik SAAT DILIMIYLE kesisiyor mu diye soruluyor.

    Blok ekseninde soru "bu blok o dilimle kesisiyor mu" idi ve ayni yaniti
    veriyordu; saat ekseninde ayni tanimin daha ince bir sonucu var: ogleden
    once izinli bir personel 16.00'da baslayan bloga atanabilir.
    """
    kural = H7Musaitlik(parametreler={})
    baglam.musaitlik.append(MusaitlikKaydi(1, _BIR_GUN, _BIR_GUN, MusaitlikDilimi.OGLEDEN_ONCE))
    assert kural.dogrula([blok(1, _BIR_GUN, 16, 8, GUVENLIK)], baglam) == []
    assert kural.dogrula([blok(1, _BIR_GUN, 8, 8, GUVENLIK)], baglam) != []


def test_h7_aktiflik_araligi_disinda_ihlal_verir(baglam: Baglam) -> None:
    kural = H7Musaitlik(parametreler={})
    ihlaller = kural.dogrula([blok(1, date(2025, 12, 31), 8, 8, GUVENLIK)], baglam)
    assert [i.kural_kimlik for i in ihlaller] == ["H7"]


def test_h7_musait_gunde_ihlal_vermez(baglam: Baglam) -> None:
    kural = H7Musaitlik(parametreler={})
    assert kural.dogrula([blok(1, _BIR_GUN, 8, 8, GUVENLIK)], baglam) == []


def test_h8_yetkinligi_olmayan_personel_ihlal_verir(baglam: Baglam) -> None:
    kural = H8OnkosulYetkinligi(parametreler={})
    ihlaller = kural.dogrula([blok(2, _BIR_GUN, 8, 8, SEFLIK)], baglam)
    assert [i.kural_kimlik for i in ihlaller] == ["H8"]


def test_h8_yetkin_personel_ihlal_vermez(baglam: Baglam) -> None:
    kural = H8OnkosulYetkinligi(parametreler={})
    assert kural.dogrula([blok(1, _BIR_GUN, 8, 8, SEFLIK)], baglam) == []


def test_h8_onkosulsuz_noktada_herkes_calisabilir(baglam: Baglam) -> None:
    kural = H8OnkosulYetkinligi(parametreler={})
    assert kural.dogrula([blok(2, _BIR_GUN, 8, 8, GUVENLIK)], baglam) == []


# --- H9, H10 ---------------------------------------------------------------


def test_h9_gunluk_tavani_asan_blok_ihlal_verir(baglam: Baglam) -> None:
    kural = H9GunlukAzamiSaat(parametreler={"azami_gunluk_saat": 11})
    ihlaller = kural.dogrula([blok(1, _BIR_GUN, 8, 12, GUVENLIK)], baglam)
    assert [i.personel_id for i in ihlaller] == [1]
    assert "tavan 11" in ihlaller[0].aciklama


def test_h9_gece_yarisini_asan_uzun_blok_da_yakalanir(baglam: Baglam) -> None:
    """Duvar saati okumasinin kacirdigi durum.

    20.00–08.00 blogu on iki saattir. Gun basina duvar saati toplanmis
    olsaydi 4 + 8 gorunur, ikisi de on birin altinda kalir ve kural blok
    uzunlugunu hic sinirlamamis olurdu (SRS H9'un metni: "saatler basladigi
    gune sayilir").
    """
    kural = H9GunlukAzamiSaat(parametreler={"azami_gunluk_saat": 11})
    ihlaller = kural.dogrula([blok(1, _BIR_GUN, 20, 12, GUVENLIK)], baglam)
    assert [i.tarih for i in ihlaller] == [_BIR_GUN]


def test_h9_tavanin_altindaki_blok_ihlal_vermez(baglam: Baglam) -> None:
    kural = H9GunlukAzamiSaat(parametreler={"azami_gunluk_saat": 11})
    assert kural.dogrula([blok(1, _BIR_GUN, 8, 8, GUVENLIK)], baglam) == []


def test_h10_kota_asilinca_ihlal_verir(baglam: Baglam) -> None:
    """Fazla calisma TAKVIM HAFTASI uzerinden toplanir (TD-14).

    Pazartesi-pazar arasi alti gun x 12 saat = 72 saat; esik 45 -> 27 saat
    fazla. Kota 20 olunca asilir.
    """
    baglam.donem_baslangic = _PZT
    baglam.donem_bitis = _PZT + timedelta(days=6)
    kural = H10YillikFazlaCalismaKotasi(
        parametreler={"fazla_calisma_esigi": 45, "yillik_fazla_kotasi": 20}
    )
    atamalar = [blok(1, _PZT + timedelta(days=i), 8, 12, GUVENLIK) for i in range(6)]
    ihlaller = kural.dogrula(atamalar, baglam)
    assert [i.personel_id for i in ihlaller] == [1]
    assert "27.0" in ihlaller[0].aciklama


def test_h10_esigin_altinda_kalan_hafta_kotayi_tuketmez(baglam: Baglam) -> None:
    baglam.donem_baslangic = _PZT
    baglam.donem_bitis = _PZT + timedelta(days=6)
    kural = H10YillikFazlaCalismaKotasi(
        parametreler={"fazla_calisma_esigi": 45, "yillik_fazla_kotasi": 20}
    )
    atamalar = [blok(1, _PZT + timedelta(days=i), 8, 8, GUVENLIK) for i in range(5)]
    assert kural.dogrula(atamalar, baglam) == []


def test_h10_devir_bakiyesi_kotaya_eklenir(baglam: Baglam) -> None:
    """`devir[p]` personel kaydindan okunur (TD-6)."""
    baglam.personel[1] = PersonelBilgisi(
        1,
        date(2026, 1, 1),
        None,
        frozenset({GUVENLIK_GOREVI}),
        devir_fazla_calisma_saat=19.0,
    )
    baglam.donem_baslangic = _PZT
    baglam.donem_bitis = _PZT + timedelta(days=6)
    kural = H10YillikFazlaCalismaKotasi(
        parametreler={"fazla_calisma_esigi": 45, "yillik_fazla_kotasi": 20}
    )
    # 4 gun x 12 = 48 saat -> 3 saat fazla; devirle birlikte 22, kota 20.
    atamalar = [blok(1, _PZT + timedelta(days=i), 8, 12, GUVENLIK) for i in range(4)]
    ihlaller = kural.dogrula(atamalar, baglam)
    assert len(ihlaller) == 1
    assert "Devir 19.0" in ihlaller[0].aciklama


def test_h10_kayan_pencere_degil_takvim_haftasi_kullanir(baglam: Baglam) -> None:
    """TD-14'un asil noktasi: kota ORTUSMEYEN pencerelerde anlamlidir."""
    baglam.donem_baslangic = _PZT - timedelta(days=3)
    baglam.donem_bitis = _PZT + timedelta(days=3)
    kural = H10YillikFazlaCalismaKotasi(
        parametreler={"fazla_calisma_esigi": 45, "yillik_fazla_kotasi": 20}
    )
    # Her iki takvim haftasinda 3 x 12 = 36 saat; ikisi de esigin altinda.
    atamalar = [blok(1, _PZT + timedelta(days=i), 8, 12, GUVENLIK) for i in (-3, -2, -1, 0, 1, 2)]
    assert kural.dogrula(atamalar, baglam) == []


# --- modele_ekle tarafi ----------------------------------------------------


def _tek_gunluk_model(baglam: Baglam, gunler: list[date]):  # noqa: ANN202 - test yardimcisi
    """Verilen gunler icin z/bas/devir degiskenlerini kuran kucuk bir model.

    `model_kur`un kendisini cagirir: gosterge degiskenleri kuralin degil
    EKSENIN yapisidir ve elle kurulan bir kopya iki tarafi ayristirirdi.
    """
    from app.cozucu import model_kur

    return model_kur(baglam, gunler, [])


def test_h1_modele_ekle_gunde_iki_blogu_engeller() -> None:
    """H1'in CP-SAT kisiti: ayni gunde iki ayri blok imkansizdir."""
    from ortools.sat.python import cp_model

    gunler = [_BIR_GUN]
    baglam = Baglam(
        gorev_noktalari={GUVENLIK: GorevNoktasiBilgisi(GUVENLIK)},
        personel={1: PersonelBilgisi(1, date(2026, 1, 1), None, frozenset())},
        talep_saat={(_BIR_GUN, saat, GUVENLIK): 1 for saat in range(24)},
        donem_baslangic=_BIR_GUN,
        donem_bitis=_BIR_GUN,
    )
    model, x, baglam, _ = _tek_gunluk_model(baglam, gunler)
    H1GundeTekKesintisizCalisma(parametreler={"asgari_blok_saat": 4}).modele_ekle(model, x, baglam)

    # Sabah dort saat, aksam dort saat: iki ayri baslangic.
    for saat in (8, 9, 10, 11, 18, 19, 20, 21):
        model.add(x[(1, saat, GUVENLIK)] == 1)
    for saat in (12, 13, 14, 15, 16, 17):
        model.add(x[(1, saat, GUVENLIK)] == 0)

    cozucu = cp_model.CpSolver()
    assert cozucu.solve(model) == cp_model.INFEASIBLE


def test_h1_nokta_sabitligi_talep_bitince_de_uygulanir() -> None:
    """DEGISKEN ELEME BU KISITI BIR KEZ SESSIZCE IPTAL ETTI (SDD 5.3).

    Kisit geriye donuk yaziliyor ve `x[p,s,n]` bulunamadiginda atlaniyordu.
    Talebi biten bir noktanin o saatteki degiskeni elendigi icin (talep
    sifirsa degisken uretilmez) kisit hic kurulmuyor ve personel CALISMAYI
    KESMEDEN nokta degistirebiliyordu; cozucu bunu buldu ve uyum testi
    yakaladi.

    Senaryo tam o deseni kurar: A noktasinin talebi 16.00'da biter,
    B noktasininki 16.00'da baslar. Kesintisiz 14.00-20.00 calisip 16.00'da
    nokta degistirmek IMKANSIZ olmalidir.
    """
    from ortools.sat.python import cp_model

    from app.cozucu import model_kur

    nokta_a, nokta_b = 1, 2
    baglam = Baglam(
        gorev_noktalari={
            nokta_a: GorevNoktasiBilgisi(nokta_a),
            nokta_b: GorevNoktasiBilgisi(nokta_b),
        },
        personel={1: PersonelBilgisi(1, date(2026, 1, 1), None, frozenset())},
        talep_saat=(
            {(_BIR_GUN, saat, nokta_a): 1 for saat in range(8, 16)}
            | {(_BIR_GUN, saat, nokta_b): 1 for saat in range(16, 24)}
        ),
        donem_baslangic=_BIR_GUN,
        donem_bitis=_BIR_GUN,
    )
    model, x, baglam, _ = model_kur(baglam, [_BIR_GUN], [])

    # 14.00-16.00 A noktasinda, 16.00-20.00 B noktasinda; arada bosluk yok.
    for saat in (14, 15):
        model.add(x[(1, saat, nokta_a)] == 1)
    for saat in (16, 17, 18, 19):
        model.add(x[(1, saat, nokta_b)] == 1)

    cozucu = cp_model.CpSolver()
    assert cozucu.solve(model) == cp_model.INFEASIBLE, (
        "Blok icinde nokta degisimi mumkun olmamali; kisit talebin bittigi "
        "saatte de uygulanmali."
    )


def test_h1_ara_verip_baska_noktada_calismak_serbesttir() -> None:
    """Yukaridaki kisitin fazla siki OLMADIGININ kontrolu.

    Nokta sabitligi BLOK ICINDE gecerlidir; calisma kesilip yeni bir blok
    baslarsa nokta degisebilir. (H1'in gunde tek baslangic kurali bu ornegi
    ayrica disliyor ama burada H1 modele EKLENMEDI - olculen sey yalnizca
    nokta sabitligi.)
    """
    from ortools.sat.python import cp_model

    from app.cozucu import model_kur

    nokta_a, nokta_b = 1, 2
    baglam = Baglam(
        gorev_noktalari={
            nokta_a: GorevNoktasiBilgisi(nokta_a),
            nokta_b: GorevNoktasiBilgisi(nokta_b),
        },
        personel={1: PersonelBilgisi(1, date(2026, 1, 1), None, frozenset())},
        talep_saat=(
            {(_BIR_GUN, saat, nokta_a): 1 for saat in range(8, 16)}
            | {(_BIR_GUN, saat, nokta_b): 1 for saat in range(16, 24)}
        ),
        donem_baslangic=_BIR_GUN,
        donem_bitis=_BIR_GUN,
    )
    model, x, baglam, _ = model_kur(baglam, [_BIR_GUN], [])

    for saat in (10, 11, 12, 13):
        model.add(x[(1, saat, nokta_a)] == 1)
    model.add(baglam.zv(1, 14) == 0)  # ARA
    model.add(baglam.zv(1, 15) == 0)
    for saat in (16, 17, 18, 19):
        model.add(x[(1, saat, nokta_b)] == 1)

    cozucu = cp_model.CpSolver()
    assert cozucu.solve(model) in (cp_model.OPTIMAL, cp_model.FEASIBLE)


def test_isitma_penceresi_gercekten_sabitlenir() -> None:
    """SDD 5.3: pencere icindeki saatler karar degiskeni DEGIL sabit girdidir.

    Sabitleme atlandiginda cozucu gecmise ait calisma "icat eder" ve bu
    uydurma gecmis H2, H3 ve H4'u besler: donem basindaki dinlenme ve
    ardisiklik kurallari fiilen devre disi kalir. Belirti sessizdir - model
    cozulur, cizelge uretilir, kurallar saglanmis gorunur.
    """
    from ortools.sat.python import cp_model

    from app.cozucu import model_kur

    isitma = _BIR_GUN
    donem = _BIR_GUN + timedelta(days=1)
    baglam = Baglam(
        gorev_noktalari={GUVENLIK: GorevNoktasiBilgisi(GUVENLIK)},
        personel={1: PersonelBilgisi(1, date(2026, 1, 1), None, frozenset())},
        talep_saat={(g, saat, GUVENLIK): 1 for g in (isitma, donem) for saat in range(24)},
        donem_baslangic=donem,
        donem_bitis=donem,
    )
    model, x, baglam, _ = model_kur(
        baglam,
        [isitma, donem],
        [],
        # Gecmiste YALNIZ bu blok var.
        isitma_penceresi_atamalari=[blok(1, isitma, 8, 8, GUVENLIK)],
    )

    # Isitma penceresinde 08.00-16.00 disinda bir saat calisilmis olamaz.
    model.add(baglam.zv(1, 0) == 1)

    cozucu = cp_model.CpSolver()
    assert cozucu.solve(model) == cp_model.INFEASIBLE, (
        "Isitma penceresinin bos saatleri de sabittir; cozucu gecmise calisma " "ekleyememeli."
    )


def test_h9_modele_ekle_gece_yarisini_asan_uzun_blogu_engeller() -> None:
    """Modelde de blok uzunlugu tavana takilir; duvar saatine bolunmez."""
    from ortools.sat.python import cp_model

    gunler = [_BIR_GUN, _BIR_GUN + timedelta(days=1)]
    baglam = Baglam(
        gorev_noktalari={GUVENLIK: GorevNoktasiBilgisi(GUVENLIK)},
        personel={1: PersonelBilgisi(1, date(2026, 1, 1), None, frozenset())},
        talep_saat={(g, saat, GUVENLIK): 1 for g in gunler for saat in range(24)},
        donem_baslangic=gunler[0],
        donem_bitis=gunler[-1],
    )
    model, x, baglam, _ = _tek_gunluk_model(baglam, gunler)
    H9GunlukAzamiSaat(parametreler={"azami_gunluk_saat": 11}).modele_ekle(model, x, baglam)

    # 20.00'den ertesi gun 08.00'e: on iki saat, tek blok.
    for s in range(20, 32):
        model.add(x[(1, s, GUVENLIK)] == 1)

    cozucu = cp_model.CpSolver()
    assert cozucu.solve(model) == cp_model.INFEASIBLE


def test_h10_kotasi_dolmus_personel_esige_kadar_calisabilir() -> None:
    """SRS 4.2 H10: kural ZORUNLUDUR ama modeli cozulemez YAPMAZ.

    Yalnizca fazla calismayi sinirlar, calismayi degil: kotasi dolmus bir
    personel haftalik esige kadar calismaya devam eder - `fazla[p,w] = 0`
    her zaman uygulanabilir bir degerdir.
    """
    from app.cozucu import CozucuAdaptoru, model_kur
    from app.kurallar.esnek import S1TalepKarsilama

    gunler = [_PZT + timedelta(days=i) for i in range(7)]
    baglam = Baglam(
        gorev_noktalari={GUVENLIK: GorevNoktasiBilgisi(GUVENLIK, onkosul_yetkinlik_id=None)},
        personel={
            1: PersonelBilgisi(
                1,
                date(2026, 1, 1),
                None,
                frozenset(),
                # Kota tamamen dolu: bir saat bile fazla calisamaz.
                devir_fazla_calisma_saat=270.0,
            )
        },
        talep_saat={(g, saat, GUVENLIK): 1 for g in gunler for saat in range(8, 16)},
        donem_baslangic=gunler[0],
        donem_bitis=gunler[-1],
    )
    kurallar = [
        H1GundeTekKesintisizCalisma(parametreler={"asgari_blok_saat": 4}),
        H9GunlukAzamiSaat(parametreler={"azami_gunluk_saat": 11}),
        H10YillikFazlaCalismaKotasi(
            parametreler={"fazla_calisma_esigi": 45, "yillik_fazla_kotasi": 270}
        ),
        S1TalepKarsilama(parametreler={}, agirlik=10000),
    ]
    model, x, baglam, _ceza = model_kur(baglam, gunler, kurallar)
    sonuc = CozucuAdaptoru.coz(model, x, zaman_limiti_saniye=20.0, arama_iscisi_sayisi=3)

    assert sonuc.durum in ("optimal", "uygun"), (
        "Kotasi dolmus personel modeli COZULEMEZ yapmamali; H10 fazla "
        "calismayi sinirlar, calismayi degil."
    )
    # Esik 45 saat: kisi calisir ama haftalik toplami 45'i asamaz.
    assert 0 < len(sonuc.atanan_anahtarlar) <= 45


# --- Kayit defteri ---------------------------------------------------------


def test_kayit_defterinde_h1_h10_tamami_bulunur() -> None:
    for kimlik in ["H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8", "H9", "H10"]:
        assert bul(kimlik) is not None, f"{kimlik} kayit defterinde yok"


def test_kurallari_yukle_kayitli_siniftan_nesne_uretir() -> None:
    class SahteSatir:
        def __init__(self, kimlik: str, parametreler: dict, agirlik: int | None) -> None:
            self.kimlik = kimlik
            self.parametreler = parametreler
            self.agirlik = agirlik

    satirlar = [SahteSatir("H2", {"asgari_dinlenme_saati": 16}, None)]
    kurallar = kurallari_yukle(satirlar)
    assert len(kurallar) == 1
    assert isinstance(kurallar[0], H2AsgariDinlenme)
    assert kurallar[0].parametreler == {"asgari_dinlenme_saati": 16}


def test_kurallari_yukle_tanimsiz_kimlikte_hata_verir() -> None:
    class SahteSatir:
        kimlik = "H99"
        parametreler: dict = {}
        agirlik = None

    with pytest.raises(ValueError, match="Tanimsiz kural kimligi"):
        kurallari_yukle([SahteSatir()])


def test_ihlal_alanlari_dogru_atanir() -> None:
    ihlal = Ihlal(kural_kimlik="H1", personel_id=1, tarih=_BIR_GUN, aciklama="aciklama")
    assert ihlal.kural_kimlik == "H1"
    assert ihlal.personel_id == 1
    assert ihlal.ceza is None


def test_atama_kaydi_gece_saatini_hesaplar() -> None:
    """TD-2: gece saati isaretlenmez, HESAPLANIR.

    20.00–06.00 blogunun on saatinin tamami gece penceresindedir; 08.00–16.00
    blogununsa hicbiri. Eski modelde bu bilgi vardiya tipi uzerindeki
    `gece_mi` bayragindan geliyordu ve bayragin bir oneriyle ezilmesi K3'un
    karsilanmamasinin iki nedeninden biri olmustu.
    """
    gece = blok(1, _BIR_GUN, 20, 10, GUVENLIK)
    gunduz = blok(1, _BIR_GUN, 8, 8, GUVENLIK)
    assert gece.gece_saati == 10
    assert gunduz.gece_saati == 0
    assert gece.bitis == datetime.combine(_BIR_GUN + timedelta(days=1), time(6, 0))
