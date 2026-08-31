"""Kullaniciya donen hatalarin MAKINE KODU.

Neden gerekli: arayuz iki dilli oldu ve hata metinleri arka ucta Turkce
yaziliydi. Ingilizce arayuzde Turkce bir cumle cikmasi, cevirinin yarim
kaldigini en gorunur yerde ilan ederdi.

Secilen yol: metin degil KOD tasinir. Arka uc `kod="surum_yok"` doner,
metni arayuz kendi sozlugunden yazar. Boylece cumle tek yerde durur ve
yeni bir dil eklemek arka uca hic dokunmaz.

`detail` KALDI ve kaldirilmayacak. Kaldirmak butun testleri, gunlukleri ve
API'yi tarayicidan degil kabuktan kullanan herkesi ayni anda kirardi;
oysa `kod` eklemek hicbir seyi kirmaz. Arayuz kodu taniyorsa onu kullanir,
tanimiyorsa `detail`e duser - yani ceviri eksik kalsa bile kullanici bos
bir kutu degil Turkce bir cumle gorur.

ALAN HATALARININ KODU SINIF ADINDAN TURETILMEZ. Turetilseydi bir sinifi
yeniden adlandirmak API sozlesmesini sessizce degistirirdi ve bunu ne
derleyici ne test yakalardi. Kodlar asagida ACIKCA yaziliyor;
`test_hata_kodlari.py` her alan hatasinin bir kodu oldugunu dogruluyor,
yani yeni bir hata sinifi kodsuz kalirsa takim yuksek sesle duser.
"""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import KaldirilmisAyarError
from app.repositories.sonuc import SurumSilinemezError, TaslakSiniriAsildiError
from app.services.belge_servisi import (
    BelgeCokBuyukError,
    BelgeTipiKabulEdilmediError,
)
from app.services.calisan_servisi import (
    TercihDonemiBulunamadiError,
    TercihKararlanmisError,
)
from app.services.cozum_servisi import DurdurulamazError, KararUygulanamazError
from app.services.dogrulama_servisi import (
    DamgaCakismasiError,
    SurumTaslakDegilError,
    ZorunluIhlalError,
)
from app.services.kimlik_servisi import (
    GirisBasarisizError,
    HesapKilitliError,
    HesapPasifError,
    ParolaAyniError,
    ParolaHataliError,
)
from app.services.kullanici_servisi import (
    HesapYonetmeYetkisiYokError,
    KendiHesabiError,
    KullaniciAdiGecersizError,
    KullaniciAdiKullanimdaError,
    KullaniciBulunamadiError,
    PersonelBaglantisiGerekliError,
    PersonelBulunamadiError,
    PersonelZatenBagliError,
    SistemYoneticisineDokunulamazError,
    SonSistemYoneticisiError,
)
from app.services.parola import ParolaKuraliError
from app.services.surum_servisi import (
    KopyalanamazSurumDurumuError,
    SurumlerAyniDonemdeDegilError,
)
from app.services.tanim_servisi import (
    CakisanTalepAraligiError,
    KuralParametresiError,
    SicilKullanimdaError,
)
from app.veri_temizligi import UretimKilidiError


