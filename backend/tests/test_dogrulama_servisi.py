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
from app.models.kural import Kural, KuralTipi
from app.models.sonuc import Atama, AtamaKaynagi, CizelgeSurumu, CizelgeSurumuDurumu, Donem
from app.models.tanim import GorevNoktasi, GunTipi, Personel, Talep, VardiyaTipi
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


def _kurali_garantile(
    oturum, kimlik: str, tip: KuralTipi, parametreler: dict, agirlik: int | None
) -> None:  # noqa: ANN001 - Session
    """Kuralin tabloda ve AKTIF oldugundan emin olur.

    `kural.kimlik` global benzersiz ve tablo butun testlerce paylasiliyor;
    senaryo kuran testler onu bosaltiyor (veri_temizligi.TEMIZLIK_SIRASI).
    Bu testler eskiden tablonun BASKA testlerden ya da demo verisinden
    kalan icerigine guveniyordu - yani siraya bagli olarak tesadufen
    geciyorlardi. Olculen sey kuralin kendisi oldugunda, kurali testin
    kurmasi gerekir.
    """
    mevcut = oturum.execute(select(Kural).where(Kural.kimlik == kimlik)).scalar_one_or_none()
    if mevcut is None:
        oturum.add(
            Kural(
                kimlik=kimlik,
                tip=tip,
                parametreler=parametreler,
                agirlik=agirlik,
                aktif=True,
            )
        )
    else:
        mevcut.tip = tip
        mevcut.parametreler = parametreler
        mevcut.agirlik = agirlik
        mevcut.aktif = True
    oturum.flush()


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
        # Olculen sey H2; kurali testin kendisi kurar (bkz. _kurali_garantile).
        _kurali_garantile(oturum, "H2", KuralTipi.ZORUNLU, {"asgari_dinlenme_saati": 16}, None)
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


