from fastapi import FastAPI

from app.routers import saglik

app = FastAPI(title="Vardiya Cizelgeleme Karar Destek Araci")

app.include_router(saglik.router)
