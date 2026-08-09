"""Kimlik uc noktalarinin semalari (SRS FR-10.1, FR-10.7; SDD 5.1b).

Hicbir semada parola ya da belirtec DONMEZ. Parola yalnizca istek
govdesinde girer, belirtec yalnizca cerezde cikar; ikisi de yanit
govdesinde gorunmez ki gunluge, tarayici gecmisine ya da bir hata
raporuna dusmesinler.
"""

from pydantic import BaseModel, Field

from app.models.kimlik import Rol


class GirisIstegi(BaseModel):
    kullanici_adi: str
    parola: str


class BenOku(BaseModel):
    """Giris yapmis kullanicinin arayuze donen tanimi.

    `personel_id` bilgilendirme icindir; calisan isteklerinde hangi
    personelin verisinin donecegi sunucuda OTURUMDAN belirlenir ve bu alanin
    istemciye donmesi o secime hicbir sekilde girmez (SRS FR-9.1).
    """

    kullanici_adi: str
    rol: Rol
    parola_degistirmeli: bool
    personel_id: int | None
    ad_soyad: str | None


class ParolaDegistirIstegi(BaseModel):
    mevcut_parola: str
    # Asgari uzunluk burada TEKRARLANMAZ; kural app/services/parola.py'de tek
    # yerde durur ve ihlali 400 olarak doner. Iki yerde tanimlansaydi biri
    # degistiginde digeri sessizce eski kurali uygulamaya devam ederdi.
    yeni_parola: str = Field(min_length=1)
