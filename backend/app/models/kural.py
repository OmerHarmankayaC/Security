import enum

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.ortak import ZamanDamgasiKarisimi


class KuralTipi(enum.StrEnum):
    ZORUNLU = "zorunlu"
    ESNEK = "esnek"


class Kural(Base, ZamanDamgasiKarisimi):
    __tablename__ = "kural"

    kural_id: Mapped[int] = mapped_column(primary_key=True)
    kimlik: Mapped[str] = mapped_column(unique=True)
    tip: Mapped[KuralTipi]
    parametreler: Mapped[dict] = mapped_column(JSONB)
    agirlik: Mapped[int | None]
    aktif: Mapped[bool] = mapped_column(default=True)


__all__ = ["Kural", "KuralTipi"]
