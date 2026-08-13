"""Kurallarin dogrula ve modele_ekle metotlarinin paylastigi yardimcilar.

Butun gun bazli sayimlar bir noktada birlesir: bir blok BASLADIGI gune
sayilir (SRS TD-1). Ardisiklik, izin, haftalik tavan ve adalet hesaplarinin
tamami ayni tabani kullanmak zorundadir; ikisi ayrisirsa gece yarisini asan
bir blok bir kuralda bir gun, digerinde iki gun gorunur.
"""

from collections import defaultdict
from collections.abc import Callable, Iterable
from datetime import date, timedelta
from typing import Any

from ortools.sat.python import cp_model

from app.kurallar.baglam import AtamaKaydi, Baglam
from app.kurallar.temel import Ihlal


def personel_bazinda_sirali(atamalar: Iterable[AtamaKaydi]) -> dict[int, list[AtamaKaydi]]:
    """Her personelin bloklarini baslangic zamanina gore sirali dondurur (H2)."""
    gruplar: dict[int, list[AtamaKaydi]] = defaultdict(list)
    for atama in atamalar:
        gruplar[atama.personel_id].append(atama)
    for kayitlar in gruplar.values():
        kayitlar.sort(key=lambda a: a.baslangic)
    return dict(gruplar)


def calisilan_gunler(atamalar: Iterable[AtamaKaydi]) -> dict[int, set[date]]:
    """Her personelin calistigi gunler — blogun BASLADIGI gun (H4, H6, S7)."""
    gunler: dict[int, set[date]] = defaultdict(set)
    for atama in atamalar:
        gunler[atama.personel_id].add(atama.tarih)
    return dict(gunler)


def gece_gunleri(atamalar: Iterable[AtamaKaydi], gece_esigi_saat: int) -> dict[int, set[date]]:
    """H3'un GECE GUNU tanimi: gece saati esige ulasan gunler.

    Esik ergonomik yorumu tasir — iki saat gece calismak bir gece nobeti
    degildir (SRS TD-2). Olcu, blogun 20.00–06.00 araligiyla kesisiminin
    uzunlugudur ve gun blogun basladigi gundur.
    """
    gunler: dict[int, set[date]] = defaultdict(set)
    for atama in atamalar:
        if atama.gece_saati >= gece_esigi_saat:
            gunler[atama.personel_id].add(atama.tarih)
    return dict(gunler)


def gunluk_saat(atamalar: Iterable[AtamaKaydi]) -> dict[int, dict[date, float]]:
    """Her personelin gun basina calisma saati (H5, H9, H10).

    Blogun saatlerinin TAMAMI basladigi gune yazilir (TD-1); gece yarisini
    asan bir blogun ertesi gune tasan saatleri o gunun tavanini doldurmaz.
    """
    saatler: dict[int, dict[date, float]] = defaultdict(lambda: defaultdict(float))
    for atama in atamalar:
        saatler[atama.personel_id][atama.tarih] += atama.sure_saat
    return {personel_id: dict(gunler) for personel_id, gunler in saatler.items()}


def ardisik_kosu_ihlalleri(
    kural_kimlik: str,
    gunler_by_personel: dict[int, set[date]],
    sinir: int,
    aciklama_sablonu: str,
) -> list[Ihlal]:
    """Bir personelin ardisik takvim gunu kosusu sinir sayisini astiginda ihlal uretir (H3, H4).

    Kosu, sinirin ustune cikan her gun icin ayri raporlanir; boylece kac gun
    asildigi da gorulur.
    """
    ihlaller: list[Ihlal] = []
    for personel_id, gunler in gunler_by_personel.items():
        sirali = sorted(gunler)
        onceki_gun: date | None = None
        kosu = 0
        for gun in sirali:
            ardisik = onceki_gun is not None and gun == onceki_gun + timedelta(days=1)
            kosu = kosu + 1 if ardisik else 1
            if kosu > sinir:
                ihlaller.append(
                    Ihlal(
                        kural_kimlik=kural_kimlik,
                        personel_id=personel_id,
                        tarih=gun,
                        aciklama=aciklama_sablonu.format(kosu=kosu, sinir=sinir),
                    )
                )
            onceki_gun = gun
    return ihlaller


