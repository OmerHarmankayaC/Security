#!/usr/bin/env python3
"""`doktor_raporu_sablonu.png` uretir — demo verisinin ornek izin belgesi.

NEDEN BIR BETIK: depoya kaynagi olmayan bir ikili dosya birakmak, o dosyanin
nereden geldigini ve neyi gosterdigini bilinmez kilar. Bu betik goruntuyu
her calistirmada AYNI sekilde uretir; dosya degistiginde neyin degistigi
buradan okunur.

NEDEN PILLOW YOK: yalnizca bir yer tutucu goruntu icin derleme gerektiren
bir bagimlilik eklemek, dagitim yuzeyini bir kutuphane genisletir. PNG
bicimi dikduortgenler icin elle yazilabilecek kadar basittir (zlib + crc32
standart kutuphanede).

Kullanim:
    python scripts/ornek_belge_uret.py
"""

import struct
import zlib
from pathlib import Path

GENISLIK, YUKSEKLIK = 620, 877  # A4 orani

_BEYAZ = (255, 255, 255)
_KAGIT = (247, 246, 243)
_BASLIK = (26, 31, 38)
_METIN = (176, 174, 168)
_VURGU = (15, 110, 99)


def _dikdortgen(piksel: list[list[tuple[int, int, int]]], x: int, y: int, g: int, h: int, renk):  # noqa: ANN001, ANN202
    for satir in range(y, min(y + h, YUKSEKLIK)):
        for sutun in range(x, min(x + g, GENISLIK)):
            piksel[satir][sutun] = renk


def goruntuyu_kur() -> list[list[tuple[int, int, int]]]:
    """Bir rapor SAYFASI izlenimi: baslik bandi, metin satirlari, imza yeri.

    Gercek bir rapor DEGILDIR ve oyle gorunmemelidir - icinde okunabilir bir
    tibbi bilgi yoktur, yalnizca yerlesim vardir.
    """
    piksel = [[_KAGIT for _ in range(GENISLIK)] for _ in range(YUKSEKLIK)]
    _dikdortgen(piksel, 40, 40, GENISLIK - 80, YUKSEKLIK - 80, _BEYAZ)
    _dikdortgen(piksel, 40, 40, GENISLIK - 80, 70, _BASLIK)  # baslik bandi
    _dikdortgen(piksel, 70, 62, 150, 12, _BEYAZ)  # baslik yazisi yerine blok
    _dikdortgen(piksel, 70, 140, 220, 10, _VURGU)  # alt baslik
    y = 180
    for i in range(14):  # metin satirlari
        _dikdortgen(piksel, 70, y, GENISLIK - 140 - (60 if i % 4 == 3 else 0), 8, _METIN)
        y += 26
    _dikdortgen(piksel, 70, y + 40, 200, 8, _METIN)  # tarih
    _dikdortgen(piksel, GENISLIK - 250, y + 90, 180, 2, _BASLIK)  # imza cizgisi
    _dikdortgen(piksel, GENISLIK - 250, y + 100, 110, 8, _METIN)  # imza altindaki ad
    return piksel


def png_yaz(piksel: list[list[tuple[int, int, int]]], hedef: Path) -> None:
    ham = b"".join(
        b"\x00" + b"".join(struct.pack("BBB", *renk) for renk in satir) for satir in piksel
    )

    def parca(tur: bytes, veri: bytes) -> bytes:
        govde = tur + veri
        return struct.pack(">I", len(veri)) + govde + struct.pack(">I", zlib.crc32(govde))

    hedef.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + parca(b"IHDR", struct.pack(">IIBBBBB", GENISLIK, YUKSEKLIK, 8, 2, 0, 0, 0))
        + parca(b"IDAT", zlib.compress(ham, 9))
        + parca(b"IEND", b"")
    )


def main() -> int:
    hedef = (
        Path(__file__).resolve().parents[1] / "app" / "ornek_belgeler" / "doktor_raporu_sablonu.png"
    )
    hedef.parent.mkdir(parents=True, exist_ok=True)
    png_yaz(goruntuyu_kur(), hedef)
    print(f"{hedef} yazildi ({hedef.stat().st_size} bayt)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
