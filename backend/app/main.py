from fastapi import FastAPI

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
