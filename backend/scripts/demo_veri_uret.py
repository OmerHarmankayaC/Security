#!/usr/bin/env python3
"""Gosterim (demo) ortaminin verisini uretir — VARDIS Demo Senaryosu 1.0.

Kapsam VERIDIR. Kural katalogu, agirliklar, gereksinimler ve tasarim bu
betigin kapsami disindadir; onlarin kaynagi SRS ve SDD'dir. Demo verisi
kurallari degistirmez, kurallara uyar (Demo Senaryosu 2.6).

ILKELER (Demo Senaryosu 2):

  KURGUSALDIR. Hicbir kayit gercek bir kuruma veya kisiye ait degildir.
  URETILIR. Tek uretici bu betiktir; arayuzden yapilan elle duzeltme bir
    sonraki sifirlamada kaybolur.
  TARIHLER GORECELIDIR. Calistirma gunu referanstir. Sabit takvim tarihi
    yalnizca resmi tatil takvimindedir (o da kutuphaneden gelir), boylece
    demo alti ay sonra da "canli" gorunur.
  DETERMINISTIKTIR. Sabit tohum (`_SABIT_TOHUM`) kullanilir: ayni gun iki
    kez calistirilan betik ayni personeli, ayni izinleri, ayni tercihleri
    uretir.

    *** TEK ISTISNA ATAMALARDIR. *** CP-SAT paralel arama yurutur; ayni
    model iki kez cozuldugunde farkli (esdeger) bir cozume varabilir ve
    zaman limitine takilan arama makinenin o andaki yukune gore farkli bir
    noktada kesilir. Yani `atama`, `kapsama_acigi`, `fazla_kadro` ve
    `cozum_isi` satirlari iki kosum arasinda BIREBIR AYNI OLMAYABILIR.
    Tanim ve girdi verisi (bina, personel, yetkinlik, nokta, talep, ozel
    gun, musaitlik, tercih, kural) birebir aynidir; kabul olcutu
    (Demo Senaryosu 9.5) tam olarak bu ayrimi yapar.

DONEM YAPISI (Demo Senaryosu 6). Bugunun icinde bulundugu hafta D0'dir:

  D-12 ... D-1   yayinlandi   gercek cozucuyle uretilmis on iki hafta;
                              ikisi izin dalgasi tasir
  D0             yayinlandi   guncel cizelge; calisan panelinin ve Ozet
                              ekraninin gosterdigi donem
  D+1            iki surum    1: cozucu ciktisi, 2: uzerinde elle degisiklik
  D+2            sikisik      kadronun dortte biri izinli; kapsama acigi

Gecmis donem sayisi adalet ufkunun (90 gun) tamamini dolduracak bicimde
secilmistir; Analiz ekranindaki ufuk anahtari ancak boyle iki farkli sonuc
gosterir.

HESAPLAR (Demo Senaryosu 7). Parolalar `DEMO_PAROLA` ortam degiskeninden
okunur; ne bu dosyada, ne depoda, ne baska bir yerde durur. Degisken
verilmezse hesaplar ACILMAZ ve betik bunu yuksek sesle soyler.

Kullanim:
    DEMO_PAROLA=... python scripts/demo_veri_uret.py --reset

--reset verilirse once tum tanim/girdi/kural/sonuc satirlari silinir
(silinecek tablolarin listesi app/veri_temizligi.py'de) ve demo hesaplari
YENIDEN KURULUR. Temizlik `kullanici.personel_id` bagini tasiyan hesaplari
dusurmek zorundadir - aksi halde `DELETE FROM personel` bir kisit hatasiyla
duserdi - ve bu yuzden calisan hesaplari temizlikten SONRA yeniden acilir.

Betik, VERI_TEMIZLIGINE_IZIN ortam degiskeni verilmeden calismaz
(app/veri_temizligi.py, uretim kilidi).
"""

import argparse
import random
import sys
from dataclasses import dataclass
from datetime import date, time, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import ayarlar
from app.db import OturumYerel
from app.models.girdi import (
    Musaitlik,
    MusaitlikDilimi,
    MusaitlikTipi,
    Tercih,
    TercihDurumu,
    TercihTipi,
)
from app.models.kimlik import Kullanici, Rol
from app.models.sonuc import Atama, AtamaKaynagi, CozumIsi, Donem
from app.models.tanim import (
    Bina,
    GorevNoktasi,
    OzelGun,
    Personel,
    Talep,
    Yetkinlik,
)
from app.repositories.sonuc import AtamaDeposu, CizelgeSurumuDeposu
from app.services import parola as parola_araclari
from app.services.cozum_servisi import CozumServisi, cozum_isini_calistir
from app.services.kullanici_servisi import KullaniciServisi
from app.services.kural_katalogu_tohumu import KURAL_TANIMLARI, katalogu_kur
from app.services.ornek_senaryo import (
    GUVENLIK_GOREVI,
    NOKTA_TANIMLARI,
    PERSONEL_GRUPLARI,
    VARDIYA_SEFI,
    talep_satirlarini_olustur,
)
from app.services.surum_servisi import SurumServisi
from app.services.tatil_takvimi import resmi_tatiller, yil_araligi
from app.veri_temizligi import (
    HesapKapsami,
    TemizlikSonucu,
    UretimKilidiError,
    veriyi_temizle,
)

# --- Determinizm -----------------------------------------------------------
#
# Tohum SABIT ve GORUNURDUR. `random` modulunun genel durumu yerine ayri bir
# uretec tutulur: genel durum, iceri aktarilan herhangi bir modulun
# cagrisiyla ilerleyebilir ve betigin ciktisi sessizce degisirdi.
_SABIT_TOHUM = 20260827


# --- Donem takvimi ---------------------------------------------------------
#
# Butun donemler PAZARTESI baslar (SRS 3.3: haftalik planlama) ve
# birbirleriyle CAKISMAZ - `guncel_donemi_bul` cakisan donemlerde hangisini
# sececegini bilemezdi.
#
# Donemler eskiden sabit takvim tarihlerine baglanmisti; gosterim verisinin
# uretildigi gun o tarihleri gectiginde sistem BOS gorunuyordu (calisan
# panelinin "Vardiyalarim"i bugunu iceren bir donem bulamiyordu).
_GECMIS_HAFTA_SAYISI = 12  # D-12 ... D-1 (Demo Senaryosu 6)
_GELECEK_HAFTA_SAYISI = 2  # D+1 (iki surum) ve D+2 (sikisik)

