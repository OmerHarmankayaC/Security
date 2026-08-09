"""Parola ozeti ve parola kurali (SRS FR-10.2; SDD 5.1b).

Argon2id kullanilir. Secim SDD 5.1b'de verilidir; parametreler
`argon2-cffi`nin kendi varsayilanlaridir (RFC 9106'nin dusuk bellek profili:
64 MiB, 3 gecis, 4 kol). Parametreleri elle sabitlemek yerine kutuphanenin
varsayilanina birakmak bilincli: kutuphane surumuyle birlikte guncellenirler
ve `dogrula` eski ozetleri PARAMETRELERI OZETIN ICINDEN okuyarak dogrulamaya
devam eder.

Ozet dizesi kendi tuzunu ve parametrelerini tasir; ayri bir tuz sutunu
yoktur (SDD 4.2.1 `kullanici` tablosunda da yalniz `parola_ozeti` vardir).
"""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

# SRS'te sayi verilmemistir; kural tek olcut olarak uzunluktur. Karakter
# sinifi zorunlulugu (buyuk/kucuk/rakam) kullaniciyi "Parola1!" kalibina
# iter ve gercek entropiyi uzunluk kadar buyutmez.
ASGARI_UZUNLUK = 12

_ozetleyici = PasswordHasher()

# Kullanici bulunamadiginda karsilastirilacak SABIT ozet. Varlik sizintisini
# kapatmak icin gereklidir: kullanici yoksa dogrulama hic yapilmazsa yanit
# belirgin bicimde daha erken doner ve giris ekrani bir kullanici adi
# sayacina donusur (SDD 5.1b). Bu ozet gercek bir hesaba ait DEGILDIR;
# yalnizca ayni maliyetli hesabin yapilmasini saglar.
_SAHTE_OZET = _ozetleyici.hash("kullanici-yok-bu-ozet-hicbir-hesaba-ait-degil")


class ParolaKuraliError(ValueError):
    """Parola asgari kurali saglamiyor (router 400'e cevirir)."""


def kurali_dogrula(parola: str) -> None:
    if len(parola) < ASGARI_UZUNLUK:
        raise ParolaKuraliError(f"Parola en az {ASGARI_UZUNLUK} karakter olmalidir")


def ozetle(parola: str) -> str:
    """Kurali dogrular ve Argon2id ozetini uretir."""
    kurali_dogrula(parola)
    return _ozetleyici.hash(parola)


def dogrula(ozet: str, parola: str) -> bool:
    """Parolanin ozete uydugunu dogrular.

    Kurali BURADA uygulamaz: kural sonradan sikilastirilirsa, eskiden
    gecerli bir parolayla acilmis hesap giris yapamaz hale gelirdi. Kural
    parola YAZILIRKEN uygulanir.
    """
    try:
        return _ozetleyici.verify(ozet, parola)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        # InvalidHashError ayrica yakalanir: ozet alani bozuksa ya da baska
        # bir bicimde yazilmissa giris 500'e dusmemeli, basarisiz giris gibi
        # ele alinmalidir - aksi halde yanit koduyla "bu hesabin ozeti
        # bozuk" bilgisi disari sizar.
        return False


def bosa_dogrula() -> None:
    """Kullanici bulunamadiginda cagrilir; gercek bir dogrulama kadar surer.

    Donus degeri yoktur cunku sonucu her zaman "basarisiz"dir - tek isi
    zamani esitlemektir.
    """
    dogrula(_SAHTE_OZET, "yanlis")
