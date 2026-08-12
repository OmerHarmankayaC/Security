"""Tanim yonetimi CRUD uc noktalari icin mutlu yol testleri (Sprint 1 Gun 4 kabul kriteri).

Canli bir PostgreSQL gerektirir (bkz. README "Kurulum"); bagilanamiyorsa atlanir.
Personel + yetkinlik + gorev noktasi + talep zincirinin elle (burada API
uzerinden) kurulabildigini dogrular.
"""

import uuid
from datetime import date, time
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.db import OturumYerel
from app.services.tanim_servisi import TanimServisi
from tests.conftest import (
    bos_vardiya_blogu,
    gecici_vardiya_tipi,
    pg_yoksa_atla,
    yetkili_istemci,
)


@pytest.fixture
def istemci() -> TestClient:
    pg_yoksa_atla()
    return yetkili_istemci()


def _benzersiz(on_ek: str) -> str:
    """Testler yeniden calistirildiginda benzersizlik kisitlarina takilmamak icin."""
    return f"{on_ek}-{uuid.uuid4().hex[:8]}"


def test_yetkinlik_olustur_listele_guncelle_sil(istemci: TestClient) -> None:
    yanit = istemci.post("/api/yetkinlik", json={"ad": _benzersiz("Test Yetkinligi FR12")})
    assert yanit.status_code == 201
    yetkinlik_id = yanit.json()["yetkinlik_id"]

    yanit = istemci.get("/api/yetkinlik")
    assert yanit.status_code == 200
    assert any(y["yetkinlik_id"] == yetkinlik_id for y in yanit.json())

    yanit = istemci.put(f"/api/yetkinlik/{yetkinlik_id}", json={"aciklama": "guncellendi"})
    assert yanit.status_code == 200
    assert yanit.json()["aciklama"] == "guncellendi"

    yanit = istemci.delete(f"/api/yetkinlik/{yetkinlik_id}")
    assert yanit.status_code == 204

    yanit = istemci.put(f"/api/yetkinlik/{yetkinlik_id}", json={"aciklama": "x"})
    assert yanit.status_code == 404


def test_bina_crud(istemci: TestClient) -> None:
    yanit = istemci.post("/api/bina", json={"ad": "Test Bina FR15"})
    assert yanit.status_code == 201
    bina_id = yanit.json()["bina_id"]

    yanit = istemci.put(f"/api/bina/{bina_id}", json={"ad": "Test Bina FR15 Guncel"})
    assert yanit.status_code == 200
    assert yanit.json()["ad"] == "Test Bina FR15 Guncel"

    assert istemci.delete(f"/api/bina/{bina_id}").status_code == 204


def test_vardiya_tipi_olustururken_gece_mi_onerilir(istemci: TestClient) -> None:
    # Saatler burada testin KONUSU (gece onerisi 00.00-08.00'e bakar), o
    # yuzden bos blok yardimcisi degil gecici blok kullaniliyor: kayit
    # birakilsaydi benzersizlik kisiti bu testi bir daha gecirmezdi.
    govde_istegi = {
        "ad": "Test Gece FR14",
        "baslangic_saati": "00:00:00",
        "bitis_saati": "08:00:00",
    }
    with gecici_vardiya_tipi(istemci, govde_istegi) as govde:
        assert govde["gece_mi"] is True
        assert float(govde["sure_saat"]) == 8.0


def test_vardiya_tipi_gece_mi_elle_belirtilebilir(istemci: TestClient) -> None:
    istek = {"ad": "Test Aksam FR14", "gece_mi": False, **bos_vardiya_blogu(istemci)}
    with gecici_vardiya_tipi(istemci, istek) as govde:
        assert govde["gece_mi"] is False


