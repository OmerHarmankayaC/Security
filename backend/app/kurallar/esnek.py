"""S1-S8 esnek hedefleri (SRS Bolum 4.3, SDD Ek A ornek sablonu - S2).

dogrula metotlari, SDD Ek A'daki S2 ornegiyle tutarli olarak agirliksiz
(ham) ceza buyuklugu dondurur; agirlikli toplam (w1..w8) amac fonksiyonu
(SDD 5.3) ve ceza dokumu raporlamasi (SDD 5.7) tarafindan hesaplanir.

Uc adalet hedefi de (S2, S3, S4) SAAT birimindedir; `w2`, `w3` ve `w4`
dogrudan karsilastirilabilir.
"""

from collections import defaultdict
from collections.abc import Callable
from datetime import date, datetime, timedelta
from math import ceil, floor
from typing import Any

from ortools.sat.python import cp_model

from app.kurallar.baglam import AtamaKaydi, Baglam
from app.kurallar.kayit_defteri import kayitli
from app.kurallar.temel import EsnekHedef, Ihlal, KuralKapsami, ParametreTanimi, XAnahtari
from app.kurallar.yardimcilar import calisilan_gunler
from app.kurallar.zaman_araligi import (
    aralik_metni,
    aralik_sure_saat_damga,
    baslangic_kaymasi,
    gece_saati_mi,
    saat_kumesi,
    saatleri_araliklara_birlestir,
)
from app.models.girdi import TercihTipi

# SRS 3.3.5. Kural kaydinda parametre bulunmadiginda kullanilir; katalog
# disindan kurulan test baglamlari bu yoldan gecer.
_VARSAYILAN_DESEN_TOLERANSI_SAAT = 2

# Bir gunluk calismanin asamayacagi saat sayisi; gosterge kisitlarinda
# "yeterince buyuk sabit" olarak kullanilir.
_GUNUN_SAATI = 24


