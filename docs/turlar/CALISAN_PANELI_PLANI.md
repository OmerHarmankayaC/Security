# Çalışan Paneli Düzeltmesi — Uygulama Planı

> **Ajan işçiler için:** GEREKLİ ALT BECERİ: `superpowers:subagent-driven-development`
> (önerilen) ya da `superpowers:executing-plans` ile görev görev uygulayın.
> Adımlar takip için onay kutusu (`- [ ]`) söz dizimindedir.

**Hedef:** Çalışan panelini yönetici analiziyle aynı ölçü tanımına oturtmak,
tercih formunun doğrulama boşluklarını kapatmak ve ızgara okunurluğunu düzeltmek.

**Mimari:** Dönem özeti `vardiyalarim` yükünden ayrılıp kendi uç noktasına taşınır
ve ufuk parametresini doğrudan `AnalizServisi.hesapla`ya geçirir — ikinci bir
adalet formülü yazılmaz. Tercih tekilliği veritabanı kısıtıyla garanti altına
alınır; servis, beklemedeki tercihin üstüne yazar, kararlanmışta 409 döner.

**Teknoloji:** FastAPI + SQLAlchemy 2 + Alembic (PostgreSQL), React 19 + TypeScript
+ Tailwind, Vitest + Testing Library, pytest.

**Tasarım belgesi:** [CALISAN_PANELI_TASARIM.md](CALISAN_PANELI_TASARIM.md)

## Global Kısıtlar

- Dört kanonik dokümana (`VARDIS_ProjectCharter.md`, `VARDIS_SRS.md`,
  `VARDIS_SDD.md`, `VARDIS_Backlog.md`) **dokunulmaz**. Etki doğarsa
  `PROGRESS_V2.md`'ye "DOKÜMAN BORCU" başlığı altında yazılır.
- Git: `add`, `commit`, `tag` serbest; `push` ve `remote` **asla**.
- Commit mesajları **İngilizce**; kod yorumları, arayüz metinleri ve dokümanlar
  Türkçe.
- Başarısız test silinmez — `xfail` ile ve gerekçesiyle bırakılır.
- Analiz ekranı ve `analiz_servisi.py` **kapsam dışı** (Tur 10 eş zamanlı yürüyor).
- Charter 1.5: kümülatif sapma kabul kriteri değil **göstergedir** — çalışan
  panelinin varsayılan ufku `donem`dir.
- Backend testleri canlı PostgreSQL ister; bağlanamıyorsa `pg_yoksa_atla` ile
  atlanır. "Atlandı" **geçti demek değildir**; veritabanı olmadan görev bitmiş
  sayılmaz.
- Türkçe büyütme daima `buyukHarf()` ile (`toUpperCase()` "i" harfini bozar).
- Alembic head: `b8d21f6a90c3`. Yeni göç bunun üstüne yazılır.

## Dosya Haritası

| Dosya | Sorumluluk |
|---|---|
| `backend/app/schemas/calisan.py` | `DonemOzetiOku` ufuk + adil pay alanlarını taşır; `VardiyalarimOku`dan `ozet` çıkar |
| `backend/app/services/calisan_servisi.py` | `donem_ozetim(personel_id, ufuk)`; tercih üstüne yazma kuralı |
| `backend/app/routers/calisan.py` | `GET /api/calisan/ozetim`; 409 eşlemesi |
| `backend/app/models/girdi.py` | `Tercih` tekillik kısıtı |
| `backend/app/repositories/girdi.py` | `personel_ve_tarihe_gore_getir` |
| `backend/alembic/versions/c4f1a7d20b93_*.py` | Kopya temizliği + tekillik kısıtı |
| `backend/tests/test_calisan_api.py` | Ufuk, tekillik, kapalı pencere |
| `frontend/src/api/types.ts` | `DonemOzeti` sözleşmesi |
| `frontend/src/api/client.ts` | `calisanOzetim(ufuk)` |
| `frontend/src/lib/metin.ts` | `benzersizKisaltma()` |
| `frontend/src/screens/calisan/DonemOzetimEkrani.tsx` | Ufuk seçici, adil pay kıyası, göreli eşik |
| `frontend/src/screens/calisan/TercihlerimEkrani.tsx` | Tarih sınırları, kapalı dönem, 409, onay |
| `frontend/src/screens/calisan/VardiyalarimEkrani.tsx` | Kısaltma + lejant |
| `frontend/src/components/CalisanShell.tsx` | Mobil üst çubuk + kaydırılabilir sekme |

---

### Görev 1: Dönem özeti kendi uç noktasına taşınır

**Dosyalar:**
- Değiştir: `backend/app/schemas/calisan.py:61-100`
- Değiştir: `backend/app/services/calisan_servisi.py:48-230`
- Değiştir: `backend/app/routers/calisan.py:22-41`
- Test: `backend/tests/test_calisan_api.py`

**Arayüzler:**
- Kullanır: `AnalizServisi.hesapla(surum_id: int, ufuk: str = "donem") -> AnalizOku | None`;
  `KisiSayisiOku(personel_id, ad_soyad, sayi, pay: float | None)`;
  `SaatDengesiOku(personel_id, ad_soyad, toplam_saat, hedef_saat, sapma)`
- Üretir: `GET /api/calisan/ozetim?ufuk=donem|adalet` → `DonemOzetiOku | None`;
  `CalisanServisi.donem_ozetim(personel_id: int, ufuk: str = "donem") -> DonemOzetiOku | None`

**Kararlar (uygulayan bunları değiştirmez):**
- Özet yoksa (aktif dönem yok / yayınlanmış sürüm yok) uç nokta **200 + `null`**
  döner, 404 değil. 404 "personel yok" demektir ve panel zaten `vardiyalarim`
  çağrısında o duruma düşer; iki ayrı yokluğu tek koda bindirmek arayüzde
  "veri gelmedi" ile "henüz çizelge yok" ayrımını siler.
- `ekip_ortalama_*` alanları **kalır** — ikincil bağlam olarak gösterilecek.
  Kıyasın referansı `adil_pay_*`tır.

- [ ] **Adım 1: Şemayı genişlet**

`backend/app/schemas/calisan.py` — `DonemOzetiOku`ya alanları ekle:

```python
class DonemOzetiOku(BaseModel):
    """FR-9.5: ... (mevcut docstring korunur, altına eklenir)

    KIYASIN REFERANSI ADIL PAYDIR, ekip ortalamasi degil. Erisilebilirligi
    kisitli bir havuz tek ortalamaya vuruldugunda kalici olarak sapmali
    gorunur (bkz. schemas/analiz.py, KisiSayisiOku.pay). Ekip ortalamasi
    ikincil baglam olarak tasinmaya devam eder.

    `ufuk` YANITIN ICINDE tasinir: iki ufkun sayilari farklidir ve hangisinin
    okundugu belirsiz kalirsa sayi yanlis okunur (SDD 6.3.4).
    """

    ufuk: Literal["donem", "adalet"] = "donem"
    gece_saati: float
    ekip_ortalama_gece: float
    adil_pay_gece: float | None
    gece_havuzunda: bool
    hafta_sonu_saati: float
    ekip_ortalama_hafta_sonu: float
    adil_pay_hafta_sonu: float | None
    hafta_sonu_havuzunda: bool
    toplam_saat: float
    ekip_ortalama_saat: float
    hedef_saat: float
```

