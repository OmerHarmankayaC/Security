"""Test takiminin veritabani kapisi (Urun Backlog'u B-20).

BU DOSYA `tests/` ICINDE DEGIL, DEPO KOKUNDE. Nedeni sira: pytest, kok
dizindeki conftest'i `tests/conftest.py`den ve dolayisiyla `app.db`den ONCE
okur. Baglanti adresi ancak burada, motor kurulmadan once degistirilebilir.

NEDEN AYRI BIR VERITABANI. Testler geliştirme veritabaninda kosuyordu ve
ayni kokten uc ayri belirti cikti (B-20):

  - Cozum iscisi arka planda calisirken test kuyrugundan is kapiyor; testin
    bekledigi is bir baska surecte calisiyor ve test zaman asimina dusuyor.
  - Test takimi kullanici hesaplarini siliyor. `kullanici.personel_id`
    personel tablosuna bagli oldugu icin temizlik hesaplari da goturuyor;
    test kosumundan sonra sisteme girilemez hale geliyor.
  - Kabul olcumu ile testler birbirinin verisini boziyor.

KILIT ACIK KONUSUR. Adres bir test veritabanini gostermiyorsa takim
CALISMAZ - varsayilana dusup gelistirme verisini sessizce temizlemek, tam
olarak kacinilmak istenen sey. Bu, `VERI_TEMIZLIGINE_IZIN` kilidinin
YERINE gecmez; onun yaninda duran ikinci bir kapidir. Birincisi "yikici
islem yapilabilir mi", ikincisi "hangi veritabaninda".
"""

import os

import pytest
from sqlalchemy.engine import make_url

# app.config, `.env` dosyasini okur ve `app.db`yi import ETMEZ; motor bu
# yuzden asagidaki atamadan sonra kurulur.
from app.config import ayarlar

_ORTAM_ANAHTARI = "TEST_VERITABANI_URL"

_KURULUM_ADIMLARI = f"""
Test takimi AYRI bir veritabani ister (Urun Backlog'u B-20).

  1. Veritabanini olusturun:
       createdb vardiya_test
     (Docker ile: docker exec -it <container> createdb -U vardiya vardiya_test)

  2. Semayi gocle kurun:
       cd backend
       VERITABANI_URL=<test-adresi> .venv/bin/alembic upgrade head

  3. Adresi backend/.env dosyasina yazin:
       {_ORTAM_ANAHTARI}=postgresql+psycopg://vardiya:<PAROLA>@localhost:5432/vardiya_test

Veritabani adi 'test' gecmelidir; kilit bunu arar.
""".strip()


def _test_veritabanini_zorunlu_kil() -> None:
    adres = os.environ.get(_ORTAM_ANAHTARI) or ayarlar.test_veritabani_url
    if not adres:
        raise pytest.UsageError(
            f"{_ORTAM_ANAHTARI} tanimli degil; testler gelistirme veritabaninda "
            f"KOSTURULMAZ.\n\n{_KURULUM_ADIMLARI}"
        )

    ad = make_url(adres).database
    if not ad or "test" not in ad.lower():
        # Ad kontrolu kaba ama amaci dar: yanlislikla gelistirme adresinin
        # yapistirilmasini yakalamak. Ikisi de ayni sunucuda, ayni kullanici
        # adiyla duruyor; ayirt eden tek sey veritabani adi.
        raise pytest.UsageError(
            f"{_ORTAM_ANAHTARI} bir TEST veritabanini gostermiyor "
            f"(veritabani adi: {ad!r}).\n\n{_KURULUM_ADIMLARI}"
        )

    # Motor bu degerden kurulacak. Ortam degiskeni de yazilir: testlerin
    # actigi alt surecler (ve alembic) ayni adresi gormeli.
    ayarlar.veritabani_url = adres
    os.environ["VERITABANI_URL"] = adres

    _baglantiyi_dogrula(adres)


def _baglantiyi_dogrula(adres: str) -> None:
    """Yapilandirilmis test veritabanina baglanilamazsa takim DURUR.

    Atlamak degil durmak: adres acikca yapilandirildigi halde
    baglanilamiyorsa bu bir kurulum hatasidir. Sessizce atlamak, uc yuzden
    fazla testin "gecti" gibi gorunmesine ve kimsenin fark etmemesine yol
    acardi.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.exc import OperationalError

    motor = create_engine(adres)
    try:
        with motor.connect():
            pass
    except OperationalError as hata:
        raise pytest.UsageError(
            f"Test veritabanina baglanilamadi ({make_url(adres).database!r}): "
            f"{hata.orig}\n\n{_KURULUM_ADIMLARI}"
        ) from hata
    finally:
        motor.dispose()


_test_veritabanini_zorunlu_kil()
