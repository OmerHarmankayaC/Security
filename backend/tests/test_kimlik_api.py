"""Giris, oturum ve parola degistirme (SRS FR-10.1 - FR-10.3, FR-10.7,
FR-10.8; SDD 5.1b).

Istemci `https://testserver` uzerinden konusur. Bu bilincli: cerez
uretimde Secure niteligi tasir ve duz http'de tarayici onu geri
gondermez - testler http kullansaydi, uretimde gecerli olan ayarin
DISINDA bir yolu dogrulamis olurdu.

Canli bir PostgreSQL gerektirir; baglanamiyorsa atlanir.
"""

import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Annotated

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.config import ayarlar
from app.db import OturumYerel
from app.guvenlik import giris_yapan
from app.main import app
from app.models.kimlik import Kullanici, OturumKaydi, Rol
from app.models.tanim import Personel
from app.services import parola as parola_araclari
from app.services.kimlik_servisi import GirisBasarisizError, KimlikServisi
from app.services.oturum_servisi import (
    CEREZ_ADI,
    OturumBaglami,
    OturumServisi,
    belirtec_ozeti,
)
from app.services.parola import ozetle
from tests.conftest import pg_yoksa_atla

PAROLA = "cok-uzun-bir-parola"
YENI_PAROLA = "bambaska-uzun-parola"


@pytest.fixture
def istemci() -> TestClient:
    pg_yoksa_atla()
    _temizle()
    return TestClient(app, base_url="https://testserver")


def _temizle() -> None:
    oturum = OturumYerel()
    try:
        oturum.execute(text("TRUNCATE oturum, kullanici CASCADE"))
        oturum.commit()
    finally:
        oturum.close()


def _kullanici_olustur(
    kullanici_adi: str,
    *,
    parola: str = PAROLA,
    rol: Rol = Rol.YONETICI,
    aktif: bool = True,
    parola_degistirmeli: bool = False,
    personel_id: int | None = None,
) -> int:
    oturum = OturumYerel()
    try:
        kullanici = Kullanici(
            kullanici_adi=kullanici_adi,
            parola_ozeti=ozetle(parola),
            rol=rol,
            aktif=aktif,
            parola_degistirmeli=parola_degistirmeli,
            personel_id=personel_id,
        )
        oturum.add(kullanici)
        oturum.commit()
        return kullanici.kullanici_id
    finally:
        oturum.close()


def _personel_olustur() -> int:
    oturum = OturumYerel()
    try:
        personel = Personel(
            ad_soyad="Kimlik API Personeli",
            sicil_no=f"KAPI-{uuid.uuid4().hex[:8]}",
            haftalik_hedef_saat=40,
            aktif_baslangic=date(2026, 1, 1),
        )
        oturum.add(personel)
        oturum.commit()
        return personel.personel_id
    finally:
        oturum.close()


def _giris(istemci: TestClient, kullanici_adi: str, parola: str = PAROLA):
    return istemci.post("/api/giris", json={"kullanici_adi": kullanici_adi, "parola": parola})


# --- Giris (FR-10.1, FR-10.3) -----------------------------------------------


def test_giris_cerez_yazar_ve_rolu_dondurur(istemci: TestClient) -> None:
    _kullanici_olustur("giris-mutlu", rol=Rol.YONETIM)

    yanit = _giris(istemci, "giris-mutlu")

    assert yanit.status_code == 200
    assert yanit.json()["rol"] == "yonetim"
    assert yanit.json()["parola_degistirmeli"] is False

    cerez = yanit.headers["set-cookie"]
    assert CEREZ_ADI in cerez
    # Uc nitelik de SDD 5.1b'de acikca sayilir.
    assert "HttpOnly" in cerez
    assert "Secure" in cerez
    assert "samesite=lax" in cerez.lower()


