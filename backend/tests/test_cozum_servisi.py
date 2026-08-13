"""SDD 5.4 cozum isi durum makinesi testleri (Sprint 2 Gun 8).

Canli bir PostgreSQL gerektirir; CozumServisi.baslat() gercek bir
multiprocessing.Process baslattigi icin bu testler islerin bitmesini
bekleyerek (poll) calisir.
"""

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
from tests.conftest import isi_calistir_ve_bekle, pg_yoksa_atla


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
                    baslangic=time(8, 0),
                    bitis=time(16, 0),
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

    durum = isi_calistir_ve_bekle(is_id)
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
        # UST SINIR ARTIK ESNEK (K4, Tur 4): cozucu talebin uzerine
        # cikabilir ve bunun kucuk bir cezasi vardir (S1f, w1f=2). Bu
        # yuzden atama sayisi 7'ye SABIT DEGIL, en az 7'dir - her gunun
        # doldurulmus olmasi yeterli kosuldur. Once uzeri zorunlu kisitla
        # kapaliydi ve sayi tam 7 olurdu.
        #
        # Fazla kadronun kendisi bir hata degil: karisik uzunluklu
        # katalogda yapisaldir ve S1f onu kaydeder. Testin asil olctugu
        # sey asagida: BU noktada kapsama acigi yok.
        assert len(atamalar) >= 7
        assert {a.tarih for a in atamalar} == {baslangic + timedelta(days=i) for i in range(7)}
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


def test_on_kontrol_bulgusu_cozumu_dusurmez_cizelge_yine_uretilir(
    temel_kurulum: dict,
) -> None:
    """SDD 5.2 / SRS FR-5.2: ON KONTROL BULGUSU COZUMU ENGELLEMEZ.

    Iki kisilik havuzda izinlerin tam gun ortustugu bir gun, SDD 5.2'nin
    Kontrol 4'unun (nokta bazli musaitlik) yakalayacagi turden kesin bir
    bulgudur. Eskiden is bu durumda cozucu hic calistirilmadan
    `basarisiz` oluyordu; bu, "personel yetersizliginde cozumu reddetmek
    yerine cizelgeyi uret ve kapsama aciklarini goster" gereksinimini
    dogrudan ihlal ediyordu ve S1'in baskin agirlikli ESNEK hedef olarak
    tasarlanmasinin tek gerekcesini islevsiz birakiyordu.

    Beklenen yeni davranis: cizelge URETILIR, atamalar yazilir, acik
    kapsama acigi olarak raporlanir ve bulgu is kaydinda KALICI olur.

    Nokta, yalnizca bu iki kisinin sahip oldugu YENI bir yetkinlikle
    kisitlanir; aksi halde paylasilan test veritabanindaki ilgisiz (ve
    kisitsiz) diger personel de aday olup acigi kapatabilir.
    """
    on_ek = temel_kurulum["on_ek"]

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
                    baslangic=time(8, 0),
                    bitis=time(16, 0),
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

    durum = isi_calistir_ve_bekle(is_id)
    # Kadro yetersiz oldugu icin acik var: `uyarili`. `basarisiz` DEGIL -
    # isin dusmesinin tek mesru nedeni cozucunun modeli cozulemez
    # bulmasidir (FR-5.5).
    assert durum == CozumIsiDurumu.UYARILI

    oturum = OturumYerel()
    try:
        is_kaydi = CozumIsiDeposu(oturum).getir(is_id)
        assert is_kaydi is not None
        # Bulgu KAYBOLMAZ: sonucla birlikte gosterilebilmesi ve surum
        # raporunda kalmasi icin is kaydinda durur.
        assert is_kaydi.on_kontrol_bulgulari
        bulgu_metinleri = " ".join(b["aciklama"] for b in is_kaydi.on_kontrol_bulgulari)
        assert str(ortusen_gun) in bulgu_metinleri
        # Cizelge URETILDI: bulgunun isaret ettigi gun disinda atamalar var.
        atamalar = oturum.execute(select(Atama).where(Atama.surum_id == surum_id)).scalars().all()
        assert atamalar, "On kontrol bulgusu cizelgenin uretilmesini engellememeli"
        # Acik, kapsama acigi olarak raporlandi.
        acilar = (
            oturum.execute(select(KapsamaAcigi).where(KapsamaAcigi.surum_id == surum_id))
            .scalars()
            .all()
        )
        assert acilar, "Kapatilamayan talep kapsama acigi olarak raporlanmali"
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