# Cozum zaman limiti (saniye). Gecmis donemler OLCUM DEGIL GOSTERIM
# verisidir (Demo Senaryosu 6); kabul olcumu ayri veritabaninda alinmaya
# devam eder. Yine de kisa tutulamaz: on bes saniyelik bir limit kirk
# kisilik bir haftada cozucuyu adalet hedeflerine sira gelmeden kesiyor ve
# ekranda gereginden dengesiz bir cizelge birakiyordu.
_COZUM_ZAMAN_LIMITI_SANIYE = 60

# --- Kadro (Demo Senaryosu 4.3) --------------------------------------------
#
# Sicil numarasi havuzdan BAGIMSIZ ve suredir: D-1001 ... D-1040. Ilk dokuz
# sicil vardiya seflerine, kalan otuz biri guvenlik gorevlilerine duser
# (PERSONEL_GRUPLARI sirasi).
_SICIL_BASLANGIC = 1001


def _sicil(sira: int) -> str:
    """Sifirdan sayan sira numarasindan sicil: 0 -> D-1001."""
    return f"D-{_SICIL_BASLANGIC + sira}"


# Haftalik hedef saat: otuz yedi personel 45, uc personel 30. Deger S4'un
# MUTLAK hedefi degil, adil payin ORANIDIR (app/kurallar/esnek.py,
# s4_hedef_paylari); kismi zamanli uc kisi bu yuzden orantili olarak daha
# kucuk bir pay alir ve payin orantili hesaplandigi ekranda gorunur.
_TAM_ZAMANLI_HEDEF_SAAT = 45
_KISMI_ZAMANLI_HEDEF_SAAT = 30
_KISMI_ZAMANLI_SICILLER = ("D-1015", "D-1026", "D-1037")

# UC SINIR DURUMU (Demo Senaryosu 4.3). Bunlar susleme degil: sistemin en
# kolay kacirilan davranisini - calisabilirlik orani, SDD 5.9 - gorunur
# kilarlar.
#
# YENI BASLAYAN. Adalet ufku doksan gundur; bu kisi ufkun ORTASINDA ise
# basladigi icin `calisabilir_oran` yaklasik 0,5 cikar ve adil payi
# yarilanir. Demo verisi bunu tasimasaydi oranin etkisi hicbir ekranda
# gorunmezdi: herkes ufkun tamaminda calisabilir oldugunda oran hep 1,0'dir
# ve kod calisiyormus gibi durur. Oranin var olma nedeni de burada okunur -
# bu kisi tam payla olculseydi kalici olarak hedefin ALTINDA gorunur ve
# sapmasi hicbir cizelgeyle kapatilamazdi (SRS TD-6).
_YENI_BASLAYAN_SICIL = "D-1040"
_YENI_BASLAYAN_GUN_ONCE = 45

# AYRILAN. Aktiflik penceresi gecmiste kapanmis bir kayit (SDD 4.2.1).
# Tanimlar ekranindaki "Pasifleri goster" filtresini ve H7'nin aktiflik
# araligi kontrolunu gorunur kilar; hicbir pasif kayit yoksa ikisi de bos
# calisir. Gecen ay kapanir - yani uretilen gecmis donemlerin ICINDE, ki
# adalet sayaclari kismen calisabilen bir kisiyi de gorsun.
_AYRILAN_SICIL = "D-1039"
_AYRILAN_GUN_ONCE = 30

# DEVIR BAKIYESI (H10, FR-1.1). Kota senaryosunun tamami bu uc satirda;
# yillik kota 270 saat, esik 45 saat/hafta.
#
#   D-1010: 265 saat -> kalan 5. Bir haftalik fazla calismaya bile yetmez;
#     on kontrol "kotasi dolmus" uyarisi verir ve H10 bu kisiyi esigin
#     UZERINE cikaramaz. KURAL COZULEMEZLIK URETMEZ: kisi esige kadar
#     calismaya devam eder (SRS 4.2 H10). Kabul olcutu 9.3'u (kota
#     kartinda en az bir kisi yillik kotanin yarisinin ustunde) bu satir
#     karsilar: 265 > 135.
#   D-1011: 240 saat -> kalan 30. Bir haftalik fazla calismayi (azami 21
#     saat) kaldirir ama ikisini kaldirmaz; kotanin BAGLAYICI oldugu ama
#     tuketilmedigi ara durum.
#   D-1001: 120 saat -> kalan 150. Kirilgan sef havuzunda kota bol;
#     sikisik senaryonun acigi kotadan DEGIL kisi sayisindan dogar, ikisi
#     karismasin diye.
#
# Kota yili demo uretildigi yildir; sabit yazilsaydi yil donunce butun
# bakiyeler "gecen yilin" gorunurdu.
_DEVIR_BAKIYELERI: dict[str, float] = {
    "D-1010": 265.0,
    "D-1011": 240.0,
    "D-1001": 120.0,
}

# KURGUSAL AD HAVUZU (Demo Senaryosu 2.1). Kirk ad, tekrarsiz. Adlar
# kurgudur ve hicbiri gercek bir kisiye ait degildir; ekranlarda satirlarin
# birbirinden ayirt edilebilmesi icin gercekci tutulmuslardir - "Demo
# Personel 17" bicimindeki adlar cizelge izgarasinda, analiz tablosunda ve
# calisan panelinde okunmuyordu.
#
# Liste sicil sirasina gore okunur. Kadrodan kisa kalirsa kalan kisiler
# sicilleriyle gorunur ve betik DURMAZ: kadro buyuklugunu denemek isteyen
# kullaniciyi bir ad listesi yuzunden durdurmak icin neden yok.
_ADLAR: tuple[str, ...] = (
    # D-1001 ... D-1009: vardiya sefleri
    "Mehmet Aydın",
    "Hatice Şahin",
    "Ali Rıza Koç",
    "Zeynep Arslan",
    "Mustafa Yıldırım",
    "Emine Doğan",
    "Hüseyin Çetin",
    "Şükran Balcı",
    "Orhan Tekin",
    # D-1010 ... D-1040: guvenlik gorevlileri
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
    "Derya Korkmaz",
    "Gülay Sezer",
    "Necati Baran",
    "Ferhat Toprak",
    "Yasemin Akın",
    "Burak Sevinç",
    "Selim Nalbant",
    "Hakan Efeoğlu",
)

