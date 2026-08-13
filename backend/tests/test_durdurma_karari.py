"""Durdurma ve kullanici karari (SRS FR-4.9 - FR-4.11; SDD 4.2.4, 5.4.1, 6.1).

Durdurma artik tek yonlu bir iptal degil: arama sonlanir, bulunmus cozum
`gecici_sonuc`ta saklanir ve kullanici uc secenekten birini secer -
kullan / at / devam.

Bu dosyanin olctugu asil sey, gecici sonucun BIR OKUMA YUZEYI OLMAMASIDIR.
Ayni bilginin atama tablosu disinda ikinci bir yerde durmasi, bu projede
birkac kez bedeli odenmis bir kalip; kabul edilebilir olmasinin tek nedeni
alanin tek yonlu ve tek seferlik bir aktarim tamponu olmasi. Test bunu
dogruluyor: isci bir kez yazar, karar bir kez okuyup bosaltir, arada hicbir
okuma ucu ondan beslenmez.

Canli bir PostgreSQL gerektirir; baglanamiyorsa atlanir.
"""

import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy import select

from app.db import OturumYerel
from app.models.kimlik import Rol
from app.models.kural import Kural, KuralTipi
from app.models.sonuc import (
    Atama,
    CizelgeSurumu,
    CizelgeSurumuDurumu,
    CozumIsi,
    CozumIsiDurumu,
    Donem,
    KapsamaAcigi,
)
from app.models.tanim import GorevNoktasi, GunTipi, Personel, Talep, VardiyaTipi
from app.repositories.sonuc import CozumIsiDeposu
from app.services.cozum_servisi import (
    CozumServisi,
    Karar,
    KararUygulanamazError,
    durdurma_karari_uygula,
)
from scripts.cozum_iscisi import siradaki_isi_kap
from tests.conftest import (
    isi_calistir_ve_bekle,
    pg_yoksa_atla,
    senaryo_verisini_temizle,
    yetkili_istemci,
)

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
    on_ek = _benzersiz("karar")
    oturum = OturumYerel()
    try:
        senaryo_verisini_temizle(oturum)

        vardiya = VardiyaTipi(
            ad=f"Gunduz-{on_ek}",
            baslangic_saati="08:00",
            bitis_saati="16:00",
            sure_saat=8,
            gece_mi=False,
        )
        oturum.add(vardiya)
        nokta = GorevNoktasi(ad=f"Nokta-{on_ek}")
        oturum.add(nokta)
        oturum.add_all(
            Personel(
                ad_soyad=f"P{i}-{on_ek}",
                sicil_no=_benzersiz(f"KR{i}"),
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
                    baslangic=vardiya.baslangic_saati,
                    bitis=vardiya.bitis_saati,
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


def _durdurulmus_is(donem_id: int, monkeypatch: pytest.MonkeyPatch) -> int:
    """Cozum SURERKEN durdurulmus, elinde bir cozum olan bir is uretir.

    Durdurma istegini gercek zamanli yarisa birakmamak icin, kontrol
    fonksiyonu arama basladiktan sonraki ilk yoklamada dogru doner.
    """
    import app.services.cozum_servisi as cozum_modulu

    oturum = OturumYerel()
    try:
        is_id = CozumServisi(oturum).baslat(donem_id, zaman_limiti_saniye=20).is_id
    finally:
        oturum.close()

    gercek = cozum_modulu._durdurma_istendi_mi

    def sahte(oturum_, is_kaydi_):  # noqa: ANN001, ANN202 - test sahtesi
        if is_kaydi_.durum == CozumIsiDurumu.COZULUYOR:
            return True
        return gercek(oturum_, is_kaydi_)

    monkeypatch.setattr(cozum_modulu, "_durdurma_istendi_mi", sahte)
    assert isi_calistir_ve_bekle(is_id) is CozumIsiDurumu.DURDURULDU
    monkeypatch.undo()
    return is_id


def _atama_kumesi(oturum: OturumYerel, surum_id: int) -> set[tuple[int, date, int, int]]:
    satirlar = oturum.execute(select(Atama).where(Atama.surum_id == surum_id)).scalars().all()
    return {(a.personel_id, a.tarih, a.vardiya_tipi_id, a.nokta_id) for a in satirlar}


# --- Karar: kullan -----------------------------------------------------------


def test_kullan_karari_cozumu_surume_yazar(
    kurulum: dict[str, int], monkeypatch: pytest.MonkeyPatch
) -> None:
    """SRS FR-4.10 (a): sonuc kullanildiginda atamalar yazilir, surum
    `cozuldu` olur ve gecici sonuc BOSALIR."""
    is_id = _durdurulmus_is(kurulum["donem_id"], monkeypatch)

    oturum = OturumYerel()
    try:
        is_kaydi = CozumIsiDeposu(oturum).getir(is_id)
        surum_id = is_kaydi.surum_id
        beklenen = {
            (p, date.fromisoformat(g), v, n) for p, g, v, n in is_kaydi.gecici_sonuc["atamalar"]
        }
        assert beklenen, "Durdurulan isin elinde bir cozum olmali"
        assert _atama_kumesi(oturum, surum_id) == set(), "Karar oncesi surum bos olmali"

        durdurma_karari_uygula(oturum, is_id, Karar.KULLAN)
    finally:
        oturum.close()

    oturum = OturumYerel()
    try:
        is_son = CozumIsiDeposu(oturum).getir(is_id)
        assert is_son.durum in (CozumIsiDurumu.TAMAMLANDI, CozumIsiDurumu.UYARILI)
        assert is_son.gecici_sonuc is None, "Karar, gecici sonucu bosaltmali"
        assert _atama_kumesi(oturum, surum_id) == beklenen
        surum = oturum.execute(
            select(CizelgeSurumu).where(CizelgeSurumu.surum_id == surum_id)
        ).scalar_one()
        assert surum.durum is CizelgeSurumuDurumu.COZULDU
    finally:
        oturum.close()


def test_kullan_karari_cozum_yokken_reddedilir(kurulum: dict[str, int]) -> None:
    """SDD 5.4.1: bos bir sonucun sessizce bos cizelge olarak yazilmasi,
    kural ihlali icermeyen ama kapsamasi SIFIR olan bir surum uretirdi ve
    bu, gercekten cozulmus bir cizelgeden ayirt edilemezdi."""
    oturum = OturumYerel()
    try:
        is_kaydi = CozumServisi(oturum).baslat(kurulum["donem_id"], zaman_limiti_saniye=10)
        is_id = is_kaydi.is_id
        # Cozucu hic calismadan durduruldu: gecici_sonuc bos.
        is_kaydi.durum = CozumIsiDurumu.DURDURULDU
        oturum.commit()

        with pytest.raises(KararUygulanamazError):
            durdurma_karari_uygula(oturum, is_id, Karar.KULLAN)
    finally:
        oturum.close()


def test_karar_yalniz_durdurulmus_iste_uygulanir(kurulum: dict[str, int]) -> None:
    oturum = OturumYerel()
    try:
        is_id = CozumServisi(oturum).baslat(kurulum["donem_id"], zaman_limiti_saniye=10).is_id
        with pytest.raises(KararUygulanamazError):
            durdurma_karari_uygula(oturum, is_id, Karar.AT)
    finally:
        oturum.close()


# --- Karar: at ---------------------------------------------------------------


def test_at_karari_surumu_hic_degistirmez(
    kurulum: dict[str, int], monkeypatch: pytest.MonkeyPatch
) -> None:
    """SRS FR-4.10 (b): surum durdurma oncesindeki haliyle BIREBIR ayni
    kalir. Sonuc atamalara hic yazilmadigi icin geri alinacak bir sey de
    yoktur (SDD 4.2.4)."""
    is_id = _durdurulmus_is(kurulum["donem_id"], monkeypatch)

    oturum = OturumYerel()
    try:
        surum_id = CozumIsiDeposu(oturum).getir(is_id).surum_id
        onceki_atamalar = _atama_kumesi(oturum, surum_id)
        onceki_durum = oturum.execute(
            select(CizelgeSurumu.durum).where(CizelgeSurumu.surum_id == surum_id)
        ).scalar_one()

        durdurma_karari_uygula(oturum, is_id, Karar.AT)
    finally:
        oturum.close()

    oturum = OturumYerel()
    try:
        is_son = CozumIsiDeposu(oturum).getir(is_id)
        assert is_son.durum is CozumIsiDurumu.IPTAL
        assert is_son.gecici_sonuc is None
        assert _atama_kumesi(oturum, surum_id) == onceki_atamalar
        sonraki_durum = oturum.execute(
            select(CizelgeSurumu.durum).where(CizelgeSurumu.surum_id == surum_id)
        ).scalar_one()
        assert sonraki_durum == onceki_durum
        acilar = (
            oturum.execute(select(KapsamaAcigi).where(KapsamaAcigi.surum_id == surum_id))
            .scalars()
            .all()
        )
        assert acilar == []
    finally:
        oturum.close()


# --- Karar: devam ------------------------------------------------------------


def test_devam_karari_ipucuyla_yeni_is_baslatir(
    kurulum: dict[str, int], monkeypatch: pytest.MonkeyPatch
) -> None:
    """SRS FR-4.10 (c): yeni is baslar, iki is `devam_kaynagi_is_id` ile
    baglidir ve sonuc ipucundan kotu degildir.

    "Devam", aramanin kaldigi yerden surdurulmesi DEGILDIR; bulunan cozum
    ipucu verilerek yeni bir arama baslar ve sure sifirdan isler."""
    is_id = _durdurulmus_is(kurulum["donem_id"], monkeypatch)

    oturum = OturumYerel()
    try:
        eski = CozumIsiDeposu(oturum).getir(is_id)
        surum_id = eski.surum_id
        ipucu_ceza = float(eski.en_iyi_ceza)
        _, yeni_is = durdurma_karari_uygula(oturum, is_id, Karar.DEVAM, zaman_limiti_saniye=15)
        assert yeni_is is not None
        yeni_is_id = yeni_is.is_id
        assert yeni_is.devam_kaynagi_is_id == is_id
        assert yeni_is.zaman_limiti_saniye == 15
        assert yeni_is.surum_id == surum_id, "Devam ayni surum uzerinde surer"
    finally:
        oturum.close()

    oturum = OturumYerel()
    try:
        eski = CozumIsiDeposu(oturum).getir(is_id)
        assert eski.durum is CozumIsiDurumu.IPTAL
        assert eski.gecici_sonuc is None, "Kaynak isin CIKTISI kararla bosalir"
        yeni = CozumIsiDeposu(oturum).getir(yeni_is_id)
        # Ipucu, ciktinin durdugu alanda degil KENDI sutununda (SDD 4.2.4):
        # girdi ile cikti ayri alanlarda durur.
        assert yeni.cozum_ipucu is not None, "Ipucu yeni isin girdi alaninda bekliyor olmali"
        assert yeni.gecici_sonuc is None, "Yeni isin daha bir ciktisi yok"
    finally:
        oturum.close()

    assert isi_calistir_ve_bekle(yeni_is_id) in (
        CozumIsiDurumu.TAMAMLANDI,
        CozumIsiDurumu.UYARILI,
    )

    oturum = OturumYerel()
    try:
        yeni = CozumIsiDeposu(oturum).getir(yeni_is_id)
        assert float(yeni.en_iyi_ceza) <= ipucu_ceza, "Sonuc ipucundan kotu olmamali"
        assert yeni.cozum_ipucu is None, "Ipucu IS SONLANINCA bosalir"
        assert _atama_kumesi(oturum, surum_id), "Yeni is atamalari yazmis olmali"
    finally:
        oturum.close()


def test_ipucu_model_kurulduktan_sonra_yerinde_durur(
    kurulum: dict[str, int], monkeypatch: pytest.MonkeyPatch
) -> None:
    """SDD 4.2.4: `cozum_ipucu` model kurulunca DEGIL, IS SONLANINCA bosalir.

    Model kurulumunda silinseydi, iscinin yeniden baslamasi (servis yeniden
    baslatilir ya da is kuyruga doner) isi ipucusuz surdururdu: sonuc
    sessizce kotulesir ve bunu gosteren hicbir iz kalmazdi. Test, model
    kurulduktan sonraki ANI yakalamak icin aramayi o noktada durduruyor.
    """
    import app.services.cozum_servisi as cozum_modulu

    is_id = _durdurulmus_is(kurulum["donem_id"], monkeypatch)

    oturum = OturumYerel()
    try:
        _, yeni_is = durdurma_karari_uygula(oturum, is_id, Karar.DEVAM, zaman_limiti_saniye=20)
        yeni_is_id = yeni_is.is_id
    finally:
        oturum.close()

    # Arama basladiktan (yani model kurulduktan) sonraki ilk yoklamada
    # durdurulur; is `durduruldu`da kalir - terminal degildir.
    gercek = cozum_modulu._durdurma_istendi_mi

    def sahte(oturum_, is_kaydi_):  # noqa: ANN001, ANN202 - test sahtesi
        if is_kaydi_.durum == CozumIsiDurumu.COZULUYOR:
            return True
        return gercek(oturum_, is_kaydi_)

    monkeypatch.setattr(cozum_modulu, "_durdurma_istendi_mi", sahte)
    assert isi_calistir_ve_bekle(yeni_is_id) is CozumIsiDurumu.DURDURULDU
    monkeypatch.undo()

    oturum = OturumYerel()
    try:
        assert (
            CozumIsiDeposu(oturum).getir(yeni_is_id).cozum_ipucu is not None
        ), "Model kuruldu ve arama sonlandi, ama is HENUZ SONLANMADI: ipucu durmali"
        # Karar verilince is sonlanir ve ipucu ancak o zaman bosalir.
        durdurma_karari_uygula(oturum, yeni_is_id, Karar.AT)
    finally:
        oturum.close()

    oturum = OturumYerel()
    try:
        son = CozumIsiDeposu(oturum).getir(yeni_is_id)
        assert son.durum is CozumIsiDurumu.IPTAL
        assert son.cozum_ipucu is None, "Is sonlaninca ipucu bosalir"
    finally:
        oturum.close()


# --- Gecici sonucun okuma yuzeylerine sizmamasi ------------------------------


def test_gecici_sonuc_hicbir_okuma_yuzeyine_sizmaz(
    kurulum: dict[str, int], monkeypatch: pytest.MonkeyPatch
) -> None:
    """SDD 4.2.4: gecici sonuc BIR OKUMA KAYNAGI DEGILDIR.

    Cizelge izgarasi, kapsama acigi, fazla kadro, surum listesi ve analiz -
    hepsi atama tablosundan beslenir. Is durduruldugunda elde bir cozum
    olmasina ragmen bu uclarin hicbiri onu gormemeli; aksi halde kullanici
    henuz KARAR VERMEDIGI bir cizelgeyi her ekranda gorurdu."""
    is_id = _durdurulmus_is(kurulum["donem_id"], monkeypatch)

    oturum = OturumYerel()
    try:
        is_kaydi = CozumIsiDeposu(oturum).getir(is_id)
        surum_id = is_kaydi.surum_id
        assert is_kaydi.gecici_sonuc["atamalar"], "Onkosul: elde bir cozum var"
    finally:
        oturum.close()

    istemci = yetkili_istemci(Rol.YONETICI)
    assert istemci.get(f"/api/surum/{surum_id}/atama").json() == []
    assert istemci.get(f"/api/surum/{surum_id}/kapsama-acigi").json() == []
    assert istemci.get(f"/api/surum/{surum_id}/fazla-kadro").json() == []

    surumler = istemci.get(f"/api/surum?donem_id={kurulum['donem_id']}").json()
    bu_surum = next(s for s in surumler if s["surum_id"] == surum_id)
    assert bu_surum["durum"] == "taslak"

    # Cozum ucunun kendisi de gecici sonucun ICERIGINI vermez; yalnizca
    # "kullan" secenegini etkinlestirmek icin varligini bildirir.
    cozum = istemci.get(f"/api/cozum/{is_id}").json()
    assert cozum["kullanilabilir_sonuc_var"] is True
    assert "gecici_sonuc" not in cozum


# --- Aktif is ucu (SRS FR-4.11) ----------------------------------------------


def test_aktif_uc_karar_bekleyen_isi_de_dondurur(
    kurulum: dict[str, int], monkeypatch: pytest.MonkeyPatch
) -> None:
    """SDD 6.1: karar bekleyen is de gostergede gorunur - kullanici baska
    ekrandayken durdurup unutursa is sessizce askida kalmasin."""
    is_id = _durdurulmus_is(kurulum["donem_id"], monkeypatch)

    istemci = yetkili_istemci(Rol.YONETICI)
    aktif = istemci.get("/api/cozum/aktif").json()
    assert aktif is not None
    assert aktif["is_id"] == is_id
    assert aktif["durum"] == "durduruldu"

    oturum = OturumYerel()
    try:
        durdurma_karari_uygula(oturum, is_id, Karar.AT)
    finally:
        oturum.close()

    assert istemci.get("/api/cozum/aktif").json() is None


def test_aktif_uc_calisan_rolune_kapali(kurulum: dict[str, int]) -> None:
    """Rol kapisi: yonetici + yonetim (SRS 5.10)."""
    oturum = OturumYerel()
    try:
        personel_id = oturum.execute(select(Personel.personel_id)).scalars().first()
    finally:
        oturum.close()

    assert (
        yetkili_istemci(Rol.CALISAN, personel_id=personel_id).get("/api/cozum/aktif").status_code
        == 403
    )
    assert yetkili_istemci(Rol.YONETICI).get("/api/cozum/aktif").status_code == 200
    assert yetkili_istemci(Rol.YONETIM).get("/api/cozum/aktif").status_code == 200


# --- Uc noktalar --------------------------------------------------------------


def test_kuyruktaki_isin_durdurulmasi_dogrudan_iptaldir(kurulum: dict[str, int]) -> None:
    """SDD 5.4.1: karar noktasi yalnizca arama SURERKEN dogar.

    Kuyruktaki bir iste henuz arama baslamamistir; saklanacak bir sonuc,
    dolayisiyla verilecek bir karar da yoktur. Karar paneli acmak uc
    secenekten ikisini anlamsiz kilardi."""
    oturum = OturumYerel()
    try:
        is_id = CozumServisi(oturum).baslat(kurulum["donem_id"], zaman_limiti_saniye=10).is_id
    finally:
        oturum.close()

    istemci = yetkili_istemci(Rol.YONETICI)
    yanit = istemci.post(f"/api/cozum/{is_id}/durdur", json={})
    assert yanit.status_code == 200
    govde = yanit.json()
    assert govde["durum"] == "iptal"
    assert govde["kullanilabilir_sonuc_var"] is False

    oturum = OturumYerel()
    try:
        is_kaydi = CozumIsiDeposu(oturum).getir(is_id)
        assert is_kaydi.gecici_sonuc is None, "Karar sorulmadigi icin saklanan sonuc da yok"
        assert is_kaydi.bitis_zamani is not None
        # Karar akisi bu ise KAPALI: karar bekleyen durumda degil.
        with pytest.raises(KararUygulanamazError):
            durdurma_karari_uygula(oturum, is_id, Karar.KULLAN)
    finally:
        oturum.close()

    # Isci boyle bir isi hic almaz: kapma sorgusu yalniz `kuyrukta` secer.
    calisan = OturumYerel()
    try:
        assert siradaki_isi_kap(calisan) is None
    finally:
        calisan.close()


def test_cozulurken_durdurma_karar_noktasi_dogurur(
    kurulum: dict[str, int], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ayni ucun DIGER yolu: arama basladiysa is `durduruldu` olur ve karar
    sorulur (SRS FR-4.9)."""
    is_id = _durdurulmus_is(kurulum["donem_id"], monkeypatch)

    istemci = yetkili_istemci(Rol.YONETICI)
    govde = istemci.get(f"/api/cozum/{is_id}").json()
    assert govde["durum"] == "durduruldu"
    assert govde["kullanilabilir_sonuc_var"] is True

    # Ayni istek ikinci kez: is artik durdurulabilir bir durumda degil ve
    # bunu anlasilir bir mesajla soyler.
    yanit = istemci.post(f"/api/cozum/{is_id}/durdur", json={})
    assert yanit.status_code == 409
    assert "kararinizi bekliyor" in yanit.json()["detail"]


def test_sonlanmis_isin_durdurulmasi_anlasilir_hata_verir(
    kurulum: dict[str, int], monkeypatch: pytest.MonkeyPatch
) -> None:
    is_id = _durdurulmus_is(kurulum["donem_id"], monkeypatch)
    oturum = OturumYerel()
    try:
        durdurma_karari_uygula(oturum, is_id, Karar.AT)
    finally:
        oturum.close()

    yanit = yetkili_istemci(Rol.YONETICI).post(f"/api/cozum/{is_id}/durdur", json={})
    assert yanit.status_code == 409
    assert "iptal" in yanit.json()["detail"].lower()

    assert (
        yetkili_istemci(Rol.YONETICI).post("/api/cozum/999999/durdur", json={}).status_code == 404
    )


def test_karar_ucu_uc_secenegi_de_kabul_eder(
    kurulum: dict[str, int], monkeypatch: pytest.MonkeyPatch
) -> None:
    is_id = _durdurulmus_is(kurulum["donem_id"], monkeypatch)
    istemci = yetkili_istemci(Rol.YONETICI)

    yanit = istemci.post(f"/api/cozum/{is_id}/karar", json={"karar": "at"})
    assert yanit.status_code == 200
    govde = yanit.json()
    assert govde["is_kaydi"]["durum"] == "iptal"
    assert govde["yeni_is"] is None

    # Ayni karar ikinci kez uygulanamaz: is artik karar bekleyen durumda degil.
    assert istemci.post(f"/api/cozum/{is_id}/karar", json={"karar": "at"}).status_code == 409


def test_karar_ucu_zaman_limitini_yalniz_devamda_kabul_eder(
    kurulum: dict[str, int], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Zaman limiti "devam"a ozgudur: yeni bir arama baslatilir ve sure
    sifirdan isler. "Kullan"/"at" bir arama baslatmadigi icin oradaki bir
    sure degeri sessizce yok sayilirdi."""
    is_id = _durdurulmus_is(kurulum["donem_id"], monkeypatch)
    istemci = yetkili_istemci(Rol.YONETICI)

    yanit = istemci.post(
        f"/api/cozum/{is_id}/karar", json={"karar": "at", "zaman_limiti_saniye": 30}
    )
    assert yanit.status_code == 422

    yanit = istemci.post(
        f"/api/cozum/{is_id}/karar", json={"karar": "devam", "zaman_limiti_saniye": 30}
    )
    assert yanit.status_code == 200
    assert yanit.json()["yeni_is"]["zaman_limiti_saniye"] == 30

    oturum = OturumYerel()
    try:
        yeni_is_id = yanit.json()["yeni_is"]["is_id"]
        yeni = oturum.execute(select(CozumIsi).where(CozumIsi.is_id == yeni_is_id)).scalar_one()
        assert yeni.devam_kaynagi_is_id == is_id
    finally:
        oturum.close()
