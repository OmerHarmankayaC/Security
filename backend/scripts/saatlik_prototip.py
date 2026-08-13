#!/usr/bin/env python3
"""Tur 5 Is 1 — saat eksenli modelin PERFORMANS SONDAJI (SAATLIK_MODEL_KARARLARI M7).

BU BIR OLCUM BETIGIDIR, TAM MODEL DEGILDIR. Amaci tek bir soruyu yanitlamak:
saat eksenli formulasyon K1 kabul kriterinin (kirk personel / yirmi sekiz gun,
altmis saniye) altinda kalabiliyor mu? Karar kurali tur promptunda yazili:
40 x 28 olceginde ILK UYGUN COZUME ulasma suresi otuz saniyeyi asiyorsa tam
uygulamaya gecilmez, once formulasyon gozden gecirilir.

Modelde yalnizca su vardir (SRS TD-13, H1, H9 ve 4.3 S1):

  z[p,s] ∈ {0,1}            p personeli s (MUTLAK) saatinde calisiyor
  x[p,s,n] ∈ {0,1}          … ve n gorev noktasinda
  Σ_n x[p,s,n] = z[p,s]
  bas[p,s]                  blok baslangici gostergesi
  Σ_{s ∈ gun d} bas[p,s] ≤ 1
  x[p,s,n] ≥ z[p,s] + x[p,s−1,n] − 1        nokta sabitligi
  blok_saat[p,d] ≥ asgari_blok_saat · bas_gun[p,d]
  blok_saat[p,d] ≤ azami_gunluk_saat
  S1: Σ_p x[p,s,n] + eksik[s,n] ≥ talep[s,n],  Σ_p x[p,s,n] − fazla[s,n] ≤ talep[s,n]

Diger kural EKLENMEZ; sondajin isi kisit YAPISININ maliyetini olcmektir.

## Formulasyondan iki sapma ve nedenleri

**1. Gunluk saat, DUVAR SAATI degil BLOGUN BASLADIGI GUNE yazilir.** SRS H1
ve H9 gunluk toplami `Σ_{s ∈ gun d} z[p,s]` diye yazar; H9'un metni ise ayni
paragrafta "gece yarisini asan blogun saatleri basladigi gune sayilir (TD-1);
ertesi gunun tavani bu saatlerle dolmaz" der. Ikisi ayni sey degildir ve
formulun duvar saati okunmasi iki kurali da bozar:

  - H9 blok uzunlugunu SINIRLAYAMAZ. 20.00–08.00 blogu duvar saatinde 4 + 8
    saattir; ikisi de on bir tavanin altinda kalir ve on iki saatlik blok
    gecer.
  - H1'in asgari suresi AKSAM BASLANGICLARINI YASAKLAR. 21.00'de baslayan
    bir blok o gune yalnizca uc saat birakir ve `≥ 4 · bas` kisiti duser —
    oysa gece kapsamasinin ihtiyac duydugu bloklar tam olarak bunlardir.

Metin normatiftir, gosterim kisaltmadir: "gun d" blogun sayildigi gundur.
Bu yuzden gun basina saat, devralinan saatler cikarilarak ve tasan saatler
eklenerek hesaplanir (`devir` gostergesi). Sondajin olctugu maliyet buna
DAHILDIR — tam uygulama da ayni yapiyi tasiyacak.

**2. H9 sondaja dahildir.** Prompt "diger kurallari ekleme" diyor; gunluk
tavan olmadan cozucu gunde yirmi dort saat calistirabilir, kapsama bedelsiz
kapanir ve olculen sure gercek modelin suresi olmaz. H9 ayrica SRS 3.3.1'de
asgari blok suresiyle AYNI uc parametreli cerceve icinde tanimli: alt sinir
ve ust sinir birlikte blogun cercevesini cizer.

Kullanim:
    python scripts/saatlik_prototip.py              # dort olcek
    python scripts/saatlik_prototip.py --json
    python scripts/saatlik_prototip.py --olcek 40x28
"""

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ortools.sat.python import cp_model  # noqa: E402

