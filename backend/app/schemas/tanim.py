"""Tanim yonetimi uc noktalarinin istek/yanit semalari (SDD 3.2, Ek B)."""

from datetime import date, time
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.kurallar.zaman_araligi import tam_saat_mi
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


# Sicil kirpilir ve bos birakilamaz. Kirpma sunucuda yapilir, arayuzde
# degil: bastaki/sondaki bosluk gorunmez ve "AY-1" ile "AY-1 " iki ayri
# kayit olarak gecip benzersizlik kontrolunu anlamsiz kilardi.
Sicil = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class PersonelOlustur(BaseModel):
    ad_soyad: str
    sicil_no: Sicil
    haftalik_hedef_saat: int
    aktif_baslangic: date
    aktif_bitis: date | None = None
    yetkinlik_idleri: list[int] = Field(default_factory=list)
    # Devir bakiyesi (SRS FR-1.1). Bos birakildiginda SIFIR: "devri bilmiyorum"
    # ile "devri yok" arasindaki fark, bakiyeyi okuyan bir kural yazilana
    # kadar (Tur 4) hicbir hesaba girmiyor.
    devir_fazla_calisma_saat: Decimal = Decimal(0)
    kota_yili: int | None = None


class PersonelGuncelle(BaseModel):
    ad_soyad: str | None = None
    sicil_no: Sicil | None = None
    haftalik_hedef_saat: int | None = None
    aktif_baslangic: date | None = None
    aktif_bitis: date | None = None
    yetkinlik_idleri: list[int] | None = None
    devir_fazla_calisma_saat: Decimal | None = None
    kota_yili: int | None = None


class PersonelOku(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    personel_id: int
    ad_soyad: str
    sicil_no: str
    haftalik_hedef_saat: int
    aktif_baslangic: date
    aktif_bitis: date | None
    yetkinlik_idleri: list[int]
    devir_fazla_calisma_saat: Decimal
    kota_yili: int | None

    @classmethod
    def modelden_olustur(cls, personel: Personel) -> "PersonelOku":
        return cls(
            personel_id=personel.personel_id,
            ad_soyad=personel.ad_soyad,
            sicil_no=personel.sicil_no,
            haftalik_hedef_saat=personel.haftalik_hedef_saat,
            aktif_baslangic=personel.aktif_baslangic,
            aktif_bitis=personel.aktif_bitis,
            yetkinlik_idleri=[y.yetkinlik_id for y in personel.yetkinlikler],
            devir_fazla_calisma_saat=personel.devir_fazla_calisma_saat,
            kota_yili=personel.kota_yili,
        )


# --- Ozel Gun (resmi tatil) ------------------------------------------------


class OzelGunOlustur(BaseModel):
    tarih: date
    ad: str


class OzelGunGuncelle(BaseModel):
    """Yalniz ad degisir; tarih birincil anahtardir (SDD 4.2.1).

    Tarihi degistirmek yeni bir kayit acmakla aynidir ve o yol zaten
    ekleme/silme ikilisiyle aciktir; PUT'a tarih koymak, ayni islemin ikinci
    bir yolunu yaratirdi.
    """

    ad: str


class OzelGunOku(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tarih: date
    ad: str


# --- Talep -----------------------------------------------------------------


class TalepYazma(BaseModel):
    """Bir talep ARALIGI (SDD 4.2.2, SRS FR-1.7).

    Gun sonu `00.00` ile yazilir; `bitis <= baslangic` araligin gun sonuna
    kadar surdugunu (ya da gece yarisini astigini) gosterir - `vardiya_tipi`
    tablosunun zaten kullandigi sozlesme.
    """

    nokta_id: int
    gun_tipi: GunTipi
    tarih: date | None = None
    baslangic: time
    bitis: time
    gereken_sayi: int = Field(ge=0)

    @model_validator(mode="after")
    def _saat_basinda_olmali(self) -> "TalepYazma":
        # Kapsama kisiti saat ekseninde yazilir (SRS 4.3 S1); yarim saatlik
        # bir sinir hicbir saate denk dusmez ve talep sessizce kaybolurdu.
        if not tam_saat_mi(self.baslangic) or not tam_saat_mi(self.bitis):
            raise ValueError("Talep araliklari saat basinda baslar ve biter")
        return self


class TalepOku(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    talep_id: int
    nokta_id: int
    gun_tipi: GunTipi
    tarih: date | None
    baslangic: time
    bitis: time
    gereken_sayi: int


class YukGostergesi(BaseModel):
    """FR-1.9: talepten hesaplanan haftalik yuk ve asgari kadro buyuklugu.

    HESAP SAAT TABANLIDIR ve kisi-vardiya karsiligi GOSTERILMEZ: karisik
    uzunluklu bir katalogda o sayi katalogun bilesimine baglidir ve ayni
    talep icin farkli sayilar uretir (SRS 3.3.6, FR-1.9).
    """

    haftalik_kisi_saat: Decimal
    asgari_kadro: int


class TalepYaniti(BaseModel):
    # Alan adi `hucreler` DEGIL: talep artik gorev noktasi x vardiya tipi
    # matrisinin bir hucresi degil, bagimsiz bir zaman araligi kaydidir
    # (SDD 4.2.2). Eski ad, ekranin da matris cizmesine yol acmisti.
    araliklar: list[TalepOku]
    yuk_gostergesi: YukGostergesi
