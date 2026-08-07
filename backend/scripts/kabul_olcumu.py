#!/usr/bin/env python3
"""Proje Tanim Dokumani bolum 5'teki kabul kriterlerini OLCER ve raporlar
(UYGULAMA_PLANI.md Sprint 3 Gun 14).

Olculen bes kriter (planin Gun 14 maddesinde sayilanlar):

  K1  Kirk personel / yirmi sekiz gunluk referans ornek altmis saniyenin
      altinda cozulur.                                     (Charter 5, NFR-1)
  K2  Uretilen cizelgede zorunlu kisit ihlali bulunmaz.     (Charter 5)
  K3  Kisi basina dusen gece sayisi hedeften en fazla bir birim sapar.
                                                            (Charter 5, NFR-9)
  K4  Kasten celiskili kurulan ornekte sistem hangi gun, hangi vardiyada ve
      kac kisi eksik kaldigini gosterir.                     (Charter 5)
  K5  Manuel duzenlemede kural ihlali bir saniyenin altinda bildirilir.
                                                            (Charter 5, NFR-2)

Charter'in altinci kriteri ("yeniden cozumde degisen atama sayisi
raporlanir") burada OLCULMEZ: raporlama yuzeyi Surumler ekranindaki
karsilastirma islevidir (SDD 6.3.5) ve o ekran Gun 15'in isidir. Planin
Gun 14 maddesi de bes kriter sayar.

REFERANS DONANIM (SDD 3.4.2): dort cekirdek, sekiz gigabayt. CP-SAT paralel
arama yurutur, dolayisiyla sure cekirdek sayisina dogrudan baglidir ve
donanim belirtilmeden verilen bir olcum tekrarlanabilir degildir. Bu betik
arama iscisi sayisini SDD 3.4.3'teki referans degere (dort cekirdegin bir
eksigi = 3) sabitler; boylece daha cok cekirdekli bir makinede calissa bile
cozucunun PARALELLIGI referans donanimla ayni olur. Cekirdek BASINA hiz
farki kalir - bu yuzden rapor, uzerinde calisilan makineyi de yazar.

Kullanim:
    python scripts/kabul_olcumu.py            # olc, tabloyu yazdir
    python scripts/kabul_olcumu.py --json     # makine okunur cikti

DIKKAT: Betik kendi olcum verisini kurabilmek icin veritabanindaki tanim,
girdi, kural ve sonuc tablolarini TEMIZLER (demo_veri_uret.py --reset ile
ayni sozlesme). Olcum verisi sonda birakilir; basarisiz bir kriter
incelenebilsin diye silinmez.

Cikis kodu: butun kriterler gectiyse 0, en az biri gectiyse 1.
"""

import argparse
import json
import sys
import time as zaman
from dataclasses import dataclass, field
from datetime import date, time, timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.config import ayarlar  # noqa: E402
from app.cozucu import CozucuAdaptoru, model_kur  # noqa: E402
from app.db import OturumYerel  # noqa: E402
from app.kurallar.baglam import AtamaKaydi  # noqa: E402
from app.kurallar.kayit_defteri import bul  # noqa: E402
from app.models.girdi import Musaitlik, MusaitlikDilimi, MusaitlikTipi, Tercih  # noqa: E402
from app.models.kural import Kural  # noqa: E402
from app.models.kural import KuralTipi as KuralTipiEnum
from app.models.sonuc import (  # noqa: E402
    Atama,
    AtamaKaynagi,
    CizelgeSurumu,
    CizelgeSurumuDurumu,
    CozumIsi,
    Donem,
    KapsamaAcigi,
)
from app.models.tanim import (  # noqa: E402
    Bina,
    GorevNoktasi,
    Personel,
    PersonelYetkinlik,
    Talep,
    VardiyaTipi,
    Yetkinlik,
)
from app.services.baglam_kurucu import baglam_olustur, zaman_ekseni_olustur  # noqa: E402
from app.services.dogrulama_servisi import AtamaDegisikligi, DogrulamaServisi  # noqa: E402
from app.services.ornek_senaryo import (  # noqa: E402
    NOKTA_TANIMLARI,
    talep_satirlarini_olustur,
)
from app.services.vardiya_hesaplari import sure_saat_hesapla  # noqa: E402

