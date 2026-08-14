"""H1-H10 zorunlu kisitlari (SRS Bolum 4.2, SDD Ek A ornek sablonu, SDD 5.3).

Her kuralin hem dogrula (elle kurulan atama listeleri uzerinde) hem
modele_ekle (gercek CP-SAT model nesnesi uzerinde) tarafi doludur; SDD
3.2.1'in "iki yorumlayici da ayni kural nesnesinden beslenir" ilkesiyle
tutarli.

BUTUN GUN BAZLI SAYIMLAR BLOGUN BASLADIGI GUNE YAZILIR (TD-1) ve tek bir
tabandan gecer: `Baglam.blok_saati` / `Baglam.calisti`. Duvar saatine dusen
bir sayim gece yarisini asan blogu bir kuralda bir gun, digerinde iki gun
gosterirdi.
"""

from ortools.sat.python import cp_model

from app.kurallar.baglam import AtamaKaydi, Baglam
from app.kurallar.kayit_defteri import kayitli
from app.kurallar.temel import Ihlal, ParametreTanimi, XAnahtari, ZorunluKural
from app.kurallar.yardimcilar import (
    ardisik_kosu_ihlalleri,
    calisilan_gunler,
    gece_gunleri,
    gunluk_saat,
    kayan_pencere_ihlalleri,
    kayan_pencere_kisiti_ekle,
    personel_bazinda_sirali,
    takvim_haftalari,
)

# SRS 3.3.5. Kural kaydinda parametre bulunmadiginda kullanilir; katalog
# disindan kurulan test baglamlari bu yoldan gecer.
_VARSAYILAN_ASGARI_BLOK_SAAT = 4
_VARSAYILAN_GECE_ESIGI_SAAT = 4


@kayitli("H1")
class H1GundeTekKesintisizCalisma(ZorunluKural):
    """Bir personelin bir takvim gunundeki calismasi TEK ve KESINTISIZDIR.

    ```
    bas[p,s] ≥ z[p,s] − z[p,s−1]              blok baslangici gostergesi
    bas[p,s] ≤ z[p,s]
    bas[p,s] ≤ 1 − z[p,s−1]
    ∀p, ∀d :  Σ_{s ∈ gün d} bas[p,s] ≤ 1
    ∀p, ∀d :  blok_saat[p,d] ≥ asgari_blok_saat · Σ_{s ∈ gün d} bas[p,s]
    ∀p, ∀s, ∀n :  x[p,s,n] ≥ z[p,s] + x[p,s−1,n] − 1      nokta sabitligi
    ```

    Kural once "gunde en fazla bir atama" idi ve blok katalogu altinda bunu
    soylemek yeterliydi - atama zaten bir blok secimiydi. Saat ekseninde
    ayni cumle uc ayri sey ister: gunde tek BASLANGIC, blogun asgari SURE,
    ve blok boyunca NOKTA SABITLIGI. Gun icinde bolunmus calisma (dort saat
    calisip ara verip bes saat daha) bu kuralla dislanir: ikinci bir aralik
    ikinci bir baslangic gostergesi uretir ve toplam bir sinirini asar.

    Gece yarisini asan bloklar kurali BOZMAZ - tasan saatler yeni bir
    baslangic uretmez ve blok basladigi gune sayilir (TD-1, TD-13).

    Gosterge degiskenleri (`bas`, `devir`) ve nokta sabitligi model kurucu
    tarafindan olusturulur: onlar kuralin degil EKSENIN yapisidir ve
    baglamdaki her ifade (H3, H5, H9, H10, S2, S3, S4) onlara dayanir.
    Burada kalan, kuralin kendi kararlari: gunde tek baslangic ve asgari
    sure.
    """

    ad = "Günde tek ve kesintisiz çalışma"
    aciklama = (
        "Bir personelin bir takvim gününde en fazla bir çalışma bloğu bulunur; blok "
        "kesintisizdir, asgari blok süresinden kısa olamaz ve blok boyunca görev noktası "
        "değişmez."
    )
    parametre_tanimlari = (
        ParametreTanimi(
            anahtar="asgari_blok_saat",
            etiket="Asgari blok süresi",
            birim="saat",
            asgari=1,
            azami=24,
        ),
    )

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> None:
        asgari = int(self.parametreler.get("asgari_blok_saat", _VARSAYILAN_ASGARI_BLOK_SAAT))
        for p in baglam.personel:
            for g in baglam.zaman_ekseni:
                baslangiclar = baglam.calisti(p, g)
                if isinstance(baslangiclar, int):
                    continue
                model.add(baslangiclar <= 1)
                # Bir gun calisma basladiysa o blogun suresi asgariye
                # ulasmali; hic calisilmayan gunde iki taraf da sifirdir.
                model.add(baglam.blok_saati(p, g) >= asgari * baslangiclar)
        return None

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        asgari = int(self.parametreler.get("asgari_blok_saat", _VARSAYILAN_ASGARI_BLOK_SAAT))
        ihlaller: list[Ihlal] = []
        for personel_id, sirali in personel_bazinda_sirali(atamalar).items():
            gunluk: dict[object, int] = {}
            for atama in sirali:
                gunluk[atama.tarih] = gunluk.get(atama.tarih, 0) + 1
                if atama.sure_saat < asgari:
                    ihlaller.append(
                        Ihlal(
                            kural_kimlik=self.kimlik,
                            personel_id=personel_id,
                            tarih=atama.tarih,
                            aciklama=f"Blok {atama.sure_saat} saat; asgari {asgari} saat",
                        )
                    )
            for tarih, sayi in sorted(gunluk.items()):
                if sayi > 1:
                    ihlaller.append(
                        Ihlal(
                            kural_kimlik=self.kimlik,
                            personel_id=personel_id,
                            tarih=tarih,
                            aciklama=f"{tarih} gununde {sayi} blok var; en fazla 1 olmali",
                        )
                    )
        return ihlaller


