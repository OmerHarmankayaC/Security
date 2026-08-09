"""Surum ve yayin yonetimi servisi (SDD 3.2 izlenebilirlik matrisi: FR-7.x ->
SurumServisi; SDD 6.3.5 Surumler ekrani).

Iki is yapar:
  - Surum listesini ekranin istedigi ozet bilgilerle zenginlestirir
    (numara, durum, olusturma zamani, toplam ceza, kapsama acigi sayisi).
  - Iki surumu karsilastirip farkli atamalari listeler (SDD 6.3.5
    "Karsilastir Butonu"; Proje Tanim Dokumani bolum 5'in altinci kabul
    kriteri "yeniden cozumde degisen atama sayisi raporlanir").
"""

from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.sonuc import Atama, CizelgeSurumu, CizelgeSurumuDurumu
from app.repositories.sonuc import (
    AtamaDeposu,
    CizelgeSurumuDeposu,
    CozumIsiDeposu,
    KapsamaAcigiDeposu,
)
from app.repositories.tanim import GorevNoktasiDeposu, PersonelDeposu, VardiyaTipiDeposu
from app.schemas.surum import (
    AtamaFarkiOku,
    SurumKarsilastirmaOku,
    SurumOzetiOku,
)

# Taslak olarak kopyalanabilecek durumlar. Taslak ve cozuldu disarida: onlar
# zaten duzenlenebilir, kopyalamak kullaniciya bir sey kazandirmaz ve ayni
# donemde amacsiz kopyalar biriktirir.
_KOPYALANABILIR_DURUMLAR = (CizelgeSurumuDurumu.ARSIV, CizelgeSurumuDurumu.YAYINLANDI)


class SurumlerAyniDonemdeDegilError(Exception):
    """Farkli donemlerin surumleri karsilastirilamaz: atamalar farkli takvim
    gunlerine dustugu icin "degisen gun" diye bir sey tanimlanamaz
    (router 409'a cevirir)."""


class KopyalanamazSurumDurumuError(Exception):
    """Kaynak surum kopyalanabilir bir durumda degil (router 409'a cevirir)."""


@dataclass(frozen=True, slots=True)
class _AtamaOzeti:
    vardiya_tipi_id: int
    nokta_id: int


