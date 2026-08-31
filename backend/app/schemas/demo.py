"""Gosterim kimlik bilgisinin sozlesmesi (Demo Senaryosu 7)."""

from pydantic import BaseModel


class DemoHesabiOku(BaseModel):
    kullanici_adi: str
    rol: str
    aciklama: str
    #: HER HESABIN KENDI PAROLASI. Once dordu icin tek bir alan tutuluyordu;
    #: ayni dize demekti ve "parolayi biliyorum" ile "hepsini biliyorum" ayni
    #: seye cikiyordu. Deger saklanmaz, tohumdan turetilir.
    parola: str


class DemoKimlikOku(BaseModel):
    hesaplar: list[DemoHesabiOku]


__all__ = ["DemoHesabiOku", "DemoKimlikOku"]
