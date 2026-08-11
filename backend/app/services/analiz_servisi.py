"""Analiz servisi (SDD 3.2: analiz_router'in kullandigi servis; SDD 5.7'deki
yedi metrigin uygulamasi).

Butun hesaplar yalnizca planlama donemini kapsar, isitma penceresini
kapsamaz (SRS TD-6) - bu, atama satirlarinin `baglam.donem_icinde(tarih)`
ile filtrelenmesiyle saglanir (bkz. baglam_kurucu.baglam_olustur docstring'i:
atama SORGUSU donem disini filtrelemez, ama zaman ekseni ISITMA PENCERESINI
DE kapsadigindan bu filtre burada acikca uygulanmalidir).
"""

from collections import defaultdict
from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.kurallar.baglam import AtamaKaydi
from app.kurallar.esnek import S4_OLCEK, S6bBinaTutarliligi, s4_hedef_paylari_x10
from app.models.girdi import TercihTipi
from app.models.sonuc import Atama
from app.models.tanim import Personel
from app.repositories.sonuc import (
    AtamaDeposu,
    CizelgeSurumuDeposu,
    CozumIsiDeposu,
    DonemDeposu,
    FazlaKadroDeposu,
    KapsamaAcigiDeposu,
)
from app.repositories.tanim import PersonelDeposu
from app.schemas.analiz import AnalizOku, FazlaKadroKalemi, KisiSayisiOku, SaatDengesiOku
from app.services.baglam_kurucu import baglam_olustur


def _ad(bilgi: object) -> str:
    """Baglam nesnesinin gosterim adi; yoksa bos yerine anlasilir bir metin."""
    ad = getattr(bilgi, "ad", "") or ""
    return ad if ad else "—"


