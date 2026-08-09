"""Giris, cikis, kim oldugum ve parola degistirme uc noktalari
(SRS FR-10.1, FR-10.3, FR-10.7; SDD 5.1b).

Kayit uc noktasi YOKTUR ve olmayacaktir (FR-10.1): hesaplari yonetim rolu
acar, ilk yonetim hesabini arayuz disi bir betik acar (FR-10.10).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.db import oturum_al
from app.guvenlik import Baglam, cerez_sil, cerez_yaz
from app.models.kimlik import Kullanici
from app.repositories.tanim import PersonelDeposu
from app.schemas.kimlik import BenOku, GirisIstegi, ParolaDegistirIstegi
from app.services.kimlik_servisi import (
    GirisBasarisizError,
    HesapKilitliError,
    HesapPasifError,
    KimlikServisi,
    ParolaAyniError,
    ParolaHataliError,
)
from app.services.parola import ParolaKuraliError

router = APIRouter(prefix="/api", tags=["kimlik"])

Oturum = Annotated[Session, Depends(oturum_al)]

# Kullanici adi hatali da olsa parola hatali da olsa AYNI metin doner
# (SDD 5.1b). Iki ayri mesaj, giris ekranini bir kullanici adi sayacina
# cevirirdi.
_GENEL_RET = "Kullanici adi veya parola hatali"


def _ben(kullanici: Kullanici, oturum: Session) -> BenOku:
    ad_soyad = None
    if kullanici.personel_id is not None:
        personel = PersonelDeposu(oturum).getir(kullanici.personel_id)
        ad_soyad = personel.ad_soyad if personel is not None else None
    return BenOku(
        kullanici_adi=kullanici.kullanici_adi,
        rol=kullanici.rol,
        parola_degistirmeli=kullanici.parola_degistirmeli,
        personel_id=kullanici.personel_id,
        ad_soyad=ad_soyad,
    )


@router.post("/giris", response_model=BenOku)
def giris(veri: GirisIstegi, yanit: Response, oturum: Oturum) -> BenOku:
    try:
        sonuc = KimlikServisi(oturum).giris(veri.kullanici_adi, veri.parola)
    except GirisBasarisizError as hata:
        raise HTTPException(status_code=401, detail=_GENEL_RET) from hata
    except HesapKilitliError as hata:
        # Kilit mesaji yalnizca PAROLA DOGRUYKEN buraya ulasir; parolayi
        # bilmeyen biri bu metni hicbir kullanici adi icin goremez, yani
        # FR-10.8'in bildirim gereksinimi kullanici sayimina kapi acmaz.
        raise HTTPException(status_code=401, detail=str(hata)) from hata
    except HesapPasifError as hata:
        raise HTTPException(status_code=401, detail="Hesabiniz devre disi birakilmis") from hata

    cerez_yaz(yanit, sonuc.belirtec)
    return _ben(sonuc.kullanici, oturum)


@router.post("/cikis", status_code=204)
def cikis(baglam: Baglam, yanit: Response, oturum: Oturum) -> None:
    """Oturum kaydini SILER. Yalniz cerezi silmek yetmezdi: elinde belirtecin
    kopyasi olan biri onu kullanmaya devam edebilirdi."""
    KimlikServisi(oturum).cikis(baglam.oturum_id)
    cerez_sil(yanit)


@router.get("/ben", response_model=BenOku)
def ben(baglam: Baglam, oturum: Oturum) -> BenOku:
    """Arayuzun hangi yuzeyi acacagini belirlemesi icin (SRS 5.10).

    `giris_yapan` DEGIL `oturum_baglami` kullanir: parola borcu olan
    kullanicinin da kim oldugunu ogrenebilmesi gerekir, yoksa arayuz onu
    parola ekranina yonlendiremez.
    """
    return _ben(baglam.kullanici, oturum)


@router.post("/parola-degistir", response_model=BenOku)
def parola_degistir(
    veri: ParolaDegistirIstegi, baglam: Baglam, yanit: Response, oturum: Oturum
) -> BenOku:
    """Kullanicinin kendi parolasini degistirmesi (FR-10.7 ve kendi istegiyle).

    Parola borclu kullanici da cagirabilmelidir - borcunu odemesinin tek
    yolu budur.
    """
    servis = KimlikServisi(oturum)
    try:
        belirtec = servis.parola_degistir(baglam.kullanici, veri.mevcut_parola, veri.yeni_parola)
    except ParolaHataliError as hata:
        raise HTTPException(status_code=400, detail="Mevcut parola hatali") from hata
    except ParolaAyniError as hata:
        raise HTTPException(
            status_code=400, detail="Yeni parola mevcut parolayla ayni olamaz"
        ) from hata
    except ParolaKuraliError as hata:
        raise HTTPException(status_code=400, detail=str(hata)) from hata

    # Parola degisikligi butun oturumlari kapatti; cagiran istek de kendi
    # oturumunu kaybetti ve yerine yenisi acildi. Cerez tazelenmezse
    # kullanici kendi parolasini degistirdikten sonra disari duserdi.
    cerez_yaz(yanit, belirtec)
    return _ben(baglam.kullanici, oturum)
