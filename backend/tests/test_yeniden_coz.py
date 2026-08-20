"""SDD 5.6 (yeniden_coz) ve TD-8 (surum durum gecisleri) testleri (Sprint 2 Gun 11).

Canli bir PostgreSQL gerektirir; CozumServisi.baslat() gercek bir
multiprocessing.Process baslattigi icin bu testler islerin bitmesini
bekleyerek (poll) calisir.
"""

import uuid
from datetime import date, time, timedelta

import pytest
from pydantic import ValidationError
from sqlalchemy import select

from app.db import OturumYerel
from app.models.kural import Kural, KuralTipi
from app.models.sonuc import Atama, CizelgeSurumu, CizelgeSurumuDurumu, CozumIsiDurumu, Donem
from app.models.tanim import GorevNoktasi, GunTipi, Personel, Talep
from app.repositories.sonuc import CizelgeSurumuDeposu, CozumIsiDeposu
from app.schemas.cozum import CozumBaslatIstek
from app.services.cozum_servisi import CozumServisi
from tests.conftest import isi_calistir_ve_bekle, pg_yoksa_atla


def _standart_kurallari_ekle(oturum: OturumYerel) -> None:
    if oturum.execute(select(Kural).where(Kural.kimlik == "H1")).scalar_one_or_none():
        return
    tanimlar = [
        ("H1", KuralTipi.ZORUNLU, {}, None),
        ("H2", KuralTipi.ZORUNLU, {"asgari_dinlenme_saati": 16}, None),
        ("H3", KuralTipi.ZORUNLU, {"azami_ardisik_gece": 3}, None),
        ("H4", KuralTipi.ZORUNLU, {"azami_ardisik_calisma_gunu": 6}, None),
        ("H5", KuralTipi.ZORUNLU, {"haftalik_mutlak_tavan": 66}, None),
        ("H6", KuralTipi.ZORUNLU, {"haftalik_asgari_izin_gunu": 1}, None),
        ("H7", KuralTipi.ZORUNLU, {}, None),
        ("H8", KuralTipi.ZORUNLU, {}, None),
        ("S1", KuralTipi.ESNEK, {}, 1000),
        ("S2", KuralTipi.ESNEK, {}, 5),
        ("S3", KuralTipi.ESNEK, {}, 5),
        ("S4", KuralTipi.ESNEK, {}, 3),
        ("S5", KuralTipi.ESNEK, {}, 2),
        ("S6", KuralTipi.ESNEK, {}, 10),
        ("S6b", KuralTipi.ESNEK, {}, 6),
        ("S7", KuralTipi.ESNEK, {}, 2),
        ("S8", KuralTipi.ESNEK, {}, 8),
    ]
    for kimlik, tip, parametreler, agirlik in tanimlar:
        oturum.add(Kural(kimlik=kimlik, tip=tip, parametreler=parametreler, agirlik=agirlik))


@pytest.fixture
def kurulum() -> dict:
    pg_yoksa_atla()
    on_ek = uuid.uuid4().hex[:8]
    oturum = OturumYerel()
    try:
        nokta = GorevNoktasi(ad=f"Nokta-{on_ek}")
        oturum.add_all([nokta])
        _standart_kurallari_ekle(oturum)
        oturum.flush()

        baslangic = date(2026, 9, 7)  # Pazartesi
        bitis = baslangic + timedelta(days=6)
        personel_satirlari = [
            Personel(
                ad_soyad=f"YC Test P{i}-{on_ek}",
                sicil_no=f"YENIDEN-COZ-{on_ek}-{i}",
                haftalik_hedef_saat=40,
                aktif_baslangic=date(2026, 1, 1),
            )
            for i in range(1, 3)
        ]
        oturum.add_all(personel_satirlari)
        for gun_ofset in range(7):
            oturum.add(
                Talep(
                    nokta_id=nokta.nokta_id,
                    baslangic=time(8, 0),
                    bitis=time(16, 0),
                    gun_tipi=GunTipi.HAFTA_ICI if gun_ofset < 5 else GunTipi.HAFTA_SONU,
                    tarih=baslangic + timedelta(days=gun_ofset),
                    gereken_sayi=1,
                )
            )
        donem = Donem(
            baslangic_tarihi=baslangic,
            bitis_tarihi=bitis,
            tercih_son_tarihi=baslangic - timedelta(days=7),
        )
        oturum.add(donem)
        oturum.commit()
        return {
            "on_ek": on_ek,
            "nokta_id": nokta.nokta_id,
            "donem_id": donem.donem_id,
            "personel_idleri": [p.personel_id for p in personel_satirlari],
        }
    finally:
        oturum.close()


