"""Sonuc varliklari icin depo katmani (SDD 4.2.4)."""

from sqlalchemy.orm import Session

from app.models.sonuc import Donem
from app.repositories.taban import TabanDepo


class DonemDeposu(TabanDepo[Donem]):
    def __init__(self, oturum: Session) -> None:
        super().__init__(oturum, Donem)
