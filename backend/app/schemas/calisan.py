"""Calisan Paneli uc noktalarinin semalari (SDD 6.1, Ek B; SRS FR-9.x).

Sadece calisanin kendi verisini tasir - Analiz servisinin aksine, ekip
ortalamalari haric baska personelin ad/sicil/gece-hafta sonu/saat kirilimi
bu semalar uzerinden client'a hic dogru gitmez (SDD 6.1 kabul kriteri:
"baska bir personelin verisine erisemiyor").
"""

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, model_validator

from app.kurallar.zaman_araligi import tam_saat_mi
from app.models.girdi import TercihDurumu, TercihTipi

# FR-9.4'un uc degisim turunden ikisi; ucuncusu ("kaldirildi") bir vardiya
# uzerinde tasinamaz, cunku o gun artik vardiya YOKTUR - bkz. KaldirilanGunOku.
DegisimTipi = Literal["eklendi", "degisti"]
KarsilanmaDurumu = Literal["karsilandi", "karsilanmadi", "henuz_belirsiz"]


class VardiyamOku(BaseModel):
    """Calisanin bir gunluk calisma BLOGU.

    Blok adi diye bir sey yok (SRS TD-13); calisanin gormesi gereken bilgi
    saatin kendisidir. `gece_saati` HESAPLANIR (TD-2), isaretlenmez: gece
    bayragi vardiya tipi uzerinde duruyordu ve o tablo kalkti.
    """

    tarih: date
    baslangic_zamani: datetime
    bitis_zamani: datetime
    sure_saat: int
    gece_saati: int
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
    onceki_baslangic_zamani: datetime
    onceki_bitis_zamani: datetime
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

    KIYASIN REFERANSI ADIL PAYDIR, ekip ortalamasi degil. Erisilebilirligi
    kisitli bir havuz tek ortalamaya vuruldugunda kalici olarak sapmali
    gorunur (bkz. schemas/analiz.py, KisiSayisiOku.pay). Ekip ortalamasi
    ikincil baglam olarak tasinmaya devam eder.

    `ufuk` YANITIN ICINDE tasinir: iki ufkun sayilari farklidir ve hangisinin
    okundugu belirsiz kalirsa sayi yanlis okunur (SDD 6.3.4).
    """

    ufuk: Literal["donem", "adalet"] = "donem"
    # Birim SAAT (SRS S2, S3): blok sureleri cozumun ciktisi oldugundan
    # sayima dayali bir olcu tanimsizdir.
    gece_saati: float
    ekip_ortalama_gece: float
    adil_pay_gece: float | None
    gece_havuzunda: bool
    hafta_sonu_saati: float
    ekip_ortalama_hafta_sonu: float
    adil_pay_hafta_sonu: float | None
    hafta_sonu_havuzunda: bool
    toplam_saat: float
    ekip_ortalama_saat: float
    hedef_saat: float


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
    # `ozet` BURADA DEGIL: /api/calisan/ozetim uc noktasinda. Ozet bir tam
    # AnalizServisi.hesapla() odemesi ve panelin her acilisi onu odemek
    # zorunda degil - calisan Vardiyalarim sekmesine bakarken hesap hic
    # calismaz.


class AcikDonemOku(BaseModel):
    donem_id: int
    baslangic_tarihi: date
    bitis_tarihi: date
    tercih_son_tarihi: date


class CalisanTercihOku(BaseModel):
    tercih_id: int
    tarih: date
    tip: TercihTipi
    # Zaman araligi tercihinde istenen aralik; calismama tercihinde bos.
    tercih_baslangic: time | None
    tercih_bitis: time | None
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
    """Tercih bildirimi (SRS FR-3.2).

    Tercih artik bir vardiya TIPI degil bir ZAMAN ARALIGI gosterir: form,
    calisanin "su saatler arasinda calismak isterim" demesine izin verir.
    Calismama tercihinde aralik bos birakilir.
    """

    tarih: date
    tip: TercihTipi
    tercih_baslangic: time | None = None
    tercih_bitis: time | None = None
    calisan_notu: str | None = None

    @model_validator(mode="after")
    def _araligi_dogrula(self) -> "CalisanTercihOlustur":
        if self.tip == TercihTipi.CALISMAMA:
            return self
        if self.tercih_baslangic is None or self.tercih_bitis is None:
            raise ValueError("Zaman aralığı tercihinde başlangıç ve bitiş saati zorunludur.")
        for saat in (self.tercih_baslangic, self.tercih_bitis):
            if not tam_saat_mi(saat):
                raise ValueError("Tercih saatleri saat başında olmalı (örnek: 08.00).")
        return self
