"""Analiz uc noktasi testleri (Sprint 3 Gun 12: SDD 5.7'deki metrikler,
SRS FR-8.x). Kucuk, elle kurulmus bir senaryo uzerinde her metrigin
beklenen degeri elle hesaplanip dogrulanir; canli PostgreSQL gerektirir.
"""

import uuid
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.db import OturumYerel
from app.models.girdi import Tercih, TercihDurumu, TercihTipi
from app.models.kural import Kural, KuralTipi
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
                baslangic_zamani=datetime.combine(date(2026, 9, 13), time(0, 0)),
                bitis_zamani=datetime.combine(date(2026, 9, 13), time(8, 0)),
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


def test_kota_satirinda_devir_ayri_yazilir(istemci: TestClient) -> None:
    """Kotayi DEVIR doldurmussa satir bunu gosterir (SDD 6.3.4).

    Kart, kalan kotasi en az olani en uste alir. Devir yazilmadiginda o satir
    "fazla calisma 0,0 sa - kalan kota 5,0 sa" olarak cikiyor ve hesap
    hatasi gibi okunuyordu: tuketimin yilin onceki bolumunden geldigi
    gorunmuyordu. Bu senaryoda donem ici fazla calisma GERCEKTEN sifirdir
    (32 saat < 45 saatlik esik); anlamli olan devirdir.
    """
    on_ek = _benzersiz("kota")
    oturum = OturumYerel()
    try:
        senaryo_verisini_temizle(oturum)

        nokta = GorevNoktasi(ad=f"Nokta-{on_ek}")
        oturum.add(nokta)
        devirli = Personel(
            ad_soyad=f"Devirli-{on_ek}",
            sicil_no=_benzersiz("KO1"),
            haftalik_hedef_saat=40,
            aktif_baslangic=date(2026, 1, 1),
            devir_fazla_calisma_saat=Decimal("265"),
        )
        temiz = Personel(
            ad_soyad=f"Temiz-{on_ek}",
            sicil_no=_benzersiz("KO2"),
            haftalik_hedef_saat=40,
            aktif_baslangic=date(2026, 1, 1),
        )
        oturum.add_all([devirli, temiz])
        oturum.flush()

        donem = Donem(
            baslangic_tarihi=date(2026, 9, 7),
            bitis_tarihi=date(2026, 9, 13),
            tercih_son_tarihi=date(2026, 8, 31),
        )
        oturum.add(donem)
        oturum.flush()

        surum = CizelgeSurumu(
            donem_id=donem.donem_id, surum_no=1, durum=CizelgeSurumuDurumu.COZULDU
        )
        oturum.add(surum)
        oturum.flush()

        # Dort gun x 8 saat = 32 saat: haftalik esigin (45) ALTINDA.
        for i in range(4):
            oturum.add(
                Atama(
                    surum_id=surum.surum_id,
                    personel_id=devirli.personel_id,
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

        oturum.commit()
        surum_id = surum.surum_id
        devirli_id = devirli.personel_id
        temiz_id = temiz.personel_id
    finally:
        oturum.rollback()
        oturum.close()

    govde = istemci.get(f"/api/analiz/{surum_id}").json()

    assert govde["yillik_kota_saat"] == pytest.approx(270.0)
    satirlar = {k["personel_id"]: k for k in govde["kota_durumu"]}

    # SIRA RISKE GORE: kalan kotasi en az olan en ustte.
    assert govde["kota_durumu"][0]["personel_id"] == devirli_id

    assert satirlar[devirli_id]["devir_saat"] == pytest.approx(265.0)
    assert satirlar[devirli_id]["fazla_calisma_saat"] == pytest.approx(0.0)
    assert satirlar[devirli_id]["kalan_kota_saat"] == pytest.approx(5.0)

    assert satirlar[temiz_id]["devir_saat"] == pytest.approx(0.0)
    assert satirlar[temiz_id]["kalan_kota_saat"] == pytest.approx(270.0)


# --- Gunluk kapsama dokumu (Gorev 6, SDD 6.3.1 Ozet ekrani gunluk seridi) --


def test_analiz_gunluk_kapsama_dokumu(istemci: TestClient) -> None:
    """Uc iddia: (1) seridin toplami `karsilanmayan_kisi_saat`e esittir -
    aralik sayisi ile kisi-saat bu projede bir kez karistirildi ve disa
    aktarma basliginda yanlis sayi basildi; (2) donemin acigi OLMAYAN
    gunleri de sifirla listeye girer, yoksa serit "veri yok" gibi bosluk
    birakir; (3) gece yarisini asan acik BASLADIGI gune yazilir (TD-1).
    """
    on_ek = _benzersiz("gkapsama")
    oturum = OturumYerel()
    try:
        senaryo_verisini_temizle(oturum)

        nokta = GorevNoktasi(ad=f"Nokta-{on_ek}")
        oturum.add(nokta)
        oturum.flush()

        # Uc gunluk donem: 09-07, 09-08, 09-09.
        donem = Donem(
            baslangic_tarihi=date(2026, 9, 7),
            bitis_tarihi=date(2026, 9, 9),
            tercih_son_tarihi=date(2026, 8, 31),
        )
        oturum.add(donem)
        oturum.flush()

        surum = CizelgeSurumu(
            donem_id=donem.donem_id, surum_no=1, durum=CizelgeSurumuDurumu.COZULDU
        )
        oturum.add(surum)
        oturum.flush()

        # 09-07 gunduz: iki kisi eksik, sekiz saat -> 16 kisi-saat.
        oturum.add(
            KapsamaAcigi(
                surum_id=surum.surum_id,
                baslangic_zamani=datetime.combine(date(2026, 9, 7), time(8, 0)),
                bitis_zamani=datetime.combine(date(2026, 9, 7), time(16, 0)),
                nokta_id=nokta.nokta_id,
                eksik_sayi=2,
            )
        )
        # 09-08 22.00 -> 09-09 06.00: gece yarisini asiyor, bir kisi eksik,
        # sekiz saat -> 8 kisi-saat. TD-1: BASLADIGI gune (09-08) yazilmali,
        # bitis gunune (09-09) degil.
        oturum.add(
            KapsamaAcigi(
                surum_id=surum.surum_id,
                baslangic_zamani=datetime.combine(date(2026, 9, 8), time(22, 0)),
                bitis_zamani=datetime.combine(date(2026, 9, 9), time(6, 0)),
                nokta_id=nokta.nokta_id,
                eksik_sayi=1,
            )
        )
        # 09-09'un kendi acigi yok; yine de listede sifirla gorunmeli.

        oturum.commit()
        surum_id = surum.surum_id
    finally:
        oturum.rollback()
        oturum.close()

    yanit = istemci.get(f"/api/analiz/{surum_id}")
    assert yanit.status_code == 200
    govde = yanit.json()

    gunluk = {g["tarih"]: g for g in govde["gunluk_kapsama"]}
    # Donemin UC gunu de listede - acigi olmayan da sifirla girer.
    assert set(gunluk) == {"2026-09-07", "2026-09-08", "2026-09-09"}

    assert gunluk["2026-09-07"]["acik_aralik_sayisi"] == 1
    assert gunluk["2026-09-07"]["karsilanmayan_kisi_saat"] == 16

    assert gunluk["2026-09-08"]["acik_aralik_sayisi"] == 1
    assert gunluk["2026-09-08"]["karsilanmayan_kisi_saat"] == 8

    assert gunluk["2026-09-09"]["acik_aralik_sayisi"] == 0
    assert gunluk["2026-09-09"]["karsilanmayan_kisi_saat"] == 0

    # Seridin toplami karsilanmayan_kisi_saat'e esittir.
    toplam = sum(g["karsilanmayan_kisi_saat"] for g in govde["gunluk_kapsama"])
    assert toplam == govde["karsilanmayan_kisi_saat"] == 24


# --- Ceza dokumunun kaynagi (Gorev 5, SDD 5.7 revizyonu) -------------------
#
# Cozum isi hic calismamis ya da atamalar isten SONRA elle degismisse
# cozucunun eski dokumu artik baska bir cizelgeyi anlatir. Bu blok o uc
# senaryoyu (cozucusuz, taze, bayatlamis) ayri ayri sinar.


def _haftalik_donem_ve_talep_kur(oturum: OturumYerel, on_ek: str):
    """Uc testin ortak fikstürü: bir nokta, iki personel, 7 gunluk donem,
    hafta ici gunduz + hafta sonu gece talebi (mevcut testlerdeki senaryonun
    aynisi - S1'in acacagi acigin nereden geldigi boylece bilinir)."""
    nokta = GorevNoktasi(ad=f"Nokta-{on_ek}")
    oturum.add(nokta)
    p1 = Personel(
        ad_soyad=f"P1-{on_ek}",
        sicil_no=_benzersiz("KY1"),
        haftalik_hedef_saat=40,
        aktif_baslangic=date(2026, 1, 1),
    )
    p2 = Personel(
        ad_soyad=f"P2-{on_ek}",
        sicil_no=_benzersiz("KY2"),
        haftalik_hedef_saat=40,
        aktif_baslangic=date(2026, 1, 1),
    )
    oturum.add_all([p1, p2])
    oturum.flush()

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
    return nokta, p1, p2, donem


def _hafta_ici_ve_cumartesi_atamalarini_kur(
    oturum: OturumYerel, surum: CizelgeSurumu, nokta: GorevNoktasi, p1: Personel, p2: Personel
) -> list[Atama]:
    """5 hafta ici gunduz (P1) + cumartesi gece (P2); PAZAR GECE BOS BIRAKILIR
    - S1'in yakalayacagi tek acik budur (8 kisi-saat)."""
    atamalar = []
    for i in range(5):
        a = Atama(
            surum_id=surum.surum_id,
            personel_id=p1.personel_id,
            baslangic_zamani=datetime.combine(date(2026, 9, 7) + timedelta(days=i), time(8, 0)),
            bitis_zamani=datetime.combine(date(2026, 9, 7) + timedelta(days=i), time(16, 0)),
            nokta_id=nokta.nokta_id,
            kaynak=AtamaKaynagi.COZUCU,
        )
        oturum.add(a)
        atamalar.append(a)
    a = Atama(
        surum_id=surum.surum_id,
        personel_id=p2.personel_id,
        baslangic_zamani=datetime.combine(date(2026, 9, 12), time(0, 0)),
        bitis_zamani=datetime.combine(date(2026, 9, 12), time(8, 0)),
        nokta_id=nokta.nokta_id,
        kaynak=AtamaKaynagi.COZUCU,
    )
    oturum.add(a)
    atamalar.append(a)
    return atamalar


def test_ceza_kaynagi_cozucusuz_surumde_kurallardan_hesaplanir(istemci: TestClient) -> None:
    """Cozum isi hic yoksa dokum ESNEK KURALLARIN KENDISINDEN hesaplanir:
    kaynak 'kurallardan', her kalemde ham x agirlik == agirlikli, ve S8 -
    aktif ve agirlikli olsa bile - hesaplanan dokumde YER ALMAZ (analiz
    baglami baglam.onceki_atamalar'i kurmuyor, o yuzden S8 anlamsizdir)."""
    on_ek = _benzersiz("kurlndn")
    oturum = OturumYerel()
    try:
        senaryo_verisini_temizle(oturum)
        # Kural katalogu bilinçli olarak S1 (ve S8) ile sinirli tutulur ki
        # beklenen ceza elle hesaplanabilsin.
        oturum.add(
            Kural(kimlik="S1", tip=KuralTipi.ESNEK, parametreler={}, agirlik=10000, aktif=True)
        )
        oturum.add(Kural(kimlik="S8", tip=KuralTipi.ESNEK, parametreler={}, agirlik=4, aktif=True))

        nokta, p1, p2, donem = _haftalik_donem_ve_talep_kur(oturum, on_ek)

        surum = CizelgeSurumu(donem_id=donem.donem_id, surum_no=1, durum=CizelgeSurumuDurumu.TASLAK)
        oturum.add(surum)
        oturum.flush()
        _hafta_ici_ve_cumartesi_atamalarini_kur(oturum, surum, nokta, p1, p2)

        oturum.commit()
        surum_id = surum.surum_id
    finally:
        oturum.rollback()
        oturum.close()

    govde = istemci.get(f"/api/analiz/{surum_id}").json()

    assert govde["ceza_kaynagi"] == "kurallardan"
    assert govde["ceza_dokumu"] == pytest.approx({"S1": 8.0})
    assert "S8" not in govde["ceza_dokumu"]
    assert govde["toplam_ceza"] == pytest.approx(80000.0)
    for kalem in govde["ceza_kalemleri"]:
        assert kalem["ham_deger"] * kalem["agirlik"] == pytest.approx(kalem["agirlikli_ceza"])


def test_ceza_kaynagi_taze_cozum_isinde_cozucu(istemci: TestClient) -> None:
    """Cozum isi TAZEYSE (atamalar isten eski/esit) kaynak 'cozucu' ve dokum
    isin KENDI dokumudur - kurallar YENIDEN calistirilmaz."""
    on_ek = _benzersiz("taze")
    oturum = OturumYerel()
    try:
        senaryo_verisini_temizle(oturum)
        nokta, p1, p2, donem = _haftalik_donem_ve_talep_kur(oturum, on_ek)

        surum = CizelgeSurumu(
            donem_id=donem.donem_id, surum_no=1, durum=CizelgeSurumuDurumu.COZULDU
        )
        oturum.add(surum)
        oturum.flush()
        _hafta_ici_ve_cumartesi_atamalarini_kur(oturum, surum, nokta, p1, p2)

        # Cozucu atamalar ile AYNI islemde yazar (SDD 5.7): is kaydinin
        # kendi dokumu, gercek acikla (S1: 8.0) BILEREK FARKLI tutulur ki
        # test "isin kendi dokumu donuyor" ile "kurallar yeniden hesaplandi"
        # ayrimini yapabilsin.
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
    finally:
        oturum.rollback()
        oturum.close()

    govde = istemci.get(f"/api/analiz/{surum_id}").json()

    assert govde["ceza_kaynagi"] == "cozucu"
    assert govde["ceza_dokumu"] == {"S1": 1000.0, "S2": 234.0}
    assert govde["toplam_ceza"] == pytest.approx(1234.0)


def test_ceza_kaynagi_atama_guncellenince_kurallara_doner(istemci: TestClient) -> None:
    """Cozulmus, taze bir surumun bir ataması ELLE (baska bir islemde)
    guncellenince kaynak KURALLARA doner ve toplam ceza degisir - eski dokum
    artik baska bir cizelgeyi anlatir (Gorev 5).

    SANIYE ALTI SIRALAMAYA DAYANMAZ: ikinci okuma AYRI BIR ISLEMDIR ve
    PostgreSQL'in her islem icin sabit `now()`'i, bir onceki islem COMMIT
    olduktan SONRA baslar - damga kesin olarak ilerler.
    """
    on_ek = _benzersiz("bayat")
    oturum = OturumYerel()
    try:
        senaryo_verisini_temizle(oturum)
        oturum.add(
            Kural(kimlik="S1", tip=KuralTipi.ESNEK, parametreler={}, agirlik=10000, aktif=True)
        )

        nokta, p1, p2, donem = _haftalik_donem_ve_talep_kur(oturum, on_ek)

        surum = CizelgeSurumu(
            donem_id=donem.donem_id, surum_no=1, durum=CizelgeSurumuDurumu.COZULDU
        )
        oturum.add(surum)
        oturum.flush()
        atamalar = _hafta_ici_ve_cumartesi_atamalarini_kur(oturum, surum, nokta, p1, p2)

        oturum.add(
            CozumIsi(
                surum_id=surum.surum_id,
                durum=CozumIsiDurumu.UYARILI,
                baslangic_zamani=datetime.now(UTC),
                bitis_zamani=datetime.now(UTC),
                zaman_limiti_saniye=60,
                en_iyi_ceza=1234,
                ceza_dokumu={"S1": 1000.0},
                kural_anlik_goruntu={},
            )
        )
        oturum.commit()
        surum_id = surum.surum_id
        guncellenecek_atama_id = atamalar[0].atama_id
    finally:
        oturum.rollback()
        oturum.close()

    ilk = istemci.get(f"/api/analiz/{surum_id}").json()
    assert ilk["ceza_kaynagi"] == "cozucu"
    assert ilk["toplam_ceza"] == pytest.approx(1234.0)

    # AYRI bir islemde elle duzenleme: kilit acikca cevrilir, kapsamayi
    # etkilemez ama guncelleme_zamani'ni ILERLETIR.
    oturum2 = OturumYerel()
    try:
        atama = oturum2.get(Atama, guncellenecek_atama_id)
        assert atama is not None
        atama.kilitli = True
        oturum2.commit()
    finally:
        oturum2.close()

    sonra = istemci.get(f"/api/analiz/{surum_id}").json()
    assert sonra["ceza_kaynagi"] == "kurallardan"
    assert sonra["ceza_dokumu"] == pytest.approx({"S1": 8.0})
    assert sonra["toplam_ceza"] == pytest.approx(80000.0)
    assert sonra["toplam_ceza"] != pytest.approx(1234.0)
