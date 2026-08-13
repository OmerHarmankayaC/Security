"""Kurallarin modele_ekle/dogrula metotlarina aktarilan calisma baglami.

Cozucu ve dogrulayici, veritabanindan okudugu tanim ve girdi verisini bu
hafif, ORM'den bagimsiz yapiya donusturur (SDD 3.2.1: "her iki yorumlayici
da ayni kural nesnesinden beslenir"). ORM'den bagimsiz olmasi, kural
birim testlerinin veritabani gerektirmeden elle kurulan ornekler uzerinde
calismasini saglar.
"""

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from itertools import product
from typing import Any

from app.kurallar.zaman_araligi import aralik_saatleri as _aralik_saatleri
from app.kurallar.zaman_araligi import gece_saat_sayisi
from app.models.girdi import MusaitlikDilimi, TercihTipi


@dataclass(frozen=True, slots=True)
class VardiyaTipiBilgisi:
    vardiya_tipi_id: int
    baslangic_saati: time
    bitis_saati: time
    sure_saat: float
    gece_mi: bool
    # Yalniz KULLANICIYA GOSTERILEN metin icin; hicbir kural karari ada
    # bakmaz (SRS 2.4: "kurallar vardiya adina degil zaman bilgisine gore
    # ifade edilir"). Varsayilani bos: ad tasimayan bir baglam kurmak
    # (testler) hala gecerli, yalnizca ihlal metni kimlikle yazilir.
    ad: str = ""


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
    # H10: kota yilinin basindan bu doneme kadar birikmis fazla calisma
    # saati. BU TURDA personel kaydindaki alandan gelir; yayinlanmis
    # surumlerden turetme Tur 5'in isi (`GecmisSayaclar`), o zaman ikisi
    # TOPLANIR - alan turetilen degerin yerine gecmez (TD-6).
    devir_fazla_calisma_saat: float = 0.0


@dataclass(frozen=True, slots=True)
class MusaitlikKaydi:
    personel_id: int
    baslangic_tarihi: date
    bitis_tarihi: date
    dilim: MusaitlikDilimi


@dataclass(frozen=True, slots=True)
class AtamaKaydi:
    """Atama tablosunun (SDD 4.2.4) kural degerlendirmesi icin gereken alt kumesi."""

    personel_id: int
    tarih: date
    vardiya_tipi_id: int
    nokta_id: int


@dataclass(frozen=True, slots=True)
class TercihKaydi:
    """Onaylanmis bir tercih kaydi (SDD 4.2.2). Sadece onaylanmislar Baglam'a girer (SRS S5)."""

    personel_id: int
    tarih: date
    tip: TercihTipi
    vardiya_tipi_id: int | None = None


