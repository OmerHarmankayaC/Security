"""Gosterim ortaminin kimlik bilgisi (Demo Senaryosu 7).

UC NOKTA YALNIZCA DEMO KIPINDE VARDIR. Kapali kipte 404 doner - "yetkiniz
yok" (403) degil: 403, var olan ama erisilemeyen bir kaynagi isaret eder ve
gercek bir kurulumda "demo kimlik bilgisi bir yerlerde duruyor ama bana
kapali" izlenimi verirdi. Kapali kipte boyle bir kaynak YOKTUR.

PAROLA ON YUZ PAKETINE GOMULMEZ. Calisma zamaninda buradan gelir; boylece
depoda, derlenmis pakette ve surum gecmisinde hicbir yerde bulunmaz. Kaynagi
`ayarlar.demo_parola`, yani ortam degiskeni.

Yetki ISTEMEZ, cunku gosterildigi yer giris ekranidir: bilgiyi gormesi
gereken kisi henuz giris yapmamis olandir.
"""

from fastapi import APIRouter, HTTPException, status

from app.config import ayarlar
from app.schemas.demo import DemoHesabiOku, DemoKimlikOku
from app.services.demo_hesaplari import gosterilecekler

router = APIRouter(prefix="/api", tags=["demo"])


@router.get("/demo/kimlik", response_model=DemoKimlikOku)
def demo_kimligini_oku() -> DemoKimlikOku:
    # IKI KOSUL DA GEREKLI. Demo kipi acik ama parola tanimsizsa gosterilecek
    # bir kimlik bilgisi yoktur; bos parolali bir kutu cizmek, calismayan bir
    # girisi calisiyormus gibi gostermek olurdu.
    if not ayarlar.demo_kipi or not ayarlar.demo_parola:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return DemoKimlikOku(
        parola=ayarlar.demo_parola,
        hesaplar=[
            DemoHesabiOku(kullanici_adi=h.kullanici_adi, rol=h.rol.value, aciklama=h.aciklama)
            for h in gosterilecekler()
        ],
    )
