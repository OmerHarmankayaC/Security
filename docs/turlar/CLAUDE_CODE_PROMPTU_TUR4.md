# Claude Code — Sürüm 2, Tur 4: Kural Kataloğu

## Bağlam

VARDİS'in ikinci geliştirme aşamasındasın. Tur 3 saatlik düzenin **veri temelini**
kurdu: talep zaman aralığı oldu, S1 saat eksenine taşındı, kapsama kayıtları
aralığa geçti. Ancak kural kataloğuna dokunulmadı ve blok kataloğu üç blokta
bırakıldı — bu yüzden sistem **dışarıdan hâlâ eski gibi görünüyor.**

Bu tur farkı görünür kılar: katalog genişler, yeni kurallar devreye girer,
gösterim verisi kuralların işlediğini gösterebilecek hâle gelir.

### Doküman sürümleri — ilk işin bunları doğrulamak

| Doküman | Sürüm |
|---|---|
| `BOTAS_Vardiya_Cizelgeleme_SRS.md` | **1.16** |
| `BOTAS_Vardiya_Cizelgeleme_SDD.md` | **1.26** |
| `BOTAS_Vardiya_Cizelgeleme_Backlog.md` | **1.12** |
| `BOTAS_Vardiya_Cizelgeleme_ProjectCharter.md` | 1.2 (değişmedi) |

Taşımıyorlarsa dur ve bana söyle.

### Okunacaklar

- SRS **TD-2** (gece: bayrak ve saat), **TD-6** (ölçüm ufukları), **TD-7**,
  **TD-14** (iki hafta kavramı), **3.3.1** (genişletilmiş katalog), **3.3.5**
  (parametreler), **3.3.6** (kadro analizi), **4.2** (H5, H9, H10), **4.3**
  (S1, S2, S3, S6), **4.4** (amaç fonksiyonu)
- SDD **5.2** (yeni ön kontrol bulguları), **5.3** (takvim haftası kümeleri,
  türevin kaldırılması), **6.3.3** (çizelge ızgarası)
- `docs/SAATLIK_GECIS_KARARLARI.md` — K4, K5, K6, K7, K8, K9, K12, K13, K16
- `docs/turlar/UYGULAMA_PLANI_V2.md` — Tur 4 maddesi

## Çalışma kuralları

- Dört kanonik dokümana **dokunmazsın**. Etki doğuran bir şey çıkarsa
  `PROGRESS_V2.md`'ye "DOKÜMAN BORCU" başlığı altında yaz.
- Tasarımdan sapma gerekiyorsa **önce nedenini söyle**, sonra uygula.
- Şema değişikliği yalnızca Alembic göçüyle.
- Git: `add`, `commit`, `tag` senin; `push` ve `remote` **asla**.
- Backend'de tip açıklamaları zorunlu; `ruff` temiz. Frontend'de TypeScript strict.
- **Yeni bir kural asla tek başına eklenmez:** sınıf + `modele_ekle` + `dogrula` +
  birim test + kural kayıt defterine kayıt aynı commit'te gider.
- **Yeniden tanımlanan bir kuralın eski testi silinmez, güncellenir.** Beklenen
  değerler gerekçesiyle birlikte değişir; davranışın bilinçli mi kazayla mı
  değiştiği bilgisi kaybolmaz.
- Bu tur uzun. **Her iş grubundan sonra commit at**, hepsini sona bırakma.

## Hata kalıpları — bu turda hepsi sahnede

1. **Aynı tanımın iki yerde durması.** İki hafta kavramı (kayan pencere / takvim
   haftası) ayrı yardımcılarda kalmalı; birleştirilirse hangi kuralın hangisini
   kullandığı çağrı yerine bakılarak anlaşılır ve karışması an meselesidir.
2. **Metriğin ayrım üretmemesi.** S2 ve S3'ün birimi değişiyor; hedefin paydası
   yine uygun havuzdur. Bu payda bir kez yanlış hesaplandı ve K3 kabul kriterinin
   kalmasına yol açtı.
3. **Isıtma penceresini hesaba katmamak (TD-5).** İki kez oldu. H10'un dönem
   sınırındaki haftası tam olarak buna bağlı.
