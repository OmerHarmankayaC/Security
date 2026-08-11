"""Tanim varliklari icin depo katmani (SDD 3.2, SDD 4.2.1)."""

import enum
from collections.abc import Sequence
from datetime import date, timedelta
from typing import TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import Base
from app.models.tanim import (
    Bina,
    GorevNoktasi,
    GunTipi,
    OzelGun,
    Personel,
    Talep,
    VardiyaTipi,
    Yetkinlik,
)
from app.repositories.taban import TabanDepo
from app.services.tanim_kullanimi import kullanimi_olc

M_Tanim = TypeVar("M_Tanim", bound=Base)


class SilmeSonucu(enum.StrEnum):
    """DELETE'in tanim uzerinde fiilen yaptigi sey."""

    SILINDI = "silindi"
    PASIFLESTIRILDI = "pasiflestirildi"
    BULUNAMADI = "bulunamadi"


class TanimDeposu(TabanDepo[M_Tanim]):
    """Silme kurali ortak olan tanim depolarinin tabani.

    Kural (madde 1): tanim baska bir kayitta kullaniliyorsa satir SILINMEZ,
    pasiflestirilir; hic kullanilmamis bir tanim gercekten silinir. Kullanim
    sayimi ile silme karari tek yerden (tanim_kullanimi) besleniyor.
    """

    def pasiflestir(self, nesne: M_Tanim) -> None:
        """Varsayilan pasiflestirme: `aktif` bayragi. Personel bunu ezer."""
        nesne.aktif = False  # type: ignore[attr-defined]

    def sil(self, id_: int) -> SilmeSonucu:
        nesne = self.getir(id_)
        if nesne is None:
            return SilmeSonucu.BULUNAMADI
        if kullanimi_olc(self.oturum, self.model, id_).kullanimda_mi:
            self.pasiflestir(nesne)
            self.oturum.flush()
            return SilmeSonucu.PASIFLESTIRILDI
        self.oturum.delete(nesne)
        self.oturum.flush()
        return SilmeSonucu.SILINDI


class YetkinlikDeposu(TanimDeposu[Yetkinlik]):
    def __init__(self, oturum: Session) -> None:
        super().__init__(oturum, Yetkinlik)


class BinaDeposu(TanimDeposu[Bina]):
    def __init__(self, oturum: Session) -> None:
        super().__init__(oturum, Bina)


class VardiyaTipiDeposu(TanimDeposu[VardiyaTipi]):
    def __init__(self, oturum: Session) -> None:
        super().__init__(oturum, VardiyaTipi)


class GorevNoktasiDeposu(TanimDeposu[GorevNoktasi]):
    def __init__(self, oturum: Session) -> None:
        super().__init__(oturum, GorevNoktasi)


class PersonelDeposu(TanimDeposu[Personel]):
    def __init__(self, oturum: Session) -> None:
        super().__init__(oturum, Personel)

    def sicille_bul(self, sicil_no: str, *, haric_personel_id: int | None = None) -> int | None:
        """Sicili tasiyan personelin kimligi (yoksa None).

        `haric_personel_id`, guncelleme icin: kaydin KENDI sicili cakisma
        sayilmamalidir, yoksa hicbir personel adini degistirip sicilini
        aynen birakamazdi.
        """
        stmt = select(Personel.personel_id).where(Personel.sicil_no == sicil_no)
        if haric_personel_id is not None:
            stmt = stmt.where(Personel.personel_id != haric_personel_id)
        return self.oturum.execute(stmt).scalars().first()

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

    def pasiflestir(self, nesne: Personel) -> None:
        """Personelin `aktif` bayragi yok; aktiflik tarih araligiyla ifade edilir
        (SDD 4.2.1). Pasiflestirme, aktiflik penceresini DUNDE kapatmaktir.

        Bugun yazilamaz: aktif_bitis dahil son gun oldugundan (H7, SRS 3.2)
        bugun yazmak personeli bugun hala musait birakir ve pasiflestirme
        istegi bugunku cozumde karsiliksiz kalir.
        """
        dun = date.today() - timedelta(days=1)
        # Zaten daha erken kapanmis bir pencere ileri tasinmaz.
        if nesne.aktif_bitis is None or nesne.aktif_bitis > dun:
            nesne.aktif_bitis = dun


class OzelGunDeposu(TabanDepo[OzelGun]):
    """Resmi tatil isaretleri (FR-1.10).

    `TanimDeposu`dan TUREMEZ ve bu bilincli: o taban, "kullanimda olan tanim
    silinmez, pasiflestirilir" kurali uzerine kurulu (aktif bayragi +
    kullanim sayimi). Ozel gunun ne bir `aktif` sutunu vardir ne de ona
    referans veren bir tablo; bir tarih ya resmi tatildir ya degildir.
    Pasiflestirilebilir bir tatil, olmayan bir kavrami modellemek olurdu.

    Birincil anahtar tarihin kendisidir (SDD 4.2.1), tamsayi bir kimlik
    degil - `TabanDepo.getir` de o anahtarla calisir.
    """

    def __init__(self, oturum: Session) -> None:
        super().__init__(oturum, OzelGun)

    def araliktakiler(self, baslangic: date, bitis: date) -> Sequence[OzelGun]:
        return (
            self.oturum.execute(
                select(OzelGun)
                .where(OzelGun.tarih >= baslangic, OzelGun.tarih <= bitis)
                .order_by(OzelGun.tarih)
            )
            .scalars()
            .all()
        )

    def tumunu_getir(self) -> Sequence[OzelGun]:
        """Tarihe gore SIRALI. Takvim gibi okunan bir liste, sirasiz
        dondugunde arayuzun her tuketicisi kendi siralamasini yazardi."""
        return self.oturum.execute(select(OzelGun).order_by(OzelGun.tarih)).scalars().all()


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
