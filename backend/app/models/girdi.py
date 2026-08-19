import enum
from datetime import date, time

from sqlalchemy import Date, ForeignKey, LargeBinary, Time, UniqueConstraint
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
    # Blok katalogu kalktigi icin tercih artik bir vardiya TIPINI degil bir
    # ZAMAN ARALIGINI gosterir (SRS FR-3.2, TD-12).
    ZAMAN_ARALIGI_TERCIHI = "zaman_araligi_tercihi"


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


# Kisit ADI tek yerde: yakalayan taraf (routers/tanim.py) hangi kisidin
# dustugunu metinden ayirt eder ve yabanci anahtar ihlalini yanlislikla
# "bu gun icin zaten tercih var" diye raporlamaz.
TERCIH_GUN_TEKILLIGI = "uq_tercih_personel_tarih"


class Tercih(Base, ZamanDamgasiKarisimi):
    __tablename__ = "tercih"
    # Bir calisan bir gun icin TEK tercih bildirir. Iki kayit, biri
    # "calismam" digeri "08-16 calisirim" oldugunda hangisinin gecerli
    # oldugu tanimsiz kalirdi; ikisi de onaylanabilirdi.
    __table_args__ = (UniqueConstraint("personel_id", "tarih", name=TERCIH_GUN_TEKILLIGI),)

    tercih_id: Mapped[int] = mapped_column(primary_key=True)
    personel_id: Mapped[int] = mapped_column(ForeignKey("personel.personel_id"))
    donem_id: Mapped[int] = mapped_column(ForeignKey("donem.donem_id"))
    tarih: Mapped[date] = mapped_column(Date)
    tip: Mapped[TercihTipi]
    # Zaman araligi tercihlerinde istenen aralik; calismama tercihinde bos.
    # Gun sonu `00.00` ile yazilir (zaman_araligi modulundeki sozlesme).
    tercih_baslangic: Mapped[time | None] = mapped_column(Time)
    tercih_bitis: Mapped[time | None] = mapped_column(Time)
    durum: Mapped[TercihDurumu] = mapped_column(default=TercihDurumu.BEKLEMEDE)
    calisan_notu: Mapped[str | None] = mapped_column(default=None)
    ret_gerekcesi: Mapped[str | None] = mapped_column(default=None)


class MusaitlikBelgesi(Base, ZamanDamgasiKarisimi):
    """Bir izin kaydina eklenen belge (doktor raporu, izin dilekcesi).

    AYRI TABLO, `musaitlik` sutunu DEGIL. Izin listesi her ekranda okunur ve
    ikili icerigi ayni satirda tasimak, belgeyi hic istemeyen sorgulari da
    ona baglardi. Bire bir iliski `musaitlik_id` uzerindeki benzersizlik
    kisitiyla zorlanir: bir izin kaydinin en fazla bir belgesi olur.

    ICERIK VERITABANINDA DURUR (bytea), dosya sisteminde degil. Projenin
    yedekleme yordami `pg_dump`tir (deploy/DAGITIM.md) ve dosya sistemi ondan
    HARICTIR; belgeler diske yazilsaydi yedegi alinmayan bir veri turu dogar
    ve bu ancak geri yukleme gununde fark edilirdi.

    SAGLIK VERISI OLABILIR (doktor raporu): okuma yetkisi kayit sahibine ve
    yonetici tarafina sinirlidir, bkz. routers/girdi.py.
    """

    __tablename__ = "musaitlik_belgesi"
    __table_args__ = (UniqueConstraint("musaitlik_id", name="uq_musaitlik_belgesi_musaitlik"),)

    belge_id: Mapped[int] = mapped_column(primary_key=True)
    musaitlik_id: Mapped[int] = mapped_column(ForeignKey("musaitlik.musaitlik_id"))
    # Kullanicinin yukledigi ad; indirmede bu adla sunulur.
    dosya_adi: Mapped[str]
    # MIME tipi; taranan ad degil, KABUL EDILEN tiplerden biri (servis dogrular).
    icerik_tipi: Mapped[str]
    boyut_bayt: Mapped[int]
    icerik: Mapped[bytes] = mapped_column(LargeBinary)


__all__ = [
    "TERCIH_GUN_TEKILLIGI",
    "MusaitlikBelgesi",
    "Musaitlik",
    "MusaitlikDilimi",
    "MusaitlikTipi",
    "Tercih",
    "TercihDurumu",
    "TercihTipi",
]
