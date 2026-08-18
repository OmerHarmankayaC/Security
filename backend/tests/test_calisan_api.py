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
from app.models.tanim import GorevNoktasi, GunTipi, Personel, Talep
from tests.conftest import oturumlu_istemci, pg_yoksa_atla, senaryo_verisini_temizle

BUGUN = date.today()

# Blok BASLANGIC SAATLERI; sure sekiz saat (blok katalogu kalkti, SRS TD-13).
_GUNDUZ, _GECE = 8, 0


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


def _senaryo_kur(oturum) -> int:  # noqa: ANN001 - Session, testlere ozel yardimci
    """Ortak taban senaryo: personel + BUGUN'u kapsayan donem + gorev
    noktasi + talep (adil pay havuzu icin) + yayinlanmis surum + bir atama.

    Donem ozetim (FR-9.5) ve vardiyalarim'in duz mutlu yolunu sinayan
    testler bu tek kurulumu paylasir; FR-9.4'un degisen-gun izlemesi
    (arsiv + yayin ikilisi, gun bazinda desen) `senaryo` fikstüründe ayri
    kalir - o senaryo bu yardimciya indirgenemeyecek kadar kendine ozgu
    veri tasir."""
    on_ek = _benzersiz("ozet")
    nokta = GorevNoktasi(ad=f"Nokta-{on_ek}")
    oturum.add(nokta)
    personel = Personel(
        ad_soyad=f"Ozet-{on_ek}",
        sicil_no=_benzersiz("OZT"),
        haftalik_hedef_saat=40,
        aktif_baslangic=date(2026, 1, 1),
    )
    oturum.add(personel)
    oturum.flush()

    # Talep satirlari: AnalizServisi'nin adil pay havuzu (P_gece / P_hs)
    # bunlardan turer - talep olmadan gece/hafta sonu metrikleri hic uretilmez.
    oturum.add_all(
        [
            Talep(
                nokta_id=nokta.nokta_id,
                baslangic=time(8, 0),
                bitis=time(16, 0),
                gun_tipi=GunTipi.HAFTA_ICI,
                tarih=None,
                gereken_sayi=1,
            ),
            Talep(
                nokta_id=nokta.nokta_id,
                baslangic=time(0, 0),
                bitis=time(8, 0),
                gun_tipi=GunTipi.HAFTA_ICI,
                tarih=None,
                gereken_sayi=1,
            ),
            Talep(
                nokta_id=nokta.nokta_id,
                baslangic=time(0, 0),
                bitis=time(8, 0),
                gun_tipi=GunTipi.HAFTA_SONU,
                tarih=None,
                gereken_sayi=1,
            ),
        ]
    )

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
            baslangic_zamani=datetime.combine(BUGUN, time(8, 0)),
            bitis_zamani=datetime.combine(BUGUN, time(16, 0)),
            nokta_id=nokta.nokta_id,
            kaynak=AtamaKaynagi.COZUCU,
        )
    )
    oturum.commit()
    return personel.personel_id


# BUGUN'un haftanin hangi gunune denk geldigi TESTI CALISTIRAN GUNE GORE
# DEGISIR; asagidaki iki yardimci, tarih seciminin hangi gun calistirilirsa
# calistirilsin AYNI (deterministik) davranmasini saglar.
def _ilk_hafta_sonu(baslangic: date, gun_sayisi: int) -> date:
    for i in range(gun_sayisi):
        aday = baslangic + timedelta(days=i)
        if aday.weekday() >= 5:
            return aday
    raise AssertionError("pencerede hafta sonu bulunamadi")  # pragma: no cover


def _ilk_hafta_ici(baslangic: date, gun_sayisi: int) -> date:
    for i in range(gun_sayisi):
        aday = baslangic + timedelta(days=i)
        if aday.weekday() < 5:
            return aday
    raise AssertionError("pencerede hafta ici gun bulunamadi")  # pragma: no cover


