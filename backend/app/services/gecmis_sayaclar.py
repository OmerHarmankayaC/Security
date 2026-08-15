"""Donem oncesi birikim — TEK KAYNAK (SDD 5.9, SRS TD-6).

Dort tuketici ayni servisi cagirir: cozucu (S2, S3, S4 ve H10 icin), on
kontrol, analiz servisi ve kabul olcum betigi. Besinci bir hesap yeri
acilmaz; bu projede ayni hesabin iki yerde durmasinin bedeli birkac kez
odendi.

BIRIKIM TURETILIR, SAKLANMAZ. Kaynak yayinlanmis surumlerin atamalaridir;
ayri bir sayac tablosu yok. Saklanan sayac, bir donem yeniden cozuldugunde
veya bir surum arsive alindiginda bayatlar ve gecersiz kilma mantigi hesabin
kendisinden karmasik olur. Tek istisna personel kaydindaki devir bakiyesidir
ve o da turetilen degerin YERINE GECMEZ, ona eklenir (bkz. `yasal_devir`).

ONBELLEK KURULMAZ. Doksan gunluk pencerede otuz personel icin yaklasik uc
bin blok okunur; olcek bunu gerektirmiyor.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.kurallar.gecmis import GecmisYuk, PersonelSayaci
from app.kurallar.yardimcilar import takvim_haftalari
from app.kurallar.zaman_araligi import gece_saat_sayisi
from app.models.girdi import Musaitlik, MusaitlikDilimi
from app.models.sonuc import Atama, CizelgeSurumu, CizelgeSurumuDurumu, Donem
from app.models.tanim import Personel

# SRS TD-6: adalet ufkunun varsayilani.
ADALET_UFKU_GUN = 90


@dataclass(frozen=True, slots=True)
class _GecmisAtama:
    """Pencereye giren bir blok — sayaca ve paya AYNI kayittan girer."""

    personel_id: int
    nokta_id: int
    gun: date
    sure_saat: float
    gece_saat: float


class GecmisSayaclar:
    def __init__(self, oturum: Session) -> None:
        self.oturum = oturum

    # --- Genel giris -------------------------------------------------------

    def hesapla(
        self,
        donem: Donem,
        ufuk_gun: int = ADALET_UFKU_GUN,
        *,
        erisebilen: dict[int, frozenset[int]] | None = None,
    ) -> GecmisYuk:
        """Donemin BASLANGICINDAN geriye `ufuk_gun` gunluk pencere.

        `erisebilen` verildiginde gecmis atamalarin adil paya katkisi da
        hesaplanir: her blogun saati, blogun noktasina BUGUN erisebilenler
        arasinda bolunur. Erisilebilirligin bugunku tanimdan alinmasi
        bilincli bir yaklasikliktir (SRS TD-6) - gecmiste kimin nerede
        calisabildigi kayit altinda degil ve tarihce tutmanin kazandiracagi
        kesinlik maliyetini karsilamaz.
        """
        pencere_bit = donem.baslangic_tarihi
        pencere_bas = pencere_bit - timedelta(days=ufuk_gun)
        atamalar = self._pencere_atamalari(pencere_bas, pencere_bit)

        sayaclar = self._sayaclari_topla(atamalar)
        paylar = self._paylari_topla(atamalar, erisebilen or {})
        return GecmisYuk(
            ufuk_gun=ufuk_gun,
            pencere_bas=pencere_bas,
            pencere_bit=pencere_bit,
            sayaclar=sayaclar,
            pay_gece=paylar["gece"],
            pay_hafta_sonu=paylar["hafta_sonu"],
            pay_toplam=paylar["toplam"],
            calisabilir_oran=self._calisabilir_oranlar(pencere_bas, pencere_bit, ufuk_gun),
        )

    # --- Okuma -------------------------------------------------------------

    def son_yayinlanan_surumler(self, pencere_bas: date, pencere_bit: date) -> list[int]:
        """Pencereye degen her donem icin EN SON YAYINLANAN surumun kimligi.

        Arsivlenmis ve taslak surumler sayilmaz: biri gecmisi iki kez sayar
        (ayni donemin hem arsivi hem yayini), digeri henuz gerceklesmemis bir
        cizelgeyi gecmise yazar.
        """
        satirlar = self.oturum.execute(
            select(CizelgeSurumu.surum_id, CizelgeSurumu.donem_id, CizelgeSurumu.surum_no)
            .join(Donem, Donem.donem_id == CizelgeSurumu.donem_id)
            .where(
                CizelgeSurumu.durum == CizelgeSurumuDurumu.YAYINLANDI,
                Donem.baslangic_tarihi < pencere_bit,
                Donem.bitis_tarihi >= pencere_bas,
            )
            .order_by(CizelgeSurumu.donem_id, CizelgeSurumu.surum_no.desc())
        ).all()
        sonuc: dict[int, int] = {}
        for surum_id, donem_id, _surum_no in satirlar:
            # Siralama surum_no'ya gore azalan; her donemin ILK gordugumuz
            # satiri en son yayinlanandir.
            sonuc.setdefault(donem_id, surum_id)
        return list(sonuc.values())

    def _pencere_atamalari(self, pencere_bas: date, pencere_bit: date) -> list[_GecmisAtama]:
        surum_idler = self.son_yayinlanan_surumler(pencere_bas, pencere_bit)
        if not surum_idler:
            return []
        atamalar = (
            self.oturum.execute(select(Atama).where(Atama.surum_id.in_(surum_idler)))
            .scalars()
            .all()
        )
        sonuc: list[_GecmisAtama] = []
        for a in atamalar:
            # BLOK BASLADIGI GUNE YAZILIR (TD-1). Ufuk bir donemin ortasina
            # dustugunde filtre bu gune bakar; gece yarisini asan blogun
            # tamami baslangic gunune sayilir.
            gun = a.baslangic_zamani.date()
            if not (pencere_bas <= gun < pencere_bit):
                continue
            sure = (a.bitis_zamani - a.baslangic_zamani).total_seconds() / 3600
            sonuc.append(
                _GecmisAtama(
                    personel_id=a.personel_id,
                    nokta_id=a.nokta_id,
                    gun=gun,
                    sure_saat=sure,
                    gece_saat=float(
                        gece_saat_sayisi(a.baslangic_zamani.time(), a.bitis_zamani.time())
                    ),
                )
            )
        return sonuc

    # --- Toplama -----------------------------------------------------------

    @staticmethod
    def _sayaclari_topla(atamalar: list[_GecmisAtama]) -> dict[int, PersonelSayaci]:
        toplam: dict[int, float] = defaultdict(float)
        gece: dict[int, float] = defaultdict(float)
        hafta_sonu: dict[int, float] = defaultdict(float)
        for a in atamalar:
            toplam[a.personel_id] += a.sure_saat
            gece[a.personel_id] += a.gece_saat
            if a.gun.weekday() >= 5:
                hafta_sonu[a.personel_id] += a.sure_saat
        return {
            p: PersonelSayaci(
                toplam_saat=toplam[p],
                gece_saat=gece[p],
                hafta_sonu_saat=hafta_sonu[p],
                # Fazla calisma ADALET ufkunda anlamsizdir: haftalik esigin
                # asilmasi yasal ufkun olcusudur ve ayri cagrilir
                # (`yasal_devir`). Burada sifir kalir ki iki ufuk sessizce
                # birbirinin yerine gecmesin.
                fazla_calisma_saat=0.0,
            )
            for p in toplam
        }

    @staticmethod
    def _paylari_topla(
        atamalar: list[_GecmisAtama], erisebilen: dict[int, frozenset[int]]
    ) -> dict[str, dict[int, float]]:
        """Gecmis yukun ADIL PAYA katkisi.

        Her blogun saati, noktasina erisebilenler arasinda esit bolunur -
        donem ici talebin bolunmesiyle AYNI islem. Ikisi ayni islemden
        gecmezse yuk ile hedef farkli birimlerde olculur ve sapma anlamini
        kaybeder.
        """
        pay_gece: dict[int, float] = defaultdict(float)
        pay_hafta_sonu: dict[int, float] = defaultdict(float)
        pay_toplam: dict[int, float] = defaultdict(float)
        for a in atamalar:
            havuz = erisebilen.get(a.nokta_id)
            if not havuz:
                continue
            for p in havuz:
                pay_toplam[p] += a.sure_saat / len(havuz)
                pay_gece[p] += a.gece_saat / len(havuz)
                if a.gun.weekday() >= 5:
                    pay_hafta_sonu[p] += a.sure_saat / len(havuz)
        return {
            "gece": dict(pay_gece),
            "hafta_sonu": dict(pay_hafta_sonu),
            "toplam": dict(pay_toplam),
        }

    # --- Calisabilirlik orani (SRS TD-6) -----------------------------------

    def _calisabilir_oranlar(
        self, pencere_bas: date, pencere_bit: date, ufuk_gun: int
    ) -> dict[int, float]:
        """`ufuk icinde calisabilir gun / ufuk gun sayisi`.

        Ufkun tamaminda calisabilir olmayan personel — arada ise baslamis,
        uzun izne ayrilmis, aktifligi sona ermis — tam payla
        karsilastirilirsa KALICI olarak hedefin altinda gorunur ve sapmasi
        hicbir cizelgeyle kapatilamaz. Bu, ayni hatanin ucuncu bicimidir;
        ilk ikisi bu projede yasandi (bkz. `Baglam.adil_paylar`).

        Yalniz TAM GUN kapsayan musaitlik kayitlari gunu dusurur: yarim gun
        izinli personel o gun calisabilir durumdadir.
        """
        if ufuk_gun <= 0:
            return {}
        personeller = self.oturum.execute(select(Personel)).scalars().all()
        kapali = self._tam_gun_kapali_gunler(pencere_bas, pencere_bit)

        oranlar: dict[int, float] = {}
        for p in personeller:
            bas = max(p.aktif_baslangic, pencere_bas)
            bit = min(p.aktif_bitis or pencere_bit, pencere_bit)
            gun_sayisi = 0
            gun = bas
            while gun < bit:
                if gun not in kapali.get(p.personel_id, frozenset()):
                    gun_sayisi += 1
                gun += timedelta(days=1)
            oranlar[p.personel_id] = min(gun_sayisi / ufuk_gun, 1.0)
        return oranlar

    def _tam_gun_kapali_gunler(
        self, pencere_bas: date, pencere_bit: date
    ) -> dict[int, frozenset[date]]:
        kayitlar = (
            self.oturum.execute(
                select(Musaitlik).where(
                    Musaitlik.dilim == MusaitlikDilimi.TAM_GUN,
                    Musaitlik.baslangic_tarihi < pencere_bit,
                    Musaitlik.bitis_tarihi >= pencere_bas,
                )
            )
            .scalars()
            .all()
        )
        toplayici: dict[int, set[date]] = defaultdict(set)
        for k in kayitlar:
            gun = max(k.baslangic_tarihi, pencere_bas)
            son = min(k.bitis_tarihi, pencere_bit - timedelta(days=1))
            while gun <= son:
                toplayici[k.personel_id].add(gun)
                gun += timedelta(days=1)
        return {p: frozenset(gunler) for p, gunler in toplayici.items()}

    # --- Yasal ufuk (SRS TD-6, H10) ---------------------------------------

    def yasal_devir(self, donem: Donem, esik: float) -> dict[int, float]:
        """H10'un `devir[p]`si: KOTA YILI ICI turetilen fazla calisma + kayit alani.

        Yasal ufuk adalet ufkundan AYRIDIR ve ayni fonksiyondan gecmez;
        `hesapla` ile tek cagrida birlestirilseydi hangi kuralin hangi ufku
        kullandigi cagri yerine bakilmadan anlasilmazdi (SRS TD-14 ile ayni
        gerekce).

        Iki parca TOPLANIR, biri digerinin yerine gecmez: turetilen deger
        sistemin gordugu yayinlanmis surumlerden gelir, kayit alani ise
        sistemin kota yilinin basindan beri her seyi bilmedigi durumu
        karsilar (SRS TD-6).

        Fazla calisma TAKVIM HAFTASI basina olculur (TD-14): haftalik toplamin
        esigi astigi kadari. Kayan pencerede olculseydi ayni saat yedi ayri
        pencereye girer ve kota gercekte asilmadan asilmis gorunurdu.
        """
        personeller = self.oturum.execute(select(Personel)).scalars().all()

        # PENCERE BASINA BIR KEZ HESAPLANIR. Onceki surumde bu cagri personel
        # dongusunun icindeydi ve ayni agir sorgu kisi sayisi kadar
        # kosuyordu; tam takim on dakikadan yirmi bes dakikaya cikti.
        # Kota yili kisiye gore degisebildigi icin onbellek yil_bas ANAHTARLI.
        onbellek: dict[date, dict[int, float]] = {}

        sonuc: dict[int, float] = {}
        for p in personeller:
            yil = p.kota_yili or donem.baslangic_tarihi.year
            yil_bas = date(yil, 1, 1)
            turetilen = 0.0
            if yil_bas < donem.baslangic_tarihi:
                if yil_bas not in onbellek:
                    onbellek[yil_bas] = self._turetilen_fazla_calisma(
                        yil_bas, donem.baslangic_tarihi, esik
                    )
                turetilen = onbellek[yil_bas].get(p.personel_id, 0.0)
            sonuc[p.personel_id] = turetilen + float(p.devir_fazla_calisma_saat)
        return sonuc

    def _turetilen_fazla_calisma(
        self, pencere_bas: date, pencere_bit: date, esik: float
    ) -> dict[int, float]:
        atamalar = self._pencere_atamalari(pencere_bas, pencere_bit)
        gunluk: dict[int, dict[date, float]] = defaultdict(lambda: defaultdict(float))
        for a in atamalar:
            gunluk[a.personel_id][a.gun] += a.sure_saat

        sonuc: dict[int, float] = {}
        for personel_id, gunler in gunluk.items():
            toplam = 0.0
            for hafta in takvim_haftalari(gunler).values():
                # YARIM HAFTALAR DA SAYILIR. Pencerenin ilk ve son takvim
                # haftasi kismen disarida kalabilir; disarida kalan gunlerin
                # saati zaten `gunler`de yok, dolayisiyla haftalik toplam
                # eksik ve esigi asma ihtimali dusuk olur. Haftayi tumden
                # atmak ise gercekten yapilmis fazla calismayi yok sayardi.
                toplam += max(sum(gunler[g] for g in hafta) - esik, 0.0)
            sonuc[personel_id] = toplam
        return sonuc
