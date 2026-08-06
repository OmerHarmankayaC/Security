"""Cizelgeleme uc noktalari (SDD 3.2: cizelge_router; SDD Ek B).

/api/on-kontrol (Sprint 2 Gun 7) ve /api/cozum (Sprint 2 Gun 8). /api/donem,
/api/surum, /api/atama sonraki gunlerde eklenecek.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import oturum_al
from app.models.sonuc import CozumIsiDurumu
from app.repositories.sonuc import CozumIsiDeposu
from app.schemas.cozum import CozumBaslatIstek, CozumOku
from app.schemas.on_kontrol import BulguOku, OnKontrolIstek, OnKontrolYaniti
from app.services.cozum_servisi import CozumServisi
from app.services.on_kontrol_servisi import OnKontrolServisi

router = APIRouter(prefix="/api", tags=["cizelge"])

Oturum = Annotated[Session, Depends(oturum_al)]

_TAMAMLANMIS_DURUMLAR = (
    CozumIsiDurumu.TAMAMLANDI,
    CozumIsiDurumu.UYARILI,
    CozumIsiDurumu.BASARISIZ,
    CozumIsiDurumu.IPTAL,
)


@router.post("/on-kontrol", response_model=OnKontrolYaniti)
def on_kontrol_calistir(istek: OnKontrolIstek, oturum: Oturum) -> OnKontrolYaniti:
    servis = OnKontrolServisi(oturum)
    bulgular = servis.calistir(istek.donem_id)
    if bulgular is None:
        raise HTTPException(status_code=404, detail="Donem bulunamadi")
    return OnKontrolYaniti(bulgular=[BulguOku.model_validate(b) for b in bulgular])


@router.post("/cozum", response_model=CozumOku, status_code=201)
def cozum_baslat(istek: CozumBaslatIstek, oturum: Oturum) -> CozumOku:
    servis = CozumServisi(oturum)
    is_kaydi = servis.baslat(istek.donem_id, zaman_limiti_saniye=istek.zaman_limiti_saniye)
    if is_kaydi is None:
        raise HTTPException(status_code=404, detail="Donem bulunamadi")
    return CozumOku.model_validate(is_kaydi)


@router.get("/cozum/{is_id}", response_model=CozumOku)
def cozum_durumu(is_id: int, oturum: Oturum) -> CozumOku:
    is_kaydi = CozumIsiDeposu(oturum).getir(is_id)
    if is_kaydi is None:
        raise HTTPException(status_code=404, detail="Cozum isi bulunamadi")
    return CozumOku.model_validate(is_kaydi)


@router.post("/cozum/{is_id}/iptal", response_model=CozumOku)
def cozum_iptal(is_id: int, oturum: Oturum) -> CozumOku:
    """En iyi caba: durumu iptal olarak isaretler. Ayri surecte fiilen calisan
    CP-SAT aramasini zorla sonlandirmaz (bu, surec izlemeyi gerektirir ve
    Sprint 3'teki systemd entegrasyonuna birakildi); is zaten sonuclanmissa
    (tamamlandi/basarisiz/vb.) hicbir sey degistirmez."""
    depo = CozumIsiDeposu(oturum)
    is_kaydi = depo.getir(is_id)
    if is_kaydi is None:
        raise HTTPException(status_code=404, detail="Cozum isi bulunamadi")
    if is_kaydi.durum not in _TAMAMLANMIS_DURUMLAR:
        is_kaydi.durum = CozumIsiDurumu.IPTAL
    return CozumOku.model_validate(is_kaydi)