def test_personel_yetkinlik_nokta_talep_zinciri(istemci: TestClient) -> None:
    """Gun 4 kabul kriteri: personel+yetkinlik+gorev noktasi+talep zinciri API'den kurulur."""
    yetkinlik_yaniti = istemci.post(
        "/api/yetkinlik", json={"ad": _benzersiz("Guvenlik Gorevi FR-zincir")}
    )
    yetkinlik_id = yetkinlik_yaniti.json()["yetkinlik_id"]
    bina_id = istemci.post("/api/bina", json={"ad": "Bina A FR-zincir"}).json()["bina_id"]
    nokta_id = istemci.post(
        "/api/nokta",
        json={"ad": "Kapi FR-zincir", "bina_id": bina_id, "onkosul_yetkinlik_id": yetkinlik_id},
    ).json()["nokta_id"]
    # Vardiya tipi ARTIK ZINCIRDE DEGIL: talep bir calisma bloguna degil bir
    # zaman araligina baglaniyor (SDD 4.2.2), dolayisiyla bu testin kurdugu
    # zincirde blok katalogunun bir rolu kalmadi.

    yanit = istemci.post(
        "/api/personel",
        json={
            "ad_soyad": "Test Personel FR-zincir",
            "sicil_no": _benzersiz("ZNCR"),
            "haftalik_hedef_saat": 40,
            "aktif_baslangic": "2026-01-01",
            "yetkinlik_idleri": [yetkinlik_id],
        },
    )
    assert yanit.status_code == 201
    govde = yanit.json()
    personel_id = govde["personel_id"]
    assert govde["yetkinlik_idleri"] == [yetkinlik_id]

    # Talep artik HUCRE degil KAYIT: bir zaman araligi eklenir (SRS 3.3.4,
    # FR-1.7). Vardiya tipi kimligi tasimaz.
    yanit = istemci.post(
        "/api/talep",
        json={
            "nokta_id": nokta_id,
            "baslangic": "08:00",
            "bitis": "16:00",
            "gun_tipi": "hafta_ici",
            "gereken_sayi": 3,
        },
    )
    assert yanit.status_code == 201
    govde = yanit.json()
    assert any(h["nokta_id"] == nokta_id and h["gereken_sayi"] == 3 for h in govde["araliklar"])
    # 3 kisi x 5 hafta ici gun x 8 saat = 120 kisi-saat.
    assert float(govde["yuk_gostergesi"]["haftalik_kisi_saat"]) >= 120

    # Ayni nokta ve gun tipi icin CAKISAN aralik reddedilir (SDD 4.2.2):
    # cakisan iki kayit ayni saat icin iki farkli gereken sayi uretir.
    cakisan = istemci.post(
        "/api/talep",
        json={
            "nokta_id": nokta_id,
            "baslangic": "12:00",
            "bitis": "20:00",
            "gun_tipi": "hafta_ici",
            "gereken_sayi": 1,
        },
    )
    assert cakisan.status_code == 409

    yanit = istemci.get("/api/talep")
    assert yanit.status_code == 200
    assert any(h["nokta_id"] == nokta_id for h in yanit.json()["araliklar"])

    # DELETE personel icin pasiflestirmedir; kayit silinmez, aktif_bitis dolar.
    assert istemci.delete(f"/api/personel/{personel_id}").status_code == 204
    kalan = istemci.get("/api/personel").json()
    guncel = next(p for p in kalan if p["personel_id"] == personel_id)
    assert guncel["aktif_bitis"] is not None

    # DELETE gorev noktasi icin de pasiflestirmedir (aktif=False).
    assert istemci.delete(f"/api/nokta/{nokta_id}").status_code == 204
    kalan_noktalar = istemci.get("/api/nokta").json()
    guncel_nokta = next(n for n in kalan_noktalar if n["nokta_id"] == nokta_id)
    assert guncel_nokta["aktif"] is False


def test_kullanilmayan_tanim_gercekten_silinir(istemci: TestClient) -> None:
    """Madde 1: hicbir yerde kullanilmamis bir tanim gercekten silinebilir."""
    bina_id = istemci.post("/api/bina", json={"ad": _benzersiz("Bos Bina")}).json()["bina_id"]

    kullanim = istemci.get(f"/api/bina/{bina_id}/kullanim").json()
    assert kullanim == {"kullanimda_mi": False, "toplam": 0, "kalemler": []}

    assert istemci.delete(f"/api/bina/{bina_id}").status_code == 204
    assert all(b["bina_id"] != bina_id for b in istemci.get("/api/bina").json())
    assert istemci.get(f"/api/bina/{bina_id}/kullanim").status_code == 404


