"""SDD 5.2 FONKSIYON on_kontrol()'un birebir uygulamasi.

Cozucu calistirilmadan once yapisal engelleri aritmetik olarak, saniyeler
icinde tespit eder. Bu kontroller gerek sarttir, yeter sart degildir:
hepsinin gecmesi cizelgenin cozulebilecegini garanti etmez (dinlenme
suresi ve ardisiklik gibi zaman yapisina bagli kisitlar bu aritmetikle
yakalanamaz); herhangi birinin basarisiz olmasi ise cozumun kesinlikle
acik verecegini gosterir. Bulgu bir uyari degil, kesin bir teshistir;
bulgusuzluk yalnizca bilinen engellerin bulunmadigi anlamina gelir.
"""

import enum
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import ROUND_CEILING, Decimal

from app.kurallar.baglam import Baglam
from app.kurallar.zaman_araligi import saat_metni
from app.services.kadro_hesaplari import surdurulebilir_haftalik_saat


class BulguTipi(enum.StrEnum):
    DONEM_KAPASITESI_YETERSIZ = "donem_kapasitesi_yetersiz"
    YETKINLIK_HAVUZU_YETERSIZ = "yetkinlik_havuzu_yetersiz"
    GUNLUK_PERSONEL_YETERSIZ = "gunluk_personel_yetersiz"
    NOKTA_ICIN_UYGUN_PERSONEL_YOK = "nokta_icin_uygun_personel_yok"
    # Yapilandirma bulgusu: veri yeterli olabilir ama kural katalogu cozumu
    # anlamsizlastiracak bicimde ayarlanmis.
    KAPSAMA_KURALI_PASIF = "kapsama_kurali_pasif"
    # Kota bulgulari (SDD 5.2, Tur 4). Ikisi de BULGUDUR, ENGEL DEGIL (K18):
    # cozum yine calisir.
    DEVIR_KOTAYI_ASMIS = "devir_kotayi_asmis"
    KOTASI_DOLMUS_PERSONEL = "kotasi_dolmus_personel"


@dataclass(frozen=True, slots=True, kw_only=True)
class Bulgu:
    tip: BulguTipi
    aciklama: str
    eksik: int | None = None
    yetkinlik_id: int | None = None
    tarih: date | None = None
    # Blok katalogu kalktigi icin bulgu bir vardiya TIPINI degil bir SAATI
    # gosterir (SRS TD-13): "su gun, su saatte, su noktada".
    saat: int | None = None
    nokta_id: int | None = None
    personel_id: int | None = None
    # KESIN BULGU MU, UYARI MI? (SDD 5.2, karar notu K18)
    #
    # Bu alan bir zamanlar "cozumu durdurur mu" demekti ve yapisal bir
    # bulguda cozum isi hic baslatilmiyordu. O davranis SRS FR-5.2'yi
    # dogrudan ihlal ediyordu ("personel yetersizliginde cozumu reddetmek
    # yerine cizelgeyi uret ve kapsama aciklarini goster") ve S1'in zorunlu
    # kisit yerine baskin agirlikli esnek hedef olarak tasarlanmasinin tek
    # gerekcesini islevsiz birakiyordu.
    #
    # ARTIK HICBIR BULGU ISI DUSURMEZ. Ayrim yalnizca OKUMA amaclidir:
    #   True  — kesin bulgu: "bu acik kesinlikle olusacak"; cikan acigin
    #           kadro yetersizliginden kaynaklandigini ONCEDEN dogrular.
    #   False — uyari: "sonucu su kosulla oku" (or. S1 pasif).
    kesin_mi: bool = True


def kesin_bulgular(bulgular: list[Bulgu]) -> list[Bulgu]:
    """Kesin bulgular; uyarilardan AYRI gosterilirler, isi DUSURMEZLER."""
    return [b for b in bulgular if b.kesin_mi]


