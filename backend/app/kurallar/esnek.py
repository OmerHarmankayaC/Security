"""S1-S8 esnek hedefleri (SRS Bolum 4.3, SDD Ek A ornek sablonu - S2).

dogrula metotlari, SDD Ek A'daki S2 ornegiyle tutarli olarak agirliksiz
(ham) ceza buyuklugu dondurur; agirlikli toplam (w1..w8) amac fonksiyonu
(SDD 5.3, Sprint 2 Gun 6) ve ceza dokumu raporlamasi (SDD 5.7,
Sprint 3 Gun 12) tarafindan hesaplanir.
"""

from collections import defaultdict
from collections.abc import Callable
from datetime import date, time, timedelta
from math import ceil, floor

from ortools.sat.python import cp_model

from app.kurallar.baglam import AtamaKaydi, Baglam
from app.kurallar.kayit_defteri import kayitli
from app.kurallar.temel import EsnekHedef, Ihlal, KuralKapsami, XAnahtari
from app.kurallar.yardimcilar import calisilan_gunler
from app.kurallar.zaman_araligi import aralik_sure_saat as _aralik_sure_saat
from app.kurallar.zaman_araligi import saatleri_araliklara_birlestir
from app.models.girdi import TercihTipi


def _saat_metni(an: time) -> str:
    """Saati "08.00" bicimiyle yazar; gun sonu 24.00 olarak gosterilir."""
    return f"{an.hour:02d}.00" if an.hour else "24.00"


