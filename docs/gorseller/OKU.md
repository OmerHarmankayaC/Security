# Görseller — README'ye gömülecek ekran görüntüleri

README bu dizindeki beş dosyaya isimle bağlıdır. Dosya adları **birebir** bu
olmalı, yoksa README'de kırık görsel çıkar:

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

## Yerleştirdikten sonra

README'deki beş `![...]` satırı kendiliğinden çalışır; başka değişiklik
gerekmez. Kontrol için README'yi bir markdown önizleyicide aç ya da GitHub'a
gönderdikten sonra bak.