@kayitli("H2")
class H2AsgariDinlenme(ZorunluKural):
    """Ardisik iki blok arasindaki bosluk asgari_dinlenme_saati degerinden az olamaz.

    ```
    ∀p, ∀s :  d · bas[p,s] + Σ_{k=1..d} z[p,s−k] ≤ d
    ```

    Bir blogun bitisi, onu izleyen baslangictan onceki son calisilan
    saattir; dolayisiyla "baslangictan onceki d saat bostur" demek
    "bloklar arasinda en az d saat vardir" demektir. Kisit tek satirda
    yazilir: `bas = 1` iken toplam sifira zorlanir, `bas = 0` iken zaten
    saglanir. Her saat cifti icin ayri kisit yazmak ayni seyi d kat
    pahaliya soylerdi.
    """

    ad = "Asgari dinlenme süresi"
    aciklama = (
        "Ardışık iki blok arasındaki boşluk, tanımlı asgari dinlenme süresinden az olamaz. "
        "Gece vardiyasından çıkan personele ertesi sabah görev verilmesini engelleyen kuralın "
        "genel biçimidir."
    )
    parametre_tanimlari = (
        ParametreTanimi(
            anahtar="asgari_dinlenme_saati",
            etiket="Asgari dinlenme süresi",
            birim="saat",
            asgari=1,
            azami=72,
        ),
    )

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> None:
        d = int(self.parametreler["asgari_dinlenme_saati"])
        for (p, s), gosterge in baglam.bas.items():
            onceki_saatler = sum(baglam.zv(p, s - k) for k in range(1, d + 1))
            if isinstance(onceki_saatler, int) and onceki_saatler == 0:
                continue
            model.add(d * gosterge + onceki_saatler <= d)
        return None

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        d = self.parametreler["asgari_dinlenme_saati"]
        ihlaller: list[Ihlal] = []
        for personel_id, sirali in personel_bazinda_sirali(atamalar).items():
            for onceki, sonraki in zip(sirali, sirali[1:], strict=False):
                ara = (sonraki.baslangic - onceki.bitis).total_seconds() / 3600
                if ara < d:
                    ihlaller.append(
                        Ihlal(
                            kural_kimlik=self.kimlik,
                            personel_id=personel_id,
                            tarih=sonraki.tarih,
                            aciklama=f"Onceki blokla arada yalnizca {ara:.1f} saat var; "
                            f"en az {d} saat gerekli",
                        )
                    )
        return ihlaller


