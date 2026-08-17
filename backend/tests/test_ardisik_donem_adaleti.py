"""Kabul testi: kumulatif adalet DOGRU YONDE calisiyor mu (SRS TD-6, Tur 9 Is 3).

Bu bir ozellik testi degil DOGRULUK testidir. Kumulatif adaletin yanlis yonde
calismasi hic calismamasindan kotudur: sistem adaleti duzelttigini iddia
ederken bozar.

## Neden bir kez SILINIP geri getirildi

Test uc denemede de gecmedigi icin silinmisti; bu bir hataydi. Basarisiz bir
test BILGI TASIR - silindiginde geriye yalniz bir rapor cumlesi kalir ve kodun
kendisi hicbir sey soylemez. Ayni gerekce projenin "yeniden tanimlanan kuralin
eski testi silinmez, guncellenir" kuraliyla aynidir.

Geri getirilip duzeltildikten sonra GECTI. Dordunculuk denemede bulunan sey
kodda bir hata degil, karsilastirmanin kendisindeki hataydi (asagida).

## Uc denemenin ozeti

Sentetik senaryo (iki personel, tek gece nobeti) UC farkli kurulumda da ayirt
edici olmadi:

  1. Yalin hali: ufuk KAPALIYKEN de geciyordu. `baglam_olustur` veritabanindaki
     tum aktif personeli yukler; test veritabaninda baska testlerden kalan otuz
     kusur kisi vardi ve nobetler onlara dagiliyordu.
  2. Havuz yetkinlikle kapatildi, olcum yarisilan noktayla sinirlandi.
  3. S4'un cekisi `haftalik_hedef_saat=0` ile kaldirildi.

Ucunde de sonuc BIREBIR ayni cikti (46'ya 41, yanlis yonde). Kurulum
degisirken sonucun hic degismemesi, olculen seyin kurulan senaryo olmadigina
isaret ediyor.

Bu surumde senaryo GOSTERIM VERISI uzerine kuruldu: uc ardisik yayinlanmis
donem, gercek cozucuyle uretilmis. Boylece "tum aktif personel yukleniyor"
bir kirlilik degil DOGRU davranis oluyor.

## Dorduncu deneme neyi ogretti

Gosterim verisi uzerinde ilk sorulusta da KALDI, ama sebep mekanizma degil
KARSILASTIRMANIN KENDISIYDI. Test "en cok tasiyan" ile "en az tasiyan"i
seciyordu ve ikisi:

  - FARKLI YETKINLIK HAVUZLARINDAYDI (VS-001 vardiya sefi, GG-020 guvenlik
    gorevlisi). Ayni nobetler icin yarismayan iki kisinin gece saatini
    karsilastirmak anlamsizdir; adil paylari zaten farklidir.
  - Biri UFKUN ORTASINDA ISE BASLAMISTI. Onun payi `calisabilir_oran` ile
    yarilanir, yani az tasimasi DOGRU davranistir - onu "hafif" sayip
    kiyaslamak olcunun kendi kuralini ihlal eder.

Duzeltilmis hali AYNI HAVUZ icinde ve yalnizca ufkun tamaminda calisabilen
personel arasinda karsilastirir. Bu haliyle YON IKI HAVUZDA DA DOGRU CIKTI:
vardiya sefligi havuzunda en agir tasiyan ucuncu donemde 16, en hafif 23 gece
saati aldi; guvenlik havuzunda ust ucte birin ortalamasi 12,3'e karsi alt
ucte birin 14,2.

Tek kisi yerine UCTE BIR DILIM karsilastirilir: tek kisi cozucunun o donemki
esitlik tercihine, izin kayitlarina ve talep dagilimina fazla duyarlidir.
Dilim ortalamasi egilimi olcer, tekil sonucu degil.
"""

from datetime import timedelta

import pytest
from sqlalchemy import select

from app.db import OturumYerel
from app.kurallar.zaman_araligi import gece_saat_sayisi
from app.models.sonuc import Atama, CizelgeSurumu, CizelgeSurumuDurumu, Donem
from app.models.tanim import Personel
from app.services.gecmis_sayaclar import ADALET_UFKU_GUN, GecmisSayaclar
from tests.conftest import pg_yoksa_atla

# Ufkun TAMAMINDA calisabilir sayilma esigi. Altinda kalanin payi zaten
# kucultulmustur (SRS TD-6) ve az tasimasi dogru davranistir; olcuye
# katilmasi karsilastirmayi bozar.
_TAM_CALISABILIR_ESIGI = 0.95


def _yayinlanmis_donemler(oturum) -> list[tuple[Donem, int]]:
    """Yayinlanmis surumu olan donemler, ESKIDEN YENIYE."""
    satirlar = oturum.execute(
        select(Donem, CizelgeSurumu.surum_id)
        .join(CizelgeSurumu, CizelgeSurumu.donem_id == Donem.donem_id)
        .where(CizelgeSurumu.durum == CizelgeSurumuDurumu.YAYINLANDI)
        .order_by(Donem.baslangic_tarihi, CizelgeSurumu.surum_no.desc())
    ).all()
    sonuc: dict[int, tuple[Donem, int]] = {}
    for donem, surum_id in satirlar:
        sonuc.setdefault(donem.donem_id, (donem, surum_id))
    return sorted(sonuc.values(), key=lambda x: x[0].baslangic_tarihi)


