"""Cozucu-dogrulayici uyum testinin OLCEKLI hali: rastgele uretilen 20+ ornek
gercek CP-SAT cozucusuyle cozulur ve cikan cizelge dogrulayicidan gecirilir
(UYGULAMA_PLANI.md Sprint 3 Gun 14; SDD 3.2.1).

SDD 3.2.1'in sozu: "rastgele uretilen ornekler cozulur ve elde edilen cizelge
dogrulayicidan gecirilir; cozucunun gecerli saydigi bir cizelgede
dogrulayicinin ihlal bulmasi ... bir YAZILIM HATASI olarak ele alinir."

tests/test_cozucu_dogrulayici_uyumu.py Sprint 1'den kalma iskeledir (elle
kurulan cizelgeler, cozucu yok) ve dogrulayicinin kendi ic tutarliligini
guvenceye alir. Bu dosya onun yerini almaz, uzerine cozucuyu ekler.

Veritabani GEREKTIRMEZ: model_kur ve CozucuAdaptoru yalnizca Baglam uzerinde
calisir. Ornekler kucuk tutulur (5-9 personel, 5-10 gun) ki 20+ ornek makul
surede bitsin; amac olcek stresi degil, kural motorunun iki yorumlayicisi
arasindaki UYUM.
"""

import random
from datetime import date, time, timedelta

import pytest

from app.cozucu import CozucuAdaptoru, model_kur
from app.kurallar import (
    AtamaKaydi,
    Baglam,
    GorevNoktasiBilgisi,
    PersonelBilgisi,
    VardiyaTipiBilgisi,
)
from app.kurallar.kayit_defteri import bul
from app.models.kural import KuralTipi
from tests.conftest import blok_talebini_saate_ac

ORNEK_SAYISI = 24  # Gun 14: "rastgele 20+ ornek"
TOHUM = 20260814  # Sabit tohum: basarisiz bir ornek birebir yeniden uretilebilsin.

GECE, GUNDUZ, AKSAM = 1, 2, 3
_VARDIYA_TIPLERI = {
    GECE: VardiyaTipiBilgisi(GECE, time(0, 0), time(8, 0), 8.0, True),
    GUNDUZ: VardiyaTipiBilgisi(GUNDUZ, time(8, 0), time(16, 0), 8.0, False),
    AKSAM: VardiyaTipiBilgisi(AKSAM, time(16, 0), time(0, 0), 8.0, False),
}

_H_PARAMETRELERI = {
    "H1": {},
    "H2": {"asgari_dinlenme_saati": 16},
    "H3": {"azami_ardisik_gece": 3},
    "H4": {"azami_ardisik_calisma_gunu": 6},
    "H5": {"haftalik_mutlak_tavan": 66},
    "H6": {"haftalik_asgari_izin_gunu": 1},
    "H7": {},
    "H8": {},
}
_S_AGIRLIKLARI = {
    "S1": 10000.0,
    "S2": 40.0,
    "S3": 35.0,
    "S4": 5.0,
    "S5": 20.0,
    "S6": 10.0,
    "S6b": 10.0,
    "S7": 15.0,
    "S8": 15.0,
}


def _kurallari_kur() -> list:
    kurallar = []
    for kimlik, parametreler in _H_PARAMETRELERI.items():
        kurallar.append(bul(kimlik)(parametreler=parametreler))
    for kimlik, agirlik in _S_AGIRLIKLARI.items():
        kurallar.append(bul(kimlik)(parametreler={}, agirlik=agirlik))
    return kurallar


