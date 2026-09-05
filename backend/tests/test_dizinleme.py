"""Arama motoru dizinlemesine ACIK olma sozlesmesi.

Onceki hal bunun TERSIYDI: her yanit `X-Robots-Tag: noindex` tasiyordu ve
yedi test onu kilitliyordu. O karar demo YAYINLANMAYACAKKEN alinmisti;
gerekcesi, baglamdan kopuk bir arama sonucunda gorulen kurgu verinin
gercek bir kurumun cizelgesi sanilmasiydi. Demo artik herkese acik ve
bulunabilir olmasi isteniyor.

Test SILINMEDI, TERSINE CEVRILDI. Silinseydi ara katmani geri ekleyen bir
degisiklik hicbir seyi kirmadan gecerdi ve siteyi arama sonuclarindan
sessizce dusururdu - kimse fark etmezdi, cunku "gorunmuyor" ile "hic
aranmadi" disaridan ayni gorunur. Bir basligin YOKLUGUNU sinamak, varligini
sinamaktan daha az yer tutar: yedi test yerine bir tane yetiyor, cunku
korunacak sey de daha basit.
"""

import pytest
from fastapi.testclient import TestClient

from app.config import ayarlar
from app.main import app

istemci = TestClient(app)


@pytest.mark.parametrize(
    "yol",
    [
        "/health",
        "/api/ortam",
        "/api/demo/kimlik",  # kapali kipte 404
        "/api/personel",  # oturumsuz 401
        "/api/boyle-bir-yol-yok",  # 404
    ],
)
def test_hicbir_yanit_dizinlemeyi_engellemez(yol: str) -> None:
    yanit = istemci.get(yol)

    assert "X-Robots-Tag" not in yanit.headers, (
        f"{yol} ({yanit.status_code}) dizinlemeyi engelleyen bir baslik dondurdu; "
        "demo artik aranabilir olmali."
    )


def test_gosterim_kipi_de_engellemez(monkeypatch) -> None:  # noqa: ANN001
    """Hata yanitlari ve gosterim kipi ayrica sinaniyor cunku engel, eger
    geri gelirse, en kolay oralardan geri gelir: birini kapsamayan bir ara
    katman yazmak, hepsini kapsayan birini yazmaktan kolaydir."""
    monkeypatch.setattr(ayarlar, "demo_kipi", True)

    yanit = istemci.post("/api/personel", json={})

    assert yanit.status_code == 403  # salt okunur reddi
    assert "X-Robots-Tag" not in yanit.headers