# --- Referans ornek (Charter 5 / NFR-1: kirk personel, yirmi sekiz gun) ------

REFERANS_PERSONEL_SAYISI = 40
REFERANS_GUN_SAYISI = 28
REFERANS_BASLANGIC = date(2026, 2, 2)  # Pazartesi
CELISKILI_BASLANGIC = date(2026, 6, 1)  # Pazartesi

# SRS 3.3.6'daki havuz asgarileri (izin payiyla): Vardiya Sefi 7, Muracaat 6,
# Guvenlik Gorevi 23. Demo senaryosunun 44 kisilik kadrosu (9/7/28) referans
# olcek olan 40'a, YALNIZCA Guvenlik Gorevi havuzu 28'den 24'e cekilerek
# indirildi: kirilgan iki havuz (VS, MR) oldugu gibi korunur, Guvenlik
# Gorevi verebilen toplam kadro 9+24=33 ile 23 asgarisinin uzerinde kalir.
_REFERANS_GRUPLARI: tuple[tuple[tuple[str, ...], int, str], ...] = (
    (("Vardiya Şefi", "Güvenlik Görevi"), 9, "VS"),
    (("Müracaat Görevlisi",), 7, "MR"),
    (("Güvenlik Görevi",), 24, "GG"),
)

# SRS 3.3.1'deki tablo birebir: (baslangic, bitis, gece_mi). Bayrak TANIMLI
# bir degerdir, gece_mi_oner()'in onerisi degil (TD-2; bkz. demo_veri_uret.py).
_VARDIYA_TANIMLARI: dict[str, tuple[time, time, bool]] = {
    "Gece": (time(0, 0), time(8, 0), True),
    "Gündüz": (time(8, 0), time(16, 0), False),
    "Akşam": (time(16, 0), time(0, 0), False),
}

# demo_veri_uret.py ile ayni kural katalogu; kalibre edilmis agirliklar dahil
# (bkz. PROGRESS.md, agirlik kalibrasyonu).
_KURAL_PARAMETRELERI: dict[str, dict[str, Any]] = {
    "H1": {},
    "H2": {"asgari_dinlenme_saati": 16},
    "H3": {"azami_ardisik_gece": 3},
    "H4": {"azami_ardisik_calisma_gunu": 6},
    "H5": {"azami_haftalik_saat": 45},
    "H6": {"haftalik_asgari_izin_gunu": 1},
    "H7": {},
    "H8": {},
}


@dataclass
class Kriter:
    kimlik: str
    baslik: str
    esik: str
    olculen: str
    gecti: bool
    ayrinti: list[str] = field(default_factory=list)


# --- Veri kurulumu ----------------------------------------------------------


def _temizle(oturum: Session) -> None:
    """FK bagimliligi sirasiyla; cizelge_surumu kendi kendine referans
    verdiginden (onceki_surum_id) once o bag koparilir."""
    oturum.execute(delete(KapsamaAcigi))
    oturum.execute(delete(CozumIsi))
    oturum.execute(delete(Atama))
    oturum.execute(CizelgeSurumu.__table__.update().values(onceki_surum_id=None))
    oturum.execute(delete(CizelgeSurumu))
    oturum.execute(delete(Tercih))
    oturum.execute(delete(Musaitlik))
    oturum.execute(delete(Donem))
    oturum.execute(delete(Talep))
    oturum.execute(delete(PersonelYetkinlik))
    oturum.execute(delete(Personel))
    oturum.execute(delete(GorevNoktasi))
    oturum.execute(delete(VardiyaTipi))
    oturum.execute(delete(Bina))
    oturum.execute(delete(Yetkinlik))
    oturum.execute(delete(Kural))
    oturum.flush()