@kayitli("S1")
class S1TalepKarsilama(EsnekHedef):
    """Nokta bazinda kapsama acigi: baskin agirlikli, alt sinir esnek hedef."""

    ad = "Talep karşılama"
    aciklama = (
        "Karşılanamayan her kişi-saat ceza üretir. Ağırlığı diğerlerinin toplamından "
        "belirgin biçimde büyük seçilir; böylece çözücü başka bir hedefi iyileştirmek için "
        "kapsama açığı bırakmaz."
    )

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> cp_model.LinearExprT:
        """SRS S1: kapsama kisiti SAAT EKSENINDE yazilir.

        ```
        ∀d, ∀t (saat), ∀n :
            Σ_p x[p,s,n] + eksik[d,t,n] ≥ talep[d,t,n]   (alt sinir, esnek)
            Σ_p x[p,s,n] − fazla[d,t,n] ≤ talep[d,t,n]   (ust sinir, esnek)
        ```

        Ceza SAAT BASINA birikir: iki saat bir kisi eksik kalmak, bir saat
        iki kisi eksik kalmakla ayni cezayi uretir. Ikisi de ayni miktarda
        karsilanmamis kisi-saattir.

        ## Saat gruplamasi neden burada YOK

        Tur 3'te eklenen "ayni kisiti ureten ardisik saatler tek `eksik`
        degiskeni uretir" iyilestirmesi blok katalogunun bir hastaligini
        tedavi ediyordu: hizali bir katalogda bir blogun sekiz saati AYNI
        degisken kumesi tarafindan kapsaniyor, dolayisiyla sekiz
        BIRBIRININ YERINE GECEBILEN `eksik` degiskeni doguyordu ve cozucu
        arama zamaninin cogunu bu simetriyi kirmaya harciyordu (olculdu:
        ayni donem 120 saniyede sifir aciktan 704 kisi-saat acikla
        cikiyordu).

        Saat ekseninde o simetri YAPISAL OLARAK YOKTUR: her saatin kendi
        `x[p,s,n]` degiskenleri vardir ve iki saat asla ayni kisiti
        uretmez. Gruplama kodunun burada yapabilecegi tek sey her saati
        kendi grubuna koymaktir; hicbir sey yapmayan bir kod katmani
        birakmak yerine kisit dogrudan saat basina yazildi. Iyilestirmenin
        yerini eksenin kendisi aldi - Is 1'in sondaji bunu olcerek
        dogruladi (40 x 28, ilk uygun cozum 5,0 sn, sifir acik).

        UST SINIR DA ESNEKTIR. Zorunlu tutulursa kadro yeterken bile
        modelin cozulemez hale gelebilecegi durumlar dogar; `fazla`
        degiskenleri baglama birakilir ve CEZALARINI S1f uretir (SDD
        4.2.3'teki kural tablosu kural basina TEK agirlik sutunu tasir,
        S1'in formulasyonunda ise iki agirlik vardir: w1, w1f).
        """
        # Bir saati hangi karar degiskenlerinin doldurabilecegi: saat
        # ekseninde bu dogrudan okunur, ara bir tablo gerekmez.
        saat_indeksleri: dict[tuple[date, int], int] = {}
        for s in baglam.saat_ekseni:
            saat_indeksleri[(baglam.saat_gunu(s), baglam.gun_saati(s))] = s

        ceza_terimi: cp_model.LinearExprT = 0
        for (gun, saat, n), gereken in sorted(baglam.talep_saat.items()):
            if gereken == 0 or not baglam.donem_icinde(gun):
                continue
            s = saat_indeksleri.get((gun, saat))
            if s is None:
                continue
            ilgili = [degiskenler[(p, s, n)] for p in baglam.personel if (p, s, n) in degiskenler]
            atanan_ifadesi = sum(ilgili) if ilgili else 0
            eksik = model.new_int_var(0, gereken, f"s1_eksik_g{gun}_t{saat}_n{n}")
            model.add(atanan_ifadesi + eksik >= gereken)
            fazla = model.new_int_var(0, max(len(ilgili), 1), f"s1_fazla_g{gun}_t{saat}_n{n}")
            model.add(atanan_ifadesi - fazla <= gereken)
            ceza_terimi = ceza_terimi + eksik
            baglam.kapsama_eksikleri[(gun, saat, n)] = eksik
            baglam.kapsama_fazlalari[(gun, saat, n)] = fazla
            baglam.kadro_fazlalari[(gun, saat, n)] = (fazla, 1)
        return ceza_terimi

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        """S1'in IKI YARISI da denetlenir.

        Once yalnizca alt sinir (kapsama acigi) bakiliyordu; ust sinir
        (`atanan > gereken`) hicbir yerde sorulmuyordu ve elle duzenlemede
        bir noktaya talepten fazla kisi yazilabiliyordu. Iki yorumlayicinin
        ayrismasi SDD 3.2.1'e gore yazilim hatasidir.

        FAZLA KADRO BURADA DEGIL, S1f'te bildirilir - agirligi ayri oldugu
        icin kural kaydi da ayri (bkz. `modele_ekle`).
        """
        eksik_saatler, _fazla_saatler = baglam.sapma_saatleri(atamalar)

        ihlaller: list[Ihlal] = []
        for nokta_id, saatler in sorted(eksik_saatler.items()):
            for bas, bit, sayi in saatleri_araliklara_birlestir(saatler):
                ihlaller.append(
                    Ihlal(
                        kural_kimlik=self.kimlik,
                        # Acik BASLADIGI gune sayilir (TD-1 ile ayni sozlesme);
                        # aralik gun sinirini kendisi tasiyabilir (B-23).
                        tarih=bas.date(),
                        ceza=sayi * aralik_sure_saat_damga(bas, bit),
                        aciklama=(
                            f"{self._yer_metni(baglam, bas, bit, nokta_id)} — " f"{sayi} kişi eksik"
                        ),
                    )
                )
        return ihlaller

    @staticmethod
    def _yer_metni(baglam: Baglam, baslangic: datetime, bitis: datetime, nokta_id: int) -> str:
        """ "2026-02-02 · 00.00–08.00 · Vardiya Şefliği" — kimlik degil AD (NFR-5)."""
        return (
            f"{baslangic.date().isoformat()} · "
            f"{aralik_metni(baslangic.time(), bitis.time())} · "
            f"{baglam.nokta_adi(nokta_id)}"
        )


@kayitli("S1f")
class S1fFazlaKadro(EsnekHedef):
    """Talebin uzerinde kalan kadro (SRS 4.3 S1'in ust siniri, ceza terimi `w1f`).

    AYRI BIR KURAL KAYDI OLMASININ NEDENI AGIRLIK: SDD 4.2.3'teki kural
    tablosu kural basina TEK agirlik sutunu tasir, S1'in formulasyonunda ise
    iki agirlik vardir (`w1` eksik, `w1f` fazla). Ayni bolme S6/S6b'de de
    yapildi. Kisitin kendisi ve `fazla` degiskenleri S1'de kurulur; burada
    yalnizca cezalari toplanir.

    MANUEL DUZENLEMEDE CEZA URETMEZ (`dogrula` ceza=None dondurur) ve bu
    AYRIM BILINCLIDIR (SRS 4.3): cozucu kendi urettigi fazlayi en aza
    indirmeye calisir, kullanicinin bilerek yazdigini sorgulamaz.
    """

    ad = "Fazla kadro"
    aciklama = (
        "Talebin üzerinde kalan her kişi-saat küçük bir ceza üretir; ceza gereksiz fazlayı "
        "ayıklar."
    )

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> cp_model.LinearExprT:
        """S1'in kurdugu `fazla` degiskenlerinin saat agirlikli toplami.

        S1 PASIFSE burasi bos doner ve bu dogrudur: kapsama kisiti hic
        kurulmadiginda ust sinir da yoktur (SDD 5.2, "S1 pasifken").
        """
        ceza_terimi: cp_model.LinearExprT = 0
        for fazla, saat_sayisi in baglam.kadro_fazlalari.values():
            ceza_terimi = ceza_terimi + saat_sayisi * fazla
        return ceza_terimi

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        """Fazla kadro UYARI olarak bildirilir, ceza uretmez (ceza=None)."""
        _eksik_saatler, fazla_saatler = baglam.sapma_saatleri(atamalar)
        ihlaller: list[Ihlal] = []
        for nokta_id, saatler in sorted(fazla_saatler.items()):
            for bas, bit, sayi in saatleri_araliklara_birlestir(saatler):
                ihlaller.append(
                    Ihlal(
                        kural_kimlik=self.kimlik,
                        tarih=bas.date(),
                        ceza=None,
                        aciklama=(
                            f"{bas.date().isoformat()} · "
                            f"{aralik_metni(bas.time(), bit.time())} · "
                            f"{baglam.nokta_adi(nokta_id)} — talepten {sayi} kişi fazla"
                        ),
                    )
                )
        return ihlaller


