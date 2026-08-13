import enum
from datetime import date, time
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    # SDD 4.2.1 / SRS FR-1.1: icinde bulunulan kota yilinda, sistemin bildigi
    # donemlerden ONCE birikmis fazla calisma saati ve bu bakiyenin ait oldugu
    # takvim yili. Birikim normalde yayinlanmis surumlerin atamalarindan
    # turetilir ve saklanmaz (karar notu K11); devir bakiyesi tek istisnadir -
    # sistem canliya alinmadan onceki aylari bilemez. Turetilen deger buna
    # EKLENIR, bunun yerine gecmez.
    #
    # BU TURDA HICBIR KURAL BU ALANLARI OKUMAZ; Tur 5'te (GecmisSayaclar)
    # kullanilacak, simdilik yalnizca veri girilebilir hale geliyor.
    devir_fazla_calisma_saat: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal(0))
    kota_yili: Mapped[int | None]
    aktif_baslangic: Mapped[date] = mapped_column(Date)
    aktif_bitis: Mapped[date | None] = mapped_column(Date)

    yetkinlikler: Mapped[list["Yetkinlik"]] = relationship(secondary="personel_yetkinlik")


class Yetkinlik(Base, ZamanDamgasiKarisimi):
    __tablename__ = "yetkinlik"

    yetkinlik_id: Mapped[int] = mapped_column(primary_key=True)
    ad: Mapped[str] = mapped_column(unique=True)
    aciklama: Mapped[str | None]
    # Kullanimda olan bir tanim SILINMEZ, pasiflestirilir: gecmis cizelgeler
    # tanim satirlarina referansla durur (SDD 4.1) ve satir gidince atamalar
    # okunamaz hale gelir. gorev_noktasi'nda hali hazirda bulunan bu bayrak
    # (SDD 4.2.1) yetkinlik ve binaya da eklendi.
    aktif: Mapped[bool] = mapped_column(default=True)


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
    aktif: Mapped[bool] = mapped_column(default=True)


class GorevNoktasi(Base, ZamanDamgasiKarisimi):
    __tablename__ = "gorev_noktasi"

    nokta_id: Mapped[int] = mapped_column(primary_key=True)
    ad: Mapped[str]
    bina_id: Mapped[int | None] = mapped_column(ForeignKey("bina.bina_id"))
    onkosul_yetkinlik_id: Mapped[int | None] = mapped_column(ForeignKey("yetkinlik.yetkinlik_id"))
    aktif: Mapped[bool] = mapped_column(default=True)


class Talep(Base, ZamanDamgasiKarisimi):
    """Talep bir calisma bloguna degil bir ZAMAN ARALIGINA baglanir (SRS 3.3.4,
    TD-13; SDD 4.2.2).

    Talep bir bloga baglanamaz cunku blok diye bir tanim kalmadi: baslangic
    saati ve sure cozumun ciktisidir. Kullanicinin soylemek istedigi sey
    zaten "sabah sekizden aksam on ikiye kadar dokuz kisi bulunsun"dur;
    hangi bloklarin bu araligi hangi bilesimle kapatacagi cozucunun
    kararidir.

    GUN SONU `00.00` ILE GOSTERILIR. SDD 4.2.2 bunun icin `24.00` yaziyor;
    PostgreSQL o degeri saklayabiliyor fakat surucu (psycopg) `datetime.time`
    24:00 tasiyamadigi icin geri OKUYAMIYOR. Uygulanan sozlesme tektir:
    `bitis <= baslangic` ise aralik gun sonuna kadar surer ve gece yarisini
    asiyorsa ertesi gune tasar; acilim tek yerde (`talebi_saate_ac`) bu
    kurali uygular.
    """

    __tablename__ = "talep"

    talep_id: Mapped[int] = mapped_column(primary_key=True)
    nokta_id: Mapped[int] = mapped_column(ForeignKey("gorev_noktasi.nokta_id"))
    baslangic: Mapped[time] = mapped_column(Time)
    bitis: Mapped[time] = mapped_column(Time)
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
    "Yetkinlik",
]
