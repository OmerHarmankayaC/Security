"""SRS FR-5.x: on kontrolu bir Donem uzerinde calistiran servis katmani."""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.repositories.kural import KuralDeposu
from app.repositories.sonuc import DonemDeposu
from app.services.baglam_kurucu import baglam_olustur, donem_gunlerini_uret
from app.services.on_kontrol import Bulgu, on_kontrol_yap

_VARSAYILAN_FAZLA_CALISMA_ESIGI = Decimal(45)
_VARSAYILAN_AZAMI_GUNLUK_SAAT = Decimal(11)
_VARSAYILAN_YILLIK_FAZLA_KOTASI = Decimal(270)
_VARSAYILAN_HAFTALIK_ASGARI_IZIN_GUNU = 1


class OnKontrolServisi:
    def __init__(self, oturum: Session) -> None:
        self.oturum = oturum
        self.donem = DonemDeposu(oturum)
        self.kural = KuralDeposu(oturum)

    def calistir(self, donem_id: int) -> list[Bulgu] | None:
        """Donem bulunamazsa None doner; yonlendirici bunu 404'e cevirir."""
        donem = self.donem.getir(donem_id)
        if donem is None:
            return None

        baglam = baglam_olustur(self.oturum, donem)
        donem_gunleri = donem_gunlerini_uret(donem.baslangic_tarihi, donem.bitis_tarihi)
        # Kapasite hesabi FAZLA CALISMA ESIGINDEN gecer (SRS 3.3.6): H5'in
        # mutlak tavani (66) surdurulebilir tempo degil, asilamayan sinirdir.
        fazla_calisma_esigi = Decimal(
            self.kural.parametre_getir(
                "H10", "fazla_calisma_esigi", varsayilan=_VARSAYILAN_FAZLA_CALISMA_ESIGI
            )
        )
        azami_gunluk_saat = Decimal(
            self.kural.parametre_getir(
                "H9", "azami_gunluk_saat", varsayilan=_VARSAYILAN_AZAMI_GUNLUK_SAAT
            )
        )
        yillik_fazla_kotasi = Decimal(
            self.kural.parametre_getir(
                "H10", "yillik_fazla_kotasi", varsayilan=_VARSAYILAN_YILLIK_FAZLA_KOTASI
            )
        )
        haftalik_asgari_izin_gunu = int(
            self.kural.parametre_getir(
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
            yillik_fazla_kotasi=yillik_fazla_kotasi,
            aktif_kural_kimlikleri=frozenset(k.kimlik for k in self.kural.aktif_kurallari_getir()),
        )
