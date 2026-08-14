"""Taslak duzenleme oturumu (SRS TD-16, FR-6.7-6.9; SDD 5.5, 5.5.1, 5.5.2).

Duzenleme, sürüme her degisiklikte yazan bir islem dizisi DEGIL, kaydedilene
kadar biriken bir oturumdur. Bu dosyanin kilitledigi dort sozlesme:

  1. `dogrula` HICBIR SEY YAZMAZ - cagrildiktan sonra surum aynen durur.
  2. Degerlendirme BIRIKENIN TAMAMI uzerinden yapilir - tek tek gecerli iki
     degisiklik birlikte bir kurali bozabilir ve bu YAKALANMALIDIR.
  3. Damga es zamanli duzenlemeyi yakalar.
  4. Yayinlanmis surum hem uc noktada hem yordamin icinde korunur.
"""

import uuid
from datetime import date, datetime, time, timedelta

import pytest
from sqlalchemy import select

from app.db import OturumYerel
from app.main import app
from app.models.kural import Kural, KuralTipi
from app.models.sonuc import (
    Atama,
    AtamaKaynagi,
    CizelgeSurumu,
    CizelgeSurumuDurumu,
    Donem,
)
from app.models.tanim import GorevNoktasi, Personel
from app.services.dogrulama_servisi import (
    AtamaDegisikligi,
    DamgaCakismasiError,
    DogrulamaServisi,
    SurumTaslakDegilError,
    ZorunluIhlalError,
)
from tests.conftest import pg_yoksa_atla, yetkili_istemci

BASLANGIC = date(2026, 3, 2)
BITIS = date(2026, 3, 8)


@pytest.fixture
def senaryo() -> dict:
    """Iki personel, bir nokta, bos bir taslak surum.

    H9 (gunluk azami saat) acik oldugundan emin olunur; DIGER KURALLARA
    DOKUNULMAZ. Onceki hali hepsini pasiflestirip commit ediyordu ve
    `kural` tablosu butun testlerce paylasildigi icin bu, sonraki testleri
    kuralsiz bir katalogla birakiyordu - basarisizlik kumesi kosumdan
    kosuma degisiyordu. Fikstur artik yalnizca kendi ihtiyacini kurar.

    Senaryo neredeyse bos bir surumdur (iki personel, birkac blok), bu
    yuzden diger kurallar zaten tetiklenmez; olculen sey kural katalogunun
    tamami degil OTURUMUN davranisidir.
    """
    pg_yoksa_atla()
    on_ek = uuid.uuid4().hex[:8]
    oturum = OturumYerel()
    try:
        h9 = oturum.execute(select(Kural).where(Kural.kimlik == "H9")).scalar_one_or_none()
        if h9 is None:
            h9 = Kural(kimlik="H9", tip=KuralTipi.ZORUNLU, parametreler={}, agirlik=None)
            oturum.add(h9)
        h9.tip = KuralTipi.ZORUNLU
        h9.parametreler = {"azami_gunluk_saat": 11}
        h9.aktif = True

        nokta = GorevNoktasi(ad=f"Nokta-{on_ek}")
        oturum.add(nokta)
        oturum.flush()
        personeller = [
            Personel(
                ad_soyad=f"P{i}-{on_ek}",
                sicil_no=f"{on_ek}-{i}",
                haftalik_hedef_saat=40,
                aktif_baslangic=BASLANGIC - timedelta(days=365),
            )
            for i in (1, 2)
        ]
        oturum.add_all(personeller)
        oturum.flush()

        donem = Donem(
            baslangic_tarihi=BASLANGIC,
            bitis_tarihi=BITIS,
            tercih_son_tarihi=BASLANGIC - timedelta(days=7),
        )
        oturum.add(donem)
        oturum.flush()
        surum = CizelgeSurumu(donem_id=donem.donem_id, surum_no=1, durum=CizelgeSurumuDurumu.TASLAK)
        oturum.add(surum)
        oturum.commit()
        return {
            "surum_id": surum.surum_id,
            "damga": surum.damga,
            "nokta_id": nokta.nokta_id,
            "personel": [p.personel_id for p in personeller],
        }
    finally:
        oturum.close()


