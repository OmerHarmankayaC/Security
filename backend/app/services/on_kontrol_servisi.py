"""SRS FR-5.x: on kontrolu bir Donem uzerinde calistiran servis katmani."""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.repositories.kural import KuralDeposu
from app.repositories.sonuc import DonemDeposu
from app.services.baglam_kurucu import baglam_olustur, donem_gunlerini_uret
from app.services.on_kontrol import Bulgu, on_kontrol_yap

_VARSAYILAN_AZAMI_HAFTALIK_SAAT = Decimal(45)
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
        azami_haftalik_saat = Decimal(
            self.kural.parametre_getir(
                "H5", "azami_haftalik_saat", varsayilan=_VARSAYILAN_AZAMI_HAFTALIK_SAAT
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
            azami_haftalik_saat=azami_haftalik_saat,
            haftalik_asgari_izin_gunu=haftalik_asgari_izin_gunu,
            aktif_kural_kimlikleri=frozenset(k.kimlik for k in self.kural.aktif_kurallari_getir()),
        )