# --- Bina (Demo Senaryosu 4.2) ---------------------------------------------
#
# Bina kayitlari yazilir ama gorev noktalari TESIS GENELIDIR (bina_id
# bostur, Charter 2.5). Ikisi celiski degil: bina tanimi urunun destekledigi
# bir boyuttur ve Tanimlar ekraninda gorunur; bu senaryoda hicbir nokta ona
# baglanmaz, dolayisiyla S6b (bina tutarliligi) modelde daima sifir katki
# verir ve katalogda pasif tutulur.
_BINA_ADLARI = ("A Blok", "B Blok")


# --- Musaitlik dagilimi (Demo Senaryosu 5.1) -------------------------------
#
# Her donemde kadronun yuzde 8 ile 12'si izinlidir: kirk kisilik kadroda
# uc ile bes kisi arasi.
_IZIN_ORANI_ALT = 0.08
_IZIN_ORANI_UST = 0.12

# Gecmis donemlerden IKISI izin dalgasi tasir (kadronun yaklasik dortte
# biri ayni hafta izinli). Bu iki donem, kota kartinin dolmasini saglayan
# fazla calismayi uretir.
_DALGA_ORANI = 0.25
_DALGA_DONEM_INDISLERI = (3, 8)  # D-12'den sayilir: D-9 ve D-4

# DALGADA SEF SAYISI SINIRLIDIR. Yayinlanan hicbir donemde kapsama acigi
# olmamalidir (Demo Senaryosu 9.4) ve acik, sef havuzu daraldiginda dogar:
# Vardiya Sefligi noktasi haftada 168 kisi-saat ister, kalan k sef en cok
# k x 6 x 11 kisi-saat verebilir. Uc sef bile 198 > 168 verir; ikiye
# dusuldugunde 132 < 168 olur ve acik kapanamaz.
_GECMISTE_AZAMI_IZINLI_SEF = 2

# SIKISIK TASLAK (Demo Senaryosu 6, D+2). Kadronun dortte biri izinli ve
# acik BILEREK uretilir: yedi sef izne cikar, kalan iki sef 132 kisi-saat
# verebilir, nokta 168 ister. Eksik olan SAAT degil KISIDIR ve hicbir blok
# uzunlugu bunu kapatamaz (SRS TD-13). Ayni etkiyi kadroyu kucultmekle
# uretmek MUMKUN DEGILDIR: blok uzunlugu cozumun ciktisidir, cozucu ayni
# kadroyla daha uzun bloklar uretip acigi kapatir.
_SIKISIK_IZINLI_SEF = 7
_SIKISIK_IZINLI_GUVENLIK = 3

_IZIN_TIPLERI = (
    MusaitlikTipi.YILLIK_IZIN,
    MusaitlikTipi.RAPOR,
    MusaitlikTipi.EGITIM,
    MusaitlikTipi.MAZERET,
)
# Dilim COGUNLUKLA tam gun, birkac kayit yarim gundur (Demo Senaryosu 5.1).
# TD-4'un iki dilimi de gorunur kalsin diye ogleden once ve ogleden sonra
# esit paylasilir.
_YARIM_GUN_PAYI = 0.2

_IZIN_NOTLARI = {
    MusaitlikTipi.YILLIK_IZIN: "Yıllık izin",
    MusaitlikTipi.RAPOR: "İstirahat raporu",
    MusaitlikTipi.EGITIM: "Hizmet içi eğitim",
    MusaitlikTipi.MAZERET: "Mazeret izni",
}

# --- Tercih dagilimi (Demo Senaryosu 5.2) ----------------------------------
#
# Guncel (D0) ve gelecek (D+1) donem icin yaklasik yirmi bes kayit. Durum
# dagilimi uc degeri de kapsar; bir kismi calisan notu tasir. AYNI PERSONELE
# AYNI GUN IKINCI TERCIH YAZILMAZ (FR-9.6) - veritabani da bunu
# `uq_tercih_personel_tarih` ile zorlar.
_TERCIH_SAYISI = {"guncel": 10, "gelecek": 15}

_CALISAN_NOTLARI = (
    "Kardeşimin düğünü var",
    "Sağlık kontrolü randevum var",
    "Çocuğumu okuldan almam gerekiyor",
    "Aile ziyareti için şehir dışına çıkacağım",
    "Ehliyet sınavım var",
    "Taşınıyorum",
    "Veli toplantısına katılmam gerekiyor",
)
_RET_GEREKCELERI = (
    "Aynı gün için üç talep geldi; kıdem sırası gözetildi",
    "Vardiya şefi havuzu o hafta zaten dar",
    "Aynı personel için bu dönemde bir tercih daha karşılandı",
)

# --- Hesaplar (Demo Senaryosu 7) -------------------------------------------
_PAROLA_DEGISKENI = "DEMO_PAROLA"
_YONETIM_HESAPLARI: tuple[tuple[str, Rol], ...] = (
    ("demo_sistem", Rol.SISTEM_YONETICISI),
    ("demo_hesap", Rol.HESAP_YONETICISI),
    ("demo_idare", Rol.IDARE),
)
# Iki calisan hesabi: biri kotasi dolmaya yaklasmis personele (D-1010,
# devir bakiyesi 265), digeri ortalama yuklu bir personele bagli. Boylece
# calisan paneli iki farkli tabloyla gosterilebilir (Demo Senaryosu 7).
_CALISAN_HESABI_SICILLERI = ("D-1010", "D-1020")


def _bu_haftanin_pazartesisi(bugun: date) -> date:
    return bugun - timedelta(days=bugun.weekday())


