#!/usr/bin/env python3
"""Gosterim amacli ornek veri seti uretir (FR-1.14; UYGULAMA_PLANI.md Sprint 1 Gun 5).

SRS 3.3'teki guvenlik personeli senaryosunu tek bir ~44 kisilik personel
havuzu, SRS 3.3.4'teki talep matrisi ve 16+1 kuralla (H1-H8, S1-S8, S6b)
veritabanina yazar. Ayni havuz ve talep uzerinde iki donem uretilir:

  - "Rahat Donem": izin kaydi yok, kadro talebi rahatlikla karsiliyor.
    Bir hafta uzunlugunda (SRS 3.3'teki yeni varsayilan donem uzunlugu).
  - "Sikisik Donem": dort hafta (28 gun) uzunlugunda - bu uzunluk kasitli,
    bkz. _SIKISIK_DONEM_UZUNLUGU_GUN sabiti. Vardiya Sefligi havuzunun
    (9 kisi) 5'i, donemin YALNIZCA ilk iki haftasi icin yillik izne
    cikariliyor; SRS 3.3.6'nin anlattigi uzere 5 kisilik teorik asgari
    havuzun altina inildiginde (9-5=4 < 5) kapanamayan bir kapsama acigi
    doguruyor (haftalik gereken 21 vardiyaya karsi kalan 4 kisinin H5/H6
    tavaniyla sinirli azami HAFTALIK kapasitesi 20'de kaliyor) - ama bu
    acik donem genelinin (4 hafta) yalnizca yarisinda oldugu icin donem
    toplamlarina bakan on_kontrol'u (SDD 5.2) atlatir, yalnizca cozucunun
    kapsama_acigi'yla ortaya cikar (Sprint 2 Gun 7/8, Backlog B-14).

Kullanim:
    python scripts/demo_veri_uret.py [--reset]

--reset verilirse, once (yalnizca) bu betigin urettigi turden veriler
(tum tanim/girdi/kural/donem satirlari) silinip yeniden uretilir. Betik,
zaten demo verisi bulunan bir veritabaninda --reset verilmeden calistirilirsa
acik bir hatayla durur (sessizce yinelenen kayit olusturmaz).
"""

import argparse
import sys
from datetime import date, time, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db import OturumYerel
from app.models.girdi import Musaitlik, MusaitlikDilimi, MusaitlikTipi, Tercih
from app.models.kural import Kural, KuralTipi
from app.models.sonuc import Atama, CizelgeSurumu, CozumIsi, Donem, KapsamaAcigi
from app.models.tanim import (
    Bina,
    GorevNoktasi,
    Personel,
    PersonelYetkinlik,
    Talep,
    VardiyaTipi,
    Yetkinlik,
)
from app.services.ornek_senaryo import (
    NOKTA_TANIMLARI,
    PERSONEL_GRUPLARI,
    talep_satirlarini_olustur,
)
from app.services.vardiya_hesaplari import gece_mi_oner, sure_saat_hesapla

_VARDIYA_SAATLERI = {
    "Gece": (time(0, 0), time(8, 0)),
    "Gündüz": (time(8, 0), time(16, 0)),
    "Akşam": (time(16, 0), time(0, 0)),
}

