"""Sprint 2 Gun 6 kabul kriteri: kucuk bir ornek (5 personel, 3 gun) uctan uca
cozuluyor. Cozucu-dogrulayici uyum testini (Sprint 1 Gun 5) gercek CP-SAT
ciktisiyla genisletir: cozucunun uygun buldugu bir cizelgede dogrulayici
H1-H8 icin hicbir ihlal bulmamalidir (SDD 3.2.1).

Ek Gorev (Sprint 2 sonu): ayni uyum guvencesi S1-S8+S6b'ye de genisletildi
- modele_ekle'nin urettigi ham ceza terimi (ham_terimler[kimlik]) ile
dogrula'nin bagimsizca hesapladigi ceza toplaminin BIREBIR ayni sayiyi
uretmesi gerekir (SDD 3.2.1: "cozucu ile dogrulayicinin ayni kurali ifade
ettigi... uyumu bir dogrulama testine baglar"). Bu, S4'un dakika/saat
birim uyusmazligini ve S2/S3'un modele_ekle'sinin (eski) aralik
minimizasyonuyla dogrula'nin normatif SRS 4.3 formulu arasindaki
celismeyi ortaya cikaran testtir (bkz. PROGRESS.md, Ek Gorev).
"""

import uuid
from datetime import date, time, timedelta

from sqlalchemy import select

from app.cozucu import CozucuAdaptoru, model_kur
from app.db import OturumYerel
from app.kurallar import (
    AtamaKaydi,
    Baglam,
    GorevNoktasiBilgisi,
    PersonelBilgisi,
    TercihKaydi,
    VardiyaTipiBilgisi,
)
from app.kurallar.esnek import S4_OLCEK
from app.kurallar.kayit_defteri import bul
from app.models.girdi import TercihTipi
from app.models.sonuc import Atama, AtamaKaynagi, CizelgeSurumu, Donem
from app.models.tanim import GorevNoktasi as GorevNoktasiSatiri
from app.models.tanim import GunTipi
from app.models.tanim import Personel as PersonelSatiri
from app.models.tanim import Talep as TalepSatiri
from app.models.tanim import VardiyaTipi as VardiyaTipiSatiri
from tests.conftest import pg_yoksa_atla

GECE, GUNDUZ, AKSAM = 1, 2, 3
KAPI = 1

_H_PARAMETRELERI = {
    "H1": {},
    "H2": {"asgari_dinlenme_saati": 16},
    "H3": {"azami_ardisik_gece": 3},
    "H4": {"azami_ardisik_calisma_gunu": 6},
    "H5": {"azami_haftalik_saat": 45},
    "H6": {"haftalik_asgari_izin_gunu": 1},
    "H7": {},
    "H8": {},
}
_S_AGIRLIKLARI = {
    "S1": 1000,
    "S2": 5,
    "S3": 5,
    "S4": 3,
    "S5": 2,
    "S6": 10,
    "S6b": 6,
    "S7": 2,
    "S8": 8,
}


def _kucuk_baglam() -> tuple[Baglam, list[date]]:
    vardiya_tipleri = {
        GECE: VardiyaTipiBilgisi(GECE, time(0, 0), time(8, 0), 8, True),
        GUNDUZ: VardiyaTipiBilgisi(GUNDUZ, time(8, 0), time(16, 0), 8, False),
        AKSAM: VardiyaTipiBilgisi(AKSAM, time(16, 0), time(0, 0), 8, False),
    }
    gorev_noktalari = {KAPI: GorevNoktasiBilgisi(KAPI)}
    personel = {
        p: PersonelBilgisi(p, date(2026, 1, 1), None, frozenset(), haftalik_hedef_saat=40)
        for p in range(1, 6)
    }
    gunler = [date(2026, 2, 2) + timedelta(days=i) for i in range(3)]
    # S1 artik SAAT ekseninde calisiyor: talep, GUNDUZ blogunun kapsadigi
    # her saate yazilir (SRS 4.3). Blok gorunumu S2/S3/S4 icin duruyor.
    talep_saat = {(g, saat, KAPI): 1 for g in gunler for saat in range(8, 16)}
    talep = {(g, GUNDUZ, KAPI): 1 for g in gunler}
    baglam = Baglam(
        vardiya_tipleri=vardiya_tipleri,
        gorev_noktalari=gorev_noktalari,
        personel=personel,
        talep_saat=talep_saat,
        talep=talep,
        donem_baslangic=gunler[0],
        donem_bitis=gunler[-1],
    )
    return baglam, gunler


