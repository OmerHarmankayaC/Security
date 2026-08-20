"""/api/donem, /api/surum, /api/surum/{id}/atama+kapsama-acigi semalari (SDD Ek B)."""

from datetime import date, datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, computed_field, model_validator

from app.models.sonuc import AtamaKaynagi, CizelgeSurumuDurumu

# Planlama doneminin azami uzunlugu (gun). Kabul kriteri 28 gunluk referans
# ornekle olculur (NFR-1); 31 gun onu kapsar ve takvimsel olarak "en uzun bir
# ay" karsiligidir. Ust sinirin varlik nedeni cozum suresinin donem uzunluguyla
# birlikte hizla buyumesi: sinir kaldirildiginda kullanici, arayuzden hicbir
# uyari almadan saatlerce donecek bir is baslatabilir.
#
# Bu deger dort kanonik dokumanda TANIMLI DEGILDIR; karar gunlugune islenmek
# uzere kullaniciya bildirildi.
AZAMI_DONEM_GUN = 31


class DonemOlustur(BaseModel):
    baslangic_tarihi: date
    bitis_tarihi: date
    tercih_son_tarihi: date

    @model_validator(mode="after")
    def _araligi_dogrula(self) -> Self:
        if self.bitis_tarihi < self.baslangic_tarihi:
            raise ValueError("Bitiş tarihi başlangıç tarihinden önce olamaz.")
        gun_sayisi = (self.bitis_tarihi - self.baslangic_tarihi).days + 1
        if gun_sayisi > AZAMI_DONEM_GUN:
            raise ValueError(
                f"Planlama dönemi en fazla {AZAMI_DONEM_GUN} gün olabilir; "
                f"seçilen aralık {gun_sayisi} gün."
            )
        if self.tercih_son_tarihi > self.bitis_tarihi:
            raise ValueError("Tercih son bildirim tarihi dönemin bitişinden sonra olamaz.")
        return self


