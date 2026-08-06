"""H1-H8 zorunlu kisitlari (SRS Bolum 4.2, SDD Ek A ornek sablonu, SDD 5.3).

Her kuralin hem dogrula (elle kurulan atama listeleri uzerinde, Sprint 1)
hem modele_ekle (gercek CP-SAT model nesnesi uzerinde, Sprint 2 Gun 6)
tarafi doludur; SDD 3.2.1'in "iki yorumlayici da ayni kural nesnesinden
beslenir" ilkesiyle tutarli.
"""

from collections import Counter

from ortools.sat.python import cp_model

from app.kurallar.baglam import AtamaKaydi, Baglam
from app.kurallar.kayit_defteri import kayitli
from app.kurallar.temel import Ihlal, XAnahtari, ZorunluKural
from app.kurallar.yardimcilar import (
    ardisik_kosu_ihlalleri,
    calisilan_gunler,
    gece_calisilan_gunler,
    gunluk_saat,
    kayan_pencere_ihlalleri,
    kayan_pencere_kisiti_ekle,
    personel_bazinda_sirali,
)


@kayitli("H1")
class H1GundeBirVardiya(ZorunluKural):
    """Bir personel bir takvim gununde en fazla bir vardiyaya atanabilir. Parametresizdir."""

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> None:
        for p in baglam.personel:
            for g in baglam.zaman_ekseni:
                ilgili = [
                    degiskenler[(p, g, v, n)]
                    for v in baglam.vardiya_tipleri
                    for n in baglam.gorev_noktalari
                    if (p, g, v, n) in degiskenler
                ]
                if ilgili:
                    model.add(sum(ilgili) <= 1)
        return None

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        sayac = Counter((a.personel_id, a.tarih) for a in atamalar)
        return [
            Ihlal(
                kural_kimlik=self.kimlik,
                personel_id=personel_id,
                tarih=tarih,
                aciklama=f"{tarih} gununde {sayi} atama var; en fazla 1 olmali",
            )
            for (personel_id, tarih), sayi in sayac.items()
            if sayi > 1
        ]


@kayitli("H2")
class H2AsgariDinlenme(ZorunluKural):
    """Ardisik iki atama arasindaki bosluk asgari_dinlenme_saati degerinden az olamaz."""

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> None:
        """SDD Ek A'daki H2 ornegiyle birebir."""
        d = self.parametreler["asgari_dinlenme_saati"]
        for v1, v2 in baglam.vardiya_ciftleri:
            for g1, g2 in baglam.gun_ciftleri:
                ara = baglam.saat_farki_ham(g1, v1, g2, v2)
                if 0 <= ara < d:
                    for p in baglam.personel:
                        model.add(baglam.y[(p, g1, v1)] + baglam.y[(p, g2, v2)] <= 1)
        return None

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        d = self.parametreler["asgari_dinlenme_saati"]
        ihlaller: list[Ihlal] = []
        for personel_id, sirali in personel_bazinda_sirali(atamalar, baglam).items():
            for onceki, sonraki in zip(sirali, sirali[1:], strict=False):
                ara = baglam.saat_farki(onceki, sonraki)
                if ara < d:
                    ihlaller.append(
                        Ihlal(
                            kural_kimlik=self.kimlik,
                            personel_id=personel_id,
                            tarih=sonraki.tarih,
                            aciklama=f"Onceki vardiyayla arada yalnizca {ara:.1f} saat var; "
                            f"en az {d} saat gerekli",
                        )
                    )
        return ihlaller


@kayitli("H3")
class H3ArdisikGeceUstSiniri(ZorunluKural):
    """Bir personel ust uste azami_ardisik_gece degerinden fazla gece vardiyasi tutamaz."""

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> None:
        sinir = self.parametreler["azami_ardisik_gece"]
        kayan_pencere_kisiti_ekle(
            model,
            baglam,
            pencere_uzunlugu=sinir + 1,
            vardiyalar=baglam.gece_vardiyalari,
            agirlik_fn=lambda _v: 1,
            ust_sinir=sinir,
        )
        return None

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

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> None:
        sinir = self.parametreler["azami_ardisik_calisma_gunu"]
        kayan_pencere_kisiti_ekle(
            model,
            baglam,
            pencere_uzunlugu=sinir + 1,
            vardiyalar=baglam.vardiya_tipleri,
            agirlik_fn=lambda _v: 1,
            ust_sinir=sinir,
        )
        return None

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

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> None:
        tavan_saat = self.parametreler["azami_haftalik_saat"]
        kayan_pencere_kisiti_ekle(
            model,
            baglam,
            pencere_uzunlugu=7,
            vardiyalar=baglam.vardiya_tipleri,
            agirlik_fn=baglam.sure_dakika,
            ust_sinir=int(tavan_saat * 60),
        )
        return None

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

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> None:
        izin_gunu = self.parametreler["haftalik_asgari_izin_gunu"]
        kayan_pencere_kisiti_ekle(
            model,
            baglam,
            pencere_uzunlugu=7,
            vardiyalar=baglam.vardiya_tipleri,
            agirlik_fn=lambda _v: 1,
            ust_sinir=7 - izin_gunu,
        )
        return None

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
    """Personel, musait olmadigi zaman araligiyla kesisen bir vardiyaya atanamaz (TD-4).

    modele_ekle bilerek bostur: model_kur, musait olmayan (p,g,v,n) icin hic
    karar degiskeni uretmez (SDD 5.3), bu yuzden ayrica bir kisit gerekmez.
    """

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> None:
        return None

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        return [
            Ihlal(
                kural_kimlik=self.kimlik,
                personel_id=atama.personel_id,
                tarih=atama.tarih,
                aciklama="Personel bu tarihte/vardiyada musait degil",
            )
            for atama in atamalar
            if not baglam.musait_mi(atama)
        ]


@kayitli("H8")
class H8OnkosulYetkinligi(ZorunluKural):
    """Bir noktaya atanan personel, o noktanin gerektirdigi yetkinlige sahip olmalidir (TD-9).

    modele_ekle bilerek bostur: model_kur, ön kosul yetkinligine sahip
    olmayan personel icin ilgili noktada hic karar degiskeni uretmez
    (SDD 5.3), bu yuzden ayrica bir kisit gerekmez.
    """

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> None:
        return None

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        ihlaller: list[Ihlal] = []
        for atama in atamalar:
            nokta = baglam.gorev_noktalari.get(atama.nokta_id)
            if nokta is None or nokta.onkosul_yetkinlik_id is None:
                continue
            if not baglam.yetkin_mi(atama.personel_id, nokta.onkosul_yetkinlik_id):
                ihlaller.append(
                    Ihlal(
                        kural_kimlik=self.kimlik,
                        personel_id=atama.personel_id,
                        tarih=atama.tarih,
                        aciklama=f"Personel, {atama.nokta_id} nolu noktanin gerektirdigi "
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