def test_kullanimdaki_tanim_silinmez_pasiflestirilir(istemci: TestClient) -> None:
    """Madde 1: kullanimda olan tanim satiri KALIR, yalnizca aktif=False olur.

    Gerekce SDD 4.1: gecmis cizelgeler tanim satirlarina referansla durur.
    """
    bina_id = istemci.post("/api/bina", json={"ad": _benzersiz("Dolu Bina")}).json()["bina_id"]
    nokta_id = istemci.post(
        "/api/nokta", json={"ad": _benzersiz("Nokta"), "bina_id": bina_id}
    ).json()["nokta_id"]

    kullanim = istemci.get(f"/api/bina/{bina_id}/kullanim").json()
    assert kullanim["kullanimda_mi"] is True
    assert kullanim["toplam"] == 1
    assert kullanim["kalemler"] == [{"kayit_turu": "görev noktası", "sayi": 1}]

    assert istemci.delete(f"/api/bina/{bina_id}").status_code == 204

    kalan = istemci.get("/api/bina").json()
    guncel = next(b for b in kalan if b["bina_id"] == bina_id)
    assert guncel["aktif"] is False, "kullanimdaki bina silinmemeli, pasiflesmeli"

    # Noktanin binaya referansi bozulmadi.
    nokta = next(n for n in istemci.get("/api/nokta").json() if n["nokta_id"] == nokta_id)
    assert nokta["bina_id"] == bina_id


def test_kullanim_sayimi_kayit_turu_kiriliminda(istemci: TestClient) -> None:
    """Onay kutusunun metni bu dokumden kurulur (FR-1.1, NFR-5)."""
    yetkinlik_id = istemci.post("/api/yetkinlik", json={"ad": _benzersiz("Yetkinlik")}).json()[
        "yetkinlik_id"
    ]
    istemci.post(
        "/api/nokta", json={"ad": _benzersiz("Nokta"), "onkosul_yetkinlik_id": yetkinlik_id}
    )
    for _ in range(2):
        istemci.post(
            "/api/personel",
            json={
                "ad_soyad": "Test Personel",
                "sicil_no": _benzersiz("KULL"),
                "haftalik_hedef_saat": 40,
                "aktif_baslangic": "2026-01-01",
                "yetkinlik_idleri": [yetkinlik_id],
            },
        )

    kullanim = istemci.get(f"/api/yetkinlik/{yetkinlik_id}/kullanim").json()
    assert kullanim["toplam"] == 3
    assert {k["kayit_turu"]: k["sayi"] for k in kullanim["kalemler"]} == {
        "personel yetkinliği": 2,
        "görev noktası ön koşulu": 1,
    }


def test_pasif_vardiya_tipi_listede_ayirt_edilebilir(istemci: TestClient) -> None:
    """Pasif tanimlar listeden dusmez; arayuz onlari isaretleyip filtreleyebilsin
    diye `aktif` alani yanitta tasinir."""
    istek = {"ad": _benzersiz("Pasif"), **bos_vardiya_blogu(istemci)}
    with gecici_vardiya_tipi(istemci, istek) as kayit:
        vardiya_tipi_id = kayit["vardiya_tipi_id"]
        guncel = istemci.put(f"/api/vardiya-tipi/{vardiya_tipi_id}", json={"aktif": False})
        assert guncel.status_code == 200
        assert guncel.json()["aktif"] is False

        listede = next(
            v
            for v in istemci.get("/api/vardiya-tipi").json()
            if v["vardiya_tipi_id"] == vardiya_tipi_id
        )
        assert listede["aktif"] is False


def test_pasif_tanim_yeni_cozume_girmez_mevcut_surumde_gorunur() -> None:
    """Madde 1'in ikinci yarisi: "yeni çözümlerde kullanılmaz, mevcut
    kayıtlarda görünmeye devam eder".

    Cozum/on kontrol yolu baglami `yalniz_aktif=True` ile kurar (pasif tanim
    dusuru); analiz/dogrulama yolu `False` ile kurar, cunku MEVCUT bir surumun
    atamalari pasiflestirmeden onceki tanimlara referans verebilir.
    """
    from app.db import OturumYerel
    from app.models.sonuc import Donem
    from app.models.tanim import VardiyaTipi
    from app.services.baglam_kurucu import baglam_olustur

    pg_yoksa_atla()
    oturum = OturumYerel()
    try:
        donem = Donem(
            baslangic_tarihi=date(2026, 3, 2),
            bitis_tarihi=date(2026, 3, 8),
            tercih_son_tarihi=date(2026, 2, 25),
        )
        pasif = VardiyaTipi(
            ad=_benzersiz("Pasif Vardiya"),
            baslangic_saati=time(8, 0),
            bitis_saati=time(16, 0),
            sure_saat=Decimal(8),
            gece_mi=False,
            aktif=False,
        )
        oturum.add_all([donem, pasif])
        oturum.flush()

        cozum_baglami = baglam_olustur(oturum, donem)
        okuma_baglami = baglam_olustur(oturum, donem, yalniz_aktif=False)

        assert pasif.vardiya_tipi_id not in cozum_baglami.vardiya_tipleri
        assert pasif.vardiya_tipi_id in okuma_baglami.vardiya_tipleri
    finally:
        oturum.rollback()
        oturum.close()


