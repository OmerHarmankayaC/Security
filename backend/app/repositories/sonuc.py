"""Sonuc varliklari icin depo katmani (SDD 4.2.4)."""

from collections.abc import Sequence
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.sonuc import (
    Atama,
    CizelgeSurumu,
    CizelgeSurumuDurumu,
    CozumIsi,
    CozumIsiDurumu,
    Donem,
    FazlaKadro,
    KapsamaAcigi,
)
from app.repositories.taban import TabanDepo

# Kullanicinin hala ilgilendigi isler: yurumekte olanlar ve KARAR BEKLEYEN
# (SDD 5.4.1) is. Terminal durumlar (tamamlandi/uyarili/basarisiz/iptal)
# disaridadir.
AKTIF_DURUMLAR = (
    CozumIsiDurumu.KUYRUKTA,
    CozumIsiDurumu.ON_KONTROL,
    CozumIsiDurumu.COZULUYOR,
    CozumIsiDurumu.DURDURULDU,
)


class DonemDeposu(TabanDepo[Donem]):
    def __init__(self, oturum: Session) -> None:
        super().__init__(oturum, Donem)

    def guncel_donemi_bul(self, bugun: date) -> Donem | None:
        """Calisan Paneli (SDD 6.1): 'bugun' tarihini iceren donem; yoksa en
        yakin gelecek donem; o da yoksa en son gecmis donem."""
        icinde = (
            self.oturum.execute(
                select(Donem).where(Donem.baslangic_tarihi <= bugun, Donem.bitis_tarihi >= bugun)
            )
            .scalars()
            .first()
        )
        if icinde is not None:
            return icinde
        gelecek = (
            self.oturum.execute(
                select(Donem)
                .where(Donem.baslangic_tarihi > bugun)
                .order_by(Donem.baslangic_tarihi.asc())
            )
            .scalars()
            .first()
        )
        if gelecek is not None:
            return gelecek
        return (
            self.oturum.execute(
                select(Donem).where(Donem.bitis_tarihi < bugun).order_by(Donem.bitis_tarihi.desc())
            )
            .scalars()
            .first()
        )

    def tarihi_iceren_donemi_bul(self, tarih: date) -> Donem | None:
        stmt = select(Donem).where(Donem.baslangic_tarihi <= tarih, Donem.bitis_tarihi >= tarih)
        return self.oturum.execute(stmt).scalars().first()

    def tercihe_acik_donemi_bul(self, bugun: date) -> Donem | None:
        """Tercih bildirimine hala acik (tercih_son_tarihi >= bugun), baslangici
        en yakin donem (SDD 6.1: Tercihlerim'deki 'bildirim X'te kapanıyor' bandı)."""
        stmt = (
            select(Donem)
            .where(Donem.tercih_son_tarihi >= bugun)
            .order_by(Donem.baslangic_tarihi.asc())
        )
        return self.oturum.execute(stmt).scalars().first()


