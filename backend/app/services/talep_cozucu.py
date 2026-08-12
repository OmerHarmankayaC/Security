"""Talebin cozumlenmesi ve SAATE ACILIMI — TEK YER (SDD 5.3).

Iki asama vardir:

  1. **Cozumleme.** Bir gun icin gecerli talep satirlari belirlenir: once o
     tarihe ozgu istisna satirlari aranir, bulunamazsa gun tipine karsilik
     gelen genel satirlar kullanilir. Karisim YAPILMAZ - bir tarih icin
     istisna satiri varsa o gunun talebi yalnizca istisna satirlarindan
     olusur (SDD 4.2.2).
  2. **Acilim.** Zaman araligi kayitlari saat eksenine acilir:
     `talep_saat[gun, saat, nokta]`.

ACILIM TEK BU MODULDE YAPILIR. Bes tuketici ayni ciktiyi kullanir: model
kurucu, on kontrol, dogrulayici, analiz servisi ve kabul olcumu. Her
tuketicinin kendi acilimini yazmasi halinde arali sinirlarinin kapaliligi
gibi bir ayrintida ayrisirlar ve ayni cizelge icin farkli kapsama orani
raporlarlar; bu projede ayni hesabin iki yerde durmasinin bedeli birkac kez
odenmistir.

ARALIK SINIRLARI baslangicta KAPALI, bitiste ACIKTIR: `08.00-16.00` araligi
08, 09, … 15 saatlerini kapsar, 16'yi kapsamaz. Boylece `08.00-16.00` ve
`16.00-24.00` cakismadan bitisir.

GUN SONU `00.00` ILE YAZILIR. SDD 4.2.2 `24.00` diyor; PostgreSQL o degeri
saklayabiliyor fakat surucu `datetime.time` olarak geri okuyamiyor (24:00
Python'da yok). `vardiya_tipi`nin zaten kullandigi sozlesme uygulanir:
`bitis <= baslangic` ise aralik gun sonuna kadar surer, gece yarisini
asiyorsa ERTESI GUNUN saatlerine tasar. Talepte tasan saatler ertesi gunun
duvar saatleridir - bir noktanin 03.00'te dolu olmasi gerekiyorsa bu, o
saati kapsayan blogun hangi gun basladigindan bagimsiz bir gereksinimdir.
"""

from collections.abc import Iterable, Sequence
from datetime import date

from app.kurallar.baglam import VardiyaTipiBilgisi
from app.kurallar.zaman_araligi import aralik_saatleri
from app.models.tanim import GunTipi, Talep

# (tarih, saat, nokta_id) -> gereken_sayi
TalepSaat = dict[tuple[date, int, int], int]


def gun_tipi_belirle(tarih: date, ozel_gunler: frozenset[date]) -> GunTipi:
    """TD-3: ozel gun ise resmi tatil, cumartesi/pazar ise hafta sonu, aksi hafta ici."""
    if tarih in ozel_gunler:
        return GunTipi.RESMI_TATIL
    if tarih.weekday() >= 5:
        return GunTipi.HAFTA_SONU
    return GunTipi.HAFTA_ICI


def talebi_saate_ac(
    talep_satirlari: Sequence[Talep],
    zaman_ekseni: Sequence[date],
    ozel_gunler: frozenset[date],
) -> TalepSaat:
    """SDD 5.3: `talep_saat[gun, saat, nokta]`.

    `zaman_ekseni` ISITMA PENCERESINI DE kapsamalidir (TD-5): model kurucu
    karar degiskenlerini o pencerede de uretir ve talebi sifir gorurse o
    gunlere hic degisken acmaz.

    Ayni (nokta, saat) icin birden fazla satir denk gelirse EN BUYUK deger
    alinir. Cakisan araliklar uygulama katmaninda zaten reddedilir (SDD
    4.2.2); buradaki secim, gecmiste girilmis cakisan bir kaydin talebi
    sessizce DUSURMEMESI icindir - sessiz veri kaybi bu projede tekrarlayan
    bir kalip.
    """
    gunler = set(zaman_ekseni)
    istisna_gunleri = {s.tarih for s in talep_satirlari if s.tarih is not None}

    talep_saat: TalepSaat = {}
    for satir in talep_satirlari:
        for gun in _satirin_gunleri(satir, gunler, istisna_gunleri, ozel_gunler):
            for saat_gunu, saat in aralik_saatleri(gun, satir.baslangic, satir.bitis):
                anahtar = (saat_gunu, saat, satir.nokta_id)
                if satir.gereken_sayi > talep_saat.get(anahtar, 0):
                    talep_saat[anahtar] = satir.gereken_sayi
    return talep_saat