`VardiyalarimOku`dan `ozet: DonemOzetiOku | None` satırını **sil** ve yerine
yorum bırak:

```python
    siradaki: VardiyamOku | None
    # `ozet` BURADA DEGIL: /api/calisan/ozetim uc noktasinda. Ozet bir tam
    # AnalizServisi.hesapla() odemesi ve panelin her acilisi onu odemek
    # zorunda degil - calisan Vardiyalarim sekmesine bakarken hesap hic
    # calismaz.
```

- [ ] **Adım 2: Servisi ufka aç**

`calisan_servisi.py` — `vardiyalarim` dönüşünden `ozet=self._donem_ozeti(...)`
satırını çıkar (ve `bos` sözlüğündeki `ozet=None` satırını da). `_donem_ozeti`yi
imzasıyla birlikte değiştir ve üstüne yeni ortak yöntemi ekle:

```python
    def donem_ozetim(
        self, personel_id: int, ufuk: str = "donem", *, bugun: date | None = None
    ) -> DonemOzetiOku | None:
        """FR-9.5 ozetinin kendi uc noktasi. `ufuk` dogrudan AnalizServisi'ne
        gecer - ikinci bir adalet formulu YAZILMAZ, tanim tek yerde kalir.

        None: aktif donem yok, yayinlanmis surum yok ya da analiz hesaplanamadi.
        Personel yoklugu burada AYRISTIRILMAZ; panel o duruma vardiyalarim
        cagrisinda zaten duser."""
        bugun = bugun if bugun is not None else date.today()
        donem = self.donem.guncel_donemi_bul(bugun)
        if donem is None:
            return None
        yayinlanan = self.surum.yayinlanan_getir(donem.donem_id)
        if yayinlanan is None:
            return None
        return self._donem_ozeti(personel_id, yayinlanan.surum_id, ufuk)

    def _donem_ozeti(
        self, personel_id: int, surum_id: int, ufuk: str = "donem"
    ) -> DonemOzetiOku | None:
```

Gövdede `hesapla` çağrısını ve dönüşü değiştir:

```python
        analiz = AnalizServisi(self.oturum).hesapla(surum_id, ufuk)
```

```python
        return DonemOzetiOku(
            ufuk=ufuk,
            gece_saati=gece,
            ekip_ortalama_gece=ekip_gece,
            adil_pay_gece=gece_kaydi.pay if gece_kaydi is not None else None,
            gece_havuzunda=gece_kaydi is not None,
            hafta_sonu_saati=hs,
            ekip_ortalama_hafta_sonu=ekip_hs,
            adil_pay_hafta_sonu=hs_kaydi.pay if hs_kaydi is not None else None,
            hafta_sonu_havuzunda=hs_kaydi is not None,
            toplam_saat=saat.toplam_saat if saat is not None else 0.0,
            ekip_ortalama_saat=ekip_saat,
            hedef_saat=saat.hedef_saat if saat is not None else 0.0,
        )
```

- [ ] **Adım 3: Uç noktayı ekle**

`routers/calisan.py` — `DonemOzetiOku` importunu ekle ve `/vardiyalarim`ın
altına:

```python
@router.get("/ozetim", response_model=DonemOzetiOku | None)
def ozetim_getir(
    personel_id: Personel,
    oturum: Oturum,
    ufuk: Literal["donem", "adalet"] = "donem",
) -> DonemOzetiOku | None:
    """FR-9.5. `ufuk` olculerin hangi pencereden okundugunu secer (SDD 6.3.4).

    Ozet yoksa 200 + null doner: "henuz cizelge yok" bir hata degil bir
    durumdur ve arayuz onu kendi metniyle anlatir."""
    return CalisanServisi(oturum).donem_ozetim(personel_id, ufuk)
```

`from typing import Annotated, Literal` olarak importu genişlet.

- [ ] **Adım 4: Başarısız testi yaz**

`backend/tests/test_calisan_api.py` sonuna:

```python
def test_ozetim_ufku_yaniti_icinde_tasir() -> None:
    """SDD 6.3.4: hangi ufkun okundugu yanitin icinde durur; iki ufkun
    sayilari farklidir ve belirsiz kalirsa sayi yanlis okunur."""
    pg_yoksa_atla()
    with OturumYerel() as oturum:
        _temizle(oturum)
        personel_id = _senaryo_kur(oturum)
    istemci = _calisan_istemcisi(personel_id)

    donem_yaniti = istemci.get("/api/calisan/ozetim")
    adalet_yaniti = istemci.get("/api/calisan/ozetim?ufuk=adalet")

    assert donem_yaniti.status_code == 200
    assert donem_yaniti.json()["ufuk"] == "donem"
    assert adalet_yaniti.json()["ufuk"] == "adalet"


def test_ozetim_yayin_yoksa_null_doner() -> None:
    """404 DEGIL: "henuz cizelge yok" bir hata degil bir durumdur."""
    pg_yoksa_atla()
    with OturumYerel() as oturum:
        _temizle(oturum)
        personel = Personel(
            ad_soyad=_benzersiz("Ozetsiz"),
            sicil_no=_benzersiz("S"),
            haftalik_hedef_saat=40,
            aktif_baslangic=BUGUN - timedelta(days=30),
        )
        oturum.add(personel)
        oturum.commit()
        personel_id = personel.personel_id
    istemci = _calisan_istemcisi(personel_id)

    yanit = istemci.get("/api/calisan/ozetim")

    assert yanit.status_code == 200
    assert yanit.json() is None


def test_vardiyalarim_artik_ozet_tasimaz() -> None:
    """Ozet ayri uc noktada; panelin her acilisi bir tam hesapla() odemez."""
    pg_yoksa_atla()
    with OturumYerel() as oturum:
        _temizle(oturum)
        personel_id = _senaryo_kur(oturum)
    istemci = _calisan_istemcisi(personel_id)

    yanit = istemci.get("/api/calisan/vardiyalarim")

    assert yanit.status_code == 200
    assert "ozet" not in yanit.json()
```

`_senaryo_kur(oturum) -> int` dosyada zaten var mı diye bak: yoksa mevcut
testlerdeki kurulum bloğunu (personel + dönem + görev noktası + talep +
yayınlanmış sürüm + atama) tek yardımcıya çıkar ve **mevcut testleri de ona
bağla** — aynı kurulumun dördüncü kopyası yazılmaz.

- [ ] **Adım 5: Testi çalıştır, düştüğünü gör**

```bash
cd backend && pytest tests/test_calisan_api.py -v -k "ozetim or ozet_tasimaz"
```

Beklenen: `404` (uç nokta yok) ve `KeyError`/`assert` düşüşleri. "Atlandı"
çıkıyorsa PostgreSQL ayakta değil — görev bu hâlde bitmiş sayılmaz.

- [ ] **Adım 6: Adım 1–3'ü uygula, testleri çalıştır**

```bash
cd backend && pytest tests/test_calisan_api.py -v
```

Beklenen: hepsi PASS. `ozet` alanını okuyan eski testler varsa yeni uç noktaya
taşınır (silinmez).

- [ ] **Adım 7: Commit**

```bash
git add backend/app/schemas/calisan.py backend/app/services/calisan_servisi.py backend/app/routers/calisan.py backend/tests/test_calisan_api.py
git commit -m "feat(calisan): move the period summary to its own endpoint with a horizon parameter"
```

