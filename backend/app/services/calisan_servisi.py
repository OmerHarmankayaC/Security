"""Calisan Paneli servisi (SDD 6.1; SRS FR-9.x; Sprint 3 Gun 13).

Bu katmandaki hicbir yazma islemi cizelgeyi etkilemez (SDD 6.1) - tek yazma
yolu tercih_bildir'dir ve yalniz bir Tercih kaydi dogurur.
"""

from datetime import date, time

from sqlalchemy.orm import Session

from app.kurallar.zaman_araligi import saat_kumesi
from app.models.girdi import TercihDurumu, TercihTipi
from app.models.sonuc import Atama, CizelgeSurumu
from app.repositories.girdi import TercihDeposu
from app.repositories.sonuc import AtamaDeposu, CizelgeSurumuDeposu, DonemDeposu
from app.repositories.tanim import GorevNoktasiDeposu, PersonelDeposu
from app.schemas.calisan import (
    AcikDonemOku,
    CalisanTercihListesiOku,
    CalisanTercihOku,
    CalisanTercihOlustur,
    DonemOzetiOku,
    KaldirilanGunOku,
    VardiyalarimOku,
    VardiyamOku,
)
from app.services.analiz_servisi import AnalizServisi
from app.services.atama_donusumu import atama_kaydina_cevir


class TercihDonemiBulunamadiError(Exception):
    """Bildirilmek istenen tarih hicbir donemin icine dusmuyor ya da o
    donemin tercih bildirim penceresi kapanmis (router 400'e cevirir)."""


class TercihKararlanmisError(Exception):
    """O gun icin zaten KARARLANMIS (onaylanmis/reddedilmis) bir tercih var;
    ustune yazmak yonetici kararini sessizce silerdi (router 409'a cevirir)."""


