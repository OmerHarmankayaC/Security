#!/usr/bin/env python3
"""Gosterim amacli ornek veri seti uretir (FR-1.14; UYGULAMA_PLANI.md Sprint 1 Gun 5).

SRS 3.3'teki guvenlik personeli senaryosunu 30 kisilik bir personel havuzu
(7 vardiya sefi + 23 guvenlik gorevlisi), SRS 3.3.4'teki talep matrisi ve
kural kataloguyla veritabanina yazar.

DONEMLER GECMISE BAKAR. Bugunu iceren hafta ve onceki dordu, toplam BES
HAFTALIK donem uretilir; hepsi gercek cozucuyle cozulur ve yayin
durumlarina dagitilir. Boylece urun ilk acildiginda yasanmis bir takvim
gosterir: adalet sayaclari (S2/S3/S4) uzerinde calisacak bir birikim,
calisan panelinde gecmis vardiyalar ve karsilastirilabilir surumler bulunur.

Haftalarin ikisi senaryo tasir:

  - DAR HAFTA (uc hafta once): Vardiya Sefligi havuzunun yedisinden besi
    yillik izinde. Nokta kesintisiz doludur ve haftada 168 kisi-saat ister;
    kalan iki kisi gunluk tavan (11 saat) ve haftalik izin gunu (H6)
    altinda en cok 132 kisi-saat verebilir. Eksik olan SAAT degil KISIDIR
    ve hicbir blok uzunlugu bunu kapatamaz (SRS TD-13) - kapanamayan
    kapsama acigi boyle dogar. Bu hafta COZULUR ama yayinlanmaz.
  - RAHAT HAFTA (iki hafta once): hic izin kaydi yok, kadro talebi
    rahatlikla karsiliyor. Agirlik kalibrasyonunun tabani (bkz.
    tests/test_agirlik_kalibrasyonu.py).

Resmi tatiller `app/services/tatil_takvimi.py` uzerinden kutuphaneden gelir
(dini bayramlar dahil) ve talep matrisinin RESMI_TATIL satirlarini tetikler.

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
from decimal import Decimal

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
    Yetkinlik,
)
from app.repositories.sonuc import CizelgeSurumuDeposu
from app.services.cozum_servisi import CozumServisi, cozum_isini_calistir
from app.services.ornek_senaryo import (
    GUVENLIK_GOREVI,
    NOKTA_TANIMLARI,
    PERSONEL_GRUPLARI,
    VARDIYA_SEFI,
    talep_satirlarini_olustur,
)
from app.services.tatil_takvimi import resmi_tatiller
from app.veri_temizligi import (
    HesapKapsami,
    TemizlikSonucu,
    UretimKilidiError,
    veriyi_temizle,
)

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


# Uretilen haftalik donem sayisi: BUGUNU iceren hafta + onceki dordu.
#
# Gosterim verisi bir GECMIS tasimali. Onceki surumde donemler ileriye
# bakiyordu (dort haftalik sikisik donem, sonraki bayram haftasi) ve
# ekranlar cogunlukla henuz yasanmamis bir takvimi gosteriyordu; oysa
# yoneticinin urunle ilk karsilastigi soru "gecen haftalar nasil gecti"
# oluyor. Bes hafta, adalet sayaclarinin (S2/S3/S4) ve devir bakiyesinin
# uzerinde calisacagi bir birikim de uretir.
_HAFTA_SAYISI = 5

# Cozum zaman limiti (saniye). Gosterim verisi eniyilenmis olmak zorunda
# degil ama INANDIRICI olmali: on bes saniyelik bir limit otuz kisilik bir
# haftada cozucuyu adalet hedeflerine sira gelmeden kesiyor ve ekranda
# gereginden dengesiz bir cizelge kaliyordu (T-08 ile ayni mekanizma).
_COZUM_ZAMAN_LIMITI_SANIYE = 60


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


def _yetkinlikleri_olustur(oturum: Session) -> dict[str, Yetkinlik]:
    yetkinlikler = {ad: Yetkinlik(ad=ad) for ad in (GUVENLIK_GOREVI, VARDIYA_SEFI)}
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


def _talebi_olustur(oturum: Session, noktalar: list[GorevNoktasi]) -> None:
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


# Pasiflestirilmis personel: aktiflik penceresi GECMISTE kapanmis bir kayit
# (SDD 4.2.1). Tanimlar ekranindaki "Pasifleri goster" filtresini ve H7'nin
# aktiflik araligi kontrolunu gorunur kilar - demoda hicbir pasif kayit
# olmadigi icin ikisi de bos calisiyordu.
#
# Tarih BUGUNE GORE hesaplanir, sabit degil: sabit bir 2026 tarihi, demo
# 2027'de uretildiginde "gecmiste kapanmis" olmaktan cikmaz ama en eski
# donemin de gerisinde kalir ve kaydin gosterdigi sey (yakin gecmiste ayrilmis
# personel) anlamini yitirirdi. Uretilen en eski haftadan once kapanir.
_PASIF_PERSONEL_SICIL = "GG-017"
_PASIF_KAPANIS_GUN_ONCE = 7 * _HAFTA_SAYISI + 3

# DEVIR BAKIYESI (H10, FR-1.1). Kota senaryosunun tamami bu uc satirda:
# yillik kota 270 saat, esik 45 saat/hafta.
#
#   - GG-001: 265 saat -> kalan 5. Bir haftalik fazla calismaya bile
#     yetmez; on kontrol "kotasi dolmus" uyarisi verir ve H10 bu kisiyi
#     esigin UZERINE cikaramaz. KURAL COZULEMEZLIK URETMEZ: kisi esige
#     kadar calismaya devam eder (SRS 4.2 H10).
#   - GG-002: 240 saat -> kalan 30. Bir haftalik fazla calismayi (azami 21
#     saat) kaldirir ama ikisini kaldirmaz; kotanin BAGLAYICI oldugu ama
#     tuketilmedigi ara durum.
#   - VS-001: 120 saat -> kalan 150. Kirilgan havuzda kota bol; sikisik
#     senaryonun acigi kotadan DEGIL kisi sayisindan dogar, ikisi
#     karismasin diye.
#
# Kota yili demo uretildigi yildir; sabit yazilsaydi yil donunce butun
# bakiyeler "gecen yilin" gorunurdu.
_DEVIR_BAKIYELERI: dict[str, float] = {
    "GG-001": 265.0,
    "GG-002": 240.0,
    "VS-001": 120.0,
}


# GERCEKCI ADLAR (Tur 4). Onceki "Demo Personel GG-001" bicimi ekranlarda
# okunmuyordu: cizelge izgarasinda, analiz tablosunda ve calisan panelinde
# satirlar birbirinden ayirt edilemiyordu. Adlar kurgudur; sicil numaralari
# havuzu gosterdigi icin (VS/MR/GG) korundu.
#
# Liste havuz basina AYRI tutulur ki bir havuzun buyuklugu degistiginde
# digerlerinin adlari kaymasin - kaysaydi iki demo uretimi arasinda ayni
# sicil farkli bir ada duserdi ve ekran goruntuleri karsilastirilamazdi.
_ADLAR: dict[str, tuple[str, ...]] = {
    "VS": (
        "Mehmet Aydın",
        "Hatice Şahin",
        "Ali Rıza Koç",
        "Zeynep Arslan",
        "Mustafa Yıldırım",
        "Emine Doğan",
        "Hüseyin Çetin",
    ),
    "GG": (
        "Fatma Kaya",
        "Ayşe Demir",
        "Elif Yılmaz",
        "Merve Öztürk",
        "Sevgi Aksoy",
        "Nurten Polat",
        "Ahmet Yılmaz",
        "Osman Kurt",
        "İbrahim Yalçın",
        "Ramazan Erdoğan",
        "Süleyman Aslan",
        "Kadir Bulut",
        "Murat Şimşek",
        "Yusuf Kılıç",
        "Halil Özdemir",
        "Bekir Sarı",
        "Cemal Turan",
        "Serkan Avcı",
        "Volkan Kaplan",
        "Erhan Güneş",
        "Tolga Ayhan",
        "Kemal Uçar",
        "Sinan Ekinci",
    ),
}


def _ad_soyad(sicil_on_eki: str, sira: int) -> str:
    """Sicil sirasina karsilik gelen ad; liste yetmezse sicile duser.

    Duserek devam etmesi bilincli: havuz buyudugunde uretec CALISMAYA
    DEVAM eder, yalnizca son kisiler sicilleriyle gorunur. Hata vermek,
    kadro buyuklugunu denemek isteyen kullaniciyi durdururdu.
    """
    adlar = _ADLAR.get(sicil_on_eki, ())
    return adlar[sira - 1] if sira <= len(adlar) else f"{sicil_on_eki}-{sira:03d}"


def _personeli_olustur(
    oturum: Session, yetkinlikler: dict[str, Yetkinlik], bugun: date
) -> dict[str, list[Personel]]:
    # Aktiflik penceresi uretilen en eski donemden BELIRGIN once acilir:
    # H7 aktiflik araligi disindaki gunlerde personeli musait saymaz ve
    # sabit bir yil basi tarihi, demo yil basinda uretildiginde gecmis
    # haftalarin bir kismini kadrosuz birakirdi.
    ise_baslama = bugun - timedelta(days=365)
    pasif_kapanis = bugun - timedelta(days=_PASIF_KAPANIS_GUN_ONCE)

    gruplar: dict[str, list[Personel]] = {}
    for grup in PERSONEL_GRUPLARI:
        kisiler: list[Personel] = []
        for i in range(1, grup.sayi + 1):
            sicil_no = f"{grup.sicil_on_eki}-{i:03d}"
            personel = Personel(
                ad_soyad=_ad_soyad(grup.sicil_on_eki, i),
                sicil_no=sicil_no,
                haftalik_hedef_saat=40,
                aktif_baslangic=ise_baslama,
                aktif_bitis=pasif_kapanis if sicil_no == _PASIF_PERSONEL_SICIL else None,
                devir_fazla_calisma_saat=Decimal(str(_DEVIR_BAKIYELERI.get(sicil_no, 0.0))),
                kota_yili=bugun.year,
            )
            personel.yetkinlikler = [yetkinlikler[ad] for ad in grup.yetkinlikler]
            oturum.add(personel)
            kisiler.append(personel)
        gruplar[grup.sicil_on_eki] = kisiler
    oturum.flush()
    return gruplar


def _ozel_gunleri_olustur(oturum: Session, bugun: date) -> None:
    """FR-1.10: resmi tatil takvimi, KUTUPHANEDEN.

    Onceki surum yalnizca sabit tarihli yedi ulusal bayrami yaziyor, dini
    bayramlari disarida birakiyordu. Artik ikisi de `app/services/
    tatil_takvimi.py` uzerinden geliyor; oradaki modul dogru tarihleri
    hesapliyor ve gerekcesi orada yazili.

    Iki yil uretilir (icinde bulunulan ve sonraki): gosterim verisi yil
    sonuna yakin uretildiginde bir sonraki donemin tatilleri de takvimde
    bulunmali.

    Talep matrisi RESMI_TATIL satirlari tasidigi icin (bkz.
    ornek_senaryo.talep_satirlarini_olustur) bu gunler gercekten azaltilmis
    kadroyla cozulur; TD-3 uyarinca adalet sayaclarinda da hafta sonuyla
    ayni sayaca eklenirler.
    """
    tatiller = resmi_tatiller((bugun.year, bugun.year + 1))
    oturum.add_all(OzelGun(tarih=tarih, ad=ad) for tarih, ad in tatiller)
    oturum.flush()
    print(f"  Resmi tatil: {len(tatiller)} gun ({bugun.year}-{bugun.year + 1})", flush=True)


@dataclass(frozen=True, slots=True)
class DemoDonemleri:
    """Bes haftalik donem, ESKIDEN YENIYE sirali.

    Adlandirilmis alanlar yerine liste: haftalarin tek farki takvimdeki
    yerleri ve tasidiklari izin kayitlari; her birine ayri bir isim vermek
    (gecen, onceki, daha_onceki...) sayiyi degistirmeyi zorlastirirdi.
    Senaryo tasiyan iki hafta ayrica isimle de erisilebilir, cunku onlara
    BAKAN kod (testler ve cizelge dagitimi) hangisi olduklarini bilmek
    zorunda.
    """

    haftalar: tuple[Donem, ...]

    @property
    def bu_hafta(self) -> Donem:
        """Bugunu iceren hafta. Calisan panelinin tamami buna baglidir."""
        return self.haftalar[-1]

    @property
    def dar_hafta(self) -> Donem:
        """Sef havuzunun kapanamayan acik verdigi hafta (asagida kurulur)."""
        return self.haftalar[_DAR_HAFTA_INDISI]

    @property
    def rahat_hafta(self) -> Donem:
        """Hic izin kaydi tasimayan hafta; agirlik kalibrasyonunun tabani."""
        return self.haftalar[_RAHAT_HAFTA_INDISI]


# Senaryolarin hangi haftaya dustugu. Indisler ESKIDEN YENIYE sayilir ve
# bugunu iceren hafta her zaman sonuncudur.
#
# Dar hafta neden en eskiye degil ikinciye konuyor: en eski hafta, bir
# sonraki donemin isitma penceresidir (TD-5) ve kapsama acikli bir hafta
# oradan sonraki her haftanin baslangic kosulunu bozardi. Rahat hafta ise
# dar haftadan SONRA gelir ki ikisi ekranda yan yana karsilastirilabilsin.
_DAR_HAFTA_INDISI = 1
_RAHAT_HAFTA_INDISI = 2


def _donemleri_ve_izinleri_olustur(
    oturum: Session, personel_gruplari: dict[str, list[Personel]], bugun: date
) -> DemoDonemleri:
    """Bes haftalik donem ve izin kayitlari.

    | Hafta | Yeri            | Ne gosterir                                  |
    |-------|-----------------|----------------------------------------------|
    | H-4   | dort hafta once | En eski gecmis; sonraki haftanin isitma       |
    |       |                 | penceresi (TD-5)                              |
    | H-3   | uc hafta once   | DAR HAFTA: sef havuzunun kapanamayan acigi    |
    | H-2   | iki hafta once  | RAHAT: hic izin yok, kadro talebi karsiliyor  |
    | H-1   | gecen hafta     | Musaitlik TIPLERININ ve yarim gun dilimlerin  |
    |       |                 | tamami                                        |
    | H-0   | BUGUNU ICERIR   | Calisan panelinin "Vardiyalarim"i, "siradaki  |
    |       |                 | vardiya" ve ACIK tercih penceresi             |

    Butun donemler PAZARTESI baslar (SRS 3.3: haftalik planlama) ve
    birbirleriyle CAKISMAZ - `guncel_donemi_bul` cakisan donemlerde hangisini
    sececegini bilemezdi.
    """
    bu_pzt = _bu_haftanin_pazartesisi(bugun)

    def kapali_pencere(baslangic: date) -> date:
        """Tercih penceresini KESIN olarak kapali birakan son tarih.

        `tercihe_acik_donemi_bul` "tercih_son_tarihi >= bugun" olan en erken
        donemi dondurur; demoda tercih bildirimini BU HAFTA uzerinden
        gostermek istiyoruz, dolayisiyla gecmis haftalarin penceresi bugunden
        once kapanmis olmali.
        """
        return min(baslangic - timedelta(days=7), bugun - timedelta(days=1))

    haftalar: list[Donem] = []
    for geriye in range(_HAFTA_SAYISI - 1, -1, -1):
        bas = bu_pzt - timedelta(days=7 * geriye)
        haftalar.append(
            Donem(
                baslangic_tarihi=bas,
                bitis_tarihi=bas + timedelta(days=6),
                # TEK ACIK PENCERE bugunu iceren haftadir. Bes donemin hepsi
                # bugun veya gecmis oldugundan, pencere acik birakilmazsa
                # Tercihler ekrani ve calisan panelinin tercih formu HIC
                # calismaz - `tercihe_acik_donemi_bul` hicbir donem bulamaz.
                # Devam eden bir hafta icin tercih toplamak alisildik degil,
                # ama alternatifi ozelligi gosterememekti.
                tercih_son_tarihi=(bas + timedelta(days=6) if geriye == 0 else kapali_pencere(bas)),
            )
        )
    oturum.add_all(haftalar)
    oturum.flush()

    donemler = DemoDonemleri(haftalar=tuple(haftalar))
    _dar_hafta_izinleri(oturum, personel_gruplari, donemler.dar_hafta)
    _cesitlilik_izinleri(oturum, personel_gruplari, donemler.haftalar[-2])
    _bu_hafta_girdileri(oturum, personel_gruplari, donemler.bu_hafta)
    _en_eski_hafta_izinleri(oturum, personel_gruplari, donemler.haftalar[0])
    oturum.flush()
    return donemler


def _dar_hafta_izinleri(
    oturum: Session, personel_gruplari: dict[str, list[Personel]], donem: Donem
) -> None:
    """Kapanamayan kapsama acigi — SEF HAVUZU uzerinden.

    CELISKI KADRO BUYUKLUGU UZERINDEN KURULAMAZ. Blok uzunlugu artik
    cozumun CIKTISIDIR (SRS TD-13); "kadroyu kucult" mekanizmasi calismaz,
    cozucu ayni kadroyla daha uzun bloklar uretip acigi kapatir. Sef havuzu
    ise blok uzunlugundan BAGIMSIZ bir sinir tasir: Vardiya Sefligi
    noktasina yalnizca Vardiya Sefi yetkinligi olanlar girebilir (H8) ve o
    nokta kesintisiz doludur - haftada 168 kisi-saat. Yedi kisilik havuzun
    besini izne cikarmak, kalan ikisinin gunluk tavan (11 saat) ve haftalik
    izin gunu (H6) altinda kapatamayacagi bir bosluk dogurur: iki kisi
    haftada en cok 2 x 6 x 11 = 132 kisi-saat verir, gereken 168'dir. Eksik
    olan SAAT degil KISIDIR ve hicbir blok uzunlugu bunu degistiremez.

    Bu senaryo eskiden dort haftalik ayri bir "sikisik donem"deydi. Donemler
    haftalik olunca aciklik donem geneline seyrelmiyor ve dogrudan
    gorunuyor - kapsama satiri, yazdirma ciktisi ve Analiz karti ayni
    haftada okunabiliyor.
    """
    for personel in personel_gruplari["VS"][:5]:
        oturum.add(
            Musaitlik(
                personel_id=personel.personel_id,
                baslangic_tarihi=donem.baslangic_tarihi,
                bitis_tarihi=donem.bitis_tarihi,
                dilim=MusaitlikDilimi.TAM_GUN,
                tip=MusaitlikTipi.YILLIK_IZIN,
                not_="Demo: dar hafta - vardiya şefliği kapsama açığı",
            )
        )


def _en_eski_hafta_izinleri(
    oturum: Session, personel_gruplari: dict[str, list[Personel]], donem: Donem
) -> None:
    """En eski haftanin olagan izinleri.

    Amaci senaryo kurmak degil, gecmisin BOS gorunmemesi: hicbir izin
    tasimayan bes hafta ust uste, izin yonetiminin hic kullanilmadigi bir
    kurum izlenimi verirdi.
    """
    guvenlik = personel_gruplari["GG"]
    oturum.add_all(
        [
            Musaitlik(
                personel_id=guvenlik[4].personel_id,
                baslangic_tarihi=donem.baslangic_tarihi,
                bitis_tarihi=donem.baslangic_tarihi + timedelta(days=4),
                dilim=MusaitlikDilimi.TAM_GUN,
                tip=MusaitlikTipi.YILLIK_IZIN,
                not_="Demo: beş günlük yıllık izin",
            ),
            Musaitlik(
                personel_id=guvenlik[5].personel_id,
                baslangic_tarihi=donem.baslangic_tarihi + timedelta(days=3),
                bitis_tarihi=donem.baslangic_tarihi + timedelta(days=4),
                dilim=MusaitlikDilimi.TAM_GUN,
                tip=MusaitlikTipi.MAZERET,
                not_="Demo: iki günlük mazeret izni",
            ),
        ]
    )


def _cesitlilik_izinleri(
    oturum: Session, personel_gruplari: dict[str, list[Personel]], donem: Donem
) -> None:
    """Musaitlik TIPLERININ ve yarim gun dilimlerin tamami tek haftada.

    Cesitlilik BILEREK tek bir haftada toplaniyor: dar haftanin izinleri tek
    bir seyi gostermek icin kurulmus ve rahat hafta tanimi geregi izin
    tasimaz; ikisine de kayit eklemek o senaryolarin anlatimini bozardi.

    Burada gosterilenler: dort musaitlik tipi (yillik izin, rapor, egitim,
    mazeret) ve iki yarim gun dilimi (TD-4).

    INDISLER SONDAN SAYILIR. Kadro buyuklugu degistiginde sabit indisler
    listeden tasar; bu kayitlarin amaci belirli bir KISIYI degil, cesitliligi
    gostermek.
    """
    guvenlik = personel_gruplari["GG"]
    sefler = personel_gruplari["VS"]
    gun = donem.baslangic_tarihi

    oturum.add_all(
        [
            Musaitlik(
                personel_id=guvenlik[-3].personel_id,
                baslangic_tarihi=gun + timedelta(days=1),
                bitis_tarihi=gun + timedelta(days=3),
                dilim=MusaitlikDilimi.TAM_GUN,
                tip=MusaitlikTipi.RAPOR,
                not_="Demo: üç günlük istirahat raporu",
            ),
            Musaitlik(
                personel_id=guvenlik[-2].personel_id,
                baslangic_tarihi=gun,
                bitis_tarihi=gun,
                dilim=MusaitlikDilimi.OGLEDEN_ONCE,
                tip=MusaitlikTipi.EGITIM,
                # TD-4: ogleden once 00:00-12:00 ile kesisen HER blogu
                # engeller - gece ve gunduz dahil.
                not_="Demo: yarım gün eğitim (öğleden önce)",
            ),
            Musaitlik(
                personel_id=guvenlik[-1].personel_id,
                baslangic_tarihi=gun + timedelta(days=2),
                bitis_tarihi=gun + timedelta(days=2),
                dilim=MusaitlikDilimi.OGLEDEN_SONRA,
                tip=MusaitlikTipi.MAZERET,
                not_="Demo: yarım gün mazeret izni (öğleden sonra)",
            ),
            Musaitlik(
                personel_id=sefler[-1].personel_id,
                baslangic_tarihi=gun + timedelta(days=4),
                bitis_tarihi=gun + timedelta(days=5),
                dilim=MusaitlikDilimi.TAM_GUN,
                tip=MusaitlikTipi.YILLIK_IZIN,
                not_="Demo: iki günlük yıllık izin",
            ),
        ]
    )


def _bu_hafta_girdileri(
    oturum: Session, personel_gruplari: dict[str, list[Personel]], donem: Donem
) -> None:
    """Bugunu iceren haftanin izinleri ve TERCIHLERI.

    Tercihler buraya baglanir cunku tek ACIK tercih penceresi bu donemdir
    (bkz. `_donemleri_ve_izinleri_olustur`); baska bir doneme baglansalardi
    calisan panelindeki tercih formu onlari hic gostermezdi.

    Tercihin uc durumu (beklemede, onaylandi, reddedildi) ve iki tipi
    (calismama, zaman araligi tercihi) burada gorunur; yalnizca ONAYLANMIS
    olanlar modele girer (FR-3.5, S5).
    """
    guvenlik = personel_gruplari["GG"]
    gun = donem.baslangic_tarihi

    oturum.add(
        Musaitlik(
            personel_id=guvenlik[6].personel_id,
            baslangic_tarihi=gun + timedelta(days=2),
            bitis_tarihi=gun + timedelta(days=3),
            dilim=MusaitlikDilimi.TAM_GUN,
            tip=MusaitlikTipi.RAPOR,
            not_="Demo: iki günlük istirahat raporu",
        )
    )

    oturum.add_all(
        [
            Tercih(
                personel_id=guvenlik[0].personel_id,
                donem_id=donem.donem_id,
                tarih=gun + timedelta(days=5),
                tip=TercihTipi.CALISMAMA,
                durum=TercihDurumu.ONAYLANDI,
                calisan_notu="Kardeşimin düğünü",
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
                tarih=gun + timedelta(days=5),
                tip=TercihTipi.CALISMAMA,
                durum=TercihDurumu.REDDEDILDI,
                calisan_notu="Hafta sonu iznine çıkmak istiyorum",
                ret_gerekcesi="Aynı gün için üç talep geldi; kıdem sırası gözetildi",
            ),
            # ZAMAN ARALIGI TERCIHI (SRS FR-3.2, TD-12): calisan artik bir
            # vardiya tipi degil, calismak istedigi saatleri bildirir.
            Tercih(
                personel_id=guvenlik[3].personel_id,
                donem_id=donem.donem_id,
                tarih=gun + timedelta(days=2),
                tip=TercihTipi.ZAMAN_ARALIGI_TERCIHI,
                tercih_baslangic=time(8, 0),
                tercih_bitis=time(16, 0),
                durum=TercihDurumu.ONAYLANDI,
                calisan_notu="Çocuğumu okuldan almam gerekiyor, gündüz çalışmak isterim",
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

    Dagilim bilincli; TD-8'in durumlarindan ucu ekranda gorunur:

      Gecmis haftalar -> yayinlandi   (yasanmis cizelge)
      DAR hafta       -> cozuldu      (kapsama acikli, YAYINLANMAMIS: acigi
                                       olan bir cizelge yayinlanmadan once
                                       incelenir; Surumler ekraninin
                                       "cozuldu" durumu da ancak boyle
                                       gorunur)
      Bu hafta        -> arsiv + yayinlandi (iki surum: FR-9.4'un "degisen
                                       gunler" isareti ancak bir arsiv
                                       tabani varsa hesaplanabilir)

    Dorduncu durum (taslak) uretilmez: her "Yeniden Coz" zaten bir taslak
    acar, yani kullanici onu ilk tiklamada kendisi gorur. Uydurma bir taslak
    eklemek Surumler listesini gercekte olmayacak bir kayitla doldururdu.
    """
    surum_depo = CizelgeSurumuDeposu(oturum)
    limit = _COZUM_ZAMAN_LIMITI_SANIYE

    for sira, donem in enumerate(donemler.haftalar):
        gecmis = donem is not donemler.bu_hafta
        etiket = f"H-{len(donemler.haftalar) - 1 - sira}"

        if donem is donemler.dar_hafta:
            # Cozulur birakilir; yayinlanmaz.
            _donemi_coz(oturum, donem, zaman_limiti=limit, etiket=f"{etiket} (dar hafta)")
            oturum.commit()
            continue

        surum = _donemi_coz(oturum, donem, zaman_limiti=limit, etiket=etiket)
        if surum is None:
            continue
        surum_depo.yayinla(surum)
        oturum.commit()

        if gecmis:
            continue

        # Bu hafta icin IKINCI surum: yeniden cozum (SDD 5.6). Yayinlandiginda
        # birincisi arsive duser ve calisan panelindeki karsilastirma tabani
        # olusur - FR-9.4'un "degisen gunler" isareti bunsuz hesaplanamaz.
        ikinci_is = CozumServisi(oturum).baslat(onceki_surum_id=surum, zaman_limiti_saniye=limit)
        if ikinci_is is not None:
            print(f"  {etiket} (2. surum): yeniden cozuluyor...", flush=True)
            cozum_isini_calistir(oturum, ikinci_is.is_id)
            surum_depo.yayinla(ikinci_is.surum_id)
            oturum.commit()
            print(f"  {etiket} (2. surum): yayinlandi, 1. surum arsivde", flush=True)


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

        yetkinlikler = _yetkinlikleri_olustur(oturum)
        noktalar = _noktalari_olustur(oturum, yetkinlikler)
        _talebi_olustur(oturum, noktalar)
        _kurallari_olustur(oturum)
        _ozel_gunleri_olustur(oturum, bugun)
        personel_gruplari = _personeli_olustur(oturum, yetkinlikler, bugun)
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
        f"Demo verisi uretildi: {toplam_personel} personel (1 pasif), "
        f"{len(NOKTA_TANIMLARI)} gorev noktasi, {len(_KURAL_TANIMLARI)} kural, "
        f"{len(resmi_tatiller((bugun.year, bugun.year + 1)))} resmi tatil, "
        f"{_HAFTA_SAYISI} haftalik donem (en eskisi "
        f"{_bu_haftanin_pazartesisi(bugun) - timedelta(days=7 * (_HAFTA_SAYISI - 1))}, "
        f"sonuncusu bugunu icerir)."
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
