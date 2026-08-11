"""Analiz uc noktasinin yanit semasi (SDD 3.2: analiz_router; SDD 5.7, Ek B;
SRS FR-8.x)."""

from datetime import date

from pydantic import BaseModel, Field


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


class FazlaKadroKalemi(BaseModel):
    """Talepten fazla kadro yazilmis bir hucre; ADLARIYLA birlikte.

    Analiz ekrani ve disa aktarma kimlik degil ad gosterir (NFR-5); adlari
    burada cozmek, her tuketicinin ayri ayri eslestirme yapmasini onler.
    """

    tarih: date
    vardiya_tipi_id: int
    vardiya_tipi_ad: str
    nokta_id: int
    nokta_ad: str
    fazla_sayi: int


class AnalizOku(BaseModel):
    surum_id: int
    kapsama_orani: float
    # Kapsama oranindan AYRI tutulur: oran "talebin ne kadari karsilandi"
    # sorusunu yanitlar, fazla kadro o soruya bir sey eklemez.
    fazla_kadro: list[FazlaKadroKalemi] = Field(default_factory=list)
    toplam_fazla_kadro: int = 0
    kisi_basina_gece: list[KisiSayisiOku]
    kisi_basina_hafta_sonu: list[KisiSayisiOku]
    saat_dagilimi: list[SaatDengesiOku]
    en_dengesiz_personel_id: int | None
    en_dengesiz_ad_soyad: str | None
    tercih_karsilama_orani: float | None
    bina_degisim_sayisi: list[KisiSayisiOku]
    ceza_dokumu: dict[str, float] | None
    toplam_ceza: float | None
