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

# FR-9.4'un uc degisim turunden ikisi; ucuncusu ("kaldirildi") bir vardiya
# uzerinde tasinamaz, cunku o gun artik vardiya YOKTUR - bkz. KaldirilanGunOku.
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


class KaldirilanGunOku(BaseModel):
    """FR-9.4'un ucuncu degisim turu: karsilastirma tabaninda (en son arsiv)
    o gun bir atama VARDI, yayinlanmis surumde YOK.

    Ayri bir tip olmasinin nedeni, bunun bir vardiya degil bir vardiyanin
    YOKLUGU olmasidir. `vardiyalar` listesine karistirilsaydi, o listeden
    beslenen her sey (vardiya sayisi, "siradaki vardiyan", donem izgarasinin
    dolu hucreleri) calisana artik sahip olmadigi bir vardiyayi varmis gibi
    gosterirdi. Alanlar bu yuzden `onceki_` on ekiyle adlandirilmistir:
    tasidiklari, calisanin ELINDEN ALINAN vardiyanin bilgisidir.
    """

    tarih: date
    onceki_vardiya_tipi_ad: str
    onceki_baslangic_saati: time
    onceki_bitis_saati: time
    onceki_gece_mi: bool
    onceki_nokta_ad: str


class DonemOzetiOku(BaseModel):
    """FR-9.5: ekip ortalamasi, AnalizServisi'nin hesabinin ortalamasidir -
    tek tek diger personelin verisi disari cikmaz.

    Gece ve hafta sonu ortalamalari UYGUN HAVUZ (SRS S2/S3'teki P_gece, P_hs)
    uzerinden hesaplanir (SDD 5.7 surum 1.7). Bu havuzun DISINDAKI bir
    calisan icin karsilastirma anlamsizdir: yetkinligi geregi o vardiyalari
    hic alamaz, dolayisiyla kendi sayisi kalici olarak 0 ve "ortalamanin
    altinda" gorunur. Bu yuzden havuz uyeligi ayrica tasinir ve arayuz,
    havuz disindaki calisana o karsilastirmayi hic gostermez.
    """

    gece_sayisi: int
    ekip_ortalama_gece: float
    gece_havuzunda: bool
    hafta_sonu_sayisi: int
    ekip_ortalama_hafta_sonu: float
    hafta_sonu_havuzunda: bool
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
    # FR-9.4 ucuncu tur; `vardiyalar`dan ayri tutulur (bkz. KaldirilanGunOku).
    kaldirilan_gunler: list[KaldirilanGunOku]
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
    # TD-12: "Turetme yalnizca onaylanmis tercihler icin yapilir." Bekleyen ya
    # da reddedilmis bir tercihte karsilanma diye bir bilgi YOKTUR (reddedilen
    # tercih zaten modele girmez, FR-3.5) - o durumda None doner ve arayuz
    # karsilanma satirini hic gostermez. "karsilanmadi" yazmak yaniltici
    # olurdu: reddedilen bir tercihin karsilanmamasi bir sonuc degil, tanim.
    karsilanma: KarsilanmaDurumu | None


class CalisanTercihListesiOku(BaseModel):
    acik_donem: AcikDonemOku | None
    tercihler: list[CalisanTercihOku]


class CalisanTercihOlustur(BaseModel):
    tarih: date
    tip: TercihTipi
    vardiya_tipi_id: int | None = None
    calisan_notu: str | None = None
