"""Veritabani satirlarindan bir Donem icin Baglam kurar.

Ornek Kural.dogrula/modele_ekle cagrilari icin elle kurulan Baglam'larin
(Sprint 1-2 testleri) aksine, bu modul gercek tanim/girdi verisini okuyup
kural motorunun (app.kurallar) ihtiyac duydugu DB'den bagimsiz yapiya
cevirir. Repository/servis katmani disina SQL sizdirmama ilkesiyle
tutarli olarak, cagiran taraf (ör. on_kontrol/cozum servisleri) oturumu
sagliyor; bu fonksiyon yalnizca okuma yapar.

Not: SDD 5.2'deki on_kontrol(donem, tanimlar, musaitlikler) isitma
penceresi almaz; bu yuzden burada yalnizca donem gunleri icin talep
cozulur. Isitma penceresini de kapsayan zaman_ekseni, cozum isini
yurutecek modul tarafindan (Sprint 2 Gun 8) ayrica kurulacak.
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
from app.models.tanim import GorevNoktasi, OzelGun, Personel, Talep, VardiyaTipi
from app.services.talep_cozucu import talep_matrisini_coz


def donem_gunlerini_uret(baslangic: date, bitis: date) -> list[date]:
    gun_sayisi = (bitis - baslangic).days + 1
    return [baslangic + timedelta(days=i) for i in range(gun_sayisi)]


def baglam_olustur(oturum: Session, donem: Donem) -> Baglam:
    """Donem icin Baglam'i kurar (talep yalniz donem gunleri icin cozulur)."""
    vardiya_tipleri = {
        v.vardiya_tipi_id: VardiyaTipiBilgisi(
            v.vardiya_tipi_id, v.baslangic_saati, v.bitis_saati, float(v.sure_saat), v.gece_mi
        )
        for v in oturum.execute(select(VardiyaTipi)).scalars().all()
    }
    gorev_noktalari = {
        n.nokta_id: GorevNoktasiBilgisi(n.nokta_id, n.onkosul_yetkinlik_id, n.bina_id)
        for n in oturum.execute(select(GorevNoktasi).where(GorevNoktasi.aktif.is_(True)))
        .scalars()
        .all()
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

    donem_gunleri = donem_gunlerini_uret(donem.baslangic_tarihi, donem.bitis_tarihi)
    talep_satirlari = oturum.execute(select(Talep)).scalars().all()
    talep = talep_matrisini_coz(talep_satirlari, donem_gunleri, ozel_gunler)

    return Baglam(
        vardiya_tipleri=vardiya_tipleri,
        gorev_noktalari=gorev_noktalari,
        personel=personel,
        musaitlik=musaitlik,
        talep=talep,
        donem_baslangic=donem.baslangic_tarihi,
        donem_bitis=donem.bitis_tarihi,
        ozel_gunler=ozel_gunler,
        tercihler=tercihler,
    )
