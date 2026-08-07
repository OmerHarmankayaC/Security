"""Kisiye ozel baglanti anahtarinin turetilmesi (Backlog B-05, SRS FR-9.1).

Veritabani gerektirmez - saf fonksiyon testleri.
"""

from app.config import ayarlar
from app.services import calisan_baglantisi
from app.services.calisan_baglantisi import anahtar_gecerli_mi, anahtar_uret, baglanti_yolu


def test_anahtar_kisiye_ozeldir() -> None:
    """Asil nokta: iki personelin anahtari FARKLI olmalidir - tek ortak
    anahtarla URL'deki personel_id'yi degistiren herkes baskasinin
    cizelgesini gorebiliyordu (FR-9.1 ihlali)."""
    assert anahtar_uret(1) != anahtar_uret(2)


def test_anahtar_ayni_girdi_icin_kararlidir() -> None:
    """Anahtar saklanmadigi icin (ek tablo yok) her istekte yeniden turetilir;
    ayni personel_id her zaman ayni anahtari vermelidir, yoksa daha once
    dagitilan baglantilar bozulur."""
    assert anahtar_uret(42) == anahtar_uret(42)


def test_dogrulama_yalniz_kendi_anahtarini_kabul_eder() -> None:
    assert anahtar_gecerli_mi(7, anahtar_uret(7))
    assert not anahtar_gecerli_mi(7, anahtar_uret(8))
    assert not anahtar_gecerli_mi(7, "")
    assert not anahtar_gecerli_mi(7, "yanlis")


def test_anahtar_sunucu_sirrina_baglidir(monkeypatch) -> None:  # noqa: ANN001 - pytest fixture
    """Sir degisince butun anahtarlar degisir (sir sizarsa dondurulebilir)."""
    onceki = anahtar_uret(5)
    monkeypatch.setattr(
        calisan_baglantisi.ayarlar, "calisan_paneli_baglanti_anahtari", "baska-bir-sir"
    )
    assert anahtar_uret(5) != onceki


def test_baglanti_yolu_panelin_bekledigi_bicimde() -> None:
    """main.tsx yolu `/calisan/{personel_id}` olarak ayristirir ve `anahtar`
    sorgu parametresini bekler; betigin urettigi baglanti buna uymali."""
    yol = baglanti_yolu(3)
    assert yol == f"/calisan/3?anahtar={anahtar_uret(3)}"


def test_varsayilan_sir_hala_kullanimda_ise_gorunur_olsun() -> None:
    """Uyari niteliginde: .env.example'daki varsayilan sir degistirilmeden
    dagitim yapilirsa anahtarlar tahmin edilebilir olur. Bu test sirri
    zorlamaz (yerel gelistirmede varsayilan normaldir), yalnizca ayarin
    okunabildigini ve bos olmadigini dogrular."""
    assert ayarlar.calisan_paneli_baglanti_anahtari
