"""Izin belgesi servisi: yukleme, okuma, silme.

BELGE SAGLIK VERISI OLABILIR. `musaitlik.tip` "rapor" oldugunda ekli dosya
bir doktor raporudur; okuma yetkisi bu yuzden kayit sahibine ve yonetici
tarafina sinirlidir (router). Servis katmani yetkiyi BILMEZ, yalnizca
icerigin kendisini dogrular.
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.girdi import Musaitlik, MusaitlikBelgesi

# KABUL EDILEN TIPLER BEYAZ LISTEDIR, kara liste degil. Tarayicida
# calisabilen bir tip (text/html, image/svg+xml) saklanip ayni tiple geri
# sunuldugunda depolanmis bir saldiri yuzeyi olur; hangi tiplerin zararsiz
# oldugunu saymak, hangilerinin zararli oldugunu saymaktan guvenlidir.
KABUL_EDILEN_TIPLER = frozenset({"image/png", "image/jpeg", "application/pdf"})

# Bes megabayt. Rapor goruntusu ve tek sayfalik PDF bunun cok altinda kalir;
# sinir, veritabanini tek bir yuklemeyle sisirmeye karsidir.
AZAMI_BAYT = 5 * 1024 * 1024


class BelgeTipiKabulEdilmediError(Exception):
    """Icerik tipi beyaz listede degil (router 415'e cevirir)."""


class BelgeCokBuyukError(Exception):
    """Icerik azami boyutu asiyor (router 413'e cevirir)."""


@dataclass(frozen=True)
class BelgeOzeti:
    dosya_adi: str
    icerik_tipi: str
    boyut_bayt: int


class BelgeServisi:
    def __init__(self, oturum: Session) -> None:
        self.oturum = oturum

    def getir(self, musaitlik_id: int) -> MusaitlikBelgesi | None:
        return self.oturum.execute(
            select(MusaitlikBelgesi).where(MusaitlikBelgesi.musaitlik_id == musaitlik_id)
        ).scalar_one_or_none()

    def yukle(
        self, musaitlik_id: int, dosya_adi: str, icerik_tipi: str, icerik: bytes
    ) -> MusaitlikBelgesi | None:
        """Belgeyi kaydeder; izin kaydi yoksa None doner.

        IKINCI YUKLEME USTUNE YAZAR. Tabloda bire bir kisit var; hata
        dondurmek yerine degistirmek, yanlis dosyayi secen kullaniciyi once
        silmeye zorlamamak icin.
        """
        if icerik_tipi not in KABUL_EDILEN_TIPLER:
            raise BelgeTipiKabulEdilmediError(icerik_tipi)
        if len(icerik) > AZAMI_BAYT:
            raise BelgeCokBuyukError(len(icerik))
        if self.oturum.get(Musaitlik, musaitlik_id) is None:
            return None

        mevcut = self.getir(musaitlik_id)
        if mevcut is None:
            mevcut = MusaitlikBelgesi(musaitlik_id=musaitlik_id)
            self.oturum.add(mevcut)
        mevcut.dosya_adi = dosya_adi
        mevcut.icerik_tipi = icerik_tipi
        mevcut.boyut_bayt = len(icerik)
        mevcut.icerik = icerik
        self.oturum.flush()
        return mevcut

    def sil(self, musaitlik_id: int) -> bool:
        belge = self.getir(musaitlik_id)
        if belge is None:
            return False
        self.oturum.delete(belge)
        self.oturum.flush()
        return True

    def belgesi_olan_izinler(self) -> set[int]:
        """Belgesi bulunan izin kimlikleri — LISTE ICIN TEK SORGU.

        Arayuz her satirda dugmeyi belgenin varligina gore cizer. Satir basina
        ayri sorgu (ya da indirme denemesi) otuz kayitlik bir listede otuz
        gidis donus ederdi.
        """
        return set(self.oturum.execute(select(MusaitlikBelgesi.musaitlik_id)).scalars().all())