def _tanimlari_kur(oturum: Session) -> None:
    vardiyalar = {}
    for ad, (baslangic, bitis, gece_mi) in _VARDIYA_TANIMLARI.items():
        vardiya = VardiyaTipi(
            ad=ad,
            baslangic_saati=baslangic,
            bitis_saati=bitis,
            sure_saat=sure_saat_hesapla(baslangic, bitis),
            gece_mi=gece_mi,
        )
        oturum.add(vardiya)
        vardiyalar[ad] = vardiya

    yetkinlikler = {
        ad: Yetkinlik(ad=ad) for ad in ("Güvenlik Görevi", "Vardiya Şefi", "Müracaat Görevlisi")
    }
    oturum.add_all(yetkinlikler.values())
    oturum.flush()

    noktalar = [
        GorevNoktasi(
            ad=tanim.ad,
            bina_id=None,
            onkosul_yetkinlik_id=yetkinlikler[tanim.onkosul_yetkinlik].yetkinlik_id,
        )
        for tanim in NOKTA_TANIMLARI
    ]
    oturum.add_all(noktalar)
    oturum.flush()

    for tanim in talep_satirlarini_olustur():
        oturum.add(
            Talep(
                nokta_id=noktalar[tanim.nokta_index].nokta_id,
                vardiya_tipi_id=vardiyalar[tanim.vardiya_tipi].vardiya_tipi_id,
                gun_tipi=tanim.gun_tipi,
                tarih=None,
                gereken_sayi=tanim.gereken_sayi,
            )
        )

    for kimlik, parametreler in _KURAL_PARAMETRELERI.items():
        oturum.add(
            Kural(kimlik=kimlik, tip=KuralTipiEnum.ZORUNLU, parametreler=parametreler, aktif=True)
        )
    for kimlik, agirlik in _esnek_agirliklar().items():
        oturum.add(
            Kural(
                kimlik=kimlik,
                tip=KuralTipiEnum.ESNEK,
                parametreler={},
                agirlik=agirlik,
                aktif=True,
            )
        )

    for yetkinlik_adlari, sayi, on_ek in _REFERANS_GRUPLARI:
        for i in range(1, sayi + 1):
            personel = Personel(
                ad_soyad=f"Referans Personel {on_ek}-{i:03d}",
                sicil_no=f"{on_ek}-{i:03d}",
                haftalik_hedef_saat=40,
                aktif_baslangic=date(2026, 1, 1),
            )
            oturum.add(personel)
            oturum.flush()
            for ad in yetkinlik_adlari:
                oturum.add(
                    PersonelYetkinlik(
                        personel_id=personel.personel_id,
                        yetkinlik_id=yetkinlikler[ad].yetkinlik_id,
                    )
                )
    oturum.flush()


def _esnek_agirliklar() -> dict[str, float]:
    """demo_veri_uret.py'deki kalibre edilmis agirliklar (PROGRESS.md, agirlik
    kalibrasyonu turu): w1, diger hedeflerin ulasabildigi agirlikli toplamdan
    buyuk olmalidir."""
    return {
        "S1": 10000,
        "S2": 40,
        "S3": 35,
        "S4": 5,
        "S5": 20,
        "S6": 10,
        "S6b": 10,
        "S7": 15,
        "S8": 15,
    }


def _donem_olustur(oturum: Session, baslangic: date, gun_sayisi: int) -> Donem:
    donem = Donem(
        baslangic_tarihi=baslangic,
        bitis_tarihi=baslangic + timedelta(days=gun_sayisi - 1),
        tercih_son_tarihi=baslangic - timedelta(days=7),
    )
    oturum.add(donem)
    oturum.flush()
    return donem


def _kurallari_yukle(oturum: Session) -> list:
    kurallar = []
    for satir in oturum.execute(select(Kural).where(Kural.aktif.is_(True))).scalars().all():
        sinif = bul(satir.kimlik)
        kurallar.append(
            sinif(parametreler=satir.parametreler or {}, agirlik=float(satir.agirlik or 0))
        )
    return kurallar


# --- Cozme --------------------------------------------------------------


@dataclass
class CozumOlcumu:
    durum: str
    atamalar: list[AtamaKaydi]
    kapsama_eksikleri: dict
    model_kurma_saniye: float
    cozum_saniye: float
    ilk_cozum_saniye: float | None
    toplam_saniye: float


