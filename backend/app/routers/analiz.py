"""Analiz ve Excel disa aktarma uc noktalari (SDD 3.2, 5.8; SRS FR-8.x)."""

from io import BytesIO
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db import oturum_al
from app.guvenlik import yonetici_yetkisi
from app.schemas.analiz import AnalizOku
from app.services.analiz_servisi import AnalizServisi
from app.services.disa_aktarma_servisi import DisaAktarmaServisi, dosya_adi

# Analiz raporlari butun personelin gece/hafta sonu/saat kirilimini tasir;
# yonetici yetkisi ister (SRS 5.10).
router = APIRouter(prefix="/api", tags=["analiz"], dependencies=[Depends(yonetici_yetkisi)])

Oturum = Annotated[Session, Depends(oturum_al)]


@router.get("/analiz/{surum_id}", response_model=AnalizOku)
def analiz_getir(
    surum_id: int,
    oturum: Oturum,
    ufuk: Literal["donem", "adalet"] = "donem",
) -> AnalizOku:
    """`ufuk` adalet olculerinin hangi pencereden okundugunu secer (SDD 6.3.4).

    Varsayilan DONEM: kabul kriteri planlama donemini olcer (Charter 1.5) ve
    ekran ilk acildiginda o sayiyi gostermelidir. Adalet ufku bilincli bir
    secimle acilir.
    """
    sonuc = AnalizServisi(oturum).hesapla(surum_id, ufuk)
    if sonuc is None:
        raise HTTPException(status_code=404, detail="Cizelge surumu bulunamadi")
    return sonuc


# XLSX'in resmi MIME turu. Tarayici indirme adini `Content-Disposition`dan
# okur; ad donem ve surum tasir, yoksa iki indirme "(1)" ile ayrisir ve
# hangisinin hangi surum oldugu kaybolur.
_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _kitabi_gonder(kitap, ad: str) -> StreamingResponse:
    """Calisma kitabini BELLEKTEN dogrudan doner.

    Ayri bir is kuyrugu KURULMAZ (SDD 5.8): bir donemdeki atama sayisi
    birkac yuzdur ve olcek bunu gerektirmez. Kuyruk, ureten ile indiren
    arasina bir durum makinesi daha koyardi.
    """
    tampon = BytesIO()
    kitap.save(tampon)
    tampon.seek(0)
    return StreamingResponse(
        tampon,
        media_type=_XLSX,
        headers={"Content-Disposition": f'attachment; filename="{ad}"'},
    )


@router.get("/surum/{surum_id}/cizelge.xlsx")
def cizelge_excel(surum_id: int, oturum: Oturum) -> StreamingResponse:
    """Cizelgenin uc sayfali Excel ciktisi (SRS FR-8.5)."""
    servis = DisaAktarmaServisi(oturum)
    kitap = servis.cizelge_calisma_kitabi(surum_id)
    if kitap is None:
        raise HTTPException(status_code=404, detail="Cizelge surumu bulunamadi")
    surum = servis.surum.getir(surum_id)
    assert surum is not None
    return _kitabi_gonder(kitap, dosya_adi(surum, "cizelge"))


@router.get("/surum/{surum_id}/analiz.xlsx")
def analiz_excel(surum_id: int, oturum: Oturum) -> StreamingResponse:
    """Analizin dort sayfali, grafikli Excel ciktisi (SRS FR-8.9)."""
    servis = DisaAktarmaServisi(oturum)
    kitap = servis.analiz_calisma_kitabi(surum_id)
    if kitap is None:
        raise HTTPException(status_code=404, detail="Cizelge surumu bulunamadi")
    surum = servis.surum.getir(surum_id)
    assert surum is not None
    return _kitabi_gonder(kitap, dosya_adi(surum, "analiz"))
