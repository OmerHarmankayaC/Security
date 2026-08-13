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
from app.kurallar.temel import Ihlal, ParametreTanimi, XAnahtari, ZorunluKural
from app.kurallar.yardimcilar import (
    ardisik_kosu_ihlalleri,
    calisilan_gunler,
    gece_calisilan_gunler,
    gunluk_saat,
    kayan_pencere_ihlalleri,
    kayan_pencere_kisiti_ekle,
    personel_bazinda_sirali,
    takvim_haftalari,
)


@kayitli("H1")
class H1GundeBirVardiya(ZorunluKural):
    """Bir personel bir takvim gununde en fazla bir vardiyaya atanabilir. Parametresizdir."""

    ad = "Günde en fazla bir vardiya"
    aciklama = (
        "Bir personel bir takvim gününde en fazla bir vardiyaya ve o vardiya içinde en fazla "
        "bir görev noktasına atanabilir."
    )

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

    ad = "Asgari dinlenme süresi"
    aciklama = (
        "Ardışık iki atama arasındaki boşluk, tanımlı asgari dinlenme süresinden az olamaz. "
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

    ad = "Ardışık gece üst sınırı"
    aciklama = "Bir personel üst üste tanımlı sayıdan fazla gece vardiyası tutamaz."
    parametre_tanimlari = (
        ParametreTanimi(
            anahtar="azami_ardisik_gece",
            etiket="Azami ardışık gece",
            birim="vardiya",
            asgari=1,
            azami=14,
        ),
    )

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
    """Kayan yedi gunluk pencerede MUTLAK tavan (SRS 4.2 H5).

    Kural once kirk bes saatlik bir tavandi. Kirk bes saat artik tavan degil,
    fazla calismanin basladigi ESIKTIR ve H10'un parametresidir: haftalik
    kirk bes saatin uzerinde calismak yasak degildir, yillik kotaya yazilir.
    H5 ise dinlenme amacli, asilamayan ust siniri korur (varsayilan 66 =
    gunluk 11 saat x alti calisma gunu; H6 yedinci gunu izin birakir).
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
        tavan_saat = self.parametreler["haftalik_mutlak_tavan"]
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
        tavan = self.parametreler["haftalik_mutlak_tavan"]
        saatler = gunluk_saat(atamalar, baglam)
        return kayan_pencere_ihlalleri(
            self.kimlik,
            saatler,
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

    ad = "Müsaitlik"
    aciklama = (
        "Personel, müsait olmadığı zaman aralığıyla kesişen bir vardiyaya atanamaz. Aktiflik "
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
                        aciklama=f"Personel, {atama.nokta_id} nolu noktanin gerektirdigi "
                        f"{nokta.onkosul_yetkinlik_id} nolu yetkinlige sahip degil",
                    )
                )
        return ihlaller


@kayitli("H9")
class H9GunlukAzamiSaat(ZorunluKural):
    """Bir personelin bir takvim gunundeki calisma suresi gunluk tavani asamaz.

    ```
    ∀p, ∀d :  Σ_b sure[b] · y[p,d,b] ≤ azami_gunluk_saat
    ```

    H1 bir gunde en fazla bir blok verdiginden bu kural PRATIKTE "katalogdaki
    hicbir blok gunluk tavani asamaz" demeye gelir ve ayni sinir blok
    tanimlanirken de uygulanir (FR-1.3) - gecersiz veriyi giriste durdurmak,
    dakikalar suren bir cozumun sonunda kesfetmekten ucuzdur. Kural yine de
    AYRI yazilir: yasal dayanagi H1'den bagimsizdir ve H1'in gelecekte
    gevsetilmesi halinde tek basina gecerliligini korumalidir. Gerekce
    H6'nin H4 karsisindaki durumuyla ayni.

    BLOK KATALOGU KISITI BU PARAMETREYI OKUR (`TanimServisi`); iki ayri deger
    tanimlanmaz. Ayrisirlarsa girisi gecen bir blok cozumde her gun ayni
    ihlali uretir.
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
        # Tek gunluk kayan pencere = takvim gunu; ayri bir dongu yazmak
        # ayni kisiti ikinci kez tanimlamak olurdu.
        kayan_pencere_kisiti_ekle(
            model,
            baglam,
            pencere_uzunlugu=1,
            vardiyalar=baglam.vardiya_tipleri,
            agirlik_fn=baglam.sure_dakika,
            ust_sinir=int(self.parametreler["azami_gunluk_saat"] * 60),
        )
        return None

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        tavan = self.parametreler["azami_gunluk_saat"]
        ihlaller: list[Ihlal] = []
        for personel_id, gunler in gunluk_saat(atamalar, baglam).items():
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
    saat[p,w]  = Σ_{d ∈ w} Σ_b sure[b] · y[p,d,b]
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
        esik_dk = int(self.parametreler["fazla_calisma_esigi"] * 60)
        kota_dk = int(self.parametreler["yillik_fazla_kotasi"] * 60)
        # Dakika cinsinden calisilir: sure_saat kesirli olabilir, CP-SAT
        # tamsayi katsayi ister ve ayni donusum H5'te de kullaniliyor.
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
                # HAFTANIN DONEM DISI GUNLERI DE SAYILIR (TD-6). Onlarin y
                # degiskenleri isitma penceresinde SABITLENMISTIR (SDD 5.3),
                # dolayisiyla toplama sabit terim olarak girerler. Disarida
                # birakilmalari halinde donem sinirindaki hafta EKSIK olculur
                # ve kota sessizce asilir - kuralin hic bulunmamasiyla ayni
                # sonucu verir. Isitma penceresinden de once kalan gunler
                # zaman ekseninde bulunmaz ve sifir sayilir.
                haftalik = sum(
                    baglam.sure_dakika(v) * baglam.y[(p, g, v)]
                    for g in gunler
                    for v in baglam.vardiya_tipleri
                    if (p, g, v) in baglam.y
                )
                fazla = model.new_int_var(0, 7 * 24 * 60, f"h10_fazla_p{p}_w{hafta_basi}")
                model.add(fazla >= haftalik - esik_dk)
                fazlalar.append(fazla)
            if not fazlalar:
                continue
            devir_dk = int(round(baglam.devir_fazla_calisma_saat(p) * 60))
            model.add(sum(fazlalar) <= max(kota_dk - devir_dk, 0))
        return None

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        esik = float(self.parametreler["fazla_calisma_esigi"])
        kota = float(self.parametreler["yillik_fazla_kotasi"])
        saatler = gunluk_saat(atamalar, baglam)
        ihlaller: list[Ihlal] = []
        for personel_id in sorted(baglam.personel):
            gunluk = saatler.get(personel_id, {})
            # modele_ekle ile AYNI hafta kumesi: donemin dokundugu haftalar.
            # Iki yorumlayicinin ayni sayiyi uretmesi zorunludur (SDD 3.2.1).
            toplam_fazla = 0.0
            for gunler in takvim_haftalari(gunluk).values():
                if not any(baglam.donem_icinde(g) for g in gunler):
                    continue
                haftalik = sum(gunluk[g] for g in gunler)
                toplam_fazla += max(haftalik - esik, 0.0)
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


__all__ = [
    "H1GundeBirVardiya",
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
