"""S1-S8 esnek hedefleri (SRS Bolum 4.3, SDD Ek A ornek sablonu - S2).

dogrula metotlari, SDD Ek A'daki S2 ornegiyle tutarli olarak agirliksiz
(ham) ceza buyuklugu dondurur; agirlikli toplam (w1..w8) amac fonksiyonu
(SDD 5.3, Sprint 2 Gun 6) ve ceza dokumu raporlamasi (SDD 5.7,
Sprint 3 Gun 12) tarafindan hesaplanir.
"""

from collections import Counter, defaultdict
from collections.abc import Callable
from datetime import date, timedelta
from math import ceil, floor

from app.kurallar.baglam import AtamaKaydi, Baglam
from app.kurallar.kayit_defteri import kayitli
from app.kurallar.temel import EsnekHedef, Ihlal
from app.kurallar.yardimcilar import calisilan_gunler
from app.models.girdi import TercihTipi


@kayitli("S1")
class S1TalepKarsilama(EsnekHedef):
    """Nokta bazinda kapsama acigi: baskin agirlikli, alt sinir esnek hedef."""

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        atanan = Counter((a.tarih, a.vardiya_tipi_id, a.nokta_id) for a in atamalar)
        ihlaller: list[Ihlal] = []
        for (tarih, vardiya_tipi_id, nokta_id), gereken in baglam.talep.items():
            eksik = gereken - atanan.get((tarih, vardiya_tipi_id, nokta_id), 0)
            if eksik > 0:
                ihlaller.append(
                    Ihlal(
                        kural_kimlik=self.kimlik,
                        tarih=tarih,
                        ceza=eksik,
                        aciklama=(
                            f"{tarih} gunu {vardiya_tipi_id} nolu vardiyada {nokta_id} nolu "
                            f"noktada {eksik} kisi eksik"
                        ),
                    )
                )
        return ihlaller


@kayitli("S2")
class S2GeceAdaleti(EsnekHedef):
    """Kisi basina gece vardiyasi sayisinin donem hedefinden sapmasi (SDD Ek A ornegi)."""

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        return _adalet_sapmasi_ihlalleri(
            kural_kimlik=self.kimlik,
            atamalar=atamalar,
            baglam=baglam,
            atama_uygun_mu=lambda a: baglam.gece_mi(a.vardiya_tipi_id),
            talep_uygun_mu=lambda anahtar: baglam.gece_mi(anahtar[1]),
            aciklama="gece vardiyasi sayisi donem hedefinden sapiyor",
        )


@kayitli("S3")
class S3HaftaSonuAdaleti(EsnekHedef):
    """Kisi basina hafta sonu/resmi tatil vardiyasi sayisinin hedeften sapmasi (TD-3)."""

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        return _adalet_sapmasi_ihlalleri(
            kural_kimlik=self.kimlik,
            atamalar=atamalar,
            baglam=baglam,
            atama_uygun_mu=lambda a: baglam.hafta_sonu_mu(a.tarih),
            talep_uygun_mu=lambda anahtar: baglam.hafta_sonu_mu(anahtar[0]),
            aciklama="hafta sonu/resmi tatil vardiyasi sayisi donem hedefinden sapiyor",
        )


@kayitli("S4")
class S4ToplamSaatDengesi(EsnekHedef):
    """Kisi basina toplam saatin, kisisel donemlik hedeften mutlak sapmasi."""

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        donem_gun_sayisi = _donem_gun_sayisi(baglam)
        saatler: dict[int, float] = defaultdict(float)
        for a in atamalar:
            if baglam.donem_icinde(a.tarih):
                saatler[a.personel_id] += baglam.sure_saat(a.vardiya_tipi_id)

        ihlaller: list[Ihlal] = []
        for personel_id, personel in baglam.personel.items():
            hedef_saat = personel.haftalik_hedef_saat * (donem_gun_sayisi / 7)
            sapma = abs(saatler.get(personel_id, 0.0) - hedef_saat)
            if sapma > 1e-9:
                ihlaller.append(
                    Ihlal(
                        kural_kimlik=self.kimlik,
                        personel_id=personel_id,
                        ceza=sapma,
                        aciklama=(
                            f"Toplam saat {saatler.get(personel_id, 0.0):.1f}, "
                            f"donemlik hedef {hedef_saat:.1f} saatten {sapma:.1f} saat sapiyor"
                        ),
                    )
                )
        return ihlaller


