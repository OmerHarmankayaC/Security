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

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.kurallar.baglam import AtamaKaydi, Baglam, TercihKaydi
from app.kurallar.esnek import S6bBinaTutarliligi, s4_hedef_paylari
from app.kurallar.kayit_defteri import kurallari_yukle
from app.kurallar.zaman_araligi import gece_saati_mi, saat_kumesi
from app.kurallar.zorunlu import h10_fazla_calisma_saatleri
from app.models.girdi import TercihTipi
from app.models.kural import KuralTipi
from app.models.sonuc import CizelgeSurumu, CizelgeSurumuDurumu, Donem
from app.models.tanim import Personel
from app.repositories.kural import KuralDeposu
from app.repositories.sonuc import (
    AtamaDeposu,
    CizelgeSurumuDeposu,
    CozumIsiDeposu,
    DonemDeposu,
    FazlaKadroDeposu,
    KapsamaAcigiDeposu,
)
from app.repositories.tanim import PersonelDeposu
from app.schemas.analiz import (
    AnalizOku,
    CezaKalemiOku,
    FazlaKadroKalemi,
    KisiSayisiOku,
    KotaDurumuOku,
    KumulatifDegisimOku,
    SaatDengesiOku,
)
from app.services.atama_donusumu import atama_kayitlarina_cevir
from app.services.baglam_kurucu import baglam_olustur


