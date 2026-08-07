import enum
from datetime import date

from sqlalchemy import Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.ortak import ZamanDamgasiKarisimi


class MusaitlikDilimi(enum.StrEnum):
    TAM_GUN = "tam_gun"
    OGLEDEN_ONCE = "ogleden_once"
    OGLEDEN_SONRA = "ogleden_sonra"


class MusaitlikTipi(enum.StrEnum):
    YILLIK_IZIN = "yillik_izin"
    RAPOR = "rapor"
    EGITIM = "egitim"
    MAZERET = "mazeret"


class TercihTipi(enum.StrEnum):
    CALISMAMA = "calismama"
    VARDIYA_TIPI_TERCIHI = "vardiya_tipi_tercihi"


class TercihDurumu(enum.StrEnum):
    BEKLEMEDE = "beklemede"
    ONAYLANDI = "onaylandi"
    REDDEDILDI = "reddedildi"


class Musaitlik(Base, ZamanDamgasiKarisimi):
    __tablename__ = "musaitlik"

    musaitlik_id: Mapped[int] = mapped_column(primary_key=True)
    personel_id: Mapped[int] = mapped_column(ForeignKey("personel.personel_id"))
    baslangic_tarihi: Mapped[date] = mapped_column(Date)
    bitis_tarihi: Mapped[date] = mapped_column(Date)
    dilim: Mapped[MusaitlikDilimi]
    tip: Mapped[MusaitlikTipi]
    not_: Mapped[str | None] = mapped_column("not", default=None)


class Tercih(Base, ZamanDamgasiKarisimi):
    __tablename__ = "tercih"

    tercih_id: Mapped[int] = mapped_column(primary_key=True)
    personel_id: Mapped[int] = mapped_column(ForeignKey("personel.personel_id"))
    donem_id: Mapped[int] = mapped_column(ForeignKey("donem.donem_id"))
    tarih: Mapped[date] = mapped_column(Date)
    tip: Mapped[TercihTipi]
    vardiya_tipi_id: Mapped[int | None] = mapped_column(ForeignKey("vardiya_tipi.vardiya_tipi_id"))
    durum: Mapped[TercihDurumu] = mapped_column(default=TercihDurumu.BEKLEMEDE)
    calisan_notu: Mapped[str | None] = mapped_column(default=None)
    ret_gerekcesi: Mapped[str | None] = mapped_column(default=None)


__all__ = [
    "Musaitlik",
    "MusaitlikDilimi",
    "MusaitlikTipi",
    "Tercih",
    "TercihDurumu",
    "TercihTipi",
]
