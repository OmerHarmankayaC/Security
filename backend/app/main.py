from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.dizinleme import noindex_basligi
from app.repositories.sonuc import TaslakSiniriAsildiError
from app.routers import (
    analiz,
    belge,
    calisan,
    cizelge,
    demo,
    kimlik,
    kullanici,
    ortam,
    saglik,
    tanim,
)
from app.salt_okunur import salt_okunur_kapisi

app = FastAPI(title="Vardiya Cizelgeleme Karar Destek Araci")

# Gosterim kipinde yazma yasagi (app/salt_okunur.py). Ara katman, uc nokta
# bagimliligi DEGIL: yarin eklenen bir yazma ucu bunu unutamaz.
app.middleware("http")(salt_okunur_kapisi)

# Arama motorlarina kapali (app/dizinleme.py). Kosulsuz: bu bir API ve
# gercek bir kurulumda da dizine girmesi icin bir neden yok.
app.middleware("http")(noindex_basligi)


@app.exception_handler(TaslakSiniriAsildiError)
def taslak_siniri(_istek: Request, hata: TaslakSiniriAsildiError) -> JSONResponse:
    """Donem basina acik surum siniri (SDD 5.6) — 409.

    Uc noktalarda tek tek yakalanmiyor: surum acan dort yol var (bos taslak,
    turetilmis taslak, kopya, cozum baslatma) ve yarin bir besincisi
    eklenebilir. Uygulama duzeyinde tek isleyici, o yolun yakalamayi
    unutmasini imkansiz kilar.

    409, 400 DEGIL: istek gecerli, CAKISTIGI sey sistemin o andaki durumu -
    ve kullanicinin yapacagi sey istegi duzeltmek degil, yer acmak.
    """
    return JSONResponse(status_code=409, content={"detail": str(hata)})


app.include_router(saglik.router)
app.include_router(ortam.router)
app.include_router(demo.router)
app.include_router(kimlik.router)
app.include_router(kullanici.router)
app.include_router(tanim.router)
app.include_router(cizelge.router)
app.include_router(analiz.router)
app.include_router(calisan.router)
app.include_router(belge.router)
