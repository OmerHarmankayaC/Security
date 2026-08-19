# VARDİS — Claude Code için çalışma notu

Vardiya çizelgeleme karar destek aracı. CP-SAT tabanlı çözücü + FastAPI +
React. Bu dosya oturum başında okunur; projenin tanıtımı `README.md`'dedir.

## Düzen

```
backend/app/kurallar/    zorunlu (H*) ve esnek (S*) kural sınıfları, Baglam
backend/app/services/    iş mantığı; çözücü ayrı bir serviste (cozum_servisi)
backend/app/schemas/     Pydantic sözleşmeleri (API girdi/çıktı)
backend/app/routers/     uç noktalar; yetki bağımlılıkları burada
backend/app/repositories/ SQL YALNIZ burada (SDD 3.2)
backend/alembic/versions/ göçler
frontend/src/screens/    yönetici ekranları; calisan/ altı çalışan paneli
frontend/src/lib/        saf yardımcılar (tarih, metin, saat aralığı)
docs/                    dört kanonik doküman + turlar
```

Çözücü ayrı bir süreçte koşar (`scripts/cozum_iscisi.py`); API iş kaydı
oluşturur, işçi onu alır. **Yerelde bu süreç de koşmalı** — koşmazsa çözüm
istekleri "KUYRUKTA" durumunda sonsuza kadar bekler ve arayüzde hiçbir hata
görünmez. Belirti tam olarak budur: iş kaydı oluşur, durum değişmez.

## Komutlar

```bash
# backend (backend/ içinden, .venv kurulu)
.venv/bin/pytest -q                     # tam takım — AĞIR DOSYALAR İÇİN AŞAĞI BAK
.venv/bin/ruff check .                  # lint
.venv/bin/ruff format --check .         # BİÇİM — bir tur boyunca unutuldu, ayrı koş
.venv/bin/alembic upgrade head          # göç
VERITABANI_URL=$TEST_VERITABANI_URL .venv/bin/alembic upgrade head   # test db'ye de
python scripts/cozum_iscisi.py          # ÇÖZÜM İŞÇİSİ — API'nin yanı sıra koşmalı
python scripts/cozum_iscisi.py --tek-adim   # tek iş alıp çık (sınama)
python scripts/demo_veri_uret.py [--reset]
python scripts/uc_noktalari_listele.py --denetle    # Ek B ile karşılaştır
VERI_TEMIZLIGINE_IZIN=1 python scripts/kabul_olcumu.py

# frontend (frontend/ içinden)
npm run test      # vitest
npm run lint      # oxlint
npx tsc -b        # tip denetimi
```

## Ağır test dosyaları — ayrı koşturulur

On bir OR-Tools dosyası tek koşumda ~10 dakika sürer ve sandbox zaman
aşımına takılır. Bir tur boyunca **sessizce koşmadılar**; "atlandı" ile
"geçti" aynı şey değildir.

```
test_cozucu_uctan_uca · test_cozucu_dogrulayici_uyumu
test_cozucu_dogrulayici_uyumu_olcek · test_cozum_servisi · test_cozum_iscisi
test_agirlik_kalibrasyonu · test_durdurma_karari · test_kurallar_zorunlu
test_kurallar_esnek · test_yeniden_coz · test_kabul_olcumu_dumani
```

Hafif takım: bunları `--ignore` ile dışarıda bırak. Tur kapanışında ağırları
bir kez ayrıca koştur.

## Tuzaklar

- **Testler ayrı veritabanında koşar** ve adında `test` geçmelidir; kapı
  `backend/conftest.py`'de, geçemezse takım yüksek sesle durur.
- **İki pytest süreci aynı anda koşamaz** (B-24): oturum boyunca tutulan bir
  PostgreSQL danışma kilidi ikincisini anlaşılır bir hatayla durdurur.
  Eşzamanlı koşum `StaleDataError` ve sessiz veri karışması üretiyordu.
- **`VERI_TEMIZLIGINE_IZIN`** verilmeden yıkıcı betikler çalışmaz; kabul
  ölçümü veritabanını temizler.
- **Koşulmuş bir göç değiştirilmez** — yenisi yazılır.
- **Kural sınıfları kendilerine verilen parametre nesnesini değiştirmez**
  (SDD 5.9); paylaşılan nesnedir, değiştiren sonraki çağrıyı bozar.
- **Şema `create_all` ile değil göçle kurulur** — göçlerin kendisi de böyle
  sınanır. Yeni göç iki veritabanına da uygulanmalı.

## Çalışma protokolü

- `docs/` altındaki dört kanonik doküman (Charter, SRS, SDD, Backlog) **tek
  gerçek kaynaktır ve Claude Code onlara dokunmaz.** Doküman etkisi doğuran
  bir değişiklik yaptıysan `PROGRESS_V2.md`'ye **DOKÜMAN BORCU** başlığı
  altında yaz; sürümleri chat tarafı üretir.
- Kayıt kanıt değildir, kod kanıttır. Doküman ile kod çelişirse önce kodu
  doğrula, sonra kaydı düzelt.
- Git: `add`, `commit`, `tag` serbest. **`push` ve `remote` asla.**
- Commit mesajları İngilizce; kod yorumları, arayüz metinleri ve dokümanlar
  Türkçe. Backend docstring'leri ASCII'ye indirgenmiş Türkçe kullanır —
  dokunduğun dosyanın kendi biçimine uy.
- Türkçe büyütme her zaman `buyukHarf()` ile; düz `.toUpperCase()` "i"
  harfini bozar.
- Başarısız test silinmez; `xfail` ile ve gerekçesiyle bırakılır.
