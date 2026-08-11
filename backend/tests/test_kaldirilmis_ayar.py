"""Kaldirilmis yapilandirma anahtarlari aciliste reddedilir (bulgu B4).

Bu testin varlik nedeni, belgeye yazilmis bir SOZUN gerceklesmesidir.
`.env.example` ve deploy/DAGITIM.md, `CALISAN_PANELI_BAGLANTI_ANAHTARI`
satiri silinmezse uygulamanin acilmayacagini yaziyordu. O soz gercek
dagitim yolunda tutulmuyordu:

  - `Ayarlar` `extra='forbid'` tasir, ama pydantic-settings bunu yalnizca
    DOTENV DOSYASINDAN okunan anahtarlara uygular; tanimadigi ORTAM
    DEGISKENLERINI sessizce yok sayar.
  - Sunucuda ayarlar tam olarak ortam degiskeni olarak gelir: systemd
    `EnvironmentFile=/opt/vardiya/.env` satirlari ortama cevirir ve
    uygulamanin calisma dizininde bir `.env` dosyasi bulunmaz.

Yani sunucuda eski anahtar kalsa uygulama sorunsuz aciliyordu. Asagidaki
iki test iki yolun da ayni sonucu verdigini kilitler.
"""

import pytest

from app.config import KaldirilmisAyarError, _kaldirilmis_anahtarlari_dogrula


def test_ortam_degiskeni_olarak_gelen_eski_anahtar_reddedilir(monkeypatch) -> None:  # noqa: ANN001
    """Sunucudaki gercek yol: systemd EnvironmentFile -> ortam degiskeni."""
    monkeypatch.setenv("CALISAN_PANELI_BAGLANTI_ANAHTARI", "eski-sir")

    with pytest.raises(KaldirilmisAyarError) as hata:
        _kaldirilmis_anahtarlari_dogrula()

    mesaj = str(hata.value)
    # Mesaj ne yapilacagini soylemeli: hangi anahtar, nereden silinecek.
    assert "CALISAN_PANELI_BAGLANTI_ANAHTARI" in mesaj
    assert "/opt/vardiya/.env" in mesaj
    # Sirrin KENDISI mesaja girmemeli; hata gunluge duser.
    assert "eski-sir" not in mesaj


def test_harf_buyuklugu_kontrolu_atlatmaz(monkeypatch) -> None:  # noqa: ANN001
    """pydantic-settings esleme yaparken harf buyuklugune bakmaz; elle
    yazilmis bir kontrolun daha dar olmasi, kucuk harfle yazilmis bir
    satirin sessizce gecmesi demek olurdu."""
    monkeypatch.setenv("calisan_paneli_baglanti_anahtari", "eski-sir")

    with pytest.raises(KaldirilmisAyarError):
        _kaldirilmis_anahtarlari_dogrula()


def test_temiz_ortamda_sessiz_gecer(monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.delenv("CALISAN_PANELI_BAGLANTI_ANAHTARI", raising=False)
    _kaldirilmis_anahtarlari_dogrula()
