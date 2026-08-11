import os

from pydantic_settings import BaseSettings, SettingsConfigDict

# --- Kaldirilmis ayarlar (bulgu B4) ------------------------------------------
#
# Buradaki her ad, bir zamanlar var olup KALDIRILMIS bir yapilandirma
# anahtaridir. Uygulama bunlardan birini gorurse acilmayi reddeder.
#
# Neden ayri bir kontrol: `Ayarlar` zaten `extra='forbid'` tasiyor, ama bu
# yalnizca DOTENV DOSYASINDAN okunan anahtarlar icin isler. Tanimadigi
# ORTAM DEGISKENLERINI pydantic-settings sessizce yok sayar - ve gosterim
# sunucusunda ayarlar tam olarak oradan gelir: systemd
# `EnvironmentFile=/opt/vardiya/.env` satirlari ortam degiskenine cevirir
# ve uygulamanin calisma dizininde (`/opt/vardiya/backend`) bir `.env`
# dosyasi bulunmaz.
#
# Dolayisiyla ".env'den o satiri silmezseniz uygulama acilmaz" sozu,
# gercek dagitim yolunda kendiliginden dogru DEGILDI. Asagidaki kontrol
# sozu yerine getirir: iki yol da ayni sonucu verir.
_KALDIRILMIS_ANAHTARLAR: dict[str, str] = {
    # Kisiye ozel calisan paneli baglantisinin HMAC sirri. Kimlik dogrulama
    # (SRS 5.10) geldiginde o yol tumuyle kalkti; parolalar Argon2id ozeti
    # olarak veritabaninda, oturum belirteci her giriste rastgele uretilir.
    # Sessizce yok saymak, kaldirilmis bir sirrin hala ise yaradigi
    # izlenimini birakirdi.
    "CALISAN_PANELI_BAGLANTI_ANAHTARI": (
        "kisiye ozel calisan paneli baglantisi kaldirildi; panele artik "
        "kullanici adi ve parola ile girilir (SRS 5.10)"
    ),
}


class KaldirilmisAyarError(RuntimeError):
    """Ortamda, artik kullanilmayan bir yapilandirma anahtari bulundu."""


def _kaldirilmis_anahtarlari_dogrula() -> None:
    """Ortam degiskenleri arasinda kaldirilmis bir anahtar varsa aciliste hata verir.

    Modul duzeyinde, `Ayarlar()` kurulmadan ONCE cagrilir: hata mesaji
    "eksik ayar" degil "kaldirilmis ayar" demeli, aksi halde okuyan kisi
    degeri doldurmaya calisir.
    """
    # Ortam degiskeni adlari geleneksel olarak buyuk harf; pydantic-settings
    # de esleme yaparken harf buyuklugune bakmaz. Ayni toleransi burada da
    # gosteriyoruz, yoksa kucuk harfle yazilmis bir satir kontrolu atlardi.
    mevcut = {ad.upper(): ad for ad in os.environ}
    bulunanlar = [(mevcut[a], a) for a in _KALDIRILMIS_ANAHTARLAR if a in mevcut]
    if not bulunanlar:
        return
    satirlar = [
        f"  {yazildigi_hal}: {_KALDIRILMIS_ANAHTARLAR[anahtar]}"
        for yazildigi_hal, anahtar in bulunanlar
    ]
    raise KaldirilmisAyarError(
        "Ortamda artik kullanilmayan yapilandirma anahtari var; uygulama acilmadi.\n"
        + "\n".join(satirlar)
        + "\n\nBu satirlari .env dosyasindan (sunucuda /opt/vardiya/.env) silin ve "
        "servisleri yeniden baslatin."
    )


_kaldirilmis_anahtarlari_dogrula()


class Ayarlar(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    veritabani_url: str = "postgresql+psycopg://vardiya:vardiya@localhost:5432/vardiya"
    cozucu_zaman_limiti_saniye: int = 60
    cozucu_arama_iscisi_sayisi: int = 3

    # --- Kimlik dogrulama (SRS 5.10; SDD 5.1b) ------------------------------
    # SRS ve SDD bu dordune sayi vermez; degerler urun karari olarak burada
    # tanimlanir ve ortamdan degistirilebilir.

    # Hareketsizlik suresi ve mutlak son kullanma AYRI uygulanir (SDD 4.2.1):
    # birincisi son istekten, ikincisi girisin kendisinden olculur. Surekli
    # istek gonderen bir oturum da mutlak siniri gecince kapanir.
    oturum_hareketsizlik_dakika: int = 30
    oturum_azami_saat: int = 12

    # FR-10.8: ardisik basarisiz giriste gecici kilit.
    giris_kilit_esigi: int = 5
    giris_kilit_dakika: int = 15

    # Oturum cerezinin Secure niteligi. Sunucuda HTTPS oldugu icin
    # VARSAYILAN true; yerel gelistirme http://localhost uzerinden
    # calistigindan orada .env ile false yapilir - Secure bir cerezi tarayici
    # duz http'ye GONDERMEZ ve giris sessizce basarisiz olur. Yalnizca cerez
    # niteligini etkiler, ikinci bir erisim yolu acmaz.
    oturum_cerezi_secure: bool = True

    # --- Yikici islem izni (bulgu B1/B2) ------------------------------------
    # Veritabanini bosaltan betikler ve test fikstürleri bu ayar olmadan
    # calismaz (app/veri_temizligi.py). VARSAYILANI FALSE olmasi tasarimin
    # kendisidir: kilit, ayarin YOKLUGUNDA devrededir, dolayisiyla ayari
    # tasimayan her ortam - ozellikle gosterim sunucusu - korunur.
    #
    # Gelistirme makinesinde backend/.env icinde true'dur. Sunucuda o dosya
    # hic bulunmaz (dagitimda rsync ile dislanir).
    veri_temizligine_izin: bool = False


ayarlar = Ayarlar()
