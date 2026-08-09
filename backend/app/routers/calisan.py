"""Calisan Paneli uc noktalari (SDD 3.2, 6.1; SDD Ek B; SRS FR-9.x).

Panele GIRISLE girilir; kisiye ozel baglanti kapisi kaldirilmistir
(Backlog B-05 kapsama alindi, 09.08.2026).

FR-9.1 -- BU DOSYANIN EN ONEMLI OZELLIGI: hicbir uc nokta `personel_id`
ALMAZ. Hangi personelin verisinin donecegini `oturumdaki_personel`
bagimliligi yanitlar ve o da yalnizca oturuma bakar. Kimlik bir parametre
olsaydi, her uc noktada "bu parametreyi oturumla karsilastirmayi unutma"
diye bir yukumluluk dogardi; parametreyi hic almayarak o hata bicimi
ortadan kaldirilmistir. Kisiye ozel baglanti doneminde tam olarak bu
acikti: URL'deki kimlik degistirilebiliyordu.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import oturum_al
from app.guvenlik import calisan_yetkisi, oturumdaki_personel
from app.repositories.tanim import VardiyaTipiDeposu
from app.schemas.calisan import (
    CalisanTercihListesiOku,
    CalisanTercihOku,
    CalisanTercihOlustur,
    CalisanVardiyaTipiOku,
    VardiyalarimOku,
)
from app.services.calisan_servisi import CalisanServisi, TercihDonemiBulunamadiError

router = APIRouter(prefix="/api/calisan", tags=["calisan"], dependencies=[Depends(calisan_yetkisi)])

Oturum = Annotated[Session, Depends(oturum_al)]
Personel = Annotated[int, Depends(oturumdaki_personel)]


@router.get("/vardiyalarim", response_model=VardiyalarimOku)
def vardiyalarim_getir(personel_id: Personel, oturum: Oturum) -> VardiyalarimOku:
    sonuc = CalisanServisi(oturum).vardiyalarim(personel_id)
    if sonuc is None:
        raise HTTPException(status_code=404, detail="Personel bulunamadi")
    return sonuc


@router.get("/tercih", response_model=CalisanTercihListesiOku)
def tercihlerim_getir(personel_id: Personel, oturum: Oturum) -> CalisanTercihListesiOku:
    sonuc = CalisanServisi(oturum).tercihlerim(personel_id)
    if sonuc is None:
        raise HTTPException(status_code=404, detail="Personel bulunamadi")
    return sonuc


@router.post("/tercih", response_model=CalisanTercihOku, status_code=201)
def tercih_bildir(
    personel_id: Personel, veri: CalisanTercihOlustur, oturum: Oturum
) -> CalisanTercihOku:
    try:
        sonuc = CalisanServisi(oturum).tercih_bildir(personel_id, veri)
    except TercihDonemiBulunamadiError as hata:
        raise HTTPException(status_code=400, detail=str(hata)) from hata
    if sonuc is None:
        raise HTTPException(status_code=404, detail="Personel bulunamadi")
    return sonuc


@router.get("/vardiya-tipi", response_model=list[CalisanVardiyaTipiOku])
def vardiya_tipleri(oturum: Oturum) -> list[CalisanVardiyaTipiOku]:
    """Tercih formundaki vardiya tipi listesi.

    Calisan panelinin `/api/vardiya-tipi`yi (tanim yonlendiricisi)
    cagirmasi, tanim uc noktalarini calisan rolune acmak demek olurdu; SRS
    5.10 bunu acikca disarida birakiyor. Ihtiyac duyulan sey bir tanim
    yonetimi degil, tercihini bildirebilmek icin vardiyanin ADI - bu yuzden
    calisan yuzeyinin altinda, yalniz aktif tipleri ve yalniz gosterim
    alanlarini tasiyan ayri bir okuma ucu var.
    """
    return [
        CalisanVardiyaTipiOku(
            vardiya_tipi_id=v.vardiya_tipi_id,
            ad=v.ad,
            baslangic_saati=v.baslangic_saati,
            bitis_saati=v.bitis_saati,
            gece_mi=v.gece_mi,
        )
        for v in VardiyaTipiDeposu(oturum).tumunu_getir()
        if v.aktif
    ]
