"""Kural katalogunun TEK tohum tanimi (SRS bolum 4).

Katalog daha once yalnizca `scripts/demo_veri_uret.py` icinde duruyordu ve
gocler (e7b2c4915d80) katalogun UC satirini (H9, H10, S1f) ayrica
yaziyordu. Bos bir veritabaninda goc zinciri kosturuldugunda katalog bu uc
satirdan ibaret kaliyor, uretec sonradan kosturuldugunda ise ayni uc kimlik
icin `kimlik` tekilligi hatasi veriyordu. Iki yerde yazilan bir olgunun
klasik sonucu: ortamlar arasinda sessizce ayrisan katalog.

Bu modul katalogu tek yerde tanimlar ve kurulumu KIMLIK UZERINDEN
UPSERT yapar; boylece:

  - bos + goc kosturulmus bir veritabaninda tam katalog olusur,
  - gocun yazdigi uc satir yinelenmez, uzerine yazilir,
  - uretec iki kez kosturuldugunda katalog degismez.

Kabul olcumu (`scripts/kabul_olcumu.py`) kendi ZORUNLU kural parametre
kopyasini tutmaya devam eder; o akis ayri bir veritabaninda kosar ve bu
turun kapsami disindadir.
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.kural import Kural, KuralTipi

# SRS 4.2 / 4.3 / 4.4: on zorunlu kisit, on esnek hedef. Amac fonksiyonunun
# sembol listesi (SRS 4.4) bu yirmi kimligin tamamini kapsar.
KURAL_TANIMLARI: list[dict[str, Any]] = [
    {"kimlik": "H1", "tip": KuralTipi.ZORUNLU, "parametreler": {}, "agirlik": None},
    {
        "kimlik": "H2",
        "tip": KuralTipi.ZORUNLU,
        "parametreler": {"asgari_dinlenme_saati": 16},
        "agirlik": None,
    },
    {
        "kimlik": "H3",
        "tip": KuralTipi.ZORUNLU,
        "parametreler": {"azami_ardisik_gece": 3},
        "agirlik": None,
    },
    {
        "kimlik": "H4",
        "tip": KuralTipi.ZORUNLU,
        "parametreler": {"azami_ardisik_calisma_gunu": 6},
        "agirlik": None,
    },
    {
        "kimlik": "H5",
        "tip": KuralTipi.ZORUNLU,
        "parametreler": {"haftalik_mutlak_tavan": 66},
        "agirlik": None,
    },
    {
        "kimlik": "H6",
        "tip": KuralTipi.ZORUNLU,
        "parametreler": {"haftalik_asgari_izin_gunu": 1},
        "agirlik": None,
    },
    {"kimlik": "H7", "tip": KuralTipi.ZORUNLU, "parametreler": {}, "agirlik": None},
    {"kimlik": "H8", "tip": KuralTipi.ZORUNLU, "parametreler": {}, "agirlik": None},
    {
        "kimlik": "H9",
        "tip": KuralTipi.ZORUNLU,
        "parametreler": {"azami_gunluk_saat": 11},
        "agirlik": None,
    },
    {
        "kimlik": "H10",
        "tip": KuralTipi.ZORUNLU,
        "parametreler": {"fazla_calisma_esigi": 45, "yillik_fazla_kotasi": 270},
        "agirlik": None,
    },
    # Agirlik kalibrasyonu (PROGRESS, agirlik kalibrasyonu turu): S1 agirligi,
    # digerlerinin agirlikli toplam katkisindan belirgin buyuk olmali (SRS S1,
    # "baskin agirlik" ilkesi) - 1000 sikisik senaryoda S1-haric agirlikli
    # toplami (2107) garantilemiyordu, 10000'e cikarildi (bkz.
    # tests/test_agirlik_kalibrasyonu.py). Ayrica S2/S3'un ham birimi VARDIYA,
    # S4'unku SAAT (bir vardiya=8 saat); w4, vardiya-esdegeri basina S4'un
    # S2/S3 kadar onemli sayilmasi icin ~w2/8 olacak sekilde dusuruldu.
    {"kimlik": "S1", "tip": KuralTipi.ESNEK, "parametreler": {}, "agirlik": 10000},
    # w1f = 2 (K4 baslangic degeri). Kesin olan `w1f << w1` bagintisidir.
    {"kimlik": "S1f", "tip": KuralTipi.ESNEK, "parametreler": {}, "agirlik": 2},
    {"kimlik": "S2", "tip": KuralTipi.ESNEK, "parametreler": {}, "agirlik": 10},
    {"kimlik": "S3", "tip": KuralTipi.ESNEK, "parametreler": {}, "agirlik": 8},
    {"kimlik": "S4", "tip": KuralTipi.ESNEK, "parametreler": {}, "agirlik": 1},
    {"kimlik": "S5", "tip": KuralTipi.ESNEK, "parametreler": {}, "agirlik": 12},
    {
        "kimlik": "S6",
        "tip": KuralTipi.ESNEK,
        "parametreler": {"desen_toleransi_saat": 2},
        "agirlik": 4,
    },
    # S6b (bina tutarliligi) bu senaryoda pasif: nokta sadelestirmesinden beri
    # butun gorev noktalari tesis geneli (bina_id NULL), bina degisimi fiziksel
    # olarak imkansiz oldugundan S6b modelde daima 0 katki verir. Kural katalogda
    # kalir - binaya bagli bir nokta tanimlanirsa kendiliginden devreye girer -
    # ama gereksiz bir amac fonksiyonu terimi olarak aktif tutulmaz.
    {"kimlik": "S6b", "tip": KuralTipi.ESNEK, "parametreler": {}, "agirlik": 6, "aktif": False},
    {"kimlik": "S7", "tip": KuralTipi.ESNEK, "parametreler": {}, "agirlik": 6},
    {"kimlik": "S8", "tip": KuralTipi.ESNEK, "parametreler": {}, "agirlik": 15},
]


def katalogu_kur(oturum: Session) -> int:
    """Katalogu kimlik uzerinden upsert eder; yazilan satir sayisini dondurur.

    UPSERT, INSERT degil: goc zinciri katalogun bir bolumunu zaten yazmis
    olabilir (H9, H10, S1f). Duz INSERT o veritabaninda `kimlik` tekilligine
    carpar, "once sil sonra yaz" ise kullanicinin ekrandan degistirdigi
    agirliklari sessizce geri alirdi. Upsert her iki durumda da katalogu
    tanimla ayni hale getirir ve ne yaptigini sayiyla soyler.

    `flush` cagirilir, `commit` CAGIRILMAZ: islem sinirinin sahibi cagirandir.
    """
    mevcut = {kural.kimlik: kural for kural in oturum.execute(select(Kural)).scalars().all()}
    for tanim in KURAL_TANIMLARI:
        kural = mevcut.get(tanim["kimlik"])
        if kural is None:
            oturum.add(Kural(**tanim))
            continue
        kural.tip = tanim["tip"]
        kural.parametreler = tanim["parametreler"]
        kural.agirlik = tanim["agirlik"]
        kural.aktif = tanim.get("aktif", True)
    oturum.flush()
    return len(KURAL_TANIMLARI)


__all__ = ["KURAL_TANIMLARI", "katalogu_kur"]