class CizelgeSurumuDeposu(TabanDepo[CizelgeSurumu]):
    def __init__(self, oturum: Session) -> None:
        super().__init__(oturum, CizelgeSurumu)

    def donem_icin_sonraki_surum_no(self, donem_id: int) -> int:
        stmt = select(func.max(CizelgeSurumu.surum_no)).where(CizelgeSurumu.donem_id == donem_id)
        mevcut_en_buyuk = self.oturum.execute(stmt).scalar_one_or_none()
        return (mevcut_en_buyuk or 0) + 1

    def listele(self, *, donem_id: int | None = None) -> Sequence[CizelgeSurumu]:
        stmt = select(CizelgeSurumu)
        if donem_id is not None:
            stmt = stmt.where(CizelgeSurumu.donem_id == donem_id)
        return self.oturum.execute(stmt.order_by(CizelgeSurumu.surum_no.desc())).scalars().all()

    def taslak_turet(self, onceki_surum_id: int) -> CizelgeSurumu | None:
        """SDD 5.6: yeni_surum <- SurumServisi.taslak_turet(onceki_surum_id).

        Onceki surumun atamalarini KOPYALAMAZ - yeni surumun atamalari
        cozucunun urettigi sonuctan yazilir (bkz. cozum_servisi.py); burada
        yalnizca donem_id/surum_no/onceki_surum_id baglantili yeni bir
        taslak satiri olusturulur.
        """
        onceki = self.getir(onceki_surum_id)
        if onceki is None:
            return None
        surum_no = self.donem_icin_sonraki_surum_no(onceki.donem_id)
        return self.olustur(
            donem_id=onceki.donem_id,
            surum_no=surum_no,
            durum=CizelgeSurumuDurumu.TASLAK,
            onceki_surum_id=onceki.surum_id,
        )

    def yayinla(self, surum_id: int) -> CizelgeSurumu | None:
        """TD-8: yayinlanan surum salt okunur olur; ayni donemde daha once
        yayinlanmis bir surum varsa arsiv durumuna gecer."""
        surum = self.getir(surum_id)
        if surum is None:
            return None
        onceki_yayinlar = self.oturum.execute(
            select(CizelgeSurumu).where(
                CizelgeSurumu.donem_id == surum.donem_id,
                CizelgeSurumu.durum == CizelgeSurumuDurumu.YAYINLANDI,
            )
        ).scalars()
        for onceki in onceki_yayinlar:
            onceki.durum = CizelgeSurumuDurumu.ARSIV
        surum.durum = CizelgeSurumuDurumu.YAYINLANDI
        surum.yayin_zamani = datetime.now(UTC)
        return surum

    def yayinlanan_getir(self, donem_id: int) -> CizelgeSurumu | None:
        """Calisan Paneli (FR-9.2): calisana yalniz YAYINLANDI durumundaki
        surum gosterilir; bir donemde en fazla bir tanesi bu durumda olabilir."""
        stmt = select(CizelgeSurumu).where(
            CizelgeSurumu.donem_id == donem_id,
            CizelgeSurumu.durum == CizelgeSurumuDurumu.YAYINLANDI,
        )
        return self.oturum.execute(stmt).scalars().first()

    def en_son_arsivlenen_getir(self, donem_id: int) -> CizelgeSurumu | None:
        """FR-9.4: 'degisen gunler' karsilastirma tabani - ayni donemde en son
        ARSIV durumuna gecmis surum (yayin_zamani'na gore en yenisi)."""
        stmt = (
            select(CizelgeSurumu)
            .where(
                CizelgeSurumu.donem_id == donem_id,
                CizelgeSurumu.durum == CizelgeSurumuDurumu.ARSIV,
            )
            .order_by(CizelgeSurumu.yayin_zamani.desc())
        )
        return self.oturum.execute(stmt).scalars().first()


