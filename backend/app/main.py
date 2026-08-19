from fastapi import FastAPI

from app.routers import analiz, belge, calisan, cizelge, kimlik, kullanici, saglik, tanim

app = FastAPI(title="Vardiya Cizelgeleme Karar Destek Araci")

app.include_router(saglik.router)
app.include_router(kimlik.router)
app.include_router(kullanici.router)
app.include_router(tanim.router)
app.include_router(cizelge.router)
app.include_router(analiz.router)
app.include_router(calisan.router)
app.include_router(belge.router)
