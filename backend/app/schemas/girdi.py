"""Musaitlik/Tercih uc noktalarinin istek/yanit semalari (SDD Ek B; SRS FR-2.x, FR-3.x)."""

from datetime import date

from pydantic import BaseModel, ConfigDict

from app.models.girdi import MusaitlikDilimi, MusaitlikTipi, TercihDurumu, TercihTipi

# --- Musaitlik (FR-2.1, FR-2.2) -------------------------------------------


class MusaitlikOlustur(BaseModel):
    personel_id: int
    baslangic_tarihi: date
    bitis_tarihi: date
    dilim: MusaitlikDilimi
    tip: MusaitlikTipi
    not_: str | None = None


class MusaitlikOku(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    musaitlik_id: int
    personel_id: int
    baslangic_tarihi: date
    bitis_tarihi: date
    dilim: MusaitlikDilimi
    tip: MusaitlikTipi
    not_: str | None


# --- Tercih (FR-3.1, FR-3.2, FR-3.4) --------------------------------------


class TercihOlustur(BaseModel):
    personel_id: int
    donem_id: int
    tarih: date
    tip: TercihTipi
    vardiya_tipi_id: int | None = None


class TercihGuncelle(BaseModel):
    """Yalniz durum degisir (FR-3.4: yonetici onaylar veya reddeder)."""

    durum: TercihDurumu


class TercihOku(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tercih_id: int
    personel_id: int
    donem_id: int
    tarih: date
    tip: TercihTipi
    vardiya_tipi_id: int | None
    durum: TercihDurumu
