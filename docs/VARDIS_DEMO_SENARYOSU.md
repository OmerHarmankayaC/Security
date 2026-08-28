# VARDİS Demo Senaryosu

**Sürüm 1.0 · 27.08.2026 · Ömer HARMANKAYA**

| Ad | Tarih | Değişiklik Nedeni | Sürüm |
| --- | --- | --- | --- |
| Ömer HARMANKAYA | 27.08.2026 | İlk sürüm: gösterim ortamının veri kurgusu, üretim ilkeleri ve kabul ölçütleri tanımlandı | 1.0 |

## 1. Amaç

Bu doküman, VARDİS'in gösterim (demo) ortamında bulunacak **verinin** tanımıdır.
Gösterim ortamı artık yalnız mentör sunumu için değil, deponun ve ürünün genel
gösterimi için de kullanılacağından, veri kurgusu tekrarlanabilir ve yazılı
olmak zorundadır.

Kapsam veridir. Kural kataloğu, ağırlıklar, gereksinimler ve tasarım bu
dokümanın kapsamı dışındadır; onların kaynağı SRS ve SDD'dir. Demo verisi
kuralları değiştirmez, kurallara uyar.

## 2. İlkeler

1. **Kurgusaldır.** Hiçbir kayıt gerçek bir kuruma veya kişiye ait değildir.
   Kurum adı, kurum kısaltması ve gerçek personel adı hiçbir alanda,
   hiçbir dosyada geçmez.
2. **Üretilir, elle girilmez.** Tek üretici `scripts/demo_veri_uret.py`'dir.
   Veri üzerinde arayüzden yapılan elle düzeltme kalıcı sayılmaz; bir sonraki
   sıfırlamada kaybolur.
3. **Tarihler görecelidir.** Çalıştırma günü referanstır. Sabit takvim
   tarihleri yalnız resmî tatil listesinde bulunur. Böylece demo altı ay sonra
   da "canlı" görünür.
4. **Deterministiktir.** Sabit tohum kullanılır: aynı gün iki kez çalıştırılan
   betik aynı personeli, aynı izinleri, aynı tercihleri üretir.
   **Tek istisna atamalardır**; CP-SAT paralel arama yürüttüğü için çözüm
   çıktısı çalıştırmalar arasında farklılaşabilir.
5. **Veri kurala uyar.** Geçmiş ve güncel çizelgeler gerçek çözücüyle
   üretilir. Uydurulmuş atama, doğrulayıcıdan geçmeyen bir çizelge demektir ve
   Analiz ekranını yalancı çıkarır.
6. **Sayıları güzelleştirmek için kural ayarlanmaz.** Demo çıktısı beğenilmezse
   değiştirilecek şey senaryodur (kadro, izin dağılımı, dönem sayısı), kural
   parametresi veya ağırlık değildir.

## 3. Kurgu

Kesintisiz çalışan bir tesisin güvenlik biriminin çizelgesi. Tesiste iki blok
bulunur, güvenlik hizmeti kesintisizdir, devriye görevi yoktur. Kurgu
Charter 2.5'teki yapının birebir aynısıdır; demo bu yapıyı değiştirmez, doldurur.

## 4. Tanım verisi

### 4.1 Yetkinlik

| Ad | Açıklama |
| --- | --- |
| Güvenlik Görevi | Güvenlik noktasında görev alabilmenin ön koşulu |
| Vardiya Şefi | Vardiya şefliği noktasının ön koşulu; taşıyıcısı Güvenlik Görevi yetkinliğini de taşır |

### 4.2 Bina ve görev noktası

Bina kayıtları `A Blok` ve `B Blok`'tur. Görev noktaları tesis genelidir,
`bina_id` boştur (Charter 2.5).

| Görev Noktası | Ön koşul yetkinlik |
| --- | --- |
| Vardiya Şefliği | Vardiya Şefi |
| Güvenlik | Güvenlik Görevi |

### 4.3 Personel

Toplam **40 personel**: 9 vardiya şefi, 31 güvenlik görevlisi. Kadro, kabul
ölçümünün referans örneğiyle aynı ölçektedir (SDD 3.4.2), böylece demo ile
ölçüm kaydı aynı büyüklüğü anlatır.

