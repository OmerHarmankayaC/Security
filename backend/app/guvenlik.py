"""Isteklerin kimlik ve yetki kapisi (SRS FR-10.3, FR-10.4, FR-10.7;
SDD 5.1b).

Uygulama duzeyinde tek bir dosyada durur, router basina degil: bir uc
noktanin kapisiz kalmasi, o uc noktanin kapisinin BASKA turlu olmasindan
cok daha olasidir. Burada tanimli bagimliliklar router imzalarina yazilir ve
imzada gorunur olurlar.

Kademeler:

  `oturum_baglami`  - gecerli bir oturum var mi? (kimlik dogrulama)
  `giris_yapan`     - ustune: parola degistirme borcu var mi? (FR-10.7)

Rol kapilari (FR-10.4) bu ikisinin uzerine kurulur.
"""

from typing import Annotated

from fastapi import Depends, Request, Response
from sqlalchemy.orm import Session

from app.config import ayarlar
from app.db import oturum_al
from app.hatalar import Hata
from app.models.kimlik import HESAP_YONETEN_ROLLER, IDARE_VE_USTU, Rol
from app.services.oturum_servisi import CEREZ_ADI, OturumBaglami, OturumServisi

VeriOturumu = Annotated[Session, Depends(oturum_al)]

# Parola degistirme borcu varken acik kalan tek uc nokta kumesi disindaki her
# sey bu mesajla kapanir (FR-10.7).
_PAROLA_BORCU_MESAJI = "Once parolanizi degistirmelisiniz"


def cerez_yaz(yanit: Response, belirtec: str) -> None:
    """Oturum cerezini yazar (SDD 5.1b).

    - HttpOnly: JavaScript belirteci okuyamaz, XSS ile calinamaz.
    - Secure:   duz http uzerinden gonderilmez (yerelde .env ile kapatilir).
    - SameSite=Lax: baska sitelerden gelen POST isteklerine cerez eklenmez,
      yani sitelerarasi istek sahteciligi (CSRF) yazma uc noktalarina
      ulasamaz. GET'lerde cerez gittigi icin normal gezinme bozulmaz.
    """
    yanit.set_cookie(
        key=CEREZ_ADI,
        value=belirtec,
        httponly=True,
        secure=ayarlar.oturum_cerezi_secure,
        samesite="lax",
        path="/",
        # Son kullanma cereze YAZILMAZ. Oturumun gecerliligi yalnizca
        # sunucudaki kayittan okunur; cereze bir sure yazmak, iki kaynagin
        # (tarayici ve veritabani) ayrisabildigi ikinci bir gercek uretirdi.
    )


def cerez_sil(yanit: Response) -> None:
    yanit.delete_cookie(
        key=CEREZ_ADI,
        httponly=True,
        secure=ayarlar.oturum_cerezi_secure,
        samesite="lax",
        path="/",
    )


def oturum_baglami(istek: Request, veri_oturumu: VeriOturumu) -> OturumBaglami:
    """Gecerli bir oturum zorunlu kilar; yoksa 401.

    Parola degistirme borcunu KONTROL ETMEZ - borclu kullanicinin da
    erisebilmesi gereken uc noktalar var (kim oldugunu sormak, parolasini
    degistirmek, cikmak).
    """
    belirtec = istek.cookies.get(CEREZ_ADI)
    if not belirtec:
        raise Hata(status_code=401, kod="oturum_yok", detail="Oturum acik degil")

    baglam = OturumServisi(veri_oturumu).dogrula(belirtec)
    if baglam is None:
        raise Hata(
            status_code=401, kod="oturum_gecersiz", detail="Oturum gecersiz veya suresi dolmus"
        )
    return baglam


Baglam = Annotated[OturumBaglami, Depends(oturum_baglami)]


def giris_yapan(baglam: Baglam) -> OturumBaglami:
    """Gecerli oturum + parola borcu yok (FR-10.7).

    Yonetimin atadigi parola degistirilene kadar diger uc noktalar KAPALI.
    Arayuzun kullaniciyi parola ekranina goturmesi bunun yerine gecmez:
    istek dogrudan gonderildiginde de reddedilir.
    """
    if baglam.kullanici.parola_degistirmeli:
        raise Hata(status_code=403, kod="parola_borcu", detail=_PAROLA_BORCU_MESAJI)
    return baglam


GirisYapan = Annotated[OturumBaglami, Depends(giris_yapan)]