def _tercih_karsilandi(atama: AtamaKaydi, tercih: TercihKaydi) -> bool:
    """TD-12: zaman araligi tercihi, blogun TAMAMI araligin icinde kalirsa
    karsilanmis sayilir; bir kismi disariya tasiyorsa karsilanmamistir.

    S5'in `dogrula`si ile ayni olcut - iki yuzey ayni tercih icin farkli
    yanit verirse calisan panelindeki durum ile cezanin isareti celisir.
    """
    if tercih.tercih_baslangic is None or tercih.tercih_bitis is None:
        return False
    istenen = saat_kumesi(tercih.tercih_baslangic, tercih.tercih_bitis)
    return all(an.hour in istenen for an in atama.saatler())


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
        self.kural = KuralDeposu(oturum)

    def _h10_parametreleri(self) -> tuple[float, float]:
        """H10'un haftalik esigi ve yillik kotasi (saat).

        Kural katalogundan okunur, ekrana da bu deger gider: kotanin sayisi
        iki yerde yazili olsaydi parametre degistiginde biri geride kalirdi.
        """
        h10 = next(
            (k for k in kurallari_yukle(self.kural.aktif_kurallari_getir()) if k.kimlik == "H10"),
            None,
        )
        esik = float(h10.parametreler.get("fazla_calisma_esigi", 45)) if h10 else 45.0
        kota = float(h10.parametreler.get("yillik_fazla_kotasi", 270)) if h10 else 270.0
        return esik, kota

    def _kota_durumu(
        self,
        atamalar: list,
        baglam: Baglam,
        personel_satirlari: Sequence[Personel],
        esik: float,
        kota: float,
    ) -> list[KotaDurumuOku]:
        """H10: kisi basina fazla calisma ve kalan kota, RISKE gore sirali.

        Fazla calisma H10'un KENDI fonksiyonundan okunur; burada yeniden
        hesaplansaydi ekranda, sistemin baska hicbir yerinde bulunmayan bir
        sayi olurdu (SDD 5.8 ile ayni gerekce).

        DEVIR de gonderilir. Kalan kota devir + donem fazlasindan cikar ama
        satirda yalniz donem fazlasi yaziliydi: kotasi devirden dolmus bir
        kisi ekranda "fazla calisma 0,0 - kalan 5,0" olarak gorunuyor ve
        satir hesap hatasi gibi okunuyordu.
        """
        fazlalar = h10_fazla_calisma_saatleri(atamalar, baglam, esik)
        adlar = {p.personel_id: p.ad_soyad for p in personel_satirlari}
        satirlar = [
            KotaDurumuOku(
                personel_id=p,
                ad_soyad=adlar.get(p, str(p)),
                devir_saat=round(baglam.devir_fazla_calisma_saat(p), 1),
                fazla_calisma_saat=round(fazlalar.get(p, 0.0), 1),
                kalan_kota_saat=round(
                    max(kota - baglam.devir_fazla_calisma_saat(p) - fazlalar.get(p, 0.0), 0.0), 1
                ),
            )
            for p in baglam.personel
        ]
        # SINIRA DAYANAN USTTE: kartin amaci listeyi degil riski gostermek.
        satirlar.sort(key=lambda k: (k.kalan_kota_saat, -k.fazla_calisma_saat))
        return satirlar

    def _ceza_kalemleri(self, ceza_dokumu: dict[str, float] | None) -> list[CezaKalemiOku]:
        """Ham deger / agirlik / agirlikli ceza — UC AYRI SUTUN (SDD 6.3.4).

        Ham deger cozucunun kendi dokumunden gelir; agirlik kural
        katalogundan. Carpimlarinin toplami `toplam_ceza`ya esittir ve dosya
        bu iliskiyi canli formulle gosterir (SDD 5.8).
        """
        if not ceza_dokumu:
            return []
        kurallar = {k.kimlik: k for k in kurallari_yukle(self.kural.aktif_kurallari_getir())}
        kalemler = []
        for kimlik, ham in sorted(ceza_dokumu.items()):
            kural = kurallar.get(kimlik)
            agirlik = float(kural.agirlik or 0) if kural else 0.0
            kalemler.append(
                CezaKalemiOku(
                    kimlik=kimlik,
                    ad=(kural.ad if kural and kural.ad else kimlik),
                    ham_deger=float(ham),
                    agirlik=agirlik,
                    agirlikli_ceza=float(ham) * agirlik,
                )
            )
        return kalemler

    def _ceza_kaynagi_ve_dokum(
        self, surum_id: int, atamalar: list[AtamaKaydi], baglam: Baglam
    ) -> tuple[str, dict[str, float] | None, float | None]:
        """(kaynak, ceza_dokumu, toplam_ceza).

        COZUCUNUN DOKUMU YALNIZ TAZEYSE KULLANILIR. Cozulmus bir surum elle
        duzenlendiginde eski dokum duruyordu ve ekran degismis bir cizelgeyi
        degismemis bir cezayla gosteriyordu.

        Cozucusuz surumde dokum ESNEK KURALLARIN KENDISINDEN hesaplanir; ayni
        siniflar dogrulama servisinin de kaynagi (dogrulama_servisi.py).
        Ikinci bir gerceklik kurulmuyor: cozucu ile dogrulayicinin ayni
        cizelgede ayni seyi gormesi zaten guvence altinda (SDD 3.2.1).

        IKI FARKLI SAAT KARSILASTIRILIYOR: `son_atama` veritabaninin sunucu
        tarafi `now()`'i (islemin baslangic ani), `is_kaydi.bitis_zamani`
        ise uygulamanin `datetime.now(UTC)`'si. Cozucu ikisini de AYNI
        islemde yazar ve atama damgasi daha erkendir, dolayisiyla
        karsilastirma `<=` ile yapilir - ESITLIK TAZE SAYILIR. Saatler
        kayarsa sonuc zararsizdir: surum bayat sayilir ve dokum kurallardan
        hesaplanir; ikisinin ayni sayiyi vermesi zaten guvence altindadir.
        """
        is_kaydi = self.cozum_isi.surume_gore_en_son(surum_id)
        son_atama = self.atama.surume_gore_son_guncelleme(surum_id)
        taze = (
            is_kaydi is not None
            and is_kaydi.ceza_dokumu is not None
            and is_kaydi.bitis_zamani is not None
            and son_atama is not None
            and son_atama <= is_kaydi.bitis_zamani
        )
        if taze:
            dokum = {k: float(v) for k, v in is_kaydi.ceza_dokumu.items()}
            toplam = float(is_kaydi.en_iyi_ceza) if is_kaydi.en_iyi_ceza is not None else None
            return "cozucu", dokum, toplam

        # S8 NEDEN DISARIDA: "onceki surumden sapma" yalniz
        # baglam.onceki_atamalar doluyken tanimlidir; analiz baglami onu
        # kurmuyor (baglam_olustur'un boyle bir parametresi yok). Sifir
        # yazmak "sapma yok" derdi; dogrusu "bu olcu burada tanimsiz", bu
        # yuzden kalem hic uretilmez - sonraki okuyucu eksikligi hata
        # sanmasin diye burada acikca yaziliyor.
        kurallar = kurallari_yukle(self.kural.aktif_kurallari_getir())
        dokum: dict[str, float] = {}
        agirliklar: dict[str, float] = {}
        for kural in kurallar:
            if kural.tip != KuralTipi.ESNEK or kural.kimlik == "S8":
                continue
            ceza = sum(i.ceza or 0.0 for i in kural.dogrula(atamalar, baglam))
            if ceza:
                dokum[kural.kimlik] = ceza
                agirliklar[kural.kimlik] = float(kural.agirlik or 0)

        if not dokum:
            return "yok", None, None
        toplam_ceza = sum(ceza * agirliklar[kimlik] for kimlik, ceza in dokum.items())
        return "kurallardan", dokum, toplam_ceza

    def _kumulatif_degisim(
        self, surum, donem, baglam: Baglam, atamalar: list
    ) -> KumulatifDegisimOku:
        """Kisi basina gece sapmasinin ONCEKI yayinlanmis doneme gore degisimi.

        Kumulatif adaletin vaadi sapmanin kucuk olmasi degil, ZAMANLA
        kucuulmesidir (Charter 5, K3).
        """
        simdiki = _ortalama_gece_sapmasi(baglam, atamalar)
        onceki = self._onceki_yayinlanan(donem)
        if onceki is None:
            return KumulatifDegisimOku(simdiki_ortalama_sapma=simdiki)

        onceki_donem = self.donem.getir(onceki.donem_id)
        if onceki_donem is None:
            return KumulatifDegisimOku(simdiki_ortalama_sapma=simdiki)
        onceki_baglam = baglam_olustur(self.oturum, onceki_donem, yalniz_aktif=False)
        onceki_atamalar = [
            a
            for a in atama_kayitlarina_cevir(self.atama.surume_gore_getir(onceki.surum_id))
            if onceki_baglam.donem_icinde(a.tarih)
        ]
        return KumulatifDegisimOku(
            onceki_surum_id=onceki.surum_id,
            onceki_ortalama_sapma=_ortalama_gece_sapmasi(onceki_baglam, onceki_atamalar),
            simdiki_ortalama_sapma=simdiki,
        )

    def _onceki_yayinlanan(self, donem):
        """Bu donemden ONCE biten donemlerin EN SON yayinlanmis surumu.

        Ayni donemin arsiv surumu degil: karsilastirma "gecen doneme gore"
        yapilir, "bu donemin onceki denemesine gore" degil. Ikisi ayri
        sorulardir ve ikincisi Surumler ekraninin isidir (SDD 6.3.5).
        """
        return (
            self.oturum.execute(
                select(CizelgeSurumu)
                .join(Donem, Donem.donem_id == CizelgeSurumu.donem_id)
                .where(
                    CizelgeSurumu.durum == CizelgeSurumuDurumu.YAYINLANDI,
                    Donem.bitis_tarihi < donem.baslangic_tarihi,
                )
                .order_by(Donem.bitis_tarihi.desc(), CizelgeSurumu.surum_no.desc())
            )
            .scalars()
            .first()
        )

    def hesapla(self, surum_id: int, ufuk: str = "donem") -> AnalizOku | None:
        """`ufuk`: "donem" (varsayilan) ya da "adalet" (doksan gun, SRS TD-6).

        IKI UFKUN SAYILARI FARKLIDIR ve hangisine bakildigi belirsiz kalirsa
        tablo yanlis okunur (SDD 6.3.4) - bu yuzden secilen ufuk yanitin
        icinde geri doner ve ekran onu her zaman gosterir.

        Adalet ufkunda hem YUK hem PAY genisler: gecmis gerceklesen saat yuke,
        gecmis pay hedefe eklenir ve pay calisabilirlik oraniyla olceklenir.
        Yalniz biri genisletilseydi kisi hic yapmadigi bir isin hesabini
        verirken gorunurdu.
        """
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

        atamalar = [
            a
            for a in atama_kayitlarina_cevir(self.atama.surume_gore_getir(surum_id))
            if baglam.donem_icinde(a.tarih)
        ]

        personel_satirlari: Sequence[Personel] = self.personel.tumunu_getir()
        h10_esigi, yillik_kota = self._h10_parametreleri()

        # --- Kapsama orani (FR-8.1, SDD 5.7): ATAMA KAYITLARINDAN.
        #
        #   karsilanan = Σ min(atanan[d,t,n], talep[d,t,n])
        #   toplam     = Σ talep[d,t,n]
        #
        # Kaynagin atamalar olmasi sarttir. Oran daha once kapsama acigi
        # TABLOSUNDAN tureiliyordu ve o tabloda kayit bulunmamasi "acik yok"
        # sayiliyordu: hic atamasi olmayan, cozum dahi calistirilmamis bir
        # surum %100 kapsama raporluyordu. Gozlenmis bir hatadir. Acik
        # tablosu bir RAPORLAMA DETAYIDIR, oranin kaynagi degildir.
        #
        # `min(...)` sart: bir saatteki fazla kadro, baska bir saatteki
        # acigi kapatmaz.
        #
        # Birim KISI-SAAT (TD-6 geregi yalniz donem gunleri; `talep_saat`
        # isitma penceresini de kapsayan eksen icin cozulur).
        atanan_saat = baglam.atanan_saat_sayilari(atamalar)
        toplam_talep = 0
        karsilanan = 0
        for anahtar, gereken in baglam.talep_saat.items():
            if not baglam.donem_icinde(anahtar[0]):
                continue
            toplam_talep += gereken
            karsilanan += min(atanan_saat.get(anahtar, 0), gereken)
        # Talep yoksa oran TANIMSIZ (None) - sifir bolme yerine yuzde yuz
        # varsaymak, bos bir donemi kusursuz bir cizelge gibi gosterir.
        kapsama_orani = karsilanan / toplam_talep if toplam_talep > 0 else None

        # --- Fazla kadro (SRS 4.3 S1 ust siniri). Kapsama ORANINA
        # KARISTIRILMAZ: oran "talebin ne kadari karsilandi" sorusunu
        # yanitlar ve fazla kadro o soruya bir sey eklemez - fazla atama
        # bir hucreyi daha iyi kapsamis olmaz. Ayri bir sayi olarak
        # raporlanir; ekranda da ayri durur.
        fazla_satirlari = self.fazla_kadro.surume_gore_getir(surum_id)
        fazla_kadro = [
            FazlaKadroKalemi(
                baslangic_zamani=f.baslangic_zamani,
                bitis_zamani=f.bitis_zamani,
                nokta_id=f.nokta_id,
                nokta_ad=_ad(baglam.gorev_noktalari.get(f.nokta_id)),
                fazla_sayi=f.fazla_sayi,
            )
            for f in fazla_satirlari
        ]
        toplam_fazla = sum(f.fazla_sayi for f in fazla_satirlari)

        # --- Kisi basina gece / hafta sonu SAATI (FR-8.2), saat dagilimi.
        #
        # BIRIM SAAT, VARDIYA SAYISI DEGIL. Blok sureleri artik cozumun
        # ciktisi oldugundan sayima dayali bir olcu tanimsizdir: on iki saat
        # gece calisan personel ile alti saat calisan ayni sayilamaz
        # (SRS S2). Analiz, S2/S3 ile ayni tabani okumak zorundadir - iki
        # yerde farkli birim, ayni cizelge icin farkli rapor demektir.
        gece_saat: dict[int, float] = defaultdict(float)
        hs_saat: dict[int, float] = defaultdict(float)
        saat_toplam: dict[int, float] = defaultdict(float)
        for a in atamalar:
            gece_saat[a.personel_id] += a.gece_saati
            if baglam.hafta_sonu_mu(a.tarih):
                hs_saat[a.personel_id] += a.sure_saat
            saat_toplam[a.personel_id] += a.sure_saat

        # SDD 5.7 (surum 1.7): gece ve hafta sonu metrikleri UYGUN HAVUZ
        # (SRS S2/S3'teki P_gece, P_hs) uzerinden raporlanir - yetkinligi
        # geregi o talebin bulundugu hicbir noktada calisamayan personel
        # olcume dahil edilmez, aksi halde kalici olarak ortalamanin altinda
        # gorunur. Havuz tanimi Baglam.adil_paylar'da tek yerde durur (havuz,
        # payi sifirdan buyuk olanlardir); cozucu, dogrulayici ve Analiz ayni
        # tabani kullanir.
        # Yuklem SAAT EKSENLI talebe uygulanir (anahtar: tarih, saat, nokta).
        #
        # PAY DA RAPORLANIR (Tur 6). Havuz uyeligi zaten "payi sifirdan
        # buyuk olan" demek; `uygun_havuz` payi hesaplayip atiyordu ve
        # arayuz elinde yalnizca sayilarla kalinca referans olarak HAVUZ
        # ORTALAMASINI cizmek zorunda kaliyordu. Ortalama, S2/S3'un acikca
        # reddettigi olcudur: erisilebilirligi kisitli bir havuz ona gore
        # kalici olarak sapmali gorunur. Paylar bir kez hesaplanir, havuz
        # ondan turer — iki ayri gecis yapilmaz ve tanim yine tek yerdedir.
        # UFUK SECIMI TEK YERDE: `olcu` verilirse gecmis pay eklenir ve oran
        # uygulanir, verilmezse donem ici kalir (bkz. `Baglam.adil_paylar`).
        gece_olcu = "gece" if ufuk == "adalet" else None
        hs_olcu = "hafta_sonu" if ufuk == "adalet" else None
        gece_paylari = baglam.adil_paylar(lambda anahtar: gece_saati_mi(anahtar[1]), olcu=gece_olcu)
        hs_paylari = baglam.adil_paylar(
            lambda anahtar: baglam.hafta_sonu_mu(anahtar[0]), olcu=hs_olcu
        )
        # Yuk de ayni ufku kapsamali.
        gecmis_gece = baglam.gecmis_gece_saat if ufuk == "adalet" else (lambda _p: 0.0)
        gecmis_hs = baglam.gecmis_hafta_sonu_saat if ufuk == "adalet" else (lambda _p: 0.0)

        kisi_basina_gece = [
            KisiSayisiOku(
                personel_id=p.personel_id,
                ad_soyad=p.ad_soyad,
                sayi=gece_saat.get(p.personel_id, 0.0) + gecmis_gece(p.personel_id),
                pay=gece_paylari[p.personel_id],
            )
            for p in personel_satirlari
            if gece_paylari.get(p.personel_id, 0.0) > 0
        ]
        kisi_basina_hafta_sonu = [
            KisiSayisiOku(
                personel_id=p.personel_id,
                ad_soyad=p.ad_soyad,
                sayi=hs_saat.get(p.personel_id, 0.0) + gecmis_hs(p.personel_id),
                pay=hs_paylari[p.personel_id],
            )
            for p in personel_satirlari
            if hs_paylari.get(p.personel_id, 0.0) > 0
        ]

        # SDD 5.7 (surum 1.7): saat dagiliminin tabani kisisel SOZLESME saati
        # degil, SRS S4'teki ADIL PAY (pay[p]). Sozlesme saati taban alindiginda
        # H5+H6 kisi basina azami vardiya sayisini sinirladigi icin kadro asgari
        # gereksinimin uzerindeyken hic kimse hedefine ulasamiyor, tablo butun
        # satirlarda ayni yonde sapma gosterip hicbir ayrim uretmiyordu.
        # Hesap S4'un kendi fonksiyonundan gelir - kural iki ayri yerde
        # kodlanmaz (SDD 2.4); S4_OLCEK onda bir saat oldugundan dogal birime
        # geri cevrilir (SDD Ek A, "Kesirli hedeflerin tamsayiya olceklenmesi").
        # SAAT DENGESI DE UFKU IZLER — gece ve hafta sonu gibi. Bu satir
        # eskiden hedefi gecmisi KATARAK, yuku ise yalniz donem icinden
        # okuyordu: hedef doksan gunu, yuk yedi gunu kapsiyordu ve herkes
        # hedefinin yuz altmis saat altinda gorunuyordu (olculdu: toplam
        # 52,0 / hedef 212,4). Iki taraf ayni pencereden okunmak zorunda.
        # S4'un dogrula'si zaten boyle yapiyor (esnek.py, S4.dogrula):
        # yuke gecmis saati ekler. Analiz onunla ayni sayiyi vermelidir.
        paylar = s4_hedef_paylari(baglam, donem_gun_sayisi, gecmisi_kat=ufuk == "adalet")
        gecmis_saat = baglam.gecmis_toplam_saat if ufuk == "adalet" else (lambda _p: 0.0)
        saat_dagilimi: list[SaatDengesiOku] = []
        for p in personel_satirlari:
            hedef = paylar.get(p.personel_id, 0.0)
            toplam = saat_toplam.get(p.personel_id, 0.0) + gecmis_saat(p.personel_id)
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
            elif atama is not None and _tercih_karsilandi(atama, tercih):
                karsilanan += 1
        tercih_orani = karsilanan / len(baglam.tercihler) if baglam.tercihler else None

        # --- Ceza dokumu / toplam ceza / kaynagi (FR-8.6, Gorev 5). Kaynak
        # secimi ve gerekcesi _ceza_kaynagi_ve_dokum'de: cozucunun dokumu
        # yalniz TAZEYSE kullanilir, degilse kural motorundan hesaplanir.
        ceza_kaynagi, ceza_dokumu, toplam_ceza = self._ceza_kaynagi_ve_dokum(
            surum_id, atamalar, baglam
        )

        # --- Kapsama acigi: ARALIK SAYISI ve KISI-SAAT ayri olculer.
        aciklar = self.kapsama.surume_gore_getir(surum_id)
        karsilanmayan = sum(
            a.eksik_sayi * round((a.bitis_zamani - a.baslangic_zamani).total_seconds() / 3600)
            for a in aciklar
        )

        return AnalizOku(
            surum_id=surum_id,
            ufuk=ufuk,
            karsilanmayan_kisi_saat=karsilanmayan,
            acik_aralik_sayisi=len(aciklar),
            kota_durumu=self._kota_durumu(
                atamalar, baglam, personel_satirlari, h10_esigi, yillik_kota
            ),
            yillik_kota_saat=yillik_kota,
            ceza_kalemleri=self._ceza_kalemleri(ceza_dokumu),
            kumulatif_degisim=self._kumulatif_degisim(surum, donem, baglam, atamalar),
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
            ceza_kaynagi=ceza_kaynagi,
        )


def _ortalama_gece_sapmasi(baglam: Baglam, atamalar: list[AtamaKaydi]) -> float | None:
    """Kisi basina gece saatinin adil paydan ORTALAMA mutlak sapmasi.

    Ufuk DONEM ICIDIR (Charter 1.5): `adil_paylar` `olcu` verilmeden
    cagrilir. Kumulatif degisim gostergesi iki donemi karsilastirir ve
    ikisinin de kendi donemi icinde olculmesi gerekir; biri ufuk biri donem
    olsaydi karsilastirma anlamsizlasirdi.
    """
    paylar = baglam.adil_paylar(lambda anahtar: gece_saati_mi(anahtar[1]))
    havuz = [p for p, pay in paylar.items() if pay > 0]
    if not havuz:
        return None
    yukler: dict[int, float] = defaultdict(float)
    for a in atamalar:
        if baglam.donem_icinde(a.tarih):
            yukler[a.personel_id] += a.gece_saati
    return round(sum(abs(yukler[p] - paylar[p]) for p in havuz) / len(havuz), 2)
