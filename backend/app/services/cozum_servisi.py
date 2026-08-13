"""SDD 5.4: cozum isinin durum makinesi (Sekil 5.1) ve yasam dongusu yonetimi.

cozum_isini_calistir(), SDD 5.4'teki YORDAM'in birebir Python karsiligidir.

YURUTME BAGLAMI (SDD 3.4.4). Cozum isi AYRI BIR SISTEM SERVISI olarak
calisir; iki surec arasinda dogrudan iletisim yoktur, is durumu/ilerleme/
sonuc yalnizca veritabani uzerinden aktarilir. Bu yuzden:
  - `CozumServisi.baslat` surec ACMAZ, isi `kuyrukta` durumunda birakir.
  - `scripts/cozum_iscisi.py` kuyruktan is alip `cozum_isini_calistir`i
    cagirir.
  - Durdurma istegi de ayni kanaldan gelir: API isin durumunu DURDURULDU'ya
    ceker, isci bunu ARAMA SURERKEN duzenli araliklarla taze okur ve
    aramayi disaridan sonlandirir (SDD 5.4.2, bkz. _aramayi_sur).
Sprint 2 Gun 8'deki multiprocessing.Process ara cozumu kaldirildi.

DURDURMA COZUMU ATMAZ (SDD 5.4.1, SRS FR-4.9). Isci aramayi sonlandirdiginda
elindeki en iyi cozumu ATAMALARA degil `gecici_sonuc` alanina yazar; is
`durduruldu` durumunda kullanici kararini bekler. Kararin uygulanmasi
`durdurma_karari_uygula`dadir.
"""

import enum
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time
from decimal import Decimal
from typing import Any

from sqlalchemy import case, cast, literal, update
from sqlalchemy.orm import Session

from app.config import ayarlar
from app.cozucu import AramaKolu, CozucuAdaptoru, CozumSonucu, Ilerleme, model_kur
from app.kurallar.baglam import AtamaKaydi
from app.kurallar.kayit_defteri import kurallari_yukle
from app.kurallar.zaman_araligi import saatleri_araliklara_birlestir
from app.models.kural import Kural
from app.models.sonuc import (
    Atama,
    AtamaKaynagi,
    CizelgeSurumu,
    CizelgeSurumuDurumu,
    CozumIsi,
    CozumIsiDurumu,
    Donem,
)
from app.repositories.kural import KuralDeposu
from app.repositories.sonuc import (
    AtamaDeposu,
    CizelgeSurumuDeposu,
    CozumIsiDeposu,
    DonemDeposu,
    FazlaKadroDeposu,
    KapsamaAcigiDeposu,
)
from app.services.baglam_kurucu import baglam_olustur, donem_gunlerini_uret, zaman_ekseni_olustur
from app.services.on_kontrol import Bulgu, on_kontrol_yap

_VARSAYILAN_ZAMAN_LIMITI_SANIYE = 60
# SDD 5.4.2: ana dongunun durdurma istegini yoklama araligi (saniye).
_DURDURMA_YOKLAMA_ARALIGI_SANIYE = 0.5
_VARSAYILAN_FAZLA_CALISMA_ESIGI = Decimal(45)
_VARSAYILAN_AZAMI_GUNLUK_SAAT = Decimal(11)
_VARSAYILAN_HAFTALIK_ASGARI_IZIN_GUNU = 1

_COZUM_BULUNAMADI_MESAJI = "Cozucu, zaman limiti icinde uygun bir cizelge bulamadi"
_DURDURMADA_COZUM_YOK_MESAJI = (
    "Cozucu ilk uygun cizelgeye ulasmadan durduruldu; kullanilabilir bir sonuc yok"
)


def _araliklara_cevir(
    saat_eksikleri: dict[tuple[date, int, int], int],
) -> tuple[tuple[date, time, time, int, int], ...]:
    """Cozucunun `(gun, saat, nokta) -> eksik` ciktisini ARALIGA cevirir.

    Birlestirme YAZMA aninda yapilir (SDD 4.2.4) ve `dogrula` yolunun
    kullandigi ayni yardimciya dayanir; iki yerde yazilsaydi ayni cizelge
    icin farkli sayida acik kaydi uretilirdi.
    """
    nokta_saatleri: dict[int, dict[tuple[date, int], int]] = {}
    for (tarih, saat, nokta_id), sayi in saat_eksikleri.items():
        if sayi > 0:
            nokta_saatleri.setdefault(nokta_id, {})[(tarih, saat)] = sayi
    cikti: list[tuple[date, time, time, int, int]] = []
    for nokta_id, saatler in sorted(nokta_saatleri.items()):
        for tarih, bas, bit, sayi in saatleri_araliklara_birlestir(saatler):
            cikti.append((tarih, bas, bit, nokta_id, sayi))
    return tuple(cikti)


class Karar(enum.StrEnum):
    """SDD 5.4.1: durdurulan iste kullanicinin uc secenegi (SRS FR-4.10)."""

    KULLAN = "kullan"
    AT = "at"
    DEVAM = "devam"


