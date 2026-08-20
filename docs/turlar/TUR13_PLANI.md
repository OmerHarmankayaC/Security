# Tur 13 — Boş taslak çizelge, elle çizilen sürümün cezası, Özet ekranı

Tasarım: [`docs/superpowers/specs/2026-08-20-bos-taslak-ve-ozet-tasarim.md`](../superpowers/specs/2026-08-20-bos-taslak-ve-ozet-tasarim.md)

Yedi görev, üç parça. Her görev kendi başına çalışır, kendi testleriyle gelir
ve kendi commit'ini alır. Görev sırası bağlayıcıdır: 2 → 1, 4 → 3, 7 → 6.

## Turun kuralları

- Kayıt İngilizce, kod yorumu ve arayüz metni Türkçe. Backend docstring'leri
  ASCII'ye indirgenmiş Türkçe — dokunduğun dosyanın kendi biçimine uy.
- Türkçe büyütme her zaman `buyukHarf()`; düz `.toUpperCase()` "i"yi bozar.
- **Koşulmuş göç değiştirilmez.** Bu turda göç YOK; hiçbir görev şema
  değiştirmiyor (yalnız yanıt alanları ekleniyor).
- Kural sınıfları kendilerine verilen parametre nesnesini değiştirmez (SDD 5.9).
- Başarısız test silinmez; `xfail` ile ve gerekçesiyle bırakılır.
- Her görevin sonunda: `ruff check .`, `ruff format --check .`, ilgili pytest
  dosyaları; ön yüzde `npx tsc -b`, `npm run lint`, ilgili vitest dosyaları.
- Ağır OR-Tools dosyaları görev içinde koşturulmaz; tur kapanışında bir kez
  (`CLAUDE.md` → "Ağır test dosyaları").

---

# Parça 1 — Boş taslak

## Görev 1: Depoya `taslak_ac`

**Dosyalar**
- Değiştir: `backend/app/repositories/sonuc.py` (`CizelgeSurumuDeposu`)
- Test: `backend/tests/test_surum_deposu.py` (yoksa oluştur)

**Ürettiği sözleşme** — Görev 2 bunu çağırır:

```python
def taslak_ac(self, donem_id: int) -> CizelgeSurumu:
    """Donemde ATAMASIZ yeni bir taslak acar.

    `taslak_turet`ten farki: onceki surum bilinmek zorunda degil. Donemde
    surum varsa yenisi EN SONUNCUYA baglanir - S8 ("onceki surumden sapma")
    ve Surumler ekraninin karsilastirmasi surum zincirine dayanir ve
    kullanici bos taslak acti diye zincir kopmamali. Hic surum yoksa
    `onceki_surum_id` bos kalir.
    """
```

Gövde `donem_icin_sonraki_surum_no` ve `listele(donem_id=...)`i kullanır;
`listele` zaten `surum_no` azalan sıralı döner, ilk öğe en sonuncudur.

**Adımlar**

1. `backend/tests/test_surum_deposu.py` içine iki test yaz:
   - `test_taslak_ac_bos_donemde_bagsiz_acar`: sürümü olmayan bir dönemde
     `taslak_ac` çağır; `surum_no == 1`, `onceki_surum_id is None`,
     `durum == CizelgeSurumuDurumu.TASLAK`, atama sayısı sıfır.
   - `test_taslak_ac_mevcut_surume_baglanir`: dönemde iki sürüm oluştur
     (no 1 ve 2), `taslak_ac` çağır; `surum_no == 3` ve `onceki_surum_id`
     **surum_no 2 olanın** kimliği.
   Fikstür deseni için `tests/test_analiz_api.py`'deki `OturumYerel` +
   `senaryo_verisini_temizle` kalıbını izle; canlı PostgreSQL gerekir
   (`pg_yoksa_atla`).
2. Koştur, "AttributeError: taslak_ac" ile başarısız olduğunu gör.
3. `taslak_ac`'i yaz.
4. Koştur, geçtiğini gör.
5. `ruff check .` ve `ruff format --check .`
6. Commit: `feat(repo): open a blank draft version for a period`

