"""Yikici veri temizliginin TEK tanimi: hangi tablolar, hangi sirayla, ve
hesaplara ne olur.

NEDEN TEK YERDE. Ayni sozlesme daha once iki yerde iki AYRI semantikle
yaziliydi: testler `TRUNCATE ... personel ... CASCADE` calistiriyordu,
betikler ise `DELETE`. Ikisi ayni sey degil.

  - `TRUNCATE ... CASCADE`, personel'e yabanci anahtarla bakan HER tabloyu
    bosaltir. `kullanici.personel_id -> personel` oldugu icin `kullanici`
    tablosunun tamami gidiyordu; personele hic bagli olmayan (personel_id
    NULL) YONETIM hesaplari dahil. Yani `pytest`, uzerinde kostugu
    veritabanindaki butun hesaplari siliyordu ve bu hicbir yerde yazmiyordu.
  - `DELETE` ise kaskad yapmaz. `kullanici_personel_id_fkey` ON DELETE
    NO ACTION oldugu icin, personele bagli tek bir calisan hesabi varken
    `DELETE FROM personel` yabanci anahtar hatasi verir: iki betik de o
    noktada cokerdi.

Ikisinin ortak sorunu ayni: SILINECEKLER LISTESINI kim yaziyor. `CASCADE`
onu PostgreSQL'e yazdirir; liste buyudugunde kimse fark etmez. Burada
liste ACIKTIR (`TEMIZLIK_SIRASI`) ve hesaplarin akibeti cagiranin ACIK
bir secimidir (`HesapKapsami`).

KAPSAM SECIMI.
  `HesapKapsami.HEPSI`           testler icin: hesap tablolari da sifirlanir.
  `HesapKapsami.PERSONELE_BAGLI` betikler icin: yalnizca personele bagli
                                 hesaplar silinir (yabanci anahtari tutan
                                 satirlar), personel_id'si bos olan yonetim
                                 hesaplarina DOKUNULMAZ. Boylece demo
                                 verisini yeniden uretmek sistemin giris
                                 kapisini kapatmaz.

Her iki yol da `uretim_kilidini_dogrula()`den gecer (bkz. asagisi).
"""

import enum
from dataclasses import dataclass

from sqlalchemy import delete, func, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.config import ayarlar
from app.db import Base
from app.models.girdi import Musaitlik, Tercih
from app.models.kimlik import Kullanici, OturumKaydi
from app.models.kural import Kural
from app.models.sonuc import (
    Atama,
    CizelgeSurumu,
    CozumIsi,
    Donem,
    FazlaKadro,
    KapsamaAcigi,
)
from app.models.tanim import (
    Bina,
    GorevNoktasi,
    OzelGun,
    Personel,
    PersonelYetkinlik,
    Talep,
    VardiyaTipi,
    Yetkinlik,
)

# Yikici islem izninin okundugu ayarin ortam degiskeni adi. Hata mesajinda
# gecmesi icin burada duruyor; degerin kendisi `ayarlar` uzerinden okunur.
IZIN_DEGISKENI = "VERI_TEMIZLIGINE_IZIN"


class HesapKapsami(enum.StrEnum):
    """Temizligin `kullanici`/`oturum` tablolarina ne yapacagi."""

    # Testler. Hesap tablolari da sifirlanir; test fikstürleri kendi
    # hesaplarini kurar ve aralarinda sizma olmamalidir.
    HEPSI = "hepsi"
    # Betikler. Yalnizca personele bagli hesaplar - yani `DELETE FROM
    # personel`i engelleyen satirlarin TAM KUMESI. Yonetim hesaplari kalir.
    PERSONELE_BAGLI = "personele_bagli"


# Cocuktan ebeveyne dogru yabanci anahtar sirasi. Liste burada durur ve
# elle bakilabilir; veritabanina "sen bul" denmez.
#
# `ozel_gun` de listededir. Eski iki listenin hicbirinde yoktu: hicbir
# tabloya bagli olmadigi icin silme sirasini bozmuyordu, ama artik
# arayuzden girilebilen bir tanim oldugundan (FR-1.10) temizlikten arta
# kalmasi, bir sonraki senaryoya sizan resmi tatil demek olurdu.
TEMIZLIK_SIRASI: tuple[type[Base], ...] = (
    KapsamaAcigi,
    FazlaKadro,
    CozumIsi,
    Atama,
    CizelgeSurumu,
    Musaitlik,
    Tercih,
    Donem,
    Talep,
    PersonelYetkinlik,
    Personel,
    GorevNoktasi,
    VardiyaTipi,
    Bina,
    Yetkinlik,
    OzelGun,
    Kural,
)


class UretimKilidiError(RuntimeError):
    """Yikici islem, izin verilmemis bir veritabaninda calistirilmak istendi."""


