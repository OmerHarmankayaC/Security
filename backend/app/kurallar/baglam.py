"""Kurallarin modele_ekle/dogrula metotlarina aktarilan calisma baglami.

Cozucu ve dogrulayici, veritabanindan okudugu tanim ve girdi verisini bu
hafif, ORM'den bagimsiz yapiya donusturur (SDD 3.2.1: "her iki yorumlayici
da ayni kural nesnesinden beslenir"). ORM'den bagimsiz olmasi, kural
birim testlerinin veritabani gerektirmeden elle kurulan ornekler uzerinde
calismasini saglar.

## Eksen MUTLAKTIR (SRS TD-13)

Karar degiskeni artik "hangi blok" degil "hangi saat"tir ve saat ekseni gun
basina SIFIRLANMAZ:

    S = { 0, 1, …, 24·D−1 }   zaman ekseninin (isitma penceresi dahil) saatleri
    z[p,s]                    p personeli s saatinde calisiyor
    x[p,s,n]                  … ve n gorev noktasinda

Eksenin gun x saat bicimde kurulmasi halinde gece yarisini asan bir calisma
gunun sonunda kesilir, ertesi gunun basinda yeniden baslar ve kesintisizlik
kisiti onu IKI AYRI BLOK sayar; kural, tam da izin verilmesi gereken
calismayi yasaklamis olur.

## "Gun d'nin saatleri" DUVAR SAATI DEGILDIR

TD-1 blogun basladigi gune sayilmasini soyler ve H9'un metni bunu acikca
tekrarlar: "gece yarisini asan blogun saatleri basladigi gune sayilir;
ertesi gunun tavani bu saatlerle dolmaz". Duvar saati okumasi iki kurali da
bozar — H9 on iki saatlik bir blogu 4 + 8 diye gorup gecirir, H1'in asgari
suresi ise aksam baslangiclarini yasaklar (21.00'de baslayan blok o gune uc
saat birakir).

Bu yuzden gun basina toplamlar `devir[p,s]` gostergesi uzerinden kurulur:
"s saati calisiliyor VE onceki gunde baslamis bir bloga ait". Bir gunun
blok saatleri = o gunun saatleri − devralinanlar + ertesi gune tasanlar
(bkz. `blok_agirlikli_toplam`).
"""

from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Any

from app.kurallar.gecmis import GecmisYuk
from app.kurallar.zaman_araligi import gece_saati_mi
from app.models.girdi import MusaitlikDilimi, TercihTipi

SAAT = timedelta(hours=1)


@dataclass(frozen=True, slots=True)
class GorevNoktasiBilgisi:
    nokta_id: int
    onkosul_yetkinlik_id: int | None = None
    bina_id: int | None = None
    ad: str = ""


@dataclass(frozen=True, slots=True)
class PersonelBilgisi:
    personel_id: int
    aktif_baslangic: date
    aktif_bitis: date | None = None
    yetkinlikler: frozenset[int] = frozenset()
    haftalik_hedef_saat: float = 0.0
    # H10: personel KAYDINDAKI devir alani. Yayinlanmis surumlerden
    # turetilen fazla calisma ile TOPLANIR (`Baglam.yasal_devir`); alan
    # turetilen degerin yerine gecmez, sistemin kota yilinin basindan beri
    # her seyi bilmedigi durumu karsilar (SRS TD-6).
    devir_fazla_calisma_saat: float = 0.0


@dataclass(frozen=True, slots=True)
class MusaitlikKaydi:
    personel_id: int
    baslangic_tarihi: date
    bitis_tarihi: date
    dilim: MusaitlikDilimi


@dataclass(frozen=True, slots=True)
class AtamaKaydi:
    """Bir CALISMA BLOGU (SDD 4.2.1) — kural degerlendirmesi icin gereken alani.

    Kayit blok basinadir, saat basina degil: cozucunun ciktisi saat
    duzeyindedir ve yazma aninda tek bloga toplanir. Gece yarisini asan blok
    tek kayitta durur; `bitis` ertesi gune duser.

    Blogun hangi gune sayildigi (TD-1) `baslangic`tan TURETILIR, ayri bir
    alanda saklanmaz — iki alan ayrisabilir.
    """

    personel_id: int
    baslangic: datetime
    bitis: datetime
    nokta_id: int

    @property
    def tarih(self) -> date:
        """TD-1: blok basladigi takvim gunune sayilir."""
        return self.baslangic.date()

    @property
    def sure_saat(self) -> int:
        return round((self.bitis - self.baslangic).total_seconds() / 3600)

    @property
    def baslangic_saati(self) -> time:
        return self.baslangic.time()

    def saatler(self) -> Iterator[datetime]:
        """Blogun kapsadigi saat dilimlerinin BASLANGIC anlari (bitis haric)."""
        an = self.baslangic
        while an < self.bitis:
            yield an
            an += SAAT

    @property
    def gece_saati(self) -> int:
        """TD-2: calismanin 20.00–06.00 araligiyla kesisiminin uzunlugu."""
        return sum(1 for an in self.saatler() if gece_saati_mi(an.hour))