def _coz(oturum: Session, donem: Donem, zaman_limiti: float) -> tuple[CozumOlcumu, Any]:
    baglam = baglam_olustur(oturum, donem)
    zaman_ekseni = zaman_ekseni_olustur(donem)
    kurallar = _kurallari_yukle(oturum)

    model_baslangic = zaman.perf_counter()
    model, x, baglam, ceza_terimleri = model_kur(baglam, zaman_ekseni, kurallar)
    model_kurma = zaman.perf_counter() - model_baslangic

    ilk_cozum: list[float] = []

    def ara_cozum(_ceza: float, gecen_sure: float) -> None:
        if not ilk_cozum:
            ilk_cozum.append(gecen_sure)

    cozum_baslangic = zaman.perf_counter()
    sonuc = CozucuAdaptoru.coz(
        model,
        x,
        zaman_limiti_saniye=zaman_limiti,
        # SDD 3.4.3: referans donanimda (dort cekirdek) arama iscisi sayisi 3.
        arama_iscisi_sayisi=ayarlar.cozucu_arama_iscisi_sayisi,
        ara_cozum_geri_cagirma=ara_cozum,
        ceza_terimleri=ceza_terimleri,
        kapsama_degiskenleri=baglam.kapsama_eksikleri,
    )
    cozum_suresi = zaman.perf_counter() - cozum_baslangic

    atamalar = [AtamaKaydi(p, g, v, n) for (p, g, v, n) in sonuc.atanan_anahtarlar]
    return (
        CozumOlcumu(
            durum=sonuc.durum,
            atamalar=atamalar,
            kapsama_eksikleri=sonuc.kapsama_eksikleri,
            model_kurma_saniye=model_kurma,
            cozum_saniye=cozum_suresi,
            ilk_cozum_saniye=ilk_cozum[0] if ilk_cozum else None,
            toplam_saniye=model_kurma + cozum_suresi,
        ),
        baglam,
    )


def _atamalari_yaz(oturum: Session, surum_id: int, olcum: CozumOlcumu, donem: Donem) -> None:
    """Cizelgeyi veritabanina yazar (K5 manuel duzenleme olcumu gercek bir
    surum uzerinde calisir). Yalniz donem ici atamalar yazilir - isitma
    penceresi atamalari surumun parcasi degildir (TD-5)."""
    for a in olcum.atamalar:
        if not (donem.baslangic_tarihi <= a.tarih <= donem.bitis_tarihi):
            continue
        oturum.add(
            Atama(
                surum_id=surum_id,
                personel_id=a.personel_id,
                tarih=a.tarih,
                vardiya_tipi_id=a.vardiya_tipi_id,
                nokta_id=a.nokta_id,
                kaynak=AtamaKaynagi.COZUCU,
            )
        )
    oturum.flush()


# --- Kriterler --------------------------------------------------------------


def _k1(olcum: CozumOlcumu) -> Kriter:
    """Charter 5 / NFR-1. 'Cozulur' = kullanilabilir (uygun) bir cizelge
    uretilir. CP-SAT bir eniyileme problemi cozdugunden zaman limiti dolana
    kadar cozumu iyilestirmeye devam eder; kriterin isaret ettigi sure, ILK
    uygun cozume ulasma suresidir (Charter bolum 6: 'limit doldugunda o ana
    kadarki en iyi cozum dondurulur'). Yine de her uc sure de raporlanir."""
    ilk = olcum.ilk_cozum_saniye
    # Modelin kurulmasi da kullanicinin bekledigi surenin parcasidir.
    ilk_toplam = None if ilk is None else olcum.model_kurma_saniye + ilk
    gecti = olcum.durum in ("optimal", "uygun") and ilk_toplam is not None and ilk_toplam < 60
    return Kriter(
        kimlik="K1",
        baslik="40 personel x 28 gun referans ornek < 60 sn",
        esik="< 60.0 sn (ilk uygun cozum, model kurma dahil)",
        olculen="cozum yok" if ilk_toplam is None else f"{ilk_toplam:.2f} sn",
        gecti=gecti,
        ayrinti=[
            f"cozucu durumu           : {olcum.durum}",
            f"model kurma             : {olcum.model_kurma_saniye:.2f} sn",
            f"ilk uygun cozum         : {'-' if ilk is None else f'{ilk:.2f} sn'} (cozucu ici)",
            f"zaman limitine kadar    : {olcum.cozum_saniye:.2f} sn",
            f"toplam (kurma + cozum)  : {olcum.toplam_saniye:.2f} sn",
            f"arama iscisi sayisi     : {ayarlar.cozucu_arama_iscisi_sayisi} (SDD 3.4.3, referans)",
        ],
    )


