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
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.kurallar.baglam import AtamaKaydi, Baglam
from app.services.kadro_hesaplari import kisi_basina_azami_haftalik_vardiya


class BulguTipi(enum.StrEnum):
    DONEM_KAPASITESI_YETERSIZ = "donem_kapasitesi_yetersiz"
    YETKINLIK_HAVUZU_YETERSIZ = "yetkinlik_havuzu_yetersiz"
    GUNLUK_PERSONEL_YETERSIZ = "gunluk_personel_yetersiz"
    NOKTA_ICIN_UYGUN_PERSONEL_YOK = "nokta_icin_uygun_personel_yok"
    # Yapilandirma bulgusu: veri yeterli olabilir ama kural katalogu cozumu
    # anlamsizlastiracak bicimde ayarlanmis.
    KAPSAMA_KURALI_PASIF = "kapsama_kurali_pasif"


@dataclass(frozen=True, slots=True, kw_only=True)
class Bulgu:
    tip: BulguTipi
    aciklama: str
    eksik: int | None = None
    yetkinlik_id: int | None = None
    tarih: date | None = None
    vardiya_tipi_id: int | None = None
    nokta_id: int | None = None
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


def on_kontrol_yap(
    baglam: Baglam,
    donem_gunleri: list[date],
    *,
    azami_haftalik_saat: Decimal,
    haftalik_asgari_izin_gunu: int,
    aktif_kural_kimlikleri: frozenset[str] = frozenset({"S1"}),
) -> list[Bulgu]:
    """aktif_kural_kimlikleri varsayilani S1'i iceren kume: bu fonksiyonun
    kural katalogundan haberi olmayan cagiranlari (kadro aritmetigini elle
    kuran testler) yapilandirma uyarisi almaz."""
    kural_bulgusu = kapsama_kurali_bulgusu(aktif_kural_kimlikleri)
    if not donem_gunleri:
        return [kural_bulgusu] if kural_bulgusu else []

    azami_vardiya_donem = _azami_vardiya_donem(
        baglam,
        donem_gunleri,
        azami_haftalik_saat=azami_haftalik_saat,
        haftalik_asgari_izin_gunu=haftalik_asgari_izin_gunu,
    )
    musait_gun_by_personel = {
        p: sum(1 for g in donem_gunleri if baglam.gunde_musait_mi(p, g)) for p in baglam.personel
    }

    # Yapilandirma bulgusu once yazilir: kullanici listeye baktiginda once
    # "kapsama kurali kapali" gorsun, sonra kapsamaya dair sayilari.
    bulgular: list[Bulgu] = [kural_bulgusu] if kural_bulgusu else []
    bulgular.extend(
        _donem_kapasitesi_kontrolu(
            baglam, donem_gunleri, azami_vardiya_donem, musait_gun_by_personel
        )
    )
    bulgular.extend(
        _yetkinlik_havuzu_kontrolu(
            baglam, donem_gunleri, azami_vardiya_donem, musait_gun_by_personel
        )
    )
    bulgular.extend(_gunluk_musaitlik_kontrolu(baglam, donem_gunleri))
    bulgular.extend(_nokta_musaitlik_kontrolu(baglam, donem_gunleri))
    return bulgular


def _azami_vardiya_donem(
    baglam: Baglam,
    donem_gunleri: list[date],
    *,
    azami_haftalik_saat: Decimal,
    haftalik_asgari_izin_gunu: int,
) -> int:
    """azami_vardiya_sayisi(donem) (SDD 5.2): kisi basina azami haftalik vardiyanin
    donem uzunluguna (hafta cinsinden) olceklenmis hali."""
    toplam_vardiya = 0
    toplam_saat = 0.0
    for g in donem_gunleri:
        for v in baglam.vardiya_tipleri:
            for n in baglam.gorev_noktalari:
                gereken = baglam.gereken_sayi(g, v, n)
                if gereken == 0:
                    continue
                toplam_vardiya += gereken
                toplam_saat += gereken * baglam.sure_saat(v)
    ortalama_sure = toplam_saat / toplam_vardiya if toplam_vardiya > 0 else 0.0
    kisi_basina_hafta = kisi_basina_azami_haftalik_vardiya(
        ortalama_sure,
        azami_haftalik_saat=azami_haftalik_saat,
        haftalik_asgari_izin_gunu=haftalik_asgari_izin_gunu,
    )
    donem_hafta_sayisi = Decimal(len(donem_gunleri)) / 7
    return int(Decimal(kisi_basina_hafta) * donem_hafta_sayisi)


