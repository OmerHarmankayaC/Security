# Çalışan Paneli Düzeltmesi — Tasarım

Tarih: 2026-08-17 · Dal: `tur8-disa-aktarma` · Durum: onay bekliyor

Tur 10 (analiz ekranı, kalibrasyon, kapanış ölçümü) eş zamanlı yürüyor. Bu
belge **yalnız çalışan panelini** kapsar; analiz ekranına dokunulmaz.

## Neden

Yönetici analizi Tur 10'da ufuk seçebilir hâle geldi (`hesapla(surum_id, ufuk)`,
`analiz_servisi.py:186`). Çalışan paneli o değişikliği görmedi: özet hâlâ tek
dönemden hesaplanıyor. Aynı kişinin gece saati iki ekranda iki farklı sayı
gösteriyor. Denetimde bunun yanında tercih formunda doğrulama boşlukları ve
ızgarada okunurluk sorunları da çıktı.

Charter 1.5: kümülatif sapma **kabul kriteri değil göstergedir**. Bu yüzden
çalışan panelinin varsayılanı dönemdir; doksan günlük görünüm ikincildir.

## Bulgular

| # | Yer | Sorun |
|---|---|---|
| 1 | `calisan_servisi.py:189` | `hesapla(surum_id)` — ufuk hep `donem`, yönetici tarafıyla ayrışıyor |
| 2 | `calisan_servisi.py:205-219` | Ekip ortalaması düz aritmetik; adalet ufkunda pay `calisabilir_oran` ile ölçekli |
| 3 | `DonemOzetimEkrani.tsx:10` | `ESIK = 0.5` saat — doksan günlük sayılarda herkesi "sapmış" gösterir |
| 4 | `TercihlerimEkrani.tsx:171` | Tarih alanında `min`/`max` yok; dönem dışı gün 400 dönüyor |
| 5 | `TercihlerimEkrani.tsx` | Açık dönem yokken form yine açık, her gönderim hataya gidiyor |
| 6 | `models/girdi.py:49` | `(personel_id, tarih)` tekilliği yok — aynı güne çelişkili iki tercih durabiliyor |
| 7 | `TercihlerimEkrani.tsx:60` | Başarılı gönderimde onay yok |
| 8 | `VardiyalarimEkrani.tsx:184` | Nokta adı 3 harfe kırpılıyor; aynı harflerle başlayan noktalar ayrışmıyor |
| 9 | `VardiyalarimEkrani.tsx:224` | Lejant kutusu ızgaradaki 3px şeritle aynı biçimde değil |
| 10 | `CalisanShell.tsx:42` | 375px'te yetkinlik listesi sıkışıyor; sekme şeridi taşarsa kaydırma yok |
| 11 | `screens/calisan/` | Üç ekranın da frontend testi yok |

Doğrulanan ama **sorun olmayan**: başlangıç = bitiş "tüm gün" demektir
(`zaman_araligi.py:39`). Davranış doğru, yalnız arayüzde görünmüyor — bölüm 3'te
etiketle çözülür.

## Tasarım

### 1. Özet ayrı uç noktaya taşınır

`ozet`, `VardiyalarimOku` yükünden çıkar. Yeni uç nokta:

```
GET /api/calisan/ozetim?ufuk=donem|adalet   → DonemOzetiOku
```

`ufuk` doğrudan `AnalizServisi.hesapla(surum_id, ufuk)`e geçer. İkinci bir
formül yazılmaz: tanım analiz servisinde tek yerde kalır, iki yüzey ayrışamaz.

Yan kazanç: bugün panelin **her** açılışı bir tam `hesapla()` ödüyor, çalışan
yalnız Vardiyalarım'a baksa bile. Ayrışınca maliyet sekmeye taşınır.

Ekranda iki durumlu seçici: **Bu Dönem** (varsayılan) | **Son 90 Gün**. Seçim
değişince yeniden çekilir. Başlık ve karşılaştırma cümlesi seçilen ufku söyler —
hangi ufkun okunduğu ekranda görünmeden sayı yanlış okunur (SDD 6.3.4'ün analiz
ekranı için koyduğu kuralın aynısı).

