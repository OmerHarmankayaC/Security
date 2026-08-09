"""/api/on-kontrol icin mutlu yol + 404 testi (Sprint 2 Gun 7).

Canli bir PostgreSQL gerektirir; baglanilamiyorsa atlanir.
"""

import uuid
from datetime import date, time, timedelta

import pytest
from fastapi.testclient import TestClient

from app.db import OturumYerel
from app.models.sonuc import Donem
from app.models.tanim import GorevNoktasi, GunTipi, Talep, VardiyaTipi
from tests.conftest import pg_yoksa_atla, yetkili_istemci


@pytest.fixture
def istemci() -> TestClient:
    pg_yoksa_atla()
    return yetkili_istemci()


def test_on_kontrol_bulunamayan_donemde_404(istemci: TestClient) -> None:
    yanit = istemci.post("/api/on-kontrol", json={"donem_id": 999999})
    assert yanit.status_code == 404


def test_on_kontrol_kadro_yeterliyken_yapisal_engel_bildirmez(istemci: TestClient) -> None:
    """Bu testin olctugu sey KADRO ARITMETIGI: talep kadroyla karsilanabiliyorsa
    yapisal engel bildirilmemeli.

    Yapilandirma uyarilari (engel_mi=False) bu olcumun disindadir ve burada
    ayiklanir: bu fikstur kural satiri kurmadigindan katalogda S1 bulunmayabilir
    ve o durumda uyari cikmasi DOGRUDUR (talep kisiti kurulmaz)."""
    on_ek = uuid.uuid4().hex[:8]
    oturum = OturumYerel()
    try:
        vardiya_tipi = VardiyaTipi(
            ad=f"Gunduz-{on_ek}",
            baslangic_saati=time(8, 0),
            bitis_saati=time(16, 0),
            sure_saat=8,
            gece_mi=False,
        )
        nokta = GorevNoktasi(ad=f"Kapi-{on_ek}")
        oturum.add_all([vardiya_tipi, nokta])
        oturum.flush()

        baslangic = date(2026, 4, 6)
        bitis = baslangic + timedelta(days=6)
        oturum.add(
            Talep(
                nokta_id=nokta.nokta_id,
                vardiya_tipi_id=vardiya_tipi.vardiya_tipi_id,
                gun_tipi=GunTipi.HAFTA_ICI,
                tarih=None,
                gereken_sayi=0,
            )
        )
        donem = Donem(
            baslangic_tarihi=baslangic,
            bitis_tarihi=bitis,
            tercih_son_tarihi=baslangic - timedelta(days=7),
        )
        oturum.add(donem)
        oturum.commit()
        donem_id = donem.donem_id
    finally:
        oturum.close()

    yanit = istemci.post("/api/on-kontrol", json={"donem_id": donem_id})
    assert yanit.status_code == 200
    engeller = [b for b in yanit.json()["bulgular"] if b["engel_mi"]]
    assert engeller == []
