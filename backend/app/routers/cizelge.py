"""Cizelgeleme uc noktalari (SDD 3.2: cizelge_router; SDD Ek B).

/api/on-kontrol (Sprint 2 Gun 7), /api/cozum (Sprint 2 Gun 8), /api/atama
(Sprint 2 Gun 9), /api/donem + /api/surum + /api/atama/kilit (Sprint 2 Gun 10 -
Cizelge/Cozum ekranlarinin ihtiyac duydugu okuma uc noktalari ve kilitleme).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import oturum_al
from app.guvenlik import idare_yetkisi
from app.hatalar import Hata, kodu
from app.kurallar.temel import Ihlal
from app.repositories.sonuc import (
    AtamaDeposu,
    CizelgeSurumuDeposu,
    CozumIsiDeposu,
    DonemDeposu,
    FazlaKadroDeposu,
    KapsamaAcigiDeposu,
    SurumSilinemezError,
)
from app.schemas.cozum import (
    CozumBaslatIstek,
    CozumKarariIstek,
    CozumKarariYaniti,
    CozumOku,
)
from app.schemas.dogrulama import (
    CezaKalemiOku,
    DogrulamaIstegi,
    DogrulamaSonucuOku,
    IhlalOku,
    KaydetIstegi,
)
from app.schemas.on_kontrol import BulguOku, OnKontrolIstek, OnKontrolYaniti
from app.schemas.surum import (
    AtamaKilitIstek,
    AtamaOku,
    CizelgeSurumuOku,
    DonemOku,
    DonemOlustur,
    FazlaKadroOku,
    KapsamaAcigiOku,
    SurumKarsilastirmaOku,
    SurumOzetiOku,
    SurumTaslakTuretIstek,
)
from app.services.cozum_servisi import (
    CozumServisi,
    DurdurulamazError,
    KararUygulanamazError,
    durdurma_istegini_uygula,
    durdurma_karari_uygula,
)
from app.services.dogrulama_servisi import (
    AtamaDegisikligi,
    DamgaCakismasiError,
    DogrulamaServisi,
    DogrulamaSonucu,
    SurumTaslakDegilError,
    ZorunluIhlalError,
)
from app.services.on_kontrol_servisi import OnKontrolServisi
from app.services.surum_servisi import (
    KopyalanamazSurumDurumuError,
    SurumlerAyniDonemdeDegilError,
    SurumServisi,
)

# Cozum, manuel duzenleme, surum ve yayin islevlerinin tamami yonetici
# yetkisi ister (SRS 5.10). Kapi router duzeyinde bagli.
router = APIRouter(prefix="/api", tags=["cizelge"], dependencies=[Depends(idare_yetkisi)])

Oturum = Annotated[Session, Depends(oturum_al)]


@router.post("/on-kontrol", response_model=OnKontrolYaniti)
def on_kontrol_calistir(istek: OnKontrolIstek, oturum: Oturum) -> OnKontrolYaniti:
    servis = OnKontrolServisi(oturum)
    bulgular = servis.calistir(istek.donem_id)
    if bulgular is None:
        raise Hata(status_code=404, kod="donem_yok", detail="Donem bulunamadi")
    return OnKontrolYaniti(bulgular=[BulguOku.model_validate(b) for b in bulgular])


@router.post("/cozum", response_model=CozumOku, status_code=201)
def cozum_baslat(istek: CozumBaslatIstek, oturum: Oturum) -> CozumOku:
    servis = CozumServisi(oturum)
    is_kaydi = servis.baslat(
        istek.donem_id,
        onceki_surum_id=istek.onceki_surum_id,
        zaman_limiti_saniye=istek.zaman_limiti_saniye,
    )
    if is_kaydi is None:
        raise Hata(
            status_code=404,
            kod="donem_ya_da_surum_yok",
            detail="Donem ya da onceki surum bulunamadi",
        )
    return CozumOku.model_validate(is_kaydi)


@router.get("/cozum/aktif", response_model=CozumOku | None)
def cozum_aktif(oturum: Oturum) -> CozumOku | None:
    """Devam eden ya da karar bekleyen is; yoksa bos (SDD 6.1, SRS FR-4.11).

    Yonetici kabugundaki calisan is gostergesi bunu yoklar. Uc noktanin
    varlik nedeni, IS KIMLIGININ ISTEMCIDE TUTULMAMASIDIR: isin varligi
    zaten veritabaninda kayitli ve tek dogru kaynak orasi. Kimligin
    tarayicida ikinci bir kopyasinin durmasi, sayfa yenilendiginde veya
    baska bir cihazdan girildiginde iki kaynagi ayristirir - is gercekte
    surerken arayuzden kaybolmasinin nedeni tam olarak buydu.

    Yol, /cozum/{is_id} deseninden ONCE tanimlanmak zorunda: aksi halde
    FastAPI "aktif" dizesini is_id olarak ayristirmaya calisir.
    """
    is_kaydi = CozumIsiDeposu(oturum).aktif_isi_getir()
    return None if is_kaydi is None else CozumOku.kayittan(is_kaydi)


@router.get("/cozum/{is_id}", response_model=CozumOku)
def cozum_durumu(is_id: int, oturum: Oturum) -> CozumOku:
    is_kaydi = CozumIsiDeposu(oturum).getir(is_id)
    if is_kaydi is None:
        raise Hata(status_code=404, kod="cozum_isi_yok", detail="Cozum isi bulunamadi")
    return CozumOku.kayittan(is_kaydi)


@router.post("/cozum/{is_id}/durdur", response_model=CozumOku)
def cozum_durdur(is_id: int, oturum: Oturum) -> CozumOku:
    """Durdurma istegini VERITABANINA yazar; sonuc isin DURUMUNA baglidir.

    Arama sururken (`cozuluyor`) bu bir IPTAL DEGIL SONLANDIRMADIR (SRS
    FR-4.9): isci aramayi sonlandirir, elindeki en iyi cozumu
    `gecici_sonuc`a yazar ve is kullanicinin kararini bekler; surume
    hicbir sey yazilmaz.

    Arama henuz baslamamissa (`kuyrukta`, `on_kontrol`) is DOGRUDAN IPTAL
    olur ve karar sorulmaz - saklanacak bir sonuc yok (SDD 5.4.1).

    Cozum isci ayri bir SERVIS oldugundan (SDD 3.4.4) API o sureci
    olduremez; iki surec arasindaki tek kanal veritabanidir. Isci durumu
    arama surerken duzenli araliklarla taze okur ve gordugunde aramayi
    disaridan sonlandirir - olculen gecikme yarim saniye mertebesinde
    (SDD 5.4.2, SRS NFR-14).
    """
    try:
        is_kaydi = durdurma_istegini_uygula(oturum, is_id)
    except LookupError as hata:
        raise Hata(status_code=404, kod=kodu(hata), detail=str(hata)) from hata
    except DurdurulamazError as hata:
        raise Hata(status_code=409, kod=kodu(hata), detail=str(hata)) from hata
    return CozumOku.kayittan(is_kaydi)


@router.post("/cozum/{is_id}/karar", response_model=CozumKarariYaniti)
def cozum_karari(is_id: int, istek: CozumKarariIstek, oturum: Oturum) -> CozumKarariYaniti:
    """Durdurulan iste kullanici karari: kullan | at | devam (SRS FR-4.10).

    SDD 5.4.1'deki `durdurma_karari_uygula` yordami. "devam", aramanin
    kaldigi yerden surdurulmesi DEGILDIR: bulunan cozum ipucu verilerek
    yeni bir arama baslatilir ve sure sifirdan isler.
    """
    try:
        is_kaydi, yeni_is = durdurma_karari_uygula(
            oturum, is_id, istek.karar, zaman_limiti_saniye=istek.zaman_limiti_saniye
        )
    except LookupError as hata:
        raise Hata(status_code=404, kod=kodu(hata), detail=str(hata)) from hata
    except KararUygulanamazError as hata:
        raise Hata(status_code=409, kod=kodu(hata), detail=str(hata)) from hata
    return CozumKarariYaniti(
        is_kaydi=CozumOku.kayittan(is_kaydi),
        yeni_is=None if yeni_is is None else CozumOku.kayittan(yeni_is),
    )


def _degisikliklere_cevir(istek: DogrulamaIstegi) -> list[AtamaDegisikligi]:
    return [
        AtamaDegisikligi(
            personel_id=d.personel_id,
            tarih=d.tarih,
            baslangic_saati=d.baslangic_saati,
            bitis_saati=d.bitis_saati,
            nokta_id=d.nokta_id,
        )
        for d in istek.degisiklikler
    ]


def _ihlali_cevir(i: Ihlal) -> IhlalOku:
    return IhlalOku(
        kural_kimlik=i.kural_kimlik,
        aciklama=i.aciklama,
        personel_id=i.personel_id,
        tarih=i.tarih,
        ceza=i.ceza,
    )


def _sonucu_cevir(sonuc: DogrulamaSonucu, *, damga: str | None = None) -> DogrulamaSonucuOku:
    return DogrulamaSonucuOku(
        kabul_edilebilir=sonuc.kabul_edilebilir,
        zorunlu_ihlaller=[_ihlali_cevir(i) for i in sonuc.zorunlu_ihlaller],
        ceza_degisimi=sonuc.ceza_degisimi,
        agirlikli_ceza_degisimi=sonuc.agirlikli_ceza_degisimi,
        ceza_dokumu=[
            CezaKalemiOku(
                kural_kimlik=k.kural_kimlik,
                ad=k.ad,
                ham_fark=k.ham_fark,
                agirlik=k.agirlik,
                agirlikli_fark=k.agirlikli_fark,
            )
            for k in sonuc.ceza_dokumu
        ],
        uyarilar=[_ihlali_cevir(i) for i in sonuc.uyarilar],
        damga=damga,
    )


@router.post("/atama/dogrula", response_model=DogrulamaSonucuOku)
def atama_dogrula(istek: DogrulamaIstegi, oturum: Oturum) -> DogrulamaSonucuOku:
    """Oturumun tamamini degerlendirir; HICBIR SEY YAZMAZ (SDD 5.5)."""
    servis = DogrulamaServisi(oturum)
    try:
        sonuc = servis.dogrula(istek.surum_id, _degisikliklere_cevir(istek))
    except SurumTaslakDegilError as hata:
        raise Hata(status_code=409, kod=kodu(hata), detail=str(hata)) from hata
    if sonuc is None:
        raise Hata(status_code=404, kod="surum_yok", detail="Cizelge surumu bulunamadi")
    return _sonucu_cevir(sonuc)


@router.post("/atama/kaydet", response_model=DogrulamaSonucuOku)
def atama_kaydet(istek: KaydetIstegi, oturum: Oturum) -> DogrulamaSonucuOku:
    """Biriken degisikliklerin tamamini TEK ISLEMDE yazar (SDD 5.5.1).

    409'un uc ayri nedeni vardir ve ucu de kullaniciya farkli sey soyler:
    surum yayinlanmis (yeni taslak turetilmeli), damga cakismis (baska biri
    kaydetmis) ya da zorunlu kisit ihlali var (degisiklik gecersiz).
    """
    servis = DogrulamaServisi(oturum)
    try:
        yanit = servis.kaydet(istek.surum_id, _degisikliklere_cevir(istek), istek.damga)
    except SurumTaslakDegilError as hata:
        raise Hata(status_code=409, kod=kodu(hata), detail=str(hata)) from hata
    except DamgaCakismasiError as hata:
        raise Hata(status_code=409, kod=kodu(hata), detail=str(hata)) from hata
    except ZorunluIhlalError as hata:
        sonuc = DogrulamaSonucuOku(
            kabul_edilebilir=False,
            zorunlu_ihlaller=[_ihlali_cevir(i) for i in hata.ihlaller],
            ceza_degisimi=0.0,
        )
        raise Hata(
            status_code=409, kod="zorunlu_ihlal", detail=sonuc.model_dump(mode="json")
        ) from hata
    if yanit is None:
        raise Hata(status_code=404, kod="surum_yok", detail="Cizelge surumu bulunamadi")
    sonuc, yeni_damga = yanit
    return _sonucu_cevir(sonuc, damga=yeni_damga)


@router.post("/atama/kilit", response_model=AtamaOku)
def atama_kilit_ayarla(istek: AtamaKilitIstek, oturum: Oturum) -> AtamaOku:
    servis = DogrulamaServisi(oturum)
    try:
        atama = servis.kilit_ayarla(istek.surum_id, istek.personel_id, istek.tarih, istek.kilitli)
    except SurumTaslakDegilError as hata:
        raise Hata(status_code=409, kod=kodu(hata), detail=str(hata)) from hata
    if atama is None:
        raise Hata(
            status_code=404,
            kod="surum_ya_da_atama_yok",
            detail="Cizelge surumu ya da atama bulunamadi",
        )
    return AtamaOku.model_validate(atama)


# --- Donem / Surum okuma uc noktalari (SDD Ek B; cizelge/cozum ekranlarinin
# donem secici + izgara + kapsama acigi ihtiyaci icin) -----------------------


@router.get("/donem", response_model=list[DonemOku])
def donem_listele(oturum: Oturum) -> list[DonemOku]:
    return list(DonemDeposu(oturum).tumunu_getir())  # type: ignore[return-value]


@router.post("/donem", response_model=DonemOku, status_code=201)
def donem_olustur(veri: DonemOlustur, oturum: Oturum) -> DonemOku:
    return DonemDeposu(oturum).olustur(**veri.model_dump())  # type: ignore[return-value]


@router.get("/surum", response_model=list[SurumOzetiOku])
def surum_listele(
    oturum: Oturum, donem_id: Annotated[int | None, Query()] = None
) -> list[SurumOzetiOku]:
    """SDD 6.3.5 Surum Listesi: numara, durum, olusturma zamani, toplam ceza
    ve kapsama acigi sayisi."""
    return SurumServisi(oturum).listele(donem_id=donem_id)


@router.get("/surum/karsilastir", response_model=SurumKarsilastirmaOku)
def surum_karsilastir(
    oturum: Oturum,
    onceki_surum_id: Annotated[int, Query()],
    yeni_surum_id: Annotated[int, Query()],
) -> SurumKarsilastirmaOku:
    """SDD 6.3.5 Karsilastir Butonu: secilen iki surum arasindaki farkli
    atamalari listeler.

    Yol, /surum/{surum_id} deseninden ONCE tanimlanmak zorunda: aksi halde
    FastAPI "karsilastir" dizesini surum_id olarak ayristirmaya calisir.
    """
    try:
        sonuc = SurumServisi(oturum).karsilastir(onceki_surum_id, yeni_surum_id)
    except SurumlerAyniDonemdeDegilError as hata:
        raise Hata(status_code=409, kod=kodu(hata), detail=str(hata)) from hata
    if sonuc is None:
        raise Hata(status_code=404, kod="surum_yok", detail="Cizelge surumu bulunamadi")
    return sonuc


@router.post("/surum", response_model=CizelgeSurumuOku, status_code=201)
def surum_taslak_turet(veri: SurumTaslakTuretIstek, oturum: Oturum) -> CizelgeSurumuOku:
    """SDD Ek B: 'Cizelge surumleri; taslak turetme'. Cozum baslatmaz.

    Iki dal: `onceki_surum_id` verilirse o suruma bagli bos bir taslak
    olusturulur (fiili yeniden cozum icin bkz. POST /api/cozum +
    onceki_surum_id); `donem_id` verilirse donemden DOGRUDAN bos bir taslak
    acilir (Tur 13) - donemde surum varsa yenisi en sonuncuya baglanir,
    yoksa onceki_surum_id bos kalir (bkz. CizelgeSurumuDeposu.taslak_ac).
    """
    depo = CizelgeSurumuDeposu(oturum)
    if veri.donem_id is not None:
        if DonemDeposu(oturum).getir(veri.donem_id) is None:
            raise Hata(status_code=404, kod="donem_yok", detail="Donem bulunamadi")
        surum = depo.taslak_ac(veri.donem_id)
    else:
        surum = depo.taslak_turet(veri.onceki_surum_id)  # type: ignore[arg-type]
        if surum is None:
            raise Hata(status_code=404, kod="onceki_surum_yok", detail="Onceki surum bulunamadi")
    return CizelgeSurumuOku.model_validate(surum)


@router.post("/surum/{surum_id}/kopyala", response_model=CizelgeSurumuOku, status_code=201)
def surum_taslak_olarak_kopyala(surum_id: int, oturum: Oturum) -> CizelgeSurumuOku:
    """Arsivlenmis (veya yayinlanmis) bir surumden atamalariyla birlikte yeni
    bir taslak turetir. Kaynak kayit degismez.

    `POST /api/surum`ten farki atamalarin KOPYALANMASI: orasi cozucunun
    dolduracagi bos bir taslak acar, burasi kaynagin cizelgesini oldugu gibi
    tasir.

    Surum satiri ve atamalarin tamami TEK islemde yazilir; islem sinirini
    `oturum_al` bagimliligi cizer (istek basariyla biterse onaylar, hata
    halinde tamamini geri alir). Yari kopyalanmis bir taslak, kural ihlali
    icermeyen ama kapsamasi eksik bir cizelgeden ayirt edilemez (SDD 5.4).
    """
    try:
        yeni = SurumServisi(oturum).taslak_olarak_kopyala(surum_id)
    except KopyalanamazSurumDurumuError as hata:
        raise Hata(status_code=409, kod=kodu(hata), detail=str(hata)) from hata
    if yeni is None:
        raise Hata(status_code=404, kod="surum_yok", detail="Cizelge surumu bulunamadi")
    return CizelgeSurumuOku.model_validate(yeni)


@router.post("/surum/{surum_id}/yayinla", response_model=CizelgeSurumuOku)
def surum_yayinla(surum_id: int, oturum: Oturum) -> CizelgeSurumuOku:
    """TD-8: surumu yayinlar; ayni donemde daha once yayinlanmis bir surum
    varsa arsiv durumuna gecer."""
    surum = CizelgeSurumuDeposu(oturum).yayinla(surum_id)
    if surum is None:
        raise Hata(status_code=404, kod="surum_yok", detail="Cizelge surumu bulunamadi")
    return CizelgeSurumuOku.model_validate(surum)


@router.delete("/surum/{surum_id}", status_code=204)
def surum_sil(surum_id: int, oturum: Oturum) -> None:
    """Yayinlanmamis bir surumu siler (SDD 5.6).

    Her cozum denemesi bir surum aciyor ve kullanilmayanlari birakmaktan
    baska yol yoktu; Surumler ekrani denenip vazgecilmis taslaklarla
    doluyordu.

    409'un uc ayri nedeni var ve ucu de kullaniciya farkli sey soyler:
    surum yayinlanmis (calisan paneli onu okuyor), arsivlenmis (FR-9.4'un
    degisen gunler isareti onu taban aliyor) ya da baska bir surum ona bagli
    (zincir kopar).
    """
    try:
        silindi = CizelgeSurumuDeposu(oturum).sil(surum_id)
    except SurumSilinemezError as hata:
        raise Hata(status_code=409, kod=kodu(hata), detail=str(hata)) from hata
    if not silindi:
        raise Hata(status_code=404, kod="surum_yok", detail="Cizelge surumu bulunamadi")


@router.get("/surum/{surum_id}/atama", response_model=list[AtamaOku])
def surum_atamalarini_getir(surum_id: int, oturum: Oturum) -> list[AtamaOku]:
    return list(AtamaDeposu(oturum).surume_gore_getir(surum_id))  # type: ignore[return-value]


@router.get("/surum/{surum_id}/kapsama-acigi", response_model=list[KapsamaAcigiOku])
def surum_kapsama_acigini_getir(surum_id: int, oturum: Oturum) -> list[KapsamaAcigiOku]:
    return list(KapsamaAcigiDeposu(oturum).surume_gore_getir(surum_id))  # type: ignore[return-value]


@router.get("/surum/{surum_id}/fazla-kadro", response_model=list[FazlaKadroOku])
def surum_fazla_kadrosunu_getir(surum_id: int, oturum: Oturum) -> list[FazlaKadroOku]:
    """Talepten fazla kadro yazilmis hucreler (SRS 4.3 S1 ust siniri).

    AYRI bir uc nokta; kapsama acigi uc noktasinin sozlesmesi
    degistirilmedi. O uc noktayi "her satir bir aciktir" varsayimiyla
    okuyan ekranlar (cizelge izgarasi, yazdirma gorunumu, Ozet) boylece
    hicbir degisiklik gerektirmeden dogru kalir.
    """
    return list(FazlaKadroDeposu(oturum).surume_gore_getir(surum_id))  # type: ignore[return-value]