@kayitli("S1")
class S1TalepKarsilama(EsnekHedef):
    """Nokta bazinda kapsama acigi: baskin agirlikli, alt sinir esnek hedef."""

    ad = "Talep karşılama"
    aciklama = (
        "Karşılanamayan her kişilik talep ceza üretir. Ağırlığı diğerlerinin toplamından "
        "belirgin biçimde büyük seçilir; böylece çözücü başka bir hedefi iyileştirmek için "
        "kapsama açığı bırakmaz."
    )

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> cp_model.LinearExprT:
        """SRS S1: kapsama kisiti SAAT EKSENINDE yazilir.

        ```
        ∀d, ∀t (saat), ∀n :
            Σ_p Σ_{b ∋ t} x[p,d,b,n] + eksik[d,t,n] ≥ talep[d,t,n]   (alt sinir, esnek)
            Σ_p Σ_{b ∋ t} x[p,d,b,n]                ≤ talep[d,t,n]   (ust sinir, zorunlu)
        ```

        Talep bir bloga degil bir ZAMAN ARALIGINA baglidir (SRS 3.3.4,
        TD-13); bir personel bir saatte, o saati kapsayan bloga atanmissa
        sayilir. Bloklarin uzunluklari farkli olabildiginden ayni saati
        farkli bloklardan gelen personel birlikte doldurabilir - blok
        eksenli eski kisit bunu ifade edemiyordu.

        Ceza SAAT BASINA birikir: iki saat bir kisi eksik kalmak, bir saat
        iki kisi eksik kalmakla ayni cezayi uretir. Ikisi de ayni miktarda
        karsilanmamis kisi-saattir.

        UST SINIR BU TURDA ZORUNLU KALIR (K4 Tur 4'un isi). Uc blok talep
        araliklariyla hizali oldugu icin sorun cikarmaz; hizalanmayan bir
        katalogda bir saatte fazla kadro YAPISAL olarak kacinilmaz olur ve
        model cozulemez hale gelir.
        """
        # Bir blogun kapsadigi saatler o gunun disina tasabilir (gece
        # yarisini asan blok); atamayi ilgili saate baglayan tablo bu.
        saati_kapsayan: dict[tuple[date, int], frozenset[tuple[date, int]]] = defaultdict(frozenset)
        for g in baglam.zaman_ekseni or baglam.donem_gunleri:
            for v in baglam.vardiya_tipleri:
                for saat_gunu, saat in baglam.blok_saatleri(g, v):
                    saati_kapsayan[(saat_gunu, saat)] |= {(g, v)}

        # AYNI KISITI URETEN SAATLER TEK DEGISKENDE TOPLANIR. Talep araliklari
        # blok sinirlariyla hizali oldugunda bir blogun sekiz saati ayni
        # personel kumesini ve ayni gerekeni tasir; her saate ayri bir `eksik`
        # degiskeni acmak sekiz BIRBIRININ YERINE GECEBILEN degisken uretir ve
        # cozucu bu simetriyi kirmak zorunda kalir - olculdu: ayni donem 120
        # saniyede sifir aciktan 704 kisi-saat acikla cikiyordu. Gruplama
        # ANLAMI DEGISTIRMEZ: ceza saat basina birikmeye devam eder, cunku
        # degiskenin amac fonksiyonundaki katsayisi grubun saat sayisidir.
        gruplar: dict[tuple[frozenset[tuple[date, int]], int, int], list[tuple[date, int]]] = (
            defaultdict(list)
        )
        for (saat_gunu, saat, n), gereken in sorted(baglam.talep_saat.items()):
            if gereken == 0 or not baglam.donem_icinde(saat_gunu):
                continue
            gruplar[(saati_kapsayan[(saat_gunu, saat)], gereken, n)].append((saat_gunu, saat))

        ceza_terimi: cp_model.LinearExprT = 0
        for (kapsayanlar, gereken, n), saatler in gruplar.items():
            ilgili = [
                degiskenler[(p, g, v, n)]
                for (g, v) in sorted(kapsayanlar)
                for p in baglam.personel
                if (p, g, v, n) in degiskenler
            ]
            atanan_ifadesi = sum(ilgili) if ilgili else 0
            model.add(atanan_ifadesi <= gereken)
            ilk_gun, ilk_saat = min(saatler)
            eksik = model.new_int_var(0, gereken, f"s1_eksik_g{ilk_gun}_t{ilk_saat}_n{n}")
            model.add(atanan_ifadesi + eksik >= gereken)
            # Katsayi = grubun kapsadigi saat sayisi; bir kisi bir saat eksik
            # kalmak bir birim ceza uretir (SRS 4.3 S1).
            ceza_terimi = ceza_terimi + len(saatler) * eksik
            # Cozumden sonra kapsama_acigi tablosuna SAAT SAAT yazilabilmesi
            # icin grubun her saati ayni degiskene bakar.
            for saat_gunu, saat in saatler:
                baglam.kapsama_eksikleri[(saat_gunu, saat, n)] = eksik
        return ceza_terimi

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        """S1'in IKI YARISI da denetlenir.

        Once yalnizca alt sinir (kapsama acigi) bakiliyordu; ust sinir
        (`atanan > gereken`) hicbir yerde sorulmuyordu. Sonuc: elle
        duzenlemede bir noktaya talepten fazla kisi yazilabiliyor ve sistem
        sessizce kabul ediyordu - oysa `modele_ekle` ayni kisiti cozucuye
        ZORUNLU olarak ekliyor. Iki yorumlayicinin ayrismasi SDD 3.2.1'e
        gore yazilim hatasidir; mevcut uyum testi de bunu yakalayamaz,
        cunku yalnizca COZUCUNUN URETTIGI cizelgeleri dogrulayiciya verir
        ve cozucu zaten fazla kadro uretemez.

        FAZLA KADRO CEZA URETMEZ, uyari uretir (ceza=None). Gerekcesi
        SRS 4.4'teki amac fonksiyonudur: orada fazla kadroya karsilik gelen
        bir terim YOKTUR (cozucu tarafinda kisit, ceza degil). Buraya bir
        ceza sayisi uydurmak, cozucunun hicbir zaman hesaplamayacagi bir
        buyuklugu ceza dokumune sokar ve iki yorumlayici ayni cizelge icin
        farkli toplam uretirdi. Bulgu kullaniciya metin olarak gider
        (urun karari, 11.08.2026: fazla kadro engel degil uyaridir).
        """
        # Talep ile atamanin farki BAGLAMDA tek yerde tanimli; sapma
        # tablolarini yazan yol da ayni tanimi kullanir (SDD 3.2.1).
        # Bulgu SAAT SAAT degil ARALIK olarak bildirilir: yirmi dort satirlik
        # bir liste kullaniciya hicbir sey anlatmaz (SRS 4.3 S1).
        eksik_saatler, fazla_saatler = baglam.sapma_saatleri(atamalar)

        ihlaller: list[Ihlal] = []
        for nokta_id, saatler in sorted(eksik_saatler.items()):
            for tarih, bas, bit, sayi in saatleri_araliklara_birlestir(saatler):
                ihlaller.append(
                    Ihlal(
                        kural_kimlik=self.kimlik,
                        tarih=tarih,
                        ceza=sayi * _aralik_sure_saat(bas, bit),
                        aciklama=(
                            f"{self._yer_metni(baglam, tarih, bas, bit, nokta_id)} — "
                            f"{sayi} kişi eksik"
                        ),
                    )
                )
        for nokta_id, saatler in sorted(fazla_saatler.items()):
            for tarih, bas, bit, sayi in saatleri_araliklara_birlestir(saatler):
                ihlaller.append(
                    Ihlal(
                        kural_kimlik=self.kimlik,
                        tarih=tarih,
                        ceza=None,
                        aciklama=(
                            f"{self._yer_metni(baglam, tarih, bas, bit, nokta_id)} — "
                            f"talepten {sayi} kişi fazla"
                        ),
                    )
                )
        return ihlaller

    @staticmethod
    def _yer_metni(baglam: Baglam, tarih: date, baslangic: time, bitis: time, nokta_id: int) -> str:
        """ "2026-02-02 · 00.00–08.00 · Vardiya Şefliği" — kimlik degil AD (NFR-5).

        Eski metin "3 nolu vardiyada 2 nolu noktada" diyordu; o sayilar
        veritabani kimlikleri ve kullaniciya hicbir sey anlatmiyordu.
        """
        return (
            f"{tarih.isoformat()} · {_saat_metni(baslangic)}–{_saat_metni(bitis)} · "
            f"{baglam.nokta_adi(nokta_id)}"
        )