def _mevcut_demo_verisi_var_mi(oturum: Session) -> bool:
    stmt = select(Yetkinlik).where(Yetkinlik.ad == GUVENLIK_GOREVI)
    return oturum.execute(stmt).scalar_one_or_none() is not None


def _her_seyi_temizle(oturum: Session) -> TemizlikSonucu:
    """Tum demo verisini siler (app/veri_temizligi.py'deki tek sozlesme).

    Silinecek tablolarin listesi ve sirasi burada DEGIL o modulde durur;
    testler de ayni listeyi kullanir. Ikisi ayri yerde yazildiginda
    birbirinden sessizce ayrisiyordu.

    Hesap kapsami PERSONELE_BAGLI: bir personel kaydina bagli hesaplar
    (yani `DELETE FROM personel`i engelleyen satirlar) silinir, yonetim
    hesaplari KALIR. Silinen calisan hesaplari uretimin sonunda yeniden
    acilir (Demo Senaryosu 10).
    """
    return veriyi_temizle(oturum, hesaplar=HesapKapsami.PERSONELE_BAGLI)


# --- Tanim verisi ----------------------------------------------------------


def _binalari_olustur(oturum: Session) -> None:
    oturum.add_all(Bina(ad=ad) for ad in _BINA_ADLARI)
    oturum.flush()


def _yetkinlikleri_olustur(oturum: Session) -> dict[str, Yetkinlik]:
    yetkinlikler = {ad: Yetkinlik(ad=ad) for ad in (GUVENLIK_GOREVI, VARDIYA_SEFI)}
    oturum.add_all(yetkinlikler.values())
    oturum.flush()
    return yetkinlikler


def _noktalari_olustur(oturum: Session, yetkinlikler: dict[str, Yetkinlik]) -> list[GorevNoktasi]:
    """Charter 2.5: butun noktalar tesis geneli (bina_id=None)."""
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
    """Katalogu app/services/kural_katalogu_tohumu.py'den kurar.

    Tanim burada DEGIL o modulde durur: goc zinciri katalogun uc satirini
    (H9, H10, S1f) zaten yaziyor ve katalog iki yerde tanimlandiginda
    ortamlar arasinda sessizce ayrisiyordu (Demo Senaryosu 4.6).
    """
    katalogu_kur(oturum)


def _ozel_gunleri_olustur(oturum: Session, pencere: tuple[date, date]) -> int:
    """Demo penceresine DUSEN resmi tatiller (Demo Senaryosu 4.5).

    Kaynak `app/services/tatil_takvimi.py` uzerinden kutuphanedir, betikte
    sabit bir liste DEGILDIR. Demo Senaryosu 4.5 sabit liste yaziyor; sabit
    liste dini bayramlari yanlis yazar (tarihleri yila gore kayar) ve demo
    bir sonraki yila girdiginde sessizce eksik takvim uretirdi. Senaryonun
    asil istedigi - "yalniz pencereye dusenler yazilir" - korunmustur:
    onceki surum iki tam YILI yaziyordu ve pencere disindaki tatiller
    takvimde gereksiz yer tutuyordu.
    """
    baslangic, bitis = pencere
    tatiller = [
        (tarih, ad)
        for tarih, ad in resmi_tatiller(yil_araligi(baslangic, bitis))
        if baslangic <= tarih <= bitis
    ]
    oturum.add_all(OzelGun(tarih=tarih, ad=ad) for tarih, ad in tatiller)
    oturum.flush()
    print(f"  Resmi tatil: {len(tatiller)} gun ({baslangic} - {bitis})", flush=True)
    return len(tatiller)


def _personeli_olustur(
    oturum: Session, yetkinlikler: dict[str, Yetkinlik], bugun: date
) -> list[Personel]:
    """Kirk personel, sicil sirasina gore (Demo Senaryosu 4.3).

    Doner: sicil sirasinda personel listesi; ilk dokuzu vardiya sefi.
    """
    # Aktiflik penceresi uretilen en eski donemden BELIRGIN once acilir: H7
    # aktiflik araligi disindaki gunlerde personeli musait saymaz ve sabit
    # bir yil basi tarihi, demo yil basinda uretildiginde gecmis haftalarin
    # bir kismini kadrosuz birakirdi.
    ise_baslama = bugun - timedelta(days=365)
    yeni_baslangic = bugun - timedelta(days=_YENI_BASLAYAN_GUN_ONCE)
    ayrilis = bugun - timedelta(days=_AYRILAN_GUN_ONCE)

    kisiler: list[Personel] = []
    sira = 0
    for grup in PERSONEL_GRUPLARI:
        for _ in range(grup.sayi):
            sicil_no = _sicil(sira)
            personel = Personel(
                ad_soyad=_ADLAR[sira] if sira < len(_ADLAR) else sicil_no,
                sicil_no=sicil_no,
                haftalik_hedef_saat=(
                    _KISMI_ZAMANLI_HEDEF_SAAT
                    if sicil_no in _KISMI_ZAMANLI_SICILLER
                    else _TAM_ZAMANLI_HEDEF_SAAT
                ),
                aktif_baslangic=(
                    yeni_baslangic if sicil_no == _YENI_BASLAYAN_SICIL else ise_baslama
                ),
                aktif_bitis=ayrilis if sicil_no == _AYRILAN_SICIL else None,
                devir_fazla_calisma_saat=Decimal(str(_DEVIR_BAKIYELERI.get(sicil_no, 0.0))),
                kota_yili=bugun.year,
            )
            personel.yetkinlikler = [yetkinlikler[ad] for ad in grup.yetkinlikler]
            oturum.add(personel)
            kisiler.append(personel)
            sira += 1
    oturum.flush()
    return kisiler


# --- Donemler --------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DemoDonemleri:
    """Demo Senaryosu 6'daki donem yapisi, ESKIDEN YENIYE sirali."""

    gecmis: tuple[Donem, ...]  # D-12 ... D-1
    guncel: Donem  # D0
    gelecek: Donem  # D+1
    sikisik: Donem  # D+2

    @property
    def hepsi(self) -> tuple[Donem, ...]:
        return (*self.gecmis, self.guncel, self.gelecek, self.sikisik)


