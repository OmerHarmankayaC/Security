"""Toplu hesap kurulumu (FR-10.6, FR-10.11, FR-10.13).

Uc sey kilitlenir:
  1. Kullanici adi ASCII olur (FR-10.11) — Turkce harf tasiyan bir sicil ya
     da ad, girisi imkansiz bir hesap uretirdi.
  2. Gecici parola SAKLANMAZ (FR-10.13) — servis onu yalnizca DONER, hicbir
     alana yazmaz; cagiran taraf bir kez gosterir.
  3. Hesabi olan personel ATLANIR — betik iki kez kosturuldugunda ikinci
     hesap acilmaz (FR-10.6: bir personelin birden fazla hesabi olamaz).
"""

import uuid
from datetime import date

import pytest

from app.db import OturumYerel
from app.models.kimlik import Kullanici, Rol
from app.models.tanim import Personel
from app.services.hesap_kurulumu import (
    HesapKurulumu,
    asciye_indir,
    gecici_parola_uret,
    kullanici_adi_turet,
)
from app.services.parola import ASGARI_UZUNLUK
from tests.conftest import pg_yoksa_atla


@pytest.fixture
def oturum():  # noqa: ANN201
    pg_yoksa_atla()
    o = OturumYerel()
    try:
        yield o
    finally:
        o.rollback()
        o.close()


def _personel(oturum, ad: str) -> Personel:  # noqa: ANN001
    p = Personel(
        ad_soyad=ad,
        sicil_no=f"KUR-{uuid.uuid4().hex[:8].upper()}",
        haftalik_hedef_saat=40,
        aktif_baslangic=date(2026, 1, 1),
    )
    oturum.add(p)
    oturum.flush()
    return p


class TestAsciyeIndirme:
    def test_turkce_harfler_ascii_karsiligina_iner(self) -> None:
        # FR-10.11'in tam sebebi: "İ" ve "ı" kucultmede veritabani ile
        # uygulama katmaninda farkli sonuc verebiliyor.
        assert asciye_indir("Ömer Harmankaya") == "omer harmankaya"
        assert asciye_indir("ŞİŞLİ") == "sisli"
        assert asciye_indir("Çağrı Öz") == "cagri oz"
        assert asciye_indir("ğüşiöç ĞÜŞİÖÇ") == "gusioc gusioc"

    def test_ascii_disi_kalinti_birakmaz(self) -> None:
        for metin in ("Ömer", "Iğdır", "Çanakkale", "Şırnak"):
            assert asciye_indir(metin).isascii()


class TestKullaniciAdi:
    def test_sicil_numarasindan_turetilir(self) -> None:
        assert kullanici_adi_turet("VS-001") == "vs001"
        assert kullanici_adi_turet("GG-017") == "gg017"

    def test_turkce_harfli_sicil_de_ascii_olur(self) -> None:
        assert kullanici_adi_turet("ŞF-003").isascii()
        assert kullanici_adi_turet("ŞF-003") == "sf003"


class TestGeciciParola:
    def test_asgari_uzunlugu_saglar(self) -> None:
        assert len(gecici_parola_uret()) >= ASGARI_UZUNLUK

    def test_her_cagride_farklidir(self) -> None:
        # Ayni parolanin iki hesaba verilmesi, birinin digerine girebilmesi
        # demektir.
        uretilenler = {gecici_parola_uret() for _ in range(50)}
        assert len(uretilenler) == 50

    def test_karistirilabilir_karakter_tasimaz(self) -> None:
        # Parola SESLI OKUNARAK ya da elle yazilarak aktarilacak; 0/O ve 1/l
        # ayrimi telefonda kaybolur.
        for _ in range(20):
            assert not (set(gecici_parola_uret()) & set("0O1lI"))


class TestCalisanHesaplari:
    def test_personel_basina_hesap_acar_ve_parolayi_doner(self, oturum) -> None:  # noqa: ANN001
        p = _personel(oturum, "Ali Veli")
        sonuc = HesapKurulumu(oturum).calisan_hesaplari_ac()

        acilan = [s for s in sonuc if s.personel_id == p.personel_id]
        assert len(acilan) == 1
        assert acilan[0].kullanici_adi == kullanici_adi_turet(p.sicil_no)
        assert len(acilan[0].gecici_parola) >= ASGARI_UZUNLUK

    def test_parola_hicbir_alanda_saklanmaz(self, oturum) -> None:  # noqa: ANN001
        p = _personel(oturum, "Ayse Yilmaz")
        sonuc = HesapKurulumu(oturum).calisan_hesaplari_ac()
        parola = next(s.gecici_parola for s in sonuc if s.personel_id == p.personel_id)

        kullanici = oturum.query(Kullanici).filter(Kullanici.personel_id == p.personel_id).one()
        # Ozet parolanin kendisi DEGILDIR ve hicbir sutun duz parolayi tasimaz.
        assert parola not in kullanici.parola_ozeti
        for deger in vars(kullanici).values():
            if isinstance(deger, str):
                assert parola not in deger

    def test_ilk_giriste_parola_degistirme_borcu_yazilir(self, oturum) -> None:  # noqa: ANN001
        p = _personel(oturum, "Mehmet Kaya")
        HesapKurulumu(oturum).calisan_hesaplari_ac()
        kullanici = oturum.query(Kullanici).filter(Kullanici.personel_id == p.personel_id).one()
        assert kullanici.parola_degistirmeli is True
        assert kullanici.rol is Rol.CALISAN

    def test_hesabi_olan_personel_atlanir(self, oturum) -> None:  # noqa: ANN001
        p = _personel(oturum, "Zeynep Ak")
        kurulum = HesapKurulumu(oturum)
        kurulum.calisan_hesaplari_ac()
        ikinci = kurulum.calisan_hesaplari_ac()

        assert all(s.personel_id != p.personel_id for s in ikinci)
        assert oturum.query(Kullanici).filter(Kullanici.personel_id == p.personel_id).count() == 1


class TestParolaSifirlama:
    def test_yeni_parola_uretir_ve_borcu_yazar(self, oturum) -> None:  # noqa: ANN001
        p = _personel(oturum, "Sifirlama Testi")
        HesapKurulumu(oturum).calisan_hesaplari_ac()
        kullanici = oturum.query(Kullanici).filter(Kullanici.personel_id == p.personel_id).one()
        onceki_ozet = kullanici.parola_ozeti
        kullanici.parola_degistirmeli = False

        sonuc = HesapKurulumu(oturum).parolayi_sifirla(kullanici.kullanici_adi)

        assert sonuc is not None
        assert sonuc.gecici_parola not in kullanici.parola_ozeti
        assert kullanici.parola_ozeti != onceki_ozet
        assert kullanici.parola_degistirmeli is True

    def test_kilit_ve_sayac_da_sifirlanir(self, oturum) -> None:  # noqa: ANN001
        # Eski parolayla dolmus bir sayac yuzunden YENI parolayla beklemenin
        # anlami yok.
        p = _personel(oturum, "Kilitli Hesap")
        HesapKurulumu(oturum).calisan_hesaplari_ac()
        kullanici = oturum.query(Kullanici).filter(Kullanici.personel_id == p.personel_id).one()
        kullanici.basarisiz_deneme = 5
        oturum.flush()

        HesapKurulumu(oturum).parolayi_sifirla(kullanici.kullanici_adi)

        assert kullanici.basarisiz_deneme == 0
        assert kullanici.kilit_bitis is None

    def test_olmayan_hesapta_none_doner(self, oturum) -> None:  # noqa: ANN001
        assert HesapKurulumu(oturum).parolayi_sifirla("boyle-bir-hesap-yok") is None
