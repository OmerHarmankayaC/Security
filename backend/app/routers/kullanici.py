"""Hesap yonetimi uc noktalari (SRS FR-10.5; SDD 5.1b).

Kapi ROUTER duzeyinde ve YALNIZ yonetim rolune acik: yonetici rolu buradan
gecemez (SRS 5.10 - "Kullanici hesaplarini yonetemez"). Yonetici arayuzunun
bu ekrani hic gostermemesi yetkilendirme sayilmaz; istek dogrudan
gonderildiginde de 403 doner.

DELETE YOKTUR (FR-10.5): hesap silinmez, `aktif` alani ile devre disi
birakilir.
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import oturum_al
from app.guvenlik import GirisYapan, yonetim_yetkisi
from app.models.kimlik import Kullanici
from app.repositories.tanim import PersonelDeposu
from app.schemas.kullanici import (
    KullaniciGuncelle,
    KullaniciOku,
    KullaniciOlustur,
    ParolaSifirla,
)
from app.services.kullanici_servisi import (
    KendiHesabiError,
    KullaniciAdiGecersizError,
    KullaniciAdiKullanimdaError,
    KullaniciBulunamadiError,
    KullaniciServisi,
    PersonelBaglantisiGerekliError,
    PersonelBulunamadiError,
    PersonelZatenBagliError,
)
from app.services.parola import ParolaKuraliError

router = APIRouter(
    prefix="/api/kullanici", tags=["kullanici"], dependencies=[Depends(yonetim_yetkisi)]
)

Oturum = Annotated[Session, Depends(oturum_al)]

# Servis, kullaniciya gosterilebilir metni istisnanin icinde tasir; hepsi
# 400'e cevrilir. Ayri ayri yazilsalardi yeni bir kural eklendiginde
# router'da karsiliginin unutulmasi 500 uretirdi.
_ISTEK_HATALARI = (
    KullaniciAdiGecersizError,
    KullaniciAdiKullanimdaError,
    PersonelBaglantisiGerekliError,
    PersonelBulunamadiError,
    PersonelZatenBagliError,
    ParolaKuraliError,
)


def _oku(kullanici: Kullanici, oturum: Session) -> KullaniciOku:
    ad_soyad = None
    if kullanici.personel_id is not None:
        personel = PersonelDeposu(oturum).getir(kullanici.personel_id)
        ad_soyad = personel.ad_soyad if personel is not None else None
    return KullaniciOku(
        kullanici_id=kullanici.kullanici_id,
        kullanici_adi=kullanici.kullanici_adi,
        rol=kullanici.rol,
        personel_id=kullanici.personel_id,
        ad_soyad=ad_soyad,
        aktif=kullanici.aktif,
        parola_degistirmeli=kullanici.parola_degistirmeli,
        kilitli_mi=(
            kullanici.kilit_bitis is not None and datetime.now(UTC) < kullanici.kilit_bitis
        ),
    )


@router.get("", response_model=list[KullaniciOku])
def listele(oturum: Oturum) -> list[KullaniciOku]:
    return [_oku(k, oturum) for k in KullaniciServisi(oturum).listele()]


@router.post("", response_model=KullaniciOku, status_code=201)
def olustur(veri: KullaniciOlustur, baglam: GirisYapan, oturum: Oturum) -> KullaniciOku:
    try:
        kullanici = KullaniciServisi(oturum).olustur(
            veri.kullanici_adi,
            veri.parola,
            veri.rol,
            veri.personel_id,
            isteyen=baglam.kullanici,
        )
    except _ISTEK_HATALARI as hata:
        raise HTTPException(status_code=400, detail=str(hata)) from hata
    return _oku(kullanici, oturum)


@router.put("/{kullanici_id}", response_model=KullaniciOku)
def guncelle(
    kullanici_id: int, veri: KullaniciGuncelle, baglam: GirisYapan, oturum: Oturum
) -> KullaniciOku:
    try:
        kullanici = KullaniciServisi(oturum).guncelle(
            kullanici_id,
            isteyen=baglam.kullanici,
            rol=veri.rol,
            aktif=veri.aktif,
            personel_id=veri.personel_id,
            personel_id_verildi="personel_id" in veri.model_fields_set,
        )
    except KullaniciBulunamadiError as hata:
        raise HTTPException(status_code=404, detail="Kullanici bulunamadi") from hata
    except KendiHesabiError as hata:
        raise HTTPException(
            status_code=400,
            detail="Kendi rolunuzu degistiremez ve kendi hesabinizi devre disi birakamazsiniz",
        ) from hata
    except _ISTEK_HATALARI as hata:
        raise HTTPException(status_code=400, detail=str(hata)) from hata
    return _oku(kullanici, oturum)


@router.post("/{kullanici_id}/parola-sifirla", response_model=KullaniciOku)
def parola_sifirla(
    kullanici_id: int, veri: ParolaSifirla, baglam: GirisYapan, oturum: Oturum
) -> KullaniciOku:
    """Parolayi degistirir, ilk giriste degistirme borcu yukler (FR-10.7) ve
    o kullanicinin ACIK OTURUMLARINI kapatir."""
    try:
        kullanici = KullaniciServisi(oturum).parola_sifirla(
            kullanici_id, veri.yeni_parola, isteyen=baglam.kullanici
        )
    except KullaniciBulunamadiError as hata:
        raise HTTPException(status_code=404, detail="Kullanici bulunamadi") from hata
    except _ISTEK_HATALARI as hata:
        raise HTTPException(status_code=400, detail=str(hata)) from hata
    return _oku(kullanici, oturum)
