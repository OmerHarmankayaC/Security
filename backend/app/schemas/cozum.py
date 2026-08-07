"""/api/cozum istek/yanit semalari (SDD Ek B, 5.4)."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator

from app.models.sonuc import CozumIsiDurumu


class CozumBaslatIstek(BaseModel):
    """donem_id: yeni bir donem icin ilk cozum. onceki_surum_id: SDD 5.6
    yeniden_coz - onceki surumden taslak turetip S8 tabanli yeniden cozer.
    Tam olarak biri verilmelidir."""

    donem_id: int | None = None
    onceki_surum_id: int | None = None
    zaman_limiti_saniye: int = 60

    @model_validator(mode="after")
    def _tam_olarak_biri(self) -> "CozumBaslatIstek":
        if (self.donem_id is None) == (self.onceki_surum_id is None):
            raise ValueError("donem_id ile onceki_surum_id'den tam olarak biri verilmeli")
        return self


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
