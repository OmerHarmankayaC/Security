"""Tanim yonetimi uc noktalari (SDD 3.2: tanim_router; SDD Ek B; SRS 5.1).

Yonlendirici ince tutulur: istegi semayla dogrular, tek bir servis metodunu
cagirir, sonucu JSON'a cevirir. Is mantigi burada yer almaz.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import oturum_al
from app.repositories.tanim import SilmeSonucu, TanimDeposu
from app.schemas.girdi import (
    MusaitlikOku,
    MusaitlikOlustur,
    TercihGuncelle,
    TercihOku,
    TercihOlustur,
)
from app.schemas.kural import KuralGuncelle, KuralOku
from app.schemas.tanim import (
    BinaGuncelle,
    BinaOku,
    BinaOlustur,
    GorevNoktasiGuncelle,
    GorevNoktasiOku,
    GorevNoktasiOlustur,
    KullanimKalemi,
    KullanimOku,
    PersonelGuncelle,
    PersonelOku,
    PersonelOlustur,
    TalepHucresi,
    TalepYaniti,
    VardiyaTipiGuncelle,
    VardiyaTipiOku,
    VardiyaTipiOlustur,
    YetkinlikGuncelle,
    YetkinlikOku,
    YetkinlikOlustur,
)
from app.services.tanim_kullanimi import kullanimi_olc
from app.services.tanim_servisi import TanimServisi

router = APIRouter(prefix="/api", tags=["tanim"])

Oturum = Annotated[Session, Depends(oturum_al)]


def _servis(oturum: Oturum) -> TanimServisi:
    return TanimServisi(oturum)


Servis = Annotated[TanimServisi, Depends(_servis)]


def _sil(depo: TanimDeposu, id_: int, bulunamadi: str) -> None:
    """Ortak silme yolu.

    Yanit kodu her iki sonucta da 204'tur: istemci acisindan "tanim artik
    listede degil/pasif" ayni sonuctur ve arayuz zaten silmeden ONCE
    /kullanim'a sorup kullaniciya ne olacagini soylemis olur. Ayri bir kod
    dondurmek, mevcut istemcilerin sozlesmesini bir bilgi kazandirmadan
    degistirirdi.
    """
    if depo.sil(id_) is SilmeSonucu.BULUNAMADI:
        raise HTTPException(status_code=404, detail=bulunamadi)


def _kullanim(depo: TanimDeposu, id_: int, bulunamadi: str) -> KullanimOku:
    if depo.getir(id_) is None:
        raise HTTPException(status_code=404, detail=bulunamadi)
    olcum = kullanimi_olc(depo.oturum, depo.model, id_)
    return KullanimOku(
        kullanimda_mi=olcum.kullanimda_mi,
        toplam=olcum.toplam,
        kalemler=[KullanimKalemi(kayit_turu=t, sayi=s) for t, s in olcum.kalemler],
    )


# --- Yetkinlik (FR-1.2) ------------------------------------------------


@router.get("/yetkinlik", response_model=list[YetkinlikOku])
def yetkinlik_listele(servis: Servis) -> list[YetkinlikOku]:
    return list(servis.yetkinlik.tumunu_getir())


@router.post("/yetkinlik", response_model=YetkinlikOku, status_code=201)
def yetkinlik_olustur(veri: YetkinlikOlustur, servis: Servis) -> YetkinlikOku:
    return servis.yetkinlik_olustur(veri.ad, veri.aciklama)  # type: ignore[return-value]


@router.put("/yetkinlik/{yetkinlik_id}", response_model=YetkinlikOku)
def yetkinlik_guncelle(yetkinlik_id: int, veri: YetkinlikGuncelle, servis: Servis) -> YetkinlikOku:
    nesne = servis.yetkinlik.guncelle(yetkinlik_id, **veri.model_dump(exclude_unset=True))
    if nesne is None:
        raise HTTPException(status_code=404, detail="Yetkinlik bulunamadi")
    return nesne  # type: ignore[return-value]


@router.get("/yetkinlik/{yetkinlik_id}/kullanim", response_model=KullanimOku)
def yetkinlik_kullanimi(yetkinlik_id: int, servis: Servis) -> KullanimOku:
    return _kullanim(servis.yetkinlik, yetkinlik_id, "Yetkinlik bulunamadi")


@router.delete("/yetkinlik/{yetkinlik_id}", status_code=204)
def yetkinlik_sil(yetkinlik_id: int, servis: Servis) -> None:
    _sil(servis.yetkinlik, yetkinlik_id, "Yetkinlik bulunamadi")


# --- Bina (FR-1.5) -------------------------------------------------------


@router.get("/bina", response_model=list[BinaOku])
def bina_listele(servis: Servis) -> list[BinaOku]:
    return list(servis.bina.tumunu_getir())


@router.post("/bina", response_model=BinaOku, status_code=201)
def bina_olustur(veri: BinaOlustur, servis: Servis) -> BinaOku:
    return servis.bina_olustur(veri.ad)  # type: ignore[return-value]


@router.put("/bina/{bina_id}", response_model=BinaOku)
def bina_guncelle(bina_id: int, veri: BinaGuncelle, servis: Servis) -> BinaOku:
    nesne = servis.bina.guncelle(bina_id, **veri.model_dump(exclude_unset=True))
    if nesne is None:
        raise HTTPException(status_code=404, detail="Bina bulunamadi")
    return nesne  # type: ignore[return-value]


@router.get("/bina/{bina_id}/kullanim", response_model=KullanimOku)
def bina_kullanimi(bina_id: int, servis: Servis) -> KullanimOku:
    return _kullanim(servis.bina, bina_id, "Bina bulunamadi")


@router.delete("/bina/{bina_id}", status_code=204)
def bina_sil(bina_id: int, servis: Servis) -> None:
    _sil(servis.bina, bina_id, "Bina bulunamadi")


# --- Gorev Noktasi (FR-1.6) ----------------------------------------------


@router.get("/nokta", response_model=list[GorevNoktasiOku])
def nokta_listele(servis: Servis) -> list[GorevNoktasiOku]:
    return list(servis.nokta.tumunu_getir())


@router.post("/nokta", response_model=GorevNoktasiOku, status_code=201)
def nokta_olustur(veri: GorevNoktasiOlustur, servis: Servis) -> GorevNoktasiOku:
    return servis.nokta_olustur(veri.ad, veri.bina_id, veri.onkosul_yetkinlik_id)  # type: ignore[return-value]


@router.put("/nokta/{nokta_id}", response_model=GorevNoktasiOku)
def nokta_guncelle(nokta_id: int, veri: GorevNoktasiGuncelle, servis: Servis) -> GorevNoktasiOku:
    nesne = servis.nokta.guncelle(nokta_id, **veri.model_dump(exclude_unset=True))
    if nesne is None:
        raise HTTPException(status_code=404, detail="Gorev noktasi bulunamadi")
    return nesne  # type: ignore[return-value]


@router.get("/nokta/{nokta_id}/kullanim", response_model=KullanimOku)
def nokta_kullanimi(nokta_id: int, servis: Servis) -> KullanimOku:
    return _kullanim(servis.nokta, nokta_id, "Gorev noktasi bulunamadi")


@router.delete("/nokta/{nokta_id}", status_code=204)
def nokta_sil(nokta_id: int, servis: Servis) -> None:
    _sil(servis.nokta, nokta_id, "Gorev noktasi bulunamadi")


# --- Vardiya Tipi (FR-1.3, FR-1.4) ---------------------------------------


@router.get("/vardiya-tipi", response_model=list[VardiyaTipiOku])
def vardiya_tipi_listele(servis: Servis) -> list[VardiyaTipiOku]:
    return list(servis.vardiya_tipi.tumunu_getir())


@router.post("/vardiya-tipi", response_model=VardiyaTipiOku, status_code=201)
def vardiya_tipi_olustur(veri: VardiyaTipiOlustur, servis: Servis) -> VardiyaTipiOku:
    return servis.vardiya_tipi_olustur(veri)  # type: ignore[return-value]


@router.put("/vardiya-tipi/{vardiya_tipi_id}", response_model=VardiyaTipiOku)
def vardiya_tipi_guncelle(
    vardiya_tipi_id: int, veri: VardiyaTipiGuncelle, servis: Servis
) -> VardiyaTipiOku:
    nesne = servis.vardiya_tipi_guncelle(vardiya_tipi_id, veri)
    if nesne is None:
        raise HTTPException(status_code=404, detail="Vardiya tipi bulunamadi")
    return nesne  # type: ignore[return-value]


@router.get("/vardiya-tipi/{vardiya_tipi_id}/kullanim", response_model=KullanimOku)
def vardiya_tipi_kullanimi(vardiya_tipi_id: int, servis: Servis) -> KullanimOku:
    return _kullanim(servis.vardiya_tipi, vardiya_tipi_id, "Vardiya tipi bulunamadi")


@router.delete("/vardiya-tipi/{vardiya_tipi_id}", status_code=204)
def vardiya_tipi_sil(vardiya_tipi_id: int, servis: Servis) -> None:
    _sil(servis.vardiya_tipi, vardiya_tipi_id, "Vardiya tipi bulunamadi")


# --- Personel (FR-1.1, FR-1.2) -------------------------------------------


@router.get("/personel", response_model=list[PersonelOku])
def personel_listele(servis: Servis) -> list[PersonelOku]:
    return [PersonelOku.modelden_olustur(p) for p in servis.personel.tumunu_getir()]


@router.post("/personel", response_model=PersonelOku, status_code=201)
def personel_olustur(veri: PersonelOlustur, servis: Servis) -> PersonelOku:
    return PersonelOku.modelden_olustur(servis.personel_olustur(veri))


@router.put("/personel/{personel_id}", response_model=PersonelOku)
def personel_guncelle(personel_id: int, veri: PersonelGuncelle, servis: Servis) -> PersonelOku:
    personel = servis.personel_guncelle(personel_id, veri)
    if personel is None:
        raise HTTPException(status_code=404, detail="Personel bulunamadi")
    return PersonelOku.modelden_olustur(personel)


@router.get("/personel/{personel_id}/kullanim", response_model=KullanimOku)
def personel_kullanimi(personel_id: int, servis: Servis) -> KullanimOku:
    return _kullanim(servis.personel, personel_id, "Personel bulunamadi")


@router.delete("/personel/{personel_id}", status_code=204)
def personel_sil(personel_id: int, servis: Servis) -> None:
    _sil(servis.personel, personel_id, "Personel bulunamadi")


# --- Talep + Yuk Gostergesi (FR-1.7, FR-1.8, FR-1.9) ----------------------


@router.get("/talep", response_model=TalepYaniti)
def talep_matrisini_getir(servis: Servis) -> TalepYaniti:
    hucreler, yuk = servis.talep_matrisini_getir()
    return TalepYaniti(hucreler=hucreler, yuk_gostergesi=yuk)  # type: ignore[arg-type]


@router.put("/talep", response_model=TalepYaniti)
def talep_hucresini_guncelle(hucre: TalepHucresi, servis: Servis) -> TalepYaniti:
    servis.talep_hucresini_guncelle(hucre)
    hucreler, yuk = servis.talep_matrisini_getir()
    return TalepYaniti(hucreler=hucreler, yuk_gostergesi=yuk)  # type: ignore[arg-type]


# --- Kural (FR-1.11, FR-1.12, FR-1.13) ------------------------------------


@router.get("/kural", response_model=list[KuralOku])
def kural_listele(servis: Servis) -> list[KuralOku]:
    return list(servis.kural.tumunu_getir())


@router.put("/kural/{kimlik}", response_model=KuralOku)
def kural_guncelle(kimlik: str, veri: KuralGuncelle, servis: Servis) -> KuralOku:
    mevcut = servis.kural.kimlige_gore_bul(kimlik)
    if mevcut is None:
        raise HTTPException(status_code=404, detail="Kural bulunamadi")
    nesne = servis.kural.guncelle(mevcut.kural_id, **veri.model_dump(exclude_unset=True))
    return nesne  # type: ignore[return-value]


# --- Musaitlik (FR-2.1, FR-2.2) -------------------------------------------


@router.get("/musaitlik", response_model=list[MusaitlikOku])
def musaitlik_listele(servis: Servis) -> list[MusaitlikOku]:
    return list(servis.musaitlik.tumunu_getir())


@router.post("/musaitlik", response_model=MusaitlikOku, status_code=201)
def musaitlik_olustur(veri: MusaitlikOlustur, servis: Servis) -> MusaitlikOku:
    return servis.musaitlik.olustur(**veri.model_dump())  # type: ignore[return-value]


@router.delete("/musaitlik/{musaitlik_id}", status_code=204)
def musaitlik_sil(musaitlik_id: int, servis: Servis) -> None:
    if not servis.musaitlik.sil(musaitlik_id):
        raise HTTPException(status_code=404, detail="Musaitlik kaydi bulunamadi")


# --- Tercih (FR-3.1, FR-3.2, FR-3.4) --------------------------------------


@router.get("/tercih", response_model=list[TercihOku])
def tercih_listele(servis: Servis) -> list[TercihOku]:
    return list(servis.tercih.tumunu_getir())


@router.post("/tercih", response_model=TercihOku, status_code=201)
def tercih_olustur(veri: TercihOlustur, servis: Servis) -> TercihOku:
    return servis.tercih.olustur(**veri.model_dump())  # type: ignore[return-value]


@router.put("/tercih/{tercih_id}", response_model=TercihOku)
def tercih_guncelle(tercih_id: int, veri: TercihGuncelle, servis: Servis) -> TercihOku:
    """FR-3.4: yonetici tercihi onaylar veya reddeder (durum degisikligi)."""
    nesne = servis.tercih.guncelle(tercih_id, **veri.model_dump(exclude_unset=True))
    if nesne is None:
        raise HTTPException(status_code=404, detail="Tercih bulunamadi")
    return nesne  # type: ignore[return-value]
