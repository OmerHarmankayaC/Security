"""Demo kadrosunun sozlesmesi (Demo Senaryosu 4.3).

Veritabani gerektirmez; uretecin sabitleri uzerinde calisir. Bu dosya bir
davranisi degil bir SAYIYI kilitler, cunku sayinin kendisi anlam tasiyor:

  - kirk kisi, kabul olcumunun referans ornegiyle ayni olcek (SDD 3.4.2);
  - dokuz sef, sikisik senaryonun dayandigi kirilgan havuz;
  - uc kismi zamanli, adil payin orantili hesaplandigini gosteren kayit;
  - iki sinir durumu (yeni baslayan, ayrilan) ve ikisinin AYNI KISI
    OLMAMASI - ayni kisiye dusselerdi iki mekanizma da tek kayitta
    gizlenir ve biri bozuldugunda digeri bunu ortbas ederdi.
"""

import importlib.util
from pathlib import Path

from app.services.ornek_senaryo import PERSONEL_GRUPLARI, VARDIYA_SEFI

_BETIK = Path(__file__).resolve().parents[1] / "scripts" / "demo_veri_uret.py"


def _ureteci_yukle():  # noqa: ANN202 - modul nesnesi
    spec = importlib.util.spec_from_file_location("demo_veri_uret", _BETIK)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def test_kadro_kirk_kisi_dokuzu_sef() -> None:
    sef_grubu = next(g for g in PERSONEL_GRUPLARI if VARDIYA_SEFI in g.yetkinlikler)
    assert sum(g.sayi for g in PERSONEL_GRUPLARI) == 40
    assert sef_grubu.sayi == 9


def test_siciller_surekli_ve_kadroyu_kapsar() -> None:
    modul = _ureteci_yukle()
    kadro = sum(g.sayi for g in PERSONEL_GRUPLARI)
    siciller = [modul._sicil(i) for i in range(kadro)]

    assert siciller[0] == "D-1001"
    assert siciller[-1] == "D-1040"
    assert len(set(siciller)) == kadro


def test_uc_sinir_durumu_ayri_kisilere_duser() -> None:
    modul = _ureteci_yukle()
    kadro = sum(g.sayi for g in PERSONEL_GRUPLARI)
    siciller = {modul._sicil(i) for i in range(kadro)}

    kismi = set(modul._KISMI_ZAMANLI_SICILLER)
    assert len(kismi) == 3
    assert kismi <= siciller
    assert modul._YENI_BASLAYAN_SICIL in siciller
    assert modul._AYRILAN_SICIL in siciller
    assert modul._YENI_BASLAYAN_SICIL != modul._AYRILAN_SICIL
    # Sinir durumlari kismi zamanlilarla da CAKISMAZ: kismi zamanli birinin
    # ayrica ufkun ortasinda ise baslamasi, iki farkli oranin (hedef payi ve
    # calisabilir oran) carpimini tek kayitta gizlerdi.
    assert modul._YENI_BASLAYAN_SICIL not in kismi
    assert modul._AYRILAN_SICIL not in kismi


def test_adlar_kadroyu_karsilar_ve_tekrarsizdir() -> None:
    modul = _ureteci_yukle()
    kadro = sum(g.sayi for g in PERSONEL_GRUPLARI)

    assert len(modul._ADLAR) >= kadro
    assert len(set(modul._ADLAR)) == len(modul._ADLAR)


def test_kota_bakiyesi_kota_kartini_doldurur() -> None:
    """Demo Senaryosu 9.3: en az bir kisi yillik kotanin yarisinin ustunde."""
    modul = _ureteci_yukle()
    yillik_kota = next(t for t in modul.KURAL_TANIMLARI if t["kimlik"] == "H10")["parametreler"][
        "yillik_fazla_kotasi"
    ]

    assert max(modul._DEVIR_BAKIYELERI.values()) > yillik_kota / 2
