"""Bir tanimin baska kayitlarda kac kez gectigini sayar (madde 1).

Silme davranisinin tek karar noktasi burasidir: bir tanim herhangi bir yerde
kullaniliyorsa SILINMEZ, pasiflestirilir. Gerekce SDD 4.1'de: atama, talep ve
kapsama_acigi satirlari tanim satirlarina yabanci anahtarla baglidir; tanim
satiri gidince yayinlanmis gecmis cizelgeler okunamaz hale gelir.

Sayim ile silme ayni tablodan beslenir. Ayri yazilsalardi arayuzun onay
kutusunda soyledigi ("42 atamada kullaniliyor, pasiflestirilecek") ile
DELETE'in fiilen yaptigi sey zamanla ayrisabilirdi.
"""

from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import InstrumentedAttribute, Session

from app.db import Base
from app.models.girdi import Musaitlik, Tercih
from app.models.kimlik import Kullanici
from app.models.sonuc import Atama, KapsamaAcigi
from app.models.tanim import (
    Bina,
    GorevNoktasi,
    Personel,
    PersonelYetkinlik,
    Talep,
    VardiyaTipi,
    Yetkinlik,
)


@dataclass(frozen=True, slots=True)
class KullanimKaynagi:
    """Tanima referans veren tek bir yabanci anahtar sutunu.

    Sutun lambda yerine dogrudan tutulur; boylece bu listenin modeldeki
    gercek yabanci anahtarlarla ortustugu testte karsilastirilabiliyor.
    """

    # Kullaniciya gosterilecek ad ("atama", "talep satiri"); alan adi degil,
    # operasyon dili (NFR-5).
    kayit_turu: str
    sutun: InstrumentedAttribute[Any]


@dataclass(frozen=True, slots=True)
class Kullanim:
    kullanimda_mi: bool
    toplam: int
    kalemler: tuple[tuple[str, int], ...]


# Her tanim varligi icin ona referans veren tablolar. Yeni bir referans
# eklendiginde (or. yeni bir tablo vardiya_tipi'ne baglandiginda) buraya bir
# satir eklenmezse silme sessizce yabanci anahtar hatasina duser; testte bu
# liste ile modeldeki gercek yabanci anahtarlar karsilastirilir.
_KAYNAKLAR: dict[type[Base], tuple[KullanimKaynagi, ...]] = {
    Yetkinlik: (
        KullanimKaynagi("personel yetkinliği", PersonelYetkinlik.yetkinlik_id),
        KullanimKaynagi("görev noktası ön koşulu", GorevNoktasi.onkosul_yetkinlik_id),
    ),
    Bina: (KullanimKaynagi("görev noktası", GorevNoktasi.bina_id),),
    VardiyaTipi: (
        KullanimKaynagi("atama", Atama.vardiya_tipi_id),
        KullanimKaynagi("talep satırı", Talep.vardiya_tipi_id),
        KullanimKaynagi("tercih", Tercih.vardiya_tipi_id),
        KullanimKaynagi("sabit vardiyalı personel", Personel.sabit_vardiya_tipi_id),
        KullanimKaynagi("kapsama açığı", KapsamaAcigi.vardiya_tipi_id),
    ),
    GorevNoktasi: (
        KullanimKaynagi("atama", Atama.nokta_id),
        KullanimKaynagi("talep satırı", Talep.nokta_id),
        KullanimKaynagi("kapsama açığı", KapsamaAcigi.nokta_id),
    ),
    Personel: (
        KullanimKaynagi("atama", Atama.personel_id),
        KullanimKaynagi("müsaitlik kaydı", Musaitlik.personel_id),
        KullanimKaynagi("tercih", Tercih.personel_id),
        KullanimKaynagi("yetkinlik ataması", PersonelYetkinlik.personel_id),
        # Calisan hesabi personele baglidir (FR-10.6). Sayima girmezse
        # hesabi olan bir personel "hicbir kayitta kullanilmiyor" gorunur,
        # gercek silme denenir ve yabanci anahtar kisitina duser. Sonuc
        # pasiflestirme olmalidir: hesap ayakta kalir, personel yeni
        # cizelgelere girmez.
        KullanimKaynagi("kullanıcı hesabı", Kullanici.personel_id),
    ),
}


def kaynaklari_getir(model: type[Base]) -> tuple[KullanimKaynagi, ...]:
    return _KAYNAKLAR[model]


def sayilan_modeller() -> tuple[type[Base], ...]:
    return tuple(_KAYNAKLAR)


def kullanimi_olc(oturum: Session, model: type[Base], id_: int) -> Kullanim:
    """Tanimin kac kayitta gectigini kayit turu kiriliminda dondurur.

    Sifir olan kalemler listeye girmez; arayuz yalnizca gercekten var olan
    kullanimlari yazar ("Bu personel 42 atamada kullanılıyor").
    """
    kalemler: dict[str, int] = {}
    for kaynak in _KAYNAKLAR[model]:
        sayi = int(
            oturum.execute(
                select(func.count()).select_from(kaynak.sutun.parent).where(kaynak.sutun == id_)
            ).scalar_one()
        )
        if sayi:
            # Ayni kayit turu adi birden fazla sutundan gelebilir (or. iki ayri
            # sutun da "atama" ise); kullaniciya tek satir olarak toplanir.
            kalemler[kaynak.kayit_turu] = kalemler.get(kaynak.kayit_turu, 0) + sayi
    toplam = sum(kalemler.values())
    return Kullanim(kullanimda_mi=toplam > 0, toplam=toplam, kalemler=tuple(kalemler.items()))
