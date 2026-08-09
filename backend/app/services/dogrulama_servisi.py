"""SDD 5.5 (surum 1.3): degisikligi_dogrula - manuel duzenleme dogrulamasi.

Iki ayri atama kumesi uzerinde calisir: pencere (degistirilen gunun +-7
gunu - H1-H8 dogasi geregi, S1/S5/S6/S6b/S7/S8 tek hucrelik degisiklik
etkisi acisindan yeterlidir) ve donem geneli (S2/S3/S4 - donem genelindeki
bir agregata baktiklari icin pencereyle sinirlandirilamaz). Zorunlu
kurallar yalnizca degisiklik SONRASI durumda degerlendirilir (kabul/red
karari icin bu yeterlidir); esnek hedefler ise degisiklik ONCESI ve
SONRASI iki kez degerlendirilip farki raporlanir - bu, pencere disindaki
gunler icin baglamdan (talep, tercihler, donem sinirlari) kaynaklanan
sabit/degismeyen sapmalarin farkta iptal olmasini saglar.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.kurallar.baglam import AtamaKaydi
from app.kurallar.kayit_defteri import kurallari_yukle
from app.kurallar.temel import Ihlal, KuralKapsami
from app.models.kural import KuralTipi
from app.models.sonuc import Atama, AtamaKaynagi, CizelgeSurumuDurumu
from app.repositories.kural import KuralDeposu
from app.repositories.sonuc import AtamaDeposu, CizelgeSurumuDeposu, DonemDeposu
from app.services.baglam_kurucu import baglam_olustur

_PENCERE_GUN = 7


class SurumTaslakDegilError(Exception):
    """FR-7.3/TD-8: yayinlanmis (veya arsiv) bir surumun dogrudan duzenlenmesi
    engellenir. TD-8'e gore yalnizca 'yayinlandi' salt okunurdur - 'taslak' ve
    'cozuldu' ikisi de duzenlenebilir (bir cozum isi bitince surum otomatik
    'cozuldu' olur; kullanici bunun uzerinde elle degisiklik yapabilmelidir)."""


_DUZENLENEBILIR_DURUMLAR = (CizelgeSurumuDurumu.TASLAK, CizelgeSurumuDurumu.COZULDU)


@dataclass(frozen=True, slots=True)
class AtamaDegisikligi:
    surum_id: int
    personel_id: int
    tarih: date
    vardiya_tipi_id: int | None = None
    nokta_id: int | None = None


@dataclass(frozen=True, slots=True)
class DogrulamaSonucu:
    kabul_edilebilir: bool
    zorunlu_ihlaller: list[Ihlal] = field(default_factory=list)
    ceza_degisimi: float = 0.0


class DogrulamaServisi:
    def __init__(self, oturum: Session) -> None:
        self.oturum = oturum
        self.surum = CizelgeSurumuDeposu(oturum)
        self.donem = DonemDeposu(oturum)
        self.kural = KuralDeposu(oturum)
        self.atama = AtamaDeposu(oturum)

    def dogrula(self, degisiklik: AtamaDegisikligi) -> DogrulamaSonucu | None:
        """Surum bulunamazsa None doner (404); duzenlenebilir durumda degilse
        (yayinlandi/arsiv) SurumTaslakDegilError firlatir (409)."""
        surum = self.surum.getir(degisiklik.surum_id)
        if surum is None:
            return None
        if surum.durum not in _DUZENLENEBILIR_DURUMLAR:
            raise SurumTaslakDegilError(
                f"Surum {surum.surum_id} duzenlenebilir durumda degil (durum={surum.durum})"
            )
        donem = self.donem.getir(surum.donem_id)
        # yalniz_aktif=False: dogrulama var olan bir taslak uzerinde calisir;
        # o taslaktaki atamalarin tanimlari sonradan pasiflestirilmis olabilir.
        baglam = baglam_olustur(self.oturum, donem, yalniz_aktif=False)
        kurallar = kurallari_yukle(self.kural.aktif_kurallari_getir())

        pencere_baslangic = degisiklik.tarih - timedelta(days=_PENCERE_GUN)
        pencere_bitis = degisiklik.tarih + timedelta(days=_PENCERE_GUN)
        once_pencere = _cevir(
            self.atama.surume_ve_araliga_gore_getir(
                surum.surum_id, pencere_baslangic, pencere_bitis
            )
        )
        once_donem = _cevir(self.atama.surume_gore_getir(surum.surum_id))
        sonra_pencere = _degisikligi_uygula(once_pencere, degisiklik)
        sonra_donem = _degisikligi_uygula(once_donem, degisiklik)

        zorunlu_ihlaller: list[Ihlal] = []
        ceza_once = 0.0
        ceza_sonra = 0.0
        for kural in kurallar:
            atamalar_once = (
                once_donem if kural.kapsam == KuralKapsami.DONEM_GENELI else once_pencere
            )
            atamalar_sonra = (
                sonra_donem if kural.kapsam == KuralKapsami.DONEM_GENELI else sonra_pencere
            )
            if kural.tip == KuralTipi.ZORUNLU:
                zorunlu_ihlaller.extend(kural.dogrula(atamalar_sonra, baglam))
            else:
                ceza_once += sum(i.ceza or 0.0 for i in kural.dogrula(atamalar_once, baglam))
                ceza_sonra += sum(i.ceza or 0.0 for i in kural.dogrula(atamalar_sonra, baglam))

        return DogrulamaSonucu(
            kabul_edilebilir=not zorunlu_ihlaller,
            zorunlu_ihlaller=zorunlu_ihlaller,
            ceza_degisimi=ceza_sonra - ceza_once,
        )

    def uygula(self, degisiklik: AtamaDegisikligi) -> DogrulamaSonucu | None:
        """Once dogrula(); zorunlu ihlal yoksa degisikligi kalici olarak yazar."""
        sonuc = self.dogrula(degisiklik)
        if sonuc is None or not sonuc.kabul_edilebilir:
            return sonuc

        mevcut = self.atama.tekil_getir(
            degisiklik.surum_id, degisiklik.personel_id, degisiklik.tarih
        )
        if degisiklik.vardiya_tipi_id is None:
            if mevcut is not None:
                self.oturum.delete(mevcut)
        elif mevcut is not None:
            mevcut.vardiya_tipi_id = degisiklik.vardiya_tipi_id
            mevcut.nokta_id = degisiklik.nokta_id
            mevcut.kaynak = AtamaKaynagi.MANUEL
        else:
            self.oturum.add(
                Atama(
                    surum_id=degisiklik.surum_id,
                    personel_id=degisiklik.personel_id,
                    tarih=degisiklik.tarih,
                    vardiya_tipi_id=degisiklik.vardiya_tipi_id,
                    nokta_id=degisiklik.nokta_id,
                    kaynak=AtamaKaynagi.MANUEL,
                )
            )
        return sonuc

    def kilit_ayarla(
        self, surum_id: int, personel_id: int, tarih: date, kilitli: bool
    ) -> Atama | None:
        """FR-6.5: bir atamayi kilitler/kilidini acar.

        Kural dogrulamasi gerektirmez - kilit atamanin kendisini degistirmez,
        yalnizca yeniden cozumde (Gun 11, S8) sabitlenip sabitlenmeyecegini
        belirler. Surum ya da atama bulunamazsa None doner (404); surum
        taslak/cozuldu disindaysa SurumTaslakDegilError firlatir (409).
        """
        surum = self.surum.getir(surum_id)
        if surum is None:
            return None
        if surum.durum not in _DUZENLENEBILIR_DURUMLAR:
            raise SurumTaslakDegilError(
                f"Surum {surum.surum_id} kilitlenebilir durumda degil (durum={surum.durum})"
            )
        atama = self.atama.tekil_getir(surum_id, personel_id, tarih)
        if atama is None:
            return None
        atama.kilitli = kilitli
        return atama


def _cevir(atamalar: Sequence[Atama]) -> list[AtamaKaydi]:
    return [AtamaKaydi(a.personel_id, a.tarih, a.vardiya_tipi_id, a.nokta_id) for a in atamalar]


def _degisikligi_uygula(
    atamalar: list[AtamaKaydi], degisiklik: AtamaDegisikligi
) -> list[AtamaKaydi]:
    kalanlar = [
        a
        for a in atamalar
        if not (a.personel_id == degisiklik.personel_id and a.tarih == degisiklik.tarih)
    ]
    if degisiklik.vardiya_tipi_id is not None and degisiklik.nokta_id is not None:
        kalanlar.append(
            AtamaKaydi(
                degisiklik.personel_id,
                degisiklik.tarih,
                degisiklik.vardiya_tipi_id,
                degisiklik.nokta_id,
            )
        )
    return kalanlar


__all__ = ["AtamaDegisikligi", "DogrulamaServisi", "DogrulamaSonucu", "SurumTaslakDegilError"]