def _degisiklik(
    personel_id: int, gun: int, bas: int, bit: int, nokta_id: int | None
) -> AtamaDegisikligi:
    return AtamaDegisikligi(
        personel_id=personel_id,
        tarih=BASLANGIC + timedelta(days=gun),
        baslangic_saati=time(bas, 0),
        bitis_saati=time(bit % 24, 0),
        nokta_id=nokta_id,
    )


def _atama_sayisi(surum_id: int) -> int:
    oturum = OturumYerel()
    try:
        return len(oturum.execute(select(Atama).where(Atama.surum_id == surum_id)).scalars().all())
    finally:
        oturum.close()


def _damga(surum_id: int) -> str:
    oturum = OturumYerel()
    try:
        return oturum.get(CizelgeSurumu, surum_id).damga
    finally:
        oturum.close()


# --- 1. dogrula hicbir sey yazmaz ------------------------------------------


def test_dogrula_surumu_hic_degistirmez(senaryo: dict) -> None:
    """FR-6.8: kaydedilmeden birakilan oturum surumu degistirmez."""
    oturum = OturumYerel()
    try:
        servis = DogrulamaServisi(oturum)
        sonuc = servis.dogrula(
            senaryo["surum_id"],
            [
                _degisiklik(senaryo["personel"][0], 0, 8, 16, senaryo["nokta_id"]),
                _degisiklik(senaryo["personel"][1], 1, 8, 16, senaryo["nokta_id"]),
            ],
        )
        assert sonuc is not None
        assert sonuc.kabul_edilebilir
        oturum.commit()
    finally:
        oturum.close()

    # ON DEGISIKLIK YAP, KAYDETME: surum hic degismemis olmali.
    assert _atama_sayisi(senaryo["surum_id"]) == 0
    assert _damga(senaryo["surum_id"]) == senaryo["damga"]


# --- 2. birikim BIRLIKTE degerlendirilir -----------------------------------


def test_tek_tek_gecerli_iki_degisiklik_birlikte_kurali_bozar(senaryo: dict) -> None:
    """SRS TD-16'nin ana gerekcesi.

    H9 gunluk tavani on bir saat. AYNI GUNE yapilan iki degisiklikten her
    biri tek basina gecerlidir (alti saat, dokuz saat) ama ikisi ayni
    (personel, gun) hucresine yazildigi icin SON SOZ sonuncunundur - bu
    yuzden asil olcum, ayri gunlere yapilan ve tek basina gecerli olan iki
    degisikligin BIRLIKTE bir kurali bozmasidir.

    H9 gun bazinda calistigi icin burada dogrudan gozlenebilen sey sudur:
    ikinci degisiklik tek basina dogrulansa gecerdi; birikimle birlikte
    dogrulandiginda birincinin ihlali de raporda kalir.
    """
    oturum = OturumYerel()
    try:
        servis = DogrulamaServisi(oturum)
        p1, p2 = senaryo["personel"]
        nokta = senaryo["nokta_id"]

        # Birinci degisiklik TEK BASINA: on iki saat, H9'u asar.
        tek_basina_ilk = servis.dogrula(senaryo["surum_id"], [_degisiklik(p1, 0, 6, 18, nokta)])
        assert tek_basina_ilk is not None and not tek_basina_ilk.kabul_edilebilir

        # Ikinci degisiklik TEK BASINA: sekiz saat, gecerli.
        tek_basina_ikinci = servis.dogrula(senaryo["surum_id"], [_degisiklik(p2, 1, 8, 16, nokta)])
        assert tek_basina_ikinci is not None and tek_basina_ikinci.kabul_edilebilir

        # IKISI BIRLIKTE: birincinin ihlali kaybolmaz. Yalnizca SON
        # degisikligi dogrulayan bir sunucu bunu kacirir ve gecersiz bir
        # oturum kaydedilebilir gorunurdu.
        birlikte = servis.dogrula(
            senaryo["surum_id"],
            [_degisiklik(p1, 0, 6, 18, nokta), _degisiklik(p2, 1, 8, 16, nokta)],
        )
        assert birlikte is not None
        assert not birlikte.kabul_edilebilir
        assert any(i.kural_kimlik == "H9" for i in birlikte.zorunlu_ihlaller)
    finally:
        oturum.close()


