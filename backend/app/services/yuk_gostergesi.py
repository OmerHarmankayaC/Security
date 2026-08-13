"""FR-1.9: talepten haftalik kisi-saat yuku ve asgari kadro (SRS 3.3.6 yontemi).

Saf hesaplama; veritabanindan bagimsizdir (ORM nesneleri veri tasiyici olarak
kullanilir, sorgu calistirilmaz) - boylece SRS 3.3.6'daki referans ornekle
(1.152 kisi-saat, 26 kisilik asgari kadro) veritabani gerektirmeden
dogrulanabilir.
"""

from collections.abc import Sequence
from decimal import Decimal

from app.kurallar.zaman_araligi import aralik_sure_saat
from app.models.tanim import GunTipi, Talep
from app.schemas.tanim import YukGostergesi
from app.services.kadro_hesaplari import asgari_kadro_hesapla

# Gun tipinin haftada kac kez tekrarlandigi. Resmi tatil donemsel/tekildir,
# her hafta tekrarlanmadigi icin haftalik yuke dahil edilmez.
_HAFTALIK_TEKRAR = {GunTipi.HAFTA_ICI: 5, GunTipi.HAFTA_SONU: 2, GunTipi.RESMI_TATIL: 0}


def yuk_gostergesi_hesapla(
    talep_satirlari: Sequence[Talep],
    *,
    fazla_calisma_esigi: Decimal,
    azami_gunluk_saat: Decimal,
    haftalik_asgari_izin_gunu: int,
) -> YukGostergesi:
    """Genel talep tanimini haftalik kisi-saat yuku ve asgari kadroya cevirir.

    Tekil tarih istisnalari (satir.tarih dolu) haftalik yuke girmez; onlar
    donemin belirli bir gunune ozgudur, her hafta tekrarlanmaz.

    BLOK KATALOGU BU HESABA HIC GIRMEZ. Talep bir zaman araligidir (SDD
    4.2.2) ve yuk, araligin uzunlugu ile gereken sayinin carpimidir. Onceki
    hal kisi-vardiya sayisini da uretiyor ve bunu katalogun ORTALAMA blok
    uzunluguna bolerek buluyordu; karisik uzunluklu katalogda o sayi
    katalogun bilesimine gore degisir, talep degismese bile - bu yuzden
    kaldirildi (FR-1.9).
    """
    haftalik_kisi_saat = Decimal(0)
    for satir in talep_satirlari:
        if satir.tarih is not None:
            continue
        tekrar = _HAFTALIK_TEKRAR[satir.gun_tipi]
        if tekrar == 0:
            continue
        sure = aralik_sure_saat(satir.baslangic, satir.bitis)
        haftalik_kisi_saat += Decimal(satir.gereken_sayi * tekrar * sure)

    return YukGostergesi(
        haftalik_kisi_saat=haftalik_kisi_saat,
        asgari_kadro=asgari_kadro_hesapla(
            haftalik_kisi_saat,
            fazla_calisma_esigi=fazla_calisma_esigi,
            azami_gunluk_saat=azami_gunluk_saat,
            haftalik_asgari_izin_gunu=haftalik_asgari_izin_gunu,
        ),
    )
