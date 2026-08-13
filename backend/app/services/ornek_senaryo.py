"""SRS 3.3'teki guvenlik personeli ornek senaryosunun yapisal (DB'siz) tanimi.

Hem demo veri uretecinin (scripts/demo_veri_uret.py) hem de FR-1.9
dogrulama testinin (tests/test_yuk_gostergesi.py) ortak veri kaynagidir;
boylece iki yerde ayni tablo iki kez elle yazilip birbirinden sapmaz.
"""

from dataclasses import dataclass
from datetime import time

from app.models.tanim import GunTipi

GUVENLIK_GOREVI = "Güvenlik Görevi"
VARDIYA_SEFI = "Vardiya Şefi"
MURACAAT_GOREVLISI = "Müracaat Görevlisi"

GECE = "Gece"
GUNDUZ = "Gündüz"
AKSAM = "Akşam"


@dataclass(frozen=True, slots=True)
class NoktaTanimi:
    ad: str
    bina_adi: str | None
    onkosul_yetkinlik: str


# SRS 3.3.3 — Gorev Noktalari (surum 1.1: bina ayrimi kaldirildi, kapi ve kontrol
# odasi tek bir "Guvenlik" noktasinda birlesti — kontrol odasindaki personel zaten
# ayri bir meslek grubu degil, ayni yetkinlige sahip bir guvenlik gorevlisiydi).
# Sira, TALEP_ARALIKLARI ile index uzerinden eslenir.
NOKTA_TANIMLARI: tuple[NoktaTanimi, ...] = (
    NoktaTanimi("Vardiya Şefliği", None, VARDIYA_SEFI),
    NoktaTanimi("Güvenlik", None, GUVENLIK_GOREVI),
    NoktaTanimi("Müracaat", None, MURACAAT_GOREVLISI),
)

# SRS 3.3.4 — Talep, bir calisma bloguna DEGIL bir ZAMAN ARALIGINA baglidir.
# Her satir: (nokta_index, hafta ici araliklari, azaltilmis kadro sayisi).
# Azaltilmis kadro hafta sonu VE resmi tatilde gun boyu (00.00-24.00)
# gecerlidir - SRS 3.3.4 ikisini tek sutunda tutar.
#
# GUN SONU 00.00 ILE YAZILIR (SDD 4.2.2): `bitis <= baslangic` araligin gun
# sonuna kadar surdugunu gosterir.
_GUN_BASI = time(0, 0)
_SEKIZ = time(8, 0)

# nokta_index -> (hafta ici araliklari, azaltilmis kadro)
TALEP_ARALIKLARI: tuple[tuple[tuple[tuple[time, time, int], ...], int], ...] = (
    # Vardiya Şefliği: gun boyu bir kisi.
    (((_GUN_BASI, _GUN_BASI, 1),), 1),
    # Güvenlik: gunduz+aksam saatlerinde yedi, gece uc.
    (((_SEKIZ, _GUN_BASI, 7), (_GUN_BASI, _SEKIZ, 3)), 3),
    # Müracaat: yalnizca hafta ici gunduz saatlerinde acik.
    (((_SEKIZ, _GUN_BASI, 2),), 0),
)


@dataclass(frozen=True, slots=True)
class TalepAraligiTanimi:
    nokta_index: int
    gun_tipi: GunTipi
    baslangic: time
    bitis: time
    gereken_sayi: int


