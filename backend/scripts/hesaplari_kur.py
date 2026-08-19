#!/usr/bin/env python3
"""Gercek kurulum icin hesaplari acar (SRS FR-10.6, FR-10.10, FR-10.13).

GECICI PAROLA BIR KEZ GOSTERILIR. Hicbir dosyaya yazilmaz, hicbir tabloda
saklanmaz ve yeniden okunamaz; kaybedilirse Kullanicilar ekranindan yeniden
sifirlanir. Otuz kisilik bir kadro icin parola listesi uretmek, o listeyi
sistemin en zayif noktasi yapardi.

CIKTI YONLENDIRILEMEZ. Betik, stdout bir terminale bagli degilse calismaz:
`> parolalar.txt` yazan bir kosum, tam da onlemek istedigimiz dosyayi
uretirdi.

Kullanim:
    python scripts/hesaplari_kur.py --sistem-yoneticisi omer
    python scripts/hesaplari_kur.py --calisanlar
    python scripts/hesaplari_kur.py --yukselt omer        # mevcut hesabi yukseltir
    python scripts/hesaplari_kur.py --durum               # yalniz sayim, parola uretmez
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.db import OturumYerel  # noqa: E402
from app.models.kimlik import Kullanici, Rol  # noqa: E402
from app.services.hesap_kurulumu import AcilanHesap, HesapKurulumu  # noqa: E402

_AYRAC = "─" * 72


def _ciktiyi_dogrula() -> bool:
    if sys.stdout.isatty():
        return True
    print(
        "HATA: Cikti bir terminale bagli degil. Bu betik gecici parola "
        "gosterir ve parola bir dosyaya YAZILMAMALIDIR (FR-10.13).",
        file=sys.stderr,
    )
    return False


def _yaz(acilanlar: list[AcilanHesap]) -> None:
    if not acilanlar:
        print("Acilan hesap yok.")
        return
    print(f"\n{_AYRAC}")
    print("GECICI PAROLALAR — BU EKRAN BIR KEZ GOSTERILIR")
    print("Parolalar hicbir yerde saklanmadi. Simdi dagitin; kaybolursa")
    print("Kullanicilar ekranindan yeniden sifirlayin.")
    print(_AYRAC)
    print(f"{'KULLANICI ADI':<18} {'GECICI PAROLA':<20} ROL / PERSONEL")
    for hesap in acilanlar:
        kime = hesap.ad_soyad or hesap.rol.value
        print(f"{hesap.kullanici_adi:<18} {hesap.gecici_parola:<20} {kime}")
    print(_AYRAC)
    print(f"{len(acilanlar)} hesap acildi. Hepsi ilk girise parola degistirecek.\n")


def main() -> int:
    ayristirici = argparse.ArgumentParser(description=__doc__)
    ayristirici.add_argument(
        "--calisanlar", action="store_true", help="Personel basina calisan hesabi"
    )
    ayristirici.add_argument(
        "--sistem-yoneticisi", metavar="ADI", help="Yeni sistem yoneticisi hesabi"
    )
    ayristirici.add_argument(
        "--hesap-yoneticisi", metavar="ADI", help="Yeni hesap yoneticisi hesabi"
    )
    ayristirici.add_argument("--idare", metavar="ADI", help="Yeni idare hesabi")
    ayristirici.add_argument(
        "--yukselt", metavar="ADI", help="Mevcut hesabi sistem yoneticisi yapar"
    )
    ayristirici.add_argument("--durum", action="store_true", help="Yalniz sayim gosterir")
    argumanlar = ayristirici.parse_args()

    oturum = OturumYerel()
    try:
        kurulum = HesapKurulumu(oturum)

        if argumanlar.durum:
            toplam = len(oturum.execute(select(Kullanici.kullanici_id)).scalars().all())
            print(f"Hesap sayisi: {toplam}")
            print(f"Etkin sistem yoneticisi: {kurulum.etkin_sistem_yoneticisi_sayisi()}")
            return 0

        if argumanlar.yukselt:
            hedef = oturum.execute(
                select(Kullanici).where(Kullanici.kullanici_adi == argumanlar.yukselt)
            ).scalar_one_or_none()
            if hedef is None:
                print(f"HATA: '{argumanlar.yukselt}' adinda hesap yok.", file=sys.stderr)
                return 1
            # Yukseltme PAROLA URETMEZ; mevcut hesabin parolasi degismez.
            hedef.rol = Rol.SISTEM_YONETICISI
            oturum.commit()
            print(f"'{hedef.kullanici_adi}' sistem yoneticisi yapildi.")
            return 0

        if not _ciktiyi_dogrula():
            return 2

        acilanlar: list[AcilanHesap] = []
        for ad, rol in (
            (argumanlar.sistem_yoneticisi, Rol.SISTEM_YONETICISI),
            (argumanlar.hesap_yoneticisi, Rol.HESAP_YONETICISI),
            (argumanlar.idare, Rol.IDARE),
        ):
            if ad:
                acilanlar.append(kurulum.yonetim_hesabi_ac(ad, rol))
        if argumanlar.calisanlar:
            acilanlar.extend(kurulum.calisan_hesaplari_ac())

        if not acilanlar and not argumanlar.calisanlar:
            ayristirici.print_help()
            return 1

        oturum.commit()
        _yaz(acilanlar)

        kalan = kurulum.etkin_sistem_yoneticisi_sayisi()
        if kalan == 0:
            print(
                "UYARI: Sistemde etkin sistem yoneticisi YOK. "
                "--sistem-yoneticisi ya da --yukselt ile bir hesap belirleyin "
                "(FR-10.12).",
                file=sys.stderr,
            )
        return 0
    except Exception:
        oturum.rollback()
        raise
    finally:
        oturum.close()


if __name__ == "__main__":
    raise SystemExit(main())
