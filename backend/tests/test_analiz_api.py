"""Analiz uc noktasi testleri (Sprint 3 Gun 12: SDD 5.7'deki metrikler,
SRS FR-8.x). Kucuk, elle kurulmus bir senaryo uzerinde her metrigin
beklenen degeri elle hesaplanip dogrulanir; canli PostgreSQL gerektirir.
"""

import uuid
from datetime import UTC, date, datetime, time, timedelta

import pytest
from fastapi.testclient import TestClient

from app.db import OturumYerel
from app.models.girdi import Tercih, TercihDurumu, TercihTipi
from app.models.sonuc import (
    Atama,
    AtamaKaynagi,
    CizelgeSurumu,
    CizelgeSurumuDurumu,
    CozumIsi,
    CozumIsiDurumu,
    Donem,
    KapsamaAcigi,
)
from app.models.tanim import GorevNoktasi, GunTipi, Personel, Talep
from tests.conftest import pg_yoksa_atla, senaryo_verisini_temizle, yetkili_istemci


@pytest.fixture
def istemci() -> TestClient:
    pg_yoksa_atla()
    return yetkili_istemci()


def _benzersiz(on_ek: str) -> str:
    return f"{on_ek}-{uuid.uuid4().hex[:8]}"


def test_analiz_bulunamayan_surumde_404(istemci: TestClient) -> None:
    assert istemci.get("/api/analiz/999999999").status_code == 404