def _k2(olcum: CozumOlcumu, baglam: Any, kurallar: list) -> Kriter:
    """Charter 5: uretilen cizelgede zorunlu kisit ihlali bulunmaz.
    SDD 3.2.1: cozucunun gecerli saydigi bir cizelgede dogrulayicinin ihlal
    bulmasi bir YAZILIM HATASIDIR."""
    ihlaller: list[str] = []
    for kural in kurallar:
        if kural.tip is not KuralTipiEnum.ZORUNLU:
            continue
        for ihlal in kural.dogrula(olcum.atamalar, baglam):
            ihlaller.append(f"{ihlal.kural_kimlik}: {ihlal.aciklama}")
    return Kriter(
        kimlik="K2",
        baslik="Zorunlu kisit ihlali sifir",
        esik="0 ihlal (H1-H8)",
        olculen=f"{len(ihlaller)} ihlal",
        gecti=not ihlaller,
        ayrinti=ihlaller[:10] or ["H1-H8'in tamami dogrulayicidan temiz gecti"],
    )


def _k3(olcum: CozumOlcumu, baglam: Any) -> Kriter:
    """Charter 5 / NFR-9: kisi basina gece sayisi hedeften en fazla bir birim
    sapar.

    Hedef, S2'nin tanimiyla BIREBIR ayni kaynaktan gelir (SRS 1.5): donem ici
    gece talebi / |P_gece| - payda butun personel DEGIL, uygun havuzdur ve
    olcum de yalniz o havuz uzerinde yapilir. Havuz tanimi Baglam'da tek
    yerde durur; olcum betigi kendi tanimini uydurmaz."""
    gece_talebi = sum(
        gereken
        for (tarih, vardiya_tipi_id, _nokta), gereken in baglam.talep.items()
        if baglam.gece_mi(vardiya_tipi_id) and baglam.donem_icinde(tarih)
    )
    havuz = baglam.uygun_havuz(lambda anahtar: baglam.gece_mi(anahtar[1]))
    hedef = gece_talebi / len(havuz) if havuz else 0.0

    sayilar = dict.fromkeys(havuz, 0)
    for a in olcum.atamalar:
        if (
            a.personel_id in havuz
            and baglam.donem_icinde(a.tarih)
            and baglam.gece_mi(a.vardiya_tipi_id)
        ):
            sayilar[a.personel_id] += 1

    sapmalar = {p: abs(s - hedef) for p, s in sayilar.items()}
    en_buyuk = max(sapmalar.values()) if sapmalar else 0.0
    asanlar = [p for p, s in sapmalar.items() if s > 1 + 1e-9]

    havuz_disi = len(baglam.personel) - len(havuz)
    ayrinti = [
        f"donem ici gece talebi   : {gece_talebi} kisi-vardiya",
        f"uygun havuz |P_gece|    : {len(havuz)} kisi "
        f"({havuz_disi} kisi olcum disi - gece talebi olan noktada calisamiyor)",
        f"hedef (talep / P_gece)  : {hedef:.2f} gece",
        f"gozlenen aralik         : {min(sayilar.values(), default=0)} - "
        f"{max(sayilar.values(), default=0)} gece",
        f"1'den fazla sapan kisi  : {len(asanlar)}",
    ]
    ayrinti.extend(_k3_ulasilabilirlik_teshisi(baglam, hedef))
    return Kriter(
        kimlik="K3",
        baslik="Kisi basina gece sayisi hedeften en fazla 1 sapar",
        esik="azami |sapma| <= 1.0",
        olculen=f"{en_buyuk:.2f}",
        gecti=not asanlar,
        ayrinti=ayrinti,
    )


