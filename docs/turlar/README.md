# Geliştirme Turları

Bu klasör, geliştirmenin **nasıl yönlendirildiğinin** kaydıdır: her turun
başında verilen görev tanımı ve sırada bekleyen işlerin listesi.

**Buradaki dosyalar kanonik doküman DEĞİLDİR.** Tek gerçek kaynak `docs/`
kökündeki dört dokümandır — Proje Tanım Dokümanı, Yazılım Gereksinim
Belirtimi, Ürün Backlog'u ve Yazılım Tasarım Dokümanı. Bir turun görev
tanımı ile dokümanlar arasında bir çelişki varsa doküman geçerlidir; tur
dosyası o anda ne istendiğini gösterir, neyin doğru olduğunu değil.

Ayrı klasörde durmalarının nedeni de bu: kanonik dörtlünün yanında
durduklarında ikisi karışıyor ve bir tur dosyası kaynak sanılabiliyordu.

| Dosya | İçerik |
| --- | --- |
| `CLAUDE_CODE_PROMPTU_TUR1.md` | İkinci aşama, tur 1 — durdurma akışı ve kabuk |
| `CLAUDE_CODE_PROMPTU_TUR2.md` | İkinci aşama, tur 2 — doküman borçları ve test izolasyonu |
| `yapilacaklar.md` | Sıradaki işlerin ham listesi; turlar buradan seçiliyor |

Turların ne zaman ve nasıl uygulandığı [`PROGRESS.md`](../../PROGRESS.md)
dosyasında, alınan kararlar ise Ürün Backlog'unun karar günlüğünde.
