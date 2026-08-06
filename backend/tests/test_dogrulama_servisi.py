"""SDD 5.5 (surum 1.3) degisikligi_dogrula testleri (Sprint 2 Gun 9).

Iki katman: (1) veritabani gerektirmeyen, elle kurulan Baglam/AtamaKaydi
ornekleriyle S2'nin donem geneli kapsaminin neden pencereyle
sinirlandirilamayacagini dogrudan gosteren testler; (2) canli PostgreSQL
gerektiren, DogrulamaServisi'ni uctan uca (zorunlu red / esnek kabul +
ceza farki / surum durumlari) dogrulayan testler.
"""

import uuid
from datetime import date, time, timedelta

import pytest
from sqlalchemy import select

from app.db import OturumYerel
from app.kurallar import (
    AtamaKaydi,
    Baglam,
    GorevNoktasiBilgisi,
    PersonelBilgisi,
    VardiyaTipiBilgisi,
)
from app.kurallar.esnek import S2GeceAdaleti
from app.kurallar.kayit_defteri import bul
from app.kurallar.temel import KuralKapsami
from app.models.sonuc import Atama, AtamaKaynagi, CizelgeSurumu, CizelgeSurumuDurumu, Donem
from app.models.tanim import GorevNoktasi, Personel, VardiyaTipi
from app.services.dogrulama_servisi import AtamaDegisikligi, DogrulamaServisi, SurumTaslakDegilError
from tests.conftest import pg_yoksa_atla

GECE = 1
KAPI = 1


def test_kural_kapsamlari_sdd_5_5_ile_tutarli() -> None:
    """H1-H8 ile S1,S5,S6,S6b,S7,S8 PENCERE; S2,S3,S4 DONEM_GENELI (SDD 5.5, surum 1.3)."""
    pencere_kimlikleri = [
        "H1",
        "H2",
        "H3",
        "H4",
        "H5",
        "H6",
        "H7",
        "H8",
        "S1",
        "S5",
        "S6",
        "S6b",
        "S7",
        "S8",
    ]
    donem_geneli_kimlikleri = ["S2", "S3", "S4"]
    for kimlik in pencere_kimlikleri:
        sinif = bul(kimlik)
        assert sinif is not None, kimlik
        assert sinif.kapsam == KuralKapsami.PENCERE, kimlik
    for kimlik in donem_geneli_kimlikleri:
        sinif = bul(kimlik)
        assert sinif is not None, kimlik
        assert sinif.kapsam == KuralKapsami.DONEM_GENELI, kimlik


def test_s2_pencereyle_sinirlanirsa_donem_genelindeki_yuku_yanlis_yonde_hesaplar() -> None:
    """Personel 1, degisiklik gununden (25) uzak on gunde (1-10) zaten donem
    genelinin tavaninda - +-7 gunluk bir pencere bu on golgeyi hic gormez.

    Donem geneli (dogru) atamalarla degerlendirilince 11. gece eklemek
    cezayi arttirir (+1); yalnizca pencereyle (yanlis) degerlendirilince
    ayni degisiklik cezayi azaltiyormus gibi gorunur (-1) - SDD 5.5'in
    S2/S3/S4'u DONEM_GENELI olarak isaretlemesinin sebebi tam olarak bu
    yanlis yon hatasidir.
    """
    vardiya_tipleri = {GECE: VardiyaTipiBilgisi(GECE, time(0, 0), time(8, 0), 8, True)}
    gorev_noktalari = {KAPI: GorevNoktasiBilgisi(KAPI)}
    personel = {
        1: PersonelBilgisi(1, date(2026, 1, 1), None, frozenset(), haftalik_hedef_saat=40),
        2: PersonelBilgisi(2, date(2026, 1, 1), None, frozenset(), haftalik_hedef_saat=40),
    }
    baglam = Baglam(
        vardiya_tipleri=vardiya_tipleri,
        gorev_noktalari=gorev_noktalari,
        personel=personel,
        donem_baslangic=date(2026, 1, 1),
        donem_bitis=date(2026, 1, 31),
    )
    for i in range(10):
        baglam.talep[(date(2026, 1, 1 + i), GECE, KAPI)] = 1
    kural = S2GeceAdaleti(parametreler={}, agirlik=2)

    degisiklik_gunu = date(2026, 1, 25)
    on_gece = [AtamaKaydi(1, date(2026, 1, 1 + i), GECE, KAPI) for i in range(10)]
    yeni_gece = AtamaKaydi(1, degisiklik_gunu, GECE, KAPI)

    def _ceza(ihlaller: list, personel_id: int) -> float:
        return sum(i.ceza or 0.0 for i in ihlaller if i.personel_id == personel_id)

    # Donem geneli (dogru): 10 -> 11 gece, personel zaten tavanin uzerinde -> ceza artar.
    ceza_once_donem = _ceza(kural.dogrula(on_gece, baglam), 1)
    ceza_sonra_donem = _ceza(kural.dogrula([*on_gece, yeni_gece], baglam), 1)
    assert ceza_sonra_donem - ceza_once_donem == 1

    # Yalnizca pencere (+-7 gun, degisiklik gunu merkezli): on gecenin hicbiri
    # pencereye girmiyor, yeni gece ise giriyor -> 0 -> 1, tavanin cok altinda
    # kalindigi icin ceza AZALIYORMUS gibi gorunur (yanlis yon).
    ceza_once_pencere = _ceza(kural.dogrula([], baglam), 1)
    ceza_sonra_pencere = _ceza(kural.dogrula([yeni_gece], baglam), 1)
    assert ceza_sonra_pencere - ceza_once_pencere == -1

    assert (ceza_sonra_donem - ceza_once_donem) != (ceza_sonra_pencere - ceza_once_pencere)