def _k3_ulasilabilirlik_teshisi(baglam: Any, hedef: float) -> list[str]:
    """K3 kaldiginda nedenini otomatik ayirt eder: cozucu yeterince
    iyilestiremedi mi, yoksa hedef bazi personel icin ULASILAMAZ mi?

    Kanit su basit sinirdan gelir: yetkinlikleri ayni olan bir S personel
    kumesinin ulasabildigi toplam gece-isaretli talep R ise, o kumedeki
    kisilerin gece sayilari toplami R'yi asamaz; dolayisiyla ortalamalari
    en fazla R/|S| olur. R/|S| < hedef-1 ise, S'deki en az bir kisinin
    hedeften birden fazla sapmasi KACINILMAZDIR - bu durumda hicbir
    cizelge kriteri saglayamaz ve ek cozucu suresi sonucu degistirmez.
    """
    # Yalniz UYGUN HAVUZDAKI personel gruplanir: havuz disindakiler zaten
    # olcume girmiyor (SRS 1.5), onlari "ulasilamaz" diye raporlamak yanlis
    # alarm olurdu.
    havuz = baglam.uygun_havuz(lambda anahtar: baglam.gece_mi(anahtar[1]))
    gruplar: dict[frozenset[int], list[int]] = {}
    for personel_id, bilgi in baglam.personel.items():
        if personel_id in havuz:
            gruplar.setdefault(bilgi.yetkinlikler, []).append(personel_id)

    satirlar: list[str] = []
    for yetkinlikler, kisiler in sorted(gruplar.items(), key=lambda oge: -len(oge[1])):
        # Bu yetkinlik kumesinin girebildigi noktalardaki gece-isaretli talep.
        ulasilabilir = sum(
            gereken
            for (tarih, vardiya_tipi_id, nokta_id), gereken in baglam.talep.items()
            if baglam.donem_icinde(tarih)
            and baglam.gece_mi(vardiya_tipi_id)
            and _nokta_uygun(baglam, nokta_id, yetkinlikler)
        )
        tavan = ulasilabilir / len(kisiler)
        imkansiz = tavan < hedef - 1 - 1e-9
        isaret = "  <-- ULASILAMAZ" if imkansiz else ""
        satirlar.append(
            f"  {len(kisiler):>2} kisilik havuz: ulasabildigi gece talebi {ulasilabilir:>4} "
            f"-> kisi basi tavan {tavan:.2f}{isaret}"
        )
    if any("ULASILAMAZ" in s for s in satirlar):
        satirlar.insert(
            0,
            "ULASILABILIRLIK TESHISI (hedef bazi havuzlar icin yapisal olarak erisilemez;"
            " ek cozucu suresi bunu degistirmez):",
        )
    else:
        satirlar.insert(0, "ULASILABILIRLIK TESHISI: her havuz hedefe erisebiliyor.")
    return satirlar


def _nokta_uygun(baglam: Any, nokta_id: int, yetkinlikler: frozenset[int]) -> bool:
    nokta = baglam.gorev_noktalari.get(nokta_id)
    if nokta is None:
        return False
    return nokta.onkosul_yetkinlik_id is None or nokta.onkosul_yetkinlik_id in yetkinlikler


def _k4(oturum: Session, celiskili_donem: Donem, olcum: CozumOlcumu) -> Kriter:
    """Charter 5: celiskili ornekte hangi GUN, hangi VARDIYADA, KAC KISI eksik
    kaldigi gosterilir. Uc bilginin de tasindigi dogrulanir (yalniz 'acik var'
    demek yeterli degil)."""
    vardiya_adlari = {
        v.vardiya_tipi_id: v.ad for v in oturum.execute(select(VardiyaTipi)).scalars().all()
    }
    nokta_adlari = {n.nokta_id: n.ad for n in oturum.execute(select(GorevNoktasi)).scalars().all()}

    eksikler = sorted(olcum.kapsama_eksikleri.items())
    toplam_eksik = sum(eksikler_sayi for _, eksikler_sayi in eksikler)
    ornekler = [
        f"{tarih.isoformat()} / {vardiya_adlari.get(v, v)} / "
        f"{nokta_adlari.get(n, n)} -> {sayi} kisi eksik"
        for (tarih, v, n), sayi in eksikler[:5]
    ]
    # Uc bilginin de dolu olmasi (gun, vardiya, nokta) ve en az bir acik.
    tam_bilgi = all(
        isinstance(tarih, date) and v in vardiya_adlari and n in nokta_adlari
        for (tarih, v, n), _ in eksikler
    )
    return Kriter(
        kimlik="K4",
        baslik="Celiskili ornekte gun/vardiya/eksik sayisi gosterilir",
        esik="en az 1 acik, her birinde gun+vardiya+nokta+sayi dolu",
        olculen=f"{len(eksikler)} acik hucre, toplam {toplam_eksik} kisi eksik",
        gecti=bool(eksikler) and tam_bilgi,
        ayrinti=ornekler or ["Celiskili senaryoda hic kapsama acigi uretilmedi"],
    )


