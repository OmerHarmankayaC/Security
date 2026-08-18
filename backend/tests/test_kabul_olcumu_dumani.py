"""Kabul olcumu betigi KIRIK MI (Backlog B-25).

`scripts/kabul_olcumu.py` IKI TUR boyunca sessizce kirik kaldi. Iki ayri
imza degisikligi onu patlatiyordu — `saatleri_araliklara_birlestir` uc deger
dondurmeye basladi (B-23) ve `AtamaDegisikligi` `surum_id` almayi birakti
(TD-16) — ama betigi kosan hicbir sey olmadigi icin kimse gormedi. SDD 5.9
onu `GecmisSayaclar`in dort tuketicisinden biri sayiyor; denetleyen bir sey
olmadikca "dort tuketici tek kaynaktan beslenir" sozlesmesi kagit ustunde
kalir.

## Neden betik BASTAN SONA kosturulmuyor

`main()` ilk isi olarak veritabanini TEMIZLER ve iki donemi gercek cozucuyle
cozer. Takim icinde kosturmak, o ana kadar veri yazmis butun testleri
silmek olurdu; paylasimlı test veritabaninda bu tam olarak bu projenin bir
kez bedelini odedigi hata (B-24).

Bunun yerine betigin PARCALARI cagrilir. Kirilan iki sey de imza/sekil
uyusmazligiydi ve ikisi de bu yolla yakalanirdi: modul yuklenirken ve kriter
fonksiyonlari cagrilirken. Olculen sey kriterlerin GECMESI degil, betigin
CALISMASIDIR — gecmeleri ayri bir olcumun isi.
"""

import importlib
from datetime import date, timedelta

import pytest

from app.kurallar.baglam import Baglam, GorevNoktasiBilgisi, PersonelBilgisi
from tests.conftest import blok

NOKTA = 1
_G = date(2026, 1, 5)  # pazartesi


@pytest.fixture(scope="module")
def betik():
    """Modulu YUKLER. Import zamaninda patlayan bir betik burada dusmeli."""
    return importlib.import_module("scripts.kabul_olcumu")


def test_betik_yuklenebiliyor(betik) -> None:
    """Charter'in ALTI kriterinin altisi da uygulanmis olmali.

    Uzun sure besi uygulanmisti: K6 (yeniden cozumde degisen atama sayisi)
    Charter'da vardi ama betikte yoktu ve rapor "5 kriter" diyordu. Bir
    kriterin var olmasi, olcen bir sey olmadikca saglandigi anlamina gelmez.
    """
    for kimlik in ("_k1", "_k2", "_k3", "_k4", "_k5", "_k6"):
        assert hasattr(betik, kimlik), f"{kimlik} betikte yok"


def test_k3_donem_ici_ufku_kullaniyor(betik) -> None:
    """Charter 1.5: K3 planlama donemini olcer, doksan gunluk ufku degil.

    Bu testin yakaladigi somut hata: `adil_paylar` calisabilirlik oranini
    kosulsuz uyguluyordu ve K3 dogru cozumlerde bile 61,27 raporluyordu.
    """
    baglam = Baglam(
        gorev_noktalari={NOKTA: GorevNoktasiBilgisi(NOKTA)},
        personel={
            1: PersonelBilgisi(1, date(2025, 1, 1), None, frozenset(), haftalik_hedef_saat=40),
            2: PersonelBilgisi(2, date(2025, 1, 1), None, frozenset(), haftalik_hedef_saat=40),
        },
        zaman_ekseni=[_G + timedelta(days=i) for i in range(7)],
        donem_baslangic=_G,
        donem_bitis=_G + timedelta(days=6),
    )
    for i in (0, 1):
        for saat in range(20, 24):
            baglam.talep_saat[(_G + timedelta(days=i), saat, NOKTA)] = 1

    olcum = betik.CozumOlcumu(
        durum="uygun",
        atamalar=[blok(1, _G, 20, 4, NOKTA)],
        kapsama_eksikleri={},
        model_kurma_saniye=0.1,
        cozum_saniye=1.0,
        ilk_cozum_saniye=1.0,
        toplam_saniye=1.1,
    )
    kriter = betik._k3(olcum, baglam)
    assert kriter.kimlik == "K3"
    # Baslik ve esik metni DONEM ICI oldugunu soylemeli; rapora bakan kisi
    # hangi ufkun olculdugunu okuyabilmeli.
    assert "DONEM ICI" in kriter.esik
    assert any("kumulatif gosterge" in satir for satir in kriter.ayrinti)


def test_kriter_ciktisi_rapora_yetecek_alanlari_tasiyor(betik) -> None:
    """Rapor `Kriter` alanlarindan uretilir; biri bosalirsa cikti sessizce
    eksilir."""
    kriter = betik.Kriter(kimlik="K0", baslik="deneme", esik="esik", olculen="0", gecti=True)
    assert kriter.ayrinti == []
    assert kriter.gecti is True
