"""S2/S3/S4 kumulatif ufka gectiginde ne degisir (SRS TD-6, 4.3).

Bu dosya ARITMETIGI kilitler; ardisik iki donemin gercekten cozuldugu kabul
testi `test_cozucu_uctan_uca.py`dedir.

Kilitlenen uc sey:

  1. **Yuk ile hedef BIRLIKTE olceklenir.** Gecmis saat yuke eklenirken
     gecmis pay da hedefe eklenir. Yalniz biri eklenseydi kisi hic yapmadigi
     bir isin hesabini verirken gosterilirdi.
  2. **Gecmis yuk sabit terimdir**, karar degiskeni degil.
  3. **Calisabilirlik orani payi kucultur** (SRS TD-6).
"""

import math
from datetime import date, timedelta

import pytest

from app.kurallar.baglam import Baglam, GorevNoktasiBilgisi, PersonelBilgisi
from app.kurallar.esnek import S2GeceAdaleti, S3HaftaSonuAdaleti, S4ToplamSaatDengesi
from app.kurallar.gecmis import GecmisYuk, PersonelSayaci
from tests.conftest import blok

NOKTA = 1
_G = date(2026, 1, 5)  # pazartesi


def _gun(kayma: int) -> date:
    return _G + timedelta(days=kayma)


def _baglam(gecmis: GecmisYuk | None = None) -> Baglam:
    b = Baglam(
        gorev_noktalari={NOKTA: GorevNoktasiBilgisi(NOKTA)},
        personel={
            1: PersonelBilgisi(1, date(2025, 1, 1), None, frozenset(), haftalik_hedef_saat=40),
            2: PersonelBilgisi(2, date(2025, 1, 1), None, frozenset(), haftalik_hedef_saat=40),
        },
        zaman_ekseni=[_gun(i) for i in range(7)],
        donem_baslangic=_gun(0),
        donem_bitis=_gun(6),
        gecmis=gecmis,
    )
    # Iki gecelik talep: her gece bir kisi, sekiz saat.
    for i in (0, 1):
        for saat in range(20, 24):
            b.talep_saat[(_gun(i), saat, NOKTA)] = 1
        for saat in range(0, 4):
            b.talep_saat[(_gun(i + 1), saat, NOKTA)] = 1
    return b


def _gecmis(
    *,
    gece: dict[int, float] | None = None,
    pay_gece: dict[int, float] | None = None,
    oran: dict[int, float] | None = None,
    toplam: dict[int, float] | None = None,
    pay_toplam: dict[int, float] | None = None,
    hafta_sonu: dict[int, float] | None = None,
    pay_hafta_sonu: dict[int, float] | None = None,
) -> GecmisYuk:
    kisiler = set(gece or {}) | set(toplam or {}) | set(hafta_sonu or {})
    return GecmisYuk(
        ufuk_gun=90,
        pencere_bas=_gun(-90),
        pencere_bit=_gun(0),
        sayaclar={
            p: PersonelSayaci(
                toplam_saat=(toplam or {}).get(p, 0.0),
                gece_saat=(gece or {}).get(p, 0.0),
                hafta_sonu_saat=(hafta_sonu or {}).get(p, 0.0),
            )
            for p in kisiler
        },
        pay_gece=pay_gece or {},
        pay_hafta_sonu=pay_hafta_sonu or {},
        pay_toplam=pay_toplam or {},
        calisabilir_oran=oran or {},
    )


def _s2_cezasi(baglam: Baglam, atamalar: list) -> dict[int, float]:
    return {
        i.personel_id: i.ceza or 0.0
        for i in S2GeceAdaleti(parametreler={}, agirlik=2).dogrula(atamalar, baglam)
    }


def test_gecmiste_agir_gece_yuku_alan_kisi_donem_ici_esitlikte_cezali_olur() -> None:
    """Turun ozu: gecmis gorunmezken 'esit' olan dagilim artik esit degil.

    Iki kisi donem icinde birer gece aliyor. Gecmis kapaliyken bu kusursuz;
    gecmis acikken 1 numara ufkun tamaminda 2'nin iki katini tasimis oluyor
    ve ceza onda birikiyor. Cozucu bir sonraki donemde yuku digerine kaydirir.
    """
    atamalar = [
        blok(1, _gun(0), 20, 8, NOKTA),
        blok(2, _gun(1), 20, 8, NOKTA),
    ]

    gecmissiz = _s2_cezasi(_baglam(), atamalar)
    assert gecmissiz.get(1, 0.0) == 0.0
    assert gecmissiz.get(2, 0.0) == 0.0

    # Gecmiste 1 numara 16 saat gece tasimis, 2 numara hic. Pay ikisine de
    # esit dagilir (8'er saat) cunku ayni noktaya erisiyorlar.
    gecmisli = _s2_cezasi(
        _baglam(_gecmis(gece={1: 16.0, 2: 0.0}, pay_gece={1: 8.0, 2: 8.0})),
        atamalar,
    )
    # Gecmis acilinca ceza ORTAYA CIKIYOR: donem ici esitlik ufuk boyunca
    # esitlik degilmis.
    assert gecmisli, "gecmis acikken dengesizlik gorunmeli"

    # Ceza MUTLAK sapmadir, bu yuzden dengesizlik iki tarafta da ayni
    # buyuklukte gorunur; YONU gormek icin yuk ile paya bakilir.
    baglam = _baglam(_gecmis(gece={1: 16.0, 2: 0.0}, pay_gece={1: 8.0, 2: 8.0}))
    paylar = baglam.adil_paylar(lambda a: a[1] >= 20 or a[1] < 6, olcu="gece")
    yukler = {1: 16.0 + 8, 2: 0.0 + 8}
    assert yukler[1] > paylar[1], "gecmiste agir yuk tasiyan kisi payinin USTUNDE"
    assert yukler[2] < paylar[2], "hic tasimayan kisi payinin ALTINDA"
    # Cozucu bir sonraki donemde yuku 2'ye kaydirarak bu farki kapatir.


