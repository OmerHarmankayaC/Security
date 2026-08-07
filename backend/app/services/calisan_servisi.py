"""Calisan Paneli servisi (SDD 6.1; SRS FR-9.x; Sprint 3 Gun 13).

Bu katmandaki hicbir yazma islemi cizelgeyi etkilemez (SDD 6.1) - tek yazma
yolu tercih_bildir'dir ve yalniz bir Tercih kaydi dogurur.
"""

from datetime import date, time

from sqlalchemy.orm import Session

from app.models.girdi import TercihTipi
from app.models.sonuc import Atama, CizelgeSurumu
from app.repositories.girdi import TercihDeposu
from app.repositories.sonuc import AtamaDeposu, CizelgeSurumuDeposu, DonemDeposu
from app.repositories.tanim import GorevNoktasiDeposu, PersonelDeposu, VardiyaTipiDeposu
from app.schemas.calisan import (
    AcikDonemOku,
    CalisanTercihListesiOku,
    CalisanTercihOku,
    CalisanTercihOlustur,
    DonemOzetiOku,
    VardiyalarimOku,
    VardiyamOku,
)
from app.services.analiz_servisi import AnalizServisi


class TercihDonemiBulunamadiError(Exception):
    """Bildirilmek istenen tarih hicbir donemin icine dusmuyor ya da o
    donemin tercih bildirim penceresi kapanmis (router 400'e cevirir)."""