4. **Sessiz yanlış çalışma.** `blok_gorunumu_uret` türevi karışık katalogda
   sessizce yanlış hesaplar. İş 2 bunun için var.
5. **Öneri kuralının tanımlı değeri ezmesi.** `gece_mi` bayrağı tanımlı alandır;
   öneri yalnızca yeni blok oluşturulurken ön-doldurur. Bu bir kez çiğnendi.

---

## İş 1 — Testler arası veri sızıntısı (B-22)

**Turun ilk işi.** Test veritabanı ayrı (B-20) fakat testler arasında
sıfırlanmıyor; kayıt bırakan testler sonrakileri etkiliyor. İki kez gözlendi:
`test_cizelge_api` sıra bağımlı hâle gelmişti, ve blok yaratan testlerin
bıraktığı kayıtlar katalogda üç ayrı 08.00 bloğu biriktirip benzersizlik kısıtını
kırmıştı. İki durumda da kırılan test değil, **testin gördüğü dünya** yanlıştı.

Bu tur çok sayıda yeni tanım ve kural testi getirecek; aynı sızıntıyla girme.

- Testler arasında tanım/girdi/sonuç tablolarını temizleyen bir fikstür.
- Temizlik uygulamanın kendi silme yolundan geçsin, elle `DELETE` ile değil —
  yabancı anahtar sırası tek yerde tanımlı kalsın.
- Bir testin bıraktığı veri sonrakini etkilerse bu **testin hatası** olarak
  görünsün, gizemli bir kırılma olarak değil.

**Kabul:** Test dosyalarının sırası değiştirildiğinde takım yine geçiyor.

---

## İş 2 — Blok görünümü türevini kaldır

**Dayanak:** SDD 5.3.

Tur 3'te S2/S3/S4 talebi hâlâ vardiya biriminde okuduğu için talep saat
ekseninden blok eksenine geri türetiliyordu (`blok_gorunumu_uret`). Türev bir
bloğun gereken sayısını "kapsadığı saatlerdeki en büyük gereken" olarak alır —
**yalnızca hizalı katalogda doğru.** Bu turda katalog karışık hâle geliyor.

- Türevi kullanan her yer S2/S3'ün yeni saat tabanlı hesabına geçsin.
- Türev fonksiyonu ve "tek uzunluklu katalog varsayımı" yorumları silinsin.
- Talep ekranındaki blok görünümü de kalksın; talep zaten aralık olarak
  gösteriliyor.

**Kabul:** Kod tabanında `blok_gorunumu_uret` çağrısı kalmamış.

---

## İş 3 — H5 yeniden, H9 ve H10 (SRS 4.2)

**H5** artık kırk beş saatlik tavan değil, `haftalik_mutlak_tavan` (66).
Parametre adı da değişiyor (`azami_haftalik_saat` → `haftalik_mutlak_tavan`);
göçte mevcut kural kaydının parametresi taşınmalı, değeri 66'ya güncellenmeli.

**H9 — günlük azami saat** (`azami_gunluk_saat`, 11). Blok kataloğu kısıtı
(`tanim_servisi.py:51`) bu parametreyi okusun; oradaki **geçici sabit silinsin**.
İki ayrı değer bırakma.

**H10 — yıllık fazla çalışma kotası.** SRS 4.2'deki formülasyonu birebir uygula.

- Takvim haftası kümeleri (pazartesi–pazar) kayan pencerelerden **ayrı** bir
  yardımcıda üretilsin (SRS TD-14). Karışmanın sonucu sessizdir: kayan pencerede
  toplanan fazla çalışma yedi katına çıkar ve kota gerçekte aşılmadan aşılmış
  görünür.
- Dönem sınırını aşan haftanın dönem dışı günleri sabit terim olarak girsin:
  ısıtma penceresinden veya yayınlanmış sürümlerden okunsun, ikisi de yoksa sıfır.
- `devir[p]` bu turda **personel kaydındaki alandan** okunsun. Yayınlanmış
  sürümlerden türetme Tur 5'in işi (`GecmisSayaclar`); şimdi alan tek kaynak.
- Kural zorunlu ama modeli çözülemez yapmaz — `fazla = 0` her zaman uygulanabilir.
  Bunu doğrulayan bir test yaz: kotası dolmuş personel eşiğe kadar çalışmaya
  devam ediyor, üstüne çıkmıyor.

