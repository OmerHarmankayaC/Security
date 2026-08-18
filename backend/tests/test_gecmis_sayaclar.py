"""Donem oncesi birikim (SRS TD-6, SDD 5.9).

Bu dosyanin kilitledigi dort sozlesme:

  1. **Sayim yayinlanmis surumlerden gelir** ve bir donemin yalniz EN SON
     yayinlananindan. Arsiv sayilsaydi gecmis iki kez, taslak sayilsaydi
     henuz gerceklesmemis bir cizelge gecmis olarak sayilirdi.
  2. **Ufkun ortasina dusen donemin yalniz pencereye giren gunleri** sayilir.
  3. **Calisabilirlik orani payi kucultur.** Ufkun yarisinda ise baslayan
     personel tam payla olculseydi sapmasi hicbir cizelgeyle kapatilamazdi.
  4. **Yasal devir turetilen + kayit alanidir**; biri digerinin yerine gecmez.
"""

import uuid
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import select

from app.db import OturumYerel
from app.kurallar.gecmis import GecmisYuk
from app.models.girdi import Musaitlik, MusaitlikDilimi, MusaitlikTipi
from app.models.sonuc import (
    Atama,
    AtamaKaynagi,
    CizelgeSurumu,
    CizelgeSurumuDurumu,
    Donem,
)
from app.models.tanim import GorevNoktasi, Personel
from app.services.gecmis_sayaclar import GecmisSayaclar
from tests.conftest import pg_yoksa_atla

# Donem 3 planlanacak olan; 1 ve 2 gecmiste ve yayinlanmis.
D3_BAS = date(2026, 3, 2)
D2_BAS = D3_BAS - timedelta(days=7)
D1_BAS = D3_BAS - timedelta(days=14)


def _donem(oturum, bas: date) -> Donem:
    donem = Donem(
        baslangic_tarihi=bas,
        bitis_tarihi=bas + timedelta(days=6),
        tercih_son_tarihi=bas - timedelta(days=7),
    )
    oturum.add(donem)
    oturum.flush()
    return donem


def _surum(oturum, donem: Donem, no: int, durum: CizelgeSurumuDurumu) -> CizelgeSurumu:
    surum = CizelgeSurumu(donem_id=donem.donem_id, surum_no=no, durum=durum)
    oturum.add(surum)
    oturum.flush()
    return surum


def _blok(oturum, surum, personel, nokta, gun: date, bas_saat: int, sure: int) -> None:
    baslangic = datetime.combine(gun, datetime.min.time()).replace(hour=bas_saat)
    oturum.add(
        Atama(
            surum_id=surum.surum_id,
            personel_id=personel.personel_id,
            nokta_id=nokta.nokta_id,
            baslangic_zamani=baslangic,
            bitis_zamani=baslangic + timedelta(hours=sure),
            kaynak=AtamaKaynagi.COZUCU,
        )
    )


@pytest.fixture
def senaryo() -> dict:
    """Iki gecmis donem, iki personel; biri ufkun ORTASINDA ise basliyor."""
    pg_yoksa_atla()
    on_ek = uuid.uuid4().hex[:8]
    oturum = OturumYerel()
    try:
        nokta = GorevNoktasi(ad=f"Guvenlik-{on_ek}")
        oturum.add(nokta)
        # Tam ufuk boyunca calisabilir.
        tam = Personel(
            sicil_no=f"T-{on_ek}",
            ad_soyad=f"Tam {on_ek}",
            aktif_baslangic=D3_BAS - timedelta(days=365),
            haftalik_hedef_saat=40,
        )
        # Ufkun ortasinda ise baslamis: calisabilirlik orani ~yarim.
        yarim = Personel(
            sicil_no=f"Y-{on_ek}",
            ad_soyad=f"Yarim {on_ek}",
            aktif_baslangic=D3_BAS - timedelta(days=45),
            haftalik_hedef_saat=40,
        )
        oturum.add_all([tam, yarim])
        oturum.flush()

        d1, d2, d3 = _donem(oturum, D1_BAS), _donem(oturum, D2_BAS), _donem(oturum, D3_BAS)
        # D1: hem ARSIV hem YAYIN surumu var — yalniz yayin sayilmali.
        arsiv = _surum(oturum, d1, 1, CizelgeSurumuDurumu.ARSIV)
        d1_yayin = _surum(oturum, d1, 2, CizelgeSurumuDurumu.YAYINLANDI)
        d2_yayin = _surum(oturum, d2, 1, CizelgeSurumuDurumu.YAYINLANDI)
        taslak = _surum(oturum, d2, 2, CizelgeSurumuDurumu.TASLAK)

        # Arsiv ve taslak: sayilmamalari gerekiyor, bol saat koyuyoruz ki
        # sayilirlarsa test yuksek sesle patlasin.
        _blok(oturum, arsiv, tam, nokta, D1_BAS, 8, 12)
        _blok(oturum, taslak, tam, nokta, D2_BAS, 8, 12)

        # Gercek gecmis: `tam` iki gece blogu, `yarim` bir gunduz blogu.
        _blok(oturum, d1_yayin, tam, nokta, D1_BAS, 20, 8)  # 20-04: 8 saat gece
        _blok(oturum, d2_yayin, tam, nokta, D2_BAS, 20, 8)
        _blok(oturum, d2_yayin, yarim, nokta, D2_BAS, 8, 8)  # gunduz, gece 0
        # Hafta sonu blogu: D1_BAS + 5 gun = cumartesi mi? gun.weekday()>=5
        hs_gun = next(
            D1_BAS + timedelta(days=i)
            for i in range(7)
            if (D1_BAS + timedelta(days=i)).weekday() >= 5
        )
        _blok(oturum, d1_yayin, tam, nokta, hs_gun, 8, 8)
        oturum.commit()
        return {
            "donem3_id": d3.donem_id,
            "nokta_id": nokta.nokta_id,
            "tam_id": tam.personel_id,
            "yarim_id": yarim.personel_id,
            "hs_gun": hs_gun,
        }
    finally:
        oturum.close()


