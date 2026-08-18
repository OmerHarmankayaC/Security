#!/usr/bin/env python3
"""Agirlik kalibrasyonu olcum araci (Backlog T-07, T-08).

Kullanim:
    python scripts/agirlik_kalibrasyonu.py                 # mevcut agirliklarla olc
    python scripts/agirlik_kalibrasyonu.py S2=40 S4=8      # once ayarla, sonra olc
    python scripts/agirlik_kalibrasyonu.py --geri-al       # ozgun agirliklara don

## Neden GERCEK COZUM YOLUNU kullanir

Ilk yazilisinda `model_kur` + `CozucuAdaptoru.coz` dogrudan cagriliyordu ve
her agirlik kumesinde BIREBIR ayni sayi cikiyordu. Sebep agirliklar degildi:
cozum hic bulunamiyordu (`durum=cozum_yok`, sifir atama). Olculen sey bos bir
cizelgeydi - "0 saat fazla calisma" bosluktan geliyordu, "21,0 sapma" ise
sapma degil en buyuk adil payin kendisiydi (yuk sifirken |0 - pay| = pay).

Nedeni ISITMA PENCERESIYDI. TD-5 isitma gunlerinin SABIT GIRDI oldugunu
soyler; dogrudan cagri onlari karar degiskeni birakiyordu. Yedi gun x otuz
kisi x yirmi dort saatlik ek serbestlik, uzerinde talep bulunmayan ama butun
zorunlu kurallarin islediigi bir arama uzayi acti ve cozucu yuz yirmi
saniyede bile uygun cozum bulamadi. Ayni donem gercek yolda altmis saniyede
cozuluyor.

Ders: OLCUM ARACI URETIM YOLUNU TAKLIT ETMEZ, ONU KULLANIR. Taklit ettigi
anda olctugu sey urunun davranisi olmaktan cikar.

## Ne olcer

  T-07  Dengeli senaryoda fazla calisma (hedef: sifira yakin)
  T-08  Donem ici gece sapmasi = K3 (esik: 8 gece saati, Charter 1.5)
        S1 baskinligi (w1 > S1-haric agirlikli toplam)

Her kosum bir cozum isi ve bir taslak surum yaratir; bu bilinclidir, cunku
uretim yolu odur. Birikenler `--temizle` ile silinir.
"""

import argparse
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.db import OturumYerel  # noqa: E402
from app.kurallar.zaman_araligi import gece_saati_mi  # noqa: E402
from app.kurallar.zorunlu import h10_fazla_calisma_saatleri  # noqa: E402
from app.models.kural import Kural  # noqa: E402
from app.models.sonuc import CizelgeSurumu, CizelgeSurumuDurumu, Donem  # noqa: E402
from app.repositories.sonuc import AtamaDeposu, CozumIsiDeposu  # noqa: E402
from app.services.atama_donusumu import atama_kayitlarina_cevir  # noqa: E402
from app.services.baglam_kurucu import baglam_olustur  # noqa: E402
from app.services.cozum_servisi import CozumServisi  # noqa: E402
from scripts.cozum_iscisi import siradaki_isi_isle  # noqa: E402

# SRS 4.2 H10 esigine karsilik gelen kabul esigi (Charter 1.5).
K3_ESIK = 8.0

# Ozgun agirliklar — `--geri-al` bunlara doner. Kalibrasyon bir ARAMA
# surecidir ve yarim kalmis bir kume birakmak, sonraki olcumun tabanini
# sessizce kaydirir.
OZGUN = {
    "S1": 10000,
    "S1f": 2,
    "S2": 10,
    "S3": 8,
    "S4": 1,
    "S5": 12,
    "S6": 4,
    "S6b": 6,
    "S7": 6,
    "S8": 15,
}


def _agirliklari_yaz(oturum, degerler: dict[str, float]) -> None:
    for kural in oturum.execute(select(Kural)).scalars():
        if kural.kimlik in degerler:
            kural.agirlik = Decimal(str(degerler[kural.kimlik]))
    oturum.commit()


def _dengeli_donem(oturum) -> Donem:
    """Gosterim verisinin RAHAT haftasi (T-07'nin acikca isaret ettigi senaryo).

    Uretecte haftalar eskiden yeniye sirali; dar hafta ucuncu, rahat hafta
    dorduncu sirada (indis 2). Indis oradan okunur, burada yeniden sayilmaz.
    """
    donemler = sorted(
        oturum.execute(select(Donem)).scalars().all(), key=lambda d: d.baslangic_tarihi
    )
    if len(donemler) < 3:
        raise SystemExit(
            "Gosterim verisi yok. Once: "
            "VERI_TEMIZLIGINE_IZIN=true python scripts/demo_veri_uret.py --reset"
        )
    return donemler[2]