def _k5(oturum: Session, surum_id: int, donem: Donem) -> Kriter:
    """Charter 5 / NFR-2: manuel duzenlemede kural ihlali bir saniyenin
    altinda bildirilir. En agir durum olcusun diye, DONEM GENELI kapsamli
    kurallari (S2-S4, SDD 5.5 surum 1.3) da tetikleyen gercek bir degisiklik
    dogrulanir; olcum birkac kez tekrarlanip en kotu sure raporlanir."""
    servis = DogrulamaServisi(oturum)
    mevcut = (
        oturum.execute(
            select(Atama).where(Atama.surum_id == surum_id).order_by(Atama.tarih).limit(1)
        )
        .scalars()
        .first()
    )
    if mevcut is None:
        return Kriter(
            kimlik="K5",
            baslik="Manuel duzenleme dogrulamasi < 1 sn",
            esik="< 1.000 sn",
            olculen="olculemedi",
            gecti=False,
            ayrinti=["Referans surumde atama bulunamadi"],
        )

    vardiya_tipleri = [
        v.vardiya_tipi_id for v in oturum.execute(select(VardiyaTipi)).scalars().all()
    ]
    hedef_vardiya = next(
        (v for v in vardiya_tipleri if v != mevcut.vardiya_tipi_id), mevcut.vardiya_tipi_id
    )

    sureler: list[float] = []
    for _ in range(5):
        baslangic = zaman.perf_counter()
        servis.dogrula(
            AtamaDegisikligi(
                surum_id=surum_id,
                personel_id=mevcut.personel_id,
                tarih=mevcut.tarih,
                vardiya_tipi_id=hedef_vardiya,
                nokta_id=mevcut.nokta_id,
            )
        )
        sureler.append(zaman.perf_counter() - baslangic)

    en_kotu = max(sureler)
    return Kriter(
        kimlik="K5",
        baslik="Manuel duzenleme dogrulamasi < 1 sn",
        esik="< 1.000 sn (en kotu olcum)",
        olculen=f"{en_kotu:.3f} sn",
        gecti=en_kotu < 1.0,
        ayrinti=[
            f"olcum sayisi   : {len(sureler)}",
            f"en iyi / ortanca / en kotu : {min(sureler):.3f} / "
            f"{sorted(sureler)[len(sureler) // 2]:.3f} / {en_kotu:.3f} sn",
            f"donem uzunlugu : {(donem.bitis_tarihi - donem.baslangic_tarihi).days + 1} gun",
        ],
    )


# --- Celiskili ornek --------------------------------------------------------


def _celiskili_izinleri_kur(oturum: Session, donem: Donem) -> None:
    """SRS 3.3.6'daki kirilganlik mekanizmasi: Vardiya Sefi havuzunun (9 kisi)
    bes kisisi donem boyunca izinli; kalan dort kisi, haftada 21 vardiya
    gerektiren tek noktayi H5/H6 tavanini asmadan dolduramaz -> kapatilamayan
    kapsama acigi (demo_veri_uret.py'deki 'sikisik' senaryonun ayni gerekcesi,
    burada donemin TAMAMINI kapsayacak sekilde, cunku bu kriterin olctugu sey
    on kontrolun degil cozucunun acigi RAPORLAMASI)."""
    sefler = (
        oturum.execute(
            select(Personel).where(Personel.sicil_no.like("VS-%")).order_by(Personel.sicil_no)
        )
        .scalars()
        .all()
    )
    for personel in sefler[:5]:
        oturum.add(
            Musaitlik(
                personel_id=personel.personel_id,
                baslangic_tarihi=donem.baslangic_tarihi,
                bitis_tarihi=donem.bitis_tarihi,
                dilim=MusaitlikDilimi.TAM_GUN,
                tip=MusaitlikTipi.YILLIK_IZIN,
            )
        )
    oturum.flush()


# --- Raporlama --------------------------------------------------------------


def _makine_bilgisi() -> list[str]:
    import os
    import platform

    return [
        f"makine        : {platform.platform()}",
        f"islemci       : {platform.processor() or platform.machine()}",
        f"cekirdek      : {os.cpu_count()} (referans donanim: 4 - SDD 3.4.2)",
        f"arama iscisi  : {ayarlar.cozucu_arama_iscisi_sayisi} (referans deger, SDD 3.4.3)",
        f"python        : {platform.python_version()}",
    ]


