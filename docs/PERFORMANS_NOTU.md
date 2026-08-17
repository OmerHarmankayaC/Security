# Performans ve Kabul Kriteri Notu

**Tarih:** 17.08.2026 · **Kapsam:** Tur 10 kapanış ölçümü · **Sürüm:** 3.0

Bu not, Proje Tanım Dokümanı bölüm 5'teki altı kabul kriterinin ölçüm
sonuçlarını içerir. Altısı da `backend/scripts/kabul_olcumu.py` ile tek
koşumda alınır — sürüm 2.0'da K6 ayrı ölçülüyordu, artık betiğin içinde
(bölüm 6). Notun sayıları elle yazılmaz, ölçümün çıktısından alınır ve
ölçüm yeniden çalıştırılarak doğrulanabilir (bölüm 7).

> Bu dosya `docs/` altındaki dört kanonik dokümandan (Proje Tanım
> Dokümanı, SRS, SDD, Backlog) biri **değildir**; kapanış turunun ürettiği
> ayrı bir çıktıdır.

---

## 1. Sürüm 2.0'dan bu yana ne değişti

Beş değişiklik ölçümü doğrudan etkiledi:

| Değişiklik | Ölçüme etkisi |
|---|---|
| **Model saatlik düzene geçti** (Tur 5, SRS TD-13) | Karar değişkeni "hangi blok" değil "hangi saat". Blok katalogu kalktı; blok uzunlukları artık çözümün çıktısı. K3'ün birimi vardiya sayısından **gece saatine** döndü. |
| **Müracaat görev noktası kapsamdan çıktı** (Charter 1.4) | Referans örnek 3 noktadan **2 noktaya** indi; havuz yapısı değişti. |
| **Adalet kümülatif ufka taşındı** (Tur 9, SRS TD-6) | S2/S3/S4 doksan günlük pencereyi kapsıyor; yük ile pay birlikte ölçekleniyor. |
| **K3'ün ölçüm ufku sınırlandı** (Charter 1.5) | Kriter **planlama dönemini** ölçer; kümülatif sapma kriter değil gösterge. |
| **Ağırlıklar kalibre edildi** (Tur 10) | S2 10→20, S4 1→4. |

**Sürüm 2.0 ile doğrudan sayı karşılaştırması yapılamaz.** K3'ün birimi
değişti (vardiya → saat), eşiği değişti (1,0 → 8 gece saati) ve referans
örnek küçüldü (3 nokta → 2). Sürüm 2.0'ın "K3 = 0,61" değeri bu notun
"69,00" değeriyle aynı ölçünün iki okuması değildir.

---

## 2. Ölçüm ortamları

Ölçüm **iki ortamda** alınmıştır. Belirleyici olan gösterim sunucusudur;
geliştirme makinesi sütunu donanım etkisini görünür kılmak için durur.

| | Geliştirme makinesi | **Gösterim sunucusu (referans donanım)** |
|---|---|---|
| İşletim sistemi | macOS 15.7.3, arm64 | **Linux x86_64 (Ubuntu)** |
| Çekirdek | 10 | **4** |
| Bellek | 16 GB | **7 GB** |
| Arama işçisi | 3 | **3** (SDD 3.4.3: çekirdek − 1) |
| Python | 3.13 | **3.14.4** |
| OR-Tools | 9.15.6755 | **9.15.6755** |
| Ortam | yalnız ölçüm | **paylaşımlı** |

**Gösterim sunucusu paylaşımlıdır** (SDD 3.4.1/3.4.2): aynı makinede
`vera-rag` ve `energy-api` de çalışır. Ölçülen süreler, izole bir makinede
alınacak sürenin **üst sınırı** gibi okunmalıdır.

**Belirlenimsizlik.** CP-SAT paralel aramada belirlenimsizdir; aynı örnek
farklı çalıştırmalarda farklı (eşit iyilikte) çözümler verebilir. K3'ün
sapması ve K4'ün açık sayısı çalıştırmadan çalıştırmaya değişir; geçme
kararı ve K1/K2/K5 değerleri değişmez.

---