def _satirin_gunleri(
    satir: Talep,
    gunler: set[date],
    istisna_gunleri: set[date],
    ozel_gunler: frozenset[date],
) -> Iterable[date]:
    """Bir talep satirinin gecerli oldugu gunler.

    Istisna satiri yalnizca kendi tarihinde gecerlidir. Genel satir ise o
    gun tipindeki gunlerde gecerlidir - AMA istisna satiri bulunan bir gunde
    DEGIL: bir tarih icin istisna varsa o gunun talebi yalnizca istisna
    satirlarindan olusur (SDD 4.2.2).
    """
    if satir.tarih is not None:
        if satir.tarih in gunler:
            yield satir.tarih
        return
    for gun in gunler:
        if gun in istisna_gunleri:
            continue
        if gun_tipi_belirle(gun, ozel_gunler) is satir.gun_tipi:
            yield gun


def blok_gorunumu_uret(
    talep_saat: TalepSaat,
    vardiya_tipleri: dict[int, VardiyaTipiBilgisi],
) -> dict[tuple[date, int, int], int]:
    """Saat eksenli talebin BLOK eksenli turevi: `(gun, blok, nokta) -> gereken`.

    GECICI BIR UYUM KATMANIDIR. S2, S3 ve S4 talebi hala VARDIYA biriminde
    okuyor (`hedef_gece = Σ talep / |havuz|`, `Σ sure_saat × gereken`) ve bu
    turda kural katalogu degismiyor. Talep dogrudan saate cevrilseydi
    S2/S3'un hedefi sekiz katina cikar ve ayni donem ayni cezayi vermezdi.
    Tur 4'te S2/S3 saat birimine gecince bu turev kalkar.

    Ikinci bir TANIM degildir: tek kaynak `talep_saat`tir, buradaki islem
    ondan tek yerde yapilan bir TUREVDIR. Bir blogun gereken sayisi,
    kapsadigi saatlerdeki EN BUYUK gerekendir; talep araliklari blok
    sinirlariyla hizali oldugunda (bu turdaki uc bloklu katalog) bu deger
    blogun her saatinde ayni olur ve blok eksenli eski tablonun birebir
    aynisini verir.

    VARSAYIM - TEK UZUNLUKLU, HIZALI KATALOG. "En buyuk gereken" ancak
    boyle dogrudur. Tur 4'te 10 ve 12 saatlik bloklar girdiginde bir blok
    farkli gerekenler tasiyan saatleri kapsayacak (orn. 06.00-18.00 blogu,
    gece 3 ve gunduz 7 kisilik talebi birlikte orter) ve turev o blogu 7
    kisilik sayacak: fazla kadro talep gibi gorunur, HATA VERMEDEN. Bu
    fonksiyon o turda kalkmalidir, duzeltilmemelidir - dogru cozum S2/S3'u
    saat eksenine tasimaktir.
    """
    gunler = {tarih for (tarih, _saat, _nokta) in talep_saat}
    noktalar = {nokta for (_tarih, _saat, nokta) in talep_saat}
    gorunum: dict[tuple[date, int, int], int] = {}
    for gun in gunler:
        for blok_id, blok in vardiya_tipleri.items():
            dilimler = list(aralik_saatleri(gun, blok.baslangic_saati, blok.bitis_saati))
            for nokta in noktalar:
                gereken = max(
                    (talep_saat.get((d, s, nokta), 0) for d, s in dilimler),
                    default=0,
                )
                if gereken > 0:
                    gorunum[(gun, blok_id, nokta)] = gereken
    return gorunum