| Özellik | Değer |
| --- | --- |
| Ad soyad | Betikteki sabit kurgusal ad havuzundan, tekrarsız |
| Sicil no | `D-1001` … `D-1040` |
| Haftalık hedef saat | 37 personel 45, 3 personel 30 (kısmi zamanlı) |
| Sabit vardiya tipi | Hiçbirinde tanımlı değil |

Üç sınır durumu kasıtlı olarak kadroya konur, çünkü bunlar sistemin en kolay
kaçırılan davranışını (çalışabilirlik oranı, SDD 5.9) görünür kılar:

- bir personel **üç hafta önce** işe başlamıştır (`aktif_baslangic` geçmiş
  ufkun ortasında),
- bir personel **geçen ay ayrılmıştır** (`aktif_bitis` dolu),
- kısmi zamanlı üç personel, adil payın orantılı hesaplandığını gösterir.

### 4.4 Talep

Charter 2.5'teki talep tablosu, zaman aralığı kayıtları olarak:

| Görev Noktası | Gün tipi | Aralık | Gereken |
| --- | --- | --- | --- |
| Vardiya Şefliği | her gün tipi | 00.00 – 24.00 | 1 |
| Güvenlik | hafta içi | 08.00 – 24.00 | 9 |
| Güvenlik | hafta içi | 00.00 – 08.00 | 3 |
| Güvenlik | hafta sonu / tatil | 00.00 – 24.00 | 3 |

Haftalık toplam 1.152 kişi-saattir. Bu talep 40 kişilik kadroyla rahatça
karşılanır; demo temel hâlinde **kapsama açığı vermez**. Açık, 6.3'teki
sıkışık taslakta bilerek üretilir.

### 4.5 Özel gün

Demo penceresine düşen Türkiye resmî tatilleri betikte sabit liste olarak
tutulur ve yalnız pencereye düşenler yazılır.

### 4.6 Kural kataloğu

Katalog, üretim ortamındakiyle **birebir aynı** kurulur: aynı kural kimlikleri,
aynı parametreler, aynı ağırlıklar, aynı aktiflik durumları (S1f aktif,
S6b pasif). Ölçüm ortamıyla üretim ortamı arasında geçmişte oluşan katalog
farkı burada tekrar edilmemelidir; katalogun kaynağı SRS bölüm 4'tür.

## 5. Girdi verisi

### 5.1 Müsaitlik

Her dönemde kadronun **yüzde 8 ile 12'si** izinlidir. Tipler karışıktır:
yıllık izin, rapor, eğitim, mazeret. Dilim çoğunlukla tam gün, birkaç kayıt
yarım gündür.

Geçmiş dönemlerden **ikisi izin dalgası** taşır (kadronun yaklaşık dörtte
biri aynı hafta izinli). Bu iki dönem, kota kartının dolmasını sağlayan
fazla çalışmayı üretir.

### 5.2 Tercih

Güncel ve gelecek dönem için yaklaşık 25 tercih kaydı bulunur. Durum dağılımı
üç değeri de kapsar: onaylanmış, reddedilmiş (ret gerekçesi dolu), beklemede.
Bir kısmında çalışan notu doludur. Aynı personele aynı gün ikinci tercih
yazılmaz (FR-9.6).

## 6. Dönemler ve sürümler

Bugünün içinde bulunduğu hafta `D0` kabul edilir.

| Dönem | Durum | İçerik |
| --- | --- | --- |
| D-12 … D-1 (12 haftalık dönem) | Yayınlandı | Gerçek çözücüyle üretilmiş, doğrulayıcıdan sıfır ihlalle geçen çizelgeler. İkisi izin dalgalı |
| D0 (bu hafta) | Yayınlandı | Güncel çizelge; çalışan panelinin ve Özet ekranının gösterdiği dönem |
| D+1 (gelecek hafta) | Taslak, iki sürüm | Sürüm 1 çözücü çıktısı; sürüm 2 üzerinde birkaç elle değişiklik yapılmış. Sürümler ve Karşılaştır ekranı bu ikisiyle dolar |
| D+2 | Taslak, sıkışık senaryo | Kadronun dörtte biri izinli; çözüm kapsama açığıyla tamamlanır |

