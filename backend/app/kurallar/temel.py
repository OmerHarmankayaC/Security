"""Kural katalogunun temel arayuzu (SDD 3.2.1)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Any, ClassVar

from ortools.sat.python import cp_model

from app.models.kural import KuralTipi

# CP-SAT ifadesi (ceza terimi); model_kur bunu kural.agirlik ile carpip toplar (SDD 5.3).
CezaTerimi = Any

# x[p, g, v, n]: personel_id, tarih, vardiya_tipi_id, nokta_id -> CP-SAT BoolVar.
XAnahtari = tuple[int, date, int, int]


class KuralKapsami(StrEnum):
    """SDD 5.5 (surum 1.3): degisikligi_dogrula icin kuralin dogrula kapsami.

    PENCERE: degistirilen gunun +-7 gunluk penceresindeki atamalar yeterlidir
    (H1-H8 dogasi geregi yerel; S1/S5/S6/S6b/S7/S8 icin tek hucrelik bir
    degisikligin etkisi de yalnizca o hucreye/komsu gune bakilarak hesaplanir).
    DONEM_GENELI: kuralin kendisi donem genelindeki bir agregata (en yuksek/en
    dusuk deger veya donem toplami) bakar, pencereyle sinirlandirilamaz (S2,
    S3, S4).
    """

    PENCERE = "pencere"
    DONEM_GENELI = "donem_geneli"


@dataclass(frozen=True, slots=True, kw_only=True)
class Ihlal:
    """Zorunlu kisit ihlali veya esnek hedef ceza kaydi (SDD Ek A).

    personel_id/tarih zorunlu kisitlarda (H1-H8) daima doludur; bazi esnek
    hedefler (orn. S1 kapsama acigi, S2 adalet dagilimi) tek bir kisi/gune
    bagli olmayan toplu bir ceza urettigi icin bu iki alan opsiyoneldir
    (Ek A'daki `Ihlal('S2', ceza=acik)` ornegiyle tutarli).
    """

    kural_kimlik: str
    aciklama: str
    personel_id: int | None = None
    tarih: date | None = None
    ceza: float | None = None


class Kural(ABC):
    """SDD 3.2.1'deki Kural sinifinin Python karsiligi."""

    kimlik: ClassVar[str]
    tip: ClassVar[KuralTipi]
    kapsam: ClassVar[KuralKapsami] = KuralKapsami.PENCERE

    def __init__(self, parametreler: dict[str, Any], agirlik: int | None = None) -> None:
        self.parametreler = parametreler
        self.agirlik = agirlik

    @abstractmethod
    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, Any], baglam: Any
    ) -> CezaTerimi | None: ...

    @abstractmethod
    def dogrula(self, atamalar: Any, baglam: Any) -> list[Ihlal]: ...


class ZorunluKural(Kural):
    tip: ClassVar[KuralTipi] = KuralTipi.ZORUNLU


class EsnekHedef(Kural):
    tip: ClassVar[KuralTipi] = KuralTipi.ESNEK
