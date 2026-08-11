"""OR-Tools ile butun etkilesimi kapsayan dar arayuz (SDD 3.2, 3.4.3).

Sistemin geri kalani CP-SAT'i yalnizca bu modul uzerinden gorur: model kur
(model_kurucu.model_kur), coz, ara cozum bildir, sonucu dondur. Kutuphanenin
surum degisiklikleri veya cozucunun degistirilmesi yalnizca bu dosyayi
etkiler.

DURDURMA (SDD 5.4.2). Arama, cagiran tarafin ayri bir is parcaciginda
yurutulur (`AramaKolu`); durdurma istegi geldiginde `stop_search()`
CAGRILARAK arama disaridan sonlandirilir. Eski yol - istegi ara cozum geri
cagiriminda okumak - kaldirildi: geri cagirim yalnizca cozucu DAHA IYI bir
cozum buldugunda tetiklendigi icin istek iki iyilesme arasindaki
sessizlikte dakikalarca bekleyebiliyordu. Iki yol birlikte durmaz, biri
secilir (SDD 5.4.2).

Olculdu (11.08.2026, ortools 9.15.6755, 60x45x4 boyutlu bir model): arama
baska bir is parcaciginda yururken ana is parcacigindan yapilan
`stop_search()` cagrisi aramayi 0.02-0.05 saniye icinde sonlandirdi; son
iyilesmenin uzerinden 10 saniye gecmis olan olcumde de ayni. Elde edilen
cozum korunuyor (durum FEASIBLE).
"""

import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from ortools.sat.python import cp_model

from app.kurallar.temel import XAnahtari

_UYGUN_DURUMLAR = (cp_model.OPTIMAL, cp_model.FEASIBLE)

KapsamaAnahtari = tuple[date, int, int]


@dataclass(frozen=True, slots=True)
class Ilerleme:
    """Cozucunun o ana kadar buldugu en iyi cozumun ozeti (SDD 5.4)."""

    ceza: float
    gecen_sure: float


@dataclass(frozen=True, slots=True)
class CozumSonucu:
    durum: str  # "optimal" | "uygun" | "cozum_yok"
    atanan_anahtarlar: frozenset[XAnahtari]
    toplam_ceza: float | None
    sure_saniye: float
    # SDD 5.4: cozum.hedef_bazinda_ceza() ve cozum.eksik_degiskenleri.
    ceza_dokumu: dict[str, float] = field(default_factory=dict)
    kapsama_eksikleri: dict[KapsamaAnahtari, int] = field(default_factory=dict)
    # Arama, durdurma istegi geldigi icin sonlandirildi. Cagiran taraf
    # sonucu ATAMALARA degil `gecici_sonuc`a yazar ve kullanicinin kararini
    # bekler (SDD 5.4.1).
    durduruldu: bool = False


class _IlerlemeGeriCagrisi(cp_model.CpSolverSolutionCallback):
    """SDD 5.4: ara_cozum_geri_cagirma = FONKSIYON(ceza, gecen_sure): ...

    Ilerleme BELLEGE yazilir, veritabanina degil. Bu geri cagirim cozucunun
    kendi is parcaciginda calisir; SQLAlchemy oturumu ise is parcaciklari
    arasinda paylasilamaz. Veritabanina yazan taraf oturumun tek sahibi olan
    ana dongudur (SDD 5.4.2), o da ilerlemeyi buradan okur.
    """

    def __init__(self) -> None:
        super().__init__()
        self._kilit = threading.Lock()
        self._ilerleme: Ilerleme | None = None

    def on_solution_callback(self) -> None:
        with self._kilit:
            self._ilerleme = Ilerleme(ceza=self.objective_value, gecen_sure=self.wall_time)

    def son_ilerleme(self) -> Ilerleme | None:
        with self._kilit:
            return self._ilerleme


