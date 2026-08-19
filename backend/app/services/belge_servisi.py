"""Izin belgesi servisi: yukleme, okuma, silme (SDD 5.10; SRS FR-2.7, TD-17).

BELGE SAGLIK VERISI OLABILIR. Servis katmani YETKI BILMEZ; erisim denetimi
indirme yolunun icindedir (routers/belge.py) cunku ayrim rolde degil kaydin
SAHIPLIGINDEDIR: calisan kendi kaydina erisebilir, baskasininkine
erisemez. Bu katmanin isi icerigin kendisini dogrulamaktir.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.girdi import Musaitlik

# KABUL EDILEN TIPLER BEYAZ LISTEDIR, kara liste degil. Tarayicida
# calisabilen bir tip (text/html, image/svg+xml) saklanip ayni tiple geri
# sunuldugunda depolanmis bir saldiri yuzeyi olur; hangi tiplerin zararsiz
# oldugunu saymak, hangilerinin zararli oldugunu saymaktan guvenlidir.
KABUL_EDILEN_TIPLER = frozenset({"image/png", "image/jpeg", "application/pdf"})

# Bes megabayt. Rapor goruntusu ve tek sayfalik PDF bunun cok altinda kalir;
# sinir, veritabanini tek bir yuklemeyle sisirmeye karsidir.
AZAMI_BAYT = 5 * 1024 * 1024

# TIP ICERIKTEN OKUNUR, UZANTIDAN DEGIL (SDD 5.10). Uzanti da, tarayicinin
# gonderdigi `Content-Type` de kullanici girdisidir: "rapor.png" adiyla
# gonderilen bir HTML dosyasi, ada guvenildiginde image/png olarak saklanir
# ve indirilirken ayni tiple sunulur. Imza baytlari icerigin kendisidir.
_IMZALAR: tuple[tuple[bytes, str], ...] = (
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"%PDF-", "application/pdf"),
)


class BelgeTipiKabulEdilmediError(Exception):
    """Icerik imzasi beyaz listede degil (router 415'e cevirir)."""


class BelgeCokBuyukError(Exception):
    """Icerik azami boyutu asiyor (router 413'e cevirir)."""


@dataclass(frozen=True)
class BelgeOzeti:
    dosya_adi: str
    icerik_tipi: str
    boyut_bayt: int


def icerikten_tipi_belirle(icerik: bytes) -> str | None:
    """Baslangic baytlarindan MIME tipi; taninmiyorsa None."""
    for imza, tip in _IMZALAR:
        if icerik.startswith(imza):
            return tip
    return None


class BelgeServisi:
    def __init__(self, oturum: Session) -> None:
        self.oturum = oturum

    def kaydi_getir(self, musaitlik_id: int) -> Musaitlik | None:
        return self.oturum.get(Musaitlik, musaitlik_id)

    def yukle(self, musaitlik_id: int, dosya_adi: str, icerik: bytes) -> Musaitlik | None:
        """Belgeyi kaydeder; izin kaydi yoksa None doner.

        `icerik_tipi` PARAMETRE DEGILDIR: istemcinin bildirdigi tipe
        guvenilmez, imzadan okunur.

        IKINCI YUKLEME USTUNE YAZAR. Kayit basina tek dosya; hata dondurmek
        yerine degistirmek, yanlis dosyayi secen kullaniciyi once silmeye
        zorlamamak icin.
        """
        if len(icerik) > AZAMI_BAYT:
            raise BelgeCokBuyukError(len(icerik))
        tip = icerikten_tipi_belirle(icerik)
        if tip is None or tip not in KABUL_EDILEN_TIPLER:
            raise BelgeTipiKabulEdilmediError(tip or "taninmayan")

        kayit = self.kaydi_getir(musaitlik_id)
        if kayit is None:
            return None
        kayit.belge_adi = dosya_adi
        kayit.belge_tipi = tip
        kayit.belge_boyut = len(icerik)
        kayit.belge_icerik = icerik
        self.oturum.flush()
        return kayit

    def sil(self, musaitlik_id: int) -> bool:
        kayit = self.kaydi_getir(musaitlik_id)
        if kayit is None or kayit.belge_icerik is None:
            return False
        kayit.belge_adi = None
        kayit.belge_tipi = None
        kayit.belge_boyut = None
        kayit.belge_icerik = None
        self.oturum.flush()
        return True
