"""S1-S8 (+S6b) dogrula/ceza testleri: elle kurulan ornek atama listeleriyle (Sprint 1 Gun 3-4).

Bu testler veritabani gerektirmez; Baglam ve AtamaKaydi elle olusturulur.
"""

from datetime import date, time

import pytest

from app.kurallar import (
    AtamaKaydi,
    Baglam,
    GorevNoktasiBilgisi,
    PersonelBilgisi,
    TercihKaydi,
    VardiyaTipiBilgisi,
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
    S6VardiyaDeseniTutarliligi,
    S7IzoleGun,
    S8DegisimMinimizasyonu,
)
from app.models.girdi import TercihTipi

GECE = 1
GUNDUZ = 2
AKSAM = 3

KAPI = 1
KONTROL_ODASI = 2
KAPI_BINA_A = 3
KAPI_BINA_B = 4


@pytest.fixture
def baglam() -> Baglam:
    vardiya_tipleri = {
        GECE: VardiyaTipiBilgisi(GECE, time(0, 0), time(8, 0), 8, True),
        GUNDUZ: VardiyaTipiBilgisi(GUNDUZ, time(8, 0), time(16, 0), 8, False),
        AKSAM: VardiyaTipiBilgisi(AKSAM, time(16, 0), time(0, 0), 8, False),
    }
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
        vardiya_tipleri=vardiya_tipleri, gorev_noktalari=gorev_noktalari, personel=personel
    )


def _blok_talebi(baglam: Baglam, tarih: date, blok: int, nokta: int, gereken: int) -> None:
    """Bir blogun kapsadigi HER SAATE ayni talebi yazar.

    S1 artik saat ekseninde calisiyor (SRS 4.3): talep bir bloga degil bir
    zaman araligina baglidir. Sekiz saatlik bir blokta bir kisilik acik,
    sekiz kisi-saat ceza uretir.
    """
    for gun, saat in baglam.blok_saatleri(tarih, blok):
        baglam.talep_saat[(gun, saat, nokta)] = gereken


def test_s1_kapsama_acigi_ceza_uretir(baglam: Baglam) -> None:
    kural = S1TalepKarsilama(parametreler={}, agirlik=100)
    _blok_talebi(baglam, date(2026, 1, 5), GUNDUZ, KAPI, 2)
    atamalar = [AtamaKaydi(1, date(2026, 1, 5), GUNDUZ, KAPI)]
    ihlaller = kural.dogrula(atamalar, baglam)
    # Sekiz saatin her birinde bir kisi eksik: TEK aralik kaydi, sekiz
    # kisi-saat ceza.
    assert len(ihlaller) == 1
    assert ihlaller[0].kural_kimlik == "S1"
    assert ihlaller[0].ceza == 8
    assert "08.00–16.00" in ihlaller[0].aciklama


def test_s1_talep_karsilaninca_ceza_uretmez(baglam: Baglam) -> None:
    kural = S1TalepKarsilama(parametreler={}, agirlik=100)
    _blok_talebi(baglam, date(2026, 1, 5), GUNDUZ, KAPI, 1)
    atamalar = [AtamaKaydi(1, date(2026, 1, 5), GUNDUZ, KAPI)]
    assert kural.dogrula(atamalar, baglam) == []


def test_s2_gece_adaletsizligi_ceza_uretir(baglam: Baglam) -> None:
    kural = S2GeceAdaleti(parametreler={}, agirlik=2)
    baglam.donem_baslangic = date(2026, 1, 5)
    baglam.donem_bitis = date(2026, 1, 8)
    for i in range(4):
        gun = date(2026, 1, 5 + i)
        _blok_talebi(baglam, gun, GECE, KAPI, 1)
        _blok_talebi(baglam, gun, GECE, KONTROL_ODASI, 1)
    # OLCU ARTIK SAAT (K12). GECE blogu 00.00-08.00; gece donemiyle
    # (20:00-06:00) kesisimi ALTI saattir (00-05; 06 gece degil).
    # Talep: 4 gun x 2 nokta x 6 gece saati = 48 kisi-saat, havuz 2 ->
    # hedef 24. Personel 1 sekiz gece blogunun tamamini aliyor: 8 x 6 = 48,
    # sapma 24; personel 2 hic almiyor, sapma 24.
    # Onceki beklenti 4'tu ve birimi VARDIYA sayisiydi.
    atamalar = [AtamaKaydi(1, date(2026, 1, 5 + i), GECE, KAPI) for i in range(4)] + [
        AtamaKaydi(1, date(2026, 1, 5 + i), GECE, KONTROL_ODASI) for i in range(4)
    ]
    ihlaller = kural.dogrula(atamalar, baglam)
    ceza_by_personel = {i.personel_id: i.ceza for i in ihlaller}
    assert ceza_by_personel == {1: 24, 2: 24}
    assert all(i.kural_kimlik == "S2" for i in ihlaller)


