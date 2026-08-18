# Claude Code — Sürüm 2, Tur 8: Dışa Aktarma

## Bağlam

Kullanıcı sistemi gerçek kullanımda denedi. Dışa aktarmayla ilgili iki şey
bildirdi:

1. **Çizelge dışa aktarması çizelgeyi vermiyor** — yalnızca talep açığını CSV
   olarak veriyor. İstenen, çizelgenin kendisinin okunabilir bir Excel dosyası
   olarak çıkması.
2. **Analiz için diyagramlı bir çıktı yok** — hem ham veri hem düzenli bir özet
   isteniyor.

Bunlardan önce kapatılması gereken bir borç var: kapsama açığı kayıtları hâlâ
tarih ve ofsetsiz saat taşıyor, dolayısıyla gece yarısını aşan bir açık aralığı
dosyada okunamaz.

### Doküman sürümleri — ilk işin bunları doğrulamak

| Doküman | Sürüm |
|---|---|
| `VARDIS_ProjectCharter.md` | 1.4 |
| `VARDIS_SRS.md` | **1.24** |
| `VARDIS_SDD.md` | **1.31** |
| `VARDIS_Backlog.md` | **1.21** |

Taşımıyorlarsa dur ve bana söyle.

### Okunacaklar

- SRS **FR-8.5, FR-8.7, FR-8.9** ve **7.2** (dosya yapıları — bu turun tanımı)
- SDD **5.8** (dışa aktarma servisi), **4.2.4** (`kapsama_acigi`, `fazla_kadro`)
- Backlog **B-23**

## Çalışma kuralları

- Dört kanonik dokümana **dokunmazsın**. Etki doğuran bir şey çıkarsa
  `PROGRESS_V2.md`'ye "DOKÜMAN BORCU" başlığı altında yaz.
- Tasarımdan sapma gerekiyorsa **önce nedenini söyle**, sonra uygula.
- Şema değişikliği yalnızca Alembic göçüyle.
- Git: `add`, `commit`, `tag` senin; `push` ve `remote` **asla**.
- `ruff`, `tsc -b`, `oxlint` temiz; her iş grubundan sonra commit.

---

## İş 1 — B-23: kapsama kayıtları zaman damgasına

**Turun ilk işi.** Dışa aktarma bu düzeltilmeden yapılamaz.

`kapsama_acigi` ve `fazla_kadro` tabloları bugün `tarih` (DATE) ve `baslangic` /
`bitis` (TIME) taşıyor. `atama` tablosu Tur 5'te zaman damgasına geçti, bu ikisi
geride kaldı.

- Alembic göçü: `tarih`, `baslangic`, `bitis` yerine `baslangic_zamani` ve
  `bitis_zamani` (TIMESTAMPTZ).
- **Mevcut kayıtlar dönüştürülmez, silinir.** Bu iki tablo bir çözümün
  çıktısıdır, kullanıcının girdiği veri değil; sürüm yeniden çözüldüğünde veya
  elle düzenlendiğinde doğru biçimde yeniden yazılır. Aynı karar Tur 3'te de
  verildi ve gerekçesi aynı: yanlış dönüşmüş bir açık kaydı hiç olmamasından
  kötüdür, çünkü rapora doğru gibi girer.
- Yazma yolu (`sapmalari_yenile` ve çözücü sonucu yazma) ile okuma yüzeyleri
  yeni alanlara uyarlanır. Aralık birleştirme yardımcısı korunur.

**Kabul:** Gece yarısını aşan bir açık aralığı (örneğin 22.00–02.00) tek kayıtta
duruyor ve hangi güne ait olduğu belirsiz kalmıyor.

---

## İş 2 — Çizelgenin Excel çıktısı

**Dayanak:** SRS FR-8.5, 7.2; SDD 5.8.

Üç sayfalı bir çalışma kitabı:

| Sayfa | İçerik |
|---|---|
| **Çizelge** | Personel × gün. Hücrede çalışma saatleri ve görev noktası kısaltması; hücre dolgusu saatin gün içindeki konumunu gösterir. Kapsama açığı bulunan günler işaretli |
| **Özet** | Personel başına toplam saat, gece saati, hafta sonu saati, fazla çalışma saati, kalan yıllık kota |
| **Ham veri** | Blok başına bir satır, ISO zaman damgalarıyla — CSV çıktısının aynısı |

