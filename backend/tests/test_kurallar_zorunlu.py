"""H1-H8 dogrula testleri: elle kurulan ornek atama listeleriyle (Sprint 1 Gun 2 kabul kriteri).

Bu testler veritabani gerektirmez; Baglam ve AtamaKaydi elle olusturulur.
"""

from datetime import date, time, timedelta

import pytest

from app.kurallar import (
    AtamaKaydi,
    Baglam,
    GorevNoktasiBilgisi,
    Ihlal,
    MusaitlikKaydi,
    PersonelBilgisi,
    VardiyaTipiBilgisi,
    bul,
    kurallari_yukle,
)
from app.kurallar.zorunlu import (
    H1GundeBirVardiya,
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

GECE = 1
GUNDUZ = 2
AKSAM = 3

KAPI = 1
KONTROL_ODASI = 2
MURACAAT = 3

GUVENLIK_GOREVI = 1
UZUN_GUNDUZ = 9  # 08.00-20.00, on iki saat (SRS 3.3.1)
_PZT = date(2026, 2, 2)  # pazartesi
MURACAAT_GOREVLISI = 2


@pytest.fixture
def baglam() -> Baglam:
    vardiya_tipleri = {
        GECE: VardiyaTipiBilgisi(GECE, time(0, 0), time(8, 0), 8, True),
        GUNDUZ: VardiyaTipiBilgisi(GUNDUZ, time(8, 0), time(16, 0), 8, False),
        AKSAM: VardiyaTipiBilgisi(AKSAM, time(16, 0), time(0, 0), 8, False),
    }
    gorev_noktalari = {
        KAPI: GorevNoktasiBilgisi(KAPI, onkosul_yetkinlik_id=None),
        KONTROL_ODASI: GorevNoktasiBilgisi(KONTROL_ODASI, onkosul_yetkinlik_id=GUVENLIK_GOREVI),
        MURACAAT: GorevNoktasiBilgisi(MURACAAT, onkosul_yetkinlik_id=MURACAAT_GOREVLISI),
    }
    personel = {
        1: PersonelBilgisi(1, date(2026, 1, 1), None, frozenset({GUVENLIK_GOREVI})),
        2: PersonelBilgisi(2, date(2026, 1, 1), None, frozenset({MURACAAT_GOREVLISI})),
    }
    return Baglam(
        vardiya_tipleri=vardiya_tipleri, gorev_noktalari=gorev_noktalari, personel=personel
    )


def test_h1_ayni_gune_iki_atama_ihlal_verir(baglam: Baglam) -> None:
    kural = H1GundeBirVardiya(parametreler={})
    atamalar = [
        AtamaKaydi(1, date(2026, 1, 5), GUNDUZ, KAPI),
        AtamaKaydi(1, date(2026, 1, 5), AKSAM, KAPI),
    ]
    ihlaller = kural.dogrula(atamalar, baglam)
    assert len(ihlaller) == 1
    assert ihlaller[0].kural_kimlik == "H1"


def test_h1_farkli_gunlerde_atama_ihlal_vermez(baglam: Baglam) -> None:
    kural = H1GundeBirVardiya(parametreler={})
    atamalar = [
        AtamaKaydi(1, date(2026, 1, 5), GUNDUZ, KAPI),
        AtamaKaydi(1, date(2026, 1, 6), GUNDUZ, KAPI),
    ]
    assert kural.dogrula(atamalar, baglam) == []


def test_h2_yetersiz_dinlenme_ihlal_verir(baglam: Baglam) -> None:
    kural = H2AsgariDinlenme(parametreler={"asgari_dinlenme_saati": 16})
    atamalar = [
        AtamaKaydi(1, date(2026, 1, 5), AKSAM, KAPI),  # biter: 06 00:00
        AtamaKaydi(1, date(2026, 1, 6), GUNDUZ, KAPI),  # baslar: 06 08:00 -> 8 saat ara
    ]
    ihlaller = kural.dogrula(atamalar, baglam)
    assert len(ihlaller) == 1
    assert ihlaller[0].kural_kimlik == "H2"


def test_h2_yeterli_dinlenme_ihlal_vermez(baglam: Baglam) -> None:
    kural = H2AsgariDinlenme(parametreler={"asgari_dinlenme_saati": 16})
    atamalar = [
        AtamaKaydi(1, date(2026, 1, 5), GECE, KAPI),  # biter: 05 08:00
        AtamaKaydi(1, date(2026, 1, 6), AKSAM, KAPI),  # baslar: 06 16:00 -> 32 saat ara
    ]
    assert kural.dogrula(atamalar, baglam) == []


def test_h3_dort_ardisik_gece_ihlal_verir(baglam: Baglam) -> None:
    kural = H3ArdisikGeceUstSiniri(parametreler={"azami_ardisik_gece": 3})
    atamalar = [AtamaKaydi(1, date(2026, 1, 5 + i), GECE, KAPI) for i in range(4)]
    ihlaller = kural.dogrula(atamalar, baglam)
    assert len(ihlaller) == 1
    assert ihlaller[0].kural_kimlik == "H3"
    assert ihlaller[0].tarih == date(2026, 1, 8)


def test_h3_uc_ardisik_gece_ihlal_vermez(baglam: Baglam) -> None:
    kural = H3ArdisikGeceUstSiniri(parametreler={"azami_ardisik_gece": 3})
    atamalar = [AtamaKaydi(1, date(2026, 1, 5 + i), GECE, KAPI) for i in range(3)]
    assert kural.dogrula(atamalar, baglam) == []


def test_h4_yedi_ardisik_gun_ihlal_verir(baglam: Baglam) -> None:
    kural = H4ArdisikCalismaGunuUstSiniri(parametreler={"azami_ardisik_calisma_gunu": 6})
    atamalar = [AtamaKaydi(1, date(2026, 1, 5 + i), GUNDUZ, KAPI) for i in range(7)]
    ihlaller = kural.dogrula(atamalar, baglam)
    assert len(ihlaller) == 1
    assert ihlaller[0].kural_kimlik == "H4"


def test_h4_alti_ardisik_gun_ihlal_vermez(baglam: Baglam) -> None:
    kural = H4ArdisikCalismaGunuUstSiniri(parametreler={"azami_ardisik_calisma_gunu": 6})
    atamalar = [AtamaKaydi(1, date(2026, 1, 5 + i), GUNDUZ, KAPI) for i in range(6)]
    assert kural.dogrula(atamalar, baglam) == []


def test_h5_haftalik_saat_tavani_asilinca_ihlal_verir(baglam: Baglam) -> None:
    kural = H5KayanHaftalikSaatTavani(parametreler={"haftalik_mutlak_tavan": 45})
    # 6 gun x 8 saat = 48 saat, 7 gunluk pencerede tavani (45) asar.
    atamalar = [AtamaKaydi(1, date(2026, 1, 5 + i), GUNDUZ, KAPI) for i in range(6)]
    ihlaller = kural.dogrula(atamalar, baglam)
    assert len(ihlaller) == 1
    assert ihlaller[0].kural_kimlik == "H5"


def test_h5_tavan_altinda_ihlal_vermez(baglam: Baglam) -> None:
    kural = H5KayanHaftalikSaatTavani(parametreler={"haftalik_mutlak_tavan": 45})
    # 5 gun x 8 saat = 40 saat, tavanin altinda.
    atamalar = [AtamaKaydi(1, date(2026, 1, 5 + i), GUNDUZ, KAPI) for i in range(5)]
    assert kural.dogrula(atamalar, baglam) == []


def test_h6_yedi_gun_ust_uste_calisinca_ihlal_verir(baglam: Baglam) -> None:
    kural = H6HaftalikAsgariIzinGunu(parametreler={"haftalik_asgari_izin_gunu": 1})
    atamalar = [AtamaKaydi(1, date(2026, 1, 5 + i), GUNDUZ, KAPI) for i in range(7)]
    ihlaller = kural.dogrula(atamalar, baglam)
    assert len(ihlaller) == 1
    assert ihlaller[0].kural_kimlik == "H6"


def test_h6_haftada_bir_izin_gunuyle_ihlal_vermez(baglam: Baglam) -> None:
    kural = H6HaftalikAsgariIzinGunu(parametreler={"haftalik_asgari_izin_gunu": 1})
    # 7 gunluk pencerede 6. gun (indeks 5) bos birakilir.
    atamalar = [AtamaKaydi(1, date(2026, 1, 5 + i), GUNDUZ, KAPI) for i in range(7) if i != 5]
    assert kural.dogrula(atamalar, baglam) == []


def test_h7_izinli_gunde_atama_ihlal_verir(baglam: Baglam) -> None:
    kural = H7Musaitlik(parametreler={})
    baglam.musaitlik.append(
        MusaitlikKaydi(1, date(2026, 1, 5), date(2026, 1, 5), MusaitlikDilimi.TAM_GUN)
    )
    atamalar = [AtamaKaydi(1, date(2026, 1, 5), GUNDUZ, KAPI)]
    ihlaller = kural.dogrula(atamalar, baglam)
    assert len(ihlaller) == 1
    assert ihlaller[0].kural_kimlik == "H7"


def test_h7_aktiflik_araligi_disinda_ihlal_verir(baglam: Baglam) -> None:
    kural = H7Musaitlik(parametreler={})
    atamalar = [AtamaKaydi(1, date(2025, 12, 31), GUNDUZ, KAPI)]  # aktif_baslangic: 2026-01-01
    ihlaller = kural.dogrula(atamalar, baglam)
    assert len(ihlaller) == 1
    assert ihlaller[0].kural_kimlik == "H7"


def test_h7_musait_gunde_ihlal_vermez(baglam: Baglam) -> None:
    kural = H7Musaitlik(parametreler={})
    atamalar = [AtamaKaydi(1, date(2026, 1, 5), GUNDUZ, KAPI)]
    assert kural.dogrula(atamalar, baglam) == []


def test_h8_yetkinligi_olmayan_personel_ihlal_verir(baglam: Baglam) -> None:
    kural = H8OnkosulYetkinligi(parametreler={})
    atamalar = [AtamaKaydi(2, date(2026, 1, 5), GUNDUZ, KONTROL_ODASI)]  # personel 2: muracaat
    ihlaller = kural.dogrula(atamalar, baglam)
    assert len(ihlaller) == 1
    assert ihlaller[0].kural_kimlik == "H8"


def test_h8_yetkin_personel_ihlal_vermez(baglam: Baglam) -> None:
    kural = H8OnkosulYetkinligi(parametreler={})
    atamalar = [AtamaKaydi(1, date(2026, 1, 5), GUNDUZ, KONTROL_ODASI)]  # personel 1: guvenlik
    assert kural.dogrula(atamalar, baglam) == []


def test_h8_onkosulsuz_noktada_herkes_calisabilir(baglam: Baglam) -> None:
    kural = H8OnkosulYetkinligi(parametreler={})
    atamalar = [AtamaKaydi(2, date(2026, 1, 5), GUNDUZ, KAPI)]
    assert kural.dogrula(atamalar, baglam) == []


def test_h1_modele_ekle_ayni_gune_iki_atamayi_engeller(baglam: Baglam) -> None:
    """H1'in gercek CP-SAT kisitinin, ayni gun icin iki degiskeni de 1 yapmayi
    imkansiz kildigini dogrular (Sprint 2 Gun 6)."""
    from ortools.sat.python import cp_model

    model = cp_model.CpModel()
    gun = date(2026, 1, 5)
    x1 = model.new_bool_var("x1")
    x2 = model.new_bool_var("x2")
    degiskenler = {
        (1, gun, GUNDUZ, KAPI): x1,
        (1, gun, AKSAM, KAPI): x2,
    }
    baglam.zaman_ekseni = [gun]

    kural = H1GundeBirVardiya(parametreler={})
    assert kural.modele_ekle(model, degiskenler, baglam) is None

    model.add(x1 == 1)
    model.add(x2 == 1)
    cozucu = cp_model.CpSolver()
    durum = cozucu.solve(model)
    assert durum == cp_model.INFEASIBLE


def test_kayit_defterinde_h1_h8_tamami_bulunur() -> None:
    for kimlik in ["H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8"]:
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
    ihlal = Ihlal(kural_kimlik="H1", personel_id=1, tarih=date(2026, 1, 5), aciklama="aciklama")
    assert ihlal.kural_kimlik == "H1"
    assert ihlal.personel_id == 1
    assert ihlal.ceza is None


# --- H9 / H10 (Tur 4, SRS 4.2) ---------------------------------------------


def test_h9_gunluk_tavani_asan_blok_ihlal_verir(baglam: Baglam) -> None:
    """H1 gunde tek blok verdigi icin bu pratikte "katalogdaki hicbir blok
    gunluk tavani asamaz" demeye gelir; kural yine de ayri yazilir cunku
    yasal dayanagi H1'den bagimsizdir (SRS 4.2 H9)."""
    baglam.vardiya_tipleri[UZUN_GUNDUZ] = VardiyaTipiBilgisi(
        UZUN_GUNDUZ, time(8, 0), time(20, 0), 12, False
    )
    kural = H9GunlukAzamiSaat(parametreler={"azami_gunluk_saat": 11})
    ihlaller = kural.dogrula([AtamaKaydi(1, date(2026, 1, 5), UZUN_GUNDUZ, KAPI)], baglam)
    assert len(ihlaller) == 1
    assert ihlaller[0].personel_id == 1
    assert "tavan 11" in ihlaller[0].aciklama


def test_h9_tavanin_altindaki_blok_ihlal_vermez(baglam: Baglam) -> None:
    kural = H9GunlukAzamiSaat(parametreler={"azami_gunluk_saat": 11})
    assert kural.dogrula([AtamaKaydi(1, date(2026, 1, 5), GUNDUZ, KAPI)], baglam) == []


def test_h10_kota_asilinca_ihlal_verir(baglam: Baglam) -> None:
    """Fazla calisma TAKVIM HAFTASI uzerinden toplanir (TD-14).

    Pazartesi-pazar arasi alti gun x 12 saat = 72 saat; esik 45 -> 27 saat
    fazla. Kota 20 olunca asilir.
    """
    baglam.vardiya_tipleri[UZUN_GUNDUZ] = VardiyaTipiBilgisi(
        UZUN_GUNDUZ, time(8, 0), time(20, 0), 12, False
    )
    baglam.donem_baslangic = _PZT
    baglam.donem_bitis = _PZT + timedelta(days=6)
    kural = H10YillikFazlaCalismaKotasi(
        parametreler={"fazla_calisma_esigi": 45, "yillik_fazla_kotasi": 20}
    )
    atamalar = [AtamaKaydi(1, _PZT + timedelta(days=i), UZUN_GUNDUZ, KAPI) for i in range(6)]
    ihlaller = kural.dogrula(atamalar, baglam)
    assert [i.personel_id for i in ihlaller] == [1]
    assert "27.0" in ihlaller[0].aciklama


def test_h10_esigin_altinda_kalan_hafta_kotayi_tuketmez(baglam: Baglam) -> None:
    baglam.donem_baslangic = _PZT
    baglam.donem_bitis = _PZT + timedelta(days=6)
    kural = H10YillikFazlaCalismaKotasi(
        parametreler={"fazla_calisma_esigi": 45, "yillik_fazla_kotasi": 20}
    )
    # 5 gun x 8 saat = 40 saat; esigin altinda, fazla yok.
    atamalar = [AtamaKaydi(1, _PZT + timedelta(days=i), GUNDUZ, KAPI) for i in range(5)]
    assert kural.dogrula(atamalar, baglam) == []


def test_h10_devir_bakiyesi_kotaya_eklenir(baglam: Baglam) -> None:
    """`devir[p]` personel kaydindan okunur (TD-6; Tur 5'te yayinlanmis
    surumlerden turetilen degere EKLENECEK, yerine gecmeyecek)."""
    baglam.personel[1] = PersonelBilgisi(
        1,
        date(2026, 1, 1),
        None,
        frozenset({GUVENLIK_GOREVI}),
        devir_fazla_calisma_saat=19.0,
    )
    baglam.vardiya_tipleri[UZUN_GUNDUZ] = VardiyaTipiBilgisi(
        UZUN_GUNDUZ, time(8, 0), time(20, 0), 12, False
    )
    baglam.donem_baslangic = _PZT
    baglam.donem_bitis = _PZT + timedelta(days=6)
    kural = H10YillikFazlaCalismaKotasi(
        parametreler={"fazla_calisma_esigi": 45, "yillik_fazla_kotasi": 20}
    )
    # 4 gun x 12 = 48 saat -> 3 saat fazla. Tek basina kotanin altinda;
    # devirle birlikte (19 + 3 = 22) asiyor.
    atamalar = [AtamaKaydi(1, _PZT + timedelta(days=i), UZUN_GUNDUZ, KAPI) for i in range(4)]
    ihlaller = kural.dogrula(atamalar, baglam)
    assert len(ihlaller) == 1
    assert "Devir 19.0" in ihlaller[0].aciklama


def test_h10_kayan_pencere_degil_takvim_haftasi_kullanir(baglam: Baglam) -> None:
    """TD-14'un asil noktasi: kota ORTUSMEYEN pencerelerde anlamlidir.

    Ayni alti gunluk yogunluk iki takvim haftasina BOLUNDUGUNDE her hafta
    esigin altinda kalir ve fazla dogmaz. Kayan pencere kullanilsaydi ayni
    atamalar yedi ayri pencereye girer ve toplam yedi katina cikardi.
    """
    baglam.vardiya_tipleri[UZUN_GUNDUZ] = VardiyaTipiBilgisi(
        UZUN_GUNDUZ, time(8, 0), time(20, 0), 12, False
    )
    baglam.donem_baslangic = _PZT - timedelta(days=3)
    baglam.donem_bitis = _PZT + timedelta(days=3)
    kural = H10YillikFazlaCalismaKotasi(
        parametreler={"fazla_calisma_esigi": 45, "yillik_fazla_kotasi": 20}
    )
    # Cuma-cumartesi-pazar (onceki hafta) + pazartesi-sali-carsamba: her
    # haftada 3 x 12 = 36 saat, ikisi de esigin altinda.
    atamalar = [
        AtamaKaydi(1, _PZT + timedelta(days=i), UZUN_GUNDUZ, KAPI) for i in (-3, -2, -1, 0, 1, 2)
    ]
    assert kural.dogrula(atamalar, baglam) == []


def test_h10_kotasi_dolmus_personel_esige_kadar_calisabilir() -> None:
    """SRS 4.2 H10: kural ZORUNLUDUR ama modeli cozulemez YAPMAZ.

    Yalnizca fazla calismayi sinirlar, calismayi degil: kotasi dolmus bir
    personel haftalik esige kadar calismaya devam eder, yalnizca ustune
    cikamaz - `fazla[p,w] = 0` her zaman uygulanabilir bir degerdir.

    Bu testin olctugu sey tam olarak budur: kotasi TAMAMEN dolmus tek
    kisilik bir kadroda model cozulur ve kisi calisir.
    """
    from app.cozucu import CozucuAdaptoru, model_kur
    from app.kurallar.esnek import S1TalepKarsilama

    gunler = [_PZT + timedelta(days=i) for i in range(7)]
    baglam = Baglam(
        vardiya_tipleri={GUNDUZ: VardiyaTipiBilgisi(GUNDUZ, time(8, 0), time(16, 0), 8, False)},
        gorev_noktalari={KAPI: GorevNoktasiBilgisi(KAPI, onkosul_yetkinlik_id=None)},
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
        talep_saat={(g, saat, KAPI): 1 for g in gunler for saat in range(8, 16)},
        donem_baslangic=gunler[0],
        donem_bitis=gunler[-1],
    )
    # S1 olmadan modelin amaci bos kalir ve "hic atama yapma" optimaldir;
    # testin olctugu sey kotanin CALISMAYI degil FAZLA CALISMAYI
    # sinirladigi, dolayisiyla kapsama baskisi da bulunmali.
    kurallar = [
        H1GundeBirVardiya(parametreler={}),
        H10YillikFazlaCalismaKotasi(
            parametreler={"fazla_calisma_esigi": 45, "yillik_fazla_kotasi": 270}
        ),
        S1TalepKarsilama(parametreler={}, agirlik=10000),
    ]
    model, x, baglam, _ceza = model_kur(baglam, gunler, kurallar)
    sonuc = CozucuAdaptoru.coz(model, x, zaman_limiti_saniye=10.0, arama_iscisi_sayisi=3)

    assert sonuc.durum in ("optimal", "uygun"), (
        "Kotasi dolmus personel modeli COZULEMEZ yapmamali; H10 fazla "
        "calismayi sinirlar, calismayi degil."
    )
    # Esik 45 saat / 8 saatlik blok -> en cok bes gun; kisi calismaya devam
    # ediyor ama alti gune cikamiyor.
    assert 0 < len(sonuc.atanan_anahtarlar) <= 5