class Hata(HTTPException):
    """Kod tasiyan HTTP hatasi.

    `HTTPException`in kendisi genisletiliyor, yanina yeni bir tur
    konulmuyor: FastAPI'nin butun akislari (bagimliliklar, alt
    uygulamalar, `raise from`) HTTPException bekliyor ve ayri bir tur
    bunlarin hepsinde ayrica ele alinmayi gerektirirdi.
    """

    def __init__(
        self,
        status_code: int,
        kod: str,
        detail: object,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.kod = kod


# --- Alan hatalarinin kodlari ----------------------------------------------
#
# Yonlendiriciler bu hatalari yakalayip metnini `str(hata)` ile geciriyor;
# kod da ayni yerden, hatanin TIPINDEN cikar. Yonlendiricinin her alan
# hatasini tek tek tanimasi gerekmez.
ALAN_KODLARI: dict[type[Exception], str] = {
    BelgeCokBuyukError: "belge_cok_buyuk",
    BelgeTipiKabulEdilmediError: "belge_tipi_kabul_edilmedi",
    CakisanTalepAraligiError: "cakisan_talep_araligi",
    DamgaCakismasiError: "damga_cakismasi",
    DurdurulamazError: "durdurulamaz",
    GirisBasarisizError: "giris_basarisiz",
    HesapKilitliError: "hesap_kilitli",
    HesapPasifError: "hesap_pasif",
    HesapYonetmeYetkisiYokError: "hesap_yonetme_yetkisi_yok",
    KaldirilmisAyarError: "kaldirilmis_ayar",
    KararUygulanamazError: "karar_uygulanamaz",
    KendiHesabiError: "kendi_hesabi",
    KopyalanamazSurumDurumuError: "kopyalanamaz_surum_durumu",
    KullaniciAdiGecersizError: "kullanici_adi_gecersiz",
    KullaniciAdiKullanimdaError: "kullanici_adi_kullanimda",
    KullaniciBulunamadiError: "kullanici_yok",
    KuralParametresiError: "kural_parametresi",
    ParolaAyniError: "parola_ayni",
    ParolaHataliError: "parola_hatali",
    ParolaKuraliError: "parola_kurali",
    PersonelBaglantisiGerekliError: "personel_baglantisi_gerekli",
    PersonelBulunamadiError: "personel_yok",
    PersonelZatenBagliError: "personel_zaten_bagli",
    SicilKullanimdaError: "sicil_kullanimda",
    SistemYoneticisineDokunulamazError: "sistem_yoneticisine_dokunulamaz",
    SonSistemYoneticisiError: "son_sistem_yoneticisi",
    SurumSilinemezError: "surum_silinemez",
    SurumTaslakDegilError: "surum_taslak_degil",
    SurumlerAyniDonemdeDegilError: "surumler_ayni_donemde_degil",
    TaslakSiniriAsildiError: "taslak_siniri_asildi",
    TercihDonemiBulunamadiError: "tercih_donemi_yok",
    TercihKararlanmisError: "tercih_kararlanmis",
    UretimKilidiError: "uretim_kilidi",
    ZorunluIhlalError: "zorunlu_ihlal",
}

_BILINMEYEN = "bilinmeyen_hata"


def kodu(hata: Exception) -> str:
    """Alan hatasinin kodu.

    MRO uzerinden bakilir: bir alt sinif kendi kodunu tanimlamadiysa
    atasininkine duser, `KeyError` ile yukselmez. Yukselseydi bir kenar
    durumdaki hata, kullaniciya hata mesaji yerine 500 dondururdu.
    """
    for tip in type(hata).__mro__:
        kod = ALAN_KODLARI.get(tip)  # type: ignore[arg-type]
        if kod is not None:
            return kod
    return _BILINMEYEN


async def hata_isleyici(_istek: Request, hata: Exception) -> JSONResponse:
    """`kod` tasiyan hatalar icin govdeye o alani da koyar.

    Kod tasimayanlar FastAPI'nin varsayilaniyla BIREBIR ayni cikar; bu
    isleyicinin var olmasi mevcut hicbir yaniti degistirmez.

    Tip STARLETTE'in HTTPException'i, FastAPI'ninki DEGIL. Bilinmeyen bir
    yola gelen 404'u Starlette'inki yukseltiyor ve FastAPI'ninkine gore
    daraltilmis bir kontrol orada duserdi.
    """
    assert isinstance(hata, StarletteHTTPException)
    govde: dict[str, object] = {"detail": hata.detail}
    kod = getattr(hata, "kod", None)
    if kod is not None:
        govde["kod"] = kod
    return JSONResponse(status_code=hata.status_code, content=govde, headers=hata.headers)
