"""Veritabani satirlarindan bir Donem icin Baglam kurar.

Ornek Kural.dogrula/modele_ekle cagrilari icin elle kurulan Baglam'larin
(Sprint 1-2 testleri) aksine, bu modul gercek tanim/girdi verisini okuyup
kural motorunun (app.kurallar) ihtiyac duydugu DB'den bagimsiz yapiya
cevirir. Repository/servis katmani disina SQL sizdirmama ilkesiyle
tutarli olarak, cagiran taraf (ör. on_kontrol/cozum servisleri) oturumu
sagliyor; bu fonksiyon yalnizca okuma yapar.
"""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.kurallar.baglam import (
    Baglam,
    GorevNoktasiBilgisi,
    MusaitlikKaydi,
    PersonelBilgisi,
    TercihKaydi,
    VardiyaTipiBilgisi,
)
from app.models.girdi import Musaitlik, Tercih, TercihDurumu
from app.models.sonuc import Donem
from app.models.tanim import GorevNoktasi, OzelGun, Personel, Talep, VardiyaTipi, Yetkinlik
from app.services.talep_cozucu import blok_gorunumu_uret, talebi_saate_ac


def donem_gunlerini_uret(baslangic: date, bitis: date) -> list[date]:
    gun_sayisi = (bitis - baslangic).days + 1
    return [baslangic + timedelta(days=i) for i in range(gun_sayisi)]


def zaman_ekseni_olustur(donem: Donem, *, isitma_penceresi_gun: int = 7) -> list[date]:
    """TD-5: isitma penceresi (donemden hemen once, varsayilan 7 gun) + donem gunleri,
    ardisik takvim gunlerinden olusan tek bir liste olarak."""
    isitma_baslangic = donem.baslangic_tarihi - timedelta(days=isitma_penceresi_gun)
    isitma_bitis = donem.baslangic_tarihi - timedelta(days=1)
    isitma_gunleri = (
        donem_gunlerini_uret(isitma_baslangic, isitma_bitis) if isitma_penceresi_gun > 0 else []
    )
    return isitma_gunleri + donem_gunlerini_uret(donem.baslangic_tarihi, donem.bitis_tarihi)


def baglam_olustur(
    oturum: Session,
    donem: Donem,
    *,
    isitma_penceresi_gun: int = 7,
    yalniz_aktif: bool = True,
) -> Baglam:
    """Donem icin Baglam'i kurar.

    Talep, isitma penceresini de kapsayan tam zaman ekseni icin cozulur
    (model_kur'un karar degiskeni uretimi zaman_ekseni'nin tamami uzerinde
    calisir); donem_baslangic/donem_bitis ise yalnizca donemi isaretler
    (TD-6: adalet sayaclari isitma penceresini kapsamaz).

    yalniz_aktif (madde 1): pasiflestirilmis tanimlarin ("yeni cozumlerde
    kullanilmaz, mevcut kayitlarda gorunmeye devam eder") ele alinisi.
    Cozum ve on kontrol yollari True verir; MEVCUT bir surumu okuyan
    analiz ve dogrulama yollari False verir, cunku o surumun atamalari
    pasiflestirmeden onceki tanimlara referans verebilir ve tanim
    kumeden dusurulurse atama sessizce sayilmaz hale gelir.

    Pasif bir vardiya tipi icin karar degiskeni uretilmez; isitma
    penceresindeki veya kilitli atamalar arasinda o tipe ait bir kayit
    varsa model_kur onu zaten sessizce atlar (talebin sifira dusmesi
    durumuyla ayni yol).
    """
    vardiya_sorgusu = select(VardiyaTipi)
    nokta_sorgusu = select(GorevNoktasi)
    if yalniz_aktif:
        vardiya_sorgusu = vardiya_sorgusu.where(VardiyaTipi.aktif.is_(True))
        nokta_sorgusu = nokta_sorgusu.where(GorevNoktasi.aktif.is_(True))

    vardiya_tipleri = {
        v.vardiya_tipi_id: VardiyaTipiBilgisi(
            v.vardiya_tipi_id,
            v.baslangic_saati,
            v.bitis_saati,
            float(v.sure_saat),
            v.gece_mi,
            ad=v.ad,
        )
        for v in oturum.execute(vardiya_sorgusu).scalars().all()
    }
    gorev_noktalari = {
        n.nokta_id: GorevNoktasiBilgisi(n.nokta_id, n.onkosul_yetkinlik_id, n.bina_id, ad=n.ad)
        for n in oturum.execute(nokta_sorgusu).scalars().all()
    }
    personel = {
        p.personel_id: PersonelBilgisi(
            p.personel_id,
            p.aktif_baslangic,
            p.aktif_bitis,
            frozenset(y.yetkinlik_id for y in p.yetkinlikler),
            haftalik_hedef_saat=float(p.haftalik_hedef_saat),
        )
        for p in oturum.execute(select(Personel)).scalars().all()
    }
    # Bulgu metinleri kimlik degil AD tasir (SRS FR-5.6).
    yetkinlik_adlari = {
        y.yetkinlik_id: y.ad for y in oturum.execute(select(Yetkinlik)).scalars().all()
    }
    musaitlik = [
        MusaitlikKaydi(m.personel_id, m.baslangic_tarihi, m.bitis_tarihi, m.dilim)
        for m in oturum.execute(select(Musaitlik)).scalars().all()
    ]
    tercihler = [
        TercihKaydi(t.personel_id, t.tarih, t.tip, t.vardiya_tipi_id)
        for t in oturum.execute(
            select(Tercih).where(
                Tercih.durum == TercihDurumu.ONAYLANDI,
                Tercih.donem_id == donem.donem_id,
            )
        )
        .scalars()
        .all()
    ]
    ozel_gunler = frozenset(
        og.tarih
        for og in oturum.execute(
            select(OzelGun).where(
                OzelGun.tarih >= donem.baslangic_tarihi, OzelGun.tarih <= donem.bitis_tarihi
            )
        )
        .scalars()
        .all()
    )

    zaman_ekseni = zaman_ekseni_olustur(donem, isitma_penceresi_gun=isitma_penceresi_gun)
    talep_satirlari = oturum.execute(select(Talep)).scalars().all()
    # Saat ekseni TEK KAYNAK (SDD 5.3); blok gorunumu ondan turetilir.
    talep_saat = talebi_saate_ac(talep_satirlari, zaman_ekseni, ozel_gunler)
    talep = blok_gorunumu_uret(talep_saat, vardiya_tipleri)

    return Baglam(
        vardiya_tipleri=vardiya_tipleri,
        gorev_noktalari=gorev_noktalari,
        personel=personel,
        musaitlik=musaitlik,
        talep_saat=talep_saat,
        talep=talep,
        donem_baslangic=donem.baslangic_tarihi,
        donem_bitis=donem.bitis_tarihi,
        ozel_gunler=ozel_gunler,
        yetkinlik_adlari=yetkinlik_adlari,
        tercihler=tercihler,
    )
