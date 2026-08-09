"""Giris denemelerinin ve hesap yonetimi islemlerinin kaydi (SRS FR-10.9).

NE KAYDEDILIR. Olayin turu, ilgili kullanici adi, rol ve islemi yapan kisi.
Zaman damgasi bicimlendiricinin isi (asagida).

NE KAYDEDILMEZ. Parola, parola ozeti, oturum belirteci ve belirtecin ozeti.
Kayitlar sistem gunlugune yazilir ve gunlugu okuyabilen herkes onlari gorur;
oraya yazilan bir sir artik sir degildir. Bu yuzden kaydin aldigi degerler
cagri yerlerinde tek tek secilir, "ne varsa yaz" diye bir yol birakilmaz.

BICIM. `anahtar=deger` ciftleri. Insan tarafindan okunabilir ve `journalctl
-u vardiya-api | grep olay=giris_basarisiz` gibi bir komutla suzulebilir;
ayri bir kayit altyapisi (JSON, harici toplayici) bu olcekte tasidigindan
fazla parca olurdu.
"""

import logging
import re
import sys

_KAYITCI_ADI = "vardiya"
_kayitci = logging.getLogger(f"{_KAYITCI_ADI}.kimlik")

# Guvenli karakter kumesi disindaki her sey noktaya cevrilir. Neden: giris
# denemesindeki kullanici adi SALDIRGANIN yazdigi metindir ve icine satir
# sonu koyup gunluge sahte bir satir uydurabilirdi ("olay=giris_basarili
# ..."). Kirpma da var: uzun bir ad gunlugu sisirmesin.
_GUVENSIZ = re.compile(r"[^A-Za-z0-9._@-]")
_AZAMI_UZUNLUK = 64


def _temizle(deger: object) -> str:
    metin = str(deger)
    if len(metin) > _AZAMI_UZUNLUK:
        metin = metin[:_AZAMI_UZUNLUK] + "…"
    return _GUVENSIZ.sub(".", metin)


def _kur() -> None:
    """Zaman damgali bir cikti hazirlar (FR-10.9: 'zaman damgasiyla').

    Kendi isleyicisini kurar cunku uvicorn yalnizca kendi kayitcilarini
    yapilandirir; bu kayitci ona birakilsa INFO satirlari sessizce
    dusebilirdi ve gereksinim tam da o satirlar hakkinda. `propagate`
    kapatilmaz: ana kayitci yapilandirilmissa oraya da ulassin.
    """
    ust = logging.getLogger(_KAYITCI_ADI)
    if ust.handlers:
        return
    isleyici = logging.StreamHandler(sys.stdout)
    isleyici.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s",
            # ISO 8601, saniye cozunurlugu. Sunucu UTC calisir; systemd
            # gunlugu ayrica kendi zaman damgasini ekler ve ikisi
            # karsilastirilabilir olsun diye bicim sabit tutulur.
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )
    ust.addHandler(isleyici)
    ust.setLevel(logging.INFO)


_kur()


def olay(ad: str, **alanlar: object) -> None:
    """Bir kimlik/hesap olayini kaydeder.

    Alan degerleri cagri yerinde acikca secilir; bir nesneyi butunuyle
    gecirmek (ornegin Kullanici) parola ozetini de kayda sokabilirdi.
    """
    parcalar = " ".join(f"{anahtar}={_temizle(deger)}" for anahtar, deger in alanlar.items())
    _kayitci.info("olay=%s %s", ad, parcalar)
