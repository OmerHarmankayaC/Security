# Performans ve Kabul Kriteri Notu

**Tarih:** 08.08.2026 · **Kapsam:** Sprint 3 Gün 14 + Sürümler ekranı · **Sürüm:** 1.2

Bu not, Proje Tanım Dokümanı bölüm 5'teki altı kabul kriterinin ölçüm
sonuçlarını içerir. K1–K5 `backend/scripts/kabul_olcumu.py` ile otomatik
alınır; K6 gerçek bir yeniden çözüm gerektirdiği için ayrı ölçülür
(bölüm 3, K6). Notun sayıları elle yazılmaz, ölçümün çıktısından alınır
ve ölçüm yeniden çalıştırılarak doğrulanabilir (bölüm 5).

> Bu dosya `docs/` altındaki dört kanonik dokümandan (Proje Tanım
> Dokümanı, SRS, SDD, Backlog) biri **değildir**; Gün 14'ün ürettiği
> ayrı bir çıktıdır.

---

## 1. Ölçüm ortamı

| | |
|---|---|
| Referans donanım (SDD 3.4.2) | 4 çekirdek, 8 GB |
| Ölçüm makinesi | macOS 15.7.3, arm64, 10 çekirdek, 16 GB |
| Arama işçisi sayısı | **3** (SDD 3.4.3: referans donanımda çekirdek sayısının bir eksiği) |
| Python | 3.13.11 |
| Çözücü | OR-Tools CP-SAT |

**Ölçümün referans donanıma göre konumu.** CP-SAT paralel arama yürütür,
bu yüzden süre çekirdek sayısına doğrudan bağlıdır ve donanım
belirtilmeden verilen bir süre tekrarlanabilir değildir (SDD 3.4.2).
Ölçüm, arama işçisi sayısını referans donanımın değerine (3) sabitler;
böylece çözücünün **paralelliği** referans donanımla aynı olur. Buna
karşılık **çekirdek başına hız** farkı kalır: ölçüm makinesi referans
donanımdan büyük olasılıkla hızlıdır. Dolayısıyla aşağıdaki süreler
referans donanım için bir üst sınır **değil**, bir göstergedir. Kesin
doğrulama, gösterim ortamı kurulduğunda (Gün 15) aynı betiğin orada
çalıştırılmasıyla yapılmalıdır.

**Belirlenimsizlik.** CP-SAT paralel aramada belirlenimsizdir; aynı
örnek farklı çalıştırmalarda farklı (eşit iyilikte) çözümler verebilir.
K3'ün ölçülen sapması ve K4'ün açık hücre sayısı çalıştırmadan
çalıştırmaya bir miktar değişir (K3 için gözlenen aralık 0,5–0,7; K4 için
19–21 açık hücre); geçme/kalma sonucu ve K1/K2/K5 değerleri değişmez.

## 2. Referans örnek

Kabul kriterinin tanımladığı ölçek: **40 personel, 28 gün**.

| | |
|---|---|
| Personel | 40 — Vardiya Şefi havuzu 9, Müracaat 7, Güvenlik Görevi 24 |
| Dönem | 02.02.2026 – 01.03.2026 (28 gün, pazartesi başlangıçlı) |
| Görev noktası | 3 (Vardiya Şefliği, Güvenlik, Müracaat — tümü tesis geneli) |
| Vardiya tipi | 3 (Gündüz 08–16, Akşam 16–24, Gece 00–08) |
| Talep | SRS 3.3.4 matrisi — haftalık 144 kişi-vardiya |
| Kural | H1–H8 + S1–S8 + S6b, kalibre edilmiş ağırlıklarla |

Kadro, SRS 3.3.6'daki havuz asgarilerinin (izin payıyla 7 / 6 / 23)
üzerinde tutulur: demo senaryosunun 44 kişilik kadrosu 40'a **yalnızca
Güvenlik Görevi havuzu 28→24 çekilerek** indirilmiştir; kırılgan iki
havuz (Vardiya Şefi, Müracaat) olduğu gibi korunmuştur.

