"""Resmi tatil takvimi — TEK KAYNAK (SRS FR-1.10).

NEDEN KUTUPHANE. Turkiye'nin resmi tatilleri iki kumeye ayrilir: sabit
tarihli ulusal bayramlar (1 Ocak, 23 Nisan, 1 Mayis, 19 Mayis, 15 Temmuz,
30 Agustos, 29 Ekim) ve tarihi HICRI TAKVIME bagli dini bayramlar (Ramazan,
Kurban). Ikincisi her yil yaklasik on bir gun geriye kayar ve cok gunludur.

Onceki surumde gosterim ureteci yalnizca sabit tarihli olanlari yaziyor,
dini bayramlari bilincli olarak disarida birakiyordu; gerekcesi de yaziliydi:
"gosterim verisine tahmini bir tarih yazmak, dogru sanilan yanlis bir veri
uretirdi". Itiraz dogruydu, cozumu eksikti — tarihleri ELLE yazmamak ile
tarihleri HIC yazmamak ayni sey degil. Kutuphane ucuncu yolu acar: tarihler
hesaplanir, elle bakim gerektirmez ve yil donunce eskimez.

TALEBI DOGRUDAN ETKILER. Talep matrisi RESMI_TATIL gun tipi tasir
(SRS 3.3.4); burada uretilen her gun, o gunun kadro ihtiyacini hafta
sonu/tatil satirlarina dusurur ve TD-3 uyarinca adalet sayaclarinda hafta
sonuyla ayni sayaca eklenir. Yani bu liste bir gosterim ayrintisi degil,
cozucunun girdisidir.

KULLANICI SON SOZU SOYLER. Uretilen gunler `ozel_gun` tablosuna yazilir ve
oradan Ozel Gun ekraniyla duzenlenebilir/silinebilir (FR-1.10): kurum kendi
idari izin gunlerini ekleyebilir, uygulanmayan bir gunu kaldirabilir.
Takvim bir baslangic noktasidir, degistirilemez bir dogru degil.
"""

from collections.abc import Iterable
from datetime import date

import holidays

# Kutuphanenin Turkiye takvimi. Dil TURKCE secilir: varsayilan Ingilizce
# adlar ("Republic Day") Ozel Gun ekraninda dogrudan kullaniciya gorunur.
_ULKE = "TR"
_DIL = "tr"


def resmi_tatiller(yillar: Iterable[int]) -> list[tuple[date, str]]:
    """Verilen yillarin resmi tatilleri, tarihe gore sirali.

    Cok gunlu bayramlar GUN GUN dondurulur (Kurban Bayrami dort satirdir):
    talep matrisi ve adalet sayaclari gun bazinda calisir, aralik bazinda
    degil.
    """
    takvim = holidays.country_holidays(_ULKE, years=list(yillar), language=_DIL)
    return sorted(takvim.items())


def yil_araligi(baslangic: date, bitis: date) -> list[int]:
    """Iki tarihin kapsadigi yillar.

    Ayri bir yardimci, cunku donem araligi yil sinirini asabilir ve tek yil
    istemek sessizce eksik takvim uretirdi: aralikta 1 Ocak varsa onceki
    yilin son gunleri ile yeni yilin ilk gunleri farkli yillara duser.
    """
    return list(range(baslangic.year, bitis.year + 1))