def _tum_kurallari_yukle() -> list:
    kurallar = []
    for kimlik, parametreler in _H_PARAMETRELERI.items():
        sinif = bul(kimlik)
        assert sinif is not None
        kurallar.append(sinif(parametreler=parametreler))
    for kimlik, agirlik in _S_AGIRLIKLARI.items():
        sinif = bul(kimlik)
        assert sinif is not None
        kurallar.append(sinif(parametreler={}, agirlik=agirlik))
    return kurallar


def test_kucuk_ornek_uctan_uca_cozuluyor_ve_h_kurallarini_saglar() -> None:
    baglam, gunler = _kucuk_baglam()
    kurallar = _tum_kurallari_yukle()

    model, x, baglam, ham_terimler = model_kur(baglam, gunler, kurallar)
    sonuc = CozucuAdaptoru.coz(model, x, zaman_limiti_saniye=10, arama_iscisi_sayisi=1)

    assert sonuc.durum in ("optimal", "uygun"), f"Beklenmeyen durum: {sonuc.durum}"
    assert len(sonuc.atanan_anahtarlar) > 0

    atamalar = [
        AtamaKaydi(personel_id=p, tarih=g, vardiya_tipi_id=v, nokta_id=n)
        for (p, g, v, n) in sonuc.atanan_anahtarlar
    ]

    tum_ihlaller = []
    for kimlik, parametreler in _H_PARAMETRELERI.items():
        sinif = bul(kimlik)
        assert sinif is not None
        kural = sinif(parametreler=parametreler)
        tum_ihlaller.extend(kural.dogrula(atamalar, baglam))

    assert tum_ihlaller == [], f"Cozucu ciktisi dogrulayicidan gecemedi: {tum_ihlaller}"

    # S1 baskin agirlikli oldugu icin, kadro yeterliyken (5 personel, gunde 1 talep)
    # her gun KAPI'nin doldurulmus olmasi beklenir (kapsama acigi olmamali).
    for gun in gunler:
        assert any(
            a.tarih == gun and a.nokta_id == KAPI for a in atamalar
        ), f"{gun} gunu KAPI doldurulmamis"