def test_s2_dengeli_dagilim_ceza_uretmez(baglam: Baglam) -> None:
    kural = S2GeceAdaleti(parametreler={}, agirlik=2)
    baglam.donem_baslangic = date(2026, 1, 5)
    baglam.donem_bitis = date(2026, 1, 8)
    for i in range(4):
        gun = date(2026, 1, 5 + i)
        _blok_talebi(baglam, gun, GECE, KAPI, 1)
        _blok_talebi(baglam, gun, GECE, KONTROL_ODASI, 1)
    atamalar = [AtamaKaydi(1, date(2026, 1, 5 + i), GECE, KAPI) for i in range(4)] + [
        AtamaKaydi(2, date(2026, 1, 5 + i), GECE, KONTROL_ODASI) for i in range(4)
    ]
    assert kural.dogrula(atamalar, baglam) == []


def test_s3_hafta_sonu_adaletsizligi_ceza_uretir(baglam: Baglam) -> None:
    kural = S3HaftaSonuAdaleti(parametreler={}, agirlik=3)
    baglam.donem_baslangic = date(2026, 1, 5)
    baglam.donem_bitis = date(2026, 1, 11)
    _blok_talebi(baglam, date(2026, 1, 10), GUNDUZ, KAPI, 1)  # cumartesi
    _blok_talebi(baglam, date(2026, 1, 11), GUNDUZ, KAPI, 1)  # pazar
    # OLCU ARTIK SAAT (K12). GUNDUZ blogu sekiz saat; hafta sonu talebi
    # 2 gun x 8 saat = 16 kisi-saat, havuz 2 -> hedef 8. Personel 1 iki
    # gunu de aliyor: 16 saat, sapma 8; personel 2 sifir, sapma 8.
    # Onceki beklenti 1'di ve birimi VARDIYA sayisiydi.
    atamalar = [
        AtamaKaydi(1, date(2026, 1, 10), GUNDUZ, KAPI),
        AtamaKaydi(1, date(2026, 1, 11), GUNDUZ, KAPI),
    ]
    ihlaller = kural.dogrula(atamalar, baglam)
    ceza_by_personel = {i.personel_id: i.ceza for i in ihlaller}
    assert ceza_by_personel == {1: 8, 2: 8}
    assert all(i.kural_kimlik == "S3" for i in ihlaller)


def test_s3_dengeli_hafta_sonu_ceza_uretmez(baglam: Baglam) -> None:
    kural = S3HaftaSonuAdaleti(parametreler={}, agirlik=3)
    baglam.donem_baslangic = date(2026, 1, 5)
    baglam.donem_bitis = date(2026, 1, 11)
    _blok_talebi(baglam, date(2026, 1, 10), GUNDUZ, KAPI, 1)
    _blok_talebi(baglam, date(2026, 1, 11), GUNDUZ, KAPI, 1)
    atamalar = [
        AtamaKaydi(1, date(2026, 1, 10), GUNDUZ, KAPI),
        AtamaKaydi(2, date(2026, 1, 11), GUNDUZ, KAPI),
    ]
    assert kural.dogrula(atamalar, baglam) == []


