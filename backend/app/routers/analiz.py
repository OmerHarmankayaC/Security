"""Analiz uc noktasi (SDD 3.2: analiz_router; SDD Ek B; SRS FR-8.x)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import oturum_al
from app.guvenlik import yonetici_yetkisi
from app.schemas.analiz import AnalizOku
from app.services.analiz_servisi import AnalizServisi

# Analiz raporlari butun personelin gece/hafta sonu/saat kirilimini tasir;
# yonetici yetkisi ister (SRS 5.10).
router = APIRouter(prefix="/api", tags=["analiz"], dependencies=[Depends(yonetici_yetkisi)])

Oturum = Annotated[Session, Depends(oturum_al)]


@router.get("/analiz/{surum_id}", response_model=AnalizOku)
def analiz_getir(surum_id: int, oturum: Oturum) -> AnalizOku:
    sonuc = AnalizServisi(oturum).hesapla(surum_id)
    if sonuc is None:
        raise HTTPException(status_code=404, detail="Cizelge surumu bulunamadi")
    return sonuc