class KararUygulanamazError(RuntimeError):
    """Karar, isin bulundugu duruma ya da elindeki sonuca uymuyor."""


class DurdurulamazError(RuntimeError):
    """Is, durdurulabilecek bir durumda degil (SDD 5.4.1)."""


# Durdurma istegi yalnizca bu durumlardaki isleri etkiler; digerleri zaten
# sonlanmis ya da karar bekliyordur.
_DURDURULABILIR_DURUMLAR = (
    CozumIsiDurumu.KUYRUKTA,
    CozumIsiDurumu.ON_KONTROL,
    CozumIsiDurumu.COZULUYOR,
)

_DURUM_SUTUN_TIPI = CozumIsi.__table__.c.durum.type


def _durum_degeri(durum: CozumIsiDurumu):  # noqa: ANN202 - SQLAlchemy ifadesi
    """CASE dalinda kullanilabilen, ACIKCA enum'a cevrilmis durum degeri.

    Cast sart: dallardaki parametreler tip bilgisi olmadan `text` baglanir
    ve PostgreSQL bir enum sutununa text yazmayi reddeder.
    """
    return cast(literal(durum, _DURUM_SUTUN_TIPI), _DURUM_SUTUN_TIPI)


# Reddedilen durdurma istegine verilecek yanit, KULLANICININ EKRANDA
# GORDUGU seye gore degisir; tek bir "durdurulamaz" mesaji, karar bekleyen
# bir isle coktan bitmis bir isi ayni kefeye koyardi.
_DURDURULAMAZ_MESAJLARI = {
    CozumIsiDurumu.DURDURULDU: "Is zaten durduruldu ve kararinizi bekliyor",
    CozumIsiDurumu.TAMAMLANDI: "Is tamamlandi; durdurulacak bir arama yok",
    CozumIsiDurumu.UYARILI: "Is tamamlandi; durdurulacak bir arama yok",
    CozumIsiDurumu.BASARISIZ: "Is basarisiz olarak sonlandi",
    CozumIsiDurumu.IPTAL: "Is zaten iptal edilmis",
}


@dataclass(frozen=True, slots=True)
class CozumYazmaVerisi:
    """Bir cozumun surume yazilmasi icin gereken her sey (SDD 5.4).

    IKI KAYNAKTAN gelir - cozucunun dogrudan sonucundan ve durdurulmus bir
    isin `gecici_sonuc`undan - ve TEK bir yazma yordamina (`_sonucu_yaz`)
    gider. Iki ayri yazma yolu birakilsaydi atamalarin, kapsama
    aciklarinin ve fazla kadro kayitlarinin birlikte yazilmasi kurali iki
    yerde tanimlanmis olurdu ve biri guncellenirken digeri geride
    kalabilirdi (SDD 5.4.1).
    """

    atamalar: tuple[tuple[int, date, int, int], ...]
    # (tarih, baslangic, bitis, nokta_id, sayi) — ARALIK (SDD 4.2.4).
    kapsama_eksikleri: tuple[tuple[date, time, time, int, int], ...]
    # Cozucu fazla kadro URETEMEZ (S1'in ust siniri modele zorunlu kisit
    # olarak giriyor), bu yuzden cozum sonucundan gelen deger her zaman
    # bostur. Alan yine de tasinir: SDD 4.2.4 gecici sonucun icerigini
    # boyle tanimlar ve yazma blogu ucuncu tabloyu da temizledigi icin
    # sozlesme eksiksiz kalir.
    fazla_kadro: tuple[tuple[date, time, time, int, int], ...] = ()
    ceza_dokumu: dict[str, float] = field(default_factory=dict)
    toplam_ceza: float | None = None
    sure_saniye: float | None = None

    @classmethod
    def cozum_sonucundan(cls, sonuc: CozumSonucu) -> "CozumYazmaVerisi":
        return cls(
            atamalar=tuple(sorted(sonuc.atanan_anahtarlar)),
            # Cozucunun SAAT eksenli eksikleri, yazma aninda ARALIGA
            # birlestirilir (SDD 4.2.4): birlestirme tek yerde, `dogrula`
            # yolunun kullandigi ayni yardimciyla yapilir.
            kapsama_eksikleri=_araliklara_cevir(sonuc.kapsama_eksikleri),
            ceza_dokumu={k: float(v) for k, v in sonuc.ceza_dokumu.items()},
            toplam_ceza=sonuc.toplam_ceza,
            sure_saniye=sonuc.sure_saniye,
        )

    def json_olarak(self) -> dict[str, Any]:
        """JSONB'ye yazilabilir bicim. Tarihler ISO dizeye cevrilir."""
        return {
            "atamalar": [
                [personel_id, tarih.isoformat(), vardiya_tipi_id, nokta_id]
                for personel_id, tarih, vardiya_tipi_id, nokta_id in self.atamalar
            ],
            "kapsama_eksikleri": [
                [tarih.isoformat(), bas.isoformat(), bit.isoformat(), nokta_id, sayi]
                for tarih, bas, bit, nokta_id, sayi in self.kapsama_eksikleri
            ],
            "fazla_kadro": [
                [tarih.isoformat(), bas.isoformat(), bit.isoformat(), nokta_id, sayi]
                for tarih, bas, bit, nokta_id, sayi in self.fazla_kadro
            ],
            "ceza_dokumu": self.ceza_dokumu,
            "toplam_ceza": self.toplam_ceza,
            "sure_saniye": self.sure_saniye,
        }

    @classmethod
    def jsondan(cls, veri: dict[str, Any]) -> "CozumYazmaVerisi":
        return cls(
            atamalar=tuple(
                (int(p), date.fromisoformat(g), int(v), int(n)) for p, g, v, n in veri["atamalar"]
            ),
            kapsama_eksikleri=tuple(
                (
                    date.fromisoformat(g),
                    time.fromisoformat(b),
                    time.fromisoformat(s),
                    int(n),
                    int(k),
                )
                for g, b, s, n, k in veri.get("kapsama_eksikleri", [])
            ),
            fazla_kadro=tuple(
                (
                    date.fromisoformat(g),
                    time.fromisoformat(b),
                    time.fromisoformat(s),
                    int(n),
                    int(k),
                )
                for g, b, s, n, k in veri.get("fazla_kadro", [])
            ),
            ceza_dokumu=dict(veri.get("ceza_dokumu") or {}),
            toplam_ceza=veri.get("toplam_ceza"),
            sure_saniye=veri.get("sure_saniye"),
        )


