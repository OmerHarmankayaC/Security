"""SDD 5.4 cozum isi durum makinesi testleri (Sprint 2 Gun 8).

Canli bir PostgreSQL gerektirir; CozumServisi.baslat() gercek bir
multiprocessing.Process baslattigi icin bu testler islerin bitmesini
bekleyerek (poll) calisir.
"""

import time as zaman
import uuid
from datetime import date, time, timedelta

import pytest
from sqlalchemy import select

from app.db import OturumYerel
from app.models.girdi import Musaitlik, MusaitlikDilimi, MusaitlikTipi
from app.models.kural import Kural, KuralTipi
from app.models.sonuc import Atama, CozumIsiDurumu, Donem, KapsamaAcigi
from app.models.tanim import GorevNoktasi, GunTipi, Personel, Talep, VardiyaTipi, Yetkinlik
from app.repositories.sonuc import CozumIsiDeposu
from app.services.cozum_servisi import CozumServisi
from tests.conftest import pg_yoksa_atla

_SONUCLANMIS = (
    CozumIsiDurumu.TAMAMLANDI,
    CozumIsiDurumu.UYARILI,
    CozumIsiDurumu.BASARISIZ,
    CozumIsiDurumu.IPTAL,
)


def _bekle_ve_getir(is_id: int, *, zaman_asimi_saniye: float = 150) -> CozumIsiDurumu:
    baslangic = zaman.monotonic()
    while zaman.monotonic() - baslangic < zaman_asimi_saniye:
        oturum = OturumYerel()
        try:
            is_kaydi = CozumIsiDeposu(oturum).getir(is_id)
            if is_kaydi is not None and is_kaydi.durum in _SONUCLANMIS:
                return is_kaydi.durum
        finally:
            oturum.close()
        zaman.sleep(0.5)
    pytest.fail(f"Cozum isi {zaman_asimi_saniye} saniyede sonuclanmadi")


