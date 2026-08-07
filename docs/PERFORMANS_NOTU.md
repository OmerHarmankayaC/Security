# Performans ve Kabul Kriteri Notu

**Tarih:** 07.08.2026 · **Kapsam:** Sprint 3 Gün 14 · **Sürüm:** 1.0

Bu not, Proje Tanım Dokümanı bölüm 5'teki kabul kriterlerinin ölçüm
sonuçlarını içerir. Ölçümler `backend/scripts/kabul_olcumu.py` ile
otomatik olarak alınır; not elle güncellenmez, betiğin çıktısından
yazılır ve betik yeniden çalıştırılarak doğrulanabilir.

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
çalıştırmaya değişir; K1/K2/K5 sonuçları değişmez.

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
| **K1** 40×28 referans örnek < 60 sn | < 60,0 sn | **1,21 sn** | ✅ geçti |
| **K2** Zorunlu kısıt ihlali sıfır | 0 ihlal | **0 ihlal** | ✅ geçti |
| **K3** Kişi başına gece sayısı hedeften en fazla 1 sapar | ≤ 1,0 | **4,60** | ❌ kaldı |
| **K4** Çelişkili örnekte gün/vardiya/eksik sayısı gösterilir | ≥ 1 açık, üç bilgi de dolu | **31 açık hücre** | ✅ geçti |
| **K5** Manuel düzenleme doğrulaması < 1 sn | < 1,000 sn | **0,036 sn** | ✅ geçti |

**4/5 kriter geçti.**

Charter'ın altıncı kriteri ("yeniden çözümde değişen atama sayısı
raporlanır") bu turda ölçülmemiştir: raporlama yüzeyi Sürümler
ekranındaki karşılaştırma işlevidir (SDD 6.3.5) ve o ekran Gün 15'in
işidir. Uygulama Planı'nın Gün 14 maddesi de beş kriter sayar.

### K1 — Çözüm süresi

| Aşama | Süre |
|---|---|
| Model kurma | 0,51 sn |
| İlk uygun çözüme ulaşma (çözücü içi) | 0,70 sn |
| **Kullanıcının beklediği toplam** | **1,21 sn** |
| Zaman limitine kadar iyileştirme | 60,06 sn |

**"Çözülür" ne demektir.** CP-SAT bir eniyileme problemi çözer ve zaman
limiti dolana kadar çözümü iyileştirmeye devam eder; 60 saniyede
eniyilik kanıtlanmaz (durum: *uygun*). Kriterin işaret ettiği süre, ilk
**kullanılabilir** çizelgeye ulaşma süresidir — Charter bölüm 6'nın
önlem cümlesi de bunu söyler: "limit dolduğunda o ana kadarki en iyi
çözüm döndürülür". Bu okumayla ölçülen 1,21 saniye, 60 saniyelik eşiğin
yaklaşık 50 kat altındadır. Referans donanımın daha yavaş çekirdekleri
bu payı daraltır ama kapatması beklenmez.

### K3 — Gece adaleti (kalan kriter)

Ölçülen azami sapma **4,60** (eşik 1,0). Gözlenen aralık 4–12 gece,
hedef 8,60.

**Bu bir çözücü yetersizliği değildir.** Aynı örnek 5 kat uzun süreyle
(300 sn) çözüldüğünde azami sapma **değişmemiştir** (4,60). Betiğin
ürettiği ulaşılabilirlik teşhisi nedeni gösterir:

| Havuz | Ulaşabildiği gece talebi | Kişi başı tavan |
|---|---|---|
| 24 kişilik (Güvenlik Görevi) | 248 | 10,33 |
| 9 kişilik (Vardiya Şefi) | 304 | 33,78 |
| **7 kişilik (Müracaat)** | **40** | **5,71** ← ulaşılamaz |

**Kanıt.** Müracaat görevlileri yalnızca Müracaat noktasında
görevlendirilebilir (H8); bu noktanın gece işaretli talebi dönem boyunca
toplam 40 kişi-vardiyadır. Yedi kişinin gece sayıları toplamı 40'ı
aşamaz. Kriterin sağlanması için her birinin en az 8,60 − 1 = 7,60 gece
alması gerekirdi; bu da toplamda 7 × 7,60 = 53,2 > 40 demektir. Çelişki.
**Hiçbir çizelge bu örnekte K3'ü sağlayamaz**, ek çözücü süresi sonucu
değiştirmez.

**Kökeni: iki tanımın birleşimi.**

