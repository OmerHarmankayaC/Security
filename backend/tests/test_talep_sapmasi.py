"""Talep sapmasinin kalici hale getirilmesi (11.08.2026 kapanis turu).

Iki sozlesme kilitleniyor:

1. MANUEL DUZENLEME SAPMA TABLOLARINI TAZELER. Once `kapsama_acigi`'ni
   yalnizca cozucu yaziyordu; elle bir atamayi kaldirmak gercek bir acik
   dogurdugu halde tablo bos kaliyordu. Sonucta Analiz'deki kapsama orani
   (SDD 5.7: "kapsama acigi tablosundan turetilir"), surum raporundaki
   acik sayisi ve disa aktarilan acik dosyasi elle duzenlenmis her
   surumde BAYAT oluyordu.

2. FAZLA KADRO KALICI. SRS 4.3 S1 ust siniri "zorunlu" tanimlar; asilmasi
   yalnizca manuel duzenlemeden gelebilir ve cizelgeye bakan herkesin
   gormesi gereken bir bilgidir.
"""

import uuid
from datetime import date, time, timedelta

import pytest
from sqlalchemy import select

from app.db import OturumYerel
from app.models.sonuc import (
    Atama,
    AtamaKaynagi,
    CizelgeSurumu,
    CizelgeSurumuDurumu,
    Donem,
    FazlaKadro,
    KapsamaAcigi,
)
from app.models.tanim import GorevNoktasi, GunTipi, Personel, Talep, VardiyaTipi
from app.services.dogrulama_servisi import AtamaDegisikligi, DogrulamaServisi
from app.services.talep_sapmasi import sapmalari_yenile
from tests.conftest import pg_yoksa_atla, senaryo_verisini_temizle


@pytest.fixture
def senaryo() -> dict:
    """Tek gunluk donem: Seflik 1 kisi, Guvenlik 2 kisi; ucu de dolu."""
    pg_yoksa_atla()
    on_ek = uuid.uuid4().hex[:8]
    gun = date(2026, 11, 2)  # Pazartesi
    oturum = OturumYerel()
    try:
        # `talep` donem-agnostik bir TANIM varligidir (SDD 4.2.1): tablodaki
        # her satir her donem icin cozulur. Baska bir testten ya da demo
        # verisinden kalan talep satirlari bu senaryonun sapma sayimina
        # karisir; bu yuzden senaryo kendi verisini temiz bir zeminde kurar
        # (tests/test_analiz_api.py ve test_calisan_api.py'deki ayni desen).
        senaryo_verisini_temizle(oturum)

        donem = Donem(
            baslangic_tarihi=gun,
            bitis_tarihi=gun,
            tercih_son_tarihi=gun - timedelta(days=7),
        )
        oturum.add(donem)
        vardiya = VardiyaTipi(
            ad=f"Aksam-{on_ek}",
            baslangic_saati=time(16, 0),
            bitis_saati=time(0, 0),
            sure_saat=8,
            gece_mi=False,
        )
        seflik = GorevNoktasi(ad=f"Seflik-{on_ek}")
        guvenlik = GorevNoktasi(ad=f"Guvenlik-{on_ek}")
        oturum.add_all([vardiya, seflik, guvenlik])
        oturum.flush()

        oturum.add_all(
            [
                Talep(
                    nokta_id=seflik.nokta_id,
                    baslangic=vardiya.baslangic_saati,
                    bitis=vardiya.bitis_saati,
                    gun_tipi=GunTipi.HAFTA_ICI,
                    tarih=None,
                    gereken_sayi=1,
                ),
                Talep(
                    nokta_id=guvenlik.nokta_id,
                    baslangic=vardiya.baslangic_saati,
                    bitis=vardiya.bitis_saati,
                    gun_tipi=GunTipi.HAFTA_ICI,
                    tarih=None,
                    gereken_sayi=2,
                ),
            ]
        )

        kisiler = {}
        for etiket in ("sef", "g1", "g2"):
            p = Personel(
                ad_soyad=f"{etiket}-{on_ek}",
                sicil_no=f"SAPMA-{etiket}-{on_ek}",
                haftalik_hedef_saat=40,
                aktif_baslangic=date(2026, 1, 1),
            )
            oturum.add(p)
            oturum.flush()
            kisiler[etiket] = p.personel_id

        surum = CizelgeSurumu(
            donem_id=donem.donem_id, surum_no=1, durum=CizelgeSurumuDurumu.COZULDU
        )
        oturum.add(surum)
        oturum.flush()
        for etiket, nokta in (("sef", seflik), ("g1", guvenlik), ("g2", guvenlik)):
            oturum.add(
                Atama(
                    surum_id=surum.surum_id,
                    personel_id=kisiler[etiket],
                    tarih=gun,
                    vardiya_tipi_id=vardiya.vardiya_tipi_id,
                    nokta_id=nokta.nokta_id,
                    kaynak=AtamaKaynagi.COZUCU,
                )
            )
        oturum.commit()
        return {
            "gun": gun,
            "surum_id": surum.surum_id,
            "vardiya_id": vardiya.vardiya_tipi_id,
            "seflik_id": seflik.nokta_id,
            "guvenlik_id": guvenlik.nokta_id,
            **kisiler,
        }
    finally:
        oturum.close()