def test_s4_saat_sapmasi_ceza_uretir(baglam: Baglam) -> None:
    kural = S4ToplamSaatDengesi(parametreler={}, agirlik=4)
    baglam.donem_baslangic = date(2026, 1, 5)
    baglam.donem_bitis = date(2026, 1, 11)  # 7 gun -> carpan 1.0
    # Ikisi de hedef=40 (esit agirlik) -> toplam_talep_saat 5*8=40'i esit bolusur: pay=20.
    for i in range(5):
        _blok_talebi(baglam, date(2026, 1, 5 + i), GUNDUZ, KAPI, 1)
    # personel 1 yalnizca 3 vardiya x 8 saat = 24 saat calisiyor (payin 4 saat ustunde).
    atamalar = [AtamaKaydi(1, date(2026, 1, 5 + i), GUNDUZ, KAPI) for i in range(3)]
    ihlaller = kural.dogrula(atamalar, baglam)
    ceza_by_personel = {i.personel_id: i.ceza for i in ihlaller}
    assert ceza_by_personel[1] == pytest.approx(4.0)
    assert ceza_by_personel[2] == pytest.approx(20.0)  # hic calismiyor, payin tamami eksik


def test_s4_hedefi_tutturunca_ceza_uretmez(baglam: Baglam) -> None:
    kural = S4ToplamSaatDengesi(parametreler={}, agirlik=4)
    baglam.donem_baslangic = date(2026, 1, 5)
    baglam.donem_bitis = date(2026, 1, 11)
    baglam.personel = {1: PersonelBilgisi(1, date(2026, 1, 1), None, frozenset(), 40)}
    # Tek personel oldugu icin toplam_talep_saatin tamami onun payi: 5*8=40 saat.
    for i in range(5):
        _blok_talebi(baglam, date(2026, 1, 5 + i), GUNDUZ, KAPI, 1)
    atamalar = [AtamaKaydi(1, date(2026, 1, 5 + i), GUNDUZ, KAPI) for i in range(5)]  # 40 saat
    assert kural.dogrula(atamalar, baglam) == []


def test_s5_calismama_tercihi_ihlal_edilince_ceza_uretir(baglam: Baglam) -> None:
    kural = S5TercihKarsilama(parametreler={}, agirlik=5)
    baglam.tercihler.append(TercihKaydi(1, date(2026, 1, 5), TercihTipi.CALISMAMA))
    atamalar = [AtamaKaydi(1, date(2026, 1, 5), GUNDUZ, KAPI)]
    ihlaller = kural.dogrula(atamalar, baglam)
    assert len(ihlaller) == 1
    assert ihlaller[0].kural_kimlik == "S5"
    assert ihlaller[0].ceza == 1


def test_s5_calismama_tercihine_uyulunca_ceza_uretmez(baglam: Baglam) -> None:
    kural = S5TercihKarsilama(parametreler={}, agirlik=5)
    baglam.tercihler.append(TercihKaydi(1, date(2026, 1, 5), TercihTipi.CALISMAMA))
    assert kural.dogrula([], baglam) == []


def test_s5_vardiya_tipi_tercihi_farkli_vardiyaya_atanirsa_ceza_uretir(baglam: Baglam) -> None:
    kural = S5TercihKarsilama(parametreler={}, agirlik=5)
    baglam.tercihler.append(
        TercihKaydi(1, date(2026, 1, 5), TercihTipi.VARDIYA_TIPI_TERCIHI, GUNDUZ)
    )
    atamalar = [AtamaKaydi(1, date(2026, 1, 5), AKSAM, KAPI)]
    ihlaller = kural.dogrula(atamalar, baglam)
    assert len(ihlaller) == 1


def test_s5_vardiya_tipi_tercihi_karsilaninca_ceza_uretmez(baglam: Baglam) -> None:
    kural = S5TercihKarsilama(parametreler={}, agirlik=5)
    baglam.tercihler.append(
        TercihKaydi(1, date(2026, 1, 5), TercihTipi.VARDIYA_TIPI_TERCIHI, GUNDUZ)
    )
    atamalar = [AtamaKaydi(1, date(2026, 1, 5), GUNDUZ, KAPI)]
    assert kural.dogrula(atamalar, baglam) == []


def test_s5_atanmamis_gun_vardiya_tipi_tercihini_ihlal_etmez(baglam: Baglam) -> None:
    kural = S5TercihKarsilama(parametreler={}, agirlik=5)
    baglam.tercihler.append(
        TercihKaydi(1, date(2026, 1, 5), TercihTipi.VARDIYA_TIPI_TERCIHI, GUNDUZ)
    )
    assert kural.dogrula([], baglam) == []


