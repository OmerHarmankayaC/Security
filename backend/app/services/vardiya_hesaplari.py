"""Vardiya tipi turetilmis alanlari: sure ve gece bayragi onerisi (FR-1.3, FR-1.4, TD-2)."""

from datetime import time
from decimal import Decimal

_GECE_PENCERESI_DK = [(20 * 60, 24 * 60), (0, 6 * 60)]  # 20:00-24:00 ve 00:00-06:00 (TD-2)
_GECE_ONERI_ESIGI_DK = 4 * 60


def sure_saat_hesapla(baslangic_saati: time, bitis_saati: time) -> Decimal:
    """FR-1.3: sure, baslangic ve bitis saatinden hesaplanir; gece yarisini asan
    vardiyalarda bitis ertesi gune sarkar (TD-1)."""
    baslangic_dk = baslangic_saati.hour * 60 + baslangic_saati.minute
    bitis_dk = bitis_saati.hour * 60 + bitis_saati.minute
    if bitis_dk <= baslangic_dk:
        bitis_dk += 24 * 60
    return Decimal(bitis_dk - baslangic_dk) / Decimal(60)


def gece_mi_oner(baslangic_saati: time, bitis_saati: time) -> bool:
    """TD-2: 20:00-06:00 penceresiyle kesisim dort saat veya fazlaysa gece onerilir."""
    baslangic_dk = baslangic_saati.hour * 60 + baslangic_saati.minute
    bitis_dk = bitis_saati.hour * 60 + bitis_saati.minute
    if bitis_dk <= baslangic_dk:
        vardiya_araliklari = [(baslangic_dk, 24 * 60), (0, bitis_dk)]
    else:
        vardiya_araliklari = [(baslangic_dk, bitis_dk)]

    kesisim_dk = sum(
        max(0, min(v_bitis, g_bitis) - max(v_baslangic, g_baslangic))
        for v_baslangic, v_bitis in vardiya_araliklari
        for g_baslangic, g_bitis in _GECE_PENCERESI_DK
    )
    return kesisim_dk >= _GECE_ONERI_ESIGI_DK
