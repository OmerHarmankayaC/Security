"""H1-H8 zorunlu kisitlari (SRS Bolum 4.2, SDD Ek A ornek sablonu).

modele_ekle, CP-SAT entegrasyonu Sprint 2 Gun 6'da tamamlanana kadar
ZorunluKural.modele_ekle'nin NotImplementedError firlatan varsayilanini
kullanir; burada yalnizca dogrula uygulanir.
"""

from collections import Counter

from app.kurallar.baglam import AtamaKaydi, Baglam
from app.kurallar.kayit_defteri import kayitli
from app.kurallar.temel import Ihlal, ZorunluKural
from app.kurallar.yardimcilar import (
    ardisik_kosu_ihlalleri,
    calisilan_gunler,
    gece_calisilan_gunler,
    gunluk_saat,
    kayan_pencere_ihlalleri,
    personel_bazinda_sirali,
)


@kayitli("H1")
class H1GundeBirVardiya(ZorunluKural):
    """Bir personel bir takvim gununde en fazla bir vardiyaya atanabilir. Parametresizdir."""

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        sayac = Counter((a.personel_id, a.tarih) for a in atamalar)
        return [
            Ihlal(
                self.kimlik,
                personel_id,
                tarih,
                f"{tarih} gununde {sayi} atama var; en fazla 1 olmali",
            )
            for (personel_id, tarih), sayi in sayac.items()
            if sayi > 1
        ]


@kayitli("H2")
class H2AsgariDinlenme(ZorunluKural):
    """Ardisik iki atama arasindaki bosluk asgari_dinlenme_saati degerinden az olamaz."""

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        d = self.parametreler["asgari_dinlenme_saati"]
        ihlaller: list[Ihlal] = []
        for personel_id, sirali in personel_bazinda_sirali(atamalar, baglam).items():
            for onceki, sonraki in zip(sirali, sirali[1:], strict=False):
                ara = baglam.saat_farki(onceki, sonraki)
                if ara < d:
                    ihlaller.append(
                        Ihlal(
                            self.kimlik,
                            personel_id,
                            sonraki.tarih,
                            f"Onceki vardiyayla arada yalnizca {ara:.1f} saat var; "
                            f"en az {d} saat gerekli",
                        )
                    )
        return ihlaller


@kayitli("H3")
class H3ArdisikGeceUstSiniri(ZorunluKural):
    """Bir personel ust uste azami_ardisik_gece degerinden fazla gece vardiyasi tutamaz."""

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        sinir = self.parametreler["azami_ardisik_gece"]
        gunler = gece_calisilan_gunler(atamalar, baglam)
        return ardisik_kosu_ihlalleri(
            self.kimlik,
            gunler,
            sinir,
            "{kosu} ardisik gece vardiyasi; en fazla {sinir} olmali",
        )


@kayitli("H4")
class H4ArdisikCalismaGunuUstSiniri(ZorunluKural):
    """Bir personel ust uste azami_ardisik_calisma_gunu degerinden fazla gun calisamaz."""

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        sinir = self.parametreler["azami_ardisik_calisma_gunu"]
        gunler = calisilan_gunler(atamalar)
        return ardisik_kosu_ihlalleri(
            self.kimlik,
            gunler,
            sinir,
            "{kosu} ardisik calisma gunu; en fazla {sinir} olmali",
        )


@kayitli("H5")
class H5KayanHaftalikSaatTavani(ZorunluKural):
    """Herhangi bir yedi gunluk pencerede toplam calisma saati azami_haftalik_saat'i asamaz."""

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        tavan = self.parametreler["azami_haftalik_saat"]
        saatler = gunluk_saat(atamalar, baglam)
        return kayan_pencere_ihlalleri(
            self.kimlik,
            saatler,
            tavan,
            "7 gunluk pencerede {toplam:.1f} saat; tavan {sinir} saat",
        )


@kayitli("H6")
class H6HaftalikAsgariIzinGunu(ZorunluKural):
    """Herhangi bir yedi gunluk pencerede en az haftalik_asgari_izin_gunu kadar bos gun olmali."""

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        izin_gunu = self.parametreler["haftalik_asgari_izin_gunu"]
        ust_sinir = 7 - izin_gunu
        gunler = calisilan_gunler(atamalar)
        calisma_gostergesi = {
            personel_id: dict.fromkeys(gunler_kumesi, 1.0)
            for personel_id, gunler_kumesi in gunler.items()
        }
        return kayan_pencere_ihlalleri(
            self.kimlik,
            calisma_gostergesi,
            ust_sinir,
            "7 gunluk pencerede {toplam:.0f} gun calisilmis; en fazla {sinir:.0f} olmali",
        )


@kayitli("H7")
class H7Musaitlik(ZorunluKural):
    """Personel, musait olmadigi zaman araligiyla kesisen bir vardiyaya atanamaz (TD-4)."""

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        return [
            Ihlal(
                self.kimlik,
                atama.personel_id,
                atama.tarih,
                "Personel bu tarihte/vardiyada musait degil",
            )
            for atama in atamalar
            if not baglam.musait_mi(atama)
        ]


@kayitli("H8")
class H8OnkosulYetkinligi(ZorunluKural):
    """Bir noktaya atanan personel, o noktanin gerektirdigi yetkinlige sahip olmalidir (TD-9)."""

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        ihlaller: list[Ihlal] = []
        for atama in atamalar:
            nokta = baglam.gorev_noktalari.get(atama.nokta_id)
            if nokta is None or nokta.onkosul_yetkinlik_id is None:
                continue
            if not baglam.yetkin_mi(atama.personel_id, nokta.onkosul_yetkinlik_id):
                ihlaller.append(
                    Ihlal(
                        self.kimlik,
                        atama.personel_id,
                        atama.tarih,
                        f"Personel, {atama.nokta_id} nolu noktanin gerektirdigi "
                        f"{nokta.onkosul_yetkinlik_id} nolu yetkinlige sahip degil",
                    )
                )
        return ihlaller


__all__ = [
    "H1GundeBirVardiya",
    "H2AsgariDinlenme",
    "H3ArdisikGeceUstSiniri",
    "H4ArdisikCalismaGunuUstSiniri",
    "H5KayanHaftalikSaatTavani",
    "H6HaftalikAsgariIzinGunu",
    "H7Musaitlik",
    "H8OnkosulYetkinligi",
]