def test_s6_baslangic_saati_kaymasi_ceza_uretir(baglam: Baglam) -> None:
    """OLCU BLOK KIMLIGI DEGIL BASLANGIC SAATI (K13).

    08.00 -> 16.00 kaymasi sekiz saat, tolerans iki saat: cezali.
    """
    kural = S6VardiyaDeseniTutarliligi(parametreler={"desen_toleransi_saat": 2}, agirlik=10)
    atamalar = [
        AtamaKaydi(1, date(2026, 1, 5), GUNDUZ, KAPI),
        AtamaKaydi(1, date(2026, 1, 6), AKSAM, KAPI),
    ]
    ihlaller = kural.dogrula(atamalar, baglam)
    assert len(ihlaller) == 1
    assert "baslangici" in ihlaller[0].aciklama.lower()


def test_s6_bina_degisimini_degerlendirmez(baglam: Baglam) -> None:
    """S6, yalniz vardiya tipi tutarliligina bakar; bina tutarliligi S6b'nin isidir."""
    kural = S6VardiyaDeseniTutarliligi(parametreler={}, agirlik=10)
    atamalar = [
        AtamaKaydi(1, date(2026, 1, 5), GUNDUZ, KAPI_BINA_A),
        AtamaKaydi(1, date(2026, 1, 6), GUNDUZ, KAPI_BINA_B),
    ]
    assert kural.dogrula(atamalar, baglam) == []


def test_s6_tutarli_desen_ceza_uretmez(baglam: Baglam) -> None:
    kural = S6VardiyaDeseniTutarliligi(parametreler={}, agirlik=10)
    atamalar = [
        AtamaKaydi(1, date(2026, 1, 5), GUNDUZ, KAPI_BINA_A),
        AtamaKaydi(1, date(2026, 1, 6), GUNDUZ, KAPI_BINA_A),
    ]
    assert kural.dogrula(atamalar, baglam) == []


def test_s6b_bina_degisimi_ceza_uretir(baglam: Baglam) -> None:
    kural = S6bBinaTutarliligi(parametreler={}, agirlik=6)
    atamalar = [
        AtamaKaydi(1, date(2026, 1, 5), GUNDUZ, KAPI_BINA_A),
        AtamaKaydi(1, date(2026, 1, 6), GUNDUZ, KAPI_BINA_B),
    ]
    ihlaller = kural.dogrula(atamalar, baglam)
    assert len(ihlaller) == 1
    assert "bina" in ihlaller[0].aciklama.lower()


def test_s6b_vardiya_tipi_degisimini_degerlendirmez(baglam: Baglam) -> None:
    """S6b, yalniz bina tutarliligina bakar; vardiya tipi degisimi S6'nin isidir."""
    kural = S6bBinaTutarliligi(parametreler={}, agirlik=6)
    atamalar = [
        AtamaKaydi(1, date(2026, 1, 5), GUNDUZ, KAPI),
        AtamaKaydi(1, date(2026, 1, 6), AKSAM, KAPI),
    ]
    assert kural.dogrula(atamalar, baglam) == []


def test_s6b_ayni_binada_ceza_uretmez(baglam: Baglam) -> None:
    kural = S6bBinaTutarliligi(parametreler={}, agirlik=6)
    atamalar = [
        AtamaKaydi(1, date(2026, 1, 5), GUNDUZ, KAPI_BINA_A),
        AtamaKaydi(1, date(2026, 1, 6), GUNDUZ, KAPI_BINA_A),
    ]
    assert kural.dogrula(atamalar, baglam) == []


def test_s6b_tesis_geneli_noktalar_bina_degisimine_girmez(baglam: Baglam) -> None:
    """Bina bilgisi bos olan (tesis geneli) noktalar arasi gecis bina degisimi sayilmaz."""
    kural = S6bBinaTutarliligi(parametreler={}, agirlik=6)
    atamalar = [
        AtamaKaydi(1, date(2026, 1, 5), GUNDUZ, KAPI),  # bina_id yok
        AtamaKaydi(1, date(2026, 1, 6), GUNDUZ, KAPI_BINA_A),
    ]
    assert kural.dogrula(atamalar, baglam) == []