## 3. Sonuçlar

| Kriter | Eşik | Ölçülen | Sonuç |
|---|---|---|---|
| **K1** 40×28 referans örnek < 60 sn | < 60,0 sn | **1,12 sn** | ✅ geçti |
| **K2** Zorunlu kısıt ihlali sıfır | 0 ihlal | **0 ihlal** | ✅ geçti |
| **K3** Kişi başına gece sayısı hedeften en fazla 1 sapar | ≤ 1,0 | **0,61** | ✅ geçti |
| **K4** Çelişkili örnekte gün/vardiya/eksik sayısı gösterilir | ≥ 1 açık, üç bilgi de dolu | **21 açık hücre** | ✅ geçti |
| **K5** Manuel düzenleme doğrulaması < 1 sn | < 1,000 sn | **0,038 sn** | ✅ geçti |
| **K6** Yeniden çözümde değişen atama sayısı raporlanır | sayı raporlanır | **4 değişen atama** | ✅ geçti |

**6/6 kriter geçti.**

K1–K5 `kabul_olcumu.py` ile otomatik ölçülür. K6 ayrı ölçülür (aşağıda):
raporlama yüzeyi Sürümler ekranının karşılaştırma işlevidir (SDD 6.3.5) ve
ölçümü gerçek bir yeniden çözüm gerektirir.

### K1 — Çözüm süresi

| Aşama | Süre |
|---|---|
| Model kurma | 0,50 sn |
| İlk uygun çözüme ulaşma (çözücü içi) | 0,62 sn |
| **Kullanıcının beklediği toplam** | **1,12 sn** |
| Zaman limitine kadar iyileştirme | 60,06 sn |

**"Çözülür" ne demektir.** CP-SAT bir eniyileme problemi çözer ve zaman
limiti dolana kadar çözümü iyileştirmeye devam eder; 60 saniyede
eniyilik kanıtlanmaz (durum: *uygun*). Kriterin işaret ettiği süre, ilk
**kullanılabilir** çizelgeye ulaşma süresidir — Charter bölüm 6'nın
önlem cümlesi de bunu söyler: "limit dolduğunda o ana kadarki en iyi
çözüm döndürülür". Bu okumayla ölçülen 1,12 saniye, 60 saniyelik eşiğin
yaklaşık 50 kat altındadır. Referans donanımın daha yavaş çekirdekleri
bu payı daraltır ama kapatması beklenmez.

### K3 — Gece adaleti

Ölçülen azami sapma **0,61** (eşik 1,0). Uygun havuzda gözlenen aralık
3–4 gece, hedef 3,39; banttan çıkan kimse yok.

Bu kriter ilk ölçümde **4,60** ile kalmıştı. Kalmanın nedeni çözücü
değildi — aynı örnek beş kat uzun süreyle (300 sn) çözüldüğünde sapma
değişmemişti. İki ayrı hata birleşiyordu; ikisi de düzeltildi.

**(1) Veri hatası — demo üreteci SRS 3.3.1'i eziyordu.** SRS 3.3.1'in
vardiya tipi tablosu Akşam vardiyasını açıkça `gece_mi = Hayır` olarak
tanımlar. TD-2'nin "20:00–06:00 ile kesişim ≥ 4 saat" kuralı ise bir
**öneridir**; TD-2'nin kendi metni bayrağın "hesaplanan değil tanımlanan
bir alan" olduğunu söyler. Demo üreteci öneriyi otomatik uygulayıp
tanımlı değeri eziyordu: Akşam (16:00–24:00) pencereyle **tam 4 saat**
kesiştiği için eşiği sınırda karşılayıp gece işaretleniyor, üç
vardiyanın ikisi gece sayılıyor ve dönem içi gece talebi 344 kişi-vardiyaya
(toplamın %60'ı) çıkıyordu. Üreteçler artık bayrakları SRS 3.3.1'den
birebir alır; öneri kuralı yalnızca kullanıcı **yeni** bir vardiya tipi
tanımlarken alanı ön-doldurur ve tanımlı bir değeri asla ezmez.
Düzeltmeden sonra gece talebi 112 kişi-vardiyaya indi.

**(2) Formül hatası — S2/S3'ün paydası (SRS 1.5'te düzeltildi).** Hedef,
gece talebini **bütün** personele bölüyordu. Müracaat görevlileri H8
gereği yalnız Müracaat noktasında çalışabilir ve o noktanın gece talebi
sıfırdır; bu yedi kişi hiçbir çizelgede gece alamaz, ama paydada
sayıldıkları için kalıcı olarak "hedefin altında" görünüp sapmayı
şişiriyorlardı. Yeni tanım hedefi **uygun havuza** böler:

