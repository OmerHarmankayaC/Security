"""Izin belgesinin indirilmesi (SDD 5.10; SRS FR-2.8, TD-17).

BU YONLENDIRICININ KAPISI "GIRIS YAPMIS HER ROL"DUR ve bu bilinclidir.
Yetki denetimi INDIRME YOLUNUN ICINDEDIR, uc noktanin rol kapisinda degil:
calisan rolu KENDI kaydinin belgesine erisebilmeli, baskasininkine
erisememelidir. Ayrim rolde degil kaydin SAHIPLIGINDEDIR ve rol kapisi bu
ayrimi ifade edemez.

Yukleme ve silme yonetim islemidir; onlar `routers/tanim.py`de, idare
kapisinin arkasinda durur.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.db import oturum_al
from app.guvenlik import OturumBaglami, giris_yapan
from app.hatalar import Hata
from app.kayit import olay
from app.models.kimlik import IDARE_VE_USTU, Rol
from app.services.belge_servisi import BelgeServisi

router = APIRouter(prefix="/api", tags=["belge"])

Oturum = Annotated[Session, Depends(oturum_al)]
Baglam = Annotated[OturumBaglami, Depends(giris_yapan)]


@router.get("/musaitlik/{musaitlik_id}/belge")
def izin_belgesi_indir(musaitlik_id: int, oturum: Oturum, baglam: Baglam) -> Response:
    kayit = BelgeServisi(oturum).kaydi_getir(musaitlik_id)
    if kayit is None or kayit.belge_icerik is None:
        raise Hata(status_code=404, kod="belge_yok", detail="Bu izin kaydinda belge yok")

    kullanici = baglam.kullanici
    if kullanici.rol is Rol.CALISAN:
        # SAHIPLIK: adres bilmek erisim hakki vermez.
        if kayit.personel_id != kullanici.personel_id:
            raise Hata(
                status_code=403, kod="belge_yetkisi_yok", detail="Bu belgeye erisim yetkiniz yok"
            )
    elif kullanici.rol not in IDARE_VE_USTU:
        raise Hata(
            status_code=403, kod="belge_yetkisi_yok", detail="Bu belgeye erisim yetkiniz yok"
        )

    # HER ERISIM KAYDA GECER (TD-17): saglik verisinde "kim gordu" sorusunun
    # yanitsiz kalmasi, verinin korunmadigi anlamina gelir. BELGENIN KENDISI
    # hicbir gunluge girmez - yalnizca kim, hangi kayit, ne zaman.
    olay(
        "belge_erisim",
        kullanici=kullanici.kullanici_adi,
        rol=kullanici.rol.value,
        musaitlik_id=musaitlik_id,
        personel_id=kayit.personel_id,
    )
    return Response(
        content=kayit.belge_icerik,
        media_type=kayit.belge_tipi or "application/octet-stream",
        # `inline` DEGIL `attachment`: tarayicinin belgeyi kendi baglaminda
        # acmasi yerine indirmesi istenir.
        headers={"Content-Disposition": f'attachment; filename="{kayit.belge_adi or "belge"}"'},
    )
