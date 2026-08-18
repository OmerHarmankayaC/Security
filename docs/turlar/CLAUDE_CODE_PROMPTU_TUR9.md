# Claude Code — Sürüm 2, Tur 9: Geçmiş Sayaçlar ve Kümülatif Adalet

## Bağlam

Adalet hesapları bugün yalnızca planlama dönemini kapsıyor. Bir personel bir
dönemde ağır gece yükü aldıysa, bir sonraki dönemde bu hiç görünmüyor ve aynı
kişiye yeniden ağır yük düşebiliyor. Bu turda adalet ufku doksan güne genişliyor
ve yıllık kotanın devri gerçek geçmişten türetiliyor.

Bu, ürün listesindeki **madde 8** ve Backlog'daki **B-01**'dir; ikinci aşamanın
başından beri bekliyor.

### Doküman sürümleri — ilk işin bunları doğrulamak

| Doküman | Sürüm |
|---|---|
| `VARDIS_ProjectCharter.md` | 1.4 |
| `VARDIS_SRS.md` | **1.25** |
| `VARDIS_SDD.md` | **1.32** |
| `VARDIS_Backlog.md` | **1.22** |

Taşımıyorlarsa dur ve bana söyle.

### Okunacaklar

- SRS **TD-6** (ölçüm ufukları — bu turun tanımı), **TD-5** (ısıtma penceresi),
  **4.3** (S2, S3, S4), **H10**
- SDD **5.9** (geçmiş sayaçlar servisi), **5.3** (model kurma)

## Çalışma kuralları

- Dört kanonik dokümana **dokunmazsın**. Etki doğuran bir şey çıkarsa
  `PROGRESS_V2.md`'ye "DOKÜMAN BORCU" başlığı altında yaz.
- Tasarımdan sapma gerekiyorsa **önce nedenini söyle**, sonra uygula.
- Git: `add`, `commit`, `tag` senin; `push` ve `remote` **asla**.
- `ruff`, `tsc -b`, `oxlint` temiz; her iş grubundan sonra commit.
- Yeniden tanımlanan bir kuralın eski testi silinmez, güncellenir; her değişen
  beklenen değerin yanına **neden** değiştiği yazılır.

---

## İş 1 — `GecmisSayaclar` servisi

**Dayanak:** SDD 5.9.

Bir dönem ve bir ufuk alır; her personel için gece saati, hafta sonu saati,
toplam saat ve fazla çalışma saati döndürür.

- Kaynak **yayınlanmış sürümlerin atamalarıdır**; ayrı bir sayaç tablosu yok.
- Bir dönemin birden çok yayınlanmış sürümü olabilir — her dönem için **en son
  yayınlanan** kullanılır. Arşivlenmiş ve taslak sürümler sayılmaz: biri geçmişi
  iki kez sayar, diğeri henüz gerçekleşmemiş bir çizelgeyi geçmişe yazar.
- Ufuk bir dönemin ortasına düşerse o dönemin yalnızca pencereye giren günleri
  sayılır; blok başladığı güne yazılır (TD-1).
- **Önbellek kurma.** Doksan günlük pencerede yaklaşık üç bin blok okunur; ölçek
  gerektirmiyor. Önbellek bir sürüm yayınlandığında bayatlar ve geçersiz kılma
  mantığı hesabın kendisinden karmaşık olur.

**Dört tüketici, tek kaynak:** çözücü, ön kontrol, analiz servisi, kabul ölçüm
betiği. Beşinci bir hesap yeri açma.

**Kabul:** Arka arkaya iki dönem yayınlandığında, ikincisinin sayaçları
birincinin yükünü görüyor. Aynı dönemin iki yayınlanmış sürümü varsa yalnız
sonuncusu sayılıyor.

---

## İş 2 — Çalışabilirlik oranı

**Dayanak:** SRS TD-6.

**Bu turun en kolay kaçırılan yeri.** Ufkun tamamında çalışabilir olmayan
personel — arada işe başlamış, uzun izne ayrılmış, aktifliği sona ermiş — tam
payla karşılaştırılırsa **kalıcı olarak hedefin altında görünür** ve sapması
hiçbir çizelgeyle kapatılamaz.

```
calisabilir_oran[p] = ufuk içinde p'nin çalışabilir olduğu gün / ufuk gün sayısı
pay[p] ← pay[p] · calisabilir_oran[p]
```

Çalışabilirlik personelin aktiflik tarih aralığından ve **tam gün kapsayan**
müsaitlik kayıtlarından hesaplanır. Oran `GecmisSayaclar` içinde hesaplanır —
ayrı bir yerde hesaplanması ufkun tanımını ikiye böler.

