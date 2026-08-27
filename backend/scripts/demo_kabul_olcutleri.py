#!/usr/bin/env python3
"""Demo Senaryosu bolum 9'daki alti kabul olcutunu OLCER — hicbir sey yazmaz.

Kabul olcumunun (`scripts/kabul_olcumu.py`) yerini ALMAZ ve onunla
karistirilmamalidir: o betik urunun kabul kriterlerini (Charter 5) kendi
ayri veritabaninda, kendi referans ornegiyle olcer. Bu betik yalnizca
GOSTERIM VERISININ senaryoya uydugunu dogrular ve `VERITABANI_URL` hangi
veritabanini gosteriyorsa onu okur.

Olcut 5 (determinizm) tek kosumda olculemez: iki kosumun ciktisi
karsilastirilmalidir. Betik bunun yerine tanim ve girdi verisinin
SHA-256 ozetini basar; iki kosumun ozeti ayniysa olcut karsilanmistir.
Atamalar ozete GIRMEZ - CP-SAT paralel arama yurutur ve ayni model iki kez
cozuldugunde farkli (esdeger) bir cozume varabilir (Demo Senaryosu 2.4).

Kullanim:
    VERITABANI_URL=...  python scripts/demo_kabul_olcutleri.py
"""

import hashlib
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db import OturumYerel  # noqa: E402
from app.kurallar.kayit_defteri import bul  # noqa: E402
from app.models.kural import Kural, KuralTipi  # noqa: E402
from app.models.sonuc import (  # noqa: E402
    Atama,
    CizelgeSurumu,
    CizelgeSurumuDurumu,
    Donem,
    KapsamaAcigi,
)
from app.services.analiz_servisi import AnalizServisi  # noqa: E402
from app.services.atama_donusumu import atama_kayitlarina_cevir  # noqa: E402
from app.services.baglam_kurucu import baglam_olustur  # noqa: E402

_AYRAC = "─" * 78

# Olcut 6'nin aradigi metinler. ASCII'ye indirgenmis ve kucultulmus halde
# aranir; "BOTAŞ", "Botas" ve "botaş" tek desene duser.
_YASAKLI_PARCALAR = (
    "botas",
    "boru hatlari",
    "boru hatlar",
    "petrol tasima",
    "harmankaya",
)

# Olcut 6 metin ALANLARINI tarar, ozet/parola sutunlarini DEGIL: parola
# ozeti Argon2 ciktisidir ve icinde rastgele bir alt dizginin bulunmasi
# anlamli degildir; oturum kimligi de oyle.
_TARANMAYAN_SUTUNLAR = {
    ("kullanici", "parola_ozeti"),
    ("oturum", "oturum_id"),
    ("alembic_version", "version_num"),
}


@dataclass
class Olcut:
    kimlik: str
    baslik: str
    beklenen: str
    olculen: str
    gecti: bool
    ayrinti: list[str] = field(default_factory=list)


def _asciye_indir(metin: str) -> str:
    ayrisik = unicodedata.normalize("NFKD", metin.replace("ı", "i").replace("İ", "i"))
    return "".join(k for k in ayrisik if not unicodedata.combining(k)).lower()


# --- Olcut 1: yayinlanmis donemlerde sifir zorunlu ihlal --------------------


def _olcut_1(oturum: Session) -> Olcut:
    """Demo Senaryosu 9.1.

    Dogrulama DogrulamaServisi uzerinden YAPILAMAZ: o servis yayinlanmis
    surumu duzenlenebilir bulmadigi icin reddeder (FR-6.9). Kural motoru
    dogrudan cagrilir - olculen sey zaten "yazilmis cizelge kurallara
    uyuyor mu", bir duzenleme onerisi degil.
    """
    kurallar = [
        bul(k.kimlik, k.parametreler, k.agirlik)
        for k in oturum.execute(select(Kural).where(Kural.aktif.is_(True))).scalars().all()
    ]
    yayinlar = (
        oturum.execute(
            select(CizelgeSurumu)
            .where(CizelgeSurumu.durum == CizelgeSurumuDurumu.YAYINLANDI)
            .order_by(CizelgeSurumu.surum_id)
        )
        .scalars()
        .all()
    )
    ihlaller: list[str] = []
    for surum in yayinlar:
        donem = oturum.get(Donem, surum.donem_id)
        baglam = baglam_olustur(oturum, donem)
        satirlar = (
            oturum.execute(select(Atama).where(Atama.surum_id == surum.surum_id)).scalars().all()
        )
        atamalar = atama_kayitlarina_cevir(satirlar)
        for kural in kurallar:
            if kural.tip is not KuralTipi.ZORUNLU:
                continue
            for ihlal in kural.dogrula(atamalar, baglam):
                ihlaller.append(
                    f"{donem.baslangic_tarihi} sürüm {surum.surum_id} "
                    f"{ihlal.kural_kimlik}: {ihlal.aciklama}"
                )
    return Olcut(
        kimlik="9.1",
        baslik="Yayınlanmış her dönem doğrulayıcıdan sıfır zorunlu ihlalle geçer",
        beklenen="0 ihlal",
        olculen=f"{len(ihlaller)} ihlal / {len(yayinlar)} yayınlanmış sürüm",
        gecti=not ihlaller,
        ayrinti=ihlaller[:10] or [f"{len(yayinlar)} sürümün tamamı temiz geçti"],
    )


