"""Kurallarin modele_ekle/dogrula metotlarina aktarilan calisma baglami.

Cozucu ve dogrulayici, veritabanindan okudugu tanim ve girdi verisini bu
hafif, ORM'den bagimsiz yapiya donusturur (SDD 3.2.1: "her iki yorumlayici
da ayni kural nesnesinden beslenir"). ORM'den bagimsiz olmasi, kural
birim testlerinin veritabani gerektirmeden elle kurulan ornekler uzerinde
calismasini saglar.
"""

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

from app.models.girdi import MusaitlikDilimi


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


@dataclass(frozen=True, slots=True)
class PersonelBilgisi:
    personel_id: int
    aktif_baslangic: date
    aktif_bitis: date | None = None
    yetkinlikler: frozenset[int] = frozenset()


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


@dataclass(slots=True)
class Baglam:
    vardiya_tipleri: dict[int, VardiyaTipiBilgisi]
    gorev_noktalari: dict[int, GorevNoktasiBilgisi]
    personel: dict[int, PersonelBilgisi]
    musaitlik: list[MusaitlikKaydi] = field(default_factory=list)

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
        _, onceki_bitis = self.vardiya_araligi(onceki.tarih, onceki.vardiya_tipi_id)
        sonraki_baslangic, _ = self.vardiya_araligi(sonraki.tarih, sonraki.vardiya_tipi_id)
        return (sonraki_baslangic - onceki_bitis).total_seconds() / 3600

    def gece_mi(self, vardiya_tipi_id: int) -> bool:
        return self.vardiya_tipleri[vardiya_tipi_id].gece_mi

    def sure_saat(self, vardiya_tipi_id: int) -> float:
        return self.vardiya_tipleri[vardiya_tipi_id].sure_saat

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

    def yetkin_mi(self, personel_id: int, yetkinlik_id: int) -> bool:
        personel = self.personel.get(personel_id)
        return personel is not None and yetkinlik_id in personel.yetkinlikler


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
