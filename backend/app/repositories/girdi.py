"""Girdi varliklari icin depo katmani (SDD 3.2, SDD 4.2.2)."""

from sqlalchemy.orm import Session

from app.models.girdi import Musaitlik, Tercih
from app.repositories.taban import TabanDepo


class MusaitlikDeposu(TabanDepo[Musaitlik]):
    def __init__(self, oturum: Session) -> None:
        super().__init__(oturum, Musaitlik)


class TercihDeposu(TabanDepo[Tercih]):
    def __init__(self, oturum: Session) -> None:
        super().__init__(oturum, Tercih)