class CozumServisi:
    def __init__(self, oturum: Session) -> None:
        self.oturum = oturum
        self.donem = DonemDeposu(oturum)
        self.surum = CizelgeSurumuDeposu(oturum)
        self.is_ = CozumIsiDeposu(oturum)

    def baslat(
        self,
        donem_id: int | None = None,
        *,
        onceki_surum_id: int | None = None,
        surum_id: int | None = None,
        zaman_limiti_saniye: int = _VARSAYILAN_ZAMAN_LIMITI_SANIYE,
        cozum_ipucu: CozumYazmaVerisi | None = None,
        devam_kaynagi_is_id: int | None = None,
    ) -> CozumIsi | None:
        """Isi KUYRUGA YAZAR ve hemen doner; cozumu ayri bir SERVIS calistirir.

        SDD 3.4.4: cozum isi ayri bir sistem servisi olarak calisir ve iki
        surec arasinda dogrudan iletisim yoktur - is durumu, ilerleme ve
        sonuc yalnizca veritabani uzerinden aktarilir. Bu metot bu yuzden
        surec ACMAZ; isi `kuyrukta` durumunda birakir, `cozum_iscisi` onu
        alir (bkz. scripts/cozum_iscisi.py).

        onceki_surum_id verilirse SDD 5.6 (yeniden_coz): donem_id onceki
        surumden turetilir, yeni surum onceki_surum_id'ye baglanir (bkz.
        CizelgeSurumuDeposu.taslak_turet) - kilitli atamalarin sabitlenmesi
        ve S8 taban atamalari cozum_isini_calistir'de islenir.

        surum_id verilirse VAR OLAN surum icin yeni bir is acilir; "devam
        et" karari (SDD 5.4.1) bunu kullanir. Durdurulan is surume hicbir
        sey yazmamis oldugu icin yeni bir surum turetmek gereksiz bir
        bos kayit birakirdi.
        """
        surum: CizelgeSurumu | None
        if surum_id is not None:
            surum = self.surum.getir(surum_id)
            if surum is None:
                return None
        elif onceki_surum_id is not None:
            surum = self.surum.taslak_turet(onceki_surum_id)
            if surum is None:
                return None
        else:
            if donem_id is None or self.donem.getir(donem_id) is None:
                return None
            surum_no = self.surum.donem_icin_sonraki_surum_no(donem_id)
            surum = self.surum.olustur(
                donem_id=donem_id, surum_no=surum_no, durum=CizelgeSurumuDurumu.TASLAK
            )
        self.oturum.flush()

        is_kaydi = self.is_.olustur(
            surum_id=surum.surum_id,
            durum=CozumIsiDurumu.KUYRUKTA,
            baslangic_zamani=datetime.now(UTC),
            zaman_limiti_saniye=zaman_limiti_saniye,
            kural_anlik_goruntu={},
            # Ipucu KENDI sutununda tasinir (SDD 4.2.4). `gecici_sonuc`
            # isin ciktisidir; ikisini tek alanda birlestirmek, ayni degeri
            # bir iste "karar bekliyor", baskasinda "modele verilecek
            # ipucu" anlamina getirirdi.
            cozum_ipucu=cozum_ipucu.json_olarak() if cozum_ipucu is not None else None,
            devam_kaynagi_is_id=devam_kaynagi_is_id,
        )
        self.oturum.flush()
        # Isciyi ayri bir SERVIS oldugu icin ancak onaylanmis satirlar
        # gorur; kuyruga yazmak bu commit ile tamamlanir.
        self.oturum.commit()
        return is_kaydi


