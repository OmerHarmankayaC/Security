"""Gosterim ortaminin kimlik bilgisi (Demo Senaryosu 7).

UC NOKTA YALNIZCA DEMO KIPINDE VARDIR. Kapali kipte 404 doner - "yetkiniz
yok" (403) degil: 403, var olan ama erisilemeyen bir kaynagi isaret eder ve
gercek bir kurulumda "demo kimlik bilgisi bir yerlerde duruyor ama bana
kapali" izlenimi verirdi. Kapali kipte boyle bir kaynak YOKTUR.

PAROLALAR ON YUZ PAKETINE GOMULMEZ ve saklanmaz da: her istekte tohumdan
(`ayarlar.demo_parola_tohumu`, ortam degiskeni) yeniden turetilirler. Boylece
depoda, derlenmis pakette, surum gecmisinde ve veritabaninda duz metin olarak
hicbir yerde bulunmazlar - hesabi acan uretec de ayni turetmeyi yapar.

Yetki ISTEMEZ, cunku gosterildigi yer giris ekranidir: bilgiyi gormesi
gereken kisi henuz giris yapmamis olandir.
"""

from fastapi import APIRouter, HTTPException, status

from app.config import ayarlar
from app.schemas.demo import DemoHesabiOku, DemoKimlikOku
from app.services.demo_hesaplari import gosterilecekler, parola_uret

router = APIRouter(prefix="/api", tags=["demo"])


@router.get("/demo/kimlik", response_model=DemoKimlikOku)
def demo_kimligini_oku() -> DemoKimlikOku:
    # IKI KOSUL DA GEREKLI. Demo kipi acik ama tohum tanimsizsa turetilecek
    # bir parola yoktur; bos parolali bir kutu cizmek, calismayan bir girisi
    # calisiyormus gibi gostermek olurdu.
    tohum = ayarlar.demo_parola_tohumu
    if not ayarlar.demo_kipi or not tohum:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return DemoKimlikOku(
        hesaplar=[
            DemoHesabiOku(
                kullanici_adi=h.kullanici_adi,
                rol=h.rol.value,
                aciklama=h.aciklama,
                parola=parola_uret(tohum, h.kullanici_adi),
            )
            for h in gosterilecekler()
        ],
    )
