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
from app.models.tanim import GorevNoktasi, Personel
from tests.conftest import pg_yoksa_atla, senaryo_verisini_temizle, yetkili_istemci

# Blok BASLANGIC SAATLERI; sure sekiz saat (blok katalogu kalkti, SRS TD-13).
_GUNDUZ, _GECE = 8, 0


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
        senaryo_verisini_temizle(oturum)

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

        def at(surum_id: int, personel_id: int, tarih: date, baslangic: int) -> Atama:
            """`baslangic` blogun BASLANGIC SAATI; sure sekiz saat."""
            bas = datetime.combine(tarih, time(baslangic))
            return Atama(
                surum_id=surum_id,
                personel_id=personel_id,
                baslangic_zamani=bas,
                bitis_zamani=bas + timedelta(hours=8),
                nokta_id=nokta.nokta_id,
                kaynak=AtamaKaynagi.COZUCU,
            )

        oturum.add_all(
            [
                at(s1.surum_id, p1.personel_id, gun0, _GUNDUZ),
                at(s1.surum_id, p1.personel_id, gun1, _GUNDUZ),
                at(s1.surum_id, p1.personel_id, gun2, _GUNDUZ),
                at(s1.surum_id, p2.personel_id, gun0, _GECE),
                at(s2.surum_id, p1.personel_id, gun0, _GUNDUZ),
                at(s2.surum_id, p1.personel_id, gun1, _GECE),
                at(s2.surum_id, p1.personel_id, gun3, _GUNDUZ),
                at(s2.surum_id, p2.personel_id, gun0, _GECE),
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
                    baslangic_zamani=datetime.combine(gun0, time(8, 0)),
                    bitis_zamani=datetime.combine(gun0, time(16, 0)),
                    nokta_id=nokta.nokta_id,
                    eksik_sayi=2,
                ),
                KapsamaAcigi(
                    surum_id=s2.surum_id,
                    baslangic_zamani=datetime.combine(gun1, time(8, 0)),
                    bitis_zamani=datetime.combine(gun1, time(16, 0)),
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


def test_surum_listesi_atama_sayisi_tasir(istemci: TestClient, senaryo: dict[str, int]) -> None:
    """Gorev 6: Ozet ekrani "olculebilir surum"u artik "taslak degil" degil
    "atamasi var" olcutuyle secer (bos taslak bunu gecersiz kildi) - olcut
    surum listesinin `atama_sayisi` alanina dayanir.
    """
    yanit = istemci.get(f"/api/surum?donem_id={senaryo['donem_id']}")
    assert yanit.status_code == 200
    satirlar = {s["surum_id"]: s for s in yanit.json()}

    # senaryo fikstüründeki her iki surumde de DORT atama var (bkz. `at(...)`
    # cagrilari): s1 icin gun0/gun1/gun2 P1 + gun0 P2, s2 icin gun0/gun1/gun3
    # P1 + gun0 P2.
    assert satirlar[senaryo["s1"]]["atama_sayisi"] == 4
    assert satirlar[senaryo["s2"]]["atama_sayisi"] == 4


def test_surum_listesi_atamasiz_taslakta_atama_sayisi_sifir(istemci: TestClient) -> None:
    """Elle cizilen bos taslagin (Gorev 1) hic atamasi yoktur; eski olcut
    ("taslak degil") bu surumu de "olculebilir" sayardi, yeni alan bunu
    ayirt eder.
    """
    oturum = OturumYerel()
    try:
        senaryo_verisini_temizle(oturum)
        donem_id = _bos_donem_olustur(oturum)
    finally:
        oturum.close()

    olustur = istemci.post("/api/surum", json={"donem_id": donem_id})
    assert olustur.status_code == 201
    surum_id = olustur.json()["surum_id"]

    yanit = istemci.get(f"/api/surum?donem_id={donem_id}")
    assert yanit.status_code == 200
    satirlar = {s["surum_id"]: s for s in yanit.json()}
    assert satirlar[surum_id]["atama_sayisi"] == 0


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
    # Karsilastirma artik blok ADINI degil ZAMAN ARALIGINI gosterir
    # (blok adi diye bir sey kalmadi, SRS TD-13).
    assert degisen["onceki_blok"] == "08.00–16.00"
    assert degisen["yeni_blok"] == "00.00–08.00"
    assert degisen["personel_id"] == senaryo["p1"]

    kaldirilan = next(f for f in govde["farklar"] if f["tur"] == "kaldirildi")
    assert kaldirilan["yeni_blok"] is None
    eklenen = next(f for f in govde["farklar"] if f["tur"] == "eklendi")
    assert eklenen["onceki_blok"] is None


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
            a["baslangic_zamani"],
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


# --- Bos taslak: dogrudan donemden (Tur 13, Gorev 2) ------------------------
#
# POST /api/surum artik iki turlu istegi kabul eder: MEVCUT BIR SURUMDEN
# (onceki_surum_id, eski davranis) ya da DOGRUDAN DONEMDEN (donem_id, yeni).
# Depo tarafi (`CizelgeSurumuDeposu.taslak_ac`) Gorev 1'de yazildi; burada
# yalniz yonlendiricinin dogru dali sectigi ve semanin "tam olarak biri"
# kuralini uyguladigi sinanir.


def _bos_donem_olustur(oturum: OturumYerel) -> int:
    """Uzerinde hic surum olmayan yeni bir donem acar."""
    on_ek = _benzersiz("bos-donem")
    donem = Donem(
        baslangic_tarihi=date(2026, 11, 2),  # Pazartesi
        bitis_tarihi=date(2026, 11, 8),
        tercih_son_tarihi=date(2026, 10, 26),
    )
    oturum.add(donem)
    oturum.commit()
    _ = on_ek  # benzersizlik gerekmiyor, temizlik butun donemleri siler
    return donem.donem_id


def test_donem_id_ile_taslak_acilir_ve_onceki_surum_id_bostur(istemci: TestClient) -> None:
    oturum = OturumYerel()
    try:
        senaryo_verisini_temizle(oturum)
        donem_id = _bos_donem_olustur(oturum)
    finally:
        oturum.close()

    yanit = istemci.post("/api/surum", json={"donem_id": donem_id})
    assert yanit.status_code == 201
    govde = yanit.json()
    assert govde["donem_id"] == donem_id
    assert govde["surum_no"] == 1
    assert govde["durum"] == "taslak"
    assert govde["onceki_surum_id"] is None


def test_donem_id_ile_mevcut_surume_baglanir(istemci: TestClient, senaryo: dict[str, int]) -> None:
    """Donemde surum varsa yenisi EN SONUNCUYA baglanir (senaryo'da s2,
    surum_no=2)."""
    yanit = istemci.post("/api/surum", json={"donem_id": senaryo["donem_id"]})
    assert yanit.status_code == 201
    govde = yanit.json()
    assert govde["surum_no"] == 3
    assert govde["onceki_surum_id"] == senaryo["s2"]


def test_olmayan_donemle_donem_id_404(istemci: TestClient) -> None:
    yanit = istemci.post("/api/surum", json={"donem_id": 999999999})
    assert yanit.status_code == 404


def test_iki_alan_birden_verilince_422(istemci: TestClient, senaryo: dict[str, int]) -> None:
    yanit = istemci.post(
        "/api/surum", json={"donem_id": senaryo["donem_id"], "onceki_surum_id": senaryo["s1"]}
    )
    assert yanit.status_code == 422


def test_hicbiri_verilmeyince_422(istemci: TestClient) -> None:
    assert istemci.post("/api/surum", json={}).status_code == 422


def test_onceki_surum_id_ile_eski_davranis_degismedi(
    istemci: TestClient, senaryo: dict[str, int]
) -> None:
    """Regresyon: `onceki_surum_id` dali Gorev 2'den once nasil calisiyorsa
    oyle calismaya devam eder."""
    yanit = istemci.post("/api/surum", json={"onceki_surum_id": senaryo["s1"]})
    assert yanit.status_code == 201
    govde = yanit.json()
    assert govde["onceki_surum_id"] == senaryo["s1"]
    assert govde["donem_id"] == senaryo["donem_id"]
    assert govde["durum"] == "taslak"

    yanit_404 = istemci.post("/api/surum", json={"onceki_surum_id": 999999999})
    assert yanit_404.status_code == 404


# --- Duzenleme damgasi (SRS TD-16, SDD 5.5.1) -------------------------------
#
# Damga SOZLESMENIN parcasidir: cizelge ekrani duzenlemeye baslarken onu
# surum listesinden okur ve kaydederken geri gonderir. Sema onu tasimadigi
# surece istemcinin elinde damga hic olusmaz ve "Kaydet" SESSIZCE hicbir sey
# yapmaz - istek gitmez, hata cikmaz. Bu yuzden sinanan sey fikstur degil
# YANITIN KENDISI.


def test_surum_listesi_her_satirda_damga_tasir(
    istemci: TestClient, senaryo: dict[str, int]
) -> None:
    yanit = istemci.get(f"/api/surum?donem_id={senaryo['donem_id']}")
    assert yanit.status_code == 200
    satirlar = yanit.json()
    assert satirlar
    for satir in satirlar:
        assert isinstance(satir.get("damga"), str)
        assert satir["damga"]


def test_taslak_turetme_yaniti_damga_tasir(istemci: TestClient, senaryo: dict[str, int]) -> None:
    yanit = istemci.post("/api/surum", json={"onceki_surum_id": senaryo["s1"]})
    assert yanit.status_code == 201
    assert yanit.json()["damga"]


def test_donemden_acilan_bos_taslagin_yaniti_damga_tasir(istemci: TestClient) -> None:
    """Elle cizilecek bos taslak (Gorev 1): damgasiz donerse ekran acilir ama
    Kaydet hicbir sey yapmaz."""
    oturum = OturumYerel()
    try:
        senaryo_verisini_temizle(oturum)
        donem_id = _bos_donem_olustur(oturum)
    finally:
        oturum.close()

    yanit = istemci.post("/api/surum", json={"donem_id": donem_id})
    assert yanit.status_code == 201
    yeni_damga = yanit.json()["damga"]
    assert yeni_damga

    # Listeden okunan damga ile olusturma yanitindaki damga AYNI olmali:
    # ekran ikisini birbirinin yerine kullaniyor.
    liste = istemci.get(f"/api/surum?donem_id={donem_id}")
    assert liste.status_code == 200
    satir = next(s for s in liste.json() if s["surum_id"] == yanit.json()["surum_id"])
    assert satir["damga"] == yeni_damga