def _donemleri_olustur(oturum: Session, bugun: date) -> DemoDonemleri:
    """On bes haftalik donem zinciri.

    TERCIH PENCERESI. `tercihe_acik_donemi_bul` "tercih_son_tarihi >= bugun"
    olan EN ERKEN donemi dondurur. Acik pencere D+1'dir: D0 zaten
    yayinlanmis, yasanmakta olan cizelgedir ve ona tercih bildirmek anlamli
    degildir. Gecmis donemlerin ve D0'in penceresi bu yuzden bugunden once
    kapanir; D+2'ninki D+1'den SONRA kapanir ki "en erken acik" D+1 olsun.
    """
    bu_pzt = _bu_haftanin_pazartesisi(bugun)
    dun = bugun - timedelta(days=1)

    def hafta(kayma: int, son_tarih: date) -> Donem:
        bas = bu_pzt + timedelta(days=7 * kayma)
        return Donem(
            baslangic_tarihi=bas,
            bitis_tarihi=bas + timedelta(days=6),
            tercih_son_tarihi=son_tarih,
        )

    gecmis = [
        # Kapali pencere: donem baslamadan bir hafta once VE her hâlükârda
        # bugunden once.
        hafta(-k, min(bu_pzt - timedelta(days=7 * k + 7), dun))
        for k in range(_GECMIS_HAFTA_SAYISI, 0, -1)
    ]
    donemler = DemoDonemleri(
        gecmis=tuple(gecmis),
        guncel=hafta(0, dun),
        gelecek=hafta(1, bu_pzt + timedelta(days=6)),
        sikisik=hafta(2, bu_pzt + timedelta(days=13)),
    )
    oturum.add_all(donemler.hepsi)
    oturum.flush()
    return donemler


# --- Girdi verisi ----------------------------------------------------------


def _aktif_mi(personel: Personel, gun: date) -> bool:
    if personel.aktif_baslangic > gun:
        return False
    return personel.aktif_bitis is None or personel.aktif_bitis >= gun


def _izin_yaz(
    oturum: Session,
    rng: random.Random,
    personel: Personel,
    donem: Donem,
    *,
    tam_hafta: bool = False,
) -> None:
    """Bir personele bir donem icinde tek izin kaydi yazar."""
    tip = rng.choice(_IZIN_TIPLERI)
    if tam_hafta:
        bas, bitis = donem.baslangic_tarihi, donem.bitis_tarihi
        dilim = MusaitlikDilimi.TAM_GUN
    elif rng.random() < _YARIM_GUN_PAYI:
        gun = donem.baslangic_tarihi + timedelta(days=rng.randrange(7))
        bas = bitis = gun
        dilim = rng.choice((MusaitlikDilimi.OGLEDEN_ONCE, MusaitlikDilimi.OGLEDEN_SONRA))
    else:
        uzunluk = rng.randint(1, 4)
        basla = rng.randrange(0, 7 - uzunluk + 1)
        bas = donem.baslangic_tarihi + timedelta(days=basla)
        bitis = bas + timedelta(days=uzunluk - 1)
        dilim = MusaitlikDilimi.TAM_GUN
    oturum.add(
        Musaitlik(
            personel_id=personel.personel_id,
            baslangic_tarihi=bas,
            bitis_tarihi=bitis,
            dilim=dilim,
            tip=tip,
            not_=_IZIN_NOTLARI[tip],
        )
    )


def _izinleri_olustur(
    oturum: Session,
    rng: random.Random,
    personeller: list[Personel],
    donemler: DemoDonemleri,
) -> None:
    """Musaitlik dagilimi (Demo Senaryosu 5.1).

    Her donemde kadronun %8-12'si izinlidir; iki gecmis donem izin dalgasi
    tasir (dortte bir). Sikisik taslak (D+2) kendi kurgusuyla doldurulur.

    IZIN VERILEN KISI O DONEMDE AKTIF OLMALIDIR: ayrilmis bir personele
    ayrildiktan sonraki bir hafta icin izin yazmak, hicbir kurala takilmayan
    ama veriyi anlamsizlastiran bir kayit uretirdi.
    """
    sefler = [p for p in personeller if VARDIYA_SEFI in {y.ad for y in p.yetkinlikler}]
    sef_idleri = {p.personel_id for p in sefler}
    guvenlik = [p for p in personeller if p.personel_id not in sef_idleri]
    kadro = len(personeller)

    for indis, donem in enumerate(donemler.gecmis):
        dalga = indis in _DALGA_DONEM_INDISLERI
        sayi = (
            round(kadro * _DALGA_ORANI)
            if dalga
            else rng.randint(round(kadro * _IZIN_ORANI_ALT), round(kadro * _IZIN_ORANI_UST))
        )
        uygun_sef = [p for p in sefler if _aktif_mi(p, donem.baslangic_tarihi)]
        uygun_guvenlik = [p for p in guvenlik if _aktif_mi(p, donem.baslangic_tarihi)]
        secilen_sef = rng.sample(uygun_sef, min(_GECMISTE_AZAMI_IZINLI_SEF, len(uygun_sef), sayi))
        kalan = max(0, sayi - len(secilen_sef))
        secilen = secilen_sef + rng.sample(uygun_guvenlik, min(kalan, len(uygun_guvenlik)))
        for personel in secilen:
            _izin_yaz(oturum, rng, personel, donem, tam_hafta=dalga)

    for donem in (donemler.guncel, donemler.gelecek):
        sayi = rng.randint(round(kadro * _IZIN_ORANI_ALT), round(kadro * _IZIN_ORANI_UST))
        uygun = [p for p in personeller if _aktif_mi(p, donem.baslangic_tarihi)]
        for personel in rng.sample(uygun, min(sayi, len(uygun))):
            _izin_yaz(oturum, rng, personel, donem)

    # SIKISIK TASLAK. Sef havuzu bilerek daraltilir; acik buradan dogar.
    for personel in sefler[:_SIKISIK_IZINLI_SEF]:
        oturum.add(
            Musaitlik(
                personel_id=personel.personel_id,
                baslangic_tarihi=donemler.sikisik.baslangic_tarihi,
                bitis_tarihi=donemler.sikisik.bitis_tarihi,
                dilim=MusaitlikDilimi.TAM_GUN,
                tip=MusaitlikTipi.YILLIK_IZIN,
                not_="Yıllık izin",
            )
        )
    for personel in rng.sample(guvenlik, _SIKISIK_IZINLI_GUVENLIK):
        _izin_yaz(oturum, rng, personel, donemler.sikisik, tam_hafta=True)
    oturum.flush()