def _sapmalar(surum_id: int) -> tuple[int, int]:
    """(toplam eksik kisi, toplam fazla kisi)."""
    oturum = OturumYerel()
    try:
        eksik = (
            oturum.execute(select(KapsamaAcigi).where(KapsamaAcigi.surum_id == surum_id))
            .scalars()
            .all()
        )
        fazla = (
            oturum.execute(select(FazlaKadro).where(FazlaKadro.surum_id == surum_id))
            .scalars()
            .all()
        )
        return sum(e.eksik_sayi for e in eksik), sum(f.fazla_sayi for f in fazla)
    finally:
        oturum.close()


def test_elle_atama_kaldirmak_kapsama_acigini_tazeler(senaryo: dict) -> None:
    """Bulgunun kendisi: once bu tablo elle duzenlemede hic guncellenmiyordu."""
    oturum = OturumYerel()
    try:
        sapmalari_yenile(oturum, senaryo["surum_id"])
        oturum.commit()
    finally:
        oturum.close()
    assert _sapmalar(senaryo["surum_id"]) == (0, 0), "baslangicta tam kapsanmali"

    oturum = OturumYerel()
    try:
        DogrulamaServisi(oturum).uygula(
            AtamaDegisikligi(
                surum_id=senaryo["surum_id"],
                personel_id=senaryo["sef"],
                tarih=senaryo["gun"],
                vardiya_tipi_id=None,  # atamayi kaldir
                nokta_id=None,
            )
        )
        oturum.commit()
    finally:
        oturum.close()

    eksik, fazla = _sapmalar(senaryo["surum_id"])
    assert eksik == 1, "Seflik acikta kaldi; tablo bunu tasimali"
    assert fazla == 0


def test_elle_fazla_kadro_yazmak_kalici_iz_birakir(senaryo: dict) -> None:
    """Sizin senaryonuz: sefi Guvenlik'e cekmek -> Seflik 0/1, Guvenlik 3/2."""
    oturum = OturumYerel()
    try:
        DogrulamaServisi(oturum).uygula(
            AtamaDegisikligi(
                surum_id=senaryo["surum_id"],
                personel_id=senaryo["sef"],
                tarih=senaryo["gun"],
                vardiya_tipi_id=senaryo["vardiya_id"],
                nokta_id=senaryo["guvenlik_id"],
            )
        )
        oturum.commit()
    finally:
        oturum.close()

    eksik, fazla = _sapmalar(senaryo["surum_id"])
    assert eksik == 1, "Seflik acikta"
    assert fazla == 1, "Guvenlik'te talepten bir fazla"


def test_sapma_geri_alindiginda_satirlar_da_silinir(senaryo: dict) -> None:
    """Yenileme fark alip guncellemez, tabloyu BASTAN yazar; "artik gecerli
    olmayan ama silinmeyi unutulmus satir" bicimi boylece hic olusmaz."""
    oturum = OturumYerel()
    try:
        servis = DogrulamaServisi(oturum)
        servis.uygula(
            AtamaDegisikligi(
                surum_id=senaryo["surum_id"],
                personel_id=senaryo["sef"],
                tarih=senaryo["gun"],
                vardiya_tipi_id=senaryo["vardiya_id"],
                nokta_id=senaryo["guvenlik_id"],
            )
        )
        oturum.commit()
        assert _sapmalar(senaryo["surum_id"]) == (1, 1)

        servis.uygula(
            AtamaDegisikligi(
                surum_id=senaryo["surum_id"],
                personel_id=senaryo["sef"],
                tarih=senaryo["gun"],
                vardiya_tipi_id=senaryo["vardiya_id"],
                nokta_id=senaryo["seflik_id"],
            )
        )
        oturum.commit()
    finally:
        oturum.close()

    assert _sapmalar(senaryo["surum_id"]) == (0, 0)