def cozum_isini_calistir(oturum: Session, is_id: int) -> None:
    """SDD 5.4 YORDAM cozum_isini_calistir(is_id)'nin birebir uygulamasi."""
    is_depo = CozumIsiDeposu(oturum)
    surum_depo = CizelgeSurumuDeposu(oturum)
    donem_depo = DonemDeposu(oturum)
    kural_depo = KuralDeposu(oturum)
    atama_depo = AtamaDeposu(oturum)

    is_kaydi = is_depo.getir(is_id)
    if is_kaydi is None:
        return
    surum = surum_depo.getir(is_kaydi.surum_id)
    donem = donem_depo.getir(surum.donem_id)

    is_kaydi.durum = CozumIsiDurumu.ON_KONTROL
    oturum.commit()

    # ON KONTROL BULGULARI ISI DUSURMEZ (SDD 5.2, SRS FR-5.1/FR-5.2, karar
    # notu K18). Onceki davranis, yapisal bir bulguda cozumu hic
    # baslatmiyordu; sonucta sürüm "basarisiz" damgasiyla, TEK BIR ATAMA
    # OLMADAN kaliyordu. Bu, "personel yetersizliginde cozumu reddetmek
    # yerine cizelgeyi uret ve kapsama aciklarini goster" gereksinimini
    # dogrudan ihlal ediyor ve S1'in zorunlu kisit yerine baskin agirlikli
    # ESNEK hedef olarak tasarlanmasinin tek gerekcesini islevsiz
    # birakiyordu.
    #
    # On kontrolun soyleyebildigi ile cozucunun soyleyebildigi ayni sey
    # degildir: on kontrol kadro aritmetigine bakar ve "su kadar acik
    # olusacak" der; HANGI GUN, HANGI SAAT, HANGI NOKTADA olusacagini
    # soyleyemez. Kullanicinin acigi kapatmak icin ihtiyac duydugu bilgi
    # ikincisidir ve yalnizca cozucu uretir.
    #
    # Bulgular sonucla BIRLIKTE gosterilir ve is kaydinda KALICI olur;
    # yalnizca cozum aninda gorunup kaybolan bir bilgi, yayinlanmis
    # cizelgeye sonradan bakan kisi icin hic var olmamistir.
    bulgular = _on_kontrolu_calistir(oturum, kural_depo, donem)
    is_kaydi.on_kontrol_bulgulari = [_bulguyu_json_yap(b) for b in bulgular]
    oturum.commit()

    kural_satirlari = list(kural_depo.aktif_kurallari_getir())
    kurallar = kurallari_yukle(kural_satirlari)
    is_kaydi.kural_anlik_goruntu = _kural_anlik_goruntu_olustur(kural_satirlari)
    oturum.commit()

    baglam = baglam_olustur(oturum, donem)
    zaman_ekseni = zaman_ekseni_olustur(donem)

    kilitli_atamalar: list[AtamaKaydi] = []
    if surum.onceki_surum_id is not None:
        # SDD 5.6 yeniden_coz: onceki_atamalar S8'in taban aldigi cizelge
        # (baglam.onceki_atamalar), kilitli olanlar ise modele x=1 olarak
        # sabitlenir (bkz. model_kur'un kilitli_atamalar parametresi).
        onceki_atama_satirlari = atama_depo.surume_gore_getir(surum.onceki_surum_id)
        onceki_atamalar = [
            AtamaKaydi(a.personel_id, a.tarih, a.vardiya_tipi_id, a.nokta_id)
            for a in onceki_atama_satirlari
        ]
        baglam.onceki_atamalar = onceki_atamalar
        kilitli_atamalar = [
            AtamaKaydi(a.personel_id, a.tarih, a.vardiya_tipi_id, a.nokta_id)
            for a in onceki_atama_satirlari
            if a.kilitli
        ]

    # SDD 4.2.4 "devam et" ipucu: kendi sutunundan okunur ve BURADA
    # BOSALTILMAZ. Bosaltma is sonlandiginda yapilir (`_isi_sonlandir`);
    # burada silinseydi, isci yeniden basladiginda is ipucusuz devam eder ve
    # sonuc sessizce kotulesirdi.
    model, x, baglam, ceza_terimleri = model_kur(
        baglam,
        zaman_ekseni,
        kurallar,
        kilitli_atamalar=kilitli_atamalar or None,
        cozum_ipucu=_ipucunu_al(is_kaydi),
    )

    # Model kurulurken (uzun surebilir) durdurma istenmis olabilir.
    # `kuyrukta`/`on_kontrol`teki bir ise gelen durdurma DOGRUDAN IPTALDIR
    # (SDD 5.4.1): karar noktasi yalnizca arama sururken dogar.
    durum = _taze_durum(oturum, is_kaydi)
    if durum is CozumIsiDurumu.IPTAL:
        return  # API isi zaten sonlandirdi; yazilacak hicbir sey yok
    if durum is CozumIsiDurumu.DURDURULDU:
        _durdurulmus_olarak_kapat(oturum, is_kaydi, sonuc=None)
        return

    is_kaydi.durum = CozumIsiDurumu.COZULUYOR
    oturum.commit()

    kol = CozucuAdaptoru.aramayi_baslat(
        model,
        x,
        zaman_limiti_saniye=is_kaydi.zaman_limiti_saniye,
        arama_iscisi_sayisi=ayarlar.cozucu_arama_iscisi_sayisi,
        ceza_terimleri=ceza_terimleri,
        kapsama_degiskenleri=baglam.kapsama_eksikleri,
    )
    _aramayi_sur(oturum, is_kaydi, kol)
    sonuc = kol.sonuc()

    # SDD 5.4.1: durdurma cozumu ATMAZ. Elde ne varsa `gecici_sonuc`a yazilir
    # ve is kullanici kararini bekler; atamalara hicbir sey yazilmaz.
    if sonuc.durduruldu or _durdurma_istendi_mi(oturum, is_kaydi):
        _durdurulmus_olarak_kapat(oturum, is_kaydi, sonuc=sonuc)
        return

    if sonuc.durum == "cozum_yok":
        is_kaydi.hata_mesaji = _COZUM_BULUNAMADI_MESAJI
        _isi_sonlandir(is_kaydi, CozumIsiDurumu.BASARISIZ)
        oturum.commit()
        return

    _sonucu_yaz(oturum, is_kaydi, surum, CozumYazmaVerisi.cozum_sonucundan(sonuc))
    oturum.commit()


