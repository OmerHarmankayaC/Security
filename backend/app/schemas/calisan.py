"""Calisan Paneli uc noktalarinin semalari (SDD 6.1, Ek B; SRS FR-9.x).

Sadece calisanin kendi verisini tasir - Analiz servisinin aksine, ekip
ortalamalari haric baska personelin ad/sicil/gece-hafta sonu/saat kirilimi
bu semalar uzerinden client'a hic dogru gitmez (SDD 6.1 kabul kriteri:
"baska bir personelin verisine erisemiyor").
"""

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel

from app.models.girdi import TercihDurumu, TercihTipi

DegisimTipi = Literal["eklendi", "degisti"]
KarsilanmaDurumu = Literal["karsilandi", "karsilanmadi", "henuz_belirsiz"]


class VardiyamOku(BaseModel):
    tarih: date
    vardiya_tipi_id: int
    vardiya_tipi_ad: str
    baslangic_saati: time
    bitis_saati: time
    gece_mi: bool
    nokta_id: int
    nokta_ad: str
    # FR-9.4: karsilastirma tabani (en son arsivlenen surum) yoksa hicbir
    # gun isaretlenmez - bu alan o zaman hep None'dir.
    degisim_tipi: DegisimTipi | None


class DonemOzetiOku(BaseModel):
    """FR-9.5: ekip ortalamasi, AnalizServisi'nin butun personel uzerindeki
    hesabinin ortalamasidir - tek tek diger personelin verisi disari cikmaz."""

    gece_sayisi: int
    ekip_ortalama_gece: float
    hafta_sonu_sayisi: int
    ekip_ortalama_hafta_sonu: float
    toplam_saat: float
    ekip_ortalama_saat: float


class VardiyalarimOku(BaseModel):
    personel_id: int
    ad_soyad: str
    sicil_no: str
    yetkinlikler: list[str]
    donem_id: int | None
    donem_baslangic_tarihi: date | None
    donem_bitis_tarihi: date | None
    surum_id: int | None
    yayinlanmis_surum_var: bool
    yayin_zamani: datetime | None
    vardiyalar: list[VardiyamOku]
    siradaki: VardiyamOku | None
    ozet: DonemOzetiOku | None


class AcikDonemOku(BaseModel):
    donem_id: int
    baslangic_tarihi: date
    bitis_tarihi: date
    tercih_son_tarihi: date


class CalisanTercihOku(BaseModel):
    tercih_id: int
    tarih: date
    tip: TercihTipi
    vardiya_tipi_id: int | None
    vardiya_tipi_ad: str | None
    calisan_notu: str | None
    durum: TercihDurumu
    ret_gerekcesi: str | None
    karsilanma: KarsilanmaDurumu


class CalisanTercihListesiOku(BaseModel):
    acik_donem: AcikDonemOku | None
    tercihler: list[CalisanTercihOku]


class CalisanTercihOlustur(BaseModel):
    tarih: date
    tip: TercihTipi
    vardiya_tipi_id: int | None = None
    calisan_notu: str | None = None