@pytest.fixture
def istemci_kurulum() -> dict:
    pg_yoksa_atla()
    on_ek = uuid.uuid4().hex[:8]
    oturum = OturumYerel()
    try:
        vardiya_aksam = VardiyaTipi(
            ad=f"Aksam-{on_ek}",
            baslangic_saati=time(16, 0),
            bitis_saati=time(0, 0),
            sure_saat=8,
            gece_mi=False,
        )
        vardiya_gunduz = VardiyaTipi(
            ad=f"Gunduz-{on_ek}",
            baslangic_saati=time(8, 0),
            bitis_saati=time(16, 0),
            sure_saat=8,
            gece_mi=False,
        )
        nokta = GorevNoktasi(ad=f"Nokta-{on_ek}")
        oturum.add_all([vardiya_aksam, vardiya_gunduz, nokta])
        oturum.flush()
        oturum.commit()
        return {
            "on_ek": on_ek,
            "aksam_id": vardiya_aksam.vardiya_tipi_id,
            "gunduz_id": vardiya_gunduz.vardiya_tipi_id,
            "nokta_id": nokta.nokta_id,
        }
    finally:
        oturum.close()


def _taslak_surum_olustur(on_ek: str, baslangic: date, bitis: date) -> tuple[int, int]:
    oturum = OturumYerel()
    try:
        donem = Donem(
            baslangic_tarihi=baslangic,
            bitis_tarihi=bitis,
            tercih_son_tarihi=baslangic - timedelta(days=7),
        )
        oturum.add(donem)
        oturum.flush()
        surum = CizelgeSurumu(donem_id=donem.donem_id, surum_no=1, durum=CizelgeSurumuDurumu.TASLAK)
        oturum.add(surum)
        oturum.commit()
        return donem.donem_id, surum.surum_id
    finally:
        oturum.close()


def test_dogrula_zorunlu_kisit_ihlalini_reddeder(istemci_kurulum: dict) -> None:
    """H2 (asgari dinlenme): aksam vardiyasi (16-24) biten bir gunun ertesi
    gunune gunduz vardiyasi (08-16) atamak 8 saatlik dinlenme birakir,
    varsayilan asgari 16 saatin altinda - kabul_edilebilir False olmali."""
    on_ek = istemci_kurulum["on_ek"]
    aksam_id, gunduz_id, nokta_id = (
        istemci_kurulum["aksam_id"],
        istemci_kurulum["gunduz_id"],
        istemci_kurulum["nokta_id"],
    )
    baslangic = date(2026, 7, 6)  # Pazartesi
    bitis = baslangic + timedelta(days=13)
    _donem_id, surum_id = _taslak_surum_olustur(on_ek, baslangic, bitis)

    oturum = OturumYerel()
    try:
        personel = Personel(
            ad_soyad=f"H2 Test-{on_ek}",
            sicil_no=f"DOGRULA-H2-{on_ek}",
            haftalik_hedef_saat=40,
            aktif_baslangic=date(2026, 1, 1),
        )
        oturum.add(personel)
        oturum.flush()
        oturum.add(
            Atama(
                surum_id=surum_id,
                personel_id=personel.personel_id,
                tarih=baslangic,
                vardiya_tipi_id=aksam_id,
                nokta_id=nokta_id,
                kaynak=AtamaKaynagi.COZUCU,
            )
        )
        oturum.commit()
        personel_id = personel.personel_id
    finally:
        oturum.close()

    oturum = OturumYerel()
    try:
        servis = DogrulamaServisi(oturum)
        degisiklik = AtamaDegisikligi(
            surum_id=surum_id,
            personel_id=personel_id,
            tarih=baslangic + timedelta(days=1),
            vardiya_tipi_id=gunduz_id,
            nokta_id=nokta_id,
        )
        sonuc = servis.dogrula(degisiklik)
        assert sonuc is not None
        assert sonuc.kabul_edilebilir is False
        assert any(i.kural_kimlik == "H2" for i in sonuc.zorunlu_ihlaller)

        uygulama_sonucu = servis.uygula(degisiklik)
        assert uygulama_sonucu is not None
        assert uygulama_sonucu.kabul_edilebilir is False
    finally:
        oturum.close()

    oturum = OturumYerel()
    try:
        atamalar = (
            oturum.execute(
                select(Atama).where(
                    Atama.surum_id == surum_id, Atama.tarih == baslangic + timedelta(days=1)
                )
            )
            .scalars()
            .all()
        )
        assert atamalar == []  # reddedilen degisiklik kalici olarak yazilmamis olmali
    finally:
        oturum.close()