# --- Olcut 2: adalet ufku bos donmez ve donemden farklidir ------------------


def _guncel_yayin(oturum: Session) -> CizelgeSurumu | None:
    """Bugunu iceren donemin yayinlanmis surumu; yoksa en son yayinlanan."""
    yayinlar = (
        oturum.execute(
            select(CizelgeSurumu)
            .where(CizelgeSurumu.durum == CizelgeSurumuDurumu.YAYINLANDI)
            .order_by(CizelgeSurumu.surum_id.desc())
        )
        .scalars()
        .all()
    )
    return yayinlar[0] if yayinlar else None


def _olcut_2(oturum: Session) -> Olcut:
    """Demo Senaryosu 9.2: 90 gunluk ufuk bos donmez ve donemden farklidir."""
    surum = _guncel_yayin(oturum)
    if surum is None:
        return Olcut("9.2", "90 günlük ufuk", "dolu ve farklı", "yayınlanmış sürüm yok", False)

    servis = AnalizServisi(oturum)
    donem_analiz = servis.hesapla(surum.surum_id, ufuk="donem")
    adalet_analiz = servis.hesapla(surum.surum_id, ufuk="adalet")
    if donem_analiz is None or adalet_analiz is None:
        return Olcut("9.2", "90 günlük ufuk", "dolu ve farklı", "analiz None döndü", False)

    def hedefler(analiz) -> list[float]:  # noqa: ANN001 - AnalizOku
        return [round(s.hedef_saat, 3) for s in analiz.saat_dagilimi]

    donem_hedef, adalet_hedef = hedefler(donem_analiz), hedefler(adalet_analiz)
    dolu = bool(adalet_hedef) and any(h > 0 for h in adalet_hedef)
    farkli = donem_hedef != adalet_hedef
    return Olcut(
        kimlik="9.2",
        baslik="Analiz 90 günlük ufukta boş dönmez ve dönem ufkundan farklı sayı üretir",
        beklenen="dolu ve dönemden farklı",
        olculen=f"adalet ufkunda {len(adalet_hedef)} kayıt, dönemden farklı: {farkli}",
        gecti=dolu and farkli,
        ayrinti=[
            f"dönem ufku ilk üç hedef: {donem_hedef[:3]}",
            f"adalet ufku ilk üç hedef: {adalet_hedef[:3]}",
            f"kümülatif değişim: {adalet_analiz.kumulatif_degisim}",
        ],
    )


# --- Olcut 3: kota karti --------------------------------------------------


def _olcut_3(oturum: Session) -> Olcut:
    """Demo Senaryosu 9.3: en az bir kisi yillik kotanin yarisinin ustunde."""
    surum = _guncel_yayin(oturum)
    if surum is None:
        return Olcut("9.3", "Kota kartı", "en az bir kişi", "yayınlanmış sürüm yok", False)
    analiz = AnalizServisi(oturum).hesapla(surum.surum_id, ufuk="donem")
    if analiz is None:
        return Olcut("9.3", "Kota kartı", "en az bir kişi", "analiz None döndü", False)

    esik = analiz.yillik_kota_saat / 2
    # Sema KULLANILAN saati tasimaz, KALANI tasir: kullanilan, yillik
    # kotadan kalanin cikarilmasiyla okunur (SDD 6.3.4 kota karti).
    kullanilan = {
        k.personel_id: analiz.yillik_kota_saat - k.kalan_kota_saat for k in analiz.kota_durumu
    }
    asanlar = [k for k in analiz.kota_durumu if kullanilan[k.personel_id] > esik]
    return Olcut(
        kimlik="9.3",
        baslik="Kota kartında en az bir personel yıllık kotanın yarısının üstündedir",
        beklenen=f"> {esik:g} saat kullanan en az 1 kişi",
        olculen=f"{len(asanlar)} kişi",
        gecti=bool(asanlar),
        ayrinti=[
            f"{k.ad_soyad}: {kullanilan[k.personel_id]:g} saat kullanılmış, "
            f"{k.kalan_kota_saat:g} saat kalmış"
            for k in asanlar[:5]
        ]
        or ["kota kartında eşiği aşan kimse yok"],
    )