def test_yuk_ile_hedef_birlikte_olceklenir() -> None:
    """Gecmis yuke eklenip paya eklenmezse kisi hic yapmadigi isin hesabini verir.

    Ayni gecmis saat hem yuke hem paya girdiginde — herkes esit tasimissa —
    sapma yine sifirdir. Yalniz yuk eklenseydi HERKES cezali cikardi.
    """
    atamalar = [
        blok(1, _gun(0), 20, 8, NOKTA),
        blok(2, _gun(1), 20, 8, NOKTA),
    ]
    # Ikisi de gecmiste 8'er saat gece tasimis; pay da 8'er saat.
    dengeli = _s2_cezasi(
        _baglam(_gecmis(gece={1: 8.0, 2: 8.0}, pay_gece={1: 8.0, 2: 8.0})),
        atamalar,
    )
    assert dengeli == {}, "esit tasinan gecmis ceza uretmemeli"


def test_calisabilir_oran_payi_kucultur() -> None:
    """SRS TD-6: ufkun yarisinda ise baslayan kisi tam payla olculemez.

    Oran uygulanmasaydi bu kisi hicbir cizelgeyle kapatamayacagi bir sapma
    tasirdi; olcu ayirt ediciligini kaybederdi.
    """
    baglam = _baglam(_gecmis(gece={1: 0.0, 2: 0.0}, oran={1: 1.0, 2: 0.5}))
    paylar = baglam.adil_paylar(lambda a: a[1] >= 20 or a[1] < 6, olcu="gece")
    assert paylar[2] == pytest.approx(paylar[1] * 0.5)


def test_gecmis_yoksa_paylar_ve_cezalar_eski_davranista_kalir() -> None:
    """Gecmisi olmayan kurulumda olcu yalniz donemi kapsar.

    Bu, kumulatif ufkun geriye donuk uyumlulugudur: `gecmis is None` iken
    hicbir olceklendirme yapilmaz.
    """
    baglam = _baglam()
    assert baglam.calisabilir_oran(1) == 1.0
    olcusuz = baglam.adil_paylar(lambda a: True)
    olculu = baglam.adil_paylar(lambda a: True, olcu="gece")
    assert olcusuz == olculu


def test_s4_gecmis_toplam_saati_hem_yuke_hem_paya_katar() -> None:
    atamalar = [blok(1, _gun(0), 8, 8, NOKTA)]
    baglam = _baglam(_gecmis(toplam={1: 40.0, 2: 0.0}, pay_toplam={1: 20.0, 2: 20.0}))
    ihlaller = {
        i.personel_id: i.ceza or 0.0
        for i in S4ToplamSaatDengesi(parametreler={}, agirlik=4).dogrula(atamalar, baglam)
    }
    # 1 numara ufuk boyunca 48 saat tasidi, payi ise donem payi + 20.
    # 2 numara hic tasimadi ama ayni payi aldi; ikisi de sapmali ve
    # sapmalar ZIT yonlerde - bu, olcunun iki yonlu calistigini gosterir.
    assert ihlaller.get(1, 0.0) > 0
    assert ihlaller.get(2, 0.0) > 0


def test_s3_hafta_sonu_gecmisi_ayri_olcuden_gelir() -> None:
    """Gece ve hafta sonu AYRI sayaclardir; biri digerinin yerine gecmez."""
    hs_gun = next(_gun(i) for i in range(7) if _gun(i).weekday() >= 5)
    baglam = _baglam(_gecmis(hafta_sonu={1: 16.0, 2: 0.0}, pay_hafta_sonu={1: 8.0, 2: 8.0}))
    for saat in range(8, 16):
        baglam.talep_saat[(hs_gun, saat, NOKTA)] = 1
    atamalar = [blok(1, hs_gun, 8, 8, NOKTA)]
    kural = S3HaftaSonuAdaleti(parametreler={}, agirlik=2)
    ihlaller = {i.personel_id: i.ceza or 0.0 for i in kural.dogrula(atamalar, baglam)}

    # Gecmissiz de bir dengesizlik var (1 calisti, 2 calismadi) ama gecmis
    # acilinca sapma BUYUYOR: 1 numaranin hafta sonu yuku ufuk boyunca
    # 8 degil 24 saat. Olcunun hafta sonu sayacini okudugu buradan anlasilir
    # — gece sayaci ayni senaryoda hic dolu degil.
    gecmissiz = _baglam()
    for saat in range(8, 16):
        gecmissiz.talep_saat[(hs_gun, saat, NOKTA)] = 1
    gecmissiz_ceza = {i.personel_id: i.ceza or 0.0 for i in kural.dogrula(atamalar, gecmissiz)}
    assert ihlaller[1] > gecmissiz_ceza[1]
    assert baglam.gecmis_gece_saat(1) == 0.0