def _yazdir(kriterler: list[Kriter]) -> None:
    print("=" * 78)
    print("KABUL KRITERI OLCUMU  (Proje Tanim Dokumani bolum 5)")
    print("=" * 78)
    for satir in _makine_bilgisi():
        print(f"  {satir}")
    print()
    print(
        "  NOT: arama iscisi sayisi referans donanimin degerine sabitlendigi icin"
        "\n  cozucunun PARALELLIGI referans donanimla ayni; cekirdek BASINA hiz farki"
        "\n  kalir, dolayisiyla sureler yaklasik bir ust/alt sinir degil bir GOSTERGEDIR."
    )
    print()

    for kriter in kriterler:
        isaret = "GECTI " if kriter.gecti else "KALDI "
        print("-" * 78)
        print(f"[{isaret}] {kriter.kimlik}  {kriter.baslik}")
        print(f"          esik    : {kriter.esik}")
        print(f"          olculen : {kriter.olculen}")
        for satir in kriter.ayrinti:
            print(f"                    {satir}")
    print("-" * 78)
    gecen = sum(1 for k in kriterler if k.gecti)
    print(f"SONUC: {gecen}/{len(kriterler)} kriter gecti.")
    if gecen != len(kriterler):
        print("Gecmeyen kriterler yukarida 'KALDI' olarak isaretli; olculen degerler")
        print("esiklerle birlikte verildigi icin acigin buyuklugu dogrudan okunabilir.")


def main() -> int:
    ayristirici = argparse.ArgumentParser(description="Kabul kriteri olcumu")
    ayristirici.add_argument("--json", action="store_true", help="Makine okunur cikti")
    ayristirici.add_argument(
        "--zaman-limiti",
        type=float,
        default=60.0,
        help="Cozucuye verilecek ust sure sinir (varsayilan 60, kabul kriteriyle ayni)",
    )
    argumanlar = ayristirici.parse_args()

    oturum = OturumYerel()
    kriterler: list[Kriter] = []
    try:
        _temizle(oturum)
        _tanimlari_kur(oturum)
        oturum.commit()

        # --- Referans ornek: K1, K2, K3, K5
        referans_donem = _donem_olustur(oturum, REFERANS_BASLANGIC, REFERANS_GUN_SAYISI)
        oturum.commit()

        olcum, baglam = _coz(oturum, referans_donem, argumanlar.zaman_limiti)
        kurallar = _kurallari_yukle(oturum)

        surum = CizelgeSurumu(
            donem_id=referans_donem.donem_id,
            surum_no=1,
            durum=CizelgeSurumuDurumu.TASLAK,
        )
        oturum.add(surum)
        oturum.flush()
        _atamalari_yaz(oturum, surum.surum_id, olcum, referans_donem)
        oturum.commit()

        kriterler.append(_k1(olcum))
        kriterler.append(_k2(olcum, baglam, kurallar))
        kriterler.append(_k3(olcum, baglam))

        # --- Celiskili ornek: K4
        celiskili_donem = _donem_olustur(oturum, CELISKILI_BASLANGIC, REFERANS_GUN_SAYISI)
        _celiskili_izinleri_kur(oturum, celiskili_donem)
        oturum.commit()
        celiskili_olcum, _ = _coz(oturum, celiskili_donem, argumanlar.zaman_limiti)
        kriterler.append(_k4(oturum, celiskili_donem, celiskili_olcum))

        # --- Manuel duzenleme: K5
        kriterler.append(_k5(oturum, surum.surum_id, referans_donem))
        oturum.commit()
    finally:
        oturum.close()

    if argumanlar.json:
        print(
            json.dumps(
                {
                    "makine": _makine_bilgisi(),
                    "kriterler": [
                        {
                            "kimlik": k.kimlik,
                            "baslik": k.baslik,
                            "esik": k.esik,
                            "olculen": k.olculen,
                            "gecti": k.gecti,
                            "ayrinti": k.ayrinti,
                        }
                        for k in kriterler
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        _yazdir(kriterler)

    return 0 if all(k.gecti for k in kriterler) else 1


if __name__ == "__main__":
    raise SystemExit(main())