class CozumIsiDeposu(TabanDepo[CozumIsi]):
    def __init__(self, oturum: Session) -> None:
        super().__init__(oturum, CozumIsi)

    def aktif_isi_getir(self) -> CozumIsi | None:
        """Devam eden ya da karar bekleyen is (SDD 6.1, SRS FR-4.11).

        Kabuktaki calisan is gostergesinin kaynagi. Karar bekleyen is de
        aktiftir: kullanici baska bir ekrandayken durdurup unutursa, is
        sessizce askida kalmamali.

        Kuramsal olarak birden fazla olabilir (iki isin ayni anda kuyruga
        yazilmasi engellenmis degil); gostergede tek bir is durdugu icin en
        yenisi secilir.
        """
        stmt = (
            select(CozumIsi)
            .where(CozumIsi.durum.in_(AKTIF_DURUMLAR))
            .order_by(CozumIsi.is_id.desc())
        )
        return self.oturum.execute(stmt).scalars().first()

    def surume_gore_en_son(self, surum_id: int) -> CozumIsi | None:
        """Bir surumun (yeniden calistirma ile birden fazla olabilecek) cozum
        islerinden en sonuncusu - Analiz servisinin ceza dokumu/toplam ceza
        kaynagi (SDD 5.7, Gun 12 notu: cozum_isi.surum_id iliskisi)."""
        stmt = select(CozumIsi).where(CozumIsi.surum_id == surum_id).order_by(CozumIsi.is_id.desc())
        return self.oturum.execute(stmt).scalars().first()

    def surumlere_gore_en_son_ceza(self, surum_idleri: Sequence[int]) -> dict[int, float]:
        """Surum listesi icin (SDD 6.3.5) her surumun EN SON cozum isindeki
        toplam cezasi - surum basina ayri sorgu yerine tek sorguda.

        Bir surumun birden fazla cozum isi olabilir (yeniden calistirma);
        surume_gore_en_son ile ayni secim: en buyuk is_id."""
        if not surum_idleri:
            return {}
        en_son = (
            select(func.max(CozumIsi.is_id).label("is_id"))
            .where(CozumIsi.surum_id.in_(surum_idleri))
            .group_by(CozumIsi.surum_id)
            .scalar_subquery()
        )
        stmt = select(CozumIsi.surum_id, CozumIsi.en_iyi_ceza).where(CozumIsi.is_id.in_(en_son))
        return {
            surum_id: float(ceza)
            for surum_id, ceza in self.oturum.execute(stmt).all()
            if ceza is not None
        }


class AtamaDeposu(TabanDepo[Atama]):
    def __init__(self, oturum: Session) -> None:
        super().__init__(oturum, Atama)

    def surume_gore_sil(self, surum_id: int) -> None:
        """SDD 5.4: atamalar yazilmadan once o surumun mevcut atamalari silinir."""
        self.oturum.execute(delete(Atama).where(Atama.surum_id == surum_id))

    def surume_gore_getir(self, surum_id: int) -> Sequence[Atama]:
        stmt = select(Atama).where(Atama.surum_id == surum_id)
        return self.oturum.execute(stmt).scalars().all()

    def surume_ve_araliga_gore_getir(
        self, surum_id: int, baslangic: date, bitis: date
    ) -> Sequence[Atama]:
        """SDD 5.5: degisikligi_dogrula'nin pencere kapsamli kurallar icin kullandigi
        atama kumesi (degistirilen gunun +-7 gunluk penceresi).

        Sinir BASLANGIC ZAMANINA gore alinir: blok basladigi gune sayilir
        (SRS TD-1) ve pencere de o gunler uzerinde tanimlidir. Bitis
        zamanina bakan bir filtre, pencerenin son gecesinde baslayip ertesi
        sabah biten blogu pencerenin disinda birakirdi.
        """
        stmt = select(Atama).where(
            Atama.surum_id == surum_id,
            Atama.baslangic_zamani >= datetime.combine(baslangic, time.min),
            Atama.baslangic_zamani < datetime.combine(bitis + timedelta(days=1), time.min),
        )
        return self.oturum.execute(stmt).scalars().all()

    def surume_ve_personele_gore_getir(self, surum_id: int, personel_id: int) -> Sequence[Atama]:
        """Calisan Paneli — Vardiyalarim (SDD 6.1): bir surumdeki, tek bir
        personele ait bloklar, baslangic zamanina gore sirali."""
        stmt = (
            select(Atama)
            .where(Atama.surum_id == surum_id, Atama.personel_id == personel_id)
            .order_by(Atama.baslangic_zamani)
        )
        return self.oturum.execute(stmt).scalars().all()

    def gune_gore_getir(self, surum_id: int, personel_id: int, tarih: date) -> Sequence[Atama]:
        """Bir personelin o gun BASLAYAN bloklari (SRS TD-1).

        LISTE DONDURUR, tekil kayit degil. Eski benzersizlik kisiti
        `(surum_id, personel_id, tarih)` idi ve "gunde tek atama"yi
        veritabani duzeyinde zorluyordu; yeni anahtar baslangic ZAMANINI
        tasidigi icin ayni gunde farkli saatte baslayan ikinci bir blogu
        yakalayamaz (SDD 4.2.1). Kural artik yalnizca uygulama
        katmanindadir; cagiran taraf "en fazla bir tane" varsayimini
        yapamaz, saymak zorundadir.
        """
        stmt = (
            select(Atama)
            .where(
                Atama.surum_id == surum_id,
                Atama.personel_id == personel_id,
                Atama.baslangic_zamani >= datetime.combine(tarih, time.min),
                Atama.baslangic_zamani < datetime.combine(tarih + timedelta(days=1), time.min),
            )
            .order_by(Atama.baslangic_zamani)
        )
        return self.oturum.execute(stmt).scalars().all()


