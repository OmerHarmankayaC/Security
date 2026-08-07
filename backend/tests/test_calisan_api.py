"""Calisan Paneli uc noktalari testleri (Sprint 3 Gun 13: SDD 6.1, Ek B;
SRS FR-9.x). SRS TD-12 (karsilanma durumu, uc degerli), FR-9.4 (degisen
gunler) ve FR-9.6 (tercih bildirimi) elle kurulmus senaryolarla dogrulanir.

Canli bir PostgreSQL gerektirir; baglanamiyorsa atlanir.
"""

import uuid
from datetime import UTC, date, datetime, time, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.config import ayarlar
from app.db import OturumYerel
from app.main import app
from app.models.girdi import Tercih, TercihDurumu, TercihTipi
from app.models.sonuc import Atama, AtamaKaynagi, CizelgeSurumu, CizelgeSurumuDurumu, Donem
from app.models.tanim import GorevNoktasi, Personel, VardiyaTipi
from tests.conftest import pg_yoksa_atla


@pytest.fixture
def istemci() -> TestClient:
    pg_yoksa_atla()
    return TestClient(app)


def _benzersiz(on_ek: str) -> str:
    return f"{on_ek}-{uuid.uuid4().hex[:8]}"


ANAHTAR = ayarlar.calisan_paneli_baglanti_anahtari
BUGUN = date.today()


def test_vardiyalarim_bulunmayan_personelde_404(istemci: TestClient) -> None:
    yanit = istemci.get(f"/api/calisan/vardiyalarim?personel_id=999999999&anahtar={ANAHTAR}")
    assert yanit.status_code == 404


def test_vardiyalarim_yanlis_anahtarda_403(istemci: TestClient) -> None:
    yanit = istemci.get("/api/calisan/vardiyalarim?personel_id=1&anahtar=yanlis")
    assert yanit.status_code == 403