---

## Görev 2: Uç nokta `donem_id` kabul etsin

**Dosyalar**
- Değiştir: `backend/app/schemas/surum.py` (`SurumTaslakTuretIstek`)
- Değiştir: `backend/app/routers/cizelge.py` (`surum_taslak_turet`)
- Test: `backend/tests/test_surum_api.py` (yoksa oluştur)

**Şema** — iki alandan tam olarak biri:

```python
class SurumTaslakTuretIstek(BaseModel):
    """Bos taslak istegi: MEVCUT BIR SURUMDEN ya da DOGRUDAN DONEMDEN.

    Ikisi de verilirse hangisinin kazandigi belirsiz kalir ve istegi yazan
    taraf yanlis varsayimla devam eder; hicbiri verilmezse istek zaten
    anlamsizdir. Ikisi de 422 ile reddedilir.
    """

    onceki_surum_id: int | None = None
    donem_id: int | None = None

    @model_validator(mode="after")
    def _tam_olarak_biri(self) -> "SurumTaslakTuretIstek":
        if (self.onceki_surum_id is None) == (self.donem_id is None):
            raise ValueError("onceki_surum_id ya da donem_id verilmeli, ikisi birden degil")
        return self
```

`pydantic.model_validator` içe aktarımı dosyanın mevcut çok satırlı
`from pydantic import ...` bloğunun **kapanış parantezinden sonra** değil,
bloğun içine alfabetik yerine eklenecek — bu projede satır ortasına import
sokup üç kez bozdum.

**Yönlendirici** — mevcut gövde korunur, `donem_id` dalı eklenir:

```python
@router.post("/surum", response_model=CizelgeSurumuOku, status_code=201)
def surum_taslak_turet(veri: SurumTaslakTuretIstek, oturum: Oturum) -> CizelgeSurumuOku:
    depo = CizelgeSurumuDeposu(oturum)
    if veri.donem_id is not None:
        if DonemDeposu(oturum).getir(veri.donem_id) is None:
            raise HTTPException(status_code=404, detail="Donem bulunamadi")
        surum = depo.taslak_ac(veri.donem_id)
    else:
        surum = depo.taslak_turet(veri.onceki_surum_id)  # type: ignore[arg-type]
        if surum is None:
            raise HTTPException(status_code=404, detail="Onceki surum bulunamadi")
    return CizelgeSurumuOku.model_validate(surum)
```

Yetki: uç noktanın bugünkü kapısı değişmez.

**Adımlar**

1. Testleri yaz: `donem_id` ile 201 ve `onceki_surum_id is None`; olmayan
   dönemle 404; iki alan birden verilince 422; hiçbiri verilmeyince 422;
   `onceki_surum_id` ile bugünkü davranışın **değişmediği**.
2. Koştur, başarısız olduğunu gör.
3. Şemayı ve yönlendiriciyi yaz.
4. Koştur, geçtiğini gör.
5. `python scripts/uc_noktalari_listele.py --denetle` — uç nokta sayısı
   değişmedi, imza değişti; Ek B'de fark çıkarsa `--yaz` ile güncelle.
6. `ruff check .`, `ruff format --check .`
7. Commit: `feat(api): allow opening a blank draft straight from a period`

---

## Görev 3: Izgara satırları personel listesinden

**Dosyalar**
- Oluştur: `frontend/src/lib/izgaraSatirlari.ts`
- Oluştur: `frontend/src/lib/izgaraSatirlari.test.ts`
- Değiştir: `frontend/src/screens/CizelgeEkrani.tsx:300-307` (`tumIzgaraPersonelleri`)

**Neden ayrı dosya:** `CizelgeEkrani.tsx` 1219 satır. Bu mantık saf bir
süzgeç ve testi ekranı render etmeden yazılabilir; ekranın içinde kalırsa
testi ancak tüm ekranı kurarak yazılır.

**Ürettiği sözleşme:**

