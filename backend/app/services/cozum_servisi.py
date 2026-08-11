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
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.config import ayarlar
from app.cozucu import AramaKolu, CozucuAdaptoru, CozumSonucu, Ilerleme, model_kur
from app.kurallar.baglam import AtamaKaydi
from app.kurallar.kayit_defteri import kurallari_yukle
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
from app.services.on_kontrol import Bulgu, engelleyenler, on_kontrol_yap

_VARSAYILAN_ZAMAN_LIMITI_SANIYE = 60
# SDD 5.4.2: ana dongunun durdurma istegini yoklama araligi (saniye).
_DURDURMA_YOKLAMA_ARALIGI_SANIYE = 0.5
_VARSAYILAN_AZAMI_HAFTALIK_SAAT = Decimal(45)
_VARSAYILAN_HAFTALIK_ASGARI_IZIN_GUNU = 1

_COZUM_BULUNAMADI_MESAJI = "Cozucu, zaman limiti icinde uygun bir cizelge bulamadi"
_DURDURMADA_COZUM_YOK_MESAJI = (
    "Cozucu ilk uygun cizelgeye ulasmadan durduruldu; kullanilabilir bir sonuc yok"
)


class Karar(enum.StrEnum):
    """SDD 5.4.1: durdurulan iste kullanicinin uc secenegi (SRS FR-4.10)."""

    KULLAN = "kullan"
    AT = "at"
    DEVAM = "devam"


