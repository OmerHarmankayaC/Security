"""SRS 3.3'teki guvenlik personeli ornek senaryosunun yapisal (DB'siz) tanimi.

Hem demo veri uretecinin (scripts/demo_veri_uret.py) hem de FR-1.9
dogrulama testinin (tests/test_yuk_gostergesi.py) ortak veri kaynagidir;
boylece iki yerde ayni tablo iki kez elle yazilip birbirinden sapmaz.
"""

from dataclasses import dataclass

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
# Sira, TALEP_DEGERLERI ile index uzerinden eslenir.
NOKTA_TANIMLARI: tuple[NoktaTanimi, ...] = (
    NoktaTanimi("Vardiya Şefliği", None, VARDIYA_SEFI),
    NoktaTanimi("Güvenlik", None, GUVENLIK_GOREVI),
    NoktaTanimi("Müracaat", None, MURACAAT_GOREVLISI),
)

# SRS 3.3.4 — Talep Matrisi: (hafta_ici_gunduz, hafta_ici_aksam, gece/hafta_sonu/tatil).
# Ucuncu deger; hafta ici gece VE hafta sonu/resmi tatildeki her uc vardiya icin ortaktir
# ("Hafta sonu ve resmi tatillerde uc vardiyanin tamami azaltilmis kadroyla calisir").
# Guvenlik talebi, onceki surumde ayri satirlar olan kapi ve kontrol odasi
# taleplerinin toplamidir; toplam kisi sayisi degismemistir, yalnizca
# noktanin kendisi birlesmistir.
TALEP_DEGERLERI: tuple[tuple[int, int, int], ...] = (
    (1, 1, 1),  # Vardiya Şefliği
    (7, 7, 3),  # Güvenlik
    (2, 2, 0),  # Müracaat
)


@dataclass(frozen=True, slots=True)
class TalepSatiriTanimi:
    nokta_index: int
    vardiya_tipi: str
    gun_tipi: GunTipi
    gereken_sayi: int


def talep_satirlarini_olustur() -> list[TalepSatiriTanimi]:
    """SRS 3.3.4'teki ozet tabloyu tam acilmis (nokta, vardiya, gun_tipi) satirlarina cevirir."""
    satirlar: list[TalepSatiriTanimi] = []
    for index, (hi_gunduz, hi_aksam, azaltilmis) in enumerate(TALEP_DEGERLERI):
        satirlar.append(TalepSatiriTanimi(index, GUNDUZ, GunTipi.HAFTA_ICI, hi_gunduz))
        satirlar.append(TalepSatiriTanimi(index, AKSAM, GunTipi.HAFTA_ICI, hi_aksam))
        for vardiya_tipi, gun_tipi in (
            (GECE, GunTipi.HAFTA_ICI),
            (GUNDUZ, GunTipi.HAFTA_SONU),
            (AKSAM, GunTipi.HAFTA_SONU),
            (GECE, GunTipi.HAFTA_SONU),
        ):
            satirlar.append(TalepSatiriTanimi(index, vardiya_tipi, gun_tipi, azaltilmis))
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


PERSONEL_GRUPLARI: tuple[PersonelGrubuTanimi, ...] = (
    PersonelGrubuTanimi((VARDIYA_SEFI, GUVENLIK_GOREVI), 9, "VS"),
    PersonelGrubuTanimi((MURACAAT_GOREVLISI,), 7, "MR"),
    PersonelGrubuTanimi((GUVENLIK_GOREVI,), 28, "GG"),
)