Başlık bölümünde dönem, sürüm numarası, üretim tarihi, kapsama oranı ve toplam
açık bulunur.

**Renk tek başına bilgi taşımaz.** Saat aralığı hücrede metin olarak da yazılı ve
bir açıklama satırı dolgunun anlamını söylüyor. Renksiz basılan bir çıktı bilgi
kaybettirmemeli — ekrandaki renk bandı için konan kural burada da geçerli.

**CSV kalır.** İkisi birbirinin yerine geçmez: CSV başka bir sisteme veri taşır,
Excel masaya konur ve bakılır. Mevcut CSV çıktısını kaldırma.

---

## İş 3 — Analizin Excel çıktısı

**Dayanak:** SRS FR-8.9, 7.2.

| Sayfa | İçerik |
|---|---|
| **Özet** | Kapsama oranı, toplam ceza, hedef bazında ceza dökümü |
| **Adalet** | Personel başına gece saati, hafta sonu saati, toplam saat; her biri için kişiye düşen adil pay ve sapma. Grafikler bu sayfada |
| **Kapsama açıkları** | Gün, saat aralığı, görev noktası, eksik kişi sayısı |
| **Ham veri** | Yukarıdaki tabloların biçimlendirilmemiş hâli |

**Grafiklerin referans çizgisi kişiye düşen adil paydır**, havuz ortalaması değil.
Ortalamayı göstermek, S2'nin açıkça reddettiği ölçüyü dosyaya taşımak olur — aynı
hata ekranda bir kez yapıldı ve Tur 6'da düzeltildi.

---

## İş 4 — Dışa aktarma tek serviste

**Dayanak:** SDD 5.8.

`DisaAktarmaServisi` verisini **mevcut okuma yüzeylerinden** alır: çizelge
atamalardan, analiz `AnalizServisi`'nden, açıklar kapsama açığı kayıtlarından.
**İkinci bir hesap yapmaz.**

Kendi toplamlarını hesaplayan bir dışa aktarma, aynı sayının ekranda ve dosyada
farklı çıkması demektir. Blok geometrisi ve saat biçimlemesi de aynı yardımcıdan
geçsin — saat metni biçimleyicisinin üç kopyası bir kez hataya yol açtı.

Uç noktalar dosyayı doğrudan döndürür; ayrı bir iş kuyruğu kurma. Bir dönemdeki
atama sayısı birkaç yüz.

**Kabul:** Excel'deki kapsama oranı, toplam saat ve adil pay değerleri Analiz
ekranındakiyle **birebir aynı**. Bunu doğrulayan bir test yaz.

---

## Turun bitiş kontrolü

- [ ] `pytest` tam takım geçiyor — ters dosya sırasında da
- [ ] `ruff`, `tsc -b`, `oxlint` temiz; frontend testleri geçiyor
- [ ] Göç sıfırdan çalışıyor, geri alma yazılmış ve denenmiş
- [ ] Ekran ile dosyanın aynı sayıyı verdiğini gösteren test
- [ ] Gece yarısını aşan açık aralığının dosyada okunabildiğini gösteren test
- [ ] `EK_B_UC_NOKTALAR.md` yeniden üretildi (iki yeni uç nokta)
- [ ] `git status` temiz, sır yok, `PROGRESS_V2.md` güncel

## Kullanıcı dosyaları kendi açacak

Üretilen iki Excel dosyasını kullanıcı açıp bakacak. Turun sonunda örnek
dosyaları nereye bıraktığını yaz. Özellikle şunlar gözle bakılmalı: hücre
dolgusunun okunabilirliği, sütun genişliklerinin saat metnini kesip kesmediği,
grafiklerin referans çizgisinin görünürlüğü.

## Bu turda yapmayacakların

- **Analiz ekranının kendisinin iyileştirilmesi.** Kullanıcı bunu istedi ama
  neyin eksik olduğu henüz tanımlı değil; ayrı bir turda ele alınacak. Bu turda
  ekrana dokunma, yalnızca dosya üret.
- PDF çıktı — Excel birincil biçim olarak seçildi.
- `GecmisSayaclar` ve kümülatif adalet (Tur 9).
- Ağırlık kalibrasyonu — T-07 ve T-08 biliniyor, ağırlıklara dokunma.
- Sunucuya dağıtım.