def _senaryo_kur_gecmis_donemli(oturum) -> int:  # noqa: ANN001 - Session, testlere ozel yardimci
    """`_senaryo_kur` ile AYNI taban (SDD 6.3.4 testinin ihtiyaci): tek
    farkla, donemin BASLANGICINDAN once, doksan gunluk adalet penceresine
    (`ADALET_UFKU_GUN`) giren YAYINLANMIS bir onceki donem ve o donemde
    GECE + HAFTA SONUNA denk bir atama ekler.

    Final review bulgu 6: eski `_senaryo_kur` hicbir gecmis atama tasimiyordu,
    dolayisiyla "donem" ve "adalet" ufuklari SAYISAL OLARAK AYNI cikiyordu —
    testler bunu hic fark etmeden `ufuk` alaninin yanitta yankilandigini
    dogruluyordu ama `hesapla()`ya GERCEKTEN ULASTIGINI degil. Burada
    eklenen gecmis atama, iki ufkun GERCEKTEN FARKLI sayilar urettigini
    kanitlamaya yeter.
    """
    on_ek = _benzersiz("ozetgecmis")
    nokta = GorevNoktasi(ad=f"Nokta-{on_ek}")
    oturum.add(nokta)
    personel = Personel(
        ad_soyad=f"OzetGecmis-{on_ek}",
        sicil_no=_benzersiz("OZG"),
        haftalik_hedef_saat=40,
        aktif_baslangic=date(2026, 1, 1),
    )
    oturum.add(personel)
    oturum.flush()

    oturum.add_all(
        [
            Talep(
                nokta_id=nokta.nokta_id,
                baslangic=time(8, 0),
                bitis=time(16, 0),
                gun_tipi=GunTipi.HAFTA_ICI,
                tarih=None,
                gereken_sayi=1,
            ),
            Talep(
                nokta_id=nokta.nokta_id,
                baslangic=time(0, 0),
                bitis=time(8, 0),
                gun_tipi=GunTipi.HAFTA_ICI,
                tarih=None,
                gereken_sayi=1,
            ),
            Talep(
                nokta_id=nokta.nokta_id,
                baslangic=time(0, 0),
                bitis=time(8, 0),
                gun_tipi=GunTipi.HAFTA_SONU,
                tarih=None,
                gereken_sayi=1,
            ),
        ]
    )

    # Mevcut donem `guncel_donemi_bul(bugun)` geregi BUGUN'u kapsamak
    # ZORUNDA (calisan_servisi.donem_ozetim), ama BUGUN'un haftanin hangi
    # gunune denk geldigi test calisma anina gore degisir. On uc gunluk
    # (BUGUN-6..BUGUN+6) pencere, BUGUN hangi gun olursa olsun EN AZ BIR
    # tam hafta sonu icermeyi garanti eder -- boylece donem-ici HAFTA_SONU
    # talebi her zaman gercek bir tarihe denk gelir ve
    # `hafta_sonu_havuzunda` iki ufukta da GUVENILIR sekilde True olur.
    donem_baslangic = BUGUN - timedelta(days=6)
    donem_bitis = BUGUN + timedelta(days=6)
    donem = Donem(
        baslangic_tarihi=donem_baslangic,
        bitis_tarihi=donem_bitis,
        tercih_son_tarihi=donem_bitis + timedelta(days=5),
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

    # Mevcut donemdeki tek atama GUNDUZ VE HAFTA ICI bir gunde (BUGUN'un
    # kendisi degil -- `_ilk_hafta_ici` ile, BUGUN hafta sonuna denk gelse
    # bile deterministik): donem-ici gece/hafta sonu saati SIFIR kalir,
    # boylece adalet ufkundaki fark TAMAMEN gecmis atamadan gelir ve delta
    # acikca olculebilir.
    atama_gunu = _ilk_hafta_ici(donem_baslangic, 13)
    oturum.add(
        Atama(
            surum_id=surum.surum_id,
            personel_id=personel.personel_id,
            baslangic_zamani=datetime.combine(atama_gunu, time(8, 0)),
            bitis_zamani=datetime.combine(atama_gunu, time(16, 0)),
            nokta_id=nokta.nokta_id,
            kaynak=AtamaKaynagi.COZUCU,
        )
    )

    # --- Gecmis (onceki, YAYINLANMIS) donem: ADALET_UFKU_GUN=90 penceresine
    # giren ama mevcut donemden ONCE biten yedi gunluk bir donem.
    gecmis_baslangic = BUGUN - timedelta(days=33)
    gecmis_bitis = BUGUN - timedelta(days=27)
    gecmis_donem = Donem(
        baslangic_tarihi=gecmis_baslangic,
        bitis_tarihi=gecmis_bitis,
        tercih_son_tarihi=gecmis_baslangic - timedelta(days=1),
    )
    oturum.add(gecmis_donem)
    oturum.flush()

    gecmis_surum = CizelgeSurumu(
        donem_id=gecmis_donem.donem_id,
        surum_no=1,
        durum=CizelgeSurumuDurumu.YAYINLANDI,
        yayin_zamani=datetime.now(UTC),
    )
    oturum.add(gecmis_surum)
    oturum.flush()

    # Blok 00:00-08:00, HAFTA SONUNA denk bir gunde baslar: gece_saat_sayisi
    # (20:00-06:00 kesisimi) 6 saat gece, blogun TAMAMI (8 saat) hafta sonu
    # sayilir (TD-1: blok BASLADIGI gune yazilir) — GecmisSayaclar
    # ikisini de BAGIMSIZ topluyor (bkz. gecmis_sayaclar.py:
    # _sayaclari_topla).
    hafta_sonu_gunu = _ilk_hafta_sonu(gecmis_baslangic, 7)
    oturum.add(
        Atama(
            surum_id=gecmis_surum.surum_id,
            personel_id=personel.personel_id,
            baslangic_zamani=datetime.combine(hafta_sonu_gunu, time(0, 0)),
            bitis_zamani=datetime.combine(hafta_sonu_gunu, time(8, 0)),
            nokta_id=nokta.nokta_id,
            kaynak=AtamaKaynagi.COZUCU,
        )
    )
    oturum.commit()
    return personel.personel_id


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
                    baslangic=time(8, 0),
                    bitis=time(16, 0),
                    gun_tipi=GunTipi.HAFTA_ICI,
                    tarih=None,
                    gereken_sayi=1,
                ),
                Talep(
                    nokta_id=nokta.nokta_id,
                    baslangic=time(0, 0),
                    bitis=time(8, 0),
                    gun_tipi=GunTipi.HAFTA_ICI,
                    tarih=None,
                    gereken_sayi=1,
                ),
                Talep(
                    nokta_id=nokta.nokta_id,
                    baslangic=time(0, 0),
                    bitis=time(8, 0),
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

        def _atama(surum_id: int, tarih: date, baslangic: int) -> Atama:
            """`baslangic` blogun BASLANGIC SAATI; sure sekiz saat."""
            bas = datetime.combine(tarih, time(baslangic))
            return Atama(
                surum_id=surum_id,
                personel_id=personel.personel_id,
                baslangic_zamani=bas,
                bitis_zamani=bas + timedelta(hours=8),
                nokta_id=nokta.nokta_id,
                kaynak=AtamaKaynagi.COZUCU,
            )

        # Arsiv: gun0 + gun1 + gun2 (hepsi gunduz).
        oturum.add_all(
            [
                _atama(arsiv.surum_id, gun0, _GUNDUZ),
                _atama(arsiv.surum_id, gun1, _GUNDUZ),
                _atama(arsiv.surum_id, gun2, _GUNDUZ),
            ]
        )
        # Yayinlanan: gun0 YOK (kaldirildi), gun1 ayni, gun2 gece'ye degisti,
        # gun3 yeni (eklendi).
        oturum.add_all(
            [
                _atama(yayinlanan.surum_id, gun1, _GUNDUZ),
                _atama(yayinlanan.surum_id, gun2, _GECE),
                _atama(yayinlanan.surum_id, gun3, _GUNDUZ),
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
    assert kaldirilan["onceki_baslangic_zamani"].endswith("T08:00:00")

    # Siradaki, kaldirilan gunu SECMEZ; bugunden itibaren ilk gercek vardiya.
    assert govde["siradaki"]["tarih"] == gun2

    # Donem ozeti (FR-9.5) artik kendi uc noktasindadir (/api/calisan/ozetim,
    # bkz. test_ozetim_ufku_yaniti_icinde_tasir); burada YALNIZ ozetin
    # `vardiyalarim` govdesinde OLMADIGI dogrulanir.
    assert "ozet" not in govde

    # Donem ozeti (FR-9.5) yalniz yayinlanmis surumden hesaplanir - kaldirilan
    # gun sayilara girmez. Tek personel oldugu icin kendi degeri = ekip ort.
    # BIRIM SAAT (SRS S2): 00.00-08.00 blogunun ALTI saati gece penceresine
    # (20.00-06.00) duser. Onceki beklenti 1'di ve birimi vardiya sayisiydi.
    ozetim = istemci.get("/api/calisan/ozetim").json()
    assert ozetim["gece_saati"] == pytest.approx(6.0)
    assert ozetim["ekip_ortalama_gece"] == pytest.approx(6.0)
    assert ozetim["toplam_saat"] == pytest.approx(24.0)


def test_ilk_yayinda_hicbir_gun_isaretlenmez() -> None:
    """FR-9.4: donemin ilk yayininda karsilastirma tabani (arsiv surumu)
    bulunmadigindan hicbir gun isaretlenmez ve kaldirilan gun olmaz."""
    pg_yoksa_atla()
    with OturumYerel() as oturum:
        _temizle(oturum)
        personel_id = _senaryo_kur(oturum)

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
    # `ozet` artik bu govdede yok (bkz. test_vardiyalarim_artik_ozet_tasimaz):
    # donem ozeti /api/calisan/ozetim uc noktasina tasindi.
    assert "ozet" not in govde


# --- Tercihlerim / karsilanma durumu (TD-12, FR-3.6, FR-9.6) ----------------


def test_tercihlerim_karsilanma_uc_degerli_ve_yalniz_onaylanmislarda() -> None:
    on_ek = _benzersiz("caltercih")
    oturum = OturumYerel()
    try:
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
                baslangic_zamani=datetime(2026, 6, 10, 8, 0),
                bitis_zamani=datetime(2026, 6, 10, 16, 0),
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
                baslangic_zamani=datetime(2026, 6, 9, 8, 0),
                bitis_zamani=datetime(2026, 6, 9, 16, 0),
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


def test_ayni_gune_ikinci_tercih_beklemedekinin_uzerine_yazar() -> None:
    """Calisan fikrini degistirebilir; ayni gun icin iki celiskili tercih
    (calismam + 08-16 calisirim) yan yana duramaz."""
    pg_yoksa_atla()
    with OturumYerel() as oturum:
        _temizle(oturum)
        personel_id = _senaryo_kur(oturum)
    istemci = _calisan_istemcisi(personel_id)
    hedef = (BUGUN + timedelta(days=1)).isoformat()

    ilk = istemci.post("/api/calisan/tercih", json={"tarih": hedef, "tip": "calismama"})
    ikinci = istemci.post(
        "/api/calisan/tercih",
        json={
            "tarih": hedef,
            "tip": "zaman_araligi_tercihi",
            "tercih_baslangic": "08:00:00",
            "tercih_bitis": "16:00:00",
        },
    )

    assert ilk.status_code == 201
    assert ikinci.status_code == 201
    assert ikinci.json()["tercih_id"] == ilk.json()["tercih_id"]
    liste = istemci.get("/api/calisan/tercih").json()["tercihler"]
    assert len([t for t in liste if t["tarih"] == hedef]) == 1


def test_kararlanmis_tercihin_uzerine_yazilmaz() -> None:
    """Yonetici karari sessizce silinmez (409)."""
    pg_yoksa_atla()
    with OturumYerel() as oturum:
        _temizle(oturum)
        personel_id = _senaryo_kur(oturum)
        hedef_tarih = BUGUN + timedelta(days=1)
        donem = oturum.query(Donem).first()
        oturum.add(
            Tercih(
                personel_id=personel_id,
                donem_id=donem.donem_id,
                tarih=hedef_tarih,
                tip=TercihTipi.CALISMAMA,
                durum=TercihDurumu.ONAYLANDI,
            )
        )
        oturum.commit()
    istemci = _calisan_istemcisi(personel_id)

    yanit = istemci.post(
        "/api/calisan/tercih",
        json={"tarih": hedef_tarih.isoformat(), "tip": "calismama"},
    )

    assert yanit.status_code == 409


def test_ayni_gunde_yaris_durumunda_temiz_409_doner(monkeypatch: pytest.MonkeyPatch) -> None:
    """Final review bulgu 4 (yaris kismi): iki es zamanli istek de
    `personel_ve_tarihe_gore_getir` ile "mevcut yok" gorup INSERT'e girebilir;
    ikincisi `uq_tercih_personel_tarih`e (goc c4f1a7d20b93) carpar. Bunu
    SIMULE ETMEK icin bir kayit onceden yaratilir ve okuma yolu HICBIR
    ZAMAN onu gormuyormus gibi zorlanir -- gercek yaristaki ikinci istegin
    SELECT'i de tam boyle davranir (rakibinin commit'i henuz gorunur olmadan
    once baslar). Duzeltmeden once bu, yakalanmamis bir IntegrityError
    olarak 500 uretirdi."""
    pg_yoksa_atla()
    with OturumYerel() as oturum:
        _temizle(oturum)
        personel_id = _senaryo_kur(oturum)
    hedef_tarih = BUGUN + timedelta(days=1)

    with OturumYerel() as oturum:
        donem = oturum.query(Donem).first()
        oturum.add(
            Tercih(
                personel_id=personel_id,
                donem_id=donem.donem_id,
                tarih=hedef_tarih,
                tip=TercihTipi.CALISMAMA,
                durum=TercihDurumu.BEKLEMEDE,
            )
        )
        oturum.commit()

    monkeypatch.setattr(
        "app.repositories.girdi.TercihDeposu.personel_ve_tarihe_gore_getir",
        lambda self, personel_id, tarih: None,
    )

    istemci = _calisan_istemcisi(personel_id)
    yanit = istemci.post(
        "/api/calisan/tercih",
        json={"tarih": hedef_tarih.isoformat(), "tip": "calismama"},
    )

    assert yanit.status_code == 409


# --- Donem ozetim / /api/calisan/ozetim (FR-9.5, SDD 6.3.4) -----------------


def test_ozetim_ufku_yaniti_icinde_tasir() -> None:
    """SDD 6.3.4: hangi ufkun okundugu yanitin icinde durur; iki ufkun
    sayilari farklidir ve belirsiz kalirsa sayi yanlis okunur."""
    pg_yoksa_atla()
    with OturumYerel() as oturum:
        _temizle(oturum)
        personel_id = _senaryo_kur(oturum)
    istemci = _calisan_istemcisi(personel_id)

    donem_yaniti = istemci.get("/api/calisan/ozetim")
    adalet_yaniti = istemci.get("/api/calisan/ozetim?ufuk=adalet")

    assert donem_yaniti.status_code == 200
    assert donem_yaniti.json()["ufuk"] == "donem"
    assert adalet_yaniti.json()["ufuk"] == "adalet"


def test_ozetim_adalet_ufku_gecmis_atamayla_gercekten_farkli_sayilar_uretir() -> None:
    """Final review bulgu 6: eskiden `_senaryo_kur`de hicbir gecmis atama
    yoktu, bu yuzden yukaridaki test `ufuk` alaninin ECHO edildigini
    dogruluyordu ama `donem_ozetim`in `ufuk`u GERCEKTEN `AnalizServisi.
    hesapla()`ya GECIRDIGINI degil -- `ufuk` parametresi sessizce yok
    sayilsa bile o test GECERdi (iki ufuk sayisal olarak ayni cikardi).

    Bu test, doksan gunluk adalet penceresine giren YAYINLANMIS bir onceki
    donem + gece VE hafta sonuna denk bir atama ekleyen bir senaryo kurar
    (`_senaryo_kur_gecmis_donemli`) ve iki ufkun GERCEKTEN FARKLI sayilar
    urettigini kanitlar -- `ufuk` `hesapla()`ya ulasmayi bıraksa bu test
    KIRILIR.

    Ayrica bu turda hicbir backend testinin dokunmadigi alanlari da
    (`adil_pay_gece`, `adil_pay_hafta_sonu`, `hedef_saat`, `gece_havuzunda`)
    sinar.
    """
    pg_yoksa_atla()
    with OturumYerel() as oturum:
        _temizle(oturum)
        personel_id = _senaryo_kur_gecmis_donemli(oturum)
    istemci = _calisan_istemcisi(personel_id)

    donem_yaniti = istemci.get("/api/calisan/ozetim")
    adalet_yaniti = istemci.get("/api/calisan/ozetim?ufuk=adalet")
    assert donem_yaniti.status_code == 200
    assert adalet_yaniti.status_code == 200
    donem_govde = donem_yaniti.json()
    adalet_govde = adalet_yaniti.json()

    # --- Havuz uyeligi: Talep satirlari gece/hafta sonu icerdigi icin
    # personel HER IKI ufukta da havuzdadir (SDD 5.7) -- bu alan hicbir
    # backend testinde daha once dogrulanmamisti.
    assert donem_govde["gece_havuzunda"] is True
    assert donem_govde["hafta_sonu_havuzunda"] is True
    assert adalet_govde["gece_havuzunda"] is True
    assert adalet_govde["hafta_sonu_havuzunda"] is True

    # --- Yuk (SEN): donem-ici atama GUNDUZ oldugu icin donem ufkunda gece/
    # hafta sonu saati SIFIR; adalet ufku gecmis atamanin 6 saat gece + 8
    # saat hafta sonunu EKLER (bkz. fixture docstring'i).
    assert donem_govde["gece_saati"] == 0.0
    assert donem_govde["hafta_sonu_saati"] == 0.0
    assert adalet_govde["gece_saati"] == pytest.approx(6.0)
    assert adalet_govde["hafta_sonu_saati"] == pytest.approx(8.0)
    # ASIL IDDIA: iki ufuk GERCEKTEN farkli sayilar uretir.
    assert adalet_govde["gece_saati"] != donem_govde["gece_saati"]
    assert adalet_govde["hafta_sonu_saati"] != donem_govde["hafta_sonu_saati"]

    # --- Adil pay: adalet ufkunda gecmis YUK gibi gecmis PAY da eklenir
    # (Baglam.adil_paylar, `olcu` verildiginde) -- tek personelli bu
    # senaryoda pay tek basina butun talebi tasir, dolayisiyla adalet
    # ufkundaki pay donem ufkundakinden BUYUK olmali (kesin sayi degil,
    # yon dogrulanir -- `s4_hedef_paylari`/`adil_paylar` ic hesabi bu
    # testin kapsami disinda).
    assert donem_govde["adil_pay_gece"] is not None
    assert adalet_govde["adil_pay_gece"] is not None
    assert adalet_govde["adil_pay_gece"] > donem_govde["adil_pay_gece"]
    assert donem_govde["adil_pay_hafta_sonu"] is not None
    assert adalet_govde["adil_pay_hafta_sonu"] is not None
    assert adalet_govde["adil_pay_hafta_sonu"] > donem_govde["adil_pay_hafta_sonu"]

    # --- hedef_saat VE toplam_saat: saat dengesi de artik ufku izler.
    #
    # Bu satir eskiden ikisinin ESIT oldugunu iddia ediyordu ve o iddia bir
    # HATAYI sabitliyordu: hedef gecmisi katiyordu (`s4_hedef_paylari`,
    # `baglam.gecmis` doluysa kosulsuz), yuk ise yalniz donem icini
    # sayiyordu. Gercek veride olculdu: toplam 52,0 karsisinda hedef 212,4
    # -- HERKES hedefinin yuz altmis saat altinda gorunuyordu, her iki
    # ufukta da. Iki taraf ayni pencereden okunmak zorunda; S4'un
    # `dogrula`si zaten boyle yapar (yuke gecmis saati ekler).
    assert adalet_govde["hedef_saat"] > donem_govde["hedef_saat"]
    assert adalet_govde["toplam_saat"] > donem_govde["toplam_saat"]


def test_ozetim_yayin_yoksa_null_doner() -> None:
    """404 DEGIL: "henuz cizelge yok" bir hata degil bir durumdur."""
    pg_yoksa_atla()
    with OturumYerel() as oturum:
        _temizle(oturum)
        personel = Personel(
            ad_soyad=_benzersiz("Ozetsiz"),
            sicil_no=_benzersiz("S"),
            haftalik_hedef_saat=40,
            aktif_baslangic=BUGUN - timedelta(days=30),
        )
        oturum.add(personel)
        oturum.commit()
        personel_id = personel.personel_id
    istemci = _calisan_istemcisi(personel_id)

    yanit = istemci.get("/api/calisan/ozetim")

    assert yanit.status_code == 200
    assert yanit.json() is None


def test_vardiyalarim_artik_ozet_tasimaz() -> None:
    """Ozet ayri uc noktada; panelin her acilisi bir tam hesapla() odemez."""
    pg_yoksa_atla()
    with OturumYerel() as oturum:
        _temizle(oturum)
        personel_id = _senaryo_kur(oturum)
    istemci = _calisan_istemcisi(personel_id)

    yanit = istemci.get("/api/calisan/vardiyalarim")

    assert yanit.status_code == 200
    assert "ozet" not in yanit.json()