---

### Görev 2: Tercih tekilliği ve üstüne yazma

**Dosyalar:**
- Değiştir: `backend/app/models/girdi.py:49-63`
- Değiştir: `backend/app/repositories/girdi.py:17-24`
- Değiştir: `backend/app/services/calisan_servisi.py:316-353`
- Değiştir: `backend/app/routers/calisan.py:52-62`
- Oluştur: `backend/alembic/versions/c4f1a7d20b93_tercih_gun_tekilligi.py`
- Test: `backend/tests/test_calisan_api.py`

**Arayüzler:**
- Kullanır: `TabanDepo.olustur(**alanlar)`, `TabanDepo.guncelle(id_, **alanlar)`
- Üretir: `TercihDeposu.personel_ve_tarihe_gore_getir(personel_id: int, tarih: date) -> Tercih | None`;
  `TercihKararlanmisError`; POST `/api/calisan/tercih` artık 409 de dönebilir

- [ ] **Adım 1: Başarısız testleri yaz**

```python
def test_ayni_gune_ikinci_tercih_beklemedekinin_uzerine_yazar() -> None:
    """Calisan fikrini degistirebilir; ayni gun icin iki celiskili tercih
    (calismam + 08-16 calisirim) yan yana duramaz."""
    pg_yoksa_atla()
    with OturumYerel() as oturum:
        _temizle(oturum)
        personel_id = _senaryo_kur(oturum)
    istemci = _calisan_istemcisi(personel_id)
    hedef = (BUGUN + timedelta(days=1)).isoformat()

    ilk = istemci.post("/api/calisan/tercih", json={"tarih": hedef, "tip": "CALISMAMA"})
    ikinci = istemci.post(
        "/api/calisan/tercih",
        json={
            "tarih": hedef,
            "tip": "ZAMAN_ARALIGI_TERCIHI",
            "tercih_baslangic": "08:00:00",
            "tercih_bitis": "16:00:00",
        },
    )

    assert ilk.status_code == 201
    assert ikinci.status_code == 201
    assert ikinci.json()["tercih_id"] == ilk.json()["tercih_id"]
    liste = istemci.get("/api/calisan/tercih").json()["tercihler"]
    assert len([t for t in liste if t["tarih"] == hedef]) == 1


def test_kararlanmis_tercihin_uzerine_yazilmaz() -> None:
    """Yonetici karari sessizce silinmez (409)."""
    pg_yoksa_atla()
    with OturumYerel() as oturum:
        _temizle(oturum)
        personel_id = _senaryo_kur(oturum)
        hedef_tarih = BUGUN + timedelta(days=1)
        donem = oturum.query(Donem).first()
        oturum.add(
            Tercih(
                personel_id=personel_id,
                donem_id=donem.donem_id,
                tarih=hedef_tarih,
                tip=TercihTipi.CALISMAMA,
                durum=TercihDurumu.ONAYLANDI,
            )
        )
        oturum.commit()
    istemci = _calisan_istemcisi(personel_id)

    yanit = istemci.post(
        "/api/calisan/tercih",
        json={"tarih": hedef_tarih.isoformat(), "tip": "CALISMAMA"},
    )

    assert yanit.status_code == 409
```

`TercihTipi`/`TercihDurumu` değerlerinin gövdedeki yazımını mevcut testlerden
doğrula (`_benzersiz` kullanan bloklar) — enum adı farklıysa oradaki yazımı kullan.

- [ ] **Adım 2: Testleri çalıştır, düştüklerini gör**

```bash
cd backend && pytest tests/test_calisan_api.py -v -k "ayni_gune or kararlanmis"
```

Beklenen: ikinci POST 201 dönüyor ama **yeni** `tercih_id` ile (ilk test düşer);
kararlanmış durumda 409 yerine 201 (ikinci test düşer).

- [ ] **Adım 3: Modele kısıtı ekle**

`models/girdi.py` — `Tercih` sınıfının başına:

```python
class Tercih(Base, ZamanDamgasiKarisimi):
    __tablename__ = "tercih"
    # Bir calisan bir gun icin TEK tercih bildirir. Iki kayit, biri
    # "calismam" digeri "08-16 calisirim" oldugunda hangisinin gecerli
    # oldugu tanimsiz kalirdi; ikisi de onaylanabilirdi.
    __table_args__ = (
        UniqueConstraint("personel_id", "tarih", name="uq_tercih_personel_tarih"),
    )
```

`from sqlalchemy import ..., UniqueConstraint` importunu genişlet.

- [ ] **Adım 4: Depo yöntemini ekle**

`repositories/girdi.py` — `TercihDeposu` içine:

```python
    def personel_ve_tarihe_gore_getir(self, personel_id: int, tarih: date) -> Tercih | None:
        """Tekillik kisitinin okuma tarafi: o gunun tercihi (varsa)."""
        stmt = select(Tercih).where(
            Tercih.personel_id == personel_id, Tercih.tarih == tarih
        )
        return self.oturum.execute(stmt).scalars().one_or_none()
```

`from datetime import date` importunu gerekiyorsa ekle.

- [ ] **Adım 5: Göçü yaz**

`backend/alembic/versions/c4f1a7d20b93_tercih_gun_tekilligi.py`:

```python
"""tercih tablosunda (personel_id, tarih) tekilligi

Revision ID: c4f1a7d20b93
Revises: b8d21f6a90c3
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c4f1a7d20b93"
down_revision: str | Sequence[str] | None = "b8d21f6a90c3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    baglanti = op.get_bind()
    # (a) SAYIM once ve GORUNUR: kac satirin gidecegi bilinmeden kisit
    # konulmaz. Cikti dagitim gunlugune ve PROGRESS_V2'ye gecer.
    kopyalar = baglanti.execute(
        sa.text(
            "SELECT personel_id, tarih, count(*) AS adet FROM tercih "
            "GROUP BY personel_id, tarih HAVING count(*) > 1 ORDER BY personel_id, tarih"
        )
    ).fetchall()
    for satir in kopyalar:
        print(
            f"[goc c4f1a7d20b93] kopya: personel={satir.personel_id} "
            f"tarih={satir.tarih} adet={satir.adet}"
        )
    # (b) Her (personel, tarih) icin EN YENI kayit kalir.
    silinen = baglanti.execute(
        sa.text(
            "DELETE FROM tercih t USING tercih y "
            "WHERE t.personel_id = y.personel_id AND t.tarih = y.tarih "
            "AND t.tercih_id < y.tercih_id RETURNING t.tercih_id"
        )
    ).fetchall()
    print(f"[goc c4f1a7d20b93] silinen kopya satir: {len(silinen)} -> {[s.tercih_id for s in silinen]}")
    # (c) Kisit en sona: temizlik yapilmadan konulursa goc patlardi.
    op.create_unique_constraint("uq_tercih_personel_tarih", "tercih", ["personel_id", "tarih"])


def downgrade() -> None:
    # Silinen kopyalar GERI GELMEZ; downgrade yalniz kisiti kaldirir.
    op.drop_constraint("uq_tercih_personel_tarih", "tercih", type_="unique")
```

- [ ] **Adım 6: Göçü yerelde uygula**