Geçmiş dönem sayısı adalet ufkunun (90 gün) tamamını dolduracak biçimde
seçilmiştir; Analiz ekranındaki ufuk anahtarı ancak böyle iki farklı sonuç
gösterir.

Geçmiş dönemler çözülürken zaman limiti kısa tutulabilir (60 saniye); bu
dönemler ölçüm değil gösterim verisidir. Kabul ölçümü ayrı veritabanında
alınmaya devam eder.

## 7. Hesaplar

Her rol için birer demo hesabı, çalışan rolü için iki hesap açılır: biri kotası
dolmaya yaklaşmış personele, diğeri ortalama yüklü bir personele bağlıdır.
Böylece çalışan paneli iki farklı tabloyla gösterilebilir.

Parolalar ortam değişkeninden okunur. Parola ne bu dokümanda, ne betikte, ne
depoda bulunur.

## 8. Ekran başına hedeflenen görüntü

Demo verisi aşağıdakilerin hepsini aynı anda gösterebilmelidir. Bu liste aynı
zamanda ekran görüntüsü çekim listesidir.

| Ekran | Görünmesi gereken |
| --- | --- |
| Özet | Yayınlanmış güncel dönem, dolu sayılar |
| Çizelge (gün) | Dolu ızgara, en az bir gece yarısını aşan blok, en az bir kilitli atama |
| Çizelge (hafta) | 40 personelin haftalık şeridi |
| Çözüm | Tamamlanmış iş kaydı, ceza dökümü dolu |
| Analiz (dönem) | Kapsama tam, adalet kartında iki yönlü sapma |
| Analiz (90 gün) | Dönemden farklı sayılar; kümülatif değişim göstergesi dolu |
| Analiz (kota) | En az bir personel yıllık kotasının yarısının üstünde |
| Sürümler | En az iki sürüm ve aralarında okunabilir bir fark |
| Sıkışık taslak | Kapsama açığı, gün başlığında açık rozeti |
| Çalışan paneli | Dolu dönem özeti, adil pay kıyası, üç durumdaki tercihler |

## 9. Kabul ölçütleri

1. Yayınlanmış her dönem, doğrulayıcıdan **sıfır zorunlu kural ihlaliyle**
   geçer.
2. Analiz ekranı 90 günlük ufukta boş dönmez ve dönem ufkundan farklı sayı
   üretir.
3. Kota kartında en az bir personel yıllık kotanın yarısının üstündedir.
4. Temel hâlde (D-12 … D0) kapsama açığı yoktur; D+2 taslağında vardır.
5. Betik iki kez çalıştırıldığında tanım ve girdi verisi birebir aynıdır
   (atamalar hariç, madde 2.4).
6. Veritabanının hiçbir metin alanında kurum adı, kurum kısaltması veya gerçek
   kişi adı geçmez.

## 10. Sıfırlama

Gösterim ortamı herkese açık olacaksa veri her gece yeniden üretilir.
Sıfırlama, veri temizliği kilidini (`VERI_TEMIZLIGINE_IZIN`) geçici olarak
açan tek bir zamanlanmış görevdir; kilit kalıcı olarak açık bırakılmaz.

Sıfırlama hesapları da yeniden kurar. Geçmişte kabul ölçümü betiğinin personel
tablosunu temizlemesi, `kullanici.personel_id` bağı yüzünden çalışan
hesaplarını düşürmüştü; sıfırlama akışı bu sırayı açıkça ele almalıdır.

## 11. Bilinçli olarak dışarıda bırakılanlar

- Gerçek kuruma ait hiçbir veri, ad veya sayı.
- Kural ağırlıklarının demo görüntüsü için ayarlanması.
- Kabul ölçümünün demo veritabanında alınması; ölçüm ayrı veritabanında kalır.
- Yük testi ölçeğinde veri (40 personel referans ölçektir, stres ölçeği değil).