def _rastgele_ornek(rastgele: random.Random, sira: int) -> tuple[Baglam, list[date]]:
    """Cozulebilir olmasi BEKLENEN bir ornek uretir.

    Talep, kadronun H5/H6 tavani altinda kalacak sekilde ust sinirlanir:
    bir personel haftada en fazla bes vardiya tutabilir (SRS 3.3.6), yani
    gun basina azami toplam talep ~ personel_sayisi * 5/7. Bu, ornegin
    kapsama acigi olmadan cozulebilmesini saglar; uyum testinin olctugu sey
    fizibilite degil, cozucunun urettigi cizelgenin dogrulayicidan temiz
    gecmesidir. (S1 esnek oldugu icin ornek yine de cozulur; acik cikmasi
    testi gecersiz kilmaz, yalnizca daha az bilgi tasir.)
    """
    personel_sayisi = rastgele.randint(5, 9)
    gun_sayisi = rastgele.randint(5, 10)
    nokta_sayisi = rastgele.randint(1, 2)
    baslangic = date(2026, 3, 2) + timedelta(days=7 * sira)

    # Yetkinlikler: 1 = genel (her noktada gecerli), 2 = ozel.
    noktalar: dict[int, GorevNoktasiBilgisi] = {}
    for nokta_id in range(1, nokta_sayisi + 1):
        onkosul = 1 if nokta_id == 1 else rastgele.choice([1, 2])
        noktalar[nokta_id] = GorevNoktasiBilgisi(nokta_id, onkosul_yetkinlik_id=onkosul)

    personel: dict[int, PersonelBilgisi] = {}
    for personel_id in range(1, personel_sayisi + 1):
        # Herkes 1'e sahip; bir kismi 2'ye de sahip - boylece H8 gercekten baglar.
        yetkinlikler = {1} | ({2} if rastgele.random() < 0.6 else set())
        personel[personel_id] = PersonelBilgisi(
            personel_id,
            aktif_baslangic=date(2026, 1, 1),
            aktif_bitis=None,
            yetkinlikler=frozenset(yetkinlikler),
            haftalik_hedef_saat=40.0,
        )

    gunler = [baslangic + timedelta(days=i) for i in range(gun_sayisi)]
    gunluk_tavan = max(1, int(personel_sayisi * 5 / 7))
    talep: dict[tuple[date, int, int], int] = {}
    for gun in gunler:
        kalan = gunluk_tavan
        for vardiya_tipi_id in (GUNDUZ, AKSAM, GECE):
            for nokta_id in noktalar:
                if kalan <= 0:
                    break
                gereken = rastgele.randint(0, min(2, kalan))
                if gereken:
                    talep[(gun, vardiya_tipi_id, nokta_id)] = gereken
                    kalan -= gereken

    # Isitma penceresi yok (zaman_ekseni = donem gunleri): bu testin konusu
    # TD-5 degil, uyum. Boylece ornek de kucuk kalir.
    baglam = Baglam(
        vardiya_tipleri=dict(_VARDIYA_TIPLERI),
        gorev_noktalari=noktalar,
        personel=personel,
        talep_saat=blok_talebini_saate_ac(talep, dict(_VARDIYA_TIPLERI)),
        donem_baslangic=gunler[0],
        donem_bitis=gunler[-1],
    )
    return baglam, gunler


@pytest.mark.parametrize("sira", range(ORNEK_SAYISI))
def test_cozucunun_urettigi_cizelge_dogrulayicidan_temiz_gecer(sira: int) -> None:
    """SDD 3.2.1: cozucunun gecerli saydigi cizelgede dogrulayici ZORUNLU
    kisit ihlali bulmamalidir."""
    rastgele = random.Random(TOHUM + sira)
    baglam, gunler = _rastgele_ornek(rastgele, sira)
    kurallar = _kurallari_kur()

    model, x, baglam, _ceza_terimleri = model_kur(baglam, gunler, kurallar)
    sonuc = CozucuAdaptoru.coz(model, x, zaman_limiti_saniye=5.0, arama_iscisi_sayisi=3)

    assert sonuc.durum in ("optimal", "uygun"), (
        f"Ornek {sira} cozulemedi (tohum {TOHUM + sira}); talep kadro tavaninin "
        f"altinda tutuldugu icin uygun bir cozum beklenir."
    )

    atamalar = [AtamaKaydi(p, g, v, n) for (p, g, v, n) in sonuc.atanan_anahtarlar]
    ihlaller = []
    for kural in kurallar:
        if kural.tip is KuralTipi.ZORUNLU:
            ihlaller.extend(kural.dogrula(atamalar, baglam))

    assert ihlaller == [], (
        f"Ornek {sira} (tohum {TOHUM + sira}): cozucunun gecerli saydigi cizelgede "
        f"dogrulayici ihlal buldu - SDD 3.2.1'e gore bu bir yazilim hatasidir. "
        f"Ihlaller: {[(i.kural_kimlik, i.aciklama) for i in ihlaller[:5]]}"
    )
