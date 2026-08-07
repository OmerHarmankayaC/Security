"""Cizelgeleme uc noktalari (SDD 3.2: cizelge_router; SDD Ek B).

/api/on-kontrol (Sprint 2 Gun 7), /api/cozum (Sprint 2 Gun 8), /api/atama
(Sprint 2 Gun 9), /api/donem + /api/surum + /api/atama/kilit (Sprint 2 Gun 10 -
Cizelge/Cozum ekranlarinin ihtiyac duydugu okuma uc noktalari ve kilitleme).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import oturum_al
from app.models.sonuc import CozumIsiDurumu
from app.repositories.sonuc import (
    AtamaDeposu,
    CizelgeSurumuDeposu,
    CozumIsiDeposu,
    DonemDeposu,
    KapsamaAcigiDeposu,
)
from app.schemas.cozum import CozumBaslatIstek, CozumOku
from app.schemas.dogrulama import AtamaDegisikligiIstek, DogrulamaSonucuOku, IhlalOku
from app.schemas.on_kontrol import BulguOku, OnKontrolIstek, OnKontrolYaniti
from app.schemas.surum import (
    AtamaKilitIstek,
    AtamaOku,
    CizelgeSurumuOku,
    DonemOku,
    DonemOlustur,
    KapsamaAcigiOku,
    SurumTaslakTuretIstek,
)
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
    is_kaydi = servis.baslat(
        istek.donem_id,
        onceki_surum_id=istek.onceki_surum_id,
        zaman_limiti_saniye=istek.zaman_limiti_saniye,
    )
    if is_kaydi is None:
        raise HTTPException(status_code=404, detail="Donem ya da onceki surum bulunamadi")
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


@router.post("/atama/kilit", response_model=AtamaOku)
def atama_kilit_ayarla(istek: AtamaKilitIstek, oturum: Oturum) -> AtamaOku:
    servis = DogrulamaServisi(oturum)
    try:
        atama = servis.kilit_ayarla(istek.surum_id, istek.personel_id, istek.tarih, istek.kilitli)
    except SurumTaslakDegilError as hata:
        raise HTTPException(status_code=409, detail=str(hata)) from hata
    if atama is None:
        raise HTTPException(status_code=404, detail="Cizelge surumu ya da atama bulunamadi")
    return AtamaOku.model_validate(atama)


# --- Donem / Surum okuma uc noktalari (SDD Ek B; cizelge/cozum ekranlarinin
# donem secici + izgara + kapsama acigi ihtiyaci icin) -----------------------


@router.get("/donem", response_model=list[DonemOku])
def donem_listele(oturum: Oturum) -> list[DonemOku]:
    return list(DonemDeposu(oturum).tumunu_getir())  # type: ignore[return-value]


@router.post("/donem", response_model=DonemOku, status_code=201)
def donem_olustur(veri: DonemOlustur, oturum: Oturum) -> DonemOku:
    return DonemDeposu(oturum).olustur(**veri.model_dump())  # type: ignore[return-value]


@router.get("/surum", response_model=list[CizelgeSurumuOku])
def surum_listele(
    oturum: Oturum, donem_id: Annotated[int | None, Query()] = None
) -> list[CizelgeSurumuOku]:
    return list(CizelgeSurumuDeposu(oturum).listele(donem_id=donem_id))  # type: ignore[return-value]


@router.post("/surum", response_model=CizelgeSurumuOku, status_code=201)
def surum_taslak_turet(veri: SurumTaslakTuretIstek, oturum: Oturum) -> CizelgeSurumuOku:
    """SDD Ek B: 'Cizelge surumleri; taslak turetme'. Cozum baslatmaz - yalniz
    onceki surume bagli bos bir taslak olusturur (fiili yeniden cozum icin
    bkz. POST /api/cozum + onceki_surum_id)."""
    surum = CizelgeSurumuDeposu(oturum).taslak_turet(veri.onceki_surum_id)
    if surum is None:
        raise HTTPException(status_code=404, detail="Onceki surum bulunamadi")
    return CizelgeSurumuOku.model_validate(surum)


@router.post("/surum/{surum_id}/yayinla", response_model=CizelgeSurumuOku)
def surum_yayinla(surum_id: int, oturum: Oturum) -> CizelgeSurumuOku:
    """TD-8: surumu yayinlar; ayni donemde daha once yayinlanmis bir surum
    varsa arsiv durumuna gecer."""
    surum = CizelgeSurumuDeposu(oturum).yayinla(surum_id)
    if surum is None:
        raise HTTPException(status_code=404, detail="Cizelge surumu bulunamadi")
    return CizelgeSurumuOku.model_validate(surum)


@router.get("/surum/{surum_id}/atama", response_model=list[AtamaOku])
def surum_atamalarini_getir(surum_id: int, oturum: Oturum) -> list[AtamaOku]:
    return list(AtamaDeposu(oturum).surume_gore_getir(surum_id))  # type: ignore[return-value]


@router.get("/surum/{surum_id}/kapsama-acigi", response_model=list[KapsamaAcigiOku])
def surum_kapsama_acigini_getir(surum_id: int, oturum: Oturum) -> list[KapsamaAcigiOku]:
    return list(KapsamaAcigiDeposu(oturum).surume_gore_getir(surum_id))  # type: ignore[return-value]