class AnalizServisi:
    def __init__(self, oturum: Session) -> None:
        self.oturum = oturum
        self.surum = CizelgeSurumuDeposu(oturum)
        self.donem = DonemDeposu(oturum)
        self.atama = AtamaDeposu(oturum)
        self.kapsama = KapsamaAcigiDeposu(oturum)
        self.fazla_kadro = FazlaKadroDeposu(oturum)
        self.cozum_isi = CozumIsiDeposu(oturum)
        self.personel = PersonelDeposu(oturum)

    def hesapla(self, surum_id: int) -> AnalizOku | None:
        surum = self.surum.getir(surum_id)
        if surum is None:
            return None
        donem = self.donem.getir(surum.donem_id)
        if donem is None:
            return None

        # yalniz_aktif=False: analiz MEVCUT bir surumu okur. Pasiflestirilmis
        # bir vardiya tipi veya noktaya yapilmis gecmis atamalar kumeden
        # dusurulurse kapsama orani ve adalet sayaclari sessizce eksik cikar.
        baglam = baglam_olustur(self.oturum, donem, yalniz_aktif=False)
        donem_gun_sayisi = (donem.bitis_tarihi - donem.baslangic_tarihi).days + 1

        atama_satirlari: Sequence[Atama] = [
            a for a in self.atama.surume_gore_getir(surum_id) if baglam.donem_icinde(a.tarih)
        ]
        atamalar = [
            AtamaKaydi(a.personel_id, a.tarih, a.vardiya_tipi_id, a.nokta_id)
            for a in atama_satirlari
        ]

        personel_satirlari: Sequence[Personel] = self.personel.tumunu_getir()

        # --- Kapsama orani (FR-8.1): karsilanan / toplam talep, kapsama
        # acigi tablosundan turetilir (SDD 5.7). Toplam talep, donem
        # icindeki talep hucrelerinin toplamidir (baglam.talep isitma
        # penceresini de kapsayan zaman ekseni icin cozulur, TD-6 geregi
        # burada donem_icinde filtresi uygulanir).
        toplam_talep = sum(
            gereken
            for (tarih, _vardiya_tipi_id, _nokta_id), gereken in baglam.talep.items()
            if baglam.donem_icinde(tarih)
        )
        toplam_eksik = sum(k.eksik_sayi for k in self.kapsama.surume_gore_getir(surum_id))
        kapsama_orani = (toplam_talep - toplam_eksik) / toplam_talep if toplam_talep > 0 else 1.0

        # --- Fazla kadro (SRS 4.3 S1 ust siniri). Kapsama ORANINA
        # KARISTIRILMAZ: oran "talebin ne kadari karsilandi" sorusunu
        # yanitlar ve fazla kadro o soruya bir sey eklemez - fazla atama
        # bir hucreyi daha iyi kapsamis olmaz. Ayri bir sayi olarak
        # raporlanir; ekranda da ayri durur.
        fazla_satirlari = self.fazla_kadro.surume_gore_getir(surum_id)
        fazla_kadro = [
            FazlaKadroKalemi(
                tarih=f.tarih,
                vardiya_tipi_id=f.vardiya_tipi_id,
                vardiya_tipi_ad=_ad(baglam.vardiya_tipleri.get(f.vardiya_tipi_id)),
                nokta_id=f.nokta_id,
                nokta_ad=_ad(baglam.gorev_noktalari.get(f.nokta_id)),
                fazla_sayi=f.fazla_sayi,
            )
            for f in fazla_satirlari
        ]
        toplam_fazla = sum(f.fazla_sayi for f in fazla_satirlari)

        # --- Kisi basina gece / hafta sonu sayisi (FR-8.2), saat dagilimi
        gece_sayac: dict[int, int] = defaultdict(int)
        hs_sayac: dict[int, int] = defaultdict(int)
        saat_toplam: dict[int, float] = defaultdict(float)
        for a in atamalar:
            if baglam.gece_mi(a.vardiya_tipi_id):
                gece_sayac[a.personel_id] += 1
            if baglam.hafta_sonu_mu(a.tarih):
                hs_sayac[a.personel_id] += 1
            saat_toplam[a.personel_id] += baglam.sure_saat(a.vardiya_tipi_id)

        # SDD 5.7 (surum 1.7): gece ve hafta sonu metrikleri UYGUN HAVUZ
        # (SRS S2/S3'teki P_gece, P_hs) uzerinden raporlanir - yetkinligi
        # geregi o talebin bulundugu hicbir noktada calisamayan personel
        # olcume dahil edilmez, aksi halde kalici olarak ortalamanin altinda
        # gorunur. Havuz tanimi Baglam.uygun_havuz'da tek yerde durur;
        # cozucu, dogrulayici ve Analiz ayni tabani kullanir.
        gece_havuzu = baglam.uygun_havuz(lambda anahtar: baglam.gece_mi(anahtar[1]))
        hs_havuzu = baglam.uygun_havuz(lambda anahtar: baglam.hafta_sonu_mu(anahtar[0]))

        kisi_basina_gece = [
            KisiSayisiOku(
                personel_id=p.personel_id,
                ad_soyad=p.ad_soyad,
                sayi=gece_sayac.get(p.personel_id, 0),
            )
            for p in personel_satirlari
            if p.personel_id in gece_havuzu
        ]
        kisi_basina_hafta_sonu = [
            KisiSayisiOku(
                personel_id=p.personel_id, ad_soyad=p.ad_soyad, sayi=hs_sayac.get(p.personel_id, 0)
            )
            for p in personel_satirlari
            if p.personel_id in hs_havuzu
        ]

        # SDD 5.7 (surum 1.7): saat dagiliminin tabani kisisel SOZLESME saati
        # degil, SRS S4'teki ADIL PAY (pay[p]). Sozlesme saati taban alindiginda
        # H5+H6 kisi basina azami vardiya sayisini sinirladigi icin kadro asgari
        # gereksinimin uzerindeyken hic kimse hedefine ulasamiyor, tablo butun
        # satirlarda ayni yonde sapma gosterip hicbir ayrim uretmiyordu.
        # Hesap S4'un kendi fonksiyonundan gelir - kural iki ayri yerde
        # kodlanmaz (SDD 2.4); S4_OLCEK onda bir saat oldugundan dogal birime
        # geri cevrilir (SDD Ek A, "Kesirli hedeflerin tamsayiya olceklenmesi").
        paylar_x10 = s4_hedef_paylari_x10(baglam, donem_gun_sayisi)
        saat_dagilimi: list[SaatDengesiOku] = []
        for p in personel_satirlari:
            hedef = paylar_x10.get(p.personel_id, 0) / S4_OLCEK
            toplam = saat_toplam.get(p.personel_id, 0.0)
            saat_dagilimi.append(
                SaatDengesiOku(
                    personel_id=p.personel_id,
                    ad_soyad=p.ad_soyad,
                    toplam_saat=toplam,
                    hedef_saat=hedef,
                    sapma=toplam - hedef,
                )
            )

        en_dengesiz = max(saat_dagilimi, key=lambda s: abs(s.sapma), default=None)

        # --- Bina degisim sayisi (S6b'nin dogrula'sinin dogrudan yeniden
        # kullanimi - kural iki ayri yerde kodlanmaz, SDD 2.4).
        bina_ihlalleri = S6bBinaTutarliligi(parametreler={}).dogrula(atamalar, baglam)
        bina_sayac: dict[int, int] = defaultdict(int)
        for ihlal in bina_ihlalleri:
            if ihlal.personel_id is not None:
                bina_sayac[ihlal.personel_id] += 1
        bina_degisim_sayisi = [
            KisiSayisiOku(
                personel_id=p.personel_id,
                ad_soyad=p.ad_soyad,
                sayi=bina_sayac.get(p.personel_id, 0),
            )
            for p in personel_satirlari
            if bina_sayac.get(p.personel_id, 0) > 0
        ]

        # --- Tercih karsilama orani (FR-8.4): baglam.tercihler zaten yalniz
        # bu donemin ONAYLANMIS tercihlerini tasir (bkz. baglam_olustur).
        gunluk_atama = {(a.personel_id, a.tarih): a for a in atamalar}
        karsilanan = 0
        for tercih in baglam.tercihler:
            atama = gunluk_atama.get((tercih.personel_id, tercih.tarih))
            if tercih.tip == TercihTipi.CALISMAMA:
                if atama is None:
                    karsilanan += 1
            elif atama is not None and atama.vardiya_tipi_id == tercih.vardiya_tipi_id:
                karsilanan += 1
        tercih_orani = karsilanan / len(baglam.tercihler) if baglam.tercihler else None

        # --- Ceza dokumu / toplam ceza (FR-8.6, Gun 12 notu: cozum_isi.surum_id
        # iliskisi zaten var, ayri bir router acmadan burada kullaniliyor)
        is_kaydi = self.cozum_isi.surume_gore_en_son(surum_id)
        ceza_dokumu = (
            {k: float(v) for k, v in is_kaydi.ceza_dokumu.items()}
            if is_kaydi is not None and is_kaydi.ceza_dokumu is not None
            else None
        )
        toplam_ceza = (
            float(is_kaydi.en_iyi_ceza)
            if is_kaydi is not None and is_kaydi.en_iyi_ceza is not None
            else None
        )

        return AnalizOku(
            surum_id=surum_id,
            kapsama_orani=kapsama_orani,
            fazla_kadro=fazla_kadro,
            toplam_fazla_kadro=toplam_fazla,
            kisi_basina_gece=kisi_basina_gece,
            kisi_basina_hafta_sonu=kisi_basina_hafta_sonu,
            saat_dagilimi=saat_dagilimi,
            en_dengesiz_personel_id=en_dengesiz.personel_id if en_dengesiz else None,
            en_dengesiz_ad_soyad=en_dengesiz.ad_soyad if en_dengesiz else None,
            tercih_karsilama_orani=tercih_orani,
            bina_degisim_sayisi=bina_degisim_sayisi,
            ceza_dokumu=ceza_dokumu,
            toplam_ceza=toplam_ceza,
        )
