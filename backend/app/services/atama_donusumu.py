"""ORM `Atama` satirlarini kural motorunun `AtamaKaydi`sine cevirir — TEK YER.

Donusum kucuk ama bes yol ondan geciyor (dogrulama, sapma tablolari, analiz,
cozum servisi ve calisan paneli) ve hepsi ayni alan eslemesini yapmak
zorunda. Kopyalandiginda gozden kacan sey alan siralamasi degil ZAMAN
DILIMIDIR: `baslangic_zamani` timestamptz'dir ve saat dilimi tasir, kural
motoru ise duvar saatiyle calisir (`Baglam.saat_zamani` naive uretir).
Karsilastirmalar bu yuzden tek bir yerde naive yerel zamana indirgenir;
iki taraf ayrisirsa `saat_indeksi` sessizce None dondurur ve atama modele
hic girmez.
"""

from collections.abc import Iterable

from app.kurallar.baglam import AtamaKaydi
from app.models.sonuc import Atama


def atama_kaydina_cevir(atama: Atama) -> AtamaKaydi:
    return AtamaKaydi(
        personel_id=atama.personel_id,
        baslangic=atama.baslangic_zamani.replace(tzinfo=None),
        bitis=atama.bitis_zamani.replace(tzinfo=None),
        nokta_id=atama.nokta_id,
    )


def atama_kayitlarina_cevir(atamalar: Iterable[Atama]) -> list[AtamaKaydi]:
    return [atama_kaydina_cevir(a) for a in atamalar]


__all__ = ["atama_kaydina_cevir", "atama_kayitlarina_cevir"]