class CalisanServisi:
    def __init__(self, oturum: Session) -> None:
        self.oturum = oturum
        self.personel = PersonelDeposu(oturum)
        self.donem = DonemDeposu(oturum)
        self.surum = CizelgeSurumuDeposu(oturum)
        self.atama = AtamaDeposu(oturum)
        self.tercih = TercihDeposu(oturum)
        self.vardiya_tipi = VardiyaTipiDeposu(oturum)
        self.nokta = GorevNoktasiDeposu(oturum)

    # --- Vardiyalarim / Donem Ozetim (FR-9.1 - FR-9.5) ----------------------

    def vardiyalarim(
        self, personel_id: int, *, bugun: date | None = None
    ) -> VardiyalarimOku | None:
        personel = self.personel.getir(personel_id)
        if personel is None:
            return None
        bugun = bugun if bugun is not None else date.today()

        bos = VardiyalarimOku(
            personel_id=personel.personel_id,
            ad_soyad=personel.ad_soyad,
            sicil_no=personel.sicil_no,
            yetkinlikler=[y.ad for y in personel.yetkinlikler],
            donem_id=None,
            donem_baslangic_tarihi=None,
            donem_bitis_tarihi=None,
            surum_id=None,
            yayinlanmis_surum_var=False,
            yayin_zamani=None,
            vardiyalar=[],
            siradaki=None,
            ozet=None,
        )

        donem = self.donem.guncel_donemi_bul(bugun)
        if donem is None:
            return bos

        yayinlanan = self.surum.yayinlanan_getir(donem.donem_id)
        if yayinlanan is None:
            return bos.model_copy(
                update={
                    "donem_id": donem.donem_id,
                    "donem_baslangic_tarihi": donem.baslangic_tarihi,
                    "donem_bitis_tarihi": donem.bitis_tarihi,
                }
            )

        vardiyalar = self._vardiyalari_olustur(donem.donem_id, yayinlanan, personel_id)
        siradaki = next((v for v in vardiyalar if v.tarih >= bugun), None)

        return VardiyalarimOku(
            personel_id=personel.personel_id,
            ad_soyad=personel.ad_soyad,
            sicil_no=personel.sicil_no,
            yetkinlikler=[y.ad for y in personel.yetkinlikler],
            donem_id=donem.donem_id,
            donem_baslangic_tarihi=donem.baslangic_tarihi,
            donem_bitis_tarihi=donem.bitis_tarihi,
            surum_id=yayinlanan.surum_id,
            yayinlanmis_surum_var=True,
            yayin_zamani=yayinlanan.yayin_zamani,
            vardiyalar=vardiyalar,
            siradaki=siradaki,
            ozet=self._donem_ozeti(personel_id, yayinlanan.surum_id),
        )

    def _vardiyalari_olustur(
        self, donem_id: int, yayinlanan: CizelgeSurumu, personel_id: int
    ) -> list[VardiyamOku]:
        """FR-9.3/FR-9.4: yayinlanmis surumdeki atamalar, en son ARSIV
        surumune gore 'eklendi'/'degisti' isaretli (karsilastirma tabani
        yoksa - ilk yayin - hicbir gun isaretlenmez)."""
        vardiya_tipleri = {v.vardiya_tipi_id: v for v in self.vardiya_tipi.tumunu_getir()}
        noktalar = {n.nokta_id: n for n in self.nokta.tumunu_getir()}

        onceki_arsiv = self.surum.en_son_arsivlenen_getir(donem_id)
        onceki_atamalar: dict[date, Atama] = {}
        if onceki_arsiv is not None:
            onceki_atamalar = {
                a.tarih: a
                for a in self.atama.surume_ve_personele_gore_getir(
                    onceki_arsiv.surum_id, personel_id
                )
            }

        sonuc: list[VardiyamOku] = []
        for a in self.atama.surume_ve_personele_gore_getir(yayinlanan.surum_id, personel_id):
            vt = vardiya_tipleri.get(a.vardiya_tipi_id)
            nk = noktalar.get(a.nokta_id)
            degisim_tipi = None
            if onceki_arsiv is not None:
                onceki = onceki_atamalar.get(a.tarih)
                if onceki is None:
                    degisim_tipi = "eklendi"
                elif onceki.vardiya_tipi_id != a.vardiya_tipi_id or onceki.nokta_id != a.nokta_id:
                    degisim_tipi = "degisti"
            sonuc.append(
                VardiyamOku(
                    tarih=a.tarih,
                    vardiya_tipi_id=a.vardiya_tipi_id,
                    vardiya_tipi_ad=vt.ad if vt is not None else "?",
                    baslangic_saati=vt.baslangic_saati if vt is not None else time(0, 0),
                    bitis_saati=vt.bitis_saati if vt is not None else time(0, 0),
                    gece_mi=vt.gece_mi if vt is not None else False,
                    nokta_id=a.nokta_id,
                    nokta_ad=nk.ad if nk is not None else "?",
                    degisim_tipi=degisim_tipi,
                )
            )
        return sonuc

    def _donem_ozeti(self, personel_id: int, surum_id: int) -> DonemOzetiOku | None:
        """FR-9.5: AnalizServisi'nin (SDD 5.7) mevcut hesaplarinin yeniden
        kullanimi - burada yalniz bu personelin kendi degeri + ekip
        ortalamasi (tekil deger) client'a cikar, digerlerinin kirilimi
        cikmaz (bkz. schemas/calisan.py docstring'i)."""
        analiz = AnalizServisi(self.oturum).hesapla(surum_id)
        if analiz is None:
            return None

        gece = next((k.sayi for k in analiz.kisi_basina_gece if k.personel_id == personel_id), 0)
        hs = next(
            (k.sayi for k in analiz.kisi_basina_hafta_sonu if k.personel_id == personel_id), 0
        )
        saat = next((s for s in analiz.saat_dagilimi if s.personel_id == personel_id), None)

        ekip_gece = (
            sum(k.sayi for k in analiz.kisi_basina_gece) / len(analiz.kisi_basina_gece)
            if analiz.kisi_basina_gece
            else 0.0
        )
        ekip_hs = (
            sum(k.sayi for k in analiz.kisi_basina_hafta_sonu) / len(analiz.kisi_basina_hafta_sonu)
            if analiz.kisi_basina_hafta_sonu
            else 0.0
        )
        ekip_saat = (
            sum(s.toplam_saat for s in analiz.saat_dagilimi) / len(analiz.saat_dagilimi)
            if analiz.saat_dagilimi
            else 0.0
        )

        return DonemOzetiOku(
            gece_sayisi=gece,
            ekip_ortalama_gece=ekip_gece,
            hafta_sonu_sayisi=hs,
            ekip_ortalama_hafta_sonu=ekip_hs,
            toplam_saat=saat.toplam_saat if saat is not None else 0.0,
            ekip_ortalama_saat=ekip_saat,
        )

    # --- Tercih bildirimi / Tercihlerim (FR-9.6, FR-3.x) ---------------------

    def tercihlerim(self, personel_id: int) -> CalisanTercihListesiOku | None:
        personel = self.personel.getir(personel_id)
        if personel is None:
            return None

        vardiya_tipleri = {v.vardiya_tipi_id: v for v in self.vardiya_tipi.tumunu_getir()}
        surum_onbellek: dict[int, CizelgeSurumu | None] = {}

        sonuc: list[CalisanTercihOku] = []
        for t in self.tercih.personele_gore_getir(personel_id):
            if t.donem_id not in surum_onbellek:
                surum_onbellek[t.donem_id] = self.surum.yayinlanan_getir(t.donem_id)
            yayinlanan = surum_onbellek[t.donem_id]

            karsilanma = self._karsilanma_durumu(
                t.tip, t.tarih, t.vardiya_tipi_id, personel_id, yayinlanan
            )

            vt = vardiya_tipleri.get(t.vardiya_tipi_id) if t.vardiya_tipi_id is not None else None
            sonuc.append(
                CalisanTercihOku(
                    tercih_id=t.tercih_id,
                    tarih=t.tarih,
                    tip=t.tip,
                    vardiya_tipi_id=t.vardiya_tipi_id,
                    vardiya_tipi_ad=vt.ad if vt is not None else None,
                    calisan_notu=t.calisan_notu,
                    durum=t.durum,
                    ret_gerekcesi=t.ret_gerekcesi,
                    karsilanma=karsilanma,
                )
            )

        acik = self.donem.tercihe_acik_donemi_bul(date.today())
        acik_donem = (
            AcikDonemOku(
                donem_id=acik.donem_id,
                baslangic_tarihi=acik.baslangic_tarihi,
                bitis_tarihi=acik.bitis_tarihi,
                tercih_son_tarihi=acik.tercih_son_tarihi,
            )
            if acik is not None
            else None
        )
        return CalisanTercihListesiOku(acik_donem=acik_donem, tercihler=sonuc)

    def _karsilanma_durumu(
        self,
        tip: TercihTipi,
        tarih: date,
        vardiya_tipi_id: int | None,
        personel_id: int,
        yayinlanan: CizelgeSurumu | None,
    ) -> str:
        """SRS TD-12 (Karsilanma durumu): SAKLANMAZ, okuma aninda yayinlanmis
        cizelgeden turetilir, UC DEGERLIDIR - yayinlanmis surum yoksa
        'karsilanmadi' DEGIL 'henuz_belirsiz' donulur (ikili bir isaret,
        cizelge uretilmeden once butun tercihleri reddedilmis gosterir)."""
        if yayinlanan is None:
            return "henuz_belirsiz"
        atama = self.atama.tekil_getir(yayinlanan.surum_id, personel_id, tarih)
        if tip == TercihTipi.CALISMAMA:
            return "karsilandi" if atama is None else "karsilanmadi"
        karsilandi = atama is not None and atama.vardiya_tipi_id == vardiya_tipi_id
        return "karsilandi" if karsilandi else "karsilanmadi"

    def tercih_bildir(
        self, personel_id: int, veri: CalisanTercihOlustur
    ) -> CalisanTercihOku | None:
        personel = self.personel.getir(personel_id)
        if personel is None:
            return None

        donem = self.donem.tarihi_iceren_donemi_bul(veri.tarih)
        if donem is None:
            raise TercihDonemiBulunamadiError(
                f"{veri.tarih.isoformat()} tarihi hicbir planlama donemine dahil degil"
            )
        if donem.tercih_son_tarihi < date.today():
            raise TercihDonemiBulunamadiError("Bu donem icin tercih bildirim penceresi kapandi")

        kayit = self.tercih.olustur(
            personel_id=personel_id,
            donem_id=donem.donem_id,
            tarih=veri.tarih,
            tip=veri.tip,
            vardiya_tipi_id=veri.vardiya_tipi_id,
            calisan_notu=veri.calisan_notu,
        )

        vardiya_tipleri = {v.vardiya_tipi_id: v for v in self.vardiya_tipi.tumunu_getir()}
        vt = (
            vardiya_tipleri.get(kayit.vardiya_tipi_id)
            if kayit.vardiya_tipi_id is not None
            else None
        )
        return CalisanTercihOku(
            tercih_id=kayit.tercih_id,
            tarih=kayit.tarih,
            tip=kayit.tip,
            vardiya_tipi_id=kayit.vardiya_tipi_id,
            vardiya_tipi_ad=vt.ad if vt is not None else None,
            calisan_notu=kayit.calisan_notu,
            durum=kayit.durum,
            ret_gerekcesi=kayit.ret_gerekcesi,
            karsilanma="henuz_belirsiz",
        )