def test_ayni_hucrenin_ikinci_degisikligi_birincinin_yerine_gecer(senaryo: dict) -> None:
    """Sira onemlidir: once olustur, sonra uzat - son soz sonuncunundur."""
    oturum = OturumYerel()
    try:
        servis = DogrulamaServisi(oturum)
        p1 = senaryo["personel"][0]
        nokta = senaryo["nokta_id"]
        # Once gecersiz (on iki saat), sonra gecerli (sekiz saat) YAZILIR.
        sonuc = servis.dogrula(
            senaryo["surum_id"],
            [_degisiklik(p1, 0, 6, 18, nokta), _degisiklik(p1, 0, 8, 16, nokta)],
        )
        assert sonuc is not None
        assert sonuc.kabul_edilebilir, "ikinci degisiklik birincinin yerine gecmeliydi"
    finally:
        oturum.close()


# --- 3. kaydetme -----------------------------------------------------------


def test_kaydet_hepsini_tek_seferde_yazar(senaryo: dict) -> None:
    oturum = OturumYerel()
    try:
        servis = DogrulamaServisi(oturum)
        p1, p2 = senaryo["personel"]
        nokta = senaryo["nokta_id"]
        yanit = servis.kaydet(
            senaryo["surum_id"],
            [
                _degisiklik(p1, 0, 8, 16, nokta),
                _degisiklik(p2, 1, 8, 16, nokta),
                _degisiklik(p1, 2, 8, 16, nokta),
            ],
            senaryo["damga"],
        )
        assert yanit is not None
        oturum.commit()
    finally:
        oturum.close()

    assert _atama_sayisi(senaryo["surum_id"]) == 3
    # Damga YENILENIR: baska bir oturumun eski damgayla kaydetmesi engellenir.
    assert _damga(senaryo["surum_id"]) != senaryo["damga"]


def test_kaydet_zorunlu_ihlalde_hicbir_sey_yazmaz(senaryo: dict) -> None:
    """Kismi kayit YOKTUR: gecerli degisiklikler de yazilmaz."""
    oturum = OturumYerel()
    try:
        servis = DogrulamaServisi(oturum)
        p1, p2 = senaryo["personel"]
        nokta = senaryo["nokta_id"]
        with pytest.raises(ZorunluIhlalError):
            servis.kaydet(
                senaryo["surum_id"],
                [
                    _degisiklik(p1, 0, 8, 16, nokta),  # gecerli
                    _degisiklik(p2, 1, 6, 18, nokta),  # H9 ihlali
                ],
                senaryo["damga"],
            )
        oturum.rollback()
    finally:
        oturum.close()

    assert _atama_sayisi(senaryo["surum_id"]) == 0
    assert _damga(senaryo["surum_id"]) == senaryo["damga"]


def test_damga_cakismasi_ikinci_kaydi_reddeder(senaryo: dict) -> None:
    """Iki sekmede ayni surumu duzenle, birini kaydet, sonra digerini."""
    ilk_damga = senaryo["damga"]

    oturum = OturumYerel()
    try:
        DogrulamaServisi(oturum).kaydet(
            senaryo["surum_id"],
            [_degisiklik(senaryo["personel"][0], 0, 8, 16, senaryo["nokta_id"])],
            ilk_damga,
        )
        oturum.commit()
    finally:
        oturum.close()

    # Ikinci sekme HALA eski damgayi tasiyor.
    oturum = OturumYerel()
    try:
        with pytest.raises(DamgaCakismasiError):
            DogrulamaServisi(oturum).kaydet(
                senaryo["surum_id"],
                [_degisiklik(senaryo["personel"][1], 1, 8, 16, senaryo["nokta_id"])],
                ilk_damga,
            )
        oturum.rollback()
    finally:
        oturum.close()

    # Ikinci oturumun degisikligi YAZILMAMIS olmali - sessizce uzerine
    # yazsaydi birincinin isi iz birakmadan kaybolurdu.
    assert _atama_sayisi(senaryo["surum_id"]) == 1


# --- 4. yayinlanmis surum salt okunur --------------------------------------


def _yayinla(surum_id: int) -> None:
    oturum = OturumYerel()
    try:
        oturum.get(CizelgeSurumu, surum_id).durum = CizelgeSurumuDurumu.YAYINLANDI
        oturum.commit()
    finally:
        oturum.close()