def _sonucu_yaz(
    oturum: Session, is_kaydi: CozumIsi, surum: CizelgeSurumu, veri: CozumYazmaVerisi
) -> None:
    """SDD 5.4'teki yazma blogu. TEK kopya (SDD 5.4.1).

    Hem cozumun normal tamamlanma yolu hem de durdurmadaki "kullan" karari
    buradan gecer. Cagiran taraf ONAYLAMAZ: yazma, cagiranin islemi icinde
    kalir, boylece atamalar - kapsama aciklari - fazla kadro ucusu tek bir
    veritabani isleminde yazilir. Yarim kalmis bir cizelge, kural ihlali
    icermeyen fakat kapsamasi eksik bir cizelgeden ayirt edilemez.
    """
    AtamaDeposu(oturum).surume_gore_sil(surum.surum_id)
    kapsama_depo = KapsamaAcigiDeposu(oturum)
    kapsama_depo.surume_gore_sil(surum.surum_id)
    # Fazla kadro satirlari da temizlenir. Cozucu boyle bir satir URETEMEZ
    # (S1'in ust siniri modele zorunlu kisit olarak giriyor), ama surum
    # yeniden cozulmeden ONCE elle duzenlenmis olabilir; o turdan kalan
    # satirlar cozucunun urettigi yeni cizelgeyle ilgisiz olurdu.
    fazla_depo = FazlaKadroDeposu(oturum)
    fazla_depo.surume_gore_sil(surum.surum_id)

    for personel_id, tarih, vardiya_tipi_id, nokta_id in veri.atamalar:
        oturum.add(
            Atama(
                surum_id=surum.surum_id,
                personel_id=personel_id,
                tarih=tarih,
                vardiya_tipi_id=vardiya_tipi_id,
                nokta_id=nokta_id,
                kaynak=AtamaKaynagi.COZUCU,
            )
        )
    for tarih, bas, bit, nokta_id, eksik_sayi in veri.kapsama_eksikleri:
        kapsama_depo.olustur(
            surum_id=surum.surum_id,
            tarih=tarih,
            baslangic=bas,
            bitis=bit,
            nokta_id=nokta_id,
            eksik_sayi=eksik_sayi,
        )
    for tarih, bas, bit, nokta_id, fazla_sayi in veri.fazla_kadro:
        fazla_depo.olustur(
            surum_id=surum.surum_id,
            tarih=tarih,
            baslangic=bas,
            bitis=bit,
            nokta_id=nokta_id,
            fazla_sayi=fazla_sayi,
        )

    is_kaydi.ceza_dokumu = dict(veri.ceza_dokumu)
    is_kaydi.en_iyi_ceza = _ondalik(veri.toplam_ceza) if veri.toplam_ceza is not None else None
    is_kaydi.sure_saniye = _ondalik(veri.sure_saniye) if veri.sure_saniye is not None else None
    _isi_sonlandir(
        is_kaydi,
        CozumIsiDurumu.UYARILI if veri.kapsama_eksikleri else CozumIsiDurumu.TAMAMLANDI,
    )
    surum.durum = CizelgeSurumuDurumu.COZULDU


