"""SDD 5.4: cozum isinin durum makinesi (Sekil 5.1) ve yasam dongusu yonetimi.

cozum_isini_calistir(), SDD 5.4'teki YORDAM'in birebir Python karsiligidir.
Cozum, SDD 3.4.4 geregi HTTP istek-yanit dongusunden bagimsiz, ayri bir
surecte calisir (bu asamada basit bir multiprocessing.Process yeterli;
systemd entegrasyonu Sprint 3'te). Baslat(), isi kuyruga alip surumu
dondurur; asil calisma _disaridan_calistir uzerinden ayri bir Python
sureci icinde yurutulur.
"""

import multiprocessing
from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.cozucu import CozucuAdaptoru, model_kur
from app.db import OturumYerel
from app.kurallar.kayit_defteri import kurallari_yukle
from app.models.kural import Kural
from app.models.sonuc import (
    Atama,
    AtamaKaynagi,
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
_VARSAYILAN_ARAMA_ISCISI_SAYISI = 3
_VARSAYILAN_AZAMI_HAFTALIK_SAAT = Decimal(45)
_VARSAYILAN_HAFTALIK_ASGARI_IZIN_GUNU = 1


class CozumServisi:
    def __init__(self, oturum: Session) -> None:
        self.oturum = oturum
        self.donem = DonemDeposu(oturum)
        self.surum = CizelgeSurumuDeposu(oturum)
        self.is_ = CozumIsiDeposu(oturum)

    def baslat(
        self, donem_id: int, *, zaman_limiti_saniye: int = _VARSAYILAN_ZAMAN_LIMITI_SANIYE
    ) -> CozumIsi | None:
        """Isi kuyruga alir, hemen doner; gercek cozum ayri bir surecte calisir."""
        donem = self.donem.getir(donem_id)
        if donem is None:
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
        # Ayri surecin bu satirlari gorebilmesi icin once onaylamak sart.
        self.oturum.commit()

        surec = multiprocessing.Process(
            target=_disaridan_calistir, args=(is_kaydi.is_id,), daemon=False
        )
        surec.start()
        return is_kaydi


def _disaridan_calistir(is_id: int) -> None:
    """multiprocessing.Process hedefi: kendi oturumunu acar (ayri surec, ayri baglanti)."""
    oturum = OturumYerel()
    try:
        cozum_isini_calistir(oturum, is_id)
    finally:
        oturum.close()


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
    model, x, baglam, ceza_terimleri = model_kur(baglam, zaman_ekseni, kurallar)

    is_kaydi.durum = CozumIsiDurumu.COZULUYOR
    oturum.commit()

    def ara_cozum_geri_cagirma(ceza: float, _gecen_sure: float) -> None:
        is_kaydi.en_iyi_ceza = _ondalik(ceza)
        oturum.commit()

    sonuc = CozucuAdaptoru.coz(
        model,
        x,
        zaman_limiti_saniye=is_kaydi.zaman_limiti_saniye,
        arama_iscisi_sayisi=_VARSAYILAN_ARAMA_ISCISI_SAYISI,
        ara_cozum_geri_cagirma=ara_cozum_geri_cagirma,
        ceza_terimleri=ceza_terimleri,
        kapsama_degiskenleri=baglam.kapsama_eksikleri,
    )

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
