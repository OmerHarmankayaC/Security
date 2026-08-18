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
Python'da yok (denendi: `DataError: hour must be in 0..23`). Uygulanan
sozlesme tektir: `bitis <= baslangic` ise aralik gun sonuna kadar surer ve
gece yarisini asiyorsa ertesi gunun saatlerine tasar.

Modul ORM'den ve veritabanindan bagimsizdir; kural birim testleri onu elle
kurulan orneklerle cagirabilir.
"""

from collections.abc import Iterable, Iterator, Mapping
from datetime import date, datetime, time, timedelta
from typing import TypeVar

# Bir saatin "hangi kosuya ait oldugunu" belirleyen deger: kapsama aciginda
# eksik sayisi, blok toplamada gorev noktasi.
Etiket = TypeVar("Etiket")


def aralik_sure_saat_damga(baslangic: datetime, bitis: datetime) -> int:
    """Iki damga arasindaki saat sayisi. Damga aralikta gun sinirini kendisi
    tasidigi icin burada mod aritmetigi YOKTUR - `aralik_sure_saat`in
    `time` uzerinde yapmak zorunda oldugu tahmin ortadan kalkar."""
    return round((bitis - baslangic).total_seconds() / 3600)


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


def ardisik_saatleri_grupla(
    etiketli_saatler: Iterable[tuple[int, Etiket]], *, gun_sinirinda_kes: bool
) -> list[tuple[int, int, Etiket]]:
    """Ardisik ve ETIKETI AYNI saatleri tek kosuya toplar — TEK TANIM.

    `(mutlak_saat, etiket)` cifti alir, `(ilk_saat, son_saat, etiket)`
    listesi dondurur. Mutlak saat, gun sinirini asan kosularin dogal
    ifadesidir: `tarih.toordinal() * 24 + saat`.

    IKI TUKETICI, TEK BIRLESTIRME. Kapsama acigi kayitlari ardisik ve
    EKSIK SAYISI esit saatleri araliga toplar (SDD 4.2.4); cozucu ciktisi
    ardisik ve NOKTASI ayni saatleri bloga toplar (SDD 4.2.1). Ikisi de
    ayni sorunun ayni yaniti - "ardisik ve ayni olanlar tek kayit" - ve
    ikinci bir kopya yazilsaydi biri gun sinirinda kesip digeri kesmedigi
    icin ayrisirlardi.

    `gun_sinirinda_kes` ikisini ayiran TEK parametredir:

    - **Kapsama acigi True verir.** Gun sinirini asan bir aralik
      (22.00-02.00) `bitis <= baslangic` sozlesmesiyle gosterilebilirdi,
      ama okuyan tarafin "bu kayit hangi gune ait" sorusunu ikinci kez
      sormasi gerekirdi; gun basina ayri kayit belirsizlik birakmaz.
    - **Blok toplama False verir.** Gece yarisini asan calisma TEK KAYITTA
      durmak zorundadir (SDD 4.2.1); kesilmesi halinde 20.00-06.00 blogu
      iki atama satiri olur ve H1 ile TD-1 kayitta gorunmez hale gelir.
    """
    kosular: list[tuple[int, int, Etiket]] = []
    for saat, etiket in sorted(etiketli_saatler, key=lambda oge: oge[0]):
        if kosular:
            ilk, son, onceki_etiket = kosular[-1]
            bitisik = son + 1 == saat and onceki_etiket == etiket
            gun_degisti = gun_sinirinda_kes and saat % 24 == 0
            if bitisik and not gun_degisti:
                kosular[-1] = (ilk, saat, etiket)
                continue
        kosular.append((saat, saat, etiket))
    return kosular


def mutlak_saat(tarih: date, saat: int) -> int:
    """`(tarih, saat)` ciftinin gun sinirindan bagimsiz sirali karsiligi."""
    return tarih.toordinal() * 24 + saat


def saatleri_araliklara_birlestir(
    saat_sayilari: Mapping[tuple[date, int], int],
) -> list[tuple[datetime, datetime, int]]:
    """Ardisik ve SAYISI ESIT saatleri tek araliga toplar (SDD 4.2.4).

    `(tarih, saat) -> sayi` alir, `(baslangic_zamani, bitis_zamani, sayi)`
    listesi dondurur. 00, 01, … 07 saatlerinde 1 kisi eksikse tek bir
    `00.00-08.00 / 1` kaydi cikar, sekiz satir degil: yirmi dort satirlik
    bir liste kullaniciya hicbir sey anlatmaz.

    GUN SINIRINDA ARTIK KESILMEZ (Tur 8, B-23). Kayitlar tarih + ofsetsiz
    saat olarak durdugu surece 22.00-02.00 gibi bir aralik tek satirda
    gosterilemiyordu ve gun basina bolunuyordu; okuyan taraf da "bu kayit
    hangi gune ait" sorusunu ikinci kez sormak zorunda kaliyordu. Kayit
    zaman damgasina tasindiktan sonra aralik kendini tasiyor ve bolme
    gereksizlesti - kesilmeye devam etseydi dosyada iki ayri acik gorunur,
    oysa tek bir acik vardir.

    Sayisi sifir olan saatler kayit uretmez.
    """
    etiketli = [
        (mutlak_saat(tarih, saat), sayi)
        for (tarih, saat), sayi in saat_sayilari.items()
        if sayi > 0
    ]
    return [
        (_an(ilk), _an(son + 1), sayi)
        for ilk, son, sayi in ardisik_saatleri_grupla(etiketli, gun_sinirinda_kes=False)
    ]


def _an(mutlak: int) -> datetime:
    """Mutlak saati zaman damgasina cevirir; gun siniri kendiliginden asilir."""
    return datetime.combine(date.fromordinal(mutlak // 24), time(mutlak % 24))


def _saat(deger: int) -> time:
    """Saat degerini `time`a cevirir; 24 gun sonunu gosterir ve 00.00 yazilir."""
    return time(deger % 24)


def saat_metni(an: time, *, bitis: bool = False) -> str:
    """Saati "08.00" bicimiyle yazar. TEK TANIM.

    Gun sonu depoda 00.00 durur (SDD 4.2.2) ve kullaniciya 24.00 gosterilir
    - ama YALNIZCA BITIS olarak. Ayrimi tasimayan bir yardimci, gun basinda
    baslayan bir araligi "24.00-08.00" diye yazar; okuyan kisi bunu gece
    yarisini asan bir aralik sanir. Uc ayri modul bu yardimcinin kendi
    kopyasini tasiyordu ve ucu de ayni yanlisi yapiyordu.
    """
    return "24.00" if bitis and an.hour == 0 else f"{an.hour:02d}.00"


def aralik_metni(baslangic: time, bitis: time) -> str:
    """ "08.00–24.00" — arayuze ve bulgu metinlerine giden bicim."""
    return f"{saat_metni(baslangic)}–{saat_metni(bitis, bitis=True)}"


# Gece donemi (SRS TD-2, K5): 20:00-06:00. Yarim acik aralik - 06 saati
# gece degildir, 20 saati gecedir.
GECE_BASLANGIC_SAATI = 20
GECE_BITIS_SAATI = 6
GECE_SAATLERI: frozenset[int] = frozenset(
    (GECE_BASLANGIC_SAATI + kayma) % 24
    for kayma in range((GECE_BITIS_SAATI - GECE_BASLANGIC_SAATI) % 24)
)


def gece_saati_mi(saat: int) -> bool:
    """Duvar saati gece donemine (20:00-06:00) dusuyor mu?"""
    return saat in GECE_SAATLERI


def gece_saat_sayisi(baslangic: time, bitis: time) -> int:
    """`|aralik ∩ [20:00, 06:00]|` — TEK TANIM (SRS TD-2).

    GECE HESAPLANIR, ISARETLENMEZ. Onceki surumlerde calisma zamani bir
    katalogdan secildigi icin gece bilgisi vardiya tipi uzerinde `gece_mi`
    BAYRAGI olarak duruyordu ve bayragin otomatik hesaplanan bir oneriyle
    ezilmesi bir kez yasanip K3'un karsilanmamasinin iki nedeninden biri
    olmustu. Blok katalogu kalktigi icin isaretlenecek bir nesne de
    kalmamistir; risk artik YAPISAL OLARAK yoktur, cunku tek tanim vardir.

    Iki tuketici ayni tabandan beslenir: H3 bir gunun gece gunu sayilip
    sayilmadigini (esige ulasiyor mu), S2 kisinin tasidigi gece yukunu
    okur.

    Olcu saat olmak zorunda: on iki saatlik bir gece blogu ile sekiz
    saatlik bir gece blogunu adalet hesabinda ayni saymak, uzun blogu alan
    personelin dort saatlik fazla yukunu olcuye hic sokmaz.
    """
    return sum(
        1
        for kayma in range(aralik_sure_saat(baslangic, bitis))
        if gece_saati_mi((baslangic.hour + kayma) % 24)
    )


def baslangic_kaymasi(onceki: time, sonraki: time) -> int:
    """Iki blogun baslangic saatleri arasindaki DAIRESEL fark (SRS 4.3 S6).

    `min(|Δ|, 24 − |Δ|)`. Dairesellik zorunlu: 22.00 ile 02.00 arasindaki
    kayma dort saattir, yirmi saat degil. Duz cikarma kullanan bir olcu,
    gece bloklari arasindaki en kucuk gecisleri en buyuk ceza gibi
    gosterirdi.
    """
    fark = abs(sonraki.hour - onceki.hour)
    return min(fark, 24 - fark)
