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

    def tumunu_getir(self) -> Sequence[Talep]:
        """Okunabilir bir sirada: nokta, gun tipi, tarih, baslangic.

        Sirasiz dondugunde arayuzun her tuketicisi kendi siralamasini
        yazardi ve iki liste ayrisirdi.
        """
        stmt = select(Talep).order_by(
            Talep.nokta_id, Talep.gun_tipi, Talep.tarih.nulls_first(), Talep.baslangic
        )
        return self.oturum.execute(stmt).scalars().all()

    def ayni_kapsamdakiler(
        self, *, nokta_id: int, gun_tipi: GunTipi, tarih: date | None
    ) -> Sequence[Talep]:
        """Ayni (nokta, gun tipi, tarih) uclusundeki satirlar - cakisma denetiminin kumesi.

        Istisna satirlari (tarih dolu) genel satirlarla CAKISMAZ: bir tarih
        icin istisna varsa o gunun talebi yalnizca istisna satirlarindan
        olusur (SDD 4.2.2), yani iki kume ayni gunde bir arada
        degerlendirilmez.
        """
        stmt = select(Talep).where(
            Talep.nokta_id == nokta_id,
            Talep.gun_tipi == gun_tipi,
            Talep.tarih.is_(None) if tarih is None else Talep.tarih == tarih,
        )
        return self.oturum.execute(stmt).scalars().all()
