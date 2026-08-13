"""/api/atama/dogrula ve /api/atama semalari (SDD 5.5, SRS FR-6.x)."""

from datetime import date, time

from pydantic import BaseModel, Field, model_validator

from app.kurallar.zaman_araligi import tam_saat_mi


class AtamaDegisikligiIstek(BaseModel):
    """Cizelge izgarasindaki bir (personel, gun) satirina yazilan BLOK (SDD 6.3.3).

    Blok katalogu kalktigi icin istek bir vardiya tipi secmez; baslangic ve
    bitis SAATINI verir (SRS TD-13). Ucu de bos ise o gunun blogu
    kaldirilir; ucu de doluysa gunun blogu bu olur ve var olanin yerine
    gecer.

    Saatler SAAT BASINDA olmak zorundadir. Saat ekseni yarim saatlik
    sinirlari temsil edemez (SDD 6.3.1); serbest birakilsaydi 08.30 gibi bir
    deger sessizce yuvarlanir ya da modele hic girmezdi.

    Bitis baslangictan kucuk ya da esitse blok gece yarisini asar ve ertesi
    gune tasar - `zaman_araligi` modulundeki sozlesmenin aynisi.
    """

    surum_id: int
    personel_id: int
    tarih: date
    baslangic_saati: time | None = None
    bitis_saati: time | None = None
    nokta_id: int | None = None

    @model_validator(mode="after")
    def _ucu_birlikte_doluysa_ya_da_bossa(self) -> "AtamaDegisikligiIstek":
        alanlar = (self.baslangic_saati, self.bitis_saati, self.nokta_id)
        dolu = [a for a in alanlar if a is not None]
        if dolu and len(dolu) != len(alanlar):
            raise ValueError(
                "baslangic_saati, bitis_saati ve nokta_id birlikte doldurulmali ya da "
                "ucu de bos birakilmali (hucreyi bosaltmak icin)"
            )
        for saat in (self.baslangic_saati, self.bitis_saati):
            if saat is not None and not tam_saat_mi(saat):
                raise ValueError("Blok saatleri saat başında olmalı (örnek: 08.00).")
        return self


class IhlalOku(BaseModel):
    kural_kimlik: str
    aciklama: str
    personel_id: int | None
    tarih: date | None
    ceza: float | None


class CezaKalemiOku(BaseModel):
    """Bir esnek hedefin ceza degisimi, agirligiyla birlikte (FR-4.8)."""

    kural_kimlik: str
    ad: str
    ham_fark: float
    agirlik: float
    agirlikli_fark: float


class DogrulamaSonucuOku(BaseModel):
    kabul_edilebilir: bool
    zorunlu_ihlaller: list[IhlalOku]
    # Ham (agirliksiz) toplam. Korunuyor ama arayuzun gostermesi gereken
    # deger `agirlikli_ceza_degisimi`: ham toplam, farkli birimlerdeki
    # cezalari (kisi, vardiya, saat, gun) agirliksiz topladigi icin
    # buyuklukleri karsilastirilabilir degil.
    ceza_degisimi: float
    agirlikli_ceza_degisimi: float = 0.0
    ceza_dokumu: list[CezaKalemiOku] = Field(default_factory=list)
    # Degisikligin yeni dogurdugu, bir yere isaret eden esnek bulgular
    # (kapsama acigi, fazla kadro). Zorunlu ihlal DEGILDIR: degisiklik
    # uygulanir, karar kullaniciya birakilir (SDD 5.5).
    uyarilar: list[IhlalOku] = Field(default_factory=list)