## 3. Referans örnek

Kabul kriterinin tanımladığı ölçek: **40 personel, 28 gün**.

| | |
|---|---|
| Personel | 40 — Vardiya Şefi havuzu 9, Güvenlik Görevi 31 |
| Dönem | 02.02.2026 – 01.03.2026 (28 gün, pazartesi başlangıçlı) |
| Görev noktası | 2 (Vardiya Şefliği, Güvenlik) — Müracaat Charter 1.4 ile kapsam dışı |
| Talep | SRS 3.3.4 matrisi; dönem içi gece talebi **1.600 kişi-saat** |
| Kural | H1–H10 + S1–S8, kalibre edilmiş ağırlıklarla |
| Zaman limiti | **60 sn** (ürün varsayılanı) |

Ağırlıklar: S1 = 10000, S1f = 2, **S2 = 20**, S3 = 8, **S4 = 4**, S5 = 12,
S6 = 4, S7 = 6, S8 = 15.

---

## 4. Sonuçlar

| Kriter | Eşik | Geliştirme makinesi | **Gösterim sunucusu** | Sonuç |
|---|---|---|---|---|
| K1 — çözüm süresi | < 60 sn | 8,63 sn | **23,88 sn** | ✅ |
| K2 — zorunlu ihlal | 0 | 0 | **0** | ✅ |
| K3 — gece adaleti | ≤ 8 gece saati | 22,00 | **69,00** | ❌ |
| K4 — çelişkili örnek | ≥ 1 açık, tam bilgi | 160 aralık | **151 aralık** | ✅ |
| K5 — düzenleme doğrulaması | < 1 sn | 0,076 sn | **0,251 sn** | ✅ |
| K6 — yeniden çözüm farkı | rapor üretilir | — | **896 değişiklik** | ✅ |

**5/6 kriter geçiyor.**

### K1 — Çözüm süresi

23,88 sn (model kurma 5,07 sn dahil), eşik 60 sn. Geliştirme makinesinde
8,63 sn; aradaki **2,8 kat** fark donanımdan gelir (10 çekirdek karşısında
4). Eşiğin altında rahat bir pay var.

### K2 — Zorunlu kısıt ihlali

H1–H8'in tamamı doğrulayıcıdan temiz geçti.

### K3 — Gece adaleti · **KALDI**

Ölçülen azami sapma **69,00**, eşik 8 gece saati.

| | |
|---|---|
| Ölçüme giren personel | 40 (ölçüm dışı: 0) |
| Adil pay aralığı | 33,0 – 64,1 gece saati |
| Gözlenen yük aralığı | 36 – 102 gece saati |
| Eşiği aşan | **33 / 40** |
| Ulaşılabilirlik teşhisi | **her havuz hedefe erişebiliyor** |

Teşhis, engelin kadro olmadığını söylüyor: 31 kişilik havuzun erişebildiği
gece talebi 1.320 → kişi başı tavan 42,58; 9 kişilik havuzda 1.600 → 177,78.
Yani hedef her iki havuz için de ulaşılabilir; sorun **aramanın hedefe
yetişememesi**.

**Donanım farkı bu kriterde belirleyici.** Aynı ağırlıklarla geliştirme
makinesinde 22,00, sunucuda 69,00 — üç katından fazla. K1'deki 2,8 katlık
fark aynı kökten gelir: sunucuda 60 saniye, geliştirme makinesinin 60
saniyesinden çok daha az arama demektir.

**Kalibrasyon ile süre ayrıştırıldı** (Tur 10, İş 4). Referans örneğinde,
geliştirme makinesinde ölçülmüştür:

| Ağırlıklar | Limit | K3 | Eşiği aşan |
|---|---|---|---|
| S2=10, S4=1 | 60 sn | 25,00 | 10 |
| S2=20, S4=4 | 60 sn | 22,00 | 10 |
| S2=20, S4=4 | 300 sn | 12,00 | 1 |

