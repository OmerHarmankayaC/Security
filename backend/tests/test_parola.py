"""Parola ozeti ve parola kurali (SRS FR-10.2; SDD 5.1b).

Veritabani gerektirmez - saf fonksiyon testleri.
"""

import pytest

from app.services.parola import (
    ASGARI_UZUNLUK,
    ParolaKuraliError,
    bosa_dogrula,
    dogrula,
    kurali_dogrula,
    ozetle,
)

_GECERLI = "cok-uzun-bir-parola"


def test_ozet_parolayi_icermez() -> None:
    """FR-10.2'nin can alici noktasi: ozet geri cevrilebilir olmamalidir.

    Tam tersini kanitlamak bir testin isi degil (Argon2id'nin isi); burada
    dogrulanan, parolanin ozetin icinde DUZ METIN olarak durmadigidir - bu
    hata, ozetleme yerine kodlama kullanildiginda gercekten yasanir.
    """
    ozet = ozetle(_GECERLI)
    assert _GECERLI not in ozet
    assert ozet.startswith("$argon2id$")


def test_ayni_parola_her_seferinde_farkli_ozet_verir() -> None:
    """Tuz ozetin icindedir: ayni parolanin iki hesabi ayni satiri uretmez,
    yani veritabanini goren biri 'bu ikisinin parolasi ayni' diyemez."""
    assert ozetle(_GECERLI) != ozetle(_GECERLI)


def test_dogrulama_dogru_parolayi_kabul_yanlisini_ret_eder() -> None:
    ozet = ozetle(_GECERLI)
    assert dogrula(ozet, _GECERLI)
    assert not dogrula(ozet, _GECERLI + "x")
    assert not dogrula(ozet, "")


def test_bozuk_ozet_hata_firlatmaz_false_doner() -> None:
    """Elle bozulmus ya da baska bicimde yazilmis bir ozet, girisi 500'e
    dusurmemeli; basarisiz giris gibi ele alinmali."""
    assert not dogrula("bu-bir-argon2-ozeti-degil", _GECERLI)


def test_kural_asgari_uzunlugu_zorlar() -> None:
    with pytest.raises(ParolaKuraliError):
        kurali_dogrula("a" * (ASGARI_UZUNLUK - 1))
    kurali_dogrula("a" * ASGARI_UZUNLUK)


def test_ozetleme_kurali_uygular_dogrulama_uygulamaz() -> None:
    """Kural yazarken uygulanir, okurken degil: kural sonradan
    sikilastirilirsa eskiden gecerli bir parolayla acilmis hesap giris
    yapamaz hale gelmemelidir."""
    with pytest.raises(ParolaKuraliError):
        ozetle("kisa")

    # Kurali by-pass ederek uretilmis (kural oncesi) bir ozet hala dogrulanir.
    from argon2 import PasswordHasher

    eski_ozet = PasswordHasher().hash("kisa")
    assert dogrula(eski_ozet, "kisa")


def test_bosa_dogrulama_hata_firlatmaz() -> None:
    """Kullanici bulunamadigi yolda cagrilir; patlarsa 500 ile 401 ayrimi
    yine kullanicinin var olup olmadigini ele verirdi (SDD 5.1b)."""
    bosa_dogrula()