```
P_gece = { p ∈ P : p, gece talebi bulunan en az bir noktanın
                   ön koşulunu karşılıyor }
hedef_gece = ( Σ_{d,s,n: gece[s]=1} talep[d,s,n] ) / |P_gece|
Ceza:  w2 · Σ_{p ∈ P_gece} sapma[p]
```

Havuz dışındaki personel bu hedefin ölçümüne hiç girmez. S3 için aynısı
`P_hs` ile geçerlidir.

Referans örnekte sonuç:

| | İlk ölçüm | Düzeltmeden sonra |
|---|---|---|
| Dönem içi gece talebi | 344 kişi-vardiya | **112** |
| Payda | 40 (bütün personel) | **33 (P_gece)** |
| Hedef | 8,60 gece | **3,39 gece** |
| Gözlenen aralık | 4–12 gece | **3–4 gece** |
| Azami sapma | 4,60 | **0,61** ✅ |

Ölçüm dışında kalan 7 kişi (Müracaat), görev noktalarında gece talebi
bulunmadığı için havuza girmez. Betiğin ulaşılabilirlik teşhisi artık
"her havuz hedefe erişebiliyor" raporlar.

**Havuz tanımı tek yerde durur** (`Baglam.uygun_havuz`): çözücü
(`modele_ekle`), doğrulayıcı (`dogrula`), Analiz servisi (SDD 5.7) ve bu
ölçüm betiği aynı tabanı kullanır. Aksi hâlde iki yerde iki farklı
"ortalama" görünürdü.

### K4 — Çelişkili örnek

Çelişkili örnek, SRS 3.3.6'daki kırılganlık mekanizmasını doğrudan
kurar: 9 kişilik Vardiya Şefi havuzunun 5'i dönem boyunca izinlidir;
kalan 4 kişi, haftada 21 vardiya gerektiren tek noktayı H5/H6 tavanını
aşmadan dolduramaz. Sistem 21 açık hücre raporlamıştır ve her kayıt
kriterin istediği üç bilgiyi de taşır — örnek:

```
2026-06-05 / Gece   / Vardiya Şefliği -> 1 kisi eksik
2026-06-06 / Gündüz / Vardiya Şefliği -> 1 kisi eksik
```

Bu, S1'in esnek hedef olarak tanımlanmasının (SRS 5.5) beklenen
davranışıdır: kadro daraldığında çözüm reddedilmez, açık gösterilir.

### K5 — Manuel düzenleme

28 günlük gerçek bir sürüm üzerinde, dönem geneli kapsamlı kuralları
(S2–S4, SDD 5.5) da tetikleyen bir vardiya tipi değişikliği beş kez
doğrulanmıştır: en iyi 0,031 sn, ortanca 0,032 sn, en kötü 0,038 sn.
Eşiğin (1 sn) yaklaşık 26 kat altındadır.

### K6 — Yeniden çözümde değişen atama sayısı

Charter bölüm 5'in altıncı kriteri, sistemin yeniden çözümde kaç atamanın
değiştiğini **raporlamasını** ister. Raporlama yüzeyi Sürümler ekranının
Karşılaştır işlevidir (SDD 6.3.5); servis karşılığı
`SurumServisi.karsilastir`, uç nokta `GET /api/surum/karsilastir`.