def durdurma_istegini_uygula(oturum: Session, is_id: int) -> CozumIsi:
    """SDD 5.4.1: durdurma istegini isin BULUNDUGU DURUMA gore uygular.

    Karar noktasi yalnizca arama sururken dogar:

      cozuluyor            -> durduruldu, kullanici karari beklenir
      kuyrukta/on_kontrol  -> iptal, karar sorulmaz

    Ikincisinde henuz arama baslamamistir; saklanacak bir sonuc, dolayisiyla
    verilecek bir karar da yoktur. Boyle bir iste karar paneli acmak, uc
    secenekten ikisini anlamsiz ("kullan" - ortada sonuc yok), birini de
    zaten var olan bir eylemin uzun yolu ("devam" - isi iptal edip yenisini
    baslatmak) hale getirirdi.

    GECIS TEK BIR KOSULLU UPDATE'TIR. Once okuyup sonra yazsaydik, tam o
    aralikta isci isi `on_kontrol`den `cozuluyor`a gecirmis olabilirdi ve
    karar noktasi dogmasi gereken bir is SESSIZCE iptal edilirdi. Burada
    hangi yola girildigini veritabaninin dondurdugu satir soyler.
    """
    yeni_durum = oturum.execute(
        update(CozumIsi)
        .where(CozumIsi.is_id == is_id, CozumIsi.durum.in_(_DURDURULABILIR_DURUMLAR))
        .values(
            durum=case(
                (
                    CozumIsi.durum == CozumIsiDurumu.COZULUYOR,
                    _durum_degeri(CozumIsiDurumu.DURDURULDU),
                ),
                else_=_durum_degeri(CozumIsiDurumu.IPTAL),
            )
        )
        .returning(CozumIsi.durum)
    ).scalar_one_or_none()

    is_kaydi = CozumIsiDeposu(oturum).getir(is_id)
    if yeni_durum is None:
        if is_kaydi is None:
            raise LookupError("Cozum isi bulunamadi")
        raise DurdurulamazError(_DURDURULAMAZ_MESAJLARI[is_kaydi.durum])

    assert is_kaydi is not None  # UPDATE satiri bulduysa kayit da vardir
    if yeni_durum is CozumIsiDurumu.IPTAL:
        # Isci bu isi hic almayacak (kapma sorgusu yalniz `kuyrukta`yi
        # secer) ya da aldiysa model kurulumundan sonraki taze okumada
        # gorup hicbir sey yazmadan cikacak. Terminal bakim burada yapilir.
        _isi_sonlandir(is_kaydi, CozumIsiDurumu.IPTAL)
    oturum.commit()
    return is_kaydi


def durdurma_karari_uygula(
    oturum: Session,
    is_id: int,
    karar: Karar,
    *,
    zaman_limiti_saniye: int | None = None,
) -> tuple[CozumIsi, CozumIsi | None]:
    """SDD 5.4.1 YORDAM durdurma_karari_uygula(is_id, karar, yeni_zaman_limiti).

    Durdurulan isi ve - "devam" karariysa - baslatilan yeni isi dondurur.
    """
    is_depo = CozumIsiDeposu(oturum)
    is_kaydi = is_depo.getir(is_id)
    if is_kaydi is None:
        raise LookupError("Cozum isi bulunamadi")
    if is_kaydi.durum is not CozumIsiDurumu.DURDURULDU:
        raise KararUygulanamazError("Is karar bekleyen durumda degil")

    gecici = is_kaydi.gecici_sonuc

    if karar is Karar.KULLAN:
        if not gecici:
            # Bos bir sonucun sessizce bos cizelge olarak yazilmasi, kural
            # ihlali icermeyen ama kapsamasi sifir olan bir surum uretirdi
            # ve bu, gercekten cozulmus bir cizelgeden ayirt edilemezdi
            # (SDD 5.4.1).
            raise KararUygulanamazError("Kullanilabilir cozum yok")
        surum = CizelgeSurumuDeposu(oturum).getir(is_kaydi.surum_id)
        _sonucu_yaz(oturum, is_kaydi, surum, CozumYazmaVerisi.jsondan(gecici))
        is_kaydi.gecici_sonuc = None
        oturum.commit()
        return is_kaydi, None

    if karar is Karar.AT:
        # Surum hic degismedi: sonuc atamalara yazilmamisti, dolayisiyla
        # geri alinacak bir sey de yok (SDD 4.2.4).
        is_kaydi.gecici_sonuc = None
        _isi_sonlandir(is_kaydi, CozumIsiDurumu.IPTAL)
        oturum.commit()
        return is_kaydi, None

    yeni_is = CozumServisi(oturum).baslat(
        surum_id=is_kaydi.surum_id,
        zaman_limiti_saniye=zaman_limiti_saniye or is_kaydi.zaman_limiti_saniye,
        cozum_ipucu=CozumYazmaVerisi.jsondan(gecici) if gecici else None,
        devam_kaynagi_is_id=is_kaydi.is_id,
    )
    if yeni_is is None:
        raise KararUygulanamazError("Isin surumu bulunamadi")
    is_kaydi.gecici_sonuc = None
    _isi_sonlandir(is_kaydi, CozumIsiDurumu.IPTAL)
    oturum.commit()
    return is_kaydi, yeni_is