def test_belirtec_veritabaninda_duz_durmaz_yalniz_ozeti_durur(istemci: TestClient) -> None:
    """SDD 5.1b'nin gerekcesi: veritabani okunsa bile acik oturumlar ele
    gecirilemez."""
    _kullanici_olustur("giris-ozet")
    _giris(istemci, "giris-ozet")
    belirtec = istemci.cookies[CEREZ_ADI]

    oturum = OturumYerel()
    try:
        kayitlar = oturum.query(OturumKaydi).all()
        assert len(kayitlar) == 1
        assert kayitlar[0].oturum_id != belirtec
        assert kayitlar[0].oturum_id == belirtec_ozeti(belirtec)
    finally:
        oturum.close()


def test_yanit_kullanici_adini_kucuk_harfe_esler(istemci: TestClient) -> None:
    _kullanici_olustur("giris-kucuk")
    assert _giris(istemci, "  GIRIS-KUCUK ").status_code == 200


def test_giris_bilgisi_yanit_govdesinde_parola_veya_belirtec_tasimaz(
    istemci: TestClient,
) -> None:
    _kullanici_olustur("giris-sizinti")
    govde = _giris(istemci, "giris-sizinti").json()
    metin = str(govde)
    assert PAROLA not in metin
    assert "belirtec" not in govde
    assert "parola_ozeti" not in govde


# --- Varlik sizintisi (SDD 5.1b) --------------------------------------------


def test_yok_olan_kullanici_ile_yanlis_parola_ayni_yaniti_verir(istemci: TestClient) -> None:
    """Giris ekrani bir kullanici adi sayacina donusmemeli: iki yol AYNI
    durum kodunu ve AYNI metni dondurur."""
    _kullanici_olustur("giris-varolan")

    yok = _giris(istemci, "boyle-bir-kullanici-yok")
    yanlis = _giris(istemci, "giris-varolan", parola="yanlis-parola-ama-uzun")

    assert yok.status_code == yanlis.status_code == 401
    assert yok.json()["detail"] == yanlis.json()["detail"]
    assert yok.headers.get("set-cookie") is None