@dataclass(frozen=True, slots=True)
class TercihKaydi:
    """Onaylanmis bir tercih kaydi (SDD 4.2.2). Sadece onaylanmislar Baglam'a girer (SRS S5).

    Blok katalogu kalktigi icin tercih artik bir vardiya tipini degil bir
    ZAMAN ARALIGINI gosterir (SRS FR-3.2, TD-12): "su saatler arasinda
    calismak isterim".
    """

    personel_id: int
    tarih: date
    tip: TercihTipi
    tercih_baslangic: time | None = None
    tercih_bitis: time | None = None


# ADIL PAY YUVARLANARAK DONER — kayan nokta artigi taban/tavan bandini bozuyor.
#
# Pay tek tek toplanarak kurulur (`adil_paylar`); 1/3 gibi ikilik tabanda tam
# gosterilemeyen bir deger yeterince toplandiginda artik birikir ve
# matematiksel olarak TAM SAYI olan bir pay 21.000000000000085 ya da
# 20.999999999999993 olarak cikar. S2/S3/S4'un bandi `floor(pay)`/`ceil(pay)`
# ile kuruldugu icin band [21,21] yerine [21,22] ya da [20,21] olur: payini
# tam tutturan kisi cezali gorunur, sapmalar bir saat sisik ya da eksik
# raporlanir. Gercek veride olculdu — otuz kisilik havuzun on dokuzunda.
#
# Dokuz basamak, gercek kesirli paylari (10,333333...) bozmadan artigi siler.
PAY_BASAMAK = 9


def payi_yuvarla(pay: float) -> float:
    """Adil payi taban/tavan hesabina girmeden once artiktan arindirir."""
    return round(pay, PAY_BASAMAK)


