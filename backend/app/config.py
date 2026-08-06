from pydantic_settings import BaseSettings, SettingsConfigDict


class Ayarlar(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    veritabani_url: str = "postgresql+psycopg://vardiya:vardiya@localhost:5432/vardiya"
    cozucu_zaman_limiti_saniye: int = 60
    cozucu_arama_iscisi_sayisi: int = 3
    calisan_paneli_baglanti_anahtari: str = "degistirilmeli"


ayarlar = Ayarlar()
