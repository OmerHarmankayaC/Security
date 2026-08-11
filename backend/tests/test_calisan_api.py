"""Calisan Paneli uc noktalari testleri (SDD 6.1, Ek B; SRS FR-9.x).

SRS TD-12 (karsilanma durumu, yalniz onaylanmislar icin ve uc degerli),
FR-9.4 (degisen gunler, uc tur) ve FR-9.6 (tercih bildirimi) elle kurulmus
senaryolarla dogrulanir.

FR-9.1 (baska personelin verisine erisim yok) artik OTURUM uzerinden
dogrulanir; kisiye ozel baglanti anahtari kaldirildi. Testin bicimi de
degisti ve bu degisiklik testin kendisi kadar onemli: eskiden "yanlis
anahtarla baskasinin kimligini denemek reddediliyor mu" diye sorulurdu,
simdi "istekte gelen kimlik SONUCU DEGISTIRIYOR MU" diye soruluyor -
cunku yeni tasarimda kimlik bir parametre degil.

Canli bir PostgreSQL gerektirir; baglanamiyorsa atlanir.
"""

import uuid
from datetime import UTC, date, datetime, time, timedelta

import pytest
from fastapi.testclient import TestClient

from app.db import OturumYerel
from app.main import app
from app.models.girdi import Tercih, TercihDurumu, TercihTipi
from app.models.kimlik import Rol
from app.models.sonuc import Atama, AtamaKaynagi, CizelgeSurumu, CizelgeSurumuDurumu, Donem
from app.models.tanim import GorevNoktasi, GunTipi, Personel, Talep, VardiyaTipi
from tests.conftest import oturumlu_istemci, pg_yoksa_atla, senaryo_verisini_temizle

BUGUN = date.today()


def _benzersiz(on_ek: str) -> str:
    return f"{on_ek}-{uuid.uuid4().hex[:8]}"


def _calisan_istemcisi(personel_id: int) -> TestClient:
    """O personele bagli bir calisan hesabiyla giris yapmis istemci."""
    pg_yoksa_atla()
    return oturumlu_istemci(Rol.CALISAN, personel_id=personel_id)


def _temizle(oturum) -> None:  # noqa: ANN001 - Session, testlere ozel yardimci
    """AnalizServisi (dolayisiyla ekip ortalamasi) ve `guncel_donemi_bul` TUM
    tabloyu tarar; baska bir oturumdan/testten kalan veri sonuclari bozar
    (bkz. tests/test_analiz_api.py'deki ayni desen)."""
    senaryo_verisini_temizle(oturum)


# --- FR-9.1: gosterilecek personel YALNIZ oturumdan belirlenir --------------


def test_oturumsuz_istek_401_alir() -> None:
    pg_yoksa_atla()
    istemci = TestClient(app, base_url="https://testserver")
    assert istemci.get("/api/calisan/vardiyalarim").status_code == 401
    assert istemci.get("/api/calisan/tercih").status_code == 401