def test_kullanim_bulunamayanda_404(istemci: TestClient) -> None:
    for yol in ("yetkinlik", "bina", "nokta", "vardiya-tipi", "personel"):
        assert istemci.get(f"/api/{yol}/999999/kullanim").status_code == 404, yol


def test_personel_bulunamayanda_404(istemci: TestClient) -> None:
    assert istemci.put("/api/personel/999999", json={"ad_soyad": "yok"}).status_code == 404
    assert istemci.delete("/api/personel/999999").status_code == 404


def test_kural_bulunamayanda_404(istemci: TestClient) -> None:
    yanit = istemci.put("/api/kural/TANIMSIZ-KIMLIK", json={"agirlik": 5})
    assert yanit.status_code == 404


def test_kural_guncelle(istemci: TestClient) -> None:
    from app.db import OturumYerel
    from app.models.kural import Kural, KuralTipi

    kimlik = _benzersiz("TEST-KURAL-FR11")
    oturum = OturumYerel()
    try:
        oturum.add(Kural(kimlik=kimlik, tip=KuralTipi.ESNEK, parametreler={}, agirlik=1))
        oturum.commit()
    finally:
        oturum.close()

    yanit = istemci.put(f"/api/kural/{kimlik}", json={"agirlik": 7, "aktif": False})
    assert yanit.status_code == 200
    govde = yanit.json()
    assert govde["agirlik"] == 7
    assert govde["aktif"] is False


# --- Personel: sicil benzersizligi ve yetkinlik kumesi ----------------------


def _personel_govdesi(**ustune: object) -> dict:
    govde: dict = {
        "ad_soyad": "Sicil Denemesi",
        "sicil_no": _benzersiz("SCL"),
        "haftalik_hedef_saat": 40,
        "aktif_baslangic": "2026-01-01",
        "yetkinlik_idleri": [],
    }
    govde.update(ustune)
    return govde


def test_ayni_sicille_ikinci_personel_409_alir(istemci: TestClient) -> None:
    """Bulgu: benzersizlik yalniz veritabani kisitindaydi ve ihlali
    yakalanmamis bir IntegrityError olarak 500 uretiyordu.

    409 secilmesi bilincli: istek bicimsel olarak gecerlidir (400 degil),
    yalnizca mevcut veriyle cakisir. Mesaj hangi sicilin cakistigini yazar,
    yoksa kullanici hangi alani duzeltecegini bilemez (NFR-5).
    """
    govde = _personel_govdesi()
    assert istemci.post("/api/personel", json=govde).status_code == 201

    yanit = istemci.post("/api/personel", json=_personel_govdesi(sicil_no=govde["sicil_no"]))
    assert yanit.status_code == 409
    assert govde["sicil_no"] in yanit.json()["detail"]


def test_guncellemede_baskasinin_sicili_409_kendi_sicili_gecerli(istemci: TestClient) -> None:
    """Kaydin KENDI sicili cakisma sayilmamalidir; aksi halde hicbir personel
    yalnizca adini degistiremezdi."""
    birinci = istemci.post("/api/personel", json=_personel_govdesi()).json()
    ikinci = istemci.post("/api/personel", json=_personel_govdesi()).json()

    cakisma = istemci.put(
        f"/api/personel/{ikinci['personel_id']}", json={"sicil_no": birinci["sicil_no"]}
    )
    assert cakisma.status_code == 409

    ayni = istemci.put(
        f"/api/personel/{ikinci['personel_id']}",
        json={"ad_soyad": "Yeni Ad", "sicil_no": ikinci["sicil_no"]},
    )
    assert ayni.status_code == 200
    assert ayni.json()["ad_soyad"] == "Yeni Ad"