def _aramayi_sur(oturum: Session, is_kaydi: CozumIsi, kol: AramaKolu) -> None:
    """Arama surerken ilerlemeyi yazar ve durdurma istegini yoklar (SDD 5.4.2).

    Bu dongu oturumun TEK sahibidir; arama ayri bir is parcaciginda yurur ve
    veritabanina hic dokunmaz (SQLAlchemy oturumu is parcaciklari arasinda
    paylasilamaz). Ilerleme koldan okunur, durdurma istegi kayittan TAZE
    okunur, istek gorulunce arama disaridan sonlandirilir.

    Yoklama araligi, durdurmanin olculen gecikmesinin ust siniridir: istek
    en kotu ihtimalle bir aralik kadar bekler, `stop_search` sonrasi arama
    milisaniyeler icinde doner. Eski yolda gecikmenin ust siniri iki
    iyilesme arasindaki sessizlikti - yani zaman limitinin kendisi.
    """
    yazilan: Ilerleme | None = None
    durduruldu = False
    while not kol.bekle(_DURDURMA_YOKLAMA_ARALIGI_SANIYE):
        ilerleme = kol.son_ilerleme()
        if ilerleme is not None and ilerleme != yazilan:
            yazilan = ilerleme
            is_kaydi.en_iyi_ceza = _ondalik(ilerleme.ceza)
            oturum.commit()
        if not durduruldu and _durdurma_istendi_mi(oturum, is_kaydi):
            kol.durdur()
            durduruldu = True


def _isi_sonlandir(is_kaydi: CozumIsi, durum: CozumIsiDurumu) -> None:
    """Terminal duruma gecisin TEK yeri (SDD 4.2.4).

    `tamamlandi`, `uyarili`, `basarisiz` ve `iptal` buradan gecer;
    `durduruldu` GECMEZ - o terminal degildir, is orada kullanici kararini
    bekler ve ipucunu hala tasiyor olabilir.

    Iki bakim isi burada toplandi. Birincisi `cozum_ipucu`nun bosaltilmasi:
    alan yalnizca calisan bir isin girdisidir, sonlanmis bir iste tasidigi
    deger hicbir sey ifade etmez. Ikincisi `bitis_zamani`; DAHA ONCE
    YAZILMISSA DOKUNULMAZ, cunku durdurulan bir iste o damga ARAMANIN
    bittigi ani tasir ve kullanicinin karar verme suresi ona eklenmemelidir
    (SDD 4.2.4).
    """
    is_kaydi.durum = durum
    is_kaydi.cozum_ipucu = None
    if is_kaydi.bitis_zamani is None:
        is_kaydi.bitis_zamani = datetime.now(UTC)


def _ipucunu_al(is_kaydi: CozumIsi) -> list[AtamaKaydi] | None:
    """ "Devam et" karariyla acilmis isin devraldigi cozum (SDD 4.2.4).

    OKUR, BOSALTMAZ. Bosaltma is sonlandiginda yapilir (`_isi_sonlandir`):
    burada silinseydi, isci yeniden basladiginda is ipucusuz devam eder ve
    sonuc sessizce kotulesirdi.
    """
    if not is_kaydi.cozum_ipucu:
        return None
    veri = CozumYazmaVerisi.jsondan(is_kaydi.cozum_ipucu)
    return [AtamaKaydi(p, g, v, n) for p, g, v, n in veri.atamalar]


def _taze_durum(oturum: Session, is_kaydi: CozumIsi) -> CozumIsiDurumu:
    """Isin durumunu VERITABANINDAN taze okur.

    Durdurma icin ayri bir bayrak sutunu yoktur; bilgiyi `durum` alani
    zaten tasir. API `/api/cozum/{id}/durdur` cagrisinda isi - hangi
    durumda oldugua gore - `durduruldu` ya da `iptal`e ceker (SDD 5.4.1).
    Isci ayri bir servis oldugundan (SDD 3.4.4) API o sureci olduremez;
    tek haberlesme kanali veritabanidir.

    `refresh` sart: is_kaydi bu oturumun kimlik haritasinda onbelleklidir ve
    API'nin BASKA bir baglantidan yaptigi degisiklik yeniden okunmadan
    gorulmez.
    """
    oturum.refresh(is_kaydi, ["durum"])
    return is_kaydi.durum


def _durdurma_istendi_mi(oturum: Session, is_kaydi: CozumIsi) -> bool:
    """Arama SURERKEN durdurma istegi geldi mi?"""
    return _taze_durum(oturum, is_kaydi) is CozumIsiDurumu.DURDURULDU


