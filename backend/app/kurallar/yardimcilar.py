"""H1-H8 dogrula ve modele_ekle metotlarinin paylastigi kucuk yardimci fonksiyonlar."""

from collections import defaultdict
from collections.abc import Callable, Iterable
from datetime import date, timedelta

from ortools.sat.python import cp_model

from app.kurallar.baglam import AtamaKaydi, Baglam
from app.kurallar.temel import Ihlal


def personel_bazinda_sirali(
    atamalar: Iterable[AtamaKaydi], baglam: Baglam
) -> dict[int, list[AtamaKaydi]]:
    """Her personelin atamalarini vardiya baslangic zamanina gore sirali dondurur (H2)."""
    gruplar: dict[int, list[AtamaKaydi]] = defaultdict(list)
    for atama in atamalar:
        gruplar[atama.personel_id].append(atama)
    for kayitlar in gruplar.values():
        kayitlar.sort(key=lambda a: baglam.vardiya_araligi(a.tarih, a.vardiya_tipi_id)[0])
    return dict(gruplar)


def calisilan_gunler(atamalar: Iterable[AtamaKaydi]) -> dict[int, set[date]]:
    """Her personelin calistigi (herhangi bir vardiyada atandigi) gunler kumesi (H4, H6)."""
    gunler: dict[int, set[date]] = defaultdict(set)
    for atama in atamalar:
        gunler[atama.personel_id].add(atama.tarih)
    return dict(gunler)


def gece_calisilan_gunler(atamalar: Iterable[AtamaKaydi], baglam: Baglam) -> dict[int, set[date]]:
    """Her personelin gece vardiyasi tuttugu gunler kumesi (H3)."""
    gunler: dict[int, set[date]] = defaultdict(set)
    for atama in atamalar:
        if baglam.gece_mi(atama.vardiya_tipi_id):
            gunler[atama.personel_id].add(atama.tarih)
    return dict(gunler)


def gunluk_saat(atamalar: Iterable[AtamaKaydi], baglam: Baglam) -> dict[int, dict[date, float]]:
    """Her personelin gun basina toplam calisma saati (H5)."""
    saatler: dict[int, dict[date, float]] = defaultdict(lambda: defaultdict(float))
    for atama in atamalar:
        saatler[atama.personel_id][atama.tarih] += baglam.sure_saat(atama.vardiya_tipi_id)
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
    vardiyalar: Iterable[int],
    agirlik_fn: Callable[[int], int],
    ust_sinir: int,
) -> None:
    """H3, H4, H5, H6'nin ortak deseni: zaman_ekseninin her N-gunluk ardisik
    penceresinde, verilen vardiya alt kumesi uzerinden agirlikli y toplami
    bir ust siniri asamaz. zaman_ekseninin ardisik takvim gunlerinden olustugu
    varsayilir (model_kur bunu boyle kurar).
    """
    gunler = baglam.zaman_ekseni
    vardiyalar = list(vardiyalar)
    for i in range(len(gunler) - pencere_uzunlugu + 1):
        pencere = gunler[i : i + pencere_uzunlugu]
        for p in baglam.personel:
            toplam = sum(agirlik_fn(v) * baglam.y[(p, g, v)] for g in pencere for v in vardiyalar)
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
    "gece_calisilan_gunler",
    "gunluk_saat",
    "kayan_pencere_ihlalleri",
    "kayan_pencere_kisiti_ekle",
    "personel_bazinda_sirali",
    "takvim_haftalari",
]
