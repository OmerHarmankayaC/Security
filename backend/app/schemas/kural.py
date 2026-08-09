"""Kural uc noktasinin istek/yanit semalari (SDD 3.2.1, 4.2.3; SRS FR-1.11-FR-1.13)."""

from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.kural import Kural, KuralTipi


class KuralGuncelle(BaseModel):
    """Yalniz veri degisir, kod dokunulmaz (SDD 3.2.1): parametreler, agirlik, aktiflik."""

    parametreler: dict[str, Any] | None = None
    agirlik: int | None = None
    aktif: bool | None = None


class ParametreTanimiOku(BaseModel):
    """Parametrenin arayuzde alan-deger olarak duzenlenebilmesi icin gereken tanim.

    Parametreler veritabaninda belge alaninda durur (SDD 4.2.3), cunku her
    kuralin parametre kumesi farklidir. Kullaniciya ham JSON gostermek NFR-5'e
    aykiri oldugundan, okunabilir etiket ve sinirlar kural sinifindan
    (app.kurallar.temel.ParametreTanimi) buraya tasinir.
    """

    anahtar: str
    etiket: str
    birim: str | None
    asgari: int | None
    azami: int | None


class KuralOku(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    kural_id: int
    kimlik: str
    tip: KuralTipi
    parametreler: dict[str, Any]
    agirlik: int | None
    aktif: bool

    # --- Kayit defterinden gelen katalog bilgisi (SRS bolum 4) --------------
    # Veritabani satiri kuralin yalnizca DEGERLERINI tasir; adi, aciklamasi ve
    # parametre semasi kodda tanimlidir (SDD 3.2.1). Ikisi okuma aninda
    # birlestirilir, boylece arayuz tek istekle "H1" yerine "Günde en fazla bir
    # vardiya"yi gosterebilir.
    ad: str
    aciklama: str
    parametre_tanimlari: list[ParametreTanimiOku]
    # Katalog kurallari (H1-H8, S1-S8) modelin yapisini olusturur ve SILINEMEZ;
    # yalnizca pasiflestirilir, parametreleri ve agirliklari degistirilir.
    # Kayit defterinde sinifi olmayan bir kural satiri zaten yuklenemez
    # (kayit_defteri.kurallari_yukle "Tanimsiz kural kimligi" hatasi verir),
    # dolayisiyla kullanicinin sonradan ekledigi bir kural bu mimaride
    # OLUSAMAZ. Alan yine de tasinir: arayuz ayrimi gorunur kilar ve mimari
    # degisirse tek dogruluk kaynagi burasi olur.
    silinebilir_mi: bool

    @classmethod
    def modelden_olustur(cls, kural: Kural) -> "KuralOku":
        from app.kurallar import kayit_defteri

        sinif = kayit_defteri.bul(kural.kimlik)
        return cls(
            kural_id=kural.kural_id,
            kimlik=kural.kimlik,
            tip=kural.tip,
            parametreler=kural.parametreler,
            agirlik=kural.agirlik,
            aktif=kural.aktif,
            ad=sinif.ad if sinif else kural.kimlik,
            aciklama=sinif.aciklama if sinif else "",
            parametre_tanimlari=[
                ParametreTanimiOku(
                    anahtar=t.anahtar,
                    etiket=t.etiket,
                    birim=t.birim,
                    asgari=t.asgari,
                    azami=t.azami,
                )
                for t in (sinif.parametre_tanimlari if sinif else ())
            ],
            # Kayit defterinde karsiligi olan her kural katalog kuralidir.
            silinebilir_mi=sinif is None,
        )
