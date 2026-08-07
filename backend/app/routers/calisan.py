"""Calisan Paneli uc noktalari (SDD 3.2, 6.1; SDD Ek B; SRS FR-9.x).

Backlog B-05: gercek kimlik dogrulama ertelendi, panele "kisiye ozel
baglanti" ile girilir. Bunun karsiligi, her istekte beklenen `anahtar`
sorgu parametresidir; anahtar personel_id'den sunucu sirriyla turetilir
(bkz. services/calisan_baglantisi.py) - yani her personelin baglantisi
kendine ozeldir ve URL'deki personel_id'yi degistirmek baskasinin
cizelgesini acmaz (FR-9.1). Giris ekrani yoktur.

Anahtar dogrulamasi personelin var olup olmadigina BAKILMADAN once yapilir:
boylece 403/404 farkindan gecerli personel kimlikleri sayilamaz.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import oturum_al
from app.schemas.calisan import (
    CalisanTercihListesiOku,
    CalisanTercihOku,
    CalisanTercihOlustur,
    VardiyalarimOku,
)
from app.services.calisan_baglantisi import anahtar_gecerli_mi
from app.services.calisan_servisi import CalisanServisi, TercihDonemiBulunamadiError

router = APIRouter(prefix="/api/calisan", tags=["calisan"])

Oturum = Annotated[Session, Depends(oturum_al)]


def _anahtari_dogrula(personel_id: int, anahtar: str) -> None:
    if not anahtar_gecerli_mi(personel_id, anahtar):
        raise HTTPException(status_code=403, detail="Gecersiz baglanti")


@router.get("/vardiyalarim", response_model=VardiyalarimOku)
def vardiyalarim_getir(personel_id: int, anahtar: str, oturum: Oturum) -> VardiyalarimOku:
    _anahtari_dogrula(personel_id, anahtar)
    sonuc = CalisanServisi(oturum).vardiyalarim(personel_id)
    if sonuc is None:
        raise HTTPException(status_code=404, detail="Personel bulunamadi")
    return sonuc


@router.get("/tercih", response_model=CalisanTercihListesiOku)
def tercihlerim_getir(personel_id: int, anahtar: str, oturum: Oturum) -> CalisanTercihListesiOku:
    _anahtari_dogrula(personel_id, anahtar)
    sonuc = CalisanServisi(oturum).tercihlerim(personel_id)
    if sonuc is None:
        raise HTTPException(status_code=404, detail="Personel bulunamadi")
    return sonuc


@router.post("/tercih", response_model=CalisanTercihOku, status_code=201)
def tercih_bildir(
    personel_id: int, anahtar: str, veri: CalisanTercihOlustur, oturum: Oturum
) -> CalisanTercihOku:
    _anahtari_dogrula(personel_id, anahtar)
    try:
        sonuc = CalisanServisi(oturum).tercih_bildir(personel_id, veri)
    except TercihDonemiBulunamadiError as hata:
        raise HTTPException(status_code=400, detail=str(hata)) from hata
    if sonuc is None:
        raise HTTPException(status_code=404, detail="Personel bulunamadi")
    return sonuc
