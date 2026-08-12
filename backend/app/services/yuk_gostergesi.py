"""FR-1.9: talep matrisinden haftalik yuk ve asgari kadro buyuklugu (SRS 3.3.6 yontemi).

Saf hesaplama; veritabanindan bagimsizdir (ORM nesneleri veri tasiyici olarak
kullanilir, sorgu calistirilmaz) - boylece SRS 3.3.6'daki referans ornekle
(144 kisi-vardiya, 1.152 saat, 29 kisilik asgari kadro) veritabani gerektirmeden
dogrulanabilir.
"""

from collections.abc import Sequence
from decimal import Decimal

from app.kurallar.zaman_araligi import aralik_sure_saat
from app.models.tanim import GunTipi, Talep, VardiyaTipi
from app.schemas.tanim import YukGostergesi
from app.services.kadro_hesaplari import kisi_basina_azami_haftalik_vardiya

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
    # KISI-SAAT ARTIK DOGRUDAN OLCULUR. Talep bir zaman araligidir (SDD
    # 4.2.2); yuk, araligin uzunlugu ile gereken sayinin carpimidir ve
    # blok kataloguna hic bakmaz.
    haftalik_kisi_saat = Decimal(0)
    for hucre in hucreler:
        if hucre.tarih is not None:
            continue
        tekrar = _HAFTALIK_TEKRAR[hucre.gun_tipi]
        if tekrar == 0:
            continue
        sure = aralik_sure_saat(hucre.baslangic, hucre.bitis)
        haftalik_kisi_saat += Decimal(hucre.gereken_sayi * tekrar * sure)

    # KISI-VARDIYA TUREVDIR. Asgari kadro hesabi kisi basina azami VARDIYA
    # sayisindan gecer (SRS 3.3.6) ve bu, tam sayi vardiya varsayimini
    # tasir: sekiz saatlik bloklarla haftada 45 saat, 5,6 degil BES vardiya
    # eder. Talep artik blok tasimadigi icin kisi-vardiya, kisi-saatin
    # katalogdaki ORTALAMA blok uzunluguna bolunmesiyle bulunur; tek
    # uzunluklu katalogda (bu turdaki uc blok) bolum tamdir ve SRS
    # 3.3.6'daki referans ornegi birebir verir (1.152 saat / 8 = 144
    # kisi-vardiya, 29 kisilik asgari kadro).
    ortalama_blok = _ortalama_blok_suresi(vardiya_tipleri)
    haftalik_kisi_vardiya = int(-(-haftalik_kisi_saat // ortalama_blok)) if ortalama_blok > 0 else 0

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


def _ortalama_blok_suresi(vardiya_tipleri: dict[int, VardiyaTipi]) -> Decimal:
    """Aktif blok katalogunun ortalama uzunlugu; katalog bossa sekiz saat.

    Katalog bos oldugunda da bir sayi uretilmesi gerekir: gosterge talep
    girilirken de okunuyor ve blok tanimlanmadan once sifira bolme
    olusurdu. Sekiz saat, sistemin ciktigi ucluk duzenin uzunlugudur.
    """
    sureler = [Decimal(v.sure_saat) for v in vardiya_tipleri.values() if v.aktif]
    if not sureler:
        return Decimal(8)
    return sum(sureler) / len(sureler)


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

    ortalama_sure = haftalik_kisi_saat / haftalik_kisi_vardiya if haftalik_kisi_saat > 0 else 0
    kisi_basina_azami = kisi_basina_azami_haftalik_vardiya(
        ortalama_sure,
        azami_haftalik_saat=azami_haftalik_saat,
        haftalik_asgari_izin_gunu=haftalik_asgari_izin_gunu,
    )
    if kisi_basina_azami <= 0:
        return 0
    return -(-haftalik_kisi_vardiya // kisi_basina_azami)  # tavana yuvarlanan tam sayi bolme
