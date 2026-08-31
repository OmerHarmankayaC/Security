"""Hata kodlarinin sozlesmesi.

Kodlar arayuzun hangi cumleyi yazacagini belirliyor. Kodsuz kalan bir alan
hatasi arayuzde sessizce Turkce metne duser: Ingilizce bakan kullanici
Turkce bir cumle gorur ve bunu kimse fark etmez, cunku hicbir sey
kirilmaz. Bu dosyanin isi o sessizligi bozmak.

EN ONEMLI TEST `test_her_alan_hatasinin_kodu_var`: yeni bir hata sinifi
yazan kisi kodunu eklemeyi unutursa takim duser. Kodlarin elle yazilmis
olmasi bilincli bir tercihti (sinif adindan turetilseydi bir yeniden
adlandirma API sozlesmesini sessizce degistirirdi) ve elle yazilan her
listenin eksik kalma egilimi vardir; bekcisi budur.
"""

import importlib
import inspect
import pkgutil

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException

import app as uygulama_paketi
from app.hatalar import ALAN_KODLARI, Hata, hata_isleyici, kodu


def _alan_hatalari() -> list[type[Exception]]:
    """`app/` altinda TANIMLANMIS butun `*Error` siniflari.

    Iceri aktarilanlar degil TANIMLANANLAR: `__module__` kontrolu olmasaydi
    `IntegrityError` gibi SQLAlchemy siniflari da listeye girer ve kod
    bekleyen bir liste, bizim olmayan siniflarla dolardi.
    """
    bulunan: dict[str, type[Exception]] = {}
    for bilgi in pkgutil.walk_packages(
        uygulama_paketi.__path__, prefix=f"{uygulama_paketi.__name__}."
    ):
        modul = importlib.import_module(bilgi.name)
        for ad, nesne in inspect.getmembers(modul, inspect.isclass):
            if (
                issubclass(nesne, Exception)
                and ad.endswith("Error")
                and nesne.__module__.startswith("app.")
            ):
                bulunan[f"{nesne.__module__}.{ad}"] = nesne
    return list(bulunan.values())


def test_her_alan_hatasinin_kodu_var() -> None:
    eksik = sorted(h.__name__ for h in _alan_hatalari() if h not in ALAN_KODLARI)

    assert eksik == [], (
        f"Kodsuz alan hatasi: {eksik}. app/hatalar.py icindeki ALAN_KODLARI'na "
        "ekleyin, yoksa arayuz bu hatayi ceviremez."
    )


def test_kodlar_benzersiz() -> None:
    """Iki hata ayni kodu tasisaydi arayuz ikisine ayni cumleyi yazardi."""
    kodlar = list(ALAN_KODLARI.values())

    assert len(kodlar) == len(set(kodlar))


def test_kodlar_makine_okunur_bicimde() -> None:
    """Kod bir METIN DEGIL tanimlayicidir; bosluk ya da buyuk harf
    tasirsa bir gun metin gibi gosterilmeye calisilir."""
    for kod in ALAN_KODLARI.values():
        assert kod.islower()
        assert " " not in kod


def test_alt_sinif_atasinin_koduna_duser() -> None:
    """`KeyError` ile yukselseydi kenar durumdaki bir hata, kullaniciya
    hata mesaji yerine 500 dondururdu."""
    ata, beklenen = next(iter(ALAN_KODLARI.items()))

    class Turemis(ata):  # type: ignore[misc, valid-type]
        pass

    assert kodu(Turemis()) == beklenen


def test_tanimsiz_hata_bilinmeyen_doner() -> None:
    class YabanciError(Exception):
        pass

    assert kodu(YabanciError()) == "bilinmeyen_hata"


# --- Yanit govdesi ----------------------------------------------------------


@pytest.fixture
def istemci() -> TestClient:
    uyg = FastAPI()
    uyg.add_exception_handler(StarletteHTTPException, hata_isleyici)

    @uyg.get("/kodlu")
    def kodlu() -> None:
        raise Hata(status_code=404, kod="surum_yok", detail="Cizelge surumu bulunamadi")

    @uyg.get("/kodsuz")
    def kodsuz() -> None:
        raise HTTPException(status_code=404, detail="Cizelge surumu bulunamadi")

    return TestClient(uyg)


