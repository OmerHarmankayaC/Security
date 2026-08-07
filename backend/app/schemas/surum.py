"""/api/donem, /api/surum, /api/surum/{id}/atama+kapsama-acigi semalari (SDD Ek B)."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.sonuc import AtamaKaynagi, CizelgeSurumuDurumu


class DonemOlustur(BaseModel):
    baslangic_tarihi: date
    bitis_tarihi: date
    tercih_son_tarihi: date


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