@kayitli("S2")
class S2GeceAdaleti(EsnekHedef):
    """Kisi basina gece SAATININ kisiye ozel adil paydan sapmasi (SRS 4.3 S2).

    ```
    gece_yuku[p] = Σ_{s ∈ ufuk, s gece saati} z[p,s]
    ```

    Gece saati, calismanin 20.00–06.00 araligiyla kesisimidir ve HESAPLANIR
    (TD-2). Blogun gece saatleri basladigi gune yazilir (TD-1), boylece H3
    ile S2 ayni tabandan beslenir.

    SDD 5.5 (surum 1.3): donem geneli kapsamli - pencereyle sinirlandirilamaz.
    """

    ad = "Gece adaleti"
    aciklama = (
        "Kişi başına düşen gece saatinin adil paydan sapması cezalandırılır. Pay, yalnızca "
        "gece görevi alabilecek personele bölünür."
    )

    kapsam = KuralKapsami.DONEM_GENELI

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> cp_model.LinearExprT:
        gunler = baglam.donem_gunleri
        gece_yuku = {p: sum(baglam.gece_blok_saati(p, g) for g in gunler) for p in baglam.personel}
        return _adalet_sapmasi_terimi(
            model=model,
            baglam=baglam,
            sayilar=gece_yuku,
            ust_sinir=len(gunler) * _GUNUN_SAATI,
            talep_uygun_mu=lambda anahtar: gece_saati_mi(anahtar[1]),
            degisken_onek="s2_sapma",
        )

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        return _adalet_sapmasi_ihlalleri(
            kural_kimlik=self.kimlik,
            atamalar=atamalar,
            baglam=baglam,
            atama_agirligi=lambda a: a.gece_saati,
            talep_uygun_mu=lambda anahtar: gece_saati_mi(anahtar[1]),
            aciklama="gece saati adil paydan sapiyor",
        )


@kayitli("S3")
class S3HaftaSonuAdaleti(EsnekHedef):
    """Kisi basina hafta sonu/resmi tatil SAATININ adil paydan sapmasi (TD-3).

    ```
    hs_yuku[p] = Σ_{d: hs[d]=1} blok_saat[p,d]
    ```

    Formulasyon S2 ile aynidir; gece saati yerine hafta sonu GUNLERINDE
    BASLAYAN bloklarin toplam suresi kullanilir. Cuma gunu baslayip
    cumartesi biten blok hafta sonu sayilmaz, pazar baslayip pazartesi
    biten sayilir (TD-1, TD-3).
    """

    ad = "Hafta sonu adaleti"
    aciklama = (
        "Kişi başına düşen hafta sonu ve resmî tatil saatinin adil paydan sapması "
        "cezalandırılır."
    )

    kapsam = KuralKapsami.DONEM_GENELI

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> cp_model.LinearExprT:
        hs_gunleri = [g for g in baglam.donem_gunleri if baglam.hafta_sonu_mu(g)]
        hs_yuku = {p: sum(baglam.blok_saati(p, g) for g in hs_gunleri) for p in baglam.personel}
        return _adalet_sapmasi_terimi(
            model=model,
            baglam=baglam,
            sayilar=hs_yuku,
            ust_sinir=len(hs_gunleri) * _GUNUN_SAATI,
            talep_uygun_mu=lambda anahtar: baglam.hafta_sonu_mu(anahtar[0]),
            degisken_onek="s3_sapma",
        )

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        return _adalet_sapmasi_ihlalleri(
            kural_kimlik=self.kimlik,
            atamalar=atamalar,
            baglam=baglam,
            atama_agirligi=lambda a: a.sure_saat if baglam.hafta_sonu_mu(a.tarih) else 0,
            talep_uygun_mu=lambda anahtar: baglam.hafta_sonu_mu(anahtar[0]),
            aciklama="hafta sonu/resmi tatil saati adil paydan sapiyor",
        )