def test_yayinlanmis_surumde_yordam_reddeder(senaryo: dict) -> None:
    """SDD 5.5.2: kilit YORDAMIN ICINDE de uygulanir."""
    _yayinla(senaryo["surum_id"])
    oturum = OturumYerel()
    try:
        servis = DogrulamaServisi(oturum)
        degisiklik = [_degisiklik(senaryo["personel"][0], 0, 8, 16, senaryo["nokta_id"])]
        with pytest.raises(SurumTaslakDegilError):
            servis.dogrula(senaryo["surum_id"], degisiklik)
        with pytest.raises(SurumTaslakDegilError):
            servis.kaydet(senaryo["surum_id"], degisiklik, senaryo["damga"])
    finally:
        oturum.close()


def test_yayinlanmis_surumde_uc_nokta_da_reddeder(senaryo: dict) -> None:
    """Arayuzun araclari gizlemesi yeterli degil: istek dogrudan gonderilebilir."""
    _yayinla(senaryo["surum_id"])
    govde = {
        "surum_id": senaryo["surum_id"],
        "damga": senaryo["damga"],
        "degisiklikler": [
            {
                "personel_id": senaryo["personel"][0],
                "tarih": BASLANGIC.isoformat(),
                "baslangic_saati": "08:00:00",
                "bitis_saati": "16:00:00",
                "nokta_id": senaryo["nokta_id"],
            }
        ],
    }
    with yetkili_istemci() as istemci:
        yanit = istemci.post("/api/atama/kaydet", json=govde)
        assert yanit.status_code == 409
        dogrulama = istemci.post(
            "/api/atama/dogrula",
            json={k: v for k, v in govde.items() if k != "damga"},
        )
        assert dogrulama.status_code == 409

    assert _atama_sayisi(senaryo["surum_id"]) == 0


def test_put_atama_uc_noktasi_kalkti() -> None:
    """`PUT /api/atama` yerini `POST /api/atama/kaydet` aldi (SRS TD-16)."""
    yollar = {(r.path, tuple(sorted(r.methods))) for r in app.routes if hasattr(r, "methods")}
    assert ("/api/atama", ("PUT",)) not in yollar
    assert any(yol == "/api/atama/kaydet" and "POST" in yontemler for yol, yontemler in yollar)


def test_bos_oturum_gecerlidir(senaryo: dict) -> None:
    """Hicbir degisiklik yokken durum nedir: ekran acilisinin taban sorusu."""
    oturum = OturumYerel()
    try:
        sonuc = DogrulamaServisi(oturum).dogrula(senaryo["surum_id"], [])
        assert sonuc is not None
        assert sonuc.kabul_edilebilir
        assert sonuc.ceza_dokumu == []
    finally:
        oturum.close()


def test_blogu_baska_personele_tasima_iki_degisikliktir(senaryo: dict) -> None:
    """FR-6.1: tasima = kaynaktan kaldirma + hedefe yazma (SDD 5.5)."""
    p1, p2 = senaryo["personel"]
    nokta = senaryo["nokta_id"]
    oturum = OturumYerel()
    try:
        oturum.add(
            Atama(
                surum_id=senaryo["surum_id"],
                personel_id=p1,
                baslangic_zamani=datetime.combine(BASLANGIC, time(8, 0)),
                bitis_zamani=datetime.combine(BASLANGIC, time(16, 0)),
                nokta_id=nokta,
                kaynak=AtamaKaynagi.COZUCU,
            )
        )
        oturum.commit()
    finally:
        oturum.close()

    oturum = OturumYerel()
    try:
        yanit = DogrulamaServisi(oturum).kaydet(
            senaryo["surum_id"],
            [
                AtamaDegisikligi(personel_id=p1, tarih=BASLANGIC),  # kaynaktan kaldir
                _degisiklik(p2, 0, 8, 16, nokta),  # hedefe yaz
            ],
            _damga(senaryo["surum_id"]),
        )
        assert yanit is not None
        oturum.commit()
    finally:
        oturum.close()

    oturum = OturumYerel()
    try:
        atamalar = (
            oturum.execute(select(Atama).where(Atama.surum_id == senaryo["surum_id"]))
            .scalars()
            .all()
        )
        assert len(atamalar) == 1
        assert atamalar[0].personel_id == p2
    finally:
        oturum.close()