class CalisanServisi:
    def __init__(self, oturum: Session) -> None:
        self.oturum = oturum
        self.personel = PersonelDeposu(oturum)
        self.donem = DonemDeposu(oturum)
        self.surum = CizelgeSurumuDeposu(oturum)
        self.atama = AtamaDeposu(oturum)
        self.tercih = TercihDeposu(oturum)
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
            kaldirilan_gunler=[],
            siradaki=None,
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

        vardiyalar, kaldirilan_gunler = self._vardiyalari_olustur(
            donem.donem_id, yayinlanan, personel_id
        )
        # "Siradaki" yalniz gercek vardiyalardan secilir; kaldirilan bir gun
        # calisanin artik gitmeyecegi bir vardiyadir, one cikarilamaz.
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
            kaldirilan_gunler=kaldirilan_gunler,
            siradaki=siradaki,
        )

    def _vardiyalari_olustur(
        self, donem_id: int, yayinlanan: CizelgeSurumu, personel_id: int
    ) -> tuple[list[VardiyamOku], list[KaldirilanGunOku]]:
        """FR-9.3/FR-9.4: yayinlanmis surumdeki atamalar, en son ARSIV
        surumune gore UC turde isaretlenmis olarak.

        Donen ikili: (vardiyalar, kaldirilan_gunler).
          - eklendi : gun yalniz yayinlanmis surumde var
          - degisti : ikisinde de var, blogun saatleri veya noktasi farkli
          - kaldirildi : gun yalniz arsiv surumunde var -> AYRI listede
            (bkz. KaldirilanGunOku: bu bir vardiya degil, yoklugudur)
        Karsilastirma tabani yoksa (donemin ilk yayini) hicbir gun isaretlenmez
        ve kaldirilan gun listesi bostur.
        """
        noktalar = {n.nokta_id: n for n in self.nokta.tumunu_getir()}

        onceki_arsiv = self.surum.en_son_arsivlenen_getir(donem_id)
        onceki_atamalar: dict[date, Atama] = {}
        if onceki_arsiv is not None:
            onceki_atamalar = {
                a.baslangic_zamani.date(): a
                for a in self.atama.surume_ve_personele_gore_getir(
                    onceki_arsiv.surum_id, personel_id
                )
            }

        vardiyalar: list[VardiyamOku] = []
        yayinlanan_tarihler: set[date] = set()
        for a in self.atama.surume_ve_personele_gore_getir(yayinlanan.surum_id, personel_id):
            kayit = atama_kaydina_cevir(a)
            yayinlanan_tarihler.add(kayit.tarih)
            nk = noktalar.get(a.nokta_id)
            degisim_tipi = None
            if onceki_arsiv is not None:
                onceki = onceki_atamalar.get(kayit.tarih)
                if onceki is None:
                    degisim_tipi = "eklendi"
                elif (
                    onceki.baslangic_zamani != a.baslangic_zamani
                    or onceki.bitis_zamani != a.bitis_zamani
                    or onceki.nokta_id != a.nokta_id
                ):
                    degisim_tipi = "degisti"
            vardiyalar.append(
                VardiyamOku(
                    tarih=kayit.tarih,
                    baslangic_zamani=kayit.baslangic,
                    bitis_zamani=kayit.bitis,
                    sure_saat=kayit.sure_saat,
                    gece_saati=kayit.gece_saati,
                    nokta_id=a.nokta_id,
                    nokta_ad=nk.ad if nk is not None else "?",
                    degisim_tipi=degisim_tipi,
                )
            )

        # Kaldirilan gunler: arsivde olup yayinlanmis surumde olmayan tarihler.
        kaldirilan_gunler: list[KaldirilanGunOku] = []
        for tarih, onceki in sorted(onceki_atamalar.items()):
            if tarih in yayinlanan_tarihler:
                continue
            nk = noktalar.get(onceki.nokta_id)
            onceki_kayit = atama_kaydina_cevir(onceki)
            kaldirilan_gunler.append(
                KaldirilanGunOku(
                    tarih=tarih,
                    onceki_baslangic_zamani=onceki_kayit.baslangic,
                    onceki_bitis_zamani=onceki_kayit.bitis,
                    onceki_nokta_ad=nk.ad if nk is not None else "?",
                )
            )
        return vardiyalar, kaldirilan_gunler

    def donem_ozetim(
        self, personel_id: int, ufuk: str = "donem", *, bugun: date | None = None
    ) -> DonemOzetiOku | None:
        """FR-9.5 ozetinin kendi uc noktasi. `ufuk` dogrudan AnalizServisi'ne
        gecer - ikinci bir adalet formulu YAZILMAZ, tanim tek yerde kalir.

        None: aktif donem yok, yayinlanmis surum yok ya da analiz hesaplanamadi.
        Personel yoklugu burada AYRISTIRILMAZ; panel o duruma vardiyalarim
        cagrisinda zaten duser."""
        bugun = bugun if bugun is not None else date.today()
        donem = self.donem.guncel_donemi_bul(bugun)
        if donem is None:
            return None
        yayinlanan = self.surum.yayinlanan_getir(donem.donem_id)
        if yayinlanan is None:
            return None
        return self._donem_ozeti(personel_id, yayinlanan.surum_id, ufuk)

    def _donem_ozeti(
        self, personel_id: int, surum_id: int, ufuk: str = "donem"
    ) -> DonemOzetiOku | None:
        """FR-9.5: AnalizServisi'nin (SDD 5.7) mevcut hesaplarinin yeniden
        kullanimi - burada yalniz bu personelin kendi degeri + ekip
        ortalamasi (tekil deger) client'a cikar, digerlerinin kirilimi
        cikmaz (bkz. schemas/calisan.py docstring'i)."""
        analiz = AnalizServisi(self.oturum).hesapla(surum_id, ufuk)
        if analiz is None:
            return None

        # analiz.kisi_basina_* artik yalniz uygun havuzu (P_gece / P_hs) tasir
        # (SDD 5.7 surum 1.7); listede olmamak "havuz disinda" demektir.
        gece_kaydi = next(
            (k for k in analiz.kisi_basina_gece if k.personel_id == personel_id), None
        )
        hs_kaydi = next(
            (k for k in analiz.kisi_basina_hafta_sonu if k.personel_id == personel_id), None
        )
        gece = gece_kaydi.sayi if gece_kaydi is not None else 0.0
        hs = hs_kaydi.sayi if hs_kaydi is not None else 0.0
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
            ufuk=ufuk,
            gece_saati=gece,
            ekip_ortalama_gece=ekip_gece,
            adil_pay_gece=gece_kaydi.pay if gece_kaydi is not None else None,
            gece_havuzunda=gece_kaydi is not None,
            hafta_sonu_saati=hs,
            ekip_ortalama_hafta_sonu=ekip_hs,
            adil_pay_hafta_sonu=hs_kaydi.pay if hs_kaydi is not None else None,
            hafta_sonu_havuzunda=hs_kaydi is not None,
            toplam_saat=saat.toplam_saat if saat is not None else 0.0,
            ekip_ortalama_saat=ekip_saat,
            hedef_saat=saat.hedef_saat if saat is not None else 0.0,
        )

    # --- Tercih bildirimi / Tercihlerim (FR-9.6, FR-3.x) ---------------------

    def tercihlerim(self, personel_id: int) -> CalisanTercihListesiOku | None:
        personel = self.personel.getir(personel_id)
        if personel is None:
            return None

        surum_onbellek: dict[int, CizelgeSurumu | None] = {}

        sonuc: list[CalisanTercihOku] = []
        for t in self.tercih.personele_gore_getir(personel_id):
            # TD-12: turetme YALNIZ onaylanmis tercihler icin yapilir; bekleyen
            # ya da reddedilmis bir tercihte karsilanma bilgisi tanimsizdir.
            karsilanma: str | None = None
            if t.durum == TercihDurumu.ONAYLANDI:
                if t.donem_id not in surum_onbellek:
                    surum_onbellek[t.donem_id] = self.surum.yayinlanan_getir(t.donem_id)
                karsilanma = self._karsilanma_durumu(
                    t.tip,
                    t.tarih,
                    t.tercih_baslangic,
                    t.tercih_bitis,
                    personel_id,
                    surum_onbellek[t.donem_id],
                )

            sonuc.append(
                CalisanTercihOku(
                    tercih_id=t.tercih_id,
                    tarih=t.tarih,
                    tip=t.tip,
                    tercih_baslangic=t.tercih_baslangic,
                    tercih_bitis=t.tercih_bitis,
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
        tercih_baslangic: time | None,
        tercih_bitis: time | None,
        personel_id: int,
        yayinlanan: CizelgeSurumu | None,
    ) -> str:
        """SRS TD-12 (Karsilanma durumu): SAKLANMAZ, okuma aninda yayinlanmis
        cizelgeden turetilir, UC DEGERLIDIR - yayinlanmis surum yoksa
        'karsilanmadi' DEGIL 'henuz_belirsiz' donulur (ikili bir isaret,
        cizelge uretilmeden once butun tercihleri reddedilmis gosterir).

        Zaman araligi tercihi, blogun TAMAMI araligin icinde kalirsa
        karsilanmis sayilir; bir kismi disariya tasiyorsa karsilanmamistir.
        Olcut S5'in `dogrula`si ile aynidir - iki yuzey ayrisirsa calisanin
        gordugu durum ile cezanin isareti celisir."""
        if yayinlanan is None:
            return "henuz_belirsiz"
        bloklar = self.atama.gune_gore_getir(yayinlanan.surum_id, personel_id, tarih)
        if tip == TercihTipi.CALISMAMA:
            return "karsilandi" if not bloklar else "karsilanmadi"
        if not bloklar or tercih_baslangic is None or tercih_bitis is None:
            return "karsilanmadi"
        istenen = saat_kumesi(tercih_baslangic, tercih_bitis)
        karsilandi = all(
            an.hour in istenen for blok in bloklar for an in atama_kaydina_cevir(blok).saatler()
        )
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

        mevcut = self.tercih.personel_ve_tarihe_gore_getir(personel_id, veri.tarih)
        if mevcut is not None:
            if mevcut.durum is not TercihDurumu.BEKLEMEDE:
                raise TercihKararlanmisError(
                    "Bu gun icin kararlanmis bir tercihin var; degistirmek icin yoneticine basvur"
                )
            kayit = self.tercih.guncelle(
                mevcut.tercih_id,
                tip=veri.tip,
                tercih_baslangic=veri.tercih_baslangic,
                tercih_bitis=veri.tercih_bitis,
                calisan_notu=veri.calisan_notu,
            )
            assert kayit is not None  # az once okundu
        else:
            kayit = self.tercih.olustur(
                personel_id=personel_id,
                donem_id=donem.donem_id,
                tarih=veri.tarih,
                tip=veri.tip,
                tercih_baslangic=veri.tercih_baslangic,
                tercih_bitis=veri.tercih_bitis,
                calisan_notu=veri.calisan_notu,
            )

        return CalisanTercihOku(
            tercih_id=kayit.tercih_id,
            tarih=kayit.tarih,
            tip=kayit.tip,
            tercih_baslangic=kayit.tercih_baslangic,
            tercih_bitis=kayit.tercih_bitis,
            calisan_notu=kayit.calisan_notu,
            durum=kayit.durum,
            ret_gerekcesi=kayit.ret_gerekcesi,
            # Yeni bildirilen tercih BEKLEMEDE dogar; TD-12 geregi karsilanma
            # yalniz onaylanmislar icin turetilir, dolayisiyla burada tanimsiz.
            karsilanma=None,
        )
