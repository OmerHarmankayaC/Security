"""Giris, cikis ve parola degistirme (SRS FR-10.1 - FR-10.3, FR-10.7, FR-10.8;
SDD 5.1b).

Bu servisin en onemli davranisi, BASARISIZ girisin kullanicinin var olup
olmadigini ele vermemesidir. Uc yerde birden korunur:

  1. Ayni mesaj. Kullanici yoksa da parola yanlissa da `GirisBasarisizError`
     dogar ve router ayni metni dondurur.
  2. Benzer sure. Kullanici bulunamadiginda da bir Argon2id dogrulamasi
     yapilir (`parola.bosa_dogrula`); yoksa yanit belirgin bicimde erken
     doner ve sure farkindan kullanici adi sayilabilirdi.
  3. Ayrintili mesajlar yalniz PAROLA DOGRUYKEN. Hesabin kilitli ya da devre
     disi oldugu, ancak dogru parolayi bilen birine soylenir. Parolayi
     bilmeyen bir saldirgan bu mesajlari hicbir kullanici adi icin goremez,
     yani FR-10.8'in "kilit suresini bildir" gereksinimi kullanici sayimina
     kapi acmaz.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import ayarlar
from app.models.kimlik import Kullanici
from app.services import parola as parola_araclari
from app.services.oturum_servisi import OturumServisi


class GirisBasarisizError(Exception):
    """Kullanici adi ya da parola hatali. Ikisi ayirt EDILMEZ."""


class HesapKilitliError(Exception):
    """FR-10.8: hesap gecici olarak kilitli. Kalan sure mesajda bildirilir."""

    def __init__(self, kalan_dakika: int) -> None:
        super().__init__(
            f"Hesap gecici olarak kilitlendi. {kalan_dakika} dakika sonra tekrar deneyin."
        )
        self.kalan_dakika = kalan_dakika


class HesapPasifError(Exception):
    """Hesap devre disi birakilmis (FR-10.5). Silinmedigi icin parola dogrudur."""


class ParolaHataliError(Exception):
    """Parola degistirmede mevcut parola dogrulanamadi."""


class ParolaAyniError(Exception):
    """Yeni parola mevcut parolayla ayni."""


@dataclass(frozen=True)
class GirisSonucu:
    kullanici: Kullanici
    belirtec: str


class KimlikServisi:
    def __init__(self, oturum: Session) -> None:
        self.oturum = oturum
        self.oturumlar = OturumServisi(oturum)

    # --- Giris (FR-10.1, FR-10.3, FR-10.8) ----------------------------------

    def giris(
        self, kullanici_adi: str, parola: str, *, simdi: datetime | None = None
    ) -> GirisSonucu:
        simdi = simdi if simdi is not None else datetime.now(UTC)
        kullanici = self._kullaniciyi_bul(kullanici_adi)

        if kullanici is None:
            parola_araclari.bosa_dogrula()
            raise GirisBasarisizError

        kilitli = kullanici.kilit_bitis is not None and simdi < kullanici.kilit_bitis
        if not kilitli and kullanici.kilit_bitis is not None:
            # Kilit suresi dolmus: sayac ve kilit temizlenir, kullanici yeni
            # bir denemeler penceresine baslar.
            kullanici.kilit_bitis = None
            kullanici.basarisiz_deneme = 0

        # Kilitliyken de dogrulama YAPILIR. Iki nedeni var: sure kilitli ve
        # kilitsiz yol arasinda ayni kalir, ve kilit mesajinin yalniz dogru
        # parolayla gosterilebilmesi icin parolanin dogrulugu bilinmelidir.
        dogru = parola_araclari.dogrula(kullanici.parola_ozeti, parola)

        if kilitli:
            if not dogru:
                raise GirisBasarisizError
            assert kullanici.kilit_bitis is not None
            raise HesapKilitliError(self._kalan_dakika(kullanici.kilit_bitis, simdi))

        if not dogru:
            self._basarisizligi_isle(kullanici, simdi)
            raise GirisBasarisizError

        if not kullanici.aktif:
            raise HesapPasifError

        kullanici.basarisiz_deneme = 0
        kullanici.kilit_bitis = None
        belirtec = self.oturumlar.olustur(kullanici.kullanici_id, simdi=simdi)
        return GirisSonucu(kullanici=kullanici, belirtec=belirtec)

    def _basarisizligi_isle(self, kullanici: Kullanici, simdi: datetime) -> None:
        kullanici.basarisiz_deneme += 1
        if kullanici.basarisiz_deneme >= ayarlar.giris_kilit_esigi:
            kullanici.kilit_bitis = simdi + timedelta(minutes=ayarlar.giris_kilit_dakika)
            # Sayac sifirlanir: kilit bittikten sonra kullanici tam bir
            # deneme penceresine daha sahip olur. Sifirlanmasaydi kilitten
            # cikan hesap tek bir yanlis denemeyle yeniden kilitlenirdi.
            kullanici.basarisiz_deneme = 0

        # BU SERVISIN COMMIT CAGIRAN TEK YERI ve istisna bilincli.
        # Kural (SDD 3.2) su: bir servis metodunun baslattigi islem ya
        # butunuyle islenir ya da butunuyle geri alinir; islemi
        # `oturum_al` bagimliligi kapatir ve HATA halinde GERI ALIR.
        # Basarisiz giris tam olarak bu durumdur - istek 401 ile biter,
        # dolayisiyla sayac da geri alinirdi ve kilit HIC devreye girmezdi
        # (FR-10.8 sessizce islevsiz kalirdi). Sayacin yasamasi gereken sey
        # istegin basarisi degil, denemenin kendisidir.
        self.oturum.commit()

    @staticmethod
    def _kalan_dakika(kilit_bitis: datetime, simdi: datetime) -> int:
        kalan = (kilit_bitis - simdi).total_seconds() / 60
        # Yukari yuvarlanir: "0 dakika sonra deneyin" anlamsiz bir mesajdir.
        return max(1, -(-int(kalan * 60) // 60))

    # --- Cikis (FR-10.3) ----------------------------------------------------

    def cikis(self, oturum_id: str) -> None:
        self.oturumlar.sil(oturum_id)

    # --- Parola degistirme (FR-10.7) ----------------------------------------

    def parola_degistir(self, kullanici: Kullanici, mevcut: str, yeni: str) -> str:
        """Parolayi degistirir, ACIK BUTUN OTURUMLARI kapatir ve yeni bir
        oturum acar; donen belirtec cereze yazilir.

        Butun oturumlarin kapatilmasi bilincli: parola degisikligi, calinmis
        bir belirtecin kullanici tarafindan iptal edilebilecegi tek andir.
        Cagiran istegin oturumu da kapandigi icin yerine yenisi acilir -
        kullanici kendi parolasini degistirdiginde disari atilmaz, ama
        elindeki belirtec de tazelenir.
        """
        if not parola_araclari.dogrula(kullanici.parola_ozeti, mevcut):
            raise ParolaHataliError
        if parola_araclari.dogrula(kullanici.parola_ozeti, yeni):
            raise ParolaAyniError

        # Kural ihlalinde (ParolaKuraliError) hicbir sey degismemis olur:
        # ozetleme once yapilir, yazma sonra.
        yeni_ozet = parola_araclari.ozetle(yeni)
        kullanici.parola_ozeti = yeni_ozet
        kullanici.parola_degistirmeli = False

        self.oturumlar.kullanicinin_oturumlarini_sil(kullanici.kullanici_id)
        return self.oturumlar.olustur(kullanici.kullanici_id)

    # --- Yardimcilar --------------------------------------------------------

    def _kullaniciyi_bul(self, kullanici_adi: str) -> Kullanici | None:
        # Girilen ad kucuk harfe cevrilip TAM eslenir. Sutunun uzerinde
        # `lower()` cagirmak gerekmiyor: sema zaten kucuk harf saklanmasini
        # garanti ediyor (ck_kullanici_adi_kucuk_harf) ve sutun uzerindeki
        # fonksiyon benzersizlik indeksini de kullanilamaz hale getirirdi.
        return self.oturum.execute(
            select(Kullanici).where(Kullanici.kullanici_adi == kullanici_adi.strip().lower())
        ).scalar_one_or_none()
