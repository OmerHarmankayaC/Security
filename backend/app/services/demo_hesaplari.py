"""Gosterim ortaminin hesap tanimi — TEK YER (Demo Senaryosu 7).

Iki tuketicisi var ve ikisi de ayni listeyi bilmek zorunda: hesaplari ACAN
uretec (`scripts/demo_veri_uret.py`) ve giris ekraninda kimlik bilgisini
GOSTEREN uc nokta (`app/routers/demo.py`). Liste iki yerde yazilsaydi,
uretecin actigi hesapla ekranin gosterdigi hesap sessizce ayrisir ve
kullanici calismayan bir kullanici adiyla karsilasirdi.

PAROLA BURADA YAZILI DEGIL, TURETILIR. Her hesabin kendi parolasi vardir ve
`parola_uret` onu tek bir tohumdan (`ayarlar.demo_parola_tohumu`, ortam
degiskeni) hesaplar. Boylece:

  - parolalar hesap basina FARKLIDIR - biri elden ele dolastiginda digerleri
    etkilenmez, ve dordu de ayni dizeyse "parolayi biliyorum" demek "hepsini
    biliyorum" demek olurdu;
  - hicbiri saklanmaz. Ne depoda, ne `.env` icinde, ne veritabaninda ayri
    bir sutunda dururlar; hesaplari acan uretec ile onlari giris ekraninda
    gosteren uc nokta ayni turetmeyi yapar ve ayni sonuca varir. Iki yerde
    saklanan bir parola, iki yerin ayrisabilecegi anlamina gelirdi.

SISTEM YONETICISI LISTEDE YOK. Uretec onu acar - gosterim ortaminin da bir
sistem yoneticisine ihtiyaci var (FR-10.12) - ama giris ekraninda
gosterilmez. Gosterim ortami herkese aciktir ve en genis yetkiyi ekrana
yazmak, demoyu gezen herkese kendi kullanici hesaplarini yonetme hakki
vermek demektir. Ekranda gorunen uc rol, urunun anlatmak istedigi uc
yuzeydir: idare, hesap yonetimi ve calisan paneli.
"""

import hashlib
import hmac
import string
from dataclasses import dataclass

from app.models.kimlik import Rol

# Parola alfabesi ve uzunlugu. Kucuk harf + rakam: gosterim parolasi ekrandan
# ELLE de yazilabilmeli ve buyuk/kucuk harf ayrimi ile birbirine benzeyen
# karakterler (I/l, O/0) o isi zorlastirir. Uzunluk on iki - tahmin edilmeye
# calisilacak bir sey degil, ama kisa bir dize gosterim ortamini kaba kuvvet
# denemelerine acik hale getirirdi.
_ALFABE = string.ascii_lowercase + string.digits
_UZUNLUK = 12


@dataclass(frozen=True, slots=True)
class DemoHesabi:
    kullanici_adi: str
    rol: Rol
    #: Ekranda rolun yanina yazilan tek cumlelik aciklama. Hangi hesabin
    #: neyi gosterdigi yazilmazsa iki calisan hesabi ayirt edilemez.
    aciklama: str
    #: Personel sicili — yalnizca calisan hesaplari icin dolu. Uretec
    #: hesabi bu sicile bagli personele baglar.
    sicil_no: str | None = None
    #: Giris ekraninda gosterilir mi. Sistem yoneticisi acilir ama
    #: GOSTERILMEZ (yukaridaki gerekce).
    gosterilir: bool = True


DEMO_HESAPLARI: tuple[DemoHesabi, ...] = (
    DemoHesabi(
        kullanici_adi="demo_sistem",
        rol=Rol.SISTEM_YONETICISI,
        aciklama="Sistem yöneticisi",
        gosterilir=False,
    ),
    DemoHesabi(
        kullanici_adi="demo_idare",
        rol=Rol.IDARE,
        aciklama="Çizelgeyi kuran ve yayınlayan rol; hesap yönetimi dışındaki her şey",
    ),
    DemoHesabi(
        kullanici_adi="demo_hesap",
        rol=Rol.HESAP_YONETICISI,
        aciklama="Yalnızca kullanıcı hesaplarını yönetir; çizelgeye dokunmaz",
    ),
    DemoHesabi(
        kullanici_adi="demo_d1010",
        rol=Rol.CALISAN,
        aciklama="Çalışan — yıllık fazla çalışma kotası dolmaya yakın",
        sicil_no="D-1010",
    ),
    DemoHesabi(
        kullanici_adi="demo_d1020",
        rol=Rol.CALISAN,
        aciklama="Çalışan — ortalama yüklü",
        sicil_no="D-1020",
    ),
)


def parola_uret(tohum: str, kullanici_adi: str) -> str:
    """Tohum + kullanici adindan on iki karakterlik parola turetir.

    HMAC kullanilir, duz `sha256(tohum + ad)` degil: duz birlestirmede
    tohumu bilmeyen biri bile iki hesabin parolasi arasindaki iliskiden
    tohum hakkinda bilgi toplayabilir. Burada korunacak bir sey olmamasi
    (parolalar zaten giris ekraninda yazili) bunu dogru yapmamak icin bir
    gerekce degil - bu kod baska bir yerde ornek alinabilir.

    DETERMINISTIKTIR ve oyle olmak ZORUNDADIR: hesabi acan uretec ile onu
    ekranda gosteren uc nokta ayri sureclerdir, aralarinda tek ortak sey
    tohumdur. Rastgele uretilseydi ekrandaki parola ile veritabanindakinin
    tutmasi icin bir yerde saklanmalari gerekirdi.
    """
    ozet = hmac.new(tohum.encode("utf-8"), kullanici_adi.encode("utf-8"), hashlib.sha256).digest()
    sayi = int.from_bytes(ozet, "big")
    harfler = []
    for _ in range(_UZUNLUK):
        sayi, kalan = divmod(sayi, len(_ALFABE))
        harfler.append(_ALFABE[kalan])
    return "".join(harfler)


def gosterilecekler() -> tuple[DemoHesabi, ...]:
    return tuple(h for h in DEMO_HESAPLARI if h.gosterilir)


__all__ = ["DEMO_HESAPLARI", "DemoHesabi", "gosterilecekler", "parola_uret"]
