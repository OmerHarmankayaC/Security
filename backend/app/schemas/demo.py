"""Gosterim kimlik bilgisinin sozlesmesi (Demo Senaryosu 7)."""

from pydantic import BaseModel


class DemoHesabiOku(BaseModel):
    kullanici_adi: str
    rol: str
    aciklama: str


class DemoKimlikOku(BaseModel):
    #: Butun demo hesaplari AYNI parolayi tasir. Ayri parolalar gosterim
    #: ortaminda hicbir sey korumaz - hepsi zaten ayni ekranda yazili - ama
    #: ekrani uzatir ve kopyalamayi zorlastirirdi.
    parola: str
    hesaplar: list[DemoHesabiOku]


__all__ = ["DemoHesabiOku", "DemoKimlikOku"]
