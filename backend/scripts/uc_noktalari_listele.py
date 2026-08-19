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
    python scripts/uc_noktalari_listele.py --yaz      # Ek B'yi yerinde tazele

`--denetle`, dokumanda olmayan ya da dokumanda olup uygulamada bulunmayan
her satiri yazar ve fark varsa 1 ile cikar.

`--yaz`, tablolari yonlendirme tablosundan yeniden kurar. ISLEV METNI
KORUNUR: her (yol, yontem) icin dokumanda yazan islev metni tasinir, yeni
bir uc nokta icin `TANIMLANACAK` birakilir ve insan doldurur. Boylece
"uretilmistir" sozu tutulur ama elle yazilan sutun kaybolmaz. Toplam sayi
ve kapi basina ozet tablosu da yeniden hesaplanir - bunlar elle
guncellendiginde geride kaliyordu (dokumanda 68 yaziyorken 70 satir vardi).
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.routing import APIRoute  # noqa: E402

from app.guvenlik import (  # noqa: E402
    calisan_yetkisi,
    hesap_yonetimi_yetkisi,
    idare_yetkisi,
    oturum_baglami,
    sistem_yoneticisi_yetkisi,
)
from app.main import app  # noqa: E402

EK_B = Path(__file__).resolve().parents[2] / "docs" / "EK_B_UC_NOKTALAR.md"