class DonemOku(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    donem_id: int
    baslangic_tarihi: date
    bitis_tarihi: date
    tercih_son_tarihi: date


class CizelgeSurumuOku(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    surum_id: int
    donem_id: int
    surum_no: int
    durum: CizelgeSurumuDurumu
    onceki_surum_id: int | None
    yayin_zamani: datetime | None
    guncelleme_zamani: datetime
    # DUZENLEME DAMGASI (SRS TD-16, SDD 5.5.1). Es zamanli duzenlemeyi
    # yakalar: istemci duzenlemeye baslarken bu degeri alir, kaydederken
    # POST /api/atama/kaydet ile geri gonderir; degismisse baska bir oturum
    # ayni surumu degistirmis demektir ve kayit reddedilir. Istemci icin
    # OPAK bir dizedir - yorumlanmaz, tasinir.
    #
    # SEMADAN DUSURULEMEZ: alan yanitta yoksa istemcinin elinde damga hic
    # olusmaz ve "Kaydet" sessizce hicbir sey yapmaz (istek gitmez, hata
    # cikmaz, kullanici emegini kaybeder).
    damga: str


class AtamaOku(BaseModel):
    """Bir calisma blogu (SDD 4.2.1).

    `tarih` alani TURETILMISTIR, saklanmaz: blok basladigi gune sayilir
    (SRS TD-1) ve izgara satirlari o gune gore gruplanir. Ayri bir sutunda
    tutulsaydi iki alan ayrisabilirdi.
    """

    model_config = ConfigDict(from_attributes=True)

    atama_id: int
    personel_id: int
    baslangic_zamani: datetime
    bitis_zamani: datetime
    nokta_id: int
    kilitli: bool
    kaynak: AtamaKaynagi

    @computed_field  # type: ignore[prop-decorator]
    @property
    def tarih(self) -> date:
        return self.baslangic_zamani.date()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sure_saat(self) -> int:
        return round((self.bitis_zamani - self.baslangic_zamani).total_seconds() / 3600)


class KapsamaAcigiOku(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    acik_id: int
    # ZAMAN DAMGASI (B-23): gece yarisini asan aralik tek kayitta durur ve
    # disa aktarmada ISO damgasi olarak yazilir (SRS 7.2).
    baslangic_zamani: datetime
    bitis_zamani: datetime
    nokta_id: int
    eksik_sayi: int


class FazlaKadroOku(BaseModel):
    """Bir noktaya talepten fazla kisi atanmis olmasi (SRS 4.3 S1 ust siniri).

    `KapsamaAcigiOku` ile ayni sekli tasir; ayri tutulmasinin gerekcesi
    goc a4d92c15e807'de yazili.
    """

    model_config = ConfigDict(from_attributes=True)

    fazla_id: int
    baslangic_zamani: datetime
    bitis_zamani: datetime
    nokta_id: int
    fazla_sayi: int


class AtamaKilitIstek(BaseModel):
    surum_id: int
    personel_id: int
    tarih: date
    kilitli: bool


class SurumTaslakTuretIstek(BaseModel):
    """Bos taslak istegi: MEVCUT BIR SURUMDEN ya da DOGRUDAN DONEMDEN.

    Ikisi de verilirse hangisinin kazandigi belirsiz kalir ve istegi yazan
    taraf yanlis varsayimla devam eder; hicbiri verilmezse istek zaten
    anlamsizdir. Ikisi de 422 ile reddedilir.
    """

    onceki_surum_id: int | None = None
    donem_id: int | None = None

    @model_validator(mode="after")
    def _tam_olarak_biri(self) -> "SurumTaslakTuretIstek":
        if (self.onceki_surum_id is None) == (self.donem_id is None):
            raise ValueError("onceki_surum_id ya da donem_id verilmeli, ikisi birden degil")
        return self


# --- Surumler ekrani (SDD 6.3.5) -------------------------------------------


class SurumOzetiOku(BaseModel):
    """Surum listesi satiri: SDD 6.3.5'in istedigi "numara, durum, olusturma
    zamani, toplam ceza ve kapsama acigi sayisi"."""

    surum_id: int
    donem_id: int
    surum_no: int
    durum: CizelgeSurumuDurumu
    onceki_surum_id: int | None
    yayin_zamani: datetime | None
    olusturma_zamani: datetime
    guncelleme_zamani: datetime
    # DUZENLEME DAMGASI (SRS TD-16, SDD 5.5.1) - `CizelgeSurumuOku.damga` ile
    # ayni deger, ayni amac: es zamanli duzenlemeyi yakalar. Cizelge ekrani
    # damgayi BU LISTEDEN okur (surum seciciyle birlikte gelen tek kaynak),
    # kaydederken geri gonderir. Alan burada eksikse Kaydet sessizce hicbir
    # sey yapmaz.
    damga: str
    # Surumun EN SON cozum isindeki toplam ceza; hic cozulmemis bir taslakta None.
    toplam_ceza: float | None
    # Acik hucre sayisi degil toplam eksik KISI sayisi (bkz. depo metodu).
    kapsama_acigi_sayisi: int
    # Talepten FAZLA yazilmis toplam kisi sayisi (SRS 4.3 S1 ust siniri).
    # Ayri bir alan: kapsama acigiyla toplanmasi iki zit yondeki sapmayi
    # tek sayida gizler ve "3 acik" ile "3 fazla" ayni gorunurdu.
    fazla_kadro_sayisi: int = 0
    # Surumun toplam atama sayisi (Gorev 6). Ozet ekrani "olculebilir
    # surum"u bununla secer: olcut artik "taslak degil" degil "atamasi
    # var" - elle cizilen bos taslak (Gorev 1) "taslak degil" olcutunu
    # gecersiz kildi.
    atama_sayisi: int = 0


class AtamaFarkiOku(BaseModel):
    """Iki surum arasinda (personel, tarih) ekseninde tek bir fark."""

    personel_id: int
    ad_soyad: str
    tarih: date
    tur: Literal["eklendi", "kaldirildi", "degisti"]
    # Blok adi diye bir sey yok; karsilastirmanin gosterdigi sey blogun
    # SAAT ARALIGIDIR ("08.00–16.00"). Metin biciminde tasinir cunku
    # karsilastirma ekrani onu oldugu gibi yazar.
    onceki_blok: str | None
    onceki_nokta_ad: str | None
    yeni_blok: str | None
    yeni_nokta_ad: str | None


class SurumKarsilastirmaOku(BaseModel):
    onceki_surum_id: int
    yeni_surum_id: int
    onceki_surum_no: int
    yeni_surum_no: int
    eklenen: int
    kaldirilan: int
    degisen: int
    # Charter bolum 5, altinci kabul kriteri: "yeniden cozumde degisen atama
    # sayisi raporlanir" - raporlanan sayi budur.
    toplam_degisiklik: int
    farklar: list[AtamaFarkiOku]