def test_istekte_gelen_personel_kimligi_donen_veriyi_degistiremez() -> None:
    """FR-9.1'in cekirdegi.

    Eski tasarimda kimlik adreste gelir ve dogrulanirdi; dogrulamayi
    atlayan tek bir uc nokta butun ayrimi kaldiriyordu. Yeni tasarimda
    kimlik PARAMETRE DEGIL - bu test onu kanitlar: A'nin oturumuyla B'nin
    kimligini adreste de govdede de gondermek A'nin verisini dondurur,
    B'ninkini degil.

    Onemli olan ret DEGIL, kimligin sonuca hic girmemesidir. Bir ret
    beklemek, kimligin okundugunu ve yalnizca reddedildigini varsayardi;
    okunmadigini dogrulamak daha guclu bir ifadedir.
    """
    on_ek = _benzersiz("izolasyon")
    oturum = OturumYerel()
    try:
        a = Personel(
            ad_soyad=f"A-{on_ek}",
            sicil_no=_benzersiz("IZA"),
            haftalik_hedef_saat=40,
            aktif_baslangic=date(2026, 1, 1),
        )
        b = Personel(
            ad_soyad=f"B-{on_ek}",
            sicil_no=_benzersiz("IZB"),
            haftalik_hedef_saat=40,
            aktif_baslangic=date(2026, 1, 1),
        )
        oturum.add_all([a, b])
        oturum.commit()
        a_id, b_id = a.personel_id, b.personel_id
        a_ad = a.ad_soyad
    finally:
        oturum.rollback()
        oturum.close()

    istemci = _calisan_istemcisi(a_id)

    kendi = istemci.get("/api/calisan/vardiyalarim").json()
    assert kendi["personel_id"] == a_id
    assert kendi["ad_soyad"] == a_ad

    # (a) Adreste baskasinin kimligi.
    kacak = istemci.get(f"/api/calisan/vardiyalarim?personel_id={b_id}")
    assert kacak.status_code == 200
    assert kacak.json()["personel_id"] == a_id

    # (b) Kendi kimligini gondermek de bir sey degistirmez; alan okunmuyor.
    assert (
        istemci.get(f"/api/calisan/vardiyalarim?personel_id={a_id}").json()["personel_id"] == a_id
    )

    # (c) Tercih okuma yolu.
    assert istemci.get(f"/api/calisan/tercih?personel_id={b_id}").status_code == 200

    # (d) YAZMA yolu: govdedeki kimlik de yok sayilir, kayit A adina dogar.
    yanit = istemci.post(
        f"/api/calisan/tercih?personel_id={b_id}",
        json={"tarih": BUGUN.isoformat(), "tip": "calismama", "personel_id": b_id},
    )
    if yanit.status_code == 201:
        oturum = OturumYerel()
        try:
            kayit = oturum.get(Tercih, yanit.json()["tercih_id"])
            assert kayit is not None
            assert kayit.personel_id == a_id
        finally:
            oturum.close()
    else:
        # Bugun hicbir donemin tercih penceresine dusmuyorsa 400 doner;
        # o durumda da B adina bir kayit DOGMAMIS olmalidir.
        assert yanit.status_code == 400
        oturum = OturumYerel()
        try:
            assert oturum.query(Tercih).filter(Tercih.personel_id == b_id).count() == 0
        finally:
            oturum.close()


def test_yonetici_rolu_calisan_panelinden_gecemez() -> None:
    """SRS 5.10: calisan rolu digerlerinin alt kumesi degildir; kendi
    verisine erisim personel kaydina bagli AYRI bir yetkidir. Yonetim
    rolunun buradan gecmesi, kimin verisinin donecegini yanitsiz birakirdi."""
    pg_yoksa_atla()
    istemci = oturumlu_istemci(Rol.YONETIM)
    assert istemci.get("/api/calisan/vardiyalarim").status_code == 403


# --- Vardiyalarim / degisen gunler (FR-9.3, FR-9.4) -------------------------