def test_kodlu_hata_govdede_kod_tasir(istemci: TestClient) -> None:
    yanit = istemci.get("/kodlu")

    assert yanit.status_code == 404
    assert yanit.json() == {"detail": "Cizelge surumu bulunamadi", "kod": "surum_yok"}


def test_detay_kalir(istemci: TestClient) -> None:
    """`detail` kaldirilmadi ve kaldirilmayacak.

    Arayuz kodu tanimiyorsa metne duser; yani ceviri eksik kalsa bile
    kullanici bos bir kutu degil Turkce bir cumle gorur. Ayrica API'yi
    tarayicidan degil kabuktan kullanan herkes icin tek okunur alan odur.
    """
    assert istemci.get("/kodlu").json()["detail"] == "Cizelge surumu bulunamadi"


def test_kodsuz_hata_eskisi_gibi_cikar(istemci: TestClient) -> None:
    """Isleyicinin VAR OLMASI mevcut hicbir yaniti degistirmemeli."""
    yanit = istemci.get("/kodsuz")

    assert yanit.json() == {"detail": "Cizelge surumu bulunamadi"}
    assert "kod" not in yanit.json()


# --- Iki tuketici, tek tanim ------------------------------------------------


def _on_yuz_kodlari() -> set[str]:
    """`frontend/src/i18n/sozluk.ts` icindeki `HataKodu` birlesimi.

    Dosya METIN olarak okunuyor cunku burada TypeScript kosturacak bir sey
    yok; amac bir tip kontrolu degil, iki listenin ayni olup olmadigi.
    """
    import re
    from pathlib import Path

    yol = Path(__file__).resolve().parents[2] / "frontend" / "src" / "i18n" / "sozluk.ts"
    if not yol.exists():  # pragma: no cover - depo eksik kurulmus
        pytest.skip(f"on yuz sozlugu bulunamadi: {yol}")
    metin = yol.read_text(encoding="utf-8")
    birlesim = metin.split("export type HataKodu =", 1)[1].split("\n\n", 1)[0]
    return set(re.findall(r"'([a-z_]+)'", birlesim))


# Salt okunur reddi (`salt_okunur`) bu karsilastirmanin DISINDA.
# Ara katmanda uretiliyor ve arayuzde `hataMetni` yoluna hic girmiyor:
# `SaltOkunurHatasi` olarak yakalanip ucan uyariya gidiyor, metni de
# sunucudan geliyor. Iki listeye de eklemek, orada olmayan bir baglantiyi
# varmis gibi gostermek olurdu.
_KAPSAM_DISI = {"salt_okunur"}


def _arka_uc_kodlari() -> set[str]:
    """Arka ucun UREBILECEGI butun kodlar: alan hatalari + yonlendiricilerde
    elle yazilanlar."""
    import re
    from pathlib import Path

    kok = Path(__file__).resolve().parents[1] / "app"
    yazili = set()
    for p in kok.rglob("*.py"):
        yazili |= set(re.findall(r'kod="([a-z_]+)"', p.read_text(encoding="utf-8")))
    return (yazili | set(ALAN_KODLARI.values())) - _KAPSAM_DISI


def test_on_yuz_her_kodu_taniyor() -> None:
    """Iki tuketici, tek tanim.

    Sunucuya eklenip sozluge eklenmeyen bir kod hicbir seyi kirmaz: arayuz
    `detail`e duser ve kullanici Ingilizce ekranda Turkce bir cumle gorur.
    Sessiz oldugu icin bu test var.
    """
    eksik = sorted(_arka_uc_kodlari() - _on_yuz_kodlari())

    assert eksik == [], (
        f"Arka ucta olup on yuz sozlugunde olmayan kod: {eksik}. "
        "frontend/src/i18n/sozluk.ts icindeki HataKodu birlesimine ve iki dilin "
        "`hatalar` tablosuna ekleyin."
    )


def test_sozlukte_olup_arka_ucta_olmayan_kod_yok() -> None:
    """Ters yon de sinaniyor: kaldirilan bir kodun cevirisi sozlukte
    kalirsa, bir daha hic gosterilmeyecek metni tasimaya devam ederiz."""
    fazla = sorted(_on_yuz_kodlari() - _arka_uc_kodlari())

    assert fazla == [], f"Sozlukte olup arka ucun uretmedigi kod: {fazla}"