def test_sicil_kirpilir(istemci: TestClient) -> None:
    """Bastaki/sondaki bosluk gorunmez; kirpilmasaydi 'AY-1' ile 'AY-1 '
    iki ayri kayit olur ve benzersizlik anlamini yitirirdi."""
    sicil = _benzersiz("KIRP")
    olusan = istemci.post("/api/personel", json=_personel_govdesi(sicil_no=f"  {sicil}  "))
    assert olusan.status_code == 201
    assert olusan.json()["sicil_no"] == sicil
    assert istemci.post("/api/personel", json=_personel_govdesi(sicil_no=sicil)).status_code == 409


def test_yetkinlik_kumesi_gonderildigi_gibi_korunur(istemci: TestClient) -> None:
    """B3'un sunucu tarafi: gonderilen TAM KUME saklanir.

    Arayuz eskiden yalnizca ilk yetkinligi gonderiyordu ve `yetkinlikleri_ayarla`
    kumeyi degistirmek yerine DEGISTIRDIGI icin ikinci yetkinlik sessizce
    siliniyordu. Sunucu sozlesmesi burada kilitleniyor: ne gonderilirse o
    kalir; alan hic gonderilmezse kume hic dokunulmadan durur.
    """
    y1 = istemci.post("/api/yetkinlik", json={"ad": _benzersiz("Y1")}).json()["yetkinlik_id"]
    y2 = istemci.post("/api/yetkinlik", json={"ad": _benzersiz("Y2")}).json()["yetkinlik_id"]

    olusan = istemci.post("/api/personel", json=_personel_govdesi(yetkinlik_idleri=[y1, y2])).json()
    assert sorted(olusan["yetkinlik_idleri"]) == sorted([y1, y2])

    # Alan gonderilmezse kume korunur.
    dokunmadan = istemci.put(
        f"/api/personel/{olusan['personel_id']}", json={"ad_soyad": "Ad Degisti"}
    ).json()
    assert sorted(dokunmadan["yetkinlik_idleri"]) == sorted([y1, y2])

    # Alan gonderilirse TAM KUME yazilir (tek eleman gondermek digerini siler).
    tek = istemci.put(
        f"/api/personel/{olusan['personel_id']}", json={"yetkinlik_idleri": [y1]}
    ).json()
    assert tek["yetkinlik_idleri"] == [y1]


def test_olmayan_personele_baglanan_hesap_400_alir() -> None:
    """B14: yabanci anahtar kisitina carpip 500 donmek yerine anlasilir 400."""
    from app.models.kimlik import Rol

    pg_yoksa_atla()
    yonetim = yetkili_istemci(Rol.YONETIM)
    yanit = yonetim.post(
        "/api/kullanici",
        json={
            "kullanici_adi": _benzersiz("hayalet").lower().replace("_", "-"),
            "parola": "yeterince-uzun-parola",
            "rol": "calisan",
            "personel_id": 999999999,
        },
    )
    assert yanit.status_code == 400
    assert "999999999" in yanit.json()["detail"]


# --- Ozel gun / resmi tatil (FR-1.10) --------------------------------------


def test_ozel_gun_isaretle_listele_guncelle_sil(istemci: TestClient) -> None:
    """FR-1.10: resmi tatiller takvimde isaretlenebilir.

    Tablo ve cozucu tarafi bastan beri vardi (baglam_kurucu ozel gunleri
    okuyor); eksik olan YAZMA yoluydu, dolayisiyla talep matrisinin
    `resmi_tatil` gun tipi hicbir zaman tetiklenemiyordu.
    """
    tarih = "2026-04-23"
    olusan = istemci.post("/api/ozel-gun", json={"tarih": tarih, "ad": "Ulusal Egemenlik"})
    assert olusan.status_code == 201
    assert olusan.json() == {"tarih": tarih, "ad": "Ulusal Egemenlik"}

    liste = istemci.get("/api/ozel-gun")
    assert liste.status_code == 200
    assert any(g["tarih"] == tarih for g in liste.json())

    yeniden = istemci.put(f"/api/ozel-gun/{tarih}", json={"ad": "23 Nisan"})
    assert yeniden.status_code == 200
    assert yeniden.json()["ad"] == "23 Nisan"

    assert istemci.delete(f"/api/ozel-gun/{tarih}").status_code == 204
    assert all(g["tarih"] != tarih for g in istemci.get("/api/ozel-gun").json())


