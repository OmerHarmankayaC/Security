from pydantic_settings import BaseSettings, SettingsConfigDict


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


ayarlar = Ayarlar()