Bu, aynı hatanın **üçüncü biçimi**. İlk ikisi bu projede yaşandı: önce gece
talebi bulunan hiçbir noktada çalışamayan personel paydada sayılıyordu (K3'ün
4,60 ile kalmasının nedeni), sonra erişilebilirliği kısıtlı havuz tek ortalamaya
vuruluyordu (K3'ün 34 ile kalmasının nedeni). Üçünde de ölçü, kapatılamayan bir
sapma raporlayarak ayırt ediciliğini kaybediyor.

**Kabul:** Ufkun ortasında işe başlamış bir personelin payı, tam dönem çalışan
bir personelin payının yaklaşık yarısı. Ulaşılabilirlik teşhisi "her havuz hedefe
erişebiliyor" demeye devam ediyor.

---

## İş 3 — S2, S3, S4 kümülatif ufka geçer

**Dayanak:** SRS TD-6, 4.3.

**Yük ile hedef birlikte ölçeklenir:**

```
gece_yuku[p]  = geçmiş_gece[p] + dönem içi gece saati
pay_gece[p]   = ( geçmiş gerçekleşen gece saati + dönem gece talebi )
                erişebilenler arasında bölünüp p'nin payları toplanarak,
                sonra calisabilir_oran[p] ile ölçeklenerek
```

Dönem içi yükü ufuk boyunca hesaplanmış bir payla karşılaştırma — kişiyi hiç
yapmadığı bir işin hesabını verirken göstermiş olursun.

Geçmiş için **talep değil gerçekleşen saat** kullanılır: geçmiş dönemlerin talep
tanımları o günden bu yana değişmiş olabilir; elimizdeki kesin bilgi kimin ne
kadar çalıştığıdır.

Geçmiş yük **karar değişkeni değil sabit terimdir**; sapma ifadelerinde dönem içi
toplama eklenen bir sayıdır.

Erişilebilirlik geçmiş için de **bugünkü yetkinlik tanımından** alınır; geçmişte
kimin nerede çalışabildiği kayıt altında değil. Yaklaşıklık bilinçli.

**Kabul:** İlk dönemde ağır gece yükü alan personel, ikinci dönemde daha az gece
alıyor. Bunu doğrudan gösteren bir test yaz — iki dönemi ardışık çözüp aynı
kişinin yükünü karşılaştıran.

---

## İş 4 — H10'un devri türetilir

**Dayanak:** SRS TD-6, H10.

Yasal ufuk adalet ufkundan **ayrıdır**: ısıtma penceresini ve personel kaydındaki
devir bakiyesini kapsar. Aynı servisten geçer ama farklı parametreyle çağrılır.

`devir[p]` artık iki parçadan oluşur: yayınlanmış sürümlerden türetilen kota yılı
içi fazla çalışma **artı** personel kaydındaki devir alanı. İkincisi sistemin kota
yılının başından beri her şeyi bilmediği durumu karşılar; türetilen değerin yerine
geçmez, ona eklenir.

İki ufku tek çağrıda birleştirme — hangi kuralın hangisini kullandığı çağrı
yerine bakılmadan anlaşılmaz hâle gelir. Aynı gerekçe TD-14'te iki hafta kavramı
için de geçerli.

**Kabul:** Kota senaryosunda, önceki dönemde fazla çalışmış bir personelin kalan
kotası azalmış görünüyor ve yeni dönemde eşiği daha erken buluyor.

---

## İş 5 — Gösterim verisi: ardışık yayınlanmış dönemler

Kümülatif davranış, geçmişi olmayan bir veride görünmez.

- Ufkun gerçekten dolduğu bir geçmiş: arka arkaya **en az üç yayınlanmış dönem**.
- Bir personel ufkun ortasında işe başlamış olsun (İş 2'nin görünür olması için).
- Bir personel önceki dönemde fazla çalışmış olsun (İş 4'ün görünür olması için).

**Kabul:** Üçüncü dönem çözüldüğünde adalet sayaçları önceki iki dönemin yükünü
görüyor ve bu Analiz ekranında okunabiliyor.

---

## Turun bitiş kontrolü

- [ ] `pytest` tam takım geçiyor — ters dosya sırasında da
- [ ] `ruff`, `tsc -b`, `oxlint` temiz
- [ ] Çözücü–doğrulayıcı uyum testi 24/24
- [ ] **Kabul ölçümü koşuldu**; K1 süresi `PROGRESS_V2.md`'de. Geçmiş sayaçlar
      model kurma süresine ekleniyor — artış beklenir, eşiğin yarısını aşarsa dur
      ve bana söyle
- [ ] **K3 ölçümü ayrıca kaydedildi** — kümülatif ufuk sapmayı hangi yöne
      taşıdı? Tur 10'un kalibrasyonu bu sayıya bakacak
- [ ] Ulaşılabilirlik teşhisi hâlâ "her havuz hedefe erişebiliyor" diyor
- [ ] `git status` temiz, sır yok, `PROGRESS_V2.md` güncel

## Bu turda yapmayacakların

- **Analiz ekranının yeniden yapılması** — sıradaki tur. Bu turda ekrana yalnızca
  kümülatif değerlerin okunabilmesi kadar dokun.
- Ağırlık kalibrasyonu — T-07 ve T-08 biliniyor, Tur 10'un işi. Ağırlıklara
  dokunma; K3 bu turda da geçmeyebilir ve bu **beklenen** bir durum.
- Excel çıktısının biçimi — ayrı bir yönergeyle gelecek.
- Sunucuya dağıtım.
