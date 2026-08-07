"""S2/S3'un uygun havuzu (SRS 1.5: P_gece, P_hs) — Baglam.uygun_havuz.

Bu testin varlik nedeni, PROGRESS.md'de dort kez tekrarlanan bir hata
kalibidir: bir adalet/denge metriginin hedefi, ona ULASAMAYACAK personeli de
kapsayacak sekilde tanimlaniyor; sonucta herkes ayni yonde sapmis gorunuyor,
metrik hicbir ayrim uretmiyor ve kabul kriteri hicbir cizelgeyle
saglanamiyor (S4'un sozlesme hedefi, Analiz'in saat dagilimi, S2/S3'un
paydasi). Buradaki testler o kalibin S2/S3 ayagini kilitler.

Veritabani gerektirmez.
"""

from datetime import date, time

from app.kurallar.baglam import (
    Baglam,
    GorevNoktasiBilgisi,
    PersonelBilgisi,
    VardiyaTipiBilgisi,
)

GECE, GUNDUZ = 1, 2
GUVENLIK, MURACAAT = 10, 20  # nokta kimlikleri
YET_GUVENLIK, YET_MURACAAT = 100, 200

_PAZARTESI = date(2026, 2, 2)
_CUMARTESI = date(2026, 2, 7)


def _baglam(talep: dict[tuple[date, int, int], int]) -> Baglam:
    return Baglam(
        vardiya_tipleri={
            GECE: VardiyaTipiBilgisi(GECE, time(0, 0), time(8, 0), 8.0, True),
            GUNDUZ: VardiyaTipiBilgisi(GUNDUZ, time(8, 0), time(16, 0), 8.0, False),
        },
        gorev_noktalari={
            GUVENLIK: GorevNoktasiBilgisi(GUVENLIK, onkosul_yetkinlik_id=YET_GUVENLIK),
            MURACAAT: GorevNoktasiBilgisi(MURACAAT, onkosul_yetkinlik_id=YET_MURACAAT),
        },
        personel={
            1: PersonelBilgisi(1, date(2026, 1, 1), None, frozenset({YET_GUVENLIK})),
            2: PersonelBilgisi(2, date(2026, 1, 1), None, frozenset({YET_MURACAAT})),
        },
        talep=talep,
        donem_baslangic=_PAZARTESI,
        donem_bitis=date(2026, 2, 8),
    )


def _gece_havuzu(baglam: Baglam) -> set[int]:
    return baglam.uygun_havuz(lambda anahtar: baglam.gece_mi(anahtar[1]))


def _hs_havuzu(baglam: Baglam) -> set[int]:
    return baglam.uygun_havuz(lambda anahtar: baglam.hafta_sonu_mu(anahtar[0]))


def test_gece_talebi_olmayan_noktanin_personeli_havuz_disindadir() -> None:
    """Asil senaryo (Gun 14 K3 bulgusu): Muracaat gorevlisi yalniz Muracaat
    noktasinda calisabilir (H8) ve o noktanin gece talebi yoktur; gece sayisi
    hicbir cizelgede sifirdan yukari cikamaz, dolayisiyla paydaya girmemelidir."""
    baglam = _baglam(
        {
            (_PAZARTESI, GECE, GUVENLIK): 1,  # gece talebi YALNIZ Guvenlik'te
            (_PAZARTESI, GUNDUZ, MURACAAT): 2,
        }
    )
    assert _gece_havuzu(baglam) == {1}


def test_gece_talebi_bulunan_noktanin_personeli_havuzdadir() -> None:
    baglam = _baglam(
        {
            (_PAZARTESI, GECE, GUVENLIK): 1,
            (_PAZARTESI, GECE, MURACAAT): 1,  # Muracaat'ta da gece talebi var
        }
    )
    assert _gece_havuzu(baglam) == {1, 2}


def test_sifir_gereken_talep_satiri_havuza_sokmaz() -> None:
    """Talep matrisi gun tipi x vardiya tipi kombinasyonlarinin tamamini
    satir olarak tasir; karsilanmasi gereken sayisi SIFIR olan bir satir
    'o noktada o vardiya var' anlamina gelmez."""
    baglam = _baglam(
        {
            (_PAZARTESI, GECE, GUVENLIK): 1,
            (_PAZARTESI, GECE, MURACAAT): 0,  # satir var ama gereken 0
        }
    )
    assert _gece_havuzu(baglam) == {1}


def test_donem_disi_talep_havuza_sokmaz() -> None:
    """TD-6: sayimlar yalniz planlama donemini kapsar. baglam.talep isitma
    penceresini de iceren tam zaman ekseni icin cozuldugunden (TD-5), donem
    disi bir gece talebi havuzu genisletmemelidir."""
    donem_disi = date(2026, 1, 26)  # donem baslangicindan bir hafta once
    baglam = _baglam(
        {
            (_PAZARTESI, GECE, GUVENLIK): 1,
            (donem_disi, GECE, MURACAAT): 1,
        }
    )
    assert _gece_havuzu(baglam) == {1}


def test_hafta_sonu_havuzu_ayni_mantikla_belirlenir() -> None:
    """S3'un P_hs'si: hafta sonu talebi bulunan noktanin on kosulunu
    karsilayanlar. Hafta ici talebi olan nokta havuza sokmaz (TD-3)."""
    baglam = _baglam(
        {
            (_CUMARTESI, GUNDUZ, GUVENLIK): 1,  # hafta sonu talebi
            (_PAZARTESI, GUNDUZ, MURACAAT): 2,  # yalnizca hafta ici
        }
    )
    assert _hs_havuzu(baglam) == {1}


def test_onkosulu_olmayan_nokta_herkesi_havuza_alir() -> None:
    """Tesis geneli / on kosulsuz bir noktada herkes calisabilir (H8 baglamaz)."""
    baglam = _baglam({(_PAZARTESI, GECE, GUVENLIK): 1})
    baglam.gorev_noktalari[GUVENLIK] = GorevNoktasiBilgisi(GUVENLIK, onkosul_yetkinlik_id=None)
    assert _gece_havuzu(baglam) == {1, 2}


def test_hic_gece_talebi_yoksa_havuz_bostur() -> None:
    """Gece talebi hic yoksa gece adaleti sorusu da yoktur; havuz bos kalir ve
    S2 ceza uretmez (bolme hatasi da vermez)."""
    baglam = _baglam({(_PAZARTESI, GUNDUZ, GUVENLIK): 1})
    assert _gece_havuzu(baglam) == set()
