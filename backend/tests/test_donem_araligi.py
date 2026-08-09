"""Planlama donemi araliginin dogrulanmasi (madde 4).

Veritabani gerektirmez; sema dogrulamasi uzerinde calisir. Uc noktanin bu
semayi kullandigi test_cizelge_api.py'de dogrulanir.
"""

from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.surum import AZAMI_DONEM_GUN, DonemOlustur


def _donem(baslangic: date, bitis: date) -> DonemOlustur:
    return DonemOlustur(
        baslangic_tarihi=baslangic,
        bitis_tarihi=bitis,
        tercih_son_tarihi=baslangic,
    )


def test_bir_haftalik_donem_kabul_edilir() -> None:
    """Varsayilan secim bir haftadir (Backlog karar gunlugu, 07.08.2026)."""
    donem = _donem(date(2026, 8, 3), date(2026, 8, 9))
    assert (donem.bitis_tarihi - donem.baslangic_tarihi).days + 1 == 7


def test_kabul_kriterinin_yirmi_sekiz_gunu_kabul_edilir() -> None:
    """NFR-1 referans ornegi 28 gun; ust sinir onu kapsamak zorunda."""
    _donem(date(2026, 8, 3), date(2026, 8, 30))


def test_azami_gun_sayisi_tam_sinirda_kabul_edilir() -> None:
    _donem(date(2026, 8, 1), date(2026, 8, 31))  # tam 31 gun


def _mesaj(hata: pytest.ExceptionInfo[ValidationError]) -> str:
    """Kullaniciya ulasan metin: FastAPI'nin 422 govdesindeki detail[].msg."""
    return hata.value.errors()[0]["msg"]


def test_azami_gun_sayisi_asilinca_reddedilir() -> None:
    with pytest.raises(ValidationError) as hata:
        _donem(date(2026, 8, 1), date(2026, 9, 1))  # 32 gun
    mesaj = _mesaj(hata)
    assert str(AZAMI_DONEM_GUN) in mesaj
    assert "32 gün" in mesaj, "kullaniciya secilen uzunluk da soylenmeli (NFR-5)"


def test_bitis_baslangictan_once_olamaz() -> None:
    with pytest.raises(ValidationError):
        _donem(date(2026, 8, 9), date(2026, 8, 3))


def test_tercih_son_tarihi_donem_bitisinden_sonra_olamaz() -> None:
    with pytest.raises(ValidationError):
        DonemOlustur(
            baslangic_tarihi=date(2026, 8, 3),
            bitis_tarihi=date(2026, 8, 9),
            tercih_son_tarihi=date(2026, 8, 20),
        )


def test_hata_mesaji_teknik_terim_icermez() -> None:
    """NFR-5: uyarilar operasyon diliyle ifade edilmeli.

    Olculen sey kullaniciya ulasan metin (detail[].msg); Pydantic'in tam
    temsili girdi sozlugunu de tasir ve alan adlarini orada aramak yanlis
    olurdu.
    """
    with pytest.raises(ValidationError) as hata:
        _donem(date(2026, 8, 1), date(2026, 9, 30))
    mesaj = _mesaj(hata)
    for terim in ("timedelta", "baslangic_tarihi", "bitis_tarihi", "None"):
        assert terim not in mesaj, terim