### 2. Kıyas ve eşik

Adalet ufkunda kıyas, `calisabilir_oran` ile ölçeklenmiş hedef pay üzerinden
yapılır — dönemin yarısında izinli olan biri tam ekip ortalamasıyla
kıyaslanamaz. Oran analiz servisinden okunur, panelde yeniden hesaplanmaz.

Eşik mutlak yerine göreli: **ekip ortalamasının %5'i, en az 0,5 saat**. Dönem
ufkunda bugünkü davranışa yakın kalır, doksan günde anlamlı olur.

### 3. Tercihlerim formu

- Tarih alanı açık dönemle sınırlanır: `min = max(bugün, dönem başlangıcı)`,
  `max = dönem bitişi`.
- Açık dönem yoksa form yerine bilgi kartı ("Şu anda tercihe açık bir dönem
  yok"), gönderim düğmesi hiç çizilmez.
- Zaman aralığı seçicisinde seçilen aralığın kaç saat sürdüğü yazılır; başlangıç
  = bitiş seçildiğinde "tüm gün (24 saat)" görünür.
- Başarılı gönderimde satır içi onay; hata mesajı forma yakın durur.

### 4. Aynı güne ikinci tercih — üstüne yazma

`(personel_id, tarih)` üzerine tekillik kısıtı + alembic göçü.

Servis kuralı:
- Mevcut tercih **BEKLEMEDE** ise yeni bildirim onun yerine geçer (güncelleme).
- Mevcut tercih **ONAYLANDI/REDDEDILDI** ise 409 — yönetici kararı sessizce
  silinmez; kullanıcıya "bu gün için kararlanmış bir tercihin var, yöneticine
  başvur" denir.

Göç sırası: (a) kopyaları sayan salt-okuma sorgusu, sonucu göç günlüğüne yazar;
(b) her `(personel_id, tarih)` için en büyük `tercih_id` kalır, eskiler silinir
ve silinen her satır günlüğe yazılır; (c) tekillik kısıtı eklenir. Dağıtımdan
önce aynı sayım sunucuda elle çalıştırılır ve sonucu `PROGRESS_V2.md`'ye
geçer — kaç satırın gideceği önceden bilinmeden göç uygulanmaz.

### 5. Görsel

- `lib/metin.ts`'e `benzersizKisaltma(adlar: string[]): Map<string, string>` —
  aynı harflerle başlayan nokta adlarını ayrıştıran deterministik kısaltma.
  Izgara bunu kullanır, `slice(0, 3)` kalkar.
- Lejanttaki "Değişen gün" işareti ızgaradaki 3px şeritle aynı biçime çevrilir.
- Üst çubukta yetkinlik listesi 375px'te taşmaz; sekme şeridi kaydırılabilir.

### 6. Testler

Frontend (şu an sıfır):
- `DonemOzetimEkrani.test.tsx` — ufuk değişimi, havuz dışı metinler, göreli eşik
- `TercihlerimEkrani.test.tsx` — kapalı dönem, tarih sınırları, 409, onay
- `VardiyalarimEkrani.test.tsx` — kısaltma ayrışması, kaldırılan gün satırı

Backend `test_calisan_api.py`:
- `/api/calisan/ozetim` iki ufukta
- tekillik: beklemedeki tercihin üstüne yazma, kararlanmışta 409
- kapalı tercih penceresi

## Kapsam dışı

- Analiz ekranı ve `analiz_servisi` (Tur 10 eş zamanlı yürüyor)
- Tercih silme/geri çekme ucu — üstüne yazma bunu gereksiz kılıyor
- Dönem Özetim'e dağılım/min-maks bandı
- Dört kanonik doküman; etki doğarsa `PROGRESS_V2.md`'ye doküman borcu yazılır
