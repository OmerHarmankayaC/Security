"""Hesap yonetimi semalari (SRS FR-10.5 - FR-10.7).

Okuma semasi PAROLA OZETINI TASIMAZ. Ozet dogrulanabilir bir veridir;
arayuze gonderilmesinin hicbir karsiligi yok, sizmasinin ise cevrimdisi
deneme maliyeti var.
"""

from pydantic import BaseModel, Field

from app.models.kimlik import Rol


class KullaniciOku(BaseModel):
    kullanici_id: int
    kullanici_adi: str
    rol: Rol
    personel_id: int | None
    ad_soyad: str | None
    aktif: bool
    parola_degistirmeli: bool
    kilitli_mi: bool


class KullaniciOlustur(BaseModel):
    kullanici_adi: str
    # Asgari uzunluk kurali app/services/parola.py'de tek yerde durur; burada
    # tekrarlanirsa biri degistiginde digeri sessizce eski kurali uygular.
    parola: str = Field(min_length=1)
    rol: Rol
    personel_id: int | None = None


class KullaniciGuncelle(BaseModel):
    """Kismi guncelleme; verilmeyen alan degismez.

    `personel_id` icin `None` GECERLI bir degerdir (baglantiyi kaldirmak),
    dolayisiyla "verilmedi" ile "None verildi" ayrimi alanin sozlukte
    bulunup bulunmamasindan okunur (`model_fields_set`).
    """

    rol: Rol | None = None
    aktif: bool | None = None
    personel_id: int | None = None


class ParolaSifirla(BaseModel):
    yeni_parola: str = Field(min_length=1)
