#!/usr/bin/env python3
"""`docs/EK_B_UC_NOKTALAR.md`nin sayim ve kapi tarafini UYGULAMADAN uretir.

Ek B "uretilmistir" diyor; bu betik o sozu tutulabilir kilar. Uc nokta
listesi ile her ucun gectigi rol kapisi FastAPI yonlendirme tablosundan ve
`Depends` bagimliliklarindan okunur - elle sayilmaz. Islev sutunu duz metin
oldugu icin dokumanda elle durur; betigin isi, o dokumanin ARTIK var olmayan
ya da EKSIK kalan bir uc nokta listelemedigini gorunur kilmaktir.

Kullanim:
    python scripts/uc_noktalari_listele.py            # yol/yontem/rol tablosu
    python scripts/uc_noktalari_listele.py --denetle  # Ek B ile karsilastir

`--denetle`, dokumanda olmayan ya da dokumanda olup uygulamada bulunmayan
her satiri yazar ve fark varsa 1 ile cikar.
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.routing import APIRoute  # noqa: E402

from app.guvenlik import (  # noqa: E402
    calisan_yetkisi,
    oturum_baglami,
    yonetici_yetkisi,
    yonetim_yetkisi,
)
from app.main import app  # noqa: E402

EK_B = Path(__file__).resolve().parents[2] / "docs" / "EK_B_UC_NOKTALAR.md"

# Kapi fonksiyonu -> dokumanda yazan rol adi.
_KAPI_ADLARI = {
    yonetim_yetkisi: "yonetim",
    yonetici_yetkisi: "yonetici",
    calisan_yetkisi: "calisan",
    oturum_baglami: "giris yapmis her rol",
}

# Kimlik dogrulamasi olmayan uclar (SRS 5.10: giris ve saglik yoklamasi).
ACIK = "**yok** (acik)"


def _rol(rota: APIRoute) -> str:
    """Rotanin gectigi EN DAR kapi. Router duzeyindeki kapi da sayilir."""
    kapilar = {
        bagimlilik.call for bagimlilik in rota.dependant.dependencies if bagimlilik.call is not None
    }
    for kapi, ad in _KAPI_ADLARI.items():
        if kapi in kapilar:
            return ad
    return ACIK


def uc_noktalar() -> list[tuple[str, str, str]]:
    """(yol, yontem, rol) uclulerinin siralanmis listesi."""
    satirlar: list[tuple[str, str, str]] = []
    for rota in app.routes:
        if not isinstance(rota, APIRoute):
            continue
        rol = _rol(rota)
        for yontem in sorted(rota.methods - {"HEAD", "OPTIONS"}):
            satirlar.append((rota.path, yontem, rol))
    return sorted(satirlar)


def _belgedeki_uclar() -> set[tuple[str, str]]:
    """Ek B tablolarindaki (yol, yontem) ikilileri."""
    desen = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*([A-Z]+)\s*\|")
    bulunanlar: set[tuple[str, str]] = set()
    for satir in EK_B.read_text(encoding="utf-8").splitlines():
        eslesme = desen.match(satir)
        if eslesme:
            bulunanlar.add((eslesme.group(1), eslesme.group(2)))
    return bulunanlar


def main() -> int:
    ayristirici = argparse.ArgumentParser(description=__doc__)
    ayristirici.add_argument("--denetle", action="store_true", help="Ek B ile karsilastir")
    secenekler = ayristirici.parse_args()

    satirlar = uc_noktalar()
    if not secenekler.denetle:
        for yol, yontem, rol in satirlar:
            print(f"| `{yol}` | {yontem} | {rol} |")
        print(f"\nToplam {len(satirlar)} uc nokta.")
        return 0

    uygulamada = {(yol, yontem) for yol, yontem, _ in satirlar}
    belgede = _belgedeki_uclar()
    eksik = sorted(uygulamada - belgede)
    fazla = sorted(belgede - uygulamada)
    for yol, yontem in eksik:
        print(f"EKSIK  (uygulamada var, Ek B'de yok): {yontem} {yol}")
    for yol, yontem in fazla:
        print(f"FAZLA  (Ek B'de var, uygulamada yok): {yontem} {yol}")
    print(f"\nUygulama: {len(uygulamada)} uc nokta · Ek B: {len(belgede)} uc nokta")
    return 1 if (eksik or fazla) else 0


if __name__ == "__main__":
    raise SystemExit(main())