def test_kullanici_bulunamadiginda_da_ozet_dogrulamasi_yapilir(
    istemci: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sureyi esitleyen adim (SDD 5.1b: 'benzer sure').

    Sure olcmek yerine cagrinin YAPILDIGI dogrulanir: olcum makine yukune
    gore oynar ve testi kirilgan yapardi; kaybolmasi gereken sey ise bu
    cagrinin kendisidir.
    """
    cagrildi = False

    def _sayan() -> None:
        nonlocal cagrildi
        cagrildi = True
        parola_araclari.dogrula("bozuk", "yanlis")

    monkeypatch.setattr(parola_araclari, "bosa_dogrula", _sayan)
    _giris(istemci, "hic-var-olmayan-kullanici")
    assert cagrildi


# --- Gecici kilit (FR-10.8) -------------------------------------------------


def test_esik_alti_yanlis_denemeden_sonra_dogru_parola_calisir(istemci: TestClient) -> None:
    _kullanici_olustur("kilit-altinda")
    for _ in range(ayarlar.giris_kilit_esigi - 1):
        assert _giris(istemci, "kilit-altinda", parola="yanlis-parola-uzun").status_code == 401
    assert _giris(istemci, "kilit-altinda").status_code == 200


def test_esik_asilinca_dogru_parola_da_kabul_edilmez_ve_sure_bildirilir(
    istemci: TestClient,
) -> None:
    _kullanici_olustur("kilit-ustunde")
    for _ in range(ayarlar.giris_kilit_esigi):
        _giris(istemci, "kilit-ustunde", parola="yanlis-parola-uzun")

    yanit = _giris(istemci, "kilit-ustunde")
    assert yanit.status_code == 401
    # FR-10.8: kilit suresi bildirilir.
    assert "dakika" in yanit.json()["detail"]
    assert yanit.headers.get("set-cookie") is None


def test_kilitliyken_yanlis_parola_kilit_mesajini_gostermez(istemci: TestClient) -> None:
    """Kilit mesaji yalniz dogru parolayla gorulur; aksi halde FR-10.8'in
    bildirim gereksinimi, kullanici adi sayimina kapi acardi."""
    _kullanici_olustur("kilit-gizli")
    for _ in range(ayarlar.giris_kilit_esigi):
        _giris(istemci, "kilit-gizli", parola="yanlis-parola-uzun")

    kilitli = _giris(istemci, "kilit-gizli", parola="yine-yanlis-parola")
    yok = _giris(istemci, "hic-boyle-bir-kullanici-yok")
    assert kilitli.json()["detail"] == yok.json()["detail"]


def test_kilit_suresi_dolunca_giris_yeniden_acilir() -> None:
    """Zaman enjekte edilir; test beklemez."""
    pg_yoksa_atla()
    _temizle()
    _kullanici_olustur("kilit-suresi")

    oturum = OturumYerel()
    try:
        servis = KimlikServisi(oturum)
        simdi = datetime.now(UTC)
        for _ in range(ayarlar.giris_kilit_esigi):
            with pytest.raises(GirisBasarisizError):
                servis.giris("kilit-suresi", "yanlis-parola-uzun", simdi=simdi)

        sonra = simdi + timedelta(minutes=ayarlar.giris_kilit_dakika + 1)
        sonuc = servis.giris("kilit-suresi", PAROLA, simdi=sonra)
        assert sonuc.belirtec
    finally:
        oturum.rollback()
        oturum.close()


# --- Devre disi hesap (FR-10.5) ---------------------------------------------


def test_devre_disi_hesap_dogru_parolayla_da_giremez(istemci: TestClient) -> None:
    _kullanici_olustur("pasif-hesap", aktif=False)
    yanit = _giris(istemci, "pasif-hesap")
    assert yanit.status_code == 401
    assert yanit.headers.get("set-cookie") is None


# --- Oturum suresi (SDD 4.2.1) ----------------------------------------------


def test_hareketsizlik_ve_mutlak_sure_ayri_ayri_uygulanir() -> None:
    """Ikisi AYRI kurallardir: surekli istek gonderen bir oturum
    hareketsizlige takilmaz ama mutlak siniri gecince yine kapanir."""
    pg_yoksa_atla()
    _temizle()
    kullanici_id = _kullanici_olustur("sure-testi")

    oturum = OturumYerel()
    try:
        servis = OturumServisi(oturum)
        basla = datetime.now(UTC)
        belirtec = servis.olustur(kullanici_id, simdi=basla)
        oturum.flush()

        # (a) Hareketsizlik: son erisimden sonra sinir gecilirse duser.
        bos_bekleme = basla + timedelta(minutes=ayarlar.oturum_hareketsizlik_dakika + 1)
        assert servis.dogrula(belirtec, simdi=bos_bekleme) is None

        # (b) Mutlak: duzenli istekle hareketsizlik hic dolmasa bile duser.
        belirtec = servis.olustur(kullanici_id, simdi=basla)
        oturum.flush()
        an = basla
        adim = timedelta(minutes=ayarlar.oturum_hareketsizlik_dakika - 1)
        while an < basla + timedelta(hours=ayarlar.oturum_azami_saat) - adim:
            an += adim
            assert servis.dogrula(belirtec, simdi=an) is not None
        assert (
            servis.dogrula(belirtec, simdi=basla + timedelta(hours=ayarlar.oturum_azami_saat))
            is None
        )
    finally:
        oturum.rollback()
        oturum.close()


def test_suresi_dolan_oturum_kaydi_silinir() -> None:
    pg_yoksa_atla()
    _temizle()
    kullanici_id = _kullanici_olustur("sure-temizlik")

    oturum = OturumYerel()
    try:
        servis = OturumServisi(oturum)
        basla = datetime.now(UTC)
        belirtec = servis.olustur(kullanici_id, simdi=basla)
        oturum.flush()
        servis.dogrula(belirtec, simdi=basla + timedelta(hours=ayarlar.oturum_azami_saat + 1))
        oturum.flush()
        assert servis.kullanicinin_oturum_sayisi(kullanici_id) == 0
    finally:
        oturum.rollback()
        oturum.close()


def test_cerezsiz_ve_uydurma_cerezli_istek_401_alir(istemci: TestClient) -> None:
    assert istemci.get("/api/ben").status_code == 401
    istemci.cookies.set(CEREZ_ADI, "uydurma-belirtec", domain="testserver")
    assert istemci.get("/api/ben").status_code == 401


# --- Cikis (FR-10.3) --------------------------------------------------------


def test_cikis_oturumu_siler_elde_kalan_belirtec_ise_yaramaz(istemci: TestClient) -> None:
    """Yalniz cerezi silmek yetmezdi: belirtecin kopyasi elinde olan biri
    kullanmaya devam ederdi."""
    kullanici_id = _kullanici_olustur("cikis-testi")
    _giris(istemci, "cikis-testi")
    belirtec = istemci.cookies[CEREZ_ADI]
    assert istemci.get("/api/ben").status_code == 200

    assert istemci.post("/api/cikis").status_code == 204

    oturum = OturumYerel()
    try:
        assert OturumServisi(oturum).kullanicinin_oturum_sayisi(kullanici_id) == 0
    finally:
        oturum.close()

    istemci.cookies.set(CEREZ_ADI, belirtec, domain="testserver")
    assert istemci.get("/api/ben").status_code == 401


# --- Oturumlarin toplu iptali (SDD 4.2.1'in varlik nedeni) ------------------


def test_hesap_devre_disi_birakilinca_acik_oturum_gecersiz_olur(istemci: TestClient) -> None:
    kullanici_id = _kullanici_olustur("iptal-pasif")
    _giris(istemci, "iptal-pasif")
    assert istemci.get("/api/ben").status_code == 200

    oturum = OturumYerel()
    try:
        # Yonetim ekraninin yapacagi sey (adim 3): bayrak + oturum iptali.
        kullanici = oturum.get(Kullanici, kullanici_id)
        assert kullanici is not None
        kullanici.aktif = False
        OturumServisi(oturum).kullanicinin_oturumlarini_sil(kullanici_id)
        oturum.commit()
    finally:
        oturum.close()

    assert istemci.get("/api/ben").status_code == 401


def test_pasif_hesabin_oturumu_iptal_edilmese_bile_gecmez(istemci: TestClient) -> None:
    """Ikinci savunma hatti: `aktif` bayragi tek basina da yeter, oturum
    iptali atlanmis olsa bile acik oturum gecmez."""
    kullanici_id = _kullanici_olustur("iptal-bayrak")
    _giris(istemci, "iptal-bayrak")

    oturum = OturumYerel()
    try:
        kullanici = oturum.get(Kullanici, kullanici_id)
        assert kullanici is not None
        kullanici.aktif = False
        oturum.commit()
    finally:
        oturum.close()

    assert istemci.get("/api/ben").status_code == 401


# --- Parola degistirme (FR-10.7) --------------------------------------------


def test_parola_degistirme_borcu_diger_uc_noktalari_kapatir(istemci: TestClient) -> None:
    """FR-10.7. Arayuzun kullaniciyi parola ekranina goturmesi yetkilendirme
    degildir; istek dogrudan gonderildiginde de reddedilmelidir.

    Kapinin kendisi (`giris_yapan`) burada olculur; adim 3 onu butun gercek
    uc noktalara baglar.
    """
    _kullanici_olustur("borclu", parola_degistirmeli=True)
    _giris(istemci, "borclu")

    kapili = FastAPI()

    @kapili.get("/deneme")
    def _deneme(_: Annotated[OturumBaglami, Depends(giris_yapan)]) -> dict[str, bool]:
        return {"acildi": True}

    kapili_istemci = TestClient(kapili, base_url="https://testserver")
    cerez = {"Cookie": f"{CEREZ_ADI}={istemci.cookies[CEREZ_ADI]}"}
    assert kapili_istemci.get("/deneme", headers=cerez).status_code == 403

    # Kim oldugunu sormak ve cikmak acik kalir: borcunu odemesinin yolu budur.
    assert istemci.get("/api/ben").status_code == 200
    assert istemci.get("/api/ben").json()["parola_degistirmeli"] is True


def test_parola_degistirme_borcu_kapatir_ve_yeni_parola_gecerli_olur(
    istemci: TestClient,
) -> None:
    _kullanici_olustur("borclu-oder", parola_degistirmeli=True)
    _giris(istemci, "borclu-oder")

    yanit = istemci.post(
        "/api/parola-degistir",
        json={"mevcut_parola": PAROLA, "yeni_parola": YENI_PAROLA},
    )
    assert yanit.status_code == 200
    assert yanit.json()["parola_degistirmeli"] is False

    istemci.post("/api/cikis")
    assert _giris(istemci, "borclu-oder", parola=PAROLA).status_code == 401
    assert _giris(istemci, "borclu-oder", parola=YENI_PAROLA).status_code == 200


def test_parola_degisince_diger_oturumlar_kapanir_cagiran_ayakta_kalir(
    istemci: TestClient,
) -> None:
    """Parola degisikligi, calinmis bir belirtecin iptal edilebilecegi tek
    andir; cagiranin kendi oturumu yerine yenisiyle degistirilir."""
    _kullanici_olustur("cok-oturum")
    _giris(istemci, "cok-oturum")
    ilk_belirtec = istemci.cookies[CEREZ_ADI]

    ikinci = TestClient(app, base_url="https://testserver")
    _giris(ikinci, "cok-oturum")
    assert ikinci.get("/api/ben").status_code == 200

    assert (
        istemci.post(
            "/api/parola-degistir",
            json={"mevcut_parola": PAROLA, "yeni_parola": YENI_PAROLA},
        ).status_code
        == 200
    )

    # Diger oturum dustu, cagiranin cerezi tazelendi ve calismaya devam ediyor.
    assert ikinci.get("/api/ben").status_code == 401
    assert istemci.cookies[CEREZ_ADI] != ilk_belirtec
    assert istemci.get("/api/ben").status_code == 200


def test_parola_degistirme_mevcut_parolayi_dogrular(istemci: TestClient) -> None:
    _kullanici_olustur("parola-yanlis")
    _giris(istemci, "parola-yanlis")
    yanit = istemci.post(
        "/api/parola-degistir",
        json={"mevcut_parola": "bu-parola-yanlis", "yeni_parola": YENI_PAROLA},
    )
    assert yanit.status_code == 400


def test_parola_degistirme_kisa_parolayi_ve_ayni_parolayi_reddeder(istemci: TestClient) -> None:
    _kullanici_olustur("parola-kural")
    _giris(istemci, "parola-kural")

    kisa = istemci.post(
        "/api/parola-degistir", json={"mevcut_parola": PAROLA, "yeni_parola": "kisa"}
    )
    assert kisa.status_code == 400

    ayni = istemci.post(
        "/api/parola-degistir", json={"mevcut_parola": PAROLA, "yeni_parola": PAROLA}
    )
    assert ayni.status_code == 400


# --- /api/ben ---------------------------------------------------------------


def test_ben_calisan_hesabinda_personel_bilgisini_tasir(istemci: TestClient) -> None:
    personel_id = _personel_olustur()
    _kullanici_olustur("ben-calisan", rol=Rol.CALISAN, personel_id=personel_id)
    _giris(istemci, "ben-calisan")

    govde = istemci.get("/api/ben").json()
    assert govde["rol"] == "calisan"
    assert govde["personel_id"] == personel_id
    assert govde["ad_soyad"] == "Kimlik API Personeli"