@pytest.fixture
def senaryo() -> dict[str, int]:
    """BUGUN'u iceren bir donem: bir ARSIV surumu (karsilastirma tabani) +
    bir YAYINLANDI surumu (calisana gosterilen). Personelin gunleri:
    - gun1 (bugunden 1 gun once): arsiv ve yayin ayni -> degisim yok.
    - gun2 (bugun): yayinda vardiya tipi degisti -> 'degisti'.
    - gun3 (yarin): yalniz yayinda var -> 'eklendi'.
    """
    on_ek = _benzersiz("cal")
    oturum = OturumYerel()
    try:
        # _donem_ozeti AnalizServisi'ni (dolayisiyla TUM `personel` tablosunu,
        # bkz. tests/test_analiz_api.py) kullandigindan, ekip ortalamasini
        # elle hesaplanabilir tutmak icin ayni TRUNCATE deseni uygulanir.
        oturum.execute(
            text(
                "TRUNCATE kapsama_acigi, cozum_isi, atama, cizelge_surumu, musaitlik, "
                "donem, talep, personel_yetkinlik, personel, gorev_noktasi, "
                "vardiya_tipi, bina, yetkinlik, kural, tercih CASCADE"
            )
        )
        oturum.commit()

        gunduz = VardiyaTipi(
            ad=f"Gunduz-{on_ek}",
            baslangic_saati=time(8, 0),
            bitis_saati=time(16, 0),
            sure_saat=8,
            gece_mi=False,
        )
        gece = VardiyaTipi(
            ad=f"Gece-{on_ek}",
            baslangic_saati=time(0, 0),
            bitis_saati=time(8, 0),
            sure_saat=8,
            gece_mi=True,
        )
        oturum.add_all([gunduz, gece])
        nokta = GorevNoktasi(ad=f"Nokta-{on_ek}")
        oturum.add(nokta)
        personel = Personel(
            ad_soyad=f"Calisan-{on_ek}",
            sicil_no=_benzersiz("CAL"),
            haftalik_hedef_saat=40,
            aktif_baslangic=date(2026, 1, 1),
        )
        oturum.add(personel)
        oturum.flush()

        donem = Donem(
            baslangic_tarihi=BUGUN - timedelta(days=3),
            bitis_tarihi=BUGUN + timedelta(days=3),
            tercih_son_tarihi=BUGUN + timedelta(days=10),
        )
        oturum.add(donem)
        oturum.flush()

        arsiv = CizelgeSurumu(
            donem_id=donem.donem_id,
            surum_no=1,
            durum=CizelgeSurumuDurumu.ARSIV,
            yayin_zamani=datetime.now(UTC) - timedelta(days=1),
        )
        yayinlanan = CizelgeSurumu(
            donem_id=donem.donem_id,
            surum_no=2,
            durum=CizelgeSurumuDurumu.YAYINLANDI,
            onceki_surum_id=None,
            yayin_zamani=datetime.now(UTC),
        )
        oturum.add_all([arsiv, yayinlanan])
        oturum.flush()

        gun1 = BUGUN - timedelta(days=1)
        gun2 = BUGUN
        gun3 = BUGUN + timedelta(days=1)

        # Arsiv: gun1 gunduz, gun2 gunduz (yayinda gece'ye degisecek).
        oturum.add_all(
            [
                Atama(
                    surum_id=arsiv.surum_id,
                    personel_id=personel.personel_id,
                    tarih=gun1,
                    vardiya_tipi_id=gunduz.vardiya_tipi_id,
                    nokta_id=nokta.nokta_id,
                    kaynak=AtamaKaynagi.COZUCU,
                ),
                Atama(
                    surum_id=arsiv.surum_id,
                    personel_id=personel.personel_id,
                    tarih=gun2,
                    vardiya_tipi_id=gunduz.vardiya_tipi_id,
                    nokta_id=nokta.nokta_id,
                    kaynak=AtamaKaynagi.COZUCU,
                ),
            ]
        )
        # Yayinlanan: gun1 ayni (gunduz), gun2 gece'ye degisti, gun3 yeni (eklendi).
        oturum.add_all(
            [
                Atama(
                    surum_id=yayinlanan.surum_id,
                    personel_id=personel.personel_id,
                    tarih=gun1,
                    vardiya_tipi_id=gunduz.vardiya_tipi_id,
                    nokta_id=nokta.nokta_id,
                    kaynak=AtamaKaynagi.COZUCU,
                ),
                Atama(
                    surum_id=yayinlanan.surum_id,
                    personel_id=personel.personel_id,
                    tarih=gun2,
                    vardiya_tipi_id=gece.vardiya_tipi_id,
                    nokta_id=nokta.nokta_id,
                    kaynak=AtamaKaynagi.COZUCU,
                ),
                Atama(
                    surum_id=yayinlanan.surum_id,
                    personel_id=personel.personel_id,
                    tarih=gun3,
                    vardiya_tipi_id=gunduz.vardiya_tipi_id,
                    nokta_id=nokta.nokta_id,
                    kaynak=AtamaKaynagi.COZUCU,
                ),
            ]
        )
        oturum.commit()
        return {
            "personel_id": personel.personel_id,
            "donem_id": donem.donem_id,
            "surum_id": yayinlanan.surum_id,
        }
    finally:
        oturum.rollback()
        oturum.close()


def test_vardiyalarim_degisen_gunleri_uc_ture_ayirir(
    istemci: TestClient, senaryo: dict[str, int]
) -> None:
    yanit = istemci.get(
        f"/api/calisan/vardiyalarim?personel_id={senaryo['personel_id']}&anahtar={ANAHTAR}"
    )
    assert yanit.status_code == 200
    govde = yanit.json()

    assert govde["yayinlanmis_surum_var"] is True
    assert govde["surum_id"] == senaryo["surum_id"]

    degisim_map = {v["tarih"]: v["degisim_tipi"] for v in govde["vardiyalar"]}
    gun1 = (BUGUN - timedelta(days=1)).isoformat()
    gun2 = BUGUN.isoformat()
    gun3 = (BUGUN + timedelta(days=1)).isoformat()
    assert degisim_map[gun1] is None
    assert degisim_map[gun2] == "degisti"
    assert degisim_map[gun3] == "eklendi"

    # Siradaki: bugunden itibaren ilk vardiya (gun2).
    assert govde["siradaki"]["tarih"] == gun2

    # Donem ozeti (FR-9.5): AnalizServisi'nin yeniden kullanimindan - tek
    # personel oldugu icin kendi degeri = ekip ortalamasi.
    assert govde["ozet"] is not None
    assert govde["ozet"]["gece_sayisi"] == 1
    assert govde["ozet"]["ekip_ortalama_gece"] == pytest.approx(1.0)


