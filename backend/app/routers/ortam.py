"""Ortamin kendisi hakkinda soyledigi sey (Demo Senaryosu 10).

UC NOKTA YETKI ISTEMEZ. Serit giris ekraninda da gorunmelidir: gosterim
ortamina ilk bakan kisi henuz giris yapmamistir ve ona "bu veri gercek
degil" demenin tek ani odur. Donen tek alan bir yapilandirma BEYANIDIR;
hicbir veri, sayim ya da kimlik tasimaz.
"""

from fastapi import APIRouter

from app.config import ayarlar
from app.schemas.ortam import OrtamOku

router = APIRouter(prefix="/api", tags=["ortam"])


@router.get("/ortam", response_model=OrtamOku)
def ortami_oku() -> OrtamOku:
    return OrtamOku(demo_kipi=ayarlar.demo_kipi)