class KararUygulanamazError(RuntimeError):
    """Karar, isin bulundugu duruma ya da elindeki sonuca uymuyor."""


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
    kapsama_eksikleri: tuple[tuple[date, int, int, int], ...]
    # Cozucu fazla kadro URETEMEZ (S1'in ust siniri modele zorunlu kisit
    # olarak giriyor), bu yuzden cozum sonucundan gelen deger her zaman
    # bostur. Alan yine de tasinir: SDD 4.2.4 gecici sonucun icerigini
    # boyle tanimlar ve yazma blogu ucuncu tabloyu da temizledigi icin
    # sozlesme eksiksiz kalir.
    fazla_kadro: tuple[tuple[date, int, int, int], ...] = ()
    ceza_dokumu: dict[str, float] = field(default_factory=dict)
    toplam_ceza: float | None = None
    sure_saniye: float | None = None

    @classmethod
    def cozum_sonucundan(cls, sonuc: CozumSonucu) -> "CozumYazmaVerisi":
        return cls(
            atamalar=tuple(sorted(sonuc.atanan_anahtarlar)),
            kapsama_eksikleri=tuple(
                (tarih, vardiya_tipi_id, nokta_id, eksik_sayi)
                for (tarih, vardiya_tipi_id, nokta_id), eksik_sayi in sorted(
                    sonuc.kapsama_eksikleri.items()
                )
            ),
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
                [tarih.isoformat(), vardiya_tipi_id, nokta_id, sayi]
                for tarih, vardiya_tipi_id, nokta_id, sayi in self.kapsama_eksikleri
            ],
            "fazla_kadro": [
                [tarih.isoformat(), vardiya_tipi_id, nokta_id, sayi]
                for tarih, vardiya_tipi_id, nokta_id, sayi in self.fazla_kadro
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
                (date.fromisoformat(g), int(v), int(n), int(sayi))
                for g, v, n, sayi in veri.get("kapsama_eksikleri", [])
            ),
            fazla_kadro=tuple(
                (date.fromisoformat(g), int(v), int(n), int(sayi))
                for g, v, n, sayi in veri.get("fazla_kadro", [])
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
            # Ipucu, YENI isin kendi `gecici_sonuc` alaninda tasinir ve
            # model kurulur kurulmaz bosaltilir (SDD 5.4.1). Kaynak isin
            # alani kararla birlikte bosaldigi icin ipucunu orada
            # birakmak, "karar bir kez okuyup bosaltir" sozlesmesini
            # bozardi.
            gecici_sonuc=cozum_ipucu.json_olarak() if cozum_ipucu is not None else None,
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

    bulgular = _on_kontrolu_calistir(oturum, kural_depo, donem)
    # Yalnizca YAPISAL engeller isi durdurur. Yapilandirma uyarilari (or. S1
    # pasif) kullanicinin bilincli bir ayari olabilir; sistem onun yerine
    # karar vermez, uyariyi is kaydina yazar ve cozume devam eder.
    engeller = engelleyenler(bulgular)
    if engeller:
        is_kaydi.durum = CozumIsiDurumu.BASARISIZ
        is_kaydi.hata_mesaji = _bulgulari_ozetle(engeller)
        is_kaydi.bitis_zamani = datetime.now(UTC)
        oturum.commit()
        return
    if bulgular:
        is_kaydi.hata_mesaji = _bulgulari_ozetle(bulgular)
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

    # SDD 5.4.1 "devam et": is bir ipucuyla baslatildiysa ipucu kendi
    # `gecici_sonuc` alanindadir. Modele islendikten HEMEN SONRA bosaltilir;
    # boylece alan, bu isin kendi durdurma sonucundan baska bir sey tasimaz.
    ipucu_atamalari = _ipucunu_al(is_kaydi)

    model, x, baglam, ceza_terimleri = model_kur(
        baglam,
        zaman_ekseni,
        kurallar,
        kilitli_atamalar=kilitli_atamalar or None,
        cozum_ipucu=ipucu_atamalari,
    )
    if is_kaydi.gecici_sonuc is not None:
        is_kaydi.gecici_sonuc = None
        oturum.commit()

    # Model kurulurken (uzun surebilir) durdurma istenmis olabilir.
    if _durdurma_istendi_mi(oturum, is_kaydi):
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
        is_kaydi.durum = CozumIsiDurumu.BASARISIZ
        is_kaydi.hata_mesaji = _COZUM_BULUNAMADI_MESAJI
        is_kaydi.bitis_zamani = datetime.now(UTC)
        oturum.commit()
        return

    _sonucu_yaz(oturum, is_kaydi, surum, CozumYazmaVerisi.cozum_sonucundan(sonuc))
    is_kaydi.bitis_zamani = datetime.now(UTC)
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
    for tarih, vardiya_tipi_id, nokta_id, eksik_sayi in veri.kapsama_eksikleri:
        kapsama_depo.olustur(
            surum_id=surum.surum_id,
            tarih=tarih,
            vardiya_tipi_id=vardiya_tipi_id,
            nokta_id=nokta_id,
            eksik_sayi=eksik_sayi,
        )
    for tarih, vardiya_tipi_id, nokta_id, fazla_sayi in veri.fazla_kadro:
        fazla_depo.olustur(
            surum_id=surum.surum_id,
            tarih=tarih,
            vardiya_tipi_id=vardiya_tipi_id,
            nokta_id=nokta_id,
            fazla_sayi=fazla_sayi,
        )

    is_kaydi.ceza_dokumu = dict(veri.ceza_dokumu)
    is_kaydi.en_iyi_ceza = _ondalik(veri.toplam_ceza) if veri.toplam_ceza is not None else None
    is_kaydi.sure_saniye = _ondalik(veri.sure_saniye) if veri.sure_saniye is not None else None
    is_kaydi.durum = CozumIsiDurumu.UYARILI if veri.kapsama_eksikleri else CozumIsiDurumu.TAMAMLANDI
    surum.durum = CizelgeSurumuDurumu.COZULDU


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
        is_kaydi.durum = CozumIsiDurumu.IPTAL
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
    is_kaydi.durum = CozumIsiDurumu.IPTAL
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


def _ipucunu_al(is_kaydi: CozumIsi) -> list[AtamaKaydi] | None:
    """ "Devam et" karariyla acilmis isin devraldigi cozum (SDD 5.4.1)."""
    if is_kaydi.devam_kaynagi_is_id is None or not is_kaydi.gecici_sonuc:
        return None
    veri = CozumYazmaVerisi.jsondan(is_kaydi.gecici_sonuc)
    return [AtamaKaydi(p, g, v, n) for p, g, v, n in veri.atamalar]


def _durdurma_istendi_mi(oturum: Session, is_kaydi: CozumIsi) -> bool:
    """Durdurma bayragini VERITABANINDAN taze okur.

    Bayrak ayri bir sutun degil, `durum` alanidir: API
    `/api/cozum/{id}/durdur` cagrisinda durumu DURDURULDU'ya ceker (SDD
    5.4.1). Isci ayri bir servis oldugundan (SDD 3.4.4) API o sureci
    olduremez; tek haberlesme kanali veritabanidir.

    `refresh` sart: is_kaydi bu oturumun kimlik haritasinda onbelleklidir ve
    API'nin BASKA bir baglantidan yaptigi degisiklik yeniden okunmadan
    gorulmez.
    """
    oturum.refresh(is_kaydi, ["durum"])
    return is_kaydi.durum == CozumIsiDurumu.DURDURULDU


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
    is_kaydi.durum = CozumIsiDurumu.DURDURULDU
    # ARAMANIN bittigi an. Karar daha sonra verilir ve bu damgayi
    # degistirmez: alan "isin sonlandigi an"i tasir (SDD 4.2.4), kararin
    # verildigi ani degil.
    is_kaydi.bitis_zamani = datetime.now(UTC)
    oturum.commit()


def _on_kontrolu_calistir(oturum: Session, kural_depo: KuralDeposu, donem: Donem) -> list[Bulgu]:
    baglam = baglam_olustur(oturum, donem)
    donem_gunleri = donem_gunlerini_uret(donem.baslangic_tarihi, donem.bitis_tarihi)
    azami_haftalik_saat = Decimal(
        kural_depo.parametre_getir(
            "H5", "azami_haftalik_saat", varsayilan=_VARSAYILAN_AZAMI_HAFTALIK_SAAT
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
        azami_haftalik_saat=azami_haftalik_saat,
        haftalik_asgari_izin_gunu=haftalik_asgari_izin_gunu,
        aktif_kural_kimlikleri=frozenset(k.kimlik for k in kural_depo.aktif_kurallari_getir()),
    )


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
