"""Surumler ekraninin uc noktalari (Sprint 3: SDD 6.3.5, FR-7.x).

Surum listesinin ozet bilgileri (toplam ceza, kapsama acigi sayisi) ve
karsilastirma islevi - ki bu ayni zamanda Proje Tanim Dokumani bolum 5'in
altinci kabul kriterinin ("yeniden cozumde degisen atama sayisi
raporlanir") olculdugu yerdir.

Canli bir PostgreSQL gerektirir; baglanamiyorsa atlanir.
"""

import uuid
from datetime import UTC, date, datetime, time, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db import OturumYerel
from app.models.sonuc import (
    Atama,
    AtamaKaynagi,
    CizelgeSurumu,
    CizelgeSurumuDurumu,
    CozumIsi,
    CozumIsiDurumu,
    Donem,
    KapsamaAcigi,
)
from app.models.tanim import GorevNoktasi, Personel, VardiyaTipi
from tests.conftest import pg_yoksa_atla, yetkili_istemci

_TABLOLAR = (
    "TRUNCATE kapsama_acigi, cozum_isi, atama, cizelge_surumu, musaitlik, "
    "donem, talep, personel_yetkinlik, personel, gorev_noktasi, "
    "vardiya_tipi, bina, yetkinlik, kural, tercih CASCADE"
)


@pytest.fixture
def istemci() -> TestClient:
    pg_yoksa_atla()
    return yetkili_istemci()


def _benzersiz(on_ek: str) -> str:
    return f"{on_ek}-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def senaryo() -> dict[str, int]:
    """Ayni donemde iki surum. Personel P1'in gunleri:
      gun0: iki surumde de ayni            -> fark yok
      gun1: surum 2'de vardiya tipi degisti -> 'degisti'
      gun2: yalniz surum 1'de               -> 'kaldirildi'
      gun3: yalniz surum 2'de               -> 'eklendi'
    P2'nin gun0'i iki surumde de ayni -> fark yok (fark sayimi personel
    ekseninde de dogru calissin diye ikinci bir personel var).
    """
    on_ek = _benzersiz("surum")
    oturum = OturumYerel()
    try:
        oturum.execute(text(_TABLOLAR))
        oturum.commit()

        gunduz = VardiyaTipi(
            ad=f"Gunduz-{on_ek}",
            baslangic_saati=time(8, 0),
            bitis_saati=time(16, 0),
            sure_saat=8,
            gece_mi=False,
        )
        gece = VardiyaTipi(
            ad=f"Gece-{on_ek}",
            baslangic_saati=time(0, 0),
            bitis_saati=time(8, 0),
            sure_saat=8,
            gece_mi=True,
        )
        oturum.add_all([gunduz, gece])
        nokta = GorevNoktasi(ad=f"Nokta-{on_ek}")
        oturum.add(nokta)
        p1 = Personel(
            ad_soyad=f"P1-{on_ek}",
            sicil_no=_benzersiz("SR1"),
            haftalik_hedef_saat=40,
            aktif_baslangic=date(2026, 1, 1),
        )
        p2 = Personel(
            ad_soyad=f"P2-{on_ek}",
            sicil_no=_benzersiz("SR2"),
            haftalik_hedef_saat=40,
            aktif_baslangic=date(2026, 1, 1),
        )
        oturum.add_all([p1, p2])
        oturum.flush()

        donem = Donem(
            baslangic_tarihi=date(2026, 5, 4),
            bitis_tarihi=date(2026, 5, 10),
            tercih_son_tarihi=date(2026, 4, 27),
        )
        oturum.add(donem)
        oturum.flush()

        s1 = CizelgeSurumu(donem_id=donem.donem_id, surum_no=1, durum=CizelgeSurumuDurumu.ARSIV)
        s2 = CizelgeSurumu(donem_id=donem.donem_id, surum_no=2, durum=CizelgeSurumuDurumu.TASLAK)
        oturum.add_all([s1, s2])
        oturum.flush()

        gun0, gun1 = date(2026, 5, 4), date(2026, 5, 5)
        gun2, gun3 = date(2026, 5, 6), date(2026, 5, 7)

        def at(surum_id: int, personel_id: int, tarih: date, vardiya_tipi_id: int) -> Atama:
            return Atama(
                surum_id=surum_id,
                personel_id=personel_id,
                tarih=tarih,
                vardiya_tipi_id=vardiya_tipi_id,
                nokta_id=nokta.nokta_id,
                kaynak=AtamaKaynagi.COZUCU,
            )

        oturum.add_all(
            [
                at(s1.surum_id, p1.personel_id, gun0, gunduz.vardiya_tipi_id),
                at(s1.surum_id, p1.personel_id, gun1, gunduz.vardiya_tipi_id),
                at(s1.surum_id, p1.personel_id, gun2, gunduz.vardiya_tipi_id),
                at(s1.surum_id, p2.personel_id, gun0, gece.vardiya_tipi_id),
                at(s2.surum_id, p1.personel_id, gun0, gunduz.vardiya_tipi_id),
                at(s2.surum_id, p1.personel_id, gun1, gece.vardiya_tipi_id),
                at(s2.surum_id, p1.personel_id, gun3, gunduz.vardiya_tipi_id),
                at(s2.surum_id, p2.personel_id, gun0, gece.vardiya_tipi_id),
            ]
        )

        # Surum 2 icin iki cozum isi: liste EN SONUNCUSUNUN cezasini gostermeli.
        oturum.add_all(
            [
                CozumIsi(
                    surum_id=s2.surum_id,
                    durum=CozumIsiDurumu.TAMAMLANDI,
                    baslangic_zamani=datetime.now(UTC) - timedelta(hours=2),
                    zaman_limiti_saniye=60,
                    en_iyi_ceza=9999,
                    kural_anlik_goruntu={},
                ),
                CozumIsi(
                    surum_id=s2.surum_id,
                    durum=CozumIsiDurumu.TAMAMLANDI,
                    baslangic_zamani=datetime.now(UTC),
                    zaman_limiti_saniye=60,
                    en_iyi_ceza=8240,
                    kural_anlik_goruntu={},
                ),
            ]
        )
        # Kapsama acigi: iki hucre ama toplam UC kisi eksik.
        oturum.add_all(
            [
                KapsamaAcigi(
                    surum_id=s2.surum_id,
                    tarih=gun0,
                    vardiya_tipi_id=gece.vardiya_tipi_id,
                    nokta_id=nokta.nokta_id,
                    eksik_sayi=2,
                ),
                KapsamaAcigi(
                    surum_id=s2.surum_id,
                    tarih=gun1,
                    vardiya_tipi_id=gece.vardiya_tipi_id,
                    nokta_id=nokta.nokta_id,
                    eksik_sayi=1,
                ),
            ]
        )
        oturum.commit()
        return {
            "donem_id": donem.donem_id,
            "s1": s1.surum_id,
            "s2": s2.surum_id,
            "p1": p1.personel_id,
        }
    finally:
        oturum.rollback()
        oturum.close()


