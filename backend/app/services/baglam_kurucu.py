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
)
from app.models.girdi import Musaitlik, Tercih, TercihDurumu
from app.models.kural import Kural
from app.models.sonuc import Donem
from app.models.tanim import GorevNoktasi, OzelGun, Personel, Talep, Yetkinlik
from app.services.gecmis_sayaclar import ADALET_UFKU_GUN, GecmisSayaclar
from app.services.talep_cozucu import talebi_saate_ac


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


# H10 kayitli degilse kuralin kendi varsayilaniyla ayni deger kullanilir.
_VARSAYILAN_FAZLA_CALISMA_ESIGI = 45.0


def _h10_esigi(oturum: Session) -> float:
    satir = oturum.execute(select(Kural).where(Kural.kimlik == "H10")).scalars().first()
    if satir is None or not satir.parametreler:
        return _VARSAYILAN_FAZLA_CALISMA_ESIGI
    return float(satir.parametreler.get("fazla_calisma_esigi", _VARSAYILAN_FAZLA_CALISMA_ESIGI))


def baglam_olustur(
    oturum: Session,
    donem: Donem,
    *,
    isitma_penceresi_gun: int = 7,
    yalniz_aktif: bool = True,
    adalet_ufku_gun: int = ADALET_UFKU_GUN,
) -> Baglam:
    """Donem icin Baglam'i kurar.

    Talep, isitma penceresini de kapsayan tam zaman ekseni icin cozulur
    (model_kur'un karar degiskeni uretimi zaman_ekseni'nin tamami uzerinde
    calisir); donem_baslangic/donem_bitis ise yalnizca donemi isaretler
    (TD-6: adalet sayaclari isitma penceresini kapsamaz).

    adalet_ufku_gun (SRS TD-6): donem oncesi birikimin kapsandigi kayan
    pencere. Sifir verildiginde gecmis hic okunmaz ve olcu yalniz donemi
    kapsar - gecmisi olmayan kurulumda ve gecmisten bagimsiz sinanmak
    isteyen testlerde dogru olan davranis budur.

    yalniz_aktif (madde 1): pasiflestirilmis tanimlarin ("yeni cozumlerde
    kullanilmaz, mevcut kayitlarda gorunmeye devam eder") ele alinisi.
    Cozum ve on kontrol yollari True verir; MEVCUT bir surumu okuyan
    analiz ve dogrulama yollari False verir, cunku o surumun atamalari
    pasiflestirmeden onceki tanimlara referans verebilir ve tanim
    kumeden dusurulurse atama sessizce sayilmaz hale gelir.
    """
    nokta_sorgusu = select(GorevNoktasi)
    if yalniz_aktif:
        nokta_sorgusu = nokta_sorgusu.where(GorevNoktasi.aktif.is_(True))

    gorev_noktalari = {
        n.nokta_id: GorevNoktasiBilgisi(n.nokta_id, n.onkosul_yetkinlik_id, n.bina_id, ad=n.ad)
        for n in oturum.execute(nokta_sorgusu).scalars().all()
    }
    personel_satirlari = oturum.execute(select(Personel)).scalars().all()
    personel = {
        p.personel_id: PersonelBilgisi(
            p.personel_id,
            p.aktif_baslangic,
            p.aktif_bitis,
            frozenset(y.yetkinlik_id for y in p.yetkinlikler),
            haftalik_hedef_saat=float(p.haftalik_hedef_saat),
            # H10'un `devir[p]`i (TD-6). Bu turda TEK KAYNAK personel
            # kaydidir; yayinlanmis surumlerden turetme Tur 5'te eklenip
            # buna EKLENECEK, yerine gecmeyecek.
            devir_fazla_calisma_saat=float(p.devir_fazla_calisma_saat),
        )
        for p in personel_satirlari
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
        TercihKaydi(t.personel_id, t.tarih, t.tip, t.tercih_baslangic, t.tercih_bitis)
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
    # Saat ekseni TEK KAYNAK (SDD 5.3): talep, kapsama kisiti, adil pay ve
    # analiz ayni acilimdan besleniyor.
    talep_saat = talebi_saate_ac(talep_satirlari, zaman_ekseni, ozel_gunler)

    # GECMIS EN SONA BIRAKILIR: adil pay katkisi `erisebilen` kumelerine
    # dayanir, o da yetkinlik ve nokta tanimlarindan kurulur. Once gecici
    # bir baglam kurulup erisim kumeleri ondan okunur; tanimin ikinci bir
    # kopyasini cikarmak yerine mevcut `erisebilen`i kullanmis oluruz.
    taban = Baglam(
        gorev_noktalari=gorev_noktalari,
        # Eksen BURADA da doldurulur, yalniz model_kur'da degil: dogrula
        # yolundaki kurallar (S8) mutlak saat indeksini baglamdan okur ve
        # eksen bos oldugunda `saat_indeksi` sessizce None dondururdu -
        # bulgular hic uretilmeden kaybolurdu.
        zaman_ekseni=zaman_ekseni,
        personel=personel,
        musaitlik=musaitlik,
        talep_saat=talep_saat,
        donem_baslangic=donem.baslangic_tarihi,
        donem_bitis=donem.bitis_tarihi,
        ozel_gunler=ozel_gunler,
        personel_adlari={p.personel_id: p.ad_soyad for p in personel_satirlari},
        yetkinlik_adlari=yetkinlik_adlari,
        tercihler=tercihler,
    )
    if adalet_ufku_gun <= 0:
        return taban
    erisebilen = {n: taban.erisebilen(n) for n in gorev_noktalari}
    taban.gecmis = GecmisSayaclar(oturum).hesapla(donem, adalet_ufku_gun, erisebilen=erisebilen)
    return taban
