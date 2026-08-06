from fastapi import APIRouter

router = APIRouter(tags=["saglik"])


@router.get("/health")
def saglik_kontrolu() -> dict[str, str]:
    return {"durum": "ok"}
