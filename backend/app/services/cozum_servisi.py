"""SDD 5.4: cozum isinin durum makinesi (Sekil 5.1) ve yasam dongusu yonetimi.

cozum_isini_calistir(), SDD 5.4'teki YORDAM'in birebir Python karsiligidir.

YURUTME BAGLAMI (SDD 3.4.4). Cozum isi AYRI BIR SISTEM SERVISI olarak
calisir; iki surec arasinda dogrudan iletisim yoktur, is durumu/ilerleme/
sonuc yalnizca veritabani uzerinden aktarilir. Bu yuzden:
  - `CozumServisi.baslat` surec ACMAZ, isi `kuyrukta` durumunda birakir.
  - `scripts/cozum_iscisi.py` kuyruktan is alip `cozum_isini_calistir`i
    cagirir.
  - Durdurma istegi de ayni kanaldan gelir: API isin durumunu IPTAL'e
    ceker, isci bunu cozum geri cagiriminda okuyup aramayi sonlandirir
    ve HICBIR sonuc yazmadan cikar (bkz. _iptal_istendi_mi).
Sprint 2 Gun 8'deki multiprocessing.Process ara cozumu kaldirildi.
"""

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.config import ayarlar
from app.cozucu import CozucuAdaptoru, model_kur
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
    KapsamaAcigiDeposu,
)
from app.services.baglam_kurucu import baglam_olustur, donem_gunlerini_uret, zaman_ekseni_olustur
from app.services.on_kontrol import Bulgu, on_kontrol_yap

_VARSAYILAN_ZAMAN_LIMITI_SANIYE = 60
_VARSAYILAN_AZAMI_HAFTALIK_SAAT = Decimal(45)
_VARSAYILAN_HAFTALIK_ASGARI_IZIN_GUNU = 1


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
        zaman_limiti_saniye: int = _VARSAYILAN_ZAMAN_LIMITI_SANIYE,
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
        """
        surum: CizelgeSurumu | None
        if onceki_surum_id is not None:
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
    kapsama_depo = KapsamaAcigiDeposu(oturum)

    is_kaydi = is_depo.getir(is_id)
    if is_kaydi is None:
        return
    surum = surum_depo.getir(is_kaydi.surum_id)
    donem = donem_depo.getir(surum.donem_id)

    is_kaydi.durum = CozumIsiDurumu.ON_KONTROL
    oturum.commit()

    bulgular = _on_kontrolu_calistir(oturum, kural_depo, donem)
    if bulgular:
        is_kaydi.durum = CozumIsiDurumu.BASARISIZ
        is_kaydi.hata_mesaji = _bulgulari_ozetle(bulgular)
        is_kaydi.bitis_zamani = datetime.now(UTC)
        oturum.commit()
        return

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

    model, x, baglam, ceza_terimleri = model_kur(
        baglam, zaman_ekseni, kurallar, kilitli_atamalar=kilitli_atamalar or None
    )

    # Model kurulurken (uzun surebilir) durdurma istenmis olabilir.
    if _iptal_istendi_mi(oturum, is_kaydi):
        _iptal_olarak_kapat(oturum, is_kaydi)
        return

    is_kaydi.durum = CozumIsiDurumu.COZULUYOR
    oturum.commit()

    def ara_cozum_geri_cagirma(ceza: float, _gecen_sure: float) -> None:
        is_kaydi.en_iyi_ceza = _ondalik(ceza)
        oturum.commit()

    sonuc = CozucuAdaptoru.coz(
        model,
        x,
        zaman_limiti_saniye=is_kaydi.zaman_limiti_saniye,
        arama_iscisi_sayisi=ayarlar.cozucu_arama_iscisi_sayisi,
        ara_cozum_geri_cagirma=ara_cozum_geri_cagirma,
        iptal_kontrolu=lambda: _iptal_istendi_mi(oturum, is_kaydi),
        ceza_terimleri=ceza_terimleri,
        kapsama_degiskenleri=baglam.kapsama_eksikleri,
    )

    # SDD 6.3.2: "Iptal edilen is, o ana kadar bulunmus en iyi cozumu
    # KAYDETMEDEN sonlanir." Bu kontrol atama yazma blogundan once gelir.
    if sonuc.iptal_edildi or _iptal_istendi_mi(oturum, is_kaydi):
        _iptal_olarak_kapat(oturum, is_kaydi)
        return

    if sonuc.durum == "cozum_yok":
        is_kaydi.durum = CozumIsiDurumu.BASARISIZ
        is_kaydi.hata_mesaji = "Cozucu, zaman limiti icinde uygun bir cizelge bulamadi"
        is_kaydi.bitis_zamani = datetime.now(UTC)
        oturum.commit()
        return

    # SDD 5.4: atamalarin yazilmasi tek bir veritabani islemi icinde yapilir; yarim
    # kalmis bir cizelge, kural ihlali icermeyen fakat kapsamasi eksik bir cizelgeden
    # ayirt edilemeyecegi icin yanilticidir.
    atama_depo.surume_gore_sil(surum.surum_id)
    kapsama_depo.surume_gore_sil(surum.surum_id)
    for personel_id, tarih, vardiya_tipi_id, nokta_id in sonuc.atanan_anahtarlar:
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
    for (tarih, vardiya_tipi_id, nokta_id), eksik_sayi in sonuc.kapsama_eksikleri.items():
        kapsama_depo.olustur(
            surum_id=surum.surum_id,
            tarih=tarih,
            vardiya_tipi_id=vardiya_tipi_id,
            nokta_id=nokta_id,
            eksik_sayi=eksik_sayi,
        )

    is_kaydi.ceza_dokumu = {k: float(v) for k, v in sonuc.ceza_dokumu.items()}
    is_kaydi.en_iyi_ceza = _ondalik(sonuc.toplam_ceza) if sonuc.toplam_ceza is not None else None
    is_kaydi.sure_saniye = _ondalik(sonuc.sure_saniye)
    is_kaydi.durum = (
        CozumIsiDurumu.UYARILI if sonuc.kapsama_eksikleri else CozumIsiDurumu.TAMAMLANDI
    )
    is_kaydi.bitis_zamani = datetime.now(UTC)
    surum.durum = CizelgeSurumuDurumu.COZULDU
    oturum.commit()


def _iptal_istendi_mi(oturum: Session, is_kaydi: CozumIsi) -> bool:
    """Durdurma bayragini VERITABANINDAN taze okur.

    Bayrak ayri bir sutun degil, `durum` alanidir: API `/api/cozum/{id}/iptal`
    cagrisinda durumu IPTAL'e ceker (SDD 5.4'un durum makinesinde zaten var
    olan terminal durum). Isci ayri bir servis oldugundan (SDD 3.4.4) API o
    sureci olduremez; tek haberlesme kanali veritabanidir.

    `refresh` sart: is_kaydi bu oturumun kimlik haritasinda onbelleklidir ve
    API'nin BASKA bir baglantidan yaptigi degisiklik yeniden okunmadan
    gorulmez.
    """
    oturum.refresh(is_kaydi, ["durum"])
    return is_kaydi.durum == CozumIsiDurumu.IPTAL


def _iptal_olarak_kapat(oturum: Session, is_kaydi: CozumIsi) -> None:
    """Isi iptal olarak sonlandirir; hicbir atama veya kapsama acigi yazilmaz."""
    is_kaydi.durum = CozumIsiDurumu.IPTAL
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
