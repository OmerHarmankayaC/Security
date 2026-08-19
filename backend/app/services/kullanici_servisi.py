"""Hesap yonetimi: olusturma, rol atama, parola sifirlama, devre disi
birakma (SRS FR-10.5 - FR-10.7; SDD 5.1b).

Hesap SILINMEZ. Gerekce tanimlarda alinan kararla ayni (Backlog,
09.08.2026): giris kayitlari ve gecmis islemler hesabin kimligine baglidir,
satir gidince o kayitlar okunamaz hale gelir.

Bu servisin butun yollari yalniz yonetim rolune aciktir; kapiyi
`app/guvenlik.yonetim_yetkisi` tutar ve router duzeyinde baglidir.
"""

import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.kayit import olay
from app.models.kimlik import HESAP_YONETEN_ROLLER, Kullanici, Rol
from app.repositories.tanim import PersonelDeposu
from app.services import parola as parola_araclari
from app.services.oturum_servisi import OturumServisi

# Kullanici adi ASCII kucuk harf kumesiyle SINIRLI. Sinirin nedeni Turkce
# I/i cifti: "İ" harfinin kucugu PostgreSQL'in yerel ayarina ve Python'un
# `str.lower`ina gore FARKLI cikar. Giris, adi Python'da kucultup
# veritabaninda esledigi icin iki taraf birbirini bulamaz ve kullanici
# dogru parolayla bile giremezdi. Sema da ayni kurali CHECK ile tutar.
# Uc ile elli karakter; basi ve sonu harf ya da rakam (bastaki/sondaki nokta
# ya da tire, gorunmez bir bosluk kadar kolay gozden kacar).
_AD_DESENI = re.compile(r"^[a-z0-9][a-z0-9._-]{1,48}[a-z0-9]$")


class KullaniciAdiGecersizError(ValueError):
    """Ad desene uymuyor (router 400'e cevirir)."""


class KullaniciAdiKullanimdaError(ValueError):
    pass


class PersonelBaglantisiGerekliError(ValueError):
    """FR-10.6: calisan rolundeki hesap bir personel kaydina baglanmalidir."""


class PersonelZatenBagliError(ValueError):
    pass


class PersonelBulunamadiError(ValueError):
    """Verilen personel_id hicbir personel kaydina karsilik gelmiyor.

    Once bu kontrol yoktu ve yabanci anahtar kisiti devreye giriyordu:
    yakalanmamis bir IntegrityError, kullaniciya 500 olarak donuyordu. Oysa
    yapilan sey gecerli bir istek bicimiydi, yalnizca isaret ettigi kayit
    yoktu (NFR-5).
    """


class KullaniciBulunamadiError(ValueError):
    pass


class KendiHesabiError(ValueError):
    """Yonetim kullanicisi kendi rolunu degistiremez ve kendini devre disi
    birakamaz."""


class HesapYonetmeYetkisiYokError(ValueError):
    """Isteyen rol hesap yonetemez (SRS 5.10: idare hesap uc noktalarina
    erisemez). Uc noktadaki rol kapisinin IKINCI katmani; kapisiz eklenen
    bir uc nokta bu kontrolle yine de durur."""


class SistemYoneticisineDokunulamazError(ValueError):
    """Hesap yoneticisi, sistem yoneticisi rolundeki hesabi degistiremez ve
    o rolde hesap acamaz (FR-10.12). Rol atamasi da bir dokunustur: kendi
    ustunde hesap acabilen bir rol, yetki tirmanmasini tek adimda yapar."""


class SonSistemYoneticisiError(ValueError):
    """Sistemde en az bir ETKIN sistem yoneticisi kalmalidir (FR-10.12).

    `KendiHesabiError`den AYRI bir kuraldir: o kazayi onler, bu iki kisinin
    birbirini kapatmasini. Yalniz biri olsaydi, iki sistem yoneticisi
    sirayla digerini dusurup sistemde sifir yetkili birakabilirdi.
    """


