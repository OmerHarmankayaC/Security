"""/api/cozum istek/yanit semalari (SDD Ek B, 5.4)."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.sonuc import CozumIsiDurumu


class CozumBaslatIstek(BaseModel):
    donem_id: int
    zaman_limiti_saniye: int = 60


class CozumOku(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    is_id: int
    surum_id: int
    durum: CozumIsiDurumu
    baslangic_zamani: datetime
    bitis_zamani: datetime | None
    sure_saniye: Decimal | None
    zaman_limiti_saniye: int
    en_iyi_ceza: Decimal | None
    ceza_dokumu: dict[str, Any] | None
    hata_mesaji: str | None