# SDD 3.4.3'teki referans deger; kabul_olcumu.py ile ayni sayi olmasi
# sonuclarin karsilastirilabilir kalmasi icindir.
ARAMA_ISCISI_SAYISI = 3
ZAMAN_LIMITI_SANIYE = 60.0

# SRS 3.3.5 / 3.3.1
ASGARI_BLOK_SAAT = 4
AZAMI_GUNLUK_SAAT = 11

# Gorev noktalari (SRS 3.3.3, Muracaat kaldirilmis hali)
SEFLIK = 0
GUVENLIK = 1

# SRS 3.3.4'teki talep matrisi — KIRK PERSONELLIK referans kadronun tam
# yuku (haftada 1.152 kisi-saat). Kucuk olcekler bu tabani P/40 ile
# olcekler; aksi halde on kisilik bir kadro kirk kisilik talebi karsilamaya
# calisir ve olculen sey cozum suresi degil kapsama acigi olur.
SEFLIK_GEREKEN = 1
GUVENLIK_HAFTA_ICI_GECE = 3  # 00.00–08.00
GUVENLIK_HAFTA_ICI_GUNDUZ = 9  # 08.00–24.00
GUVENLIK_HAFTA_SONU = 3  # 00.00–24.00


@dataclass(frozen=True, slots=True)
class Olcek:
    personel: int
    gun: int

    @property
    def ad(self) -> str:
        return f"{self.personel}x{self.gun}"

    @property
    def sef_sayisi(self) -> int:
        """Vardiya Sefligi noktasina erisebilen havuz.

        Alt sinir yapisaldir: nokta kesintisiz doldurulur (haftada 168
        kisi-saat) ve gunluk tavan on bir saattir, dolayisiyla 168/(7·11) ≈
        2,2 kisiden az bir havuz noktayi HICBIR cizelgeyle kapatamaz. Uc
        kisinin altina inilmemesi, sondajin kapsama acigi degil cozum suresi
        olcmesi icindir.
        """
        return max(3, round(7 * self.personel / 40))


@dataclass(slots=True)
class Sonuc:
    olcek: str
    personel: int
    gun: int
    degisken_sayisi: int
    ilk_uygun_saniye: float | None
    ilk_uygun_ceza: float | None
    toplam_saniye: float
    durum: str
    ceza: float | None
    kurma_saniye: float


class _IlkUygun(cp_model.CpSolverSolutionCallback):
    """Ilk uygun cozumun bulundugu ani kaydeder — karar kuralinin olctugu sayi."""

    def __init__(self) -> None:
        super().__init__()
        self.saniye: float | None = None
        self.ceza: float | None = None

    def on_solution_callback(self) -> None:
        if self.saniye is None:
            self.saniye = self.wall_time
            self.ceza = self.objective_value


def talep_uret(olcek: Olcek) -> dict[tuple[int, int], int]:
    """(mutlak_saat, nokta) -> gereken sayi. Gun 0 pazartesidir."""
    olcek_carpani = olcek.personel / 40

    def olcekli(taban: int) -> int:
        return max(1, round(taban * olcek_carpani))

    guvenlik_gece = olcekli(GUVENLIK_HAFTA_ICI_GECE)
    guvenlik_gunduz = olcekli(GUVENLIK_HAFTA_ICI_GUNDUZ)
    guvenlik_hafta_sonu = olcekli(GUVENLIK_HAFTA_SONU)

    talep: dict[tuple[int, int], int] = {}
    for gun in range(olcek.gun):
        hafta_sonu = gun % 7 >= 5
        for saat in range(24):
            s = gun * 24 + saat
            talep[(s, SEFLIK)] = SEFLIK_GEREKEN
            if hafta_sonu:
                talep[(s, GUVENLIK)] = guvenlik_hafta_sonu
            elif saat < 8:
                talep[(s, GUVENLIK)] = guvenlik_gece
            else:
                talep[(s, GUVENLIK)] = guvenlik_gunduz
    return talep