def test_ayni_tarihi_ikinci_kez_isaretlemek_adi_gunceller(istemci: TestClient) -> None:
    """Anahtar tarihin kendisi (SDD 4.2.1): "bu tarih zaten tatil" bir
    cakisma degil, zaten istenen sonuctur. Hata dondurmek, kullaniciyi
    once silip sonra eklemeye zorlardi."""
    tarih = "2026-05-19"
    istemci.post("/api/ozel-gun", json={"tarih": tarih, "ad": "Ilk ad"})
    ikinci = istemci.post("/api/ozel-gun", json={"tarih": tarih, "ad": "Ikinci ad"})
    assert ikinci.status_code == 201
    assert ikinci.json()["ad"] == "Ikinci ad"
    assert sum(1 for g in istemci.get("/api/ozel-gun").json() if g["tarih"] == tarih) == 1
    istemci.delete(f"/api/ozel-gun/{tarih}")


def test_ozel_gun_liste_tarihe_gore_sirali(istemci: TestClient) -> None:
    """Takvim gibi okunan bir liste sirasiz donerse her tuketici kendi
    siralamasini yazar; siralama depoda, tek yerde."""
    for tarih in ("2026-08-30", "2026-01-01", "2026-10-29"):
        istemci.post("/api/ozel-gun", json={"tarih": tarih, "ad": f"Gun {tarih}"})
    tarihler = [g["tarih"] for g in istemci.get("/api/ozel-gun").json()]
    assert tarihler == sorted(tarihler)
    for tarih in ("2026-08-30", "2026-01-01", "2026-10-29"):
        istemci.delete(f"/api/ozel-gun/{tarih}")


def test_olmayan_ozel_gun_404(istemci: TestClient) -> None:
    assert istemci.delete("/api/ozel-gun/2099-01-01").status_code == 404
    assert istemci.put("/api/ozel-gun/2099-01-01", json={"ad": "x"}).status_code == 404


def test_ayni_blok_ikinci_kez_tanimlanamaz(istemci: TestClient) -> None:
    """SRS FR-1.3: ayni (baslangic_saati, sure_saat) katalogda BIR KEZ bulunur.

    Kopya blok cozumu bozmaz ama modele birbirinin yerine gecebilen
    degiskenler ekler: arama simetriyi kirmakla ugrasir, cizelgede ise iki
    blok arasindaki fark hicbir yerde gorunmez (Tur 3'te S1'in saat eksenine
    tasinmasinda ayni tuzak yasandi).
    """
    blok = bos_vardiya_blogu(istemci)
    with gecici_vardiya_tipi(istemci, {"ad": _benzersiz("Ozgun"), **blok}) as ilk:
        kopya = istemci.post("/api/vardiya-tipi", json={"ad": _benzersiz("Kopya"), **blok})
        assert kopya.status_code == 409
        # Mesaj hangi blogun cakistigini SOYLER; kullanici katalogda arayarak
        # bulmak zorunda kalmasin.
        assert ilk["ad"] in kopya.json()["detail"]

        # Kaydin KENDISI kopya sayilmaz: adini degistirip saatlerini aynen
        # birakmak mumkun olmali.
        guncel = istemci.put(
            f"/api/vardiya-tipi/{ilk['vardiya_tipi_id']}", json={"ad": _benzersiz("Ozgun-yeni")}
        )
        assert guncel.status_code == 200


def test_pasif_blok_ayni_saatte_yeni_blok_acmayi_engellemez(istemci: TestClient) -> None:
    """Pasif blok benzersizlik sayiminda YOKTUR.

    Kullanimda oldugu icin silinemeyip pasiflestirilen bir blok sayilsaydi,
    o saatlerde yeni bir blok tanimlamak KALICI olarak imkansiz hale
    gelirdi - kullanicinin duzeltebilecegi bir yol da olmazdi.
    """
    blok = bos_vardiya_blogu(istemci)
    pasif = istemci.post("/api/vardiya-tipi", json={"ad": _benzersiz("Pasiflenecek"), **blok})
    assert pasif.status_code == 201
    pasif_id = pasif.json()["vardiya_tipi_id"]
    assert istemci.put(f"/api/vardiya-tipi/{pasif_id}", json={"aktif": False}).status_code == 200

    with gecici_vardiya_tipi(istemci, {"ad": _benzersiz("Yeni"), **blok}):
        pass
    istemci.delete(f"/api/vardiya-tipi/{pasif_id}")