def kapsama_kurali_bulgusu(aktif_kural_kimlikleri: frozenset[str]) -> Bulgu | None:
    """S1 pasifse uyari uretir.

    S1 modele UC sey birden ekler (bkz. S1TalepKarsilama.modele_ekle):
      1. Alt sinir  — atanan + eksik >= gereken, cezasiyla birlikte
      2. Ust sinir  — atanan <= gereken (SRS S1: "kadro, zorunlu")
      3. Kapsama acigi degiskenleri — raporlamanin okudugu kaynak

    Kural pasiflestirildiginde ucu birden kaybolur, ve sonuclari sessizdir:
      - Hicbir sey vardiyalarin doldurulmasini zorlamaz; bos ya da buyuk
        olcude bos bir cizelge gecerli sayilir.
      - Bir noktaya talebin uzerinde personel atanabilir.
      - Kapsama acigi kaydi hic uretilmez; Analiz ve Cizelge ekranlari,
        talebin tamami karsilanmamisken "0 acik" gosterir.

    Ucuncusu bu uyarinin asil nedeni: ilk ikisi cizelgeye bakinca gorulur,
    ucuncusu sistemin kendi raporunu yanlislastirir.
    """
    if "S1" in aktif_kural_kimlikleri:
        return None
    return Bulgu(
        tip=BulguTipi.KAPSAMA_KURALI_PASIF,
        kesin_mi=False,
        aciklama=(
            "S1 (Talep karşılama) kuralı pasif. Talep kısıtı modele eklenmeyecek: "
            "hiçbir vardiyanın doldurulması zorunlu olmayacak ve sonuç boş ya da büyük "
            "ölçüde boş bir çizelge olabilir. Bir noktaya talebin üzerinde personel de "
            "atanabilir. Ayrıca kapsama açığı hiç hesaplanmaz — açık kalan talep, "
            'Analiz ve Çizelge ekranlarında "0 açık" olarak görünür. '
            "Çözümü başlatmadan önce Tanımlar → Kural sekmesinden S1'i etkinleştirin."
        ),
    )


# Kalan kotanin "dolmus" sayilacagi esik: bir haftalik azami fazla calisma
# (mutlak tavan - fazla calisma esigi = 66 - 45). Sifir yerine bu deger
# secildi: bir saatlik kalan kota da pratikte kullanilamaz.
_HAFTALIK_AZAMI_FAZLA = Decimal(21)


def on_kontrol_yap(
    baglam: Baglam,
    donem_gunleri: list[date],
    *,
    fazla_calisma_esigi: Decimal,
    azami_gunluk_saat: Decimal,
    haftalik_asgari_izin_gunu: int,
    yillik_fazla_kotasi: Decimal = Decimal(270),
    aktif_kural_kimlikleri: frozenset[str] = frozenset({"S1"}),
) -> list[Bulgu]:
    """aktif_kural_kimlikleri varsayilani S1'i iceren kume: bu fonksiyonun
    kural katalogundan haberi olmayan cagiranlari (kadro aritmetigini elle
    kuran testler) yapilandirma uyarisi almaz."""
    kural_bulgusu = kapsama_kurali_bulgusu(aktif_kural_kimlikleri)
    if not donem_gunleri:
        return [kural_bulgusu] if kural_bulgusu else []

    azami_saat_donem = _kisi_basina_azami_saat(
        donem_gunleri,
        fazla_calisma_esigi=fazla_calisma_esigi,
        azami_gunluk_saat=azami_gunluk_saat,
        haftalik_asgari_izin_gunu=haftalik_asgari_izin_gunu,
    )
    musait_gun_by_personel = {
        p: sum(1 for g in donem_gunleri if baglam.gunde_musait_mi(p, g)) for p in baglam.personel
    }
    # Kisi basina kapasite SAAT cinsinden: musait gun sayisinin gunluk
    # tavanla carpimi ile surdurulebilir donem saatinin KUCUGU.
    kapasite_by_personel = {
        p: min(Decimal(musait_gun) * azami_gunluk_saat, azami_saat_donem)
        for p, musait_gun in musait_gun_by_personel.items()
    }

    # Yapilandirma bulgusu once yazilir: kullanici listeye baktiginda once
    # "kapsama kurali kapali" gorsun, sonra kapsamaya dair sayilari.
    bulgular: list[Bulgu] = [kural_bulgusu] if kural_bulgusu else []
    bulgular.extend(_donem_kapasitesi_kontrolu(baglam, donem_gunleri, kapasite_by_personel))
    bulgular.extend(_yetkinlik_havuzu_kontrolu(baglam, donem_gunleri, kapasite_by_personel))
    bulgular.extend(_gunluk_musaitlik_kontrolu(baglam, donem_gunleri))
    bulgular.extend(_nokta_musaitlik_kontrolu(baglam, donem_gunleri))
    bulgular.extend(
        _kota_kontrolu(
            baglam,
            fazla_calisma_esigi=fazla_calisma_esigi,
            yillik_fazla_kotasi=yillik_fazla_kotasi,
        )
    )
    return bulgular


