"""Gosterim kimlik bilgisinin sozlesmesi (Demo Senaryosu 7).

Bu dosyanin asil isi bir OLUMSUZ iddiayi kilitlemek: gercek bir kurulumda
demo kimlik bilgisi HICBIR yuzeyde bulunmaz. Uc nokta kapali kipte 404 doner
ve ne parola ne kullanici adi sizar.

Ikinci iddia: parolalar koda ya da on yuz paketine GOMULMEZ ve saklanmaz.
Tohumdan turetilirler; tohum degistiginde butun parolalar degisir ve her
hesabinki DIGERLERINDEN FARKLIDIR.

Ucuncu iddia: sistem yoneticisi hesabi ACILIR ama GOSTERILMEZ. Gosterim
ortami herkese aciktir; en genis yetkiyi giris ekranina yazmak, demoyu
gezen herkese hesap yonetimi hakki vermek olurdu.
"""

from fastapi.testclient import TestClient

from app.config import ayarlar
from app.main import app
from app.models.kimlik import Rol
from app.services.demo_hesaplari import DEMO_HESAPLARI, gosterilecekler, parola_uret

istemci = TestClient(app)

_TOHUM = "gosterim-icin-uzun-tohum"


def _demo_kipini_ac(monkeypatch, *, tohum: str | None = _TOHUM) -> None:  # noqa: ANN001
    monkeypatch.setattr(ayarlar, "demo_kipi", True)
    monkeypatch.setattr(ayarlar, "demo_parola_tohumu", tohum)


def test_demo_kipi_kapaliyken_404_doner() -> None:
    # Varsayilan ayar zaten kapali; acikca dogrulanir ki test, ayarin
    # varsayilanini da bir sozlesme olarak kilitlesin.
    assert ayarlar.demo_kipi is False

    yanit = istemci.get("/api/demo/kimlik")

    assert yanit.status_code == 404
    # 403 DEGIL 404: 403, var olan ama erisilemeyen bir kaynagi isaret eder
    # ve gercek bir kurulumda "demo kimlik bilgisi bir yerlerde duruyor"
    # izlenimi verirdi.
    assert yanit.status_code != 403


def test_kapali_kipte_hicbir_kimlik_bilgisi_sizmaz() -> None:
    govde = istemci.get("/api/demo/kimlik").text
    for hesap in DEMO_HESAPLARI:
        assert hesap.kullanici_adi not in govde


def test_demo_kipi_acikken_hesaplar_doner(monkeypatch) -> None:  # noqa: ANN001
    _demo_kipini_ac(monkeypatch)

    yanit = istemci.get("/api/demo/kimlik")

    assert yanit.status_code == 200
    hesaplar = yanit.json()["hesaplar"]
    assert [h["kullanici_adi"] for h in hesaplar] == [h.kullanici_adi for h in gosterilecekler()]
    for h in hesaplar:
        assert h["parola"] == parola_uret(_TOHUM, h["kullanici_adi"])


def test_her_hesabin_parolasi_farklidir(monkeypatch) -> None:  # noqa: ANN001
    """Dordu ayni dize olsaydi "parolayi biliyorum" ile "hepsini biliyorum"
    ayni seye cikardi."""
    _demo_kipini_ac(monkeypatch)

    parolalar = [h["parola"] for h in istemci.get("/api/demo/kimlik").json()["hesaplar"]]

    assert len(set(parolalar)) == len(parolalar)
    assert all(len(p) == 12 and p.isalnum() and p.islower() for p in parolalar)


def test_parolalar_calisma_zamaninda_tohumdan_turetilir(monkeypatch) -> None:  # noqa: ANN001
    """Gomulu olsalardi tohumu degistirmek yaniti degistirmezdi."""
    _demo_kipini_ac(monkeypatch)
    ilk = [h["parola"] for h in istemci.get("/api/demo/kimlik").json()["hesaplar"]]

    _demo_kipini_ac(monkeypatch, tohum="bambaska-bir-tohum")
    ikinci = [h["parola"] for h in istemci.get("/api/demo/kimlik").json()["hesaplar"]]

    assert set(ilk).isdisjoint(ikinci)


def test_tohum_tanimsizken_kutu_cizilmez(monkeypatch) -> None:  # noqa: ANN001
    """Demo kipi acik ama tohum yoksa turetilecek parola yoktur; bos parolali
    bir kutu, calismayan bir girisi calisiyor gibi gosterirdi."""
    _demo_kipini_ac(monkeypatch, tohum=None)

    assert istemci.get("/api/demo/kimlik").status_code == 404


def test_sistem_yoneticisi_acilir_ama_gosterilmez(monkeypatch) -> None:  # noqa: ANN001
    _demo_kipini_ac(monkeypatch)

    tanimli = {h.kullanici_adi for h in DEMO_HESAPLARI if h.rol is Rol.SISTEM_YONETICISI}
    donen = {h["kullanici_adi"] for h in istemci.get("/api/demo/kimlik").json()["hesaplar"]}

    assert tanimli, "gosterim ortaminin bir sistem yoneticisi olmali (FR-10.12)"
    assert not (tanimli & donen)


def test_uc_rol_de_gorunur(monkeypatch) -> None:  # noqa: ANN001
    """Idare, hesap yoneticisi ve calisan — urunun uc yuzeyi."""
    _demo_kipini_ac(monkeypatch)

    roller = {h["rol"] for h in istemci.get("/api/demo/kimlik").json()["hesaplar"]}

    assert roller == {Rol.IDARE.value, Rol.HESAP_YONETICISI.value, Rol.CALISAN.value}
