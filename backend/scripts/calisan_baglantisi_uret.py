#!/usr/bin/env python3
"""Personele verilecek kisiye ozel calisan paneli baglantisini yazdirir.

Anahtar personel_id'den sunucu sirriyla turetildigi icin (bkz.
app/services/calisan_baglantisi.py) elle hesaplanamaz; baglantiyi dagitmanin
yolu bu betiktir. Yonetici arayuzunde bir "baglantiyi kopyala" alani YOKTUR -
o bir urun karari oldugundan eklenmedi (bkz. PROGRESS.md, Gun 13 duzeltmeleri).

Kullanim:
    python scripts/calisan_baglantisi_uret.py            # butun aktif personel
    python scripts/calisan_baglantisi_uret.py 12 34      # yalniz bu kimlikler
    python scripts/calisan_baglantisi_uret.py --taban https://vardiya.ornek.gov.tr

Ciktidaki baglantilar kisiye ozeldir ve suresizdir; paylasan herkes o
personelin cizelgesini gorur. Toplu ciktinin dosyaya yazilmasi onerilmez.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.db import OturumYerel  # noqa: E402
from app.models.tanim import Personel  # noqa: E402
from app.services.calisan_baglantisi import baglanti_yolu  # noqa: E402


def main() -> int:
    ayristirici = argparse.ArgumentParser(description=__doc__)
    ayristirici.add_argument(
        "personel_idleri",
        nargs="*",
        type=int,
        help="Baglantisi uretilecek personel kimlikleri (bos birakilirsa tumu)",
    )
    ayristirici.add_argument(
        "--taban",
        default="",
        help="Baglantinin basina eklenecek adres (ornek: https://vardiya.ornek.gov.tr)",
    )
    argumanlar = ayristirici.parse_args()

    oturum = OturumYerel()
    try:
        stmt = select(Personel).order_by(Personel.sicil_no)
        if argumanlar.personel_idleri:
            stmt = stmt.where(Personel.personel_id.in_(argumanlar.personel_idleri))
        personeller = oturum.execute(stmt).scalars().all()
    finally:
        oturum.close()

    if not personeller:
        print("Eslesen personel bulunamadi.", file=sys.stderr)
        return 1

    for personel in personeller:
        taban = argumanlar.taban.rstrip("/")
        print(
            f"{personel.sicil_no}\t{personel.ad_soyad}\t{taban}{baglanti_yolu(personel.personel_id)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
