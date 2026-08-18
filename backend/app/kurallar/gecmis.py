"""Donem oncesi birikimin SEKLI ve aritmetigi (SRS TD-6, SDD 5.9).

Bu modul veritabani BILMEZ. Okuma isi `services/gecmis_sayaclar.py`de durur;
burada yalnizca "gecmis yuk nedir, adil paya nasil girer, calisabilirlik
orani neye boler" sorularinin cevabi var. Ayrimin nedeni yon: kural katmani
servis katmanini iceri almaz, tersi serbesttir.

IKI UFUK BIRBIRININ YERINE GECMEZ (SRS TD-6). Adalet ufku (S2/S3/S4) kayan
doksan gunluk penceredir; yasal ufuk (H10) isitma penceresini ve personel
kaydindaki devir bakiyesini kapsar. Ayni veri yapisindan gecerler ama AYRI
cagrilardir; tek cagrida birlestirilseydi hangi kuralin hangisini kullandigi
cagri yerine bakilmadan anlasilmazdi.
"""

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True, slots=True)
class PersonelSayaci:
    """Bir personelin ufuk icinde GERCEKLESEN yuku.

    Talep degil gerceklesen saat: gecmis donemlerin talep tanimlari o gunden
    bu yana degismis olabilir ve elimizdeki kesin bilgi kimin ne kadar
    calistigidir (SRS TD-6).
    """

    toplam_saat: float = 0.0
    gece_saat: float = 0.0
    hafta_sonu_saat: float = 0.0
    fazla_calisma_saat: float = 0.0


_BOS = PersonelSayaci()


@dataclass(frozen=True, slots=True)
class GecmisYuk:
    """Bir ufuk icin hesaplanmis birikim; `Baglam`a tek alan olarak takilir.

    `pay_*` alanlari gecmis atamalarin ADIL PAYA katkisidir, yukun kendisi
    degil. Ikisi ayri tutulur cunku olcu ikisini KARSILASTIRIR: yuk kisinin
    fiilen tasidigi, pay ise ayni pencerede ona dusen. Tek alanda tasinsalardi
    sapma her zaman sifir cikardi.
    """

    ufuk_gun: int
    pencere_bas: date
    # Pencerenin bittigi gun HARICTIR: donemin ilk gunu gecmis degildir.
    pencere_bit: date
    sayaclar: dict[int, PersonelSayaci] = field(default_factory=dict)
    pay_gece: dict[int, float] = field(default_factory=dict)
    pay_hafta_sonu: dict[int, float] = field(default_factory=dict)
    pay_toplam: dict[int, float] = field(default_factory=dict)
    # Ufkun tamaminda calisabilir olmayan personelin payi bu oranla kucultulur
    # (SRS TD-6). Bkz. `Baglam.calisabilir_oran`.
    calisabilir_oran: dict[int, float] = field(default_factory=dict)

    def sayac(self, personel_id: int) -> PersonelSayaci:
        return self.sayaclar.get(personel_id, _BOS)

    def oran(self, personel_id: int) -> float:
        """Kayit yoksa 1.0 — ufkun tamaminda calisabilir sayilir.

        Varsayilanin 0.0 olmasi, hakkinda bilgi bulunmayan personelin payini
        sifirlar ve onu olcunun tamamen disina atardi.
        """
        return self.calisabilir_oran.get(personel_id, 1.0)
