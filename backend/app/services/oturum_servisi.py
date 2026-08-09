"""Oturum yasam dongusu (SDD 4.2.1, 5.1b; SRS FR-10.3).

Belirtec rastgele uretilir ve YALNIZ cereze yazilir; veritabaninda ozeti
durur. Veritabanini okuyan biri acik oturumlari ele geciremez, cunku
ozetten belirtec uretilemez.

Ozet icin duz SHA-256 kullanilir, parolada oldugu gibi Argon2id degil.
Ikisinin tehdit modeli farklidir: parola insan tarafindan secilir ve dusuk
entropilidir, bu yuzden ozetlemenin YAVAS olmasi gerekir. Belirtec 256 bit
rastgeledir; sozluk saldirisi diye bir sey yoktur ve her istekte bir kez
hesaplandigi icin yavas bir ozet burada yalnizca gecikme olurdu.
"""

import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import ayarlar
from app.models.kimlik import Kullanici, OturumKaydi

# 256 bit. token_urlsafe(32) 43 karakterlik bir dize uretir.
_BELIRTEC_BAYT = 32

CEREZ_ADI = "vardiya_oturum"


def belirtec_ozeti(belirtec: str) -> str:
    """Cerezdeki belirtecin veritabanindaki karsiligi (64 karakter onaltilik)."""
    return hashlib.sha256(belirtec.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class OturumBaglami:
    """Dogrulanmis bir istegin kimlik baglami.

    Router ve yetkilendirme katmani buradan okur; `kullanici` ORM nesnesidir
    ve `personel_id` calisan isteklerinde hangi personelin verisinin
    donecegini belirleyen TEK kaynaktir (SRS FR-9.1).
    """

    kullanici: Kullanici
    oturum_id: str


class OturumServisi:
    def __init__(self, oturum: Session) -> None:
        self.oturum = oturum

    # --- Olusturma ----------------------------------------------------------

    def olustur(self, kullanici_id: int, *, simdi: datetime | None = None) -> str:
        """Yeni bir oturum kaydi acar ve CEREZE yazilacak belirteci dondurur.

        Belirtec yalnizca burada, bir kez gorunur; kayda ozeti gider.
        """
        simdi = simdi if simdi is not None else datetime.now(UTC)
        belirtec = secrets.token_urlsafe(_BELIRTEC_BAYT)
        self.oturum.add(
            OturumKaydi(
                oturum_id=belirtec_ozeti(belirtec),
                kullanici_id=kullanici_id,
                olusturma=simdi,
                son_erisim=simdi,
                gecerlilik_bitis=simdi + timedelta(hours=ayarlar.oturum_azami_saat),
            )
        )
        return belirtec

    # --- Dogrulama ----------------------------------------------------------

    def dogrula(self, belirtec: str, *, simdi: datetime | None = None) -> OturumBaglami | None:
        """Belirteci dogrular ve hareketsizlik sayacini tazeler.

        Gecersiz her durumda None doner ve kayit SILINIR: suresi dolmus bir
        oturumu tabloda birakmak, sonradan 'neden hala duruyor' sorusunu
        dogurur ve temizlik icin ayri bir is gerektirirdi.
        """
        simdi = simdi if simdi is not None else datetime.now(UTC)
        kayit = self.oturum.get(OturumKaydi, belirtec_ozeti(belirtec))
        if kayit is None:
            return None

        # Iki sure AYRI uygulanir (SDD 4.2.1): mutlak bitis girisin
        # kendisinden, hareketsizlik son istekten olculur.
        hareketsizlik = timedelta(minutes=ayarlar.oturum_hareketsizlik_dakika)
        if simdi >= kayit.gecerlilik_bitis or simdi - kayit.son_erisim >= hareketsizlik:
            self.oturum.delete(kayit)
            return None

        kullanici = self.oturum.get(Kullanici, kayit.kullanici_id)
        if kullanici is None or not kullanici.aktif:
            # Devre disi birakma zaten oturumlari siler; bu kontrol o yolun
            # atlandigi bir durumda (elle SQL, ileride eklenecek baska bir
            # yol) acik oturumun ayakta kalmasini engeller.
            self.oturum.delete(kayit)
            return None

        kayit.son_erisim = simdi
        return OturumBaglami(kullanici=kullanici, oturum_id=kayit.oturum_id)

    # --- Sonlandirma --------------------------------------------------------

    def sil(self, oturum_id: str) -> None:
        """Tek bir oturumu kapatir (cikis)."""
        kayit = self.oturum.get(OturumKaydi, oturum_id)
        if kayit is not None:
            self.oturum.delete(kayit)

    def kullanicinin_oturumlarini_sil(self, kullanici_id: int) -> None:
        """Bir kullanicinin BUTUN acik oturumlarini gecersiz kilar.

        Bu metot oturum tablosunun varlik nedenidir (SDD 4.2.1): hesap devre
        disi birakildiginda ve parola sifirlandiginda/degistirildiginde
        cagrilir. Kendi kendini dogrulayan bir belirtecle ayni sey ancak ayri
        bir kara liste altyapisiyla yapilabilirdi.
        """
        self.oturum.execute(delete(OturumKaydi).where(OturumKaydi.kullanici_id == kullanici_id))

    def kullanicinin_oturum_sayisi(self, kullanici_id: int) -> int:
        return len(
            self.oturum.execute(
                select(OturumKaydi.oturum_id).where(OturumKaydi.kullanici_id == kullanici_id)
            )
            .scalars()
            .all()
        )
