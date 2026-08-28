"""Gosterim ortaminin hesap tanimi — TEK YER (Demo Senaryosu 7).

Iki tuketicisi var ve ikisi de ayni listeyi bilmek zorunda: hesaplari ACAN
uretec (`scripts/demo_veri_uret.py`) ve giris ekraninda kimlik bilgisini
GOSTEREN uc nokta (`app/routers/demo.py`). Liste iki yerde yazilsaydi,
uretecin actigi hesapla ekranin gosterdigi hesap sessizce ayrisir ve
kullanici calismayan bir kullanici adiyla karsilasirdi.

PAROLA BURADA YOKTUR. Hesaplarin parolasi `ayarlar.demo_parola`dir ve ortam
degiskeninden gelir; bu modul yalnizca KIMIN hangi rolle acilacagini bilir.

SISTEM YONETICISI LISTEDE YOK. Uretec onu acar - gosterim ortaminin da bir
sistem yoneticisine ihtiyaci var (FR-10.12) - ama giris ekraninda
gosterilmez. Gosterim ortami herkese aciktir ve en genis yetkiyi ekrana
yazmak, demoyu gezen herkese kendi kullanici hesaplarini yonetme hakki
vermek demektir. Ekranda gorunen uc rol, urunun anlatmak istedigi uc
yuzeydir: idare, hesap yonetimi ve calisan paneli.
"""

from dataclasses import dataclass

from app.models.kimlik import Rol


@dataclass(frozen=True, slots=True)
class DemoHesabi:
    kullanici_adi: str
    rol: Rol
    #: Ekranda rolun yanina yazilan tek cumlelik aciklama. Hangi hesabin
    #: neyi gosterdigi yazilmazsa iki calisan hesabi ayirt edilemez.
    aciklama: str
    #: Personel sicili — yalnizca calisan hesaplari icin dolu. Uretec
    #: hesabi bu sicile bagli personele baglar.
    sicil_no: str | None = None
    #: Giris ekraninda gosterilir mi. Sistem yoneticisi acilir ama
    #: GOSTERILMEZ (yukaridaki gerekce).
    gosterilir: bool = True


DEMO_HESAPLARI: tuple[DemoHesabi, ...] = (
    DemoHesabi(
        kullanici_adi="demo_sistem",
        rol=Rol.SISTEM_YONETICISI,
        aciklama="Sistem yöneticisi",
        gosterilir=False,
    ),
    DemoHesabi(
        kullanici_adi="demo_idare",
        rol=Rol.IDARE,
        aciklama="Çizelgeyi kuran ve yayınlayan rol; hesap yönetimi dışındaki her şey",
    ),
    DemoHesabi(
        kullanici_adi="demo_hesap",
        rol=Rol.HESAP_YONETICISI,
        aciklama="Yalnızca kullanıcı hesaplarını yönetir; çizelgeye dokunmaz",
    ),
    DemoHesabi(
        kullanici_adi="demo_d1010",
        rol=Rol.CALISAN,
        aciklama="Çalışan — yıllık fazla çalışma kotası dolmaya yakın",
        sicil_no="D-1010",
    ),
    DemoHesabi(
        kullanici_adi="demo_d1020",
        rol=Rol.CALISAN,
        aciklama="Çalışan — ortalama yüklü",
        sicil_no="D-1020",
    ),
)


def gosterilecekler() -> tuple[DemoHesabi, ...]:
    return tuple(h for h in DEMO_HESAPLARI if h.gosterilir)


__all__ = ["DEMO_HESAPLARI", "DemoHesabi", "gosterilecekler"]
