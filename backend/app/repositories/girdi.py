"""Girdi varliklari icin depo katmani (SDD 3.2, SDD 4.2.2)."""

from collections.abc import Sequence
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.girdi import Musaitlik, Tercih
from app.repositories.taban import TabanDepo


class MusaitlikDeposu(TabanDepo[Musaitlik]):
    def __init__(self, oturum: Session) -> None:
        super().__init__(oturum, Musaitlik)


class TercihDeposu(TabanDepo[Tercih]):
    def __init__(self, oturum: Session) -> None:
        super().__init__(oturum, Tercih)

    def personele_gore_getir(self, personel_id: int) -> Sequence[Tercih]:
        """Calisan Paneli — Tercihlerim (SDD 6.1): en yeni tercih en ustte."""
        stmt = select(Tercih).where(Tercih.personel_id == personel_id).order_by(Tercih.tarih.desc())
        return self.oturum.execute(stmt).scalars().all()

    def personel_ve_tarihe_gore_getir(self, personel_id: int, tarih: date) -> Tercih | None:
        """Tekillik kisitinin okuma tarafi: o gunun tercihi (varsa)."""
        stmt = select(Tercih).where(
            Tercih.personel_id == personel_id, Tercih.tarih == tarih
        )
        return self.oturum.execute(stmt).scalars().one_or_none()