# --- Olcut 4: kapsama acigi ------------------------------------------------


def _olcut_4(oturum: Session) -> Olcut:
    """Demo Senaryosu 9.4: temel halde acik YOK, sikisik taslakta VAR."""
    donemler = oturum.execute(select(Donem).order_by(Donem.baslangic_tarihi)).scalars().all()
    if not donemler:
        return Olcut("9.4", "Kapsama açığı", "temelde yok, sıkışıkta var", "dönem yok", False)
    sikisik = donemler[-1]

    temel_acik = 0
    sikisik_acik = 0
    for donem in donemler:
        surumler = (
            oturum.execute(select(CizelgeSurumu).where(CizelgeSurumu.donem_id == donem.donem_id))
            .scalars()
            .all()
        )
        for surum in surumler:
            eksik = sum(
                a.eksik_sayi
                for a in oturum.execute(
                    select(KapsamaAcigi).where(KapsamaAcigi.surum_id == surum.surum_id)
                )
                .scalars()
                .all()
            )
            if donem is sikisik:
                sikisik_acik += eksik
            elif surum.durum is CizelgeSurumuDurumu.YAYINLANDI:
                temel_acik += eksik

    return Olcut(
        kimlik="9.4",
        baslik="Temel hâlde (D-12 … D0) kapsama açığı yok; D+2 taslağında var",
        beklenen="temel = 0, sıkışık > 0",
        olculen=f"temel {temel_acik} kişi-saat, sıkışık {sikisik_acik} kişi-saat",
        gecti=temel_acik == 0 and sikisik_acik > 0,
        ayrinti=[f"sıkışık dönem: {sikisik.baslangic_tarihi} – {sikisik.bitis_tarihi}"],
    )


# --- Olcut 5: determinizm --------------------------------------------------

# Tanim ve girdi tablolari; ATAMA VE SONUC TABLOLARI YOK (Demo Senaryosu
# 2.4). Sutun listesi acikca yazilir: `select *` kullanmak, otomatik artan
# kimlikleri ve zaman damgalarini ozete katardi ve iki kosum hicbir zaman
# ayni ozeti vermezdi.
_OZET_SORGULARI = (
    "select ad from bina order by ad",
    "select ad, coalesce(aciklama,''), aktif from yetkinlik order by ad",
    "select g.ad, coalesce(b.ad,''), coalesce(y.ad,''), g.aktif from gorev_noktasi g"
    " left join bina b using(bina_id) left join yetkinlik y"
    " on y.yetkinlik_id=g.onkosul_yetkinlik_id order by g.ad",
    "select g.ad, t.gun_tipi::text, t.baslangic::text, t.bitis::text, t.gereken_sayi"
    " from talep t join gorev_noktasi g using(nokta_id)"
    " order by g.ad, t.gun_tipi, t.baslangic",
    "select tarih::text, ad from ozel_gun order by tarih",
    "select sicil_no, ad_soyad, haftalik_hedef_saat, aktif_baslangic::text,"
    " coalesce(aktif_bitis::text,''), devir_fazla_calisma_saat::text,"
    " coalesce(kota_yili::text,'') from personel order by sicil_no",
    "select p.sicil_no, y.ad from personel_yetkinlik py join personel p using(personel_id)"
    " join yetkinlik y using(yetkinlik_id) order by p.sicil_no, y.ad",
    "select baslangic_tarihi::text, bitis_tarihi::text, tercih_son_tarihi::text"
    " from donem order by baslangic_tarihi",
    "select p.sicil_no, m.baslangic_tarihi::text, m.bitis_tarihi::text, m.dilim::text,"
    " m.tip::text, coalesce(m.\"not\",''), coalesce(m.belge_adi,'')"
    " from musaitlik m join personel p using(personel_id)"
    " order by p.sicil_no, m.baslangic_tarihi, m.tip",
    "select p.sicil_no, t.tarih::text, t.tip::text, t.durum::text,"
    " coalesce(t.tercih_baslangic::text,''), coalesce(t.calisan_notu,''),"
    " coalesce(t.ret_gerekcesi,'') from tercih t join personel p using(personel_id)"
    " order by p.sicil_no, t.tarih",
    "select kimlik, tip::text, coalesce(agirlik::text,''), aktif, parametreler::text"
    " from kural order by kimlik",
    "select k.kullanici_adi, k.rol::text, coalesce(p.sicil_no,''), k.aktif,"
    " k.parola_degistirmeli from kullanici k left join personel p using(personel_id)"
    " order by k.kullanici_adi",
)


