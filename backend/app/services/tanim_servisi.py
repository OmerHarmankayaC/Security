"""Tanim yonetimi servis katmani (SDD 3.2: is mantigi burada, SQL depo katmaninda)."""

from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.kurallar import kayit_defteri
from app.models.tanim import (
    Bina,
    GorevNoktasi,
    OzelGun,
    Personel,
    Talep,
    VardiyaTipi,
    Yetkinlik,
)
from app.repositories.girdi import MusaitlikDeposu, TercihDeposu
from app.repositories.kural import KuralDeposu
from app.repositories.tanim import (
    BinaDeposu,
    GorevNoktasiDeposu,
    OzelGunDeposu,
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


class KuralParametresiError(ValueError):
    """Kural parametresi katalogdaki tanima uymuyor; mesaj kullaniciya gosterilir."""


class SicilKullanimdaError(ValueError):
    """Sicil numarasi baska bir personel kaydinda (router 409'a cevirir).

    Benzersizlik veritabaninda da kisitli (personel.sicil_no UNIQUE), ama
    yalnizca orada kalmasi yeterli degildi: kisit ihlali yakalanmamis bir
    IntegrityError olarak disari cikip 500 uretiyordu. Kullanicinin gordugu
    sey "sunucu hatasi" oluyordu, oysa yaptigi sey gecerli bir veri girisi
    denemesiydi ve duzeltmesi tek bir alani degistirmekten ibaretti (NFR-5).
    """


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
        self.musaitlik = MusaitlikDeposu(oturum)
        self.tercih = TercihDeposu(oturum)
        self.ozel_gun = OzelGunDeposu(oturum)

    # --- Personel (FR-1.1, FR-1.2) ---------------------------------------

    def personel_olustur(self, veri: PersonelOlustur) -> Personel:
        self._sicili_dogrula(veri.sicil_no)
        alanlar = veri.model_dump(exclude={"yetkinlik_idleri"})
        personel = self.personel.olustur(**alanlar)
        self.personel.yetkinlikleri_ayarla(personel, veri.yetkinlik_idleri)
        return personel

    def personel_guncelle(self, id_: int, veri: PersonelGuncelle) -> Personel | None:
        if veri.sicil_no is not None:
            self._sicili_dogrula(veri.sicil_no, haric_personel_id=id_)
        alanlar = veri.model_dump(exclude={"yetkinlik_idleri"}, exclude_unset=True)
        personel = self.personel.guncelle(id_, **alanlar) if alanlar else self.personel.getir(id_)
        if personel is None:
            return None
        if veri.yetkinlik_idleri is not None:
            self.personel.yetkinlikleri_ayarla(personel, veri.yetkinlik_idleri)
        return personel

    def _sicili_dogrula(self, sicil_no: str, *, haric_personel_id: int | None = None) -> None:
        cakisan = self.personel.sicille_bul(sicil_no, haric_personel_id=haric_personel_id)
        if cakisan is not None:
            raise SicilKullanimdaError(
                f"{sicil_no} sicil numarasi baska bir personel kaydinda kullaniliyor"
            )

    # --- Ozel gun / resmi tatil (FR-1.10) ----------------------------------

    def ozel_gun_isaretle(self, tarih: date, ad: str) -> OzelGun:
        """Tarihi resmi tatil olarak isaretler; zaten isaretliyse adini gunceller.

        Ayni tarih icin ikinci bir POST'un hata vermesi yerine adi
        guncellemesi bilincli: birincil anahtar tarihin kendisi oldugundan
        (SDD 4.2.1) "bu tarih zaten tatil" durumu bir cakisma degil, zaten
        istenen sonuctur. Kullanicinin gordugu sey ya "isaretlendi" ya da
        "adi degisti" olur; ikisi de dogru ve ikisi de guvenlidir.
        """
        mevcut = self.ozel_gun.getir(tarih)
        if mevcut is not None:
            mevcut.ad = ad
            self.oturum.flush()
            return mevcut
        return self.ozel_gun.olustur(tarih=tarih, ad=ad)

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

    # --- Kural (FR-1.11, FR-1.12) ------------------------------------------

    def kural_parametrelerini_dogrula(
        self, kimlik: str, parametreler: dict[str, Any]
    ) -> dict[str, Any]:
        """Kural parametrelerini kayit defterindeki tanima gore dogrular.

        Parametreler belge alaninda (JSONB) tutuldugu icin veritabani sema
        dogrulamasi yapmaz; tanimsiz bir anahtar veya sinir disi bir deger
        sessizce yazilabilir ve hatasi ancak cozum sirasinda (KeyError) ya da
        hic ortaya cikmadan yanlis bir cizelge olarak gorunur. Dogrulama bu
        yuzden yazma anindadir.
        """
        sinif = kayit_defteri.bul(kimlik)
        if sinif is None:
            raise KuralParametresiError(f"{kimlik} kural katalogunda tanimli degil.")

        tanimlar = {t.anahtar: t for t in sinif.parametre_tanimlari}
        bilinmeyen = set(parametreler) - set(tanimlar)
        if bilinmeyen:
            beklenen = ", ".join(sorted(tanimlar)) or "yok"
            raise KuralParametresiError(
                f"{kimlik} kuralinda tanimsiz parametre: {', '.join(sorted(bilinmeyen))}. "
                f"Beklenen parametreler: {beklenen}."
            )

        temiz: dict[str, Any] = {}
        for anahtar, deger in parametreler.items():
            tanim = tanimlar[anahtar]
            # bool, Python'da int'in alt tipidir; True'nun 1 olarak gecmesini
            # engellemek icin ayrica elenir.
            if isinstance(deger, bool) or not isinstance(deger, int):
                raise KuralParametresiError(f"{tanim.etiket} bir tam sayi olmali.")
            if tanim.asgari is not None and deger < tanim.asgari:
                raise KuralParametresiError(
                    f"{tanim.etiket} en az {tanim.asgari} olmali; girilen deger {deger}."
                )
            if tanim.azami is not None and deger > tanim.azami:
                raise KuralParametresiError(
                    f"{tanim.etiket} en fazla {tanim.azami} olabilir; girilen deger {deger}."
                )
            temiz[anahtar] = deger

        # Eksik birakilan parametre mevcut degerini korur; kismi guncelleme
        # (yalniz bir alanin degistirilmesi) arayuzun dogal davranisidir.
        mevcut = self.kural.kimlige_gore_bul(kimlik)
        birlesik = dict(mevcut.parametreler) if mevcut else {}
        birlesik.update(temiz)
        return birlesik

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
        azami_haftalik_saat = self.kural.parametre_getir(
            "H5", "azami_haftalik_saat", varsayilan=_VARSAYILAN_AZAMI_HAFTALIK_SAAT
        )
        haftalik_asgari_izin_gunu = self.kural.parametre_getir(
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