def test_dogrula_yayinlanmis_surumde_409(istemci_kurulum: dict) -> None:
    on_ek = istemci_kurulum["on_ek"]
    gunduz_id, nokta_id = istemci_kurulum["gunduz_id"], istemci_kurulum["nokta_id"]
    baslangic = date(2026, 7, 20)
    bitis = baslangic + timedelta(days=6)
    _donem_id, surum_id = _taslak_surum_olustur(on_ek, baslangic, bitis)

    oturum = OturumYerel()
    try:
        surum = oturum.get(CizelgeSurumu, surum_id)
        assert surum is not None
        surum.durum = CizelgeSurumuDurumu.YAYINLANDI
        oturum.commit()
        personel = Personel(
            ad_soyad=f"Yayin Test-{on_ek}",
            sicil_no=f"DOGRULA-YAYIN-{on_ek}",
            haftalik_hedef_saat=40,
            aktif_baslangic=date(2026, 1, 1),
        )
        oturum.add(personel)
        oturum.commit()
        personel_id = personel.personel_id
    finally:
        oturum.close()

    oturum = OturumYerel()
    try:
        servis = DogrulamaServisi(oturum)
        degisiklik = AtamaDegisikligi(
            surum_id=surum_id,
            personel_id=personel_id,
            tarih=baslangic,
            vardiya_tipi_id=gunduz_id,
            nokta_id=nokta_id,
        )
        with pytest.raises(SurumTaslakDegilError):
            servis.dogrula(degisiklik)
    finally:
        oturum.close()


def test_dogrula_cozuldu_surumde_duzenlenebilir(istemci_kurulum: dict) -> None:
    """TD-8 (SRS): yalnizca 'yayinlandi' salt okunurdur. Bir cozum isi bitince
    surum 'cozuldu' olur (bkz. cozum_servisi.py) ve kullanicinin bunun
    uzerinde hala elle duzenleme yapabilmesi gerekir - Gun 10'da manuel
    tarayici testinde bulunan bir regresyon (ilk yazimda yalnizca 'taslak'
    izin veriliyordu, 'cozuldu' 409 donuyordu)."""
    on_ek = istemci_kurulum["on_ek"]
    gunduz_id, nokta_id = istemci_kurulum["gunduz_id"], istemci_kurulum["nokta_id"]
    baslangic = date(2026, 7, 27)
    bitis = baslangic + timedelta(days=6)
    _donem_id, surum_id = _taslak_surum_olustur(on_ek, baslangic, bitis)

    oturum = OturumYerel()
    try:
        surum = oturum.get(CizelgeSurumu, surum_id)
        assert surum is not None
        surum.durum = CizelgeSurumuDurumu.COZULDU
        personel = Personel(
            ad_soyad=f"Cozuldu Test-{on_ek}",
            sicil_no=f"DOGRULA-COZULDU-{on_ek}",
            haftalik_hedef_saat=40,
            aktif_baslangic=date(2026, 1, 1),
        )
        oturum.add(personel)
        oturum.commit()
        personel_id = personel.personel_id
    finally:
        oturum.close()

    oturum = OturumYerel()
    try:
        servis = DogrulamaServisi(oturum)
        degisiklik = AtamaDegisikligi(
            surum_id=surum_id,
            personel_id=personel_id,
            tarih=baslangic,
            vardiya_tipi_id=gunduz_id,
            nokta_id=nokta_id,
        )
        sonuc = servis.uygula(degisiklik)
        assert sonuc is not None
        assert sonuc.kabul_edilebilir is True
        oturum.commit()
    finally:
        oturum.close()

    oturum = OturumYerel()
    try:
        atamalar = (
            oturum.execute(
                select(Atama).where(Atama.surum_id == surum_id, Atama.personel_id == personel_id)
            )
            .scalars()
            .all()
        )
        assert len(atamalar) == 1
        assert atamalar[0].kaynak == AtamaKaynagi.MANUEL
    finally:
        oturum.close()


def test_dogrula_bulunamayan_surumde_none_doner() -> None:
    pg_yoksa_atla()
    oturum = OturumYerel()
    try:
        servis = DogrulamaServisi(oturum)
        degisiklik = AtamaDegisikligi(
            surum_id=999999,
            personel_id=1,
            tarih=date(2026, 1, 1),
            vardiya_tipi_id=1,
            nokta_id=1,
        )
        assert servis.dogrula(degisiklik) is None
    finally:
        oturum.close()
