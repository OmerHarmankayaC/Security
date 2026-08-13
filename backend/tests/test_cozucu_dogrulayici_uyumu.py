"""Cozucu-dogrulayici uyum testinin iskeleti (UYGULAMA_PLANI.md Sprint 1 Gun 5).

SDD 3.2.1: 'rastgele uretilen ornekler cozulur ve elde edilen cizelge
dogrulayicidan gecirilir; cozucunun gecerli saydigi bir cizelgede
dogrulayicinin ihlal bulmasi ... bir yazilim hatasi olarak ele alinir.'

Sprint 2'ye kadar gercek bir CP-SAT cozucusu olmadigi icin bu oturumda
'cozulmus' cizelge, H1-H8'in tumunu saglayacak sekilde elle kurulan bir
ornektir (rastgele uretim ve gercek cozucu ciktisi Sprint 2 Gun 6'da
eklenecek). Iskeletin amaci: dogrulama mekanizmasinin (Baglam + kural
kayit defteri) H1-H8'in tamami icin dogru sekilde "sifir ihlal" sonucu
uretebildigini simdiden guvenceye almak.
"""

from datetime import date, timedelta

from app.kurallar import (
    AtamaKaydi,
    Baglam,
    GorevNoktasiBilgisi,
    PersonelBilgisi,
)
from app.kurallar.kayit_defteri import bul
from tests.conftest import blok

# Baslangic saatleri (blok degil): ileri yonlu gecis sirasi.
GECE, GUNDUZ, AKSAM = 0, 8, 16
KAPI = 1
GUVENLIK_GOREVI = 1

_H_PARAMETRELERI: dict[str, dict[str, int]] = {
    "H1": {"asgari_blok_saat": 4},
    "H2": {"asgari_dinlenme_saati": 16},
    "H3": {"azami_ardisik_gece": 3, "gece_esigi_saat": 4},
    "H4": {"azami_ardisik_calisma_gunu": 6},
    "H5": {"haftalik_mutlak_tavan": 66},
    "H6": {"haftalik_asgari_izin_gunu": 1},
    "H7": {},
    "H8": {},
    "H9": {"azami_gunluk_saat": 11},
}


def _baglam() -> Baglam:
    gorev_noktalari = {KAPI: GorevNoktasiBilgisi(KAPI, onkosul_yetkinlik_id=GUVENLIK_GOREVI)}
    personel = {
        p: PersonelBilgisi(p, date(2026, 1, 1), None, frozenset({GUVENLIK_GOREVI}))
        for p in (1, 2, 3)
    }
    return Baglam(gorev_noktalari=gorev_noktalari, personel=personel)


def _elle_kurulan_gecerli_cizelge(personel_sayisi: int, gun_sayisi: int) -> list[AtamaKaydi]:
    """H1-H8'in tumunu saglayan, elle kurulan bir cizelge.

    Her personel iki gunde bir calisir (araya daima en az bir tam bos gun
    girer) ve vardiya tipini ileri yonlu sirayla (SRS 3.3.5: gunduz -> aksam
    -> gece) degistirir. Boylece H2 (16 saat dinlenme), H3 (ardisik gece),
    H4 (ardisik calisma gunu) ve H6 (haftalik asgari izin) yapisal olarak
    hicbir zaman zorlanmaz; H5 (haftalik saat tavani) haftada en fazla 4
    vardiyayla (32 saat) rahatca saglanir.
    """
    sira = [GUNDUZ, AKSAM, GECE]
    atamalar = []
    baslangic = date(2026, 2, 2)
    for personel_id in range(1, personel_sayisi + 1):
        for i, gun_ofseti in enumerate(range(0, gun_sayisi, 2)):
            atamalar.append(
                blok(
                    personel_id,
                    baslangic + timedelta(days=gun_ofseti),
                    sira[i % len(sira)],
                    8,
                    KAPI,
                )
            )
    return atamalar