```bash
cd backend && alembic upgrade head && alembic current
```

Beklenen: `c4f1a7d20b93 (head)`. Kopya varsa `[goc c4f1a7d20b93]` satırları
görünür — çıktıyı sakla, Görev 8'de `PROGRESS_V2.md`'ye geçecek.

- [ ] **Adım 7: Servis kuralını yaz**

`calisan_servisi.py` — dosyanın üstüne hata sınıfını ekle:

```python
class TercihKararlanmisError(Exception):
    """O gun icin zaten KARARLANMIS (onaylanmis/reddedilmis) bir tercih var;
    ustune yazmak yonetici kararini sessizce silerdi (router 409'a cevirir)."""
```

`tercih_bildir` içinde, dönem denetimlerinden sonra `self.tercih.olustur(...)`
çağrısını şununla değiştir:

```python
        mevcut = self.tercih.personel_ve_tarihe_gore_getir(personel_id, veri.tarih)
        if mevcut is not None:
            if mevcut.durum is not TercihDurumu.BEKLEMEDE:
                raise TercihKararlanmisError(
                    "Bu gun icin kararlanmis bir tercihin var; degistirmek icin yoneticine basvur"
                )
            kayit = self.tercih.guncelle(
                mevcut.tercih_id,
                tip=veri.tip,
                tercih_baslangic=veri.tercih_baslangic,
                tercih_bitis=veri.tercih_bitis,
                calisan_notu=veri.calisan_notu,
            )
            assert kayit is not None  # az once okundu
        else:
            kayit = self.tercih.olustur(
                personel_id=personel_id,
                donem_id=donem.donem_id,
                tarih=veri.tarih,
                tip=veri.tip,
                tercih_baslangic=veri.tercih_baslangic,
                tercih_bitis=veri.tercih_bitis,
                calisan_notu=veri.calisan_notu,
            )
```

- [ ] **Adım 8: Router'a 409'u ekle**

`routers/calisan.py` — importu genişlet
(`from app.services.calisan_servisi import CalisanServisi, TercihDonemiBulunamadiError, TercihKararlanmisError`)
ve `tercih_bildir` gövdesine ikinci `except` ekle:

```python
    except TercihKararlanmisError as hata:
        raise HTTPException(status_code=409, detail=str(hata)) from hata
```

- [ ] **Adım 9: Testleri çalıştır**

```bash
cd backend && pytest tests/test_calisan_api.py -v
```

Beklenen: hepsi PASS.

- [ ] **Adım 10: Commit**

```bash
git add backend/app/models/girdi.py backend/app/repositories/girdi.py backend/app/services/calisan_servisi.py backend/app/routers/calisan.py backend/alembic/versions/c4f1a7d20b93_tercih_gun_tekilligi.py backend/tests/test_calisan_api.py
git commit -m "feat(calisan): enforce one preference per day and overwrite pending ones"
```

---

### Görev 3: Frontend sözleşmesi

**Dosyalar:**
- Değiştir: `frontend/src/api/types.ts:558-588`
- Değiştir: `frontend/src/api/client.ts:296-312`

**Arayüzler:**
- Kullanır: Görev 1'in `DonemOzetiOku` alanları; mevcut `Ufuk = 'donem' | 'adalet'`
- Üretir: `api.calisanOzetim(ufuk?: Ufuk): Promise<DonemOzeti | null>`

- [ ] **Adım 1: Tipleri güncelle**

`types.ts` — `DonemOzeti`ye ekle, `Vardiyalarim`dan `ozet`i çıkar:

```ts
export interface DonemOzeti {
  /** Hangi ufkun okunduğu (SDD 6.3.4); yanıtın içinde taşınır. */
  ufuk: Ufuk
  /** Birim SAAT (SRS S2, S3). */
  gece_saati: number
  ekip_ortalama_gece: number
  /** KIYASIN REFERANSI: kişiye düşen adil pay. Havuz dışındaysa null. */
  adil_pay_gece: number | null
  gece_havuzunda: boolean
  hafta_sonu_saati: number
  ekip_ortalama_hafta_sonu: number
  adil_pay_hafta_sonu: number | null
  hafta_sonu_havuzunda: boolean
  toplam_saat: number
  ekip_ortalama_saat: number
  hedef_saat: number
}
```

- [ ] **Adım 2: İstemciye uç noktayı ekle**

`client.ts`, `calisanVardiyalarim`ın hemen altına:

```ts
  // Özet ayrı çağrıdır: bir tam analiz hesabı ödediği için Dönem Özetim
  // sekmesi açılmadan çalışmaz. `null` = henüz yayınlanmış çizelge yok.
  calisanOzetim: (ufuk: Ufuk = 'donem') =>
    istek<DonemOzeti | null>(`/api/calisan/ozetim?ufuk=${ufuk}`),
```

`DonemOzeti` tipini import listesine ekle.

- [ ] **Adım 3: Derlemeyi doğrula**

```bash
cd frontend && npx tsc -b
```

Beklenen: `DonemOzetimEkrani.tsx`'in `veri.ozet` okuduğu satırda hata — bir
sonraki görev onu düzeltiyor. Başka dosyada hata **olmamalı**.

