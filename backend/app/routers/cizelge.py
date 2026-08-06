"""Cizelgeleme uc noktalari (SDD 3.2: cizelge_router; SDD Ek B).

/api/on-kontrol (Sprint 2 Gun 7), /api/cozum (Sprint 2 Gun 8), /api/atama
(Sprint 2 Gun 9). /api/donem, /api/surum sonraki gunlerde eklenecek.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import oturum_al
from app.models.sonuc import CozumIsiDurumu
from app.repositories.sonuc import CozumIsiDeposu
from app.schemas.cozum import CozumBaslatIstek, CozumOku
from app.schemas.dogrulama import AtamaDegisikligiIstek, DogrulamaSonucuOku, IhlalOku
from app.schemas.on_kontrol import BulguOku, OnKontrolIstek, OnKontrolYaniti
from app.services.cozum_servisi import CozumServisi
from app.services.dogrulama_servisi import (
    AtamaDegisikligi,
    DogrulamaServisi,
    DogrulamaSonucu,
    SurumTaslakDegilError,
)
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


def _degisiklige_cevir(istek: AtamaDegisikligiIstek) -> AtamaDegisikligi:
    return AtamaDegisikligi(
        surum_id=istek.surum_id,
        personel_id=istek.personel_id,
        tarih=istek.tarih,
        vardiya_tipi_id=istek.vardiya_tipi_id,
        nokta_id=istek.nokta_id,
    )


def _sonucu_cevir(sonuc: DogrulamaSonucu) -> DogrulamaSonucuOku:
    return DogrulamaSonucuOku(
        kabul_edilebilir=sonuc.kabul_edilebilir,
        zorunlu_ihlaller=[
            IhlalOku(
                kural_kimlik=i.kural_kimlik,
                aciklama=i.aciklama,
                personel_id=i.personel_id,
                tarih=i.tarih,
                ceza=i.ceza,
            )
            for i in sonuc.zorunlu_ihlaller
        ],
        ceza_degisimi=sonuc.ceza_degisimi,
    )


@router.post("/atama/dogrula", response_model=DogrulamaSonucuOku)
def atama_dogrula(istek: AtamaDegisikligiIstek, oturum: Oturum) -> DogrulamaSonucuOku:
    servis = DogrulamaServisi(oturum)
    try:
        sonuc = servis.dogrula(_degisiklige_cevir(istek))
    except SurumTaslakDegilError as hata:
        raise HTTPException(status_code=409, detail=str(hata)) from hata
    if sonuc is None:
        raise HTTPException(status_code=404, detail="Cizelge surumu bulunamadi")
    return _sonucu_cevir(sonuc)


@router.put("/atama", response_model=DogrulamaSonucuOku)
def atama_guncelle(istek: AtamaDegisikligiIstek, oturum: Oturum) -> DogrulamaSonucuOku:
    servis = DogrulamaServisi(oturum)
    try:
        sonuc = servis.uygula(_degisiklige_cevir(istek))
    except SurumTaslakDegilError as hata:
        raise HTTPException(status_code=409, detail=str(hata)) from hata
    if sonuc is None:
        raise HTTPException(status_code=404, detail="Cizelge surumu bulunamadi")
    if not sonuc.kabul_edilebilir:
        raise HTTPException(status_code=409, detail=_sonucu_cevir(sonuc).model_dump(mode="json"))
    return _sonucu_cevir(sonuc)
