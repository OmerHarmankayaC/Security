"""Bir cizelge surumunun TALEPTEN SAPMASINI kalici hale getirir.

Iki yonu vardir ve ikisi de ayni karsilastirmadan (`atanan - gereken`)
dogar:

  eksik  -> `kapsama_acigi`  (SRS 4.3 S1 alt siniri, esnek hedef)
  fazla  -> `fazla_kadro`    (SRS 4.3 S1 ust siniri)

NEDEN BU MODUL VAR. Iki ayri sorun ayni yere bakiyordu:

1. `kapsama_acigi` tablosunu yalnizca COZUCU yaziyordu
   (`cozum_servisi.cozumu_yaz`). Manuel duzenleme yalnizca `atama`
   satirina dokunuyordu; dolayisiyla elle bir atamayi kaldirmak gercek
   bir acik dogurdugu halde tablo BOS kaliyordu. Sonucta Analiz'deki
   kapsama orani (SDD 5.7: "kapsama acigi tablosundan turetilir"), surum
   raporundaki acik sayisi ve disa aktarilan acik dosyasi elle
   duzenlenmis her surumde bayat oluyordu.

2. Fazla kadronun hicbir kalici izi yoktu; yalnizca duzenleme anindaki
   dogrulama panelinde goruunup kayboluyordu.

Ikisi ayni anda cozulmek zorundaydi: fazla kadro uygulama aninda
kaliciligsaydi ama acik bayat kalsaydi, ayni raporda iki farkli tazelikte
veri bulunurdu.

KAYNAK: veritabanindaki atamalar. Cozucu yolu kendi `eksik`
degiskenlerinden yazmaya devam eder (SDD 4.2.4 o birebirligi tanimliyor);
`tests/test_talep_sapmasi.py` iki kaynagin cozulmus bir surumde AYNI
sonucu verdigini olcer - SDD 3.2.1'in cozucu-dogrulayici uyum ilkesinin
bu tabloya uygulanmis hali.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.kurallar.baglam import AtamaKaydi
from app.kurallar.zaman_araligi import aralik_sure_saat, saatleri_araliklara_birlestir
from app.models.sonuc import FazlaKadro, KapsamaAcigi
from app.repositories.sonuc import (
    AtamaDeposu,
    CizelgeSurumuDeposu,
    DonemDeposu,
    FazlaKadroDeposu,
    KapsamaAcigiDeposu,
)
from app.services.baglam_kurucu import baglam_olustur


@dataclass(frozen=True, slots=True)
class SapmaOzeti:
    """Yenilemenin sonucu; cagiran bunu kullaniciya bildirebilir."""

    eksik_hucre: int
    eksik_kisi: int
    fazla_hucre: int
    fazla_kisi: int


def sapmalari_yenile(oturum: Session, surum_id: int) -> SapmaOzeti | None:
    """Surumun talep sapmalarini atamalardan yeniden hesaplar ve yazar.

    Iki tablo da once TAMAMEN silinip yeniden yazilir. Fark alip
    guncellemek yerine boyle yapilmasinin nedeni, kismi guncellemenin
    "artik gecerli olmayan ama silinmeyi unutulmus satir" bicimini acik
    birakmasidir; sapma kumesi zaten kucuk (hucre sayisi kadar) ve tek
    islem icinde yazilir.

    Surum ya da donemi bulunamazsa None doner.
    """
    surum = CizelgeSurumuDeposu(oturum).getir(surum_id)
    if surum is None:
        return None
    donem = DonemDeposu(oturum).getir(surum.donem_id)
    if donem is None:
        return None

    # yalniz_aktif=False: var olan bir surumun atamalari, sonradan
    # pasiflestirilmis tanimlara isaret ediyor olabilir (dogrulama
    # servisiyle ayni gerekce).
    baglam = baglam_olustur(oturum, donem, yalniz_aktif=False)
    atamalar = AtamaDeposu(oturum).surume_gore_getir(surum_id)
    atama_kayitlari = [
        AtamaKaydi(a.personel_id, a.tarih, a.vardiya_tipi_id, a.nokta_id) for a in atamalar
    ]

    kapsama_depo = KapsamaAcigiDeposu(oturum)
    fazla_depo = FazlaKadroDeposu(oturum)
    kapsama_depo.surume_gore_sil(surum_id)
    fazla_depo.surume_gore_sil(surum_id)

    # SAAT EKSENINDE hesaplanir, ARALIK olarak yazilir (SDD 4.2.4).
    # ISITMA PENCERESI DISARIDA: `talep_saat` zaman ekseni uzerinde cozulur
    # ve o eksen onceki donemin son yedi gununu de kapsar (SRS TD-5); o
    # gunlerin atamalari BU surumun parcasi degildir. Cozucu de ayni siniri
    # kullanir (esnek.py S1). Filtre olmadan tek gunluk bir donem yedi
    # gunluk hayali bir acik uretiyordu.
    eksik_saatler, fazla_saatler = baglam.sapma_saatleri(atama_kayitlari)

    eksik_hucre = eksik_kisi = fazla_hucre = fazla_kisi = 0
    for nokta_id, saatler in sorted(eksik_saatler.items()):
        for tarih, bas, bit, sayi in saatleri_araliklara_birlestir(saatler):
            eksik_hucre += 1
            eksik_kisi += sayi * aralik_sure_saat(bas, bit)
            oturum.add(
                KapsamaAcigi(
                    surum_id=surum_id,
                    tarih=tarih,
                    baslangic=bas,
                    bitis=bit,
                    nokta_id=nokta_id,
                    eksik_sayi=sayi,
                )
            )
    for nokta_id, saatler in sorted(fazla_saatler.items()):
        for tarih, bas, bit, sayi in saatleri_araliklara_birlestir(saatler):
            fazla_hucre += 1
            fazla_kisi += sayi * aralik_sure_saat(bas, bit)
            oturum.add(
                FazlaKadro(
                    surum_id=surum_id,
                    tarih=tarih,
                    baslangic=bas,
                    bitis=bit,
                    nokta_id=nokta_id,
                    fazla_sayi=sayi,
                )
            )
    oturum.flush()
    return SapmaOzeti(
        eksik_hucre=eksik_hucre,
        eksik_kisi=eksik_kisi,
        fazla_hucre=fazla_hucre,
        fazla_kisi=fazla_kisi,
    )


__all__ = ["SapmaOzeti", "sapmalari_yenile"]
