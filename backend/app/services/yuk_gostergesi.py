"""FR-1.9: talep matrisinden haftalik yuk ve asgari kadro buyuklugu (SRS 3.3.6 yontemi).

Saf hesaplama; veritabanindan bagimsizdir (ORM nesneleri veri tasiyici olarak
kullanilir, sorgu calistirilmaz) - boylece SRS 3.3.6'daki referans ornekle
(144 kisi-vardiya, 1.152 saat, 29 kisilik asgari kadro) veritabani gerektirmeden
dogrulanabilir.
"""

from collections.abc import Sequence
from decimal import Decimal

from app.models.tanim import GunTipi, Talep, VardiyaTipi
from app.schemas.tanim import YukGostergesi

# Gun tipinin haftada kac kez tekrarlandigi. Resmi tatil donemsel/tekildir,
# her hafta tekrarlanmadigi icin haftalik yuke dahil edilmez.
_HAFTALIK_TEKRAR = {GunTipi.HAFTA_ICI: 5, GunTipi.HAFTA_SONU: 2, GunTipi.RESMI_TATIL: 0}


def yuk_gostergesi_hesapla(
    hucreler: Sequence[Talep],
    vardiya_tipleri: dict[int, VardiyaTipi],
    *,
    azami_haftalik_saat: Decimal,
    haftalik_asgari_izin_gunu: int,
) -> YukGostergesi:
    """Genel talep matrisini haftalik yuk ve asgari kadroya cevirir.

    Tekil tarih istisnalari (hucre.tarih dolu) haftalik yuke girmez; onlar
    donemin belirli bir gunune ozgudur, her hafta tekrarlanmaz.
    """
    haftalik_kisi_vardiya = 0
    haftalik_kisi_saat = Decimal(0)
    for hucre in hucreler:
        if hucre.tarih is not None:
            continue
        tekrar = _HAFTALIK_TEKRAR[hucre.gun_tipi]
        if tekrar == 0:
            continue
        haftalik_kisi_vardiya += hucre.gereken_sayi * tekrar
        vardiya = vardiya_tipleri.get(hucre.vardiya_tipi_id)
        if vardiya is not None:
            haftalik_kisi_saat += Decimal(hucre.gereken_sayi * tekrar) * vardiya.sure_saat

    asgari_kadro = _asgari_kadro_hesapla(
        haftalik_kisi_vardiya,
        haftalik_kisi_saat,
        azami_haftalik_saat=azami_haftalik_saat,
        haftalik_asgari_izin_gunu=haftalik_asgari_izin_gunu,
    )
    return YukGostergesi(
        haftalik_kisi_vardiya=haftalik_kisi_vardiya,
        haftalik_kisi_saat=haftalik_kisi_saat,
        asgari_kadro=asgari_kadro,
    )


def _asgari_kadro_hesapla(
    haftalik_kisi_vardiya: int,
    haftalik_kisi_saat: Decimal,
    *,
    azami_haftalik_saat: Decimal,
    haftalik_asgari_izin_gunu: int,
) -> int:
    """SRS 3.3.6: kisi basina azami haftalik vardiya, H5 (saat tavani) ve H6
    (asgari izin gunu) kisitlarinin ikisinden de turetilip kucuk olani alinir;
    asgari kadro toplam kisi-vardiyanin buna bolumunun tavana yuvarlanmasidir.
    """
    if haftalik_kisi_vardiya <= 0:
        return 0

    gun_bazli_azami = 7 - haftalik_asgari_izin_gunu
    ortalama_sure = haftalik_kisi_saat / haftalik_kisi_vardiya if haftalik_kisi_saat > 0 else 0
    if ortalama_sure > 0 and azami_haftalik_saat > 0:
        saat_bazli_azami = int(azami_haftalik_saat / ortalama_sure)
        kisi_basina_azami = min(saat_bazli_azami, gun_bazli_azami)
    else:
        kisi_basina_azami = gun_bazli_azami

    if kisi_basina_azami <= 0:
        return 0
    return -(-haftalik_kisi_vardiya // kisi_basina_azami)  # tavana yuvarlanan tam sayi bolme