def _donem_kapasitesi_kontrolu(
    baglam: Baglam,
    donem_gunleri: list[date],
    azami_vardiya_donem: int,
    musait_gun_by_personel: dict[int, int],
) -> list[Bulgu]:
    """1. Donem geneli kapasite."""
    toplam_talep = sum(
        baglam.gereken_sayi(g, v, n)
        for g in donem_gunleri
        for v in baglam.vardiya_tipleri
        for n in baglam.gorev_noktalari
    )
    azami_kapasite = sum(
        min(musait_gun, azami_vardiya_donem) for musait_gun in musait_gun_by_personel.values()
    )

    if azami_kapasite < toplam_talep:
        eksik = toplam_talep - azami_kapasite
        return [
            Bulgu(
                tip=BulguTipi.DONEM_KAPASITESI_YETERSIZ,
                eksik=eksik,
                aciklama=f"Dönem genelinde {eksik} vardiyalık kapasite açığı var",
            )
        ]
    return []


def _yetkinlik_havuzu_kontrolu(
    baglam: Baglam,
    donem_gunleri: list[date],
    azami_vardiya_donem: int,
    musait_gun_by_personel: dict[int, int],
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
        y_talep = sum(
            baglam.gereken_sayi(g, v, n_id)
            for g in donem_gunleri
            for v in baglam.vardiya_tipleri
            for n_id, nokta in baglam.gorev_noktalari.items()
            if nokta.onkosul_yetkinlik_id == y
        )
        y_kapasite = sum(
            min(musait_gun_by_personel[p_id], azami_vardiya_donem)
            for p_id, p in baglam.personel.items()
            if y in p.yetkinlikler
        )
        if y_kapasite < y_talep:
            eksik = y_talep - y_kapasite
            bulgular.append(
                Bulgu(
                    tip=BulguTipi.YETKINLIK_HAVUZU_YETERSIZ,
                    yetkinlik_id=y,
                    eksik=eksik,
                    aciklama=(
                        f"{baglam.yetkinlik_adi(y)} yetkinlik havuzunda "
                        f"{eksik} vardiyalık açık var"
                    ),
                )
            )
    return bulgular


def _gunluk_musaitlik_kontrolu(baglam: Baglam, donem_gunleri: list[date]) -> list[Bulgu]:
    """3. Gun bazli musaitlik."""
    bulgular: list[Bulgu] = []
    for g in donem_gunleri:
        gun_talep = sum(
            baglam.gereken_sayi(g, v, n)
            for v in baglam.vardiya_tipleri
            for n in baglam.gorev_noktalari
        )
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
    """4. Nokta bazli musaitlik (yetkinlik dahil)."""
    bulgular: list[Bulgu] = []
    for g in donem_gunleri:
        for v in baglam.vardiya_tipleri:
            for n_id, nokta in baglam.gorev_noktalari.items():
                talep = baglam.gereken_sayi(g, v, n_id)
                if talep == 0:
                    continue
                uygun = sum(
                    1
                    for p in baglam.personel
                    if baglam.musait_mi(AtamaKaydi(p, g, v, n_id))
                    and (
                        nokta.onkosul_yetkinlik_id is None
                        or baglam.yetkin_mi(p, nokta.onkosul_yetkinlik_id)
                    )
                )
                if uygun < talep:
                    bulgular.append(
                        Bulgu(
                            tip=BulguTipi.NOKTA_ICIN_UYGUN_PERSONEL_YOK,
                            tarih=g,
                            vardiya_tipi_id=v,
                            nokta_id=n_id,
                            aciklama=(
                                f"{g} günü {baglam.vardiya_adi(v)} bloğunda "
                                f"{baglam.nokta_adi(n_id)} için uygun personel yok"
                            ),
                        )
                    )
    return bulgular