def _kota_kontrolu(
    baglam: Baglam,
    *,
    fazla_calisma_esigi: Decimal,
    yillik_fazla_kotasi: Decimal,
) -> list[Bulgu]:
    """5. Yillik fazla calisma kotasi (SDD 5.2, H10).

    Iki ayri bulgu uretir ve ikisi de BULGUDUR, ENGEL DEGIL (K18):

    - **Devir kotayi asmis.** `devir[p] > yillik_fazla_kotasi` olan bir
      personel H10'u TEK BASINA cozulemez kilar - kisit
      `devir + Σ fazla <= kota` ve `fazla >= 0` oldugundan saglanamaz. Bu
      bir VERI HATASIDIR ve cozum aninda degil burada bildirilir (FR-5.1):
      cozucunun "model cozulemez" demesi kullaniciya hangi personelin
      hangi alaninin yanlis oldugunu soylemez.
    - **Kotasi dolmus personel.** Kalan kotasi bir haftalik fazla
      calismaya bile yetmeyen personel fazla calismaya atanamaz; kadro
      hesabi bunu bilmeden yapildiginda acigin NEDENI gorunmez kalir -
      kisi listede durur ama esigin uzerinde kullanilamaz.
    """
    bulgular: list[Bulgu] = []
    kota = float(yillik_fazla_kotasi)
    esik = float(fazla_calisma_esigi)
    for personel_id in sorted(baglam.personel):
        ad = baglam.personel_adi(personel_id)
        devir = Decimal(str(baglam.devir_fazla_calisma_saat(personel_id)))
        if devir > yillik_fazla_kotasi:
            bulgular.append(
                Bulgu(
                    tip=BulguTipi.DEVIR_KOTAYI_ASMIS,
                    personel_id=personel_id,
                    eksik=int((devir - yillik_fazla_kotasi).to_integral_value(ROUND_CEILING)),
                    aciklama=(
                        f"{ad} devir bakiyesi {float(devir):g} saat; yıllık kota "
                        f"{kota:g} saat. Veri hatası: bu personel için H10 "
                        f"hiçbir çizelgeyle sağlanamaz."
                    ),
                )
            )
            continue
        # "Dolmus" esigi: kalan kota, BIR HAFTALIK fazla calismaya
        # yetmiyorsa. Sifir yerine bu esik secildi cunku 1 saatlik kalan
        # kota da pratikte kullanilamaz ve kullaniciya "neredeyse dolu"
        # demek "dolu" demekten daha az yararli olurdu.
        kalan = yillik_fazla_kotasi - devir
        if kalan < _HAFTALIK_AZAMI_FAZLA:
            bulgular.append(
                Bulgu(
                    tip=BulguTipi.KOTASI_DOLMUS_PERSONEL,
                    personel_id=personel_id,
                    kesin_mi=False,
                    aciklama=(
                        f"{ad} kotasından {float(kalan):g} saat kaldı (eşik {esik:g} "
                        f"saat/hafta). Bu personel fazla çalışmaya atanamaz; kadro "
                        f"hesabında eşiğin üstü için sayılmamalı."
                    ),
                )
            )
    return bulgular