def _coz(oturum, donem: Donem, zaman_limiti: float) -> tuple[list, object]:
    """URETIM YOLU: cozum isi acilir ve isci calistirilir.

    Isitma penceresinin sabitlenmesi, cozum ipucu ve ceza dokumunun yazilmasi
    burada olur; taklit edilse hepsi tek tek atlanirdi.
    """
    is_kaydi = CozumServisi(oturum).baslat(donem.donem_id, zaman_limiti_saniye=zaman_limiti)
    if is_kaydi is None:
        raise SystemExit(f"{donem.baslangic_tarihi} icin cozum isi acilamadi")
    oturum.commit()

    for _ in range(6):
        siradaki_isi_isle(oturum)
        oturum.expire_all()
        taze = CozumIsiDeposu(oturum).getir(is_kaydi.is_id)
        if taze is not None and taze.ceza_dokumu is not None:
            break
    taze = CozumIsiDeposu(oturum).getir(is_kaydi.is_id)
    if taze is None or taze.surum_id is None:
        raise SystemExit("cozum isi sonuclanmadi")

    atamalar = atama_kayitlarina_cevir(AtamaDeposu(oturum).surume_gore_getir(taze.surum_id))
    return atamalar, taze


def olc(oturum, zaman_limiti: float) -> None:
    etkin = {
        k.kimlik: float(k.agirlik)
        for k in oturum.execute(select(Kural)).scalars()
        if k.agirlik is not None and k.aktif
    }
    print("agirliklar :", {k: int(v) for k, v in sorted(etkin.items())})

    donem = _dengeli_donem(oturum)
    print(f"donem      : {donem.baslangic_tarihi} .. {donem.bitis_tarihi} (dengeli hafta)")

    atamalar, is_kaydi = _coz(oturum, donem, zaman_limiti)
    # BOS CIZELGE SESSIZCE OLCULMEZ. Ilk surumun tamami bu yuzden yaniltmisti.
    if not atamalar:
        print("!! COZUM BOS — olcum anlamsiz, agirliklar hakkinda bir sey soylemez")
        return
    print(f"cozum      : {len(atamalar)} blok, durum={is_kaydi.durum.value}")

    baglam = baglam_olustur(oturum, donem, yalniz_aktif=False)

    # --- T-07: dengeli senaryoda fazla calisma sifira yakin olmali
    esik = 45.0
    fazla = h10_fazla_calisma_saatleri(atamalar, baglam, esik)
    tasiyan = {p: s for p, s in fazla.items() if s > 0}
    print(
        f"T-07       : {len(tasiyan)} kisi fazla calisma, toplam {sum(tasiyan.values()):.0f} saat"
    )

    # --- T-08 / K3: DONEM ICI gece sapmasi (Charter 1.5)
    paylar = baglam.adil_paylar(lambda a: gece_saati_mi(a[1]))
    havuz = [p for p, v in paylar.items() if v > 0]
    yuk: dict[int, float] = {}
    for a in atamalar:
        if baglam.donem_icinde(a.tarih):
            yuk[a.personel_id] = yuk.get(a.personel_id, 0.0) + a.gece_saati
    sapmalar = sorted((abs(yuk.get(p, 0.0) - paylar[p]) for p in havuz), reverse=True)
    asan = sum(1 for s in sapmalar if s > K3_ESIK)
    print(
        f"K3 (T-08)  : azami {sapmalar[0]:.1f} / ortanca {sapmalar[len(sapmalar) // 2]:.1f} "
        f"(esik {K3_ESIK:.0f}) | esigi asan {asan}/{len(havuz)}"
    )

    # --- S1 baskinligi: cozucunun KENDI dokumunden
    dokum = is_kaydi.ceza_dokumu or {}
    s1_haric = sum(float(v) * etkin.get(k, 0.0) for k, v in dokum.items() if k != "S1")
    w1 = etkin.get("S1", 0.0)
    print(
        f"S1 baskin  : w1={w1:.0f} > {s1_haric:.0f} -> "
        f"{'KORUNUYOR' if w1 > s1_haric else 'BOZULDU'}"
    )
    print(f"toplam ceza: {is_kaydi.en_iyi_ceza}")


def temizle(oturum) -> None:
    """Olcum kosumlarinin biraktigi taslak surumleri siler."""
    taslaklar = (
        oturum.execute(
            select(CizelgeSurumu).where(CizelgeSurumu.durum == CizelgeSurumuDurumu.TASLAK)
        )
        .scalars()
        .all()
    )
    for s in taslaklar:
        oturum.delete(s)
    oturum.commit()
    print(f"{len(taslaklar)} taslak surum silindi")


def main() -> int:
    ayristirici = argparse.ArgumentParser(description="Agirlik kalibrasyonu olcumu")
    ayristirici.add_argument("agirlik", nargs="*", help="S2=40 S4=8 gibi")
    ayristirici.add_argument("--geri-al", action="store_true", help="Ozgun agirliklara don")
    ayristirici.add_argument("--temizle", action="store_true", help="Olcum taslaklarini sil")
    ayristirici.add_argument("--zaman-limiti", type=float, default=60.0)
    a = ayristirici.parse_args()

    oturum = OturumYerel()
    try:
        if a.temizle:
            temizle(oturum)
            return 0
        if a.geri_al:
            _agirliklari_yaz(oturum, OZGUN)
            print("ozgun agirliklara donuldu:", OZGUN)
            return 0
        if a.agirlik:
            yeni = {}
            for p in a.agirlik:
                k, v = p.split("=")
                yeni[k] = float(v)
            _agirliklari_yaz(oturum, yeni)
        olc(oturum, a.zaman_limiti)
        return 0
    finally:
        oturum.close()


if __name__ == "__main__":
    raise SystemExit(main())
