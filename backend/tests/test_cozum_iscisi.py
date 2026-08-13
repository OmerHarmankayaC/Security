"""Cozum iscisi ve durdurma (SDD 3.4.4, 5.4, 6.3.2).

`CozumServisi.baslat` artik surec ACMAZ; isi kuyruga yazar ve ayri bir
servis (scripts/cozum_iscisi.py) alir. Bu dosya o sozlesmeyi dogrular:
kuyruga yazma, yarisa kapali is kapma, durdurma istegi ve durdurulan isin
HICBIR sonuc yazmamasi.

Canli bir PostgreSQL gerektirir; baglanamiyorsa atlanir.
"""

import time as zaman
import uuid
from datetime import date, time, timedelta

import pytest
from sqlalchemy import select

from app.db import OturumYerel
from app.models.kural import Kural, KuralTipi
from app.models.sonuc import Atama, CizelgeSurumu, CozumIsiDurumu, Donem, KapsamaAcigi
from app.models.tanim import GorevNoktasi, GunTipi, Personel, Talep
from app.repositories.sonuc import CozumIsiDeposu
from app.services.cozum_servisi import CozumServisi
from scripts.cozum_iscisi import siradaki_isi_isle, siradaki_isi_kap
from tests.conftest import isi_calistir_ve_bekle, pg_yoksa_atla, senaryo_verisini_temizle

# S1 SART: kapsama kisitini (ve dolayisiyla atama uretme nedenini) o kurar.
# Yalniz H1-H8 yuklenirse model bos bir amac fonksiyonuyla cozulur, hicbir
# atama uretilmez ve is "tamamlandi" gorunur.
_KURALLAR: list[tuple[str, KuralTipi, dict, int | None]] = [
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
    ("S7", KuralTipi.ESNEK, {}, 2),
    ("S8", KuralTipi.ESNEK, {}, 8),
]


def _benzersiz(on_ek: str) -> str:
    return f"{on_ek}-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def kurulum() -> dict[str, int]:
    """Kucuk, cozulebilir bir ornek: 3 personel, 7 gun, tek nokta."""
    pg_yoksa_atla()
    on_ek = _benzersiz("isci")
    oturum = OturumYerel()
    try:
        senaryo_verisini_temizle(oturum)

        nokta = GorevNoktasi(ad=f"Nokta-{on_ek}")
        oturum.add(nokta)
        oturum.add_all(
            Personel(
                ad_soyad=f"P{i}-{on_ek}",
                sicil_no=_benzersiz(f"IS{i}"),
                haftalik_hedef_saat=40,
                aktif_baslangic=date(2026, 1, 1),
            )
            for i in range(1, 4)
        )
        oturum.add_all(
            Kural(kimlik=kimlik, tip=tip, parametreler=parametreler, agirlik=agirlik, aktif=True)
            for kimlik, tip, parametreler, agirlik in _KURALLAR
        )
        oturum.flush()

        baslangic = date(2026, 4, 6)
        for gun_ofset in range(7):
            oturum.add(
                Talep(
                    nokta_id=nokta.nokta_id,
                    baslangic=time(8, 0),
                    bitis=time(16, 0),
                    gun_tipi=GunTipi.HAFTA_ICI,
                    tarih=baslangic + timedelta(days=gun_ofset),
                    gereken_sayi=1,
                )
            )
        donem = Donem(
            baslangic_tarihi=baslangic,
            bitis_tarihi=baslangic + timedelta(days=6),
            tercih_son_tarihi=baslangic - timedelta(days=7),
        )
        oturum.add(donem)
        oturum.commit()
        return {"donem_id": donem.donem_id}
    finally:
        oturum.close()


def test_baslat_surec_acmaz_isi_kuyrukta_birakir(kurulum: dict[str, int]) -> None:
    """SDD 3.4.4: API cozum calistirmaz, yalniz kuyruga yazar."""
    oturum = OturumYerel()
    try:
        is_kaydi = CozumServisi(oturum).baslat(kurulum["donem_id"], zaman_limiti_saniye=10)
        assert is_kaydi is not None
        is_id = is_kaydi.is_id
    finally:
        oturum.close()

    # Isci hic calismadan durum degismemeli.
    oturum = OturumYerel()
    try:
        assert CozumIsiDeposu(oturum).getir(is_id).durum == CozumIsiDurumu.KUYRUKTA
    finally:
        oturum.close()