def _kisi_basina_azami_saat(
    donem_gunleri: list[date],
    *,
    fazla_calisma_esigi: Decimal,
    azami_gunluk_saat: Decimal,
    haftalik_asgari_izin_gunu: int,
) -> Decimal:
    """Bir personelin donem boyunca surdurulebilir bicimde calisabilecegi SAAT.

    Kapasite artik kisi-vardiya degil KISI-SAAT olarak olculur (SRS 3.3.6,
    FR-1.9): karisik uzunluklu katalogda vardiya sayisi katalogun bilesimine
    gore degisir ve ayni talep icin farkli kapasiteler uretir.
    """
    haftalik = surdurulebilir_haftalik_saat(
        fazla_calisma_esigi=fazla_calisma_esigi,
        azami_gunluk_saat=azami_gunluk_saat,
        haftalik_asgari_izin_gunu=haftalik_asgari_izin_gunu,
    )
    return haftalik * Decimal(len(donem_gunleri)) / 7


def _donem_kapasitesi_kontrolu(
    baglam: Baglam,
    donem_gunleri: list[date],
    kapasite_by_personel: dict[int, Decimal],
) -> list[Bulgu]:
    """1. Donem geneli kapasite — KISI-SAAT cinsinden."""
    toplam_talep = _talep_saati(baglam, donem_gunleri)
    azami_kapasite = sum(kapasite_by_personel.values(), Decimal(0))

    if azami_kapasite < toplam_talep:
        eksik = int((toplam_talep - azami_kapasite).to_integral_value(rounding=ROUND_CEILING))
        return [
            Bulgu(
                tip=BulguTipi.DONEM_KAPASITESI_YETERSIZ,
                eksik=eksik,
                aciklama=f"Dönem genelinde {eksik} kişi-saatlik kapasite açığı var",
            )
        ]
    return []


def _talep_saati(
    baglam: Baglam, donem_gunleri: list[date], *, nokta_idleri: set[int] | None = None
) -> Decimal:
    """Donemdeki toplam kisi-saat talebi (SAAT EKSENINDEN, dogrudan).

    Talep bir zaman araligidir ve saat eksenine bir kez acilir (SDD 5.3);
    kisi-saat, acilmis degerlerin toplamidir. Onceki hal blok gorunumunden
    `gereken × sure_saat` ile turetiyordu ve o turev karisik uzunluklu
    katalogda sessizce yanlisti.
    """
    gunler = set(donem_gunleri)
    return Decimal(
        sum(
            gereken
            for (tarih, _saat, nokta_id), gereken in baglam.talep_saat.items()
            if tarih in gunler and (nokta_idleri is None or nokta_id in nokta_idleri)
        )
    )


def _yetkinlik_havuzu_kontrolu(
    baglam: Baglam,
    donem_gunleri: list[date],
    kapasite_by_personel: dict[int, Decimal],
) -> list[Bulgu]:
    """2. Yetkinlik havuzu kapasitesi (SDD surum 1.2: bireysel izin de hesaba katilir,
    Kontrol 1'deki gibi kisi basina MIN(musait_gun, azami_vardiya_donem) toplanir).

    Not (SDD 5.2, surum 1.2): bu kontrol dahi dönem genelini topladigi icin,
    kucuk bir havuzun yalnizca belirli bir haftada yetersiz kalmasi (ör. eş
    zamanli iki haftalik izin) donemin geri kalanindaki serbestlikle sayisal
    olarak ortulup yakalanmayabilir - bilinçli bir sinir (Backlog B-14).
    """
    yetkinlikler = {
        n.onkosul_yetkinlik_id
        for n in baglam.gorev_noktalari.values()
        if n.onkosul_yetkinlik_id is not None
    }
    bulgular: list[Bulgu] = []
    for y in yetkinlikler:
        y_talep = _talep_saati(
            baglam,
            donem_gunleri,
            nokta_idleri={
                n_id
                for n_id, nokta in baglam.gorev_noktalari.items()
                if nokta.onkosul_yetkinlik_id == y
            },
        )
        y_kapasite = sum(
            (
                kapasite_by_personel[p_id]
                for p_id, p in baglam.personel.items()
                if y in p.yetkinlikler
            ),
            Decimal(0),
        )
        if y_kapasite < y_talep:
            eksik = int((y_talep - y_kapasite).to_integral_value(rounding=ROUND_CEILING))
            bulgular.append(
                Bulgu(
                    tip=BulguTipi.YETKINLIK_HAVUZU_YETERSIZ,
                    yetkinlik_id=y,
                    eksik=eksik,
                    aciklama=(
                        f"{baglam.yetkinlik_adi(y)} yetkinlik havuzunda "
                        f"{eksik} kişi-saatlik açık var"
                    ),
                )
            )
    return bulgular