def test_cozum_sonucu_atama_tablosuna_yaziliyor() -> None:
    """Ayni kucuk ornek, gercek veritabani kimlikleriyle kurulup cozulur ve
    sonuc atama tablosuna yazilip geri okunarak dogrulanir (Sprint 2 Gun 6
    kabul kriteri: '... sonuc atama tablosuna yaziliyor')."""
    pg_yoksa_atla()
    on_ek = uuid.uuid4().hex[:8]
    oturum = OturumYerel()
    try:
        vardiya_satirlari = {
            "gece": VardiyaTipiSatiri(
                ad=f"Gece-{on_ek}",
                baslangic_saati=time(0, 0),
                bitis_saati=time(8, 0),
                sure_saat=8,
                gece_mi=True,
            ),
            "gunduz": VardiyaTipiSatiri(
                ad=f"Gunduz-{on_ek}",
                baslangic_saati=time(8, 0),
                bitis_saati=time(16, 0),
                sure_saat=8,
                gece_mi=False,
            ),
            "aksam": VardiyaTipiSatiri(
                ad=f"Aksam-{on_ek}",
                baslangic_saati=time(16, 0),
                bitis_saati=time(0, 0),
                sure_saat=8,
                gece_mi=False,
            ),
        }
        oturum.add_all(vardiya_satirlari.values())
        nokta_satiri = GorevNoktasiSatiri(ad=f"Kapi-{on_ek}")
        oturum.add(nokta_satiri)
        personel_satirlari = [
            PersonelSatiri(
                ad_soyad=f"Test P{i}-{on_ek}",
                sicil_no=f"UCTANUCA-{on_ek}-{i}",
                haftalik_hedef_saat=40,
                aktif_baslangic=date(2026, 1, 1),
            )
            for i in range(1, 6)
        ]
        oturum.add_all(personel_satirlari)
        oturum.flush()  # gercek id'leri almak icin

        gunler = [date(2026, 3, 2) + timedelta(days=i) for i in range(3)]
        for gun in gunler:
            oturum.add(
                TalepSatiri(
                    nokta_id=nokta_satiri.nokta_id,
                    baslangic=vardiya_satirlari["gunduz"].baslangic_saati,
                    bitis=vardiya_satirlari["gunduz"].bitis_saati,
                    gun_tipi=GunTipi.HAFTA_ICI,
                    tarih=gun,
                    gereken_sayi=1,
                )
            )
        donem = Donem(
            baslangic_tarihi=gunler[0],
            bitis_tarihi=gunler[-1],
            tercih_son_tarihi=gunler[0] - timedelta(days=7),
        )
        oturum.add(donem)
        oturum.flush()
        surum = CizelgeSurumu(donem_id=donem.donem_id, surum_no=1)
        oturum.add(surum)
        oturum.flush()

        vardiya_tipleri = {
            satir.vardiya_tipi_id: VardiyaTipiBilgisi(
                satir.vardiya_tipi_id,
                satir.baslangic_saati,
                satir.bitis_saati,
                float(satir.sure_saat),
                satir.gece_mi,
            )
            for satir in vardiya_satirlari.values()
        }
        gorev_noktalari = {nokta_satiri.nokta_id: GorevNoktasiBilgisi(nokta_satiri.nokta_id)}
        personel = {
            p.personel_id: PersonelBilgisi(
                p.personel_id, p.aktif_baslangic, None, frozenset(), haftalik_hedef_saat=40
            )
            for p in personel_satirlari
        }
        talep = {
            (gun, vardiya_satirlari["gunduz"].vardiya_tipi_id, nokta_satiri.nokta_id): 1
            for gun in gunler
        }
        talep_saat = {
            (gun, saat, nokta_satiri.nokta_id): 1 for gun in gunler for saat in range(8, 16)
        }
        baglam = Baglam(
            vardiya_tipleri=vardiya_tipleri,
            gorev_noktalari=gorev_noktalari,
            personel=personel,
            talep_saat=talep_saat,
            talep=talep,
            donem_baslangic=gunler[0],
            donem_bitis=gunler[-1],
        )

        kurallar = _tum_kurallari_yukle()
        model, x, baglam, ham_terimler = model_kur(baglam, gunler, kurallar)
        sonuc = CozucuAdaptoru.coz(model, x, zaman_limiti_saniye=10, arama_iscisi_sayisi=1)
        assert sonuc.durum in ("optimal", "uygun")

        for personel_id, tarih, vardiya_tipi_id, nokta_id in sonuc.atanan_anahtarlar:
            oturum.add(
                Atama(
                    surum_id=surum.surum_id,
                    personel_id=personel_id,
                    tarih=tarih,
                    vardiya_tipi_id=vardiya_tipi_id,
                    nokta_id=nokta_id,
                    kaynak=AtamaKaynagi.COZUCU,
                )
            )
        oturum.commit()

        yazilanlar = (
            oturum.execute(select(Atama).where(Atama.surum_id == surum.surum_id)).scalars().all()
        )
        assert len(yazilanlar) == len(sonuc.atanan_anahtarlar) > 0
        assert all(a.kaynak == AtamaKaynagi.COZUCU for a in yazilanlar)
    finally:
        oturum.rollback()
        oturum.close()