@dataclass(slots=True)
class Baglam:
    vardiya_tipleri: dict[int, VardiyaTipiBilgisi]
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
    # K20): bulgu metinleri veritabani kimligi degil AD tasir. Bos
    # birakildiginda metin kimlige duser - elle kurulan test baglamlari
    # icin gecerli kalir.
    yetkinlik_adlari: dict[int, str] = field(default_factory=dict)
    # Ayni gerekce (K20): kota bulgulari personeli KIMLIKLE degil ADLA
    # gosterir. Bos birakildiginda metin kimlige duser.
    personel_adlari: dict[int, str] = field(default_factory=dict)
    tercihler: list[TercihKaydi] = field(default_factory=list)
    # Yalniz yeniden cozum dogrulamasinda dolu olur (S8); normalde None.
    onceki_atamalar: list[AtamaKaydi] | None = None
    # Asagidaki iki alan yalniz model kurma sirasinda (model_kur) doldurulur;
    # dogrula cagrilarinda bos kalir (SDD 5.3: "baglam <- Baglam(tanimlar,
    # donem, zaman_ekseni, y)").
    zaman_ekseni: list[date] = field(default_factory=list)
    y: dict[tuple[int, date, int], Any] = field(default_factory=dict)
    # S1TalepKarsilama.modele_ekle tarafindan doldurulur: (tarih, saat,
    # nokta_id) -> eksik IntVar'i. Cozumden sonra kapsama_acigi tablosuna yazilacak
    # degerleri okumak icin (SDD 5.4: 'cozum.eksik_degiskenleri').
    kapsama_eksikleri: dict[tuple[date, int, int], Any] = field(default_factory=dict)
    # Ayni saatlerin FAZLA kadro degiskenleri; fazla_kadro tablosuna yazilir.
    kapsama_fazlalari: dict[tuple[date, int, int], Any] = field(default_factory=dict)
    # S1f'in ceza terimini kurabilmesi icin: gruplanmis fazla degiskeni ->
    # (degisken, grubun saat sayisi). S1 ile S1f AYNI gruplamayi paylasir;
    # ikinci bir gruplama yazmak ayni hesabi iki yerde tutmak olurdu.
    kadro_fazlalari: dict[tuple[date, int, int], tuple[Any, int]] = field(default_factory=dict)

    def vardiya_araligi(self, tarih: date, vardiya_tipi_id: int) -> tuple[datetime, datetime]:
        """Vardiyanin mutlak baslangic/bitis zamani (TD-1: vardiya baslangic gunune yazilir)."""
        vt = self.vardiya_tipleri[vardiya_tipi_id]
        baslangic = datetime.combine(tarih, vt.baslangic_saati)
        bitis = datetime.combine(tarih, vt.bitis_saati)
        if vt.bitis_saati <= vt.baslangic_saati:
            bitis += timedelta(days=1)
        return baslangic, bitis

    def saat_farki(self, onceki: AtamaKaydi, sonraki: AtamaKaydi) -> float:
        """onceki vardiyanin bitisiyle sonraki vardiyanin baslangici arasindaki saat farki (H2)."""
        return self.saat_farki_ham(
            onceki.tarih, onceki.vardiya_tipi_id, sonraki.tarih, sonraki.vardiya_tipi_id
        )

    def saat_farki_ham(self, g1: date, v1: int, g2: date, v2: int) -> float:
        """saat_farki'nin ham (gun, vardiya) argumanlariyla calisan hali; model kurarken
        (Ek A H2 ornegi: `baglam.saat_farki(g1, v1, g2, v2)`) AtamaKaydi'ya ihtiyac duymadan
        kullanilir."""
        _, bitis1 = self.vardiya_araligi(g1, v1)
        baslangic2, _ = self.vardiya_araligi(g2, v2)
        return (baslangic2 - bitis1).total_seconds() / 3600

    def gece_mi(self, vardiya_tipi_id: int) -> bool:
        return self.vardiya_tipleri[vardiya_tipi_id].gece_mi

    def sure_saat(self, vardiya_tipi_id: int) -> float:
        return self.vardiya_tipleri[vardiya_tipi_id].sure_saat

    def devir_fazla_calisma_saat(self, personel_id: int) -> float:
        """H10'un `devir[p]`i. Personel baglamda yoksa sifir."""
        bilgi = self.personel.get(personel_id)
        return bilgi.devir_fazla_calisma_saat if bilgi is not None else 0.0

    def gece_saat(self, vardiya_tipi_id: int) -> int:
        """Blogun gece donemiyle (20:00-06:00) kesisen saat sayisi (TD-2).

        `gece_mi` BAYRAGIYLA KARISTIRILMAMALI: bayrak "bu bir gece nobeti
        midir" sorusunun ikili yanitidir ve H3 onu kullanir; buradaki olcu
        surekli bir buyukluktur ve S2 onu kullanir. Hesap tek yerde
        (`zaman_araligi.gece_saat_sayisi`).
        """
        vt = self.vardiya_tipleri[vardiya_tipi_id]
        return gece_saat_sayisi(vt.baslangic_saati, vt.bitis_saati)

    def sure_dakika(self, vardiya_tipi_id: int) -> int:
        """CP-SAT tamsayi katsayi gerektirdigi icin sure_saat'in dakika cinsinden tam sayisi."""
        return int(self.vardiya_tipleri[vardiya_tipi_id].sure_saat * 60)

    def musait_mi(self, atama: AtamaKaydi) -> bool:
        """H7: aktiflik araligi disi veya musaitlik kaydiyla kesisme durumunda musait degildir."""
        personel = self.personel.get(atama.personel_id)
        if personel is not None:
            if atama.tarih < personel.aktif_baslangic:
                return False
            if personel.aktif_bitis is not None and atama.tarih > personel.aktif_bitis:
                return False

        vardiya_baslangic, vardiya_bitis = self.vardiya_araligi(atama.tarih, atama.vardiya_tipi_id)
        for kayit in self.musaitlik:
            if kayit.personel_id != atama.personel_id:
                continue
            for gun in _gun_araligi(kayit.baslangic_tarihi, kayit.bitis_tarihi):
                if not (atama.tarih - timedelta(days=1) <= gun <= atama.tarih + timedelta(days=1)):
                    continue
                dilim_baslangic, dilim_bitis = _dilim_araligi(gun, kayit.dilim)
                if vardiya_baslangic < dilim_bitis and dilim_baslangic < vardiya_bitis:
                    return False
        return True

    def gunde_musait_mi(self, personel_id: int, tarih: date) -> bool:
        """SDD 5.2 on_kontrol: 'p, g gununde musait' - en az bir vardiya tipi icin
        musaitse gun musait sayilir (ozel_gun/nokta ayrimi yapilmaz, kaba bir kontroldur)."""
        return any(
            self.musait_mi(AtamaKaydi(personel_id, tarih, v, 0)) for v in self.vardiya_tipleri
        )

    def yetkin_mi(self, personel_id: int, yetkinlik_id: int) -> bool:
        personel = self.personel.get(personel_id)
        return personel is not None and yetkinlik_id in personel.yetkinlikler

    def yetkinlik_adi(self, yetkinlik_id: int) -> str:
        """Bulgu metinleri icin ad; bilinmiyorsa kimlige duser (FR-5.6)."""
        return self.yetkinlik_adlari.get(yetkinlik_id) or f"#{yetkinlik_id} nolu yetkinlik"

    def nokta_adi(self, nokta_id: int) -> str:
        nokta = self.gorev_noktalari.get(nokta_id)
        return (nokta.ad if nokta and nokta.ad else "") or f"#{nokta_id} nolu nokta"

    def personel_adi(self, personel_id: int) -> str:
        return self.personel_adlari.get(personel_id) or f"#{personel_id} nolu personel"

    def vardiya_adi(self, vardiya_tipi_id: int) -> str:
        vardiya = self.vardiya_tipleri.get(vardiya_tipi_id)
        return (vardiya.ad if vardiya and vardiya.ad else "") or f"#{vardiya_tipi_id} nolu blok"

    def gereken_sayi_saat(self, tarih: date, saat: int, nokta_id: int) -> int:
        """SAAT eksenli gereken sayi — kapsama kisitinin (S1) tabani."""
        return self.talep_saat.get((tarih, saat, nokta_id), 0)

    def blok_saatleri(self, tarih: date, vardiya_tipi_id: int) -> list[tuple[date, int]]:
        """Blogun kapsadigi (gun, saat) duvar saati dilimleri.

        Bir personel bir saatte, o saati kapsayan bloga atanmissa sayilir
        (SRS 4.3 S1). Gece yarisini asan blok ertesi gunun saatlerini de
        kapsar; atamanin KENDISI TD-1 uyarinca baslangic gunune yazili
        kalir, degisen yalnizca hangi duvar saatlerini doldurdugudur.
        """
        vt = self.vardiya_tipleri[vardiya_tipi_id]
        return list(_aralik_saatleri(tarih, vt.baslangic_saati, vt.bitis_saati))

    def sapma_saatleri(
        self, atamalar: Iterable[AtamaKaydi]
    ) -> tuple[dict[int, dict[tuple[date, int], int]], dict[int, dict[tuple[date, int], int]]]:
        """Talep ile atamanin SAAT BAZINDA farki: (eksik, fazla), nokta basina.

        TEK TANIM. Dogrulayicinin S1 bulgulari da, kalici sapma tablolari da
        (kapsama_acigi / fazla_kadro) buradan cikar; iki yerde yazilsaydi
        biri "her satir bir aciktir" varsayimini digeri baska bir esigi
        tasirdi ve ayni cizelge icin farkli sayilar raporlanirdi.

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
        """Atamalarin SAAT eksenindeki karsiligi: `(gun, saat, nokta) -> kisi`.

        "Atamalardan kapsama" hesabinin TEK tanimidir; dogrulayici (S1),
        sapma tablolari ve analiz servisi ayni sayiyi uretmek zorundadir
        (SDD 3.2.1). Bilinmeyen bir blok tipi tasiyan atama sessizce
        atlanir - pasiflestirilmis bir blogun eski atamalari boyle
        gorunebilir ve o atama zaten hicbir saati dolduramaz.
        """
        sayilar: dict[tuple[date, int, int], int] = {}
        for atama in atamalar:
            if atama.vardiya_tipi_id not in self.vardiya_tipleri:
                continue
            for saat_gunu, saat in self.blok_saatleri(atama.tarih, atama.vardiya_tipi_id):
                anahtar = (saat_gunu, saat, atama.nokta_id)
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
        """Yalniz planlama donemi gunleri (isitma penceresi haric); esnek hedeflerin
        cogu (S1-S7) TD-6'daki adalet ufku ilkesiyle tutarli olarak bu listeyi kullanir."""
        if self.donem_baslangic is None or self.donem_bitis is None:
            return list(self.zaman_ekseni)
        return [g for g in self.zaman_ekseni if self.donem_baslangic <= g <= self.donem_bitis]

    @property
    def gece_vardiyalari(self) -> frozenset[int]:
        return frozenset(v for v, vt in self.vardiya_tipleri.items() if vt.gece_mi)

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
        self, talep_uygun_mu: Callable[[tuple[date, int, int]], bool]
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

        Ayni mantik S4'un adil pay tanimindan geliyor; uc adalet hedefi de
        artik kisiye dusen payi olcer.

        Cozucu (modele_ekle), dogrulayici (dogrula) ve Analiz servisi (SDD
        5.7) ayni tabani kullanmak zorunda oldugu icin tanim burada, tek
        yerde durur.
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
        return paylar

    def uygun_havuz(self, talep_uygun_mu: Callable[[tuple[date, int, int]], bool]) -> set[int]:
        """SRS S2/S3'teki P_gece / P_hs: PAYI SIFIRDAN BUYUK olan personel.

        Hedefe ulasmasi imkansiz olan kimse olculmez; kismen paylasabilen
        personel ise KENDI PAYI kadar olculur (bkz. `adil_paylar`).
        """
        return {p for p, pay in self.adil_paylar(talep_uygun_mu).items() if pay > 0}

    @property
    def vardiya_ciftleri(self) -> list[tuple[int, int]]:
        """Model kurarken (H2) taranacak tum (v1, v2) vardiya tipi ciftleri (Ek A)."""
        return list(product(self.vardiya_tipleri, self.vardiya_tipleri))

    @property
    def gun_ciftleri(self) -> list[tuple[date, date]]:
        """Model kurarken (H2) taranacak tum (g1, g2) gun ciftleri (Ek A).

        zaman_ekseni'nin ardisik takvim gunlerinden olusan sirali bir liste
        oldugu varsayilir (model_kur bunu boyle kurar)."""
        return list(product(self.zaman_ekseni, self.zaman_ekseni))


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