class KullaniciServisi:
    def __init__(self, oturum: Session) -> None:
        self.oturum = oturum
        self.oturumlar = OturumServisi(oturum)

    # --- Okuma --------------------------------------------------------------

    def listele(self) -> list[Kullanici]:
        return list(
            self.oturum.execute(select(Kullanici).order_by(Kullanici.kullanici_adi)).scalars().all()
        )

    # --- Olusturma (FR-10.5, FR-10.6, FR-10.7) ------------------------------

    def olustur(
        self,
        kullanici_adi: str,
        parola: str,
        rol: Rol,
        personel_id: int | None = None,
        *,
        isteyen: Kullanici | None = None,
    ) -> Kullanici:
        # `isteyen` YOKSA kurulum betigi cagiriyordur (FR-10.10): ilk hesap
        # arayuz disi bir adimla acilir ve o anda yetki soracak bir oturum
        # bulunmaz. Arayuzden gelen her cagri isteyeni tasir.
        if isteyen is not None:
            self._hesap_yonetebilir_mi(isteyen)
            self._sistem_yoneticisine_dokunma_hakki(isteyen, rol)
        ad = self._adi_dogrula(kullanici_adi)
        self._benzersizligi_dogrula(ad)
        self._personel_baglantisini_dogrula(rol, personel_id)

        kullanici = Kullanici(
            kullanici_adi=ad,
            parola_ozeti=parola_araclari.ozetle(parola),
            rol=rol,
            personel_id=personel_id,
            # FR-10.7: yonetimin atadigi parola ilk giriste degistirilir.
            # Bayrak burada acikca yaziliyor, sema varsayilani olarak degil -
            # kullanicinin kendi degistirdigi parola bu yolu izlemez ve
            # varsayilan olsaydi o da yeniden degistirmeye zorlanirdi.
            parola_degistirmeli=True,
        )
        self.oturum.add(kullanici)
        self.oturum.flush()
        # FR-10.9. Parola ve ozeti KAYDEDILMEZ. `isteyen` bos kalabilir:
        # ilk yonetim hesabini acan kurulum betiginin arkasinda bir hesap
        # yoktur (FR-10.10).
        olay(
            "hesap_olusturuldu",
            kullanici=ad,
            rol=rol.value,
            personel_id=personel_id,
            yapan=isteyen.kullanici_adi if isteyen else "kurulum_betigi",
        )
        return kullanici

    # --- Guncelleme (FR-10.5) -----------------------------------------------

    def guncelle(
        self,
        kullanici_id: int,
        *,
        isteyen: Kullanici,
        rol: Rol | None = None,
        aktif: bool | None = None,
        personel_id: int | None = None,
        personel_id_verildi: bool = False,
    ) -> Kullanici:
        kullanici = self._getir(kullanici_id)
        self._hesap_yonetebilir_mi(isteyen)
        # HEM MEVCUT HEM ATANACAK rol denetlenir: sistem yoneticisini
        # dusurmek de, birini sistem yoneticisi yapmak da ayni yetkiyi ister.
        self._sistem_yoneticisine_dokunma_hakki(isteyen, kullanici.rol)
        if rol is not None:
            self._sistem_yoneticisine_dokunma_hakki(isteyen, rol)

        if kullanici.kullanici_id == isteyen.kullanici_id and (
            (rol is not None and rol is not kullanici.rol) or aktif is False
        ):
            # Kendi rolunu dusuren ya da kendini kapatan bir yonetim
            # kullanicisi, sistemde hic yonetim hesabi kalmadigi durumu tek
            # tikla uretebilir; o noktadan sonra hesap acmanin arayuzden yolu
            # yoktur (FR-10.10 geregi acan uc nokta BULUNMAZ) ve sunucuya
            # girip betik calistirmak gerekir.
            raise KendiHesabiError

        yeni_rol = rol if rol is not None else kullanici.rol
        self._son_sistem_yoneticisini_koru(
            kullanici, yeni_rol, kullanici.aktif if aktif is None else aktif
        )
        yeni_personel = personel_id if personel_id_verildi else kullanici.personel_id
        self._personel_baglantisini_dogrula(
            yeni_rol, yeni_personel, mevcut_kullanici_id=kullanici.kullanici_id
        )

        if yeni_rol is not kullanici.rol:
            olay(
                "rol_degistirildi",
                kullanici=kullanici.kullanici_adi,
                onceki=kullanici.rol.value,
                yeni=yeni_rol.value,
                yapan=isteyen.kullanici_adi,
            )
        kullanici.rol = yeni_rol
        kullanici.personel_id = yeni_personel
        if aktif is not None and aktif != kullanici.aktif:
            kullanici.aktif = aktif
            olay(
                "hesap_aktif_edildi" if aktif else "hesap_devre_disi_birakildi",
                kullanici=kullanici.kullanici_adi,
                yapan=isteyen.kullanici_adi,
            )
            if not aktif:
                # Devre disi birakma ACIK OTURUMLARI da kapatir. Yalniz
                # bayragi cevirmek, elindeki cerezle calisan birinin oturum
                # suresi dolana kadar icerde kalmasi demekti.
                self.oturumlar.kullanicinin_oturumlarini_sil(kullanici.kullanici_id)

        self.oturum.flush()
        return kullanici

    # --- Parola sifirlama (FR-10.5, FR-10.7) --------------------------------

    def parola_sifirla(
        self, kullanici_id: int, yeni_parola: str, *, isteyen: Kullanici
    ) -> Kullanici:
        kullanici = self._getir(kullanici_id)
        self._hesap_yonetebilir_mi(isteyen)
        self._sistem_yoneticisine_dokunma_hakki(isteyen, kullanici.rol)
        kullanici.parola_ozeti = parola_araclari.ozetle(yeni_parola)
        kullanici.parola_degistirmeli = True
        # Kilit de kalkar: parolasi sifirlanan kullanicinin eski parolayla
        # dolmus sayaci yuzunden bekletilmesinin bir anlami yok.
        kullanici.basarisiz_deneme = 0
        kullanici.kilit_bitis = None
        # Sifirlama ACIK OTURUMLARI kapatir. Parolanin sifirlanma nedeni
        # cogu zaman hesabin ele gecmis olmasidir; oturumlar ayakta kalirsa
        # sifirlama hicbir sey cozmezdi.
        self.oturumlar.kullanicinin_oturumlarini_sil(kullanici.kullanici_id)
        self.oturum.flush()
        olay(
            "parola_sifirlandi",
            kullanici=kullanici.kullanici_adi,
            yapan=isteyen.kullanici_adi,
        )
        return kullanici

    # --- Yardimcilar --------------------------------------------------------

    # --- FR-10.12 korumalari ------------------------------------------------

    def _hesap_yonetebilir_mi(self, isteyen: Kullanici) -> None:
        if isteyen.rol not in HESAP_YONETEN_ROLLER:
            raise HesapYonetmeYetkisiYokError

    def _sistem_yoneticisine_dokunma_hakki(self, isteyen: Kullanici, hedef_rol: Rol) -> None:
        """Hedef (mevcut ya da atanacak) rol sistem yoneticisiyse, yalniz
        sistem yoneticisi dokunabilir."""
        if hedef_rol is Rol.SISTEM_YONETICISI and isteyen.rol is not Rol.SISTEM_YONETICISI:
            raise SistemYoneticisineDokunulamazError

    def _etkin_sistem_yoneticisi_sayisi(self, haric: int | None = None) -> int:
        sorgu = (
            select(func.count())
            .select_from(Kullanici)
            .where(Kullanici.rol == Rol.SISTEM_YONETICISI, Kullanici.aktif.is_(True))
        )
        if haric is not None:
            sorgu = sorgu.where(Kullanici.kullanici_id != haric)
        return int(self.oturum.execute(sorgu).scalar() or 0)

    def _son_sistem_yoneticisini_koru(
        self, kullanici: Kullanici, yeni_rol: Rol, aktif: bool
    ) -> None:
        """Bu degisiklik sistemi sifir etkin sistem yoneticisiyle birakir mi?"""
        if kullanici.rol is not Rol.SISTEM_YONETICISI or not kullanici.aktif:
            return  # zaten sayima girmiyordu
        hala_yetkili = yeni_rol is Rol.SISTEM_YONETICISI and aktif
        if hala_yetkili:
            return
        if self._etkin_sistem_yoneticisi_sayisi(haric=kullanici.kullanici_id) == 0:
            raise SonSistemYoneticisiError

    def _getir(self, kullanici_id: int) -> Kullanici:
        kullanici = self.oturum.get(Kullanici, kullanici_id)
        if kullanici is None:
            raise KullaniciBulunamadiError
        return kullanici

    @staticmethod
    def _adi_dogrula(kullanici_adi: str) -> str:
        ad = kullanici_adi.strip().lower()
        if not _AD_DESENI.fullmatch(ad):
            raise KullaniciAdiGecersizError(
                "Kullanici adi 3-50 karakter olmali ve yalniz ingiliz alfabesi "
                "harfleri, rakam, nokta, tire ve alt cizgi icermelidir"
            )
        return ad

    def _benzersizligi_dogrula(self, ad: str) -> None:
        var_mi = self.oturum.execute(
            select(Kullanici.kullanici_id).where(Kullanici.kullanici_adi == ad)
        ).first()
        if var_mi is not None:
            raise KullaniciAdiKullanimdaError("Bu kullanici adi zaten kullaniliyor")

    def _personel_baglantisini_dogrula(
        self, rol: Rol, personel_id: int | None, *, mevcut_kullanici_id: int | None = None
    ) -> None:
        if rol is Rol.CALISAN and personel_id is None:
            raise PersonelBaglantisiGerekliError(
                "Calisan rolundeki hesap bir personel kaydina baglanmalidir"
            )
        if personel_id is None:
            return

        if PersonelDeposu(self.oturum).getir(personel_id) is None:
            raise PersonelBulunamadiError(f"{personel_id} numarali personel kaydi bulunamadi")

        # Bir personelin iki hesabi olmasi engellenir. SRS bunu ayri bir
        # madde olarak yazmaz; FR-10.6'nin kurdugu "hesap -> personel"
        # baglantisinin tek anlamli kalmasi icin gerekli. Iki hesap FR-9.1'i
        # ihlal etmezdi (her ikisi de yalniz kendi verisini gorurdu) ama
        # parola sifirlandiginda hangi hesabin sifirlandigi belirsizlesirdi.
        stmt = select(Kullanici.kullanici_id).where(Kullanici.personel_id == personel_id)
        if mevcut_kullanici_id is not None:
            stmt = stmt.where(Kullanici.kullanici_id != mevcut_kullanici_id)
        if self.oturum.execute(stmt).first() is not None:
            raise PersonelZatenBagliError("Bu personelin zaten bir hesabi var")