# --- Rol kapilari (FR-10.4) -------------------------------------------------
#
# Kapilar router DUZEYINDE baglanir, uc nokta basina degil: bir yonlendiriciye
# sonradan eklenen uc noktanin kapisiz kalmasi, kapisinin yanlis olmasindan
# cok daha olasi bir hatadir. Yonlendiricinin butun uc noktalari ayni
# yetkiyi paylasmiyorsa kapi yine de en dar olanindan secilir ve gevsemesi
# gereken uc nokta bunu imzasinda acikca yazar.


def _rol_kapisi(*izinli: Rol):  # noqa: ANN202 - FastAPI bagimliligi dondurur
    def kapi(baglam: GirisYapan) -> OturumBaglami:
        if baglam.kullanici.rol not in izinli:
            # 404 degil 403: kaynagin varligi zaten gizli degil, gizli olan
            # ona erisim yetkisi. 404 dondurmek, arayuzu hata ayiklanamaz
            # hale getirirdi.
            raise Hata(status_code=403, kod="yetki_yok", detail="Bu islem icin yetkiniz yok")
        return baglam

    return kapi


# Yonetici arayuzunun tamami: tanimlar, cozum, surum, analiz, musaitlik.
# Rol kapsayicidir (SRS 5.10): sistem yoneticisi hesap yoneticisinin, hesap
# yoneticisi idarenin yetkilerini icerir.
idare_yetkisi = _rol_kapisi(*IDARE_VE_USTU)

# HESAP UC NOKTALARI (FR-10.5). IDARE BURAYA GIREMEZ ve bu, dort rollu
# duzenin en kritik ayrimidir: cizelgeyi kuran kisinin parola sifirlamasi
# icin bir neden yok. Ayrim yalnizca burada degil SERVISTE de denetlenir
# (services/kullanici_servisi.py) - tek katmanli bir kontrol, ileride
# eklenecek bir uc noktanin kapisiz kalmasiyla sessizce delinir.
hesap_yonetimi_yetkisi = _rol_kapisi(*HESAP_YONETEN_ROLLER)

# Yalniz sistem yoneticisi. Hesap yoneticisinin dokunamayacagi islemler
# (sistem yoneticisi hesaplarinin degistirilmesi) icin.
sistem_yoneticisi_yetkisi = _rol_kapisi(Rol.SISTEM_YONETICISI)


def calisan_yetkisi(baglam: GirisYapan) -> OturumBaglami:
    """Calisan panelinin kapisi (SRS 5.10, FR-9.1).

    Yalniz `calisan` rolu gecer. Rol kapsayiciliginin BURAYA UZANMAMASI
    bilincli: SRS 5.10 "calisan rolu digerlerinin alt kumesi degildir; kendi
    verisine erisim, personel kaydina bagli AYRI bir yetkidir" der. Yonetim
    rolunun buradan gecmesi, kimin verisinin donecegi sorusunu yanitsiz
    birakirdi.

    `personel_id`nin dolu oldugu ayrica dogrulanir. Sema bunu zaten garanti
    ediyor (ck_kullanici_calisan_personele_bagli); buradaki kontrol o
    garantinin ileride gevsetilmesi halinde FR-9.1'in sessizce
    `personel_id=None` ile calismaya baslamasini engeller.
    """
    if baglam.kullanici.rol is not Rol.CALISAN:
        raise Hata(status_code=403, kod="yetki_yok", detail="Bu islem icin yetkiniz yok")
    if baglam.kullanici.personel_id is None:
        raise Hata(
            status_code=403,
            kod="personel_baglantisi_yok",
            detail="Hesap bir personel kaydina bagli degil",
        )
    return baglam


def oturumdaki_personel(baglam: Annotated[OturumBaglami, Depends(calisan_yetkisi)]) -> int:
    """Calisan isteklerinde hangi personelin verisinin donecegi (SRS FR-9.1).

    BU, O SORUNUN TEK YANITIDIR. Adreste ya da govdede gelen bir personel
    kimligi bu secime hicbir kosulda giremez; calisan uc noktalari personel
    kimligini parametre olarak ALMAZ, boylece "parametreyi dogrulamayi
    unutma" diye bir hata bicimi de kalmaz. Once bu bir acikti (kisiye ozel
    baglantida URL'deki kimlik degistirilebiliyordu) ve bir daha ayni yere
    donulmemesi icin kimlik parametre olmaktan tumuyle cikarilmistir.
    """
    assert baglam.kullanici.personel_id is not None  # calisan_yetkisi garanti eder
    return baglam.kullanici.personel_id