def test_fazla_kadro_kapsama_oranini_bozmaz(senaryo: dict) -> None:
    """Kapsama orani "talebin ne kadari karsilandi" sorusunu yanitlar; fazla
    atama bir hucreyi daha iyi kapsamis olmaz. Iki sayi ayri durmali."""
    from app.services.analiz_servisi import AnalizServisi

    oturum = OturumYerel()
    try:
        # Yalnizca FAZLA kadro yarat: g1'i Seflik'e degil, ucuncu bir kisiyi
        # Guvenlik'e ekleyemedigimiz icin sefi tasiyoruz ve sonra Seflik'i
        # yeniden dolduramayiz - bu yuzden burada eksik de olusur. Olculen
        # sey oranin FAZLADAN etkilenmemesi: eksik 1 iken oran 2/3 olmali.
        DogrulamaServisi(oturum).uygula(
            AtamaDegisikligi(
                surum_id=senaryo["surum_id"],
                personel_id=senaryo["sef"],
                tarih=senaryo["gun"],
                vardiya_tipi_id=senaryo["vardiya_id"],
                nokta_id=senaryo["guvenlik_id"],
            )
        )
        oturum.commit()
        analiz = AnalizServisi(oturum).hesapla(senaryo["surum_id"])
    finally:
        oturum.close()

    assert analiz is not None
    # Toplam talep 3, eksik 1 -> 2/3. Fazla kadro (1) bu orana GIRMEZ.
    assert analiz.kapsama_orani == pytest.approx(2 / 3)
    assert analiz.toplam_fazla_kadro == 1
    assert len(analiz.fazla_kadro) == 1
    # Adlariyla birlikte gelir (NFR-5): ekran kimlik gostermez.
    assert analiz.fazla_kadro[0].nokta_ad.startswith("Guvenlik-")


def test_resmi_tatil_gunu_talebi_sifira_dusurmez() -> None:
    """FR-1.10'un sessiz tuzagi: tatil satiri olmayan bir matriste bir gunu
    resmi tatil isaretlemek o gunun TALEBINI SIFIRLAR.

    `talep_matrisini_coz` gun tipine karsilik gelen genel satiri bulamazsa
    hucreyi sonuca hic koymaz; kapsama acigi da olusmaz (talep sifirdir),
    dolayisiyla hata hicbir ekranda gorunmez. Ornek senaryo bu yuzden
    RESMI_TATIL satirlarini da uretir ve tatil gunu hafta sonuyla ayni
    azaltilmis kadroya duser (SRS 3.3.4).
    """
    from app.services.ornek_senaryo import talep_satirlarini_olustur
    from app.services.talep_cozucu import gun_tipi_belirle, talebi_saate_ac

    tatil = date(2026, 4, 23)  # Persembe
    hafta_ici = date(2026, 4, 22)  # Carsamba
    hafta_sonu = date(2026, 4, 25)  # Cumartesi
    assert gun_tipi_belirle(tatil, frozenset({tatil})) is GunTipi.RESMI_TATIL

    satirlar = [
        Talep(
            talep_id=i,
            nokta_id=t.nokta_index + 1,
            baslangic=t.baslangic,
            bitis=t.bitis,
            gun_tipi=t.gun_tipi,
            tarih=None,
            gereken_sayi=t.gereken_sayi,
        )
        for i, t in enumerate(talep_satirlarini_olustur(), start=1)
    ]
    cozulmus = talebi_saate_ac(satirlar, [hafta_ici, tatil, hafta_sonu], frozenset({tatil}))

    def gun_toplami(gun: date) -> int:
        return sum(v for (t, _, _), v in cozulmus.items() if t == gun)

    assert gun_toplami(tatil) > 0, "tatil gunu talebi sifirlanmamali"
    assert gun_toplami(tatil) == gun_toplami(hafta_sonu), "tatil hafta sonu kadrosuyla calisir"
    assert gun_toplami(tatil) < gun_toplami(hafta_ici), "tatilde kadro azaltilir"