class SurumServisi:
    def __init__(self, oturum: Session) -> None:
        self.oturum = oturum
        self.surum = CizelgeSurumuDeposu(oturum)
        self.atama = AtamaDeposu(oturum)
        self.cozum_isi = CozumIsiDeposu(oturum)
        self.kapsama = KapsamaAcigiDeposu(oturum)
        self.personel = PersonelDeposu(oturum)
        self.vardiya_tipi = VardiyaTipiDeposu(oturum)
        self.nokta = GorevNoktasiDeposu(oturum)

    # --- Surum listesi (SDD 6.3.5) ------------------------------------------

    def listele(self, *, donem_id: int | None = None) -> list[SurumOzetiOku]:
        surumler: Sequence[CizelgeSurumu] = self.surum.listele(donem_id=donem_id)
        surum_idleri = [s.surum_id for s in surumler]
        cezalar = self.cozum_isi.surumlere_gore_en_son_ceza(surum_idleri)
        eksikler = self.kapsama.surumlere_gore_eksik_toplami(surum_idleri)
        return [
            SurumOzetiOku(
                surum_id=s.surum_id,
                donem_id=s.donem_id,
                surum_no=s.surum_no,
                durum=s.durum,
                onceki_surum_id=s.onceki_surum_id,
                yayin_zamani=s.yayin_zamani,
                olusturma_zamani=s.olusturma_zamani,
                guncelleme_zamani=s.guncelleme_zamani,
                toplam_ceza=cezalar.get(s.surum_id),
                kapsama_acigi_sayisi=eksikler.get(s.surum_id, 0),
            )
            for s in surumler
        ]

    # --- Arsivden taslak kopyalama (madde 8) --------------------------------

    def taslak_olarak_kopyala(self, kaynak_surum_id: int) -> CizelgeSurumu | None:
        """Arsivlenmis bir surumden ATAMALARIYLA BIRLIKTE yeni taslak turetir.

        Kaynak kayda DOKUNULMAZ. Arsiv kaydinin durumunu taslaga cevirmek iki
        seyi birden bozardi ve ikisi de arsivin degismezligine dayanir:
        calisan panelindeki karsilastirma tabani (ayni donemdeki en son arsiv,
        FR-9.4) ve Surumler ekranindaki iki surum karsilastirmasi (SDD 6.3.5).
        Geriye donuk degistirilen bir arsiv, yayinlanmis cizelgede "degisen
        gunler" isaretini sessizce yanlislastirir.

        Yeni taslak `onceki_surum_id` ile kaynagi gosterir. Bu alan zaten
        "bu surumun turetildigi surum" demek (SDD 4.2.4); yeniden cozmede
        "yeniden cozulen surum", burada "kopyalanan arsiv" anlamina gelir.
        Ayni iliski oldugu icin ikinci bir sutun eklenmedi.

        Atamalar `taslak_turet`in aksine KOPYALANIR: orada yeni surumun
        atamalarini cozucu yazacaktir, burada ise kullanicinin istedigi sey
        kaynagin cizelgesinin aynisidir.

        Kopyalama TEK islemde tamamlanir. Yarim kopyalanmis bir taslak, kural
        ihlali icermeyen ama kapsamasi eksik bir cizelgeden ayirt edilemez ve
        yaniltir (SDD 5.4'te atamalarin yazilmasi icin verilen ayni gerekce).

        Ayni donemde acik taslak bulunmasi engel DEGILDIR: her cozum
        baslatma zaten yeni bir taslak aciyor (CozumServisi.baslat), yani
        coklu taslak sistemin olagan hali; TD-8 de bir sinir koymuyor.
        """
        kaynak = self.surum.getir(kaynak_surum_id)
        if kaynak is None:
            return None
        if kaynak.durum not in _KOPYALANABILIR_DURUMLAR:
            raise KopyalanamazSurumDurumuError(
                f"Sürüm {kaynak.surum_no} {kaynak.durum.value} durumunda; "
                "yalnızca yayınlanmış veya arşivlenmiş bir sürüm taslak olarak kopyalanabilir."
            )

        yeni = self.surum.olustur(
            donem_id=kaynak.donem_id,
            surum_no=self.surum.donem_icin_sonraki_surum_no(kaynak.donem_id),
            durum=CizelgeSurumuDurumu.TASLAK,
            onceki_surum_id=kaynak.surum_id,
        )
        self.oturum.flush()

        for a in self.atama.surume_gore_getir(kaynak_surum_id):
            self.atama.olustur(
                surum_id=yeni.surum_id,
                personel_id=a.personel_id,
                tarih=a.tarih,
                vardiya_tipi_id=a.vardiya_tipi_id,
                nokta_id=a.nokta_id,
                # Kilit, kopyada TASINIR: kullanicinin "bu atama degismesin"
                # karari kaynaga degil o atamaya aittir ve kopyanin yeniden
                # cozulmesinde de gecerlidir.
                kilitli=a.kilitli,
                # Kaynak da korunur; atamayi cozucunun mu kullanicinin mi
                # yazdigi bilgisi kopyalamayla degismez (NFR-13).
                kaynak=a.kaynak,
            )

        # Kapsama acigi KOPYALANMAZ: o, bir cozum calistirmasinin ciktisidir
        # (SDD 4.2.4, S1'in eksik degiskenlerinin karsiligi) ve henuz
        # cozulmemis bir taslaga ait degildir. Kopya cozuldugunde kendi
        # aciklari yazilir.
        self.oturum.flush()
        return yeni

    # --- Karsilastirma (SDD 6.3.5; Charter bolum 5, altinci kriter) ---------

    def karsilastir(self, onceki_surum_id: int, yeni_surum_id: int) -> SurumKarsilastirmaOku | None:
        """Iki surum arasindaki farkli atamalari (personel, tarih) ekseninde
        listeler.

        Fark uc turde ayrisir - FR-9.4'un calisan panelinde kullandigi ayni
        siniflandirma, burada yonetici tarafinda:
          eklendi    : gun yalniz YENI surumde atanmis
          kaldirildi : gun yalniz ONCEKI surumde atanmis
          degisti    : ikisinde de var, vardiya tipi veya gorev noktasi farkli

        Karsilastirma tabani cagiran tarafindan verilir (Surumler ekraninda
        kullanicinin sectigi iki surum); calisan panelindeki "en son arsiv"
        secimi oraya ozgudur ve buraya karistirilmaz.
        """
        onceki = self.surum.getir(onceki_surum_id)
        yeni = self.surum.getir(yeni_surum_id)
        if onceki is None or yeni is None:
            return None
        if onceki.donem_id != yeni.donem_id:
            raise SurumlerAyniDonemdeDegilError(
                "Karsilastirilan iki surum ayni planlama donemine ait olmalidir"
            )

        onceki_atamalar = self._ozetle(self.atama.surume_gore_getir(onceki_surum_id))
        yeni_atamalar = self._ozetle(self.atama.surume_gore_getir(yeni_surum_id))

        personel_adlari = {p.personel_id: p.ad_soyad for p in self.personel.tumunu_getir()}
        vardiya_adlari = {v.vardiya_tipi_id: v.ad for v in self.vardiya_tipi.tumunu_getir()}
        nokta_adlari = {n.nokta_id: n.ad for n in self.nokta.tumunu_getir()}

        farklar: list[AtamaFarkiOku] = []
        tum_anahtarlar = sorted(
            set(onceki_atamalar) | set(yeni_atamalar), key=lambda a: (a[1], a[0])
        )
        for anahtar in tum_anahtarlar:
            personel_id, tarih = anahtar
            a = onceki_atamalar.get(anahtar)
            b = yeni_atamalar.get(anahtar)
            if a == b:
                continue
            if a is None:
                tur = "eklendi"
            elif b is None:
                tur = "kaldirildi"
            else:
                tur = "degisti"
            farklar.append(
                AtamaFarkiOku(
                    personel_id=personel_id,
                    ad_soyad=personel_adlari.get(personel_id, f"#{personel_id}"),
                    tarih=tarih,
                    tur=tur,
                    onceki_vardiya_tipi_ad=(
                        None if a is None else vardiya_adlari.get(a.vardiya_tipi_id)
                    ),
                    onceki_nokta_ad=None if a is None else nokta_adlari.get(a.nokta_id),
                    yeni_vardiya_tipi_ad=(
                        None if b is None else vardiya_adlari.get(b.vardiya_tipi_id)
                    ),
                    yeni_nokta_ad=None if b is None else nokta_adlari.get(b.nokta_id),
                )
            )

        return SurumKarsilastirmaOku(
            onceki_surum_id=onceki_surum_id,
            yeni_surum_id=yeni_surum_id,
            onceki_surum_no=onceki.surum_no,
            yeni_surum_no=yeni.surum_no,
            eklenen=sum(1 for f in farklar if f.tur == "eklendi"),
            kaldirilan=sum(1 for f in farklar if f.tur == "kaldirildi"),
            degisen=sum(1 for f in farklar if f.tur == "degisti"),
            toplam_degisiklik=len(farklar),
            farklar=farklar,
        )

    @staticmethod
    def _ozetle(atamalar: Sequence[Atama]) -> dict[tuple[int, object], _AtamaOzeti]:
        """(personel_id, tarih) -> atamanin karsilastirmaya giren alanlari.

        Atama tablosunda (surum_id, personel_id, tarih) benzersizdir
        (SDD 4.2.4), dolayisiyla bu anahtar tekildir."""
        return {
            (a.personel_id, a.tarih): _AtamaOzeti(a.vardiya_tipi_id, a.nokta_id) for a in atamalar
        }