@kayitli("S2")
class S2GeceAdaleti(EsnekHedef):
    """Kisi basina gece vardiyasi sayisinin donem hedefinden sapmasi (SRS 4.3 S2).

    SDD 5.5 (surum 1.3): donem geneli kapsamli - taban/tavan donem genelindeki
    en dusuk/en yuksek degerden turedigi icin pencereyle sinirlandirilamaz.
    """

    ad = "Gece adaleti"
    aciklama = (
        "Kişi başına düşen gece sayısının hedeften sapması cezalandırılır. Hedef, yalnızca "
        "gece görevi alabilecek personele bölünür."
    )

    kapsam = KuralKapsami.DONEM_GENELI

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> cp_model.LinearExprT:
        """SRS 4.3 S2'nin dogrudan cevirisi (SDD Ek A'nin eski araligi minimize
        eden ornegi normatif SRS formuluyle celisiyordu, sdd.docx surum 1.4'te
        duzeltildi): hedef_gece = talep/|P|, sapma[p] = max(sayi-taban, tavan-sayi, 0)."""
        gunler = baglam.donem_gunleri
        ust_sinir = len(gunler)
        gece_sayisi = {
            p: sum(baglam.y[(p, g, v)] for g in gunler for v in baglam.gece_vardiyalari)
            for p in baglam.personel
        }
        return _adalet_sapmasi_terimi(
            model=model,
            baglam=baglam,
            sayilar=gece_sayisi,
            ust_sinir=ust_sinir,
            talep_uygun_mu=lambda anahtar: baglam.gece_mi(anahtar[1]),
            degisken_onek="s2_sapma",
        )

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        return _adalet_sapmasi_ihlalleri(
            kural_kimlik=self.kimlik,
            atamalar=atamalar,
            baglam=baglam,
            atama_uygun_mu=lambda a: baglam.gece_mi(a.vardiya_tipi_id),
            talep_uygun_mu=lambda anahtar: baglam.gece_mi(anahtar[1]),
            aciklama="gece vardiyasi sayisi donem hedefinden sapiyor",
        )


@kayitli("S3")
class S3HaftaSonuAdaleti(EsnekHedef):
    """Kisi basina hafta sonu/resmi tatil vardiyasi sayisinin hedeften sapmasi (TD-3).

    SDD 5.5 (surum 1.3): donem geneli kapsamli, S2 ile ayni gerekce.
    """

    ad = "Hafta sonu adaleti"
    aciklama = (
        "Kişi başına düşen hafta sonu ve resmî tatil vardiyası sayısının hedeften sapması "
        "cezalandırılır."
    )

    kapsam = KuralKapsami.DONEM_GENELI

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> cp_model.LinearExprT:
        """S2 ile ayni formulasyon; gece[s] yerine hs[d] kullanilir (SRS S3)."""
        hs_gunleri = [g for g in baglam.donem_gunleri if baglam.hafta_sonu_mu(g)]
        ust_sinir = len(hs_gunleri) * max(len(baglam.vardiya_tipleri), 1)
        hs_sayisi = {
            p: sum(baglam.y[(p, g, v)] for g in hs_gunleri for v in baglam.vardiya_tipleri)
            for p in baglam.personel
        }
        return _adalet_sapmasi_terimi(
            model=model,
            baglam=baglam,
            sayilar=hs_sayisi,
            ust_sinir=ust_sinir,
            talep_uygun_mu=lambda anahtar: baglam.hafta_sonu_mu(anahtar[0]),
            degisken_onek="s3_sapma",
        )

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        return _adalet_sapmasi_ihlalleri(
            kural_kimlik=self.kimlik,
            atamalar=atamalar,
            baglam=baglam,
            atama_uygun_mu=lambda a: baglam.hafta_sonu_mu(a.tarih),
            talep_uygun_mu=lambda anahtar: baglam.hafta_sonu_mu(anahtar[0]),
            aciklama="hafta sonu/resmi tatil vardiyasi sayisi donem hedefinden sapiyor",
        )


S4_OLCEK = 10  # SDD Ek A "Kesirli hedeflerin tamsayiya olceklenmesi": onda bir saat