def _hesapla(donem_id: int, ufuk: int = 90, *, erisim: bool = False) -> GecmisYuk:
    oturum = OturumYerel()
    try:
        donem = oturum.get(Donem, donem_id)
        assert donem is not None
        erisebilen = None
        if erisim:
            noktalar = oturum.execute(select(GorevNoktasi)).scalars().all()
            kisiler = frozenset(
                p.personel_id for p in oturum.execute(select(Personel)).scalars().all()
            )
            erisebilen = {n.nokta_id: kisiler for n in noktalar}
        return GecmisSayaclar(oturum).hesapla(donem, ufuk, erisebilen=erisebilen)
    finally:
        oturum.close()


def test_arsiv_ve_taslak_surumler_sayilmaz(senaryo: dict) -> None:
    """Arsiv gecmisi IKI KEZ sayar, taslak ise HENUZ OLMAMIS bir cizelgeyi yazar."""
    yuk = _hesapla(senaryo["donem3_id"])
    sayac = yuk.sayac(senaryo["tam_id"])
    # Yayinlanan bloklar: 8 + 8 gece + 8 hafta sonu = 24 saat.
    # Arsiv (12) ve taslak (12) sayilsaydi 48 cikardi.
    assert sayac.toplam_saat == pytest.approx(24.0)


def test_gece_ve_hafta_sonu_ayri_olculur(senaryo: dict) -> None:
    yuk = _hesapla(senaryo["donem3_id"])
    tam = yuk.sayac(senaryo["tam_id"])
    yarim = yuk.sayac(senaryo["yarim_id"])
    # Iki adet 20.00-04.00 blogu: her biri 20-24 ve 00-04 = 8 saat gece.
    assert tam.gece_saat == pytest.approx(16.0)
    assert tam.hafta_sonu_saat == pytest.approx(8.0)
    # Gunduz blogu gece saati uretmez.
    assert yarim.gece_saat == pytest.approx(0.0)
    assert yarim.toplam_saat == pytest.approx(8.0)


def test_ufuk_kisaldiginda_pencereye_girmeyen_donem_dusuyor(senaryo: dict) -> None:
    """Ufuk bir donemin ORTASINA duserse o donemin yalniz pencereye giren gunleri sayilir.

    On gunluk pencere D2'yi tumuyle, D1'i KISMEN kapsar: D1'in hafta sonu
    blogu (D1_BAS+5) pencereye girer, ilk gunundeki gece blogu girmez. Filtre
    donemin tamamina degil BLOGUN BASLADIGI GUNE bakar (TD-1); doneme
    bakilsaydi ya donemin tamami sayilir ya hepsi duserdi.
    """
    dar = _hesapla(senaryo["donem3_id"], ufuk=10)
    # D2 gece blogu (8) + D1'in pencereye giren hafta sonu blogu (8).
    # D1'in ilk gunundeki gece blogu pencerenin disinda kaldi.
    assert dar.sayac(senaryo["tam_id"]).toplam_saat == pytest.approx(16.0)
    assert dar.sayac(senaryo["tam_id"]).gece_saat == pytest.approx(8.0)

    genis = _hesapla(senaryo["donem3_id"], ufuk=90)
    assert genis.sayac(senaryo["tam_id"]).toplam_saat == pytest.approx(24.0)
    assert genis.sayac(senaryo["tam_id"]).gece_saat == pytest.approx(16.0)


