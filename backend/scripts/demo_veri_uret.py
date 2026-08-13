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

--reset verilirse, once tum tanim/girdi/kural/sonuc satirlari silinip
yeniden uretilir (silinecek tablolarin listesi app/veri_temizligi.py'de).
Betik, zaten demo verisi bulunan bir veritabaninda --reset verilmeden
calistirilirsa acik bir hatayla durur (sessizce yinelenen kayit olusturmaz).

HESAPLAR. --reset, bir PERSONEL KAYDINA BAGLI hesaplari da siler ve kac
hesap silindigini yazar; bunlar `personel` satirlarini tutan yabanci
anahtarlardir ve silinmezlerse temizlik bir kisit hatasiyla duserdi.
Personel kaydina bagli OLMAYAN yonetim hesaplarina dokunulmaz - demo
verisini tazelemek sistemin giris kapisini kapatmamalidir.

Betik, VERI_TEMIZLIGINE_IZIN ortam degiskeni verilmeden calismaz
(app/veri_temizligi.py, uretim kilidi).
"""

import argparse
import sys
from dataclasses import dataclass
from datetime import date, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import OturumYerel
from app.models.girdi import (
    Musaitlik,
    MusaitlikDilimi,
    MusaitlikTipi,
    Tercih,
    TercihDurumu,
    TercihTipi,
)
from app.models.kural import Kural, KuralTipi
from app.models.sonuc import CozumIsi, Donem
from app.models.tanim import (
    GorevNoktasi,
    OzelGun,
    Personel,
    Talep,
    VardiyaTipi,
    Yetkinlik,
)
from app.repositories.sonuc import CizelgeSurumuDeposu
from app.services.cozum_servisi import CozumServisi, cozum_isini_calistir
from app.services.ornek_senaryo import (
    NOKTA_TANIMLARI,
    PERSONEL_GRUPLARI,
    talep_satirlarini_olustur,
)
from app.services.vardiya_hesaplari import sure_saat_hesapla
from app.veri_temizligi import (
    HesapKapsami,
    TemizlikSonucu,
    UretimKilidiError,
    veriyi_temizle,
)

# SRS 3.3.1'deki vardiya tipi tablosu BIREBIR: (baslangic, bitis, gece_mi).
#
# gece_mi degeri buradan gelir, gece_mi_oner()'den DEGIL. TD-2: bayrak
# "hesaplanan degil TANIMLANAN bir alandir"; oneri kurali (20:00-06:00 ile
# kesisim >= 4 saat) yalnizca kullanici YENI bir vardiya tipi tanimlarken
# alani on-doldurmak icindir ve tanimli bir degeri ezemez. Aksam vardiyasi
# (16:00-24:00) oneri esigini SINIRDA karsiladigi icin (tam 4 saat) otomatik
# uygulandiginda gece isaretleniyor ve SRS 3.3.1'in acik "Hayir" degerini
# eziyordu; sonucta uc vardiyanin ikisi gece sayilip donem ici gece talebi
# toplamin %60'ina cikiyor, S2'nin hedefi bozuluyordu (bkz. PROGRESS.md,
# Gun 14 K3 bulgusu).
_VARDIYA_TANIMLARI: dict[str, tuple[time, time, bool]] = {
    "Gece": (time(0, 0), time(8, 0), True),
    "Gündüz": (time(8, 0), time(16, 0), False),
    "Akşam": (time(16, 0), time(0, 0), False),
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
        "parametreler": {"haftalik_mutlak_tavan": 66},
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
    {
        "kimlik": "H9",
        "tip": KuralTipi.ZORUNLU,
        "parametreler": {"azami_gunluk_saat": 11},
        "agirlik": None,
    },
    {
        "kimlik": "H10",
        "tip": KuralTipi.ZORUNLU,
        "parametreler": {"fazla_calisma_esigi": 45, "yillik_fazla_kotasi": 270},
        "agirlik": None,
    },
    # Agirlik kalibrasyonu (PROGRESS.md, Ek Gorev - agirlik kalibrasyonu turu):
    # S1 agirligi, digerlerinin agirlikli toplam katkisindan belirgin buyuk olmali
    # (SRS S1, "baskin agirlik" ilkesi) - 1000 Sikisik senaryoda S1-haric agirlikli
    # toplami (2107) garantilemiyordu, 10000'e cikarildi (bkz.
    # tests/test_agirlik_kalibrasyonu.py). Ayrica S2/S3'un ham birimi VARDIYA,
    # S4'unku SAAT (bir vardiya=8 saat); w4, vardiya-esdegeri basina S4'un
    # S2/S3 kadar onemli sayilmasi icin ~w2/8 olacak sekilde dusuruldu.
    {"kimlik": "S1", "tip": KuralTipi.ESNEK, "parametreler": {}, "agirlik": 10000},
    # w1f = 2 (K4 baslangic degeri). Kesin olan `w1f << w1` bagintisidir.
    {"kimlik": "S1f", "tip": KuralTipi.ESNEK, "parametreler": {}, "agirlik": 2},
    {"kimlik": "S2", "tip": KuralTipi.ESNEK, "parametreler": {}, "agirlik": 10},
    {"kimlik": "S3", "tip": KuralTipi.ESNEK, "parametreler": {}, "agirlik": 8},
    {"kimlik": "S4", "tip": KuralTipi.ESNEK, "parametreler": {}, "agirlik": 1},
    {"kimlik": "S5", "tip": KuralTipi.ESNEK, "parametreler": {}, "agirlik": 12},
    {
        "kimlik": "S6",
        "tip": KuralTipi.ESNEK,
        "parametreler": {"desen_toleransi_saat": 2},
        "agirlik": 4,
    },
    # S6b (bina tutarliligi) bu senaryoda pasif: nokta sadelestirmesinden beri butun
    # gorev noktalari tesis geneli (bina_id NULL), bina degisimi fiziksel olarak
    # imkansiz oldugundan S6b modelde daima 0 katki verir. Kural katalogda kalir -
    # binaya bagli bir nokta tanimlanirsa kendiliginden devreye girer - ama gereksiz
    # bir amac fonksiyonu terimi olarak burada aktif tutulmaz (SRS'e not eklendi).
    {"kimlik": "S6b", "tip": KuralTipi.ESNEK, "parametreler": {}, "agirlik": 6, "aktif": False},
    {"kimlik": "S7", "tip": KuralTipi.ESNEK, "parametreler": {}, "agirlik": 6},
    {"kimlik": "S8", "tip": KuralTipi.ESNEK, "parametreler": {}, "agirlik": 15},
]

# --- Donem takvimi: BUGUNE GORE, sabit tarihlerle DEGIL --------------------
#
# Donemler eskiden 2026 Subat/Mart'a sabitlenmisti. Gosterim verisinin
# uretildigi gun o tarihleri gectiginde sistem BOS gorunuyordu: calisan
# panelinin "Vardiyalarim"i `guncel_donemi_bul(bugun)` ile calisir ve bugunu
# iceren bir donem yoksa hicbir sey gosteremez; tercih bildirimi de acik bir
# donem bulamaz. Yani demo, uretildikten birkac hafta sonra kendini
# gosteremez hale geliyordu.
#
# Butun donemler PAZARTESI baslar (SRS 3.3: haftalik planlama) ve
# birbirleriyle CAKISMAZ - `guncel_donemi_bul` cakisan donemlerde hangisini
# sececegini bilemezdi.


def _bu_haftanin_pazartesisi(bugun: date) -> date:
    return bugun - timedelta(days=bugun.weekday())


# Sabit tarihli ulusal bayramlar (ay, gun, ad). Dini bayramlar KASITLI olarak
# yok: tarihleri hicri takvime bagli oldugu icin gosterim verisine tahmini bir
# tarih yazmak, dogru sanilan yanlis bir veri uretirdi. Kullanici onlari Ozel
# Gun ekranindan kendisi ekler (FR-1.10).
_ULUSAL_BAYRAMLAR: tuple[tuple[int, int, str], ...] = (
    (1, 1, "Yılbaşı"),
    (4, 23, "Ulusal Egemenlik ve Çocuk Bayramı"),
    (5, 1, "Emek ve Dayanışma Günü"),
    (5, 19, "Atatürk'ü Anma, Gençlik ve Spor Bayramı"),
    (7, 15, "Demokrasi ve Millî Birlik Günü"),
    (8, 30, "Zafer Bayramı"),
    (10, 29, "Cumhuriyet Bayramı"),
)

_SIKISIK_DONEM_UZUNLUGU_GUN = 28


def _bayram_takvimi(bugun: date) -> list[tuple[date, str]]:
    """Icinde bulunulan ve sonraki yilin sabit tarihli bayramlari.

    Iki yil: yil sonuna yakin uretilen bir demoda "bundan sonraki ilk
    bayram" gelecek yila dusuyor ve tek yil uretmek tatilli donemi
    imkansiz kilardi.
    """
    return [
        (date(yil, ay, gun), ad)
        for yil in (bugun.year, bugun.year + 1)
        for ay, gun, ad in _ULUSAL_BAYRAMLAR
    ]


def _ilk_bayram(bugun: date, en_erken: date) -> tuple[date, str]:
    """`en_erken` tarihinden sonraki ilk ulusal bayram."""
    return next((t, ad) for t, ad in sorted(_bayram_takvimi(bugun)) if t >= en_erken)


def _mevcut_demo_verisi_var_mi(oturum: Session) -> bool:
    stmt = select(Yetkinlik).where(Yetkinlik.ad == "Güvenlik Görevi")
    return oturum.execute(stmt).scalar_one_or_none() is not None


def _her_seyi_temizle(oturum: Session) -> TemizlikSonucu:
    """Tum demo verisini siler (app/veri_temizligi.py'deki tek sozlesme).

    Silinecek tablolarin listesi ve sirasi burada DEGIL, o modulde durur;
    testler de ayni listeyi kullanir. Ikisi ayri yerde yazildiginda
    birbirinden sessizce ayrisiyordu.

    Hesap kapsami PERSONELE_BAGLI: bir personel kaydina bagli hesaplar
    (yani `DELETE FROM personel`i engelleyen satirlar) silinir, yonetim
    hesaplari KALIR. Demo verisini yeniden uretmek sisteme giris yolunu
    kapatmamalidir.
    """
    return veriyi_temizle(oturum, hesaplar=HesapKapsami.PERSONELE_BAGLI)


def _vardiya_tiplerini_olustur(oturum: Session) -> dict[str, VardiyaTipi]:
    vardiyalar: dict[str, VardiyaTipi] = {}
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
                baslangic=tanim.baslangic,
                bitis=tanim.bitis,
                gun_tipi=tanim.gun_tipi,
                tarih=None,
                gereken_sayi=tanim.gereken_sayi,
            )
        )
    oturum.flush()


def _kurallari_olustur(oturum: Session) -> None:
    oturum.add_all(Kural(**tanim) for tanim in _KURAL_TANIMLARI)
    oturum.flush()


# Sabit vardiyali personel (SDD 4.2.1 sabit_vardiya_tipi_id; Backlog
# 05.08.2026: "gercek kullanimda cogu personelin dondugu, bir bolumunun
# sabit vardiyada calistigi karma duzen yaygindir"). Alan bastan beri
# vardi ama gosterim verisinde HIC KULLANILMIYORDU; sonucta rotasyona
# dahil olmayan personel diye bir sey demoda gorunmuyordu.
#
# Sayilar kasitli olarak kucuk. Sabit vardiyali bir kisi yalnizca o
# vardiyaya atanabilir, yani esnek havuzdan cikar; Guvenlik Gorevi
# havuzunun (28 kisi) uctunu sabitlemek talebi zorlamaz, ama daha
# fazlasi sikisik senaryonun dengesini degistirirdi.
_SABIT_VARDIYALI = {
    "GG-004": "Gündüz",
    "GG-005": "Gündüz",
    "GG-006": "Gece",
}

# Pasiflestirilmis personel: aktiflik penceresi GECMISTE kapanmis bir kayit
# (SDD 4.2.1). Tanimlar ekranindaki "Pasifleri goster" filtresini ve H7'nin
# aktiflik araligi kontrolunu gorunur kilar - demoda hicbir pasif kayit
# olmadigi icin ikisi de bos calisiyordu.
_PASIF_PERSONEL = {"GG-028": date(2026, 1, 31)}


def _personeli_olustur(
    oturum: Session, yetkinlikler: dict[str, Yetkinlik], vardiyalar: dict[str, VardiyaTipi]
) -> dict[str, list[Personel]]:
    gruplar: dict[str, list[Personel]] = {}
    for grup in PERSONEL_GRUPLARI:
        kisiler: list[Personel] = []
        for i in range(1, grup.sayi + 1):
            sicil_no = f"{grup.sicil_on_eki}-{i:03d}"
            sabit_ad = _SABIT_VARDIYALI.get(sicil_no)
            personel = Personel(
                ad_soyad=f"Demo Personel {sicil_no}",
                sicil_no=sicil_no,
                haftalik_hedef_saat=40,
                aktif_baslangic=date(2026, 1, 1),
                aktif_bitis=_PASIF_PERSONEL.get(sicil_no),
                sabit_vardiya_tipi_id=(vardiyalar[sabit_ad].vardiya_tipi_id if sabit_ad else None),
            )
            personel.yetkinlikler = [yetkinlikler[ad] for ad in grup.yetkinlikler]
            oturum.add(personel)
            kisiler.append(personel)
        gruplar[grup.sicil_on_eki] = kisiler
    oturum.flush()
    return gruplar


def _ozel_gunleri_olustur(oturum: Session, bugun: date) -> None:
    """FR-1.10: resmi tatil takvimi (icinde bulunulan ve sonraki yil).

    Talep matrisi RESMI_TATIL satirlari tasidigi icin (bkz.
    ornek_senaryo.talep_satirlarini_olustur) bu gunler gercekten azaltilmis
    kadroyla cozulur; TD-3 uyarinca adalet sayaclarinda da hafta sonuyla
    ayni sayaca eklenirler.
    """
    oturum.add_all(OzelGun(tarih=tarih, ad=ad) for tarih, ad in _bayram_takvimi(bugun))
    oturum.flush()


@dataclass(frozen=True, slots=True)
class DemoDonemleri:
    gecen: Donem
    bu_hafta: Donem
    sikisik: Donem
    tatilli: Donem


def _donemleri_ve_izinleri_olustur(
    oturum: Session, personel_gruplari: dict[str, list[Personel]], bugun: date
) -> DemoDonemleri:
    """Dort donem, bugune gore ve cakismayacak bicimde.

    | Donem     | Yeri            | Ne gosterir                                  |
    |-----------|-----------------|----------------------------------------------|
    | Gecen     | onceki hafta    | Yayinlanmis gecmis cizelge; bir sonraki       |
    |           |                 | donemin isitma penceresi (TD-5)               |
    | Bu Hafta  | BUGUNU ICERIR   | Calisan panelinin "Vardiyalarim"i ve          |
    |           |                 | "siradaki vardiya"si ancak boyle calisir      |
    | Sikisik   | gelecek 4 hafta | Kapanamayan kapsama acigi (Backlog B-14)      |
    | Tatilli   | ilk bayram      | Resmi tatil cozumlemesi + acik tercih         |
    |           | haftasi         | penceresi                                     |
    """
    bu_pzt = _bu_haftanin_pazartesisi(bugun)

    def kapali_pencere(baslangic: date) -> date:
        """Tercih penceresini KESIN olarak kapali birakan son tarih.

        `tercihe_acik_donemi_bul` "tercih_son_tarihi >= bugun" olan en erken
        donemi dondurur; demoda tercih bildirimini TATILLI donem uzerinden
        gostermek istiyoruz, dolayisiyla digerlerinin penceresi bugunden once
        kapanmis olmali. Yalnizca "baslangic - 7 gun" yazmak yetmezdi: demo
        pazartesi uretildiginde o tarih bugune esit cikip pencereyi acik
        birakirdi.
        """
        return min(baslangic - timedelta(days=7), bugun - timedelta(days=1))

    gecen_bas = bu_pzt - timedelta(days=7)
    gecen = Donem(
        baslangic_tarihi=gecen_bas,
        bitis_tarihi=gecen_bas + timedelta(days=6),
        tercih_son_tarihi=kapali_pencere(gecen_bas),
    )
    bu_hafta = Donem(
        baslangic_tarihi=bu_pzt,
        bitis_tarihi=bu_pzt + timedelta(days=6),
        tercih_son_tarihi=kapali_pencere(bu_pzt),
    )
    sikisik_bas = bu_pzt + timedelta(days=7)
    sikisik = Donem(
        baslangic_tarihi=sikisik_bas,
        bitis_tarihi=sikisik_bas + timedelta(days=_SIKISIK_DONEM_UZUNLUGU_GUN - 1),
        tercih_son_tarihi=kapali_pencere(sikisik_bas),
    )

    # Tatilli donem: sikisik donem bittikten SONRAKI ilk ulusal bayrami
    # iceren hafta. Sabit bir tarih secilemez - donemler bugune gore kaydigi
    # icin hangi haftaya denk gelecegi uretim gunune bagli.
    bayram_tarihi, _bayram_adi = _ilk_bayram(bugun, sikisik.bitis_tarihi + timedelta(days=1))
    tatilli_bas = _bu_haftanin_pazartesisi(bayram_tarihi)
    tatilli = Donem(
        baslangic_tarihi=tatilli_bas,
        bitis_tarihi=tatilli_bas + timedelta(days=6),
        # TEK ACIK tercih penceresi. `tercihe_acik_donemi_bul` en erken
        # baslayan acik donemi dondurdugu icin, digerleri de acik olsaydi
        # calisan panelindeki tercih formu bu donemi hic gostermezdi -
        # oysa demonun tercih kayitlari bu doneme bagli.
        tercih_son_tarihi=tatilli_bas + timedelta(days=6),
    )
    oturum.add_all([gecen, bu_hafta, sikisik, tatilli])
    oturum.flush()

    # SRS 3.3.6: vardiya sefligi havuzunun teorik asgarisi 5 kisidir ("Izin
    # Payiyla" 9'a olceklenmesinin nedeni tam bu payi karsilamak, bkz.
    # PersonelGrubuTanimi docstring'i); 9 kisilik demo havuzunun 5'ini
    # (kalan 4 < teorik asgari 5) iki haftaligina izne cikarmak, H5/H6
    # tavaniyla sinirli azami HAFTALIK kapasiteyi (4x5=20) haftalik
    # gerekenin (21) altinda birakarak kapanamayan bir kapsama acigi
    # dogurur - izin suresi bilerek donemin (28 gun) TAMAMINDAN KISA
    # tutulur ki acik donem geneli toplamlarda seyrelsin.
    vardiya_sefleri = personel_gruplari["VS"]
    for personel in vardiya_sefleri[:5]:
        oturum.add(
            Musaitlik(
                personel_id=personel.personel_id,
                baslangic_tarihi=sikisik.baslangic_tarihi,
                bitis_tarihi=sikisik.baslangic_tarihi + timedelta(days=13),
                dilim=MusaitlikDilimi.TAM_GUN,
                tip=MusaitlikTipi.YILLIK_IZIN,
                not_="Demo: sikisik senaryo - vardiya sefligi kapsama acigi",
            )
        )

    _tatilli_donem_girdileri(oturum, personel_gruplari, tatilli)
    oturum.flush()
    return DemoDonemleri(gecen=gecen, bu_hafta=bu_hafta, sikisik=sikisik, tatilli=tatilli)


def _tatilli_donem_girdileri(
    oturum: Session, personel_gruplari: dict[str, list[Personel]], donem: Donem
) -> None:
    """Ucuncu donemin musaitlik ve tercih kayitlari.

    Cesitlilik BILEREK burada toplaniyor: "Rahat Donem" tanimi geregi izin
    kaydi tasimaz ve "Sikisik Donem"in izinleri tek bir seyi gostermek icin
    kurulmus (bkz. yukaridaki notlar); ikisine de kayit eklemek o
    senaryolarin anlatimini bozardi.

    Burada gosterilenler:
      - Musaitlik TIPLERININ tamami (yillik izin, rapor, egitim, mazeret)
      - YARIM GUN dilimler (TD-4): ogleden once / ogleden sonra
      - Tercihin uc durumu (beklemede, onaylandi, reddedildi) ve iki tipi
        (calismama, vardiya tipi tercihi), calisan notu ve ret gerekcesiyle
    """
    guvenlik = personel_gruplari["GG"]
    sefler = personel_gruplari["VS"]
    muracaat = personel_gruplari["MR"]
    gun = donem.baslangic_tarihi

    oturum.add_all(
        [
            Musaitlik(
                personel_id=guvenlik[9].personel_id,
                baslangic_tarihi=gun + timedelta(days=1),
                bitis_tarihi=gun + timedelta(days=3),
                dilim=MusaitlikDilimi.TAM_GUN,
                tip=MusaitlikTipi.RAPOR,
                not_="Demo: üç günlük istirahat raporu",
            ),
            Musaitlik(
                personel_id=guvenlik[10].personel_id,
                baslangic_tarihi=gun,
                bitis_tarihi=gun,
                dilim=MusaitlikDilimi.OGLEDEN_ONCE,
                tip=MusaitlikTipi.EGITIM,
                # TD-4: ogleden once 00:00-12:00 ile kesisen HER vardiyayi
                # engeller - gece (00-08) ve gunduz (08-16) dahil.
                not_="Demo: yarım gün eğitim (öğleden önce)",
            ),
            Musaitlik(
                personel_id=guvenlik[11].personel_id,
                baslangic_tarihi=gun + timedelta(days=2),
                bitis_tarihi=gun + timedelta(days=2),
                dilim=MusaitlikDilimi.OGLEDEN_SONRA,
                tip=MusaitlikTipi.MAZERET,
                not_="Demo: yarım gün mazeret izni (öğleden sonra)",
            ),
            Musaitlik(
                personel_id=sefler[8].personel_id,
                baslangic_tarihi=gun + timedelta(days=4),
                bitis_tarihi=gun + timedelta(days=5),
                dilim=MusaitlikDilimi.TAM_GUN,
                tip=MusaitlikTipi.YILLIK_IZIN,
                not_="Demo: iki günlük yıllık izin",
            ),
        ]
    )

    # Tercihler (FR-3.x, S5, TD-12). Yalnizca ONAYLANMIS olanlar modele
    # girer (FR-3.5); beklemede ve reddedilmis olanlar Tercihler ekraninda
    # karara baglanacak/baglanmis kayit olarak gorunur.
    oturum.add_all(
        [
            Tercih(
                personel_id=guvenlik[0].personel_id,
                donem_id=donem.donem_id,
                tarih=gun + timedelta(days=3),  # 23 Nisan, resmi tatil
                tip=TercihTipi.CALISMAMA,
                durum=TercihDurumu.ONAYLANDI,
                calisan_notu="Bayramda ailemle olmak istiyorum",
            ),
            Tercih(
                personel_id=guvenlik[1].personel_id,
                donem_id=donem.donem_id,
                tarih=gun + timedelta(days=1),
                tip=TercihTipi.CALISMAMA,
                durum=TercihDurumu.BEKLEMEDE,
                calisan_notu="Sağlık kontrolü randevum var",
            ),
            Tercih(
                personel_id=guvenlik[2].personel_id,
                donem_id=donem.donem_id,
                tarih=gun + timedelta(days=3),
                tip=TercihTipi.CALISMAMA,
                durum=TercihDurumu.REDDEDILDI,
                calisan_notu="Bayram tatili",
                ret_gerekcesi="Aynı gün için üç talep geldi; kıdem sırası gözetildi",
            ),
            Tercih(
                personel_id=muracaat[0].personel_id,
                donem_id=donem.donem_id,
                tarih=gun + timedelta(days=2),
                tip=TercihTipi.CALISMAMA,
                durum=TercihDurumu.BEKLEMEDE,
                calisan_notu=None,
            ),
        ]
    )


def _donemi_coz(oturum: Session, donem: Donem, *, zaman_limiti: int, etiket: str) -> int | None:
    """Donemi GERCEK cozucuyle cozer ve surum kimligini dondurur.

    Neden gercek cozucu: elle uydurulmus bir cizelge kural ihlali tasiyabilir
    ve Cizelge ekraninda ihlal isaretleriyle acilirdi; ayrica ceza dokumu,
    kapsama acigi ve cozum isi kaydi gibi ekranlarin okudugu her sey ancak
    cozucuden gercek degerlerle dolar. Kisa zaman limiti yeterli - gosterim
    verisi eniyilenmis olmak zorunda degil, GECERLI olmak zorunda.
    """
    servis = CozumServisi(oturum)
    is_kaydi = servis.baslat(donem.donem_id, zaman_limiti_saniye=zaman_limiti)
    if is_kaydi is None:
        return None
    print(f"  {etiket}: cozuluyor (limit {zaman_limiti} sn)...", flush=True)
    cozum_isini_calistir(oturum, is_kaydi.is_id)
    yenilenen = oturum.get(CozumIsi, is_kaydi.is_id)
    durum = yenilenen.durum.value if yenilenen else "?"
    print(f"  {etiket}: {durum}", flush=True)
    return is_kaydi.surum_id


def _cizelgeleri_uret(oturum: Session, donemler: DemoDonemleri) -> None:
    """Donemleri cozer ve sonuclari YAYIN DURUMLARINA dagitir.

    Eskiden uretec yalnizca tanim ve girdi yaziyordu; hicbir cizelge sürümü
    yoktu. Sonucta Cizelge, Analiz ve Surumler ekranlari bos aciliyor,
    calisan paneli de "yayinlanmis surum yok" diyordu - yani demo, urunun
    asil gosterdigi seyi gosteremiyordu.

    Dagilim bilincli; TD-8'deki dort durumun tamami ekranda gorunur:
      Gecen    -> yayinlandi        (gecmis cizelge; bir sonrakinin isitma
                                     penceresi, TD-5)
      Bu Hafta -> arsiv + yayinlandi (iki surum: FR-9.4'un "degisen gunler"
                                     isareti ancak bir arsiv tabani varsa
                                     hesaplanabilir)
      Sikisik  -> cozuldu           (kapsama acikli; yayinlanmamis)
      Tatilli  -> surum YOK         (henuz cozulmemis donem; tercih penceresi
                                     acik oldugu icin once tercih toplanir)
    """
    surum_depo = CizelgeSurumuDeposu(oturum)

    gecen_surum = _donemi_coz(oturum, donemler.gecen, zaman_limiti=15, etiket="Gecen Donem")
    if gecen_surum is not None:
        surum_depo.yayinla(gecen_surum)
        oturum.commit()

    ilk = _donemi_coz(oturum, donemler.bu_hafta, zaman_limiti=15, etiket="Bu Hafta (1. surum)")
    if ilk is not None:
        surum_depo.yayinla(ilk)
        oturum.commit()
        # Ikinci surum: yeniden cozum (SDD 5.6). Yayinlandiginda birincisi
        # arsive duser ve calisan panelindeki karsilastirma tabani olusur.
        ikinci_is = CozumServisi(oturum).baslat(onceki_surum_id=ilk, zaman_limiti_saniye=15)
        if ikinci_is is not None:
            print("  Bu Hafta (2. surum): yeniden cozuluyor...", flush=True)
            cozum_isini_calistir(oturum, ikinci_is.is_id)
            surum_depo.yayinla(ikinci_is.surum_id)
            oturum.commit()
            print("  Bu Hafta (2. surum): yayinlandi, 1. surum arsivde", flush=True)

    _donemi_coz(oturum, donemler.sikisik, zaman_limiti=30, etiket="Sikisik Donem")
    oturum.commit()


def uret(*, sifirla: bool, coz: bool = True) -> None:
    oturum = OturumYerel()
    temizlik: TemizlikSonucu | None = None
    bugun = date.today()
    try:
        if not sifirla and _mevcut_demo_verisi_var_mi(oturum):
            print(
                "Demo verisi zaten mevcut. Yeniden uretmek icin --reset kullanin.",
                file=sys.stderr,
            )
            sys.exit(1)
        if sifirla:
            # KOSULSUZ temizlik. Eskiden yalnizca _mevcut_demo_verisi_var_mi()
            # dogruysa temizleniyordu; oysa _her_seyi_temizle zaten o tablolarin
            # TUMUNU siler. Sonuc: demo disi artiklar (test fikstürleri, kabul
            # olcumu verisi) bulunan bir veritabaninda --reset sessizce hicbir
            # sey silmiyor ve uretec artiklarin USTUNE ekliyordu; ortaya iki
            # veri kumesinin karistigi bir durum cikiyordu.
            temizlik = _her_seyi_temizle(oturum)

        vardiyalar = _vardiya_tiplerini_olustur(oturum)
        yetkinlikler = _yetkinlikleri_olustur(oturum)
        noktalar = _noktalari_olustur(oturum, yetkinlikler)
        _talebi_olustur(oturum, noktalar, vardiyalar)
        _kurallari_olustur(oturum)
        _ozel_gunleri_olustur(oturum, bugun)
        personel_gruplari = _personeli_olustur(oturum, yetkinlikler, vardiyalar)
        donemler = _donemleri_ve_izinleri_olustur(oturum, personel_gruplari, bugun)

        oturum.commit()

        if coz:
            print("Cizelgeler uretiliyor (gercek cozucu):", flush=True)
            _cizelgeleri_uret(oturum, donemler)
    except Exception:
        oturum.rollback()
        raise
    finally:
        oturum.close()

    toplam_personel = sum(grup.sayi for grup in PERSONEL_GRUPLARI)
    print(
        f"Demo verisi uretildi: {toplam_personel} personel "
        f"({len(_SABIT_VARDIYALI)} sabit vardiyali, {len(_PASIF_PERSONEL)} pasif), "
        f"{len(NOKTA_TANIMLARI)} gorev noktasi, {len(_KURAL_TANIMLARI)} kural, "
        f"{len(_bayram_takvimi(bugun))} resmi tatil, 4 donem "
        f"(Gecen, Bu Hafta, Sikisik, Tatilli)."
    )
    # Silinen hesap SESSIZ kalmamali: silinen sey bir kullanicinin sisteme
    # girisidir, gecmis dondugunde geri gelmez.
    if temizlik is not None and temizlik.silinen_hesap:
        print(
            f"UYARI: personel kaydina bagli {temizlik.silinen_hesap} hesap "
            f"({temizlik.silinen_oturum} acik oturum) silindi; bu personel icin "
            f"hesaplar Kullanicilar ekranindan yeniden acilmalidir. "
            f"Personel kaydina bagli OLMAYAN yonetim hesaplarina dokunulmadi.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    ayristirici = argparse.ArgumentParser(description=__doc__)
    ayristirici.add_argument(
        "--reset", action="store_true", help="Mevcut demo verisini silip yeniden uretir."
    )
    ayristirici.add_argument(
        "--cozme",
        action="store_true",
        help=(
            "Cizelgeleri URETME - yalnizca tanim ve girdi verisi yazilir. "
            "Cozum birkac on saniye surer; yalnizca tanim ekranlarina "
            "bakilacaksa bu bayrakla atlanabilir."
        ),
    )
    argumanlar = ayristirici.parse_args()
    try:
        uret(sifirla=argumanlar.reset, coz=not argumanlar.cozme)
    except UretimKilidiError as hata:
        # Yigin izi YAZILMAZ. Bu bir program hatasi degil, kasitli bir ret;
        # mesajin kendisi ne yapilacagini soyluyor (NFR-5: hata mesajlari
        # operasyon diliyle). Yigin izi burada yalnizca gurultudur.
        print(f"REDDEDILDI: {hata}", file=sys.stderr)
        sys.exit(2)
