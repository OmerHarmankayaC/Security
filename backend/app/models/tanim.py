import enum
from datetime import date, time
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.ortak import ZamanDamgasiKarisimi


class GunTipi(enum.StrEnum):
    HAFTA_ICI = "hafta_ici"
    HAFTA_SONU = "hafta_sonu"
    RESMI_TATIL = "resmi_tatil"


class Personel(Base, ZamanDamgasiKarisimi):
    __tablename__ = "personel"

    personel_id: Mapped[int] = mapped_column(primary_key=True)
    ad_soyad: Mapped[str]
    sicil_no: Mapped[str] = mapped_column(unique=True)
    haftalik_hedef_saat: Mapped[int]
    sabit_vardiya_tipi_id: Mapped[int | None] = mapped_column(
        ForeignKey("vardiya_tipi.vardiya_tipi_id")
    )
    aktif_baslangic: Mapped[date] = mapped_column(Date)
    aktif_bitis: Mapped[date | None] = mapped_column(Date)


class Yetkinlik(Base, ZamanDamgasiKarisimi):
    __tablename__ = "yetkinlik"

    yetkinlik_id: Mapped[int] = mapped_column(primary_key=True)
    ad: Mapped[str] = mapped_column(unique=True)
    aciklama: Mapped[str | None]


class PersonelYetkinlik(Base, ZamanDamgasiKarisimi):
    """Bilesik anahtar; iliski seviyesizdir (SRS TD-9)."""

    __tablename__ = "personel_yetkinlik"

    personel_id: Mapped[int] = mapped_column(ForeignKey("personel.personel_id"), primary_key=True)
    yetkinlik_id: Mapped[int] = mapped_column(
        ForeignKey("yetkinlik.yetkinlik_id"), primary_key=True
    )


class Bina(Base, ZamanDamgasiKarisimi):
    __tablename__ = "bina"

    bina_id: Mapped[int] = mapped_column(primary_key=True)
    ad: Mapped[str]


class GorevNoktasi(Base, ZamanDamgasiKarisimi):
    __tablename__ = "gorev_noktasi"

    nokta_id: Mapped[int] = mapped_column(primary_key=True)
    ad: Mapped[str]
    bina_id: Mapped[int | None] = mapped_column(ForeignKey("bina.bina_id"))
    onkosul_yetkinlik_id: Mapped[int | None] = mapped_column(ForeignKey("yetkinlik.yetkinlik_id"))
    aktif: Mapped[bool] = mapped_column(default=True)


class VardiyaTipi(Base, ZamanDamgasiKarisimi):
    __tablename__ = "vardiya_tipi"

    vardiya_tipi_id: Mapped[int] = mapped_column(primary_key=True)
    ad: Mapped[str]
    baslangic_saati: Mapped[time] = mapped_column(Time)
    bitis_saati: Mapped[time] = mapped_column(Time)
    sure_saat: Mapped[Decimal] = mapped_column(Numeric(4, 2))
    gece_mi: Mapped[bool]


class Talep(Base, ZamanDamgasiKarisimi):
    __tablename__ = "talep"

    talep_id: Mapped[int] = mapped_column(primary_key=True)
    nokta_id: Mapped[int] = mapped_column(ForeignKey("gorev_noktasi.nokta_id"))
    vardiya_tipi_id: Mapped[int] = mapped_column(ForeignKey("vardiya_tipi.vardiya_tipi_id"))
    gun_tipi: Mapped[GunTipi]
    tarih: Mapped[date | None] = mapped_column(Date)
    gereken_sayi: Mapped[int]


class OzelGun(Base, ZamanDamgasiKarisimi):
    __tablename__ = "ozel_gun"

    tarih: Mapped[date] = mapped_column(Date, primary_key=True)
    ad: Mapped[str]


__all__ = [
    "Bina",
    "GorevNoktasi",
    "GunTipi",
    "OzelGun",
    "Personel",
    "PersonelYetkinlik",
    "Talep",
    "VardiyaTipi",
    "Yetkinlik",
]
