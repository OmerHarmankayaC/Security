"""SDD 5.5: manuel duzenleme dogrulamasi ve kaydetme (SRS TD-16).

DUZENLEME BIR OTURUMDUR, islem dizisi degil. Degisiklikler istemcide
birikir; sunucu iki uc nokta sunar ve ikisi de AYNI kural uygulamasindan
beslenir (FR-6.6):

  dogrula()  aday cizelgeyi BELLEKTE kurar, kurallari degerlendirir,
             hicbir sey yazmaz - "kaydedilmezse degisiklik olmaz"in
             uygulama karsiligi budur.
  kaydet()   tek islemde: kilitle, durumu ve damgayi dogrula, yeniden
             degerlendir, uygula, sapmalari tazele, yeni damga yaz.

DEGERLENDIRME BIRIKENIN TAMAMI UZERINDEN YAPILIR. Tek tek gecerli olan iki
degisiklik birlikte bir kurali bozabilir: iki ayri gune yapilan uzatma,
ayri ayri haftalik tavani asmazken birlikte asar. Bu yuzden istek son
degisikligi degil oturumun tamamini tasir ve degerlendirme DONEM GENELI
atamalar uzerinde kosar - eski surumdeki "degisen gunun +-7 gunu"
penceresi tek bir degisiklik varsayimina dayaniyordu ve birden fazla
degisiklikte yanlis kume uretirdi.

Zorunlu kurallar yalnizca degisiklik SONRASI durumda degerlendirilir
(kabul/red karari icin bu yeterlidir); esnek hedefler ONCESI ve SONRASI
iki kez degerlendirilip farki raporlanir - boylece degisiklikten bagimsiz
sabit sapmalar farkta iptal olur.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.kurallar.baglam import AtamaKaydi
from app.kurallar.kayit_defteri import kurallari_yukle
from app.kurallar.temel import Ihlal
from app.models.kural import KuralTipi
from app.models.sonuc import Atama, AtamaKaynagi, CizelgeSurumu, CizelgeSurumuDurumu
from app.repositories.kural import KuralDeposu
from app.repositories.sonuc import AtamaDeposu, CizelgeSurumuDeposu, DonemDeposu
from app.services.atama_donusumu import atama_kayitlarina_cevir
from app.services.baglam_kurucu import baglam_olustur
from app.services.talep_sapmasi import sapmalari_yenile


class SurumTaslakDegilError(Exception):
    """FR-7.3/TD-8: yayinlanmis (veya arsiv) bir surumun dogrudan duzenlenmesi
    engellenir. TD-8'e gore yalnizca 'yayinlandi' salt okunurdur - 'taslak' ve
    'cozuldu' ikisi de duzenlenebilir (bir cozum isi bitince surum otomatik
    'cozuldu' olur; kullanici bunun uzerinde elle degisiklik yapabilmelidir)."""


class DamgaCakismasiError(Exception):
    """SRS TD-16: surum, kullanici duzenlemeye basladigindan beri degismis.

    Baska bir oturum ayni surumu kaydetmis demektir. Sessizce uzerine yazmak
    onun isini iz birakmadan yok ederdi; kayit reddedilir ve kullaniciya
    durum bildirilir.
    """


class ZorunluIhlalError(Exception):
    """Kaydetme aninda zorunlu kisit ihlali bulundu (SDD 5.5.1).

    Istemcinin "gecerliydi" bilgisine guvenilmez: arada kural parametresi
    degismis, musaitlik kaydi girilmis olabilir. Dogrulama kaydetme aninda
    TEKRARLANIR ve ihlal varsa hicbir sey yazilmaz.
    """

    def __init__(self, ihlaller: list[Ihlal]) -> None:
        super().__init__("Zorunlu kisit ihlali")
        self.ihlaller = ihlaller


_DUZENLENEBILIR_DURUMLAR = (CizelgeSurumuDurumu.TASLAK, CizelgeSurumuDurumu.COZULDU)


@dataclass(frozen=True, slots=True)
class AtamaDegisikligi:
    """Tek bir gunun blogunu tanimlar (SDD 6.3.3).

    Blok katalogu kalktigi icin degisiklik bir vardiya TIPI secmez;
    baslangic ve bitis SAATINI verir. `baslangic_saati` bos birakildiginda
    o gunun blogu KALDIRILIR.

    Bitis saati baslangictan kucuk ya da esitse blok gece yarisini asar ve
    ertesi gune tasar - `zaman_araligi` modulundeki sozlesmenin aynisi.
    """

    personel_id: int
    tarih: date
    baslangic_saati: time | None = None
    bitis_saati: time | None = None
    nokta_id: int | None = None

    @property
    def blok(self) -> tuple[datetime, datetime] | None:
        if self.baslangic_saati is None or self.bitis_saati is None or self.nokta_id is None:
            return None
        baslangic = datetime.combine(self.tarih, self.baslangic_saati)
        bitis = datetime.combine(self.tarih, self.bitis_saati)
        if self.bitis_saati <= self.baslangic_saati:
            bitis += timedelta(days=1)
        return baslangic, bitis


@dataclass(frozen=True, slots=True)
class CezaKalemi:
    """Tek bir esnek hedefin ceza degisimi (FR-4.8'in manuel duzenleme karsiligi).

    Neden kural bazinda: `ceza_degisimi` tek bir sayiydi ve iki ayri bicimde
    yaniltiyordu. Birincisi HAM (agirliksiz) toplamdi - kapsama acigi
    (w1=10000) ile vardiya deseni degisimi (w6=4) ekranda ayni buyuklukte
    gorunuyordu. Ikincisi FARKLI BIRIMLERI topluyordu: S1 kisi, S2/S3
    vardiya, S4 saat, S6/S7 gun. Ikisinin toplami boyutsuz bir sayidir ve
    NFR-6'nin istedigi "neden bu cizelge" aciklamasini veremez.
    """

    kural_kimlik: str
    ad: str
    ham_fark: float
    agirlik: float
    agirlikli_fark: float


@dataclass(frozen=True, slots=True)
class DogrulamaSonucu:
    kabul_edilebilir: bool
    zorunlu_ihlaller: list[Ihlal] = field(default_factory=list)
    # Ham (agirliksiz) toplam. Geriye donuk uyumluluk icin korunuyor;
    # kullaniciya gosterilmesi gereken deger `agirlikli_ceza_degisimi`.
    ceza_degisimi: float = 0.0
    agirlikli_ceza_degisimi: float = 0.0
    # Yalniz DEGISEN kurallar. Degismeyenleri listelemek, kullaniciyi
    # sifirlar arasinda degisen tek satiri aramaya zorlardi.
    ceza_dokumu: list[CezaKalemi] = field(default_factory=list)
    # Degisikligin YENI DOGURDUGU, bir yere isaret eden esnek bulgular:
    # "Vardiya Sefligi bugun acikta kaldi", "Guvenlik'e talepten fazla kisi".
    # Toplam/agregat bulgular (S2, S3, S4) buraya girmez - onlarin yeri
    # ceza_dokumu'ndeki sayidir, cunku bir gune ya da noktaya isaret etmezler.
    uyarilar: list[Ihlal] = field(default_factory=list)


class DogrulamaServisi:
    def __init__(self, oturum: Session) -> None:
        self.oturum = oturum
        self.surum = CizelgeSurumuDeposu(oturum)
        self.donem = DonemDeposu(oturum)
        self.kural = KuralDeposu(oturum)
        self.atama = AtamaDeposu(oturum)

    def dogrula(
        self, surum_id: int, degisiklikler: Iterable[AtamaDegisikligi]
    ) -> DogrulamaSonucu | None:
        """Aday cizelgeyi BELLEKTE kurar ve degerlendirir; HICBIR SEY YAZMAZ.

        Surum bulunamazsa None doner (404); duzenlenebilir durumda degilse
        (yayinlandi/arsiv) SurumTaslakDegilError firlatir (409).
        """
        surum = self.surum.getir(surum_id)
        if surum is None:
            return None
        self._duzenlenebilir_mi(surum)
        return self._degerlendir(surum_id, surum.donem_id, list(degisiklikler))

    def _duzenlenebilir_mi(self, surum: CizelgeSurumu) -> None:
        """FR-6.9: yayinlanmis surum salt okunurdur.

        Kontrol YORDAMIN ICINDE durur, yalnizca uc noktada degil: arayuzun
        duzenleme araclarini gizlemesi tek basina yeterli degildir, cunku
        istek dogrudan da gonderilebilir (SDD 5.5.2).
        """
        if surum.durum not in _DUZENLENEBILIR_DURUMLAR:
            raise SurumTaslakDegilError(
                f"Surum {surum.surum_id} duzenlenebilir durumda degil (durum={surum.durum})"
            )

    def _degerlendir(
        self, surum_id: int, donem_id: int, degisiklikler: list[AtamaDegisikligi]
    ) -> DogrulamaSonucu:
        donem = self.donem.getir(donem_id)
        # yalniz_aktif=False: dogrulama var olan bir taslak uzerinde calisir;
        # o taslaktaki atamalarin tanimlari sonradan pasiflestirilmis olabilir.
        baglam = baglam_olustur(self.oturum, donem, yalniz_aktif=False)
        kurallar = kurallari_yukle(self.kural.aktif_kurallari_getir())

        # DONEM GENELI. Eski surum degisen gunun +-7 gunluk penceresini
        # kullaniyordu; o kisayol TEK degisiklik varsayimina dayaniyordu ve
        # birden fazla degisiklikte kurallarin gorecegi kume yanlis cikardi.
        once = atama_kayitlarina_cevir(self.atama.surume_gore_getir(surum_id))
        sonra = _degisiklikleri_uygula(once, degisiklikler)

        zorunlu_ihlaller: list[Ihlal] = []
        dokum: list[CezaKalemi] = []
        uyarilar: list[Ihlal] = []
        ham_toplam = 0.0
        agirlikli_toplam = 0.0

        for kural in kurallar:
            if kural.tip == KuralTipi.ZORUNLU:
                zorunlu_ihlaller.extend(kural.dogrula(sonra, baglam))
                continue

            oncekiler = kural.dogrula(once, baglam)
            sonrakiler = kural.dogrula(sonra, baglam)
            uyarilar.extend(_yeni_bulgular(oncekiler, sonrakiler))

            fark = _ceza_toplami(sonrakiler) - _ceza_toplami(oncekiler)
            ham_toplam += fark
            agirlik = float(kural.agirlik or 0)
            agirlikli_toplam += fark * agirlik
            if fark:
                dokum.append(
                    CezaKalemi(
                        kural_kimlik=kural.kimlik,
                        ad=kural.ad or kural.kimlik,
                        ham_fark=fark,
                        agirlik=agirlik,
                        agirlikli_fark=fark * agirlik,
                    )
                )

        # En pahali degisim once: kullanicinin once gormesi gereken sey, en
        # cok agirlik tasiyan kalem.
        dokum.sort(key=lambda k: -abs(k.agirlikli_fark))
        return DogrulamaSonucu(
            kabul_edilebilir=not zorunlu_ihlaller,
            zorunlu_ihlaller=zorunlu_ihlaller,
            ceza_degisimi=ham_toplam,
            agirlikli_ceza_degisimi=agirlikli_toplam,
            ceza_dokumu=dokum,
            uyarilar=uyarilar,
        )

    def kaydet(
        self, surum_id: int, degisiklikler: Iterable[AtamaDegisikligi], damga: str
    ) -> tuple[DogrulamaSonucu, str] | None:
        """Oturumun tamamini TEK ISLEMDE yazar (SDD 5.5.1).

        Kismi kayit YOKTUR: degisikliklerin bir kisminin yazilip bir kisminin
        yazilamamasi, kullanicinin ekranda gordugu ile veritabanindaki durumun
        ayrismasi demektir.

        Sirasiyla: satiri kilitle, durumu dogrula, damgayi dogrula, YENIDEN
        degerlendir, uygula, sapmalari tazele, yeni damga yaz. Doner deger
        (sonuc, yeni damga); surum yoksa None.
        """
        bekleyenler = list(degisiklikler)
        # SELECT ... FOR UPDATE: iki oturum ayni anda kaydetmeye kalkarsa
        # ikincisi birincinin islemi bitene kadar bekler ve damgayi
        # GUNCELLENMIS haliyle okur. Kilitsiz okumada ikisi de eski damgayi
        # dogru bulur ve ikinci kayit birincisini sessizce ezerdi.
        surum = self.surum.kilitle(surum_id)
        if surum is None:
            return None
        self._duzenlenebilir_mi(surum)
        if surum.damga != damga:
            raise DamgaCakismasiError(
                "Surum, duzenleme baslandigindan beri degisti; degisiklikler kaydedilmedi"
            )

        # DOGRULAMA KAYDETME ANINDA TEKRARLANIR. Istemcinin "gecerliydi"
        # bilgisine guvenilmez; arada kural parametresi degismis, musaitlik
        # kaydi girilmis olabilir.
        sonuc = self._degerlendir(surum_id, surum.donem_id, bekleyenler)
        if sonuc.zorunlu_ihlaller:
            raise ZorunluIhlalError(sonuc.zorunlu_ihlaller)

        for degisiklik in bekleyenler:
            self._blogu_yaz(surum_id, degisiklik)

        # Atamalar yazildiktan SONRA: sapma tablolari bu surumun yeni haline
        # gore bastan hesaplanir. `flush` sart - yenileme atamalari
        # veritabanindan okur.
        self.oturum.flush()
        sapmalari_yenile(self.oturum, surum_id)
        surum.damga = str(uuid4())
        return sonuc, surum.damga

    def _blogu_yaz(self, surum_id: int, degisiklik: AtamaDegisikligi) -> None:
        """O gunun blogunu YERINE KOYAR.

        GUNDE TEK BLOK BURADA GARANTI EDILIR. Eski benzersizlik kisiti
        `(surum_id, personel_id, tarih)` idi ve ikinci blogu veritabani
        duruyordu; yeni anahtar baslangic ZAMANINI tasidigi icin ayni gunde
        farkli saatte baslayan ikinci bir blogu yakalamaz (SDD 4.2.1). O gunun
        butun bloklari once silinip yerine tek blok yazilir - yol yapisal
        olarak ikinci bir blok birakmaz.
        """
        for mevcut in self.atama.gune_gore_getir(
            surum_id, degisiklik.personel_id, degisiklik.tarih
        ):
            self.oturum.delete(mevcut)
        # SILME once BOSALTILIR. SQLAlchemy'nin is birimi ayni tablo icin
        # INSERT'leri DELETE'lerden once gonderir; ayni saatte baslayan bir
        # blogun yerine yenisini yazmak benzersizlik kisitina takilirdi.
        self.oturum.flush()
        blok = degisiklik.blok
        if blok is None:
            return
        baslangic, bitis = blok
        self.oturum.add(
            Atama(
                surum_id=surum_id,
                personel_id=degisiklik.personel_id,
                baslangic_zamani=baslangic,
                bitis_zamani=bitis,
                nokta_id=degisiklik.nokta_id,
                kaynak=AtamaKaynagi.MANUEL,
            )
        )
        self.oturum.flush()

    def kilit_ayarla(
        self, surum_id: int, personel_id: int, tarih: date, kilitli: bool
    ) -> Atama | None:
        """FR-6.5: bir atamayi kilitler/kilidini acar.

        Kural dogrulamasi gerektirmez - kilit atamanin kendisini degistirmez,
        yalnizca yeniden cozumde (Gun 11, S8) sabitlenip sabitlenmeyecegini
        belirler. Surum ya da atama bulunamazsa None doner (404); surum
        taslak/cozuldu disindaysa SurumTaslakDegilError firlatir (409).
        """
        surum = self.surum.getir(surum_id)
        if surum is None:
            return None
        if surum.durum not in _DUZENLENEBILIR_DURUMLAR:
            raise SurumTaslakDegilError(
                f"Surum {surum.surum_id} kilitlenebilir durumda degil (durum={surum.durum})"
            )
        bloklar = self.atama.gune_gore_getir(surum_id, personel_id, tarih)
        if not bloklar:
            return None
        for atama in bloklar:
            atama.kilitli = kilitli
        return bloklar[0]


def _ceza_toplami(ihlaller: Sequence[Ihlal]) -> float:
    return sum(i.ceza or 0.0 for i in ihlaller)


def _yeni_bulgular(once: Sequence[Ihlal], sonra: Sequence[Ihlal]) -> list[Ihlal]:
    """Degisikligin YENI DOGURDUGU, bir yere isaret eden esnek bulgular.

    Once/sonra farki alinir; degisiklikten bagimsiz olarak zaten var olan
    bulgular listelenmez. Aksi halde tek bir hucreyi degistiren kullaniciya,
    donemin her yerindeki mevcut acikların listesi cikardi ve kendi
    degisikliginin ne yaptigi o yiginin icinde kaybolurdu.

    `tarih` tasimayan bulgular DISARIDA kalir: S2/S3/S4 donem geneli birer
    toplam uretir (bkz. `_adalet_sapmasi_ihlalleri`), bir gune ya da noktaya
    isaret etmezler. Onlarin dogru temsili ceza dokumundeki sayidir; metin
    olarak listelenmeleri "nerede" sorusuna yanit vermeyen bir satir olurdu.
    """
    onceki_metinler = {(i.kural_kimlik, i.aciklama) for i in once}
    return [
        i
        for i in sonra
        if i.tarih is not None and (i.kural_kimlik, i.aciklama) not in onceki_metinler
    ]


def _degisiklikleri_uygula(
    atamalar: list[AtamaKaydi], degisiklikler: Sequence[AtamaDegisikligi]
) -> list[AtamaKaydi]:
    """Biriken degisikliklerin TAMAMINI sirayla uygular.

    Her degisiklik o (personel, gun) hucresinin blogunu YERINE KOYAR: ayni
    gunun butun bloklari once dusurulur, boylece aday kume "gunde tek blok"
    varsayimini yapisal olarak tasir (H1). Filtre blogun BASLADIGI gune bakar
    (TD-1) - gece yarisini asip bugune tasan dunku blok, dunun blogudur ve el
    degmeden kalir.

    SIRA ONEMLIDIR: ayni hucre birden cok kez duzenlenmis olabilir (once
    olustur, sonra uzat) ve son soz sonuncunundur. Blogu baska bir personele
    TASIMAK iki degisiklik demektir - kaynaktan kaldirma ve hedefe yazma - ve
    ikisi de bu listede durur.
    """
    kalanlar = list(atamalar)
    for degisiklik in degisiklikler:
        kalanlar = [
            a
            for a in kalanlar
            if not (a.personel_id == degisiklik.personel_id and a.tarih == degisiklik.tarih)
        ]
        blok = degisiklik.blok
        if blok is not None:
            baslangic, bitis = blok
            kalanlar.append(
                AtamaKaydi(
                    personel_id=degisiklik.personel_id,
                    baslangic=baslangic,
                    bitis=bitis,
                    nokta_id=degisiklik.nokta_id,
                )
            )
    return kalanlar


__all__ = [
    "AtamaDegisikligi",
    "DamgaCakismasiError",
    "CezaKalemi",
    "DogrulamaServisi",
    "DogrulamaSonucu",
    "SurumTaslakDegilError",
    "ZorunluIhlalError",
]