NOKTA_A, NOKTA_B = 1, 2


def _esnek_uyum_baglami() -> tuple[Baglam, list[date], list[AtamaKaydi]]:
    """S1-S8+S6b'nin hepsini tetikleyecek kucuk bir senaryo: iki nokta (ayri
    binalarda, S6b icin), tam bir hafta (donem_gun_sayisi=7 - S2/S3'un taban/tavan
    hesaplarinin donem_gun_sayisi/7 boluminde tam sayi kalmasi icin bilerek
    secildi), onaylanmis tercihler (S5) ve bir onceki cizelge (S8).

    Personel 4'un hedef saati (20) digerlerinden (40) farkli birakildi: S4'un
    pay[p] payi boylece kasitli olarak kesirli cikar (144 toplam talep saati,
    140 toplam hedef saati - 40/140 ve 20/140 kesirleri tam bolunmez) ve
    S4_OLCEK'in olcekleyip geri cevirme adimi (SDD Ek A "Kesirli hedeflerin
    tamsayiya olceklenmesi") gercekten test edilir; esit hedeflerle bu adim hic
    calismadan da (kazara) uyum testinden gecebilirdi."""
    vardiya_tipleri = {
        GECE: VardiyaTipiBilgisi(GECE, time(0, 0), time(8, 0), 8, True),
        GUNDUZ: VardiyaTipiBilgisi(GUNDUZ, time(8, 0), time(16, 0), 8, False),
        AKSAM: VardiyaTipiBilgisi(AKSAM, time(16, 0), time(0, 0), 8, False),
    }
    gorev_noktalari = {
        NOKTA_A: GorevNoktasiBilgisi(NOKTA_A, bina_id=10),
        NOKTA_B: GorevNoktasiBilgisi(NOKTA_B, bina_id=20),
    }
    personel = {
        p: PersonelBilgisi(
            p, date(2026, 1, 1), None, frozenset(), haftalik_hedef_saat=(20 if p == 4 else 40)
        )
        for p in range(1, 5)
    }
    gunler = [date(2026, 2, 2) + timedelta(days=i) for i in range(7)]  # Pzt..Paz (hafta sonu dahil)

    # Blok gorunumu (S2/S3/S4) ve saat ekseni (S1) birlikte kurulur; ikisi de
    # ayni taleple beslenir.
    talep = {}
    talep_saat: dict[tuple[date, int, int], int] = {}
    blok_saatleri = {GUNDUZ: range(8, 16), AKSAM: range(16, 24), GECE: range(0, 8)}
    for i, gun in enumerate(gunler):
        hucreler = [(GUNDUZ, NOKTA_A), (AKSAM, NOKTA_B)]
        if i % 2 == 0:
            hucreler.append((GECE, NOKTA_A))
        for blok, nokta in hucreler:
            talep[(gun, blok, nokta)] = 1
            for saat in blok_saatleri[blok]:
                talep_saat[(gun, saat, nokta)] = 1

    tercihler = [
        TercihKaydi(personel_id=1, tarih=gunler[0], tip=TercihTipi.CALISMAMA),
        TercihKaydi(
            personel_id=2,
            tarih=gunler[2],
            tip=TercihTipi.VARDIYA_TIPI_TERCIHI,
            vardiya_tipi_id=AKSAM,
        ),
    ]

    # S8 icin onceki cizelge: bu modeldeki karar degiskenleriyle kismen
    # ortusen (fark uretecek), kismen kilitlenmemis serbest atamalar.
    onceki_atamalar = [
        AtamaKaydi(personel_id=3, tarih=gunler[0], vardiya_tipi_id=GUNDUZ, nokta_id=NOKTA_A),
        AtamaKaydi(personel_id=4, tarih=gunler[1], vardiya_tipi_id=AKSAM, nokta_id=NOKTA_B),
    ]

    baglam = Baglam(
        vardiya_tipleri=vardiya_tipleri,
        gorev_noktalari=gorev_noktalari,
        personel=personel,
        talep_saat=talep_saat,
        talep=talep,
        donem_baslangic=gunler[0],
        donem_bitis=gunler[-1],
        tercihler=tercihler,
        onceki_atamalar=onceki_atamalar,
    )
    return baglam, gunler, onceki_atamalar


