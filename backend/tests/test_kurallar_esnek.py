"""S1-S8 (+S6b) dogrula/ceza testleri: elle kurulan ornek blok listeleriyle.

Bu testler veritabani gerektirmez; Baglam ve AtamaKaydi elle olusturulur.

TUR 5'TE NE DEGISTI. Calisma bir katalogdan secilmiyor; test "GUNDUZ blogu"
yerine "08.00'de baslayan sekiz saatlik blok" der. Iki hedefin tanimi
degisti ve beklenen degerleri de degisti:

  - **S5** vardiya TIPI tercihi yerine ZAMAN ARALIGI tercihini olcer
    (SRS FR-3.2, TD-12): blogun TAMAMI araligin icinde kalmali.
  - **S6** karsilastirdigi sey blok kimligi degil FIILI baslangic saatidir;
    olcu zaten Tur 4'te saate gecmisti, simdi baslangic da bir karar
    degiskeni oldugu icin modelden okunuyor.
"""

from datetime import date, time, timedelta

import pytest

from app.kurallar import (
    Baglam,
    GorevNoktasiBilgisi,
    PersonelBilgisi,
    TercihKaydi,
    bul,
    tum_kimlikler,
)
from app.kurallar.esnek import (
    S1TalepKarsilama,
    S2GeceAdaleti,
    S3HaftaSonuAdaleti,
    S4ToplamSaatDengesi,
    S5TercihKarsilama,
    S6bBinaTutarliligi,
    S6CalismaDeseniTutarliligi,
    S7IzoleGun,
    S8DegisimMinimizasyonu,
)
from app.models.girdi import TercihTipi
from tests.conftest import blok

KAPI = 1
KONTROL_ODASI = 2
KAPI_BINA_A = 3
KAPI_BINA_B = 4

_G = date(2026, 1, 5)  # pazartesi


def _gun(kayma: int) -> date:
    return _G + timedelta(days=kayma)


@pytest.fixture
def baglam() -> Baglam:
    gorev_noktalari = {
        KAPI: GorevNoktasiBilgisi(KAPI),
        KONTROL_ODASI: GorevNoktasiBilgisi(KONTROL_ODASI),
        KAPI_BINA_A: GorevNoktasiBilgisi(KAPI_BINA_A, bina_id=1),
        KAPI_BINA_B: GorevNoktasiBilgisi(KAPI_BINA_B, bina_id=2),
    }
    personel = {
        1: PersonelBilgisi(1, date(2026, 1, 1), None, frozenset(), haftalik_hedef_saat=40),
        2: PersonelBilgisi(2, date(2026, 1, 1), None, frozenset(), haftalik_hedef_saat=40),
    }
    return Baglam(
        gorev_noktalari=gorev_noktalari,
        personel=personel,
        zaman_ekseni=[_gun(i) for i in range(14)],
    )