@kayitli("S4")
class S4ToplamSaatDengesi(EsnekHedef):
    """Kisi basina toplam saatin, kisisel dagilim payindan mutlak sapmasi (SRS v1.2/1.3).

    Not: eski formul (hedef_saat[p] = haftalik_hedef_saat[p] * donem_gun_sayisi/7)
    H5 (haftalik saat tavani) + H6 (haftalik asgari izin) altinda hic kimse kisisel
    hedefini asamadigindan (herkes hedefin es ya da altinda kalir, ve Sigma saat[p]
    talep tarafindan sabitlenmis oldugundan) Sigma|saat[p]-hedef_saat[p]| dagilimdan
    bagimsiz SABIT bir sayi uretiyordu - amac fonksiyonuna ekleniyor ama hicbir
    optimizasyon sinyali vermiyordu (bkz. PROGRESS.md, Ek Gorev 2. tur). Yeni formul,
    hedefi kisinin donemlik hedef saatine gore degil, donemin toplam talep saatinden
    kisiye dusen PAYA gore tanimlar - bu pay gercekten ulasilabilir oldugundan sapma
    iki yonlu olabilir ve S4 gercekten dengesizligi olcer:
        toplam_talep_saat = Sigma sure[s]*talep[d,s,n]   (yalniz baglam.donem_icinde)
        pay[p] = (hedef_saat[p] / Sigma_q hedef_saat[q]) * toplam_talep_saat
        Ceza: w4 * Sigma_p |saat[p] - pay[p]|

    Olcekleme (SDD Ek A, "Kesirli hedeflerin tamsayiya olceklenmesi"): pay[p]
    kesirli cikabildigi ve dogrudan bir mutlak sapma hesabina girdigi icin (S2/S3'un
    taban/tavan hilesi burada calismaz) CP-SAT'in tamsayi kisiti geregi hem pay hem
    calisma saati S4_OLCEK (onda bir saat) ile olceklenip tamsayiya cevrilir. Bu
    yalnizca modelin IC temsilidir: modele_ekle'nin dondurdugu terim,
    add_division_equality ile (yarim birimi yukari yuvarlayan) DOGAL BIRIME (saat)
    geri cevrilmis olarak cikar - aksi halde ceza dokumu yanlis birimde raporlanir
    ve agirligindan bagimsiz olarak on kat onemliymis gibi gorunur (bu, PROGRESS.md
    Ek Gorev 3. turda tam da bu sekilde bulundu: olceksiz sapma boyle bir donusum
    icermedigi icin degil, toplam_talep_saat isitma penceresini de sayan ayri bir
    hata yuzunden imkansiz buyuklukte cikmisti - o hata da bu turda duzeltildi,
    ayrica bkz. asagidaki donem_icinde filtresi).

    SDD 5.5 (surum 1.3): donem geneli kapsamli - kisinin donem toplam saatine
    baktigi icin pencereyle sinirlandirilamaz.
    """

    ad = "Toplam saat dengesi"
    aciklama = (
        "Kişi başına toplam çalışma saatinin, haftalık hedef saatle orantılı adil paydan "
        "sapması cezalandırılır."
    )

    kapsam = KuralKapsami.DONEM_GENELI

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> cp_model.LinearExprT:
        donem_gun_sayisi = len(baglam.donem_gunleri)
        paylar_x10 = s4_hedef_paylari_x10(baglam, donem_gun_sayisi)
        if not paylar_x10:
            return 0
        azami_vardiya_saat_x10 = max(
            (round(baglam.sure_saat(v) * S4_OLCEK) for v in baglam.vardiya_tipleri), default=0
        )
        ust_sinir_x10 = donem_gun_sayisi * azami_vardiya_saat_x10 + max(paylar_x10.values())
        terimler_x10: list[cp_model.IntVar] = []
        for p in baglam.personel:
            toplam_saat_x10 = sum(
                round(baglam.sure_saat(v) * S4_OLCEK) * baglam.y[(p, g, v)]
                for g in baglam.donem_gunleri
                for v in baglam.vardiya_tipleri
            )
            fark_x10 = model.new_int_var(-ust_sinir_x10, ust_sinir_x10, f"s4_fark_p{p}")
            model.add(fark_x10 == toplam_saat_x10 - paylar_x10[p])
            mutlak_x10 = model.new_int_var(0, ust_sinir_x10, f"s4_abs_p{p}")
            model.add_abs_equality(mutlak_x10, fark_x10)
            terimler_x10.append(mutlak_x10)

        toplam_x10_ust_sinir = ust_sinir_x10 * len(terimler_x10)
        toplam_x10 = model.new_int_var(0, toplam_x10_ust_sinir, "s4_toplam_x10")
        model.add(toplam_x10 == sum(terimler_x10))
        # yarim birimi yukari yuvarlayan tamsayi bolme: (toplam_x10 + olcek//2) // olcek
        yuvarlanmis_x10 = model.new_int_var(
            0, toplam_x10_ust_sinir + S4_OLCEK, "s4_yuvarlanmis_x10"
        )
        model.add(yuvarlanmis_x10 == toplam_x10 + S4_OLCEK // 2)
        toplam_saat = model.new_int_var(0, toplam_x10_ust_sinir // S4_OLCEK + 1, "s4_toplam_saat")
        model.add_division_equality(toplam_saat, yuvarlanmis_x10, S4_OLCEK)
        return toplam_saat

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        donem_gun_sayisi = _donem_gun_sayisi(baglam)
        paylar_x10 = s4_hedef_paylari_x10(baglam, donem_gun_sayisi)
        saatler_x10: dict[int, int] = defaultdict(int)
        for a in atamalar:
            if baglam.donem_icinde(a.tarih):
                saatler_x10[a.personel_id] += round(baglam.sure_saat(a.vardiya_tipi_id) * S4_OLCEK)

        ihlaller: list[Ihlal] = []
        for personel_id in baglam.personel:
            pay_x10 = paylar_x10.get(personel_id, 0)
            sapma_x10 = abs(saatler_x10.get(personel_id, 0) - pay_x10)
            if sapma_x10 > 0:
                saat = saatler_x10.get(personel_id, 0) / S4_OLCEK
                pay = pay_x10 / S4_OLCEK
                ihlaller.append(
                    Ihlal(
                        kural_kimlik=self.kimlik,
                        personel_id=personel_id,
                        ceza=sapma_x10 / S4_OLCEK,
                        aciklama=(
                            f"Toplam saat {saat:.1f}, dagilim payi {pay:.1f} saatten "
                            f"{sapma_x10 / S4_OLCEK:.1f} saat sapiyor"
                        ),
                    )
                )
        return ihlaller


@kayitli("S5")
class S5TercihKarsilama(EsnekHedef):
    """Onaylanmis tercihlerin ihlal edilip edilmedigi (Baglam'a yalnizca onaylananlar girer)."""

    ad = "Tercih karşılama"
    aciklama = (
        "Onaylanmış her tercih için ihlal göstergesi tanımlanır. Reddedilen veya bekleyen "
        "tercihler ceza üretmez."
    )

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> cp_model.LinearExprT:
        terimler = []
        for tercih in baglam.tercihler:
            if tercih.tip == TercihTipi.CALISMAMA:
                ihlal = sum(
                    baglam.y.get((tercih.personel_id, tercih.tarih, v), 0)
                    for v in baglam.vardiya_tipleri
                )
            else:
                ihlal = sum(
                    baglam.y.get((tercih.personel_id, tercih.tarih, v), 0)
                    for v in baglam.vardiya_tipleri
                    if v != tercih.vardiya_tipi_id
                )
            terimler.append(ihlal)
        return sum(terimler) if terimler else 0

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        gunluk_atama: dict[tuple[int, date], AtamaKaydi] = {
            (a.personel_id, a.tarih): a for a in atamalar
        }
        ihlaller: list[Ihlal] = []
        for tercih in baglam.tercihler:
            atama = gunluk_atama.get((tercih.personel_id, tercih.tarih))
            if tercih.tip == TercihTipi.CALISMAMA:
                ihlal_var = atama is not None
                aciklama = "Calismama tercihine ragmen atama yapilmis"
            else:
                ihlal_var = atama is not None and atama.vardiya_tipi_id != tercih.vardiya_tipi_id
                aciklama = "Tercih edilen vardiya tipinden farkli bir vardiyaya atanmis"
            if ihlal_var:
                ihlaller.append(
                    Ihlal(
                        kural_kimlik=self.kimlik,
                        personel_id=tercih.personel_id,
                        tarih=tercih.tarih,
                        ceza=1,
                        aciklama=aciklama,
                    )
                )
        return ihlaller


@kayitli("S6")
class S6VardiyaDeseniTutarliligi(EsnekHedef):
    """Ardisik gunlerde vardiya tipi degisimi. Bina tutarliligi S6b'de ayri degerlendirilir."""

    ad = "Vardiya deseni tutarlılığı"
    aciklama = (
        "Ardışık günlerde vardiya tipi değiştirmek ergonomik olarak istenmez ve cezalandırılır."
    )

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> cp_model.LinearExprT:
        """degisim[p,d] >= y[p,d,v1] + y[p,d+1,v2] - 1 (v1 != v2): amac fonksiyonunda
        yalnizca pozitif katkili oldugu icin alt sinirlamak yeterlidir (minimize edilen
        bir degisken, gereksiz yere yuksek tutulmaz)."""
        gunler = baglam.donem_gunleri
        terimler = []
        for p in baglam.personel:
            for g, g_sonraki in zip(gunler, gunler[1:], strict=False):
                for v1 in baglam.vardiya_tipleri:
                    for v2 in baglam.vardiya_tipleri:
                        if v1 == v2:
                            continue
                        gosterge = model.new_bool_var(f"s6_p{p}_g{g}_{v1}_{v2}")
                        model.add(
                            gosterge >= baglam.y[(p, g, v1)] + baglam.y[(p, g_sonraki, v2)] - 1
                        )
                        terimler.append(gosterge)
        return sum(terimler) if terimler else 0

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        return [
            Ihlal(
                kural_kimlik=self.kimlik,
                personel_id=personel_id,
                tarih=yarin.tarih,
                ceza=1,
                aciklama="Ardisik gunde vardiya tipi degisti",
            )
            for personel_id, bugun, yarin in _ardisik_gun_ciftleri(atamalar)
            if bugun.vardiya_tipi_id != yarin.vardiya_tipi_id
        ]


@kayitli("S6b")
class S6bBinaTutarliligi(EsnekHedef):
    """Ardisik gunlerde farkli binada gorevlendirme (tesis geneli noktalar haric).

    SDD 4.2.3'teki kural tablosu kural basina tek bir agirlik sutunu icerir; S6'nin
    formulasyonundaki iki ayri agirlik (w6, w6b) bu yuzden iki ayri kural kaydina
    bolunmustur (bkz. PROGRESS.md, Sprint 1 Gun 3/4).
    """

    ad = "Bina tutarlılığı"
    aciklama = (
        "Ardışık günlerde farklı binalarda görevlendirilmek cezalandırılır. Mevcut uygulama "
        "alanında bütün noktalar tesis geneli olduğundan bu bileşen ceza üretmez."
    )

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> cp_model.LinearExprT:
        """S6 ile ayni alt-sinirlama deseni; y yerine x kullanilir cunku bina bilgisi
        noktaya (n) bagli olup y toplaminda kaybolur."""
        gunler = baglam.donem_gunleri
        terimler = []
        for p in baglam.personel:
            for g, g_sonraki in zip(gunler, gunler[1:], strict=False):
                for v1 in baglam.vardiya_tipleri:
                    for n1, nokta1 in baglam.gorev_noktalari.items():
                        if (p, g, v1, n1) not in degiskenler or nokta1.bina_id is None:
                            continue
                        for v2 in baglam.vardiya_tipleri:
                            for n2, nokta2 in baglam.gorev_noktalari.items():
                                if (
                                    (p, g_sonraki, v2, n2) not in degiskenler
                                    or nokta2.bina_id is None
                                    or nokta1.bina_id == nokta2.bina_id
                                ):
                                    continue
                                gosterge = model.new_bool_var(f"s6b_p{p}_g{g}_{n1}_{n2}")
                                model.add(
                                    gosterge
                                    >= degiskenler[(p, g, v1, n1)]
                                    + degiskenler[(p, g_sonraki, v2, n2)]
                                    - 1
                                )
                                terimler.append(gosterge)
        return sum(terimler) if terimler else 0

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        ihlaller: list[Ihlal] = []
        for personel_id, bugun, yarin in _ardisik_gun_ciftleri(atamalar):
            bugun_nokta = baglam.gorev_noktalari.get(bugun.nokta_id)
            yarin_nokta = baglam.gorev_noktalari.get(yarin.nokta_id)
            if (
                bugun_nokta is not None
                and yarin_nokta is not None
                and bugun_nokta.bina_id is not None
                and yarin_nokta.bina_id is not None
                and bugun_nokta.bina_id != yarin_nokta.bina_id
            ):
                ihlaller.append(
                    Ihlal(
                        kural_kimlik=self.kimlik,
                        personel_id=personel_id,
                        tarih=yarin.tarih,
                        ceza=1,
                        aciklama="Ardisik gunde bina degisti",
                    )
                )
        return ihlaller


def _ardisik_gun_ciftleri(
    atamalar: list[AtamaKaydi],
) -> list[tuple[int, AtamaKaydi, AtamaKaydi]]:
    """Her personelin ardisik iki gun calistigi (bugun, yarin) atama ciftleri (S6, S6b)."""
    gunluk: dict[int, dict[date, AtamaKaydi]] = defaultdict(dict)
    for a in atamalar:
        gunluk[a.personel_id][a.tarih] = a

    ciftler: list[tuple[int, AtamaKaydi, AtamaKaydi]] = []
    for personel_id, gun_map in gunluk.items():
        for gun in sorted(gun_map):
            sonraki_gun = gun + timedelta(days=1)
            if sonraki_gun in gun_map:
                ciftler.append((personel_id, gun_map[gun], gun_map[sonraki_gun]))
    return ciftler


@kayitli("S7")
class S7IzoleGun(EsnekHedef):
    """Tek gunluk calisma bloklari ve tek gunluk izinler."""

    ad = "İzole gün"
    aciklama = (
        "Tek günlük çalışma blokları ve tek günlük izinler cezalandırılır; ikisi de pratikte "
        "istenmeyen desenlerdir."
    )

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> cp_model.LinearExprT:
        gunler = baglam.donem_gunleri
        if len(gunler) < 3:
            return 0
        terimler = []
        for p in baglam.personel:
            calisti = {g: sum(baglam.y[(p, g, v)] for v in baglam.vardiya_tipleri) for g in gunler}
            for i in range(1, len(gunler) - 1):
                g, onceki, sonraki = gunler[i], gunler[i - 1], gunler[i + 1]
                # Uc bool literalin (a,b,c) AND'i icin genel alt sinir: z >= a+b+c-2.
                # izole_calisma: a=calisti[g], b=1-calisti[onceki], c=1-calisti[sonraki]
                #   => a+b+c-2 = calisti[g]-calisti[onceki]-calisti[sonraki] (sabit 0).
                # izole_izin: a=1-calisti[g], b=calisti[onceki], c=calisti[sonraki]
                #   => a+b+c-2 = -calisti[g]+calisti[onceki]+calisti[sonraki]-1 (sabit -1).
                # Iki gostergenin literal isaretleri farkli oldugu icin sabitleri de
                # farklidir - biri digerine kopyalanip +1 yazilirsa (onceki hata) bool
                # ust siniri (1) asilir ve o kombinasyon modelde imkansiz hale gelir.
                izole_calisma = model.new_bool_var(f"s7_calisma_p{p}_g{g}")
                model.add(izole_calisma >= calisti[g] - calisti[onceki] - calisti[sonraki])
                izole_izin = model.new_bool_var(f"s7_izin_p{p}_g{g}")
                model.add(izole_izin >= -calisti[g] + calisti[onceki] + calisti[sonraki] - 1)
                terimler.extend([izole_calisma, izole_izin])
        return sum(terimler) if terimler else 0

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        aralik = _bilinen_aralik(atamalar, baglam)
        if aralik is None:
            return []
        baslangic, bitis = aralik
        if (bitis - baslangic).days < 2:
            return []

        calisilanlar = calisilan_gunler(atamalar)
        personel_idleri = set(baglam.personel) | {a.personel_id for a in atamalar}

        ihlaller: list[Ihlal] = []
        for personel_id in personel_idleri:
            gunler = calisilanlar.get(personel_id, set())
            gun = baslangic + timedelta(days=1)
            son = bitis - timedelta(days=1)
            while gun <= son:
                onceki = gun - timedelta(days=1)
                sonraki = gun + timedelta(days=1)
                bugun_calisti = gun in gunler
                onceki_calisti = onceki in gunler
                sonraki_calisti = sonraki in gunler
                if bugun_calisti and not onceki_calisti and not sonraki_calisti:
                    ihlaller.append(
                        Ihlal(
                            kural_kimlik=self.kimlik,
                            personel_id=personel_id,
                            tarih=gun,
                            ceza=1,
                            aciklama="Izole (tek gunluk) calisma bloku",
                        )
                    )
                elif not bugun_calisti and onceki_calisti and sonraki_calisti:
                    ihlaller.append(
                        Ihlal(
                            kural_kimlik=self.kimlik,
                            personel_id=personel_id,
                            tarih=gun,
                            ceza=1,
                            aciklama="Izole (tek gunluk) izin",
                        )
                    )
                gun += timedelta(days=1)
        return ihlaller


@kayitli("S8")
class S8DegisimMinimizasyonu(EsnekHedef):
    """Yeniden cozumde onceki cizelgeden sapan her atama (yalniz baglam.onceki_atamalar doluysa)."""

    ad = "Değişim minimizasyonu"
    aciklama = (
        "Yeniden çözümde önceki çizelgeden sapan her atama cezalandırılır. Yalnızca yeniden "
        "çözüm işlemlerinde etkindir."
    )

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> cp_model.LinearExprT:
        """Ceza: Σ|x[p,d,s,n] - x_onceki[p,d,s,n]| (SRS S8). x_onceki sabit (0/1)
        oldugundan |x-onceki| = onceki ise (1-x), degilse x'tir; kilitli atamalar
        model_kur'da zaten x=1 sabitlendigi icin bu terim onlar icin daima 0'dir."""
        if baglam.onceki_atamalar is None:
            return 0
        onceki_kume = {
            (a.personel_id, a.tarih, a.vardiya_tipi_id, a.nokta_id) for a in baglam.onceki_atamalar
        }
        terimler: list[cp_model.LinearExprT] = []
        for anahtar, x_degiskeni in degiskenler.items():
            terimler.append(1 - x_degiskeni if anahtar in onceki_kume else x_degiskeni)
        # onceki cizelgede olup bu modelde artik karsiligi olmayan (talep/yetkinlik
        # degismis) atamalar icin de bir birim ceza eklenir; onlar hicbir x'e denk
        # gelmedigi icin yukaridaki dongude sayilmazlar.
        kaybolanlar = sum(1 for anahtar in onceki_kume if anahtar not in degiskenler)
        return sum(terimler) + kaybolanlar if terimler or kaybolanlar else 0

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        if baglam.onceki_atamalar is None:
            return []
        yeni = {(a.personel_id, a.tarih, a.vardiya_tipi_id, a.nokta_id) for a in atamalar}
        onceki = {
            (a.personel_id, a.tarih, a.vardiya_tipi_id, a.nokta_id) for a in baglam.onceki_atamalar
        }
        degisenler = yeni ^ onceki
        return [
            Ihlal(
                kural_kimlik=self.kimlik,
                personel_id=personel_id,
                tarih=tarih,
                ceza=1,
                aciklama=f"Onceki cizelgeden sapma: vardiya={vardiya_tipi_id}, nokta={nokta_id}",
            )
            for personel_id, tarih, vardiya_tipi_id, nokta_id in sorted(
                degisenler, key=lambda k: (k[0], k[1])
            )
        ]


def _donem_gun_sayisi(baglam: Baglam) -> float:
    if baglam.donem_baslangic is not None and baglam.donem_bitis is not None:
        return (baglam.donem_bitis - baglam.donem_baslangic).days + 1
    return 7.0  # donem bilgisi yoksa (testlerde) haftalik hedefi degistirmeyen notr deger


def s4_hedef_paylari_x10(baglam: Baglam, donem_gun_sayisi: float) -> dict[int, int]:
    """S4'un SRS v1.2/1.3 formulu: donemin toplam talep saatinden kisiye, kisisel
    donemlik hedef saatiyle orantili dusen pay - S4_OLCEK (onda bir saat) ile
    olceklenmis tamsayi olarak (modele_ekle ve dogrula'nin ortak hesabi; SDD Ek A
    "Kesirli hedeflerin tamsayiya olceklenmesi").

    toplam_talep_saat yalnizca baglam.donem_icinde olan (tarih,vardiya,nokta)
    anahtarlarini sayar - _adalet_sapmasi_terimi'ndeki ayni docstring notuyla ayni
    gerekce: baglam.talep, isitma penceresini de kapsayan tam zaman ekseni icin
    cozulur (TD-5), donem filtresi olmadan toplam yaklasik iki katina cikar."""
    toplam_talep_saat_x10 = sum(
        round(baglam.sure_saat(vardiya_tipi_id) * S4_OLCEK) * gereken
        for (tarih, vardiya_tipi_id, _nokta_id), gereken in baglam.talep.items()
        if baglam.donem_icinde(tarih)
    )
    hedef_saatler = {
        p: float(personel.haftalik_hedef_saat) * donem_gun_sayisi / 7
        for p, personel in baglam.personel.items()
    }
    toplam_hedef = sum(hedef_saatler.values())
    if toplam_hedef <= 0:
        return dict.fromkeys(hedef_saatler, 0)
    return {
        p: round(hedef_saat / toplam_hedef * toplam_talep_saat_x10)
        for p, hedef_saat in hedef_saatler.items()
    }


def _bilinen_aralik(atamalar: list[AtamaKaydi], baglam: Baglam) -> tuple[date, date] | None:
    if baglam.donem_baslangic is not None and baglam.donem_bitis is not None:
        return baglam.donem_baslangic, baglam.donem_bitis
    tarihler = [a.tarih for a in atamalar]
    if not tarihler:
        return None
    return min(tarihler), max(tarihler)


def _adalet_sapmasi_terimi(
    *,
    model: cp_model.CpModel,
    baglam: Baglam,
    sayilar: dict[int, cp_model.LinearExprT],
    ust_sinir: int,
    talep_uygun_mu: Callable[[tuple[date, int, int]], bool],
    degisken_onek: str,
) -> cp_model.LinearExprT:
    """S2 ve S3'un modele_ekle'sinin ortak formulasyonu (SRS 4.3): _adalet_sapmasi_ihlalleri
    ile ayni taban/tavan hesabi, CP-SAT tarafinda kisi basina bir sapma degiskeniyle.

    toplam_talep yalnizca baglam.donem_icinde olan (g,v,n) anahtarlarini sayar (TD-6,
    SDD Ek A'daki S2 ornegi: "TOPLA(talep[g,v,n]) HER (g,v,n) ICIN baglam.donem"):
    baglam.talep, model_kur'un zaman ekseninin tamami (isitma penceresi dahil) icin
    cozulur, isitma penceresi donemle ayni takvim gunu deseninden bir hafta once
    basladigindan (TD-5) donem filtresi olmadan hedef gercek donem talebinin
    yaklasik iki katina cikardi."""
    if not sayilar:
        return 0
    # SRS 1.5: payda BUTUN personel degil UYGUN HAVUZ (P_gece / P_hs); ceza da
    # yalniz o havuzun sapmalari uzerinden toplanir.
    havuz = baglam.uygun_havuz(talep_uygun_mu)
    if not havuz:
        return 0
    toplam_talep = sum(
        gereken
        for anahtar, gereken in baglam.talep.items()
        if talep_uygun_mu(anahtar) and baglam.donem_icinde(anahtar[0])
    )
    hedef = toplam_talep / len(havuz)
    taban, tavan = floor(hedef), ceil(hedef)

    terimler: list[cp_model.IntVar] = []
    for p, sayi in sayilar.items():
        if p not in havuz:
            continue
        sapma = model.new_int_var(0, ust_sinir, f"{degisken_onek}_p{p}")
        model.add(sapma >= sayi - taban)
        model.add(sapma >= tavan - sayi)
        terimler.append(sapma)
    return sum(terimler) if terimler else 0


def _adalet_sapmasi_ihlalleri(
    *,
    kural_kimlik: str,
    atamalar: list[AtamaKaydi],
    baglam: Baglam,
    atama_uygun_mu: Callable[[AtamaKaydi], bool],
    talep_uygun_mu: Callable[[tuple[date, int, int]], bool],
    aciklama: str,
) -> list[Ihlal]:
    """S2 ve S3'un ortak formulasyonu: sapma[p] = max(sayi-taban, tavan-sayi, 0).

    toplam_talep, _adalet_sapmasi_terimi ile ayni gerekceyle donem disi (isitma
    penceresi) talebi haric tutar - bkz. o fonksiyonun docstring'i."""
    if not baglam.personel:
        return []

    # SRS 1.5: modele_ekle ile BIREBIR ayni payda (uygun havuz) - iki
    # yorumlayici ayni sayiyi uretmek zorundadir (SDD 3.2.1 uyum testi).
    havuz = baglam.uygun_havuz(talep_uygun_mu)
    if not havuz:
        return []

    toplam_talep = sum(
        gereken
        for anahtar, gereken in baglam.talep.items()
        if talep_uygun_mu(anahtar) and baglam.donem_icinde(anahtar[0])
    )
    hedef = toplam_talep / len(havuz)
    taban, tavan = floor(hedef), ceil(hedef)

    sayilar: dict[int, int] = defaultdict(int)
    for a in atamalar:
        if baglam.donem_icinde(a.tarih) and atama_uygun_mu(a):
            sayilar[a.personel_id] += 1

    ihlaller: list[Ihlal] = []
    for personel_id in sorted(havuz):
        sayi = sayilar.get(personel_id, 0)
        sapma = max(sayi - taban, tavan - sayi, 0)
        if sapma > 0:
            ihlaller.append(
                Ihlal(
                    kural_kimlik=kural_kimlik,
                    personel_id=personel_id,
                    ceza=sapma,
                    aciklama=f"{aciklama} (sayi={sayi}, hedef≈{hedef:.1f})",
                )
            )
    return ihlaller


__all__ = [
    # Analiz servisi (SDD 5.7 surum 1.7) saat dagilimi tabanini S4'un adil
    # payindan almak zorunda oldugu icin bu ikisi paylasilan hesaptir.
    "S4_OLCEK",
    "S1TalepKarsilama",
    "S2GeceAdaleti",
    "S3HaftaSonuAdaleti",
    "S4ToplamSaatDengesi",
    "S5TercihKarsilama",
    "S6VardiyaDeseniTutarliligi",
    "S6bBinaTutarliligi",
    "S7IzoleGun",
    "S8DegisimMinimizasyonu",
    "s4_hedef_paylari_x10",
]