@kayitli("H3")
class H3ArdisikGeceUstSiniri(ZorunluKural):
    """Bir personel ust uste azami_ardisik_gece degerinden fazla GECE GUNU calisamaz.

    ```
    gece_saat[p,d] = blogun 20.00–06.00 ile kesisiminin uzunlugu
    gece_gunu[p,d] = 1  eger gece_saat[p,d] ≥ gece_esigi_saat
    ∀p, ∀d :  Σ_{i=0..N} gece_gunu[p,d+i] ≤ N
    ```

    Kural once vardiya tipi uzerindeki GECE BAYRAGINA dayaniyordu. Blok
    katalogu kalktigi icin isaretlenecek bir nesne kalmamistir; bir gunun
    gece gunu sayilip sayilmadigi, o gun gece saatlerinde gecirilen surenin
    esige ulasip ulasmadigindan HESAPLANIR (TD-2). Esik ergonomik yorumu
    tasir: iki saat gece calismak bir gece nobeti degildir.

    Bayragin kalkmasi ayni zamanda bir riski yapisal olarak ortadan
    kaldirir - bayragin otomatik hesaplanan bir oneriyle ezilmesi bir kez
    yasanmis ve K3'un karsilanmamasinin iki nedeninden biri olmustu. Artik
    H3 ile S2 tek bir tanimdan besleniyor.
    """

    ad = "Ardışık gece üst sınırı"
    aciklama = (
        "Bir personel üst üste tanımlı sayıdan fazla gece günü çalışamaz. Bir gün, gece "
        "saatlerinde geçirilen süre eşiğe ulaşıyorsa gece günü sayılır."
    )
    parametre_tanimlari = (
        ParametreTanimi(
            anahtar="azami_ardisik_gece",
            etiket="Azami ardışık gece",
            birim="gün",
            asgari=1,
            azami=14,
        ),
        ParametreTanimi(
            anahtar="gece_esigi_saat",
            etiket="Gece günü eşiği",
            birim="saat",
            asgari=1,
            azami=12,
        ),
    )

    def _esik(self) -> int:
        return int(self.parametreler.get("gece_esigi_saat", _VARSAYILAN_GECE_ESIGI_SAAT))

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> None:
        sinir = int(self.parametreler["azami_ardisik_gece"])
        esik = self._esik()
        # Gunun gece gunu olup olmadigi ESIKLI bir karardir ve gece saati bir
        # ifadedir; esigin gosterge degiskenine baglanmasi icin tek yonlu
        # zorlama yeter (gosterge yalnizca bir ust sinira giriyor, cozucu onu
        # gereksiz yere 1 tutmaz).
        gece_gunu: dict[tuple[int, object], cp_model.IntVar] = {}
        for p in baglam.personel:
            for g in baglam.zaman_ekseni:
                gece_saat = baglam.gece_blok_saati(p, g)
                if isinstance(gece_saat, int):
                    continue
                gosterge = model.new_bool_var(f"h3_gece_p{p}_g{g}")
                # gece_saat ≥ esik  =>  gosterge = 1
                model.add(gece_saat <= (esik - 1) + 24 * gosterge)
                gece_gunu[(p, g)] = gosterge

        gunler = baglam.zaman_ekseni
        for i in range(len(gunler) - sinir):
            pencere = gunler[i : i + sinir + 1]
            for p in baglam.personel:
                terimler = [gece_gunu[(p, g)] for g in pencere if (p, g) in gece_gunu]
                if terimler:
                    model.add(sum(terimler) <= sinir)
        return None

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        sinir = int(self.parametreler["azami_ardisik_gece"])
        gunler = gece_gunleri(atamalar, self._esik())
        return ardisik_kosu_ihlalleri(
            self.kimlik,
            gunler,
            sinir,
            "{kosu} ardisik gece gunu; en fazla {sinir} olmali",
        )


