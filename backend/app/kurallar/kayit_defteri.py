"""Kural kayit defteri: kimlik -> sinif eslemesi (SDD 3.2.1, 5.1)."""

from collections.abc import Iterable
from typing import Any, Protocol

from app.kurallar.temel import Kural

_kayit_defteri: dict[str, type[Kural]] = {}


def kayitli(kimlik: str):
    """Bir Kural alt sinifini kimligiyle kayit defterine ekleyen sinif dekoratoru."""

    def sarmalayici(sinif: type[Kural]) -> type[Kural]:
        if kimlik in _kayit_defteri:
            raise ValueError(f"Kural kimligi zaten kayitli: {kimlik}")
        sinif.kimlik = kimlik
        _kayit_defteri[kimlik] = sinif
        return sinif

    return sarmalayici


def bul(kimlik: str) -> type[Kural] | None:
    return _kayit_defteri.get(kimlik)


def tum_kimlikler() -> list[str]:
    return sorted(_kayit_defteri)


class KuralSatiri(Protocol):
    """kural tablosu satirinin (SDD 4.2.3) kurallari_yukle icin gerekli alanlari."""

    kimlik: str
    parametreler: dict[str, Any]
    agirlik: int | None


def kurallari_yukle(satirlar: Iterable[KuralSatiri]) -> list[Kural]:
    """SDD 5.1 FONKSIYON kurallari_yukle() birebir uygulamasi.

    satirlar, cagiran tarafindan zaten aktif kurallarla sinirlandirilmis olmalidir
    (repository katmaninin sorumlulugu, Sprint 1 Gun 4).
    """
    kurallar: list[Kural] = []
    for satir in satirlar:
        sinif = bul(satir.kimlik)
        if sinif is None:
            raise ValueError(f"Tanimsiz kural kimligi: {satir.kimlik}")
        kurallar.append(sinif(parametreler=satir.parametreler, agirlik=satir.agirlik))
    return kurallar
