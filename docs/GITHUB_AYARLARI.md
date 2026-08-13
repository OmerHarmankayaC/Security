# GitHub Deposu — Ayar Önerileri

Depoya erişimim yok (private görünüyor), bu yüzden ayarları siz uygulayacaksınız.

## 1. Önce karar: public mi?

Depo public olacaksa, `docs/` altındaki dört kanonik doküman bir tesisin güvenlik
personeli düzenini anlatıyor: kadro büyüklükleri, saat başına kaç kişi bulunduğu,
hangi havuzun kırılgan olduğu, izin dönemlerinde nerelerin açık kaldığı. Sayılar
temsili olsa bile yapı gerçek.

Üç seçenek:

- **Private kalsın** — en güvenli. Portfolyoda "özel depo, talep üzerine
  gösterilir" diye anılır.
- **Public olsun, dokümanlar çıksın** — kod ve README kalır, `docs/` `.gitignore`
  edilir. Ama proje değerinin önemli kısmı dokümantasyon disiplininde; kaybı
  büyük.
- **Public olsun, sayılar genelleştirilsin** — kurum adı anılmaz, kadro ve talep
  rakamları "örnek senaryo" olarak yeniden yazılır.

Mentöre sormadan public yapmayın. Bir sonraki mentör görüşmesinde bu da gündeme
girebilir.

## 2. Depo adı

`Security` çok jenerik ve içeriği anlatmıyor; GitHub aramasında da kaybolur.
Öneri: **`vardis`** veya **`vardis-shift-scheduler`**.

GitHub yeniden adlandırmada eski adresten yönlendirme yapar, yerel deponuzun
`remote` adresini güncellemeniz yeterli:

```bash
git remote set-url origin https://github.com/OmerHarmankayaC/vardis.git
```

## 3. About açıklaması

Ayarlar → About (sağ üstteki dişli):

> Hour-level shift scheduling decision support system built with OR-Tools CP-SAT,
> FastAPI and React — produces a schedule even when staffing is short and shows
> exactly where the gap is.

## 4. Website alanı

`https://vardiya.omerharmankaya.com`

Not: canlı sistem giriş istiyor, ziyaretçi giriş ekranını görür. Portfolyo
açısından bu sorun değil (çalışan bir sistem olduğunu gösteriyor) ama README'de
"sign-in required" yazması ziyaretçiyi şaşırtmaz.

## 5. Topics

```
constraint-programming   or-tools   cp-sat   scheduling
optimization             fastapi    react    typescript
postgresql               python     operations-research
decision-support
```

## 6. README

`README_GITHUB.md` içeriğini deponun kökündeki `README.md` olarak koyun.
İngilizce — GitHub içeriklerinin İngilizce olması kararına uygun.

Kurum adı **bilinçli olarak anılmadı**; eklemek isterseniz kolay, ama önce
1. maddedeki kararı verin.

### Eklenecek: ekran görüntüleri

README'nin en zayıf yanı görsel olmaması. `docs/gorseller/` altına üç ekran
görüntüsü koyup README'ye gömün:

1. Çizelge ekranı (çözülmüş bir dönem)
2. Çözüm ekranı (ceza dökümü görünürken)
3. Analiz ekranı (adalet dağılımı)

Markdown'da:

```markdown
![Schedule view](docs/gorseller/cizelge.png)
```

Görselleri Tur 6'dan sonra almak daha iyi — saat ızgarası devreye girince ekran
projenin asıl özelliğini gösterecek.

## 7. Depo hijyeni

- **`.gitignore`** — `.env`, `.venv/`, `node_modules/`, `__pycache__/`,
  `*.db` kontrol edin.
- **Sır taraması** — depo public olacaksa önce geçmişi tarayın. Sırlar hiç
  commit'lenmediyse sorun yok, ama bir kez girdiyse geçmişten temizlenmesi
  gerekir (`git log -S` ile arayabilirsiniz).
- **Varsayılan dal** — `main`.
- **Lisans** — portfolyo deposu için MIT yeterli; kurumsal bir iş olduğu için
  lisans koymamak da savunulabilir. Lisanssız depo "tüm hakları saklı" demektir.
- **Dallar** — `tur4-kural-katmani` birleştikten sonra silinebilir.

## 8. Sonraki adım

Tur 5 ve Tur 6 bittikten sonra README'nin "Status" bölümü güncellenecek: saatlik
modele geçiş tamamlandığında "current work" cümlesi değişmeli.
