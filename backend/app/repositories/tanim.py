"""Tanim varliklari icin depo katmani (SDD 3.2, SDD 4.2.1)."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tanim import Bina, GorevNoktasi, GunTipi, Personel, Talep, VardiyaTipi, Yetkinlik
from app.repositories.taban import TabanDepo


class YetkinlikDeposu(TabanDepo[Yetkinlik]):
    def __init__(self, oturum: Session) -> None:
        super().__init__(oturum, Yetkinlik)


class BinaDeposu(TabanDepo[Bina]):
    def __init__(self, oturum: Session) -> None:
        super().__init__(oturum, Bina)


class VardiyaTipiDeposu(TabanDepo[VardiyaTipi]):
    def __init__(self, oturum: Session) -> None:
        super().__init__(oturum, VardiyaTipi)


class GorevNoktasiDeposu(TabanDepo[GorevNoktasi]):
    def __init__(self, oturum: Session) -> None:
        super().__init__(oturum, GorevNoktasi)

    def sil(self, id_: int) -> bool:
        """DELETE, gorev_noktasi icin pasiflestirmedir (aktif=False); satir silinmez.

        Nokta kimligi talep ve atama tablolarindan referans aldigi ve gecmis
        cizelgeler tanim degisikliginden etkilenmemesi gerektigi icin (SDD 4.1)
        gercek silme yerine SDD 4.2.1'deki `aktif` bayragi kullanilir.
        """
        nokta = self.getir(id_)
        if nokta is None:
            return False
        nokta.aktif = False
        self.oturum.flush()
        return True


class PersonelDeposu(TabanDepo[Personel]):
    def __init__(self, oturum: Session) -> None:
        super().__init__(oturum, Personel)

    def yetkinlikleri_ayarla(self, personel: Personel, yetkinlik_idleri: list[int]) -> None:
        yetkinlikler = (
            self.oturum.execute(
                select(Yetkinlik).where(Yetkinlik.yetkinlik_id.in_(yetkinlik_idleri))
            )
            .scalars()
            .all()
        )
        personel.yetkinlikler = list(yetkinlikler)
        self.oturum.flush()

    def sil(self, id_: int) -> bool:
        """DELETE, personel icin pasiflestirmedir (FR-1.1: 'pasiflestirilmesine imkan')."""
        personel = self.getir(id_)
        if personel is None:
            return False
        personel.aktif_bitis = date.today()
        self.oturum.flush()
        return True


class TalepDeposu(TabanDepo[Talep]):
    def __init__(self, oturum: Session) -> None:
        super().__init__(oturum, Talep)

    def dogal_anahtarla_bul(
        self, *, nokta_id: int, vardiya_tipi_id: int, gun_tipi: GunTipi, tarih: date | None
    ) -> Talep | None:
        stmt = select(Talep).where(
            Talep.nokta_id == nokta_id,
            Talep.vardiya_tipi_id == vardiya_tipi_id,
            Talep.gun_tipi == gun_tipi,
            Talep.tarih == tarih,
        )
        return self.oturum.execute(stmt).scalar_one_or_none()

    def hucreyi_guncelle(
        self,
        *,
        nokta_id: int,
        vardiya_tipi_id: int,
        gun_tipi: GunTipi,
        tarih: date | None,
        gereken_sayi: int,
    ) -> Talep:
        """SDD 4.2.1: (nokta, vardiya, gun_tipi, tarih) dogal anahtarina gore olustur/guncelle."""
        mevcut = self.dogal_anahtarla_bul(
            nokta_id=nokta_id, vardiya_tipi_id=vardiya_tipi_id, gun_tipi=gun_tipi, tarih=tarih
        )
        if mevcut is not None:
            mevcut.gereken_sayi = gereken_sayi
            self.oturum.flush()
            return mevcut
        return self.olustur(
            nokta_id=nokta_id,
            vardiya_tipi_id=vardiya_tipi_id,
            gun_tipi=gun_tipi,
            tarih=tarih,
            gereken_sayi=gereken_sayi,
        )