_KURAL_TANIMLARI: list[dict] = [
    {"kimlik": "H1", "tip": KuralTipi.ZORUNLU, "parametreler": {}, "agirlik": None},
    {
        "kimlik": "H2",
        "tip": KuralTipi.ZORUNLU,
        "parametreler": {"asgari_dinlenme_saati": 16},
        "agirlik": None,
    },
    {
        "kimlik": "H3",
        "tip": KuralTipi.ZORUNLU,
        "parametreler": {"azami_ardisik_gece": 3},
        "agirlik": None,
    },
    {
        "kimlik": "H4",
        "tip": KuralTipi.ZORUNLU,
        "parametreler": {"azami_ardisik_calisma_gunu": 6},
        "agirlik": None,
    },
    {
        "kimlik": "H5",
        "tip": KuralTipi.ZORUNLU,
        "parametreler": {"azami_haftalik_saat": 45},
        "agirlik": None,
    },
    {
        "kimlik": "H6",
        "tip": KuralTipi.ZORUNLU,
        "parametreler": {"haftalik_asgari_izin_gunu": 1},
        "agirlik": None,
    },
    {"kimlik": "H7", "tip": KuralTipi.ZORUNLU, "parametreler": {}, "agirlik": None},
    {"kimlik": "H8", "tip": KuralTipi.ZORUNLU, "parametreler": {}, "agirlik": None},
    # Agirlik kalibrasyonu (PROGRESS.md, Ek Gorev - agirlik kalibrasyonu turu):
    # S1 agirligi, digerlerinin agirlikli toplam katkisindan belirgin buyuk olmali
    # (SRS S1, "baskin agirlik" ilkesi) - 1000 Sikisik senaryoda S1-haric agirlikli
    # toplami (2107) garantilemiyordu, 10000'e cikarildi (bkz.
    # tests/test_agirlik_kalibrasyonu.py). Ayrica S2/S3'un ham birimi VARDIYA,
    # S4'unku SAAT (bir vardiya=8 saat); w4, vardiya-esdegeri basina S4'un
    # S2/S3 kadar onemli sayilmasi icin ~w2/8 olacak sekilde dusuruldu.
    {"kimlik": "S1", "tip": KuralTipi.ESNEK, "parametreler": {}, "agirlik": 10000},
    {"kimlik": "S2", "tip": KuralTipi.ESNEK, "parametreler": {}, "agirlik": 10},
    {"kimlik": "S3", "tip": KuralTipi.ESNEK, "parametreler": {}, "agirlik": 8},
    {"kimlik": "S4", "tip": KuralTipi.ESNEK, "parametreler": {}, "agirlik": 1},
    {"kimlik": "S5", "tip": KuralTipi.ESNEK, "parametreler": {}, "agirlik": 12},
    {"kimlik": "S6", "tip": KuralTipi.ESNEK, "parametreler": {}, "agirlik": 4},
    # S6b (bina tutarliligi) bu senaryoda pasif: nokta sadelestirmesinden beri butun
    # gorev noktalari tesis geneli (bina_id NULL), bina degisimi fiziksel olarak
    # imkansiz oldugundan S6b modelde daima 0 katki verir. Kural katalogda kalir -
    # binaya bagli bir nokta tanimlanirsa kendiliginden devreye girer - ama gereksiz
    # bir amac fonksiyonu terimi olarak burada aktif tutulmaz (SRS'e not eklendi).
    {"kimlik": "S6b", "tip": KuralTipi.ESNEK, "parametreler": {}, "agirlik": 6, "aktif": False},
    {"kimlik": "S7", "tip": KuralTipi.ESNEK, "parametreler": {}, "agirlik": 6},
    {"kimlik": "S8", "tip": KuralTipi.ESNEK, "parametreler": {}, "agirlik": 15},
]

_RAHAT_BASLANGIC = date(2026, 2, 2)  # Pazartesi
_SIKISIK_BASLANGIC = date(2026, 3, 2)  # Pazartesi
# SRS 3.3: planlama donemi varsayilan olarak bir haftadir (kullanici
# istedigi uzunluga cikarabilir - bu bir kisit degil, YENI donem
# olusturmanin baslangic degeri). Rahat senaryo bu varsayilanla uyumlu
# basit bir ornek oldugu icin 7 gune indirildi.
_RAHAT_DONEM_UZUNLUGU_GUN = 7
# Sikisik senaryonun 28 gun (dort hafta) olmasi KASITLIDIR, varsayilanla
# tutarsizlik degildir: senaryonun tasidigi bilgi, acigin donem icinde
# SEYRELMESI - yani on_kontrol'un (SDD 5.2) donem geneli toplamlara bakarak
# bu haftalik/yerel darbogazi KACIRMASI, yalnizca cozucunun kapsama_acigi'yla
# ortaya cikmasidir (bkz. Sprint 2 Gun 7/8, PROGRESS.md, Backlog B-14).
# Donem 7 gune inseydi izin donemin tamamini kaplar, on_kontrol acigi
# dogrudan yakalayip isi cozucu hic calismadan basarisiz bitirirdi -
# senaryo varlik nedenini kaybederdi. Sikisik senaryo bu yuzden ayri ve
# daha uzun bir sabit kullanir.
_SIKISIK_DONEM_UZUNLUGU_GUN = 28


