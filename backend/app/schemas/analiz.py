"""Analiz uc noktasinin yanit semasi (SDD 3.2: analiz_router; SDD 5.7, Ek B;
SRS FR-8.x)."""

from pydantic import BaseModel


class KisiSayisiOku(BaseModel):
    personel_id: int
    ad_soyad: str
    sayi: int


class SaatDengesiOku(BaseModel):
    personel_id: int
    ad_soyad: str
    toplam_saat: float
    hedef_saat: float
    sapma: float


class AnalizOku(BaseModel):
    surum_id: int
    kapsama_orani: float
    kisi_basina_gece: list[KisiSayisiOku]
    kisi_basina_hafta_sonu: list[KisiSayisiOku]
    saat_dagilimi: list[SaatDengesiOku]
    en_dengesiz_personel_id: int | None
    en_dengesiz_ad_soyad: str | None
    tercih_karsilama_orani: float | None
    bina_degisim_sayisi: list[KisiSayisiOku]
    ceza_dokumu: dict[str, float] | None
    toplam_ceza: float | None