def test_s7_izole_calisma_gunu_ceza_uretir(baglam: Baglam) -> None:
    kural = S7IzoleGun(parametreler={}, agirlik=7)
    baglam.donem_baslangic = date(2026, 1, 5)
    baglam.donem_bitis = date(2026, 1, 7)
    atamalar = [AtamaKaydi(1, date(2026, 1, 6), GUNDUZ, KAPI)]
    ihlaller = kural.dogrula(atamalar, baglam)
    assert len(ihlaller) == 1
    assert "calisma" in ihlaller[0].aciklama.lower()


def test_s7_izole_izin_gunu_ceza_uretir(baglam: Baglam) -> None:
    kural = S7IzoleGun(parametreler={}, agirlik=7)
    baglam.donem_baslangic = date(2026, 1, 5)
    baglam.donem_bitis = date(2026, 1, 7)
    atamalar = [
        AtamaKaydi(1, date(2026, 1, 5), GUNDUZ, KAPI),
        AtamaKaydi(1, date(2026, 1, 7), GUNDUZ, KAPI),
    ]
    ihlaller = kural.dogrula(atamalar, baglam)
    assert len(ihlaller) == 1
    assert "izin" in ihlaller[0].aciklama.lower()


def test_s7_surekli_calisma_ceza_uretmez(baglam: Baglam) -> None:
    kural = S7IzoleGun(parametreler={}, agirlik=7)
    baglam.donem_baslangic = date(2026, 1, 5)
    baglam.donem_bitis = date(2026, 1, 7)
    atamalar = [AtamaKaydi(1, date(2026, 1, 5 + i), GUNDUZ, KAPI) for i in range(3)]
    assert kural.dogrula(atamalar, baglam) == []


def test_s8_onceki_cizelge_yoksa_ceza_uretmez(baglam: Baglam) -> None:
    kural = S8DegisimMinimizasyonu(parametreler={}, agirlik=8)
    atamalar = [AtamaKaydi(1, date(2026, 1, 5), GUNDUZ, KAPI)]
    assert kural.dogrula(atamalar, baglam) == []


def test_s8_degisen_atama_ceza_uretir(baglam: Baglam) -> None:
    kural = S8DegisimMinimizasyonu(parametreler={}, agirlik=8)
    baglam.onceki_atamalar = [AtamaKaydi(1, date(2026, 1, 5), GUNDUZ, KAPI)]
    atamalar = [AtamaKaydi(1, date(2026, 1, 5), AKSAM, KAPI)]
    ihlaller = kural.dogrula(atamalar, baglam)
    # eski atama kalkti (1 birim), yeni atama geldi (1 birim) -> toplam 2 birim ceza.
    assert len(ihlaller) == 2
    assert all(i.ceza == 1 for i in ihlaller)


def test_s8_ayni_cizelgede_ceza_uretmez(baglam: Baglam) -> None:
    kural = S8DegisimMinimizasyonu(parametreler={}, agirlik=8)
    baglam.onceki_atamalar = [AtamaKaydi(1, date(2026, 1, 5), GUNDUZ, KAPI)]
    atamalar = [AtamaKaydi(1, date(2026, 1, 5), GUNDUZ, KAPI)]
    assert kural.dogrula(atamalar, baglam) == []


def test_s1_modele_ekle_karsilanamayan_talep_icin_eksigi_zorunlu_kilar(baglam: Baglam) -> None:
    """Talep 2, tek bir aday personel varken S1'in eksik degiskenini >=1'e zorladigini
    ve fazla atamayi (ust sinir) engelledigini dogrular (Sprint 2 Gun 6)."""
    from ortools.sat.python import cp_model

    model = cp_model.CpModel()
    gun = date(2026, 1, 5)
    x1 = model.new_bool_var("x1")
    degiskenler = {(1, gun, GUNDUZ, KAPI): x1}
    baglam.zaman_ekseni = [gun]
    baglam.donem_baslangic = gun
    baglam.donem_bitis = gun
    _blok_talebi(baglam, gun, GUNDUZ, KAPI, 2)

    kural = S1TalepKarsilama(parametreler={})
    terim = kural.modele_ekle(model, degiskenler, baglam)
    model.add(x1 == 1)
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