def test_vardiyalarim_yayinlanmamis_surumde_bos_liste_doner(istemci: TestClient) -> None:
    on_ek = _benzersiz("caltaslak")
    oturum = OturumYerel()
    try:
        # guncel_donemi_bul BUGUN'u iceren donemi personel-bagimsiz secer -
        # onceki testin (senaryo fixture) donemi de hala BUGUN'u kapsadigindan,
        # bu testin donemiyle karismamasi icin ayni TRUNCATE deseni gerekir.
        oturum.execute(
            text(
                "TRUNCATE kapsama_acigi, cozum_isi, atama, cizelge_surumu, musaitlik, "
                "donem, talep, personel_yetkinlik, personel, gorev_noktasi, "
                "vardiya_tipi, bina, yetkinlik, kural, tercih CASCADE"
            )
        )
        oturum.commit()

        personel = Personel(
            ad_soyad=f"Taslak-{on_ek}",
            sicil_no=_benzersiz("TAS"),
            haftalik_hedef_saat=40,
            aktif_baslangic=date(2026, 1, 1),
        )
        oturum.add(personel)
        donem = Donem(
            baslangic_tarihi=BUGUN - timedelta(days=1),
            bitis_tarihi=BUGUN + timedelta(days=1),
            tercih_son_tarihi=BUGUN + timedelta(days=5),
        )
        oturum.add(donem)
        oturum.flush()
        oturum.add(
            CizelgeSurumu(donem_id=donem.donem_id, surum_no=1, durum=CizelgeSurumuDurumu.TASLAK)
        )
        oturum.commit()
        personel_id = personel.personel_id
    finally:
        oturum.rollback()
        oturum.close()

    yanit = istemci.get(f"/api/calisan/vardiyalarim?personel_id={personel_id}&anahtar={ANAHTAR}")
    assert yanit.status_code == 200
    govde = yanit.json()
    assert govde["yayinlanmis_surum_var"] is False
    assert govde["vardiyalar"] == []
    assert govde["ozet"] is None