**Kabul:** On iki saatlik bloklar içeren bir senaryoda fazla çalışma saatleri
elle hesaplananla birebir aynı. Kotası dolmuş personelin bulunduğu senaryo
çözülüyor, infeasible dönmüyor.

---

## İş 4 — S1'in üst sınırı esnek (SRS 4.3)

Üst sınır zorunlu olmaktan çıkıyor:

```
∀d, t, n :  Σ_p Σ_{b ∋ t} x[p,d,b,n] − fazla[d,t,n] ≤ talep[d,t,n]
Ceza:  w1 · Σ eksik  +  w1f · Σ fazla        (w1f başlangıç değeri 2)
```

Karışık katalogda fazla kadro **yapısal olarak kaçınılmazdır**: 08.00–16.00
arasında dört kişi isteyen bir talep on saatlik blokla kapatıldığında 16.00–18.00
saatlerinde de kadro üretir. Zorunlu kalırsa model çözülemez.

- `fazla` değişkenleri de aynı saat gruplamasından geçsin (SDD 5.3) — `eksik`
  için yapılan simetri kırma burada da gerekli.
- Manuel düzenlemede fazla kadro **ceza üretmemeye devam eder**; değişen yalnızca
  çözücü tarafı. İki tarafın farklı davranması bilinçli (SRS 4.3).

**Kabul:** On saatlik blok içeren bir senaryo çözülüyor ve fazla kadro kaydı
üretiyor; aynı senaryo eski zorunlu üst sınırla çözülemiyordu.

---

## İş 5 — S2, S3 saat birimine; S6 kayma tanımına (SRS 4.3)

- `gece_saat[b] = |b ∩ [20:00, 06:00]|` **tek yerde** hesaplansın.
- `gece_mi` bayrağı H3'te kalsın ve **tanımlı alan olmaya devam etsin**; öneri
  kuralı yalnızca yeni blok oluşturulurken ön-doldurur ve tanımlı değeri asla
  ezmez. Bu bir kez çiğnendi ve K3'ün kalmasının iki nedeninden biri oldu.
- S2 gece saati, S3 hafta sonu saati üzerinden ölçülsün. Uygun havuz mantığı
  (`P_gece`, `P_hs`) **aynen korunsun** — payda bir kez yanlış hesaplandı.
- S6: dairesel başlangıç saati kayması, tolerans `desen_toleransi_saat` (2).
  Dairesel fark zorunlu: 22.00 ile 02.00 arası dört saat, yirmi değil.
- Amaç fonksiyonundaki `eksikK` terimi kaldırılsın; `w1f` ve `w6b` eklensin
  (SRS 4.4).

**Kabul:** Farklı uzunlukta gece blokları içeren bir senaryoda, on iki saatlik
gece bloğu alan personel sekiz saatlik alandan daha yüksek gece yükü gösteriyor.
S6, 08.00–16.00 ile 08.00–20.00 arasında geçişi cezalandırmıyor (aynı saatte
başlıyorlar), 08.00–16.00 ile 16.00–24.00 arasında cezalandırıyor.

---

## İş 6 — Blok kataloğu genişler + gösterim verisi

**Dayanak:** SRS 3.3.1, 3.3.6; Backlog karar günlüğü 13.08.2026.

Katalog SRS 3.3.1'deki yedi bloğa çıkar (mevcut üçü + 12 saatlik uzun gece ve
uzun gündüz + 10 saatlik erken ve geç).

**Gösterim verisi kuralların işlediğini gösterebilmeli.** Bugünkü demo kırk dört
kişilik kadroda haftalık 1.152 saatlik talebi taşıyor: kişi başına 26 saat, kimse
fazla çalışma eşiğine yaklaşmıyor, H10 hiçbir zaman tetiklenmiyor. Kuralların
işlediğini gösteremeyen bir gösterim verisi, kuralların yazılmamış olmasıyla aynı
kapıya çıkar.

Senaryolar:

