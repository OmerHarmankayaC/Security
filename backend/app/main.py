from fastapi import FastAPI

from app.routers import cizelge, saglik, tanim

app = FastAPI(title="Vardiya Cizelgeleme Karar Destek Araci")

app.include_router(saglik.router)
app.include_router(tanim.router)
app.include_router(cizelge.router)