def test_dogrula_ustan_uca_bir_noktayi_bosaltip_digerini_tasirsa_uyari_verir(
    istemci_kurulum: dict,
) -> None:
    """Bildirilen hata, DogrulamaServisi.dogrula UZERINDEN uctan uca:

    Vardiya Seflligi 1/1, Guvenlik 2/2 dolu bir aksamda, sefi Guvenlik'e
    cekmek onceden `kabul_edilebilir=True, ceza_degisimi hicbir sey
    soylemiyor` doenduruyordu - kullanici hicbir uyari gormeden degisikligi
    yapabiliyordu. Simdi:
      - degisiklik yine kabul edilir (S1 alt siniri esnek, urun karari),
      - `uyarilar` iki cumle tasir: Seflik acikta / Guvenlik'te fazla,
      - `ceza_dokumu`'nde S1 kalemi AGIRLIKLI farkiyla gorunur.
    """
    on_ek = istemci_kurulum["on_ek"]
    aksam_id, nokta_id = istemci_kurulum["aksam_id"], istemci_kurulum["nokta_id"]
    # istemci_kurulum'daki `nokta_id` Guvenlik rolunu oynar; ikinci bir
    # nokta Seflik rolunu oynar.
    baslangic = date(2026, 8, 3)  # Pazartesi
    bitis = baslangic + timedelta(days=6)
    donem_id, surum_id = _taslak_surum_olustur(on_ek, baslangic, bitis)

    oturum = OturumYerel()
    try:
        seflik = GorevNoktasi(ad=f"Seflik-{on_ek}")
        oturum.add(seflik)
        oturum.flush()
        seflik_id = seflik.nokta_id

        oturum.add_all(
            [
                Talep(
                    nokta_id=seflik_id,
                    baslangic=time(16, 0),
                    bitis=time(0, 0),
                    gun_tipi=GunTipi.HAFTA_ICI,
                    tarih=None,
                    gereken_sayi=1,
                ),
                Talep(
                    nokta_id=nokta_id,
                    baslangic=time(16, 0),
                    bitis=time(0, 0),
                    gun_tipi=GunTipi.HAFTA_ICI,
                    tarih=None,
                    gereken_sayi=2,
                ),
            ]
        )
        _kurali_garantile(oturum, "S1", KuralTipi.ESNEK, {}, 10000)

        sef = Personel(
            ad_soyad=f"Sef-{on_ek}",
            sicil_no=f"DOGRULA-SEF-{on_ek}",
            haftalik_hedef_saat=40,
            aktif_baslangic=date(2026, 1, 1),
        )
        g1 = Personel(
            ad_soyad=f"G1-{on_ek}",
            sicil_no=f"DOGRULA-G1-{on_ek}",
            haftalik_hedef_saat=40,
            aktif_baslangic=date(2026, 1, 1),
        )
        g2 = Personel(
            ad_soyad=f"G2-{on_ek}",
            sicil_no=f"DOGRULA-G2-{on_ek}",
            haftalik_hedef_saat=40,
            aktif_baslangic=date(2026, 1, 1),
        )
        oturum.add_all([sef, g1, g2])
        oturum.flush()

        oturum.add_all(
            [
                Atama(
                    surum_id=surum_id,
                    personel_id=sef.personel_id,
                    tarih=baslangic,
                    vardiya_tipi_id=aksam_id,
                    nokta_id=seflik_id,
                    kaynak=AtamaKaynagi.COZUCU,
                ),
                Atama(
                    surum_id=surum_id,
                    personel_id=g1.personel_id,
                    tarih=baslangic,
                    vardiya_tipi_id=aksam_id,
                    nokta_id=nokta_id,
                    kaynak=AtamaKaynagi.COZUCU,
                ),
                Atama(
                    surum_id=surum_id,
                    personel_id=g2.personel_id,
                    tarih=baslangic,
                    vardiya_tipi_id=aksam_id,
                    nokta_id=nokta_id,
                    kaynak=AtamaKaynagi.COZUCU,
                ),
            ]
        )
        oturum.commit()
        sef_id = sef.personel_id
    finally:
        oturum.close()

    oturum = OturumYerel()
    try:
        sonuc = DogrulamaServisi(oturum).dogrula(
            AtamaDegisikligi(
                surum_id=surum_id,
                personel_id=sef_id,
                tarih=baslangic,
                vardiya_tipi_id=aksam_id,
                nokta_id=nokta_id,
            )
        )
    finally:
        oturum.close()

    assert sonuc is not None
    assert sonuc.kabul_edilebilir is True  # S1 alt siniri esnek: engel degil
    assert sonuc.zorunlu_ihlaller == []

    uyari_metinleri = [u.aciklama for u in sonuc.uyarilar]
    assert any("eksik" in m for m in uyari_metinleri), uyari_metinleri
    assert any("fazla" in m for m in uyari_metinleri), uyari_metinleri

    s1_kalemi = next(k for k in sonuc.ceza_dokumu if k.kural_kimlik == "S1")
    assert s1_kalemi.agirlik == 10000
    # S1 artik KISI-SAAT olcuyor (SRS 4.3): sekiz saatlik blokta bir kisilik
    # acik sekiz birim eder. Fazla kadro ceza uretmez (uyari), bu yuzden
    # fark yalnizca eksikten gelir: 8 x 10000.
    assert s1_kalemi.ham_fark == 8
    assert s1_kalemi.agirlikli_fark == 80000


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


# --- S1'in iki yarisi (11.08.2026 hata bildirimi) ---------------------------


_S1_PZT = date(2026, 2, 2)
_S1_AKSAM = 3
_S1_SEFLIK = 10
_S1_GUVENLIK = 20


def _s1_baglami() -> Baglam:
    """Pazartesi aksami: Vardiya Sefligi 1 kisi, Guvenlik 2 kisi."""
    baglam = Baglam(
        vardiya_tipleri={
            _S1_AKSAM: VardiyaTipiBilgisi(_S1_AKSAM, time(16, 0), time(0, 0), 8, False, ad="Akşam")
        },
        gorev_noktalari={
            _S1_SEFLIK: GorevNoktasiBilgisi(_S1_SEFLIK, ad="Vardiya Şefliği"),
            _S1_GUVENLIK: GorevNoktasiBilgisi(_S1_GUVENLIK, ad="Güvenlik"),
        },
        personel={
            p: PersonelBilgisi(p, date(2026, 1, 1), None, frozenset(), haftalik_hedef_saat=40)
            for p in (1, 2, 3, 4)
        },
        donem_baslangic=_S1_PZT,
        donem_bitis=_S1_PZT,
    )
    # S1 SAAT ekseninde calisiyor: Aksam blogunun kapsadigi 16..23
    # saatlerinin her birine ayni talep yazilir (SRS 4.3).
    for saat in range(16, 24):
        baglam.talep_saat[(_S1_PZT, saat, _S1_SEFLIK)] = 1
        baglam.talep_saat[(_S1_PZT, saat, _S1_GUVENLIK)] = 2
    baglam.talep[(_S1_PZT, _S1_AKSAM, _S1_SEFLIK)] = 1
    baglam.talep[(_S1_PZT, _S1_AKSAM, _S1_GUVENLIK)] = 2
    return baglam