def test_isci_kuyruktaki_isi_alip_calistirir(kurulum: dict[str, int]) -> None:
    oturum = OturumYerel()
    try:
        is_id = CozumServisi(oturum).baslat(kurulum["donem_id"], zaman_limiti_saniye=10).is_id
    finally:
        oturum.close()

    assert isi_calistir_ve_bekle(is_id) in (CozumIsiDurumu.TAMAMLANDI, CozumIsiDurumu.UYARILI)

    oturum = OturumYerel()
    try:
        surum_id = CozumIsiDeposu(oturum).getir(is_id).surum_id
        atamalar = oturum.execute(select(Atama).where(Atama.surum_id == surum_id)).scalars().all()
        assert atamalar, "Tamamlanan isin atamalari yazilmis olmali"
    finally:
        oturum.close()


def test_bos_kuyrukta_isci_none_doner(kurulum: dict[str, int]) -> None:
    oturum = OturumYerel()
    try:
        assert siradaki_isi_isle(oturum) is None
    finally:
        oturum.close()


def test_ayni_is_iki_kez_kapilamaz(kurulum: dict[str, int]) -> None:
    """Yarisa kapali kapma: `UPDATE ... WHERE durum='KUYRUKTA' RETURNING`
    ilk cagriya isi verir, ikincisi ayni isi ALAMAZ. Iki isci es zamanli
    calistiginda ayni is iki kez cozulmemelidir."""
    oturum = OturumYerel()
    try:
        is_id = CozumServisi(oturum).baslat(kurulum["donem_id"], zaman_limiti_saniye=10).is_id
    finally:
        oturum.close()

    birinci = OturumYerel()
    ikinci = OturumYerel()
    try:
        assert siradaki_isi_kap(birinci) == is_id
        assert siradaki_isi_kap(ikinci) is None
    finally:
        birinci.close()
        ikinci.close()


def test_kuyruktayken_durdurulan_is_hic_alinmaz(kurulum: dict[str, int]) -> None:
    """Kapma sorgusu yalnizca `kuyrukta` durumundakileri secer; API'nin
    DURDURULDU'ya cektigi bir is isciye hic gitmez.

    Is, elinde hicbir sonuc olmadan karar bekler - cozucu hic calismadigi
    icin `gecici_sonuc` bostur ve arayuz "kullan"i pasif gosterir."""
    oturum = OturumYerel()
    try:
        is_kaydi = CozumServisi(oturum).baslat(kurulum["donem_id"], zaman_limiti_saniye=10)
        is_id = is_kaydi.is_id
        # API'nin /durdur ucunun yaptigi sey:
        is_kaydi.durum = CozumIsiDurumu.DURDURULDU
        oturum.commit()
    finally:
        oturum.close()

    calisan = OturumYerel()
    try:
        assert siradaki_isi_kap(calisan) is None
    finally:
        calisan.close()

    oturum = OturumYerel()
    try:
        is_son = CozumIsiDeposu(oturum).getir(is_id)
        assert is_son.durum == CozumIsiDurumu.DURDURULDU
        assert is_son.gecici_sonuc is None
    finally:
        oturum.close()


