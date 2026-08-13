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
from app.schemas.calisan import (
    CalisanTercihListesiOku,
    CalisanTercihOku,
    CalisanTercihOlustur,
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


