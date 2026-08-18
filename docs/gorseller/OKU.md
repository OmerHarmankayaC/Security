# Görseller — README'ye gömülecek ekran görüntüleri

README bu dizindeki üç dosyaya isimle bağlıdır. Dosya adları **birebir** bu
olmalı, yoksa README'de kırık görsel çıkar:

| Dosya | Ne göstermeli |
|---|---|
| `gun-izgarasi.png` | Gün ızgarası: bir günün saat ekseninde talep ve atamalar; tercihen kapsama açığı olan bir gün, çünkü aracın ne işe yaradığını en iyi o anlatır |
| `cozum-ekrani.png` | Çözüm ekranı: koşan ya da durdurulmuş bir iş, ilerleme ve karar düğmeleri görünür hâlde |
| `analiz-ekrani.png` | Analiz ekranı: kapsama, kota kartı, adalet dağılımı ve ceza dökümü; ufuk anahtarı görünür olsun |

## Alırken

- **Genişlik 1280–1600 px.** Daha darı okunmuyor, daha genişi README'de
  küçülürken ayrıntıyı kaybediyor.
- **Gerçek veriyle al, boş ekranla değil.** Boş bir ızgara aracın ne yaptığını
  anlatmaz. Demo verisi için: `python scripts/demo_veri_uret.py --reset`
- **Gerçek isimler görünüyorsa demo verisi kullan.** Depo halka açık olacak;
  kurum personelinin adı ekran görüntüsünde durmamalı.
- PNG, kayıpsız. Ekran görüntüsü JPEG'de metin kenarlarını bulandırır.

## Yerleştirdikten sonra

README'deki üç `![...]` satırı kendiliğinden çalışır; başka değişiklik
gerekmez. Kontrol için README'yi bir markdown önizleyicide aç ya da GitHub'a
gönderdikten sonra bak.
