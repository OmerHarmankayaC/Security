"""Analiz uc noktasinin yanit semasi (SDD 3.2: analiz_router; SDD 5.7, Ek B;
SRS FR-8.x)."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class KisiSayisiOku(BaseModel):
    """Kisi basina bir metrigin degeri.

    `sayi`nin BIRIMI OLCUYE GORE DEGISIR ve cagrildigi yerde yazilidir: gece
    ve hafta sonu dagilimlarinda SAAT (SRS S2/S3; blok sureleri cozumun
    ciktisi oldugundan sayima dayali bir olcu tanimsizdir), bina degisim
    sayacinda ADET.
    """

    personel_id: int
    ad_soyad: str
    sayi: float
    # KISIYE DUSEN ADIL PAY (SRS S2/S3) — olcunun referansi. Havuz ortalamasi
    # DEGIL: erisilebilirligi kisitli bir havuz tek ortalamaya vuruldugunda
    # kalici olarak sapmali gorunur ve olcu ayirt edici olmaktan cikar. Adalet
    # grafigi referans cizgisini bu degerden ceker.
    #
    # Payi olmayan olculer icin (bina degisim sayaci) None kalir: orada
    # "adil pay" diye bir kavram yok ve sifir yazmak yanlis bir hedef gosterir.
    pay: float | None = None


class SaatDengesiOku(BaseModel):
    personel_id: int
    ad_soyad: str
    toplam_saat: float
    hedef_saat: float
    sapma: float


class FazlaKadroKalemi(BaseModel):
    """Talepten fazla kadro yazilmis bir hucre; ADLARIYLA birlikte.

    Analiz ekrani ve disa aktarma kimlik degil ad gosterir (NFR-5); adlari
    burada cozmek, her tuketicinin ayri ayri eslestirme yapmasini onler.
    """

    # ZAMAN DAMGASI (B-23): aralik gun sinirini kendisi tasir.
    baslangic_zamani: datetime
    bitis_zamani: datetime
    nokta_id: int
    nokta_ad: str
    fazla_sayi: int


class KotaDurumuOku(BaseModel):
    """H10: kisi basina yillik fazla calisma ve KALAN kota.

    Kartin amaci listeyi degil RISKI gostermek (SDD 6.3.4): sirali gelir,
    kotasi tukenmeye yakin olan ustte.

    DEVIR AYRI ALANDIR. Kalan kota YILIN tamamindan hesaplanir, fazla_calisma_saat
    ise yalniz BU DONEMIN fazlasidir. Ikisi ayrilmadiginda kartta "fazla calisma
    0,0 sa - kalan kota 5,0 sa" gibi kendi icinde celiskili okunan bir satir
    cikiyordu: tuketimin nereden geldigi ancak devir yazildiginda gorunur.
    """

    personel_id: int
    ad_soyad: str
    #: Yilin onceki bolumunden devreden fazla calisma (personel kaydindan).
    devir_saat: float = 0.0
    #: YALNIZ bu donemde esigi asan saat.
    fazla_calisma_saat: float
    kalan_kota_saat: float


class CezaKalemiOku(BaseModel):
    """Bir esnek hedefin UC AYRI sayisi (SDD 6.3.4).

    Ham deger kuralin kendi biriminde olculur (kisi-saat, saat, gun);
    agirlikli ceza amac fonksiyonuna girendir. Ikisinin tek sutunda
    gosterilmesi, toplamin satirlarin toplami olmadigi bir tablo uretir.

    `ad` kimlikle degil ADLA listelenir: "S4" tek basina kimseye bir sey
    soylemez.
    """

    kimlik: str
    ad: str
    ham_deger: float
    agirlik: float
    agirlikli_ceza: float


class GunlukKapsamaOku(BaseModel):
    """Bir gunun kapsama acigi (SDD 6.3.1, Ozet ekrani gunluk seridi).

    Toplami AnalizOku.karsilanmayan_kisi_saat'e ESITTIR ve bu bir testtir:
    aralik sayisi ile kisi-saat bu projede bir kez karistirildi ve disa
    aktarma basliginda yanlis sayi basildi."""

    tarih: date
    acik_aralik_sayisi: int
    karsilanmayan_kisi_saat: int


class KumulatifDegisimOku(BaseModel):
    """Kisi basina sapmanin ONCEKI yayinlanmis doneme gore degisimi.

    Kumulatif adaletin vaadi sapmanin kucuk olmasi degil, ZAMANLA
    kucuulmesidir (Charter 5, K3). Onceki yayinlanmis donem yoksa alanlar
    None kalir ve ekran "karsilastirilacak donem yok" der - sifir yazmak
    "degisim olmadi" anlamina gelirdi.
    """

    onceki_surum_id: int | None = None
    onceki_ortalama_sapma: float | None = None
    simdiki_ortalama_sapma: float | None = None

    @property
    def azaliyor_mu(self) -> bool | None:
        if self.onceki_ortalama_sapma is None or self.simdiki_ortalama_sapma is None:
            return None
        return self.simdiki_ortalama_sapma < self.onceki_ortalama_sapma


class AnalizOku(BaseModel):
    surum_id: int
    # TANIMSIZ olabilir: talep yoksa oran hesaplanamaz ve arayuz tire
    # gosterir. Sifir bolme yerine yuzde yuz varsaymak, bos bir donemi
    # kusursuz bir cizelge gibi gosterirdi (SDD 5.7).
    kapsama_orani: float | None
    # Kapsama oranindan AYRI tutulur: oran "talebin ne kadari karsilandi"
    # sorusunu yanitlar, fazla kadro o soruya bir sey eklemez.
    fazla_kadro: list[FazlaKadroKalemi] = Field(default_factory=list)
    toplam_fazla_kadro: int = 0
    # Birim SAAT (SRS S2, S3).
    kisi_basina_gece: list[KisiSayisiOku]
    kisi_basina_hafta_sonu: list[KisiSayisiOku]
    saat_dagilimi: list[SaatDengesiOku]
    en_dengesiz_personel_id: int | None
    en_dengesiz_ad_soyad: str | None
    tercih_karsilama_orani: float | None
    bina_degisim_sayisi: list[KisiSayisiOku]
    ceza_dokumu: dict[str, float] | None
    toplam_ceza: float | None
    # Dokumun KAYNAGI (Gorev 5): "cozucu" (is dokumu taze), "kurallardan"
    # (cozucusuz ya da bayat surumde kural motorundan hesaplandi) ya da
    # "yok" (ne is dokumu var ne de hesaplanan bir ihlal). Ekran dipnotu
    # bu deger uzerinden konusur - kaynak yazilmadan bir sayinin nereden
    # geldigi kullaniciya gorunmez.
    ceza_kaynagi: str = "yok"
    # ARALIK SAYISI ile KISI-SAAT AYRI OLCULERDIR (SDD 6.3.4). Ardisik
    # saatler tek kayitta birlestigi icin satir sayisi yuku anlatmaz; ikisi
    # karistirildi ve disa aktarma basliginda yanlis sayi gosterildi.
    karsilanmayan_kisi_saat: int = 0
    acik_aralik_sayisi: int = 0
    # Gunluk kirilim (Gorev 6, SDD 6.3.1 Ozet ekrani seridi): donemin HER
    # gunu icin bir kayit, acigi olmayan gunler de sifirla. Toplami
    # karsilanmayan_kisi_saat'e esittir.
    gunluk_kapsama: list[GunlukKapsamaOku] = Field(default_factory=list)
    kota_durumu: list[KotaDurumuOku] = Field(default_factory=list)
    #: H10'un yillik fazla calisma kotasi (saat). Kart kalan kotayi neye gore
    #: soyledigini yazabilsin diye gonderilir; ekranin sabit 270 tasimasi,
    #: kural parametresi degistiginde sessizce yanlis olurdu.
    yillik_kota_saat: float = 270.0
    ceza_kalemleri: list[CezaKalemiOku] = Field(default_factory=list)
    kumulatif_degisim: KumulatifDegisimOku = Field(default_factory=KumulatifDegisimOku)
    # Hangi ufkun olculdugu (SDD 6.3.4 ufuk anahtari): "donem" | "adalet".
    ufuk: str = "donem"
