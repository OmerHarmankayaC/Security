"""Testler arasi paylasilan yardimcilar: canli PostgreSQL gerektiren testler icin
atlama ve cozum iscisinin senkron calistirilmasi."""

import sys
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
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
from app.veri_temizligi import HesapKapsami, hesaplari_temizle, veriyi_temizle

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.cozum_iscisi import siradaki_isi_isle  # noqa: E402

# Iscinin bir daha DOKUNMAYACAGI durumlar. `durduruldu` terminal degildir -
# is orada kullanici kararini bekler (SDD 5.4.1) - ama isci acisindan
# bitmistir; testin beklemesi gereken nokta da odur.
SONUCLANMIS_DURUMLAR = (
    CozumIsiDurumu.DURDURULDU,
    CozumIsiDurumu.TAMAMLANDI,
    CozumIsiDurumu.UYARILI,
    CozumIsiDurumu.BASARISIZ,
    CozumIsiDurumu.IPTAL,
)


def pg_yoksa_atla() -> None:
    """Yerel PostgreSQL'e baglanilamiyorsa testi atlar (bkz. README "Kurulum").

    ASIL KAPI ARTIK BURASI DEGIL. Depo kokundeki `conftest.py`, test
    veritabaninin yapilandirildigini ve ona baglanilabildigini takim
    baslamadan dogrular ve saglanmiyorsa yuksek sesle durur (B-20). Buradaki
    kontrol o kapidan sonra hicbir zaman tetiklenmez; testin niyetini
    imzasinda tutmak icin birakildi.
    """
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
# Ikincisinin nedeni somut: senaryo kuran testler `senaryo_verisini_temizle`
# cagirir ve o da hesap tablolarini HEPSI kapsamiyla bosaltir - yani veri
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
    hesaplari_temizle(oturum, kapsam=HesapKapsami.HEPSI)
    oturum.commit()


def senaryo_verisini_temizle(oturum: Session) -> None:
    """Senaryo kuran testlerin ortak temizligi (app/veri_temizligi.py).

    Eskiden her test kendi `TRUNCATE ... CASCADE` dizesini tasiyordu.
    `CASCADE`, silinecekler listesini PostgreSQL'e yazdirir: `kullanici`
    tablosu listede gorunmedigi halde, `personel`e yabanci anahtarla
    baktigi icin BUTUNUYLE bosaliyordu - personele hic bagli olmayan
    yonetim hesaplari dahil. Liste artik tek bir yerde ve ACIK; hesaplarin
    silinmesi de burada gorunur bir SECIM (`HesapKapsami.HEPSI`), yabanci
    anahtarin yan etkisi degil.

    Testlerde kapsam HEPSI'dir ve olmasi gereken de budur: fikstürlerin
    actigi hesaplar testler arasinda sizmamalidir.
    """
    veriyi_temizle(oturum, hesaplar=HesapKapsami.HEPSI)
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


@contextmanager
def gecici_vardiya_tipi(istemci: TestClient, govde: dict[str, object]) -> Iterator[dict]:
    """Bir calisma blogu acar ve test bitince katalogdan DUSURUR.

    Test veritabani kosumlar arasinda sifirlanmiyor; blok katalogu ise artik
    ayni (baslangic_saati, sure_saat) ikilisini iki kez kabul etmiyor
    (SRS FR-1.3, Tur 3 Is 6). Biriken bloklar bu yuzden yalnizca cop degil,
    sonraki kosumun HATASI: onceki kosumun biraktigi blok, ayni saati
    isteyen testi 409'a dusurur. Silme "kullanimdaysa pasiflestir"
    yoludur, pasif blok da benzersizlik sayiminda yer almaz.
    """
    yanit = istemci.post("/api/vardiya-tipi", json=govde)
    assert yanit.status_code == 201, yanit.text
    kayit = yanit.json()
    try:
        yield kayit
    finally:
        istemci.delete(f"/api/vardiya-tipi/{kayit['vardiya_tipi_id']}")


def bos_vardiya_blogu(istemci: TestClient, *, sure_saat: int = 8) -> dict[str, str]:
    """Katalogda henuz kullanilmayan bir calisma blogu dondurur.

    Saatleri testin konusu OLMAYAN yerler icindir: test 08.00'i degil
    "herhangi bir blogu" istiyorsa, komsularindan bagimsiz kalsin.
    """
    dolu = {
        (v["baslangic_saati"], float(v["sure_saat"]))
        for v in istemci.get("/api/vardiya-tipi").json()
        if v["aktif"]
    }
    for saat in range(24):
        baslangic = f"{saat:02d}:00:00"
        if (baslangic, float(sure_saat)) not in dolu:
            return {
                "baslangic_saati": baslangic,
                "bitis_saati": f"{(saat + sure_saat) % 24:02d}:00:00",
            }
    raise AssertionError(f"{sure_saat} saatlik butun baslangic saatleri katalogda dolu")