def test_cozum_sirasinda_durdurma_surume_hicbir_sey_yazmaz(
    kurulum: dict[str, int], monkeypatch: pytest.MonkeyPatch
) -> None:
    """SDD 5.4.1: durdurma cozumu ATMAZ ama SURUME DE YAZMAZ.

    Bulunan cozum `gecici_sonuc`a gider ve kullanici karari beklenir;
    atama, kapsama acigi ve surum durumu dokunulmamis kalir. "At" kararinin
    bedelsiz olmasi tam olarak buna dayanir.

    Durdurma istegi cozum SURERKEN gelmis gibi davranmak icin, kontrol
    ilk cagrisinda dogru doner - yani arama ilk yoklamada sonlandirilir.
    """
    import app.services.cozum_servisi as cozum_modulu

    oturum = OturumYerel()
    try:
        is_kaydi = CozumServisi(oturum).baslat(kurulum["donem_id"], zaman_limiti_saniye=20)
        is_id = is_kaydi.is_id
        surum_id = is_kaydi.surum_id
    finally:
        oturum.close()

    gercek_kontrol = cozum_modulu._durdurma_istendi_mi

    def sahte_kontrol(oturum_, is_kaydi_):  # noqa: ANN001, ANN202 - test sahtesi
        # Model kurulduktan SONRAKI ilk kontrolde henuz istek yok; arama
        # basladiktan sonraki yoklamada durdurma istenmis gibi davranilir.
        if is_kaydi_.durum == CozumIsiDurumu.COZULUYOR:
            return True
        return gercek_kontrol(oturum_, is_kaydi_)

    monkeypatch.setattr(cozum_modulu, "_durdurma_istendi_mi", sahte_kontrol)

    calisan = OturumYerel()
    try:
        assert siradaki_isi_isle(calisan) == is_id
    finally:
        calisan.close()

    oturum = OturumYerel()
    try:
        is_son = CozumIsiDeposu(oturum).getir(is_id)
        assert is_son.durum == CozumIsiDurumu.DURDURULDU
        assert is_son.bitis_zamani is not None

        atamalar = oturum.execute(select(Atama).where(Atama.surum_id == surum_id)).scalars().all()
        acilar = (
            oturum.execute(select(KapsamaAcigi).where(KapsamaAcigi.surum_id == surum_id))
            .scalars()
            .all()
        )
        assert atamalar == [], "Durdurulan is atama YAZMAMALI"
        assert acilar == [], "Durdurulan is kapsama acigi YAZMAMALI"

        surum = oturum.execute(
            select(CizelgeSurumu).where(CizelgeSurumu.surum_id == surum_id)
        ).scalar_one()
        assert surum.durum.value == "taslak", "Durdurulan is surumu cozuldu'ye cekmemeli"

        # Cozum ATILMADI: karar verilene kadar gecici sonucta duruyor.
        assert is_son.gecici_sonuc is not None
        assert is_son.gecici_sonuc["atamalar"], "Bulunmus cozum gecici sonuca yazilmali"
    finally:
        oturum.close()


def test_durdurma_yeni_bir_ara_cozum_beklemeden_uygulanir(kurulum: dict[str, int]) -> None:
    """SDD 5.4.2 / SRS NFR-14: istek, cozucu daha iyi bir cozum bulmasa da
    uygulanir.

    Eski yolda durdurma yalnizca ara cozum geri cagiriminda okunuyordu;
    geri cagirim da yalnizca cozucu DAHA IYI bir cozum buldugunda
    tetikleniyor, dolayisiyla istek iki iyilesme arasindaki sessizlikte
    zaman limitine kadar bekleyebiliyordu. Buradaki sahte kol HIC ilerleme
    bildirmez - eski yolda bu test sonsuza kadar beklerdi.
    """
    from app.services.cozum_servisi import _aramayi_sur

    oturum = OturumYerel()
    try:
        is_kaydi = CozumServisi(oturum).baslat(kurulum["donem_id"], zaman_limiti_saniye=600)
        is_id = is_kaydi.is_id
    finally:
        oturum.close()

    class _SahteKol:
        """Durdurulana kadar bitmeyen, hic ara cozum bildirmeyen arama."""

        def __init__(self) -> None:
            self.durduruldu = False

        def bekle(self, saniye: float) -> bool:
            if self.durduruldu:
                return True
            zaman.sleep(saniye)
            return False

        def son_ilerleme(self) -> None:
            return None

        def durdur(self) -> None:
            self.durduruldu = True

    isci_oturumu = OturumYerel()
    api_oturumu = OturumYerel()
    try:
        is_calisan = CozumIsiDeposu(isci_oturumu).getir(is_id)
        is_calisan.durum = CozumIsiDurumu.COZULUYOR
        isci_oturumu.commit()

        # API'nin /durdur ucunun yaptigi sey - BASKA bir baglantidan:
        CozumIsiDeposu(api_oturumu).getir(is_id).durum = CozumIsiDurumu.DURDURULDU
        api_oturumu.commit()

        kol = _SahteKol()
        basla = zaman.monotonic()
        _aramayi_sur(isci_oturumu, is_calisan, kol)  # type: ignore[arg-type]
        gecen = zaman.monotonic() - basla

        assert kol.durduruldu, "Ana dongu durdurma istegini gormeli"
        assert gecen < 5, f"Durdurma {gecen:.1f} saniye surdu; yoklama araligi kadar olmali"
    finally:
        isci_oturumu.close()
        api_oturumu.close()
