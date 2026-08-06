"""Cizelgeleme uc noktalari (SDD 3.2: cizelge_router; SDD Ek B).

Su an yalnizca /api/on-kontrol'u icerir (Sprint 2 Gun 7); /api/donem,
/api/surum, /api/cozum, /api/atama sonraki gunlerde eklenecek.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import oturum_al
from app.schemas.on_kontrol import BulguOku, OnKontrolIstek, OnKontrolYaniti
from app.services.on_kontrol_servisi import OnKontrolServisi

router = APIRouter(prefix="/api", tags=["cizelge"])

Oturum = Annotated[Session, Depends(oturum_al)]


@router.post("/on-kontrol", response_model=OnKontrolYaniti)
def on_kontrol_calistir(istek: OnKontrolIstek, oturum: Oturum) -> OnKontrolYaniti:
    servis = OnKontrolServisi(oturum)
    bulgular = servis.calistir(istek.donem_id)
    if bulgular is None:
        raise HTTPException(status_code=404, detail="Donem bulunamadi")
    return OnKontrolYaniti(bulgular=[BulguOku.model_validate(b) for b in bulgular])