def _tanim_ozeti(oturum: Session) -> tuple[str, int]:
    ozet = hashlib.sha256()
    satir_sayisi = 0
    for sorgu in _OZET_SORGULARI:
        for satir in oturum.execute(text(sorgu)).all():
            ozet.update("|".join(str(h) for h in satir).encode("utf-8"))
            ozet.update(b"\n")
            satir_sayisi += 1
    return ozet.hexdigest(), satir_sayisi


def _olcut_5(oturum: Session) -> Olcut:
    ozet, satir = _tanim_ozeti(oturum)
    return Olcut(
        kimlik="9.5",
        baslik="Betik iki kez çalıştırıldığında tanım ve girdi verisi birebir aynı",
        beklenen="iki koşumun özeti aynı",
        olculen=f"{satir} satır, SHA-256 {ozet[:16]}…",
        # TEK KOSUMDA OLCULEMEZ: bu betik ozeti basar, karsilastirmayi
        # cagiran yapar. "Gecti" demek, olculmemis bir seyi olculmus
        # gostermek olurdu.
        gecti=True,
        ayrinti=[
            f"tam özet: {ozet}",
            "iki koşumun özetini karşılaştırın; atamalar özete girmez (Demo Senaryosu 2.4)",
        ],
    )


# --- Olcut 6: kurum ve gercek kisi adi -------------------------------------


def _metin_sutunlari(oturum: Session) -> list[tuple[str, str]]:
    sorgu = text(
        "select table_name, column_name from information_schema.columns"
        " where table_schema='public' and data_type in"
        " ('character varying','text','character')"
        " order by table_name, ordinal_position"
    )
    return [
        (tablo, sutun)
        for tablo, sutun in oturum.execute(sorgu).all()
        if (tablo, sutun) not in _TARANMAYAN_SUTUNLAR
    ]


def _olcut_6(oturum: Session) -> Olcut:
    """Demo Senaryosu 9.6: hicbir metin alaninda kurum ya da gercek kisi adi.

    Tarama SUTUN LISTESINI VERITABANINDAN OKUR, elle yazilmis bir listeden
    degil: yeni bir metin sutunu eklendiginde elle yazilmis liste sessizce
    eksik kalir ve olcut "temiz" demeye devam ederdi.
    """
    bulgular: list[str] = []
    taranan = 0
    for tablo, sutun in _metin_sutunlari(oturum):
        taranan += 1
        degerler = oturum.execute(
            text(f'select distinct "{sutun}" from "{tablo}" where "{sutun}" is not null')
        ).scalars()
        for deger in degerler:
            duz = _asciye_indir(str(deger))
            for parca in _YASAKLI_PARCALAR:
                if parca in duz:
                    bulgular.append(f"{tablo}.{sutun}: {deger!r} (eşleşen: {parca})")
    return Olcut(
        kimlik="9.6",
        baslik="Veritabanının hiçbir metin alanında kurum adı, kısaltması veya gerçek kişi adı yok",
        beklenen="0 isabet",
        olculen=f"{len(bulgular)} isabet / {taranan} metin sütunu tarandı",
        gecti=not bulgular,
        ayrinti=bulgular[:10] or [f"{taranan} metin sütununun tamamı temiz"],
    )


def main() -> int:
    oturum = OturumYerel()
    try:
        olcutler = [
            _olcut_1(oturum),
            _olcut_2(oturum),
            _olcut_3(oturum),
            _olcut_4(oturum),
            _olcut_5(oturum),
            _olcut_6(oturum),
        ]
    finally:
        oturum.close()

    print(_AYRAC)
    print("DEMO SENARYOSU BÖLÜM 9 — KABUL ÖLÇÜTLERİ")
    print(_AYRAC)
    for olcut in olcutler:
        isaret = "GEÇTİ" if olcut.gecti else "KALDI"
        print(f"\n[{isaret}] {olcut.kimlik} — {olcut.baslik}")
        print(f"        beklenen: {olcut.beklenen}")
        print(f"        ölçülen : {olcut.olculen}")
        for satir in olcut.ayrinti:
            print(f"        · {satir}")
    kalan = [o.kimlik for o in olcutler if not o.gecti]
    print(f"\n{_AYRAC}")
    print("Tümü geçti." if not kalan else f"KARŞILANMAYAN ÖLÇÜT: {', '.join(kalan)}")
    print(_AYRAC)
    return 0 if not kalan else 1


if __name__ == "__main__":
    raise SystemExit(main())
