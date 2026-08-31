# İlerleme Günlüğü — Sürüm 2

Birinci aşamanın günlüğü [`PROGRESS.md`](PROGRESS.md) dosyasında kapandı ve
arşivdir; okunmaz. Sürüm 2'nin kaydı buradan başlar.

Her oturum sonunda buraya bir kayıt eklenir: tarih, tamamlanan,
kalan/ertelenen, sıradaki oturumun ilk işi. Yeni oturum bu dosyayı okuyarak
başlar.

---

## 2026-08-19 — Dağıtım: çalışan paneli turu — **TAMAMLANDI**

Kapsam: çalışan paneli düzeltme turu, K3'ün dağılım ölçüsüne çevrilmesi,
çözücü zaman limitinin 300 sn'ye çıkması ve analiz servisindeki saat dengesi
düzeltmesi. **Bir göç var** (`c4f1a7d20b93`), frontend yeniden derlendi.

### Sıra

1. Ön sayım — göçün duracağı durum var mı diye:
   ```sql
   SELECT personel_id, tarih, count(*), array_agg(durum::text ORDER BY tercih_id)
   FROM tercih GROUP BY personel_id, tarih HAVING count(*) > 1;
   -- (0 rows)
   ```
   **Üretimde kopya tercih YOK.** Göç kararlanmış tercih bulmadı, hiçbir satır
   silmedi.
2. `systemctl stop vardiya-cozucu`, ardından `vardiya-api`.
3. Yedek: `/opt/vardiya/yedek/vardiya-20260819-0802.dump`, **69K**.
4. `rsync` frontend (`dist/`) + backend; `pip install -e ".[dev]"`; `chown`.
5. `alembic upgrade head` → `c4f1a7d20b93`, servisler kapalıyken.
6. `systemctl start vardiya-api`, `vardiya-cozucu`.

### Doğrulama

| Denetim | Sonuç |
|---|---|
| Servisler | `vardiya-api` ve `vardiya-cozucu` **active** |
| `alembic current` | `c4f1a7d20b93 (head)` |
| Tekillik kısıtı | `uq_tercih_personel_tarih` veritabanında var |
| `127.0.0.1:8002/health` | `{"durum":"ok"}` |
| **`/api/calisan/ozetim`** | **401** — 404 değil, yani yeni kod canlı |
| `/api/calisan/vardiyalarim` | 401 |
| `journalctl -p err` (5 dk) | 0 satır |
| Frontend | 08:03'te güncellendi, `index-BfeeUNZo.js` |

Uç noktanın 401 dönmesi kasten aranan işaret: 404 dönseydi eski kod
duruyor olurdu. Kısıtın varlığı da ayrıca sorgulandı — göç çıktısına
güvenilmedi.

### Dağıtım rehberinde bulunan eksik

Bölüm 10'daki "Kod güncellemesi" bloğu `RSYNC_RSH` export'unu taşımıyordu.
`ssh` komutları bayrağı kendi satırında taşıyor, rsync taşımıyor; anahtar
ajanda yüklü değilse `Permission denied (publickey)` veriyor ve bu dağıtımda
tam olarak bu yaşandı. Blok düzeltildi (15.4'e gönderme, depo kökünden
koşulma uyarısı ve `cd ..` dahil).

### Bu turda değişen davranış

- Çözücü zaman limiti varsayılanı **60 → 300 sn**. Arayüzdeki alan da 300
  ile açılıyor. Mevcut işler etkilenmez; yeni işler daha uzun arar.
- Çalışan panelinde dönem özeti ayrı uç noktadan geliyor; Vardiyalarım
  sekmesi artık analiz hesabı ödemiyor.
- Analiz ekranındaki **saat dengesi sayıları değişecek** — hedef ile yük
  artık aynı pencereden okunuyor. Gerileme değil, önceki sayının bozuk
  olmasının düzeltilmesi.

### AÇIK

K3, yeni dağılım ölçüsü ve 300 sn limitle sunucuda **henüz ölçülmedi**.
`PERFORMANS_NOTU.md` sürüm 3 hâlâ eski tanımı (azami sapma ≤ 8) ve eski
limiti anlatıyor; Charter 1.6 ile çelişiyor. Ölçüm yapılmadan sürüm 4
yazılamaz.

---

## 2026-08-18 — Ağır çözücü testleri: doğrulama açığı kapandı — **TAMAMLANDI**

Çalışan paneli turu boyunca sandbox zaman aşımı yüzünden hiç koşmayan 11 ağır
OR-Tools dosyası, birleşmiş `main` üzerinde tek seferde koşturuldu.

```
cd backend && .venv/bin/pytest -q \
  tests/test_cozucu_uctan_uca.py tests/test_cozucu_dogrulayici_uyumu.py \
  tests/test_cozucu_dogrulayici_uyumu_olcek.py tests/test_cozum_servisi.py \
  tests/test_cozum_iscisi.py tests/test_agirlik_kalibrasyonu.py \
  tests/test_durdurma_karari.py tests/test_kurallar_zorunlu.py \
  tests/test_kurallar_esnek.py tests/test_yeniden_coz.py \
  tests/test_kabul_olcumu_dumani.py

→ 134 passed in 596.83s (0:09:56)
```

Böylece backend takımının **tamamı** doğrulanmış oldu: 270 + 134 = 404 test
(1 atlandı, veri eksikliğinden — `test_ardisik_donem_adaleti.py`). Turun
"sıradaki oturumun ilk işi" olarak bıraktığı açık kapandı; çözücü tarafında
gerileme yok.

Süre kayda değer: on dakika, tek dosya bazında değil toplu koşuda. Bu yüzden
tur içi döngülerde dışarıda bırakılmaları makul — ama tur kapanışında bir kez
koşturulmaları şart, çünkü "koşmadı" ile "geçti" aynı şey değil.

---

## 2026-08-18 — Çalışan paneli: nihai inceleme ve düzeltme dalgası — **TAMAMLANDI**

Turun tamamı tek parça olarak incelendi (görev incelemelerinin yapısal olarak
göremediği şeyler için). **Altı Important bulgu** çıktı, hepsi tek düzeltme
dalgasında kapatıldı: `5351a38`, `d3dd62f`, `84e2460`, `e7eb81a`. Kapsamlı
re-review: hepsi giderilmiş, yeni Critical/Important yok.

### Bulgular — neden görev incelemeleri kaçırdı

1. **`ufuk=adalet` seçilince toplam saat genişlemiyordu.**
   `analiz_servisi.py:338-351` saat dengesini ufuktan bağımsız kuruyor; gece
   ve hafta sonu 90 güne açılırken toplam saat dönem içinde kalıyor. Ekran
   "SON 90 GÜN" başlığı altında dönemin 40 saatini, yanında 96 saat geceyi
   gösteriyordu. Etiket bizim dosyamızda, anlambilim Tur 10'un dosyasında —
   hiçbir görev incelemesi ikisini birden görmedi. `analiz_servisi.py` kapsam
   dışı olduğu için **sunum tarafında** kapatıldı: Toplam Saat kartında
   kaçırılamaz bir uyarı ve cümle içinde "(dönem içi, 90 günü değil)".
   **Asıl tutarsızlık Tur 10 iş kolunda duruyor.**
2. Rozet "Ortalamanın Üstünde" diyordu, oysa kartın referansı adil paya
   geçmişti → "Adil Payın Üstünde/Altında".
3. **Göç, onaylanmış bir tercihi sessizce silebiliyordu.** En büyük
   `tercih_id` korunuyordu, `durum`a bakılmadan. Karar alınmış bir satır daha
   eski kalırsa yönetici kararı geri dönüşsüz gidiyordu ve onaylı tercihler
   çözücüye girdi olarak akıyor. Yeni politika: kopya grubunda BEKLEMEDE
   olmayan satır varsa **göç durur**, etkilenen `(personel_id, tarih)`
   çiftlerini adlarıyla bildirir, hiçbir şey silinmez.
4. Yönetici tarafındaki `POST /api/tercih` yeni tekillik kısıtına karşı
   korumasızdı (500). İki yazma yolu da artık `IntegrityError` yakalayıp
   temiz 409 dönüyor — bu aynı zamanda eşzamanlı çift gönderim yarışını da
   kapattı.
5. Tarih alanının varsayılanı kendi `min` sınırının altında kalıyordu;
   dönem başlamışsa çalışan hiçbir şeye dokunmadan geçmişe tercih
   bildirebiliyordu. Varsayılan artık `min` ile aynı fonksiyondan geliyor.
6. **Ufuk testi boştu:** `ufuk`, `hesapla`'ya hiç geçirilmese de geçiyordu,
   çünkü fixture'da önceki yayınlanmış dönem yoktu ve iki ufuk aynı sayıyı
   üretiyordu. Geçmiş dönemli fixture eklendi; test artık iki ufkun gerçekten
   farklı sayı ürettiğini doğruluyor. `adil_pay_*`, `hedef_saat`,
   `gece_havuzunda` de artık sınanıyor.

### Dağıtım öncesi — GÜNCELLENDİ

Göç artık kararlanmış tercih içeren kopya grubunda **durur**. Sunucuda
çalıştırılacak sayım sorgusu `durum`u da raporlamalı (bu turun Görev 8
kaydındaki SQL güncellendi). Sorgu boş dönmüyorsa, göç uygulanmadan önce o
günler elle ayıklanmalı.

### Ertelenen (park edilmiş) — birleştirmeyi engellemez

- `DonemOzetimEkrani.tsx:54` — kart etiket satırı `mb-4`→`mb-1` koşulsuz
  değişti; uyarı taşımayan üç kart hâlinde 12px daha sıkı duruyor. Yalnız
  görsel, testi yok.
- `tanim.py:392-397` — `except IntegrityError` hangi kısıtın düştüğüne
  bakmıyor; olmayan bir FK ile gelen POST artık 500 yerine yanıltıcı bir 409
  dönüyor. `hata.orig` kısıt adına daraltmak sonraki turun işi.

### Doğrulama (birleşmiş ağaç üzerinde)

```
frontend: 30 dosya, 319 test — hepsi geçti; lint temiz; tsc çıkış 0
backend:  270 geçti, 1 atlandı (11 ağır çözücü dosyası HARİÇ — bkz. Görev 8)
```

`tur8-disa-aktarma` → `main` birleştirmesi: `15345ef`.

---

## 2026-08-18 — Görev 8: Tam takım doğrulama ve kayıt — **TAMAMLANDI**

Çalışan paneli düzeltme turunun (yedi görev, on commit: `5e2b7de` (Görev 1),
`eb9c24d` (Görev 2), `d1c4d56` + `7fe9a72` + `e537080` (Görev 3+4, üç
commit), `9ea41ab` + `8cca290` (Görev 5, ilki ve review düzeltmesi),
`f282539` (Görev 6), `82d6de2` + `9f1bab0` (Görev 7, ilki ve review
düzeltmesi)) kapanış doğrulaması. Kaynak koduna dokunulmadı — bu görev
yalnız doğrulama ve kayıt.

### Frontend — temiz

```
cd frontend && npm run test   → 30 dosya, 314 test, hepsi geçti (4,00 sn)
cd frontend && npm run lint   → oxlint; 0 hata, 4 önceden var olan
                                 react(only-export-components) uyarısı
                                 (button.tsx, badge.tsx, TanimYonetimi.tsx,
                                 AktifIsBaglami.tsx — bu turun kapsamı dışında)
cd frontend && npx tsc -b     → çıkış 0, hata yok
```

### Backend — temiz (ağır çözücü dosyaları hariç)

```
cd backend && pytest -q
  --ignore=tests/test_cozucu_uctan_uca.py
  --ignore=tests/test_cozucu_dogrulayici_uyumu.py
  --ignore=tests/test_cozucu_dogrulayici_uyumu_olcek.py
  --ignore=tests/test_cozum_servisi.py
  --ignore=tests/test_cozum_iscisi.py
  --ignore=tests/test_agirlik_kalibrasyonu.py
  --ignore=tests/test_durdurma_karari.py
  --ignore=tests/test_kurallar_zorunlu.py
  --ignore=tests/test_kurallar_esnek.py
  --ignore=tests/test_yeniden_coz.py
  --ignore=tests/test_kabul_olcumu_dumani.py

→ 263 passed, 1 skipped (12,76 sn)
```

On bir dosya hariç tutuldu; hepsi gerçekten OR-Tools CP-SAT çözücüyü
çalıştırıyor (`cp_model` / `CozumServisi` / `isi_calistir_ve_bekle`) ve
sandbox'ın 10 dakikalık zaman aşımını aşabiliyor (bkz. Tur 10 kalibrasyon
kaydı aşağıda — tek bir ölçüm 60–900 sn arası sürebiliyor). **Bu dosyalar bu
turda koşmadı ve doğrulanmadı** — sessizce "temiz" denip geçilmiyor,
burada açıkça yazılıyor. `ruff check .` de ayrıca çalıştırıldı: temiz.

Hariç tutulan dosyalar ve sayı, Görev 2 raporunda (`task-2-report.md`)
uygulanan aynı hariç tutma listesiyle birebir aynı; o turda da (263 passed,
1 skipped) aynı sonuç alınmıştı — çalışan paneli turunun içinde regresyon
yok.

### Göç `c4f1a7d20b93` — kopya sayımı (Görev 2'den, doğrulanmış)

**Yerel geliştirme veritabanı (`vardiya`):** göç ilk uygulandığında **0
kopya** vardı — `[goc c4f1a7d20b93] kopya:` satırı hiç basılmadı, silinen
satır sayısı 0. Bugün bu görev kapsamında aynı veritabanında tekrar
sayıldı ve hâlâ boş:

```sql
SELECT personel_id, tarih, count(*) FROM tercih
GROUP BY personel_id, tarih HAVING count(*) > 1;
-- 0 satır
```

`alembic current` → `c4f1a7d20b93 (head)`, `alembic heads` ile tek başlıklı.

**Test veritabanı (`vardiya_test`) — ayrı bir gerçek, karıştırılmasın:**
orada **1 kopya bulundu ve silindi** (`personel=6862 tarih=2026-08-18
adet=2`, silinen satır `[414]`). Bu, üretim verisi DEĞİL — Görev 2'nin RED
aşamasında, kısıt henüz yokken, çakışan iki `Tercih` satırı yaratan bir
testin bıraktığı yapay artıktı; dedup mantığının kendi kanıtı oldu. Yerel
geliştirme ortamında hiçbir zaman gerçek kopya görülmedi.

### Kalan / ertelenen

- Görev 8'in kendisi tamamen bitti; bu turda ertelenen kod işi yok.
- On bir ağır çözücü test dosyası bu koşumda doğrulanmadı (yukarıda
  listelendi) — bir sonraki oturumda PostgreSQL zaten ayaktayken ve sandbox
  dışında (ya da daha yüksek zaman aşımıyla) tek tek çalıştırılıp
  doğrulanmalı.
- Tur 10, İş 4 (Ağırlık Kalibrasyonu) hâlâ **KISMEN** durumda duruyor — K3
  eşiği geçmiyor, zaman limiti kararı proje yürütücüsünde bekliyor (aşağı
  bakınız). Görev 8 bunu etkilemedi, etkilemesi de beklenmiyordu.

### DOKÜMAN BORCU

Dört kanonik doküman (Charter, SRS, SDD, Backlog) bu turda değiştirilmedi;
aşağıdakiler bir sonraki doküman geçişinde işlenmeli:

- **SDD 6.1** — dönem özeti artık `/api/calisan/vardiyalarim` içinde değil,
  kendi uç noktası `GET /api/calisan/ozetim?ufuk=donem|adalet`te; ufuk
  parametresi doğrudan `AnalizServisi.hesapla`'ya geçiyor ve yanıtta
  yankılanıyor (`adil_pay_*`, `hedef_saat` alanları istemciye taşınıyor).
- **SRS FR-9.6** — bir çalışan bir gün için tek tercih bildirebilir:
  ikinci bildirim, gün BEKLEMEDE ise mevcut kaydın üstüne yazar (aynı
  `tercih_id` korunur); gün KARARLANMIŞ (ONAYLANDI/REDDEDILDI) ise HTTP 409
  döner. Veritabanı düzeyinde `uq_tercih_personel_tarih` (personel_id,
  tarih) kısıtıyla zorlanıyor (göç `c4f1a7d20b93`).
- **SDD Ek B** — yeni uç nokta `GET /api/calisan/ozetim` (ufuk parametresi,
  yanıt gövdesi) ve `POST /api/calisan/tercih`'in 409 yanıt kodu Ek B'nin
  uç nokta tablosuna eklenmeli.

### Dağıtım öncesi sayım — dağıtımdan önce sunucuda çalıştırılacak

`alembic upgrade head` üretim veritabanında çalıştırılmadan önce şu sayım
yapılmalı ve sonucu buraya (ya da dağıtım kaydına) geçilmeli. Sorgu artık
`durum`u da taşır (final review bulgu 3): göç, bir kopya grubunun içinde
BEKLEMEDE-DIŞI (onaylanmış/reddedilmiş) bir kayıt bulursa artık **otomatik
silmez, DURUR** — operatörün önceden hangi (personel_id, tarih) çiftlerinin
elle triaj gerektirdiğini bilmesi için `durum` sütunu sayımın bir parçası:

```sql
SELECT personel_id, tarih, count(*), array_agg(durum::text ORDER BY tercih_id) AS durumlar
FROM tercih
GROUP BY personel_id, tarih HAVING count(*) > 1;
```

Sonuç boş değilse VE herhangi bir grubun `durumlar`ı yalnızca BEKLEMEDE
değilse (yani içinde ONAYLANDI/REDDEDILDI varsa), `alembic upgrade`
**patlayacaktır** (göç kasıtlı olarak `RuntimeError` fırlatır) — o satırlar
önce elle triaj edilmeden dağıtım yapılmamalı. Gruplar tamamen BEKLEMEDE
ise göç eskisi gibi en yeni `tercih_id` dışındakileri siler ve devam eder —
yerel geliştirme ortamında bu sayı şu ana dek hep 0 çıktı, ama üretim
verisi farklı olabilir.

### Sıradaki oturumun ilk işi

On bir ağır çözücü test dosyasını (yukarıdaki `--ignore` listesi) sandbox
dışında ya da uzatılmış zaman aşımıyla tek tek çalıştırıp bu turun
regresyon yaratmadığını doğrulamak. Ardından üretim dağıtımı öncesi yukarıdaki
sayım sorgusu gerçek sunucuda çalıştırılmalı.

---

## 2026-08-17 — Tur 10, İş 4: Ağırlık Kalibrasyonu — **KISMEN**

### Ölçüm aracı önce KIRIKTI ve bunu üç ölçüm boyunca fark etmedim

İlk araç `model_kur` + `CozucuAdaptoru.coz`'u doğrudan çağırıyordu. Üç farklı
ağırlık kümesinde **birebir aynı sayı** çıktı (K3 = 21,0, fazla çalışma 0).
Tur 9'da öğrendiğim işaret buydu: kurulum değişirken sonucun hiç değişmemesi.

Sebep ağırlıklar değildi — `durum=cozum_yok`, **sıfır atama**. Ölçülen şey boş
bir çizelgeydi: "0 saat fazla çalışma" boşluktan geliyordu, "21,0 sapma" ise
sapma değil en büyük adil payın kendisiydi (yük sıfırken |0 − pay| = pay).

**Kök neden ısıtma penceresi.** TD-5 ısıtma günlerinin SABİT GİRDİ olduğunu
söyler; doğrudan çağrı onları karar değişkeni bırakıyordu. Yedi gün × otuz
kişi × yirmi dört saatlik ek serbestlik, üzerinde talep bulunmayan ama bütün
zorunlu kuralların işlediği bir arama uzayı açtı; çözücü **yüz yirmi saniyede
bile** uygun çözüm bulamadı. Aynı dönem üretim yolunda altmış saniyede
çözülüyor.

**Ders:** ölçüm aracı üretim yolunu TAKLİT ETMEZ, ONU KULLANIR. Taklit ettiği
anda ölçtüğü şey ürünün davranışı olmaktan çıkar. Yeni araç
(`scripts/agirlik_kalibrasyonu.py`) `CozumServisi.baslat` + çözüm işçisini
çağırır ve boş çözümü sessizce ölçmek yerine yüksek sesle reddeder.

### Bir geri alma

Kırık ölçüme dayanarak "T-07'nin belirtisi artık yeniden üretilmiyor"
demiştim. **Yanlış.** Doğru ölçümde taban değerler: 7 kişi, 27 saat fazla
çalışma — backlog'un yazdığı "on kişi 32 saat"e yakın. T-07 duruyor.

### Ölçülen adaylar

Dengeli gösterim haftası (2026-08-03 – 08-09), 60 sn, 30 personel:

| Ağırlıklar | T-07 fazla çalışma | K3 azami / ortanca | Eşiği aşan | Toplam ceza |
|---|---|---|---|---|
| Taban: S2=10, S4=1 | 7 kişi / **27 sa** | 11,0 / 3,0 | 7/30 | 2059 |
| A: S4=8 | 5 kişi / 31 sa | 16,0 / 3,0 | 6/30 | 3912 |
| **B: S2=20, S4=4** | 6 kişi / **22 sa** | **11,0 / 2,0** | **3/30** | 3254 |
| C: S2=40, S4=4 | 6 kişi / 36 sa | 11,0 / 2,0 | 3/30 | 5442 |

**Seçilen: B (S2=20, S4=4).** Eşiği aşan kişi sayısı 7'den 3'e, ortanca sapma
3,0'dan 2,0'a indi; fazla çalışma 27'den 22 saate. A ve C'nin ikisi de fazla
çalışmayı kötüleştirdi — A çünkü S4 tek başına çok güçlendi, C çünkü S2
ötekileri ezmeye başladı. S1 baskınlığı dört kurulumda da korunuyor
(10000 > 5442, en kötü hâlde).

### T-08 ayrıştırıldı: iyileşme SÜREDEN geliyor, kalibrasyondan değil

İlk 300 sn ölçümü iki değişkeni birden değiştirdiği için yorumlanamazdı
(hem yeni ağırlıklar hem uzun süre). Ayırt edici ölçüm koşuldu — hepsi
**referans örneğinde** (40 personel × 28 gün), K3'ün kabul kriteri olarak
tanımlı olduğu yerde:

| Ağırlıklar | Limit | K3 azami | Eşiği aşan |
|---|---|---|---|
| S2=10, S4=1 (eski) | 60 sn | 25,00 | 10 |
| **S2=20, S4=4 (yeni)** | **60 sn** | **22,00** | **10** |
| S2=20, S4=4 (yeni) | 300 sn | **12,00** | **1** |

**Kalibrasyonun payı: 25 → 22** (%12, aşan sayısı değişmedi).
**Sürenin payı: 22 → 12** (%45, aşan sayısı 10'dan 1'e).

Yani iyileşmenin neredeyse tamamı arama süresinden geliyor. T-08'in kendi
uyarısı tam da buraya düşüyor: *"ölçüm koşulunu değiştirerek kriteri
geçirmek yerine nedeni giderilmeli."* 300 saniye kriteri geçirmeye
yaklaştırıyor ama nedeni gidermiyor — çözücü hâlâ baskın ağırlıklı S1'i
erken halledip adalet hedeflerine geç sıra veriyor, yalnızca ona daha çok
zaman tanınmış oluyor.

**Bir gözlem daha:** 300 saniyede yük aralığı 32–65, pay aralığı 33–64,1.
Yani otuz dokuz kişi payının içinde, kriteri düşüren **tek kişi** ve o da
12 saatlik sapmayla. Ölçünün azami sapma mı yoksa dağılım mı olması
gerektiği sorusu buradan doğuyor; Charter'ın kararıdır, burada yalnızca
görünür kılınıyor.

### K3'ün ölçüldüğü senaryo — bir yöntem hatası

K3'ü önce **dengeli gösterim haftasında** ölçtüm ve 300 saniyenin hiçbir şey
değiştirmediğini gördüm (11,0 → 11,0). Sebep: o senaryo 30 kişi × 7 gün ve
zaten 60 saniyeden çok önce en iyi çözümüne ulaşıyor; fazladan süre satın
alacak bir şey yok. T-08'in eğrisi ise **referans örneğinde** ölçülmüştü.

Kabul kriterlerinin her biri BELİRLİ BİR ÖRNEK üzerinde tanımlıdır ve bu,
ölçünün parçasıdır — eşiği kadar bağlayıcı. Aracı T-07 için kurup K3'ü de
oraya iliştirmek yanlıştı; ikisi aynı senaryoda ölçülemez.

### AÇIK: K3 hâlâ eşiği geçmiyor

Azami sapma 11,0, eşik 8. Kalibrasyon iyileştirdi ama geçirmedi. T-08'in kendi
teşhisi burada da geçerli: sapma çözücü süresine bağlı (60 sn'de 30, 900 sn'de
7 ölçülmüştü). Ağırlık aramasını daha ileri götürmek yerine **zaman limiti
kararının** verilmesi gerekiyor — T-08 zaten "ölçüm koşulunu değiştirerek
kriteri geçirmek yerine nedeni giderilmeli" diyor ve bu karar proje
yürütücüsünde.

### Yapılmayan

İş 5 (kapanış ölçümü + `PERFORMANS_NOTU.md` sürüm 3) — kalibrasyon
sonuçlanmadığı için başlanmadı.

---

## 2026-08-17 — Dağıtım: Tur 9 — **TAMAMLANDI**

Kesinti **10:37:31–10:38:17 (46 sn)** — bugüne kadarki en kısası. Kapsam dar
olduğu için: **göç yok, yeni bağımlılık yok, frontend değişmedi.** Yalnız
backend `rsync` + servis yeniden başlatma. `vera-rag` ve `energy-api`
boyunca ayakta kaldı.

Dağıtılan sürüm `1628c54` (= `origin/tur8-disa-aktarma`), çalışma ağacı temiz.

### Uygulanan sıra

1. Ön kontrol: bitmemiş çözüm işi **yok** (TAMAMLANDI 6, UYARILI 1), altı
   servis aktif, `alembic current` = `b8d21f6a90c3` — **yerelle aynı**,
   bekleyen göç yok.
2. `systemctl stop vardiya-cozucu`, ardından `vardiya-api`.
3. Yedek: `/opt/vardiya/yedek/vardiya-20260817-1037-tur9oncesi.dump`, **73K**.
4. `rsync` backend (`.env`, `.venv`, `__pycache__`, `*.pyc` hariç);
   `pip install -e ".[dev]"` → 0; `chown`.
5. `systemctl start vardiya-api`, `vardiya-cozucu`.

### Doğrulama

| Denetim | Sonuç |
|---|---|
| Altı servis | hepsi `active` |
| `127.0.0.1:8002/health` | `{"durum":"ok"}` |
| `/` \| `/api/ben` \| olmayan rota | 200 \| 401 \| **404** |
| `alembic current` | `b8d21f6a90c3 (head)` — değişmedi |
| `journalctl` hata satırı | 0 |
| `.env` sızıntı sayacı | 0 |