```ts
/**
 * Izgarada satırı olacak personel.
 *
 * DÜZENLENEBİLİR SÜRÜMDE KADRO, SALT OKUNURDA ATAMA. Taslak ve çözüldü
 * sürümlerinde soru "kime hâlâ atama yapabilirim" — ataması olmayan da
 * satır olmalı, yoksa boş bir taslakta tıklanacak hücre kalmaz.
 * Yayınlanmış/arşivde soru "ne karar verildi" ve orada boş satır gürültüdür.
 *
 * Aktiflik penceresi dışındaki personel HİÇBİR sürümde satır olmaz: H7
 * bağlamı o güne atamayı zaten reddediyor (`baglam.musait_mi`) ve satırı
 * göstermek kullanıcıyı asla kabul edilmeyecek bir tıklamaya davet ederdi.
 * Bu, pencerenin ikinci kez okunduğu yerdir; kural değil görünürlük
 * süzgecidir ve ayrışırsa sonucu zararsızdır (sunucu gerekçesiyle reddeder).
 */
export function izgaraSatirlari(girdi: {
  personeller: readonly Personel[]
  atamalar: readonly Atama[]
  duzenlenebilir: boolean
  donemBaslangic: string   // ISO
  donemBitis: string       // ISO
}): Personel[]
```

Sıralama `ad_soyad.localeCompare(a, b, 'tr')` — bugünkü davranış.

Aktiflik ölçütü:
`p.aktif_baslangic <= donemBitis && (p.aktif_bitis === null || p.aktif_bitis >= donemBaslangic)`

**Adımlar**

1. Testleri yaz (`izgaraSatirlari.test.ts`):
   - düzenlenebilir sürümde ataması olmayan personel satır olur;
   - salt okunurda olmaz;
   - dönem bitmeden önce ayrılmış personel (`aktif_bitis < donemBaslangic`)
     düzenlenebilir sürümde de satır olmaz;
   - dönem başladıktan sonra işe girmiş personel (`aktif_baslangic` dönem
     içinde) satır **olur** — kısmi katılım geçerlidir;
   - salt okunur sürümde ataması olan ama aktiflik penceresi dışında kalan
     personel yine de satır olur (geçmiş bir karar; gizlemek çizelgeyi
     eksik gösterirdi).
2. Koştur, başarısız olduğunu gör.
3. `izgaraSatirlari`i yaz.
4. Koştur, geçtiğini gör.
5. `CizelgeEkrani.tsx`'te `tumIzgaraPersonelleri`i bu fonksiyona bağla.
   `donem` değişkeni ekranda mevcut; yoksa `donemler.find(...)` ile al.
6. `npx tsc -b`, `npm run lint`, `npm run test -- --run src/lib/izgaraSatirlari.test.ts`
7. Commit: `feat(schedule): draw rows from the roster on editable versions`

---

## Görev 4: "Boş taslak aç" düğmesi

**Dosyalar**
- Değiştir: `frontend/src/api/client.ts` (`taslakTuret` yanına `bosTaslakAc`)
- Değiştir: `frontend/src/screens/CizelgeEkrani.tsx` (sürüm seçicinin yanı,
  ~satır 716) ve boş hâl metni (~satır 804)
- Test: `frontend/src/screens/CizelgeEkrani.test.tsx`

**İstemci:**

```ts
bosTaslakAc: (donemId: number) =>
  gonder<CizelgeSurumu>('/api/surum', { donem_id: donemId }),
```

**Düğme davranışı**

- Dönem seçili değilse pasif.
- Dönemde sürüm varsa `confirm` metni: `Dönemde N sürüm var; ${N+1}. sürüm
  boş bir taslak olarak açılacak.` Yoksa doğrudan açılır.
- Başarıda: sürüm listesi yeniden çekilir ve yeni sürüm seçilir
  (`setSurumId(yeni.surum_id)`), düzenleme oturumu `BOS_OTURUM`'a döner.
- Hata: mevcut `setHata` yoluna düşer.