Kalibrasyonun payı 25 → 22 (eşiği aşan sayısı değişmedi); sürenin payı
22 → 12 (aşan 10'dan 1'e). **İyileşmenin neredeyse tamamı arama
süresinden geliyor.** Backlog T-08 bu konuda açık: *"ölçüm koşulunu
değiştirerek kriteri geçirmek yerine nedeni giderilmeli."* Zaman limiti
bu turda **60 saniyede bırakılmıştır**.

**Açığın büyüklüğü:** eşik 8, ölçülen 69 — sekiz katından fazla. Kırk
kişinin otuz üçü eşiğin dışında. Bu, kalan en büyük açıktır.

### K4 — Çelişkili örnek

151 açık aralık (875 saat), toplam **2.976 kişi-saat** eksik. Her satır gün,
saat aralığı, görev noktası ve eksik kişi sayısı taşıyor; ilk beş satır
ölçüm çıktısında örneklenmiştir. Çelişki kadro büyüklüğünden değil
erişilebilirlikten kurulur (Charter bölüm 5).

### K5 — Manuel düzenleme doğrulaması

En kötü ölçüm **0,251 sn**, eşik 1 sn. Beş ölçüm: en iyi 0,201 / ortanca
0,218 / en kötü 0,251. Dönem uzunluğu 28 gün.

### K6 — Yeniden çözümde değişen atama sayısı

**896 değişiklik**: 60 eklenen, 699 kaldırılan, 137 değişen. Sürüm 1 → 2
karşılaştırması.

Bu kriter **sürüm 2.0'da betikte yoktu**. Charter altı kriter sayıyor,
betik beşini ölçüyor ve rapor "5 kriter" diyordu; kimse farkı görmemişti.
Tur 10'da eklendi (Backlog B-25).

---

## 5. Çözücü–doğrulayıcı uyumu

`test_cozucu_dogrulayici_uyumu_olcek.py` **24/24** geçiyor: rastgele
üretilen yirmi dört örnekte çözücünün ürettiği çizelge, bağımsız
doğrulayıcıdan aynı ceza dökümüyle geçiyor (SDD 3.2.1).

---

## 6. Ölçüm betiğinin kendisi

`kabul_olcumu.py` **iki tur boyunca sessizce kırık kaldı** (B-25). İki ayrı
imza değişikliği onu patlatıyordu — `saatleri_araliklara_birlestir` üç
değer döndürmeye başladı (B-23) ve `AtamaDegisikligi` `surum_id` almayı
bıraktı (TD-16) — ama betiği koşan hiçbir şey yoktu.

Tur 10'da iki şey yapıldı: kırıklar giderildi ve betiğin çalıştığını
doğrulayan bir duman testi takıma alındı
(`tests/test_kabul_olcumu_dumani.py`). Test kriterlerin **geçmesini**
ölçmez, betiğin **çalışmasını** ölçer; geçmeleri bu notun işidir.

**Ders:** bir şeyin çalıştığını gösteren tek kanıt, onun düzenli olarak
koşuluyor olmasıdır.

---

## 7. Yeniden üretme

Gösterim sunucusunda:

```bash
cd /opt/vardiya/backend
set -a; . /opt/vardiya/.env; set +a
VERI_TEMIZLIGINE_IZIN=true sudo -u vardiya --preserve-env=VERITABANI_URL,VERI_TEMIZLIGINE_IZIN \
  .venv/bin/python scripts/kabul_olcumu.py --zaman-limiti 60
```

**Betik ilk iş olarak veritabanını TEMİZLER.** Gösterim verisi silinir;
ölçümden önce yedek alın ve ölçümden sonra veriyi yeniden üretin:

```bash
pg_dump -Fc "$PGURL" -f /opt/vardiya/yedek/vardiya-$(date +%Y%m%d-%H%M)-olcum-oncesi.dump
```

```bash
VERI_TEMIZLIGINE_IZIN=true .venv/bin/python scripts/demo_veri_uret.py --reset
```

Bu ölçümün yedeği: `vardiya-20260817-1326-olcum-oncesi.dump` (73K, 19 tablo
verisi; 1.282 atama / 8 sürüm / 30 personel / 6 dönem).

Makine okunur çıktı için `--json` eklenir.