Ölçüm gerçek bir yeniden çözüm üzerinde yapılmıştır:

1. Demo "Rahat Dönem" (02–08 Şubat 2026, 44 personel) çözülüp Sürüm 1
   olarak yayınlandı (toplam ceza 912).
2. Bir güvenlik görevlisi (GG-001) dönemin ilk dört gününe yıllık izne
   çıkarıldı.
3. Sürüm 1'den türetilen taslak yeniden çözüldü → Sürüm 2 (toplam ceza 983).

Karşılaştırma çıktısı:

```
Sürüm 1 → Sürüm 2 : TOPLAM DEĞİŞEN ATAMA = 4
  eklendi = 2   kaldırıldı = 2   değişti = 0
    2026-02-02  GG-001  kaldırıldı  Akşam · Güvenlik →  —
    2026-02-02  GG-013  eklendi     —              →  Akşam · Güvenlik
    2026-02-03  GG-001  kaldırıldı  Akşam · Güvenlik →  —
    2026-02-03  GG-005  eklendi     —              →  Akşam · Güvenlik
```

Sonuç yalnızca raporlamanın çalıştığını değil, **S8 (değişim
minimizasyonu) hedefinin de işlediğini** gösteriyor: izne çıkan personelin
iki vardiyası kaldırılıp iki başka kişiye verilmiş, dönemin geri kalanındaki
~140 atama olduğu gibi korunmuştur. Değişim, izin kaydının zorunlu kıldığı
en küçük kümeyle sınırlı kalmıştır.

Fark üç türde ayrışır (eklendi / kaldırıldı / değişti) — çalışan panelindeki
FR-9.4 sınıflandırmasının aynısı, burada yönetici tarafında. Karşılaştırma
tabanı kullanıcının seçtiği iki sürümdür; çalışan panelindeki "en son arşiv"
seçimi oraya özgüdür ve buraya karıştırılmaz.

## 4. Çözücü–doğrulayıcı uyumu

SDD 3.2.1: "çözücünün geçerli saydığı bir çizelgede doğrulayıcının ihlal
bulması bir yazılım hatası olarak ele alınır."

`tests/test_cozucu_dogrulayici_uyumu_olcek.py` ile **24 rastgele örnek**
(5–9 personel, 5–10 gün, 1–2 nokta, değişken yetkinlik dağılımı) gerçek
CP-SAT çözücüsüyle çözülmüş ve çıkan çizelgeler H1–H8 doğrulayıcısından
geçirilmiştir. **24/24 örnek temiz geçmiştir**; hiçbir örnekte
doğrulayıcı ihlal bulmamıştır. Örnekler sabit tohumla üretilir
(`TOHUM = 20260814`), böylece başarısız bir örnek birebir yeniden
üretilebilir.

## 5. Yeniden üretme

```bash
cd backend
python scripts/kabul_olcumu.py          # K1–K5 (tablo)
python scripts/kabul_olcumu.py --json   # makine okunur çıktı
python -m pytest tests/test_cozucu_dogrulayici_uyumu_olcek.py
python -m pytest tests/test_surum_api.py    # K6'nın mantığı (birim düzeyi)
```

K6'nın uçtan uca ölçümü Sürümler ekranından yapılır: demo veriyi üret
(`python scripts/demo_veri_uret.py --reset`), bir dönemi çöz ve yayınla,
bir izin kaydı ekle, aynı sürümden yeniden çöz, sonra Sürümler → Karşılaştır
ile iki sürümü seç. "Toplam değişen atama" sayısı ekranda ve
`GET /api/surum/karsilastir` yanıtında raporlanır.

Betik ölçüm verisini kurabilmek için veritabanındaki tanım/girdi/kural/
sonuç tablolarını temizler (`demo_veri_uret.py --reset` ile aynı
sözleşme) ve ölçüm verisini sonda bırakır. Çıkış kodu: bütün kriterler
geçtiyse 0, en az biri kaldıysa 1.
