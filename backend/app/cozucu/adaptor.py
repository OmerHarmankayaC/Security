"""OR-Tools ile butun etkilesimi kapsayan dar arayuz (SDD 3.2, 3.4.3).

Sistemin geri kalani CP-SAT'i yalnizca bu modul uzerinden gorur: model kur
(model_kurucu.model_kur), coz, ara cozum bildir, sonucu dondur. Kutuphanenin
surum degisiklikleri veya cozucunun degistirilmesi yalnizca bu dosyayi
etkiler.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from ortools.sat.python import cp_model

from app.kurallar.temel import XAnahtari

_UYGUN_DURUMLAR = (cp_model.OPTIMAL, cp_model.FEASIBLE)

KapsamaAnahtari = tuple[date, int, int]


@dataclass(frozen=True, slots=True)
class CozumSonucu:
    durum: str  # "optimal" | "uygun" | "cozum_yok"
    atanan_anahtarlar: frozenset[XAnahtari]
    toplam_ceza: float | None
    sure_saniye: float
    # SDD 5.4: cozum.hedef_bazinda_ceza() ve cozum.eksik_degiskenleri.
    ceza_dokumu: dict[str, float] = field(default_factory=dict)
    kapsama_eksikleri: dict[KapsamaAnahtari, int] = field(default_factory=dict)


class _IlerlemeGeriCagrisi(cp_model.CpSolverSolutionCallback):
    """SDD 5.4: ara_cozum_geri_cagirma = FONKSIYON(ceza, gecen_sure): ..."""

    def __init__(self, geri_cagirma: Callable[[float, float], None] | None) -> None:
        super().__init__()
        self._geri_cagirma = geri_cagirma

    def on_solution_callback(self) -> None:
        if self._geri_cagirma is not None:
            self._geri_cagirma(self.objective_value, self.wall_time)


class CozucuAdaptoru:
    """Cozucu adaptoru: model kur (bkz. model_kurucu.model_kur), coz, sonucu dondur."""

    @staticmethod
    def coz(
        model: cp_model.CpModel,
        x: dict[XAnahtari, cp_model.IntVar],
        *,
        zaman_limiti_saniye: float,
        arama_iscisi_sayisi: int = 1,
        ara_cozum_geri_cagirma: Callable[[float, float], None] | None = None,
        ceza_terimleri: dict[str, Any] | None = None,
        kapsama_degiskenleri: dict[KapsamaAnahtari, Any] | None = None,
    ) -> CozumSonucu:
        cozucu = cp_model.CpSolver()
        cozucu.parameters.max_time_in_seconds = zaman_limiti_saniye
        cozucu.parameters.num_search_workers = arama_iscisi_sayisi
        geri_cagrisi = _IlerlemeGeriCagrisi(ara_cozum_geri_cagirma)
        durum = cozucu.solve(model, geri_cagrisi)

        if durum not in _UYGUN_DURUMLAR:
            return CozumSonucu(
                durum="cozum_yok",
                atanan_anahtarlar=frozenset(),
                toplam_ceza=None,
                sure_saniye=cozucu.wall_time,
            )

        atananlar = frozenset(anahtar for anahtar, degisken in x.items() if cozucu.value(degisken))
        ceza_dokumu = {
            kimlik: cozucu.value(terim) for kimlik, terim in (ceza_terimleri or {}).items()
        }
        kapsama_eksikleri = {
            anahtar: deger
            for anahtar, degisken in (kapsama_degiskenleri or {}).items()
            if (deger := cozucu.value(degisken)) > 0
        }
        return CozumSonucu(
            durum="optimal" if durum == cp_model.OPTIMAL else "uygun",
            atanan_anahtarlar=atananlar,
            toplam_ceza=cozucu.objective_value,
            sure_saniye=cozucu.wall_time,
            ceza_dokumu=ceza_dokumu,
            kapsama_eksikleri=kapsama_eksikleri,
        )
