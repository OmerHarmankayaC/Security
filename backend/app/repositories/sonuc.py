"""Sonuc varliklari icin depo katmani (SDD 4.2.4)."""

from collections.abc import Sequence
from datetime import date

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.sonuc import Atama, CizelgeSurumu, CozumIsi, Donem, KapsamaAcigi
from app.repositories.taban import TabanDepo


class DonemDeposu(TabanDepo[Donem]):
    def __init__(self, oturum: Session) -> None:
        super().__init__(oturum, Donem)


class CizelgeSurumuDeposu(TabanDepo[CizelgeSurumu]):
    def __init__(self, oturum: Session) -> None:
        super().__init__(oturum, CizelgeSurumu)

    def donem_icin_sonraki_surum_no(self, donem_id: int) -> int:
        stmt = select(func.max(CizelgeSurumu.surum_no)).where(CizelgeSurumu.donem_id == donem_id)
        mevcut_en_buyuk = self.oturum.execute(stmt).scalar_one_or_none()
        return (mevcut_en_buyuk or 0) + 1

    def listele(self, *, donem_id: int | None = None) -> Sequence[CizelgeSurumu]:
        stmt = select(CizelgeSurumu)
        if donem_id is not None:
            stmt = stmt.where(CizelgeSurumu.donem_id == donem_id)
        return self.oturum.execute(stmt.order_by(CizelgeSurumu.surum_no.desc())).scalars().all()


class CozumIsiDeposu(TabanDepo[CozumIsi]):
    def __init__(self, oturum: Session) -> None:
        super().__init__(oturum, CozumIsi)


class AtamaDeposu(TabanDepo[Atama]):
    def __init__(self, oturum: Session) -> None:
        super().__init__(oturum, Atama)

    def surume_gore_sil(self, surum_id: int) -> None:
        """SDD 5.4: atamalar yazilmadan once o surumun mevcut atamalari silinir."""
        self.oturum.execute(delete(Atama).where(Atama.surum_id == surum_id))

    def surume_gore_getir(self, surum_id: int) -> Sequence[Atama]:
        stmt = select(Atama).where(Atama.surum_id == surum_id)
        return self.oturum.execute(stmt).scalars().all()

    def surume_ve_araliga_gore_getir(
        self, surum_id: int, baslangic: date, bitis: date
    ) -> Sequence[Atama]:
        """SDD 5.5: degisikligi_dogrula'nin pencere kapsamli kurallar icin kullandigi
        atama kumesi (degistirilen gunun +-7 gunluk penceresi)."""
        stmt = select(Atama).where(
            Atama.surum_id == surum_id, Atama.tarih >= baslangic, Atama.tarih <= bitis
        )
        return self.oturum.execute(stmt).scalars().all()

    def tekil_getir(self, surum_id: int, personel_id: int, tarih: date) -> Atama | None:
        stmt = select(Atama).where(
            Atama.surum_id == surum_id, Atama.personel_id == personel_id, Atama.tarih == tarih
        )
        return self.oturum.execute(stmt).scalar_one_or_none()


class KapsamaAcigiDeposu(TabanDepo[KapsamaAcigi]):
    def __init__(self, oturum: Session) -> None:
        super().__init__(oturum, KapsamaAcigi)

    def surume_gore_sil(self, surum_id: int) -> None:
        self.oturum.execute(delete(KapsamaAcigi).where(KapsamaAcigi.surum_id == surum_id))

    def surume_gore_getir(self, surum_id: int) -> Sequence[KapsamaAcigi]:
        stmt = select(KapsamaAcigi).where(KapsamaAcigi.surum_id == surum_id)
        return self.oturum.execute(stmt).scalars().all()