@kayitli("H4")
class H4ArdisikCalismaGunuUstSiniri(ZorunluKural):
    """Bir personel ust uste azami_ardisik_calisma_gunu degerinden fazla gun calisamaz."""

    ad = "Ardışık çalışma günü üst sınırı"
    aciklama = "Bir personel üst üste tanımlı sayıdan fazla gün çalışamaz."
    parametre_tanimlari = (
        ParametreTanimi(
            anahtar="azami_ardisik_calisma_gunu",
            etiket="Azami ardışık çalışma günü",
            birim="gün",
            asgari=1,
            azami=30,
        ),
    )

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> None:
        sinir = int(self.parametreler["azami_ardisik_calisma_gunu"])
        kayan_pencere_kisiti_ekle(
            model,
            baglam,
            pencere_uzunlugu=sinir + 1,
            gun_ifadesi=baglam.calisti,
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
    """Kayan yedi gunluk pencerede MUTLAK tavan (SRS 4.2 H5).

    Kural once kirk bes saatlik bir tavandi. Kirk bes saat artik tavan degil,
    fazla calismanin basladigi ESIKTIR ve H10'un parametresidir: haftalik
    kirk bes saatin uzerinde calismak yasak degildir, yillik kotaya yazilir.
    H5 ise dinlenme amacli, asilamayan ust siniri korur (varsayilan 66 =
    gunluk 11 saat x alti calisma gunu; H6 yedinci gunu izin birakir).

    Blogun suresi tamamiyla BASLADIGI gune yazilir (TD-7); pencerenin son
    gununde baslayan bir blogun ertesi gune tasan saatleri de o pencereye
    sayilir. Bilincli bir yaklasiklik - alternatifi blok suresini gunlere
    bolmektir ve modeli gereksiz karmasiklastirir.
    """

    ad = "Kayan yedi günlük mutlak tavan"
    aciklama = (
        "Herhangi bir yedi günlük pencerede toplam çalışma saati mutlak tavanı aşamaz. "
        "Fazla çalışmanın başladığı eşik ayrı bir kuraldır (H10)."
    )
    parametre_tanimlari = (
        ParametreTanimi(
            anahtar="haftalik_mutlak_tavan",
            etiket="Haftalık mutlak tavan",
            birim="saat",
            asgari=1,
            azami=168,
        ),
    )

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> None:
        kayan_pencere_kisiti_ekle(
            model,
            baglam,
            pencere_uzunlugu=7,
            gun_ifadesi=baglam.blok_saati,
            ust_sinir=int(self.parametreler["haftalik_mutlak_tavan"]),
        )
        return None

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        tavan = self.parametreler["haftalik_mutlak_tavan"]
        return kayan_pencere_ihlalleri(
            self.kimlik,
            gunluk_saat(atamalar),
            tavan,
            "7 gunluk pencerede {toplam:.1f} saat; mutlak tavan {sinir} saat",
        )


@kayitli("H6")
class H6HaftalikAsgariIzinGunu(ZorunluKural):
    """Herhangi bir yedi gunluk pencerede en az haftalik_asgari_izin_gunu kadar bos gun olmali."""

    ad = "Haftalık asgari izin günü"
    aciklama = (
        "Herhangi bir yedi günlük pencerede en az bir tam gün çalışılmamalıdır. Yasal "
        "dayanağı H4’ten farklı olduğu için ayrı tutulur."
    )
    parametre_tanimlari = (
        ParametreTanimi(
            anahtar="haftalik_asgari_izin_gunu",
            etiket="Haftalık asgari izin günü",
            birim="gün",
            asgari=0,
            azami=6,
        ),
    )

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> None:
        izin_gunu = int(self.parametreler["haftalik_asgari_izin_gunu"])
        kayan_pencere_kisiti_ekle(
            model,
            baglam,
            pencere_uzunlugu=7,
            gun_ifadesi=baglam.calisti,
            ust_sinir=7 - izin_gunu,
        )
        return None

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        izin_gunu = self.parametreler["haftalik_asgari_izin_gunu"]
        gunler = calisilan_gunler(atamalar)
        calisma_gostergesi = {
            personel_id: dict.fromkeys(gunler_kumesi, 1.0)
            for personel_id, gunler_kumesi in gunler.items()
        }
        return kayan_pencere_ihlalleri(
            self.kimlik,
            calisma_gostergesi,
            7 - izin_gunu,
            "7 gunluk pencerede {toplam:.0f} gun calisilmis; en fazla {sinir:.0f} olmali",
        )


@kayitli("H7")
class H7Musaitlik(ZorunluKural):
    """Personel, musait olmadigi zaman araligiyla kesisen bir saatte calisamaz (TD-4).

    modele_ekle bilerek bostur: model_kur, musait olmayan (p,s) icin hic
    karar degiskeni uretmez (SDD 5.3), bu yuzden ayrica bir kisit gerekmez.
    """

    ad = "Müsaitlik"
    aciklama = (
        "Personel, müsait olmadığı zaman aralığıyla kesişen bir saatte çalışamaz. Aktiflik "
        "tarih aralığı dışındaki günler de müsait değil sayılır."
    )

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
                aciklama="Personel blogun kapsadigi saatlerin bir kisminda musait degil",
            )
            for atama in atamalar
            if any(not baglam.musait_mi(atama.personel_id, an) for an in atama.saatler())
        ]