**Boş hâl metni** — bugün `tumIzgaraPersonelleri.length === 0` dalında "Bu
sürümde henüz atama yok." yazıyor. Düzenlenebilir sürümde artık satır
geleceği için o dal yalnız salt okunur sürümlerde çalışır; metin
değişmez ama koşuluna `!surumDuzenlenebilir` eklenir. Düzenlenebilir
sürümde satır da yoksa (dönemde aktif personel yok) ayrı metin:
"Bu dönemde aktif personel yok; Tanımlar ekranından personel ekleyin."

**Adımlar**

1. Test yaz: dönemde sürüm varken düğmeye basınca `confirm` çağrılır ve
   onaylanınca `/api/surum` gövdesinde `donem_id` gider; iptal edilince
   istek gitmez. Mevcut testteki `vi.stubGlobal('confirm', ...)` kalıbını
   kullan.
2. Koştur, başarısız olduğunu gör.
3. İstemciyi, düğmeyi ve boş hâl dalını yaz.
4. Koştur, geçtiğini gör.
5. `npx tsc -b`, `npm run lint`, `npm run test -- --run src/screens/CizelgeEkrani.test.tsx`
6. Commit: `feat(schedule): add a button that opens a blank draft`

---

# Parça 2 — Elle çizilen sürümün cezası

## Görev 5: Ceza dökümünün kaynağı

**Dosyalar**
- Değiştir: `backend/app/services/analiz_servisi.py` (`hesapla`, yeni
  `_ceza_kaynagi_ve_dokum`)
- Değiştir: `backend/app/schemas/analiz.py` (`AnalizOku`)
- Değiştir: `backend/app/repositories/sonuc.py` (`AtamaDeposu`)
- Değiştir: `frontend/src/api/types.ts`, `screens/AnalizEkrani.tsx`
- Test: `backend/tests/test_analiz_api.py`, `frontend/src/screens/AnalizEkrani.test.tsx`

**Yeni depo metodu:**

```python
def surume_gore_son_guncelleme(self, surum_id: int) -> datetime | None:
    """Surumun atamalarindaki EN SON guncelleme zamani.

    Cozucunun dokumunun bayat olup olmadigini bu belirler: cizelge cozum
    isinden sonra elle degistirildiyse dokum artik baska bir cizelgeyi
    anlatir."""
    stmt = select(func.max(Atama.guncelleme_zamani)).where(Atama.surum_id == surum_id)
    return self.oturum.execute(stmt).scalar_one_or_none()
```

**Servis:**

```python
def _ceza_kaynagi_ve_dokum(
    self, surum_id: int, atamalar: list[AtamaKaydi], baglam: Baglam
) -> tuple[str, dict[str, float] | None, float | None]:
    """(kaynak, ceza_dokumu, toplam_ceza).

    COZUCUNUN DOKUMU YALNIZ TAZEYSE KULLANILIR. Cozulmus bir surum elle
    duzenlendiginde eski dokum duruyordu ve ekran degismis bir cizelgeyi
    degismemis bir cezayla gosteriyordu.

    Cozucusuz surumde dokum ESNEK KURALLARIN KENDISINDEN hesaplanir; ayni
    siniflar dogrulama servisinin de kaynagi (dogrulama_servisi.py). Ikinci
    bir gerceklik kurulmuyor: cozucu ile dogrulayicinin ayni cizelgede ayni
    seyi gormesi zaten guvence altinda (SDD 3.2.1).
    """
```

Karar:

```
is = cozum_isi.surume_gore_en_son(surum_id)
son_atama = atama.surume_gore_son_guncelleme(surum_id)
taze = is is not None and is.ceza_dokumu is not None and (
    is.bitis_zamani is not None and son_atama is not None
    and son_atama <= is.bitis_zamani
)
taze  → ("cozucu", is.ceza_dokumu, is.en_iyi_ceza)
degil → ("kurallardan", hesaplanan, Σ ham × agirlik)   # hesaplanan bossa ("yok", None, None)
```

Hesap:

```python
dokum = {}
for kural in kurallari_yukle(self.kural.aktif_kurallari_getir()):
    if kural.tip != KuralTipi.ESNEK or kural.kimlik == "S8":
        continue
    ceza = sum(i.ceza or 0.0 for i in kural.dogrula(atamalar, baglam))
    if ceza:
        dokum[kural.kimlik] = ceza
```