- [ ] **Adım 4: Commit** (Görev 4 ile birlikte commit'lenir; burada commit yok)

---

### Görev 4: Dönem Özetim ekranı

**Dosyalar:**
- Değiştir: `frontend/src/screens/calisan/DonemOzetimEkrani.tsx` (tamamı)
- Oluştur: `frontend/src/screens/calisan/DonemOzetimEkrani.test.tsx`

**Arayüzler:**
- Kullanır: `api.calisanOzetim(ufuk)`, `DonemOzeti`, `Vardiyalarim`
- Üretir: `DonemOzetimEkrani({ veri }: { veri: Vardiyalarim })` — prop imzası
  DEĞİŞMEZ, `CalisanApp` dokunulmadan çalışır

**Kararlar:**
- Eşik: `Math.max(0.5, referans * 0.05)` — 90 günlük sayılarda 0,5 saat herkesi
  "sapmış" gösterir.
- Kıyas referansı `adil_pay_*` (null ise ekip ortalamasına düşer); ekip
  ortalaması kartta ikincil satır olarak durur.

- [ ] **Adım 1: Başarısız testleri yaz**

`DonemOzetimEkrani.test.tsx`:

```tsx
/**
 * Dönem Özetim ekranı (SDD 6.1, FR-9.5).
 *
 * BU TESTLER GÖRSEL DOĞRULAMANIN YERİNE GEÇMEZ; ölçülen şey davranış —
 * hangi ufkun çekildiği, kıyasın hangi sayıya göre yapıldığı, havuz dışı
 * metinlerin ne dediği.
 */
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { DonemOzeti, Vardiyalarim } from '@/api/types'

import { DonemOzetimEkrani } from './DonemOzetimEkrani'

let _ozet: DonemOzeti | null
const calisanOzetim = vi.fn()

vi.mock('@/api/client', () => ({
  api: {
    calisanOzetim: (...a: unknown[]) => {
      calisanOzetim(...a)
      return Promise.resolve(_ozet)
    },
  },
}))

const VERI = {
  donem_baslangic_tarihi: '2026-08-17',
  donem_bitis_tarihi: '2026-08-23',
} as Vardiyalarim

const OZET: DonemOzeti = {
  ufuk: 'donem',
  gece_saati: 24,
  ekip_ortalama_gece: 20,
  adil_pay_gece: 16,
  gece_havuzunda: true,
  hafta_sonu_saati: 8,
  ekip_ortalama_hafta_sonu: 8,
  adil_pay_hafta_sonu: 8,
  hafta_sonu_havuzunda: true,
  toplam_saat: 160,
  ekip_ortalama_saat: 158,
  hedef_saat: 160,
}

afterEach(() => {
  cleanup()
  calisanOzetim.mockClear()
})

describe('DonemOzetimEkrani', () => {
  it('açılışta dönem ufkunu çeker', async () => {
    _ozet = OZET
    render(<DonemOzetimEkrani veri={VERI} />)
    await waitFor(() => expect(calisanOzetim).toHaveBeenCalledWith('donem'))
  })

  it('ufuk değişince adalet ufkunu çeker', async () => {
    _ozet = OZET
    render(<DonemOzetimEkrani veri={VERI} />)
    await screen.findByText(/Gece Saati/i)
    fireEvent.click(screen.getByRole('button', { name: /90 gün/i }))
    await waitFor(() => expect(calisanOzetim).toHaveBeenCalledWith('adalet'))
  })

  it('kıyası adil paya göre kurar, ekip ortalamasına göre değil', async () => {
    // gece: sen 24, adil pay 16 -> 8 saat ÜSTÜNDE. Ekip ortalaması 20 olsaydı
    // fark 4 saat olurdu; hangi referansın kullanıldığı metinden okunur.
    _ozet = OZET
    render(<DonemOzetimEkrani veri={VERI} />)
    expect(await screen.findByText(/8,0 saat üzerindesin/)).toBeTruthy()
  })

  it('eşik göreli: adil payın %5 altındaki fark sapma sayılmaz', async () => {
    // toplam: sen 160, hedef 160 -> fark 0. Hafta sonu 8 vs 8 -> fark 0.
    // gece payı 100, sen 103 -> fark 3 < 5 (100 * %5) -> "yakınsın".
    _ozet = { ...OZET, gece_saati: 103, adil_pay_gece: 100 }
    render(<DonemOzetimEkrani veri={VERI} />)
    expect(await screen.findByText(/gece saatinde ortalamaya yakınsın/)).toBeTruthy()
  })

  it('özet yoksa çizelge olmadığını söyler', async () => {
    _ozet = null
    render(<DonemOzetimEkrani veri={VERI} />)
    expect(await screen.findByText(/henüz yayınlanmış bir çizelge yok/i)).toBeTruthy()
  })

  it('havuz dışındaki karşılaştırmayı hiç göstermez', async () => {
    _ozet = { ...OZET, gece_havuzunda: false, adil_pay_gece: null }
    render(<DonemOzetimEkrani veri={VERI} />)
    await screen.findByText(/Hafta Sonu/i)
    expect(screen.queryByText(/Gece Saati/i)).toBeNull()
    expect(screen.getByText(/gece vardiyası bulunmadığı için/i)).toBeTruthy()
  })
})
```

- [ ] **Adım 2: Testleri çalıştır, düştüklerini gör**

```bash
cd frontend && npx vitest run src/screens/calisan/DonemOzetimEkrani.test.tsx
```

Beklenen: FAIL — `calisanOzetim` hiç çağrılmıyor (ekran hâlâ `veri.ozet` okuyor).

- [ ] **Adım 3: Ekranı yeniden yaz**

`DonemOzetimEkrani.tsx` — üst kısım (kalan `MetrikKarti`/`BarSatiri` yapısı
korunur, yalnız referans ve eşik değişir):

```tsx
import { useEffect, useState } from 'react'
import { api } from '@/api/client'
import type { DonemOzeti, Ufuk, Vardiyalarim } from '@/api/types'
import { Kart, KartEtiketi, Rozet } from '@/components/app-ui'
import { donemAraligiBicimle } from '@/lib/tarih'
import { sayiBicimle } from '@/lib/sayi'
import { cn } from '@/lib/utils'

interface Props {
  veri: Vardiyalarim
}

// Eşik MUTLAK DEĞİL GÖRELİ: adalet ufkunda sayılar doksan günü kapsar ve
// sabit 0,5 saat herkesi "sapmış" gösterirdi. Taban 0,5 saat, dönem ufkunda
// önceki davranışı korur.
function esik(referans: number): number {
  return Math.max(0.5, Math.abs(referans) * 0.05)
}

function karsilastirmaMetni(sen: number, referans: number, birim: string): string {
  const fark = sen - referans
  if (Math.abs(fark) < esik(referans)) return 'ortalamaya yakınsın'
  return fark > 0
    ? `adil payının ${sayiBicimle(Math.abs(fark), 1)} ${birim} üzerindesin`
    : `adil payının ${sayiBicimle(Math.abs(fark), 1)} ${birim} altındasın`
}
```

Gövde:

```tsx
export function DonemOzetimEkrani({ veri }: Props) {
  const [ufuk, setUfuk] = useState<Ufuk>('donem')
  const [ozet, setOzet] = useState<DonemOzeti | null>(null)
  const [yukleniyor, setYukleniyor] = useState(true)

  useEffect(() => {
    setYukleniyor(true)
    api
      .calisanOzetim(ufuk)
      .then(setOzet)
      .catch(() => setOzet(null))
      .finally(() => setYukleniyor(false))
  }, [ufuk])

  return (
    <>
      <UfukAnahtari ufuk={ufuk} sec={setUfuk} />
      {yukleniyor && ozet === null ? null : ozet === null ? (
        <Kart>
          <p className="m-0 text-sm text-ink-muted">
            Bu dönem için henüz yayınlanmış bir çizelge yok, özet hesaplanamıyor.
          </p>
        </Kart>
      ) : (
        <Ozet veri={veri} ozet={ozet} ufuk={ufuk} />
      )}
    </>
  )
}
```

`UfukAnahtari` — yönetici analiziyle **aynı** iki düğmeli desen
(`AnalizEkrani.tsx:320-353`), etiketleri çalışan diline çevrilmiş:

```tsx
function UfukAnahtari({ ufuk, sec }: { ufuk: Ufuk; sec: (u: Ufuk) => void }) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex gap-1" role="group" aria-label="Ölçüm ufku">
        {(
          [
            ['donem', 'Bu Dönem'],
            ['adalet', 'Son 90 Gün'],
          ] as const
        ).map(([deger, etiket]) => (
          <button
            key={deger}
            type="button"
            aria-pressed={ufuk === deger}
            onClick={() => sec(deger)}
            className={cn(
              'h-8 rounded-sm border px-3 text-sm',
              ufuk === deger
                ? 'border-accent bg-accent-soft font-medium text-accent'
                : 'border-rule bg-surface text-ink-muted',
            )}
          >
            {etiket}
          </button>
        ))}
      </div>
      <p className="m-0 text-sm text-ink-muted">
        {ufuk === 'donem'
          ? 'Sayılar yalnızca bu dönemi kapsar.'
          : 'Sayılar son doksan günü kapsar; geçmiş yayınlanmış çizelgeler dahil.'}
      </p>
    </div>
  )
}
```

`Ozet` bileşeni bugünkü gövdenin aynısıdır, üç değişiklikle:
`cumleler` referans olarak `ozet.adil_pay_gece ?? ozet.ekip_ortalama_gece`,
`ozet.adil_pay_hafta_sonu ?? ozet.ekip_ortalama_hafta_sonu` ve `ozet.hedef_saat`
kullanır; `MetrikKarti` iki bar yerine **SEN / ADİL PAY** çizer ve altına
`ekip ortalaması {sayiBicimle(ekip, 1)} sa` satırı koyar; başlıktaki dönem
etiketi `ufuk === 'adalet'` iken `SON 90 GÜN` yazar.

- [ ] **Adım 4: Testleri çalıştır**

```bash
cd frontend && npx vitest run src/screens/calisan/DonemOzetimEkrani.test.tsx && npx tsc -b
```

Beklenen: 6 test PASS, tsc temiz.

- [ ] **Adım 5: Commit**

```bash
git add frontend/src/api/types.ts frontend/src/api/client.ts frontend/src/screens/calisan/DonemOzetimEkrani.tsx frontend/src/screens/calisan/DonemOzetimEkrani.test.tsx
git commit -m "feat(calisan): let the period summary follow the selected horizon and compare against the fair share"
```

---

### Görev 5: Tercihlerim formu

**Dosyalar:**
- Değiştir: `frontend/src/screens/calisan/TercihlerimEkrani.tsx`
- Oluştur: `frontend/src/screens/calisan/TercihlerimEkrani.test.tsx`

**Arayüzler:**
- Kullanır: `api.calisanTercihlerim()`, `api.calisanTercihBildir(govde)`,
  `ApiHatasi` (`status: number` taşır), `CalisanTercihListesi`
- Üretir: yok (yaprak ekran)

- [ ] **Adım 1: Başarısız testleri yaz**

`TercihlerimEkrani.test.tsx`:

```tsx
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { CalisanTercihListesi } from '@/api/types'

import { TercihlerimEkrani } from './TercihlerimEkrani'

let _liste: CalisanTercihListesi
let _hata: unknown = null
const bildir = vi.fn()

vi.mock('@/api/client', () => ({
  api: {
    calisanTercihlerim: () => Promise.resolve(_liste),
    calisanTercihBildir: (...a: unknown[]) => {
      bildir(...a)
      return _hata ? Promise.reject(_hata) : Promise.resolve({})
    },
  },
  ApiHatasi: class extends Error {
    status: number
    constructor(status: number, mesaj: string) {
      super(mesaj)
      this.status = status
    }
  },
}))

const ACIK: CalisanTercihListesi = {
  acik_donem: {
    donem_id: 1,
    baslangic_tarihi: '2099-01-05',
    bitis_tarihi: '2099-01-11',
    tercih_son_tarihi: '2099-01-01',
  },
  tercihler: [],
}

afterEach(() => {
  cleanup()
  bildir.mockClear()
  _hata = null
})

describe('TercihlerimEkrani', () => {
  it('tarih alanını açık dönemle sınırlar', async () => {
    _liste = ACIK
    render(<TercihlerimEkrani />)
    const alan = (await screen.findByLabelText(/gün/i)) as HTMLInputElement
    expect(alan.max).toBe('2099-01-11')
    // Alt sınır bugünden önce olamaz; dönem geleceğe düştüğü için başlangıç.
    expect(alan.min).toBe('2099-01-05')
  })

  it('açık dönem yoksa formu hiç göstermez', async () => {
    _liste = { acik_donem: null, tercihler: [] }
    render(<TercihlerimEkrani />)
    expect(await screen.findByText(/tercihe açık bir dönem yok/i)).toBeTruthy()
    expect(screen.queryByRole('button', { name: /Tercihi Gönder/i })).toBeNull()
  })

  it('başarılı gönderimde onay gösterir', async () => {
    _liste = ACIK
    render(<TercihlerimEkrani />)
    fireEvent.click(await screen.findByRole('button', { name: /Tercihi Gönder/i }))
    expect(await screen.findByText(/tercihin alındı/i)).toBeTruthy()
  })

  it('409 gelince yöneticiye başvurmayı söyler', async () => {
    _liste = ACIK
    const { ApiHatasi } = await import('@/api/client')
    _hata = new (ApiHatasi as never)(409, 'kararlanmis')
    render(<TercihlerimEkrani />)
    fireEvent.click(await screen.findByRole('button', { name: /Tercihi Gönder/i }))
    expect(await screen.findByText(/yöneticine başvur/i)).toBeTruthy()
  })

  it('tüm gün seçimini açıkça yazar', async () => {
    _liste = ACIK
    render(<TercihlerimEkrani />)
    fireEvent.click(await screen.findByRole('button', { name: /Şu saatlerde/i }))
    const bitis = screen.getByLabelText(/bitiş/i)
    fireEvent.change(bitis, { target: { value: '8' } })
    expect(await screen.findByText(/tüm gün \(24 saat\)/i)).toBeTruthy()
  })
})
```

- [ ] **Adım 2: Testleri çalıştır, düştüklerini gör**

```bash
cd frontend && npx vitest run src/screens/calisan/TercihlerimEkrani.test.tsx
```

Beklenen: beş test de FAIL (etiket bağı yok, sınır yok, onay yok).

- [ ] **Adım 3: Formu düzelt**

Değişiklikler:

1. Etiketleri alanlara bağla — `<label htmlFor>` + `id` (testler `getByLabelText`
   kullanıyor; erişilebilirlik için de gerekli).
2. Tarih sınırları:

```tsx
  const acik = liste.acik_donem
  // Alt sınır: dönem başlangıcı ile bugünün BÜYÜĞÜ — geçmiş bir güne tercih
  // bildirmenin anlamı yok, dönem gelecekteyse de başlangıçtan önce gün yok.
  const enErken = acik
    ? acik.baslangic_tarihi > bugun
      ? acik.baslangic_tarihi
      : bugun
    : ''
```

```tsx
  <Input type="date" id="tercih-gun" min={enErken} max={acik?.bitis_tarihi} ... />
```

3. Açık dönem yoksa form yerine kart:

```tsx
  if (!acik) {
    return (
      <Kart>
        <p className="m-0 text-sm text-ink-muted">
          Şu anda tercihe açık bir dönem yok. Yeni dönem açıldığında buradan
          bildirebilirsin.
        </p>
      </Kart>
    )
  }
```

Bu erken dönüş `Bildirdiğim Tercihler` kartını da gizler — **gizlememeli**:
kartı erken dönüşün içine de koy, yalnız form bloğu çıksın.

4. Durum mesajları — `hata` yanına `bilgi` durumu:

```tsx
  const [bilgi, setBilgi] = useState<string | null>(null)
```

`gonder` içinde başarıda `setBilgi('Tercihin alındı.')`, `catch` içinde:

```tsx
    } catch (e) {
      setBilgi(null)
      setHata(
        e instanceof ApiHatasi && e.status === 409
          ? 'Bu gün için kararlanmış bir tercihin var; değiştirmek için yöneticine başvur.'
          : e instanceof Error
            ? e.message
            : 'Tercih gönderilemedi',
      )
    }
```

`ApiHatasi`yi `@/api/client`ten import et.

5. Aralık süresi göstergesi — saat seçicilerin yanına:

```tsx
{/* Başlangıç = bitiş TÜM GÜN demektir (zaman_araligi.py: aralik_sure_saat);
    bunu yazmazsak 08→08 seçen kullanıcı 24 saat bildirdiğini bilmez. */}
<span className="text-sm text-ink-muted">
  {baslangicSaati === bitisSaati % 24
    ? 'tüm gün (24 saat)'
    : `${(bitisSaati - baslangicSaati + 24) % 24} saat`}
</span>
```

- [ ] **Adım 4: Testleri çalıştır**

```bash
cd frontend && npx vitest run src/screens/calisan/TercihlerimEkrani.test.tsx && npx tsc -b
```

Beklenen: 5 PASS, tsc temiz.

- [ ] **Adım 5: Commit**

```bash
git add frontend/src/screens/calisan/TercihlerimEkrani.tsx frontend/src/screens/calisan/TercihlerimEkrani.test.tsx
git commit -m "fix(calisan): bound the preference form to the open period and report conflicts"
```

---

### Görev 6: Izgara kısaltması ve lejant

**Dosyalar:**
- Değiştir: `frontend/src/lib/metin.ts`
- Oluştur: `frontend/src/lib/metin.test.ts`
- Değiştir: `frontend/src/screens/calisan/VardiyalarimEkrani.tsx:184,210-225`
- Oluştur: `frontend/src/screens/calisan/VardiyalarimEkrani.test.tsx`

**Arayüzler:**
- Kullanır: mevcut `kisalt(ad: string): string`
- Üretir: `benzersizKisaltma(adlar: string[]): Map<string, string>`

- [ ] **Adım 1: Başarısız testi yaz**

`frontend/src/lib/metin.test.ts`:

```ts
import { describe, expect, it } from 'vitest'

import { benzersizKisaltma } from './metin'

/**
 * DİKKAT — çakışan örnekler bilinçli seçildi. `kisalt()` çok kelimeli adı
 * baş harflerden türetir ("Depo A" → "DA"), dolayısıyla "Depo A/B/C" ZATEN
 * benzersizdir ve ayrıştırma yolunu hiç çalıştırmaz. Gerçek çakışma tek
 * kelimeli aynı üç harf ("Güvenlik"/"Güvence" → "GÜV") ya da aynı baş
 * harfler ("Ana Kapı"/"Arka Kapı" → "AK") ile doğar.
 */
describe('benzersizKisaltma', () => {
  it('çakışmayan adlarda kisalt() ile aynı sonucu verir', () => {
    const harita = benzersizKisaltma(['Güvenlik', 'Ana Kapı'])
    expect(harita.get('Güvenlik')).toBe('GÜV')
    expect(harita.get('Ana Kapı')).toBe('AK')
  })

  it('aynı üç harfe düşen tek kelimeli adları ayrıştırır', () => {
    const harita = benzersizKisaltma(['Güvenlik', 'Güvence'])
    expect(harita.get('Güvenlik')).not.toBe(harita.get('Güvence'))
  })

  it('aynı baş harflere düşen çok kelimeli adları ayrıştırır', () => {
    const harita = benzersizKisaltma(['Ana Kapı', 'Arka Kapı'])
    expect(harita.get('Ana Kapı')).not.toBe(harita.get('Arka Kapı'))
  })

  it('üç ad aynı kısaltmaya düşerse üçü de ayrışır', () => {
    const harita = benzersizKisaltma(['Güvenlik', 'Güvence', 'Güvercin'])
    expect(new Set(harita.values()).size).toBe(3)
  })

  it('giriş sırası sonucu değiştirmez', () => {
    const a = benzersizKisaltma(['Güvenlik', 'Güvence'])
    const b = benzersizKisaltma(['Güvence', 'Güvenlik'])
    expect(a.get('Güvenlik')).toBe(b.get('Güvenlik'))
  })
})
```

- [ ] **Adım 2: Testi çalıştır, düştüğünü gör**

```bash
cd frontend && npx vitest run src/lib/metin.test.ts
```

Beklenen: FAIL — `benzersizKisaltma` yok.

- [ ] **Adım 3: Uygula**

`frontend/src/lib/metin.ts` sonuna:

```ts
/**
 * Bir ad kümesinin BENZERSİZ ızgara kısaltmaları.
 *
 * `kisalt()` tek başına çakışabilir: "Kule 1" ve "Kule 2" ikisi de "K1"/"K2"
 * üretmez, ikisi de kelime baş harflerinden "K1" ve "K2" verir — ama "Depo A"
 * ile "Depo B" gibi adlarda ilk üç harf aynı düştüğünde ızgarada iki farklı
 * nokta aynı görünür ve çalışan hangi noktaya gittiğini okuyamaz.
 *
 * Çakışanlara adın SONRAKİ ayırt edici harfi eklenir. Sonuç giriş sırasından
 * bağımsızdır: adlar önce sıralanır.
 */
export function benzersizKisaltma(adlar: string[]): Map<string, string> {
  const sirali = [...new Set(adlar)].sort((a, b) => a.localeCompare(b, 'tr'))
  const sonuc = new Map<string, string>()
  const kullanilan = new Set<string>()
  for (const ad of sirali) {
    let aday = kisalt(ad)
    const harfler = buyukHarf(ad).replace(/\s+/g, '')
    let i = aday.length
    while (kullanilan.has(aday) && i < harfler.length) {
      aday = kisalt(ad) + harfler[i]
      i += 1
    }
    // Harfler tükendiyse sayı ekle: iki ad birebir aynı olamaz (Set), ama
    // aynı harflerden oluşabilir.
    let sayac = 2
    while (kullanilan.has(aday)) {
      aday = `${kisalt(ad)}${sayac}`
      sayac += 1
    }
    kullanilan.add(aday)
    sonuc.set(ad, aday)
  }
  return sonuc
}
```

- [ ] **Adım 4: Testi çalıştır**

```bash
cd frontend && npx vitest run src/lib/metin.test.ts
```

Beklenen: 4 PASS.

- [ ] **Adım 5: Izgarayı ve lejantı düzelt**

`VardiyalarimEkrani.tsx`:

```tsx
  // Nokta adları ızgarada kısaltmayla durur; kısaltmalar bu dönemin nokta
  // kümesi içinde BENZERSİZ olacak şekilde türetilir (slice(0,3) iki noktayı
  // aynı gösteriyordu).
  const kisaltmalar = useMemo(
    () => benzersizKisaltma(veri.vardiyalar.map((v) => v.nokta_ad)),
    [veri.vardiyalar],
  )
```

Hücrede `{v ? buyukHarf(v.nokta_ad.slice(0, 3)) : '–'}` yerine:

```tsx
                  {v ? (kisaltmalar.get(v.nokta_ad) ?? kisalt(v.nokta_ad)) : '–'}
```

Lejantta `<LegendOgesi renk="bg-accent" etiket="Değişen gün" />` yerine
ızgaradaki işaretin **aynısı** (3px şerit):

```tsx
          <span className="flex items-center gap-1.5">
            <span className="h-[3px] w-6 bg-accent" />
            Değişen gün
          </span>
```

Kullanılmayan `LegendOgesi` fonksiyonunu sil.

- [ ] **Adım 6: Ekran testini yaz ve çalıştır**

`VardiyalarimEkrani.test.tsx`:

```tsx
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import type { Vardiyalarim } from '@/api/types'

import { VardiyalarimEkrani } from './VardiyalarimEkrani'

function vardiya(tarih: string, noktaAd: string) {
  return {
    tarih,
    baslangic_zamani: `${tarih}T08:00:00`,
    bitis_zamani: `${tarih}T16:00:00`,
    sure_saat: 8,
    gece_saati: 0,
    nokta_id: 1,
    nokta_ad: noktaAd,
    degisim_tipi: null,
  }
}

const VERI = {
  donem_id: 1,
  donem_baslangic_tarihi: '2026-08-17',
  donem_bitis_tarihi: '2026-08-18',
  yayinlanmis_surum_var: true,
  yayin_zamani: null,
  // Çakışan iki ad: ikisi de kisalt() ile "GÜV" verir (bkz. metin.test.ts).
  vardiyalar: [vardiya('2026-08-17', 'Güvenlik'), vardiya('2026-08-18', 'Güvence')],
  kaldirilan_gunler: [],
  siradaki: null,
} as unknown as Vardiyalarim

afterEach(cleanup)

describe('VardiyalarimEkrani', () => {
  it('aynı üç harfe düşen iki noktayı ızgarada ayrıştırır', () => {
    render(<VardiyalarimEkrani veri={VERI} />)
    // İkisi de "GÜV" görünseydi çalışan hangi noktaya gittiğini okuyamazdı.
    const hucreler = screen.getAllByText(/^GÜV/)
    expect(new Set(hucreler.map((h) => h.textContent)).size).toBe(2)
  })

  it('kaldırılan günü kendi satırı olarak gösterir', () => {
    const veri = {
      ...VERI,
      kaldirilan_gunler: [
        {
          tarih: '2026-08-18',
          onceki_baslangic_zamani: '2026-08-18T08:00:00',
          onceki_bitis_zamani: '2026-08-18T16:00:00',
          onceki_nokta_ad: 'Güvence',
        },
      ],
    } as unknown as Vardiyalarim
    render(<VardiyalarimEkrani veri={veri} />)
    expect(screen.getByText('Kaldırıldı')).toBeTruthy()
  })
})
```

```bash
cd frontend && npx vitest run src/screens/calisan src/lib/metin.test.ts && npx tsc -b
```

Beklenen: hepsi PASS.

- [ ] **Adım 7: Commit**

```bash
git add frontend/src/lib/metin.ts frontend/src/lib/metin.test.ts frontend/src/screens/calisan/VardiyalarimEkrani.tsx frontend/src/screens/calisan/VardiyalarimEkrani.test.tsx
git commit -m "fix(calisan): make grid point abbreviations unique and match the legend to the marker"
```

---

### Görev 7: Mobil üst çubuk

**Dosyalar:**
- Değiştir: `frontend/src/components/CalisanShell.tsx:41-98`

**Arayüzler:** değişmez (prop imzası aynı)

- [ ] **Adım 1: Uygula**

Üst çubuk satırı 375px'te iki bloğu üst üste alsın, yetkinlik listesi taşmasın:

```tsx
        <div className="mx-auto flex max-w-[720px] flex-col gap-4 px-6 py-6 sm:flex-row sm:items-start sm:justify-between sm:gap-6">
          <div className="min-w-0">
            <p className="m-0 text-baslik-ekran font-semibold text-chrome-ink">{adSoyad}</p>
            {/* min-w-0 + truncate: yetkinlik listesi uzadığında 375px'te
                dönem bloğunu sıkıştırıyordu (NFR-7). */}
            <p className="m-0 mt-0.5 truncate text-mono-kucuk text-chrome-ink-muted">
```

Sağ blok `shrink-0 text-right` yerine `flex items-end justify-between gap-4 sm:block sm:shrink-0 sm:text-right`.

Sekme şeridi kaydırılabilir olsun:

```tsx
        <nav className="mx-auto flex max-w-[720px] gap-6 overflow-x-auto px-6">
```

- [ ] **Adım 2: Tarayıcıda doğrula**

```bash
cd frontend && npm run dev
```

`preview_start` ile aç, `resize_window` ile 375px'e indir, çalışan hesabıyla
gir; üst çubukta taşma olmadığını ve üç sekmenin de erişilebildiğini gör.
Ekran görüntüsü al.

- [ ] **Adım 3: Commit**

```bash
git add frontend/src/components/CalisanShell.tsx
git commit -m "fix(calisan): keep the top bar from overflowing on narrow screens"
```

---

### Görev 8: Tam takım doğrulama ve kayıt

**Dosyalar:**
- Değiştir: `PROGRESS_V2.md`

- [ ] **Adım 1: Tüm takımı çalıştır**

```bash
cd frontend && npm run test && npm run lint && npx tsc -b
```

```bash
cd backend && pytest -q
```

Her ikisi de temiz olmadan bu görev bitmez. Backend "atlandı" veriyorsa
PostgreSQL ayağa kaldırılır ve tekrar çalıştırılır.

- [ ] **Adım 2: `PROGRESS_V2.md`'ye kayıt ekle**

En üste, mevcut biçimi izleyen bir bölüm: tamamlanan işler, göç çıktısı
(`[goc c4f1a7d20b93]` satırları — kaç kopya bulundu, kaç satır silindi),
kalan/ertelenen, sıradaki oturumun ilk işi.

Doküman borcu başlığına şunlar yazılır:
- SDD 6.1: dönem özeti artık `/api/calisan/ozetim` uç noktasında ve ufuk
  parametresi alıyor.
- SRS FR-9.6: bir çalışan bir gün için tek tercih bildirir; beklemedeki
  tercihin üstüne yazılır, kararlanmışta 409 döner.
- SDD Ek B: yeni uç nokta ve 409 yanıtı.

- [ ] **Adım 3: Dağıtım notu**

`PROGRESS_V2.md`'ye, dağıtımdan önce sunucuda çalıştırılacak sayım:

```sql
SELECT personel_id, tarih, count(*) FROM tercih
GROUP BY personel_id, tarih HAVING count(*) > 1;
```

Sonuç boş değilse göç kaç satır silecek — sayı kayda geçmeden `alembic upgrade`
çalıştırılmaz.

- [ ] **Adım 4: Commit**

```bash
git add PROGRESS_V2.md
git commit -m "docs(progress): record the employee panel fix round"
```

---

## Öz Denetim

**Spec kapsamı:** Tasarımın 1. bölümü Görev 1+3+4'te, 2. bölümü Görev 1 (adil
pay alanları) + Görev 4 (göreli eşik), 3. bölümü Görev 5, 4. bölümü Görev 2,
5. bölümü Görev 6+7, 6. bölümü Görev 4/5/6 testleri + Görev 1/2 backend
testleri. Açık kalan yok.

**Tip tutarlılığı:** `DonemOzetiOku` (backend) ↔ `DonemOzeti` (frontend) alan
adları birebir; `ufuk` her iki tarafta `"donem" | "adalet"`; `adil_pay_*`
her iki tarafta nullable; `hedef_saat` her iki tarafta zorunlu.
`benzersizKisaltma` Görev 6'da tanımlanıp aynı görevde tüketiliyor.

**Bilinen bağımlılık:** Görev 3 tek başına `tsc` hatası bırakır (Görev 4 onu
kapatır); bu yüzden ikisi tek commit'te birleşir.