def _tercihleri_olustur(
    oturum: Session,
    rng: random.Random,
    personeller: list[Personel],
    donemler: DemoDonemleri,
) -> int:
    """Yaklasik yirmi bes tercih kaydi (Demo Senaryosu 5.2).

    AYNI PERSONELE AYNI GUN IKINCI TERCIH YAZILMAZ (FR-9.6): kayit
    (personel_id, tarih) ikilisiyle tekildir ve veritabani da bunu
    `uq_tercih_personel_tarih` ile zorlar. Ikilik burada ONLENIR, hataya
    birakilmaz - istisna yakalamak, kac kayit yazildigini belirsiz kilardi.
    """
    yazilan = 0
    kullanilan: set[tuple[int, date]] = set()
    for donem, adet in (
        (donemler.guncel, _TERCIH_SAYISI["guncel"]),
        (donemler.gelecek, _TERCIH_SAYISI["gelecek"]),
    ):
        uygun = [p for p in personeller if _aktif_mi(p, donem.baslangic_tarihi)]
        kalan_deneme = 500  # havuz tukenirse sessiz sonsuz dongu olmasin
        donem_yazilan = 0
        while donem_yazilan < adet and kalan_deneme > 0:
            kalan_deneme -= 1
            personel = rng.choice(uygun)
            gun = donem.baslangic_tarihi + timedelta(days=rng.randrange(7))
            if (personel.personel_id, gun) in kullanilan:
                continue
            kullanilan.add((personel.personel_id, gun))

            durum = rng.choice(
                (TercihDurumu.ONAYLANDI, TercihDurumu.BEKLEMEDE, TercihDurumu.REDDEDILDI)
            )
            zaman_araligi = rng.random() < 0.3
            oturum.add(
                Tercih(
                    personel_id=personel.personel_id,
                    donem_id=donem.donem_id,
                    tarih=gun,
                    tip=(
                        TercihTipi.ZAMAN_ARALIGI_TERCIHI if zaman_araligi else TercihTipi.CALISMAMA
                    ),
                    tercih_baslangic=time(8, 0) if zaman_araligi else None,
                    tercih_bitis=time(16, 0) if zaman_araligi else None,
                    durum=durum,
                    calisan_notu=(rng.choice(_CALISAN_NOTLARI) if rng.random() < 0.7 else None),
                    ret_gerekcesi=(
                        rng.choice(_RET_GEREKCELERI) if durum is TercihDurumu.REDDEDILDI else None
                    ),
                )
            )
            donem_yazilan += 1
            yazilan += 1
    oturum.flush()
    return yazilan


# --- Ornek belge -----------------------------------------------------------

# BELGE BEKLENEN TIPLER: rapor ve mazeret. Yillik izin ve egitim icin belge
# istenmesi olagan degil; demo veriyi gercekci tutmak, ekrani gercekte
# olmayacak bir durumla doldurmamak demek. Digerleri BOS BIRAKILIR ki
# arayuzdeki iki hal de (belge var / belge yok) gorulebilsin.
_BELGELI_TIPLER = (MusaitlikTipi.RAPOR, MusaitlikTipi.MAZERET)
_BELGE_EKLENEN_IZIN_SAYISI = 3


def _ornek_belgeleri_ekle(oturum: Session) -> int:
    """Rapor/mazeret tipindeki ilk birkac izne ornek belge ekler.

    Belge dosyasi yoksa uretim DURMAZ, ama sessiz de gecmez: ornek goruntu
    depoda bulunmayabilir (uretilmediyse).
    """
    kaynak = (
        Path(__file__).resolve().parents[1] / "app" / "ornek_belgeler" / "doktor_raporu_sablonu.png"
    )
    if not kaynak.exists():
        print("UYARI: ornek belge bulunamadi, izinlere belge eklenmedi.", file=sys.stderr)
        return 0
    icerik = kaynak.read_bytes()
    izinler = (
        oturum.execute(
            select(Musaitlik)
            .where(Musaitlik.tip.in_(_BELGELI_TIPLER))
            .order_by(Musaitlik.musaitlik_id)
            .limit(_BELGE_EKLENEN_IZIN_SAYISI)
        )
        .scalars()
        .all()
    )
    for izin in izinler:
        # Belge artik AYRI TABLODA DEGIL satirin icinde (SDD 4.2.1).
        izin.belge_adi = kaynak.name
        izin.belge_tipi = "image/png"
        izin.belge_boyut = len(icerik)
        izin.belge_icerik = icerik
    return len(izinler)


# --- Cizelgeler ------------------------------------------------------------


def _donemi_coz(oturum: Session, donem: Donem, *, zaman_limiti: int, etiket: str) -> int | None:
    """Donemi GERCEK cozucuyle cozer ve surum kimligini dondurur.

    Neden gercek cozucu (Demo Senaryosu 2.5): elle uydurulmus bir cizelge
    kural ihlali tasiyabilir ve Cizelge ekraninda ihlal isaretleriyle
    acilirdi; ayrica ceza dokumu, kapsama acigi ve cozum isi kaydi gibi
    ekranlarin okudugu her sey ancak cozucuden gercek degerlerle dolar.
    """
    servis = CozumServisi(oturum)
    is_kaydi = servis.baslat(donem.donem_id, zaman_limiti_saniye=zaman_limiti)
    if is_kaydi is None:
        print(f"  {etiket}: is acilamadi", flush=True)
        return None
    cozum_isini_calistir(oturum, is_kaydi.is_id)
    yenilenen = oturum.get(CozumIsi, is_kaydi.is_id)
    durum = yenilenen.durum.value if yenilenen else "?"
    print(f"  {etiket}: {durum}", flush=True)
    return is_kaydi.surum_id