def _saat_talebi(
    baglam: Baglam, tarih: date, baslangic: int, sure: int, nokta: int, gereken: int
) -> None:
    """Bir zaman araliginin HER SAATINE ayni talebi yazar (SRS 4.3, S1).

    Sekiz saatlik bir aralikta bir kisilik acik, sekiz kisi-saat ceza uretir.
    """
    for kayma in range(sure):
        mutlak = baslangic + kayma
        baglam.talep_saat[(tarih + timedelta(days=mutlak // 24), mutlak % 24, nokta)] = gereken


def test_s1_kapsama_acigi_ceza_uretir(baglam: Baglam) -> None:
    kural = S1TalepKarsilama(parametreler={}, agirlik=100)
    _saat_talebi(baglam, _G, 8, 8, KAPI, 2)
    atamalar = [blok(1, _gun(0), 8, 8, KAPI)]
    ihlaller = kural.dogrula(atamalar, baglam)
    # Sekiz saatin her birinde bir kisi eksik: TEK aralik kaydi, sekiz
    # kisi-saat ceza.
    assert len(ihlaller) == 1
    assert ihlaller[0].kural_kimlik == "S1"
    assert ihlaller[0].ceza == 8
    assert "08.00–16.00" in ihlaller[0].aciklama


def test_s1_talep_karsilaninca_ceza_uretmez(baglam: Baglam) -> None:
    kural = S1TalepKarsilama(parametreler={}, agirlik=100)
    _saat_talebi(baglam, _G, 8, 8, KAPI, 1)
    atamalar = [blok(1, _gun(0), 8, 8, KAPI)]
    assert kural.dogrula(atamalar, baglam) == []


def test_s2_gece_adaletsizligi_ceza_uretir(baglam: Baglam) -> None:
    kural = S2GeceAdaleti(parametreler={}, agirlik=2)
    baglam.donem_baslangic = _G
    baglam.donem_bitis = _gun(3)
    for i in range(4):
        _saat_talebi(baglam, _gun(i), 0, 8, KAPI, 1)
        _saat_talebi(baglam, _gun(i), 0, 8, KONTROL_ODASI, 1)
    # OLCU ARTIK SAAT (K12). GECE blogu 00.00-08.00; gece donemiyle
    # (20:00-06:00) kesisimi ALTI saattir (00-05; 06 gece degil).
    # Talep: 4 gun x 2 nokta x 6 gece saati = 48 kisi-saat, havuz 2 ->
    # hedef 24. Personel 1 sekiz gece blogunun tamamini aliyor: 8 x 6 = 48,
    # sapma 24; personel 2 hic almiyor, sapma 24.
    # Onceki beklenti 4'tu ve birimi VARDIYA sayisiydi.
    atamalar = [blok(1, _gun(i + 5 - 5), 0, 8, KAPI) for i in range(4)] + [
        blok(1, _gun(i + 5 - 5), 0, 8, KONTROL_ODASI) for i in range(4)
    ]
    ihlaller = kural.dogrula(atamalar, baglam)
    ceza_by_personel = {i.personel_id: i.ceza for i in ihlaller}
    assert ceza_by_personel == {1: 24, 2: 24}
    assert all(i.kural_kimlik == "S2" for i in ihlaller)


def test_s2_dengeli_dagilim_ceza_uretmez(baglam: Baglam) -> None:
    kural = S2GeceAdaleti(parametreler={}, agirlik=2)
    baglam.donem_baslangic = _G
    baglam.donem_bitis = _gun(3)
    for i in range(4):
        _saat_talebi(baglam, _gun(i), 0, 8, KAPI, 1)
        _saat_talebi(baglam, _gun(i), 0, 8, KONTROL_ODASI, 1)
    atamalar = [blok(1, _gun(i + 5 - 5), 0, 8, KAPI) for i in range(4)] + [
        blok(2, _gun(i + 5 - 5), 0, 8, KONTROL_ODASI) for i in range(4)
    ]
    assert kural.dogrula(atamalar, baglam) == []


def test_s3_hafta_sonu_adaletsizligi_ceza_uretir(baglam: Baglam) -> None:
    kural = S3HaftaSonuAdaleti(parametreler={}, agirlik=3)
    baglam.donem_baslangic = _G
    baglam.donem_bitis = _gun(6)
    _saat_talebi(baglam, _gun(5), 8, 8, KAPI, 1)  # cumartesi
    _saat_talebi(baglam, _gun(6), 8, 8, KAPI, 1)  # pazar
    # OLCU ARTIK SAAT (K12). GUNDUZ blogu sekiz saat; hafta sonu talebi
    # 2 gun x 8 saat = 16 kisi-saat, havuz 2 -> hedef 8. Personel 1 iki
    # gunu de aliyor: 16 saat, sapma 8; personel 2 sifir, sapma 8.
    # Onceki beklenti 1'di ve birimi VARDIYA sayisiydi.
    atamalar = [
        blok(1, _gun(5), 8, 8, KAPI),
        blok(1, _gun(6), 8, 8, KAPI),
    ]
    ihlaller = kural.dogrula(atamalar, baglam)
    ceza_by_personel = {i.personel_id: i.ceza for i in ihlaller}
    assert ceza_by_personel == {1: 8, 2: 8}
    assert all(i.kural_kimlik == "S3" for i in ihlaller)


def test_s3_dengeli_hafta_sonu_ceza_uretmez(baglam: Baglam) -> None:
    kural = S3HaftaSonuAdaleti(parametreler={}, agirlik=3)
    baglam.donem_baslangic = _G
    baglam.donem_bitis = _gun(6)
    _saat_talebi(baglam, _gun(5), 8, 8, KAPI, 1)
    _saat_talebi(baglam, _gun(6), 8, 8, KAPI, 1)
    atamalar = [
        blok(1, _gun(5), 8, 8, KAPI),
        blok(2, _gun(6), 8, 8, KAPI),
    ]
    assert kural.dogrula(atamalar, baglam) == []


def test_s4_saat_sapmasi_ceza_uretir(baglam: Baglam) -> None:
    kural = S4ToplamSaatDengesi(parametreler={}, agirlik=4)
    baglam.donem_baslangic = _G
    baglam.donem_bitis = _gun(6)  # 7 gun -> carpan 1.0
    # Ikisi de hedef=40 (esit agirlik) -> toplam_talep_saat 5*8=40'i esit bolusur: pay=20.
    for i in range(5):
        _saat_talebi(baglam, _gun(i), 8, 8, KAPI, 1)
    # personel 1 yalnizca 3 vardiya x 8 saat = 24 saat calisiyor (payin 4 saat ustunde).
    atamalar = [blok(1, _gun(i + 5 - 5), 8, 8, KAPI) for i in range(3)]
    ihlaller = kural.dogrula(atamalar, baglam)
    ceza_by_personel = {i.personel_id: i.ceza for i in ihlaller}
    assert ceza_by_personel[1] == pytest.approx(4.0)
    assert ceza_by_personel[2] == pytest.approx(20.0)  # hic calismiyor, payin tamami eksik


def test_s4_hedefi_tutturunca_ceza_uretmez(baglam: Baglam) -> None:
    kural = S4ToplamSaatDengesi(parametreler={}, agirlik=4)
    baglam.donem_baslangic = _G
    baglam.donem_bitis = _gun(6)
    baglam.personel = {1: PersonelBilgisi(1, date(2026, 1, 1), None, frozenset(), 40)}
    # Tek personel oldugu icin toplam_talep_saatin tamami onun payi: 5*8=40 saat.
    for i in range(5):
        _saat_talebi(baglam, _gun(i), 8, 8, KAPI, 1)
    atamalar = [blok(1, _gun(i + 5 - 5), 8, 8, KAPI) for i in range(5)]  # 40 saat
    assert kural.dogrula(atamalar, baglam) == []


def test_s5_calismama_tercihi_ihlal_edilince_ceza_uretir(baglam: Baglam) -> None:
    kural = S5TercihKarsilama(parametreler={}, agirlik=5)
    baglam.tercihler.append(TercihKaydi(1, _G, TercihTipi.CALISMAMA))
    atamalar = [blok(1, _gun(0), 8, 8, KAPI)]
    ihlaller = kural.dogrula(atamalar, baglam)
    assert len(ihlaller) == 1
    assert ihlaller[0].kural_kimlik == "S5"
    assert ihlaller[0].ceza == 1


def test_s5_calismama_tercihine_uyulunca_ceza_uretmez(baglam: Baglam) -> None:
    kural = S5TercihKarsilama(parametreler={}, agirlik=5)
    baglam.tercihler.append(TercihKaydi(1, _G, TercihTipi.CALISMAMA))
    assert kural.dogrula([], baglam) == []


def test_s5_aralik_disina_tasan_blok_ceza_uretir(baglam: Baglam) -> None:
    """Kuralin YENI olcusu (SRS FR-3.2, TD-12).

    Tercih artik bir vardiya TIPI degil bir ZAMAN ARALIGI: 08.00–16.00 arasi
    calismak isteyen personel 16.00'da baslayan bloga atanirsa tercih
    karsilanmamistir.
    """
    kural = S5TercihKarsilama(parametreler={}, agirlik=5)
    baglam.tercihler.append(
        TercihKaydi(1, _G, TercihTipi.ZAMAN_ARALIGI_TERCIHI, time(8, 0), time(16, 0))
    )
    ihlaller = kural.dogrula([blok(1, _gun(0), 16, 8, KAPI)], baglam)
    assert len(ihlaller) == 1


def test_s5_aralik_icinde_kalan_blok_ceza_uretmez(baglam: Baglam) -> None:
    kural = S5TercihKarsilama(parametreler={}, agirlik=5)
    baglam.tercihler.append(
        TercihKaydi(1, _G, TercihTipi.ZAMAN_ARALIGI_TERCIHI, time(8, 0), time(16, 0))
    )
    assert kural.dogrula([blok(1, _gun(0), 8, 8, KAPI)], baglam) == []


def test_s5_araligin_bir_kismini_asan_blok_da_ceza_uretir(baglam: Baglam) -> None:
    """TD-12: blogun TAMAMI araligin icinde kalmali.

    08.00'de baslayan on saatlik blok 16.00–18.00 arasinda araligin disina
    tasar; kismi ortusme yeterli degildir.
    """
    kural = S5TercihKarsilama(parametreler={}, agirlik=5)
    baglam.tercihler.append(
        TercihKaydi(1, _G, TercihTipi.ZAMAN_ARALIGI_TERCIHI, time(8, 0), time(16, 0))
    )
    assert len(kural.dogrula([blok(1, _gun(0), 8, 10, KAPI)], baglam)) == 1


def test_s5_atanmamis_gun_aralik_tercihini_ihlal_etmez(baglam: Baglam) -> None:
    """Hic calisilmayan gun ceza uretmez — eski formulasyon da uretmiyordu
    (`Σ_{s ≠ s*} y`); karsilanma RAPORU ise TD-12 uyarinca ayri bir olcudur."""
    kural = S5TercihKarsilama(parametreler={}, agirlik=5)
    baglam.tercihler.append(
        TercihKaydi(1, _G, TercihTipi.ZAMAN_ARALIGI_TERCIHI, time(8, 0), time(16, 0))
    )
    assert kural.dogrula([], baglam) == []


def test_s6_baslangic_saati_kaymasi_ceza_uretir(baglam: Baglam) -> None:
    """OLCU BLOK KIMLIGI DEGIL BASLANGIC SAATI (K13).

    08.00 -> 16.00 kaymasi sekiz saat, tolerans iki saat: cezali.
    """
    kural = S6CalismaDeseniTutarliligi(parametreler={"desen_toleransi_saat": 2}, agirlik=10)
    atamalar = [
        blok(1, _gun(0), 8, 8, KAPI),
        blok(1, _gun(1), 16, 8, KAPI),
    ]
    ihlaller = kural.dogrula(atamalar, baglam)
    assert len(ihlaller) == 1
    assert "baslangici" in ihlaller[0].aciklama.lower()


def test_s6_bina_degisimini_degerlendirmez(baglam: Baglam) -> None:
    """S6, yalniz vardiya tipi tutarliligina bakar; bina tutarliligi S6b'nin isidir."""
    kural = S6CalismaDeseniTutarliligi(parametreler={}, agirlik=10)
    atamalar = [
        blok(1, _gun(0), 8, 8, KAPI_BINA_A),
        blok(1, _gun(1), 8, 8, KAPI_BINA_B),
    ]
    assert kural.dogrula(atamalar, baglam) == []


def test_s6_tutarli_desen_ceza_uretmez(baglam: Baglam) -> None:
    kural = S6CalismaDeseniTutarliligi(parametreler={}, agirlik=10)
    atamalar = [
        blok(1, _gun(0), 8, 8, KAPI_BINA_A),
        blok(1, _gun(1), 8, 8, KAPI_BINA_A),
    ]
    assert kural.dogrula(atamalar, baglam) == []


def test_s6b_bina_degisimi_ceza_uretir(baglam: Baglam) -> None:
    kural = S6bBinaTutarliligi(parametreler={}, agirlik=6)
    atamalar = [
        blok(1, _gun(0), 8, 8, KAPI_BINA_A),
        blok(1, _gun(1), 8, 8, KAPI_BINA_B),
    ]
    ihlaller = kural.dogrula(atamalar, baglam)
    assert len(ihlaller) == 1
    assert "bina" in ihlaller[0].aciklama.lower()


def test_s6b_vardiya_tipi_degisimini_degerlendirmez(baglam: Baglam) -> None:
    """S6b, yalniz bina tutarliligina bakar; vardiya tipi degisimi S6'nin isidir."""
    kural = S6bBinaTutarliligi(parametreler={}, agirlik=6)
    atamalar = [
        blok(1, _gun(0), 8, 8, KAPI),
        blok(1, _gun(1), 16, 8, KAPI),
    ]
    assert kural.dogrula(atamalar, baglam) == []


def test_s6b_ayni_binada_ceza_uretmez(baglam: Baglam) -> None:
    kural = S6bBinaTutarliligi(parametreler={}, agirlik=6)
    atamalar = [
        blok(1, _gun(0), 8, 8, KAPI_BINA_A),
        blok(1, _gun(1), 8, 8, KAPI_BINA_A),
    ]
    assert kural.dogrula(atamalar, baglam) == []


def test_s6b_tesis_geneli_noktalar_bina_degisimine_girmez(baglam: Baglam) -> None:
    """Bina bilgisi bos olan (tesis geneli) noktalar arasi gecis bina degisimi sayilmaz."""
    kural = S6bBinaTutarliligi(parametreler={}, agirlik=6)
    atamalar = [
        blok(1, _gun(0), 8, 8, KAPI),  # bina_id yok
        blok(1, _gun(1), 8, 8, KAPI_BINA_A),
    ]
    assert kural.dogrula(atamalar, baglam) == []


def test_s7_izole_calisma_gunu_ceza_uretir(baglam: Baglam) -> None:
    kural = S7IzoleGun(parametreler={}, agirlik=7)
    baglam.donem_baslangic = _G
    baglam.donem_bitis = _gun(2)
    atamalar = [blok(1, _gun(1), 8, 8, KAPI)]
    ihlaller = kural.dogrula(atamalar, baglam)
    assert len(ihlaller) == 1
    assert "calisma" in ihlaller[0].aciklama.lower()


def test_s7_izole_izin_gunu_ceza_uretir(baglam: Baglam) -> None:
    kural = S7IzoleGun(parametreler={}, agirlik=7)
    baglam.donem_baslangic = _G
    baglam.donem_bitis = _gun(2)
    atamalar = [
        blok(1, _gun(0), 8, 8, KAPI),
        blok(1, _gun(2), 8, 8, KAPI),
    ]
    ihlaller = kural.dogrula(atamalar, baglam)
    assert len(ihlaller) == 1
    assert "izin" in ihlaller[0].aciklama.lower()


def test_s7_surekli_calisma_ceza_uretmez(baglam: Baglam) -> None:
    kural = S7IzoleGun(parametreler={}, agirlik=7)
    baglam.donem_baslangic = _G
    baglam.donem_bitis = _gun(2)
    atamalar = [blok(1, _gun(i + 5 - 5), 8, 8, KAPI) for i in range(3)]
    assert kural.dogrula(atamalar, baglam) == []


def test_s8_onceki_cizelge_yoksa_ceza_uretmez(baglam: Baglam) -> None:
    kural = S8DegisimMinimizasyonu(parametreler={}, agirlik=8)
    atamalar = [blok(1, _gun(0), 8, 8, KAPI)]
    assert kural.dogrula(atamalar, baglam) == []


def test_s8_degisen_atama_ceza_uretir(baglam: Baglam) -> None:
    """OLCU ARTIK KISI-SAAT, ATAMA SAYISI DEGIL.

    Formul degismedi (`Σ |x − x_onceki|`); degisen, `x`in indeks kumesidir.
    Blok ekseninde bir birim "bir vardiya" demekti ve bu ornek 2 birim
    uretiyordu (biri kalkti, biri geldi). Saat ekseninde ayni degisiklik
    sekiz saat kaldirip sekiz saat ekler: 16 kisi-saat. Olcu boylece S1,
    S2, S3 ve S4 ile ayni birime geldi.
    """
    kural = S8DegisimMinimizasyonu(parametreler={}, agirlik=8)
    baglam.onceki_atamalar = [blok(1, _gun(0), 8, 8, KAPI)]
    atamalar = [blok(1, _gun(0), 16, 8, KAPI)]
    ihlaller = kural.dogrula(atamalar, baglam)
    assert len(ihlaller) == 16
    assert all(i.ceza == 1 for i in ihlaller)


def test_s8_ayni_cizelgede_ceza_uretmez(baglam: Baglam) -> None:
    kural = S8DegisimMinimizasyonu(parametreler={}, agirlik=8)
    baglam.onceki_atamalar = [blok(1, _gun(0), 8, 8, KAPI)]
    atamalar = [blok(1, _gun(0), 8, 8, KAPI)]
    assert kural.dogrula(atamalar, baglam) == []


def test_s1_modele_ekle_karsilanamayan_talep_icin_eksigi_zorunlu_kilar(baglam: Baglam) -> None:
    """Talep 2, tek bir aday personel varken S1'in eksik degiskenini >=1'e zorlar.

    Kisit artik SAAT BASINA yazilir: sekiz saatlik bir aralikta bir kisilik
    acik sekiz kisi-saat ceza uretir (SRS 4.3, S1).
    """
    from ortools.sat.python import cp_model

    model = cp_model.CpModel()
    baglam.zaman_ekseni = [_G]
    baglam.donem_baslangic = _G
    baglam.donem_bitis = _G
    _saat_talebi(baglam, _G, 8, 8, KAPI, 2)
    degiskenler = {
        (1, saat, KAPI): model.new_bool_var(f"x_{saat}") for saat in range(8, 16)
    }

    kural = S1TalepKarsilama(parametreler={})
    terim = kural.modele_ekle(model, degiskenler, baglam)
    for degisken in degiskenler.values():
        model.add(degisken == 1)
    model.minimize(terim)

    cozucu = cp_model.CpSolver()
    durum = cozucu.solve(model)
    assert durum == cp_model.OPTIMAL
    # Bir kisilik acik sekiz saat boyunca surer: sekiz kisi-saat.
    assert cozucu.objective_value == 8


def test_kayit_defterinde_s1_s8_ve_s6b_tamami_bulunur() -> None:
    for kimlik in ["S1", "S2", "S3", "S4", "S5", "S6", "S6b", "S7", "S8"]:
        assert bul(kimlik) is not None, f"{kimlik} kayit defterinde yok"


def test_kayit_defterinde_yirmi_kural_kayitli() -> None:
    """Tur 4'te uc kural eklendi: H9, H10 (SRS 4.2) ve S1f (K4).

    S1f ayri bir kayittir cunku SDD 4.2.3'teki tablo kural basina TEK
    agirlik sutunu tasir; S1'in formulasyonunda iki agirlik var (w1, w1f).
    Ayni bolme S6/S6b'de de yapilmisti.
    """
    beklenen = {f"H{i}" for i in range(1, 11)} | {f"S{i}" for i in range(1, 9)} | {"S6b", "S1f"}
    assert set(tum_kimlikler()) == beklenen
    assert len(beklenen) == 20