**S8 neden dışarıda:** "önceki sürümden sapma" yalnız `baglam.onceki_atamalar`
doluyken tanımlı, analiz bağlamı onu kurmuyor (`baglam_olustur`un böyle bir
parametresi yok). Sıfır yazmak "sapma yok" derdi; doğrusu "bu ölçü burada
tanımsız", o yüzden kalem hiç üretilmez. Bu, kodun içine yorum olarak
yazılacak — sonraki okuyucu eksikliği hata sanır.

**Şema:** `AnalizOku`'ya `ceza_kaynagi: str = "yok"`. Ön yüzde
`ceza_kaynagi: 'cozucu' | 'kurallardan' | 'yok'`.

**Ekran:** Analiz'in ceza dökümü kartındaki dipnota bir cümle eklenir:
- `cozucu` → "Döküm çözüm işinden geliyor."
- `kurallardan` → "Bu sürümde çözücü çalışmadı ya da çizelge sonradan elle
  değişti; döküm kural motorundan hesaplandı."

**Adımlar**

1. Arka uç testleri:
   - çözücüsüz, elle kurulmuş atamaları olan sürümde `ceza_kaynagi ==
     "kurallardan"`, döküm dolu ve her kalemde `ham × ağırlık == ağırlıklı`;
   - çözüm işi olan ve atamaları o işten eski olan sürümde `"cozucu"` ve
     döküm işin kendi dökümü;
   - aynı sürümün bir ataması güncellendiğinde kaynak `"kurallardan"`a döner
     ve `toplam_ceza` değişir;
   - hesaplanan dökümde `S8` anahtarı **yok**.
2. Koştur, başarısız olduğunu gör.
3. Depo metodunu, servisi ve şemayı yaz.
4. Koştur, geçtiğini gör.
5. Ön yüz testi: `ceza_kaynagi: 'kurallardan'` fikstüründe dipnot metni
   görünür; `'cozucu'`da görünmez.
6. Ön yüzü yaz; `npx tsc -b`, `npm run lint`, vitest.
7. `ruff check .`, `ruff format --check .`
8. Commit: `feat(analysis): compute the penalty breakdown when the solver did not`

---

# Parça 3 — Özet ekranı

## Görev 6: Günlük kapsama dökümü ve atama sayısı

**Dosyalar**
- Değiştir: `backend/app/schemas/analiz.py` (`GunlukKapsamaOku`, `AnalizOku`)
- Değiştir: `backend/app/schemas/surum.py` (`SurumOzetiOku.atama_sayisi`)
- Değiştir: `backend/app/services/analiz_servisi.py` (`hesapla`)
- Değiştir: `backend/app/services/surum_servisi.py` (`listele`)
- Değiştir: `backend/app/repositories/sonuc.py` (`AtamaDeposu`)
- Test: `backend/tests/test_analiz_api.py`, `backend/tests/test_surum_api.py`

**Şema:**

```python
class GunlukKapsamaOku(BaseModel):
    """Bir gunun kapsama acigi (SDD 6.3.1, Ozet ekrani gunluk seridi).

    Toplami AnalizOku.karsilanmayan_kisi_saat'e ESITTIR ve bu bir testtir:
    aralik sayisi ile kisi-saat bu projede bir kez karistirildi ve disa
    aktarma basliginda yanlis sayi basildi."""

    tarih: date
    acik_aralik_sayisi: int
    karsilanmayan_kisi_saat: int
```

`AnalizOku`'ya `gunluk_kapsama: list[GunlukKapsamaOku] = Field(default_factory=list)`.

**Servis** — mevcut `karsilanmayan` hesabının yanına, **aynı formülle**:

```python
gunluk: dict[date, list[int]] = {}   # tarih -> [aralik, kisi_saat]
for a in aciklar:
    saat = a.eksik_sayi * round((a.bitis_zamani - a.baslangic_zamani).total_seconds() / 3600)
    kayit = gunluk.setdefault(a.baslangic_zamani.date(), [0, 0])
    kayit[0] += 1
    kayit[1] += saat
```

