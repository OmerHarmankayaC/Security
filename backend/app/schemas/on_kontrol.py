"""/api/on-kontrol istek/yanit semalari (SDD Ek B, 5.2; SRS FR-5.x)."""

from datetime import date

from pydantic import BaseModel, ConfigDict

from app.services.on_kontrol import BulguTipi


class OnKontrolIstek(BaseModel):
    donem_id: int


class BulguOku(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tip: BulguTipi
    aciklama: str
    eksik: int | None = None
    yetkinlik_id: int | None = None
    tarih: date | None = None
    vardiya_tipi_id: int | None = None
    nokta_id: int | None = None


class OnKontrolYaniti(BaseModel):
    bulgular: list[BulguOku]
