"""Tanim yonetimi uc noktalarinin istek/yanit semalari (SDD 3.2, Ek B)."""

from datetime import date, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.tanim import GunTipi, Personel

# --- Silme on kontrolu -----------------------------------------------------


class KullanimKalemi(BaseModel):
    """Tanimin tek bir kayit turunde kac kez gectigi."""

    # Kullaniciya gosterilecek ad ("atama", "talep satiri", ...); alan adi degil,
    # operasyon dili (NFR-5).
    kayit_turu: str
    sayi: int


class KullanimOku(BaseModel):
    """Bir tanimin silinmeye calisildiginda ne olacagini onceden bildirir.

    Arayuz, onay kutusunun metnini bundan kurar: kullanimda olan bir tanim
    silinmez, pasiflestirilir. DELETE'in kendisi de ayni hesabi yapar; bu uc
    nokta yalnizca kullaniciya sonucu ONCEDEN gostermek icindir.
    """

    kullanimda_mi: bool
    toplam: int
    kalemler: list[KullanimKalemi]


# --- Yetkinlik ---------------------------------------------------------


class YetkinlikOlustur(BaseModel):
    ad: str
    aciklama: str | None = None


class YetkinlikGuncelle(BaseModel):
    ad: str | None = None
    aciklama: str | None = None
    aktif: bool | None = None


class YetkinlikOku(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    yetkinlik_id: int
    ad: str
    aciklama: str | None
    aktif: bool


# --- Bina ----------------------------------------------------------------


class BinaOlustur(BaseModel):
    ad: str


class BinaGuncelle(BaseModel):
    ad: str | None = None
    aktif: bool | None = None


class BinaOku(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bina_id: int
    ad: str
    aktif: bool


# --- Vardiya Tipi ----------------------------------------------------------


class VardiyaTipiOlustur(BaseModel):
    ad: str
    baslangic_saati: time
    bitis_saati: time
    gece_mi: bool | None = None  # bos ise TD-2'ye gore onerilen deger kullanilir (FR-1.4)


class VardiyaTipiGuncelle(BaseModel):
    ad: str | None = None
    baslangic_saati: time | None = None
    bitis_saati: time | None = None
    gece_mi: bool | None = None
    aktif: bool | None = None


class VardiyaTipiOku(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vardiya_tipi_id: int
    ad: str
    baslangic_saati: time
    bitis_saati: time
    sure_saat: Decimal
    gece_mi: bool
    aktif: bool


# --- Gorev Noktasi -----------------------------------------------------


class GorevNoktasiOlustur(BaseModel):
    ad: str
    bina_id: int | None = None
    onkosul_yetkinlik_id: int | None = None


class GorevNoktasiGuncelle(BaseModel):
    ad: str | None = None
    bina_id: int | None = None
    onkosul_yetkinlik_id: int | None = None
    aktif: bool | None = None


class GorevNoktasiOku(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nokta_id: int
    ad: str
    bina_id: int | None
    onkosul_yetkinlik_id: int | None
    aktif: bool


# --- Personel ------------------------------------------------------------


class PersonelOlustur(BaseModel):
    ad_soyad: str
    sicil_no: str
    haftalik_hedef_saat: int
    sabit_vardiya_tipi_id: int | None = None
    aktif_baslangic: date
    aktif_bitis: date | None = None
    yetkinlik_idleri: list[int] = Field(default_factory=list)


class PersonelGuncelle(BaseModel):
    ad_soyad: str | None = None
    sicil_no: str | None = None
    haftalik_hedef_saat: int | None = None
    sabit_vardiya_tipi_id: int | None = None
    aktif_baslangic: date | None = None
    aktif_bitis: date | None = None
    yetkinlik_idleri: list[int] | None = None


class PersonelOku(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    personel_id: int
    ad_soyad: str
    sicil_no: str
    haftalik_hedef_saat: int
    sabit_vardiya_tipi_id: int | None
    aktif_baslangic: date
    aktif_bitis: date | None
    yetkinlik_idleri: list[int]

    @classmethod
    def modelden_olustur(cls, personel: Personel) -> "PersonelOku":
        return cls(
            personel_id=personel.personel_id,
            ad_soyad=personel.ad_soyad,
            sicil_no=personel.sicil_no,
            haftalik_hedef_saat=personel.haftalik_hedef_saat,
            sabit_vardiya_tipi_id=personel.sabit_vardiya_tipi_id,
            aktif_baslangic=personel.aktif_baslangic,
            aktif_bitis=personel.aktif_bitis,
            yetkinlik_idleri=[y.yetkinlik_id for y in personel.yetkinlikler],
        )


# --- Talep -----------------------------------------------------------------


class TalepHucresi(BaseModel):
    nokta_id: int
    vardiya_tipi_id: int
    gun_tipi: GunTipi
    tarih: date | None = None
    gereken_sayi: int = Field(ge=0)


class TalepOku(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    talep_id: int
    nokta_id: int
    vardiya_tipi_id: int
    gun_tipi: GunTipi
    tarih: date | None
    gereken_sayi: int


class YukGostergesi(BaseModel):
    """FR-1.9: talep matrisinden hesaplanan haftalik yuk ve asgari kadro buyuklugu."""

    haftalik_kisi_vardiya: int
    haftalik_kisi_saat: Decimal
    asgari_kadro: int


class TalepYaniti(BaseModel):
    hucreler: list[TalepOku]
    yuk_gostergesi: YukGostergesi
