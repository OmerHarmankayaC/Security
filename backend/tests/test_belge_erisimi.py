"""Izin belgesine erisim (SRS FR-2.8, TD-17; SDD 5.10).

IKI KURAL, AYRI AYRI:
  1. Tip ICERIKTEN dogrulanir — uzanti ve istemcinin bildirdigi
     `Content-Type` kullanici girdisidir.
  2. Erisim SAHIPLIGE baglidir — calisan kendi kaydina erisir,
     baskasininkine erisemez. Adres bilmek erisim hakki vermez.
"""

import uuid
from datetime import date

import pytest

from app.db import OturumYerel
from app.models.girdi import Musaitlik, MusaitlikDilimi, MusaitlikTipi
from app.models.kimlik import Rol
from app.models.tanim import Personel
from app.services.belge_servisi import (
    BelgeServisi,
    BelgeTipiKabulEdilmediError,
    icerikten_tipi_belirle,
)
from tests.conftest import oturumlu_istemci, pg_yoksa_atla

_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000a49444154789c6360000002000100fdff03fd000000"
    "0049454e44ae426082"
)
_PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n%%EOF\n"
_HTML = b"<html><script>alert(1)</script></html>"


class TestIcerikTenTip:
    def test_imzadan_taninir(self) -> None:
        assert icerikten_tipi_belirle(_PNG) == "image/png"
        assert icerikten_tipi_belirle(_PDF) == "application/pdf"
        assert icerikten_tipi_belirle(b"\xff\xd8\xff\xe0boo") == "image/jpeg"

    def test_taninmayan_icerik_none_doner(self) -> None:
        assert icerikten_tipi_belirle(_HTML) is None
        assert icerikten_tipi_belirle(b"") is None


def _izin(oturum, personel_id: int) -> Musaitlik:  # noqa: ANN001
    kayit = Musaitlik(
        personel_id=personel_id,
        baslangic_tarihi=date(2026, 9, 1),
        bitis_tarihi=date(2026, 9, 2),
        dilim=MusaitlikDilimi.TAM_GUN,
        tip=MusaitlikTipi.RAPOR,
    )
    oturum.add(kayit)
    oturum.flush()
    return kayit


def _personel(oturum, ad: str) -> Personel:  # noqa: ANN001
    p = Personel(
        ad_soyad=ad,
        sicil_no=f"BLG-{uuid.uuid4().hex[:8].upper()}",
        haftalik_hedef_saat=40,
        aktif_baslangic=date(2026, 1, 1),
    )
    oturum.add(p)
    oturum.flush()
    return p


class TestYuklemeDogrulamasi:
    @pytest.fixture
    def oturum(self):  # noqa: ANN201
        pg_yoksa_atla()
        o = OturumYerel()
        try:
            yield o
        finally:
            o.rollback()
            o.close()

    def test_adi_png_olan_html_reddedilir(self, oturum) -> None:  # noqa: ANN001
        """Saldirinin tam sekli: dosya adi ve bildirilen tip masum, icerik
        degil. Ada guvenilseydi HTML `image/png` olarak saklanir ve
        indirilirken ayni tiple sunulurdu."""
        kayit = _izin(oturum, _personel(oturum, "Tip Testi").personel_id)
        with pytest.raises(BelgeTipiKabulEdilmediError):
            BelgeServisi(oturum).yukle(kayit.musaitlik_id, "rapor.png", _HTML)

    def test_gercek_png_kabul_edilir_ve_tip_icerikten_yazilir(self, oturum) -> None:  # noqa: ANN001
        kayit = _izin(oturum, _personel(oturum, "Png Testi").personel_id)
        # Dosya adi YANLIS uzanti tasiyor; tip yine de dogru belirlenmeli.
        sonuc = BelgeServisi(oturum).yukle(kayit.musaitlik_id, "rapor.pdf", _PNG)
        assert sonuc is not None
        assert sonuc.belge_tipi == "image/png"


class TestSahiplik:
    """Uc istemci ayri testlerde acilir: `oturumlu_istemci` kimlik
    tablolarini temizler, ayni testte iki oturum yasayamaz."""

    def _hazirla(self) -> tuple[int, int, int]:
        """(belgeli_izin_id, sahip_personel_id, yabanci_personel_id)"""
        oturum = OturumYerel()
        try:
            sahip = _personel(oturum, "Belge Sahibi")
            yabanci = _personel(oturum, "Baskasi")
            kayit = _izin(oturum, sahip.personel_id)
            BelgeServisi(oturum).yukle(kayit.musaitlik_id, "rapor.png", _PNG)
            oturum.commit()
            return kayit.musaitlik_id, sahip.personel_id, yabanci.personel_id
        finally:
            oturum.close()

    def test_calisan_kendi_belgesine_erisir(self) -> None:
        pg_yoksa_atla()
        izin_id, sahip_id, _ = self._hazirla()
        istemci = oturumlu_istemci(Rol.CALISAN, personel_id=sahip_id)

        yanit = istemci.get(f"/api/musaitlik/{izin_id}/belge")

        assert yanit.status_code == 200
        assert yanit.content == _PNG

    def test_calisan_baskasinin_belgesine_erisemez(self) -> None:
        """ADRES BILMEK ERISIM HAKKI VERMEZ. Uc noktanin rol kapisi calisani
        iceri alir; durduran sey kaydin sahipligidir."""
        pg_yoksa_atla()
        izin_id, _, yabanci_id = self._hazirla()
        istemci = oturumlu_istemci(Rol.CALISAN, personel_id=yabanci_id)

        assert istemci.get(f"/api/musaitlik/{izin_id}/belge").status_code == 403

    def test_idare_her_belgeye_erisir(self) -> None:
        pg_yoksa_atla()
        izin_id, _, _ = self._hazirla()
        istemci = oturumlu_istemci(Rol.IDARE)

        assert istemci.get(f"/api/musaitlik/{izin_id}/belge").status_code == 200


def test_erisim_kayda_gecer_belgenin_kendisi_gecmez(caplog) -> None:  # noqa: ANN001
    """TD-17: "kim gordu" sorusu yanitlanabilmeli; icerik ise hicbir
    gunluge girmemeli."""
    pg_yoksa_atla()
    oturum = OturumYerel()
    try:
        sahip = _personel(oturum, "Gunluk Testi")
        kayit = _izin(oturum, sahip.personel_id)
        BelgeServisi(oturum).yukle(kayit.musaitlik_id, "rapor.png", _PNG)
        oturum.commit()
        izin_id = kayit.musaitlik_id
    finally:
        oturum.close()

    istemci = oturumlu_istemci(Rol.IDARE)
    with caplog.at_level("INFO", logger="vardiya.kimlik"):
        istemci.get(f"/api/musaitlik/{izin_id}/belge")

    metin = caplog.text
    assert "olay=belge_erisim" in metin
    assert f"musaitlik_id={izin_id}" in metin
    # Icerik gunluge SIZMAZ.
    assert "PNG" not in metin
    assert _PNG.hex()[:16] not in metin