**Turun asıl konusu sunucuda sınandı.** Son dönem için `GecmisSayaclar`
çağrıldı: 90 günlük pencere (2026-05-19 .. 2026-08-17), **29 kişide gece
saati birikmiş** (en yükseği 118 saat), `calisabilir_oran` **0,54 ile 1,00**
arasında değişiyor. Yani hem birikim hem çalışabilirlik oranı gerçek veride
işliyor — oranın 1,00'dan farklı çıkması İş 2'nin ölü kod olmadığının
kanıtı.

### Beklenen davranış değişikliği

Mevcut yayınlanmış çizelgeler **değişmedi** (`atama` 1.282 satır, `sapma`
tabloları korundu — bu turda tablo boşaltan göç yok). Ama **Analiz
ekranındaki sapma sayıları büyüyecek**: ölçü artık tek dönem yerine doksan
günü kapsıyor. Gerileme değil, ölçünün tanımının değişmesi; K3'ün 34'ten
61,27'ye çıkması da aynı sebepten.

### SSH yine kesildi

Dağıtımdan önce SSH yedi denemede de zaman aşımına uğradı (biri ilk, altısı
60 sn aralıklı); site bu süre boyunca 200 dönüyordu ve **port 443 açık, port
22 filtreliydi** — yani makine sağlıklı, engelleme SSH'a özeldi. Muhtemel
sebep bu oturumdaki yoğun bağlantı sayısının `fail2ban`i tetiklemesi.
Denemeye ara verilince kendiliğinden düzeldi. Aynı belirti bir önceki
dağıtımda da görüldü; **teşhis yöntemi kayda değer**: 443 açık + 22 kapalı
ise sorun uygulamada değil erişimdedir.

---

## 2026-08-15 — Tur 9: Geçmiş Sayaçlar ve Kümülatif Adalet — **BİTTİ**

Kaynak: `docs/turlar/CLAUDE_CODE_PROMPTU_TUR9.md`. **Dört iş bitti, İş 5 ve
tur kapanış ölçümleri açık.** Doküman sürümleri doğrulandı: Charter **1.4**,
SRS **1.25**, SDD **1.32**, Backlog **1.22**.

### İş 1 — `GecmisSayaclar` · **BİTTİ**

`app/services/gecmis_sayaclar.py`. Kaynak yayınlanmış sürümlerin atamaları;
her dönem için **yalnız en son yayınlanan** sayılır (arşiv geçmişi iki kez
sayardı, taslak henüz olmamış bir çizelgeyi geçmişe yazardı). Ufuk bir
dönemin ortasına düşerse filtre **bloğun başladığı güne** bakar (TD-1) —
döneme bakılsaydı ya tamamı sayılır ya hepsi düşerdi. Önbellek yok.

Şekil ve aritmetik `app/kurallar/gecmis.py`de, veritabanı okuması serviste:
kural katmanı servis katmanını içeri almaz.

### İş 2 — Çalışabilirlik oranı · **BİTTİ**

Aynı serviste (ufkun tanımı ikiye bölünmesin diye). Aktiflik aralığı +
**yalnız tam gün** müsaitlik kayıtları; yarım gün izin günü düşürmez.
Kaydı olmayan personel 1.0 sayılır — varsayılan 0.0 olsaydı hakkında bilgi
bulunmayan kişi ölçünün tamamen dışına düşerdi.

### İş 3 — S2/S3/S4 kümülatif ufka geçti · **BİTTİ**

`adil_paylar` tek yer olarak kaldı ve `olcu` parametresi aldı. Geçmiş yük
sabit terim (karar değişkeni değil), geçmiş pay hedefe ekleniyor, pay son
adımda çalışabilirlik oranıyla ölçekleniyor.

### İş 4 — H10'un devri türetiliyor · **BİTTİ**

Türetilen kota yılı içi fazla çalışma **artı** kayıt alanı; `Baglam.
yasal_devir` tek erişim noktası. Eşik bağlam kurucuda H10'un kendi kayıt
satırından okunuyor — **çağıranlara parametre olarak bırakılmadı**, çünkü
onu vermeyi unutan her yol sessizce eski davranışa döner ve kota olmadığı
kadar boş görünürdü.

Dört tüketici de (çözücü, ön kontrol, analiz, dışa aktarma) `baglam_olustur`
üzerinden geçtiği için beşinci bir hesap yeri açılmadı.

### Yol boyunca bulunan iki hata

1. **`_turetilen_fazla_calisma` personel döngüsünün içindeydi.** Aynı ağır
   sorgu kişi sayısı kadar koşuyordu; tam takım 10 dakikadan 25 dakikaya
   çıktı. Pencere başına bir kez hesaplanacak şekilde düzeltildi (kota yılı
   kişiye göre değişebildiği için önbellek `yil_bas` anahtarlı).
2. **Ortak sapma teriminde `ust_sinir += gecmis`** parametreyi kalıcı
   büyütüyordu: bir kişinin geçmişi sonraki herkesin üst sınırını şişirirdi.
   Kişiye özel değişkene alındı.

### AÇIK — İş 3'ün uçtan uca kabul testi yazılamadı

Turun istediği "iki dönemi ardışık çözüp aynı kişinin yükünü karşılaştıran"
test **üç denemede de ayırt edici olmadı** ve kaldırıldı. Nedeni koddaki bir
eksiklik değil, **test veritabanının paylaşımlı olması**:

- İlk hâli ufuk **kapalıyken de** geçiyordu. `baglam_olustur` veritabanındaki
  tüm aktif personeli yükler; test veritabanında başka testlerden kalan 30+
  kişi var ve nöbetler onlara dağılıyordu.
