"""Gosterim kipinde yazma yasagi (Demo Senaryosu 2.2, 10).

Gosterim ortami PAYLASILIR. Bir ziyaretcinin cizelgeyi degistirmesi, ayni
anda bakan herkesin gordugu seyi degistirmek demektir; iki kisi ayni sayfaya
bakarken birinin sildigi personel digerinin ekranindan kaybolur. Dahasi
"her gece sifirlanir" sozu, gun icinde bozulan bir gosterimi kurtarmaz.

ARAYUZ KISITLANMAZ, SUNUCU REDDEDER. Duzenleme araclarini gizlemek urunun
yaptigi isi gormeyi engellerdi - oysa gosterim ortaminin butun amaci onu
gostermek. Ziyaretci hucreye tiklar, blogu tasir, dogrulamanin ne dedigini
gorur; yalnizca KAYDET adimi geri doner.

KAPI ARA KATMANDA, UC NOKTALARDA DEGIL. Her yazma ucuna tek tek bagimlilik
eklemek, yarin eklenen bir uc noktanin onu unutmasi demekti - ve unutuldugu
sessizce anlasilirdi. Burada varsayilan REDDETMEKTIR; izin verilenler adiyla
sayilidir.
"""

from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.status import HTTP_403_FORBIDDEN

from app.config import ayarlar

# Yazma sayilmayan yontemler.
_OKUMA_YONTEMLERI = frozenset({"GET", "HEAD", "OPTIONS"})

# GET olmayan ama HICBIR SEY YAZMAYAN uc noktalar. Uc'u de gosterimin asil
# anlatmak istedigi seyler:
#
#   /api/giris, /api/cikis  - oturum acilamazsa gosterilecek bir sey kalmaz.
#   /api/on-kontrol         - "cozmeden once neye takilir" sorusunun yaniti;
#                             yalnizca okur (app/services/on_kontrol_servisi).
#   /api/atama/dogrula      - elle duzenlemenin canli dogrulamasi; aday
#                             cizelgeyi BELLEKTE kurar (SDD 5.5). Bu ucu
#                             kapatmak, duzenleme yolunu gorunur birakip
#                             gorunmez kilardi.
_IZINLI_YOLLAR = frozenset(
    {
        "/api/giris",
        "/api/cikis",
        "/api/on-kontrol",
        "/api/atama/dogrula",
    }
)

_MESAJ = (
    "Gösterim ortamında değişiklikler kaydedilmez. Ekranı ve düzenleme "
    "araçlarını serbestçe deneyebilirsiniz; kaydetme adımı herkesin gördüğü "
    "veriyi değiştireceği için kapalıdır. Veri her gece yeniden kurulur."
)


async def salt_okunur_kapisi(
    istek: Request, sonraki: Callable[[Request], Awaitable[Response]]
) -> Response:
    if not ayarlar.demo_kipi:
        return await sonraki(istek)
    if istek.method in _OKUMA_YONTEMLERI:
        return await sonraki(istek)
    if istek.url.path in _IZINLI_YOLLAR:
        return await sonraki(istek)
    # 403, 405 DEGIL: uc nokta vardir ve yontemi destekler; reddedilen sey
    # BU ORTAMDA yazma yetkisidir. 405 "boyle bir yontem yok" derdi ve
    # arayuzun gosterdigi dugmeyi yalancı çıkarırdı.
    return JSONResponse(status_code=HTTP_403_FORBIDDEN, content={"detail": _MESAJ})


__all__ = ["salt_okunur_kapisi"]