def test_ufkun_ortasinda_baslayan_personelin_orani_yaklasik_yarim(senaryo: dict) -> None:
    """SRS TD-6: tam payla olculse sapmasi HICBIR cizelgeyle kapatilamazdi."""
    yuk = _hesapla(senaryo["donem3_id"], ufuk=90)
    assert yuk.oran(senaryo["tam_id"]) == pytest.approx(1.0)
    # 45 gun once basladi, ufuk 90 gun.
    assert yuk.oran(senaryo["yarim_id"]) == pytest.approx(0.5, abs=0.02)


def test_tam_gun_izin_calisabilir_gunu_dusurur(senaryo: dict) -> None:
    """Yarim gun izin gunu DUSURMEZ: o gun calisabilir durumdadir."""
    oturum = OturumYerel()
    try:
        oturum.add(
            Musaitlik(
                personel_id=senaryo["tam_id"],
                baslangic_tarihi=D3_BAS - timedelta(days=20),
                bitis_tarihi=D3_BAS - timedelta(days=11),
                dilim=MusaitlikDilimi.TAM_GUN,
                tip=MusaitlikTipi.YILLIK_IZIN,
            )
        )
        oturum.add(
            Musaitlik(
                personel_id=senaryo["yarim_id"],
                baslangic_tarihi=D3_BAS - timedelta(days=20),
                bitis_tarihi=D3_BAS - timedelta(days=11),
                dilim=MusaitlikDilimi.OGLEDEN_ONCE,
                tip=MusaitlikTipi.YILLIK_IZIN,
            )
        )
        oturum.commit()
    finally:
        oturum.close()
    yuk = _hesapla(senaryo["donem3_id"], ufuk=90)
    # On gunluk tam gun izin: 90 gunun 80'i kalir.
    assert yuk.oran(senaryo["tam_id"]) == pytest.approx(80 / 90, abs=0.02)
    # Yarim gun izin oranı degistirmez.
    assert yuk.oran(senaryo["yarim_id"]) == pytest.approx(0.5, abs=0.02)


def test_gecmis_pay_erisebilenler_arasinda_bolunur(senaryo: dict) -> None:
    """Gecmis yuk paya donem talebiyle AYNI islemden gecerek girer.

    Ikisi ayni islemden gecmezse yuk ile hedef farkli birimlerde olculur ve
    sapma anlamini kaybeder.
    """
    yuk = _hesapla(senaryo["donem3_id"], erisim=True)
    # Toplam gecmis 32 saat (tam 24 + yarim 8), iki kisiye bolunur.
    assert yuk.pay_toplam[senaryo["tam_id"]] == pytest.approx(16.0)
    assert yuk.pay_toplam[senaryo["yarim_id"]] == pytest.approx(16.0)
    # Gece 16 saat, ikiye bolunur — yuku tasimayan da payini alir.
    assert yuk.pay_gece[senaryo["yarim_id"]] == pytest.approx(8.0)


def test_erisim_verilmezse_pay_hesaplanmaz(senaryo: dict) -> None:
    """Sayac ile pay AYRI: cagiran yalniz sayaci isteyebilir."""
    yuk = _hesapla(senaryo["donem3_id"], erisim=False)
    assert yuk.pay_toplam == {}
    assert yuk.sayac(senaryo["tam_id"]).toplam_saat > 0


def test_yasal_devir_turetileni_ve_kayit_alanini_toplar(senaryo: dict) -> None:
    """SRS TD-6: kayit alani turetilen degerin YERINE GECMEZ, ona eklenir."""
    oturum = OturumYerel()
    try:
        kisi = oturum.get(Personel, senaryo["tam_id"])
        assert kisi is not None
        kisi.devir_fazla_calisma_saat = 30
        kisi.kota_yili = D3_BAS.year
        oturum.commit()

        donem = oturum.get(Donem, senaryo["donem3_id"])
        assert donem is not None
        # Esik 10 saat: haftalik toplamlar esigi asar ve turetilen deger >0 olur.
        dusuk_esik = GecmisSayaclar(oturum).yasal_devir(donem, esik=10.0)
        # Esik 100 saat: hicbir hafta asmaz, geriye yalniz kayit alani kalir.
        yuksek_esik = GecmisSayaclar(oturum).yasal_devir(donem, esik=100.0)
    finally:
        oturum.close()

    assert yuksek_esik[senaryo["tam_id"]] == pytest.approx(30.0)
    assert dusuk_esik[senaryo["tam_id"]] > 30.0