@kayitli("H8")
class H8OnkosulYetkinligi(ZorunluKural):
    """Bir noktaya atanan personel, o noktanin gerektirdigi yetkinlige sahip olmalidir (TD-9).

    modele_ekle bilerek bostur: model_kur, on kosul yetkinligine sahip
    olmayan personel icin ilgili noktada hic karar degiskeni uretmez
    (SDD 5.3), bu yuzden ayrica bir kisit gerekmez.
    """

    ad = "Ön koşul yetkinliği"
    aciklama = (
        "Bir görev noktasına atanan personel, o noktanın gerektirdiği yetkinliğe sahip olmak "
        "zorundadır. Ön koşulu bulunmayan noktalara her personel atanabilir."
    )

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
                        aciklama=f"Personel, {baglam.nokta_adi(atama.nokta_id)} noktasinin "
                        f"gerektirdigi {baglam.yetkinlik_adi(nokta.onkosul_yetkinlik_id)} "
                        "yetkinligine sahip degil",
                    )
                )
        return ihlaller


@kayitli("H9")
class H9GunlukAzamiSaat(ZorunluKural):
    """Bir personelin bir takvim gunundeki calisma suresi gunluk tavani asamaz.

    ```
    ∀p, ∀d :  blok_saat[p,d] ≤ azami_gunluk_saat
    ```

    H1'in asgari sure kosuluyla birlikte blogun alt ve ust sinirini cizer:
    bir gunluk calisma dort saatten kisa, on bir saatten uzun olamaz.

    TAVAN DUVAR SAATINE DEGIL BLOGA UYGULANIR (TD-1). Duvar saati okumasi
    20.00–08.00 blogunu 4 + 8 saat diye gorur; ikisi de tavanin altinda
    kalir ve on iki saatlik blok kuraldan gecerdi. H9 o zaman blok
    uzunlugunu hic sinirlamiyor olurdu.
    """

    ad = "Günlük azami çalışma süresi"
    aciklama = "Bir personelin bir takvim günündeki toplam çalışma süresi tavanı aşamaz."
    parametre_tanimlari = (
        ParametreTanimi(
            anahtar="azami_gunluk_saat",
            etiket="Günlük azami çalışma",
            birim="saat",
            asgari=1,
            azami=24,
        ),
    )

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> None:
        # Tek gunluk kayan pencere = takvim gunu; ayri bir dongu yazmak ayni
        # kisiti ikinci kez tanimlamak olurdu.
        kayan_pencere_kisiti_ekle(
            model,
            baglam,
            pencere_uzunlugu=1,
            gun_ifadesi=baglam.blok_saati,
            ust_sinir=int(self.parametreler["azami_gunluk_saat"]),
        )
        return None

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        tavan = self.parametreler["azami_gunluk_saat"]
        ihlaller: list[Ihlal] = []
        for personel_id, gunler in gunluk_saat(atamalar).items():
            for gun, saat in sorted(gunler.items()):
                if saat > tavan:
                    ihlaller.append(
                        Ihlal(
                            kural_kimlik=self.kimlik,
                            personel_id=personel_id,
                            tarih=gun,
                            aciklama=f"Gunluk {saat:.1f} saat; tavan {tavan} saat",
                        )
                    )
        return ihlaller


