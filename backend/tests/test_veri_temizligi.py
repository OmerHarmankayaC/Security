"""Yikici temizligin sozlesmesi (bulgu B1/B2).

Bu dosya bir davranisi degil, bir SOZLESMEYI kilitler: veriyi kim,
neyi, hangi kapsamda siler. Uc iddiasi var ve ucu de daha once gercekten
kirilmis durumlardir:

  1. Betik kapsami (PERSONELE_BAGLI) personele bagli hesaplari siler ama
     yonetim hesaplarina DOKUNMAZ. Once `DELETE` kaskad yapmadigi icin
     betikler bir yabanci anahtar hatasiyla coker, hicbir sey silinmezdi.
  2. Test kapsami (HEPSI) hesap tablolarini da bosaltir - ama bu artik
     ACIK bir secim, `TRUNCATE ... CASCADE`in yan etkisi degil.
  3. Uretim kilidi: izin verilmemis bir ortamda hicbiri calismaz ve
     veritabaninda TEK BIR SATIR bile degismez.
"""

import uuid
from datetime import date

import pytest
from sqlalchemy import func, select

from app.config import ayarlar
from app.db import OturumYerel
from app.models.kimlik import Kullanici, Rol
from app.models.tanim import Personel
from app.veri_temizligi import (
    HesapKapsami,
    UretimKilidiError,
    hesaplari_temizle,
    uretim_kilidini_dogrula,
    veriyi_temizle,
)
from tests.conftest import pg_yoksa_atla


def _benzersiz(on_ek: str) -> str:
    return f"{on_ek}-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def oturum():  # noqa: ANN201 - Session
    pg_yoksa_atla()
    oturum = OturumYerel()
    try:
        yield oturum
    finally:
        oturum.rollback()
        oturum.close()


def _senaryo(oturum) -> tuple[int, int]:  # noqa: ANN001 - Session
    """Bir personel + ona bagli calisan hesabi + bagimsiz bir yonetim hesabi.

    Doner: (calisan_hesap_id, yonetim_hesap_id)
    """
    personel = Personel(
        ad_soyad=_benzersiz("Temizlik"),
        sicil_no=_benzersiz("TMZ"),
        haftalik_hedef_saat=40,
        aktif_baslangic=date(2026, 1, 1),
    )
    oturum.add(personel)
    oturum.flush()

    calisan = Kullanici(
        kullanici_adi=_benzersiz("tmz-calisan").lower(),
        parola_ozeti="x",
        rol=Rol.CALISAN,
        personel_id=personel.personel_id,
    )
    yonetim = Kullanici(
        kullanici_adi=_benzersiz("tmz-yonetim").lower(),
        parola_ozeti="x",
        rol=Rol.HESAP_YONETICISI,
        personel_id=None,
    )
    oturum.add_all([calisan, yonetim])
    oturum.flush()
    return calisan.kullanici_id, yonetim.kullanici_id


def test_betik_kapsami_personele_bagli_hesaplari_siler_yonetimi_birakir(oturum) -> None:  # noqa: ANN001
    """B2c: betikler artik ne cokuyor ne de sessizce her seyi siliyor.

    Silinen sey `DELETE FROM personel`i engelleyen satirlarin TAM
    KUMESIDIR: personel_id'si dolu hesaplar. Yonetim hesabinin kalmasi
    isin ozu - demo verisini tazelemek sistemin giris kapisini
    kapatmamalidir.
    """
    calisan_id, yonetim_id = _senaryo(oturum)

    sonuc = veriyi_temizle(oturum, hesaplar=HesapKapsami.PERSONELE_BAGLI)

    assert sonuc.silinen_hesap >= 1
    assert oturum.get(Kullanici, calisan_id) is None
    assert oturum.get(Kullanici, yonetim_id) is not None
    # Asil kanit: personel tablosu gercekten bosaldi, yani yabanci anahtar
    # artik temizligi durdurmuyor.
    assert oturum.execute(select(func.count()).select_from(Personel)).scalar_one() == 0


def test_test_kapsami_yonetim_hesabini_da_siler(oturum) -> None:  # noqa: ANN001
    """HEPSI kapsami hesap tablolarini bosaltir - ACIK bir secim olarak.

    Davranis eskisiyle ayni; degisen sey nereden geldigi. Once
    `TRUNCATE ... CASCADE`in yan etkisiydi ve hicbir yerde yazmiyordu.
    """
    calisan_id, yonetim_id = _senaryo(oturum)

    sonuc = hesaplari_temizle(oturum, kapsam=HesapKapsami.HEPSI)

    assert sonuc.silinen_hesap >= 2
    assert oturum.get(Kullanici, calisan_id) is None
    assert oturum.get(Kullanici, yonetim_id) is None


def test_izin_yokken_hicbir_sey_silinmez(oturum, monkeypatch) -> None:  # noqa: ANN001
    """B1d: uretim kilidi.

    Yalniz "hata firlatiyor mu" degil, "veritabanina dokunmadan mi
    firlatiyor" da olculur. Kilit, silme basladiktan sonra devreye girseydi
    yarim temizlenmis bir veritabani birakirdi - hicbir kilidin
    olmamasindan daha kotu bir durum.
    """
    calisan_id, yonetim_id = _senaryo(oturum)
    monkeypatch.setattr(ayarlar, "veri_temizligine_izin", False)

    with pytest.raises(UretimKilidiError):
        veriyi_temizle(oturum, hesaplar=HesapKapsami.PERSONELE_BAGLI)
    with pytest.raises(UretimKilidiError):
        hesaplari_temizle(oturum, kapsam=HesapKapsami.HEPSI)

    assert oturum.get(Kullanici, calisan_id) is not None
    assert oturum.get(Kullanici, yonetim_id) is not None


def test_kilit_mesaji_hedef_veritabanini_yazar_parolayi_yazmaz(monkeypatch) -> None:
    """Mesaj eyleme donusebilir olmali: hangi veritabani, hangi degisken.

    Parolanin sizmamasi ayrica olculur; hata mesajlari gunluge duser ve
    gunluge yazilan bir sir artik sir degildir (bkz. app/kayit.py).
    """
    monkeypatch.setattr(ayarlar, "veri_temizligine_izin", False)
    monkeypatch.setattr(
        ayarlar, "veritabani_url", "postgresql+psycopg://vardiya:GIZLI@sunucu:5432/vardiya"
    )

    with pytest.raises(UretimKilidiError) as hata:
        uretim_kilidini_dogrula()

    mesaj = str(hata.value)
    assert "VERI_TEMIZLIGINE_IZIN" in mesaj
    assert "sunucu:5432/vardiya" in mesaj
    assert "GIZLI" not in mesaj
