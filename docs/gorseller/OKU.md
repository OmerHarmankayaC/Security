# Görseller — README'ye gömülecek gezinti kaydı ve ekran görüntüleri

README bu dizindeki yedi dosyaya isimle bağlıdır. Dosya adları **birebir** bu
olmalı, yoksa README'de kırık görsel çıkar:

| Dosya | Ne göstermeli |
|---|---|
| `gezinti.gif` | Gezinti kaydı, README'de gömülü olan. **8 MB altında kalmalı**; GitHub daha büyüğünü de gösterir ama sayfayı bekletir |
| `gezinti.mp4` | Aynı kaydın videosu; GIF'ten keskin ve küçüktür, README'den bağlantıyla verilir |

Ekran görüntüleri:

| Dosya | Ne göstermeli |
|---|---|
| `gun-izgarasi.png` | Gün ızgarası: bir günün saat ekseninde talep ve atamalar; **sıkışık dönemden**, çünkü kapsama şeridi ve gün başlığındaki açık rozetleri aracın ne işe yaradığını dolu bir günden iyi anlatır |
| `hafta-seridi.png` | Hafta şeridi: **yayınlanmış dönemden**; şeridin işi kırk kişinin haftasını bir bakışta göstermek ve bu ancak dolu bir haftada okunur |
| `cozum-ekrani.png` | Çözüm ekranı: ön kontrol çıktısı — yapısal engel ile yalnızca aramayı daraltan uyarının ayrıldığı hâl |
| `analiz-ekrani.png` | Analiz ekranı: **yayınlanmış dönemden**; kapsama, adalet dağılımı ve ceza dökümü. Sıkışık dönemde şef havuzunun tamamı izinli olduğu için adalet tablosu dejenere görünür (herkes 0 saat) |
| `calisan-paneli.png` | Çalışan paneli: sıradaki vardiya, dönem görünümü ve vardiya listesi |

**Çözüm ekranı açılışta BOŞTUR** — iş kartı yalnızca yürümekte olan ya da o
oturumda sonuçlanmış bir iş için çizilir, geçmiş işler için değil. Çözüm
başlatmak demo veritabanına yeni bir sürüm yazar; onun yerine **Ön Kontrol**
koşturulur, salt okunurdur.

## Alırken

- **Genişlik 1280–1600 px.** Daha darı okunmuyor, daha genişi README'de
  küçülürken ayrıntıyı kaybediyor.
- **Gerçek veriyle al, boş ekranla değil.** Boş bir ızgara aracın ne yaptığını
  anlatmaz. Demo verisi için: `python scripts/demo_veri_uret.py --reset`
- **Gerçek isimler görünüyorsa demo verisi kullan.** Depo halka açık olacak;
  kurum personelinin adı ekran görüntüsünde durmamalı.
- PNG, kayıpsız. Ekran görüntüsü JPEG'de metin kenarlarını bulandırır.

## Gezinti kaydını yeniden almak

Betik: [`scripts/gezinti_kaydi.mjs`](../../scripts/gezinti_kaydi.mjs).

```bash
# API ve ön yüz gösterim kipinde koşarken, ayrı bir kabukta:
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --headless=new --remote-debugging-port=9222 --disable-gpu \
  --hide-scrollbars --force-device-scale-factor=1 about:blank &
P=<demo_idare parolasi> GUNCEL='<yayinlanmis donem>' \
  SIKISIK='<sikisik donem>' GELECEK='<taslakli donem>' \
  node scripts/gezinti_kaydi.mjs <cikti-dizini>
```

Dönem etiketleri ortamdan verilir çünkü demo verisi **bugüne göre** üretilir;
betiğe gömülselerdi bir sonraki sıfırlamadan sonra hiçbirini bulamazdı.

Kayıt headless Chrome'u CDP üzerinden sürer; kareler `Page.captureScreenshot`
**döngüsüyle** alınır, `startScreencast` ile değil — screencast yalnızca
öndeki sekmeye akıyor ve headless'ta hiç kare göndermedi. Kareler değişken
süreli bir listeyle (ffmpeg concat demuxer) birleştirilir; sabit kare hızı
varsayılsaydı iş yüküne göre uzayan aralıklar videoyu hızlandırıp yavaşlatırdı.

Sıra: giriş ekranı ve kimlik kutusu · özet · gün ızgarası · hafta şeridi ·
analiz (dönem, 90 gün ufku, kota kartı) · sürüm karşılaştırma · çalışan paneli.

**Kayıtta yazma yoktur.** Çözüm başlatılmaz, kaydedilmez, silinmez; tek yazma
benzeri eylem giriştir. Ön kontrol serbesttir, salt okunurdur.

Kadraja metinle kaydırılır, pikselle değil — kart etiketleri `buyukHarf()` ile
büyütüldüğü için arama **Türkçe katlamayla** yapılır: düz `toLowerCase()`
"YILLIK" ile "yıllık"ı eşleştiremez ve kota kartı ilk denemede tam bu yüzden
kadraja hiç girmedi.

Kabul: hiçbir karede kurum adı, gerçek kişi adı, IP ya da alan adı görünmemeli.
Kimlik kutusundaki parolaların okunaklı olması sorun değildir; parolalar
gösterim ortamına özgüdür ve gecelik sıfırlamayla birlikte anlamlarını korur.

## Yerleştirdikten sonra

README'deki `![...]` satırları kendiliğinden çalışır; başka değişiklik
gerekmez. Kontrol için README'yi bir markdown önizleyicide aç ya da GitHub'a
gönderdikten sonra bak.