@kayitli("H10")
class H10YillikFazlaCalismaKotasi(ZorunluKural):
    """Haftalik esigin uzerinde calisilan saatlerin yillik toplami kotayi asamaz.

    ```
    W          : donemin dokundugu takvim haftalari (pazartesi-pazar, TD-14)
    saat[p,w]  = Σ_{d ∈ w} blok_saat[p,d]
    fazla[p,w] ≥ saat[p,w] − fazla_calisma_esigi
    fazla[p,w] ≥ 0
    ∀p :  devir[p] + Σ_{w ∈ W} fazla[p,w] ≤ yillik_fazla_kotasi
    ```

    TAKVIM HAFTASI, KAYAN PENCERE DEGIL (TD-14). Kota "haftalik esigin
    ustunde calisilan saatlerin toplami"dir ve bir toplam ancak ORTUSMEYEN
    pencerelerde anlamlidir; kayan pencerede ayni saat yedi ayri pencereye
    girer ve toplam yedi katina cikar. Hafta kumeleri bu yuzden
    `takvim_haftalari` ile, kayan pencere yardimcisindan AYRI uretilir.

    KURAL ZORUNLUDUR AMA MODELI COZULEMEZ YAPMAZ: yalnizca fazla calismayi
    sinirlar, calismayi degil. Kotasi dolmus bir personel haftalik esige
    kadar calismaya devam eder, yalnizca ustune cikamaz - `fazla[p,w] = 0`
    her zaman uygulanabilir bir degerdir. Tek istisna `devir[p]`in kotayi
    zaten asmis olmasidir; bu bir VERI HATASIDIR ve on kontrolde bildirilir
    (FR-5.1), cozum aninda degil.
    """

    ad = "Yıllık fazla çalışma kotası"
    aciklama = (
        "Haftalık eşiğin üzerinde çalışılan saatlerin kota yılı içindeki toplamı, yıllık "
        "kotayı aşamaz. Devir bakiyesi personel kaydından okunur."
    )
    parametre_tanimlari = (
        ParametreTanimi(
            anahtar="fazla_calisma_esigi",
            etiket="Fazla çalışma eşiği",
            birim="saat/hafta",
            asgari=1,
            azami=168,
        ),
        ParametreTanimi(
            anahtar="yillik_fazla_kotasi",
            etiket="Yıllık fazla çalışma kotası",
            birim="saat",
            asgari=0,
            azami=2000,
        ),
    )

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> None:
        esik = int(self.parametreler["fazla_calisma_esigi"])
        kota = int(self.parametreler["yillik_fazla_kotasi"])
        # W = DONEMIN DOKUNDUGU takvim haftalari (SRS 4.2 H10). Tumuyle
        # isitma penceresinde kalan bir hafta W'ye girmez: orasi gecmistir ve
        # `devir[p]` ile temsil edilir; iki kez sayilmasi kotayi olmadigi
        # kadar dolu gosterirdi.
        haftalar = {
            hafta_basi: gunler
            for hafta_basi, gunler in takvim_haftalari(baglam.zaman_ekseni).items()
            if any(baglam.donem_icinde(g) for g in gunler)
        }
        for p in baglam.personel:
            fazlalar = []
            for hafta_basi, gunler in sorted(haftalar.items()):
                # HAFTANIN DONEM DISI GUNLERI DE SAYILIR (TD-6). Onlarin
                # degiskenleri isitma penceresinde SABITLENMISTIR (SDD 5.3),
                # dolayisiyla toplama sabit terim olarak girerler. Disarida
                # birakilmalari halinde donem sinirindaki hafta EKSIK olculur
                # ve kota sessizce asilir - kuralin hic bulunmamasiyla ayni
                # sonucu verir.
                haftalik = sum(baglam.blok_saati(p, g) for g in gunler)
                if isinstance(haftalik, int):
                    continue
                fazla = model.new_int_var(0, 7 * 24, f"h10_fazla_p{p}_w{hafta_basi}")
                model.add(fazla >= haftalik - esik)
                fazlalar.append(fazla)
            if not fazlalar:
                continue
            devir = int(round(baglam.devir_fazla_calisma_saat(p)))
            model.add(sum(fazlalar) <= max(kota - devir, 0))
        return None

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        esik = float(self.parametreler["fazla_calisma_esigi"])
        kota = float(self.parametreler["yillik_fazla_kotasi"])
        fazlalar = h10_fazla_calisma_saatleri(atamalar, baglam, esik)
        ihlaller: list[Ihlal] = []
        for personel_id in sorted(baglam.personel):
            toplam_fazla = fazlalar.get(personel_id, 0.0)
            devir = baglam.devir_fazla_calisma_saat(personel_id)
            if devir + toplam_fazla > kota:
                ihlaller.append(
                    Ihlal(
                        kural_kimlik=self.kimlik,
                        personel_id=personel_id,
                        aciklama=(
                            f"Devir {devir:.1f} + donem fazlasi {toplam_fazla:.1f} = "
                            f"{devir + toplam_fazla:.1f} saat; yillik kota {kota:.0f} saat"
                        ),
                    )
                )
        return ihlaller