def test_donem_ici_pay_calisabilir_oranla_olceklenmez() -> None:
    """Oran UFKUN olcusudur; donem ici paya uygulanmasi olculen bir hataydi.

    Kabul olcumunun referans ornegi doksan gunluk pencerenin yalnizca 32
    gununu kapsiyordu. `olcu` verilmeden cagrilan `adil_paylar` paylari yine
    de 0,356 ile carpiyor, yuk ise donem ici kaldigi icin sapma 34'ten
    61,27'ye ciriyordu — ne cozucu kotulesmisti ne veri.

    Kural: ufuk genislemesi ile oran olceklemesi BIRLIKTE olur ya da hic
    olmaz.
    """
    gecmis = _gecmis(gece={1: 0.0, 2: 0.0}, pay_gece={1: 4.0, 2: 4.0}, oran={1: 1.0, 2: 0.5})
    baglam = _baglam(gecmis)

    def gece_mi(anahtar) -> bool:
        return anahtar[1] >= 20 or anahtar[1] < 6

    donem_ici = baglam.adil_paylar(gece_mi)
    ufuk = baglam.adil_paylar(gece_mi, olcu="gece")

    # Donem ici: oran YOK, gecmis pay YOK — iki kisi de ayni payi alir.
    assert donem_ici[1] == pytest.approx(donem_ici[2])
    # Ufuk: gecmis pay eklenir, sonra oran uygulanir.
    assert ufuk[1] == pytest.approx(donem_ici[1] + 4.0)
    assert ufuk[2] == pytest.approx((donem_ici[2] + 4.0) * 0.5)


# --- Pay TAM SAYIYSA taban/tavan bandi NOKTA olmalidir --------------------


def _uc_kisilik_baglam(gun_sayisi: int) -> Baglam:
    """Uc kisinin erisebildigi bir nokta; her saatte bir kisi gerekiyor.

    Kisi basi pay her saat icin 1/3'tur ve bu deger IKILIK TABANDA TAM
    GOSTERILEMEZ. Yeterince toplanınca artik birikir: 63 saat icin matematiksel
    sonuc tam 21, kayan noktada 21.000000000000085.
    """
    b = Baglam(
        gorev_noktalari={NOKTA: GorevNoktasiBilgisi(NOKTA)},
        personel={
            k: PersonelBilgisi(k, date(2025, 1, 1), None, frozenset(), haftalik_hedef_saat=40)
            for k in (1, 2, 3)
        },
        zaman_ekseni=[_gun(i) for i in range(gun_sayisi)],
        donem_baslangic=_gun(0),
        donem_bitis=_gun(gun_sayisi - 1),
    )
    saat = 0
    for gun in range(gun_sayisi):
        for s in range(24):
            if saat >= 63:
                return b
            b.talep_saat[(_gun(gun), s, NOKTA)] = 1
            saat += 1
    return b


def test_tam_sayi_pay_ceil_ile_bir_ust_bande_kacmaz() -> None:
    """Pay matematiksel olarak TAM SAYIYSA `ceil` onu bir yukari tasimamalidir.

    KAYAN NOKTA HATASI, GORUNUR SONUCU OLAN CINSTEN. `adil_paylar` payi
    tek tek toplayarak kurar; 1/3 gibi bir deger 63 kez toplandiginda sonuc
    21 degil 21.000000000000085 cikar. `ceil` bunu 22 yapar ve S2/S3/S4'un
    taban/tavan bandi [21,21] yerine [21,22] olur.

    Sonucu: PAYINI TAM TUTTURAN KISI BILE cezali gorunur
    (`max(21-21, 22-21, 0) = 1`) ve payinin altindaki herkesin sapmasi bir
    saat sisik cikar. Gercek veride olculdu: otuz kisilik havuzun on
    dokuzunda gece sapmasi birer saat fazla raporlaniyordu.
    """
    baglam = _uc_kisilik_baglam(3)
    paylar = baglam.adil_paylar(lambda _anahtar: True)

    for personel_id, pay in paylar.items():
        assert pay == pytest.approx(21.0), f"personel {personel_id}"
        # Asil iddia: taban ve tavan AYNI olmali, band bir nokta olmali.
        assert math.floor(pay) == 21, f"taban bozuk: {pay!r}"
        assert math.ceil(pay) == 21, f"tavan bir ust bande kacti: {pay!r}"
