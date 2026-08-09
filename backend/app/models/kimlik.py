"""Kimlik varliklari: kullanici ve oturum (SDD 4.2.1).

Iki tablo, iki ayri isi tasir. `kullanici` HESABI tanimlar (kim, hangi rol,
hangi personele bagli, girebilir mi); `oturum` o hesabin ACIK GIRISLERINI
tanimlar. Ayrilmalarinin nedeni geri alinabilirliktir: bir hesap devre disi
birakildiginda ya da parolasi sifirlandiginda, o hesaba ait oturum satirlari
silinerek acik girisler ANINDA gecersiz kilinir (SDD 5.1b). Kendi kendini
dogrulayan bir belirtec (JWT) bunu ayri bir kara liste altyapisi olmadan
saglayamazdi (Backlog karar gunlugu, 09.08.2026).
"""

import enum
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, String, false, text, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.ortak import ZamanDamgasi, ZamanDamgasiKarisimi


class Rol(enum.StrEnum):
    """SRS 5.10'daki uc rol.

    Roller KAPSAYICI degil, ayri degerlerdir: `YONETIM`, `YONETICI`nin
    yetkilerini icerir ama bu iceri alma veritabaninda degil yetkilendirme
    katmaninda (app/services/yetki.py) tanimlanir - siralamayi veriye
    gomsek, yeni bir rol eklendiginde siralamanin nereye girecegi sessiz bir
    karara donusurdu.
    """

    CALISAN = "calisan"
    YONETICI = "yonetici"
    YONETIM = "yonetim"


class Kullanici(Base, ZamanDamgasiKarisimi):
    __tablename__ = "kullanici"

    kullanici_id: Mapped[int] = mapped_column(primary_key=True)
    # KUCUK HARFLE saklanir (asagidaki CHECK kisiti). Aksi halde "Ahmet" ve
    # "ahmet" iki ayri satir olur ve benzersizlik kisiti bunu engellemez;
    # kullanici hangi yaziliskla hesabinin acildigini bilmek zorunda kalirdi.
    # Girisin kullanici adini kucuk harfe cevirip eslemesi ancak saklanan
    # degerin de kucuk harf oldugu garantiliyse dogru sonuc verir.
    kullanici_adi: Mapped[str] = mapped_column(unique=True)
    # Argon2id ozeti (SDD 5.1b). Parolanin kendisi hicbir bicimde saklanmaz
    # (FR-10.2); ozet uretimi ve dogrulamasi app/services/parola.py'dedir.
    parola_ozeti: Mapped[str]
    rol: Mapped[Rol]
    personel_id: Mapped[int | None] = mapped_column(ForeignKey("personel.personel_id"))
    # FR-10.7: yonetim tarafindan atanan veya sifirlanan parola ilk giriste
    # degistirilmek zorundadir; degistirilene kadar diger uc noktalar kapali.
    parola_degistirmeli: Mapped[bool] = mapped_column(server_default=false())
    # FR-10.5: hesap SILINMEZ, devre disi birakilir. Giris kayitlari ve
    # gecmis islemler hesabin kimligine baglidir (Backlog, 09.08.2026).
    aktif: Mapped[bool] = mapped_column(server_default=true())
    # FR-10.8: ardisik basarisiz giris sayaci; basarili giriste sifirlanir.
    basarisiz_deneme: Mapped[int] = mapped_column(server_default=text("0"))
    kilit_bitis: Mapped[datetime | None] = mapped_column(ZamanDamgasi)

    __table_args__ = (
        # FR-10.6: baglantisi olmayan bir CALISAN hesabi olusturulamaz.
        # Kisit veritabaninda da durur, yalniz serviste degil: bu kural
        # ihlal edildiginde ortaya cikan sey "eksik alan" degil, KIMIN
        # verisini gorecegi belirsiz bir calisan hesabidir (FR-9.1'in
        # dayandigi baglantinin ta kendisi). Betikten veya elle SQL'den
        # acilan bir hesap da bu kapiya carpar.
        CheckConstraint(
            "rol <> 'CALISAN' OR personel_id IS NOT NULL",
            name="ck_kullanici_calisan_personele_bagli",
        ),
        # Kullanici adi kucuk harfle saklanir. `lower()` burada guvenle
        # kullanilabilir cunku hesap acma yolu kullanici adini ASCII
        # kumesiyle sinirlar (bkz. app/services/kullanici_servisi.py):
        # Turkce I/i cifti, PostgreSQL'in yerel ayarina ve Python'un
        # `str.lower`ina gore FARKLI sonuc verir ve iki taraf birbirini
        # bulamazdi.
        CheckConstraint(
            "kullanici_adi = lower(kullanici_adi)",
            name="ck_kullanici_adi_kucuk_harf",
        ),
    )


class OturumKaydi(Base):
    """Acik bir girisin sunucu tarafindaki kaydi (SDD 4.2.1, 5.1b).

    SINIF ADI tabloyla ayni degil ve bu bilincli: bu kod tabaninda `oturum`
    adi bastan beri SQLAlchemy `Session`ini tasiyor (`oturum_al`, servislerin
    `self.oturum`u). `Oturum` adli bir model, `self.oturum.add(Oturum(...))`
    gibi iki ayri seyin ayni adla gectigi satirlar uretirdi. Tablo adi
    SDD 4.2.1'deki gibi `oturum` kalir.

    `ZamanDamgasiKarisimi` KULLANILMAZ. Karisimin verecegi
    `guncelleme_zamani` ile buradaki `son_erisim` ayni olguyu iki adla
    tasirdi; SDD 4.2.1 oturum icin ucu de acikca sayar ve hareketsizlik
    olcumu son_erisim uzerinden yapilir.
    """

    __tablename__ = "oturum"

    # Belirtecin KENDISI degil, ozeti (SDD 5.1b). Belirtec yalniz cerezde
    # durur; veritabani okunsa bile mevcut oturumlar ele gecirilemez.
    oturum_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    kullanici_id: Mapped[int] = mapped_column(
        # Hesap devre disi birakilir, silinmez; yine de personel/kullanici
        # temizligi yapan bir goc kalintili oturum birakmasin diye kaskad.
        ForeignKey("kullanici.kullanici_id", ondelete="CASCADE"),
        index=True,
    )
    olusturma: Mapped[datetime] = mapped_column(ZamanDamgasi)
    # Hareketsizlik suresi bu andan olculur; her yetkili istekte tazelenir.
    son_erisim: Mapped[datetime] = mapped_column(ZamanDamgasi)
    # Mutlak son kullanma. Hareketsizlikten AYRI uygulanir: surekli istek
    # gonderen bir oturum da bu ani gecince kapanir.
    gecerlilik_bitis: Mapped[datetime] = mapped_column(ZamanDamgasi)
