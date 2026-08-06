"""Kural katalogunun temel arayuzu (SDD 3.2.1)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Any, ClassVar

from app.models.kural import KuralTipi

# CP-SAT ifadesi (ceza terimi); Sprint 2 Gun 6'da CozucuAdaptoru ile somutlasacak (SDD 5.3).
CezaTerimi = Any


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

    def __init__(self, parametreler: dict[str, Any], agirlik: int | None = None) -> None:
        self.parametreler = parametreler
        self.agirlik = agirlik

    @abstractmethod
    def modele_ekle(self, model: Any, degiskenler: Any, baglam: Any) -> CezaTerimi | None: ...

    @abstractmethod
    def dogrula(self, atamalar: Any, baglam: Any) -> list[Ihlal]: ...


class ZorunluKural(Kural):
    tip: ClassVar[KuralTipi] = KuralTipi.ZORUNLU

    def modele_ekle(self, model: Any, degiskenler: Any, baglam: Any) -> None:
        raise NotImplementedError(
            "CP-SAT model entegrasyonu Sprint 2 Gun 6'da tamamlanacak (SDD 5.3)"
        )


class EsnekHedef(Kural):
    tip: ClassVar[KuralTipi] = KuralTipi.ESNEK

    def modele_ekle(self, model: Any, degiskenler: Any, baglam: Any) -> CezaTerimi:
        raise NotImplementedError(
            "CP-SAT model entegrasyonu Sprint 2 Gun 6'da tamamlanacak (SDD 5.3)"
        )