def _bir_atamayi_kilitle(oturum: Session, surum_id: int) -> bool:
    """Surumdeki ilk atamayi kilitler (Demo Senaryosu 8, "Cizelge (gun)").

    Kilitli atama, "elle basla, cozucuye devret" yolunun tek gorunur izidir;
    hicbir demo surumunde kilit yoksa o yolun calistigi ekranda okunamaz.
    """
    atama = (
        oturum.execute(
            select(Atama)
            .where(Atama.surum_id == surum_id)
            .order_by(Atama.baslangic_zamani)
            .limit(1)
        )
        .scalars()
        .first()
    )
    if atama is None:
        return False
    atama.kilitli = True
    oturum.flush()
    return True


def _elle_degistir(oturum: Session, surum_id: int, rng: random.Random) -> int:
    """Bir taslakta birkac blogu BASKA bir uygun personele tasir.

    Silmek yerine TASIMAK: silinen blok kapsama acigi uretir ve surum
    karsilastirmasinda "yonetici bir vardiyayi kaldirdi" gibi okunur, oysa
    gostermek istedigimiz sey olagan bir elle duzeltme - bir vardiyanin el
    degistirmesi.

    Alici, o gun VE komsu gunlerde HIC atamasi olmayan, noktanin on kosul
    yetkinligini tasiyan ve o gun aktif olan biri secilir; boylece H1 (gunde
    tek kesintisiz blok), H2 (asgari dinlenme) ve H8 (on kosul) elle
    degisiklikle kirilmaz.
    """
    depo = AtamaDeposu(oturum)
    atamalar = list(depo.surume_gore_getir(surum_id))
    if not atamalar:
        return 0

    noktalar = {n.nokta_id: n for n in oturum.execute(select(GorevNoktasi)).scalars().all()}
    personeller = list(oturum.execute(select(Personel)).scalars().all())
    yetkinlikleri = {p.personel_id: {y.yetkinlik_id for y in p.yetkinlikler} for p in personeller}

    # Kim hangi gun calisiyor - bir gunde ikinci blok acmamak icin.
    dolu_gunler: dict[int, set[date]] = {}
    for atama in atamalar:
        dolu_gunler.setdefault(atama.personel_id, set()).add(atama.baslangic_zamani.date())

    degisen = 0
    for atama in rng.sample(atamalar, min(3, len(atamalar))):
        gun = atama.baslangic_zamani.date()
        onkosul = noktalar[atama.nokta_id].onkosul_yetkinlik_id
        adaylar = [
            p
            for p in personeller
            if p.personel_id != atama.personel_id
            and _aktif_mi(p, gun)
            and (onkosul is None or onkosul in yetkinlikleri[p.personel_id])
            and not (
                dolu_gunler.get(p.personel_id, set())
                & {gun - timedelta(days=1), gun, gun + timedelta(days=1)}
            )
        ]
        if not adaylar:
            continue
        alici = rng.choice(adaylar)
        dolu_gunler.setdefault(alici.personel_id, set()).add(gun)
        dolu_gunler[atama.personel_id].discard(gun)
        atama.personel_id = alici.personel_id
        atama.kaynak = AtamaKaynagi.MANUEL
        degisen += 1
    oturum.flush()
    return degisen


def _cizelgeleri_uret(oturum: Session, donemler: DemoDonemleri, rng: random.Random) -> None:
    """Donemleri cozer ve sonuclari Demo Senaryosu 6'daki durumlara dagitir.

    Gecmis on iki hafta ve D0 YAYINLANIR: adalet sayaclari (S2/S3/S4),
    kumulatif ufuk ve calisan panelinin gecmisi ancak yayinlanmis bir
    gecmisle dolar.

    D+1 IKI SURUM tasir. Birincisi cozucu ciktisidir; ikincisi onun taslak
    kopyasi uzerinde birkac elle degisiklik tasir. Surumler ve Karsilastir
    ekranlari bu ikisiyle dolar - okunabilir bir fark ancak boyle olusur.

    D+2 cozulur ama YAYINLANMAZ: acigi olan bir cizelge yayinlanmadan once
    incelenir, ve Surumler ekraninin "cozuldu" durumu da ancak boyle
    gorunur.
    """
    surum_depo = CizelgeSurumuDeposu(oturum)
    limit = _COZUM_ZAMAN_LIMITI_SANIYE

    for indis, donem in enumerate(donemler.gecmis):
        etiket = f"D-{_GECMIS_HAFTA_SAYISI - indis}"
        surum = _donemi_coz(oturum, donem, zaman_limiti=limit, etiket=etiket)
        if surum is not None:
            surum_depo.yayinla(surum)
        oturum.commit()

    guncel_surum = _donemi_coz(oturum, donemler.guncel, zaman_limiti=limit, etiket="D0")
    if guncel_surum is not None:
        _bir_atamayi_kilitle(oturum, guncel_surum)
        surum_depo.yayinla(guncel_surum)
    oturum.commit()

    gelecek_surum = _donemi_coz(
        oturum, donemler.gelecek, zaman_limiti=limit, etiket="D+1 (1. sürüm)"
    )
    if gelecek_surum is not None:
        kopya = SurumServisi(oturum).taslak_olarak_kopyala(gelecek_surum)
        if kopya is not None:
            degisen = _elle_degistir(oturum, kopya.surum_id, rng)
            kilitli = _bir_atamayi_kilitle(oturum, kopya.surum_id)
            print(
                f"  D+1 (2. sürüm): {degisen} atama elle taşındı, "
                f"{'1' if kilitli else '0'} atama kilitli",
                flush=True,
            )
    oturum.commit()

    _donemi_coz(oturum, donemler.sikisik, zaman_limiti=limit, etiket="D+2 (sıkışık)")
    oturum.commit()


# --- Hesaplar --------------------------------------------------------------