@dataclass(frozen=True)
class TemizlikSonucu:
    """Cagiranin kullaniciya bildirebilmesi icin: ne silindi."""

    silinen_hesap: int
    silinen_oturum: int


def _hedef_veritabani() -> str:
    """Hata mesajinda gosterilecek hedef - parola YAZILMAZ."""
    url = make_url(ayarlar.veritabani_url)
    return f"{url.host or 'yerel'}:{url.port or 5432}/{url.database}"


def uretim_kilidini_dogrula() -> None:
    """Yikici islemleri, izin acikca verilmedikce reddeder.

    Kilit acik bir ayar sartidir, veritabani ADI kontrolu degil: gelistirme
    ve gosterim veritabanlarinin ikisi de `vardiya` adini tasiyor,
    dolayisiyla ad hicbir sey ayirt etmezdi.

    Ayar gelistirme makinesinin `backend/.env` dosyasinda bulunur,
    sunucununkinde BULUNMAZ. Iki dosya birbirine karisamaz: `.env`
    dagitimda rsync ile DISLANIR (bkz. deploy/DAGITIM.md) ve sunucudaki
    `/opt/vardiya/.env` uygulama servisinin okudugu ayri bir dosyadir.
    Sunucuda `backend/.env` hic yoktur, dolayisiyla oradan calistirilan
    bir betik varsayilan degerle (kapali) karsilasir.

    Sunucuda gercekten calistirilmasi gerekirse degisken tek seferlik
    komutun onune yazilir; o zaman yikim bilincli bir eylem olur:

        VERI_TEMIZLIGINE_IZIN=true .venv/bin/python scripts/kabul_olcumu.py
    """
    if ayarlar.veri_temizligine_izin:
        return
    raise UretimKilidiError(
        f"Bu islem veritabanindaki tanim, girdi, sonuc ve hesap kayitlarini siler. "
        f"Hedef veritabani: {_hedef_veritabani()}. "
        f"Calistirmak icin {IZIN_DEGISKENI}=true olmalidir. "
        f"Gelistirme makinesinde bu satir backend/.env icindedir; gosterim "
        f"sunucusunda BULUNMAZ ve oraya kalici olarak eklenmemelidir "
        f"(bkz. app/veri_temizligi.py ve deploy/DAGITIM.md)."
    )


def hesaplari_temizle(oturum: Session, *, kapsam: HesapKapsami) -> TemizlikSonucu:
    """`kullanici` ve `oturum` tablolarini kapsama gore bosaltir.

    Oturumlar hesaplardan ONCE ve ACIKCA silinir. Veritabanindaki
    ON DELETE CASCADE bunu zaten yapardi; acikca yazilmasinin nedeni,
    silinenin sayilabilmesi ve listenin bu dosyada tam olmasidir.
    """
    uretim_kilidini_dogrula()

    secim = select(Kullanici.kullanici_id)
    if kapsam is HesapKapsami.PERSONELE_BAGLI:
        secim = secim.where(Kullanici.personel_id.is_not(None))
    hedefler = list(oturum.execute(secim).scalars().all())
    if not hedefler:
        return TemizlikSonucu(silinen_hesap=0, silinen_oturum=0)

    oturum_sayisi = oturum.execute(
        select(func.count()).select_from(OturumKaydi).where(OturumKaydi.kullanici_id.in_(hedefler))
    ).scalar_one()
    oturum.execute(delete(OturumKaydi).where(OturumKaydi.kullanici_id.in_(hedefler)))
    oturum.execute(delete(Kullanici).where(Kullanici.kullanici_id.in_(hedefler)))
    oturum.flush()
    return TemizlikSonucu(silinen_hesap=len(hedefler), silinen_oturum=int(oturum_sayisi))


def veriyi_temizle(oturum: Session, *, hesaplar: HesapKapsami) -> TemizlikSonucu:
    """Tanim, girdi, kural ve sonuc tablolarini bosaltir.

    Hesaplar ONCE temizlenir: `kullanici.personel_id` yabanci anahtari
    ON DELETE NO ACTION oldugundan, personele bagli bir hesap ayakta
    kalirsa `personel` silinemez ve butun temizlik bir yabanci anahtar
    hatasiyla duser.
    """
    sonuc = hesaplari_temizle(oturum, kapsam=hesaplar)

    # Cizelge surumu kendi kendine referans verir (onceki_surum_id). Tek
    # bir DELETE butun satirlari birlikte kaldirdigi icin kisit zaten
    # ihlal olmaz; yine de bag once koparilir ki kismi bir silme denenmesi
    # halinde sira bozulmasin.
    oturum.execute(CizelgeSurumu.__table__.update().values(onceki_surum_id=None))
    for model in TEMIZLIK_SIRASI:
        oturum.execute(delete(model))
    oturum.flush()
    return sonuc