@kayitli("S5")
class S5TercihKarsilama(EsnekHedef):
    """Onaylanmis tercihlerin ihlal edilip edilmedigi (Baglam'a yalnizca onaylananlar girer)."""

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        gunluk_atama: dict[tuple[int, date], AtamaKaydi] = {
            (a.personel_id, a.tarih): a for a in atamalar
        }
        ihlaller: list[Ihlal] = []
        for tercih in baglam.tercihler:
            atama = gunluk_atama.get((tercih.personel_id, tercih.tarih))
            if tercih.tip == TercihTipi.CALISMAMA:
                ihlal_var = atama is not None
                aciklama = "Calismama tercihine ragmen atama yapilmis"
            else:
                ihlal_var = atama is not None and atama.vardiya_tipi_id != tercih.vardiya_tipi_id
                aciklama = "Tercih edilen vardiya tipinden farkli bir vardiyaya atanmis"
            if ihlal_var:
                ihlaller.append(
                    Ihlal(
                        kural_kimlik=self.kimlik,
                        personel_id=tercih.personel_id,
                        tarih=tercih.tarih,
                        ceza=1,
                        aciklama=aciklama,
                    )
                )
        return ihlaller


@kayitli("S6")
class S6VardiyaDeseniTutarliligi(EsnekHedef):
    """Ardisik gunlerde vardiya tipi veya bina degisimi (tesis geneli noktalar haric)."""

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        gunluk: dict[int, dict[date, AtamaKaydi]] = defaultdict(dict)
        for a in atamalar:
            gunluk[a.personel_id][a.tarih] = a

        ihlaller: list[Ihlal] = []
        for personel_id, gun_map in gunluk.items():
            for gun in sorted(gun_map):
                sonraki_gun = gun + timedelta(days=1)
                if sonraki_gun not in gun_map:
                    continue
                bugun, yarin = gun_map[gun], gun_map[sonraki_gun]
                if bugun.vardiya_tipi_id != yarin.vardiya_tipi_id:
                    ihlaller.append(
                        Ihlal(
                            kural_kimlik=self.kimlik,
                            personel_id=personel_id,
                            tarih=sonraki_gun,
                            ceza=1,
                            aciklama="Ardisik gunde vardiya tipi degisti",
                        )
                    )
                bugun_nokta = baglam.gorev_noktalari.get(bugun.nokta_id)
                yarin_nokta = baglam.gorev_noktalari.get(yarin.nokta_id)
                if (
                    bugun_nokta is not None
                    and yarin_nokta is not None
                    and bugun_nokta.bina_id is not None
                    and yarin_nokta.bina_id is not None
                    and bugun_nokta.bina_id != yarin_nokta.bina_id
                ):
                    ihlaller.append(
                        Ihlal(
                            kural_kimlik=self.kimlik,
                            personel_id=personel_id,
                            tarih=sonraki_gun,
                            ceza=1,
                            aciklama="Ardisik gunde bina degisti",
                        )
                    )
        return ihlaller


@kayitli("S7")
class S7IzoleGun(EsnekHedef):
    """Tek gunluk calisma bloklari ve tek gunluk izinler."""

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        aralik = _bilinen_aralik(atamalar, baglam)
        if aralik is None:
            return []
        baslangic, bitis = aralik
        if (bitis - baslangic).days < 2:
            return []

        calisilanlar = calisilan_gunler(atamalar)
        personel_idleri = set(baglam.personel) | {a.personel_id for a in atamalar}

        ihlaller: list[Ihlal] = []
        for personel_id in personel_idleri:
            gunler = calisilanlar.get(personel_id, set())
            gun = baslangic + timedelta(days=1)
            son = bitis - timedelta(days=1)
            while gun <= son:
                onceki = gun - timedelta(days=1)
                sonraki = gun + timedelta(days=1)
                bugun_calisti = gun in gunler
                onceki_calisti = onceki in gunler
                sonraki_calisti = sonraki in gunler
                if bugun_calisti and not onceki_calisti and not sonraki_calisti:
                    ihlaller.append(
                        Ihlal(
                            kural_kimlik=self.kimlik,
                            personel_id=personel_id,
                            tarih=gun,
                            ceza=1,
                            aciklama="Izole (tek gunluk) calisma bloku",
                        )
                    )
                elif not bugun_calisti and onceki_calisti and sonraki_calisti:
                    ihlaller.append(
                        Ihlal(
                            kural_kimlik=self.kimlik,
                            personel_id=personel_id,
                            tarih=gun,
                            ceza=1,
                            aciklama="Izole (tek gunluk) izin",
                        )
                    )
                gun += timedelta(days=1)
        return ihlaller


