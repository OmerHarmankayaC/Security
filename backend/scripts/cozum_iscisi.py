#!/usr/bin/env python3
"""Cozum iscisi: kuyruktaki cozum islerini alip calistiran servis (SDD 3.4.4).

Uygulama sunucusu (uvicorn) yalnizca istek isler ve `CozumServisi.baslat`
ile isi `kuyrukta` durumunda birakir. Bu surec o kuyrugu yoklar, bir isi
kapar ve `cozum_isini_calistir` ile yurutur. Iki surec arasinda dogrudan
iletisim yoktur; tek sozlesme veritabanidir. Bu sayede iscinin beklenmedik
sekilde sonlanmasi uygulama sunucusunu etkilemez ve isci ileride ayri bir
makineye tasinabilir.

Kullanim:
    python scripts/cozum_iscisi.py                 # servis dongusu
    python scripts/cozum_iscisi.py --tek-adim      # bir is isle ve cik

Yerel gelistirmede API'nin yani sira BU SURECIN DE calismasi gerekir;
calismazsa cozum istekleri kuyrukta bekler. Gelistirme ile sunucu ayni
yolu kullanir (bkz. README.md, Deployment).
"""

import argparse
import logging
import signal
import sys
import time as zaman
from pathlib import Path
from types import FrameType

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db import OturumYerel  # noqa: E402
from app.services.cozum_servisi import cozum_isini_calistir  # noqa: E402

_YOKLAMA_ARALIGI_SANIYE = 2.0

gunlukcu = logging.getLogger("cozum_iscisi")


class _KapanmaIstegi:
    """SIGTERM/SIGINT bayragi.

    systemd `stop` verdiginde surdurulen is YARIDA KESILMEZ: bayrak
    kaldirilir, eldeki is normal sekilde tamamlanir ve dongu ondan sonra
    cikar. Yarim bir cizelge yazmak, kural ihlali icermeyen ama kapsamasi
    eksik bir cizelgeden ayirt edilemeyecegi icin yaniltici olurdu
    (SDD 5.4). Unit dosyasindaki TimeoutStopSec bu yuzden zaman limitinden
    genis tutulur.
    """

    def __init__(self) -> None:
        self.istendi = False

    def isle(self, isaret: int, _cerceve: FrameType | None) -> None:
        self.istendi = True
        gunlukcu.info("Kapanma istegi alindi (%s); eldeki is bitince cikilacak.", isaret)


def siradaki_isi_kap(oturum: Session) -> int | None:
    """Kuyruktaki bir isi ATOMIK olarak kapar ve is_id'sini dondurur.

    `UPDATE ... WHERE durum='kuyrukta' ... RETURNING`, iki iscinin ayni isi
    almasini engeller: durum degisikligi ile secim tek ifadede olur.
    Ic sorgudaki FOR UPDATE SKIP LOCKED, es zamanli iscilerin ayni satirda
    bloke olmak yerine bir sonraki ise gecmesini saglar.

    Isi dogrudan ON_KONTROL'e cekmek, ayni zamanda "bu is sahiplenildi"
    demektir; boylece ayri bir sahiplik sutununa gerek kalmaz.
    """
    sonuc = oturum.execute(
        text("""
            UPDATE cozum_isi
               SET durum = 'ON_KONTROL'
             WHERE is_id = (
                   SELECT is_id
                     FROM cozum_isi
                    WHERE durum = 'KUYRUKTA'
                    ORDER BY is_id
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
             )
         RETURNING is_id
        """)
    ).scalar_one_or_none()
    oturum.commit()
    return sonuc


def siradaki_isi_isle(oturum: Session) -> int | None:
    """Kuyruktan BIR is alir ve calistirir; is yoksa None doner.

    Dongu bu fonksiyonun etrafinda kurulur. Testler de bunu dogrudan
    cagirir - surec acilmadigi icin davranis belirlenimlidir.
    """
    is_id = siradaki_isi_kap(oturum)
    if is_id is None:
        return None
    gunlukcu.info("Is %s alindi.", is_id)
    try:
        cozum_isini_calistir(oturum, is_id)
    except Exception:
        # Tek bir isin cokmesi isciyi dusurmemeli; is kaydi veritabaninda
        # kaldigi icin durum incelenebilir (SDD 3.4.4).
        oturum.rollback()
        gunlukcu.exception("Is %s calistirilirken hata olustu.", is_id)
    else:
        gunlukcu.info("Is %s tamamlandi.", is_id)
    return is_id


def dongu(kapanma: _KapanmaIstegi, *, yoklama_araligi: float) -> None:
    oturum = OturumYerel()
    try:
        while not kapanma.istendi:
            try:
                islenen = siradaki_isi_isle(oturum)
            except Exception:
                oturum.rollback()
                gunlukcu.exception("Kuyruk yoklanirken hata olustu.")
                islenen = None
            if islenen is None:
                # Bos kuyrukta bekleme; kapanma istegine hizli yanit
                # verebilmek icin tek uzun uyku yerine kucuk dilimler.
                bitis = zaman.monotonic() + yoklama_araligi
                while not kapanma.istendi and zaman.monotonic() < bitis:
                    zaman.sleep(0.1)
    finally:
        oturum.close()
    gunlukcu.info("Cozum iscisi kapandi.")


def main() -> int:
    ayristirici = argparse.ArgumentParser(description=__doc__)
    ayristirici.add_argument(
        "--tek-adim",
        action="store_true",
        help="Kuyruktan bir is isle ve cik (is yoksa hicbir sey yapmadan cikar)",
    )
    ayristirici.add_argument(
        "--yoklama-araligi",
        type=float,
        default=_YOKLAMA_ARALIGI_SANIYE,
        help=f"Bos kuyrukta bekleme suresi, saniye (varsayilan {_YOKLAMA_ARALIGI_SANIYE})",
    )
    argumanlar = ayristirici.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if argumanlar.tek_adim:
        oturum = OturumYerel()
        try:
            return 0 if siradaki_isi_isle(oturum) is not None else 1
        finally:
            oturum.close()

    kapanma = _KapanmaIstegi()
    signal.signal(signal.SIGTERM, kapanma.isle)
    signal.signal(signal.SIGINT, kapanma.isle)
    gunlukcu.info("Cozum iscisi basladi.")
    dongu(kapanma, yoklama_araligi=argumanlar.yoklama_araligi)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