def test_analiz_metrikleri_dogru_hesaplanir(istemci: TestClient) -> None:
    on_ek = _benzersiz("analiz")
    oturum = OturumYerel()
    try:
        # AnalizServisi'nin kapsama_orani ve saat_dagilimi/en_dengesiz
        # hesaplari sirasiyla TUM `talep` ve TUM `personel` tablosunu
        # kullanir (Talep, SDD 4.2.1 geregi donem-agnostik bir tanim
        # varligidir; saat_dagilimi da SDD 5.7'ye gore butun personeli
        # kapsar, yalniz o surume atananlari degil) - bu yuzden test,
        # kendi verisini baskasiyla karismadan olcebilmek icin once
        # ilgili tablolari temizler (bu projede tekrarlayan bir desen,
        # bkz. tests/test_agirlik_kalibrasyonu.py).
        senaryo_verisini_temizle(oturum)

        nokta = GorevNoktasi(ad=f"Nokta-{on_ek}")
        oturum.add(nokta)
        p1 = Personel(
            ad_soyad=f"P1-{on_ek}",
            sicil_no=_benzersiz("AN1"),
            haftalik_hedef_saat=40,
            aktif_baslangic=date(2026, 1, 1),
        )
        p2 = Personel(
            ad_soyad=f"P2-{on_ek}",
            sicil_no=_benzersiz("AN2"),
            haftalik_hedef_saat=40,
            aktif_baslangic=date(2026, 1, 1),
        )
        oturum.add_all([p1, p2])
        oturum.flush()

        # 7 gunluk donem, hafta ici gunduz 1, hafta sonu gece 1 talep.
        donem = Donem(
            baslangic_tarihi=date(2026, 9, 7),  # Pazartesi
            bitis_tarihi=date(2026, 9, 13),  # Pazar
            tercih_son_tarihi=date(2026, 8, 31),
        )
        oturum.add(donem)
        oturum.flush()
        oturum.add(
            Talep(
                nokta_id=nokta.nokta_id,
                baslangic=time(8, 0),
                bitis=time(16, 0),
                gun_tipi=GunTipi.HAFTA_ICI,
                tarih=None,
                gereken_sayi=1,
            )
        )
        oturum.add(
            Talep(
                nokta_id=nokta.nokta_id,
                baslangic=time(0, 0),
                bitis=time(8, 0),
                gun_tipi=GunTipi.HAFTA_SONU,
                tarih=None,
                gereken_sayi=1,
            )
        )

        surum = CizelgeSurumu(
            donem_id=donem.donem_id, surum_no=1, durum=CizelgeSurumuDurumu.COZULDU
        )
        oturum.add(surum)
        oturum.flush()

        # Hafta ici 5 gun gunduz -> P1'e atanmis (40 saat, tam hedef).
        for i in range(5):
            oturum.add(
                Atama(
                    surum_id=surum.surum_id,
                    personel_id=p1.personel_id,
                    baslangic_zamani=datetime.combine(
                        date(2026, 9, 7) + timedelta(days=i), time(8, 0)
                    ),
                    bitis_zamani=datetime.combine(
                        date(2026, 9, 7) + timedelta(days=i), time(16, 0)
                    ),
                    nokta_id=nokta.nokta_id,
                    kaynak=AtamaKaynagi.COZUCU,
                )
            )
        # Cumartesi gece -> P2'ye atanmis (8 saat); pazar gece ACIK (talep
        # karsilanmadi) - kapsama acigi kaydi.
        oturum.add(
            Atama(
                surum_id=surum.surum_id,
                personel_id=p2.personel_id,
                baslangic_zamani=datetime.combine(date(2026, 9, 12), time(0, 0)),
                bitis_zamani=datetime.combine(date(2026, 9, 12), time(8, 0)),
                nokta_id=nokta.nokta_id,
                kaynak=AtamaKaynagi.COZUCU,
            )
        )
        oturum.add(
            KapsamaAcigi(
                surum_id=surum.surum_id,
                tarih=date(2026, 9, 13),
                baslangic=time(0, 0),
                bitis=time(8, 0),
                nokta_id=nokta.nokta_id,
                eksik_sayi=1,
            )
        )

        # P1 icin onaylanmis bir calismama tercihi, PER 10'da (P1 o gun zaten
        # calisiyor - tercih KARSILANMADI).
        oturum.add(
            Tercih(
                personel_id=p1.personel_id,
                donem_id=donem.donem_id,
                tarih=date(2026, 9, 10),
                tip=TercihTipi.CALISMAMA,
                durum=TercihDurumu.ONAYLANDI,
            )
        )

        oturum.add(
            CozumIsi(
                surum_id=surum.surum_id,
                durum=CozumIsiDurumu.UYARILI,
                baslangic_zamani=datetime.now(UTC),
                bitis_zamani=datetime.now(UTC),
                zaman_limiti_saniye=60,
                en_iyi_ceza=1234,
                ceza_dokumu={"S1": 1000.0, "S2": 234.0},
                kural_anlik_goruntu={},
            )
        )

        oturum.commit()
        surum_id = surum.surum_id
        p1_id = p1.personel_id
        p2_id = p2.personel_id
    finally:
        oturum.rollback()
        oturum.close()

    yanit = istemci.get(f"/api/analiz/{surum_id}")
    assert yanit.status_code == 200
    govde = yanit.json()

    assert govde["surum_id"] == surum_id
    # Toplam talep: 5 hafta ici gunduz + 2 hafta sonu gece = 7; 1 eksik -> 6/7.
    assert govde["kapsama_orani"] == pytest.approx(6 / 7)

    # BIRIM ARTIK SAAT, VARDIYA SAYISI DEGIL (SDD 6.3.4, SRS S2/S3). Blok
    # sureleri cozumun ciktisi oldugundan sayima dayali bir olcu tanimsizdir.
    # P2'nin 00.00–08.00 blogunun ALTI saati gece penceresine (20.00–06.00)
    # duser - 06 ve 07 gece degildir; onceki beklenti 1'di ve birimi vardiya
    # sayisiydi.
    gece_map = {g["personel_id"]: g["sayi"] for g in govde["kisi_basina_gece"]}
    assert gece_map[p1_id] == 0
    assert gece_map[p2_id] == 6

    # Hafta sonu olcusu blogun TAM suresidir: sekiz saat.
    hs_map = {g["personel_id"]: g["sayi"] for g in govde["kisi_basina_hafta_sonu"]}
    assert hs_map[p1_id] == 0
    assert hs_map[p2_id] == 8

    # Saat dagiliminin tabani SDD 5.7 (surum 1.7) ile SOZLESME saatinden
    # ADIL PAYA (SRS S4'teki pay[p]) cevrildi. Bu senaryoda donem ici toplam
    # talep 7 kisi-vardiya x 8 saat = 56 saat; iki personelin de haftalik
    # hedefi 40 oldugundan pay esit bolusulur: 56/2 = 28 saat.
    #
    # Asil kazanc, sapmanin artik IKI YONLU olmasi: eski tabanda P1 0, P2 -32
    # veriyordu (ikisi de <= 0, tablo "kim payindan fazla aldi" sorusunu
    # yanitlayamiyordu); yeni tabanda P1 +12 (payindan fazla), P2 -20
    # (payindan az) - metrik gercekten dengesizligi olcuyor.
    saat_map = {s["personel_id"]: s for s in govde["saat_dagilimi"]}
    assert saat_map[p1_id]["hedef_saat"] == pytest.approx(28.0)
    assert saat_map[p2_id]["hedef_saat"] == pytest.approx(28.0)
    assert saat_map[p1_id]["toplam_saat"] == pytest.approx(40.0)
    assert saat_map[p1_id]["sapma"] == pytest.approx(12.0)
    assert saat_map[p2_id]["toplam_saat"] == pytest.approx(8.0)
    assert saat_map[p2_id]["sapma"] == pytest.approx(-20.0)

    # En dengesiz: P2, |−20| > P1'in |+12|.
    assert govde["en_dengesiz_personel_id"] == p2_id

    # Tercih: P1'in calismama tercihi PER 10'da, ama P1 o gun calisiyor -> karsilanmadi.
    assert govde["tercih_karsilama_orani"] == pytest.approx(0.0)

    assert govde["bina_degisim_sayisi"] == []

    assert govde["ceza_dokumu"] == {"S1": 1000.0, "S2": 234.0}
    assert govde["toplam_ceza"] == pytest.approx(1234.0)