def _standart_kurallari_ekle(oturum: OturumYerel) -> None:
    """Idempotent: ayni test surecinde birden fazla fixture cagrisinda kural
    kimlik'lerinin benzersizlik kisitina takilmamak icin, zaten varsa atlar."""
    if oturum.execute(select(Kural).where(Kural.kimlik == "H1")).scalar_one_or_none():
        return
    tanimlar = [
        ("H1", KuralTipi.ZORUNLU, {}, None),
        ("H2", KuralTipi.ZORUNLU, {"asgari_dinlenme_saati": 16}, None),
        ("H3", KuralTipi.ZORUNLU, {"azami_ardisik_gece": 3}, None),
        ("H4", KuralTipi.ZORUNLU, {"azami_ardisik_calisma_gunu": 6}, None),
        ("H5", KuralTipi.ZORUNLU, {"azami_haftalik_saat": 45}, None),
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
def temel_kurulum() -> dict:
    pg_yoksa_atla()
    on_ek = uuid.uuid4().hex[:8]
    oturum = OturumYerel()
    try:
        vardiya_tipi = VardiyaTipi(
            ad=f"Gunduz-{on_ek}",
            baslangic_saati=time(8, 0),
            bitis_saati=time(16, 0),
            sure_saat=8,
            gece_mi=False,
        )
        nokta = GorevNoktasi(ad=f"Nokta-{on_ek}")
        oturum.add_all([vardiya_tipi, nokta])
        _standart_kurallari_ekle(oturum)
        oturum.flush()
        oturum.commit()
        return {
            "on_ek": on_ek,
            "vardiya_tipi_id": vardiya_tipi.vardiya_tipi_id,
            "nokta_id": nokta.nokta_id,
        }
    finally:
        oturum.close()


def test_cozum_kadro_yeterliyken_tamamlandi_doner_ve_atama_yazilir(temel_kurulum: dict) -> None:
    on_ek = temel_kurulum["on_ek"]
    vardiya_tipi_id = temel_kurulum["vardiya_tipi_id"]
    nokta_id = temel_kurulum["nokta_id"]

    baslangic = date(2026, 6, 1)
    bitis = baslangic + timedelta(days=6)
    oturum = OturumYerel()
    try:
        personel_satirlari = [
            Personel(
                ad_soyad=f"Test P{i}-{on_ek}",
                sicil_no=f"COZUM-YETERLI-{on_ek}-{i}",
                haftalik_hedef_saat=40,
                aktif_baslangic=date(2026, 1, 1),
            )
            for i in range(1, 4)
        ]
        oturum.add_all(personel_satirlari)
        for gun_ofset in range(7):
            oturum.add(
                Talep(
                    nokta_id=nokta_id,
                    vardiya_tipi_id=vardiya_tipi_id,
                    gun_tipi=GunTipi.HAFTA_ICI,
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
        donem_id = donem.donem_id

        servis = CozumServisi(oturum)
        is_kaydi = servis.baslat(donem_id, zaman_limiti_saniye=20)
        assert is_kaydi is not None
        is_id = is_kaydi.is_id
        surum_id = is_kaydi.surum_id
        oturum.commit()
    finally:
        oturum.close()

    durum = _bekle_ve_getir(is_id)
    # Paylasilan test veritabaninda baska testlerin biraktigi genel (tarihsiz)
    # talep satirlari (SDD 4.2.1 geregi haftaici gunlere gecerli sekilde
    # uygulanir) baska noktalarda ek talep dogurabilir; bu yuzden is genelinde
    # 'tamamlandi' yerine 'tamamlandi veya uyarili' kabul edilir. Asil kontrol,
    # BU testin kendi noktasinda kapsama acigi olmamasidir.
    assert durum in (CozumIsiDurumu.TAMAMLANDI, CozumIsiDurumu.UYARILI)

    oturum = OturumYerel()
    try:
        atamalar = (
            oturum.execute(
                select(Atama).where(Atama.surum_id == surum_id, Atama.nokta_id == nokta_id)
            )
            .scalars()
            .all()
        )
        assert len(atamalar) == 7  # her gun 1 kisi
        kapsama = (
            oturum.execute(
                select(KapsamaAcigi).where(
                    KapsamaAcigi.surum_id == surum_id, KapsamaAcigi.nokta_id == nokta_id
                )
            )
            .scalars()
            .all()
        )
        assert kapsama == []
    finally:
        oturum.close()


def test_cozum_on_kontrolde_yapisal_engel_varsa_cozmeden_basarisiz_doner(
    temel_kurulum: dict,
) -> None:
    """Iki kisilik havuzda izinlerin tam gun ortustugu bir gun, SDD 5.2'nin
    Kontrol 4'unun (nokta bazli musaitlik) yakalayacagi turden acik bir
    yapisal engeldir; SDD 5.4'e gore cozum isi bu durumda cozucuyu hic
    calistirmadan basarisiz olarak sonlanir (bkz. Sprint 2 Gun 7: on_kontrol
    yalnizca zaman-pencereli/kumulatif haftalik acikliklari kacirir, boyle
    tam-gunluk bir engeli degil).

    Nokta, yalnizca bu iki kisinin sahip oldugu YENI bir yetkinlikle
    kisitlanir; aksi halde paylasilan test veritabanindaki ilgisiz (ve
    kisitsiz) diger personel de aday olup acigi kapatabilir.
    """
    on_ek = temel_kurulum["on_ek"]
    vardiya_tipi_id = temel_kurulum["vardiya_tipi_id"]

    baslangic = date(2026, 6, 8)
    bitis = baslangic + timedelta(days=6)
    ortusen_gun = baslangic + timedelta(days=3)

    oturum = OturumYerel()
    try:
        yetkinlik = Yetkinlik(ad=f"OzelYetkinlik-{on_ek}")
        nokta = GorevNoktasi(ad=f"NoktaKisitli-{on_ek}")
        oturum.add_all([yetkinlik, nokta])
        oturum.flush()
        nokta.onkosul_yetkinlik_id = yetkinlik.yetkinlik_id
        nokta_id = nokta.nokta_id

        kisi_a = Personel(
            ad_soyad=f"Kisi A-{on_ek}",
            sicil_no=f"COZUM-ACIK-A-{on_ek}",
            haftalik_hedef_saat=40,
            aktif_baslangic=date(2026, 1, 1),
        )
        kisi_b = Personel(
            ad_soyad=f"Kisi B-{on_ek}",
            sicil_no=f"COZUM-ACIK-B-{on_ek}",
            haftalik_hedef_saat=40,
            aktif_baslangic=date(2026, 1, 1),
        )
        kisi_a.yetkinlikler = [yetkinlik]
        kisi_b.yetkinlikler = [yetkinlik]
        oturum.add_all([kisi_a, kisi_b])
        oturum.flush()

        oturum.add_all(
            [
                Musaitlik(
                    personel_id=kisi_a.personel_id,
                    baslangic_tarihi=baslangic,
                    bitis_tarihi=ortusen_gun,
                    dilim=MusaitlikDilimi.TAM_GUN,
                    tip=MusaitlikTipi.YILLIK_IZIN,
                ),
                Musaitlik(
                    personel_id=kisi_b.personel_id,
                    baslangic_tarihi=ortusen_gun,
                    bitis_tarihi=bitis,
                    dilim=MusaitlikDilimi.TAM_GUN,
                    tip=MusaitlikTipi.YILLIK_IZIN,
                ),
            ]
        )
        for gun_ofset in range(7):
            oturum.add(
                Talep(
                    nokta_id=nokta_id,
                    vardiya_tipi_id=vardiya_tipi_id,
                    gun_tipi=GunTipi.HAFTA_ICI,
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
        donem_id = donem.donem_id

        servis = CozumServisi(oturum)
        is_kaydi = servis.baslat(donem_id, zaman_limiti_saniye=20)
        assert is_kaydi is not None
        is_id = is_kaydi.is_id
        surum_id = is_kaydi.surum_id
        oturum.commit()
    finally:
        oturum.close()

    durum = _bekle_ve_getir(is_id)
    assert durum == CozumIsiDurumu.BASARISIZ

    oturum = OturumYerel()
    try:
        is_kaydi = CozumIsiDeposu(oturum).getir(is_id)
        assert is_kaydi is not None
        assert is_kaydi.hata_mesaji is not None
        assert str(ortusen_gun) in is_kaydi.hata_mesaji
        # Cozucu hic calistirilmadigi icin bu surume atama yazilmamis olmali.
        atamalar = oturum.execute(select(Atama).where(Atama.surum_id == surum_id)).scalars().all()
        assert atamalar == []
    finally:
        oturum.close()


def test_cozum_baslat_bulunamayan_donemde_none_doner() -> None:
    pg_yoksa_atla()
    oturum = OturumYerel()
    try:
        servis = CozumServisi(oturum)
        assert servis.baslat(999999) is None
    finally:
        oturum.close()
