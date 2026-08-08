from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

# Butun zaman damgasi sutunlari SAAT DILIMI TASIR (timestamptz).
#
# Uygulama her yere datetime.now(UTC) yazar; sutun saat dilimsiz oldugunda
# bu bilgi kayboluyor, JSON'a ofsetsiz bir dize olarak cikiyor ve istemci
# tarafinin bunu yerel saat sanmasi riski doguyordu. timestamptz ile
# PostgreSQL degeri UTC saklar ve okurken saat dilimi bilgisiyle dondurur.
ZamanDamgasi = DateTime(timezone=True)


class ZamanDamgasiKarisimi:
    """Butun tablolarda ortuk bulunan olusturma/guncelleme zaman damgalari (SDD 4.2)."""

    olusturma_zamani: Mapped[datetime] = mapped_column(ZamanDamgasi, server_default=func.now())
    guncelleme_zamani: Mapped[datetime] = mapped_column(
        ZamanDamgasi, server_default=func.now(), onupdate=func.now()
    )
