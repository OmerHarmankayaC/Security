"""Gosterim kipinde yazma yasaginin sozlesmesi (Demo Senaryosu 2.2, 10).

Uc iddia:

  1. Kapali kipte HICBIR SEY degismez. Gercek bir kurulum bu dosyadan
     etkilenmemeli; kapinin varligi urunun davranisini daraltmaz.
  2. Acik kipte YAZMA UCLARININ TAMAMI reddedilir. Tek tek saymak yerine
     uygulamanin kendi yol tablosu geziliyor: yarin eklenen bir yazma ucu
     bu testi otomatik olarak kapsar. Elle yazilmis bir liste, tam da
     unutulacak yerde eksik kalirdi.
  3. Okumaya izin verilen uc POST ucu (giris, cikis, on kontrol, dogrulama)
     acik kalir. Bunlar gosterimin anlatmak istedigi seyler; kapatilsalardi
     duzenleme yolu gorunur ama denenemez olurdu.
"""

import pytest
from fastapi.testclient import TestClient

from app.config import ayarlar
from app.main import app
from app.salt_okunur import _IZINLI_YOLLAR

istemci = TestClient(app)

_YAZMA_YONTEMLERI = {"POST", "PUT", "PATCH", "DELETE"}


def _yazma_uclari() -> list[tuple[str, str]]:
    """Uygulamanin yol tablosundan yazma uclari; izinli olanlar haric."""
    uclar: list[tuple[str, str]] = []
    for yol in app.routes:
        yontemler = getattr(yol, "methods", set()) & _YAZMA_YONTEMLERI
        if not yontemler or yol.path in _IZINLI_YOLLAR:
            continue
        uclar.extend((yontem, yol.path) for yontem in sorted(yontemler))
    return uclar


def _ornek_yol(yol: str) -> str:
    """`{id}` bicimindeki parametreleri gecerli bir degerle doldurur."""
    return (
        yol.replace("{tarih}", "2026-01-01")
        .replace("}", "")
        .replace("{", "")
        .replace("bina_id", "1")
        .replace("kullanici_id", "1")
        .replace("kimlik", "H1")
        .replace("nokta_id", "1")
        .replace("personel_id", "1")
        .replace("talep_id", "1")
        .replace("tercih_id", "1")
        .replace("yetkinlik_id", "1")
        .replace("musaitlik_id", "1")
        .replace("surum_id", "1")
        .replace("is_id", "1")
    )


def test_kapali_kipte_kapi_hicbir_seye_dokunmaz() -> None:
    """Reddetme YALNIZCA demo kipine bagli; gercek kurulum etkilenmez.

    Yetkisiz bir yazma istegi kimlik dogrulamaya takilmali (401), yazma
    yasagina degil (403) - ikisi karisirsa kapi, kendisi kapali olsa bile
    urunun hata mesajlarini degistirmis olurdu.
    """
    assert ayarlar.demo_kipi is False

    yanit = istemci.post("/api/personel", json={})

    assert yanit.status_code != 403


@pytest.mark.parametrize(("yontem", "yol"), _yazma_uclari())
def test_demo_kipinde_her_yazma_ucu_reddedilir(monkeypatch, yontem: str, yol: str) -> None:  # noqa: ANN001
    monkeypatch.setattr(ayarlar, "demo_kipi", True)

    yanit = istemci.request(yontem, _ornek_yol(yol), json={})

    # KIMLIK DOGRULAMADAN ONCE reddedilir ve bu bilincli: oturumu olan bir
    # ziyaretci de yazamaz, yazamadigini da ayni mesajdan ogrenir.
    assert yanit.status_code == 403, f"{yontem} {yol} yazma yasagini gecti"
    govde = yanit.json()
    assert "kaydedilmez" in govde["detail"]
    # KOD, arayuzun uyariyi yalnizca bu ret icin cikarabilmesi icin; rol
    # tabanli 403'ler ayni uyariyi cikarmamali.
    assert govde["kod"] == "salt_okunur"


def test_okuma_uclari_demo_kipinde_de_calisir(monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.setattr(ayarlar, "demo_kipi", True)

    assert istemci.get("/health").status_code == 200
    assert istemci.get("/api/ortam").status_code == 200


def test_izinli_post_uclari_yazma_yasagina_takilmaz(monkeypatch) -> None:  # noqa: ANN001
    """Giris, cikis, on kontrol ve dogrulama acik kalmali.

    Bunlar hicbir sey yazmaz ve gosterimin asil anlattigi seylerdir; 403
    donselerdi duzenleme yolu gorunur ama denenemez olurdu.
    """
    monkeypatch.setattr(ayarlar, "demo_kipi", True)

    for yol in sorted(_IZINLI_YOLLAR):
        yanit = istemci.post(yol, json={})
        assert yanit.status_code != 403, f"{yol} yazma yasagina takildi"


def test_yazma_ucu_listesi_bos_degil() -> None:
    """Parametreli testin sessizce bos gecmemesi icin.

    Yol tablosu okunamazsa `_yazma_uclari()` bos doner, parametreli test hic
    kosmaz ve takim yesil kalir - olculmemis bir guvence, olculmus gibi
    gorunurdu.
    """
    assert len(_yazma_uclari()) > 30