def test_elle_kurulan_gecerli_cizelge_hicbir_zorunlu_kisiti_ihlal_etmez() -> None:
    baglam = _baglam()
    atamalar = _elle_kurulan_gecerli_cizelge(personel_sayisi=3, gun_sayisi=28)

    tum_ihlaller = []
    for kimlik, parametreler in _H_PARAMETRELERI.items():
        sinif = bul(kimlik)
        assert sinif is not None, f"{kimlik} kayit defterinde yok"
        kural = sinif(parametreler=parametreler)
        tum_ihlaller.extend(kural.dogrula(atamalar, baglam))

    assert tum_ihlaller == [], f"Beklenmeyen ihlaller: {tum_ihlaller}"


def test_kasten_bozulan_cizelge_h2_ihlali_yakalar() -> None:
    """Uyum testinin kendisinin de calistigini kanitlamak icin negatif kontrol:
    dinlenmeyi bilerek bozan bir atama eklenince H2'nin bunu yakaladigini dogrular."""
    baglam = _baglam()
    atamalar = _elle_kurulan_gecerli_cizelge(personel_sayisi=1, gun_sayisi=4)
    # Personel 1, gun 0'da GUNDUZ (08-16) calisiyor; hemen ertesi gun GECE eklemek
    # (00-08, yalnizca 8 saat sonra baslar) H2'yi (16 saat) acikca bozar.
    atamalar.append(blok(1, date(2026, 2, 3), GECE, 8, KAPI))

    sinif = bul("H2")
    assert sinif is not None
    kural = sinif(parametreler=_H_PARAMETRELERI["H2"])
    ihlaller = kural.dogrula(atamalar, baglam)

    assert len(ihlaller) == 1
    assert ihlaller[0].kural_kimlik == "H2"


def test_kasten_bozulan_cizelge_s1_fazla_kadroyu_yakalar() -> None:
    """S1 icin ayni negatif kontrol (11.08.2026 hata bildirimi).

    `modele_ekle` bir noktaya talepten fazla atama uretilmesini ZORUNLU
    olarak engeller (`Σ_p x <= talep`); cozucu boyle bir cizelgeyi HICBIR
    ZAMAN uretemez. Standart uyum testi (yukaridaki iki fonksiyon) bu
    yuzden bu hatayi yakalayamazdi - yalnizca cozucunun URETEBILECEGI
    ornekleri doguluyor. Bu test elle bozulmus bir girdi kullanarak
    doğrulayicinin ayni kisiti KENDI BASINA da tanidigini kanitlar; SDD
    3.2.1'in istedigi "cozucunun gecerli SAYMAYACAGI bir cizelgede
    dogrulayicinin de ihlal bulmasi" yonunun testidir.
    """
    from app.kurallar.esnek import S1fFazlaKadro

    baglam = _baglam()
    gun = date(2026, 2, 2)
    for saat in range(GUNDUZ, GUNDUZ + 8):
        baglam.talep_saat[(gun, saat, KAPI)] = 1

    # Cozucunun ureteceginden FAZLASI: talep 1 iken 2 kisi atanmis.
    fazla = [blok(1, gun, GUNDUZ, 8, KAPI), blok(2, gun, GUNDUZ, 8, KAPI)]
    ihlaller = S1fFazlaKadro(parametreler={}, agirlik=2).dogrula(fazla, baglam)

    assert len(ihlaller) == 1
    # FAZLA KADRO ARTIK S1f'IN BULGUSU (K4): S1'in ust siniri esnedi ve
    # cezasi ayri bir agirlik (w1f) tasidigi icin kayit da ayrildi.
    assert ihlaller[0].kural_kimlik == "S1f"
    assert "fazla" in ihlaller[0].aciklama
    # MANUEL DUZENLEMEDE ceza uretmez (bkz. S1fFazlaKadro.dogrula); cozucu
    # tarafinda ise w1f ile cezalanir. Iki tarafin farkli davranmasi
    # bilinclidir (SRS 4.3).
    assert ihlaller[0].ceza is None