@kayitli("S8")
class S8DegisimMinimizasyonu(EsnekHedef):
    """Yeniden cozumde onceki cizelgeden sapan her atama (yalniz baglam.onceki_atamalar doluysa)."""

    def dogrula(self, atamalar: list[AtamaKaydi], baglam: Baglam) -> list[Ihlal]:
        if baglam.onceki_atamalar is None:
            return []
        yeni = {(a.personel_id, a.tarih, a.vardiya_tipi_id, a.nokta_id) for a in atamalar}
        onceki = {
            (a.personel_id, a.tarih, a.vardiya_tipi_id, a.nokta_id) for a in baglam.onceki_atamalar
        }
        degisenler = yeni ^ onceki
        return [
            Ihlal(
                kural_kimlik=self.kimlik,
                personel_id=personel_id,
                tarih=tarih,
                ceza=1,
                aciklama=f"Onceki cizelgeden sapma: vardiya={vardiya_tipi_id}, nokta={nokta_id}",
            )
            for personel_id, tarih, vardiya_tipi_id, nokta_id in sorted(
                degisenler, key=lambda k: (k[0], k[1])
            )
        ]


def _donem_gun_sayisi(baglam: Baglam) -> float:
    if baglam.donem_baslangic is not None and baglam.donem_bitis is not None:
        return (baglam.donem_bitis - baglam.donem_baslangic).days + 1
    return 7.0  # donem bilgisi yoksa (testlerde) haftalik hedefi degistirmeyen notr deger


def _bilinen_aralik(atamalar: list[AtamaKaydi], baglam: Baglam) -> tuple[date, date] | None:
    if baglam.donem_baslangic is not None and baglam.donem_bitis is not None:
        return baglam.donem_baslangic, baglam.donem_bitis
    tarihler = [a.tarih for a in atamalar]
    if not tarihler:
        return None
    return min(tarihler), max(tarihler)


def _adalet_sapmasi_ihlalleri(
    *,
    kural_kimlik: str,
    atamalar: list[AtamaKaydi],
    baglam: Baglam,
    atama_uygun_mu: Callable[[AtamaKaydi], bool],
    talep_uygun_mu: Callable[[tuple[date, int, int]], bool],
    aciklama: str,
) -> list[Ihlal]:
    """S2 ve S3'un ortak formulasyonu: sapma[p] = max(sayi-taban, tavan-sayi, 0)."""
    if not baglam.personel:
        return []

    toplam_talep = sum(
        gereken for anahtar, gereken in baglam.talep.items() if talep_uygun_mu(anahtar)
    )
    hedef = toplam_talep / len(baglam.personel)
    taban, tavan = floor(hedef), ceil(hedef)

    sayilar: dict[int, int] = defaultdict(int)
    for a in atamalar:
        if baglam.donem_icinde(a.tarih) and atama_uygun_mu(a):
            sayilar[a.personel_id] += 1

    ihlaller: list[Ihlal] = []
    for personel_id in baglam.personel:
        sayi = sayilar.get(personel_id, 0)
        sapma = max(sayi - taban, tavan - sayi, 0)
        if sapma > 0:
            ihlaller.append(
                Ihlal(
                    kural_kimlik=kural_kimlik,
                    personel_id=personel_id,
                    ceza=sapma,
                    aciklama=f"{aciklama} (sayi={sayi}, hedef≈{hedef:.1f})",
                )
            )
    return ihlaller


__all__ = [
    "S1TalepKarsilama",
    "S2GeceAdaleti",
    "S3HaftaSonuAdaleti",
    "S4ToplamSaatDengesi",
    "S5TercihKarsilama",
    "S6VardiyaDeseniTutarliligi",
    "S7IzoleGun",
    "S8DegisimMinimizasyonu",
]
