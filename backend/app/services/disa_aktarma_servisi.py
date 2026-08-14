"""Excel disa aktarma (SDD 5.8; SRS FR-8.5, FR-8.9).

VERI MEVCUT OKUMA YUZEYLERINDEN GELIR, IKINCI BIR HESAP YAPILMAZ. Cizelge
atamalardan, analiz `AnalizServisi`'nden, aciklar kapsama kayitlarindan,
fazla calisma H10'un kendi fonksiyonundan okunur. Disa aktarmanin kendi
toplamlarini hesaplamasi, ayni sayinin ekranda ve dosyada farkli cikmasi
demektir; bu projede ayni hesabin iki yerde durmasinin bedeli birkac kez
odenmistir.

SAAT BICIMLEMESI DE TEK YERDEN: `zaman_araligi.saat_metni` ve
`aralik_metni`. Saat metni biciminin ucuncu bir kopyasi bir kez hataya yol
acti.

HUCRE DOLGUSU BILGIYI TEK BASINA TASIMAZ. Saat araligi hucrede METIN olarak
da yazilidir ve bir aciklama satiri dolgunun anlamini soyler; renksiz
basilan bir cikti okunabilir kalir. Ayni ilke ekrandaki renk bandi icin de
gecerlidir (SDD 6.3.3).
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet
from sqlalchemy.orm import Session

from app.kurallar.kayit_defteri import kurallari_yukle
from app.kurallar.zaman_araligi import aralik_metni, gece_saat_sayisi, saat_metni
from app.kurallar.zorunlu import h10_fazla_calisma_saatleri
from app.models.sonuc import CizelgeSurumu
from app.repositories.kural import KuralDeposu
from app.repositories.sonuc import (
    AtamaDeposu,
    CizelgeSurumuDeposu,
    DonemDeposu,
    FazlaKadroDeposu,
    KapsamaAcigiDeposu,
)
from app.repositories.tanim import GorevNoktasiDeposu, PersonelDeposu
from app.schemas.analiz import AnalizOku
from app.services.analiz_servisi import AnalizServisi
from app.services.atama_donusumu import atama_kayitlarina_cevir
from app.services.baglam_kurucu import baglam_olustur

# --- Bicimleme sabitleri --------------------------------------------------
#
# Renkler ekrandaki saat bandinin (SDD 6.3.3) kaba karsiligidir: gece koyu,
# gunduz acik. Excel hucre dolgusu surekli bir gradient tasiyamaz, bu yuzden
# band UC basamaga indirgenmistir. Basamak sayisi bilgi tasimaz - metin
# tasir; dolgu yalniz goze tarama kolayligi verir.
_GECE_DOLGU = PatternFill("solid", fgColor="2F3A38")
_SABAH_DOLGU = PatternFill("solid", fgColor="A4A79D")
_GUNDUZ_DOLGU = PatternFill("solid", fgColor="E9E7D9")
_ACIK_DOLGU = PatternFill("solid", fgColor="F7E2D6")
_BASLIK_DOLGU = PatternFill("solid", fgColor="E4E7E1")

_BASLIK_YAZI = Font(bold=True)
_GECE_YAZI = Font(color="E8EBE5")
_INCE = Side(style="thin", color="D2D7CE")
_KENARLIK = Border(left=_INCE, right=_INCE, top=_INCE, bottom=_INCE)
_ORTALI = Alignment(horizontal="center", vertical="center", wrap_text=True)


def _blok_dolgusu(baslangic: datetime, bitis: datetime) -> tuple[PatternFill, Font | None]:
    """Blogun gun icindeki KONUMUNU gosteren dolgu.

    Olcut blogun gece saati oranidir (SRS TD-2): tamamen gece olan blok koyu,
    hic gece saati olmayan blok acik, karisik olan ara ton. Renk BILGI TASIMAZ
    - hucrede saat araligi zaten yazili - yalnizca goz gezdirmeyi kolaylastirir.
    """
    sure = round((bitis - baslangic).total_seconds() / 3600)
    gece = gece_saat_sayisi(baslangic.time(), bitis.time())
    if gece == 0:
        return _GUNDUZ_DOLGU, None
    if gece >= sure:
        return _GECE_DOLGU, _GECE_YAZI
    return _SABAH_DOLGU, None


@dataclass(frozen=True, slots=True)
class _Baglam:
    """Iki calisma kitabinin da okudugu ortak veri."""

    surum: CizelgeSurumu
    donem_baslangic: date
    donem_bitis: date
    gunler: list[date]
    atamalar: list
    aciklar: list
    fazlalar: list
    analiz: AnalizOku
    personel_adi: dict[int, str]
    personel_sicil: dict[int, str]
    nokta_adi: dict[int, str]
    fazla_calisma: dict[int, float]
    kalan_kota: dict[int, float]


class DisaAktarmaServisi:
    def __init__(self, oturum: Session) -> None:
        self.oturum = oturum
        self.surum = CizelgeSurumuDeposu(oturum)
        self.donem = DonemDeposu(oturum)
        self.atama = AtamaDeposu(oturum)
        self.kapsama = KapsamaAcigiDeposu(oturum)
        self.fazla = FazlaKadroDeposu(oturum)
        self.personel = PersonelDeposu(oturum)
        self.nokta = GorevNoktasiDeposu(oturum)
        self.kural = KuralDeposu(oturum)
        self.analiz = AnalizServisi(oturum)

    def _baglami_kur(self, surum_id: int) -> _Baglam | None:
        surum = self.surum.getir(surum_id)
        if surum is None:
            return None
        donem = self.donem.getir(surum.donem_id)
        if donem is None:
            return None
        analiz = self.analiz.hesapla(surum_id)
        if analiz is None:
            return None

        atamalar = list(self.atama.surume_gore_getir(surum_id))
        gun_sayisi = (donem.bitis_tarihi - donem.baslangic_tarihi).days + 1
        gunler = [donem.baslangic_tarihi + timedelta(days=i) for i in range(gun_sayisi)]

        # FAZLA CALISMA VE KOTA H10'UN KENDI FONKSIYONUNDAN. Burada yeniden
        # hesaplansaydi dosyada, sistemin baska hicbir yerinde bulunmayan bir
        # sayi olurdu ve dogrulugunu kimse denetleyemezdi.
        baglam = baglam_olustur(self.oturum, donem, yalniz_aktif=False)
        kayitlar = atama_kayitlarina_cevir(atamalar)
        kurallar = kurallari_yukle(self.kural.aktif_kurallari_getir())
        h10 = next((k for k in kurallar if k.kimlik == "H10"), None)
        esik = float(h10.parametreler.get("fazla_calisma_esigi", 45)) if h10 else 45.0
        kota = float(h10.parametreler.get("yillik_fazla_kotasi", 270)) if h10 else 270.0
        fazla_calisma = h10_fazla_calisma_saatleri(kayitlar, baglam, esik)
        kalan = {
            p: max(kota - baglam.devir_fazla_calisma_saat(p) - fazla_calisma.get(p, 0.0), 0.0)
            for p in baglam.personel
        }

        return _Baglam(
            surum=surum,
            donem_baslangic=donem.baslangic_tarihi,
            donem_bitis=donem.bitis_tarihi,
            gunler=gunler,
            atamalar=atamalar,
            aciklar=list(self.kapsama.surume_gore_getir(surum_id)),
            fazlalar=list(self.fazla.surume_gore_getir(surum_id)),
            analiz=analiz,
            personel_adi={p.personel_id: p.ad_soyad for p in self.personel.tumunu_getir()},
            personel_sicil={p.personel_id: p.sicil_no for p in self.personel.tumunu_getir()},
            nokta_adi={n.nokta_id: n.ad for n in self.nokta.tumunu_getir()},
            fazla_calisma=fazla_calisma,
            kalan_kota=kalan,
        )

    # --- Cizelge calisma kitabi (FR-8.5) ---------------------------------

    def cizelge_calisma_kitabi(self, surum_id: int) -> Workbook | None:
        b = self._baglami_kur(surum_id)
        if b is None:
            return None
        kitap = Workbook()
        self._sayfa_cizelge(kitap.active, b)
        self._sayfa_ozet(kitap.create_sheet("Özet"), b)
        self._sayfa_ham_cizelge(kitap.create_sheet("Ham veri"), b)
        return kitap

    def _basligi_yaz(self, sayfa: Worksheet, b: _Baglam, baslik: str) -> int:
        """Ortak baslik blogu; ilk bos satirin numarasini dondurur."""
        oran = b.analiz.kapsama_orani
        toplam_acik = sum(a.eksik_sayi for a in b.aciklar)
        sayfa["A1"] = baslik
        sayfa["A1"].font = Font(bold=True, size=14)
        sayfa["A2"] = (
            f"Dönem {b.donem_baslangic.isoformat()} – {b.donem_bitis.isoformat()} · "
            f"Sürüm {b.surum.surum_no} ({b.surum.durum.value}) · "
            f"Üretim {date.today().isoformat()}"
        )
        sayfa["A3"] = (
            f"Kapsama {'—' if oran is None else f'%{oran * 100:.1f}'} · "
            f"Toplam açık {toplam_acik} kişi-saat · "
            f"Talepten fazla {b.analiz.toplam_fazla_kadro}"
        )
        return 5

    def _sayfa_cizelge(self, sayfa: Worksheet, b: _Baglam) -> None:
        sayfa.title = "Çizelge"
        satir = self._basligi_yaz(sayfa, b, "Vardiya Çizelgesi")

        # Aciklarin gunleri: gun basligi isaretlenir. Acik SAAT duzeyinde
        # tutulur ama sutun basligi gun duzeyindedir; ayrinti kendi
        # sayfasinda durur.
        acik_gunleri = {a.baslangic_zamani.date() for a in b.aciklar}

        sayfa.cell(satir, 1, "Personel").font = _BASLIK_YAZI
        sayfa.cell(satir, 1).fill = _BASLIK_DOLGU
        for sutun, gun in enumerate(b.gunler, start=2):
            hucre = sayfa.cell(satir, sutun, gun.strftime("%d.%m"))
            hucre.font = _BASLIK_YAZI
            hucre.alignment = _ORTALI
            hucre.fill = _ACIK_DOLGU if gun in acik_gunleri else _BASLIK_DOLGU
            hucre.border = _KENARLIK

        # Blogun SAYILDIGI gun (SRS TD-1) baslangic damgasindan turetilir.
        indeks: dict[tuple[int, date], object] = {
            (a.personel_id, a.baslangic_zamani.date()): a for a in b.atamalar
        }
        personeller = sorted(
            {a.personel_id for a in b.atamalar},
            key=lambda p: b.personel_adi.get(p, ""),
        )
        for i, personel_id in enumerate(personeller, start=1):
            r = satir + i
            ad = sayfa.cell(r, 1, b.personel_adi.get(personel_id, str(personel_id)))
            ad.border = _KENARLIK
            for sutun, gun in enumerate(b.gunler, start=2):
                hucre = sayfa.cell(r, sutun)
                hucre.border = _KENARLIK
                hucre.alignment = _ORTALI
                atama = indeks.get((personel_id, gun))
                if atama is None:
                    continue
                # METIN HER ZAMAN VAR: dolgu basilmasa da hucre okunur.
                hucre.value = (
                    f"{aralik_metni(atama.baslangic_zamani.time(), atama.bitis_zamani.time())}\n"
                    f"{b.nokta_adi.get(atama.nokta_id, '')}"
                )
                dolgu, yazi = _blok_dolgusu(atama.baslangic_zamani, atama.bitis_zamani)
                hucre.fill = dolgu
                if yazi is not None:
                    hucre.font = yazi

        aciklama = satir + len(personeller) + 2
        sayfa.cell(
            aciklama,
            1,
            "Hücre dolgusu çalışmanın gün içindeki konumunu gösterir: koyu = gece "
            "(20.00–06.00), ara ton = kısmen gece, açık = gündüz. Renk tek başına "
            "bilgi taşımaz; saat aralığı hücrede metin olarak da yazılıdır. "
            "Turuncu gün başlığı o günde kapsama açığı bulunduğunu belirtir.",
        )
        sayfa.column_dimensions["A"].width = 26
        for sutun in range(2, len(b.gunler) + 2):
            sayfa.column_dimensions[get_column_letter(sutun)].width = 13
        sayfa.freeze_panes = sayfa.cell(satir + 1, 2)

    def _sayfa_ozet(self, sayfa: Worksheet, b: _Baglam) -> None:
        satir = self._basligi_yaz(sayfa, b, "Personel Özeti")
        basliklar = [
            "Sicil",
            "Personel",
            "Toplam saat",
            "Gece saati",
            "Hafta sonu saati",
            "Fazla çalışma",
            "Kalan yıllık kota",
        ]
        for sutun, metin in enumerate(basliklar, start=1):
            hucre = sayfa.cell(satir, sutun, metin)
            hucre.font = _BASLIK_YAZI
            hucre.fill = _BASLIK_DOLGU
            hucre.border = _KENARLIK

        # UCU DE ANALIZ SERVISINDEN. Ayni sayilar ekranda da bunlardan
        # okunuyor; burada yeniden toplanmasi iki yuzey arasinda sessiz bir
        # ayrisma acardi.
        gece = {k.personel_id: k.sayi for k in b.analiz.kisi_basina_gece}
        hafta_sonu = {k.personel_id: k.sayi for k in b.analiz.kisi_basina_hafta_sonu}
        for i, denge in enumerate(b.analiz.saat_dagilimi, start=1):
            r = satir + i
            sayfa.cell(r, 1, b.personel_sicil.get(denge.personel_id, ""))
            sayfa.cell(r, 2, denge.ad_soyad)
            sayfa.cell(r, 3, round(denge.toplam_saat, 1))
            sayfa.cell(r, 4, round(gece.get(denge.personel_id, 0.0), 1))
            sayfa.cell(r, 5, round(hafta_sonu.get(denge.personel_id, 0.0), 1))
            sayfa.cell(r, 6, round(b.fazla_calisma.get(denge.personel_id, 0.0), 1))
            sayfa.cell(r, 7, round(b.kalan_kota.get(denge.personel_id, 0.0), 1))
            for sutun in range(1, 8):
                sayfa.cell(r, sutun).border = _KENARLIK
        _genislikleri_ayarla(sayfa, [12, 26, 13, 12, 17, 14, 18])

    def _sayfa_ham_cizelge(self, sayfa: Worksheet, b: _Baglam) -> None:
        """CSV ciktisiyla AYNI icerik (SRS 7.2): blok basina bir satir."""
        basliklar = [
            "tarih",
            "sicil",
            "ad",
            "baslangic",
            "bitis",
            "gorev_noktasi",
            "gece_saat",
            "hafta_sonu_mu",
            "sure_saat",
        ]
        for sutun, metin in enumerate(basliklar, start=1):
            hucre = sayfa.cell(1, sutun, metin)
            hucre.font = _BASLIK_YAZI
            hucre.fill = _BASLIK_DOLGU
        for i, a in enumerate(
            sorted(b.atamalar, key=lambda x: (x.baslangic_zamani, x.personel_id)), start=2
        ):
            gun = a.baslangic_zamani.date()
            sure = round((a.bitis_zamani - a.baslangic_zamani).total_seconds() / 3600)
            sayfa.cell(i, 1, gun.isoformat())
            sayfa.cell(i, 2, b.personel_sicil.get(a.personel_id, ""))
            sayfa.cell(i, 3, b.personel_adi.get(a.personel_id, ""))
            # TAM ISO DAMGASI: gece yarisini asan blogun bitisi ertesi gune
            # duser ve bunu yalnizca damga soyleyebilir (SRS 7.2).
            sayfa.cell(i, 4, a.baslangic_zamani.isoformat())
            sayfa.cell(i, 5, a.bitis_zamani.isoformat())
            sayfa.cell(i, 6, b.nokta_adi.get(a.nokta_id, ""))
            sayfa.cell(i, 7, gece_saat_sayisi(a.baslangic_zamani.time(), a.bitis_zamani.time()))
            sayfa.cell(i, 8, "evet" if gun.weekday() >= 5 else "hayir")
            sayfa.cell(i, 9, sure)
        _genislikleri_ayarla(sayfa, [12, 12, 24, 26, 26, 18, 11, 15, 11])

    # --- Analiz calisma kitabi (FR-8.9) ----------------------------------

    def analiz_calisma_kitabi(self, surum_id: int) -> Workbook | None:
        b = self._baglami_kur(surum_id)
        if b is None:
            return None
        kitap = Workbook()
        self._sayfa_analiz_ozet(kitap.active, b)
        self._sayfa_adalet(kitap.create_sheet("Adalet"), b)
        self._sayfa_aciklar(kitap.create_sheet("Kapsama açıkları"), b)
        self._sayfa_ham_analiz(kitap.create_sheet("Ham veri"), b)
        return kitap

    def _sayfa_analiz_ozet(self, sayfa: Worksheet, b: _Baglam) -> None:
        sayfa.title = "Özet"
        satir = self._basligi_yaz(sayfa, b, "Çizelge Analizi")
        sayfa.cell(satir, 1, "Hedef").font = _BASLIK_YAZI
        sayfa.cell(satir, 2, "Ceza").font = _BASLIK_YAZI
        for sutun in (1, 2):
            sayfa.cell(satir, sutun).fill = _BASLIK_DOLGU
        dokum = b.analiz.ceza_dokumu or {}
        for i, (kimlik, deger) in enumerate(sorted(dokum.items()), start=1):
            sayfa.cell(satir + i, 1, kimlik)
            sayfa.cell(satir + i, 2, round(float(deger), 1))
        son = satir + len(dokum) + 1
        sayfa.cell(son, 1, "TOPLAM").font = _BASLIK_YAZI
        sayfa.cell(
            son, 2, round(float(b.analiz.toplam_ceza), 1) if b.analiz.toplam_ceza else 0
        ).font = _BASLIK_YAZI
        _genislikleri_ayarla(sayfa, [16, 14])

    def _sayfa_adalet(self, sayfa: Worksheet, b: _Baglam) -> None:
        """Kisi basina gece / hafta sonu / toplam saat, ADIL PAY ve sapma.

        GRAFIKLERIN REFERANS CIZGISI ADIL PAYDIR, havuz ortalamasi degil.
        Ortalamayi gostermek S2'nin acikca reddettigi olcuyu dosyaya tasimak
        olurdu: erisilebilirligi kisitli bir havuz ona gore kalici olarak
        sapmali gorunur. Ayni hata ekranda bir kez yapildi ve Tur 6'da
        duzeltildi; dosyanin onu geri getirmemesi gerekir.
        """
        basliklar = [
            "Personel",
            "Gece saati",
            "Gece adil pay",
            "Hafta sonu saati",
            "Hafta sonu adil pay",
            "Toplam saat",
            "Toplam adil pay",
            "Toplam sapma",
        ]
        for sutun, metin in enumerate(basliklar, start=1):
            hucre = sayfa.cell(1, sutun, metin)
            hucre.font = _BASLIK_YAZI
            hucre.fill = _BASLIK_DOLGU

        gece = {k.personel_id: k for k in b.analiz.kisi_basina_gece}
        hafta_sonu = {k.personel_id: k for k in b.analiz.kisi_basina_hafta_sonu}
        for i, denge in enumerate(b.analiz.saat_dagilimi, start=2):
            g = gece.get(denge.personel_id)
            h = hafta_sonu.get(denge.personel_id)
            sayfa.cell(i, 1, denge.ad_soyad)
            sayfa.cell(i, 2, round(g.sayi, 1) if g else 0)
            sayfa.cell(i, 3, round(g.pay or 0.0, 1) if g else 0)
            sayfa.cell(i, 4, round(h.sayi, 1) if h else 0)
            sayfa.cell(i, 5, round(h.pay or 0.0, 1) if h else 0)
            sayfa.cell(i, 6, round(denge.toplam_saat, 1))
            sayfa.cell(i, 7, round(denge.hedef_saat, 1))
            sayfa.cell(i, 8, round(denge.sapma, 1))

        son_satir = len(b.analiz.saat_dagilimi) + 1
        if son_satir > 1:
            _adalet_grafigi(sayfa, "Gece saati", 2, 3, son_satir, "J2")
            _adalet_grafigi(sayfa, "Hafta sonu saati", 4, 5, son_satir, "J20")
            _adalet_grafigi(sayfa, "Toplam saat", 6, 7, son_satir, "J38")
        _genislikleri_ayarla(sayfa, [26, 12, 15, 17, 20, 13, 16, 14])

    def _sayfa_aciklar(self, sayfa: Worksheet, b: _Baglam) -> None:
        basliklar = ["Gün", "Saat aralığı", "Görev noktası", "Eksik kişi"]
        for sutun, metin in enumerate(basliklar, start=1):
            hucre = sayfa.cell(1, sutun, metin)
            hucre.font = _BASLIK_YAZI
            hucre.fill = _BASLIK_DOLGU
        if not b.aciklar:
            # Aciklarin YOKLUGU da bildirilir; bos bir sayfa "acik yok" ile
            # "rapor uretilmedi" arasindaki farki soylemez.
            sayfa.cell(2, 1, "Bu sürümde kapsama açığı yok.")
        for i, a in enumerate(b.aciklar, start=2):
            sayfa.cell(i, 1, a.baslangic_zamani.date().isoformat())
            # Aralik gun sinirini asabilir (B-23); metin iki damgadan kurulur.
            sayfa.cell(
                i, 2, f"{saat_metni(a.baslangic_zamani.time())}–{saat_metni(a.bitis_zamani.time())}"
            )
            sayfa.cell(i, 3, b.nokta_adi.get(a.nokta_id, ""))
            sayfa.cell(i, 4, a.eksik_sayi)
        _genislikleri_ayarla(sayfa, [14, 18, 22, 13])

    def _sayfa_ham_analiz(self, sayfa: Worksheet, b: _Baglam) -> None:
        """Yukaridaki tablolarin BICIMLENDIRILMEMIS hali."""
        basliklar = ["olcu", "personel_id", "ad", "deger", "adil_pay"]
        for sutun, metin in enumerate(basliklar, start=1):
            sayfa.cell(1, sutun, metin).font = _BASLIK_YAZI
        r = 2
        for olcu, kalemler in (
            ("gece_saati", b.analiz.kisi_basina_gece),
            ("hafta_sonu_saati", b.analiz.kisi_basina_hafta_sonu),
        ):
            for k in kalemler:
                sayfa.cell(r, 1, olcu)
                sayfa.cell(r, 2, k.personel_id)
                sayfa.cell(r, 3, k.ad_soyad)
                sayfa.cell(r, 4, k.sayi)
                sayfa.cell(r, 5, k.pay)
                r += 1
        for d in b.analiz.saat_dagilimi:
            sayfa.cell(r, 1, "toplam_saat")
            sayfa.cell(r, 2, d.personel_id)
            sayfa.cell(r, 3, d.ad_soyad)
            sayfa.cell(r, 4, d.toplam_saat)
            sayfa.cell(r, 5, d.hedef_saat)
            r += 1
        _genislikleri_ayarla(sayfa, [20, 14, 26, 12, 12])


def _adalet_grafigi(
    sayfa: Worksheet, baslik: str, deger_sutunu: int, pay_sutunu: int, son_satir: int, konum: str
) -> None:
    """Olculen deger CUBUK, adil pay CIZGI olarak ustune biner.

    openpyxl'de "referans cizgisi" diye bir nesne yok; bir cubuk grafigin
    uzerine ikinci bir cizgi grafik bindirilerek elde edilir. Cizgi kisiden
    kisiye degistigi icin duz bir yatay cizgi DEGILDIR - zaten oyle olmasi
    da yanlis olurdu (S2: hedef kisiye ozeldir).
    """
    cubuk = BarChart()
    cubuk.title = baslik
    cubuk.y_axis.title = "saat"
    cubuk.add_data(
        Reference(sayfa, min_col=deger_sutunu, min_row=1, max_row=son_satir), titles_from_data=True
    )
    cubuk.set_categories(Reference(sayfa, min_col=1, min_row=2, max_row=son_satir))

    cizgi = LineChart()
    cizgi.add_data(
        Reference(sayfa, min_col=pay_sutunu, min_row=1, max_row=son_satir), titles_from_data=True
    )
    cubuk += cizgi
    cubuk.height = 8
    cubuk.width = 18
    sayfa.add_chart(cubuk, konum)


def _genislikleri_ayarla(sayfa: Worksheet, genislikler: list[int]) -> None:
    for i, genislik in enumerate(genislikler, start=1):
        sayfa.column_dimensions[get_column_letter(i)].width = genislik


def dosya_adi(surum: CizelgeSurumu, ek: str) -> str:
    """`cizelge_2026-08-10_surum3.xlsx` — dönem ve sürüm adda durur.

    Ayni klasore inen iki dosya tarayicida "(1)" ile ayrisir ve o ad hangi
    surumun hangi donemi oldugunu soylemez.
    """
    return f"{ek}_surum{surum.surum_no}.xlsx"


__all__ = ["DisaAktarmaServisi", "dosya_adi"]
