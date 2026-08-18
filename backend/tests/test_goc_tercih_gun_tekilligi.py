"""Goc `c4f1a7d20b93`in karar mantigi (final review bulgu 3).

DB'ye BAGLANMAZ: goc dosyasi `alembic/versions/` altinda normal bir Python
paketi degildir (yol uzerinden `importlib` ile yuklenir) ve bu testler
yalnizca saf karar fonksiyonunu (`_riskli_gruplari_bul`) sinar -- gercek
`upgrade()`/`downgrade()` `op.get_bind()` uzerinden ancak gercek bir Alembic
goc baglaminda calisir, birim testine uygun degildir.

Kapsam: bir kopya grubunda BEKLEMEDE-DISI (KARARLANMIS) bir satir varsa goc
DURMALI ve hicbir satir silinmemeli. Bu test, o karari veren fonksiyonun
dogru grubu isaretledigini dogrular.
"""

import importlib.util
from collections import namedtuple
from datetime import date
from pathlib import Path

_GOC_YOLU = (
    Path(__file__).resolve().parents[1]
    / "alembic"
    / "versions"
    / "c4f1a7d20b93_tercih_gun_tekilligi.py"
)

_Satir = namedtuple("_Satir", "personel_id tarih adet durumlar")


def _goc_modulunu_yukle():  # noqa: ANN202 - test yardimcisi, donus tipi onemsiz
    spec = importlib.util.spec_from_file_location("goc_c4f1a7d20b93", _GOC_YOLU)
    assert spec is not None and spec.loader is not None
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def test_hepsi_beklemede_olan_grup_riskli_sayilmaz() -> None:
    modul = _goc_modulunu_yukle()
    guvenli = _Satir(
        personel_id=1, tarih=date(2026, 9, 3), adet=2, durumlar=["BEKLEMEDE", "BEKLEMEDE"]
    )
    assert modul._riskli_gruplari_bul([guvenli]) == []


def test_beklemede_disi_satir_iceren_grup_riskli_sayilir() -> None:
    """Senaryo tam olarak brief'teki ornek: personel 7 / 2026-09-03'te
    tercih_id=41 ONAYLANDI, tercih_id=58 BEKLEMEDE (sonradan girildi) --
    eski kural (en yeni tercih_id kalir) 41'i silerdi. Bu artik RISKLI
    sayilmali ve goc DURMALI."""
    modul = _goc_modulunu_yukle()
    riskli = _Satir(
        personel_id=7, tarih=date(2026, 9, 3), adet=2, durumlar=["ONAYLANDI", "BEKLEMEDE"]
    )
    assert modul._riskli_gruplari_bul([riskli]) == [riskli]


def test_karisik_liste_yalniz_riskli_gruplari_dondurur() -> None:
    """Guvenli ve riskli gruplar ayni sayimda yan yana bulunabilir; kapı
    yalnizca RISKLI olanlari isaretlemeli, guvenli olani yanlislikla
    durdurmamali."""
    modul = _goc_modulunu_yukle()
    guvenli = _Satir(
        personel_id=1, tarih=date(2026, 9, 3), adet=2, durumlar=["BEKLEMEDE", "BEKLEMEDE"]
    )
    riskli = _Satir(
        personel_id=7, tarih=date(2026, 9, 3), adet=2, durumlar=["BEKLEMEDE", "REDDEDILDI"]
    )
    assert modul._riskli_gruplari_bul([guvenli, riskli]) == [riskli]


def test_kopya_yoksa_riskli_liste_bostur() -> None:
    modul = _goc_modulunu_yukle()
    assert modul._riskli_gruplari_bul([]) == []
