"""Calisan Paneli uc noktalari (SDD 3.2, 6.1; SDD Ek B; SRS FR-9.x).

Backlog B-05: gercek kimlik dogrulama ertelendi, panele "kisiye ozel
baglanti" ile girilir - burada bunun karsiligi, config.py'de zaten tanimli
`calisan_paneli_baglanti_anahtari` paylasimli anahtaridir (giris ekrani
YOK; anahtar sadece rastgele personel_id denemesini zorlastiran bir
baglanti parametresidir, kisi-bazli gercek yetkilendirme degildir).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import ayarlar
from app.db import oturum_al
from app.schemas.calisan import (
    CalisanTercihListesiOku,
    CalisanTercihOku,
    CalisanTercihOlustur,
    VardiyalarimOku,
)
from app.services.calisan_servisi import CalisanServisi, TercihDonemiBulunamadiError

router = APIRouter(prefix="/api/calisan", tags=["calisan"])

Oturum = Annotated[Session, Depends(oturum_al)]


def _anahtari_dogrula(anahtar: str) -> None:
    if anahtar != ayarlar.calisan_paneli_baglanti_anahtari:
        raise HTTPException(status_code=403, detail="Gecersiz baglanti")


@router.get("/vardiyalarim", response_model=VardiyalarimOku)
def vardiyalarim_getir(personel_id: int, anahtar: str, oturum: Oturum) -> VardiyalarimOku:
    _anahtari_dogrula(anahtar)
    sonuc = CalisanServisi(oturum).vardiyalarim(personel_id)
    if sonuc is None:
        raise HTTPException(status_code=404, detail="Personel bulunamadi")
    return sonuc


@router.get("/tercih", response_model=CalisanTercihListesiOku)
def tercihlerim_getir(personel_id: int, anahtar: str, oturum: Oturum) -> CalisanTercihListesiOku:
    _anahtari_dogrula(anahtar)
    sonuc = CalisanServisi(oturum).tercihlerim(personel_id)
    if sonuc is None:
        raise HTTPException(status_code=404, detail="Personel bulunamadi")
    return sonuc


@router.post("/tercih", response_model=CalisanTercihOku, status_code=201)
def tercih_bildir(
    personel_id: int, anahtar: str, veri: CalisanTercihOlustur, oturum: Oturum
) -> CalisanTercihOku:
    _anahtari_dogrula(anahtar)
    try:
        sonuc = CalisanServisi(oturum).tercih_bildir(personel_id, veri)
    except TercihDonemiBulunamadiError as hata:
        raise HTTPException(status_code=400, detail=str(hata)) from hata
    if sonuc is None:
        raise HTTPException(status_code=404, detail="Personel bulunamadi")
    return sonuc