def _hesaplari_kur(oturum: Session, parola: str) -> int:
    """Demo hesaplarini acar/tazeler (Demo Senaryosu 7).

    IDEMPOTENT: var olan hesabin parolasi tazelenir, olmayan acilir.
    --reset personel kaydina bagli hesaplari siler (yabanci anahtar) ama
    yonetim hesaplarina dokunmaz; ikisi tek yoldan gecmezse ikinci kosum
    `kullanici_adi` tekilligine carpardi.

    `parola_degistirmeli` FALSE: gercek kurulumda ilk giriste parola
    degistirilir (FR-10.7), ama gosterim hesabinin parolasi zaten dagitilan
    bir parolaydir ve her gece sifirlanir; zorunlu degistirme demoyu ilk
    girisin ardindan kullanilamaz hale getirirdi.
    """
    servis = KullaniciServisi(oturum)
    mevcut = {k.kullanici_adi: k for k in oturum.execute(select(Kullanici)).scalars().all()}

    hedefler: list[tuple[str, Rol, int | None]] = [
        (ad, rol, None) for ad, rol in _YONETIM_HESAPLARI
    ]
    for sicil_no in _CALISAN_HESABI_SICILLERI:
        personel = oturum.execute(
            select(Personel).where(Personel.sicil_no == sicil_no)
        ).scalar_one_or_none()
        if personel is None:
            print(f"UYARI: {sicil_no} bulunamadi, calisan hesabi acilmadi.", file=sys.stderr)
            continue
        kullanici_adi = f"demo_{sicil_no.lower().replace('-', '')}"
        hedefler.append((kullanici_adi, Rol.CALISAN, personel.personel_id))

    for kullanici_adi, rol, personel_id in hedefler:
        kullanici = mevcut.get(kullanici_adi)
        if kullanici is None:
            kullanici = servis.olustur(kullanici_adi, parola, rol, personel_id)
        else:
            kullanici.parola_ozeti = parola_araclari.ozetle(parola)
            kullanici.rol = rol
            kullanici.personel_id = personel_id
            kullanici.aktif = True
        kullanici.parola_degistirmeli = False
    oturum.flush()
    return len(hedefler)


# --- Ana akis --------------------------------------------------------------


def uret(*, sifirla: bool, coz: bool = True) -> None:
    oturum = OturumYerel()
    temizlik: TemizlikSonucu | None = None
    bugun = date.today()
    rng = random.Random(_SABIT_TOHUM)
    parola = ayarlar.demo_parola
    try:
        if not sifirla and _mevcut_demo_verisi_var_mi(oturum):
            print(
                "Demo verisi zaten mevcut. Yeniden uretmek icin --reset kullanin.",
                file=sys.stderr,
            )
            sys.exit(1)
        if sifirla:
            # KOSULSUZ temizlik. Eskiden yalnizca demo verisi bulunuyorsa
            # temizleniyordu; oysa temizlik zaten o tablolarin TUMUNU siler.
            # Sonuc: demo disi artiklar (test fiksturleri, olcum verisi)
            # bulunan bir veritabaninda --reset sessizce hicbir sey silmiyor
            # ve uretec artiklarin USTUNE ekliyordu.
            temizlik = _her_seyi_temizle(oturum)

        _binalari_olustur(oturum)
        yetkinlikler = _yetkinlikleri_olustur(oturum)
        noktalar = _noktalari_olustur(oturum, yetkinlikler)
        _talebi_olustur(oturum, noktalar)
        _kurallari_olustur(oturum)
        personeller = _personeli_olustur(oturum, yetkinlikler, bugun)
        donemler = _donemleri_olustur(oturum, bugun)
        _ozel_gunleri_olustur(
            oturum, (donemler.hepsi[0].baslangic_tarihi, donemler.hepsi[-1].bitis_tarihi)
        )
        _izinleri_olustur(oturum, rng, personeller, donemler)
        tercih_sayisi = _tercihleri_olustur(oturum, rng, personeller, donemler)
        oturum.flush()
        belgeli_izin = _ornek_belgeleri_ekle(oturum)
        hesap_sayisi = _hesaplari_kur(oturum, parola) if parola else 0
        oturum.commit()

        if coz:
            print("Cizelgeler uretiliyor (gercek cozucu):", flush=True)
            _cizelgeleri_uret(oturum, donemler, rng)
    except Exception:
        oturum.rollback()
        raise
    finally:
        oturum.close()

    toplam_personel = sum(grup.sayi for grup in PERSONEL_GRUPLARI)
    print(
        f"Demo verisi uretildi: {toplam_personel} personel "
        f"({len(_KISMI_ZAMANLI_SICILLER)} kismi zamanli, 1 ayrilmis, 1 yeni baslayan), "
        f"{len(_BINA_ADLARI)} bina, {len(NOKTA_TANIMLARI)} gorev noktasi, "
        f"{len(KURAL_TANIMLARI)} kural, {tercih_sayisi} tercih, "
        f"{_GECMIS_HAFTA_SAYISI} gecmis + 1 guncel + {_GELECEK_HAFTA_SAYISI} gelecek donem."
    )
    print(f"Ornek belge eklenen izin kaydi: {belgeli_izin}")
    if parola:
        print(f"Demo hesabi: {hesap_sayisi} adet; parola {_PAROLA_DEGISKENI} degiskeninden okundu.")
    else:
        print(
            f"HESAP ACILMADI: {_PAROLA_DEGISKENI} ortam degiskeni verilmedi. "
            f"Parola koda ve depoya yazilmaz (Demo Senaryosu 7).",
            file=sys.stderr,
        )
    # Silinen hesap SESSIZ kalmamali: silinen sey bir kullanicinin sisteme
    # girisidir, gecmis dondugunde geri gelmez.
    if temizlik is not None and temizlik.silinen_hesap:
        print(
            f"NOT: personel kaydina bagli {temizlik.silinen_hesap} hesap "
            f"({temizlik.silinen_oturum} acik oturum) silindi; demo hesaplari "
            f"yeniden acildi, digerleri Kullanicilar ekranindan acilmalidir.",
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
            "On bes donemin cozumu birkac dakika surer; yalnizca tanim "
            "ekranlarina bakilacaksa bu bayrakla atlanabilir."
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