# Kapi fonksiyonu -> dokumanda yazan rol adi.
_KAPI_ADLARI = {
    # SIRA ONEMLI: en dar kapi once aranir (bkz. `_rol`).
    sistem_yoneticisi_yetkisi: "sistem_yoneticisi",
    hesap_yonetimi_yetkisi: "hesap_yoneticisi + sistem_yoneticisi",
    # ROLLER KAPSAYICIDIR (SRS 5.10): yonetim, yoneticinin kapisindan da
    # gecer. Belge bunu boyle yazar ve etiket TEK YERDE durur - betik
    # "yonetici" yazip belge "yonetici + yonetim" yazdiginda, --denetle
    # yalniz (yol, yontem) karsilastirdigi icin fark gorunmez kalirdi.
    idare_yetkisi: "idare ve ustu",
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


ISLEV_YOKSA = "TANIMLANACAK"


def _belgedeki_islevler() -> dict[tuple[str, str], str]:
    """(yol, yontem) -> elle yazilmis islev metni."""
    desen = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*([A-Z]+)\s*\|[^|]*\|\s*(.*?)\s*\|\s*$")
    islevler: dict[tuple[str, str], str] = {}
    for satir in EK_B.read_text(encoding="utf-8").splitlines():
        eslesme = desen.match(satir)
        if eslesme:
            islevler[(eslesme.group(1), eslesme.group(2))] = eslesme.group(3)
    return islevler


def _belgedeki_uclar() -> set[tuple[str, str]]:
    """Ek B tablolarindaki (yol, yontem) ikilileri."""
    desen = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*([A-Z]+)\s*\|")
    bulunanlar: set[tuple[str, str]] = set()
    for satir in EK_B.read_text(encoding="utf-8").splitlines():
        eslesme = desen.match(satir)
        if eslesme:
            bulunanlar.add((eslesme.group(1), eslesme.group(2)))
    return bulunanlar


_SATIR = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*([A-Z]+)\s*\|")


def _satir_yaz(yol_: str, yontem: str, rol: str, islev: str) -> str:
    return f"| `{yol_}` | {yontem} | {rol} | {islev} |"


def _tazele(satirlar: list[tuple[str, str, str]]) -> tuple[list[str], list[str]]:
    """Ek B'yi yerinde tazeler. Doner: (yeni satirlar, uyarilar).

    Belge TEK tablo degil; uc noktalar bolumlere ayrilmis birden cok tabloda
    durur. Bu yuzden tablolar yeniden KURULMAZ, yerinde guncellenir: var olan
    her satirin rolu uygulamadan tazelenir, eksik uc nokta ise yolu en cok
    benzeyen satirin yanina SIRALI olarak sokulur. Boylece bolumlendirme
    korunur ve islev sutunu kaybolmaz.
    """
    islevler = _belgedeki_islevler()
    uygulamada = {(y, m_): r for y, m_, r in satirlar}
    metin = EK_B.read_text(encoding="utf-8").splitlines()
    uyarilar: list[str] = []

    # 1) Var olan satirlarin rolunu tazele, uygulamada olmayanlari isaretle.
    cikti: list[str] = []
    belgede: set[tuple[str, str]] = set()
    for satir in metin:
        e = _SATIR.match(satir)
        if not e:
            cikti.append(satir)
            continue
        anahtar = (e.group(1), e.group(2))
        belgede.add(anahtar)
        if anahtar not in uygulamada:
            uyarilar.append(f"belgede var, uygulamada YOK: {e.group(2)} {e.group(1)}")
            cikti.append(satir)
            continue
        cikti.append(_satir_yaz(*anahtar, uygulamada[anahtar], islevler.get(anahtar, ISLEV_YOKSA)))

    # 2) Eksik uc noktalari, yolu en cok benzeyen satirin bulundugu tabloya
    #    sirali olarak sok.
    for anahtar in sorted(set(uygulamada) - belgede):
        yol_, yontem = anahtar
        aday = None
        for i, satir in enumerate(cikti):
            e = _SATIR.match(satir)
            if e and _ortak_onek(e.group(1), yol_) > 0 and (e.group(1), e.group(2)) > anahtar:
                aday = i
                break
        if aday is None:
            uyarilar.append(f"yeri bulunamadi, elle eklenmeli: {yontem} {yol_}")
            continue
        cikti.insert(aday, _satir_yaz(yol_, yontem, uygulamada[anahtar], ISLEV_YOKSA))

    # 3) Toplam sayi ve kapi basina ozet — elle guncellendiginde geride
    #    kaliyorlardi (68 yaziyordu, 70 satir vardi).
    cikti = _sayilari_tazele(cikti, satirlar)
    return cikti, uyarilar


def _ortak_onek(a: str, b: str) -> int:
    """Iki yolun ortak bolum sayisi: /api/calisan/x ile /api/calisan/y -> 2."""
    pa, pb = a.strip("/").split("/"), b.strip("/").split("/")
    ortak = 0
    for x, y in zip(pa, pb, strict=False):
        if x != y:
            break
        ortak += 1
    return ortak


def _sayilari_tazele(metin: list[str], satirlar: list[tuple[str, str, str]]) -> list[str]:
    """Toplam sayiyi ve OZET TABLOSUNU yeniden kurar.

    Ozet tablosu satir satir guncellenemez: kapi adlari degistiginde (uc
    rolden dorde gecerken oldugu gibi) eski etiketler tabloda kalir ve yeni
    olanlar hic eklenmez. Tablonun govdesi bu yuzden tamamen degistirilir.
    """
    from collections import Counter

    sayac = Counter(rol for _, _, rol in satirlar)
    cikti: list[str] = []
    ozet_govdesinde = False
    for satir in metin:
        if satir.startswith("**Toplam ") and "uç nokta" in satir:
            satir = re.sub(
                r"\*\*Toplam \d+ uç nokta\.\*\*",
                f"**Toplam {len(satirlar)} uç nokta.**",
                satir,
            )
            cikti.append(satir)
            continue
        if satir.startswith("| Kapı |"):
            ozet_govdesinde = True
            cikti.append(satir)
            continue
        if ozet_govdesinde:
            if satir.startswith("| --- |"):
                cikti.append(satir)
                # Govde: en cok uc noktali kapi ustte.
                for kapi, adet in sayac.most_common():
                    cikti.append(f"| {kapi} | {adet} |")
                continue
            if satir.startswith("|"):
                continue  # eski govde satiri — atilir
            ozet_govdesinde = False
        cikti.append(satir)
    return cikti


def main() -> int:
    ayristirici = argparse.ArgumentParser(description=__doc__)
    ayristirici.add_argument("--denetle", action="store_true", help="Ek B ile karsilastir")
    ayristirici.add_argument("--yaz", action="store_true", help="Ek B'yi yerinde tazele")
    secenekler = ayristirici.parse_args()

    satirlar = uc_noktalar()
    if secenekler.yaz:
        yeni, uyarilar = _tazele(satirlar)
        EK_B.write_text("\n".join(yeni) + "\n", encoding="utf-8")
        for uyari in uyarilar:
            print(f"UYARI  {uyari}")
        print(f"{EK_B.name} tazelendi: {len(satirlar)} uc nokta.")
        # ISLEV_YOKSA birakilan satirlar insan bekler; sessizce gecilmez.
        bekleyen = sum(1 for s in yeni if s.endswith(f"| {ISLEV_YOKSA} |"))
        if bekleyen:
            print(f"UYARI  {bekleyen} satirin islev metni {ISLEV_YOKSA} — elle doldurulmali.")
        return 1 if uyarilar or bekleyen else 0

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