- Havuz yetkinlikle kapatıldı, ölçüm yarışılan noktayla sınırlandı, S4'ün
  çekişi `haftalik_hedef_saat=0` ile kaldırıldı — **üçünde de sonuç aynı
  kaldı** (46'ya 41, yanlış yönde). İki kişi tek noktada üst üste yığılıyor.

Mekanizma **14 birim testiyle** kanıtlı (`test_gecmis_sayaclar.py` 8,
`test_kumulatif_adalet.py` 6): geçmiş yükün cezaya girdiği, yük ile hedefin
birlikte ölçeklendiği, oranın payı küçülttüğü ve **yönün** doğru olduğu
(yük > pay / yük < pay) dahil. Eksik olan uçtan uca kabuldür.

**Karar proje yürütücüsünde:** kabul testi için izole bir test şeması mı
açılsın, yoksa madde Tur 10'a mı bırakılsın?

### Test takımı — 387 yeşil, ama önce yanlış okundu

Tam takım **387 geçti** (373 + 14 yeni), 10 dk 14 sn. Süre eski seviyesinde:
yukarıdaki N× sorgu hatası düzeltilmeseydi 25 dakikaydı.

**Arada beş test kırık göründü ve bu bir YANILGIYDI.** Sebebi kodda değil,
arka planda **iki tam pytest koşusunun aynı test veritabanına aynı anda
vurmasıydı** — benim arka plan işlerini üst üste başlatmamdan.
`StaleDataError: UPDATE ... expected to update 1 row(s); 0 were matched`
bunun imzası. Tek koşuya inilince hepsi yeşil.

Aynı kök neden kaldırılan kabul testini de açıklıyor olabilir: üç farklı
kurulumda **birebir aynı sayılar** (46'ya 41) çıkmıştı ve kurulum
değişirken sonucun hiç değişmemesi, ölçülen şeyin o senaryo olmadığına
işaret ediyor.

**Ders:** bu depoda testler paylaşımlı bir PostgreSQL şemasına yazıyor;
ikinci bir koşu başlatmadan önce birincisinin bittiğinden emin ol.

### İş 5 — gösterim verisi · **BİTTİ**

Üç ardışık yayınlanmış dönem zaten vardı (H-2, H-1, H-0; dar hafta
yayınlanmadığı için zincir orada kırılıyor). Eksik olan tek şey **ufkun
ortasında işe başlamış personeldi**: herkes 365 gün önce başlıyordu, yani
`calisabilir_oran` herkeste 1,0 çıkıyor ve İş 2 hiçbir ekranda görünmüyordu —
kod çalışıyormuş gibi duruyordu. `GG-020` 45 gün önce başlatıldı, oranı 0,50.

### Kabul testi geri getirildi ve **GEÇTİ**

Silmek hataydı; `xfail` ile geri kondu, düzeltildi ve yeşile döndüğü için
işaret kaldırıldı. Test gösterim verisi olmayan bir veritabanında **atlar**.

**Dördüncü deneme neyi öğretti:** yön yanlış değildi, **karşılaştırma**
yanlıştı. Test "en çok taşıyan" ile "en az taşıyan"ı seçiyordu ve ikisi
farklı yetkinlik havuzlarındaydı (VS-001 vardiya şefi, GG-020 güvenlik
görevlisi) — aynı nöbetler için yarışmayan iki kişinin gece saatini
karşılaştırmak anlamsız. Üstelik "hafif" sayılan kişi tam da ufkun ortasında
işe başlayandı; payı zaten yarılanmış, az taşıması **doğru davranış**.

Aynı havuz içinde ve yalnız ufkun tamamında çalışabilenler arasında bakınca:

| Havuz | En çok taşıyanlar → 3. dönem | En az taşıyanlar → 3. dönem |
|---|---|---|
| Vardiya Şefliği (2 kişi) | **16** | 23 |
| Güvenlik (20 kişi) | **12,3** ort. | 14,2 ort. |

Tekil kişi yerine üçte bir dilim karşılaştırılıyor: tek kişi çözücünün o
dönemki eşitlik tercihine fazla duyarlı, dilim ortalaması eğilimi ölçer.

### Kabul ölçümü — betik İKİ TURDUR KIRIKMIŞ

`scripts/kabul_olcumu.py` çalıştırılınca iki ayrı yerde patladı; ikisi de bu
turdan değil:

1. `saatleri_araliklara_birlestir` **B-23'ten beri (Tur 8)** üç değer
   döndürüyor, betik dört açıyordu. Tarih artık ayrı alan değil, başlangıç
   damgasından türetiliyor (TD-1).
2. `AtamaDegisikligi` **Tur 7'de (TD-16)** `surum_id` almayı bıraktı ve
   `dogrula` tek değişiklik yerine bekleyen kümenin tamamını alır oldu.

İkisi de düzeltildi. **Asıl bulgu betiğin kendisi değil:** SDD 5.9 bu betiği
`GecmisSayaclar`ın dört tüketicisinden biri sayıyor, ama iki tur boyunca hiç
koşmadığı için kimse fark etmedi. Turun kapanış listesinde olmasaydı bu tur
da fark edilmeyecekti.

### K1 / K3 ölçümü

| Kriter | Eşik | Ölçülen | Durum |
|---|---|---|---|
| K1 — 40 personel × 28 gün | < 60 sn | **12,18 sn** | geçti |
| K2 — zorunlu ihlal | 0 | 0 | geçti |
| K3 — gece yükü sapması | ≤ 8 | **61,27** | kaldı |
| K4 — açık gösterimi | ≥ 1 açık, tam bilgi | 147 aralık | geçti |
| K5 — düzenleme doğrulaması | < 1 sn | 0,081 sn | geçti |

**K1:** geçmiş sayaçlar model kurmaya eklendi ama artış eşiğin yarısının
(30 sn) çok altında kaldı — durma koşulu oluşmadı.

**K3 — Tur 10'un kalibrasyonuna not.** Değer 34'ten **61,27'ye çıktı**, yani
kümülatif ufuk sapmayı **yukarı** taşıdı. Bu beklenen bir yöndür ve
ağırlıklara dokunulmadı (turun talimatı). Dikkat edilmesi gereken şey
şudur: **eşik ile ölçü artık aynı ufku kapsamıyor.** Charter 1.4'ün 8 gece
saati eşiği TEK DÖNEM için kalibre edilmişti; ölçü ise artık doksan günü
kapsıyor ve doğal olarak daha büyük bir mutlak sapma üretiyor. Tur 10 ya
eşiği ufka orantılamalı ya da K3'ü dönem içi sapmayla ölçmelidir; ağırlık
kalibrasyonu bu karardan önce yapılırsa yanlış hedefe ayarlanır.

**Ulaşılabilirlik teşhisi:** "her havuz hedefe erişebiliyor" diyor —
31 kişilik havuzda kişi başı tavan 42,58; 9 kişilik havuzda 177,78.

### Çözücü–doğrulayıcı uyumu

`test_cozucu_dogrulayici_uyumu_olcek.py` **24/24** geçiyor (6 dk 25 sn).
Kümülatif ufuk iki yorumlayıcının aynı sayıyı üretmesini bozmadı.

### Ters sıralı koşu — sıra bağımlılığı yok

| Sıra | Sonuç |
|---|---|
| İleri | 363 geçti, 1 atlandı (3 dk 55 sn) |
| Ters (`ls -r`) | **363 geçti, 1 atlandı** (3 dk 56 sn) |

Ölçek testi (24 örnek, 6,5 dk) ikisinden de hariç tutuldu; tam takım zaten
ayrıca koşuldu (387 geçti, 1 atlandı).

`--reverse` bayrağı bu kurulumda yok (pytest-reverse kurulu değil); dosyalar
`ls -r` ile ters sırada verildi. İlk denemede bayrak hata verdi ve yedek
komut **çalışmadı**: `cmd | tail || yedek` yazılmıştı ve boru hattının çıkış
kodu `tail`'inki (0) olduğu için `||` hiç tetiklenmedi. Kısa süre "koşuyor"
diye rapor edildi; düzeltildi.

### Turun bitiş kontrolü

- [x] Tam takım geçiyor — 387 geçti, 1 atlandı (atlanan: kabul testi, test
      veritabanında gösterim verisi yok)
- [x] Ters sıralı koşu aynı sonucu veriyor
- [x] `ruff` temiz (bu turda frontend değişmedi)
- [x] Uyum testi 24/24
- [x] Kabul ölçümü koşuldu; K1 = 12,18 sn
- [x] K3 ayrıca kaydedildi: 34 → 61,27
- [x] Ulaşılabilirlik teşhisi "her havuz hedefe erişebiliyor"

### Tur 10'a taşınan iki soru

1. **K3'ün eşiği ile ölçüsü aynı ufku kapsamıyor** (yukarıda). Ağırlık
   kalibrasyonu bu karardan önce yapılırsa yanlış hedefe ayarlanır.
2. **Kabul ölçümü betiği hiçbir otomatik koşumda değil.** SDD 5.9 onu
   `GecmisSayaclar`ın dört tüketicisinden biri sayıyor ama iki tur boyunca
   sessizce kırık kaldı. Takıma ya da CI'a alınması gerekir; aksi hâlde
   "dört tüketici tek kaynaktan beslenir" sözleşmesi denetimsiz kalıyor.

---

## 2026-08-14 — Düzeltme: Excel çıktısı arayüze bağlanmamıştı — **BİTTİ, DAĞITILDI**

**Tur 8 eksik teslim edilmişti.** Dört iş de bitmişti, testler yeşildi,
uç noktalar sunucuda çalışıyordu — ama `xlsx` kelimesi frontend'de **hiç
geçmiyordu**. Ekrandaki "Dışa Aktar" düğmesi hâlâ CSV üretiyordu, yani
özellik uygulamadan **ulaşılamıyordu**. Proje yürütücüsü dışa aktardığı
dosyaları gösterdi ve tabloların değişmediğini söyledi; gönderdiği iki
görüntü de CSV'ydi (sekme adı `cizelge_2026-07-13_2026-07-19_s`,
sütunlar `tarih, sicil, ad, …`).

Turun promptundaki dört iş de backend biçimindeydi ve ben de yalnız
backend'i yaptım. **Bir uç noktayı çağıran hiçbir şey yoksa iş bitmemiştir**
— testin yeşil olması özelliğin erişilebilir olduğunu söylemiyor.

### Yapılan

- `api.cizelgeExcelIndir` / `api.analizExcelIndir` — ayrı bir ikili indirme
  yolu. Ortak `istek` yardımcısı her gövdeyi JSON diye çözüyor, çalışma
  kitabı JSON değil. **401 ele alışı aynı kaldı**: atlansaydı oturumu
  kapanmış kullanıcı, sessizce inmeyen bir dosyayla baş başa kalırdı.
- **Dosya adı `Content-Disposition`'dan** okunuyor, istemcide yeniden
  kurulmuyor — ad sunucudaki `dosya_adi()`'nda tek yerde duruyor.
- Çizelge ve Analiz ekranlarına **Excel** düğmesi; CSV düğmesinin etiketi
  ne olduğunu söylüyor (ham veri). İndirme sırasında düğme "İndiriliyor…"
  oluyor ve hata ekranın **mevcut** hata yüzeyine gidiyor, ikinci bir
  duruma değil.
- Üç yeni test (`src/api/client.test.ts`): ad başlıktan okunuyor, başlık
  yoksa yedek ada düşüyor, 401 dinleyiciyi tetikliyor.

**284 → 287 vitest**, `tsc -b` ve `oxlint` temiz.

### Dağıtım

Yalnız arayüz değişti; göç yok, servis durdurulmadı. `rsync` 35 dosya,
ardından `chown`. Doğrulama, bir önceki turda öğrenilen tuzağa göre
yapıldı — HTTP 200 kanıt değil (Caddy geri düşüşü):

| Denetim | Sonuç |
|---|---|
| Canlı `index.html` paketi | `index-DnwLQ1gd.js` = yerel derleme |
| Pakette `cizelge.xlsx` / `analiz.xlsx` | 1 / 1 eşleşme |
| Pakette `Content-Disposition` | 1 eşleşme |
| `web/assets` içinde kalan paket | tek (eski silindi) |

---

## 2026-08-14 — Dağıtım: Tur 7 + 8 — **TAMAMLANDI**

Gösterim sunucusuna (46.225.109.40) çıkıldı. Kesinti **13:29:44–13:32:06
(2 dk 22 sn)**. `vera-rag` ve `energy-api` boyunca ayakta kaldı — ikisinin
de `ActiveEnterTimestamp` değeri 8 Ağustos'ta duruyor, yani hiç yeniden
başlamadılar. Ortak PostgreSQL'e dokunulmadı.

Dağıtılan sürüm `f4bcfc0` (= `origin/tur8-disa-aktarma`), çalışma ağacı
temiz. Yordam yine yerelde derle + `rsync`; `deploy/DAGITIM.md` geçerli.

### Uygulanan sıra

1. Yerelde `npm run build`, `tsc -b` (0), **284 vitest**. Backend takımı
   `c828261`'de 373 yeşildi; üzerine gelen tek commit yalnızca doküman
   dosyalarına dokunduğu için yeniden koşturulmadı.
2. Ön kontrol: bitmemiş çözüm işi **yok** (`cozum_isi` yalnız TAMAMLANDI 6
   + UYARILI 1), beş servis de aktif, `alembic current` = `f2a8c561d94b`.
3. `systemctl stop vardiya-cozucu`, ardından `vardiya-api`.
4. Yedek: `/opt/vardiya/yedek/vardiya-20260814-1330-tur7ve8oncesi.dump`,
   **70K**, `pg_restore -l` ile denetlendi (155 nesne, 19 tablo verisi).
5. `rsync`: `frontend/dist/` → `web/` (37 dosya), `backend/` → `backend/`.
   `.env`, `.venv`, `__pycache__`, `*.pyc` hariç tutuldu.
6. `pip install -e ".[dev]"` → çıkış 0; **`openpyxl` 3.1.5** kuruldu (Tur
   8'in yeni bağımlılığı, sunucuda yoktu). `chown -R vardiya:vardiya`.
7. `alembic upgrade head` → iki göç koştu, çıkış 0.
8. **`sapmalari_yenile` yedi sürümün hepsi için koşturuldu** — servisler
   *açılmadan önce*, uygulama eksik veriyle görünmesin diye.
9. `systemctl start vardiya-api`, `vardiya-cozucu`.

### `alembic current` — önce / sonra

```
önce : f2a8c561d94b
sonra: b8d21f6a90c3 (head)
```

### Göç doğrulaması — sayarak

| Ölçü | Önce | Sonra |
|---|---|---|
| `atama` satırı | 1.117 | **1.117** |
| `cizelge_surumu` / `personel` | 7 / 30 | 7 / 30 |
| `kapsama_acigi` | 9 | **0 → 8** (yenilendi) |
| `fazla_kadro` | 17 | **0 → 111** (yenilendi) |

Dört sayı da doğrudan `psql` ile sayıldı. Yenileme sonrası 8 ve 111,
`sapmalari_yenile`'nin yedi sürüm için döndürdüğü `SapmaOzeti`
toplamlarıyla da örtüşüyor (`eksik_hucre` 0+7+0+0+0+0+1, `fazla_hucre`
20+8+14+15+19+18+17) — fonksiyonun bildirdiği ile tabloda duran aynı.
| `cizelge_surumu.damga` boş olan | — | **0** |

`kapsama_acigi` sütunları artık `baslangic_zamani, bitis_zamani`; `tarih`,
`baslangic`, `bitis` düştü. Toplam kişi-saat 8.136.

**Sapma tablolarının boşalması göçün tasarımı gereğidir**, kayıp değil:
`b8d21f6a90c3` satırları siler çünkü eski `tarih + ofsetsiz saat` şeklinden
zaman damgasına birebir çeviri mümkün değil. Yeniden hesap atamalardan
yapılır ve tek doğru kaynak zaten atamalardır.

### Doğrulama

- `systemctl is-active`: vardiya-api, vardiya-cozucu, vera-rag, energy-api,
  postgresql, caddy → **altısı da active**
- `http://127.0.0.1:8002/health` → `{"durum":"ok"}`
- `GET /api/ben` kimliksiz → **401**
- `https://vardiya.omerharmankaya.com/assets/index-BNyTOpfe.js` → **200**
- `journalctl` (başlatmadan beri): **0 hata satırı**
- Turun asıl konusu sınandı: `/api/surum/{id}/cizelge.xlsx` ve
  `analiz.xlsx` rotaları kayıtlı, kimliksiz çağrıda **401** (404 değil —
  yani rota var ve yetkilendirme çalışıyor)

### `.env` denetimi

`TEST_VERITABANI_URL` ve `VERI_TEMIZLIGINE_IZIN` sayısı: **0**. İkisi de
sunucu `.env`'ine hiç yazılmadı.

### Dağıtım sonrası ikinci tur doğrulama

Dağıtımdan bir süre sonra hepsi yeniden sınandı; **SSH bir aralık
erişilemez oldu** (üç deneme: iki `Operation timed out`, bir `Network is
unreachable`), sonra kendiliğinden döndü. Uygulama bu süre boyunca ayakta
kaldı — kesinti SSH katmanındaydı, servislerde değil. SSH dönünce:

| Denetim | Sonuç |
|---|---|
| `kapsama_acigi` \| `fazla_kadro` | **8 \| 111** — `psql` ile sayıldı |
| `alembic current` | `b8d21f6a90c3 (head)` |
| Sunucudaki `disa_aktarma_servisi.py` | `_SAAT_BANDI` / `_EN_ACIK_SAAT` **var** — yani `c828261`'in biçim düzenlemesi gerçekten sunucuda |
| `openpyxl` | 3.1.5 |
| Altı servis | altısı da `active` |
| `.env` sızıntı sayacı | 0 |

**HTTP tarafında bir tuzak:** Caddy tek sayfa uygulaması için geri düşüş
yapıyor, yani `/assets/...` altındaki **var olmayan** bir dosya da 200
dönüyor (`/assets/BU-DOSYA-YOK-12345.js` → 200 ile doğrulandı). Paketin
yerinde olduğunu "200 aldım" diye kanıtlamak bu yüzden geçersiz; doğru
kanıt `index.html`'in işaret ettiği paket adının yerel derlemeyle
eşleşmesi (`index-BNyTOpfe.js`) ve paket içeriğinde turun eklediği metnin
bulunması (`Düzenlemek İçin Kopyala` → 1 eşleşme). `/api` altında geri
düşüş yok: var olmayan rota 404, dışa aktarma rotaları 401 veriyor.

---

## 2026-08-14 — Tur 8: Dışa Aktarma — **BİTTİ**

Kaynak: `docs/turlar/CLAUDE_CODE_PROMPTU_TUR8.md`. Dört iş, hepsi bitti.
Çalışma `tur8-disa-aktarma` dalında yürüdü.

Doküman sürümleri turun başında doğrulandı: Charter **1.4**, SRS **1.24**,
SDD **1.31**, Backlog **1.21** — dördü de taşıyor.

### İş 1 — B-23: sapma kayıtları zaman damgasına

`kapsama_acigi` ve `fazla_kadro` `tarih` (DATE) + `baslangic`/`bitis` (TIME)
yerine `baslangic_zamani`/`bitis_zamani` (TIMESTAMPTZ) taşıyor. Göç
**`b8d21f6a90c3`**; sıfırdan koştu, geri alma yazıldı ve **denendi**.

**Mevcut kayıtlar dönüştürülmedi, silindi.** Bu iki tablo bir çözümün
çıktısıdır, kullanıcının girdiği veri değil; `sapmalari_yenile` bir sonraki
çözümde ya da elle düzenlemede doğru biçimde yeniden yazar. Aynı karar Tur
3'te talep göçünde de verildi.

**Asıl kazanç birleştiricide.** `saatleri_araliklara_birlestir` artık gün
sınırında **kesmiyor**. O kesme doğru olduğu için değil, depolama
22.00–02.00'yi ifade edemediği için vardı; damga sınırı kendisi taşıdığı
için bir açık artık bir kayıt.

Sapma kaydının gün/aralık okuması `blok.ts`te **tek yere** toplandı
(`sapmaGunu`, `sapmaEtiketi`, `sapmaSuresi`) — beş ayrı yerde `k.tarih`
ayıklamak yerine. Sapma CSV'si ISO damgasına geçti ve `tarih` sütunu düştü
(SRS 7.2).

### İş 4 — DisaAktarmaServisi: ikinci hesap yok

Veri mevcut okuma yüzeylerinden: kapsama oranı, toplam saat, adil pay ve
sapma `AnalizServisi`'nden; açıklar kapsama kayıtlarından; fazla çalışma
**H10'un kendi fonksiyonundan**.

O fonksiyon kuralın `dogrula`sının içinde gömülüydü; paylaşılabilmesi için
`h10_fazla_calisma_saatleri` olarak dışarı çıkarıldı — `s4_hedef_paylari`
ile aynı kalıp. Dışa aktarma kendi toplamını hesaplasaydı dosyada,
sistemin başka hiçbir yerinde bulunmayan ve doğruluğu denetlenemeyen bir
sayı olurdu.

Uç noktalar dosyayı **doğrudan** döndürüyor; iş kuyruğu kurulmadı.

### İş 2 — Çizelgenin Excel çıktısı

Üç sayfa: **Çizelge** (personel × gün), **Özet** (kişi başına toplam/gece/
hafta sonu/fazla çalışma/kalan kota), **Ham veri** (blok başına satır, ISO
damgası — CSV ile aynı içerik). Başlıkta dönem, sürüm, üretim tarihi,
kapsama oranı ve toplam açık.

**Hücre dolgusu bilgiyi tek başına taşımıyor.** Saat aralığı hücrede metin
olarak da yazılı ve bir açıklama satırı dolgunun ne demek olduğunu
söylüyor; renksiz basılan çıktı bilgi kaybetmiyor. Dolgu üç basamağa
indirgendi (gece / kısmen gece / gündüz) — Excel hücresi sürekli bir
gradient taşıyamaz, ve basamak sayısı zaten bilgi taşımıyor.

### İş 3 — Analizin Excel çıktısı

Dört sayfa: **Özet** (kapsama, toplam ceza, hedef bazında döküm),
**Adalet** (kişi başına gece/hafta sonu/toplam saat + adil pay + sapma, üç
grafik), **Kapsama açıkları**, **Ham veri**.

**Grafiklerin referans çizgisi kişiye düşen ADİL PAY.** openpyxl'de
"referans çizgisi" diye bir nesne yok; çubuk grafiğin üzerine ikinci bir
çizgi grafik bindiriliyor. Çizgi kişiden kişiye değiştiği için düz yatay
bir çizgi DEĞİL — zaten öyle olması yanlış olurdu (S2: hedef kişiye
özeldir). Havuz ortalamasını dosyaya taşımak, ekranda bir kez yapılıp Tur
6'da düzeltilen hatayı geri getirmek olurdu.

### Kabul testleri

`test_disa_aktarma.py`, **11 test**:

- **Dosya ile ekran birebir aynı.** Toplam saat, adil pay, sapma, gece
  saati ve gece adil payı `AnalizServisi`'nin döndürdüğüyle alan alan
  karşılaştırılıyor; kapsama oranı başlık bloğunda aynı değerde.
- **Gece yarısını aşan açık tek satırda okunuyor** — `22.00–02.00`, bölünmüş
  değil.
- Açık yokken sayfa bunu açıkça söylüyor (boş sayfa "açık yok" ile "rapor
  üretilmedi" arasındaki farkı söylemez).
- Uç noktalar gerçekten açılabilir bir çalışma kitabı döndürüyor.

### Yeni bağımlılık

`openpyxl==3.1.5`. Saf Python, derleme gerektirmez ve grafik üretebilir.
Sürüm sabitlemesi diğerleriyle aynı sözleşmede.

### DOKÜMAN BORCU — bir madde

**SRS 7.2 — çizelge CSV'sinde `tarih` sütunu.** Sütun listesi `tarih`
içermiyor ve gerekçesi yazılı ("blok başladığı gün başlangıç damgasından
türetilir"), ama hemen altındaki paragraf "tarih sütunu … başa alınmıştır"
diyor. İkisi aynı bölümde çelişiyor. Tur CSV'ye dokunmayı istemediği için
çizelge CSV'si olduğu gibi bırakıldı (`tarih` duruyor). Sapma CSV'sinde
çelişki yoktu; orada `tarih` kalktı.

### Yerel veriye dokunuldu

Göç sapma kayıtlarını sildiği için `sapmalari_yenile` bütün sürümlerde
koşturuldu ve kayıtlar atamalardan yeniden hesaplandı (çözücü gerekmedi).
Dar hafta yine 10 açık aralığı / 36 kişi-saat gösteriyor; sürüm 34'te 12
aralık / 1.152 kişi-saat.

### Turun bitiş kontrolü

- [x] `pytest` tam takım **371 test geçiyor**
- [x] `ruff`, `tsc -b`, `oxlint` temiz; **284 frontend testi** geçiyor
- [x] Göç sıfırdan çalışıyor, geri alma yazılmış ve denenmiş
- [x] Ekran ile dosyanın aynı sayıyı verdiğini gösteren test
- [x] Gece yarısını aşan açık aralığının dosyada okunabildiğini gösteren test
- [x] `EK_B_UC_NOKTALAR.md` yeniden üretildi — **70 uç nokta**, denetim temiz
- [ ] `git status` temiz — dört kanonik doküman proje yürütücüsünde açık

**Bir koşum yanılttı.** Tam takımın bir önceki koşumunda
`test_kullanici_api`'de bir hata görünmüştü; testleri veritabanına dokunan
başka işlerle **aynı anda** koşturmaktan geliyordu. Tek başına koşan takım
371/371 geçiyor.

### Örnek çıktılar

`ornek-ciktilar/cizelge.xlsx` ve `ornek-ciktilar/analiz.xlsx` (dizin
`.gitignore`'da — üretilebilir çıktı). Dar haftadan (20–26 Tem, sürüm 29)
üretildi; kapsama sayfasında on açık aralığı var ve ilki gece yarısını
aşıyor.

**Gözle bakılacaklar:** hücre dolgusunun okunabilirliği, sütun
genişliklerinin saat metnini kesip kesmediği (`08.00–16.00` iki satıra
sarıyor; sütun 13 birim), grafiklerin referans çizgisinin görünürlüğü.

### Ek iş — çıktılar örnek dosyalara göre düzenlendi

Proje yürütücüsü `ornek-ciktilar/`e iki **hedef** dosya bıraktı
(`cizelge_ornek.xlsx`, `analiz_ornek.xlsx`). Çıktı bunlara göre yeniden
biçimlendi; farklar hücre hücre karşılaştırılarak kapatıldı.

**Renk artık tek bir ölçüden geliyor.** Dolgu, bloğun **başladığı saatten**
türeyen 13 adımlı bir bant: 13.00 en açık, 01.00 en koyu, arası sürekli.
Önceki sürüm "gece / kısmen gece / gündüz" diye üç kovaya bölen **ayrı** bir
ölçü kullanıyordu — yani aynı bilgi ekranda (SDD 6.3.3 renk bandı) ve
dosyada iki farklı biçimde tanımlıydı. Artık ikisi aynı şeyi söylüyor.

**Ceza dökümünün kaynağı düzeltildi.** Ham değerleri kuralların `dogrula`sını
yeniden çağırarak üretmeyi denedim; S2/S3/S4'te ekrandakinden **farklı**
sayılar çıktı (269/119/443 yerine 148/54/209). `dogrula` çözüm anının
bağlamını bilmiyor. Döküm `analiz.ceza_dokumu`ya alındı — modülün başındaki
"ikinci hesap yapılmaz" kuralının tam da uyardığı hataydı. Yeni bir test
Σ(ham × ağırlık) = `toplam_ceza` eşitliğini kilitliyor.

**Ölçü ayrımı dosyaya yazıldı.** "10 aralık" ile "36 kişi-saat" farklı
şeylerdir (ardışık saatler tek kayıtta birleşir); ikisi de ayrı ayrı
gösteriliyor ve aralarındaki fark bir not satırıyla söyleniyor. Kapsama
sayfasına `Kişi-saat` sütunu eklendi.

**Toplam satırları canlı formül** (`=SUM(...)`, `=C10*D10`): okuyucu satır
süzdüğünde ya da ağırlık değiştirdiğinde sonucu dosyada görür.

Ayrıca: Türkçe tarih (`20.07.2026`) ve ondalık virgül (`%96,9`) — ham veri
sayfaları ISO kalır, orası makine için; nokta adı hücrede üç harfe kısaldı;
adalet grafikleri üçten ikiye indi ve ölçülen değer ile adil pay **yan yana
iki çubuk** oldu (önceki çizgi bindirmesi, adil pay kişiye özel olduğu için
yanıltıcı bir "eğilim" görüntüsü veriyordu).

**Örnekten bilerek sapılan iki nokta:**

1. **Açık olan günün başlığı turuncu kalıyor**, örnekteki gibi düz yeşil
   değil. Örnek başlık bandını baştan biçimlendirirken bu işareti düşürmüş
   ama altındaki açıklama satırı ondan söz etmeyi sürdürüyor; işaret
   kalkarsa açıklama yalan söyler.
2. **S6/S8 adları ve S6 ağırlığı** örnektekinden farklı (`Çalışma deseni
   tutarlılığı` / `Değişim minimizasyonu`, ağırlık 4). Ad kuralın kendi
   `ad` alanından, ağırlık veritabanından geliyor — ekranda da aynısı
   görünüyor. Excel'e özel kısa adlar yazmak tanımı ikiye bölerdi. Ağırlık
   farkı örneğin üretildiği katalog durumundan; buradaki 4 değeri
   `toplam_ceza` ile tutarlı.

---

## 2026-08-14 — Tur 7: Düzenleme Sistemi — **BİTTİ**

Kaynak: bu turun promptu. **Altı iş de bitti.** Çalışma
`tur7-duzenleme-sistemi` dalında yürüdü.

Doküman sürümleri turun başında doğrulandı: Charter **1.4**, SRS **1.23**,
SDD **1.30**, Backlog **1.20** — dördü de taşıyor.

> **İSİM ÇAKIŞMASI.** Bu dosyada bir alttaki kayıt da "Tur 7" adını
> taşıyordu (gösterim verisi ve tatil takvimi). O iş bir tur promptundan
> değil doğrudan istekten doğdu; karışmasın diye **"Ara iş"** olarak
> yeniden adlandırıldı. Numaralı Tur 7 budur.

### İş 5 — yazdırma yalnızca ilk günü basıyordu · **BİTTİ**

Teşhis doğrulandı, tahmin edilenden başkaydı. Önizleme `position: fixed` +
`overflow: auto` bir kabın içinde duruyor, baskı CSS'i de yazdırma alanına
`position: absolute` veriyordu. Üçü de öğeyi normal akıştan çıkarır ve **akış
dışı içerik sayfalanmaz** — tarayıcı ilk sayfayı çizip durur. Tek tablolu
çıktıda görünmüyordu (zaten bir sayfaya sığıyordu); Tur 6'da gün başına ayrı
ızgaraya geçilince yedi günlük dönem tek sayfa basmaya başladı.

Önizleme artık `document.body`'ye **portal** ile bağlanıyor, yani `#root`un
kardeşi; baskıda `#root` tümüyle gizleniyor. Uygulama yerleşimden düştüğü
için konumlandıracak bir şey kalmadı ve görünürlük hilesi de mutlak
konumlandırma da kaldırıldı.

jsdom sayfalama yapmaz, **"yedi sayfa çıktı" TEST EDİLEMEZ.** Test asıl
bozulan şeyi kilitliyor: önizleme gövdenin çocuğu olmalı, çünkü baskı kuralı
`#root`u gizleyerek çalışıyor.

### İş 6 — haftalık görünüm okunmuyordu · **BİTTİ**

Hücre artık saat aralığını **metin** olarak yazıyor ("08–16 GÜV"), altındaki
üç piksellik **düz** çubuk bloğun günün neresinde durduğunu gösteriyor.

Çubuk gradient değil: okunması gereken şey tam olarak **sınırdır**, gradient
sürekli olduğu için onu belirsizleştirir — sürekliliğin bant için erdem
olduğu yerde burada kusur. Çubuk saat rengini de taşımıyor; gündüz tonu
(#E9E7D9) hücre zemininden (#E4E7E1) ayırt edilemiyor ve üç piksellik bir
çubukta o fark tümüyle kayboluyor. "Gece mi gündüz mü" bilgisi zaten metinde.

Düğüm sayısı hücre başına sabit kaldı; performans testinin sınırı 1.000'den
**2.000**'e çıkarıldı (30 × 7 ölçümü ~1.400). Testin koruduğu şey bugünkü
sayı değil, sayının **dilim sayısından bağımsız** kalmasıdır.

### İş 2a + İş 3'ün sunucu tarafı — taslak oturum · **BİTTİ**

`dogrula(surum_id, degisiklikler)` oturumun **tamamını** alıp aday çizelgeyi
bellekte kuruyor ve **hiçbir şey yazmıyor** — işlem açmıyor, sapma
tablolarına dokunmuyor.

`kaydet(surum_id, degisiklikler, damga)` tek işlemde: `SELECT … FOR UPDATE`
→ durum → damga → **yeniden doğrula** → uygula → sapmaları tazele → yeni
damga. Kısmi kayıt yok; istemcinin "geçerliydi" bilgisine güvenilmiyor.

`PUT /api/atama` kalktı, `POST /api/atama/kaydet` geldi.
`EK_B_UC_NOKTALAR.md` yeniden üretildi — **68 uç nokta, denetim temiz.**

**Göç `a3f5d81c7e42`** — `cizelge_surumu.damga`. Şema değişikliği, veri
dönüştürmez, geri alınabilir. Var olan satırlara `gen_random_uuid()` ile
**satır başına farklı** değer yazılır; tek adımda `server_default` verilseydi
hepsi aynı değeri alır ve damga hiçbir şey ayırt etmezdi.

**On bir yeni test** (`test_duzenleme_oturumu.py`) — turun istediği dördü:
kaydetmeden çıkınca sürüm değişmiyor, damga çakışması ikinci kaydı
reddediyor, yayınlanmış sürüm hem yordamda hem uç noktada korunuyor, ve
**biriken değişikliklerin birlikte doğrulandığı** test.

### Tasarımdan iki sapma — ikisi de gerekçeli

1. **±7 günlük doğrulama penceresi kalktı.** O kısayol TEK değişiklik
   varsayımına dayanıyordu; birden fazla değişiklikte kuralların göreceği
   küme yanlış çıkardı. SDD 5.5'in kendi sözde kodu zaten dönem geneli
   atamalar üzerinde çalışıyor.
2. **Damga `guncelleme_zamani` değil ayrı bir sütun.** O alan satırın her
   dokunuluşunda değişir (yayınlama, arşivleme) ve mikrosaniye duyarlılığıyla
   JSON üzerinden gidip gelir; eşitlik karşılaştırması biçimlendirmeye
   bağımlı hale gelirdi.

### DOKÜMAN BORCU — **bir madde**

**SDD 4.2.4 — `cizelge_surumu.damga`.** 5.5.1 `surum.damga`'dan ve
`YENİ_DAMGA()`'dan söz ediyor, ama 4.2.4'teki alan listesinde böyle bir
sütun yok. Sütun eklendi (göç `a3f5d81c7e42`), dokümana işlenmeli.

### Yol boyunca iki tuzak

**Test veritabanı göç görmemişti.** İlk koşumdaki 41 başarısızlığın tamamı
bundandı. Şema bilinçli olarak `create_all` ile değil **göçle** kuruluyor
(göçlerin kendisi de sınansın diye, conftest bunu belgeliyor); yeni bir göç
eklendiğinde `VERITABANI_URL=$TEST_VERITABANI_URL alembic upgrade head` de
koşturulmalı.

**Kendi fikstürüm test kirliliği üretti ve yanlış teşhise yol açtı.** Yeni
fikstür bütün kuralları global pasifleştirip commit ediyordu; `kural` tablosu
bütün testlerce paylaşıldığı için sonraki testler kuralsız katalogla kalıyor
ve **başarısızlık kümesi koşumdan koşuma değişiyordu**. Bu kirlilik varken
`test_kimlik_api` ve `test_calisan_api` tek başlarına koşturulduğunda dokuz
test düşüyordu ve bu, "önceden var olan bir sıra bağımlılığı" diye
kaydedilmeye çok yakındı. Fikstür düzeltildikten sonra **ikisi de izolasyonda
geçiyor** — böyle bir bağımlılık yok. Ders: paylaşılan tabloyu değiştiren bir
fikstür, ölçtüğü şeyi de bozar.

### Turun bitiş kontrolü — sunucu tarafı

- [x] `pytest` tam takım **360 test geçiyor** — **ters dosya sırasında da**
      (`ls tests/test_*.py | sort -r`), aynı 360. Sıra bağımlılığı yok
- [x] `ruff check` ve `ruff format` temiz
- [x] Taslak oturumun dört testi de yerinde
- [x] Biriken değişikliklerin **birlikte** doğrulandığı test yazıldı
- [x] `EK_B_UC_NOKTALAR.md` yeniden üretildi
- [ ] Frontend testleri ve `tsc`/`oxlint` — arayüz işi yapılmadı

### İş 1 — düzenleme ızgaranın üzerine taşındı · **BİTTİ**

Boş satırda sürükle → blok; kenardan tut → uzat/kısalt; gövdeden tut → gün
içinde kaydır **ya da başka personelin satırına bırak**; tıkla → menü (görev
noktası, kilitle, sil).

**SÜRÜKLEME SINIRA DAYANINCA DURUR.** Aralık artık uyarıyla işaretlenmiyor,
**kırpılıyor**: asgarinin altına inen sürükleme asgaride, azaminin üstüne
çıkan azamide duruyor. Değerler kural kataloğundan; kural pasifse kırpma da
yok. Kullanıcı geçersiz bir seçimi tamamlayıp sonradan reddedilmiyor.

**Silme menüde ve görünür.** Eski ekranda bir açılır listenin "— Boşalt —"
seçeneğinin içine saklıydı; bir işlemi başka bir işlemin seçeneği yapmak onu
bulunmaz kılar.

Form paneli **ikincil yol** olarak yanda kaldı (SRS 5.6): tam saat değeri
yazmak isteyen için, ızgaranın altında değil yanında.

### İş 2b — oturum arayüzü · **BİTTİ**

Değişiklikler istemcide birikiyor ve ızgarada anında görünüyor; her adımdan
sonra sunucuya **oturumun tamamı** doğrulatılıyor ve sunucu hiçbir şey
yazmıyor. Geri al / yinele birikimi ileri geri sürüyor. Kaydet tek istek
gönderiyor ve damgayı taşıyor; yanıttaki yeni damga saklanıyor.

Kirli oturumda **dönem ve sürüm seçicileri, Yeniden Çöz düğmesi kilitli** ve
sekme kapatma `beforeunload` ile uyarılıyor (FR-6.8).

**Kilit bilinçli olarak oturumun DIŞINDA** ve anında yazılıyor: kilit atamayı
değiştirmez, yalnızca yeniden çözümde sabit girdi sayılıp sayılmayacağını
belirler (FR-6.5). Oturuma alınsaydı kaydedilmemiş bir kilit "bu blok
korunuyor" diye görünür ama yeniden çözüm onu görmezdi.

### İş 3'ün arayüz tarafı · **BİTTİ**

Yayınlanmış/arşiv sürümde ızgara salt okunur, düzenleme araçları çalışmıyor
ve ekranın başında **nedenini söyleyen** bir şerit duruyor: yeni taslak
türetilmesi gerektiği (FR-7.3). Sunucu tarafı zaten reddediyordu; araçların
gizlenmesi tek başına yeterli değil, ama kullanıcının NEDEN
düzenleyemediğini okuması gerekiyor — yoksa ızgaranın tepkisizliği hataya
benziyor.

### İş 4 — sonuç dili · **BİTTİ**

Şerit önce cümleyi yazıyor: "Kapsama açığı 1 kişi azaldı; toplam saat dengesi
1 saat bozuldu." Sayısal ceza dökümü **ayrıntı bağlantısının arkasında**.

**Zorunlu ihlal varken başka hiçbir şey gösterilmiyor** — değişiklik
uygulanmadığı için ceza dökümü gerçekleşmemiş bir durumu anlatır ve ikisini
birlikte göstermek kullanıcıya iki farklı gerçeklik sunardı. "Kabul
edilebilir" ile kırmızı uyarı artık aynı anda görünemiyor.

### Bir dayanıklılık açığı — testte yakalandı

Gövde sürüklemesinde imlecin hangi saatin üzerinde olduğu, şeridin kabına
göre oranla bulunuyor. Kap **sıfır genişlikteyken** bölme `NaN` üretiyordu ve
`NaN === NaN` **false** olduğu için "kıpırdamadı" kontrolü sessizce çöküyor,
tek tık taşımaya dönüşüyordu. jsdom düzen hesaplamadığı için test bunu ilk
denemede gösterdi; tarayıcıda da henüz yerleşmemiş bir kapta aynı şey olurdu.

### Testte OLMAYAN davranışlar — gözle bakılmalı

jsdom düzen (layout) hesaplamaz. Aşağıdakiler **test edilmedi**:

- **Sürükleme akıcılığı.** Testler hücrelere doğrudan olay göndererek jestin
  mantığını doğruluyor; imlecin gerçekten o hücrenin üzerinde olup olmadığını
  doğrulamıyor.
- **Taşımada tutulan saatin korunması.** Şeridin neresinden tutulduğu oranla
  hesaplanıyor ve jsdom'da o oran hep sıfır; testler yalnızca SATIR
  değişikliğini ölçüyor.
- **Menünün konumu.** Şeridin altında açılıyor; dar sütunda ya da ızgaranın
  sağ kenarında ekrandan taşabilir.

### Turun bitiş kontrolü

- [x] `pytest` tam takım **360 test geçiyor** — **ters dosya sırasında da**
      (`ls tests/test_*.py | sort -r`), aynı 360. Sıra bağımlılığı yok
- [x] `ruff check` ve `ruff format` temiz
- [x] `tsc -b` ve `oxlint` temiz (4 uyarı, turdan önce de vardı)
- [x] **284 frontend testi** geçiyor — karışık sırada da (`--sequence.shuffle`)
- [x] Taslak oturumun dört testi de yerinde
- [x] Biriken değişikliklerin **birlikte** doğrulandığı test yazıldı
- [x] `EK_B_UC_NOKTALAR.md` yeniden üretildi
- [ ] `git status` temiz — dört kanonik doküman proje yürütücüsünde açık

### Sen ne göreceksin — şu üç ekranı kendi gözünle aç

1. **Çizelge → Gün, boş bir satırda sürükle.** Asgariye dayandığında
   sürüklemenin durduğunu hisset; önizleme "Asgari blok 4 saat (H1)" yazmalı.
2. **Bir bloğu gövdesinden tutup başka personelin satırına bırak.** Kaynak
   şerit sürükleme boyunca soluklaşıyor, önizleme hedef satırda çiziliyor.
   Tuttuğun saatin korunup korunmadığına bak — bu testte ölçülemedi.
3. **Bloğa tıkla.** Menü şeridin altında açılmalı; dar sütunda ya da
   ızgaranın sağ kenarında ekrandan taşıyorsa söyle.

Ayrıca **kaydetmeden dönem değiştirmeyi dene**: seçici kilitli olmalı ve
"Önce değişiklikleri kaydedin ya da vazgeçin" demeli.

---

## 2026-08-14 — Ara iş: Gösterim Verisi ve Tatil Takvimi — **BİTTİ, DAĞITILDI**

Sunucudaki demo verisi Tur 4 öncesindendi ("Demo Personel GG-001", 44 kişi,
Müracaat noktası); göç onu olduğu gibi taşımıştı. İstenen yenileme sırasında
üretecin kendisi de gözden geçirildi.

### Önce tespit: istenenlerin çoğu zaten yazılıydı

Gerçekçi adlar, izin ve talep demo verisi, resmi tatil üretimi, üretilmiş
çizelgeler, pasif personel, devir bakiyeleri ve Özel Gün ekranındaki
Ekle/Değiştir/Sil üçlüsü Tur 4/5'te yapılmıştı. Sunucu bunları hiç görmemişti.
Gerçek eksik üç maddeydi ve üçü de karar gerektirdi.

### Üç karar

1. **Müracaat kapsam dışı kalır.** SRS 1.19 noktayı ve yetkinliği kaldırmış,
   yükünü Güvenlik'e taşımıştı (3.3.3: "tek noktaya kapalı bir personel havuzu
   kalmamıştır"). Geri getirmek SRS 3.3.2/3.3.3/3.3.4 ve Charter kadro
   analizini değiştirirdi. **Doküman borcu doğmadı.**
2. **Beş haftalık geçmiş, senaryo dönemlerinin YERİNE geçer.**
3. **Dini bayramlar kütüphaneden gelir.**

### Yeni dönem takvimi — geçmişe bakar

Eskiden ileriye bakıyordu (dört haftalık sıkışık dönem, sonraki bayram
haftası) ve ürün çoğunlukla yaşanmamış bir takvim gösteriyordu. Artık bugünü
içeren hafta + önceki dördü, hepsi gerçek çözücüyle **60 sn** limitle
çözülüyor. Yerel koşumun sonucu (bugün 14.08.2026):

| Hafta | Tarih | Durum | Atama | Eksik kişi |
|---|---|---|---|---|
| H-4 | 13–19 Tem | yayınlandı | 151 | 0 |
| H-3 | 20–26 Tem | **çözüldü** (yayınlanmadı) | 137 | **12** |
| H-2 | 27 Tem–2 Ağu | yayınlandı | 163 | 0 |
| H-1 | 3–9 Ağu | yayınlandı | 158 | 0 |
| H-0 | 10–16 Ağu | arşiv + yayınlandı | 163 | 0 |

**Kaldırılan senaryolardan ikisi bedelsiz korundu.** Kapsama açığı senaryosu
dar haftaya (H-3) taşındı: yedi şeften beşi izinde, nokta kesintisiz dolu ve
haftada 168 kişi-saat istiyor; kalan iki kişi günlük tavan ve haftalık izin
günü altında en çok 132 verebiliyor. Eksik olan **saat değil kişi** — hiçbir
blok uzunluğu kapatamaz (SRS TD-13). Ölçülen açık **12 kişi, tamamı Vardiya
Şefliği'nde**. TD-8'in "çözüldü" durumu da o haftanın yayınlanmamasından
geliyor. Kota senaryosu personel kaydındaki devir bakiyelerinde duruyor.

**Kaybedilen:** fazla çalışma ve kota dönemleri ayrı dönem olarak yok; resmi
tatilin çözüme etkisi artık üretim gününe bağlı (bugün 15 Temmuz H-4'e
düşüyor, başka bir gün hiçbir haftaya düşmeyebilir).

**Tercih penceresi.** Beş dönemin hepsi bugün veya geçmiş olunca açık pencere
kalmıyordu ve Tercihler ekranı boş açılacaktı. Bugünü içeren haftanın
penceresi açık bırakıldı (son tarih 16 Ağu). Devam eden bir hafta için tercih
toplamak alışıldık değil; alternatifi özelliği hiç gösterememekti.

### Resmi tatil takvimi — `holidays` kütüphanesi

`app/services/tatil_takvimi.py` tek kaynak; `holidays==0.102` bağımlılık
olarak eklendi. Üretilen: **27 gün / iki yıl**, Ramazan (3 gün) ve Kurban
(4 gün) dahil, Türkçe adlarla.

Eski üreteç dini bayramları bilinçli dışarıda bırakıyordu ve gerekçesi
yazılıydı: "tahmini bir tarih yazmak, doğru sanılan yanlış bir veri
üretirdi". İtiraz doğruydu, çözümü eksikti — tarihleri **elle yazmamak** ile
**hiç yazmamak** aynı şey değil.

Sekiz test kilitliyor. Tarihler teste GÖMÜLMEDİ (kütüphanenin bilgisi, sürümle
düzelebilir); sınanan şey takvimin özellikleri: dini bayramın yıl içinde
geriye kayması, çok günlü bayramın gün gün dönmesi, adların Türkçe olması,
aynı günün iki kez dönmemesi (`ozel_gun` anahtarı tarihtir).

### Üretecin sabit tarihleri kalktı

`aktif_baslangic` 1 Ocak 2026'ya, pasif personelin kapanışı 31 Ocak 2026'ya
sabitti. İkisi de bugüne göre hesaplanıyor — dosyanın zaten uyguladığı
"BUGUNE GORE, sabit tarihlerle DEGIL" ilkesi bu iki satırda atlanmıştı.

### Baskı çıktısındaki kırpma kusuru düzeltildi

Tur 6'nın çıktısı gerçek kâğıtta denendi (PDF). Dar şeritlerde etiket
kırpılıyordu — "22.00–05.00 G…" — ve gece yarısını aşan bloğun `›` işareti
tam o kırpmanın içinde kayboluyordu. Ekranda ipucu metni kaybı telafi eder,
kâğıtta edecek bir şey yok. Dört saatten dar şeritlerin etiketi artık şeridin
yanına, gün sonuna dayananlarda soluna yazılıyor. Dört test eklendi.

### Dağıtım — **YAPILDI** (14.08.2026, kesinti ~14 dk)

Yedek: `/opt/vardiya/yedek/vardiya-20260814-0620-demo-oncesi.dump` (88K,
155 nesne). Sıra: yedek → servisleri durdur → rsync → `chown` →
`pip install -e .` → üreteç → başlat. Göç yok, şema değişmedi.

**`VERI_TEMIZLIGINE_IZIN` `.env`'e HİÇ yazılmadı.** Değer tek seferlik
komutun önüne konuldu (`app/veri_temizligi.py`'nin belgelediği kalıp), yani
açılıp kapatılan bir kilit olmadı; sunucu bir sonraki kazara çalıştırmaya
karşı korumasını hiçbir an kaybetmedi. `.env`'de satır yok, doğrulandı.

Sunucudaki sonuç (yerel koşumla aynı yapı, çözücü sayıları farklı — 60 sn
limitte arama belirlenimci değil):

| Hafta | Durum | Atama | Eksik |
|---|---|---|---|
| H-4 13–19 Tem | yayınlandı | 159 | 0 |
| H-3 20–26 Tem | **çözüldü** | 139 | **8** (yerelde 12) |
| H-2 27 Tem–2 Ağu | yayınlandı | 165 | 0 |
| H-1 3–9 Ağu | yayınlandı | 161 | 0 |
| H-0 10–16 Ağu | arşiv + yayınlandı | 164 | 0 |

Açığın tamamı yine Vardiya Şefliği'nde. 30 personel, 4 tercih, 12 izin,
27 resmi tatil (13'ü Ramazan/Kurban), 343 gece yarısını aşan blok.
Beş servis `active`, `journalctl`'de 0 hata, `/api/ben` kimliksiz 401.

**Bir tuzak yakalandı.** İlk rsync frontend'de **0 dosya** aktardı: `dist/`
baskı düzeltmesinden önce derlenmişti ve sunucudakiyle aynıydı. Yeniden
derlenip gönderildi (`index-D5cG4Hsi.js`); yakalanmasaydı eski arayüz
sessizce kalacaktı. Ders: `npm run build` ile rsync arasına başka bir
kaynak değişikliği girerse rsync "değişiklik yok" der ve HAKLIDIR — yanlış
olan derlemenin eskiliğidir.

**Yönetim hesabı silinmedi**, doğrulandı: `omerharmankaya` (YONETIM),
`yonetici1`, `yonetim1` üçü de aktif. DAGITIM.md'deki "demo yenilenirse
yönetim hesabı yeniden kurulmalı" notu `HesapKapsami.PERSONELE_BAGLI`
davranışından eskidir.

### Açık kalan — çalışan paneli için hesap yok

Temizlik **personel kaydına bağlı 1 hesabı** (1 açık oturumla) sildi; bu
beklenen davranıştır (o hesap silinen personele bağlıydı). Sonuç: şu anda
çalışan rolünde hiçbir hesap yok ve **çalışan paneli gösterilemez** —
"Vardiyalarım", "sıradaki vardiya", tercih bildirimi ve FR-9.4'ün değişen
gün işareti ancak çalışan hesabıyla görülür. Yeni personelden birine
Kullanıcılar ekranından hesap açılmalı; parola belirlemek proje
yürütücüsünün işi.

---

## 2026-08-13 — Dağıtım: Tur 1–6 birikimi — **TAMAMLANDI**

Gösterim sunucusuna (46.225.109.40) çıkıldı. Kesinti penceresi
**19:26–19:31 (~5 dk)**; `vera-rag`, `energy-api` ve ortak PostgreSQL'e
dokunulmadı, üçü de boyunca ayakta kaldı.

### Runbook'un üç varsayımı tutmadı — sıra buna göre düzeltildi

**1. Sunucu kodu git ile çekmiyor.** `/opt/vardiya` bir git deposu değil
(hiçbir alt dizininde `.git` yok), `frontend/` dizini yok (derlenmiş arayüz
`web/` altında) ve sunucuda **Node kurulu değil**. Yani "git fetch + merge
--ff-only" ve "sunucuda npm run build" adımları koşamazdı. Yürürlükteki
yordam `deploy/DAGITIM.md`'de kayıtlı ve altı dağıtımdır aynı: **yerelde
derle, `rsync` ile gönder, sonra `chown -R vardiya:vardiya`**. Bu, "dağıtım
sunucunun çektiği koddan yapılır" cümlesini tersine çevirir — dağıtılan şey
yerel çalışma ağacıdır, o yüzden önce `HEAD == origin/main == 4d8b5d7` ve
`git status` boş olduğu doğrulandı.

**2. Göç durumu farklıydı.** `alembic current` = `e7b2c4915d80`, yani:

| Göç | Runbook | Gerçek |
|---|---|---|
| `d1f83a6c40b2` (talep → aralık) | bekliyor | zaten uygulanmış (12.08) |
| `e7b2c4915d80` (kural parametre adları) | bekliyor, kodla gitmeli | zaten uygulanmış; sunucudaki kod da o dönemin koduydu, tutarlıydı |
| `f2a8c561d94b` (atama → blok, `vardiya_tipi` düşer) | — | **bekleyen tek göç** |

Dolayısıyla "eski kod / yeni parametre" `KeyError` penceresi bu dağıtımda
hiç oluşmadı; risk yalnızca veri dönüşümü ve tablo düşürmedeydi.

**3. `pg_dump "$VERITABANI_URL"` düşerdi.** Değer `postgresql+psycopg://`
ile başlıyor — SQLAlchemy'nin biçimi, libpq'nun değil. `DAGITIM.md` bunu
bir kez yaşanmış tuzak olarak kaydetmiş ("pg_dump düştü, alembic devam
etti"). Kullanılan biçim:
`PGURL=$(printf %s "$VERITABANI_URL" | sed 's|+psycopg||')`.
Yedek dizini de `/root` değil `/opt/vardiya/yedek/`.

Ayrıca runbook'un girişi "durdur → yedek", numaralı adımları "yedek →
durdur" diyordu; girişteki sıra izlendi (çalışan servis yedeğin ortasında
yazabilir).

### Uygulanan sıra

1. Yerelde `npm run build` + **231 vitest** + **341 pytest** (10 dk 28 sn)
2. Bitmemiş çözüm işi kontrolü (yok) → `systemctl stop vardiya-cozucu`, `vardiya-api`
3. **Parola rotasyonu** (aşağıda) — proje yürütücüsü koştu
4. Yedek: `/opt/vardiya/yedek/vardiya-20260813-1928-tur6oncesi.dump`,
   **85K**, `pg_restore -l` ile denetlendi: 165 nesne, 20 tablo verisi
5. `rsync`: `frontend/dist/` → `web/` (35 dosya), `backend/` → `backend/`
   (66 dosya). `--delete` yalnız iki dosya sildi: Tur 5'te kaldırılan
   `app/services/vardiya_hesaplari.py` ve testi. `.env`, `.venv`,
   `__pycache__` hariç tutuldu. Ardından `chown -R vardiya:vardiya`.
6. `pip install -e .` → çıkış 0
7. `alembic upgrade head` → tek göç koştu, çıkış 0

### `alembic current` — önce / sonra

```
önce : e7b2c4915d80
sonra: f2a8c561d94b (head)
```

### Göç doğrulaması — sayarak

| Ölçü | Önce | Sonra |
|---|---|---|
| `atama` satırı | 3.051 | **3.051** |
| toplam kişi-saat | 24.408,00 | **24.408,00** |
| `talep` / `tercih` / `kural` | 21 / 4 / 20 | 21 / 4 / 20 |
| `personel` / `cizelge_surumu` | 44 / 26 | 44 / 26 |
| `vardiya_tipi` tablosu | var (3 satır) | **düştü** |

`atama` sütunları `vardiya_tipi_id, tarih` yerine artık
`baslangic_zamani, bitis_zamani`. **1.171 blok gece yarısını aşıyor** —
mutlak eksenin var oluş nedeni sunucudaki gerçek veride de görünüyor.
Kural parametreleri yerinde: `H1.asgari_blok_saat=4`,
`H3.gece_esigi_saat=4`, `H9.azami_gunluk_saat=11`.

### Doğrulama

- `systemctl is-active`: vardiya-api, vardiya-cozucu, vera-rag,
  energy-api, postgresql → **beşi de active**
- `http://127.0.0.1:8002/health` → `{"durum":"ok"}`
- `https://vardiya.omerharmankaya.com/` → yeni paket sunuluyor
  (`index-DdDLnrHO.js` 200); `web/assets` içinde eski paket kalmadı
- `GET /api/ben` kimliksiz → **401** (API Caddy üzerinden erişilebilir,
  yetkilendirme çalışıyor)
- `journalctl` (başlatmadan beri): **0 hata satırı**
- Kural kataloğu salt okunur sınandı: 20 kural satırı → 20 kural nesnesi
  kuruldu, parametre okuma hatası yok

**Runbook'ta yanlış olan bir kontrol:** `curl https://.../health` API'ye
gitmiyor. Caddy yalnızca `/api/*`'i vekilliyor, `/health` SPA'ya düşüyor ve
`index.html` dönüyor. API'nin sağlık ucu kök altında (`/health`), yani
dışarıdan erişilebilir değil. Doğru kontrol ya yerelden `127.0.0.1:8002`
ya da `/api/ben` → 401.

### Parola rotasyonu

Dağıtım sırasında `vardiya` veritabanı kullanıcısının parolası değiştirildi.
Nedeni: bu oturumda koşulan bir şema kontrolü psycopg hatası verdi ve hata
mesajı bağlantı dizesinin tamamını, parolayı da içerecek biçimde bastı.
Rotasyonu proje yürütücüsü koştu (`\password`, komut satırına yazılmadı);
`.env` güncellendi, eski parolanın kopyasını taşıyan `/opt/vardiya/.env.yedek`
silindi. Yeni parola, göçten ÖNCE `alembic current` ve `pg_dump` ile
doğrulandı — yedeğin başarısı aynı zamanda rotasyonun sınavı oldu.

Bundan sonra sunucuya gönderilen her komutun çıktısı
`sed -E 's#://[^@]*@#://***@#g'` süzgecinden geçirildi.

### Açık kalan — `S6.desen_toleransi_saat` kural kaydında yok

Kural kataloğu sınandığında tek eksik bu çıktı. **Arıza değil:** kod
`self.parametreler.get("desen_toleransi_saat", varsayılan)` ile okuyor,
yani çözücü varsayılanla çalışır. Etkisi yalnızca Kural ekranında: bu
parametre okuma kipinde `—`, düzenleme kipinde boş kutu görünür. Kalıcı
çözüm ya ekrandan bir değer kaydetmek ya da kaydı ekleyen küçük bir göç.
Tur 5'in göçü `H1` ve `H3` için bu satırları yazmıştı, `S6` atlanmış.

### `.env` — yasaklı iki değişken yok

`TEST_VERITABANI_URL` ve `VERI_TEMIZLIGINE_IZIN` sunucuda tanımlı değil,
doğrulandı. Gösterim verisi yenileme (`demo_veri_uret.py --reset`) bu
dağıtımın parçası DEĞİLDİR ve yapılmadı — ayrı karar olarak bekliyor.
Sunucudaki veri hâlâ eski senaryo: **44 kişilik kadro**, göçle blok
kaydına çevrilmiş 3.051 atama. Tur 4/5'in 30 kişilik senaryoları yalnızca
üreteçten gelir.

### Geri dönüş kullanılmadı

Hiçbir adımda geri alınmadı. Gerekseydi: `alembic downgrade e7b2c4915d80`
(geri alma yazılı ve denenmiş), tutmazsa
`pg_restore -c -d "$PGURL" /opt/vardiya/yedek/vardiya-20260813-1928-tur6oncesi.dump`.

---

## 2026-08-13 — Tur 6: Saat Görünümleri ve Arayüz — **BİTTİ**

Kaynak: `docs/turlar/CLAUDE_CODE_PROMPTU_TUR6.md`. Altı iş, hepsi bitti.
Çalışma `tur6-saat-gorunumleri` dalında yürüdü.

Doküman sürümleri turun başında doğrulandı: Charter **1.4**, SRS **1.21**,
SDD **1.28**, Backlog **1.18** — dördü de taşıyor. (SDD'nin revizyon
tablosunda satır SIRASI bozuk: ... 1.24, 1.25, **1.27**, **1.28**, **1.26**.
İçerik eksik değil, yalnızca son üç satır sıra dışı; en yüksek sürüm 1.28.)

### İş 1 — Gün ızgarası

Satırlarda personel, sütunlarda seçili günün yirmi dört saati
(`components/GunIzgarasi.tsx`). Blok, saat hücrelerinin ÜZERİNDE tek parça
bir şerit olarak durur — hücreler yalnızca ızgara çizgisi ve sürükleme
hedefi. Ayrım görsel değil anlamsal: blok tek bir karardır (SRS TD-13) ve
yirmi dört ayrı boyalı kutu, kataloglu sürümün "vardiya dizilimi"
görüntüsünü geri getirirdi.

**Gece yarısını aşan blok** başladığı günde sağ kenara dayanır (köşe açık,
kenarlık yok, `›` işareti), ertesi gün sol kenardan başlar (`‹`). İki günde
de etiket bloğun TAMAMINI yazar ("20.00–06.00"). "20.00–24.00" ve
"00.00–06.00" yazmak, modelin tam olarak yasakladığı iki-blok görüntüsünü
ekranda üretmek olurdu. Gün toplamı bloğun BAŞLADIĞI güne yazılır (TD-1);
ertesi günün satırında altı saat görünür ama toplamına girmez.

Geometri `lib/blok.ts`te tek yerde: `gunParcasi` / `gununParcalari`. Gün
ızgarası, hafta şeridi ve yazdırma üçü de oradan okur; ikinci bir çözümleme
yazılmadı.

### İş 2 — Hafta şeridi ve **DOM ÖLÇÜMÜ**

`components/HaftaSeridi.tsx`. Her gün hücresi yirmi dört dilimlik mini
şerittir ve **tek öğeyle** çizilir: dilimler bir CSS gradientinin sert
duraklarıdır (`lib/saatRengi.ts`, `saatGradyani`).

**Ölçüm — otuz personel × yedi gün (210 hücre), jsdom, tam ağaç:**

| Çizim yolu | DOM düğümü |
|---|---|
| Bugünkü hâli (gradient, hücre başına 1 düğüm) | **574** |
| Dilim başına ayrı düğüm olsaydı | ~5.400 (yalnız dilimler 210 × 24 = 5.040) |

Ölçüm testle kilitlendi (`HaftaSeridi.test.tsx`: düğüm sayısı < 1.000 ve
210 şerit gerçekten çizilmiş). Dilimler ayrı öğelere bölünürse test düşer.

### İş 3 — Renk saatin kendisinden · **YENİ RENK BANDI**

Kategorik üç ton kalktı. `lib/vardiyaRenk.ts` silindi; yerine
`lib/saatRengi.ts` geldi.

**Bandın tanımı** (`docs/tasarim/TASARIM_REFERANSI.md` sürüm 4'ün vardiya
rampasının yerine geçer — kanonik doküman değil, proje yürütücüsü
işleyecek):

```
aydinlik(saat) = (1 − cos(2π · (saat − 1) / 24)) / 2      → 0…1
renk(saat)     = lerp(#2F3A38, #E9E7D9, aydinlik(saat))
```

- Uçlar mevcut paletten: en koyu gece `--vardiya-gece` **#2F3A38**, en açık
  gündüz `--vardiya-gunduz` **#E9E7D9**. Yeni bir palet uydurulmadı.
- Dip nokta **01.00**, tepe **13.00**. Dip, gece penceresinin (20.00–06.00,
  TD-2) ORTASINA konuldu; kenarına konsaydı 20.00 ile 05.00 farklı koyulukta
  çıkardı, oysa ikisi de gecenin kenarıdır.
- `--vardiya-aksam` (#C7CEC0) artık kullanılmıyor — bandın 16.00 civarındaki
  değeri onun yerini tutuyor.
- Bandın 24 basamağı modül yüklenirken bir kez hesaplanır; beş binden fazla
  renk sorgusunda kosinüs tekrar çalışmaz.

Örnek basamaklar: `00 #323d3b` · `01 #2f3a38` · `06 #747a74` · `08 #a4a79d`
· `12 #e6e4d6` · `13 #e9e7d9` · `16 #cecec1` · `20 #747a74` · `23 #3b4643`.

**Renk tek başına bilgi taşımıyor.** Şeridin üzerinde saat aralığı metni
durur (`blokErisilebilirEtiket`, aynı metin `aria-label`de). Kilitli blok
RENKLE değil **eğik tarama** + aksan dış çizgiyle işaretlenir
(`KILIT_DOKUSU`); kapsama açığı **▲ + sayı** ile — şekil, renk körlüğünde ve
siyah-beyaz yazdırmada da ayrışır. Şerit metni kendi yarı saydam zeminini
taşır (`ETIKET_ZEMINI`): aynı şerit hem #2F3A38 hem #E9E7D9 taşıyabildiği
için tek bir mürekkep rengi baştan sona okunmuyor.

Çalışan paneli de aynı banda taşındı — "Gündüz / Akşam / Gece" rozeti ve üç
kutulu lejant kalktı. Aynı vardiyanın yöneticide ve çalışanda farklı
okunmaması için renk iki panelde de aynı fonksiyondan geliyor.

### İş 4 — Sürükleyerek blok tanımlama

Gün satırında sürükleme bloğu tanımlar; var olan bloğun iki kenarından da
uzatma/kısaltma çalışır. Bırakıldığında panel doldurulur ve **doğrulama
isteği** gönderilir — değişiklik uygulanmaz, "Uygula" arada durur.

`asgari_blok_saat` (H1) ve `azami_gunluk_saat` (H9) **kural kataloğundan**
okunur (`lib/kuralParametre.ts`), koda gömülmez; kullanıcı parametreyi
değiştirdiğinde ızgara yeni sınırı gösterir. **Pasif kural sınır koymaz.**
Sınır sürükleme SIRASINDA görünür: önizleme kırmızıya döner ve nedenini
yazar ("Asgari blok 4 saat (H1)").

Tek tık blok tanımlamaz, yalnızca satırı seçer — bir saatlik blok üretip
ardından "asgari dört saat" diye reddetmek, kullanıcının yapmadığı bir
işlemi ona geri okumak olurdu.

### İş 5 — Yazdırma ve CSV

Yazdırılabilir görünüm artık **gün ızgarası**: her gün kendi sayfasında
başlar (`.yazdirma-sayfa-basi`), bir günün personeli sayfaya sığmadığında
tablo bölünür ve **saat başlığı `thead`de olduğu için her sayfada yeniden
basılır**. Şeridin üzerinde saat aralığı ve nokta kısaltması METİN olarak
durur: tarayıcı arka plan basmayabilir, kâğıtta kalan tek şey odur.

CSV'de `baslangic`/`bitis` saat metninden **tam ISO damgasına** çevrildi.
Dosyanın okuyucusu makinedir ve `tarih` sütununun yanında "20.00; 06.00"
gören bir okuyucu bitişin ertesi güne düştüğünü çıkaramaz — gece yarısını
aşan blok tam da bu dosyada görünmez oluyordu.

Üçüncü kopya çıkmadı: `saatEtiketi`in `talepAraligi.ts`teki ikinci tanımı
`blok.ts`e katlandı, yazdırma ızgaranın biçimlendiricilerini çağırıyor.

### İş 6 — Kural ekranı ve analiz

**Kural ekranına kod eklenmedi** ve gerekmedi: ekran parametreleri
katalogdan genel olarak çiziyor, `asgari_blok_saat` ve `gece_esigi_saat` de
göçle (`f2a8c561d94b`) kural kayıtlarına eklenmişti. Varsayım teste
çevrildi (`TanimlarEkrani.test.tsx`): ikisi de görünüyor, düzenlenebiliyor
ve onay kutusundan geçerek kaydediliyor.

**Adalet grafiğinin referansı havuz ortalamasından kişiye düşen ADİL PAYA
geçti** (SRS S2/S3). Gece ve hafta sonu artık ayrı iki grafik: havuzları da
hedefleri de farklı, iki hedefi tek yığılmış çubuktan okumak mümkün değil.
Gösterilen sapma çözücünün kendi formülü — `max(saat − ⌊pay⌋, ⌈pay⌉ − saat,
0)` — böylece ceza dökümü ile grafik aynı çizelge için farklı sayı söylemez.

Saat dengesi tablosunun "HEDEF" sütunu **"ADİL PAY"** olarak adlandırıldı;
o sütun Analiz servisi yazıldığından beri S4'ün adil payıydı ve "hedef"
demek onu sözleşme saati gibi okutuyordu.

### Backend'e dokunuldu — tek yer, ek alan

Tur backend'e neredeyse hiç dokunmamayı istiyordu. Bir yerde gerekti ve
nedeni şu: adalet grafiğinin referansı için gereken `pay_gece[p]` /
`pay_hs[p]` sunucuda **zaten hesaplanıyor ama atılıyordu** —
`Baglam.uygun_havuz` payları hesaplayıp yalnızca "payı sıfırdan büyük
olanlar" kümesini döndürüyor. Arayüz elinde sayılarla kalınca referans
olarak havuz ortalamasını çizmek zorundaydı, yani S2'nin açıkça reddettiği
ölçüyü.

Değişiklik ikisi: `KisiSayisiOku`ya `pay: float | None = None` alanı
eklendi (var olan tüketiciler için kırıcı değil), Analiz servisi
`uygun_havuz` yerine `adil_paylar`ı doğrudan çağırıp payı da yazıyor. Tanım
yine `Baglam.adil_paylar`da tek yerde; ikinci bir geçiş de yapılmıyor.
**Göç yok, şema değişikliği yok.**

### Tasarımdan sapma — Çizelge ekranındaki nokta EKSENİ kaldırıldı

Ekranda "Personel / Nokta" görünüm anahtarı vardı; yerini "Gün / Hafta"
aldı. Gerekçe: SDD 6.3.3 (sürüm 1.28) ekranın iki görünümünü ÇÖZÜNÜRLÜK
üzerinden tanımlıyor ve listesinde Görünüm Anahtarı yok. Nokta ekseni,
satırların nokta × vardiya TİPİ olduğu kataloglu sürümden kalmaydı ve Tur
5'te zaten yarısını kaybetmişti (satır doğrudan noktaya inmişti).

Kayıp telafi edildi: gün ızgarasına **nokta süzgeci** eklendi. "Bu noktada
bugün kim var" sorusu artık orada yanıtlanıyor ve yanıt saat çözünürlüğünde
— eski eksenin veremediği bilgiyle birlikte. Nokta eksenini geri
istiyorsanız söyleyin; gün ızgarasında nokta satırları alt satırlara
yığılarak çizilebilir.

### DOKÜMAN BORCU — **üçü de açık**

1. **SRS 7.2 — çizelge dışa aktarma sütunları.** Doküman hâlâ
   `vardiya_tipi` ve `gece_mi` yazıyor; kod Tur 5'ten beri
   `baslangic`/`bitis` + `gece_saat` üretiyor. Bu turda ikisi daha
   değişti: `baslangic`/`bitis` artık saat metni değil **tam ISO damgası**.
   Kapsama açığı dosyasının sütunları da `vardiya_tipi` yerine
   `baslangic`/`bitis` + `tur`/`kisi_sayisi`.
2. **SDD 6.3.3 — kaldırılan Görünüm Anahtarı ve eklenen nokta süzgeci.**
   Yukarıdaki sapma. Ayrıca gün ızgarasının kapsama satırının saat
   düzeyinde olduğu ve işaretin şekil taşıdığı yazılı değil.
3. **Ek B — `KisiSayisi` yanıtına `pay` alanı eklendi.** Uç nokta sayısı
   değişmedi, `GET /api/analiz/{surum_id}` yanıtının şekli değişti.

### Bilinen sınır — kapsama açığı dosyasında gece yarısı

Çizelge CSV'si ISO damgasına geçti; **talep sapması dosyası** hâlâ `tarih` +
saat metni taşıyor (`00.00`, `08.00`). Kapsama açığı kaydı sunucuda TIME
sütunlarında duruyor ve saat dilimi ofseti taşımıyor; ondan bir ISO damgası
kurmak ofseti uydurmak olurdu. Gece yarısını aşan bir açık aralığı bu
dosyada hâlâ okunamaz. Düzeltmenin yeri sunucu tarafı (aralığa bitiş tarihi
ya da ofset eklemek) ve bu tur backend'e dokunmama kuralının içinde
kalmadı.

### Sen ne göreceksin — **şu üç ekranı kendi gözünle aç**

Ekranı tarayıcıda yine göremedim (5173 portu başka projede, ekran girişin
arkasında). Testler kanıt yerine geçiyor ama **jest değil**: aşağıdakiler
test edilmedi ve gözle bakılmalı.

1. **Çizelge → Gün.** Sürükleyerek blok tanımla ve kenarından uzat.
   jsdom düzen (layout) hesaplamadığı için imlecin gerçekten hangi saatin
   üzerinde olduğu test edilemiyor; test hücrelere doğrudan olay göndererek
   jestin MANTIĞINI doğruluyor. Bakılacak: sürükleme akıcı mı, önizleme
   doğru hücrelerde mi, kenar tutamakları 6px genişlikte tutulabiliyor mu.
2. **Çizelge → Gün, gece yarısını aşan bir blok.** Şeridin iki günde de
   tek blok gibi okunduğu ancak gözle doğrulanabilir: köşe açıklığı,
   `‹ ›` işaretleri ve etiketin sığması. Dar sütunda etiket kırpılıyorsa
   söyle.
3. **Çizelge → Yazdır.** Yatay A4 önizlemesi. Gün ızgarası sayfaya sığıyor
   mu, saat başlığı ikinci sayfada tekrarlanıyor mu, arka plan basımı kapalı
   olduğunda şeritler hâlâ okunuyor mu — üçü de yalnızca gerçek baskı
   önizlemesinde görülür.

Ayrıca **Analiz** ekranındaki iki yeni adalet grafiğine bakmanı öneririm:
referans çizgisi (dikey ince çizgi) çubukların arasında kaybolabiliyor mu?

### Turun bitiş kontrolü

- [x] `tsc -b` temiz, `oxlint` temiz (4 uyarı, hepsi turdan önce vardı ve
      `react/only-export-components` — dosya başına bir bileşen kuralı)
- [x] `vitest` **231 test geçiyor** (turdan önce 162; 69 yeni test).
      Ters/karışık sırada da geçiyor (`--sequence.shuffle`)
- [x] `pytest` tam takım **341 test geçiyor** (10 dk 26 sn)
- [x] `ruff check` ve `ruff format --check` temiz
- [x] Hafta şeridinin DOM maliyeti ölçüldü ve yukarıda
- [x] Yeni renk bandı yukarıda (tasarım referansına proje yürütücüsü işleyecek)
- [ ] `git status` temiz — dal `main`e alınmayı bekliyor

### Bekleyen göçler — dağıtım yapılmadı

Bu tur göç üretmedi. Tur 5'in göçü (`f2a8c561d94b`) hâlâ bekliyor; durumu
değişmedi.

---

## 2026-08-13 — Tur 5: Gerçek Saatlik Model — **BİTTİ**

Kaynak: `docs/turlar/CLAUDE_CODE_PROMPTU_TUR5.md` ve devamı
`docs/turlar/TUR5_DEVAM.md`. Yedi iş. Çalışma `tur5-saatlik-model` dalında
yürüdü, sonunda `main`e alındı.

Tur ortasında bir kez **durdu**: İş 1'in sondajı yanıltıcı çıkmıştı ve karar
istendi. Devam belgesi üç seçenekten ikisini onayladı, ölçüm yeniden koşuldu
ve tur tamamlandı. Aşağıda önce turun ilk yarısı, sonra "Durma noktası ve
sonrası" başlığı altında devamı yazılı.

Doküman sürümleri turun başında doğrulandı: Charter **1.4**, SRS **1.19**,
SDD **1.27**, Backlog **1.16** — dördü de taşıyor.

### İş 1 — prototip ölçümü: **karar kuralı geçildi, devam**

Karar kuralı: 40 × 28 ölçeğinde ilk uygun çözüme ulaşma süresi 30 saniyeyi
aşarsa dur. **Aşmadı — 5,0 saniye.** Tam uygulamaya geçiliyor.

Sondaj `backend/scripts/saatlik_prototip.py`. Modelde yalnızca mutlak saat
ekseni, `bas` göstergesi, günde tek başlangıç, asgari süre, nokta sabitliği,
günlük tavan ve S1 var; başka kural yok. Talep SRS 3.3.4'ün Müracaat'sız
tablosudur ve kadroya göre `P/40` ile ölçeklenir — aksi hâlde on kişilik bir
kadro kırk kişilik talebi karşılamaya çalışır ve ölçülen şey çözüm süresi
değil kapsama açığı olurdu. Şef havuzu `max(3, 7·P/40)`: kesintisiz
doldurulan bir nokta haftada 168 kişi-saat ister, günlük tavan on bir
saattir, dolayısıyla üç kişinin altındaki bir havuz noktayı hiçbir çizelgeyle
kapatamaz.

Arama işçisi SDD 3.4.3 referansına sabit (3), makine macOS arm64 / 10
çekirdek — `kabul_olcumu.py` ile aynı sözleşme.

| Ölçek | Değişken | Kurma | **İlk uygun** | Optimale | Sonuç |
|---|---|---|---|---|---|
| 10 × 7 | 7.224 | 0,10 sn | **0,25 sn** | 0,45 sn | optimal, ceza 0 |
| 20 × 14 | 28.224 | 0,38 sn | **1,12 sn** | 4,63 sn | optimal, ceza 0 |
| 30 × 28 | 84.000 | 1,15 sn | **3,71 sn** | 28,63 sn | optimal, ceza 0 |
| 40 × 28 | 112.224 | 1,69 sn | **5,02 sn** | 56,03 sn | optimal, ceza 0 |

40 × 28 iki kez daha koşuldu: ilk uygun 4,93 ve 5,08 sn; optimale 44,6 ve
45,2 sn. İlk uygun süre kararlı.

**Ölçüm boşuna hızlı olmasın diye çıkan çizelge denetlendi** (`--denetle`).
Sondaj hızlı çözüyorsa iki açıklama vardır — formülasyon ucuzdur ya da kısıt
yanlış yazıldığı için model gerçekte kolaydır — ve ikisini ayırmanın tek yolu
sonuca bakmaktır. Dört ölçekte de: asgari süreden kısa blok yok, günlük
tavanı aşan blok yok, gün içinde ikinci blok yok, blok içinde nokta değişimi
yok. 40 × 28'de **96 blok gece yarısını aşıyor** — mutlak eksenin var oluş
nedeni tam olarak bu.

### İki sapma — nedenleri önce

**1. Günlük saat, duvar saatine değil bloğun başladığı güne yazılıyor.**
SRS H1 ve H9 günlük toplamı `Σ_{s ∈ gün d} z[p,s]` diye yazar; H9'un metni
ise aynı paragrafta "gece yarısını aşan bloğun saatleri başladığı güne
sayılır (TD-1); ertesi günün tavanı bu saatlerle dolmaz" der. İkisi aynı şey
değildir ve formülün duvar saati okunması **iki kuralı da bozar**:

- **H9 blok uzunluğunu sınırlayamaz.** 20.00–08.00 bloğu duvar saatinde
  4 + 8 saattir; ikisi de on bir tavanın altında kalır ve on iki saatlik blok
  geçer.
- **H1'in asgari süresi akşam başlangıçlarını yasaklar.** 21.00'de başlayan
  bir blok o güne yalnızca üç saat bırakır ve `≥ 4 · bas` kısıtı düşer —
  oysa gece kapsamasının ihtiyaç duyduğu bloklar tam olarak bunlardır.

Metin normatiftir, gösterim kısaltmadır: "gün d" bloğun sayıldığı gündür.
Gün başına saat bu yüzden devralınan saatler çıkarılıp taşan saatler
eklenerek hesaplanıyor (`devir[p,s]` göstergesi: "bu saat çalışılıyor ve
önceki günde başlamış bir bloğa ait"). Maliyeti ölçüme dahil — tam uygulama
da aynı yapıyı taşıyacak. Bu, aşağıdaki doküman borcunun birinci maddesidir.

**2. H9 sondaja dahil edildi.** Prompt "diğer kuralları ekleme" diyor;
günlük tavan olmadan çözücü günde yirmi dört saat çalıştırabilir, kapsama
bedelsiz kapanır ve ölçülen süre gerçek modelin süresi olmaz. H9 ayrıca
SRS 3.3.1'de asgari blok süresiyle **aynı üç parametreli çerçeve** içinde
tanımlı: alt sınır ve üst sınır birlikte bloğun çerçevesini çizer.

### K1 için erken uyarı — optimale ulaşma 45–56 sn

Karar kuralı ilk uygun çözümü ölçer ve rahat geçiyor. Ama **optimale ulaşma
süresi 40 × 28'de 45–56 saniye** ve K1'in eşiği 60 saniye. Tur 4'te aynı
kriter 1,01 saniyeydi (blok kataloğuyla). Saat modeli optimallik kanıtında
yaklaşık **elli kat** pahalı ve tam modelde on beş kural daha eklenecek.

Bu bir durdurma nedeni değil — K1 pratikte zaman limitli bir aramanın
sonucunu ölçer ve ilk uygun çözüm beş saniyede geliyor — ama turun kabul
ölçümünde K1'in **ne ölçtüğüne** dikkat edilecek: "60 saniyede optimal" ile
"60 saniyede kabul edilebilir çözüm" aynı şey değil ve saat modelinde ikisi
ilk kez ayrışıyor.

### İş 2 — göç: blok kavramı kalktı

Tek göç (`f2a8c561d94b`). `atama` blok kaydına geçti
(`baslangic_zamani`/`bitis_zamani`), `vardiya_tipi` tablosu ve
`personel.sabit_vardiya_tipi_id` düştü, tercih zaman aralığına çevrildi,
`asgari_blok_saat` = 4 ve `gece_esigi_saat` = 4 kural kayıtlarına eklendi.

**Dönüşüm sayılarak doğrulandı** ve göç eşitliği bozulursa hata verip
duruyor. Geliştirme veritabanında: önce 604 satır / 5.032 kişi-saat, sonra
604 satır / 5.032 kişi-saat. Geri alma yazıldı ve **denendi**: katalog
veriden yeniden türetiliyor (atamalarda fiilen geçen aralıklar), aynı 604
satır ve 5.032 kişi-saat geri geliyor. Sıfırdan da koşuyor (`downgrade base`
→ `upgrade head` temiz).

**H1'in güvencesi değişti ve bu bir testle kilitlendi.** Yeni benzersizlik
anahtarı `(surum_id, personel_id, baslangic_zamani)`; aynı günde farklı
saatte başlayan ikinci bir bloğu veritabanı **yakalamıyor**.
`test_ayni_gunde_farkli_saatte_ikinci_blogu_veritabani_yakalamaz` kaybı
ölçüyor; manuel düzenleme yolu o günün bloklarını silip tek blok yazarak
kuralı yapısal olarak taşıyor.

### İş 3, 4, 5, 6 — model, toplama, kurallar, gösterim verisi

Model `z[p,s]` / `x[p,s,n]` üzerine kuruldu; `bas` başlangıç göstergesi ve
`devir` devralma göstergesi eksenin parçası. Çözücü çıktısı yazma anında
bloklara toplanıyor ve toplama **kapsama açığı kayıtlarının kullandığı aynı
yardımcıdan** geçiyor (`ardisik_saatleri_grupla`); tek fark
`gun_sinirinda_kes` parametresi — gece yarısını aşan blok tek kayıtta duruyor.

Müracaat kalktı: iki nokta, iki yetkinlik, Güvenlik hafta içi 08.00–24.00
talebi 9. Haftalık toplam 1.152 kişi-saat **değişmedi** ve bunu
`test_yuk_gostergesi` kilitliyor.

**Çözücü–doğrulayıcı uyum testi 24/24 temiz** ve yol üstünde iki gerçek hata
yakaladı:

1. **Değişken eleme H1'in nokta sabitliğini deliyordu.** Kısıt geriye dönük
   yazılıyor ve `x[p,s,n]` bulunamadığında atlanıyordu; talebi biten bir
   noktanın değişkeni elendiği için kısıt hiç kurulmuyor ve personel
   **çalışmayı kesmeden** nokta değiştirebiliyordu. Çözücü bunu buldu:
   14.00–16.00 bir noktada, 16.00–24.00 başka noktada, tek kesintisiz
   çalışma. Kısıt ileri yönlü kuruldu ve eksik değişken sıfır sayılıyor.
2. **Isıtma penceresi tümüyle sabit değildi.** Atanmış saatler 1'e
   çekiliyordu ama boş saatler **serbest** kalıyordu; çözücü geçmiş bir
   haftada olmayan çalışma uydurabiliyor ve o uydurma H2/H3/H4
   pencerelerini dönemin ilk günlerinde yanlış besliyordu. TD-5 açık: o
   atamalar karar değişkeni değildir.

### Durma noktası — İş 1'in sondajı yanıltıcı çıktı

**Turun asıl bulgusu bu ve karar burada istendi.**

İş 1'in sondajı üç kuralla (H1, H9, S1) ölçtü ve 40 × 28'de ilk uygun çözümü
**5,0 saniyede** buldu. Tam model **on dokuz kural** taşıyor ve ölçüm
tamamen başka:

| Ölçek | Değişken | Kısıt | İlk uygun | 300 sn'de |
|---|---|---|---|---|
| 30 × 28 (sıkışık senaryo) | 106.603 | 229.138 | **45,6 sn** | optimal değil |

Ara ölçümler, iyileştirmelerin sırasıyla ne kazandırdığını gösteriyor:

| Durum | İlk uygun (30 × 28) |
|---|---|
| İlk hâl | 60 sn'de **bulunamadı** |
| Gün başına türev tek değişkene bağlandıktan sonra | 128 sn |
| Isıtma penceresi tümüyle sabitlendikten sonra | **45,6 sn** |

Kural bazında sondaj (taban = H1+H9+S1, 30 × 28): hiçbir kural tek başına
patlatmıyor, **S4** en pahalısı (3,8 sn → 19,6 sn), gerisi 4–7 sn arası.
Yük **birikimli**.

**İki iyileştirme yapıldı ve ikisi de tesadüfi değil, yapısal:**

1. **Gün başına türetilmiş büyüklükler tek değişkene bağlandı.**
   `blok_saati` 48 terimli bir ifade ve **altı kural** onu okuyor; her
   çağrıda yeniden açıldığında aynı bilgi modele yüz binlerce kez
   kopyalanıyordu.
2. **Isıtma penceresi sabitlendi** (yukarıdaki 2 numaralı hata). Arama
   uzayının beşte biri.

Bu noktada 40 × 28 ölçeğinde K1 ölçümü **koşulmamıştı**; 30 × 28'de ilk uygun
çözüm 45,6 saniye olduğuna göre 40 × 28'in 60 saniyenin altında kalması
muhtemel görünmüyordu. **Karar istendi.** Formülasyonda gevşetilebilecek üç
yer sıralandı, maliyeti artan sırayla:

- **`devir` göstergesinin penceresi.** Bugün her saat için üretiliyor
  (22.680 ikili değişken). Bir blok günlük tavanı (11 saat) aşamadığına
  göre ertesi güne en fazla on saat taşabilir; gösterge yalnızca günün ilk
  on bir saati için gerekli. Kazanç ~%55 daha az `devir` değişkeni.
  **Bedeli:** eksen H9'un parametresine bağlanır.
- **S4'ün bölme kısıtı.** `add_division_equality` ceza dökümünü doğal
  birimde raporlamak için var; S2/S3'ün taban/tavan yöntemine geçirilirse
  bölme kalkar. **Bedeli:** S4'ün cezası kesirli payların arasında sıfıra
  düşer — SRS'in S4 tanımını değiştirir.
- **Nokta sürekliliği** (M3'ün ve SAATLIK_MODEL_KARARLARI'nın "ilk
  gevşetilecek yer" dediği kısıt). Kaldırılırsa blok içinde nokta
  değişebilir; sahada anlamsız ama model belirgin biçimde ucuzlar.

Ölçmeden hangisinin ne kazandıracağı söylenemezdi ve ikisi tanımı
değiştiriyordu; bu yüzden denenmeden karar istendi.

---

### Devam kararı ve uygulanan iki seçenek

`docs/turlar/TUR5_DEVAM.md`: **1 ve 2 uygulanacak, 3'e dokunulmayacak.**

**Seçenek 1 — `devir` göstergesinin penceresi daraltıldı.** Gösterge artık
günün yalnızca ilk `azami_gunluk_saat` saati için üretiliyor. Bu bir tanım
değişikliği değil: bir blok H9'un tavanını aşamadığına göre ertesi güne o
tavandan fazla taşamaz, dolayısıyla eksik bırakılan göstergeler zaten her
çözümde sıfırdır — **çözüm kümesi aynı**. Eşik kuralın kendi parametresinden
okunuyor (`_azami_gunluk_saat`), sabit yazılmadı; H9 kapalıysa 24'e düşüyor,
yani gevşetme kuralın varlığına bağlı. SDD 5.3'e işlendi.

**Seçenek 2 — S4 taban/tavan yöntemine geçti.** `add_division_equality` ve
`S4_OLCEK` kalktı; sapma artık `sapma ≥ toplam − ⌊pay⌋` ve
`sapma ≥ ⌈pay⌉ − toplam` ile kuruluyor, S2/S3 ile **aynı yöntem**. Onay
başarım gerekçesiyle değil **tutarlılık** gerekçesiyle verildi: kesirli
payların arasında ceza sıfıra düşer, bu S4'ün tanımını değiştirir ve
değişiklik SRS 1.20'ye yazıldı. `s4_hedef_paylari_x10` → `s4_hedef_paylari`
(doğal saat birimi).

**Seçenek 3 — nokta sürekliliği: dokunulmadı.** Ürün kararı. Devam belgesi
ayrıca kısıtın *gerçekten uygulandığının* doğrulanmasını istedi — değişken
eleme onu bir kez sessizce iptal etmişti (yukarıdaki 1 numaralı hata). İki
test bunu kilitliyor: biri talebi dönem ortasında biten bir nokta kurup
değişkenin elendiği yerde kısıtın hâlâ kurulduğunu, diğeri ısıtma
penceresinin boş saatlerinin sıfıra sabitlendiğini ölçüyor.

### Ölçüm — devam belgesinin istediği üç ölçek

Arama işçisi 3 (SDD 3.4.3), macOS arm64, 180 sn limit:

| Ölçek | Değişken | Kısıt | **İlk uygun** | Not |
|---|---|---|---|---|
| **30 × 7** | 39.622 | 84.130 | **1,0 sn** | Gerçek kullanım — dönem varsayılanı bir hafta (Charter 2.5) |
| **30 × 28** | 94.284 | 192.278 | **5,0 sn** | Karşılaştırma noktası — durma anında 45,6 sn |
| **40 × 28** | 126.674 | 260.808 | **16,3 sn** | K1'in stres ölçeği |

Durdurma eşiği 60 saniyeydi; **aşılmadı**, tur devam etti. Asıl kullanım
ölçeğinde (30 × 7) çözüm bir saniyede geliyor.

### Kabul ölçümü — `scripts/kabul_olcumu.py` saat modelinde

Betik yeniden yazıldı. K3'ün eşiği artık katalogdan türetilmiyor,
**Charter 1.4'ün sekiz gece saati** doğrudan yazılı; referans havuzlar
Müracaat'sız kadroya göre 9 şef + 31 güvenlik.

| Çözücü limiti | K1 | K2 | K3 | K4 | K5 | Sonuç |
|---|---|---|---|---|---|---|
| 60 sn | 8,68 sn ✔ | 0 ✔ | **30,00** ✘ | 167 açık ✔ | 0,099 sn ✔ | 4/5 |
| 300 sn | 8,33 sn ✔ | 0 ✔ | **12,00** ✘ | 49 açık ✔ | 0,064 sn ✔ | 4/5 |
| **900 sn** | 8,72 sn ✔ | 0 ✔ | **7,00** ✔ | 47 açık ✔ | 0,070 sn ✔ | **5/5** |

**K1 limitten bağımsız geçiyor** — kendi ölçtüğü şey ilk uygun çözüme ulaşma
süresi ve o üç koşuda da 8–9 saniye. Limit yalnızca çözümün **kalitesini**
etkiliyor, ki K3 tam olarak kalite ölçüyor.

**K3 yakınsama sınırlı, yapısal değil.** 30 → 12 → 7: sapma çözücü süresiyle
tekdüze düşüyor ve 900 saniyede eşiğin altına iniyor. Betiğin ulaşılabilirlik
teşhisi de bunu söylüyor — her havuz hedefine erişebiliyor (31 kişilik havuz
kişi başı 42,6 gece saatine kadar, 9 kişilik havuz 177,8'e kadar), yani engel
kadro değil arama. Bu, **Tur 9'un ağırlık kalibrasyonuna** giden bir gözlem:
S3'ün ağırlığı gece dengesini daha erken sıkıştırırsa 60 saniyede de inebilir.
Ağırlıklara bu turda dokunulmadı (devam belgesinin açık talimatı).

**K4 senaryosu düzeltildi.** Saat modelinde beş şefin izinli olması açık
üretmiyordu — çözücü blokları uzatarak kapatıyordu. Senaryo dokuz şefin
**yedisini** izne çıkarıyor ve aritmetiği docstring'e yazılı: nokta haftada
168 kişi-saat istiyor, kalan iki kişi H5/H6 altında en çok 132 saat verebiliyor,
yani açık **kaçınılmaz**.

### İş 7 — arayüz

`frontend/src/lib/blok.ts` tek okuma yeri: blok ISO damgasından okunuyor,
`new Date` kullanılmıyor — tarayıcının saat dilimi ızgarayı kaydıramaz.
Çizelge ızgarası `baslangic_zamani`/`bitis_zamani` okuyor, düzenleme formunda
vardiya tipi seçicisi yerine **başlangıç ve bitiş saati** seçicileri var,
nokta görünümünde vardiya tipi ekseni kalktı. Tanımlar ekranından Vardiya
Tipi sekmesi ve Sabit Vardiya alanı silindi.

`EK_B_UC_NOKTALAR.md` yeniden üretildi: altı `vardiya-tipi` ucu düştü,
**74 → 68**; `uc_noktalari_listele.py --denetle` 68 = 68 diyor.

### Turun kapanış durumu

- Backend **341 test geçiyor** (316 + 24 örnekli uyum testi + ağırlık
  kalibrasyonu). `test_agirlik_kalibrasyonu`'nun çözücü limitleri geçici
  olarak 90/180'e çıkarılmıştı, **60/90'a geri alındı** ve o hâliyle geçiyor.
- Frontend `tsc -b` temiz, **162/162** vitest, oxlint'te yalnızca önceden
  var olan uyarılar.
- Uyum testi (SDD 3.2.1) `optimal` yerine `optimal | uygun` kabul ediyor:
  test **mutabakat** ölçüyor, optimallik değil, ve saat modelinde optimallik
  kanıtı belirgin biçimde pahalı.
- Kanonik belgeler `BOTAS_Vardiya_Cizelgeleme_*` → **`VARDIS_*`** olarak
  `git mv` ile yeniden adlandırıldı, atıflar güncellendi.
- Sunucuya dağıtım **yok**; `push`/`remote` **çalıştırılmadı**.

### DOKÜMAN BORCU — iki madde

1. **SRS H1 / H9 — `Σ_{s ∈ gün d} z[p,s]` gösterimi belirsiz.** Sembol duvar
   saatini mi bloğun sayıldığı günü mü gösterdiğini söylemiyor; H9'un metni
   ikincisini söylüyor, formül birincisi gibi okunuyor. Uygulama metne
   uyuyor. Gösterimin (SRS 4.1) "gün d" tanımını açıkça bloğun başlangıç
   gününe bağlaması gerekiyor.
2. **SRS 3.3.6 — kadro tablosu Müracaat satırını taşıyor.** Yetkinlik
   havuzları tablosunda "Müracaat Görevlisi" hâlâ duruyor; 3.3.2 ve 3.3.3
   noktayı kaldırdı. Toplam satırı da (144 kişi-vardiya / 29 kişi) blok
   sayısına dayanıyor ve blok kavramı kalktı.

---

## 2026-08-13 — Tur 4: Kural Kataloğu — **BİTTİ**

Kaynak: `docs/turlar/CLAUDE_CODE_PROMPTU_TUR4.md`, `TUR4_DEVAM.md` ve
`TUR4_K3_KARARI.md`. Sekiz iş; hepsi bitti. Çalışma `tur4-kural-katmani`
dalında yürüdü — turun ilk yarısında yarım kalan kural katmanı `main`e
bulaşmasın diye.

Doküman sürümleri turun üç noktasında doğrulandı: başta SRS 1.16 / SDD
1.26 / Backlog 1.12 / Charter 1.2; devam yönergesiyle Backlog **1.13**;
K3 kararıyla Charter **1.3** / SRS **1.17** / Backlog **1.14**.

### İş 1 — testler arası veri sızıntısı (B-22)

Her testten **önce** çalışan bir fikstür tanım/girdi/sonuç tablolarını
uygulamanın kendi silme yolundan boşaltıyor. Temizlik testten önce, sonra
değil: başarısız bir testin verisi incelenebilsin.

**Sızıntı önce ölçüldü.** `test_analiz_api` + `test_tanim_api` normal
sırada 30/30 geçiyor, ters sırada bir test düşüyordu. Fikstürden sonra iki
sıra da geçiyor; tam takım ters dosya sırasında da **327/327** verdi.

### İş 2 — blok görünümü türevi kaldırıldı

`blok_gorunumu_uret` ve `Baglam.talep` yok. S2, S3 ve S4 talebi doğrudan
saat ekseninden okuyor; türevin tüketicisi kalmadı. Yük göstergesi de
kişi-vardiya sayısını bıraktı (FR-1.9): karışık uzunluklu katalogda o sayı
kataloğun bileşimine bağlıdır, talep değişmese bile değişir.

### İş 3 — H5 yeniden, H9 ve H10

45 saat artık tavan değil **eşik** (H10'un parametresi); H5 mutlak tavanı
66'ya çıktı — günlük 11 saat × altı çalışma günü, H6 ve H9'un zaten ima
ettiği sınır. H9 günü sınırlıyor ve blok kataloğu kısıtı **aynı
parametreyi** okuyor, Tur 3'teki geçici sabit silindi.

H10 fazla çalışmayı **ayrık takvim haftalarında** topluyor; hafta kümeleri
kayan pencere yardımcısından ayrı bir fonksiyonda üretiliyor (TD-14).
Karışmanın sonucu sessizdir: kayan pencerede aynı saat yedi pencereye
girer ve toplam yedi katına çıkar.

**Kural zorunlu ama modeli çözülemez yapmıyor** ve bunu söyleyen bir test
var: kotası dolmuş personel eşiğe kadar çalışmaya devam ediyor.

### İş 4 — S1'in üst sınırı esnek

Karışık uzunluklu katalogda fazla kadro **yapısaldır** — on saatlik blokla
kapatılan sekiz saatlik talep iki saat fazla üretir — dolayısıyla zorunlu
üst sınır modeli çözülemez yapardı. `fazla` değişkenleri `eksik` ile aynı
saat gruplamasından geçiyor.

`w1f` **ayrı bir kural kaydı** (S1f): kural tablosu kural başına tek
ağırlık sütunu taşıyor ve S1'in formülasyonunda iki ağırlık var —
S6/S6b'deki aynı bölme. Karar Backlog 1.13'e işlendi; gerekçe ağırlığın
Kural ekranından ayarlanabilir olması (FR-1.11).

Manuel düzenlemede fazla kadro **ceza üretmemeye devam ediyor**; iki
tarafın farklı davranması bilinçli (SRS 4.3).

### İş 5 — S2/S3 saat birimine, S6 kaymaya

`gece_saat[b] = |b ∩ [20:00, 06:00]|` tek yerde. `gece_mi` bayrağı tanımlı
alan olarak kaldı — öneri kuralı yalnızca yeni blok oluştururken
ön-dolduruyor. S6 dairesel başlangıç saati kaymasına geçti: 08.00–16.00 ile
08.00–20.00 farklı bloklar ama aynı saatte başlıyorlar ve ergonomik bir
kayma üretmiyorlar.

### K3 KARARI — eşik değil, hedef yanlıştı

Ölçüm iki ayrı sorun gösterdi ve ikincisi ağırdı: yedi kişilik Müracaat
havuzunun erişebildiği gece talebi kişi başına en fazla **22,86 saat**,
hedef 40. O havuz hedefe **hiçbir çizelgeyle** ulaşamıyordu; hangi eşik
konursa konsun kalıcı olarak sapmalı görünürdü.

**Hedef kişiye özel adil paya döndü** (SRS 1.17): her talep birimi ona
erişebilenler arasında eşit bölünüyor, kişinin hedefi kendi paylarının
toplamı. K3'ün ölçümü **34 → 1,15**'e indi ve ulaşılabilirlik teşhisi
artık "her havuz hedefe erişebiliyor" diyor.

**Eşik katalogdan türetiliyor** (Charter 1.3): katalogdaki en uzun gece
bloğunun süresi. Sabit bir saat değeri katalog her değiştiğinde elle
yeniden ölçekleme isterdi; oran ise hedef büyüdükçe gevşer, küçüldükçe
imkânsızlaşır.

Bu, aynı kalıbın **ikinci** görülüşü: önce hiç gece alamayan personel
paydada sayılıyordu, sonra kısıtlı erişimi olan havuz tek ortalamaya
vuruluyordu. İkisinde de ölçü, hiçbir çizelgeyle kapatılamayan bir sapma
raporluyordu.

### Uyum testinin yakaladığı gerçek hata

S3'ün sapma değişkeninin üst sınırı bir kişinin **fiilen taşıyabileceği**
azami yüktü; adil pay ise kadro yetersizken bunu aşabiliyor. O durumda
kısıt sınırı aşıyor ve model **çözülemez** dönüyordu — oysa kadro
yetersizliğinin doğru cevabı çizelgeyi üretip açığı göstermektir (FR-5.2).
24 rastgele örnekten biri buna denk geldi. Üst sınır artık payı da
kapsıyor; uyum testi **24/24** temiz.

### İş 6 — katalog yedi bloğa, gösterim verisi dört senaryoya

Katalog SRS 3.3.1'deki yedi blok. On iki saatlik bloklar haftalık eşiği
gerçekten aşabildiği için H10'un işlediğini gösterebilen tek yapı.

**Kadro 44'ten 30'a indi.** 44 kişide kişi başına haftalık yük 26 saatti;
kimse eşiğe yaklaşmıyor, H10 hiçbir zaman tetiklenmiyordu. 30 kişide yük
**38,4 saat** — eşiğe yakın ama altında.

| Senaryo | Açık | En yüksek hafta | Fazla çalışma | Uzun blok |
|---|---|---|---|---|
| Dengeli (Bu Hafta) | 0 | 50 sa | 32 sa (10 kişi) | 9 |
| Sıkışık | 56 | 54 sa | 149 sa (21 kişi) | 63 |
| Fazla çalışma | 17 | 54 sa | 79 sa (17 kişi) | 19 |
| Kota sınırı | 0 | 48 sa | 30 sa (10 kişi) | 9 |

Kota senaryosunda Ahmet Yılmaz'ın (devir 265, kalan 5) haftalık yükü **40
saat**: çalışmaya devam ediyor, eşiği aşamıyor. Ön kontrol bunu adıyla
bildiriyor.

**Sıkışık senaryonun çelişkisi erişilebilirliğe taşındı.** On iki saatlik
bloklar girince "kadroyu küçült" mekanizması çalışmaz oldu — kabul ölçümü
bunu sıfır açıkla yakaladı. Vardiya şefliği havuzunun beşini izne çıkarmak
blok uzunluğundan bağımsız çalışıyor: eksik olan saat değil, o noktadan
geçebilen **kişi** (H8).

Personel gerçekçi adlar taşıyor.

### İş 7 — çizelge hücresinde saat aralığı

Hücre `08–16 · GÜV` gösteriyor, renk **başlangıç saati bandından**
geliyor. Yedi bloklu katalogda "Gündüz" adını taşıyan iki blok aynı
kısaltmaya sıkışıyor ve ızgara iki farklı çizelgeyi aynı gösteriyordu.
06.00'da başlayan uzun blok gündüzden ayrı bir bantta — aynı renk olsalardı
06–16 ile 08–16 ayırt edilemezdi.

### İş 8 — ön kontrole kota bulguları

Devir kotayı aşmışsa **kesin bulgu** (H10 tek başına sağlanamaz; veri
hatası, kişinin adıyla), kalan kotası bir haftalık fazla çalışmaya
yetmiyorsa **uyarı**. İkisi de çözümü engellemiyor (K18).

### Kabul ölçümü — 5/5

| Kriter | Eşik | Tur 3 | **Tur 4** |
|---|---|---|---|
| K1 40×28 | < 60 sn | 1,01 sn | **3,36 sn** |
| K2 zorunlu ihlal | 0 | 0 | **0** |
| K3 gece adaleti | ≤ 1 gece bloğu (10 sa) | 0,61¹ | **2,85** |
| K4 eksik gösterimi | ≥1 açık | 13 aralık | **12 aralık (76 sa)** |
| K5 manuel düzenleme | < 1 sn | 0,035 sn | **0,051 sn** |

¹ Tur 3'te birim vardiya sayısıydı; sayılar doğrudan karşılaştırılamaz.

K1 üç katına çıktı (katalog ikiye katlandı) ama eşiğin yarısı olan 30
saniyenin çok altında — K17'nin "dur" koşulu oluşmadı.

### Bilinen sapma — dengeli dönemde bir miktar fazla çalışma

Dengeli dönemde on kişi toplam 32 saat fazla çalışma taşıyor; hedef "eşiğe
yakın ama altında"ydı. Ortalama 38,4 saat, en yüksek hafta 50. Sebep
**ağırlık ölçeği**: S2/S3'ün birimi saate döndüğü hâlde ağırlıkları
değişmedi, dolayısıyla S4'ün dengeleme baskısı görece zayıf. Bu
**beklenen** bir durum ve düzeltmesi Tur 8'in kalibrasyonu; bu turda
ağırlıklara dokunulmadı.

### DOKÜMAN BORCU — yok

Bu turda dört kanonik dokümana dokunulmadı; K3 kararının gerektirdiği
Charter 1.3, SRS 1.17 ve Backlog 1.13/1.14 güncellemeleri proje
yürütücüsü tarafından yapıldı ve dala alındı.

### Bekleyen göçler — dağıtım yapılmadı

Sunucu **`d1f83a6c40b2`** noktasında (Tur 3, 12.08.2026'da çıktı; Tur 2'nin
iki göçü ondan önce uygulanmıştı). Bekleyen tek göç bu turunki:
**`e7b2c4915d80`** — şemayı değiştirmez, yalnızca `kural` tablosunu
günceller: H5'in parametresini `azami_haftalik_saat` → `haftalik_mutlak_tavan`
olarak taşır ve değerini 66 yapar, H9/H10/S1f kayıtlarını ekler. Var olan
kayda dokunmaz (kullanıcının değiştirdiği bir ağırlığı geri almaz) ve iki
kez koşulabilir.

**Dağıtımda dikkat:** göç kural kayıtlarını değiştiriyor, kod ise yeni
parametre adını okuyor — ikisi birlikte gitmeli. Eski kod yeni parametreyle
`KeyError` verir, yeni kod eski parametreyle de. Dağıtım kararı proje
yürütücüsünde.


---

## 2026-08-12 — Tur 3: Saatlik Düzenin Veri Temeli — **BİTTİ**

Kaynak: `docs/turlar/CLAUDE_CODE_PROMPTU_TUR3.md`, `TUR3_DEVAM.md` ve
`TUR3_DEVAM_2.md`. On işlik bir tur; **onu da bitti.** İlk sekiz `374caa3`
ile, kalanlar turun sonunda commit'lendi.

Doküman sürümleri iki kez doğrulandı: turun başında SRS 1.15 / SDD 1.23 /
Backlog 1.9, devam yönergesinden sonra SRS **1.15** / SDD **1.24** /
Backlog **1.10** / Proje Tanım Dokümanı 1.2. Bildirilen dört doküman
borcunun tamamı kapatılmış olarak geldi.

### Uygulama planı

[`docs/turlar/UYGULAMA_PLANI_V2.md`](docs/turlar/UYGULAMA_PLANI_V2.md).
Bir süre `docs/` altında arayıp "eksik" diye kaydetmiştim; dosya o sırada
depo kökündeydi. Yerleşim kuralı artık planın kendisinde yazılı ve tek:
**kanonik dört doküman `docs/` altında, plan/prompt/yönerge dosyalarının
tamamı `docs/turlar/` altında**, depo kökünde plan veya prompt bulunmaz.

Plan Tur 3 için bu turda yapılanları birebir doğruluyor ve iki kural
ekliyor: **her turda kabul ölçümü koşulur** (K17 — blok kataloğu
büyüdükçe K1 riski artıyor, ölçüm sona bırakılmaz) ve **yeniden tanımlanan
bir kuralın eski testi silinmez, güncellenir** (davranışın bilinçli mi
kazayla mı değiştiği bilgisi kaybolmasın). İkincisi bu turda uygulandı:
S1'in birim değişikliğinde testler silinmedi, beklenen değerler
gerekçesiyle birlikte güncellendi.

### Biten ve ölçülen işler

#### İş 1 — Talep tablosu zaman aralığına (göç `d1f83a6c40b2`)

`talep.vardiya_tipi_id` yerine `baslangic` ve `bitis` (TIME). Dönüşüm göç
içinde yapılıyor ve **sayılarak** doğrulanıyor: satır sayısı ile toplam
kişi-saat yükü eşit değilse göç hata verip duruyor. Sessizce devam etmesi
hâlinde kaybolan bir talep satırı hiçbir yerde görünmezdi — talep düştüğü
için kapsama açığı da doğmaz.

**Ölçüldü (geliştirme veritabanı):** 27 satır → 27 satır, **384 kişi-saat →
384 kişi-saat.** Geri alma yazıldı; test veritabanında ileri → geri → ileri
denendi.

Aynı göç `kapsama_acigi` ve `fazla_kadro` tablolarını da aralığa çeviriyor,
`personel`e devir bakiyesi alanlarını (`devir_fazla_calisma_saat`,
`kota_yili`) ve `cozum_isi`ne `on_kontrol_bulgulari` alanını ekliyor.

**Açık/fazla kadro satırları dönüştürülmüyor, siliniyor.** Bu iki tablo bir
çözümün çıktısıdır, kullanıcının girdiği veri değil; blok eksenli bir açık
kaydını aralığa çevirmek o kaydın üretildiği andaki talebi yeniden kurmayı
gerektirir ve talep aynı göçte değişiyor. Satırlar sürüm yeniden
çözüldüğünde ya da elle düzenlendiğinde doğru biçimde yeniden yazılıyor.
Yanlış dönüşmüş bir açık kaydı, hiç olmamasından kötüdür: rapora doğru gibi
girer.

#### İş 2 — Talebin saate açılımı, tek yerde

`app/services/talep_cozucu.py` → `talebi_saate_ac`; aralık aritmetiğinin
kendisi `app/kurallar/zaman_araligi.py`de (ORM'den bağımsız, kural katmanı
da kullanabiliyor). Sınırlar başlangıçta kapalı, bitişte açık: `08.00–16.00`
→ 08…15, 16 dışarıda. Isıtma penceresi dahil (TD-5). Gece yarısını aşan
aralık ertesi günün duvar saatlerine taşıyor.

#### İş 3 — S1 saat ekseninde; **turun asıl kabulü geçti**

Göç öncesi taban (7 günlük dönem, tek arama işçisi, 120 s):
toplam **1096**, S1 0, S2 40, S3 40, S4 202, S6 18, S7 17, **144 atama, 0
açık**.

Göç sonrası aynı dönem: **S1 0, 144 atama, 0 açık**, toplam 1055. Kapsama
birebir aynı; toplam daha düşük çünkü çözücü daha iyi bir çözüm buldu (iki
koşum da optimalliği kanıtlamıyor, "uygun" durumunda bitiyor).

**Yolda bir tuzak çıktı — kaydı burada duruyor.** İlk uygulamada aynı dönem
120 saniyede **704 kişi-saat** açıkla çıkıyordu; 420 saniyede bile 536'ya
inebildi. Sebep yapıda değildi: hizalı katalogda bir bloğun sekiz saati
**aynı kısıtı** üretiyor ve sekiz **birbirinin yerine geçebilen** `eksik`
değişkeni doğuruyordu; çözücü zamanının çoğunu bu simetriyi kırmakla
harcıyordu. Aynı kısıtı üreten saatler tek değişkende toplandı ve amaç
fonksiyonundaki katsayı grubun saat sayısı yapıldı. **Anlam değişmedi** —
ceza saat başına birikmeye devam ediyor — ama arama eski hâline döndü.

#### İş 4 — Açık ve fazla kadro aralık olarak (kısmen)

Birleştirme `saatleri_araliklara_birlestir` ile **tek yerde**: ardışık ve
sayısı eşit saatler tek satıra iniyor (00…07'de 1 kişi eksik → tek
`00.00–08.00 / 1` kaydı). Hem çözücü yolu hem elle düzenleme yolu
(`sapmalari_yenile`) aynı yardımcıyı kullanıyor. Talep ile atamanın saat
bazında farkı `Baglam.sapma_saatleri`nde tek tanım; doğrulayıcının S1
bulguları da kalıcı sapma tabloları da oradan çıkıyor.

#### İş 8 ve İş 10 — servis tarafı

Ön kontrol bulguları artık **işi düşürmüyor**: `Bulgu.engel_mi` →
`kesin_mi` (anlamı "kesin bulgu mu, uyarı mı"), `engelleyenler` →
`kesin_bulgular`, ve çözüm işçisi bulguları `cozum_isi.on_kontrol_bulgulari`
alanına yazıp çözüme devam ediyor. Bulgu metinleri kimlik yerine ad
taşıyor (`Baglam.yetkinlik_adi/nokta_adi/vardiya_adi`).

### Tasarımdan sapmalar — ikisi de zorunluydu

1. **Gün sonu `24.00` yerine `00.00` ile yazılıyor.** SDD 4.2.2 `24.00`
   diyor. PostgreSQL bu değeri saklıyor fakat sürücü (psycopg) geri
   okuyamıyor — denendi: `DataError: can't parse time '24:00:00': hour must
   be in 0..23`. Python'un `time` tipi 24:00'ı taşımıyor. Bunun yerine
   `vardiya_tipi` tablosunun **zaten kullandığı** sözleşme uygulandı:
   `bitis <= baslangic` ise aralık gün sonuna kadar sürer, gece yarısını
   aşıyorsa ertesi güne taşar. Sütun tipi SDD'deki gibi TIME kaldı; değişen
   yalnızca 24.00'ın kodlanışı ve bu kural tek yerde (`zaman_araligi.py`)
   uygulanıyor.

2. **Blok eksenli talep görünümü korundu** — saat ekseninden türetilerek.
   S2, S3 ve S4 talebi hâlâ **vardiya biriminde** okuyor
   (`hedef_gece = Σ talep / |havuz|`, `Σ sure_saat × gereken`) ve bu turda
   kural kataloğuna dokunmak yasak. Talep doğrudan saate çevrilseydi
   S2/S3'ün hedefi sekiz katına çıkar ve "aynı toplam ceza" kabulü
   kırılırdı. İkinci bir **tanım** yazılmadı: tek kaynak `talep_saat`,
   `blok_gorunumu_uret` ondan tek yerde türetilen bir **türev** (bir bloğun
   gereken sayısı, kapsadığı saatlerdeki en büyük gereken). Hizalı
   katalogda eski tablonun birebir aynısını veriyor. Tur 4'te S2/S3 saate
   geçince türev kalkar.

### DOKÜMAN BORCU — **dördü de kapatıldı**

Aşağıdaki dört madde bildirildikleri hâlleriyle duruyor; **hepsi SDD 1.24
ve Backlog 1.10 ile karşılandı** (gün sonunun kodlanışı SDD 4.2.2'ye,
`on_kontrol_bulgulari` 4.2.4'e, talep uç noktaları Ek B'ye yazıldı;
FR-1.9'un kişi-vardiya türevi Backlog **B-21** olarak kaydedildi ve Tur
4'te saat tabanına taşınacak). Açık borç DEĞİLDİR; kayıt olarak duruyor.

1. **SDD 4.2.2 / 4.2.4 — gün sonunun kodlanışı.** "24.00 gün sonunu
   gösterir" ifadesi uygulanabilir değil (yukarıdaki 1. sapma).
   Dokümanda `bitis <= baslangic` sözleşmesinin yazılması gerekiyor.
2. **SDD 4.2.4 — `cozum_isi.on_kontrol_bulgulari`.** İş 8 bulguların
   "sürüm kaydında kalıcı" olmasını istiyor; SDD'de böyle bir alan tanımlı
   değil. Alan eklendi, dokümana işlenmeli.
3. **SDD Ek B — talep uç noktaları.** Talep artık hücre değil kayıt
   olduğundan `PUT /api/talep` yerine `POST /api/talep`,
   `PUT /api/talep/{id}` ve `DELETE /api/talep/{id}` var. Ek B yalnızca
   `GET, PUT` listeliyor; uç nokta sayısı 72 → 74.
4. **FR-1.9 — kişi-vardiya artık türev.** Talep blok taşımadığı için
   haftalık kişi-vardiya, kişi-saatin katalogdaki ortalama blok uzunluğuna
   bölünmesiyle bulunuyor (tek uzunluklu katalogda SRS 3.3.6'daki referans
   örneği birebir veriyor: 1.152 saat / 8 = 144, asgari kadro 29).
   Karışık uzunluklu katalogda bu bir yaklaşıktır; asgari kadro hesabının
   saat tabanına taşınması Tur 4'ün konusu olabilir.

### Test fikstürleri aralık şekline geçirildi — takım 320/322

Ondan fazla test dosyası ve iki betik (`demo_veri_uret.py`,
`kabul_olcumu.py`) eski `Talep(vardiya_tipi_id=…)` şeklini kuruyordu.
Ortak kaynak `ornek_senaryo.py` de SRS 3.3.4'ün yeni aralık tablosuna
geçirildi ve referans yükü koruyor: **haftalık 1.152 kişi-saat**, sekiz
saatlik katalogda 144 kişi-vardiya ve 29 kişilik asgari kadro (FR-1.9
testi birebir geçiyor).

Yol boyunca üç şey ortaya çıktı ve düzeltildi:

- **Göç dosyasını koştuktan sonra değiştirmiştim** (`on_kontrol_bulgulari`
  sonradan eklendi), bu yüzden iki veritabanı da göçün eski hâlindeydi ve
  geri alma da tutmuyordu. Göç yayınlanmadığı için ikisi de göç
  zincirinden sıfırdan kuruldu — elle `ALTER TABLE` yok.
- **`test_cizelge_api` sıra bağımlıydı:** ön kontrol bütün tanım verisine
  baktığı için başka bir testin bıraktığı nokta/talep bulgu üretiyordu.
  Fikstür artık senaryo verisini temizliyor.
- **`Bulgu.engel_mi` yalnızca serviste yeniden adlandırılmıştı**; API
  şeması ve arayüz hâlâ eski adı taşıyordu. Üçü de `kesin_mi` oldu.

S1'in birimi değiştiği için beklenen test güncellemeleri yapıldı: sekiz
saatlik blokta bir kişilik açık artık **8 kişi-saat** ceza üretiyor (eski
ölçüde 1 idi) ve bulgu metni blok adı yerine **aralık** taşıyor
(`2026-02-02 · 16.00–24.00 · Güvenlik`).

`test_cozum_on_kontrolde_yapisal_engel_varsa_cozmeden_basarisiz_doner`
adıyla birlikte tersine çevrildi: artık
`test_on_kontrol_bulgusu_cozumu_dusurmez_cizelge_yine_uretilir` ve
çizelgenin **üretildiğini**, bulgunun iş kaydında kaldığını, açığın
kapsama açığı olarak raporlandığını ölçüyor.

### İş 9 — kapsama oranı atamalardan (SDD 5.7, K19)

Oran artık `Σ min(atanan, talep) / Σ talep` ile **atama kayıtlarından**
hesaplanıyor; kapsama açığı tablosu bir raporlama detayı. `min(...)` şart:
bir saatteki fazla kadro başka bir saatteki açığı kapatmaz. Talep yoksa
oran **tanımsız** (`None`) — sıfır bölme yerine yüzde yüz varsaymak, boş
bir dönemi kusursuz bir çizelge gibi gösterirdi.

### Takım yeşil — ara commit atıldı

**322/322 geçiyor**, `ruff check` ve `ruff format --check` temiz. Buraya
kadarki iş `374caa3` ile commit'lendi (TUR3_DEVAM'ın istediği ara commit).

---

## Turun ikinci yarısı — kalan altı iş bitti

Kaynak: `docs/turlar/TUR3_DEVAM_2.md`. Tur **kapandı**.

### İş 7 — Talep ekranı aralık girişine

Ekran eski matrisi çiziyor ve kırıktı: hücrelere yazılan hiçbir sayı
kaydedilemiyordu, çünkü beslendiği `PUT /api/talep` ucu artık yok. Yerine
her satırı bir aralık olan liste geldi — nokta, gün tipi, tarih, aralık,
süre, gereken — ve Ekle/Değiştir/Sil üçlüsü diğer sekmelerle **aynı
konumda, aynı sırada** (SDD 6.3.1). Görsel geliştirme Tur 6'nın işi;
buradaki hedef işlevsellikti.

Üç karar kayda değer:

1. **Saatler açılır liste, serbest metin değil.** Aralıklar saat başında
   başlamak zorunda (kapsama kısıtı saat ekseninde yazılır); serbest bir
   alan 08.30 yazdırıp sunucudan hata almayı mümkün kılardı. Bitiş
   listesinde 00.00 **yoktur** — gün sonu 24.00'tır ve ikisi aynı değeri
   kodlar; iki ayrı seçenek görünmesi kullanıcıyı yanıltırdı.
2. **Tarih alanı forma girdi.** İş tanımı beş alan sayıyordu ama talep
   kayıtlarının tarihe özgü istisnaları var ve listede zaten görünüyorlar.
   Alan olmasaydı, istisna satırı genel satırın kopyası gibi durur ve
   kullanıcı farkı hiçbir yerden okuyamazdı.
3. **Yanıt alanı `hucreler` → `araliklar`.** Eski ad ekranın da matris
   çizmesine yol açmıştı; sözleşme değişirken adın kalması, sonraki
   okuyucuyu aynı yanlışa davet ederdi.

Ekranın sözleşmesi `TanimlarEkrani.test.tsx`te kilitli: 24.00 gösterimi,
POST/PUT/DELETE yolları ve 409'un anlaşılır hâle gelmesi.

### İş 6 — blok kataloğu kısıtları

İkisi de **girişte** reddediliyor: aynı `(baslangic_saati, sure_saat)`
ikinci kez tanımlanamaz (**409** — istek geçerli, mevcut veriyle çakışıyor)
ve süre günlük azami çalışmayı aşamaz (**400** — değerin kendisi geçersiz).
Ayrım korunuyor çünkü kullanıcının yapacağı şey farklı: biri başka bir saat
seçer, öbürü süreyi kısaltır.

**Pasif bloklar benzersizlik sayımında yok.** Sayılsalardı, kullanımda
olduğu için silinemeyip pasifleştirilmiş bir blok o saatlerde yeni blok
tanımlamayı **kalıcı olarak** imkânsız kılardı ve kullanıcının
düzeltebileceği bir yol kalmazdı.

**GEÇİCİ YAPILANDIRMA DEĞERİ — Tur 4'te silinmeli.** Azami süre
`kural.parametre_getir("H9", "azami_gunluk_calisma_saati", …)` ile **kural
kataloğundan** okunuyor; H9 henüz yok, o yüzden çağrı
`_GECICI_AZAMI_GUNLUK_CALISMA_SAATI = 11` varsayılanına düşüyor
(`app/services/tanim_servisi.py`). H9 yazıldığında kısıt kendiliğinden
onun değerini kullanmaya başlar ve **sabit silinmelidir** — iki yerde duran
bir sayı sessizce birbirinden ayrılır. Kısıt ile kuralın ayrı sayılar
taşıması, girişi geçen bir bloğun çözümde her gün ihlal üretmesi demekti.

**Test takımı bu kısıtla çelişiyordu ve bu bir bulgu.** Test veritabanı
koşumlar arasında sıfırlanmıyor; blok yaratan testler kayıtlarını
bırakıyordu, dolayısıyla katalogda üç tane 08.00/8sa blok birikmişti.
Kısıt gelince üç test kırıldı — kısıt yanlış olduğu için değil, testler
katalogda çöp biriktirdiği için. İki yardımcı eklendi
(`gecici_vardiya_tipi` blok açıp test bitince düşürür, `bos_vardiya_blogu`
saatleri testin konusu olmayan yerlere boş bir saat verir) ve birikmiş
kayıtlar uygulamanın kendi silme yolundan temizlendi — elle SQL yok.

### İş 5'in form tarafı — devir bakiyesi

`devir_fazla_calisma_saat` ve `kota_yili` şemalara, API'ye ve personel
formuna girdi. **Bu turda hiçbir kural bu alanları okumuyor**; toplanmalarının
nedeni Tur 4'ün kota hesabına hazır olmaları. Boş bırakılan devir **sıfır**
(sütun NOT NULL, "bilinmiyor" hâli tanımlı değil), kota yılı boş kalabilir.
Servis açıkça `null` gönderen bir istemciye karşı da korumalı.

### Blok görünümü türevine varsayım yorumu

`blok_gorunumu_uret`, kullanıcısı (`baglam_kurucu`) ve taşıyıcı alan
(`Baglam.talep`) — üçüne de aynı uyarı yazıldı: türev **tek uzunluklu ve
hizalı** bir katalog varsayar. Tur 4'te 10 ve 12 saatlik bloklar girdiğinde
"en büyük gereken" kuralı yanlışlaşır (06.00–18.00 bloğu gece 3 ve gündüz 7
kişilik talebi birlikte örter, türev 7 sayar) ve **hata vermez**. Yorum
düzeltmeyi değil **kaldırmayı** işaret ediyor: doğru çözüm S2/S3'ü saat
eksenine taşımaktır.

### Kabul ölçümü — K1 **1,01 sn** (eşik 60 sn)

Simetri gruplamasından **sonra**, bu makinede (macOS arm64, 10 çekirdek;
arama işçisi SDD 3.4.3 referansına sabit: 3):

| Kriter | Eşik | Tur öncesi | **Şimdi** |
|---|---|---|---|
| K1 40×28 | < 60 sn | 1,12 sn | **1,01 sn** |
| K2 zorunlu ihlal | 0 | 0 | **0** |
| K3 gece sapması | ≤ 1,0 | 0,61 | **0,61** |
| K4 eksik gösterimi | ≥1 açık | 21 hücre | **13 aralık (112 saat)** |
| K5 manuel düzenleme | < 1 sn | 0,038 sn | **0,035 sn** |

**5/5 geçti.** K1 artmadı — blok kataloğu bu turda büyümedi ve simetri
gruplaması aramayı göç öncesi hâline döndürdü.

**K4 ölçümün kendisi eskimişti ve önce kaldı.** Betik açık kayıtlarının
orta anahtarını hâlâ vardiya tipi kimliği sanıyor, saat numarasını
yazdırıyordu ("2026-06-06 / 0 / Vardiya Şefliği") ve "üç bilgi de dolu"
denetimi bu yüzden düşüyordu. Ölçülen şey bozulmamıştı; ölçü İş 4'ün
ardından güncellenmemişti. Betik saat eksenli eksikleri nokta içinde
aralığa birleştirip kullanıcıya gösterilen biçimi ölçüyor artık.

**Yol üstünde bir hata daha çıktı:** saat metnini yazan yardımcı **üç ayrı
modülde** kopyalanmıştı (`esnek.py`, `tanim_servisi.py`, `kabul_olcumu.py`)
ve üçü de aynı yanlışı yapıyordu — gün başında başlayan bir aralığı
"24.00–08.00" diye yazıyorlardı, çünkü 00.00'ı başlangıç mı bitiş mi
olduğuna bakmadan 24.00'a çeviriyorlardı. Okuyan kişi bunu gece yarısını
aşan bir aralık sanardı. Tanım `zaman_araligi.py`ye taşındı
(`saat_metni`/`aralik_metni`), üç kopya kaldırıldı.

### Ek B yeniden üretildi — 72 → 74

`PUT /api/talep` kalktı; `POST /api/talep`, `PUT /api/talep/{id}` ve
`DELETE /api/talep/{id}` geldi. Dosya "üretilmiştir" diyordu ama üreteci
yoktu; `backend/scripts/uc_noktalari_listele.py` eklendi. `--denetle`
uygulamanın yönlendirme tablosunu Ek B ile karşılaştırır ve fark varsa
sıfırdan farklı kodla çıkar — sayı artık elle sayılmıyor.

### S1'in ölçeği büyüdü — Tur 8'in kalibrasyonuna not

Sekiz saatlik blokta bir kişilik açık artık **1 yerine 8 birim** ceza
üretiyor (ceza saat başına birikiyor). `w1` değişmediği için S1'in diğer
hedefler karşısındaki **baskınlığı arttı**. Şu an sorun değil — baskınlık
zaten istenen şey — ama Tur 8'in ağırlık kalibrasyonunda hesaba katılacak
bir kayma. Bu turda ağırlıklara dokunulmadı.

### Yeni doküman borcu — üç madde

Öncekiler kapandı (yukarıdaki DOKÜMAN BORCU bölümü); bunlar **yeni** ve
**açık**:

1. **SRS FR-1.3 — blok kataloğu kısıtları.** Aynı `(baslangic_saati,
   sure_saat)` ikilisinin benzersizliği ve sürenin günlük azamiyi
   aşamayacağı SRS'te yazılı değil; kısıt kodda var.
2. **SDD 4.2.1 — `personel.devir_fazla_calisma_saat` / `kota_yili`.**
   Göçle geldiler (`d1f83a6c40b2`) ve artık API şemasında da varlar;
   SDD'nin alan listesi henüz taşımıyor.
3. **SDD Ek B — 74 uç nokta.** `docs/EK_B_UC_NOKTALAR.md` güncel; SDD'nin
   kendi Ek B'sine aktarılması bekliyor.

### Bekleyen göçler — dağıtım yapılmadı

Sunucuda **üç göç** birikmiş olacak: `b6e2f81d3c07`, `c9a4b7e21f38` (Tur 2)
ve `d1f83a6c40b2` (bu tur). Sonuncusu veri dönüştürüyor; dağıtımdan önce
yedek alınmalı. Dağıtım kararı proje yürütücüsünde.

---

## Tur 12 — üç okunabilirlik düzeltmesi (Analiz ve Çözüm ekranları)

Üçü de aynı kusurun farklı yüzleri: ekranda **anlamı ancak modeli bilene
açık olan bir sayı** duruyordu.

### 1. Çözüm ekranı hedefleri kimlikle listeliyordu

Sonuç özeti "S1 · S1f · S2 …" yazıyordu; hangi hedefin ne kadar cezalandığı
kural kataloğunu ezbere bilmeyi gerektiriyordu. Artık kısa ad önce, kimlik
yanında küçük punto ile duruyor (`lib/sonucDili.ts` → `hedefAdi`). Kimlik
kaldırılmadı: dışa aktarma ve kural kataloğuyla eşleşmesi gereken şey odur.

### 2. Kota kartındaki "0" hesap hatası gibi okunuyordu

Kart, kalan kotası en az olanı en üste alır. Kotası **devirden** dolmuş bir
kişi için satır "fazla çalışma 0,0 sa · kalan kota 5,0 sa" görünüyordu:
sayılar doğruydu ama satır kendi içinde çelişkili okunuyordu, çünkü iki sütun
**iki ayrı ufku** ölçüyor — kalan kota yılın tamamını, fazla çalışma yalnız
bu dönemi.

`KotaDurumuOku` artık `devir_saat` taşıyor, `AnalizOku` da `yillik_kota_saat`.
Kart dört sütunlu: PERSONEL · DEVİR · BU DÖNEM · KALAN KOTA, altında
aritmetiği yazan bir dipnot. Kotanın sayısı ekranda sabit değil sunucudan
geliyor; kural parametresi değişirse dipnot sessizce yanlış kalmasın.

Excel'deki "Personel Özeti" sayfası da aynı hâldeydi; oraya da devir sütunu
eklendi ve başlıklara ufuk yazıldı. TOPLAM satırı artık aralık yerine **açık
sütun listesi** topluyor: devir ve kalan kota kişi başına tavan kalıntısıdır,
toplamlarının anlamı yok — aralık yazılıydı ve yeni sütun eklendiği anda
sessizce toplama giriyordu.

Bu arada dışa aktarma servisi kota üçlüsünü **kendisi hesaplamayı bıraktı**;
analiz servisinden okuyor. Aynı hesabın iki yerde durması dosyanın kendi
yorum satırlarının reddettiği şeydi.

### 3. Kümülatif değişim kartı ölçüsünü adlandırmıyordu

Kart "önceki 4,07 · şimdi 3,91 · ↓ azalıyor" yazıyordu; **neyin** azaldığı
yalnız "kümülatif değişim" başlığından çıkarılamıyordu. Başlık "gece yükü
adaleti — önceki yayınlanmış döneme göre" oldu ve ölçünün tanımı kartın
içine yazıldı: kişi başına gece saatinin adil paydan ortalama sapması, 0 sa
tam eşitlik. Hesap değişmedi.

### Sınama

Arka uç: `test_analiz_api.py`'ye devirli senaryo (donem içi fazlası gerçekten
sıfır, kotayı devir doldurmuş), `test_disa_aktarma.py`'ye sütun sırası ve
TOPLAM satırının hangi sütunları topladığı. Ön yüz: kota kartının devir
sütunu ve dipnotu, kümülatif kartın ölçü tanımı, Çözüm ekranının hedef
adları. 340 vitest + hafif arka uç takımı (307) geçti; ağır takım ayrıca
koşturuldu.

### DOKÜMAN BORCU — iki madde

1. **SDD 6.3.4 — kota kartı dört sütunlu.** Devir ayrı sütun; `AnalizOku`
   artık `yillik_kota_saat` taşıyor. SDD'deki kart tarifi üç sütun anlatıyor.
2. **SDD 5.8 / Excel "Personel Özeti" sayfası.** Sütun listesi sekize çıktı
   ve TOPLAM satırının hangi sütunları topladığı artık bir sözleşme
   (`_OZET_TOPLANAN_SUTUNLAR`); SDD bunu yazmıyor.

Önceki turun üç maddesi (SRS FR-1.3, SDD 4.2.1 alan listesi, Ek B) **hâlâ
açık**.

---

## Tur 13 — Boş taslak çizelge, elle çizilen sürümün cezası, Özet ekranı

Tasarım `docs/superpowers/specs/2026-08-20-bos-taslak-ve-ozet-tasarim.md`,
plan `docs/turlar/TUR13_PLANI.md`. Yedi görev alt ajanlara dağıtıldı, her biri
ayrı incelendi; sonunda dalın bütünü bir kez daha incelendi.

### 1. Çözücüsüz üretim yolu açıldı

`POST /api/surum` artık `onceki_surum_id` yerine `donem_id` de kabul ediyor
(tam olarak biri, aksi hâlde 422). Hiç sürümü olmayan bir dönemde bile boş
taslak açılabiliyor; dönemde sürüm varsa yenisi **en sonuncuya bağlanıyor**,
çünkü S8 ve sürüm karşılaştırması zincire dayanıyor.

Asıl tıkanma ızgaradaydı: satırlar **atamalardan** türetiliyordu, dolayısıyla
boş bir taslakta tıklanacak hücre yoktu. Artık düzenlenebilir sürümlerde
satırlar kadrodan geliyor (`lib/izgaraSatirlari.ts`), salt okunur sürümlerde
bugünkü davranış duruyor — orada soru "ne karar verildi", boş satır gürültü.

### 2. Ceza dökümünün ikinci kaynağı

Çözücü koşmamışsa **ya da atamalar çözümden sonra değişmişse** döküm esnek
kuralların kendisinden hesaplanıyor. Yeni formül yazılmadı: doğrulama
servisinin zaten kullandığı `kural.dogrula(...)` okuması, farkı değil mutlak
değeri alacak biçimde kullanıldı. Yanıt kaynağı söylüyor (`ceza_kaynagi`) ve
ekranlar bunu yazıyor.

İkinci koşul bir kusuru kapattı: çözülmüş bir sürüm elle düzenlendiğinde
Analiz **çözücünün eski dökümünü** göstermeye devam ediyordu — çizelge
değişmiş, ceza değişmemiş görünüyordu.

S8 hesaplanan dökümde yer almaz: analiz bağlamı `onceki_atamalar` kurmuyor,
ölçü orada tanımsız. Sıfır yazmak "sapma yok" demek olurdu.

### 3. Özet ekranı "şu an ne oluyor"u yanıtlıyor

Dönem seçici yok, dönem bugünden türetiliyor ve **her aralık-bağlı blok hangi
aralığı gösterdiğini yazıyor**. Günlük açık şeridi (sunucudan; toplamı
`karsilanmayan_kisi_saat`'e eşit ve bu bir test), kişi başına saat kısa hâlde,
dönemle kesişen müsaitlik kayıtları. Sekmeye dönüldüğünde tazeleniyor.

"Ölçülebilir sürüm" ölçütü **"taslak değil"den "ataması var"a** döndü: eski
ölçüt "çözülmemiş taslağın ataması yoktur" varsayımına dayanıyordu ve elle
çizilen taslak bunu geçersiz kıldı.

### Nihai inceleme dört ciddi şey buldu

**Kaydet düğmesi hiç çalışmıyordu.** `damga` veritabanında vardı, ön yüz tipi
`damga: string` diyordu, ama hiçbir uç nokta onu döndürmüyordu — `kaydet()`
`damga === null` görüp sessizce dönüyordu. İstek gitmiyor, hata çıkmıyor.
Bu turdan eski bir kusur ama elle çizim yolunun tamamı buna dayanıyordu.
Görev testleri yeşildi çünkü fikstür sürüm listesine uydurma bir damga
koyuyordu; **gerçek sözleşme hiç sınanmamıştı.**

**Kilitler hiç işlemiyordu.** Arayüz çözüm başlatırken `onceki_surum_id`
göndermiyordu, dolayısıyla kilitli atamalar okunmuyordu ve "elle başla,
çözücüye devret" yolu kâğıt üzerinde kalıyordu.

**Atamasız boş taslak yayınlanabiliyordu** ve dolu bir sürümü arşive
gönderiyordu — çalışan panelinde herkesin vardiyası kaybolurdu.

**Özet'in toplam ceza kartı kaynağı söylemiyordu.** Yalnız eksik dipnot değil:
`cozucu` kaynağı S8'i içeriyor, `kurallardan` içermiyor. Kullanıcı tek vardiya
kaydırınca sayı düşüyor ve düşüşün bir kısmı çizelgenin iyileşmesinden değil
kalemin kaynak değişince yok olmasından geliyordu.

Dördü de düzeltildi. Düzeltme dalgasının kendisi bir gerileme açtı ve yeniden
inceleme onu deney koşturarak yakaladı: `onceki_atamalar` boş taslakta `None`
değil `[]` oluyordu, S8'in koruması `is None` olduğu için boş tabanda S8 her
atamayı cezalandırıyordu — ağırlık 15 ile S4'ü 15:1 yenerek çözücüyü
sistematik olarak insanları hedef saatlerinin altında bırakmaya itiyordu.
Tek satır (`or None`) ve bir gerileme testiyle kapatıldı.

### Sınama

Hafif arka uç takımı 324 geçti, 1 atlandı. Ön yüz 376 test, 36 dosya. Ağır
OR-Tools takımı iki kez koştu (ilki 136 geçti; çözücü yoluna dokunulduğu için
düzeltmelerden sonra bir kez daha). `tsc -b` ve `ruff` temiz, uç nokta
denetimi 74/74.

### DOKÜMAN BORCU — altı madde

1. **SRS FR-6.x / FR-7.3** — elle çizim artık çözücüden bağımsız bir üretim
   yolu; boş taslak "çözücünün dolduracağı sürüm" değil.
2. **SDD 5.6** — `CizelgeSurumuDeposu.taslak_ac` ve `POST /api/surum`'un iki
   alanlı sözleşmesi (tam olarak biri, 422).
3. **SDD 5.7** — ceza dökümünün ikinci kaynağı, tazelik ölçütü
   (`atama.guncelleme_zamani <= cozum_isi.bitis_zamani`) ve S8'in hesaplanan
   dökümde bulunmaması.
4. **SDD 6.3.1** — Özet ekranının yeni yapısı, aralık etiketleri, dönem
   seçicisinin bulunmaması.
5. **SDD 6.3.5** — `SurumOzetiOku.atama_sayisi` ve `damga`; atamasız sürümün
   yayınlanamaması.
6. **SDD 4.2.4 / 5.4** — `baglam.onceki_atamalar`da boş liste ile `None`
   ayrımı: "önceki çizelge yok" ile "önceki çizelge boştu" aynı şey değil.

Önceki turun üç maddesi (SRS FR-1.3, SDD 4.2.1 alan listesi, Ek B) ve Tur
12'nin iki maddesi (SDD 6.3.4 kota kartı, SDD 5.8 Excel özet sayfası) **hâlâ
açık**.

### Ertelenenler

Nihai inceleme triyajı sonraya bıraktı: ceza toplama deyiminin iki serviste
kopya olması (ayrışmayı yakalayan değişmez zaten testli, ama ortak yardımcıya
çıkarılırsa S8 elemesinin kaybolmaması gerekir), vakumda kalan bir S8 testi,
aktiflik penceresi sınır eşitliği testi, Özet'teki iki liste üslubu, Sürümler
ve Çizelge ekranlarındaki iki "Boş Taslak Aç" düğmesinin farklı zincir
kurması, atamasız sürümde Analiz'in "kapsama %0" ile "0 açık" arasındaki
çelişkisi, ve cezası gerçekten sıfır olan bir çizimin `ceza_kaynagi="yok"`
dönmesi (sıfır ile bilinmiyor aynı şey değil).

Kapsam dışı bir kural ihlali de kayda geçti: `TercihlerEkrani.tsx:122` düz
`.toUpperCase()` kullanıyor — bu turdan önce de vardı.

---

## Tur 14 — Gösterim ortamı: sıfırdan demo veritabanı

Dokümanlar: DEMO_SENARYOSU 1.0, Charter 1.6, SRS 1.27, SDD 1.36 — dördü de
tur başında doğrulandı.

### 1. Durum tespiti ve `vardis_demo`

`vardiya` veritabanının pg_dump yedeği alındı (özel biçim, `-Fc`):
`~/Desktop/ClaudeProjects/yedekler/vardiya-20260827-211042.dump`, 73.831 bayt.

Canlı `vardiya` göç başı **f4a8c1e60d92** — depodaki `alembic heads` ile aynı.
18 uygulama tablosu + `alembic_version`, 10 enum. `rol` enum'u dört değerli:
`CALISAN, IDARE, HESAP_YONETICISI, SISTEM_YONETICISI`.

`vardis_demo` boş açıldı ve göç zinciri baştan sona **hatasız** koştu
(19 göç, `alembic current` = f4a8c1e60d92). Zincirde veri varsayan adım yok;
veri taşıyan üç göç boş veritabanında sıfır satır raporladı.

`vardiya` ile `vardis_demo` şemaları `pg_dump --schema-only` düzeyinde
**birebir aynı** (yalnız pg_dump'ın rastgele `\restrict` jetonu farklı).

**Kayıttaki şema bayat.** `docs/VERITABANI_SEMASI.md` göç başı a4d92c15e807'yi
anlatıyor; canlı şemayla farkları raporda listelendi (vardiya_tipi tablosu
düştü, atama/talep/tercih/kapsama_acigi/fazla_kadro saatlik modele geçti,
rol ve tercihtipi enum'ları değişti, sekiz yeni sütun eklendi).

### 2. Kural kataloğu tek tanıma indi

Katalog iki yerde yazılıydı: `demo_veri_uret.py::_KURAL_TANIMLARI` (20 kural)
ve göç e7b2c4915d80 (H9, H10, S1f). Boş bir veritabanında göç zinciri
koşturulduğunda katalog **üç satırdan** ibaret kalıyordu; üreteç sonradan
koşturulsa `kimlik` tekilliğine çarpacaktı. Demo Senaryosu 4.6'nın işaret
ettiği ayrışmanın mekanizması tam olarak bu.

Tanım `app/services/kural_katalogu_tohumu.py`'ye taşındı; kurulum kimlik
üzerinden **upsert** (silip yazmıyor — kullanıcının ekrandan değiştirdiği
ağırlığı sessizce geri almamak için). Üreteç bu modülü çağırıyor.

Doğru katalog üretimdekidir: SRS 4.4'ün amaç fonksiyonu sembol listesi
(w1, w1f, w2…w8, w6b) yirmi kimliğin tamamını kapsıyor. `vardis_demo` ve
`vardiya` katalogları artık satır satır aynı (20/20, S6b pasif, S1f aktif).

Kabul ölçümü kendi zorunlu-kural parametre kopyasını tutmayı sürdürüyor;
o akış ayrı veritabanında ve bu turun kapsamı dışında — **açık madde**.

### 3. Demo veri üreteci senaryoya göre yeniden yazıldı

`scripts/demo_veri_uret.py` artık DEMO_SENARYOSU bölüm 3–5 ve 7'yi uyguluyor:
40 personel (9 şef + 31 güvenlik), sürekli sicil (`D-1001` … `D-1040`),
37 kişi 45 / 3 kişi 30 saat haftalık hedef, iki bina kaydı, on beş haftalık
dönem zinciri, dönem başına kadronun %8–12'si izinli (iki geçmiş dönemde
dörtte bire çıkan dalga), üç durumu da kapsayan 25 tercih.

`ornek_senaryo.PERSONEL_GRUPLARI` 30'dan 40'a çıkarıldı. Bu sayı kabul
ölçümündeki `_REFERANS_GRUPLARI` ile **ayrışmıştı** — "referans kadro kaç
kişidir" sorusu iki yerde iki farklı sayıyla yazılıydı. Sabit yalnızca demo
üreteci tarafından okunuyordu, dolayısıyla değişiklik başka hiçbir tüketiciyi
etkilemedi; kabul ölçümü kendi kopyasını tutmaya devam ediyor (**açık madde**).

Rastgelelik tek bir tohumlu üreteçten (`random.Random(_SABIT_TOHUM)`)
akıyor; `random` modülünün genel durumu kullanılmıyor — genel durum, içeri
aktarılan herhangi bir modülün çağrısıyla ilerleyebilir ve betiğin çıktısı
sessizce değişirdi.

**Üç sınır durumu ayrı kişilere düşürüldü** ve bu bir teste bağlandı: yeni
başlayan (`D-1040`), ayrılan (`D-1039`) ve üç kısmi zamanlı. Aynı kişiye
düşselerdi iki mekanizma tek kayıtta gizlenir ve biri bozulduğunda diğeri
bunu örtbas ederdi.

Hesaplar artık üreteçte açılıyor (üç yönetim + iki çalışan); parola
`DEMO_PAROLA`'dan okunuyor, koda ve depoya yazılmıyor. Kurulum **idempotent**:
`--reset` personele bağlı hesapları düşürür ama yönetim hesaplarını bırakır,
ikisi tek yoldan geçmezse ikinci koşum `kullanici_adi` tekilliğine çarpardı.

**Sapma (küçük):** DEMO_SENARYOSU 4.5 resmî tatillerin "betikte sabit liste"
tutulmasını yazıyor. Kaynak kütüphane olarak (`tatil_takvimi.py`) bırakıldı;
sabit liste dinî bayramları yanlış yazar (tarihleri yıla göre kayar) ve demo
bir sonraki yıla girdiğinde sessizce eksik takvim üretirdi. Senaryonun asıl
istediği — "yalnız pencereye düşenler yazılır" — uygulandı: önceki sürüm iki
tam yılı yazıyordu.

### 5. Kurum adı ve gerçek ad taraması

Düzeltilenler (kod/paket/tohum): `backend/pyproject.toml` paket açıklaması,
`frontend/src/components/KunyeIcerigi.tsx` kapsam satırı, ve gerçek bir kişi
adını örnek girdi olarak kullanan `tests/test_hesap_kurulumu.py:57`.

`docs/` altındaki ve git geçmişindeki isabetler **yalnızca raporlandı**;
ikisini de değiştirmek bir sızıntıyı kapatmak değil bir kaydı tahrif etmek
olurdu.

### 6. Demo kipi ve gecelik sıfırlama

`DEMO_KIPI` ayarı ve yetki istemeyen `GET /api/ortam` uç noktası. Uç nokta
bilerek yetkisiz: şerit **giriş ekranında** görünmeli, çünkü gösterim
ortamına ilk bakan kişi henüz giriş yapmamıştır. Şerit kökte tek yerde
çiziliyor — her ekrana ayrı eklenseydi bir sonraki ekran onu unuturdu.

Ayar `veri_temizligine_izin`in türevi **değil**: ikisi tek ayara bağlansaydı,
gecelik sıfırlamanın kilidi açtığı birkaç saniye boyunca şerit yanıp söner,
kilidi elle açan bir geliştirme makinesi de kendini gösterim ortamı ilan
ederdi.

`DEMO_PAROLA` ayrıca `Ayarlar`'da tanımlandı: uygulama onu hiç okumaz ama
pydantic-settings `extra='forbid'` ile çalışıyor ve tanımlanmadan `.env`'e
yazılan bir satır **bütün arka ucu açılmaz hale getiriyordu** (denendi,
`ValidationError` ile doğrulandı).

`deploy/vardis-demo-sifirlama.{service,timer}`: 03.00'te yeniden üretim.
Kilit birimin **içinde** açılıyor, `.env`'de değil; dosyaya yazılsaydı API
sürecinin ve elle koşturulan her betiğin de yıkıcı işlem izni olurdu.
Çözüm işçisi üretim boyunca durduruluyor (aynı kuyruğu iki süreç yoklamasın)
ve üretimden sonra ölçüt raporu günlüğe yazılıyor.

### DOKÜMAN BORCU — Tur 14

1. **SRS 5.x (yeni bir FR)** — `DEMO_KIPI` ve gösterim şeridi: ortamın
   kendisini beyan etmesi bir gereksinimdir, yapılandırma ayrıntısı değil.
   Şeridin kapatılamaz olduğu ve giriş ekranında da göründüğü yazılmalı.
2. **SDD 3.4 / Ek B** — `GET /api/ortam` uç noktası (yetki istemez) ve
   `deploy/vardis-demo-sifirlama.{service,timer}` dağıtım görünümüne.
   Kilidin birim içinde açılması ve çözüm işçisinin durdurulması tasarım
   kararıdır.
3. **SDD 4.2.x** — kural kataloğunun tek tohum tanımı
   (`app/services/kural_katalogu_tohumu.py`) ve kurulumun kimlik üzerinden
   upsert olması; göçlerin kataloğun bir bölümünü yazması bu yüzden artık
   çakışma üretmiyor.
4. **SRS 3.3.6 / SDD 3.4.2** — demo referans kadrosunun 40'a çıkması ve
   kabul ölçümünün kendi kopyasını tutmaya devam etmesi. İki kaynak
   birleştirilene kadar bu bir bilinen ayrışmadır.
5. **VERITABANI_SEMASI.md bayat** — göç başı a4d92c15e807'yi anlatıyor,
   canlı şema f4a8c1e60d92. Doküman yeniden üretilmeli (türetilmiş doküman).
6. **DEMO_SENARYOSU 4.5** — resmî tatil kaynağı "betikte sabit liste" yerine
   kütüphane olarak yazılmalı; pencere filtresi korunuyor.

### 4. Dönemler gerçek çözücüyle üretildi

15 dönem, 60 saniyelik limitle, `vardis_demo` üzerinde. Üretim ~22 dakika.

| Dönem | Durum | Atama | Açık |
| --- | --- | --- | --- |
| D-12 … D-1 (12 hafta) | yayınlandı | 159–195 | 0 |
| D0 (2026-08-24) | yayınlandı | 182 | 0 |
| D+1 sürüm 1 | çözüldü | 184 | 0 |
| D+1 sürüm 2 | taslak | 184 (3'ü elle taşınmış) | — |
| D+2 (sıkışık) | çözüldü/uyarılı | 154 | **9 kişi-saat** |

**İlk koşum D+1'de çöktü.** `SurumServisi.taslak_olarak_kopyala` yalnızca
YAYINLANMIŞ ya da ARŞİV sürümü kopyalar (SDD 6.3.5); D+1'in birinci sürümü
`cozuldu` durumunda ve senaryo onu taslak istiyor. Zincir artık
`taslak_turet` ile kuruluyor, atamalar `_ikinci_surumu_kur` içinde
kopyalanıyor. Kopyalanan blokların kaynağı ÇÖZÜCÜ kalıyor; MANUEL olan
yalnızca elle taşınan üçü — hepsini manuel saymak, sürüm karşılaştırmasında
elle değişen üç bloğu geri kalan 181'in içinde kaybederdi.

Elle değişiklik **silme değil taşımadır**: alıcı, o gün ve komşu günlerde
hiç ataması olmayan, noktanın ön koşulunu taşıyan biri seçiliyor; böylece
H1, H2 ve H8 elle değişiklikle kırılmıyor ve kapsama değişmiyor.

#### Kabul ölçütleri (DEMO_SENARYOSU bölüm 9) — `scripts/demo_kabul_olcutleri.py`

| # | Ölçüt | Sonuç |
| --- | --- | --- |
| 9.1 | Yayınlanmış dönemlerde sıfır zorunlu ihlal | **GEÇTİ** — 0 ihlal / 13 sürüm |
| 9.2 | 90 günlük ufuk boş değil ve dönemden farklı | **GEÇTİ** — dönem hedefi 29,5 sa; adalet ufku 506,3 sa |
| 9.3 | Kota kartında en az bir kişi kotanın yarısı üstünde | **GEÇTİ** — 2 kişi (265 ve 240 sa; eşik 135) |
| 9.4 | Temelde açık yok, D+2'de var | **GEÇTİ** — temel 0, sıkışık 9 kişi-saat |
| 9.5 | İki koşumda tanım+girdi birebir aynı | **GEÇTİ** — ayrı bir kontrol veritabanında iki koşum, aynı SHA-256 (`7be63a8f…`), `vardis_demo` ile de aynı |
| 9.6 | Hiçbir metin alanında kurum/gerçek kişi adı yok | **GEÇTİ** — 0 isabet / 16 metin sütunu |

Doğrulayıcı yayınlanmış 13 sürümün hepsinde sıfır ihlal verdi. Ölçüm
`DogrulamaServisi` üzerinden YAPILAMAZ (o servis yayınlanmış sürümü
düzenlenebilir bulmadığı için reddeder, FR-6.9); kural motoru doğrudan
çağrılıyor.

#### Bölüm 8 — ekran başına hedeflenen görüntü

Gece yarısını aşan blok 923, kilitli atama 2 (D0 ve D+1 sürüm 2), elle
taşınmış atama 3. Tercih durumları: 11 beklemede, 7 onaylandı, 7 reddedildi.
Müsaitlik tipleri dördü de dolu (30/22/19/11), dilim 72 tam gün + 10 yarım
gün. Bölüm 8'deki on satırın hepsi karşılanıyor.

### Tur kapanış sınaması

Hafif arka uç takımı **335 geçti, 1 atlandı** — normal ve ters dosya
sırasında aynı sonuç. Ağır OR-Tools takımı ayrıca koştu: **137 geçti**
(9 dk 59 sn). Ön yüz 379 test / 37 dosya. `ruff check` ve `ruff format
--check` temiz (146 dosya), `tsc -b` temiz, `oxlint` 4 önceden var olan
uyarı (fast-refresh).

Atlanan tek test `test_ardisik_donem_adaleti`: test veritabanında üç ardışık
yayınlanmış dönem yok ve test bunu açıkça atlıyor — demo verisi ayrı
veritabanında üretildiği için beklenen durum.

**Uç nokta denetimi bir eksik buldu ve bu bir doküman borcu:**
`GET /api/ortam` uygulamada var, Ek B'de yok (uygulama 75, Ek B 74).

### Ağırlık kalibrasyonu testi neden değişti

Üreteç beş haftalık takvimden on beş döneme geçince testin okuduğu iki
dönem indisi (`_DAR_HAFTA_INDISI`, `_RAHAT_HAFTA_INDISI`, `_HAFTA_SAYISI`)
karşılıksız kaldı. Yerlerini `_RAHAT_DONEM_INDISI`, `_SIKISIK_DONEM_INDISI`
ve `_TOPLAM_DONEM_SAYISI` aldı; indisler hâlâ üreteçte duruyor, test onları
yeniden saymıyor. **İddia değişmedi:** w1, her iki dönemde de S1-hariç
ağırlıklı toplamdan büyük olmalı.

### Yetkilendirme koruması bir kaçak yakaladı

`test_yetkilendirme` bütün yolları sayıp oturumsuz cevap veren her uç
noktada düşüyor ve `/api/ortam`'ı yakaladı. Uç nokta muafiyet listesine
**gerekçesiyle** eklendi: şerit giriş ekranında çizilmek zorunda ve yanıt
tek bir yapılandırma bayrağından ibaret. Açık uç nokta testi artık yanıtın
tam olarak tek alan taşıdığını da doğruluyor.

---

## Tur 14 — ek işler: yayına hazırlık

### 5. Yayına hazırlık taraması

Arama kümesi: kurum adı/kısaltması/unvanı · sunucu IP · kapı · alan adı ·
systemd servis adları · SSH anahtar yolları · dağıtım yönergesi içeriği ·
`.env` içerikleri, parolalar, oturum/bağlantı anahtarları · gerçek kişi adları.

**`vardis_demo` temiz:** 16 metin sütunu, genişletilmiş desen kümesiyle
**0 isabet**.

**Depoda gerçek sır yok.** İzli hiçbir dosyada gömülü parola veya anahtar
bulunmadı; `PAROLA=` eşleşmelerinin tamamı test fikstürü ya da değişken
ataması. `.env` ve `backend/.env` `.gitignore` tarafından kapsanıyor,
izlenen tek `.env*` dosyası `.env.example` ve o da yalnızca yer tutucu
(`<PAROLA>`) taşıyor.

`.gitignore` doğrulandı ve genişletildi: `.env`/`.env.*` (+ `!.env.example`)
zaten vardı; **`docs/old/`, `DAGITIM*.md`, `deploy/DAGITIM.md`, `*.pem`,
`*.key`, `id_rsa*`, `id_ed25519*` ve `.yasakli-metinler` eklendi.**

**Tarama betiğinin kendisi bir isabetti.** `demo_kabul_olcutleri.py` aradığı
kurum ve kişi adlarını sabit olarak taşıyordu — depo herkese açıldığında
redaksiyon güvencesi tam da bastırmak istediği adları yayımlamış olurdu.
Yapısal desenler (adres biçimi, anahtar yolu, kurulum yolu) kodda kaldı;
kimlik desenleri izlenmeyen `.yasakli-metinler` dosyasına taşındı. **Dosya
yoksa ölçüt "geçti" demiyor, "ölçülemedi" diyor** — boş desen kümesiyle
hiçbir şey bulunmaz ve ölçüt hiçbir şeyi ayırt etmeden ölçülmüş görünürdü.

### 5c. Kurulum bilgisinin genelleştirilmesi

`deploy/DAGITIM.md` depodan çıkarıldı → `docs/old/2026-08-28-DAGITIM.md`
(izlenmez). Dosya sunucu IP'sini, barındırıcıyı, alan adını, `root@` SSH
komutlarını ve `$HOME/.ssh/vera_hetzner` anahtar yolunu taşıyordu.

Yerine README'ye **Deployment** bölümü yazıldı: `<SERVICE_USER>`,
`<INSTALL_DIR>` yer tutucuları, systemd birimlerinin kurulumu, ters vekil
sunucu ve TLS notu, demo ortamı alt bölümü. README'de IP, alan adı, kişi
adı, anahtar yolu **yok**; adres olarak yalnızca `localhost` geçiyor.

Yönergeye atıf yapan altı dosya README'ye yönlendirildi. Servis birimlerinin
`Documentation=` satırları kurulum dizinindeki README'yi gösteriyor — önce
GitHub URL'i yazmıştım, o da kişinin kullanıcı adını taşıyordu.

**README'nin demo veri bölümü bayattı** (5 dönem, 30 kişi, sabit vardiya
tipi); üreteç yeniden yazıldığından beri yanlıştı, yeni yapıya göre
düzeltildi.

Künyeden geliştirici adı kaldırıldı; rol ve kapsam satırları kaldı.

### 5b. Git geçmişi taraması — düzeltme YAPILMADI

Ayrı başlık altında raporlandı. Geçmiş yeniden yazılmadı, commit
değiştirilmedi, dosya silinmedi.

**Geçmişte gerçek kimlik bilgisi YOK.** Bağlantı dizelerindeki üç farklı
parola değeri incelendi: biri `config.py`'nin varsayılanı (`vardiya`),
ikisi yer tutucu (`PAROLA`, `GIZLI`). `password/secret/api_key` deseni
geçmişin tamamında **sıfır** isabet verdi.

Kapatılması gereken beş şey var ve hepsi kullanıcının işi: sunucu IP'si
(9 commit), alan adı (15 commit), SSH anahtar yolu ve `root@` erişimi
(9 commit, tek dosya), kurum adı (19 commit, eski doküman dosya adları
dahil), gerçek kişi adı (48 commit + 248 commit'in yazar üstverisi).

### Kapsam notları

README'ye başlığın hemen altına Türkçe kapsam notu ve depo public olacağı
için aynısının İngilizcesi; dört kanonik dokümanın her birine revizyon
tablosunun hemen üstüne kısa hâli eklendi (kullanıcının verdiği metinler,
birebir).

**Bu, kurum adını README'ye geri koyuyor** — ama muafiyet beyanı bağlamında
ve kasıtlı: bir okur, adı hiç görmediği bir depoda kadro sayılarını
işletmeye ait bir kayıt sanabilir. Notun işi tam olarak bunu kapatmak.

**Sürümler bump edildi** (kullanıcının verdiği numaralarla): Charter **1.7**,
SRS **1.28**, SDD **1.37**, Backlog **1.27**. Dördüne de 28.08.2026 tarihli
birer revizyon satırı eklendi.

Backlog için verilen numara **1.23'tü ve yanlıştı** — belge 1.22'de değil
**1.26'daydı**; hatanın kaynağı önceki oturumun rapor satırıdır, Backlog'un
sürümü hiç doğrulanmadan yazılmıştı. Sürümü düşüren bir revizyon satırı,
belgeyi yerine geçtiği kopyadan eski gösterirdi; 1.27 yazıldı.

### 7. K3'ün yeniden ölçülmesi

**Yeni ölçüm ALINMADI; var olan 300 sn'lik oturum kullanıldı** ve bu bilinçli.
`olcum/kabul-20260826-300sn.json` zaten turun istediği ölçümün ta kendisi:
tek oturum, 300 saniyelik limit, K3'ün güncel (dağılım) tanımı, referans
donanım (4 çekirdek, 3 arama işçisi), commit `f5c75cd`.

Yerelde yeniden almak ölçümü **iyileştirmez, bozar**: bu makine 10 çekirdekli
ve README ölçüm ortamı olarak referans donanımı "bağlayıcı ortam" ilan ediyor;
K1 donanıma duyarlı bir süre ölçüsü. "Demo server" sütununa geliştirme
makinesinin sayısını yazmak yanlış beyan olurdu.

Ölçümden bu yana ölçüm yolunun değişmediği doğrulandı: `f5c75cd..HEAD`
aralığında `app/kurallar/`, `app/cozucu/`, `baglam_kurucu.py`,
`dogrulama_servisi.py`, `gecmis_sayaclar.py`, `app/models/` ve
`kabul_olcumu.py` **hiç değişmedi**. Tek değişen `ornek_senaryo.py`'deki
`PERSONEL_GRUPLARI` ve kabul ölçümü o sembolü okumuyor (kendi
`_REFERANS_GRUPLARI`'nı kuruyor).

**K3 hâlâ geçmiyor ve öyle yazıldı:** 9/40 kişi (%22,5), eşik 4 kişi (%10).
60 sn'de 24/40 (%60) idi; azami sapma (teşhis) 62,1 → 24,0 gece saati.
Erişilebilirlik teşhisi hedefin ulaşılabilir olduğunu doğruluyor (40 kişinin
tamamı gece talebi olan noktada çalışabiliyor; adil pay bandı 33,0–64,1,
gözlenen 33–68). Engel arama süresi.

Tablodaki altı satırın tamamı **tek oturumdan**; tanım, limit, tarih, commit
ve ham çıktı yolu tablonun altında yazılı.

### 8. README bütünlük kontrolü

README'nin bağlantı verdiği 10 yerel hedef denetlendi. **Beşi kırıktı; ikisi
düzeltildi, üçü raporda listeli.**

Beşinin tamamı **commit `15e2c87`** ile silinmiş (28.08.2026, kullanıcının
kendi commit'i, "refactor: reorganize project documentation…"). Önceki turda
"çalışma ağacında silinmiş, kasıtlı mı bilmiyorum" diye bildirdiğim dosyalar
bunlar; kullanıcı o commit'le kararını vermiş ve itmiş.

| Hedef | Durum |
| --- | --- |
| `PROGRESS.md` (2 yerde) | **düzeltildi** — metin git geçmişine yönlendiriyor |
| `docs/turlar/UYGULAMA_PLANI.md` | **düzeltildi** — V2 zaten var, ölü bağlantı kaldırıldı |
| `docs/gorseller/gun-izgarasi.png` | **kırık** — görsel yeniden üretilmeli |
| `docs/gorseller/cozum-ekrani.png` | **kırık** |
| `docs/gorseller/analiz-ekrani.png` | **kırık** |

Ekran görüntüsü bağlantıları **bilerek bırakıldı**: doğru düzeltme bölümü
silmek değil görselleri yeniden üretmek ve bu bir çerçeveleme kararı.

**PostgreSQL sürümü üç yerde üç farklı:** `VERSIONS.md` **16** sabitliyor,
geliştirme makinesi **17.10**, referans donanım **18.6**
(`olcum/OLCUM_ORTAMI.md`). `VERSIONS.md`'nin var olma nedeni tam olarak bu iki
ortamı eşlemek (SDD 3.4.1) ve eşleme tutmuyor. Sabit değiştirilmedi — bu bir
ürün kararı; README artık 16'yı taban olarak yazıyor ve uyuşmazlığı söylüyor.

---

## Tur 15 — Yayın turu: demo giriş, ekran görüntüleri, son kontrol

Dokümanlar: Charter 1.8 · SRS 1.29 · SDD 1.38 · Backlog 1.28 ·
DEMO_SENARYOSU 1.0 — beşi de tur başında doğrulandı.

### 1. Demo kimlik bilgisi giriş ekranında

`GET /api/demo/kimlik`: demo hesaplarının kullanıcı adlarını ve ortak
parolayı döner. **Yalnız demo kipinde vardır**; kapalıyken 404 — 403 değil,
çünkü 403 var olan ama erişilemeyen bir kaynağı işaret eder ve gerçek bir
kurulumda "demo kimlik bilgisi bir yerlerde duruyor" izlenimi verirdi.

Kapalı durum iki testle kilitlendi: durum kodu ve **yanıt gövdesinde hiçbir
kullanıcı adının geçmemesi**. Parola koda ve pakete gömülü değil; uç nokta
`ayarlar.demo_parola`yı istek anında okuyor ve bunun gözlenebilir karşılığı
ayrı bir testte: ayar değişince yanıt da değişiyor.

**Sistem yöneticisi hesabı açılır ama GÖSTERİLMEZ.** Gösterim ortamı herkese
açık; en geniş yetkiyi giriş ekranına yazmak, demoyu gezen herkese hesap
yönetimi hakkı vermek olurdu. Ekranda üç rol var: idare, hesap yöneticisi,
çalışan (ikisi).

Hesap listesi `app/services/demo_hesaplari.py`'ye taşındı — hesapları AÇAN
üreteç ile GÖSTEREN uç nokta aynı tanımı okusun; iki yerde yazılsaydı
ekranın gösterdiği kullanıcı adı çalışmayabilirdi.

Yetkilendirme koruması uç noktayı yakaladı ve muafiyet listesine gerekçesiyle
eklendi. Muafiyet listesindeki diğerlerinden farkı: açık olduğu için değil,
**gerçek bir kurulumda hiç bulunmadığı** için listede.

### 2. Şerit metni

Üç şeyi söylüyor: veri gösterim amaçlı üretilmiştir, her gece sıfırlanır,
sistem herhangi bir kurumda kullanımda değildir. `Kok.test.tsx` şeridin hem
yönetici arayüzünde hem çalışan panelinde çizildiğini, kapalı kipte hiçbir
yüzeyde çizilmediğini doğruluyor.

### 3. Ekran görüntüleri

**`.env` geçici olarak `vardis_demo`ya çevrildi ve YEDEKTEN GERİ YÜKLENDİ**;
SHA-256 karşılaştırmasıyla birebir aynı olduğu doğrulandı
(`70ccc9b7343295b9…`). Depo kökünde geçici bir `.env` sembolik bağı
kurulmuştu (uvicorn kökten koştuğu için `.env`i orada arıyor) ve o da
silindi.

Beş görüntü headless Chrome + CDP ile alındı (1440×900, 2× ölçek). Uygulamada
URL tabanlı yönlendirme olmadığı için derin bağlantı kurulamıyor; oturum
`fetch` ile açılıp ekranlara tıklanarak gidildi.

Hangi ekranın hangi dönemden alındığı bir karar: **gün ızgarası sıkışık
dönemden** (kapsama şeridi ve açık rozetleri orada görünür), **hafta şeridi ve
analiz yayınlanmış dönemden** (sıkışık dönemde şef havuzunun tamamı izinli
olduğu için adalet tablosu dejenere, herkes 0 saat). **Çözüm ekranı ön
kontrol çıktısını gösteriyor**: açılışta boş (iş kartı yalnız yürüyen ya da o
oturumda sonuçlanan iş için çizilir) ve çözüm başlatmak demo veritabanına
yeni bir sürüm yazardı; ön kontrol salt okunur ve sıkışık dönemde gerçek
bulgu üretiyor (78 kişi-saatlik yapısal engel + kota uyarısı).

Beşinde de şerit görünüyor, hiçbirinde kimlik kutusu yok (kutu yalnız giriş
ekranında ve giriş ekranı çekilmedi).

### 4. Künye ve redaksiyon kümesi

Geliştirici adı künyeye geri kondu: kendi adı **atıftır**, redaksiyon hedefi
değil — bir önceki turda kurum adıyla birlikte silinmişti, oysa biri ilişki
iddiası diğeri eser sahipliği. `.yasakli-metinler`den kişi adı çıkarıldı;
kümede yalnız kurum adı, kısaltması ve barındırıcı kaldı.

### 5. Son yayın kontrolü

**Kırık bağlantı: 0** (10 yerel hedef). **`vardis_demo`: 0 isabet** (16 metin
sütunu, 4 yapısal + 6 kimlik deseni). **Gömülü sır: yok.** `.gitignore`
`.env`, `docs/old/`, `deploy/DAGITIM.md`, `.yasakli-metinler`, `*.pem`,
`*.key`, `id_rsa*`, `id_ed25519*` ve `ornek-ciktilar/` için doğrulandı.

`VERSIONS.md` PostgreSQL sabiti **16 → 18**; README ile hizalandı. Eşleme
hâlâ tam değil (geliştirme makinesi 17.x) ve bu açıkça yazıldı.

### DOKÜMAN BORCU — Tur 15

1. **SRS 5.x** — demo kimlik bilgisi uç noktası bir gereksinimdir: yalnız
   demo kipinde var olur, kapalıyken 404 döner, sistem yöneticisi hesabı
   listelenmez.
2. **SDD Ek B** — `GET /api/demo/kimlik` (yetki istemez, koşullu 404).
   Uç nokta denetimi bunu şu an eksik raporluyor.
3. **SDD 6.3.6** — giriş ekranındaki kimlik kutusu ve tek tıkla doldurma.
4. **SRS/SDD** — şerit metninin üçüncü cümlesi ("herhangi bir kurumda
   kullanımda değildir") bir beyandır, üslup değil.

### Sunucu yapılandırmasında bir kusur bulundu ve düzeltildi

Talep "`.env.demo` içinde `DEMO_KIPI=true` olduğunu doğrula" diyordu; **o
yerleştirme çalışmaz.** `vardiya-api.service` yalnızca `/opt/vardiya/.env`
okuyor, `.env.demo`yu yalnız gecelik sıfırlama birimi okuyordu. Şerit
(`DEMO_KIPI`) ve giriş ekranındaki kimlik kutusu (`DEMO_PAROLA`) API
sürecinden besleniyor — ikisi de `.env.demo`da kalsaydı sunucuda **sessizce
kapalı** kalırdı: hata yok, sadece iki ekran onlarsız açılır.

Kusurun kaynağı bu turda eklenen uç nokta: `DEMO_PAROLA` tasarlanırken
"API'nin onu görmesi için bir neden yok" diye yazılmıştı ve `/api/demo/kimlik`
o gerekçeyi geçersiz kıldı. Parola korunacak bir sır değil (giriş ekranında
zaten yazılı); gizli tutulmasının tek nedeni depoya ve sürüm geçmişine
girmemesi.

Düzeltme: ikisi de `/opt/vardiya/.env` içinde (0600), ikinci ortam dosyası
kaldırıldı, aksini söyleyen üç yorum (`config.py`, `.env.example`, birim
başlığı) düzeltildi.

### Giriş ekranı doğrulaması (tarayıcıda)

`DEMO_KIPI` **açık**: kutu giriş formunun altında, üç rol başlığı (İdare,
Hesap yöneticisi, Çalışan) ve dört hesap; sistem yöneticisi listede yok.
`demo_idare` satırına tıklamak kullanıcı adını ve 23 karakterlik parolayı
forma doldurdu, Giriş düğmesi etkinleşti.

`DEMO_KIPI` **kapalı**: `/api/demo/kimlik` **404**, gövdede hiçbir kullanıcı
adı yok; sayfa metninde ne şerit ne kutu var.

`.env` yalnız ekran doğrulaması için kökte geçici bir dosyayla ezildi
(`backend/.env`'e **dokunulmadı**, SHA-256 tur boyunca sabit:
`70ccc9b7343295b9…`); dosya silindi.

### Sunucu adımı BENDE DEĞİL

`.yasakli-metinler`i sunucuya koymak ve `.env`i düzenlemek dağıtım
işlemleridir; bu oturumun sunucuya erişimi yok ve dağıtım kullanıcının
kararıdır (CLAUDE.md: push ve remote asla). Komutlar rapora yazıldı.

### Demo girişi üç ayrı kusurla düşüyordu

**1 — Hiç hesap açılmamıştı.** Sunucuda veri üretimi `DEMO_PAROLA` boşken
koştu; üreteçte `if parola` koruması var, dolayısıyla `_hesaplari_kur` hiç
çağrılmadı. Giriş ekranındaki kutu ise **statik listeden** çiziliyor —
var olmayan dört hesabı gösterdi ve hepsi "kullanıcı adı veya parola hatalı"
verdi. Kutu var olan bir şeyi değil, olması gerekeni gösteriyordu.

Bu hâl artık sessiz değil: tohumsuz koşum stderr'e kutunun **çalışmayan
hesaplar göstereceğini** yazıyor ve ne yapılacağını söylüyor.

**2 — Parolalar hesap başına ayrıldı.** Dördü aynı dizeydi; "parolayı
biliyorum" ile "hepsini biliyorum" aynı şeye çıkıyordu. Her hesabın parolası
artık on iki karakter ve tek bir tohumdan HMAC ile türetiliyor
(`demo_hesaplari.parola_uret`). Hiçbiri saklanmıyor: hesabı açan üreteç ile
onu ekranda gösteren uç nokta aynı türetmeyi yapıyor. İki yerde saklanan bir
parola, iki yerin ayrışabileceği anlamına gelirdi.

`DEMO_PAROLA` → **`DEMO_PAROLA_TOHUMU`**. Ad değişti çünkü değerin anlamı
değişti; eskisini `.env`'de bırakmak `extra='forbid'` yüzünden arka ucu
açılmaz hâle getirir.

**3 — `--yalniz-hesaplar` kipi.** Tohum değiştiğinde ya da hesaplar eksik
açıldığında değişmesi gereken tek şey parola özetleri; on beş dönemi yeniden
çözmek yarım saati yanlış işe harcamak olurdu. Veri temizliği kilidi
istemiyor — hiçbir şey silmiyor.

Doğrulama: beş hesap da kendi parolasıyla **200**, çapraz parola **401**,
yanlış parola **401**; uç noktanın döndürdüğü dizeler veritabanındakiyle
tutuyor; tarayıcıda tek tıkla doldurup giriş yapıldı (`demo_d1010` → çalışan
paneli).

### Giriş ekranı: kayma ve beyaz şeritler

İki ayrı neden vardı. **Kök artık dikey akış** (`#root` flex sütun): gösterim
şeridi eklendiğinde sayfa "şerit + 100svh" yüksekliğine çıkıyordu, çünkü
altındaki ekran ayrıca tam bir görüntü yüksekliği istiyordu. Giriş ekranı
`min-h-svh` yerine `flex-1` ile **kalanı** dolduruyor. **`overscroll-behavior:
none`**: macOS lastik taşması sayfanın uçlarında gövde rengini (açık) koyu
yüzeyin üstünde ve altında şerit olarak gösteriyordu.

Kimlik kutusu da sıkıştırıldı: rol başlıkları ayrı satır yerine satır sonunda
etiket, hesap başına tek satır. 1280×800'de sayfa **hiç kaymıyor**
(687 → 800); 1280×560 gibi kısa bir pencerede kayıyor ama kaydırıldığında
beyazlık yok, şerit tepede sabit kalıyor.

Ölçüm headless Chrome ile alındı; tarayıcı panelinin ekran görüntüsü
yanıltıcıydı (JS `getBoundingClientRect` şeridi `top: 0`'da gösterirken panel
üstte açık bir şerit çiziyordu).

### Yan menüdeki planlama dönemi bloğu kaldırıldı

Blok, sıradan bir dizüstü ekranında oturum bloğunu ekranın altından taşırıyordu
ve gösterdiği tarihi ekranın kendi başlığı zaten yazıyordu. Onunla birlikte
taşıyıcıları da gitti: her ekranın geçirdiği `donemId` prop'u, `donemiBul`
yardımcısı ve **her yönetici sayfasında kimsenin okumadığı bir blok için
atılan `/api/donem` isteği**.

### Kabukların taşması — giriş ekranıyla aynı kusur

`AppShell` `h-svh`, `CalisanShell` ve parola ekranı `min-h-svh` istiyordu;
gösterim şeridi üstlerinde durduğu için toplam **tam bir şerit boyu**
taşıyordu (ölçüldü: 857 = 800 + 57). Yan menünün altı ekranın dışında
kalıyordu.

Kök artık **tam bir görüntü yüksekliği ve kaydırılan yüzeyin kendisi**
(`height: 100svh; overflow: auto`); kabuklar `flex-1` ile kalanı dolduruyor.
`min-height` yeterli değildi: kök yalnızca asgari yükseklik verseydi kabuk
içeriği kadar uzar, kaydırma iç alandan sayfaya taşar ve yan menü ile üst
çubuk yerinde durmazdı.

Ölçüm (1280×800): yönetici 800/800, çalışan 800/800, giriş 800/800 — hiçbiri
kaymıyor. Kısa pencerede (1280×560) giriş ekranı kökün içinde kayıyor, şerit
`top: 0`'da sabit kalıyor ve beyazlık yok.

### Not: göreli tarihler kaydı

Yerel demo verisi 27.08.2026'da üretilmişti; bugün 31.08.2026 ve **D0 artık
D+1'in yerinde**. Çalışan paneli "bu dönem için henüz yayınlanmış bir çizelge
yok" diyor, çünkü içinde bulunulan hafta artık taslak olan dönem. Kusur değil,
göreli tarihlerin beklenen davranışı; gecelik yeniden üretim takvimi her gece
bugüne yeniden çapalıyor (Demo Senaryosu 2.3, 10).
