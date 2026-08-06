"""Tanim yonetimi servis katmani (SDD 3.2: is mantigi burada, SQL depo katmaninda)."""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.tanim import Bina, GorevNoktasi, Personel, Talep, VardiyaTipi, Yetkinlik
from app.repositories.kural import KuralDeposu
from app.repositories.tanim import (
    BinaDeposu,
    GorevNoktasiDeposu,
    PersonelDeposu,
    TalepDeposu,
    VardiyaTipiDeposu,
    YetkinlikDeposu,
)
from app.schemas.tanim import (
    PersonelGuncelle,
    PersonelOlustur,
    TalepHucresi,
    VardiyaTipiGuncelle,
    VardiyaTipiOlustur,
    YukGostergesi,
)
from app.services.vardiya_hesaplari import gece_mi_oner, sure_saat_hesapla
from app.services.yuk_gostergesi import yuk_gostergesi_hesapla

_VARSAYILAN_AZAMI_HAFTALIK_SAAT = Decimal(45)
_VARSAYILAN_HAFTALIK_ASGARI_IZIN_GUNU = 1


class TanimServisi:
    def __init__(self, oturum: Session) -> None:
        self.oturum = oturum
        self.personel = PersonelDeposu(oturum)
        self.yetkinlik = YetkinlikDeposu(oturum)
        self.bina = BinaDeposu(oturum)
        self.nokta = GorevNoktasiDeposu(oturum)
        self.vardiya_tipi = VardiyaTipiDeposu(oturum)
        self.talep = TalepDeposu(oturum)
        self.kural = KuralDeposu(oturum)

    # --- Personel (FR-1.1, FR-1.2) ---------------------------------------

    def personel_olustur(self, veri: PersonelOlustur) -> Personel:
        alanlar = veri.model_dump(exclude={"yetkinlik_idleri"})
        personel = self.personel.olustur(**alanlar)
        self.personel.yetkinlikleri_ayarla(personel, veri.yetkinlik_idleri)
        return personel

    def personel_guncelle(self, id_: int, veri: PersonelGuncelle) -> Personel | None:
        alanlar = veri.model_dump(exclude={"yetkinlik_idleri"}, exclude_unset=True)
        personel = self.personel.guncelle(id_, **alanlar) if alanlar else self.personel.getir(id_)
        if personel is None:
            return None
        if veri.yetkinlik_idleri is not None:
            self.personel.yetkinlikleri_ayarla(personel, veri.yetkinlik_idleri)
        return personel

    # --- Yetkinlik / Bina (FR-1.2, FR-1.5) --------------------------------

    def yetkinlik_olustur(self, ad: str, aciklama: str | None) -> Yetkinlik:
        return self.yetkinlik.olustur(ad=ad, aciklama=aciklama)

    def bina_olustur(self, ad: str) -> Bina:
        return self.bina.olustur(ad=ad)

    # --- Gorev Noktasi (FR-1.6) --------------------------------------------

    def nokta_olustur(
        self, ad: str, bina_id: int | None, onkosul_yetkinlik_id: int | None
    ) -> GorevNoktasi:
        return self.nokta.olustur(ad=ad, bina_id=bina_id, onkosul_yetkinlik_id=onkosul_yetkinlik_id)

    # --- Vardiya Tipi (FR-1.3, FR-1.4) --------------------------------------

    def vardiya_tipi_olustur(self, veri: VardiyaTipiOlustur) -> VardiyaTipi:
        gece_mi = (
            veri.gece_mi
            if veri.gece_mi is not None
            else gece_mi_oner(veri.baslangic_saati, veri.bitis_saati)
        )
        sure_saat = sure_saat_hesapla(veri.baslangic_saati, veri.bitis_saati)
        return self.vardiya_tipi.olustur(
            ad=veri.ad,
            baslangic_saati=veri.baslangic_saati,
            bitis_saati=veri.bitis_saati,
            sure_saat=sure_saat,
            gece_mi=gece_mi,
        )

    def vardiya_tipi_guncelle(self, id_: int, veri: VardiyaTipiGuncelle) -> VardiyaTipi | None:
        mevcut = self.vardiya_tipi.getir(id_)
        if mevcut is None:
            return None
        alanlar = veri.model_dump(exclude_unset=True)
        if "baslangic_saati" in alanlar or "bitis_saati" in alanlar:
            baslangic = alanlar.get("baslangic_saati", mevcut.baslangic_saati)
            bitis = alanlar.get("bitis_saati", mevcut.bitis_saati)
            alanlar["sure_saat"] = sure_saat_hesapla(baslangic, bitis)
        return self.vardiya_tipi.guncelle(id_, **alanlar)

    # --- Talep + Yuk Gostergesi (FR-1.7, FR-1.8, FR-1.9) --------------------

    def talep_matrisini_getir(self) -> tuple[list[Talep], YukGostergesi]:
        hucreler = list(self.talep.tumunu_getir())
        return hucreler, self._yuk_gostergesi_hesapla(hucreler)

    def talep_hucresini_guncelle(self, hucre: TalepHucresi) -> Talep:
        return self.talep.hucreyi_guncelle(
            nokta_id=hucre.nokta_id,
            vardiya_tipi_id=hucre.vardiya_tipi_id,
            gun_tipi=hucre.gun_tipi,
            tarih=hucre.tarih,
            gereken_sayi=hucre.gereken_sayi,
        )

    def _yuk_gostergesi_hesapla(self, hucreler: list[Talep]) -> YukGostergesi:
        vardiya_tipleri = {v.vardiya_tipi_id: v for v in self.vardiya_tipi.tumunu_getir()}
        azami_haftalik_saat = self._kural_parametresi(
            "H5", "azami_haftalik_saat", varsayilan=_VARSAYILAN_AZAMI_HAFTALIK_SAAT
        )
        haftalik_asgari_izin_gunu = self._kural_parametresi(
            "H6",
            "haftalik_asgari_izin_gunu",
            varsayilan=_VARSAYILAN_HAFTALIK_ASGARI_IZIN_GUNU,
        )
        return yuk_gostergesi_hesapla(
            hucreler,
            vardiya_tipleri,
            azami_haftalik_saat=Decimal(azami_haftalik_saat),
            haftalik_asgari_izin_gunu=int(haftalik_asgari_izin_gunu),
        )

    def _kural_parametresi(self, kimlik: str, anahtar: str, *, varsayilan: object) -> object:
        kural = self.kural.kimlige_gore_bul(kimlik)
        if kural is None or anahtar not in kural.parametreler:
            return varsayilan
        return kural.parametreler[anahtar]