def test_yeniden_coz_taslagi_onceki_surume_baglar_ve_kilitli_atamayi_korur(
    kurulum: dict,
) -> None:
    donem_id = kurulum["donem_id"]
    nokta_id = kurulum["nokta_id"]

    # 1) Ilk cozum.
    oturum = OturumYerel()
    try:
        servis = CozumServisi(oturum)
        is_kaydi = servis.baslat(donem_id, zaman_limiti_saniye=20)
        assert is_kaydi is not None
        ilk_is_id = is_kaydi.is_id
        ilk_surum_id = is_kaydi.surum_id
        oturum.commit()
    finally:
        oturum.close()

    ilk_durum = isi_calistir_ve_bekle(ilk_is_id)
    assert ilk_durum in (CozumIsiDurumu.TAMAMLANDI, CozumIsiDurumu.UYARILI)

    # 2) Bu noktadaki bir atamayi kilitle, sonra surumu yayinla.
    oturum = OturumYerel()
    try:
        kilitlenecek = (
            oturum.execute(
                select(Atama).where(Atama.surum_id == ilk_surum_id, Atama.nokta_id == nokta_id)
            )
            .scalars()
            .first()
        )
        assert kilitlenecek is not None
        kilitlenecek.kilitli = True
        kilitli_anahtar = (
            kilitlenecek.personel_id,
            kilitlenecek.baslangic_zamani,
            kilitlenecek.bitis_zamani,
            kilitlenecek.nokta_id,
        )
        oturum.commit()

        surum = oturum.get(CizelgeSurumu, ilk_surum_id)
        assert surum is not None
        surum.durum = CizelgeSurumuDurumu.YAYINLANDI
        oturum.commit()
    finally:
        oturum.close()

    # 3) Yeniden coz (onceki_surum_id verilerek) - taslak turetilir + S8 tabanli cozulur.
    oturum = OturumYerel()
    try:
        servis = CozumServisi(oturum)
        yeni_is = servis.baslat(onceki_surum_id=ilk_surum_id, zaman_limiti_saniye=20)
        assert yeni_is is not None
        yeni_is_id = yeni_is.is_id
        yeni_surum_id = yeni_is.surum_id
        oturum.commit()
    finally:
        oturum.close()

    assert yeni_surum_id != ilk_surum_id

    yeni_durum = isi_calistir_ve_bekle(yeni_is_id)
    assert yeni_durum in (CozumIsiDurumu.TAMAMLANDI, CozumIsiDurumu.UYARILI)

    oturum = OturumYerel()
    try:
        yeni_surum = oturum.get(CizelgeSurumu, yeni_surum_id)
        assert yeni_surum is not None
        assert yeni_surum.onceki_surum_id == ilk_surum_id
        assert yeni_surum.durum == CizelgeSurumuDurumu.COZULDU

        is_kaydi = CozumIsiDeposu(oturum).getir(yeni_is_id)
        assert is_kaydi is not None
        assert is_kaydi.ceza_dokumu is not None
        assert "S8" in is_kaydi.ceza_dokumu  # onceki_atamalar aktif oldugunu kanitlar

        yeni_atama = oturum.execute(
            select(Atama).where(
                Atama.surum_id == yeni_surum_id,
                Atama.personel_id == kilitli_anahtar[0],
                Atama.baslangic_zamani == kilitli_anahtar[1],
            )
        ).scalar_one_or_none()
        assert yeni_atama is not None
        assert (
            yeni_atama.personel_id,
            yeni_atama.baslangic_zamani,
            yeni_atama.bitis_zamani,
            yeni_atama.nokta_id,
        ) == kilitli_anahtar
    finally:
        oturum.close()