def _gunluk_musaitlik_kontrolu(baglam: Baglam, donem_gunleri: list[date]) -> list[Bulgu]:
    """3. Gun bazli musaitlik."""
    bulgular: list[Bulgu] = []
    for g in donem_gunleri:
        # AYNI ANDA gereken en yuksek kisi sayisi: gun icindeki her saat
        # icin noktalarin gerekenleri toplanir, saatlerin en buyugu alinir.
        # Gun boyu toplam kisi-saat DEGIL - bir kisi gun icinde tek blok
        # calisir (TD-13) ve karsilastirilan sey o gun musait KISI sayisi.
        saat_toplamlari: dict[int, int] = defaultdict(int)
        for (tarih, saat, _nokta_id), gereken in baglam.talep_saat.items():
            if tarih == g:
                saat_toplamlari[saat] += gereken
        gun_talep = max(saat_toplamlari.values(), default=0)
        musait = sum(1 for p in baglam.personel if baglam.gunde_musait_mi(p, g))
        if musait < gun_talep:
            eksik = gun_talep - musait
            bulgular.append(
                Bulgu(
                    tip=BulguTipi.GUNLUK_PERSONEL_YETERSIZ,
                    tarih=g,
                    eksik=eksik,
                    aciklama=f"{g} günü {eksik} kişilik personel açığı var",
                )
            )
    return bulgular


def _nokta_musaitlik_kontrolu(baglam: Baglam, donem_gunleri: list[date]) -> list[Bulgu]:
    """4. Nokta bazli musaitlik — SAAT SAAT (yetkinlik dahil).

    Kontrol once blok basinaydi ve "blogun kapsadigi saatlerdeki en yuksek
    gereken" ile karsilastiriyordu; blok katalogu kalktigi icin dogrudan
    saatin kendisi sorulur. Karsilastirma saat basinadir cunku talep de
    saat basinadir: bir noktada saat 14.00'te dokuz kisi gerekiyorsa, o
    saatte musait ve yetkin dokuz kisi bulunmak zorundadir.

    Bulgu SAAT BASINA DEGIL, gun ve nokta basina EN DAR saat icin uretilir;
    yirmi dort satirlik bir liste kullaniciya hicbir sey anlatmaz (ayni
    gerekce kapsama acigi kayitlarinda da uygulandi).
    """
    bulgular: list[Bulgu] = []
    for g in donem_gunleri:
        for n_id, nokta in baglam.gorev_noktalari.items():
            en_dar: tuple[int, int, int] | None = None  # (eksik, saat, talep)
            for saat in range(24):
                talep = baglam.gereken_sayi_saat(g, saat, n_id)
                if talep == 0:
                    continue
                an = datetime.combine(g, time(saat))
                uygun = sum(
                    1
                    for p in baglam.personel
                    if baglam.musait_mi(p, an)
                    and (
                        nokta.onkosul_yetkinlik_id is None
                        or baglam.yetkin_mi(p, nokta.onkosul_yetkinlik_id)
                    )
                )
                if uygun < talep and (en_dar is None or talep - uygun > en_dar[0]):
                    en_dar = (talep - uygun, saat, talep)
            if en_dar is not None:
                eksik, saat, _talep = en_dar
                bulgular.append(
                    Bulgu(
                        tip=BulguTipi.NOKTA_ICIN_UYGUN_PERSONEL_YOK,
                        tarih=g,
                        saat=saat,
                        nokta_id=n_id,
                        eksik=eksik,
                        aciklama=(
                            f"{g} günü {saat_metni(time(saat))} saatinde "
                            f"{baglam.nokta_adi(n_id)} için {eksik} kişilik uygun "
                            "personel açığı var"
                        ),
                    )
                )
    return bulgular