def test_surum_listesi_toplam_ceza_ve_kapsama_acigi_tasir(
    istemci: TestClient, senaryo: dict[str, int]
) -> None:
    """SDD 6.3.5 Surum Listesi: numara, durum, olusturma zamani, toplam ceza
    ve kapsama acigi sayisi."""
    yanit = istemci.get(f"/api/surum?donem_id={senaryo['donem_id']}")
    assert yanit.status_code == 200
    satirlar = {s["surum_id"]: s for s in yanit.json()}

    s2 = satirlar[senaryo["s2"]]
    # Iki cozum isi var; EN SONUNCUSUNUN cezasi gosterilir.
    assert s2["toplam_ceza"] == pytest.approx(8240.0)
    # Iki acik hucre ama toplam eksik KISI sayisi 3.
    assert s2["kapsama_acigi_sayisi"] == 3
    assert s2["surum_no"] == 2
    assert s2["durum"] == "taslak"
    assert s2["olusturma_zamani"]

    s1 = satirlar[senaryo["s1"]]
    # Hic cozulmemis surumde ceza None, acik 0 (eksik satir degil, sifir).
    assert s1["toplam_ceza"] is None
    assert s1["kapsama_acigi_sayisi"] == 0


def test_karsilastirma_farklari_uc_ture_ayirir_ve_sayar(
    istemci: TestClient, senaryo: dict[str, int]
) -> None:
    """SDD 6.3.5 Karsilastir; Charter bolum 5 altinci kriter: degisen atama
    sayisi raporlanir."""
    yanit = istemci.get(
        f"/api/surum/karsilastir?onceki_surum_id={senaryo['s1']}&yeni_surum_id={senaryo['s2']}"
    )
    assert yanit.status_code == 200
    govde = yanit.json()

    assert govde["degisen"] == 1
    assert govde["kaldirilan"] == 1
    assert govde["eklenen"] == 1
    assert govde["toplam_degisiklik"] == 3

    turler = {f["tarih"]: f["tur"] for f in govde["farklar"]}
    assert "2026-05-04" not in turler  # iki surumde de ayni -> fark yok
    assert turler["2026-05-05"] == "degisti"
    assert turler["2026-05-06"] == "kaldirildi"
    assert turler["2026-05-07"] == "eklendi"

    degisen = next(f for f in govde["farklar"] if f["tur"] == "degisti")
    assert degisen["onceki_vardiya_tipi_ad"].startswith("Gunduz")
    assert degisen["yeni_vardiya_tipi_ad"].startswith("Gece")
    assert degisen["personel_id"] == senaryo["p1"]

    kaldirilan = next(f for f in govde["farklar"] if f["tur"] == "kaldirildi")
    assert kaldirilan["yeni_vardiya_tipi_ad"] is None
    eklenen = next(f for f in govde["farklar"] if f["tur"] == "eklendi")
    assert eklenen["onceki_vardiya_tipi_ad"] is None