class FazlaKadroDeposu(TabanDepo[FazlaKadro]):
    """Talepten fazla kadro kayitlari (bkz. goc a4d92c15e807).

    `KapsamaAcigiDeposu` ile ayni yuzeyi tasir; iki tablonun ayri
    tutulmasinin gerekcesi model ve goc dosyasinda yazili.
    """

    def __init__(self, oturum: Session) -> None:
        super().__init__(oturum, FazlaKadro)

    def surume_gore_sil(self, surum_id: int) -> None:
        self.oturum.execute(delete(FazlaKadro).where(FazlaKadro.surum_id == surum_id))

    def surume_gore_getir(self, surum_id: int) -> Sequence[FazlaKadro]:
        stmt = (
            select(FazlaKadro)
            .where(FazlaKadro.surum_id == surum_id)
            .order_by(FazlaKadro.tarih, FazlaKadro.baslangic, FazlaKadro.nokta_id)
        )
        return self.oturum.execute(stmt).scalars().all()

    def surumlere_gore_fazla_toplami(self, surum_idleri: Sequence[int]) -> dict[int, int]:
        """Surum basina toplam fazla KISI sayisi (Surumler ekrani icin)."""
        if not surum_idleri:
            return {}
        stmt = (
            select(FazlaKadro.surum_id, func.sum(FazlaKadro.fazla_sayi))
            .where(FazlaKadro.surum_id.in_(surum_idleri))
            .group_by(FazlaKadro.surum_id)
        )
        return {surum_id: int(toplam or 0) for surum_id, toplam in self.oturum.execute(stmt)}


class KapsamaAcigiDeposu(TabanDepo[KapsamaAcigi]):
    def __init__(self, oturum: Session) -> None:
        super().__init__(oturum, KapsamaAcigi)

    def surume_gore_sil(self, surum_id: int) -> None:
        self.oturum.execute(delete(KapsamaAcigi).where(KapsamaAcigi.surum_id == surum_id))

    def surume_gore_getir(self, surum_id: int) -> Sequence[KapsamaAcigi]:
        stmt = select(KapsamaAcigi).where(KapsamaAcigi.surum_id == surum_id)
        return self.oturum.execute(stmt).scalars().all()

    def surumlere_gore_eksik_toplami(self, surum_idleri: Sequence[int]) -> dict[int, int]:
        """Surum listesi icin (SDD 6.3.5) surum basina toplam eksik KISI sayisi.

        Acik HUCRE sayisi degil kisi sayisi toplanir: bir hucrede birden fazla
        kisi eksik olabilir (eksik_sayi > 1) ve "kapsama acigi" kullanicinin
        kapatmasi gereken kisi sayisidir."""
        if not surum_idleri:
            return {}
        stmt = (
            select(KapsamaAcigi.surum_id, func.sum(KapsamaAcigi.eksik_sayi))
            .where(KapsamaAcigi.surum_id.in_(surum_idleri))
            .group_by(KapsamaAcigi.surum_id)
        )
        return {surum_id: int(toplam or 0) for surum_id, toplam in self.oturum.execute(stmt).all()}