def _gece_yuku(oturum, surum_id: int) -> dict[int, float]:
    yuk: dict[int, float] = {}
    for a in oturum.execute(select(Atama).where(Atama.surum_id == surum_id)).scalars():
        saat = gece_saat_sayisi(a.baslangic_zamani.time(), a.bitis_zamani.time())
        yuk[a.personel_id] = yuk.get(a.personel_id, 0.0) + saat
    return yuk


def _ardisik_ucu(donemler: list[tuple[Donem, int]]) -> list[tuple[Donem, int]] | None:
    """Arka arkaya gelen UC yayinlanmis donem; yoksa None.

    "Ardisik" burada takvimsel bitisikliktir: bir donemin bitisinden sonraki
    gun digerinin baslangicidir. Arada yayinlanmamis bir hafta varsa (gosterim
    verisindeki DAR HAFTA gibi) zincir kirilir.
    """
    for i in range(len(donemler) - 2):
        ucu = donemler[i : i + 3]
        bitisik = all(
            ucu[j][0].bitis_tarihi + timedelta(days=1) == ucu[j + 1][0].baslangic_tarihi
            for j in range(2)
        )
        if bitisik:
            return ucu
    return None


def _havuzlar(oturum, oranlar) -> dict[frozenset[int], list[int]]:
    """Personeli ERISIM HAVUZUNA gore gruplar.

    Havuz yetkinlik kumesidir: ayni yetkinliklere sahip iki kisi ayni gorev
    noktalarina erisir, dolayisiyla ayni nobetler icin yarisir ve adil paylari
    ayni tabandan hesaplanir. Farkli havuzdaki iki kisinin gece saatini
    karsilastirmak anlamsizdir - biri gece talebi olan bir noktaya hic
    erisemiyor olabilir.
    """
    gruplar: dict[frozenset[int], list[int]] = {}
    for kisi in oturum.execute(select(Personel)).scalars():
        if oranlar(kisi.personel_id) < _TAM_CALISABILIR_ESIGI:
            continue
        anahtar = frozenset(y.yetkinlik_id for y in kisi.yetkinlikler)
        gruplar.setdefault(anahtar, []).append(kisi.personel_id)
    return gruplar


def test_gecmiste_agir_gece_yuku_alan_havuz_dilimi_sonraki_donemde_daha_az_alir() -> None:
    pg_yoksa_atla()
    oturum = OturumYerel()
    try:
        ucu = _ardisik_ucu(_yayinlanmis_donemler(oturum))
        if ucu is None:
            pytest.skip(
                "Uc ardisik yayinlanmis donem yok; once "
                "`python scripts/demo_veri_uret.py --reset` calistirin."
            )

        (_d1, s1), (_d2, s2), (d3, s3) = ucu
        birikim_kaynagi = (_gece_yuku(oturum, s1), _gece_yuku(oturum, s2))
        son_yuk = _gece_yuku(oturum, s3)
        sayaclar = GecmisSayaclar(oturum).hesapla(d3, ADALET_UFKU_GUN)

        # Gecmis GERCEKTEN okunuyor mu — okunmuyorsa asagisi bir sey kanitlamaz.
        assert any(
            sayaclar.sayac(p).gece_saat > 0 for p in son_yuk
        ), "ucuncu donem gecmisi hic gormuyor"

        sinanan = 0
        for havuz in _havuzlar(oturum, sayaclar.oran).values():
            birikim = {
                p: birikim_kaynagi[0].get(p, 0.0) + birikim_kaynagi[1].get(p, 0.0) for p in havuz
            }
            if len(havuz) < 2 or max(birikim.values()) == min(birikim.values()):
                # Tek kisilik ya da tumuyle esit havuz bir sey soylemez.
                continue
            sirali = sorted(havuz, key=lambda p: -birikim[p])
            dilim = max(len(sirali) // 3, 1)
            ust, alt = sirali[:dilim], sirali[-dilim:]
            ust_ort = sum(son_yuk.get(p, 0.0) for p in ust) / len(ust)
            alt_ort = sum(son_yuk.get(p, 0.0) for p in alt) / len(alt)
            assert ust_ort < alt_ort, (
                f"havuz({len(havuz)} kisi): ilk iki donemde EN COK tasiyanlar "
                f"ucuncu donemde ort. {ust_ort:.1f} gece saati aldi, en az "
                f"tasiyanlar {alt_ort:.1f} — kumulatif ufuk yuku YANLIS YONE "
                f"kaydirdi"
            )
            sinanan += 1

        assert sinanan, "karsilastirilabilir havuz bulunamadi"
    finally:
        oturum.close()