def test_ayni_surum_kendisiyle_karsilastirilinca_fark_cikmaz(
    istemci: TestClient, senaryo: dict[str, int]
) -> None:
    yanit = istemci.get(
        f"/api/surum/karsilastir?onceki_surum_id={senaryo['s2']}&yeni_surum_id={senaryo['s2']}"
    )
    assert yanit.status_code == 200
    assert yanit.json()["toplam_degisiklik"] == 0


def test_karsilastirma_bulunmayan_surumde_404(istemci: TestClient, senaryo: dict[str, int]) -> None:
    yanit = istemci.get(
        f"/api/surum/karsilastir?onceki_surum_id={senaryo['s1']}&yeni_surum_id=999999999"
    )
    assert yanit.status_code == 404


def test_farkli_donemlerin_surumleri_karsilastirilamaz(istemci: TestClient) -> None:
    """Farkli donemlerin atamalari farkli takvim gunlerine dustugu icin
    "degisen gun" tanimsizdir; sessizce anlamsiz bir fark listesi uretmek
    yerine 409 donulur."""
    oturum = OturumYerel()
    try:
        d1 = Donem(
            baslangic_tarihi=date(2026, 7, 6),
            bitis_tarihi=date(2026, 7, 12),
            tercih_son_tarihi=date(2026, 6, 29),
        )
        d2 = Donem(
            baslangic_tarihi=date(2026, 7, 13),
            bitis_tarihi=date(2026, 7, 19),
            tercih_son_tarihi=date(2026, 7, 6),
        )
        oturum.add_all([d1, d2])
        oturum.flush()
        s1 = CizelgeSurumu(donem_id=d1.donem_id, surum_no=1, durum=CizelgeSurumuDurumu.TASLAK)
        s2 = CizelgeSurumu(donem_id=d2.donem_id, surum_no=1, durum=CizelgeSurumuDurumu.TASLAK)
        oturum.add_all([s1, s2])
        oturum.commit()
        a, b = s1.surum_id, s2.surum_id
    finally:
        oturum.rollback()
        oturum.close()

    yanit = istemci.get(f"/api/surum/karsilastir?onceki_surum_id={a}&yeni_surum_id={b}")
    assert yanit.status_code == 409


# --- Arsivden taslak kopyalama (madde 8) -----------------------------------


def _atama_kumesi(istemci: TestClient, surum_id: int) -> set[tuple[int, str, int, int, bool, str]]:
    """Atamalari kimlikten bagimsiz, karsilastirilabilir bir kumeye cevirir."""
    return {
        (
            a["personel_id"],
            a["tarih"],
            a["vardiya_tipi_id"],
            a["nokta_id"],
            a["kilitli"],
            a["kaynak"],
        )
        for a in istemci.get(f"/api/surum/{surum_id}/atama").json()
    }