@pytest.fixture
def senaryo() -> dict[str, int]:
    """BUGUN'u iceren bir donem: bir ARSIV surumu (karsilastirma tabani) +
    bir YAYINLANDI surumu (calisana gosterilen). Personelin gunleri:
    - gun0 (bugunden 2 gun once): yalniz arsivde -> 'kaldirildi'.
    - gun1 (bugunden 1 gun once): arsiv ve yayin ayni -> degisim yok.
    - gun2 (bugun): yayinda vardiya tipi degisti -> 'degisti'.
    - gun3 (yarin): yalniz yayinda var -> 'eklendi'.
    """
    on_ek = _benzersiz("cal")
    oturum = OturumYerel()
    try:
        _temizle(oturum)

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

        # Talep satirlari: Donem Ozetim'in ekip ortalamasi AnalizServisi'nden
        # gelir ve o da SRS S2/S3'teki UYGUN HAVUZU (P_gece / P_hs) talepten
        # turetir - talep tanimlanmazsa havuz bos kalir ve gece/hafta sonu
        # metrikleri hic uretilmez. Senaryo bu yuzden gercek bir talep tasir.
        oturum.add_all(
            [
                Talep(
                    nokta_id=nokta.nokta_id,
                    vardiya_tipi_id=gunduz.vardiya_tipi_id,
                    gun_tipi=GunTipi.HAFTA_ICI,
                    tarih=None,
                    gereken_sayi=1,
                ),
                Talep(
                    nokta_id=nokta.nokta_id,
                    vardiya_tipi_id=gece.vardiya_tipi_id,
                    gun_tipi=GunTipi.HAFTA_ICI,
                    tarih=None,
                    gereken_sayi=1,
                ),
                Talep(
                    nokta_id=nokta.nokta_id,
                    vardiya_tipi_id=gece.vardiya_tipi_id,
                    gun_tipi=GunTipi.HAFTA_SONU,
                    tarih=None,
                    gereken_sayi=1,
                ),
            ]
        )

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
            yayin_zamani=datetime.now(UTC),
        )
        oturum.add_all([arsiv, yayinlanan])
        oturum.flush()

        gun0 = BUGUN - timedelta(days=2)
        gun1 = BUGUN - timedelta(days=1)
        gun2 = BUGUN
        gun3 = BUGUN + timedelta(days=1)

        def _atama(surum_id: int, tarih: date, vardiya_tipi_id: int) -> Atama:
            return Atama(
                surum_id=surum_id,
                personel_id=personel.personel_id,
                tarih=tarih,
                vardiya_tipi_id=vardiya_tipi_id,
                nokta_id=nokta.nokta_id,
                kaynak=AtamaKaynagi.COZUCU,
            )

        # Arsiv: gun0 + gun1 + gun2 (hepsi gunduz).
        oturum.add_all(
            [
                _atama(arsiv.surum_id, gun0, gunduz.vardiya_tipi_id),
                _atama(arsiv.surum_id, gun1, gunduz.vardiya_tipi_id),
                _atama(arsiv.surum_id, gun2, gunduz.vardiya_tipi_id),
            ]
        )
        # Yayinlanan: gun0 YOK (kaldirildi), gun1 ayni, gun2 gece'ye degisti,
        # gun3 yeni (eklendi).
        oturum.add_all(
            [
                _atama(yayinlanan.surum_id, gun1, gunduz.vardiya_tipi_id),
                _atama(yayinlanan.surum_id, gun2, gece.vardiya_tipi_id),
                _atama(yayinlanan.surum_id, gun3, gunduz.vardiya_tipi_id),
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


def test_vardiyalarim_degisen_gunleri_uc_ture_ayirir(senaryo: dict[str, int]) -> None:
    istemci = _calisan_istemcisi(senaryo["personel_id"])
    yanit = istemci.get("/api/calisan/vardiyalarim")
    assert yanit.status_code == 200
    govde = yanit.json()

    assert govde["yayinlanmis_surum_var"] is True
    assert govde["surum_id"] == senaryo["surum_id"]

    gun0 = (BUGUN - timedelta(days=2)).isoformat()
    gun1 = (BUGUN - timedelta(days=1)).isoformat()
    gun2 = BUGUN.isoformat()
    gun3 = (BUGUN + timedelta(days=1)).isoformat()

    degisim_map = {v["tarih"]: v["degisim_tipi"] for v in govde["vardiyalar"]}
    assert degisim_map[gun1] is None
    assert degisim_map[gun2] == "degisti"
    assert degisim_map[gun3] == "eklendi"

    # Ucuncu tur: kaldirilan gun AYRI listede; `vardiyalar` icinde YOKTUR
    # (orada olsaydi calisan artik sahip olmadigi bir vardiyayi gorurdu).
    assert gun0 not in degisim_map
    assert [k["tarih"] for k in govde["kaldirilan_gunler"]] == [gun0]
    kaldirilan = govde["kaldirilan_gunler"][0]
    assert kaldirilan["onceki_baslangic_saati"] == "08:00:00"
    assert kaldirilan["onceki_gece_mi"] is False

    # Siradaki, kaldirilan gunu SECMEZ; bugunden itibaren ilk gercek vardiya.
    assert govde["siradaki"]["tarih"] == gun2

    # Donem ozeti (FR-9.5) yalniz yayinlanmis surumden hesaplanir - kaldirilan
    # gun sayilara girmez. Tek personel oldugu icin kendi degeri = ekip ort.
    assert govde["ozet"]["gece_sayisi"] == 1
    assert govde["ozet"]["ekip_ortalama_gece"] == pytest.approx(1.0)
    assert govde["ozet"]["toplam_saat"] == pytest.approx(24.0)


def test_ilk_yayinda_hicbir_gun_isaretlenmez() -> None:
    """FR-9.4: donemin ilk yayininda karsilastirma tabani (arsiv surumu)
    bulunmadigindan hicbir gun isaretlenmez ve kaldirilan gun olmaz."""
    on_ek = _benzersiz("ilkyayin")
    oturum = OturumYerel()
    try:
        _temizle(oturum)
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
            ad_soyad=f"Ilk-{on_ek}",
            sicil_no=_benzersiz("ILK"),
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
        surum = CizelgeSurumu(
            donem_id=donem.donem_id,
            surum_no=1,
            durum=CizelgeSurumuDurumu.YAYINLANDI,
            yayin_zamani=datetime.now(UTC),
        )
        oturum.add(surum)
        oturum.flush()
        oturum.add(
            Atama(
                surum_id=surum.surum_id,
                personel_id=personel.personel_id,
                tarih=BUGUN,
                vardiya_tipi_id=gunduz.vardiya_tipi_id,
                nokta_id=nokta.nokta_id,
                kaynak=AtamaKaynagi.COZUCU,
            )
        )
        oturum.commit()
        personel_id = personel.personel_id
    finally:
        oturum.rollback()
        oturum.close()

    govde = _calisan_istemcisi(personel_id).get("/api/calisan/vardiyalarim").json()
    assert [v["degisim_tipi"] for v in govde["vardiyalar"]] == [None]
    assert govde["kaldirilan_gunler"] == []


def test_vardiyalarim_yayinlanmamis_surumde_bos_liste_doner() -> None:
    on_ek = _benzersiz("caltaslak")
    oturum = OturumYerel()
    try:
        # guncel_donemi_bul BUGUN'u iceren donemi personel-bagimsiz secer -
        # onceki testlerin donemi de hala BUGUN'u kapsadigindan temizlik sart.
        _temizle(oturum)
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

    yanit = _calisan_istemcisi(personel_id).get("/api/calisan/vardiyalarim")
    assert yanit.status_code == 200
    govde = yanit.json()
    assert govde["yayinlanmis_surum_var"] is False
    assert govde["vardiyalar"] == []
    assert govde["kaldirilan_gunler"] == []
    assert govde["ozet"] is None


# --- Tercihlerim / karsilanma durumu (TD-12, FR-3.6, FR-9.6) ----------------


def test_tercihlerim_karsilanma_uc_degerli_ve_yalniz_onaylanmislarda() -> None:
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

        # Donem A: yayinlanmis surumu YOK -> onaylanmis tercih henuz_belirsiz.
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

        ortak = {"personel_id": personel.personel_id, "tip": TercihTipi.CALISMAMA}
        oturum.add_all(
            [
                # Onaylanmis, donemin surumu yok -> henuz_belirsiz.
                Tercih(
                    **ortak,
                    donem_id=donem_a.donem_id,
                    tarih=date(2026, 6, 3),
                    durum=TercihDurumu.ONAYLANDI,
                ),
                # Onaylanmis, o gun calisiyor -> karsilanmadi.
                Tercih(
                    **ortak,
                    donem_id=donem_b.donem_id,
                    tarih=date(2026, 6, 9),
                    durum=TercihDurumu.ONAYLANDI,
                ),
                # Onaylanmis, o gun atama yok -> karsilandi.
                Tercih(
                    **ortak,
                    donem_id=donem_b.donem_id,
                    tarih=date(2026, 6, 11),
                    durum=TercihDurumu.ONAYLANDI,
                ),
                # BEKLEMEDE -> TD-12 geregi turetme YAPILMAZ (null).
                Tercih(
                    **ortak,
                    donem_id=donem_b.donem_id,
                    tarih=date(2026, 6, 12),
                    durum=TercihDurumu.BEKLEMEDE,
                ),
                # REDDEDILDI -> turetme YAPILMAZ (null), gerekce gosterilir.
                Tercih(
                    **ortak,
                    donem_id=donem_b.donem_id,
                    tarih=date(2026, 6, 13),
                    durum=TercihDurumu.REDDEDILDI,
                    ret_gerekcesi="Kadro yetersiz",
                ),
            ]
        )
        # 9 Haziran'da da calisiyor (yukaridaki "karsilanmadi" icin).
        oturum.add(
            Atama(
                surum_id=surum_b.surum_id,
                personel_id=personel.personel_id,
                tarih=date(2026, 6, 9),
                vardiya_tipi_id=gunduz.vardiya_tipi_id,
                nokta_id=nokta.nokta_id,
                kaynak=AtamaKaynagi.COZUCU,
            )
        )
        oturum.commit()
        personel_id = personel.personel_id
    finally:
        oturum.rollback()
        oturum.close()

    yanit = _calisan_istemcisi(personel_id).get("/api/calisan/tercih")
    assert yanit.status_code == 200
    govde = yanit.json()

    karsilanma_map = {t["tarih"]: t["karsilanma"] for t in govde["tercihler"]}
    # Uc deger, yalniz ONAYLANMIS tercihlerde:
    assert karsilanma_map["2026-06-03"] == "henuz_belirsiz"
    assert karsilanma_map["2026-06-09"] == "karsilanmadi"
    assert karsilanma_map["2026-06-11"] == "karsilandi"
    # TD-12: bekleyen/reddedilen tercihte karsilanma TURETILMEZ.
    assert karsilanma_map["2026-06-12"] is None
    assert karsilanma_map["2026-06-13"] is None

    ret_map = {t["tarih"]: t["ret_gerekcesi"] for t in govde["tercihler"]}
    assert ret_map["2026-06-13"] == "Kadro yetersiz"


def test_tercih_bildir_mutlu_yol_ve_donem_disi_tarih_400() -> None:
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

    istemci = _calisan_istemcisi(personel_id)
    yanit = istemci.post(
        "/api/calisan/tercih",
        json={"tarih": icindeki_tarih, "tip": "calismama", "calisan_notu": "Kardeşimin düğünü var"},
    )
    assert yanit.status_code == 201
    govde = yanit.json()
    assert govde["tip"] == "calismama"
    assert govde["calisan_notu"] == "Kardeşimin düğünü var"
    assert govde["durum"] == "beklemede"
    # Yeni tercih BEKLEMEDE dogar -> TD-12 geregi karsilanma turetilmez.
    assert govde["karsilanma"] is None

    oturum = OturumYerel()
    try:
        kayit = oturum.get(Tercih, govde["tercih_id"])
        assert kayit is not None
        assert kayit.donem_id == donem_id
    finally:
        oturum.close()

    disari_tarih = (BUGUN + timedelta(days=100)).isoformat()
    yanit = istemci.post(
        "/api/calisan/tercih",
        json={"tarih": disari_tarih, "tip": "calismama"},
    )
    assert yanit.status_code == 400
