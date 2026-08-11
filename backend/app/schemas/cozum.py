"""/api/cozum istek/yanit semalari (SDD Ek B, 5.4)."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator

from app.models.sonuc import CozumIsi, CozumIsiDurumu
from app.services.cozum_servisi import Karar


class CozumBaslatIstek(BaseModel):
    """donem_id: yeni bir donem icin ilk cozum. onceki_surum_id: SDD 5.6
    yeniden_coz - onceki surumden taslak turetip S8 tabanli yeniden cozer.
    Tam olarak biri verilmelidir."""

    donem_id: int | None = None
    onceki_surum_id: int | None = None
    zaman_limiti_saniye: int = 60

    @model_validator(mode="after")
    def _tam_olarak_biri(self) -> "CozumBaslatIstek":
        if (self.donem_id is None) == (self.onceki_surum_id is None):
            raise ValueError("donem_id ile onceki_surum_id'den tam olarak biri verilmeli")
        return self


class CozumKarariIstek(BaseModel):
    """SDD 5.4.1 / SRS FR-4.10: durdurulan iste kullanicinin karari."""

    karar: Karar
    # Yalnizca `devam` kararinda anlamli: yeni arama SIFIRDAN baslar ve
    # kendi zaman limitini alir (SDD 5.4.1 - "kaldigi yerden devam" degil).
    zaman_limiti_saniye: int | None = None

    @model_validator(mode="after")
    def _zaman_limiti_yalniz_devamda(self) -> "CozumKarariIstek":
        if self.zaman_limiti_saniye is not None:
            if self.karar is not Karar.DEVAM:
                raise ValueError("zaman_limiti_saniye yalnizca 'devam' kararinda verilir")
            if self.zaman_limiti_saniye < 1:
                raise ValueError("zaman_limiti_saniye en az 1 olmali")
        return self


class CozumOku(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    is_id: int
    surum_id: int
    durum: CozumIsiDurumu
    baslangic_zamani: datetime
    bitis_zamani: datetime | None
    sure_saniye: Decimal | None
    zaman_limiti_saniye: int
    en_iyi_ceza: Decimal | None
    ceza_dokumu: dict[str, Any] | None
    hata_mesaji: str | None
    devam_kaynagi_is_id: int | None = None
    # `gecici_sonuc`un KENDISI DEGIL, yalnizca var olup olmadigi. Alan bir
    # okuma yuzeyi degildir (SDD 4.2.4); arayuzun ondan tek ihtiyaci
    # "kullan" secenegini etkinlestirip etkinlestirmeyecegidir.
    kullanilabilir_sonuc_var: bool = False
    # Karar panelinin gosterdigi kapsama acigi SAYISI (SDD 6.3.2). Yine
    # icerik degil OZET: hangi gunde hangi noktada acik oldugu, karar
    # verilip atamalar yazildiktan sonra kapsama acigi ucundan okunur.
    gecici_kapsama_acigi_sayisi: int | None = None

    @classmethod
    def kayittan(cls, is_kaydi: CozumIsi) -> "CozumOku":
        """ORM kaydindan; `gecici_sonuc` yerine yalnizca ozetini tasir."""
        gecici = is_kaydi.gecici_sonuc
        return cls.model_validate(is_kaydi).model_copy(
            update={
                "kullanilabilir_sonuc_var": bool(gecici),
                "gecici_kapsama_acigi_sayisi": (
                    len(gecici.get("kapsama_eksikleri") or []) if gecici else None
                ),
            }
        )


class CozumKarariYaniti(BaseModel):
    """Karar sonrasi isin son hali; `devam` karariysa acilan yeni is da."""

    is_kaydi: CozumOku
    yeni_is: CozumOku | None = None
