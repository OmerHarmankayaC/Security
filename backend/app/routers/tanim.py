"""Tanim yonetimi uc noktalari (SDD 3.2: tanim_router; SDD Ek B; SRS 5.1).

Yonlendirici ince tutulur: istegi semayla dogrular, tek bir servis metodunu
cagirir, sonucu JSON'a cevirir. Is mantigi burada yer almaz.
"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import oturum_al
from app.guvenlik import idare_yetkisi
from app.models.girdi import TERCIH_GUN_TEKILLIGI
from app.repositories.tanim import SilmeSonucu, TanimDeposu
from app.schemas.girdi import (
    BelgeOku,
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
    OzelGunGuncelle,
    OzelGunOku,
    OzelGunOlustur,
    PersonelGuncelle,
    PersonelOku,
    PersonelOlustur,
    TalepYaniti,
    TalepYazma,
    YetkinlikGuncelle,
    YetkinlikOku,
    YetkinlikOlustur,
)
from app.services.belge_servisi import (
    BelgeCokBuyukError,
    BelgeServisi,
    BelgeTipiKabulEdilmediError,
)
from app.services.tanim_kullanimi import kullanimi_olc
from app.services.tanim_servisi import (
    CakisanTalepAraligiError,
    KuralParametresiError,
    SicilKullanimdaError,
    TanimServisi,
)

# Butun tanim uc noktalari yonetici yetkisi ister (SRS 5.10: calisan rolu
# tanim, cozum ve yayin islevlerine erisemez). Kapi ROUTER duzeyinde: bu
# dosyaya sonradan eklenen bir uc noktanin kapisiz kalmasi mumkun degil.
router = APIRouter(prefix="/api", tags=["tanim"], dependencies=[Depends(idare_yetkisi)])

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


# --- Personel (FR-1.1, FR-1.2) -------------------------------------------


@router.get("/personel", response_model=list[PersonelOku])
def personel_listele(servis: Servis) -> list[PersonelOku]:
    return [PersonelOku.modelden_olustur(p) for p in servis.personel.tumunu_getir()]


@router.post("/personel", response_model=PersonelOku, status_code=201)
def personel_olustur(veri: PersonelOlustur, servis: Servis) -> PersonelOku:
    try:
        personel = servis.personel_olustur(veri)
    except SicilKullanimdaError as hata:
        raise HTTPException(status_code=409, detail=str(hata)) from hata
    return PersonelOku.modelden_olustur(personel)


@router.put("/personel/{personel_id}", response_model=PersonelOku)
def personel_guncelle(personel_id: int, veri: PersonelGuncelle, servis: Servis) -> PersonelOku:
    try:
        personel = servis.personel_guncelle(personel_id, veri)
    except SicilKullanimdaError as hata:
        # 409: istek bicimsel olarak gecerli (400 degil), yalniz mevcut
        # veriyle CAKISIYOR. Ayrimi korumak arayuze "alani duzeltip tekrar
        # gonder" ile "istegi bastan kur" arasindaki farki soyler.
        raise HTTPException(status_code=409, detail=str(hata)) from hata
    if personel is None:
        raise HTTPException(status_code=404, detail="Personel bulunamadi")
    return PersonelOku.modelden_olustur(personel)


@router.get("/personel/{personel_id}/kullanim", response_model=KullanimOku)
def personel_kullanimi(personel_id: int, servis: Servis) -> KullanimOku:
    return _kullanim(servis.personel, personel_id, "Personel bulunamadi")


@router.delete("/personel/{personel_id}", status_code=204)
def personel_sil(personel_id: int, servis: Servis) -> None:
    _sil(servis.personel, personel_id, "Personel bulunamadi")


# --- Ozel gun / resmi tatil (FR-1.10) --------------------------------------
#
# Tablo ve cozucu tarafi baslangictan beri vardi: `baglam_kurucu` donemdeki
# ozel gunleri okur ve `Baglam.hafta_sonu_mu` onlari hafta sonuyla ayni
# sayaca ekler (SRS TD-3), talep matrisinin `resmi_tatil` gun tipi de
# oradan tetiklenir. Eksik olan tek sey YAZMA yoluydu: hicbir uc nokta ve
# hicbir ekran `ozel_gun` tablosuna satir ekleyemiyordu, dolayisiyla
# FR-1.10 karsilanmiyor ve TD-3'un tatil hukmu olu kaliyordu.
#
# Yol `/api/ozel-gun`; anahtar TARIHIN KENDISIDIR (SDD 4.2.1), tamsayi bir
# kimlik degil.


@router.get("/ozel-gun", response_model=list[OzelGunOku])
def ozel_gun_listele(servis: Servis) -> list[OzelGunOku]:
    return [OzelGunOku.model_validate(g) for g in servis.ozel_gun.tumunu_getir()]


@router.post("/ozel-gun", response_model=OzelGunOku, status_code=201)
def ozel_gun_isaretle(veri: OzelGunOlustur, servis: Servis) -> OzelGunOku:
    return OzelGunOku.model_validate(servis.ozel_gun_isaretle(veri.tarih, veri.ad))


@router.put("/ozel-gun/{tarih}", response_model=OzelGunOku)
def ozel_gun_guncelle(tarih: date, veri: OzelGunGuncelle, servis: Servis) -> OzelGunOku:
    mevcut = servis.ozel_gun.getir(tarih)
    if mevcut is None:
        raise HTTPException(status_code=404, detail="Ozel gun bulunamadi")
    mevcut.ad = veri.ad
    return OzelGunOku.model_validate(mevcut)


@router.delete("/ozel-gun/{tarih}", status_code=204)
def ozel_gun_sil(tarih: date, servis: Servis) -> None:
    """Isareti kaldirir.

    Burada "kullanimda ise pasiflestir" kurali YOKTUR (bkz. OzelGunDeposu):
    ozel gune referans veren bir tablo yok ve bir tarih ya tatildir ya
    degildir. Gecmis cizelgeler etkilenmez - onlar uretildikleri andaki
    atamalari kendi iclerinde tasir (SDD 4.1).
    """
    if not servis.ozel_gun.sil(tarih):
        raise HTTPException(status_code=404, detail="Ozel gun bulunamadi")


# --- Talep + Yuk Gostergesi (FR-1.7, FR-1.8, FR-1.9) ----------------------


@router.get("/talep", response_model=TalepYaniti)
def talep_matrisini_getir(servis: Servis) -> TalepYaniti:
    araliklar, yuk = servis.talep_matrisini_getir()
    return TalepYaniti(araliklar=araliklar, yuk_gostergesi=yuk)  # type: ignore[arg-type]


@router.post("/talep", response_model=TalepYaniti, status_code=201)
def talep_araligi_ekle(veri: TalepYazma, servis: Servis) -> TalepYaniti:
    """Yeni bir talep araligi (SRS FR-1.7).

    Talep artik bir hucre degil bir ARALIK kaydidir; ekleme, duzenleme ve
    silme ayri uclardan yapilir. Onceki `PUT /api/talep` bir matris hucresini
    yerinde guncelliyordu ve aralik kayitlarinda karsiligi yok.
    """
    try:
        servis.talep_araligi_ekle(veri)
    except CakisanTalepAraligiError as hata:
        raise HTTPException(status_code=409, detail=str(hata)) from hata
    return _talep_yaniti(servis)


@router.put("/talep/{talep_id}", response_model=TalepYaniti)
def talep_araligi_guncelle(talep_id: int, veri: TalepYazma, servis: Servis) -> TalepYaniti:
    try:
        guncel = servis.talep_araligi_guncelle(talep_id, veri)
    except CakisanTalepAraligiError as hata:
        raise HTTPException(status_code=409, detail=str(hata)) from hata
    if guncel is None:
        raise HTTPException(status_code=404, detail="Talep kaydi bulunamadi")
    return _talep_yaniti(servis)


@router.delete("/talep/{talep_id}", response_model=TalepYaniti)
def talep_araligi_sil(talep_id: int, servis: Servis) -> TalepYaniti:
    if not servis.talep_araligi_sil(talep_id):
        raise HTTPException(status_code=404, detail="Talep kaydi bulunamadi")
    return _talep_yaniti(servis)


def _talep_yaniti(servis: TanimServisi) -> TalepYaniti:
    """Her yazma isleminden sonra LISTE ILE YUK birlikte doner.

    Yuk gostergesi (FR-1.9) talepten turetiliyor; ayri bir istekle
    alinsaydi arayuz iki cagri arasinda eski sayiyi gosterebilirdi.
    """
    araliklar, yuk = servis.talep_matrisini_getir()
    return TalepYaniti(araliklar=araliklar, yuk_gostergesi=yuk)  # type: ignore[arg-type]


# --- Kural (FR-1.11, FR-1.12, FR-1.13) ------------------------------------


@router.get("/kural", response_model=list[KuralOku])
def kural_listele(servis: Servis) -> list[KuralOku]:
    return [KuralOku.modelden_olustur(k) for k in servis.kural.tumunu_getir()]


@router.put("/kural/{kimlik}", response_model=KuralOku)
def kural_guncelle(kimlik: str, veri: KuralGuncelle, servis: Servis) -> KuralOku:
    """Kural SILINEMEZ, yalnizca degeri degisir (SDD 3.2.1).

    H1-H8 ve S1-S8 modelin yapisini olusturur ve kayit defterindeki siniflarla
    eslesir; katalogda karsiligi olmayan bir kural satiri zaten yuklenemez.
    Bu yuzden bu kaynakta DELETE yoktur — pasiflestirme `aktif` alaniyla
    yapilir.
    """
    mevcut = servis.kural.kimlige_gore_bul(kimlik)
    if mevcut is None:
        raise HTTPException(status_code=404, detail="Kural bulunamadi")
    alanlar = veri.model_dump(exclude_unset=True)
    if "parametreler" in alanlar:
        try:
            alanlar["parametreler"] = servis.kural_parametrelerini_dogrula(
                kimlik, alanlar["parametreler"]
            )
        except KuralParametresiError as hata:
            raise HTTPException(status_code=400, detail=str(hata)) from hata
    nesne = servis.kural.guncelle(mevcut.kural_id, **alanlar)
    assert nesne is not None  # kimlige_gore_bul yukarida dogruladi
    return KuralOku.modelden_olustur(nesne)


# --- Musaitlik (FR-2.1, FR-2.2) -------------------------------------------


@router.get("/musaitlik", response_model=list[MusaitlikOku])
def musaitlik_listele(servis: Servis) -> list[MusaitlikOku]:
    # `belge_var` artik satirin kendisinden okunur; ayri sorgu gerekmez.
    return [
        MusaitlikOku.model_validate(m).model_copy(update={"belge_var": m.belge_icerik is not None})
        for m in servis.musaitlik.tumunu_getir()
    ]


@router.post("/musaitlik", response_model=MusaitlikOku, status_code=201)
def musaitlik_olustur(veri: MusaitlikOlustur, servis: Servis) -> MusaitlikOku:
    return servis.musaitlik.olustur(**veri.model_dump())  # type: ignore[return-value]


@router.delete("/musaitlik/{musaitlik_id}", status_code=204)
def musaitlik_sil(musaitlik_id: int, servis: Servis) -> None:
    if not servis.musaitlik.sil(musaitlik_id):
        raise HTTPException(status_code=404, detail="Musaitlik kaydi bulunamadi")


# --- Tercih (FR-3.1, FR-3.2, FR-3.4) --------------------------------------


# --- Izin belgesi ----------------------------------------------------------
#
# ROUTER DUZEYINDEKI KAPI YONETICI YETKISIDIR (dosyanin basi). Belge saglik
# verisi tasiyabildigi icin bu yeterli degil gibi gorunse de, izinleri zaten
# ayni kapinin arkasindaki ekran yonetiyor: belgeyi gorebilen, kaydin
# kendisini de gorebiliyor. Calisanin KENDI belgesine erisimi ayri bir uc
# nokta ister (calisan panelinde izin gorunumu henuz yok).


@router.post("/musaitlik/{musaitlik_id}/belge", response_model=BelgeOku, status_code=201)
async def izin_belgesi_yukle(
    musaitlik_id: int, oturum: Oturum, dosya: Annotated[UploadFile, File()]
) -> BelgeOku:
    icerik = await dosya.read()
    try:
        # `dosya.content_type` KULLANILMAZ: istemcinin bildirdigi tiptir ve
        # kullanici girdisidir. Servis tipi icerigin imzasindan okur.
        kayit = BelgeServisi(oturum).yukle(musaitlik_id, dosya.filename or "belge", icerik)
    except BelgeTipiKabulEdilmediError as hata:
        raise HTTPException(
            status_code=415,
            detail=f"Bu dosya tipi kabul edilmiyor: {hata}. PNG, JPEG ya da PDF yukleyin.",
        ) from hata
    except BelgeCokBuyukError as hata:
        raise HTTPException(status_code=413, detail="Dosya cok buyuk; azami 5 MB.") from hata
    if kayit is None:
        raise HTTPException(status_code=404, detail="Izin kaydi bulunamadi")
    return BelgeOku(
        dosya_adi=kayit.belge_adi or "",
        icerik_tipi=kayit.belge_tipi or "",
        boyut_bayt=kayit.belge_boyut or 0,
    )


@router.delete("/musaitlik/{musaitlik_id}/belge", status_code=204)
def izin_belgesi_sil(musaitlik_id: int, oturum: Oturum) -> None:
    if not BelgeServisi(oturum).sil(musaitlik_id):
        raise HTTPException(status_code=404, detail="Bu izin kaydinda belge yok")


@router.get("/tercih", response_model=list[TercihOku])
def tercih_listele(servis: Servis) -> list[TercihOku]:
    return list(servis.tercih.tumunu_getir())


@router.post("/tercih", response_model=TercihOku, status_code=201)
def tercih_olustur(veri: TercihOlustur, servis: Servis) -> TercihOku:
    # Final review bulgu 4: `uq_tercih_personel_tarih` (goc c4f1a7d20b93)
    # calisan yolunda on-kontrol edilip ozel bir hatayla 409'a cevriliyor;
    # bu yol (yonetici) once dogrudan INSERT deniyordu ve kisit ihlali
    # yakalanmamis bir IntegrityError olarak 500 uretiyordu. Bu turun brief'i
    # bu uc noktanin semantigini (ustune yazma/karar kurali) DEGISTIRMIYOR -
    # yalniz mevcut kisidin artik sessizce 500 uretmemesini istiyor.
    #
    # KISIT ADINA DARALTILIR: bu uc nokta `personel_id`/`donem_id`yi disaridan
    # alir ve varliklarini dogrulamaz, dolayisiyla yabanci anahtar ihlali de
    # bir IntegrityError'dur. Ayrim yapilmazsa olmayan bir personel icin
    # gelen istek "bu tarih icin zaten bir tercihi var" diye yanlis bir
    # NEDENLE reddedilirdi; cagiran tarafi yanlis yere bakmaya gonderir.
    try:
        return servis.tercih.olustur(**veri.model_dump())  # type: ignore[return-value]
    except IntegrityError as hata:
        if TERCIH_GUN_TEKILLIGI not in str(hata.orig):
            raise
        raise HTTPException(
            status_code=409,
            detail="Bu personelin bu tarih icin zaten bir tercihi var",
        ) from hata


@router.put("/tercih/{tercih_id}", response_model=TercihOku)
def tercih_guncelle(tercih_id: int, veri: TercihGuncelle, servis: Servis) -> TercihOku:
    """FR-3.4: yonetici tercihi onaylar veya reddeder (durum degisikligi)."""
    nesne = servis.tercih.guncelle(tercih_id, **veri.model_dump(exclude_unset=True))
    if nesne is None:
        raise HTTPException(status_code=404, detail="Tercih bulunamadi")
    return nesne  # type: ignore[return-value]
