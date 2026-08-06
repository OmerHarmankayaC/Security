"""Genel amacli CRUD deposu (SDD 3.2: SQL yalniz bu katmanda)."""

from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import Base

M = TypeVar("M", bound=Base)


class TabanDepo(Generic[M]):
    def __init__(self, oturum: Session, model: type[M]) -> None:
        self.oturum = oturum
        self.model = model

    def tumunu_getir(self) -> Sequence[M]:
        return self.oturum.execute(select(self.model)).scalars().all()

    def getir(self, id_: int) -> M | None:
        return self.oturum.get(self.model, id_)

    def olustur(self, **alanlar: Any) -> M:
        nesne = self.model(**alanlar)
        self.oturum.add(nesne)
        self.oturum.flush()
        return nesne

    def guncelle(self, id_: int, **alanlar: Any) -> M | None:
        nesne = self.getir(id_)
        if nesne is None:
            return None
        for anahtar, deger in alanlar.items():
            setattr(nesne, anahtar, deger)
        self.oturum.flush()
        return nesne

    def sil(self, id_: int) -> bool:
        nesne = self.getir(id_)
        if nesne is None:
            return False
        self.oturum.delete(nesne)
        self.oturum.flush()
        return True