Gün, **başlangıç damgasından** okunur (TD-1: blok başladığı güne sayılır);
dönemin açığı olmayan günleri de sıfırla listeye girer, çünkü şerit dönemin
tamamını çizer ve eksik gün "veri yok" gibi görünürdü.

**Atama sayısı:**

```python
def surumlere_gore_atama_sayisi(self, surum_idleri: Sequence[int]) -> dict[int, int]:
    """Surum listesi icin surum basina atama sayisi (SDD 6.3.5).

    Ozet ekrani "olculebilir surum"u bununla secer: olcut artik "taslak
    degil" degil "atamasi var". Eski olcut "cozulmemis taslagin atamasi
    yoktur" varsayimina dayaniyordu; elle cizilen taslak bunu gecersiz kilar.
    """
```

**Adımlar**

1. Testler:
   - `gunluk_kapsama` toplamı `karsilanmayan_kisi_saat`'e eşittir;
   - dönemin her günü listede vardır (açığı olmayanlar sıfırla);
   - gece yarısını aşan açık **başladığı güne** yazılır;
   - `/api/surum` yanıtındaki `atama_sayisi` doğru; atamasız taslakta sıfır.
2. Koştur, başarısız olduğunu gör.
3. Şemaları, depo metodunu ve servisleri yaz.
4. Koştur, geçtiğini gör.
5. `ruff check .`, `ruff format --check .`
6. Commit: `feat(analysis): report coverage gaps per day and assignments per version`

---

## Görev 7: Özet ekranı

**Dosyalar**
- Değiştir: `frontend/src/lib/donemSecimi.ts` (`olculebilirSurum`)
- Değiştir: `frontend/src/lib/donemSecimi.test.ts`
- Oluştur: `frontend/src/components/GunlukKapsamaSeridi.tsx`
- Değiştir: `frontend/src/screens/OzetEkrani.tsx`
- Değiştir: `frontend/src/api/types.ts`
- Test: `frontend/src/screens/OzetEkrani.test.tsx` (yoksa oluştur)

**Ölçüt değişikliği:**

```ts
/**
 * Ölçülebilir en yeni sürüm: ATAMASI OLAN sürüm.
 *
 * Ölçüt "taslak değil" idi ve "çözülmemiş taslağın ataması yoktur"
 * varsayımına dayanıyordu. Elle çizilen taslağın ataması vardır ve
 * ölçülebilir; eski ölçütle Özet onu hiç görmezdi.
 */
export function olculebilirSurum(
  surumler: readonly CizelgeSurumu[],
): CizelgeSurumu | undefined {
  return surumler.find((s) => s.atama_sayisi > 0)
}
```

`CizelgeSurumu` tipine `atama_sayisi: number` eklenir. Mevcut
`donemSecimi.test.ts` fikstürleri güncellenecek.

**Ekranın yapısı** (yukarıdan aşağı):

