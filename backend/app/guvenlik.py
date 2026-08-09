"""Isteklerin kimlik ve yetki kapisi (SRS FR-10.3, FR-10.4, FR-10.7;
SDD 5.1b).

Uygulama duzeyinde tek bir dosyada durur, router basina degil: bir uc
noktanin kapisiz kalmasi, o uc noktanin kapisinin BASKA turlu olmasindan
cok daha olasidir. Burada tanimli bagimliliklar router imzalarina yazilir ve
imzada gorunur olurlar.

Kademeler:

  `oturum_baglami`  - gecerli bir oturum var mi? (kimlik dogrulama)
  `giris_yapan`     - ustune: parola degistirme borcu var mi? (FR-10.7)

Rol kapilari (FR-10.4) bu ikisinin uzerine kurulur.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.config import ayarlar
from app.db import oturum_al
from app.services.oturum_servisi import CEREZ_ADI, OturumBaglami, OturumServisi

VeriOturumu = Annotated[Session, Depends(oturum_al)]

# Parola degistirme borcu varken acik kalan tek uc nokta kumesi disindaki her
# sey bu mesajla kapanir (FR-10.7).
_PAROLA_BORCU_MESAJI = "Once parolanizi degistirmelisiniz"


def cerez_yaz(yanit: Response, belirtec: str) -> None:
    """Oturum cerezini yazar (SDD 5.1b).

    - HttpOnly: JavaScript belirteci okuyamaz, XSS ile calinamaz.
    - Secure:   duz http uzerinden gonderilmez (yerelde .env ile kapatilir).
    - SameSite=Lax: baska sitelerden gelen POST isteklerine cerez eklenmez,
      yani sitelerarasi istek sahteciligi (CSRF) yazma uc noktalarina
      ulasamaz. GET'lerde cerez gittigi icin normal gezinme bozulmaz.
    """
    yanit.set_cookie(
        key=CEREZ_ADI,
        value=belirtec,
        httponly=True,
        secure=ayarlar.oturum_cerezi_secure,
        samesite="lax",
        path="/",
        # Son kullanma cereze YAZILMAZ. Oturumun gecerliligi yalnizca
        # sunucudaki kayittan okunur; cereze bir sure yazmak, iki kaynagin
        # (tarayici ve veritabani) ayrisabildigi ikinci bir gercek uretirdi.
    )


def cerez_sil(yanit: Response) -> None:
    yanit.delete_cookie(
        key=CEREZ_ADI,
        httponly=True,
        secure=ayarlar.oturum_cerezi_secure,
        samesite="lax",
        path="/",
    )


def oturum_baglami(istek: Request, veri_oturumu: VeriOturumu) -> OturumBaglami:
    """Gecerli bir oturum zorunlu kilar; yoksa 401.

    Parola degistirme borcunu KONTROL ETMEZ - borclu kullanicinin da
    erisebilmesi gereken uc noktalar var (kim oldugunu sormak, parolasini
    degistirmek, cikmak).
    """
    belirtec = istek.cookies.get(CEREZ_ADI)
    if not belirtec:
        raise HTTPException(status_code=401, detail="Oturum acik degil")

    baglam = OturumServisi(veri_oturumu).dogrula(belirtec)
    if baglam is None:
        raise HTTPException(status_code=401, detail="Oturum gecersiz veya suresi dolmus")
    return baglam


Baglam = Annotated[OturumBaglami, Depends(oturum_baglami)]


def giris_yapan(baglam: Baglam) -> OturumBaglami:
    """Gecerli oturum + parola borcu yok (FR-10.7).

    Yonetimin atadigi parola degistirilene kadar diger uc noktalar KAPALI.
    Arayuzun kullaniciyi parola ekranina goturmesi bunun yerine gecmez:
    istek dogrudan gonderildiginde de reddedilir.
    """
    if baglam.kullanici.parola_degistirmeli:
        raise HTTPException(status_code=403, detail=_PAROLA_BORCU_MESAJI)
    return baglam