def test_arsivden_kopyalanan_taslak_kaynagi_gosterir(
    istemci: TestClient, senaryo: dict[str, int]
) -> None:
    yanit = istemci.post(f"/api/surum/{senaryo['s1']}/kopyala")
    assert yanit.status_code == 201
    yeni = yanit.json()

    assert yeni["durum"] == "taslak"
    assert yeni["onceki_surum_id"] == senaryo["s1"]
    assert yeni["donem_id"] == senaryo["donem_id"]
    assert yeni["surum_id"] != senaryo["s1"]
    # Donemde 1 ve 2 vardi; kopya siradaki numarayi alir.
    assert yeni["surum_no"] == 3


def test_kopyalanan_atamalar_kaynakla_birebir_ayni(
    istemci: TestClient, senaryo: dict[str, int]
) -> None:
    kaynak_atamalari = _atama_kumesi(istemci, senaryo["s1"])
    yeni_id = istemci.post(f"/api/surum/{senaryo['s1']}/kopyala").json()["surum_id"]

    kopya_atamalari = _atama_kumesi(istemci, yeni_id)
    assert len(kopya_atamalari) == len(kaynak_atamalari) == 4
    assert kopya_atamalari == kaynak_atamalari


def test_kopyalama_kaynak_surumu_degistirmez(istemci: TestClient, senaryo: dict[str, int]) -> None:
    """Arsivin degismezligi calisan panelindeki karsilastirma tabaninin ve
    Surumler ekranindaki karsilastirmanin dayanagi."""
    once_atamalar = _atama_kumesi(istemci, senaryo["s1"])
    once_durum = next(
        s
        for s in istemci.get(f"/api/surum?donem_id={senaryo['donem_id']}").json()
        if s["surum_id"] == senaryo["s1"]
    )

    istemci.post(f"/api/surum/{senaryo['s1']}/kopyala")

    sonra_durum = next(
        s
        for s in istemci.get(f"/api/surum?donem_id={senaryo['donem_id']}").json()
        if s["surum_id"] == senaryo["s1"]
    )
    assert sonra_durum["durum"] == once_durum["durum"] == "arsiv"
    assert sonra_durum["onceki_surum_id"] == once_durum["onceki_surum_id"]
    assert _atama_kumesi(istemci, senaryo["s1"]) == once_atamalar


def test_kopyaya_kapsama_acigi_tasinmaz(istemci: TestClient, senaryo: dict[str, int]) -> None:
    """Kapsama acigi bir COZUM calistirmasinin ciktisidir; henuz cozulmemis
    bir taslaga ait degildir."""
    yeni_id = istemci.post(f"/api/surum/{senaryo['s1']}/kopyala").json()["surum_id"]
    assert istemci.get(f"/api/surum/{yeni_id}/kapsama-acigi").json() == []


def test_ayni_donemde_acik_taslak_varken_de_kopyalanir(
    istemci: TestClient, senaryo: dict[str, int]
) -> None:
    """Coklu taslak sistemin olagan hali: her cozum baslatma zaten yeni bir
    taslak aciyor. Kopyalamayi engellemek tek basina tutarsiz bir istisna
    olurdu (TD-8 de bir sinir koymuyor)."""
    # senaryo'daki s2 zaten taslak durumda.
    ilk = istemci.post(f"/api/surum/{senaryo['s1']}/kopyala")
    ikinci = istemci.post(f"/api/surum/{senaryo['s1']}/kopyala")
    assert ilk.status_code == ikinci.status_code == 201
    assert ilk.json()["surum_id"] != ikinci.json()["surum_id"]
    assert ikinci.json()["surum_no"] == ilk.json()["surum_no"] + 1


def test_taslak_surum_kopyalanamaz(istemci: TestClient, senaryo: dict[str, int]) -> None:
    """Taslak zaten duzenlenebilir; kopyalamak amacsiz kopyalar biriktirir."""
    yanit = istemci.post(f"/api/surum/{senaryo['s2']}/kopyala")
    assert yanit.status_code == 409
    assert "taslak" in yanit.json()["detail"].lower()


def test_olmayan_surum_kopyalanamaz(istemci: TestClient) -> None:
    pg_yoksa_atla()
    assert istemci.post("/api/surum/999999/kopyala").status_code == 404
