from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column


class ZamanDamgasiKarisimi:
    """Butun tablolarda ortuk bulunan olusturma/guncelleme zaman damgalari (SDD 4.2)."""

    olusturma_zamani: Mapped[datetime] = mapped_column(server_default=func.now())
    guncelleme_zamani: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
