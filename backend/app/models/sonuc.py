import enum
from datetime import date, datetime, time
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Date, ForeignKey, Numeric, String, Time, UniqueConstraint
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
    # Arama sonlandi, sonuc `gecici_sonuc`ta duruyor ve KULLANICI KARARI
    # bekleniyor (SDD 5.4.1). Terminal bir durum degildir: karar `kullan`
    # ise tamamlandi/uyarili'ya, `at` ve `devam` ise iptal'e gider.
    DURDURULDU = "durduruldu"
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
    # DUZENLEME DAMGASI (SRS TD-16, SDD 5.5.1). Kullanici duzenlemeye
    # baslarken bu degeri alir, kaydederken geri gonderir; degismisse
    # baska bir oturum ayni surumu degistirmis demektir ve kayit reddedilir.
    # Sessizce uzerine yazmak, digerinin isini iz birakmadan yok ederdi.
    #
    # NEDEN `guncelleme_zamani` DEGIL: o alan satirin her dokunulusunda
    # degisir (yayinlama, arsivleme) ve mikrosaniye duyarliligiyla JSON
    # uzerinden gidip gelir; esitlik karsilastirmasi bicimlendirmeye bagimli
    # hale gelirdi. Damga OPAK bir dizedir - istemci yorumlamaz, tasir.
    damga: Mapped[str] = mapped_column(String(36), default=lambda: str(uuid4()))


class Atama(Base, ZamanDamgasiKarisimi):
    """Bir CALISMA BLOGU (SDD 4.2.1).

    KAYIT SAAT BASINA DEGIL BLOK BASINA TUTULUR. Cozucunun ciktisi saat
    duzeyindedir (SRS TD-13); ardisik calisma saatleri yazma aninda tek bir
    bloga toplanir. Saat basina satir tutulmasi halinde otuz personelin
    yedi gunluk bir donemi yaklasik bin alti yuz satir eder ve her okuma
    yuzeyi - cizelge izgarasi, manuel duzenleme, surum karsilastirmasi,
    disa aktarma - satirlari yeniden bloklara toplamak zorunda kalirdi.

    Tarih alani yerine BASLANGIC ZAMANI tutulur; gece yarisini asan blok
    boylece tek kayitta durur ve `bitis_zamani` ertesi gune duser. Blogun
    hangi gune sayildigi (SRS TD-1) baslangic zamanindan TURETILIR, ayri
    bir alanda saklanmaz - iki alan ayrisabilir.

    BENZERSIZLIK KISITI BIR GUVENCE KAYBEDDI. Eski anahtar
    `(surum_id, personel_id, tarih)` idi ve "gunde tek atama"yi veritabani
    duzeyinde zorluyordu. Yeni anahtar baslangic ZAMANINI tasidigi icin ayni
    gunde farkli saatte baslayan ikinci bir blogu yakalayamaz; o kural artik
    yalnizca uygulama katmanindadir (H1) ve manuel duzenleme yolu onu
    denetlemek zorundadir.
    """

    __tablename__ = "atama"
    __table_args__ = (
        UniqueConstraint(
            "surum_id",
            "personel_id",
            "baslangic_zamani",
            name="uq_atama_surum_personel_baslangic",
        ),
    )

    atama_id: Mapped[int] = mapped_column(primary_key=True)
    surum_id: Mapped[int] = mapped_column(ForeignKey("cizelge_surumu.surum_id"))
    personel_id: Mapped[int] = mapped_column(ForeignKey("personel.personel_id"))
    baslangic_zamani: Mapped[datetime] = mapped_column(ZamanDamgasi)
    bitis_zamani: Mapped[datetime] = mapped_column(ZamanDamgasi)
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
    # SDD 4.2.4: durdurulan isin, kullanici karari beklerken ATAMALARA
    # YAZILMAMIS cozumu - yani isin CIKTISI. HICBIR OKUMA YUZEYININ KAYNAGI
    # DEGILDIR: cizelge izgarasi, analiz, surum karsilastirmasi, disa
    # aktarma ve calisan paneli atama tablosundan beslenir. Tek yonlu, tek
    # seferlik bir aktarim tamponudur: isci bir kez yazar, karar bir kez
    # okuyup bosaltir.
    gecici_sonuc: Mapped[dict | None] = mapped_column(JSONB)
    # "Devam et" karariyla baslatilan isin cozucuye baslangic ipucu olarak
    # verdigi cozum - yani isin GIRDISI. `gecici_sonuc`tan AYRI bir sutunda
    # durur (SDD 4.2.4): ayni deger tek alanda tasinsaydi bir iste "karar
    # bekliyor", baska bir iste "modele verilecek ipucu" anlamina gelir ve
    # alanin dolulugana bakan bir sorgu henuz baslamamis bir isi karar
    # bekliyor sanabilirdi.
    #
    # IS SONLANDIGINDA bosaltilir, model kurulunca DEGIL: model kurulumunda
    # silinirse isci yeniden basladiginda (servis yeniden baslatilir ya da
    # is kuyruga doner) is ipucusuz devam eder, sonuc sessizce kotulesir ve
    # bunu gosteren hicbir iz kalmaz.
    cozum_ipucu: Mapped[dict | None] = mapped_column(JSONB)
    # ON KONTROL BULGULARI, isle birlikte KALICI (SDD 5.2, karar notu K18).
    # Bulgular artik isi dusurmuyor; sonucla BIRLIKTE gosterilmeleri ve
    # surumun raporunda kalmalari gerekiyor. Yalnizca cozum aninda
    # gorunup kaybolan bir bilgi, yayinlanmis cizelgeye sonradan bakan
    # kisi icin hic var olmamistir.
    on_kontrol_bulgulari: Mapped[list | None] = mapped_column(JSONB)
    # "Devam et" karariyla turetilmis islerde, ipucunun alindigi onceki is.
    devam_kaynagi_is_id: Mapped[int | None] = mapped_column(ForeignKey("cozum_isi.is_id"))
    hata_mesaji: Mapped[str | None]


class KapsamaAcigi(Base, ZamanDamgasiKarisimi):
    """Talebin karsilanamadigi ZAMAN ARALIKLARI (SDD 4.2.4).

    Kayit saat saat degil aralik olarak tutulur: ardisik ve eksik sayisi esit
    olan saatler tek satirda birlestirilir. Yirmi dort satirlik bir liste
    kullaniciya hicbir sey anlatmaz; "00.00-08.00 arasi bir kisi eksik"
    anlatir. Birlestirme YAZMA aninda yapilir, okuma aninda degil - aksi
    halde her tuketici kendi birlestirme mantigini yazar ve ikisi ayrisir
    (bkz. app/services/aralik_birlestirme.py).
    """

    __tablename__ = "kapsama_acigi"

    acik_id: Mapped[int] = mapped_column(primary_key=True)
    surum_id: Mapped[int] = mapped_column(ForeignKey("cizelge_surumu.surum_id"))
    tarih: Mapped[date] = mapped_column(Date)
    baslangic: Mapped[time] = mapped_column(Time)
    bitis: Mapped[time] = mapped_column(Time)
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
    baslangic: Mapped[time] = mapped_column(Time)
    bitis: Mapped[time] = mapped_column(Time)
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