| Senaryo | Amaç |
|---|---|
| Dengeli dönem | Kadro talebe uygun (~30 kişi); kişi başına haftalık yük eşiğe yakın ama altında |
| Sıkışık dönem | Mevcut kırılganlık mekanizması korunur; kapsama açığı gün/saat/nokta düzeyinde görünür |
| Fazla çalışma dönemi | 12 saatlik bloklarla eşiğin üzerine çıkılır; kota tüketimi görünür |
| Kota sınırı | Devir bakiyesi yüksek personel; kotası dolmuş kişi eşiğe kadar çalışmaya devam eder |

- **Gerçekçi personel adları** ("Demo Personel GG-001" yerine). Sicil numaraları
  kalabilir.
- Üreteç bayrakları SRS 3.3.1'den **birebir** alsın; öneri kurallarını
  uygulamasın (bu bir kez yapıldı ve gece talebi üç katına çıktı).

**Kabul:** `demo_veri_uret.py --reset` sonrası dört senaryo da çözülüyor ve
farklı davranış gösteriyor. Fazla çalışma senaryosunda en az bir personelin
kotasından tüketim var; kota sınırı senaryosunda en az bir personel eşiğe
dayanmış durumda.

---

## İş 7 — Çizelge hücresinde saat aralığı (SDD 6.3.3)

Hücre blok adının kısaltmasını değil **saat aralığını** göstersin:
`08–16 · GÜV`. Katalog karışık olduğunda "Gündüz" adını taşıyan sekiz ve on iki
saatlik bloklar aynı kısaltmaya sıkışıyor ve ızgara iki farklı çizelgeyi aynı
gösteriyor.

Hücre rengi başlangıç saati bandından hesaplansın, blok kimliğinden değil. Sabit
üç renk yalnızca üç bloklu katalogda anlamlıydı.

**Kabul:** Karışık katalogla çözülmüş bir çizelgede farklı uzunluktaki bloklar
ızgarada ayırt edilebiliyor.

---

## İş 8 — Ön kontrole kota bulguları (SDD 5.2)

- `devir[p] > yillik_fazla_kotasi` olan personel — veri hatası, H10'u tek başına
  çözülemez kılar.
- Kalan kotası sıfıra yakın personel — fazla çalışmaya atanamaz; kadro hesabı
  bunu bilmeden yapıldığında açığın nedeni görünmez kalır.

İkisi de **bulgudur, engel değildir** (K18): çözüm yine çalışır.

---

## Turun bitiş kontrolü

- [ ] `pytest` tam takım geçiyor — **test sırası değiştirildiğinde de**
- [ ] `tsc -b`, `oxlint`, `ruff check`, `ruff format --check` temiz
- [ ] Çözücü–doğrulayıcı uyum testi yeni katalogla **24/24** temiz
- [ ] **Kabul ölçümü koşuldu**, K1 süresi `PROGRESS_V2.md`'de. Katalog yedi bloğa
      çıktığı için süre artacak; eşiğin (60 sn) yarısını aşarsa dur ve bana söyle
- [ ] `tanim_servisi.py`deki geçici sabit silindi, değer H9'dan okunuyor
- [ ] `blok_gorunumu_uret` kod tabanında yok
- [ ] `EK_B_UC_NOKTALAR.md` yeniden üretildi
- [ ] `git status` temiz, sır yok, `PROGRESS_V2.md` güncel

## Bu turda yapmayacakların

- **`GecmisSayaclar` servisi ve kümülatif adalet** (Tur 5). `devir[p]` bu turda
  yalnızca personel kaydındaki alandan okunur; adalet ufku henüz dönem içidir.
- Talep ekranının görsel geliştirmesi, Analiz ekranı, Kural ekranı (Tur 6).
- **Ağırlık kalibrasyonu** (Tur 8). `w1f = 2` başlangıç değeridir; diğer
  ağırlıklara dokunma. S2/S3'ün birimi değiştiği için mevcut ağırlıklar artık
  ölçek olarak yanlış — bu **beklenen** bir durum, düzeltmesi Tur 8'de.
- Excel/analiz dışa aktarma, sürükle-bırak, özet ekranı, belge, kullanıcı
  hesapları.
- Tasarım sürüm 4'ün koda geçirilmesi.
- **Sunucuya dağıtım.** Üç göç bekliyor, bu turunkiler de eklenecek.

Bunlardan biri yolda "aslında lazım" gibi görünürse uygulama; `PROGRESS_V2.md`'ye
not düş ve devam et.