def test_esnek_hedefler_cozucu_dogrulayici_uyumu() -> None:
    """SDD 3.2.1'in uyum guvencesini S1-S8+S6b'ye genisletir: modele_ekle'nin
    urettigi ham ceza (cozucunun kendi hesabi) ile dogrula'nin bagimsizca
    urettigi ceza toplami her esnek hedef icin birebir esit olmalidir.

    S4 istisnasi: modele_ekle CP-SAT'in tamsayi kisiti geregi S4_OLCEK (onda
    bir saat) ile olcup son adimda dogal birime (saat) yarim-yukari yuvarlayarak
    geri cevirir (SDD Ek A "Kesirli hedeflerin tamsayiya olceklenmesi"); dogrula
    ise kesirli cezayi hic yuvarlamadan (onda bir saat hassasiyetinde) dondurur -
    bu ikisi ancak ayni yuvarlama uygulandiginda birebir esitlenir, cunku ozetin
    (7 vs 6.7 gibi) tam sayiya yuvarlanmasi dogrula'nin PAYLASTIRILMAMIS toplamiyla
    aritmetik olarak ayni sey degildir. Bu yuzden S4 icin dogrula_toplami'nin
    S4_OLCEK ile yeniden tam sayiya cevrilip aynen modele_ekle'deki gibi
    yarim-yukari yuvarlanmasi gerekir - test bu donusumu yeniden uygulayarak
    hem yuvarlamanin yapildigini hem DOGRU yapildigini kanitlar."""
    baglam, gunler, _ = _esnek_uyum_baglami()
    kurallar = _tum_kurallari_yukle()

    model, x, baglam, ham_terimler = model_kur(baglam, gunler, kurallar)
    sonuc = CozucuAdaptoru.coz(
        model, x, zaman_limiti_saniye=30, arama_iscisi_sayisi=1, ceza_terimleri=ham_terimler
    )

    assert sonuc.durum == "optimal", f"Beklenmeyen durum: {sonuc.durum}"

    atamalar = [
        AtamaKaydi(personel_id=p, tarih=g, vardiya_tipi_id=v, nokta_id=n)
        for (p, g, v, n) in sonuc.atanan_anahtarlar
    ]

    for kimlik in _S_AGIRLIKLARI:
        sinif = bul(kimlik)
        assert sinif is not None
        kural = sinif(parametreler={})
        dogrula_toplami = sum(
            ihlal.ceza for ihlal in kural.dogrula(atamalar, baglam) if ihlal.ceza is not None
        )
        if kimlik == "S4":
            # dogrula'nin onda-bir-saat hassasiyetli (kesirli) toplamini
            # modele_ekle'nin kendi ic olceginde (S4_OLCEK) yeniden tam sayiya
            # cevirip ayni yarim-yukari kuraliyla yuvarla (bkz. yukaridaki not).
            toplam_x10 = round(dogrula_toplami * S4_OLCEK)
            dogrula_toplami = (toplam_x10 + S4_OLCEK // 2) // S4_OLCEK
        assert sonuc.ceza_dokumu[kimlik] == dogrula_toplami, (
            f"{kimlik}: cozucunun ham cezasi ({sonuc.ceza_dokumu[kimlik]}) "
            f"dogrulayicinin hesapladigi toplamdan ({dogrula_toplami}) farkli"
        )
