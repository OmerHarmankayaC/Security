"""Zaman araliginin saat eksenine acilimi — TEK TANIM.

Hem talep kayitlari (SDD 4.2.2) hem calisma bloklari (4.2.1) bir
`(baslangic, bitis)` ciftidir ve ikisi de ayni saat eksenine acilir. Acilim
kuralinin iki yerde yazilmasi, kapsama kisitinin talebi bir sinirda dahil
edip atamayi etmemesine yol acardi; bu projede ayni hesabin iki yerde
durmasinin bedeli birkac kez odenmistir.

ARALIK SINIRLARI baslangicta KAPALI, bitiste ACIKTIR: `08.00-16.00` araligi
08, 09, … 15 saatlerini kapsar, 16'yi kapsamaz. Boylece `08.00-16.00` ve
`16.00-24.00` cakismadan bitisir (SDD 5.3).

GUN SONU `00.00` ILE YAZILIR. SDD `24.00` diyor; PostgreSQL o degeri
saklayabiliyor fakat surucu `datetime.time` olarak geri okuyamiyor - 24:00
Python'da yok (denendi: `DataError: hour must be in 0..23`). Bunun yerine
`vardiya_tipi` tablosunun ZATEN kullandigi sozlesme uygulanir:
`bitis <= baslangic` ise aralik gun sonuna kadar surer ve gece yarisini
asiyorsa ertesi gunun saatlerine tasar.

Modul ORM'den ve veritabanindan bagimsizdir; kural birim testleri onu elle
kurulan orneklerle cagirabilir.
"""

from collections.abc import Iterator, Mapping
from datetime import date, time, timedelta


def aralik_sure_saat(baslangic: time, bitis: time) -> int:
    """Araligin saat cinsinden uzunlugu.

    `bitis == baslangic` TUM GUNU gosterir (24 saat): `00.00-24.00` araligi
    veritabaninda `00:00-00:00` olarak durur.
    """
    fark = (bitis.hour - baslangic.hour) % 24
    return fark if fark != 0 else 24


def aralik_saatleri(tarih: date, baslangic: time, bitis: time) -> Iterator[tuple[date, int]]:
    """Araligin kapsadigi (gun, saat) DUVAR SAATI dilimleri.

    Baslangic dahil, bitis haric. Gece yarisini asan aralik ertesi gunun
    saatlerine tasar.
    """
    for kayma in range(aralik_sure_saat(baslangic, bitis)):
        mutlak = baslangic.hour + kayma
        yield tarih + timedelta(days=mutlak // 24), mutlak % 24


def saat_kumesi(baslangic: time, bitis: time) -> frozenset[int]:
    """Araligin kapsadigi GUNLUK saat kumesi (0-23), gunden bagimsiz.

    Cakisma denetiminin tabani: gece yarisini asan aralik da tek bir kume
    olarak ifade edilir (22.00-02.00 -> {22, 23, 0, 1}).
    """
    return frozenset(
        (baslangic.hour + kayma) % 24 for kayma in range(aralik_sure_saat(baslangic, bitis))
    )


def cakisiyor_mu(b1: time, s1: time, b2: time, s2: time) -> bool:
    """Iki aralik ortak bir saat tasiyor mu? (SDD 4.2.2)

    Cakisan iki talep kaydi ayni saat icin iki farkli gereken sayi uretir ve
    hangisinin gecerli oldugu tanimsiz kalir; bu yuzden girise kapali.
    """
    return bool(saat_kumesi(b1, s1) & saat_kumesi(b2, s2))


def tam_saat_mi(an: time) -> bool:
    """Saat ekseni saat basindadir; yarim saatlik sinirlar tanimli degildir."""
    return an.minute == 0 and an.second == 0 and an.microsecond == 0


def saatleri_araliklara_birlestir(
    saat_sayilari: Mapping[tuple[date, int], int],
) -> list[tuple[date, time, time, int]]:
    """Ardisik ve SAYISI ESIT saatleri tek araliga toplar (SDD 4.2.4).

    `(tarih, saat) -> sayi` alir, `(tarih, baslangic, bitis, sayi)` listesi
    dondurur. 00, 01, … 07 saatlerinde 1 kisi eksikse tek bir
    `00.00-08.00 / 1` kaydi cikar, sekiz satir degil: yirmi dort satirlik
    bir liste kullaniciya hicbir sey anlatmaz.

    Birlestirme GUN ICINDE kalir. Gun sinirini asan bir birlestirme
    (22.00-02.00) `bitis <= baslangic` sozlesmesiyle gosterilebilirdi, ama
    okuyan tarafin "bu kayit hangi gune ait" sorusunu ikinci kez sormasi
    gerekirdi; gun basina ayri kayit belirsizlik birakmaz.

    Sayisi sifir olan saatler kayit uretmez.
    """
    araliklar: list[tuple[date, time, time, int]] = []
    for tarih, saat in sorted(saat_sayilari):
        sayi = saat_sayilari[(tarih, saat)]
        if sayi <= 0:
            continue
        if araliklar:
            onceki_tarih, onceki_bas, onceki_bitis, onceki_sayi = araliklar[-1]
            bitisik = onceki_tarih == tarih and onceki_bitis.hour == saat
            # Gun sonuna dayanmis bir aralik (bitis 00.00) artik uzatilamaz.
            gun_sonuna_dayandi = onceki_bitis.hour == 0 and onceki_bas.hour != 0
            if bitisik and onceki_sayi == sayi and not gun_sonuna_dayandi:
                araliklar[-1] = (onceki_tarih, onceki_bas, _saat(saat + 1), sayi)
                continue
        araliklar.append((tarih, _saat(saat), _saat(saat + 1), sayi))
    return araliklar


def _saat(deger: int) -> time:
    """Saat degerini `time`a cevirir; 24 gun sonunu gosterir ve 00.00 yazilir."""
    return time(deger % 24)