def model_kur(
    olcek: Olcek,
) -> tuple[cp_model.CpModel, int, dict[tuple[int, int, int], cp_model.IntVar]]:
    """Sondaj modelini kurar; (model, ikili degisken sayisi, x) dondurur."""
    model = cp_model.CpModel()
    talep = talep_uret(olcek)
    saatler = range(olcek.gun * 24)
    personel = range(olcek.personel)
    sefler = set(range(olcek.sef_sayisi))
    noktalar = (SEFLIK, GUVENLIK)

    def erisebilir(p: int, n: int) -> bool:
        """H8'in on elemesi: Seflik noktasinin on kosulu Vardiya Sefi yetkinligidir."""
        return n != SEFLIK or p in sefler

    z: dict[tuple[int, int], cp_model.IntVar] = {}
    x: dict[tuple[int, int, int], cp_model.IntVar] = {}
    for p in personel:
        for s in saatler:
            ulasilabilir = [n for n in noktalar if erisebilir(p, n) and talep.get((s, n), 0) > 0]
            # DEGISKEN ELEME (SDD 5.3): erisilebilir nokta yoksa o saat icin
            # z de uretilmez. Uretip sifire sabitlemek ayni sonucu verir ama
            # modeli gereksiz buyutur.
            if not ulasilabilir:
                continue
            z[(p, s)] = model.new_bool_var(f"z_{p}_{s}")
            for n in ulasilabilir:
                x[(p, s, n)] = model.new_bool_var(f"x_{p}_{s}_{n}")
            model.add(sum(x[(p, s, n)] for n in ulasilabilir) == z[(p, s)])

    def zv(p: int, s: int) -> cp_model.LinearExprT:
        return z.get((p, s), 0)

    # --- H1: blok baslangici, gunde tek baslangic, nokta sabitligi ---
    bas: dict[tuple[int, int], cp_model.IntVar] = {}
    for p in personel:
        for s in saatler:
            if (p, s) not in z:
                continue
            gosterge = model.new_bool_var(f"bas_{p}_{s}")
            model.add(gosterge >= zv(p, s) - zv(p, s - 1))
            model.add(gosterge <= zv(p, s))
            model.add(gosterge <= 1 - zv(p, s - 1))
            bas[(p, s)] = gosterge
        for gun in range(olcek.gun):
            gunun_baslangiclari = [
                bas[(p, s)] for s in range(gun * 24, gun * 24 + 24) if (p, s) in bas
            ]
            if gunun_baslangiclari:
                model.add(sum(gunun_baslangiclari) <= 1)

    for p in personel:
        for s in saatler:
            for n in noktalar:
                if (p, s, n) not in x or (p, s - 1, n) not in x:
                    continue
                model.add(x[(p, s, n)] >= zv(p, s) + x[(p, s - 1, n)] - 1)

    # --- Blogun basladigi gune yazilan saat (SRS TD-1) ---
    # devir[p,s] = "s saati calisilyor VE ONCEKI GUNDE baslamis bir bloga ait".
    # Gunun ilk saatinde: calisiliyor ama baslangic degilse devralinmistir.
    # Sonraki saatlerde: bir onceki saat devralinmissa ve bu saat de
    # calisiliyorsa (araya baslangic giremez, cunku z[s−1] = 1 iken
    # bas[s] = 0'dir) yine ayni blogun parcasidir.
    devir: dict[tuple[int, int], cp_model.IntVar] = {}
    for p in personel:
        for gun in range(olcek.gun):
            for saat in range(24):
                s = gun * 24 + saat
                if (p, s) not in z:
                    continue
                gosterge = model.new_bool_var(f"devir_{p}_{s}")
                if saat == 0:
                    model.add(gosterge == zv(p, s) - bas[(p, s)])
                else:
                    onceki = devir.get((p, s - 1), 0)
                    model.add(gosterge <= onceki)
                    model.add(gosterge <= zv(p, s))
                    model.add(gosterge >= onceki + zv(p, s) - 1)
                devir[(p, s)] = gosterge

    for p in personel:
        for gun in range(olcek.gun):
            gun_saatleri = range(gun * 24, gun * 24 + 24)
            devralinan = sum(devir.get((p, s), 0) for s in gun_saatleri)
            tasan = sum(devir.get((p, s), 0) for s in range(gun * 24 + 24, gun * 24 + 48))
            blok_saat = sum(zv(p, s) for s in gun_saatleri) - devralinan + tasan
            bas_gun = sum(bas[(p, s)] for s in gun_saatleri if (p, s) in bas)
            if not isinstance(blok_saat, int):
                model.add(blok_saat >= ASGARI_BLOK_SAAT * bas_gun)  # H1 asgari sure
                model.add(blok_saat <= AZAMI_GUNLUK_SAAT)  # H9

    # --- S1: saat bazinda kapsama (alt sinir esnek, ust sinir esnek) ---
    ceza_terimleri: list[cp_model.LinearExprT] = []
    for (s, n), gereken in talep.items():
        atanan = [x[(p, s, n)] for p in personel if (p, s, n) in x]
        atanan_ifadesi = sum(atanan) if atanan else 0
        eksik = model.new_int_var(0, gereken, f"eksik_{s}_{n}")
        model.add(atanan_ifadesi + eksik >= gereken)
        fazla = model.new_int_var(0, max(len(atanan), 1), f"fazla_{s}_{n}")
        model.add(atanan_ifadesi - fazla <= gereken)
        ceza_terimleri.append(1000 * eksik + 2 * fazla)
    model.minimize(sum(ceza_terimleri))

    return model, len(z) + len(x) + len(bas) + len(devir), x


