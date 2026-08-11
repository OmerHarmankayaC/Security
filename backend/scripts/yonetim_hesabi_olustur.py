#!/usr/bin/env python3
"""Ilk yonetim hesabini acar (SRS FR-10.10; SDD 5.1b).

NEDEN BIR BETIK. Sistemin hic hesabi olmadigi bir an vardir ve o anda hesap
acan bir uc nokta BULUNMAZ - bulunsaydi, "hic hesap yoksa hesap acilabilir"
kurali arayuzde bir kapi olarak dururdu ve o kapinin kapali olup olmadigi
veritabanindaki satir sayisina baglanirdi. Bunun yerine ilk hesap, sunucuya
girebilen birinin calistirdigi bu betikle acilir. Kayit ekrani da yoktur
(FR-10.1): sonraki hesaplari yonetim rolu acar.

PAROLA ARGUMAN OLARAK ALINMAZ. Komut satirina yazilan parola kabuk
gecmisine (.bash_history / .zsh_history) ve calistigi surece `ps` ciktisina
duser; ikisi de baska kullanicilar tarafindan okunabilir. Parola yalnizca
etkilesimli olarak, ekrana yazilmadan sorulur.

Kullanim:
    python scripts/yonetim_hesabi_olustur.py
    python scripts/yonetim_hesabi_olustur.py --kullanici-adi omer
    python scripts/yonetim_hesabi_olustur.py --ilk-giriste-degistir

Sunucuda (ortam degiskenleri servis kullanicisina tasinarak):
    set -a; . /opt/vardiya/.env; set +a
    cd /opt/vardiya/backend
    sudo -u vardiya --preserve-env=VERITABANI_URL \\
        .venv/bin/python scripts/yonetim_hesabi_olustur.py
"""

import argparse
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.db import OturumYerel  # noqa: E402
from app.models.kimlik import Kullanici, Rol  # noqa: E402
from app.services.kullanici_servisi import KullaniciServisi  # noqa: E402
from app.services.parola import ASGARI_UZUNLUK  # noqa: E402

# Sistem yoneticisinin (yonetim rolu) varsayilan kullanici adi. Ingilizce ve
# sabit: bu hesabi acan kisi ile sonradan giren kisi cogu zaman ayni degildir
# ve "hangi adi vermistim" sorusu, parolasi bilinen ama adi hatirlanmayan bir
# hesap uretir. Kullanici adi bir sir degildir (giris ekrani onu zaten ele
# vermez, bkz. SDD 5.1b); tahmin edilebilir olmasi bir zayiflik degil.
VARSAYILAN_KULLANICI_ADI = "admin"


def yonetim_hesabi_var_mi(oturum) -> bool:  # noqa: ANN001 - Session
    """Aktif bir yonetim hesabi var mi?

    Pasif hesaplar sayilmaz: hepsi devre disi birakilmis bir sistemde
    kimse giremez ve betigin tam olarak o durumda calisabilmesi gerekir.
    """
    return (
        oturum.execute(
            select(Kullanici.kullanici_id).where(
                Kullanici.rol == Rol.YONETIM, Kullanici.aktif.is_(True)
            )
        ).first()
        is not None
    )


def hesap_ac(
    oturum,  # noqa: ANN001 - Session
    kullanici_adi: str,
    parola: str,
    *,
    ilk_giriste_degistir: bool = False,
) -> Kullanici:
    """Yonetim rolunde bir hesap acar.

    Dogrulama KullaniciServisi'nden gelir - kullanici adi deseni, parola
    kurali ve benzersizlik burada TEKRARLANMAZ. Tekrarlansaydi betikten
    acilan hesap, arayuzden acilandan farkli kurallara tabi olurdu ve
    ikisinin ayrismasi ancak bir kullanici giris yapamadiginda fark
    edilirdi.
    """
    servis = KullaniciServisi(oturum)
    kullanici = servis.olustur(kullanici_adi, parola, Rol.YONETIM)
    # Servis, yonetimin BASKASI icin actigi hesaba parola degistirme borcu
    # yukler (FR-10.7). Burada varsayilan olarak kaldirilir: parolayi yazan
    # kisi hesabin sahibidir, kendi sectigi parolayi ilk giriste yeniden
    # sectirmenin bir karsiligi yok. Kurulumu baskasi yapiyorsa
    # --ilk-giriste-degistir ile borc korunur.
    kullanici.parola_degistirmeli = ilk_giriste_degistir
    return kullanici


def _parolayi_sor() -> str | None:
    """Parolayi iki kez, ekrana yazmadan sorar. Uyusmazsa None doner."""
    parola = getpass.getpass("Parola: ")
    if len(parola) < ASGARI_UZUNLUK:
        print(f"HATA: Parola en az {ASGARI_UZUNLUK} karakter olmalidir.", file=sys.stderr)
        return None
    if parola != getpass.getpass("Parola (tekrar): "):
        print("HATA: Parolalar ayni degil.", file=sys.stderr)
        return None
    return parola


def main() -> int:
    ayristirici = argparse.ArgumentParser(
        description="Ilk yonetim hesabini acar (SRS FR-10.10).",
        epilog="Parola arguman olarak ALINMAZ; etkilesimli sorulur.",
    )
    ayristirici.add_argument(
        "--kullanici-adi",
        default=VARSAYILAN_KULLANICI_ADI,
        help=f"Hesabin kullanici adi (varsayilan: {VARSAYILAN_KULLANICI_ADI})",
    )
    ayristirici.add_argument(
        "--ilk-giriste-degistir",
        action="store_true",
        help=(
            "Parolayi hesabin sahibi degil de kurulumu yapan kisi yaziyorsa "
            "kullanin: hesap ilk giriste parola degistirmek zorunda kalir"
        ),
    )
    argumanlar = ayristirici.parse_args()

    if not sys.stdin.isatty():
        # getpass boru ardinda sessizce ilerler ve parola bos kalabilir;
        # ayrica bu betigin bir betikten cagrilmasi, parolanin bir yerde
        # duz metin durdugu anlamina gelir.
        print(
            "HATA: Bu betik etkilesimli bir terminal gerektirir "
            "(parola ekrana yazilmadan sorulur).",
            file=sys.stderr,
        )
        return 2

    oturum = OturumYerel()
    try:
        if yonetim_hesabi_var_mi(oturum):
            print(
                "Sistemde zaten aktif bir yonetim hesabi var.\n"
                "Yeni hesaplar Kullanicilar ekranindan acilir; bu betik ilk hesap icindir.",
                file=sys.stderr,
            )
            return 1

        kullanici_adi = argumanlar.kullanici_adi
        parola = _parolayi_sor()
        if parola is None:
            return 2

        try:
            kullanici = hesap_ac(
                oturum,
                kullanici_adi,
                parola,
                ilk_giriste_degistir=argumanlar.ilk_giriste_degistir,
            )
        except ValueError as hata:
            # KullaniciServisi ve parola kurali ayni taban tipten turer;
            # mesaj kullaniciya gosterilmek uzere yazilmistir.
            print(f"HATA: {hata}", file=sys.stderr)
            return 2

        oturum.commit()
        print(f"Yonetim hesabi acildi: {kullanici.kullanici_adi}")
        if kullanici.parola_degistirmeli:
            print("Hesap ilk giriste parola degistirmek zorunda.")
        return 0
    finally:
        oturum.close()


if __name__ == "__main__":
    raise SystemExit(main())
