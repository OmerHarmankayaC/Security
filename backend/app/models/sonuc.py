import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.ortak import ZamanDamgasi, ZamanDamgasiKarisimi


class CizelgeSurumuDurumu(enum.StrEnum):
    TASLAK = "taslak"
    COZULDU = "cozuldu"
    YAYINLANDI = "yayinlandi"
    ARSIV = "arsiv"


class AtamaKaynagi(enum.StrEnum):
    COZUCU = "cozucu"
    MANUEL = "manuel"


class CozumIsiDurumu(enum.StrEnum):
    KUYRUKTA = "kuyrukta"
    ON_KONTROL = "on_kontrol"
    COZULUYOR = "cozuluyor"
    TAMAMLANDI = "tamamlandi"
    UYARILI = "uyarili"
    BASARISIZ = "basarisiz"
    IPTAL = "iptal"


class Donem(Base, ZamanDamgasiKarisimi):
    __tablename__ = "donem"

    donem_id: Mapped[int] = mapped_column(primary_key=True)
    baslangic_tarihi: Mapped[date] = mapped_column(Date)
    bitis_tarihi: Mapped[date] = mapped_column(Date)
    tercih_son_tarihi: Mapped[date] = mapped_column(Date)


class CizelgeSurumu(Base, ZamanDamgasiKarisimi):
    __tablename__ = "cizelge_surumu"

    surum_id: Mapped[int] = mapped_column(primary_key=True)
    donem_id: Mapped[int] = mapped_column(ForeignKey("donem.donem_id"))
    surum_no: Mapped[int]
    durum: Mapped[CizelgeSurumuDurumu] = mapped_column(default=CizelgeSurumuDurumu.TASLAK)
    onceki_surum_id: Mapped[int | None] = mapped_column(ForeignKey("cizelge_surumu.surum_id"))
    yayin_zamani: Mapped[datetime | None] = mapped_column(ZamanDamgasi)


class Atama(Base, ZamanDamgasiKarisimi):
    __tablename__ = "atama"
    __table_args__ = (
        UniqueConstraint("surum_id", "personel_id", "tarih", name="uq_atama_surum_personel_tarih"),
    )

    atama_id: Mapped[int] = mapped_column(primary_key=True)
    surum_id: Mapped[int] = mapped_column(ForeignKey("cizelge_surumu.surum_id"))
    personel_id: Mapped[int] = mapped_column(ForeignKey("personel.personel_id"))
    tarih: Mapped[date] = mapped_column(Date)
    vardiya_tipi_id: Mapped[int] = mapped_column(ForeignKey("vardiya_tipi.vardiya_tipi_id"))
    nokta_id: Mapped[int] = mapped_column(ForeignKey("gorev_noktasi.nokta_id"))
    kilitli: Mapped[bool] = mapped_column(default=False)
    kaynak: Mapped[AtamaKaynagi]


class CozumIsi(Base, ZamanDamgasiKarisimi):
    __tablename__ = "cozum_isi"

    is_id: Mapped[int] = mapped_column(primary_key=True)
    surum_id: Mapped[int] = mapped_column(ForeignKey("cizelge_surumu.surum_id"))
    durum: Mapped[CozumIsiDurumu] = mapped_column(default=CozumIsiDurumu.KUYRUKTA)
    baslangic_zamani: Mapped[datetime] = mapped_column(ZamanDamgasi)
    bitis_zamani: Mapped[datetime | None] = mapped_column(ZamanDamgasi)
    sure_saniye: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    zaman_limiti_saniye: Mapped[int]
    en_iyi_ceza: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    ceza_dokumu: Mapped[dict | None] = mapped_column(JSONB)
    kural_anlik_goruntu: Mapped[dict] = mapped_column(JSONB)
    hata_mesaji: Mapped[str | None]


class KapsamaAcigi(Base, ZamanDamgasiKarisimi):
    __tablename__ = "kapsama_acigi"

    acik_id: Mapped[int] = mapped_column(primary_key=True)
    surum_id: Mapped[int] = mapped_column(ForeignKey("cizelge_surumu.surum_id"))
    tarih: Mapped[date] = mapped_column(Date)
    vardiya_tipi_id: Mapped[int] = mapped_column(ForeignKey("vardiya_tipi.vardiya_tipi_id"))
    nokta_id: Mapped[int] = mapped_column(ForeignKey("gorev_noktasi.nokta_id"))
    eksik_sayi: Mapped[int]


class FazlaKadro(Base, ZamanDamgasiKarisimi):
    """Bir noktaya TALEPTEN FAZLA kisi atanmis olmasi (SRS 4.3 S1 ust siniri).

    `KapsamaAcigi`'nin aynadaki goruntusu ama AYRI bir tablo; gerekcesi
    goc dosyasinda (a4d92c15e807) uzun uzun yazili. Ozeti: kapsama acigi
    cozucunun `eksik` degiskeniyle birebirdir (SDD 4.2.4), fazla kadronun
    ise cozucude hicbir karsiligi yoktur - kaynagi yalnizca manuel
    duzenlemedir.
    """

    __tablename__ = "fazla_kadro"

    fazla_id: Mapped[int] = mapped_column(primary_key=True)
    surum_id: Mapped[int] = mapped_column(ForeignKey("cizelge_surumu.surum_id"), index=True)
    tarih: Mapped[date] = mapped_column(Date)
    vardiya_tipi_id: Mapped[int] = mapped_column(ForeignKey("vardiya_tipi.vardiya_tipi_id"))
    nokta_id: Mapped[int] = mapped_column(ForeignKey("gorev_noktasi.nokta_id"))
    fazla_sayi: Mapped[int]


__all__ = [
    "Atama",
    "AtamaKaynagi",
    "CizelgeSurumu",
    "CizelgeSurumuDurumu",
    "CozumIsi",
    "CozumIsiDurumu",
    "Donem",
    "FazlaKadro",
    "KapsamaAcigi",
]