def _mevcut_demo_verisi_var_mi(oturum: Session) -> bool:
    stmt = select(Yetkinlik).where(Yetkinlik.ad == "Güvenlik Görevi")
    return oturum.execute(stmt).scalar_one_or_none() is not None


def _her_seyi_temizle(oturum: Session) -> None:
    """Sonuc -> girdi -> tanim sirasiyla (FK bagimliligi) tum demo verisini siler."""
    for model in (
        KapsamaAcigi,
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
        Kural,
    ):
        oturum.execute(delete(model))
    oturum.flush()


def _vardiya_tiplerini_olustur(oturum: Session) -> dict[str, VardiyaTipi]:
    vardiyalar: dict[str, VardiyaTipi] = {}
    for ad, (baslangic, bitis) in _VARDIYA_SAATLERI.items():
        vardiya = VardiyaTipi(
            ad=ad,
            baslangic_saati=baslangic,
            bitis_saati=bitis,
            sure_saat=sure_saat_hesapla(baslangic, bitis),
            gece_mi=gece_mi_oner(baslangic, bitis),
        )
        oturum.add(vardiya)
        vardiyalar[ad] = vardiya
    oturum.flush()
    return vardiyalar


def _yetkinlikleri_olustur(oturum: Session) -> dict[str, Yetkinlik]:
    yetkinlikler = {
        ad: Yetkinlik(ad=ad) for ad in ("Güvenlik Görevi", "Vardiya Şefi", "Müracaat Görevlisi")
    }
    oturum.add_all(yetkinlikler.values())
    oturum.flush()
    return yetkinlikler


def _noktalari_olustur(oturum: Session, yetkinlikler: dict[str, Yetkinlik]) -> list[GorevNoktasi]:
    """SRS 3.3.3 (surum 1.1): bina ayrimi kalkti, tum noktalar tesis geneli
    (bina_id=None) - bu senaryoda Bina tablosuna hic satir yazilmaz."""
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
    return noktalar


def _talebi_olustur(
    oturum: Session, noktalar: list[GorevNoktasi], vardiyalar: dict[str, VardiyaTipi]
) -> None:
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
    oturum.flush()


def _kurallari_olustur(oturum: Session) -> None:
    oturum.add_all(Kural(**tanim) for tanim in _KURAL_TANIMLARI)
    oturum.flush()


def _personeli_olustur(
    oturum: Session, yetkinlikler: dict[str, Yetkinlik]
) -> dict[str, list[Personel]]:
    gruplar: dict[str, list[Personel]] = {}
    for grup in PERSONEL_GRUPLARI:
        kisiler: list[Personel] = []
        for i in range(1, grup.sayi + 1):
            sicil_no = f"{grup.sicil_on_eki}-{i:03d}"
            personel = Personel(
                ad_soyad=f"Demo Personel {sicil_no}",
                sicil_no=sicil_no,
                haftalik_hedef_saat=40,
                aktif_baslangic=date(2026, 1, 1),
            )
            personel.yetkinlikler = [yetkinlikler[ad] for ad in grup.yetkinlikler]
            oturum.add(personel)
            kisiler.append(personel)
        gruplar[grup.sicil_on_eki] = kisiler
    oturum.flush()
    return gruplar


