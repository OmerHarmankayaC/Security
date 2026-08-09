"""Testler arasi paylasilan yardimcilar: canli PostgreSQL gerektiren testler icin
atlama ve cozum iscisinin senkron calistirilmasi."""

import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.config import ayarlar
from app.db import OturumYerel, engine
from app.guvenlik import oturum_baglami
from app.main import app
from app.models.kimlik import Kullanici, Rol
from app.models.sonuc import CozumIsiDurumu
from app.repositories.sonuc import CozumIsiDeposu
from app.services.oturum_servisi import OturumBaglami
from app.services.parola import ozetle

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.cozum_iscisi import siradaki_isi_isle  # noqa: E402

SONUCLANMIS_DURUMLAR = (
    CozumIsiDurumu.TAMAMLANDI,
    CozumIsiDurumu.UYARILI,
    CozumIsiDurumu.BASARISIZ,
    CozumIsiDurumu.IPTAL,
)


def pg_yoksa_atla() -> None:
    """Yerel PostgreSQL'e baglanilamiyorsa testi atlar (bkz. README "Kurulum")."""
    try:
        with engine.connect():
            pass
    except OperationalError:
        pytest.skip("Yerel PostgreSQL sunucusuna baglanilamadi")


def isi_calistir_ve_bekle(is_id: int, *, azami_adim: int = 5) -> CozumIsiDurumu:
    """Cozum iscisinin TEK ADIMINI senkron cagirir; hedef is sonuclanana
    kadar kuyruktan is isler ve isin son durumunu dondurur.

    `CozumServisi.baslat` artik surec ACMAZ (SDD 3.4.4: cozum ayri bir
    servistir), o yuzden testler isciyi kendileri surer. Surec acilmadigi
    icin davranis belirlenimlidir: yoklama, zaman asimi ve yaris yoktur.

    azami_adim, birden fazla is kuyruga alinmis testler icindir (hedef is
    kuyrukta ikinci sirada olabilir); sonsuz donguye karsi da sinirdir.
    """
    for _ in range(azami_adim):
        durum = _durumu_oku(is_id)
        if durum in SONUCLANMIS_DURUMLAR:
            return durum
        oturum = OturumYerel()
        try:
            if siradaki_isi_isle(oturum) is None:
                break  # kuyruk bos; hedef is sonuclanmamissa asagida hata verilir
        finally:
            oturum.close()

    durum = _durumu_oku(is_id)
    if durum not in SONUCLANMIS_DURUMLAR:
        pytest.fail(f"Cozum isi {is_id} {azami_adim} isci adiminda sonuclanmadi (durum: {durum})")
    return durum


def _durumu_oku(is_id: int) -> CozumIsiDurumu | None:
    oturum = OturumYerel()
    try:
        is_kaydi = CozumIsiDeposu(oturum).getir(is_id)
        return is_kaydi.durum if is_kaydi is not None else None
    finally:
        oturum.close()


# --- Kimlik dogrulama (SRS 5.10) --------------------------------------------
#
# Uc noktalarin tamami artik bir oturum arkasinda (FR-10.4) ve var olan API
# testleri kendi hesaplarini kurmaz. Iki yardimci var, ikisi de kapiyi ASMAZ -
# kapidan GECER - ama farkli yollardan:
#
#   `oturumlu_istemci`  gercek hesap acar ve gercekten giris yapar. Kimlik
#                       dogrulamanin KENDISI olculdugunde bu kullanilir.
#   `yetkili_istemci`   `oturum_baglami` bagimliligini ezer; rol kapilari,
#                       parola borcu kapisi ve FR-9.1'in personel secimi
#                       yine gercek koddan gecer, yalniz oturumun
#                       cozulmesi atlanir.
#
# Ikincisinin nedeni somut: senaryo kuran testler `TRUNCATE personel CASCADE`
# calistirir ve bu, `kullanici`yi de (yabanci anahtar) siler - yani veri
# temizligi acik oturumu dusurur. Konusu cizelge olan bir testin kimlik
# tablolarinin silinme sirasina bagimli olmasi, testi olctugu seyden baska
# bir sebeple kirilgan yapardi.


@pytest.fixture(autouse=True)
def _cerez_uretim_ayariyla_olculsun():  # noqa: ANN202 - pytest fixture
    """Testler cerezi HER ZAMAN uretim ayariyla (Secure) olcer.

    Yerel `.env` bu ayari false yapar - gelistirme http://localhost
    uzerinden yurur ve tarayici Secure bir cerezi oraya geri gondermez.
    Testlerin o yerel ayara tabi olmasi, uretimde gecerli olan yolun HIC
    olculmemesi demekti; ayari kapatan tek test bunu kendisi yapar.
    """
    onceki = ayarlar.oturum_cerezi_secure
    ayarlar.oturum_cerezi_secure = True
    yield
    ayarlar.oturum_cerezi_secure = onceki


@pytest.fixture(autouse=True)
def _bagimlilik_ezmelerini_temizle():  # noqa: ANN202 - pytest fixture
    """Ezmeler testler arasinda SIZMAZ.

    Autouse ve conftest duzeyinde: unutulabilecek bir temizlik degil.
    Sizsaydi, kimlik dogrulamayi olcen testler ezilmis bir kapiyla
    calisip yesil goruntu verirdi - yani tam da guvenilmesi gereken
    testler guvenilmez olurdu.
    """
    yield
    app.dependency_overrides.clear()


def yetkili_istemci(rol: Rol = Rol.YONETIM, *, personel_id: int | None = None) -> TestClient:
    """Verilen rolde giris yapmis sayilan istemci (oturum cozumu ezilir).

    Kullanici nesnesi veritabanina YAZILMAZ; kapilarin okudugu alanlari
    (rol, personel_id, parola_degistirmeli, aktif) tasiyan gecici bir
    nesnedir. Boylece hicbir TRUNCATE bu istemciyi dusuremez.
    """
    kullanici = Kullanici(
        kullanici_id=-1,
        kullanici_adi="test-yetkili",
        parola_ozeti="",
        rol=rol,
        personel_id=personel_id,
        parola_degistirmeli=False,
        aktif=True,
    )
    baglam = OturumBaglami(kullanici=kullanici, oturum_id="test-oturumu")
    app.dependency_overrides[oturum_baglami] = lambda: baglam
    return TestClient(app, base_url="https://testserver")


def _kimlik_tablolarini_temizle(oturum: Session) -> None:
    oturum.execute(text("TRUNCATE oturum, kullanici CASCADE"))
    oturum.commit()


def oturumlu_istemci(rol: Rol = Rol.YONETIM, *, personel_id: int | None = None) -> TestClient:
    """Verilen rolde bir hesap acip giris yapmis bir istemci dondurur.

    Istemci `https://testserver` konusur: oturum cerezi uretimde Secure
    niteligi tasir ve duz http'de tarayici onu geri gondermez.
    """
    kullanici_adi = f"test-{rol.value}-{uuid.uuid4().hex[:8]}"
    parola = "test-icin-uzun-parola"

    oturum = OturumYerel()
    try:
        _kimlik_tablolarini_temizle(oturum)
        oturum.add(
            Kullanici(
                kullanici_adi=kullanici_adi,
                parola_ozeti=ozetle(parola),
                rol=rol,
                personel_id=personel_id,
            )
        )
        oturum.commit()
    finally:
        oturum.close()

    istemci = TestClient(app, base_url="https://testserver")
    yanit = istemci.post("/api/giris", json={"kullanici_adi": kullanici_adi, "parola": parola})
    assert yanit.status_code == 200, yanit.text
    return istemci
