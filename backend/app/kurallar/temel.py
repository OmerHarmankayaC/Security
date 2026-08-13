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

# x[p, s, n]: personel_id, MUTLAK SAAT INDEKSI, nokta_id -> CP-SAT BoolVar
# (SRS TD-13). Eksen gun basina sifirlanmaz; gun kavrami yalnizca sayim
# icin kullanilir ve `Baglam.saat_gunu` uzerinden turetilir.
XAnahtari = tuple[int, int, int]


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


@dataclass(frozen=True, slots=True, kw_only=True)
class ParametreTanimi:
    """Bir kural parametresinin arayuzde nasil gosterilecegi.

    Parametreler veritabaninda belge alaninda (JSONB) durur, cunku her
    kuralin parametre kumesi farklidir (SDD 4.2.3). Ama kullaniciya ham JSON
    gostermek NFR-5'e aykiri; alan-deger olarak duzenlenebilmesi icin her
    anahtarin okunabilir bir etiketi ve siniri burada, kural sinifinin
    yaninda tanimlanir. NFR-10 zaten yeni bir kuralin "kural tanimina bir
    kayit eklemek" ile gelmesini ongoruyor — bu tanim o kaydin parcasi.
    """

    anahtar: str
    etiket: str
    birim: str | None = None
    asgari: int | None = None
    azami: int | None = None


class Kural(ABC):
    """SDD 3.2.1'deki Kural sinifinin Python karsiligi."""

    kimlik: ClassVar[str]
    tip: ClassVar[KuralTipi]
    kapsam: ClassVar[KuralKapsami] = KuralKapsami.PENCERE
    # Kural katalogundaki okunabilir ad ve kisa aciklama (SRS bolum 4).
    # Arayuzde "H1" yerine bunlar gosterilir.
    ad: ClassVar[str] = ""
    aciklama: ClassVar[str] = ""
    parametre_tanimlari: ClassVar[tuple[ParametreTanimi, ...]] = ()

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
