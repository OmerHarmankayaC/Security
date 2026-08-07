"""Calisan panelinin "kisiye ozel baglanti" kapisi (Backlog B-05; SRS FR-9.1).

B-05 gercek kimlik dogrulamayi erteliyor: panele kisiye ozel bir baglantiyla
girilir. Buradaki anahtar, personel_id'den sunucu sirriyla TURETILIR:

    anahtar = HMAC-SHA256(sunucu_sirri, personel_id)

Boylece her personelin baglantisi kendine ozeldir; URL'deki personel_id'yi
degistiren biri, o kisinin anahtarini uretemedigi icin baskasinin cizelgesini
goremez (FR-9.1). Tek ortak bir anahtar bunu saglamiyordu.

Ek tablo gerektirmez (anahtar saklanmaz, her istekte yeniden turetilir) ve
mevcut `ayarlar.calisan_paneli_baglanti_anahtari` sirri korunur.

SINIRLARI - bu bir kimlik dogrulama DEGILDIR, B-05'in yerini almaz:
  - Baglantiyi ele geciren herkes o personelin verisini gorur (tasiyici
    belirtec gibi davranir); baglanti suresiz gecerlidir, iptal edilemez.
  - Sunucu sirri sizarsa butun anahtarlar uretilebilir.
  - Yalnizca OKUMA yetkisi degil, o personel adina tercih bildirme yetkisi de
    verir (SDD 6.1: bu arayuzdeki hicbir yazma islemi cizelgeyi etkilemez,
    en fazla o kisi adina bir tercih kaydi dogar).
Kurumsal kimlik dogrulama geldiginde (B-05) bu modul tumuyle kalkar.
"""

import hashlib
import hmac

from app.config import ayarlar

# Anahtar uzunlugu: SHA-256'nin 64 karakterlik onaltilik ciktisinin ilk yarisi.
# 128 bit, kaba kuvvetle denenemeyecek kadar genis; URL'de de okunabilir kalir.
_ANAHTAR_UZUNLUGU = 32


def anahtar_uret(personel_id: int) -> str:
    """personel_id icin kisiye ozel baglanti anahtarini turetir."""
    imza = hmac.new(
        ayarlar.calisan_paneli_baglanti_anahtari.encode("utf-8"),
        str(personel_id).encode("utf-8"),
        hashlib.sha256,
    )
    return imza.hexdigest()[:_ANAHTAR_UZUNLUGU]


def anahtar_gecerli_mi(personel_id: int, anahtar: str) -> bool:
    """Verilen anahtarin o personele ait olup olmadigini sabit zamanda dogrular.

    `hmac.compare_digest` kullanilir: duz `==` karsilastirmasi ilk farkli
    karakterde donecegi icin gecen sureden anahtar karakter karakter
    tahmin edilebilirdi (zamanlama saldirisi).
    """
    return hmac.compare_digest(anahtar_uret(personel_id), anahtar)


def baglanti_yolu(personel_id: int) -> str:
    """Personele verilecek baglantinin uygulama icindeki yolu."""
    return f"/calisan/{personel_id}?anahtar={anahtar_uret(personel_id)}"
