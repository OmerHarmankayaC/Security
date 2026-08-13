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
    personel_id: int | None = None
    # KESIN BULGU MU, UYARI MI (SDD 5.2, K18). Hicbir bulgu cozumu
    # DUSURMEZ; ayrim yalnizca okuma amaclidir. Kesin bulgu, ortaya
    # cikacak acigin kadro yetersizliginden kaynaklandigini ONCEDEN
    # dogrular; uyari ise sonucun hangi kosulla okunmasi gerektigini
    # bildirir.
    kesin_mi: bool = True


class OnKontrolYaniti(BaseModel):
    bulgular: list[BulguOku]