def bloklari_denetle(
    olcek: Olcek, cozucu: cp_model.CpSolver, x: dict[tuple[int, int, int], cp_model.IntVar]
) -> list[str]:
    """Cikan cozumun H1/H9'a uydugunu SONUCTAN dogrular.

    Sondaj hizli cozuyorsa iki aciklama vardir: formulasyon ucuzdur ya da
    kisit yanlis yazildigi icin model gercekte kolaydir. Ikisini ayirmanin
    tek yolu cikan cizelgeye bakmaktir.
    """
    calisilan: dict[int, dict[int, int]] = {}
    for (p, s, n), degisken in x.items():
        if cozucu.value(degisken):
            calisilan.setdefault(p, {})[s] = n

    bulgular: list[str] = []
    for p in sorted(calisilan):
        saatler = sorted(calisilan[p])
        bloklar: list[list[int]] = []
        for s in saatler:
            if bloklar and bloklar[-1][-1] == s - 1:
                bloklar[-1].append(s)
            else:
                bloklar.append([s])
        gun_basina: dict[int, int] = {}
        for blok in bloklar:
            gun = blok[0] // 24
            gun_basina[gun] = gun_basina.get(gun, 0) + 1
            if len(blok) < ASGARI_BLOK_SAAT:
                bulgular.append(f"p{p} gun{gun}: blok {len(blok)} saat (asgari {ASGARI_BLOK_SAAT})")
            if len(blok) > AZAMI_GUNLUK_SAAT:
                bulgular.append(f"p{p} gun{gun}: blok {len(blok)} saat (azami {AZAMI_GUNLUK_SAAT})")
            if len({calisilan[p][s] for s in blok}) > 1:
                bulgular.append(f"p{p} gun{gun}: blok icinde nokta degisti")
        for gun, sayi in gun_basina.items():
            if sayi > 1:
                bulgular.append(f"p{p} gun{gun}: {sayi} blok (en fazla 1)")
    gece_asan = sum(
        1 for p in calisilan for s in calisilan[p] if s % 24 == 23 and (s + 1) in calisilan[p]
    )
    bulgular.append(f"bilgi: gece yarisini asan blok sayisi = {gece_asan}")
    return bulgular