1. **TD-2** gece bayrağını "20:00–06:00 aralığıyla kesişim ≥ 4 saat"
   kuralıyla önerir. Akşam vardiyası (16:00–24:00) bu pencereyle **tam 4
   saat** kesişir, yani eşiği sınırda karşılar ve gece olarak
   işaretlenir. Sonuçta üç vardiyanın **ikisi** gece sayılır: dönem içi
   gece talebi 344 kişi-vardiya (toplam 576'nın %60'ı).
2. **S2** (SRS 4.3) hedefi `toplam gece talebi / |P|` olarak, yani
   **bütün personele** bölerek tanımlar — yetkinliği gereği gece
   çalışamayan personel de paydadadır.

Bu ikisi birleşince, gece işaretli işin çoğuna yapısal olarak
erişemeyen bir havuz (Müracaat) hedefi kaçınılmaz olarak ıskalar.

**Not:** Akşam vardiyasının bayrağı gündüze çevrilse bile kriter
sağlanmaz. O durumda gece talebi 112, hedef 2,80 olur; Müracaat
noktasının gece talebi sıfır olduğundan Müracaat görevlilerinin gece
sayısı 0'dır ve sapma 2,80 > 1 kalır. Yani asıl bağlayıcı olan (2)
numaralı tanımdır.

**Bu bir uygulama hatası değil, tanım düzeyinde bir açıktır** ve
çözümü SRS'i etkiler; bu nedenle bu turda **değiştirilmemiştir**.
Karar için üç seçenek not edilmiştir:

- **(a)** K3/NFR-9'un kapsamını "gece çalışabilen personel" ile
  sınırlamak (S2'nin paydasını değiştirmek). Tek başına yetmez:
  mevcut çizelge bu ölçüte göre yeniden değerlendirildiğinde (33 kişi,
  hedef 344/33 = 10,42) azami sapma **1,58** çıkar — 1,0'ın hâlâ
  üstünde. *Bu bir yeniden çözüm ölçümü değil, eldeki çözümün farklı
  ölçütle yeniden değerlendirilmesidir; payda değişirse çözücü farklı
  bir çizelge üretir ve sapma bir miktar düşebilir.*
- **(b)** TD-2'nin eşiğini "> 4 saat" yapmak, böylece Akşam gündüz
  sayılır. Tek başına yeterli değildir (yukarıdaki not).
- **(c)** Kriteri, yapısal olarak erişilebilir hedefe göre yeniden
  ifade etmek (örneğin havuz bazında adalet).

Seçim mentör/paydaş kararıdır; karar verildiğinde önce ilgili doküman,
sonra kod güncellenmelidir (Uygulama Planı, "Mentör Görüşmesi Sonrası
Güncelleme Protokolü").

### K4 — Çelişkili örnek

Çelişkili örnek, SRS 3.3.6'daki kırılganlık mekanizmasını doğrudan
kurar: 9 kişilik Vardiya Şefi havuzunun 5'i dönem boyunca izinlidir;
kalan 4 kişi, haftada 21 vardiya gerektiren tek noktayı H5/H6 tavanını
aşmadan dolduramaz. Sistem 31 açık hücre raporlamıştır ve her kayıt
kriterin istediği üç bilgiyi de taşır — örnek:

```
2026-06-04 / Gece  / Vardiya Şefliği -> 1 kisi eksik
2026-06-05 / Akşam / Vardiya Şefliği -> 1 kisi eksik
```

Bu, S1'in esnek hedef olarak tanımlanmasının (SRS 5.5) beklenen
davranışıdır: kadro daraldığında çözüm reddedilmez, açık gösterilir.

### K5 — Manuel düzenleme

28 günlük gerçek bir sürüm üzerinde, dönem geneli kapsamlı kuralları
(S2–S4, SDD 5.5) da tetikleyen bir vardiya tipi değişikliği beş kez
doğrulanmıştır: en iyi 0,029 sn, ortanca 0,030 sn, en kötü 0,036 sn.
Eşiğin (1 sn) yaklaşık 28 kat altındadır.

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
python scripts/kabul_olcumu.py          # kriterleri ölç (tablo)
python scripts/kabul_olcumu.py --json   # makine okunur çıktı
python -m pytest tests/test_cozucu_dogrulayici_uyumu_olcek.py
```

Betik ölçüm verisini kurabilmek için veritabanındaki tanım/girdi/kural/
sonuç tablolarını temizler (`demo_veri_uret.py --reset` ile aynı
sözleşme) ve ölçüm verisini sonda bırakır. Çıkış kodu: bütün kriterler
geçtiyse 0, en az biri kaldıysa 1.