def h10_fazla_calisma_saatleri(
    atamalar: list[AtamaKaydi], baglam: Baglam, esik: float
) -> dict[int, float]:
    """Kisi basina DONEM ICINDEKI fazla calisma saati (SRS 4.2 H10).

    Haftalik toplamin esigi astigi kadari, donemin dokundugu her takvim
    haftasi icin toplanir. Tumuyle isitma penceresinde kalan hafta W'ye
    girmez: orasi gecmistir ve `devir[p]` ile temsil edilir; iki kez
    sayilmasi kotayi olmadigi kadar dolu gosterirdi.

    H10'un `dogrula`si ve DISA AKTARMA ayni fonksiyondan beslenir. Disa
    aktarmanin kendi toplamini hesaplamasi, dosyada ekranda hic bulunmayan
    bir sayi olusturmasi demekti (SDD 5.8: "ikinci bir hesap yapmaz").
    """
    saatler = gunluk_saat(atamalar)
    sonuc: dict[int, float] = {}
    for personel_id in sorted(baglam.personel):
        gunluk = saatler.get(personel_id, {})
        toplam = 0.0
        for gunler in takvim_haftalari(gunluk).values():
            if not any(baglam.donem_icinde(g) for g in gunler):
                continue
            toplam += max(sum(gunluk[g] for g in gunler) - esik, 0.0)
        sonuc[personel_id] = toplam
    return sonuc


__all__ = [
    "h10_fazla_calisma_saatleri",
    "H1GundeTekKesintisizCalisma",
    "H2AsgariDinlenme",
    "H3ArdisikGeceUstSiniri",
    "H4ArdisikCalismaGunuUstSiniri",
    "H5KayanHaftalikSaatTavani",
    "H6HaftalikAsgariIzinGunu",
    "H7Musaitlik",
    "H8OnkosulYetkinligi",
    "H9GunlukAzamiSaat",
    "H10YillikFazlaCalismaKotasi",
]