def _durdurulmus_olarak_kapat(
    oturum: Session, is_kaydi: CozumIsi, *, sonuc: CozumSonucu | None
) -> None:
    """Aramayi sonlandirir ve isi KULLANICI KARARINA birakir (SDD 5.4.1).

    Elde bir cozum varsa `gecici_sonuc`a yazilir - atamalara DEGIL. Surum
    dokunulmamis kalir; "at" karari bu yuzden bedelsizdir.

    Cozucu ilk uygun cizelgeye ulasamadan durdurulmussa alan bos kalir ve
    nedeni `hata_mesaji`na yazilir; arayuz "kullan" secenegini bu durumda
    pasif gosterir (SRS FR-4.10).
    """
    if sonuc is not None and sonuc.durum != "cozum_yok":
        veri = CozumYazmaVerisi.cozum_sonucundan(sonuc)
        is_kaydi.gecici_sonuc = veri.json_olarak()
        is_kaydi.ceza_dokumu = dict(veri.ceza_dokumu)
        is_kaydi.en_iyi_ceza = _ondalik(veri.toplam_ceza) if veri.toplam_ceza is not None else None
        is_kaydi.sure_saniye = _ondalik(veri.sure_saniye) if veri.sure_saniye is not None else None
    else:
        is_kaydi.gecici_sonuc = None
        is_kaydi.hata_mesaji = _DURDURMADA_COZUM_YOK_MESAJI
        if sonuc is not None:
            is_kaydi.sure_saniye = _ondalik(sonuc.sure_saniye)
    # `_isi_sonlandir`den GECMEZ: `durduruldu` terminal degildir, is burada
    # kullanici kararini bekler ve - "devam et" ile acilmis bir isse -
    # ipucunu hala tasir.
    is_kaydi.durum = CozumIsiDurumu.DURDURULDU
    # ARAMANIN bittigi an. Karar daha sonra verilir ve bu damgayi
    # degistirmez (SDD 4.2.4): olculen sure aramanin suresidir, kullanicinin
    # dusunme suresi degil.
    is_kaydi.bitis_zamani = datetime.now(UTC)
    oturum.commit()


def _on_kontrolu_calistir(oturum: Session, kural_depo: KuralDeposu, donem: Donem) -> list[Bulgu]:
    baglam = baglam_olustur(oturum, donem)
    donem_gunleri = donem_gunlerini_uret(donem.baslangic_tarihi, donem.bitis_tarihi)
    # Kapasite hesabi FAZLA CALISMA ESIGINDEN gecer (SRS 3.3.6); H5'in
    # mutlak tavani surdurulebilir tempo degil, asilamayan sinirdir.
    fazla_calisma_esigi = Decimal(
        kural_depo.parametre_getir(
            "H10", "fazla_calisma_esigi", varsayilan=_VARSAYILAN_FAZLA_CALISMA_ESIGI
        )
    )
    azami_gunluk_saat = Decimal(
        kural_depo.parametre_getir(
            "H9", "azami_gunluk_saat", varsayilan=_VARSAYILAN_AZAMI_GUNLUK_SAAT
        )
    )
    haftalik_asgari_izin_gunu = int(
        kural_depo.parametre_getir(
            "H6",
            "haftalik_asgari_izin_gunu",
            varsayilan=_VARSAYILAN_HAFTALIK_ASGARI_IZIN_GUNU,
        )
    )
    return on_kontrol_yap(
        baglam,
        donem_gunleri,
        fazla_calisma_esigi=fazla_calisma_esigi,
        azami_gunluk_saat=azami_gunluk_saat,
        haftalik_asgari_izin_gunu=haftalik_asgari_izin_gunu,
        aktif_kural_kimlikleri=frozenset(k.kimlik for k in kural_depo.aktif_kurallari_getir()),
    )


def _bulguyu_json_yap(bulgu: Bulgu) -> dict[str, Any]:
    """Bulguyu is kaydinda SAKLANABILIR bicime cevirir (SDD 5.2).

    Bulgular sonucla birlikte gosterilmek ve surum raporunda kalici olmak
    zorunda; cozum anindaki gecici bir liste bunu saglamaz.
    """
    return {
        "tip": bulgu.tip.value,
        "aciklama": bulgu.aciklama,
        "kesin_mi": bulgu.kesin_mi,
        "eksik": bulgu.eksik,
        "tarih": bulgu.tarih.isoformat() if bulgu.tarih else None,
    }


def _bulgulari_ozetle(bulgular: list[Bulgu]) -> str:
    return "; ".join(b.aciklama for b in bulgular)


def _kural_anlik_goruntu_olustur(kural_satirlari: Sequence[Kural]) -> dict:
    return {
        satir.kimlik: {
            "tip": satir.tip.value,
            "parametreler": satir.parametreler,
            "agirlik": satir.agirlik,
        }
        for satir in kural_satirlari
    }


def _ondalik(deger: float) -> Decimal:
    return Decimal(str(round(deger, 2)))
