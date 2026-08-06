"""H1-H8 dogrula metotlarinin paylastigi kucuk yardimci fonksiyonlar."""

from collections import defaultdict
from collections.abc import Iterable
from datetime import date, timedelta

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


__all__ = [
    "ardisik_kosu_ihlalleri",
    "calisilan_gunler",
    "gece_calisilan_gunler",
    "gunluk_saat",
    "kayan_pencere_ihlalleri",
    "personel_bazinda_sirali",
]
