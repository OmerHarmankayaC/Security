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

from app.models.girdi import MusaitlikDilimi, TercihTipi


@dataclass(frozen=True, slots=True)
class VardiyaTipiBilgisi:
    vardiya_tipi_id: int
    baslangic_saati: time
    bitis_saati: time
    sure_saat: float
    gece_mi: bool


@dataclass(frozen=True, slots=True)
class GorevNoktasiBilgisi:
    nokta_id: int
    onkosul_yetkinlik_id: int | None = None
    bina_id: int | None = None


@dataclass(frozen=True, slots=True)
class PersonelBilgisi:
    personel_id: int
    aktif_baslangic: date
    aktif_bitis: date | None = None
    yetkinlikler: frozenset[int] = frozenset()
    haftalik_hedef_saat: float = 0.0


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
    # (tarih, vardiya_tipi_id, nokta_id) -> gereken_sayi; istisna/genel talep satiri
    # cakismasi (SDD 4.2.1) Baglam'i kuran taraf (repository/servis) tarafindan
    # onceden cozulmus olarak verilir.
    talep: dict[tuple[date, int, int], int] = field(default_factory=dict)
    donem_baslangic: date | None = None
    donem_bitis: date | None = None
    ozel_gunler: frozenset[date] = frozenset()
    tercihler: list[TercihKaydi] = field(default_factory=list)
    # Yalniz yeniden cozum dogrulamasinda dolu olur (S8); normalde None.
    onceki_atamalar: list[AtamaKaydi] | None = None
    # Asagidaki iki alan yalniz model kurma sirasinda (model_kur) doldurulur;
    # dogrula cagrilarinda bos kalir (SDD 5.3: "baglam <- Baglam(tanimlar,
    # donem, zaman_ekseni, y)").
    zaman_ekseni: list[date] = field(default_factory=list)
    y: dict[tuple[int, date, int], Any] = field(default_factory=dict)
    # S1TalepKarsilama.modele_ekle tarafindan doldurulur: (tarih, vardiya_tipi_id,
    # nokta_id) -> eksik IntVar'i. Cozumden sonra kapsama_acigi tablosuna yazilacak
    # degerleri okumak icin (SDD 5.4: 'cozum.eksik_degiskenleri').
    kapsama_eksikleri: dict[tuple[date, int, int], Any] = field(default_factory=dict)

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

    def gereken_sayi(self, tarih: date, vardiya_tipi_id: int, nokta_id: int) -> int:
        return self.talep.get((tarih, vardiya_tipi_id, nokta_id), 0)

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

    def uygun_havuz(self, talep_uygun_mu: Callable[[tuple[date, int, int]], bool]) -> set[int]:
        """SRS S2/S3'teki P_gece / P_hs: ilgili talebi bulunan EN AZ BIR gorev
        noktasinin on kosulunu (H8) karsilayan personel.

        Neden gerekli: yetkinligi geregi o talebin bulundugu hicbir noktada
        calisamayan personel, sayisi hicbir cizelgede sifirdan yukari
        cikamayacagi icin paydaya dahil edildiginde KALICI olarak "hedefin
        altinda" gorunur. Bu sapma hicbir cizelgeyle kapatilamaz; hedef
        ayirt ediciligini kaybeder ve kabul kriteri saglanamaz hale gelir
        (SRS 1.5'te S2/S3 bu yuzden duzeltildi). Adalet, yuku
        paylasabilecekler arasinda paylastirmaktir.

        Cozucu (modele_ekle), dogrulayici (dogrula) ve Analiz servisi (SDD
        5.7) ayni tabani kullanmak zorunda oldugu icin tanim burada, tek
        yerde durur.
        """
        uygun_noktalar = {
            nokta_id
            for (tarih, vardiya_tipi_id, nokta_id), gereken in self.talep.items()
            if gereken > 0
            and self.donem_icinde(tarih)
            and talep_uygun_mu((tarih, vardiya_tipi_id, nokta_id))
        }
        havuz: set[int] = set()
        for personel_id, bilgi in self.personel.items():
            for nokta_id in uygun_noktalar:
                nokta = self.gorev_noktalari.get(nokta_id)
                if nokta is None:
                    continue
                if (
                    nokta.onkosul_yetkinlik_id is None
                    or nokta.onkosul_yetkinlik_id in bilgi.yetkinlikler
                ):
                    havuz.add(personel_id)
                    break
        return havuz

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