def kayan_pencere_ihlalleri(
    kural_kimlik: str,
    degerler_by_personel: dict[int, dict[date, float]],
    sinir: float,
    aciklama_sablonu: str,
) -> list[Ihlal]:
    """Her personelin 7 gunluk kayan penceresi sinir ustundeyse ihlal uretir (H5, H6).

    Yalnizca degeri sifirdan buyuk olan gunlerden baslayan pencereler
    kontrol edilir; bosla baslayan bir pencerenin toplami her zaman ondan
    sonraki calisilan-gun-baslangicli pencerenin toplamindan buyuk olamaz,
    dolayisiyla bu daraltma hicbir ihlali kacirmaz.
    """
    ihlaller: list[Ihlal] = []
    for personel_id, gunluk in degerler_by_personel.items():
        for pencere_baslangic in sorted(gunluk):
            toplam = sum(gunluk.get(pencere_baslangic + timedelta(days=i), 0) for i in range(7))
            if toplam > sinir:
                ihlaller.append(
                    Ihlal(
                        kural_kimlik=kural_kimlik,
                        personel_id=personel_id,
                        tarih=pencere_baslangic,
                        aciklama=aciklama_sablonu.format(toplam=toplam, sinir=sinir),
                    )
                )
    return ihlaller


def kayan_pencere_kisiti_ekle(
    model: cp_model.CpModel,
    baglam: Baglam,
    *,
    pencere_uzunlugu: int,
    gun_ifadesi: Callable[[int, date], Any],
    ust_sinir: int,
) -> None:
    """H4, H5, H6, H9'un ortak deseni: zaman ekseninin her N-gunluk ardisik
    penceresinde, gun basina bir ifadenin toplami bir ust siniri asamaz.

    `gun_ifadesi(p, g)` gunun kural acisindan tasidigi degeri verir ve HER
    ZAMAN blogun basladigi gune yazar (TD-1) - `Baglam.blok_saati` ya da
    `Baglam.calisti`. Duvar saatine dusen bir ifade bu deseni sessizce
    bozardi.
    """
    gunler = baglam.zaman_ekseni
    for i in range(len(gunler) - pencere_uzunlugu + 1):
        pencere = gunler[i : i + pencere_uzunlugu]
        for p in baglam.personel:
            toplam = sum(gun_ifadesi(p, g) for g in pencere)
            if not isinstance(toplam, int):
                model.add(toplam <= ust_sinir)


def takvim_haftalari(gunler: Iterable[date]) -> dict[date, list[date]]:
    """Gunleri AYRIK takvim haftalarina (pazartesi-pazar) toplar (SRS TD-14).

    Anahtar haftanin pazartesisidir. Yalnizca H10 (yillik fazla calisma
    kotasi) bunu kullanir.

    BU FONKSIYON `kayan_pencere_kisiti_ekle` ILE BIRLESTIRILMEMELIDIR ve
    ayri durmasi bilinclidir (TD-14, K9). Kayan pencere herhangi yedi ardisik
    gundur ve H4/H5/H6 onu kullanir; takvim haftasi ortusmeyen bir bolumdur
    ve yalniz H10 onu kullanir. Karismanin sonucu SESSIZDIR: kota "haftalik
    esigin ustunde calisilan saatlerin toplami" olarak tanimlidir ve bir
    toplam ancak ortusmeyen pencerelerde anlamlidir - kayan pencerede ayni
    saat yedi ayri pencereye girer, toplam yedi katina cikar ve kota
    gercekte asilmadan asilmis gorunur. Ters yonde de gecerli: takvim
    haftasina dayanan bir dinlenme kurali, pazar-pazartesi sinirinda yan
    yana iki yogun haftayi serbest birakir.
    """
    haftalar: dict[date, list[date]] = defaultdict(list)
    for gun in sorted(set(gunler)):
        haftalar[gun - timedelta(days=gun.weekday())].append(gun)
    return dict(haftalar)


__all__ = [
    "ardisik_kosu_ihlalleri",
    "calisilan_gunler",
    "gece_gunleri",
    "gunluk_saat",
    "kayan_pencere_ihlalleri",
    "kayan_pencere_kisiti_ekle",
    "personel_bazinda_sirali",
    "takvim_haftalari",
]