1. Ölçü kartları şeridi — üstünde tek satır: `<dönem aralığı> dönemi için`.
   Aralık metni `donemAraligiBicimle` ile (`lib/tarih.ts`'te mevcut).
2. Kapsama kartı: başlıkta aynı aralık, içinde `GunlukKapsamaSeridi`, altında
   bugünkü açık listesi — seçili gün varsa o güne süzülmüş.
3. Kişi başına saat — `analiz.saat_dagilimi`den `|sapma|` azalan ilk **altı**
   kişi; satır: ad · toplam saat · fark (işaretli). Altında "Tümünü Analiz
   ekranında görüntüle" düğmesi (`ekranSec('Analiz')`).
4. Bu dönem müsait olmayanlar — `musaitlikler`den dönemle **kesişenler**:
   `m.baslangic_tarihi <= donem.bitis_tarihi && m.bitis_tarihi >= donem.baslangic_tarihi`.
5. Yaklaşan müsaitlik kayıtları — bugünkü kart, etiketi "bugünden itibaren"
   olacak şekilde dürüstleşir.

**Şerit bileşeni:**

```tsx
/**
 * Günlük açık şeridi — dönemin her günü için bir çubuk.
 *
 * Çubuğun yüksekliği o günün eksik kişi-saatiyle orantılıdır; açığı olmayan
 * gün soluk ve çubuksuz durur. Şerit KENDİ BAŞINA bir ölçü göstermez, aynı
 * kartın altındaki listenin süzgecidir: "hangi gün sorunlu" sorusunu
 * yanıtlar, "neden" sorusunu liste yanıtlar.
 */
export function GunlukKapsamaSeridi({
  gunler,
  seciliTarih,
  gunSec,
}: {
  gunler: readonly GunlukKapsama[]
  seciliTarih: string | null
  gunSec: (tarih: string | null) => void
}) 
```

Erişilebilirlik: her gün bir `button`, `aria-pressed={secili}`,
`aria-label` gün adı + eksik kişi-saat. Seçili güne tekrar tıklamak süzgeci
kaldırır (`gunSec(null)`).

**Tazeleme:** `useEffect` içinde `visibilitychange` dinleyicisi; sekme
görünür olduğunda yükleme fonksiyonu yeniden çağrılır. Dinleyici
`removeEventListener` ile sökülür.

**Boş taslak hâli:** `olculemeyenTaslak` metni güncellenir —
"Bu dönemin son sürümü henüz boş bir taslak. Çizelge ekranından elle
çizebilir ya da Çözüm ekranını kullanabilirsin."

**Adımlar**

1. `donemSecimi.test.ts`'e test ekle: ataması olan taslak seçilir; atamasız
   sürüm atlanır. Fikstürlere `atama_sayisi` ekle.
2. Koştur, başarısız olduğunu gör; `olculebilirSurum`i ve tipi düzelt.
3. `OzetEkrani.test.tsx` yaz:
   - her aralık-bağlı blok aralık metnini taşır;
   - ekranda dönem seçici (combobox) **yoktur**;
   - şeritte bir güne tıklamak açık listesini o güne süzer, tekrar tıklamak
     süzgeci kaldırır;
   - kişi başına saat listesi en çok sapanı üstte verir ve altı satırla
     sınırlıdır;
   - müsaitlik kartı dönemle kesişmeyen kaydı göstermez;
   - atamasız taslakta ölçü yerine durum metni çıkar.
   `AnalizEkrani.test.tsx`'teki `vi.mock('../api/client', ...)` ve AppShell
   taklidi kalıbını kullan.
4. Koştur, başarısız olduğunu gör.
5. Şerit bileşenini ve ekranı yaz.
6. `npx tsc -b`, `npm run lint`, `npm run test -- --run`
7. Commit: `feat(summary): make the summary screen answer "what is happening now"`

---

# Tur kapanışı

1. Hafif arka uç takımı: `CLAUDE.md`'deki `--ignore` listesiyle.
2. **Ağır takım ayrıca**: on bir OR-Tools dosyası, tek koşumda ~10 dk.
   "Atlandı" ile "geçti" aynı şey değildir.
3. `npx tsc -b`, `npm run lint`, `npm run test -- --run` (tam vitest).
4. `python scripts/uc_noktalari_listele.py --denetle`.
5. `PROGRESS_V2.md`'ye tur kaydı ve **DOKÜMAN BORCU** başlığı. Beklenen
   borçlar:
   - SRS FR-6.x — elle çizim yolu artık çözücüden bağımsız bir üretim yolu;
   - SDD 5.6 — `taslak_ac` ve `POST /api/surum`un iki alanlı sözleşmesi;
   - SDD 5.7 — ceza dökümünün ikinci kaynağı ve tazelik ölçütü;
   - SDD 6.3.1 — Özet ekranının yeni yapısı ve aralık etiketleri;
   - SDD 6.3.5 — `SurumOzetiOku.atama_sayisi`.
6. Dağıtım kararı proje yürütücüsünde. (SSH şu an kapalı; `1a39a70` sunucuya
   gitmeyi bekliyor.)
