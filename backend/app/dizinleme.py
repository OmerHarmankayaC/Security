"""Arama motoru dizinlemesine kapali yanit basligi.

Gosterim ornegi herkese acik olabilir ama ARANABILIR olmamalidir: demo
verisi kurgudur ve bir arama sonucunda baglamsiz gorulmesi, onu gercek bir
kurumun cizelgesi sanmaya davet eder.

BASLIK KOSULSUZ GONDERILIR, demo kipine bagli DEGIL. Bu bir API; gercek bir
kurulumda da dizine girmesi icin bir neden yok ve kosula baglamak, ayarin
kapali oldugu bir ortamda uc noktalarin dizine acilmasi demekti.

`robots.txt` (frontend/public/) bir RICADIR, bu baslik ise yanitin
kendisinde durur; ikisi birlikte kullanilir cunku birini gormeyen gezgin
digerini gorur. Statik dosyalari FastAPI degil ters vekil sunuyor -
oradaki ayni baslik README'nin Deployment bolumunde yazili.
"""

from collections.abc import Awaitable, Callable

from fastapi import Request, Response

_BASLIK = "noindex, nofollow"


async def noindex_basligi(
    istek: Request, sonraki: Callable[[Request], Awaitable[Response]]
) -> Response:
    yanit = await sonraki(istek)
    yanit.headers["X-Robots-Tag"] = _BASLIK
    return yanit


__all__ = ["noindex_basligi"]
