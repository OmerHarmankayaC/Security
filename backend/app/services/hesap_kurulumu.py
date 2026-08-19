"""Toplu hesap kurulumu (SRS FR-10.6, FR-10.11, FR-10.13).

GECICI PAROLA HICBIR YERDE SAKLANMAZ. Servis onu yalnizca DONER; cagiran
taraf (kurulum betigi) bir kez gosterir ve unutur. Bir alana yazilsaydi -
"kurulum ciktisi" adinda bir tabloya ya da bir dosyaya - o yer sistemin en
zayif noktasi olurdu: otuz hesabin duz parolasi tek bir okumayla ele gecer.
Kaybedilen parola YENIDEN URETILIR, geri okunmaz (FR-10.13).
"""

import re
import secrets
import unicodedata
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.kimlik import Kullanici, Rol
from app.models.tanim import Personel
from app.services.kullanici_servisi import KullaniciServisi
from app.services.parola import ASGARI_UZUNLUK

# Karistirilabilir karakterler DISARIDA: gecici parola telefonda okunacak ya
# da elle yazilacak; 0/O ve 1/l/I ayrimi o aktarimda kaybolur ve kullanici
# "parolam calismiyor" der.
_ALFABE = "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"
_UZUNLUK = max(ASGARI_UZUNLUK + 4, 16)

# Turkce harflerin ASCII karsiligi. `unicodedata` tek basina yetmez: "ı" ve
# "ğ" ayristirilamaz, "İ" ise "I"ya inip kucultmede tekrar "i" olmaz.
_TURKCE = str.maketrans(
    {
        "ı": "i",
        "İ": "i",
        "ş": "s",
        "Ş": "s",
        "ğ": "g",
        "Ğ": "g",
        "ü": "u",
        "Ü": "u",
        "ö": "o",
        "Ö": "o",
        "ç": "c",
        "Ç": "c",
    }
)


def asciye_indir(metin: str) -> str:
    """Metni ASCII'ye indirir ve kucultur (FR-10.11).

    Turkce harfler once ELLE eslenir, sonra kalan aksanlar ayristirilarak
    atilir. Sira onemli: "İ" once "i" olmazsa NFKD onu "I" + birlesik
    noktaya ayirir ve kucultmede "i" yerine "i̇" cikar.
    """
    esli = metin.translate(_TURKCE)
    ayrisik = unicodedata.normalize("NFKD", esli)
    return "".join(k for k in ayrisik if not unicodedata.combining(k)).lower()


def kullanici_adi_turet(sicil_no: str) -> str:
    """Sicil numarasindan kullanici adi: `VS-001` -> `vs001`.

    SICILDEN TURETILIR, ADDAN DEGIL: ad benzersiz degildir ve iki "Mehmet
    Yilmaz" ayni kullanici adina duser. Sicil zaten benzersizdir.
    """
    return re.sub(r"[^a-z0-9]", "", asciye_indir(sicil_no))


def gecici_parola_uret() -> str:
    """Kriptografik olarak guclu, okunabilir gecici parola."""
    return "".join(secrets.choice(_ALFABE) for _ in range(_UZUNLUK))


@dataclass(frozen=True)
class AcilanHesap:
    """Bir kez gosterilecek kurulum sonucu. `gecici_parola` BU NESNEDEN
    BASKA hicbir yerde bulunmaz."""

    kullanici_adi: str
    gecici_parola: str
    rol: Rol
    personel_id: int | None = None
    ad_soyad: str | None = None


class HesapKurulumu:
    def __init__(self, oturum: Session) -> None:
        self.oturum = oturum
        self.kullanicilar = KullaniciServisi(oturum)

    def calisan_hesaplari_ac(self) -> list[AcilanHesap]:
        """Hesabi olmayan HER personel icin calisan hesabi acar.

        HESABI OLAN ATLANIR (FR-10.6: bir personelin birden fazla hesabi
        olamaz). Betik iki kez kosturuldugunda ikinci kosum hicbir sey
        yapmaz; bu, kurulumu yarida kalan bir sistemde tekrar calistirmayi
        guvenli kilar.
        """
        bagli = set(
            self.oturum.execute(
                select(Kullanici.personel_id).where(Kullanici.personel_id.is_not(None))
            )
            .scalars()
            .all()
        )
        personeller = (
            self.oturum.execute(select(Personel).order_by(Personel.sicil_no)).scalars().all()
        )

        acilanlar: list[AcilanHesap] = []
        for personel in personeller:
            if personel.personel_id in bagli:
                continue
            parola = gecici_parola_uret()
            kullanici = self.kullanicilar.olustur(
                kullanici_adi_turet(personel.sicil_no),
                parola,
                Rol.CALISAN,
                personel.personel_id,
            )
            # FR-10.7: kurulumda atanan parola ilk giriste degistirilir.
            kullanici.parola_degistirmeli = True
            acilanlar.append(
                AcilanHesap(
                    kullanici_adi=kullanici.kullanici_adi,
                    gecici_parola=parola,
                    rol=Rol.CALISAN,
                    personel_id=personel.personel_id,
                    ad_soyad=personel.ad_soyad,
                )
            )
        self.oturum.flush()
        return acilanlar

    def yonetim_hesabi_ac(self, kullanici_adi: str, rol: Rol) -> AcilanHesap:
        """Personel baglantisi olmayan bir yonetim hesabi acar (FR-10.6:
        calisan disindaki roller icin baglanti istege baglidir)."""
        parola = gecici_parola_uret()
        kullanici = self.kullanicilar.olustur(kullanici_adi, parola, rol)
        kullanici.parola_degistirmeli = True
        self.oturum.flush()
        return AcilanHesap(kullanici_adi=kullanici.kullanici_adi, gecici_parola=parola, rol=rol)

    def etkin_sistem_yoneticisi_sayisi(self) -> int:
        return len(
            self.oturum.execute(
                select(Kullanici.kullanici_id).where(
                    Kullanici.rol == Rol.SISTEM_YONETICISI, Kullanici.aktif.is_(True)
                )
            )
            .scalars()
            .all()
        )