def test_s1_talepten_fazla_kadroyu_gorur() -> None:
    """Bildirilen hata: bir noktaya talepten fazla kisi yazmak sessizce
    kabul ediliyordu.

    `modele_ekle` ayni kisiti cozucuye ZORUNLU olarak ekliyor
    (`Σ_p x <= talep`), `dogrula` ise yalnizca alt sinira bakiyordu. Iki
    yorumlayicinin ayrismasi SDD 3.2.1'e gore yazilim hatasidir.
    """
    from app.kurallar.esnek import S1TalepKarsilama

    baglam = _s1_baglami()
    kural = S1TalepKarsilama(parametreler={}, agirlik=10000)

    # Sef sefliginden guvenlige cekiliyor: Seflik 0/1, Guvenlik 3/2.
    bozuk = [
        AtamaKaydi(1, _S1_PZT, _S1_AKSAM, _S1_GUVENLIK),
        AtamaKaydi(2, _S1_PZT, _S1_AKSAM, _S1_GUVENLIK),
        AtamaKaydi(3, _S1_PZT, _S1_AKSAM, _S1_GUVENLIK),
    ]
    ihlaller = kural.dogrula(bozuk, baglam)
    metinler = [i.aciklama for i in ihlaller]

    assert any("fazla" in m for m in metinler), metinler
    assert any("eksik" in m for m in metinler), metinler


def test_fazla_kadro_ceza_uretmez_uyari_uretir() -> None:
    """Fazla kadronun cezasi YOKTUR ve olmamalidir.

    SRS 4.4'teki amac fonksiyonunda fazla kadroya karsilik gelen bir terim
    bulunmuyor (cozucu tarafinda kisit, ceza degil). Buraya bir sayi
    uydurmak, cozucunun hicbir zaman hesaplamayacagi bir buyuklugu ceza
    dokumune sokar ve iki yorumlayici ayni cizelge icin farkli toplam
    uretirdi.
    """
    from app.kurallar.esnek import S1TalepKarsilama

    baglam = _s1_baglami()
    kural = S1TalepKarsilama(parametreler={}, agirlik=10000)

    # Seflik tam dolu, Guvenlik'te bir fazla: TEK sapma fazla kadro.
    fazla = [
        AtamaKaydi(1, _S1_PZT, _S1_AKSAM, _S1_SEFLIK),
        AtamaKaydi(2, _S1_PZT, _S1_AKSAM, _S1_GUVENLIK),
        AtamaKaydi(3, _S1_PZT, _S1_AKSAM, _S1_GUVENLIK),
        AtamaKaydi(4, _S1_PZT, _S1_AKSAM, _S1_GUVENLIK),
    ]
    ihlaller = kural.dogrula(fazla, baglam)
    assert len(ihlaller) == 1
    assert "fazla" in ihlaller[0].aciklama
    assert ihlaller[0].ceza is None
    assert sum(i.ceza or 0.0 for i in ihlaller) == 0.0


def test_s1_metni_kimlik_degil_ad_tasir() -> None:
    """NFR-5: mesajlar operasyon diliyle. Eski metin "3 nolu vardiyada 2 nolu
    noktada" diyordu; o sayilar veritabani kimlikleri."""
    from app.kurallar.esnek import S1TalepKarsilama

    baglam = _s1_baglami()
    ihlaller = S1TalepKarsilama(parametreler={}, agirlik=1).dogrula([], baglam)
    metinler = " ".join(i.aciklama for i in ihlaller)

    assert "Vardiya Şefliği" in metinler
    assert "16.00–24.00" in metinler
    assert "nolu" not in metinler