@dataclass(slots=True)
class Baglam:
    gorev_noktalari: dict[int, GorevNoktasiBilgisi]
    personel: dict[int, PersonelBilgisi]
    musaitlik: list[MusaitlikKaydi] = field(default_factory=list)
    # SAAT EKSENLI TALEP — TEK KAYNAK (SDD 5.3, SRS 3.3.4).
    # (tarih, saat, nokta_id) -> gereken_sayi. Talep kayitlari zaman
    # araligidir; acilim `talebi_saate_ac`ta bir kez yapilir ve bes tuketici
    # ayni ciktiyi kullanir. Kapsama kisiti (S1) bu eksende yazilir.
    talep_saat: dict[tuple[date, int, int], int] = field(default_factory=dict)
    donem_baslangic: date | None = None
    donem_bitis: date | None = None
    ozel_gunler: frozenset[date] = frozenset()
    # Yalniz KULLANICIYA GOSTERILEN metinler icin (SRS FR-5.6, karar notu
    # K20): bulgu metinleri veritabani kimligi degil AD tasir.
    yetkinlik_adlari: dict[int, str] = field(default_factory=dict)
    personel_adlari: dict[int, str] = field(default_factory=dict)
    tercihler: list[TercihKaydi] = field(default_factory=list)
    # Yalniz yeniden cozum dogrulamasinda dolu olur (S8); normalde None.
    onceki_atamalar: list[AtamaKaydi] | None = None
    # ADALET UFKU (SRS TD-6): donem oncesi birikim. None ise olcu yalniz
    # donemi kapsar - eski davranis, gecmisi olmayan kurulumda dogru olan.
    gecmis: GecmisYuk | None = None
    # YASAL UFUK (SRS TD-6, H10) — adalet ufkundan AYRI. Turetilen kota yili
    # ici fazla calisma ILE personel kaydindaki devir alaninin toplamidir;
    # ikisi toplanir, biri digerinin yerine gecmez. None ise yalniz kayit
    # alani kullanilir (eski davranis).
    yasal_devir: dict[int, float] | None = None
    # Asagidaki dort alan yalniz model kurma sirasinda (model_kur) doldurulur;
    # dogrula cagrilarinda bos kalir.
    zaman_ekseni: list[date] = field(default_factory=list)
    z: dict[tuple[int, int], Any] = field(default_factory=dict)
    bas: dict[tuple[int, int], Any] = field(default_factory=dict)
    devir: dict[tuple[int, int], Any] = field(default_factory=dict)
    # Gun basina TURETILMIS BUYUKLUKLER, bir kez degiskene baglanmis hali
    # (bkz. `blok_saati`). Alti kural ayni ifadeyi okudugu icin onbellek
    # isteğe bagli bir iyilestirme degil, model buyuklugunu belirleyen sey.
    gun_saat: dict[tuple[int, date], Any] = field(default_factory=dict)
    gece_saat: dict[tuple[int, date], Any] = field(default_factory=dict)
    gun_calisti: dict[tuple[int, date], Any] = field(default_factory=dict)
    # S1TalepKarsilama.modele_ekle tarafindan doldurulur: (tarih, saat,
    # nokta_id) -> eksik degiskeni. Cozumden sonra kapsama_acigi tablosuna
    # yazilacak degerleri okumak icin.
    kapsama_eksikleri: dict[tuple[date, int, int], Any] = field(default_factory=dict)
    kapsama_fazlalari: dict[tuple[date, int, int], Any] = field(default_factory=dict)
    # S1f'in ceza terimini kurabilmesi icin: gruplanmis fazla degiskeni ->
    # (degisken, grubun saat sayisi).
    kadro_fazlalari: dict[tuple[date, int, int], tuple[Any, int]] = field(default_factory=dict)

    # --- Mutlak saat ekseni ------------------------------------------------

    @property
    def saat_sayisi(self) -> int:
        return 24 * len(self.zaman_ekseni)

    @property
    def saat_ekseni(self) -> range:
        """S = { 0, 1, …, 24·D−1 } (SRS TD-13)."""
        return range(self.saat_sayisi)

    def saat_gunu(self, s: int) -> date:
        """s saatinin dustugu TAKVIM gunu (duvar saati)."""
        return self.zaman_ekseni[s // 24]

    def gun_saati(self, s: int) -> int:
        """s saatinin gun icindeki duvar saati (0-23)."""
        return s % 24

    def saat_zamani(self, s: int) -> datetime:
        return datetime.combine(self.saat_gunu(s), time(self.gun_saati(s)))

    def saat_indeksi(self, an: datetime) -> int | None:
        """Mutlak bir anin eksen uzerindeki indeksi; eksen disindaysa None."""
        if not self.zaman_ekseni:
            return None
        gun_farki = (an.date() - self.zaman_ekseni[0]).days
        s = gun_farki * 24 + an.hour
        return s if 0 <= s < self.saat_sayisi else None

    def gun_saatleri(self, g: date) -> range:
        """g gununun 24 saatinin eksen indeksleri."""
        i = self.zaman_ekseni.index(g)
        return range(i * 24, i * 24 + 24)

    def gece_saati_mi(self, s: int) -> bool:
        return gece_saati_mi(self.gun_saati(s))

    # --- Modelden okunan ifadeler -----------------------------------------

    def zv(self, p: int, s: int) -> Any:
        """z[p,s] ya da eksen disi/elenmis saatler icin sabit 0."""
        return self.z.get((p, s), 0)

    def basv(self, p: int, s: int) -> Any:
        return self.bas.get((p, s), 0)

    def devirv(self, p: int, s: int) -> Any:
        return self.devir.get((p, s), 0)

    def blok_agirlikli_toplam(self, p: int, g: date, agirlik: Callable[[int], int]) -> Any:
        """g gununde BASLAYAN blogun agirlikli saat toplami (TD-1).

        ```
        Σ_{s ∈ gün g} w(s)·(z[p,s] − devir[p,s])  +  Σ_{s ∈ gün g+1} w(s)·devir[p,s]
        ```

        Ilk terim gunun kendi saatlerinden DEVRALINANLARI cikarir (onlar bir
        onceki gunun blogudur), ikinci terim ertesi gune TASANLARI ekler.
        Duvar saati toplamiyla karistirilmamali: H9 duvar saatinde on iki
        saatlik bir blogu 4 + 8 diye gorup gecirirdi.
        """
        toplam: Any = 0
        for s in self.gun_saatleri(g):
            katsayi = agirlik(s)
            if katsayi:
                toplam = toplam + katsayi * (self.zv(p, s) - self.devirv(p, s))
        sonraki = g + timedelta(days=1)
        if sonraki in self.zaman_ekseni:
            for s in self.gun_saatleri(sonraki):
                katsayi = agirlik(s)
                if katsayi:
                    toplam = toplam + katsayi * self.devirv(p, s)
        return toplam

    def blok_saati(self, p: int, g: date) -> Any:
        """g gununde baslayan blogun uzunlugu (H1'in asgarisi, H9'un tavani).

        ONBELLEKLI. Ifadenin kendisi 48 terimlidir (gunun saatleri +
        ertesi gune tasanlar) ve ALTI kural onu okur: H1, H5, H9, H10, S3,
        S4. Her cagrida yeniden acildiginda ayni bilgi modele defalarca
        kopyalanir - yirmi sekiz gunluk bir donemde yuz binlerce yinelenmis
        terim eder ve cozucu once onlari sadelestirmek zorunda kalir.
        `model_kur` ifadeyi bir kez bir tamsayi degiskene baglar; kurallar o
        degiskeni okur.
        """
        onbellek = self.gun_saat.get((p, g))
        if onbellek is not None:
            return onbellek
        return self.blok_agirlikli_toplam(p, g, lambda _s: 1)

    def gece_blok_saati(self, p: int, g: date) -> Any:
        """g gununde baslayan blogun gece saati (TD-2; H3 ve S2 ayni tabandan)."""
        onbellek = self.gece_saat.get((p, g))
        if onbellek is not None:
            return onbellek
        return self.blok_agirlikli_toplam(p, g, lambda s: 1 if self.gece_saati_mi(s) else 0)

    def calisti(self, p: int, g: date) -> Any:
        """p, g gununde calisiyor mu — gunde en fazla bir baslangic oldugu icin 0/1.

        Blogu bir onceki gun baslamis bir personel BU GUN calismis sayilmaz;
        blok basladigi gune yazilir (TD-1) ve ardisiklik, izin ve adalet
        hesaplarinin tamami ayni tabani kullanmak zorundadir.
        """
        onbellek = self.gun_calisti.get((p, g))
        if onbellek is not None:
            return onbellek
        toplam: Any = 0
        for s in self.gun_saatleri(g):
            toplam = toplam + self.basv(p, s)
        return toplam

    # --- Tanim sorgulari ---------------------------------------------------

    def gecmis_gece_saat(self, personel_id: int) -> float:
        return self.gecmis.sayac(personel_id).gece_saat if self.gecmis else 0.0

    def gecmis_hafta_sonu_saat(self, personel_id: int) -> float:
        return self.gecmis.sayac(personel_id).hafta_sonu_saat if self.gecmis else 0.0

    def gecmis_toplam_saat(self, personel_id: int) -> float:
        return self.gecmis.sayac(personel_id).toplam_saat if self.gecmis else 0.0

    def calisabilir_oran(self, personel_id: int) -> float:
        """Ufuk icinde calisabilir gun / ufuk gun sayisi (SRS TD-6).

        Gecmis yoksa 1.0: olcu yalniz donemi kapsar ve donem icinde herkes
        tam pay ile olculur.
        """
        return self.gecmis.oran(personel_id) if self.gecmis else 1.0

    def devir_fazla_calisma_saat(self, personel_id: int) -> float:
        """H10'un `devir[p]`si — TEK ERISIM NOKTASI.

        Turetilen deger varsa o kullanilir; icinde kayit alani zaten
        toplanmistir (`GecmisSayaclar.yasal_devir`). Iki parcanin burada
        ayrica toplanmasi kayit alanini iki kez sayardi.
        """
        if self.yasal_devir is not None:
            return self.yasal_devir.get(personel_id, 0.0)
        bilgi = self.personel.get(personel_id)
        return bilgi.devir_fazla_calisma_saat if bilgi is not None else 0.0

    def musait_mi(self, personel_id: int, an: datetime) -> bool:
        """H7: `an` saatiyle kesisen bir musaitlik kaydi varsa calisilamaz (TD-4).

        Olcu SAAT DILIMIDIR, gun degil: ogleden once izinli bir personel ayni
        gunun aksaminda calisabilir ve saat ekseni bunu artik ifade edebiliyor.
        """
        personel = self.personel.get(personel_id)
        if personel is not None:
            gun = an.date()
            if gun < personel.aktif_baslangic:
                return False
            if personel.aktif_bitis is not None and gun > personel.aktif_bitis:
                return False

        saat_bitis = an + SAAT
        for kayit in self.musaitlik:
            if kayit.personel_id != personel_id:
                continue
            for gun in _gun_araligi(kayit.baslangic_tarihi, kayit.bitis_tarihi):
                dilim_baslangic, dilim_bitis = _dilim_araligi(gun, kayit.dilim)
                if an < dilim_bitis and dilim_baslangic < saat_bitis:
                    return False
        return True

    def gunde_musait_mi(self, personel_id: int, tarih: date) -> bool:
        """SDD 5.2 on_kontrol: gunun EN AZ BIR saatinde musaitse gun musait sayilir."""
        return any(
            self.musait_mi(personel_id, datetime.combine(tarih, time(saat))) for saat in range(24)
        )

    def yetkin_mi(self, personel_id: int, yetkinlik_id: int) -> bool:
        personel = self.personel.get(personel_id)
        return personel is not None and yetkinlik_id in personel.yetkinlikler

    def erisebilir_mi(self, personel_id: int, nokta_id: int) -> bool:
        """H8'in on elemesi: noktanin on kosulu varsa personel onu tasimali."""
        nokta = self.gorev_noktalari.get(nokta_id)
        if nokta is None:
            return False
        return nokta.onkosul_yetkinlik_id is None or self.yetkin_mi(
            personel_id, nokta.onkosul_yetkinlik_id
        )

    def yetkinlik_adi(self, yetkinlik_id: int) -> str:
        """Bulgu metinleri icin ad; bilinmiyorsa kimlige duser (FR-5.6)."""
        return self.yetkinlik_adlari.get(yetkinlik_id) or f"#{yetkinlik_id} nolu yetkinlik"

    def nokta_adi(self, nokta_id: int) -> str:
        nokta = self.gorev_noktalari.get(nokta_id)
        return (nokta.ad if nokta and nokta.ad else "") or f"#{nokta_id} nolu nokta"

    def personel_adi(self, personel_id: int) -> str:
        return self.personel_adlari.get(personel_id) or f"#{personel_id} nolu personel"

    def gereken_sayi_saat(self, tarih: date, saat: int, nokta_id: int) -> int:
        """SAAT eksenli gereken sayi — kapsama kisitinin (S1) tabani."""
        return self.talep_saat.get((tarih, saat, nokta_id), 0)

    # --- Atama listelerinden turetilenler (dogrula tarafi) -----------------

    def sapma_saatleri(
        self, atamalar: Iterable[AtamaKaydi]
    ) -> tuple[dict[int, dict[tuple[date, int], int]], dict[int, dict[tuple[date, int], int]]]:
        """Talep ile atamanin SAAT BAZINDA farki: (eksik, fazla), nokta basina.

        TEK TANIM. Dogrulayicinin S1 bulgulari da, kalici sapma tablolari da
        (kapsama_acigi / fazla_kadro) buradan cikar; iki yerde yazilsaydi
        ayni cizelge icin farkli sayilar raporlanirdi.

        Isitma penceresi DISARIDA: talep tam zaman ekseni icin cozulur
        (TD-5) ama o gunlerin atamalari surumun parcasi degildir.
        """
        atanan = self.atanan_saat_sayilari(atamalar)
        eksik: dict[int, dict[tuple[date, int], int]] = {}
        fazla: dict[int, dict[tuple[date, int], int]] = {}
        for anahtar in set(atanan) | set(self.talep_saat):
            tarih, saat, nokta_id = anahtar
            if not self.donem_icinde(tarih):
                continue
            fark = atanan.get(anahtar, 0) - self.talep_saat.get(anahtar, 0)
            if fark < 0:
                eksik.setdefault(nokta_id, {})[(tarih, saat)] = -fark
            elif fark > 0:
                fazla.setdefault(nokta_id, {})[(tarih, saat)] = fark
        return eksik, fazla

    def atanan_saat_sayilari(
        self, atamalar: Iterable[AtamaKaydi]
    ) -> dict[tuple[date, int, int], int]:
        """Atamalarin SAAT eksenindeki karsiligi: `(duvar gunu, saat, nokta) -> kisi`.

        Anahtar DUVAR SAATIDIR, blogun sayildigi gun degil: talep "bu noktada
        bu saatte su kadar kisi bulunsun" der ve o saatin hangi gun baslamis
        bir bloktan doldugu talebi ilgilendirmez.
        """
        sayilar: dict[tuple[date, int, int], int] = {}
        for atama in atamalar:
            for an in atama.saatler():
                anahtar = (an.date(), an.hour, atama.nokta_id)
                sayilar[anahtar] = sayilar.get(anahtar, 0) + 1
        return sayilar

    def hafta_sonu_mu(self, tarih: date) -> bool:
        """TD-3: cumartesi/pazar veya resmi tatil hafta sonu sayilir."""
        return tarih.weekday() >= 5 or tarih in self.ozel_gunler

    def donem_icinde(self, tarih: date) -> bool:
        """TD-6: adalet sayaclari yalnizca planlama donemini kapsar, isitma penceresini degil.

        Donem sinirlari bilinmiyorsa (ornegin bu alani kullanmayan testlerde)
        her tarih donem ici sayilir.
        """
        if self.donem_baslangic is None or self.donem_bitis is None:
            return True
        return self.donem_baslangic <= tarih <= self.donem_bitis

    @property
    def donem_gunleri(self) -> list[date]:
        """Yalniz planlama donemi gunleri (isitma penceresi haric)."""
        if self.donem_baslangic is None or self.donem_bitis is None:
            return list(self.zaman_ekseni)
        return [g for g in self.zaman_ekseni if self.donem_baslangic <= g <= self.donem_bitis]

    def erisebilen(self, nokta_id: int) -> frozenset[int]:
        """Bir noktanin on kosulunu (H8) karsilayan personel.

        MUSAITLIGE BAKMAZ, yalniz yetkinlige: musaitlik donem icinde
        degisir, yetkinlik yapisaldir. Adil pay hesabi bu yuzden yetkinlik
        uzerinden kurulur - izne cikan bir personelin payi, izinli oldugu
        icin baskalarina devredilmis olmaz.
        """
        nokta = self.gorev_noktalari.get(nokta_id)
        if nokta is None:
            return frozenset()
        if nokta.onkosul_yetkinlik_id is None:
            return frozenset(self.personel)
        return frozenset(
            personel_id
            for personel_id, bilgi in self.personel.items()
            if nokta.onkosul_yetkinlik_id in bilgi.yetkinlikler
        )

    def adil_paylar(
        self,
        talep_uygun_mu: Callable[[tuple[date, int, int]], bool],
        *,
        olcu: str | None = None,
    ) -> dict[int, float]:
        """SRS 4.3 S2/S3: kisiye dusen ADIL PAY.

        ```
        erisebilen(n) = { q ∈ P : q, n'in on kosulunu karsiliyor }
        pay[p] = Σ_{d, t, n : p ∈ erisebilen(n)} talep[d,t,n] / |erisebilen(n)|
        ```

        HEDEF KISIYE OZELDIR, HAVUZ ORTALAMASI DEGIL (SRS 1.17). Tek bir
        ortalama kullanildiginda erisilebilirligi kisitli bir havuz KALICI
        olarak hedefin altinda gorunur: yalnizca tek bir noktada
        calisabilen personel, o noktanin talebi dusukse hedefe hicbir
        cizelgeyle ulasamaz. Bu bir adaletsizlik degil yapisal bir sinirdir
        ve olcunun onu sapma olarak raporlamasi, olcuyu ayirt edici
        olmaktan cikarir.

        Bu, bu projede IKI KEZ bedeli odenmis bir hatanin karsiligidir:
        once hic gece alamayan personel paydada sayiliyordu, sonra kisitli
        erisimi olan havuz tek ortalamaya vuruluyordu.

        Cozucu (modele_ekle), dogrulayici (dogrula) ve Analiz servisi (SDD
        5.7) ayni tabani kullanmak zorunda oldugu icin tanim burada, tek
        yerde durur.

        YUK ILE HEDEF BIRLIKTE OLCEKLENIR (SRS TD-6). `olcu` verildiginde
        ("gece", "hafta_sonu", "toplam") gecmis atamalarin payi donem
        talebinin payina EKLENIR; cagiran taraf da yuke gecmis saati ekler.
        Donem ici yuku ufuk boyunca hesaplanmis bir payla karsilastirmak,
        kisiyi hic yapmadigi bir isin hesabini verirken gostermek olurdu.

        Pay son adimda CALISABILIR ORANIYLA kucultulur: ufkun tamaminda
        calisabilir olmayan personel tam payla olculemez, yoksa kalici
        olarak hedefin altinda gorunur ve sapmasi hicbir cizelgeyle
        kapatilamaz.
        """
        paylar: dict[int, float] = dict.fromkeys(self.personel, 0.0)
        erisim_onbellegi: dict[int, frozenset[int]] = {}
        for (tarih, saat, nokta_id), gereken in self.talep_saat.items():
            if gereken <= 0 or not self.donem_icinde(tarih):
                continue
            if not talep_uygun_mu((tarih, saat, nokta_id)):
                continue
            if nokta_id not in erisim_onbellegi:
                erisim_onbellegi[nokta_id] = self.erisebilen(nokta_id)
            erisebilenler = erisim_onbellegi[nokta_id]
            if not erisebilenler:
                continue
            kisi_basi = gereken / len(erisebilenler)
            for personel_id in erisebilenler:
                paylar[personel_id] += kisi_basi

        # UFUK GENISLEMESI VE ORAN OLCEKLEMESI BIRLIKTE OLUR YA DA HIC OLMAZ.
        #
        # `olcu` verilmediginde cagiran DONEM ICI payi istiyor demektir ve
        # oran uygulanmamalidir: oran "kisi ufkun ne kadarinda calisabildi"
        # sorusunun cevabidir, donemin degil. Ikisini ayirmamak olculen bir
        # hataya yol acti - kabul olcumunun referans ornegi doksan gunluk
        # pencerenin yalnizca 32 gununu kapsiyordu, paylar 0,356 ile carpilip
        # 33-64 bandindan 11,7-22,8'e dusuyor, yuk ise donem ici kaldigi icin
        # sapma 34'ten 61,27'ye ciriyordu. Ne cozucu kotulesmisti ne veri;
        # yalnizca pay ile yuk farkli ufuklardan okunuyordu.
        if self.gecmis is None or olcu is None:
            return {p: payi_yuvarla(v) for p, v in paylar.items()}

        gecmis_pay = {
            "gece": self.gecmis.pay_gece,
            "hafta_sonu": self.gecmis.pay_hafta_sonu,
            "toplam": self.gecmis.pay_toplam,
        }[olcu]
        for personel_id, katki in gecmis_pay.items():
            if personel_id in paylar:
                paylar[personel_id] += katki
        for personel_id in paylar:
            paylar[personel_id] *= self.calisabilir_oran(personel_id)
        return {p: payi_yuvarla(v) for p, v in paylar.items()}

    def uygun_havuz(self, talep_uygun_mu: Callable[[tuple[date, int, int]], bool]) -> set[int]:
        """SRS S2/S3'teki P_gece / P_hs: PAYI SIFIRDAN BUYUK olan personel.

        Hedefe ulasmasi imkansiz olan kimse olculmez; kismen paylasabilen
        personel ise KENDI PAYI kadar olculur (bkz. `adil_paylar`).
        """
        return {p for p, pay in self.adil_paylar(talep_uygun_mu).items() if pay > 0}


def _gun_araligi(baslangic: date, bitis: date) -> Iterable[date]:
    gun = baslangic
    while gun <= bitis:
        yield gun
        gun += timedelta(days=1)


def _dilim_araligi(gun: date, dilim: MusaitlikDilimi) -> tuple[datetime, datetime]:
    gun_baslangici = datetime.combine(gun, time(0, 0))
    if dilim == MusaitlikDilimi.TAM_GUN:
        return gun_baslangici, gun_baslangici + timedelta(days=1)
    if dilim == MusaitlikDilimi.OGLEDEN_ONCE:
        return gun_baslangici, gun_baslangici + timedelta(hours=12)
    if dilim == MusaitlikDilimi.OGLEDEN_SONRA:
        return gun_baslangici + timedelta(hours=12), gun_baslangici + timedelta(days=1)
    raise ValueError(f"Bilinmeyen musaitlik dilimi: {dilim}")