class AramaKolu:
    """Ayri bir is parcaciginda yuruyen arama; disaridan durdurulabilir.

    Kullanim (SDD 5.4.2'deki ana dongu):

        kol = CozucuAdaptoru.aramayi_baslat(...)
        while not kol.bekle(0.5):
            ilerleme = kol.son_ilerleme()   # istege bagli: kaydet
            if durdurma_istendi:
                kol.durdur()
        sonuc = kol.sonuc()

    Is parcacigi TEK bir surecin icinde kalir; surecler arasi iletisim yine
    yalnizca veritabani uzerindendir ve mimari degismez (SDD 3.4.4).
    """

    def __init__(
        self,
        model: cp_model.CpModel,
        x: dict[XAnahtari, cp_model.IntVar],
        *,
        zaman_limiti_saniye: float,
        arama_iscisi_sayisi: int = 1,
        ceza_terimleri: dict[str, Any] | None = None,
        kapsama_degiskenleri: dict[KapsamaAnahtari, Any] | None = None,
    ) -> None:
        self._model = model
        self._x = x
        self._ceza_terimleri = ceza_terimleri or {}
        self._kapsama_degiskenleri = kapsama_degiskenleri or {}
        self._cozucu = cp_model.CpSolver()
        self._cozucu.parameters.max_time_in_seconds = zaman_limiti_saniye
        self._cozucu.parameters.num_search_workers = arama_iscisi_sayisi
        self._geri_cagrisi = _IlerlemeGeriCagrisi()
        self._durduruldu = False
        self._sonuc: CozumSonucu | None = None
        self._hata: BaseException | None = None
        self._is_parcacigi = threading.Thread(
            target=self._calistir, name="cp-sat-arama", daemon=True
        )

    def basla(self) -> None:
        self._is_parcacigi.start()

    def bekle(self, saniye: float) -> bool:
        """Aramanin bitmesini en fazla `saniye` kadar bekler; bittiyse True."""
        self._is_parcacigi.join(timeout=saniye)
        return not self._is_parcacigi.is_alive()

    def durdur(self) -> None:
        """Aramayi DISARIDAN sonlandirir (SDD 5.4.2).

        Cagrildiktan sonra `solve` milisaniyeler icinde doner ve o ana kadar
        bulunmus en iyi cozum sonuca girer.
        """
        self._durduruldu = True
        self._cozucu.stop_search()

    def son_ilerleme(self) -> Ilerleme | None:
        return self._geri_cagrisi.son_ilerleme()

    def sonuc(self) -> CozumSonucu:
        """Aramanin sonucu. Arama bitmeden cagrilirsa hata verir."""
        if self._hata is not None:
            raise self._hata
        if self._sonuc is None:
            raise RuntimeError("Arama henuz bitmedi")
        return self._sonuc

    def _calistir(self) -> None:
        try:
            durum = self._cozucu.solve(self._model, self._geri_cagrisi)
            self._sonuc = self._sonucu_kur(durum)
        except BaseException as hata:  # noqa: BLE001 - ana donguye tasinir
            # Hata is parcaciginda yutulursa cagiran taraf sonsuza kadar
            # "arama suruyor" gorur; `sonuc()` bunu yeniden firlatir.
            self._hata = hata

    def _sonucu_kur(self, durum: int) -> CozumSonucu:
        cozucu = self._cozucu
        if durum not in _UYGUN_DURUMLAR:
            return CozumSonucu(
                durum="cozum_yok",
                atanan_anahtarlar=frozenset(),
                toplam_ceza=None,
                sure_saniye=cozucu.wall_time,
                durduruldu=self._durduruldu,
            )
        atananlar = frozenset(
            anahtar for anahtar, degisken in self._x.items() if cozucu.value(degisken)
        )
        ceza_dokumu = {
            kimlik: cozucu.value(terim) for kimlik, terim in self._ceza_terimleri.items()
        }
        kapsama_eksikleri = {
            anahtar: deger
            for anahtar, degisken in self._kapsama_degiskenleri.items()
            if (deger := cozucu.value(degisken)) > 0
        }
        return CozumSonucu(
            durum="optimal" if durum == cp_model.OPTIMAL else "uygun",
            atanan_anahtarlar=atananlar,
            toplam_ceza=cozucu.objective_value,
            sure_saniye=cozucu.wall_time,
            ceza_dokumu=ceza_dokumu,
            kapsama_eksikleri=kapsama_eksikleri,
            durduruldu=self._durduruldu,
        )


class CozucuAdaptoru:
    """Cozucu adaptoru: model kur (bkz. model_kurucu.model_kur), coz, sonucu dondur."""

    @staticmethod
    def aramayi_baslat(
        model: cp_model.CpModel,
        x: dict[XAnahtari, cp_model.IntVar],
        *,
        zaman_limiti_saniye: float,
        arama_iscisi_sayisi: int = 1,
        ceza_terimleri: dict[str, Any] | None = None,
        kapsama_degiskenleri: dict[KapsamaAnahtari, Any] | None = None,
    ) -> AramaKolu:
        """Aramayi ayri bir is parcaciginda baslatir ve kolunu dondurur."""
        kol = AramaKolu(
            model,
            x,
            zaman_limiti_saniye=zaman_limiti_saniye,
            arama_iscisi_sayisi=arama_iscisi_sayisi,
            ceza_terimleri=ceza_terimleri,
            kapsama_degiskenleri=kapsama_degiskenleri,
        )
        kol.basla()
        return kol

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
        """Aramayi baslatir ve BITENE KADAR bekler.

        Durdurma ihtiyaci olmayan cagiranlar icindir (testler, olcum
        betikleri). Cozum isi bunu kullanmaz: durdurmayi gecikmesiz
        uygulayabilmek icin kolu kendisi surer (SDD 5.4.2).
        """
        kol = CozucuAdaptoru.aramayi_baslat(
            model,
            x,
            zaman_limiti_saniye=zaman_limiti_saniye,
            arama_iscisi_sayisi=arama_iscisi_sayisi,
            ceza_terimleri=ceza_terimleri,
            kapsama_degiskenleri=kapsama_degiskenleri,
        )
        bildirilen: Ilerleme | None = None
        while not kol.bekle(0.05):
            if ara_cozum_geri_cagirma is None:
                continue
            ilerleme = kol.son_ilerleme()
            if ilerleme is not None and ilerleme != bildirilen:
                bildirilen = ilerleme
                ara_cozum_geri_cagirma(ilerleme.ceza, ilerleme.gecen_sure)
        return kol.sonuc()