def test_surum_yayinla_oncekini_arsive_alir(kurulum: dict) -> None:
    donem_id = kurulum["donem_id"]
    oturum = OturumYerel()
    try:
        depo = CizelgeSurumuDeposu(oturum)
        v1 = depo.olustur(donem_id=donem_id, surum_no=1, durum=CizelgeSurumuDurumu.COZULDU)
        oturum.flush()
        oturum.commit()
        v1_id = v1.surum_id

        v1_yayinlanan = depo.yayinla(v1_id)
        assert v1_yayinlanan is not None
        assert v1_yayinlanan.durum == CizelgeSurumuDurumu.YAYINLANDI
        assert v1_yayinlanan.yayin_zamani is not None
        oturum.commit()

        v2 = depo.taslak_turet(v1_id)
        assert v2 is not None
        v2.durum = CizelgeSurumuDurumu.COZULDU
        oturum.flush()
        oturum.commit()
        v2_id = v2.surum_id

        depo.yayinla(v2_id)
        oturum.commit()
    finally:
        oturum.close()

    oturum = OturumYerel()
    try:
        v1_guncel = oturum.get(CizelgeSurumu, v1_id)
        v2_guncel = oturum.get(CizelgeSurumu, v2_id)
        assert v1_guncel is not None
        assert v2_guncel is not None
        assert v1_guncel.durum == CizelgeSurumuDurumu.ARSIV
        assert v2_guncel.durum == CizelgeSurumuDurumu.YAYINLANDI
        assert v2_guncel.onceki_surum_id == v1_id
    finally:
        oturum.close()


def test_surum_taslak_turet_bulunamayan_surumde_none_doner() -> None:
    pg_yoksa_atla()
    oturum = OturumYerel()
    try:
        assert CizelgeSurumuDeposu(oturum).taslak_turet(999999) is None
    finally:
        oturum.close()


def test_cozum_baslat_donem_ve_onceki_surum_ikisi_de_eksikse_hata() -> None:
    with pytest.raises(ValidationError):
        CozumBaslatIstek()


def test_cozum_baslat_donem_ve_onceki_surum_ikisi_de_verilirse_hata() -> None:
    with pytest.raises(ValidationError):
        CozumBaslatIstek(donem_id=1, onceki_surum_id=2)


def test_yeniden_coz_atamasiz_onceki_surumden_s8_ceza_uretmez(kurulum: dict) -> None:
    """Tur 13 gerileme: bos taslak (atamasiz surum) tabaninda S8 sifir olmali.

    Onceki surumun atamasi yoksa `atama_depo.surume_gore_getir` bos LISTE
    doner, None degil. `baglam.onceki_atamalar`e ayrimsiz atanirsa S8
    "hicbir onceki atama yok" (None) ile "onceki cizelge bos" ([]) ayrimini
    kaybeder ve her atanan kisi-saati "onceki cizelgeden sapma" sayip
    cezalandirir - oysa karsilastirilacak bir onceki cizelge hic yok.
    """
    donem_id = kurulum["donem_id"]

    # 1) "Bos taslak" tabani: hic Atama satiri olmayan, dogrudan olusturulmus
    # bir surum. Cozucu hic calistirilmadan (ya da calisip hicbir atama
    # uretmeden) yayinlanan bir taslagi temsil eder.
    oturum = OturumYerel()
    try:
        depo = CizelgeSurumuDeposu(oturum)
        bos_surum = depo.olustur(
            donem_id=donem_id, surum_no=1, durum=CizelgeSurumuDurumu.YAYINLANDI
        )
        oturum.flush()
        oturum.commit()
        bos_surum_id = bos_surum.surum_id
    finally:
        oturum.close()

    # 2) Bu bos surumden yeniden coz.
    oturum = OturumYerel()
    try:
        servis = CozumServisi(oturum)
        yeni_is = servis.baslat(onceki_surum_id=bos_surum_id, zaman_limiti_saniye=20)
        assert yeni_is is not None
        yeni_is_id = yeni_is.is_id
        oturum.commit()
    finally:
        oturum.close()

    yeni_durum = isi_calistir_ve_bekle(yeni_is_id)
    assert yeni_durum in (CozumIsiDurumu.TAMAMLANDI, CozumIsiDurumu.UYARILI)

    oturum = OturumYerel()
    try:
        is_kaydi = CozumIsiDeposu(oturum).getir(yeni_is_id)
        assert is_kaydi is not None
        assert is_kaydi.ceza_dokumu is not None
        # S8 terimi modelde daima vardir (kural aktif); onceki cizelge
        # gercekten yoksa (bos taslak) katkisi sifir olmalidir.
        assert is_kaydi.ceza_dokumu.get("S8", 0) == 0
    finally:
        oturum.close()
