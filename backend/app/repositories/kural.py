"""Kural varligi icin depo katmani (SDD 4.2.3, 5.1)."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.kural import Kural
from app.repositories.taban import TabanDepo


class KuralDeposu(TabanDepo[Kural]):
    def __init__(self, oturum: Session) -> None:
        super().__init__(oturum, Kural)

    def aktif_kurallari_getir(self) -> Sequence[Kural]:
        """SDD 5.1'deki kurallari_yukle() icin girdi; Kural satirlari zaten
        app.kurallar.kayit_defteri.KuralSatiri protokolune yapisal olarak uyar."""
        stmt = select(Kural).where(Kural.aktif.is_(True))
        return self.oturum.execute(stmt).scalars().all()

    def kimlige_gore_bul(self, kimlik: str) -> Kural | None:
        stmt = select(Kural).where(Kural.kimlik == kimlik)
        return self.oturum.execute(stmt).scalar_one_or_none()