def test_tercihlerim_karsilanma_uc_degerlidir(istemci: TestClient) -> None:
    on_ek = _benzersiz("caltercih")
    oturum = OturumYerel()
    try:
        gunduz = VardiyaTipi(
            ad=f"Gunduz-{on_ek}",
            baslangic_saati=time(8, 0),
            bitis_saati=time(16, 0),
            sure_saat=8,
            gece_mi=False,
        )
        oturum.add(gunduz)
        nokta = GorevNoktasi(ad=f"Nokta-{on_ek}")
        oturum.add(nokta)
        personel = Personel(
            ad_soyad=f"Tercihci-{on_ek}",
            sicil_no=_benzersiz("TRC"),
            haftalik_hedef_saat=40,
            aktif_baslangic=date(2026, 1, 1),
        )
        oturum.add(personel)
        oturum.flush()

        # Donem A: yayinlanmis surumu YOK -> her iki tercih de henuz_belirsiz.
        donem_a = Donem(
            baslangic_tarihi=date(2026, 6, 1),
            bitis_tarihi=date(2026, 6, 7),
            tercih_son_tarihi=date(2026, 5, 25),
        )
        # Donem B: yayinlanmis surumu VAR.
        donem_b = Donem(
            baslangic_tarihi=date(2026, 6, 8),
            bitis_tarihi=date(2026, 6, 14),
            tercih_son_tarihi=date(2026, 6, 1),
        )
        oturum.add_all([donem_a, donem_b])
        oturum.flush()

        surum_b = CizelgeSurumu(
            donem_id=donem_b.donem_id,
            surum_no=1,
            durum=CizelgeSurumuDurumu.YAYINLANDI,
            yayin_zamani=datetime.now(UTC),
        )
        oturum.add(surum_b)
        oturum.flush()

        # Donem B'de personel 10 Haziran'da CALISIYOR.
        oturum.add(
            Atama(
                surum_id=surum_b.surum_id,
                personel_id=personel.personel_id,
                tarih=date(2026, 6, 10),
                vardiya_tipi_id=gunduz.vardiya_tipi_id,
                nokta_id=nokta.nokta_id,
                kaynak=AtamaKaynagi.COZUCU,
            )
        )

        # T1: donem A'da calismama tercihi -> henuz_belirsiz (surum yok).
        t1 = Tercih(
            personel_id=personel.personel_id,
            donem_id=donem_a.donem_id,
            tarih=date(2026, 6, 3),
            tip=TercihTipi.CALISMAMA,
            durum=TercihDurumu.BEKLEMEDE,
        )
        # T2: donem B, 10 Haziran calismama tercihi ama o gun calisiyor -> karsilanmadi.
        t2 = Tercih(
            personel_id=personel.personel_id,
            donem_id=donem_b.donem_id,
            tarih=date(2026, 6, 10),
            tip=TercihTipi.CALISMAMA,
            durum=TercihDurumu.REDDEDILDI,
            ret_gerekcesi="Kadro yetersiz",
        )
        # T3: donem B, 11 Haziran calismama tercihi, o gun atama yok -> karsilandi.
        t3 = Tercih(
            personel_id=personel.personel_id,
            donem_id=donem_b.donem_id,
            tarih=date(2026, 6, 11),
            tip=TercihTipi.CALISMAMA,
            durum=TercihDurumu.ONAYLANDI,
        )
        oturum.add_all([t1, t2, t3])
        oturum.commit()
        personel_id = personel.personel_id
    finally:
        oturum.rollback()
        oturum.close()

    yanit = istemci.get(f"/api/calisan/tercih?personel_id={personel_id}&anahtar={ANAHTAR}")
    assert yanit.status_code == 200
    govde = yanit.json()

    karsilanma_map = {t["tarih"]: t["karsilanma"] for t in govde["tercihler"]}
    assert karsilanma_map["2026-06-03"] == "henuz_belirsiz"
    assert karsilanma_map["2026-06-10"] == "karsilanmadi"
    assert karsilanma_map["2026-06-11"] == "karsilandi"

    ret_map = {t["tarih"]: t["ret_gerekcesi"] for t in govde["tercihler"]}
    assert ret_map["2026-06-10"] == "Kadro yetersiz"


def test_tercih_bildir_mutlu_yol_ve_donem_disi_tarih_400(istemci: TestClient) -> None:
    on_ek = _benzersiz("calbildir")
    oturum = OturumYerel()
    try:
        personel = Personel(
            ad_soyad=f"Bildirici-{on_ek}",
            sicil_no=_benzersiz("BLD"),
            haftalik_hedef_saat=40,
            aktif_baslangic=date(2026, 1, 1),
        )
        oturum.add(personel)
        donem = Donem(
            baslangic_tarihi=BUGUN + timedelta(days=5),
            bitis_tarihi=BUGUN + timedelta(days=11),
            tercih_son_tarihi=BUGUN + timedelta(days=3),
        )
        oturum.add(donem)
        oturum.commit()
        personel_id = personel.personel_id
        donem_id = donem.donem_id
        icindeki_tarih = (BUGUN + timedelta(days=6)).isoformat()
    finally:
        oturum.rollback()
        oturum.close()

    yanit = istemci.post(
        f"/api/calisan/tercih?personel_id={personel_id}&anahtar={ANAHTAR}",
        json={"tarih": icindeki_tarih, "tip": "calismama", "calisan_notu": "Kardeşimin düğünü var"},
    )
    assert yanit.status_code == 201
    govde = yanit.json()
    assert govde["tip"] == "calismama"
    assert govde["calisan_notu"] == "Kardeşimin düğünü var"
    assert govde["durum"] == "beklemede"
    assert govde["karsilanma"] == "henuz_belirsiz"

    oturum = OturumYerel()
    try:
        kayit = oturum.get(Tercih, govde["tercih_id"])
        assert kayit is not None
        assert kayit.donem_id == donem_id
    finally:
        oturum.close()

    disari_tarih = (BUGUN + timedelta(days=100)).isoformat()
    yanit = istemci.post(
        f"/api/calisan/tercih?personel_id={personel_id}&anahtar={ANAHTAR}",
        json={"tarih": disari_tarih, "tip": "calismama"},
    )
    assert yanit.status_code == 400
