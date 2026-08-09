"""/api/donem, /api/surum, /api/surum/{id}/atama+kapsama-acigi semalari (SDD Ek B)."""

from datetime import date, datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, model_validator

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


class AtamaOku(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    atama_id: int
    personel_id: int
    tarih: date
    vardiya_tipi_id: int
    nokta_id: int
    kilitli: bool
    kaynak: AtamaKaynagi


class KapsamaAcigiOku(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    acik_id: int
    tarih: date
    vardiya_tipi_id: int
    nokta_id: int
    eksik_sayi: int


class AtamaKilitIstek(BaseModel):
    surum_id: int
    personel_id: int
    tarih: date
    kilitli: bool


class SurumTaslakTuretIstek(BaseModel):
    onceki_surum_id: int


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
    # Surumun EN SON cozum isindeki toplam ceza; hic cozulmemis bir taslakta None.
    toplam_ceza: float | None
    # Acik hucre sayisi degil toplam eksik KISI sayisi (bkz. depo metodu).
    kapsama_acigi_sayisi: int


class AtamaFarkiOku(BaseModel):
    """Iki surum arasinda (personel, tarih) ekseninde tek bir fark."""

    personel_id: int
    ad_soyad: str
    tarih: date
    tur: Literal["eklendi", "kaldirildi", "degisti"]
    onceki_vardiya_tipi_ad: str | None
    onceki_nokta_ad: str | None
    yeni_vardiya_tipi_ad: str | None
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