@kayitli("S4")
class S4ToplamSaatDengesi(EsnekHedef):
    """Kisi basina toplam saatin, kisisel dagilim payindan mutlak sapmasi.

    ```
    toplam_talep_saat = Σ_{d,t,n} talep[d,t,n]
    pay[p] = ( hedef_saat[p] / Σ_q hedef_saat[q] ) · toplam_talep_saat
    Ceza:  w4 · Σ_p |saat[p] − pay[p]|
    ```

    Sapmanin kisisel sozlesme saatine degil bu PAYA gore hesaplanmasinin
    nedeni, sozlesme saatinin ulasilabilir bir hedef olmamasidir: kadro
    asgarinin uzerinde oldugunda hicbir personel sozlesme saatine ulasamaz,
    butun sapmalar ayni yonde olur ve toplamlari - calisilan toplam saat
    talep tarafindan sabitlendigi icin - dagilimdan bagimsiz bir sabite
    doner. Paya gore hesaplanan sapma iki yonlu olabildiginden dengesizligi
    gercekten olcer.

    SAPMA TABAN/TAVAN YONTEMIYLE OLCULUR (SRS 1.20):

    ```
    ∀p :  sapma[p] ≥ toplam_saat[p] − ⌊pay[p]⌋
          sapma[p] ≥ ⌈pay[p]⌉ − toplam_saat[p]
    ```

    Bandin icindeki fark cezasizdir. Kural once kesirli payi DOGRUDAN
    kisitliyordu: hem pay hem calisma saati onda bir saate olceklenip
    tamsayiya cevriliyor, sapma mutlak deger kisitiyla aliniyor ve donen
    terim bir BOLME kisitiyla dogal birime geri cevriliyordu. Iki nedenle
    degisti:

    - **Tutarlilik.** S2 ve S3 zaten taban/tavan kullaniyordu; uc adalet
      hedefinden birinin ayri davranmasi savunulabilir degildi.
    - **Sure.** Bolme kisiti (`add_division_equality`) cozum suresini
      belirgin bicimde artiriyordu; olculdu (30 personel x 28 gun): S4
      eklenince ilk uygun cozum 3,8 saniyeden 19,6 saniyeye cikiyordu -
      tek basina en pahali kural.

    Kayip, bandin icindeki bir saatlik farktir ve olcunun birimi saat
    oldugu icin kucuktur.

    `S4_OLCEK` yine kullaniliyor ama YALNIZCA PAY HESABINDA: pay kesirlidir
    ve onda bir saat hassasiyetinde tutulur (analiz ekrani da o degeri
    gosterir). Modele giren sey payin tabani ve tavanidir.

    SDD 5.5 (surum 1.3): donem geneli kapsamli.
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
        gunler = baglam.donem_gunleri
        paylar = s4_hedef_paylari(baglam, len(gunler))
        if not paylar:
            return 0
        ust_sinir = len(gunler) * _GUNUN_SAATI
        terimler: list[cp_model.IntVar] = []
        for p in baglam.personel:
            toplam_saat = sum(baglam.blok_saati(p, g) for g in gunler)
            if isinstance(toplam_saat, int):
                continue
            taban, tavan = floor(paylar.get(p, 0.0)), ceil(paylar.get(p, 0.0))
            # UST SINIR PAYI DA KAPSAMALI (S2/S3 ile ayni gerekce): kadro
            # yetersizken pay bir kisinin tasiyabilecegi azami yuku asabilir
            # ve `sapma >= tavan − saat` kisiti degiskenin ust sinirini
            # asarak modeli COZULEMEZ yapardi.
            sapma = model.new_int_var(0, max(ust_sinir, tavan), f"s4_sapma_p{p}")
            model.add(sapma >= toplam_saat - taban)
            model.add(sapma >= tavan - toplam_saat)
            terimler.append(sapma)
        return sum(terimler) if terimler else 0

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        paylar = s4_hedef_paylari(baglam, _donem_gun_sayisi(baglam))
        saatler: dict[int, int] = defaultdict(int)
        for a in atamalar:
            if baglam.donem_icinde(a.tarih):
                saatler[a.personel_id] += a.sure_saat

        ihlaller: list[Ihlal] = []
        for personel_id in baglam.personel:
            pay = paylar.get(personel_id, 0.0)
            saat = saatler.get(personel_id, 0)
            taban, tavan = floor(pay), ceil(pay)
            sapma = max(saat - taban, tavan - saat, 0)
            if sapma > 0:
                ihlaller.append(
                    Ihlal(
                        kural_kimlik=self.kimlik,
                        personel_id=personel_id,
                        ceza=sapma,
                        aciklama=(
                            f"Toplam saat {saat}, dagilim payi {pay:.1f} saatten "
                            f"{sapma} saat sapiyor"
                        ),
                    )
                )
        return ihlaller


@kayitli("S5")
class S5TercihKarsilama(EsnekHedef):
    """Onaylanmis tercihlerin ihlal edilip edilmedigi (Baglam'a yalnizca onaylananlar girer).

    Tercih artik bir vardiya TIPINI degil bir ZAMAN ARALIGINI gosterir
    (SRS FR-3.2, TD-12): "su saatler arasinda calismak isterim". Ihlal,
    kuralin eski sekliyle ayni: o gun calisildi VE calisma tercih edilen
    araligin disina tasti. Hic calisilmayan gun ceza uretmez - eski
    formulasyon (`Σ_{s ≠ s*} y`) da uretmiyordu.
    """

    ad = "Tercih karşılama"
    aciklama = (
        "Onaylanmış her tercih için ihlal göstergesi tanımlanır. Reddedilen veya bekleyen "
        "tercihler ceza üretmez."
    )

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> cp_model.LinearExprT:
        terimler: list[cp_model.LinearExprT] = []
        for sira, tercih in enumerate(baglam.tercihler):
            if tercih.tarih not in baglam.zaman_ekseni:
                continue
            if tercih.tip == TercihTipi.CALISMAMA:
                terimler.append(baglam.calisti(tercih.personel_id, tercih.tarih))
                continue
            istenen = _tercih_saatleri(tercih)
            if istenen is None:
                continue
            disari_saat = baglam.blok_agirlikli_toplam(
                tercih.personel_id,
                tercih.tarih,
                _aralik_disi_agirlik(baglam, istenen),
            )
            if isinstance(disari_saat, int):
                continue
            ihlal = model.new_bool_var(f"s5_ihlal_{sira}")
            # Araligin disinda bir saat bile varsa tercih karsilanmamistir
            # (TD-12: blogun TAMAMI araligin icinde kalmali).
            model.add(disari_saat <= _GUNUN_SAATI * ihlal)
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
                istenen = _tercih_saatleri(tercih)
                ihlal_var = (
                    atama is not None
                    and istenen is not None
                    and any(an.hour not in istenen for an in atama.saatler())
                )
                aciklama = "Calisma blogu tercih edilen zaman araliginin disina tasiyor"
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
class S6CalismaDeseniTutarliligi(EsnekHedef):
    """Ardisik gunlerde FIILI baslangic saati kaymasi. Bina tutarliligi S6b'de ayri.

    ```
    kayma[p,d] = dairesel_fark( bas_saati[p,d+1], bas_saati[p,d] )
               = min( |Δ|, 24 − |Δ| )
    degisim[p,d] = 1  eger iki gunde de calisiliyor ve kayma > tolerans
    ```

    Kural once "ayni vardiya tipi", sonra "katalogdaki blogun baslangic
    saati" uzerinden yaziliydi. Blok katalogu kalktigi icin karsilastirilacak
    bir tip de, onceden bilinen bir baslangic saati de yok: baslangic artik
    KARAR DEGISKENIDIR ve `bas[p,s]`den okunur.

    Farkin dairesel alinmasi zorunlu: 22.00 ile 02.00 arasindaki kayma dort
    saattir, yirmi degil. Duz cikarma kullanan bir olcu, gece bloklari
    arasindaki en kucuk gecisleri en buyuk ceza gibi gosterirdi.
    """

    ad = "Çalışma deseni tutarlılığı"
    aciklama = (
        "Ardışık günlerde çalışma saatlerini kaydırmak ergonomik olarak istenmez ve "
        "cezalandırılır. Ölçü fiilî başlangıç saatidir; tolerans kadar kayma cezasızdır."
    )

    parametre_tanimlari = (
        ParametreTanimi(
            anahtar="desen_toleransi_saat",
            etiket="Desen toleransı",
            birim="saat",
            asgari=0,
            azami=12,
        ),
    )

    def _tolerans(self) -> int:
        return int(self.parametreler.get("desen_toleransi_saat", _VARSAYILAN_DESEN_TOLERANSI_SAAT))

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> cp_model.LinearExprT:
        tolerans = self._tolerans()
        gunler = baglam.donem_gunleri
        terimler = []
        for p in baglam.personel:
            for g, g_sonraki in zip(gunler, gunler[1:], strict=False):
                bugun = self._baslangic_saati(baglam, p, g)
                yarin = self._baslangic_saati(baglam, p, g_sonraki)
                if isinstance(bugun, int) or isinstance(yarin, int):
                    continue
                fark = model.new_int_var(-23, 23, f"s6_fark_p{p}_g{g}")
                model.add(fark == yarin - bugun)
                mutlak = model.new_int_var(0, 23, f"s6_mutlak_p{p}_g{g}")
                model.add_abs_equality(mutlak, fark)
                ters = model.new_int_var(1, 24, f"s6_ters_p{p}_g{g}")
                model.add(ters == 24 - mutlak)
                dairesel = model.new_int_var(0, 12, f"s6_dairesel_p{p}_g{g}")
                model.add_min_equality(dairesel, [mutlak, ters])
                gosterge = model.new_bool_var(f"s6_p{p}_g{g}")
                # Iki gunde de calisilmiyorsa `bas_saati` sifira duser ve
                # anlamsiz bir kayma uretirdi; sag taraftaki (2 − calisti −
                # calisti) terimi o durumda kisiti gevsetir.
                model.add(
                    dairesel
                    <= tolerans
                    + _GUNUN_SAATI * gosterge
                    + _GUNUN_SAATI * (2 - baglam.calisti(p, g) - baglam.calisti(p, g_sonraki))
                )
                terimler.append(gosterge)
        return sum(terimler) if terimler else 0

    @staticmethod
    def _baslangic_saati(baglam: Baglam, p: int, g: date) -> Any:
        """`bas_saati[p,d]` — gunde en fazla bir baslangic oldugu icin dogrudan toplam."""
        toplam: Any = 0
        for s in baglam.gun_saatleri(g):
            saat = baglam.gun_saati(s)
            if saat and (p, s) in baglam.bas:
                toplam = toplam + saat * baglam.bas[(p, s)]
        return toplam

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        tolerans = self._tolerans()
        return [
            Ihlal(
                kural_kimlik=self.kimlik,
                personel_id=personel_id,
                tarih=yarin.tarih,
                ceza=1,
                aciklama="Ardisik gunde calisma baslangici toleransi asan olcude kaydi",
            )
            for personel_id, bugun, yarin in _ardisik_gun_ciftleri(atamalar)
            if baslangic_kaymasi(bugun.baslangic_saati, yarin.baslangic_saati) > tolerans
        ]


@kayitli("S6b")
class S6bBinaTutarliligi(EsnekHedef):
    """Ardisik gunlerde farkli binada gorevlendirme (tesis geneli noktalar haric).

    SDD 4.2.3'teki kural tablosu kural basina tek bir agirlik sutunu icerir;
    S6'nin formulasyonundaki iki ayri agirlik (w6, w6b) bu yuzden iki ayri
    kural kaydina bolunmustur.

    Mevcut uygulama alaninda butun noktalar tesis geneli oldugundan
    (SRS 3.3.3) bu bilesen hicbir ceza uretmez; kural, binaya bagli nokta
    tanimlanmasi durumunda kendiliginden devreye girmek uzere katalogda
    tutulur.
    """

    ad = "Bina tutarlılığı"
    aciklama = (
        "Ardışık günlerde farklı binalarda görevlendirilmek cezalandırılır. Mevcut uygulama "
        "alanında bütün noktalar tesis geneli olduğundan bu bileşen ceza üretmez."
    )

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> cp_model.LinearExprT:
        """Gunun noktasi, blogun BASLADIGI saatten okunur.

        Nokta blok boyunca sabittir (H1), dolayisiyla baslangic saatindeki
        nokta blogun noktasidir; butun saatlere bakmak ayni bilgiyi tekrar
        sormak olurdu.
        """
        binali_noktalar = [
            n for n, nokta in baglam.gorev_noktalari.items() if nokta.bina_id is not None
        ]
        if len(binali_noktalar) < 2:
            return 0

        gunler = baglam.donem_gunleri
        nokta_gun: dict[tuple[int, date, int], cp_model.IntVar] = {}
        for p in baglam.personel:
            for g in gunler:
                for n in binali_noktalar:
                    saatler = [s for s in baglam.gun_saatleri(g) if (p, s, n) in degiskenler]
                    if not saatler:
                        continue
                    gosterge = model.new_bool_var(f"s6b_nokta_p{p}_g{g}_n{n}")
                    for s in saatler:
                        model.add(gosterge >= degiskenler[(p, s, n)] + baglam.basv(p, s) - 1)
                    nokta_gun[(p, g, n)] = gosterge

        terimler = []
        for p in baglam.personel:
            for g, g_sonraki in zip(gunler, gunler[1:], strict=False):
                for n1 in binali_noktalar:
                    for n2 in binali_noktalar:
                        if (
                            baglam.gorev_noktalari[n1].bina_id == baglam.gorev_noktalari[n2].bina_id
                            or (p, g, n1) not in nokta_gun
                            or (p, g_sonraki, n2) not in nokta_gun
                        ):
                            continue
                        gosterge = model.new_bool_var(f"s6b_p{p}_g{g}_{n1}_{n2}")
                        model.add(
                            gosterge >= nokta_gun[(p, g, n1)] + nokta_gun[(p, g_sonraki, n2)] - 1
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
    """Her personelin ardisik iki gun calistigi (bugun, yarin) blok ciftleri (S6, S6b)."""
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
            calisti = {g: baglam.calisti(p, g) for g in gunler}
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
                izole_calisma_ifadesi = calisti[g] - calisti[onceki] - calisti[sonraki]
                izole_izin_ifadesi = -calisti[g] + calisti[onceki] + calisti[sonraki] - 1
                if isinstance(izole_calisma_ifadesi, int):
                    continue
                izole_calisma = model.new_bool_var(f"s7_calisma_p{p}_g{g}")
                model.add(izole_calisma >= izole_calisma_ifadesi)
                izole_izin = model.new_bool_var(f"s7_izin_p{p}_g{g}")
                model.add(izole_izin >= izole_izin_ifadesi)
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
    """Yeniden cozumde onceki cizelgeden sapan her atama (yalniz baglam.onceki_atamalar doluysa).

    Formul degismedi (`Σ |x − x_onceki|`); degisen, `x`in indeks kumesidir.
    Blok ekseninde bir birim "bir vardiya", saat ekseninde "bir kisi-saat"
    demektir - olcu S1, S2, S3 ve S4 ile ayni birime gelmis oldu.
    """

    ad = "Değişim minimizasyonu"
    aciklama = (
        "Yeniden çözümde önceki çizelgeden sapan her kişi-saat cezalandırılır. Yalnızca "
        "yeniden çözüm işlemlerinde etkindir."
    )

    def modele_ekle(
        self, model: cp_model.CpModel, degiskenler: dict[XAnahtari, cp_model.IntVar], baglam: Baglam
    ) -> cp_model.LinearExprT:
        """x_onceki sabit (0/1) oldugundan |x−onceki| = onceki ise (1−x), degilse x'tir;
        kilitli atamalar model_kur'da zaten x=1 sabitlendigi icin terim onlar icin daima 0."""
        if baglam.onceki_atamalar is None:
            return 0
        onceki_kume = _saat_anahtarlari(baglam, baglam.onceki_atamalar)
        terimler: list[cp_model.LinearExprT] = []
        for anahtar, x_degiskeni in degiskenler.items():
            terimler.append(1 - x_degiskeni if anahtar in onceki_kume else x_degiskeni)
        # Onceki cizelgede olup bu modelde artik karsiligi olmayan
        # (talep/yetkinlik degismis) saatler icin de birer birim ceza eklenir;
        # onlar hicbir x'e denk gelmedigi icin yukaridaki dongude sayilmazlar.
        kaybolanlar = sum(1 for anahtar in onceki_kume if anahtar not in degiskenler)
        return sum(terimler) + kaybolanlar if terimler or kaybolanlar else 0

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        if baglam.onceki_atamalar is None:
            return []
        yeni = _saat_anahtarlari(baglam, atamalar)
        onceki = _saat_anahtarlari(baglam, baglam.onceki_atamalar)
        degisenler = yeni ^ onceki
        return [
            Ihlal(
                kural_kimlik=self.kimlik,
                personel_id=personel_id,
                tarih=baglam.saat_gunu(s) if baglam.zaman_ekseni else None,
                ceza=1,
                aciklama=f"Onceki cizelgeden sapma: saat={s}, nokta={nokta_id}",
            )
            for personel_id, s, nokta_id in sorted(degisenler)
        ]


def _saat_anahtarlari(baglam: Baglam, atamalar: list[AtamaKaydi]) -> set[XAnahtari]:
    """Blok kayitlarini `x`in indeks kumesine (personel, saat, nokta) cevirir."""
    anahtarlar: set[XAnahtari] = set()
    for atama in atamalar:
        for an in atama.saatler():
            s = baglam.saat_indeksi(an)
            if s is not None:
                anahtarlar.add((atama.personel_id, s, atama.nokta_id))
    return anahtarlar


def _aralik_disi_agirlik(baglam: Baglam, istenen: frozenset[int]) -> Callable[[int], int]:
    """Tercih araliginin DISINDA kalan saatleri 1, icinde kalanlari 0 sayan agirlik."""
    return lambda s: 0 if baglam.gun_saati(s) in istenen else 1


def _tercih_saatleri(tercih: Any) -> frozenset[int] | None:
    """Tercih edilen araligin kapsadigi gunluk saatler; aralik eksikse None."""
    if tercih.tercih_baslangic is None or tercih.tercih_bitis is None:
        return None
    return saat_kumesi(tercih.tercih_baslangic, tercih.tercih_bitis)


def _donem_gun_sayisi(baglam: Baglam) -> float:
    if baglam.donem_baslangic is not None and baglam.donem_bitis is not None:
        return (baglam.donem_bitis - baglam.donem_baslangic).days + 1
    return 7.0  # donem bilgisi yoksa (testlerde) haftalik hedefi degistirmeyen notr deger


def s4_hedef_paylari(baglam: Baglam, donem_gun_sayisi: float) -> dict[int, float]:
    """S4'un adil payi: donemin toplam talep saatinden kisiye, kisisel donemlik
    hedef saatiyle orantili dusen pay — SAAT cinsinden (modele_ekle, dogrula ve
    Analiz servisinin ortak hesabi).

    DEGER KESIRLIDIR ve oyle kalir. Once onda bir saate olceklenip tamsayiya
    cevriliyordu cunku modele dogrudan giriyordu; S4 taban/tavan yontemine
    gectikten sonra (SRS 1.20) modele giren sey payin TABANI ve TAVANIDIR,
    payin kendisi degil. Olcekleme boylece gereksizlesti ve Analiz ekrani da
    hedefi dogal biriminde okuyor.

    toplam_talep_saat yalnizca `donem_icinde` olan anahtarlari sayar: talep,
    isitma penceresini de kapsayan tam zaman ekseni icin cozulur (TD-5) ve
    donem filtresi olmadan toplam yaklasik iki katina cikardi.
    """
    toplam_talep_saat = sum(
        gereken
        for (tarih, _saat, _nokta_id), gereken in baglam.talep_saat.items()
        if baglam.donem_icinde(tarih)
    )
    hedef_saatler = {
        p: float(personel.haftalik_hedef_saat) * donem_gun_sayisi / 7
        for p, personel in baglam.personel.items()
    }
    toplam_hedef = sum(hedef_saatler.values())
    if toplam_hedef <= 0:
        return dict.fromkeys(hedef_saatler, 0.0)
    return {
        p: hedef_saat / toplam_hedef * toplam_talep_saat for p, hedef_saat in hedef_saatler.items()
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
    """S2 ve S3'un modele_ekle'sinin ortak formulasyonu (SRS 4.3).

    Hedef KISIYE OZELDIR (SRS 1.17): her talep birimi ona erisebilenler
    arasinda esit bolunur ve kisinin hedefi kendi paylarinin toplamidir.
    Tek bir havuz ortalamasi kullanildiginda erisilebilirligi kisitli bir
    havuz kalici olarak sapmali gorunuyordu; ayrinti `Baglam.adil_paylar`da.
    """
    if not sayilar:
        return 0
    paylar = baglam.adil_paylar(talep_uygun_mu)
    terimler: list[cp_model.IntVar] = []
    for p, sayi in sayilar.items():
        pay = paylar.get(p, 0.0)
        if pay <= 0 or isinstance(sayi, int):
            # Payi sifir olan personel olcunun DISINDADIR: hedefe ulasmasi
            # zaten imkansiz, sapmasini raporlamak olcuyu ayirt edici
            # olmaktan cikarir.
            continue
        # Taban/tavan: pay kesirli oldugundan iki tam sayi arasinda kalan
        # her deger cezasizdir. Ceza birimi SAAT kalir (S4 ile ayni
        # sozlesme); kesirli bir ceza CP-SAT'a tamsayi katsayi olarak
        # giremezdi.
        taban, tavan = floor(pay), ceil(pay)
        # UST SINIR PAYI DA KAPSAMALI. `ust_sinir` bir kisinin fiilen
        # tasiyabilecegi azami yuktur; pay ise talebin kisiye dusen
        # bolumudur ve KADRO YETERSIZ oldugunda bunu asabilir. O durumda
        # `sapma >= tavan − sayi` kisiti degiskenin ust sinirini asar ve
        # MODEL COZULEMEZ hale gelir - kadro yetersizliginin dogru cevabi
        # ise cizelgeyi uretip acigi gostermektir (SRS FR-5.2). Uyum testi
        # bunu 24 ornekten birinde yakaladi.
        sapma = model.new_int_var(0, max(ust_sinir, tavan), f"{degisken_onek}_p{p}")
        model.add(sapma >= sayi - taban)
        model.add(sapma >= tavan - sayi)
        terimler.append(sapma)
    return sum(terimler) if terimler else 0


def _adalet_sapmasi_ihlalleri(
    *,
    kural_kimlik: str,
    atamalar: list[AtamaKaydi],
    baglam: Baglam,
    atama_agirligi: Callable[[AtamaKaydi], int],
    talep_uygun_mu: Callable[[tuple[date, int, int]], bool],
    aciklama: str,
) -> list[Ihlal]:
    """S2 ve S3'un ortak formulasyonu: sapma[p] = max(sayi−taban, tavan−sayi, 0).

    `atama_agirligi` bir blogun olcuye KAC SAAT kattigini soyler: S2 icin
    blogun gece saati, S3 icin hafta sonu gununde baslayan blogun suresi,
    ilgisiz bloklar icin sifir.
    """
    if not baglam.personel:
        return []

    # modele_ekle ile BIREBIR ayni paylar - iki yorumlayici ayni sayiyi
    # uretmek zorundadir (SDD 3.2.1 uyum testi).
    paylar = baglam.adil_paylar(talep_uygun_mu)
    havuz = {p for p, pay in paylar.items() if pay > 0}
    if not havuz:
        return []

    sayilar: dict[int, int] = defaultdict(int)
    for a in atamalar:
        if baglam.donem_icinde(a.tarih):
            sayilar[a.personel_id] += atama_agirligi(a)

    ihlaller: list[Ihlal] = []
    for personel_id in sorted(havuz):
        sayi = sayilar.get(personel_id, 0)
        pay = paylar[personel_id]
        taban, tavan = floor(pay), ceil(pay)
        sapma = max(sayi - taban, tavan - sayi, 0)
        if sapma > 0:
            ihlaller.append(
                Ihlal(
                    kural_kimlik=kural_kimlik,
                    personel_id=personel_id,
                    ceza=sapma,
                    aciklama=f"{aciklama} (yuk={sayi}, adil pay≈{pay:.1f})",
                )
            )
    return ihlaller


__all__ = [
    # Analiz servisi (SDD 5.7) saat dagilimi tabanini S4'un adil payindan
    # almak zorunda oldugu icin bu hesap paylasilir.
    "S1TalepKarsilama",
    "S1fFazlaKadro",
    "S2GeceAdaleti",
    "S3HaftaSonuAdaleti",
    "S4ToplamSaatDengesi",
    "S5TercihKarsilama",
    "S6CalismaDeseniTutarliligi",
    "S6bBinaTutarliligi",
    "S7IzoleGun",
    "S8DegisimMinimizasyonu",
    "s4_hedef_paylari",
]
