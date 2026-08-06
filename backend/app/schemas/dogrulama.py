"""/api/atama/dogrula ve /api/atama semalari (SDD 5.5, SRS FR-6.x)."""

from datetime import date

from pydantic import BaseModel, model_validator


class AtamaDegisikligiIstek(BaseModel):
    """Cizelge izgarasindaki tek bir (personel, tarih) hucresine yapilan degisiklik.

    vardiya_tipi_id/nokta_id ikisi de None ise hucre bosaltilir (atama kaldirilir);
    ikisi de doluysa hucreye bu vardiya/nokta atanir (var olan atamanin yerine gecer).
    """

    surum_id: int
    personel_id: int
    tarih: date
    vardiya_tipi_id: int | None = None
    nokta_id: int | None = None

    @model_validator(mode="after")
    def _ikisi_birlikte_doluysa_ya_da_bossa(self) -> "AtamaDegisikligiIstek":
        if (self.vardiya_tipi_id is None) != (self.nokta_id is None):
            raise ValueError(
                "vardiya_tipi_id ve nokta_id birlikte doldurulmali ya da ikisi de bos "
                "birakilmali (hucreyi bosaltmak icin)"
            )
        return self


class IhlalOku(BaseModel):
    kural_kimlik: str
    aciklama: str
    personel_id: int | None
    tarih: date | None
    ceza: float | None


class DogrulamaSonucuOku(BaseModel):
    kabul_edilebilir: bool
    zorunlu_ihlaller: list[IhlalOku]
    ceza_degisimi: float