def test_gunluk_azamiyi_asan_blok_giriste_reddedilir(istemci: TestClient) -> None:
    """SRS FR-1.3: blok suresi gunluk azami calisma saatini asamaz.

    Deger kural katalogundan okunur (H9 Tur 4'te yazilacak); kural yoksa
    gecici varsayilan 11 saattir. Girisi gecen bir blok, cozumde her gun
    ayni ihlali uretirdi.
    """
    yanit = istemci.post(
        "/api/vardiya-tipi",
        json={
            "ad": _benzersiz("Cok Uzun"),
            "baslangic_saati": "06:00:00",
            "bitis_saati": "18:00:00",  # 12 saat
        },
    )
    # 400, 409 degil: istek mevcut veriyle cakismiyor, DEGERIN kendisi
    # gecersiz - kullanici sureyi kisaltir, baska bir saat aramaz.
    assert yanit.status_code == 400
    assert "11" in yanit.json()["detail"]


def test_azami_calisma_saati_kural_katalogundan_okunur(istemci: TestClient) -> None:
    """H9 katalogda tanimlandiginda blok kisiti onun degerini kullanir.

    Kisit ile kural ayri sayilar tasisaydi, girisi gecen bir blok cozumde
    her gun ihlal uretirdi. Test bugun H9 YOKKEN de anlamli: `parametre_getir`
    kural satirini bulamayinca gecici varsayilana duser ve kisit yine calisir.
    """
    oturum = OturumYerel()
    try:
        servis = TanimServisi(oturum)
        assert servis.azami_gunluk_calisma_saati() == Decimal(11)
    finally:
        oturum.close()


def test_devir_bakiyesi_alanlari_personel_uzerinden_yazilir(istemci: TestClient) -> None:
    """FR-1.1 devir bakiyesi: form tarafi (Tur 3 Is 5).

    Bu turda HICBIR KURAL bu alanlari okumaz; kota hesabi Tur 4'un isi.
    Test yine de gerekli: alan sema disinda kalsaydi form onu gonderir,
    sunucu sessizce yok sayardi ve kayip ancak kota hesabi yazildiginda -
    yanlis bir cizelge olarak - gorunurdu.
    """
    on_ek = _benzersiz("DEVIR")
    yanit = istemci.post(
        "/api/personel",
        json={
            "ad_soyad": "Devirli Personel",
            "sicil_no": on_ek,
            "haftalik_hedef_saat": 40,
            "aktif_baslangic": "2026-01-01",
            "devir_fazla_calisma_saat": "12.50",
            "kota_yili": 2026,
        },
    )
    assert yanit.status_code == 201
    govde = yanit.json()
    assert Decimal(govde["devir_fazla_calisma_saat"]) == Decimal("12.50")
    assert govde["kota_yili"] == 2026

    # Alan gonderilmediginde SIFIR olur, None degil: sutun NOT NULL ve
    # "devri yok" ile "devri bilinmiyor" arasinda bir ayrim tanimlanmadi.
    varsayilan = istemci.post(
        "/api/personel",
        json={
            "ad_soyad": "Devirsiz Personel",
            "sicil_no": _benzersiz("DEVIRSIZ"),
            "haftalik_hedef_saat": 40,
            "aktif_baslangic": "2026-01-01",
        },
    )
    assert varsayilan.status_code == 201
    assert Decimal(varsayilan.json()["devir_fazla_calisma_saat"]) == Decimal(0)
    assert varsayilan.json()["kota_yili"] is None

    guncel = istemci.put(
        f"/api/personel/{govde['personel_id']}", json={"devir_fazla_calisma_saat": "-3.25"}
    )
    assert guncel.status_code == 200
    # Eksi devir gecerlidir: personel kotasinin gerisinde de olabilir.
    assert Decimal(guncel.json()["devir_fazla_calisma_saat"]) == Decimal("-3.25")