def olc(olcek: Olcek, *, zaman_limiti: float, denetle: bool = False) -> Sonuc:
    import time as zaman

    kurma_basi = zaman.perf_counter()
    model, degisken_sayisi, x = model_kur(olcek)
    kurma_saniye = zaman.perf_counter() - kurma_basi

    cozucu = cp_model.CpSolver()
    cozucu.parameters.max_time_in_seconds = zaman_limiti
    cozucu.parameters.num_search_workers = ARAMA_ISCISI_SAYISI
    geri_cagirim = _IlkUygun()
    durum = cozucu.solve(model, geri_cagirim)

    uygun = durum in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    if denetle and uygun:
        for satir in bloklari_denetle(olcek, cozucu, x):
            print(f"  denetim {olcek.ad}: {satir}", file=sys.stderr)
    return Sonuc(
        olcek=olcek.ad,
        personel=olcek.personel,
        gun=olcek.gun,
        degisken_sayisi=degisken_sayisi,
        ilk_uygun_saniye=geri_cagirim.saniye,
        ilk_uygun_ceza=geri_cagirim.ceza,
        toplam_saniye=cozucu.wall_time,
        durum={cp_model.OPTIMAL: "optimal", cp_model.FEASIBLE: "uygun"}.get(durum, "cozum_yok"),
        ceza=cozucu.objective_value if uygun else None,
        kurma_saniye=kurma_saniye,
    )


OLCEKLER = (Olcek(10, 7), Olcek(20, 14), Olcek(30, 28), Olcek(40, 28))
KARAR_ESIGI_SANIYE = 30.0


def main() -> int:
    ayristirici = argparse.ArgumentParser(description=__doc__)
    ayristirici.add_argument("--json", action="store_true", help="makine okunur cikti")
    ayristirici.add_argument("--olcek", help="yalniz bu olcegi kos (orn. 40x28)")
    ayristirici.add_argument(
        "--zaman-limiti", type=float, default=ZAMAN_LIMITI_SANIYE, help="cozucu ust sinir (sn)"
    )
    ayristirici.add_argument(
        "--denetle", action="store_true", help="cikan bloklari H1/H9'a karsi denetle"
    )
    argumanlar = ayristirici.parse_args()

    olcekler = [o for o in OLCEKLER if argumanlar.olcek in (None, o.ad)]
    if not olcekler:
        print(f"Bilinmeyen olcek: {argumanlar.olcek}", file=sys.stderr)
        return 2

    sonuclar = [
        olc(o, zaman_limiti=argumanlar.zaman_limiti, denetle=argumanlar.denetle) for o in olcekler
    ]

    if argumanlar.json:
        print(json.dumps([s.__dict__ for s in sonuclar], indent=2, ensure_ascii=False))
    else:
        print(f"{'Olcek':>8} {'Degisken':>9} {'Kurma':>7} {'Ilk uygun':>10} {'Toplam':>8}  Durum")
        for s in sonuclar:
            ilk = f"{s.ilk_uygun_saniye:.2f} sn" if s.ilk_uygun_saniye is not None else "—"
            print(
                f"{s.olcek:>8} {s.degisken_sayisi:>9} {s.kurma_saniye:>6.2f}s "
                f"{ilk:>10} {s.toplam_saniye:>7.2f}s  {s.durum} (ceza={s.ceza})"
            )

    referans = next((s for s in sonuclar if s.olcek == "40x28"), None)
    if referans is None:
        return 0
    if referans.ilk_uygun_saniye is None or referans.ilk_uygun_saniye > KARAR_ESIGI_SANIYE:
        print(
            f"\nKARAR: 40x28 olceginde ilk uygun cozum {KARAR_ESIGI_SANIYE:.0f} saniyeyi asti. "
            "Tam uygulamaya gecilmeden formulasyon gozden gecirilmeli "
            "(once nokta surekliligi kisiti).",
            file=sys.stderr,
        )
        return 1
    print(
        f"\nKARAR: 40x28 olceginde ilk uygun cozum {referans.ilk_uygun_saniye:.2f} sn — "
        f"esik {KARAR_ESIGI_SANIYE:.0f} sn asilmadi, tam uygulamaya gecilebilir."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