def talep_satirlarini_olustur() -> list[TalepAraligiTanimi]:
    """SRS 3.3.4'teki ozet tabloyu tam acilmis aralik satirlarina cevirir.

    RESMI_TATIL satirlari da uretilir ve bu ZORUNLUDUR, susleme degil.
    Acilim bir gun icin once tarihe ozgu istisnayi, sonra o GUN TIPINE
    karsilik gelen genel satiri arar; hicbiri yoksa o gun icin hicbir saat
    talep tasimaz. Yani resmi tatil satiri bulunmayan bir tanimda bir gunu
    tatil olarak isaretlemek (FR-1.10), o gunun talebini sessizce SIFIRLAR
    - cizelge o gun icin kimseyi istemez ve bu bir hata gibi gorunmez,
    cunku kapsama acigi da olusmaz (talep sifirdir).

    Muracaat noktasinin hafta sonu/tatil satirlari SIFIR degerle yine de
    yazilir: "bu noktada o gun kimse gerekmiyor" ile "bu nokta icin satir
    girmeyi unuttuk" arasindaki farki veride gorunur kilar.

    Haftalik yuk (FR-1.9) bu satirlardan ETKILENMEZ: resmi tatil her hafta
    tekrarlanmadigi icin haftalik tekrar carpani sifirdir. SRS 3.3.6'nin
    referans sayilari korunur - 1.152 kisi-saat, sekiz saatlik katalogda
    144 kisi-vardiya ve 29 kisilik asgari kadro.
    """
    satirlar: list[TalepAraligiTanimi] = []
    for index, (hafta_ici_araliklar, azaltilmis) in enumerate(TALEP_ARALIKLARI):
        for baslangic, bitis, gereken in hafta_ici_araliklar:
            satirlar.append(TalepAraligiTanimi(index, GunTipi.HAFTA_ICI, baslangic, bitis, gereken))
        for gun_tipi in (GunTipi.HAFTA_SONU, GunTipi.RESMI_TATIL):
            satirlar.append(TalepAraligiTanimi(index, gun_tipi, _GUN_BASI, _GUN_BASI, azaltilmis))
    return satirlar


@dataclass(frozen=True, slots=True)
class PersonelGrubuTanimi:
    """SRS 3.3.6'daki yetkinlik havuzlarindan turetilen personel gruplari.

    Buyuklukler, 'Izin Payiyla' toplaminin (7+6+23=36) ~44'e olceklenmesiyle
    bulundu (44/36 ~ 1.22): Vardiya Sefi 7->9, Muracaat 6->7,
    yalniz Guvenlik Gorevi 23->28. Toplam 44 (UYGULAMA_PLANI.md Gun 5).
    """

    yetkinlikler: tuple[str, ...]
    sayi: int
    sicil_on_eki: str


# KADRO TALEBE GORE BOYUTLANDIRILDI (SRS 3.3.6, Tur 4). Onceki 44 kisilik
# kadroda kisi basina haftalik yuk 26 saate dusuyor, kimse fazla calisma
# esigine (45) yaklasmiyor ve H10 HICBIR ZAMAN tetiklenmiyordu - kurallarin
# isledigini gosteremeyen bir gosterim verisi, kurallarin yazilmamis
# olmasiyla ayni kapiya cikar.
#
# Yeni buyukluk 30: SRS 3.3.6'nin izin payli asgarisi 29, teorik asgarisi
# 26. Kisi basina haftalik yuk 1.152 / 30 = 38,4 saat - esige yakin ama
# ALTINDA; izin veya uzun blok girdiginde esik asilir ve kota tuketimi
# gorunur hale gelir.
#
# Havuz oranlari SRS 3.3.6'daki izin payli degerlere (7 / 6 / 23) sadik
# kalir; Vardiya Sefligi havuzunun kirilganligi (kesintisiz doldurulan tek
# nokta, haftada 21 vardiya) korunur - sikisik senaryonun dayandigi
# mekanizma budur.
PERSONEL_GRUPLARI: tuple[PersonelGrubuTanimi, ...] = (
    PersonelGrubuTanimi((VARDIYA_SEFI, GUVENLIK_GOREVI), 7, "VS"),
    PersonelGrubuTanimi((MURACAAT_GOREVLISI,), 6, "MR"),
    PersonelGrubuTanimi((GUVENLIK_GOREVI,), 17, "GG"),
)
