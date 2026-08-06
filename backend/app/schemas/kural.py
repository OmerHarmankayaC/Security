"""Kural uc noktasinin istek/yanit semalari (SDD 3.2.1, 4.2.3; SRS FR-1.11-FR-1.13)."""

from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.kural import KuralTipi


class KuralGuncelle(BaseModel):
    """Yalniz veri degisir, kod dokunulmaz (SDD 3.2.1): parametreler, agirlik, aktiflik."""

    parametreler: dict[str, Any] | None = None
    agirlik: int | None = None
    aktif: bool | None = None


class KuralOku(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    kural_id: int
    kimlik: str
    tip: KuralTipi
    parametreler: dict[str, Any]
    agirlik: int | None
    aktif: bool