def _donemleri_ve_izinleri_olustur(
    oturum: Session, personel_gruplari: dict[str, list[Personel]]
) -> None:
    rahat = Donem(
        baslangic_tarihi=_RAHAT_BASLANGIC,
        bitis_tarihi=_RAHAT_BASLANGIC + timedelta(days=_RAHAT_DONEM_UZUNLUGU_GUN - 1),
        tercih_son_tarihi=_RAHAT_BASLANGIC - timedelta(days=7),
    )
    sikisik = Donem(
        baslangic_tarihi=_SIKISIK_BASLANGIC,
        bitis_tarihi=_SIKISIK_BASLANGIC + timedelta(days=_SIKISIK_DONEM_UZUNLUGU_GUN - 1),
        tercih_son_tarihi=_SIKISIK_BASLANGIC - timedelta(days=7),
    )
    oturum.add_all([rahat, sikisik])
    oturum.flush()

    # SRS 3.3.6: vardiya sefligi havuzunun teorik asgarisi 5 kisidir ("Izin
    # Payiyla" 9'a olceklenmesinin nedeni tam bu payi karsilamak, bkz.
    # PersonelGrubuTanimi docstring'i); 9 kisilik demo havuzunun 5'ini
    # (kalan 4 < teorik asgari 5) iki haftaligina izne cikarmak, H5/H6
    # tavaniyla sinirli azami HAFTALIK kapasiteyi (4x5=20) haftalik
    # gerekenin (21) altinda birakarak kapanamayan bir kapsama acigi
    # dogurur - izin suresi bilerek donemin (28 gun) TAMAMINDAN KISA
    # tutulur ki acik donem geneli toplamlarda seyrelsin (bkz. yukaridaki
    # _SIKISIK_DONEM_UZUNLUGU_GUN notu).
    vardiya_sefleri = personel_gruplari["VS"]
    izinli_sure = timedelta(days=13)  # iki hafta
    for personel in vardiya_sefleri[:5]:
        oturum.add(
            Musaitlik(
                personel_id=personel.personel_id,
                baslangic_tarihi=_SIKISIK_BASLANGIC,
                bitis_tarihi=_SIKISIK_BASLANGIC + izinli_sure,
                dilim=MusaitlikDilimi.TAM_GUN,
                tip=MusaitlikTipi.YILLIK_IZIN,
                not_="Demo: sikisik senaryo - vardiya sefligi kapsama acigi",
            )
        )
    oturum.flush()


def uret(*, sifirla: bool) -> None:
    oturum = OturumYerel()
    try:
        if _mevcut_demo_verisi_var_mi(oturum):
            if not sifirla:
                print(
                    "Demo verisi zaten mevcut. Yeniden uretmek icin --reset kullanin.",
                    file=sys.stderr,
                )
                sys.exit(1)
            _her_seyi_temizle(oturum)

        vardiyalar = _vardiya_tiplerini_olustur(oturum)
        yetkinlikler = _yetkinlikleri_olustur(oturum)
        noktalar = _noktalari_olustur(oturum, yetkinlikler)
        _talebi_olustur(oturum, noktalar, vardiyalar)
        _kurallari_olustur(oturum)
        personel_gruplari = _personeli_olustur(oturum, yetkinlikler)
        _donemleri_ve_izinleri_olustur(oturum, personel_gruplari)

        oturum.commit()
    except Exception:
        oturum.rollback()
        raise
    finally:
        oturum.close()

    toplam_personel = sum(grup.sayi for grup in PERSONEL_GRUPLARI)
    print(
        f"Demo verisi uretildi: {toplam_personel} personel, "
        f"{len(NOKTA_TANIMLARI)} gorev noktasi, {len(_KURAL_TANIMLARI)} kural, 2 donem."
    )


if __name__ == "__main__":
    ayristirici = argparse.ArgumentParser(description=__doc__)
    ayristirici.add_argument(
        "--reset", action="store_true", help="Mevcut demo verisini silip yeniden uretir."
    )
    argumanlar = ayristirici.parse_args()
    uret(sifirla=argumanlar.reset)
