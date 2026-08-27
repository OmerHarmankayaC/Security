"""SRS 3.3'teki guvenlik personeli ornek senaryosunun yapisal (DB'siz) tanimi.

Hem demo veri uretecinin (scripts/demo_veri_uret.py) hem de FR-1.9
dogrulama testinin (tests/test_yuk_gostergesi.py) ortak veri kaynagidir;
boylece iki yerde ayni tablo iki kez elle yazilip birbirinden sapmaz.
"""

from dataclasses import dataclass
from datetime import time

from app.models.tanim import GunTipi

# SRS 3.3.2 — yetkinlikler ikiye indi. Muracaat Gorevlisi kalkti; o
# personel duz guvenlik gorevlisi olarak havuza katildi.
GUVENLIK_GOREVI = "Güvenlik Görevi"
VARDIYA_SEFI = "Vardiya Şefi"


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
    # Güvenlik: 08.00-24.00 arasi dokuz, gece uc.
    #
    # YEDIDEN DOKUZA CIKTI (SRS 3.3.4): Muracaat noktasinin hafta ici gunduz
    # ve aksam saatlerindeki iki kisilik talebi buraya EKLENDI. Haftalik
    # toplam is yuku degismedi - 1.152 kisi-saat.
    (((_SEKIZ, _GUN_BASI, 9), (_GUN_BASI, _SEKIZ, 3)), 3),
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

    Bir noktanin bir gun tipinde kimseyi gerektirmemesi durumunda satir
    SIFIR degerle yine de yazilir: "bu noktada o gun kimse gerekmiyor" ile
    "bu nokta icin satir girmeyi unuttuk" arasindaki farki veride gorunur
    kilar.

    Haftalik yuk (FR-1.9) resmi tatil satirlarindan ETKILENMEZ: tatil her
    hafta tekrarlanmadigi icin haftalik tekrar carpani sifirdir. SRS
    3.3.6'nin referans sayisi korunur — 1.152 kisi-saat.
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
    """SRS 3.3.6'daki yetkinlik havuzlarindan turetilen personel gruplari."""

    yetkinlikler: tuple[str, ...]
    sayi: int
    sicil_on_eki: str


# KADRO KIRK KISI (Demo Senaryosu 4.3; SRS 3.3.6, NFR-1 referans kadrosu).
#
# Onceki buyukluk otuzdu ve kabul olcumunun referans ornegi (kirk kisi,
# scripts/kabul_olcumu.py `_REFERANS_GRUPLARI`) ile ayrisiyordu: ayni olgu -
# "referans kadro kac kisidir" - iki yerde iki farkli sayiyla yaziliydi.
# Demo Senaryosu 4.3 ikisini esitliyor, boylece demo ile olcum kaydi ayni
# buyuklugu anlatir.
#
# Sef havuzu dokuz kisi: Vardiya Sefligi noktasi kesintisiz doldurulan tek
# noktadir ve haftada 168 kisi-saat ister. Havuzun kirilganligi, sikisik
# senaryonun (Demo Senaryosu 6.3) dayandigi mekanizmadir - yedi sef izne
# ciktiginda kalan ikisi gunluk tavan (H9, 11 saat) ve haftalik izin gunu
# (H6) altinda en cok 2 x 6 x 11 = 132 kisi-saat verebilir. Eksik olan SAAT
# degil KISIDIR ve hicbir blok uzunlugu bunu kapatamaz (SRS TD-13).
#
# SICIL NUMARASI HAVUZ BASINA DEGIL SURELIDIR (D-1001 ... D-1040): havuz on
# ekiyle numaralandirmak, bir havuzun buyuklugu degistiginde digerinin
# sicillerini kaydirmadan buyutmeyi kolaylastiriyordu ama sicilin kendisi
# gorev bilgisi tasiyordu. Numaralandirmayi ureten kod
# scripts/demo_veri_uret.py icindedir.
PERSONEL_GRUPLARI: tuple[PersonelGrubuTanimi, ...] = (
    PersonelGrubuTanimi((VARDIYA_SEFI, GUVENLIK_GOREVI), 9, "D"),
    PersonelGrubuTanimi((GUVENLIK_GOREVI,), 31, "D"),
)
