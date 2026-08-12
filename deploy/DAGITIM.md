# Dağıtım Kaydı ve Yeniden Kurulum Rehberi

**Durum:** ✅ **dağıtım tamamlandı ve doğrulandı.** Site yayında:
https://vardiya.omerharmankaya.com
**Sunucu:** 46.225.109.40 (Hetzner), Ubuntu 26.04 LTS, 4 çekirdek / 7,6 GB
**Son güncelleme:** 11.08.2026 (kapanış denetimi sunucuya çıktı — bölüm 13.6)

Bu dosya iki işi birden yapar: (a) yapılan her dağıtım adımının kaydı,
(b) sıfırdan yeniden kurulum rehberi. Dağıtım ilerledikçe her adım
gerçekte çalıştırılan komutla birlikte buraya işlenir; "şöyle yapılmalı"
değil "şöyle yapıldı" yazılır.

> **Sırlar bu dosyada yer almaz.** Veritabanı parolası ve benzeri hiçbir
> değer bu dosyaya, bir betiğe veya kaynak koda yazılmaz. Hepsi yalnızca
> sunucudaki `.env` içinde durur ve uygulamayı kuran kişi tarafından
> doldurulur (bölüm 3). Kimlik doğrulama turundan sonra doldurulması
> gereken tek sır `VERITABANI_URL`'dir; kullanıcı parolaları ve oturum
> belirteçleri ortam değişkenine dayanmaz.

---

## 1. Hedef ortam

| | |
|---|---|
| Referans donanım | 4 çekirdek, 8 GB (SDD 3.4.2) |
| Gerçek sunucu | Ubuntu 26.04 LTS, 4 çekirdek / 7,6 GB — referans donanımla uyumlu |
| Kurulum kökü | `/opt/vardiya` |
| Servis kullanıcısı | `vardiya` (sistem kullanıcısı, giriş kabuğu yok) |
| API | uvicorn, `127.0.0.1:8002`, tek işçi — `vardiya-api.service` |
| Çözüm işçisi | `vardiya-cozucu.service` |
| Ters vekil | Caddy (zaten kurulu, 80/443'ü yönetiyor) |
| Alan adı | `vardiya.omerharmankaya.com` |
| Veritabanı | PostgreSQL 18, aynı makine |
| Python | 3.14.4 (deponun tek sürümü) |
| Çözücü paralelliği | `COZUCU_ARAMA_ISCISI_SAYISI=3` (SDD 3.4.3: çekirdek −1) |

**Port 8002 neden:** makinede 8000 `vera-rag`, 8001 `energy-api` tarafından
kullanılıyor. Port tek yerde, `deploy/vardiya-api.service` içindeki `--port`
bayrağında tanımlı; `.env` bir `API_PORT` satırı taşımaz (uygulamanın
okumadığı ikinci bir tanım olurdu). Değişirse unit ve Caddy bloğu birlikte
güncellenir.

**Servis adları:** makinedeki diğer projeler proje önekli adlar kullanıyor
(`vera-rag`, `energy-api`); bu yüzden `vardiya-api` / `vardiya-cozucu`.

**Neden tek uvicorn işçisi:** çözüm yükü ayrı serviste çalışır; API süreci
yalnızca istek işler. Birden fazla uvicorn işçisi açmak dört çekirdeğin bir
kısmını çözücüden alır ve SDD 3.4.3'teki çekirdek paylaşımı kararını bozar.

## 2. Paket içeriği (`deploy/`)

| Dosya | İşlev |
|---|---|
| `vardiya-api.service` | API (uvicorn, port 8002) systemd unit'i |
| `vardiya-cozucu.service` | Çözücü işçisi systemd unit'i |
| `DAGITIM.md` | bu dosya |
| `../.env.example` | tüm ortam değişkenleri, sır gerektirenler işaretli |

## 3. Doldurulması gereken sırlar

Aşağıdaki iki değer `.env` içinde **boş bırakılmıştır** ve uygulamayı kuran
kişi tarafından doldurulur. Servisler bu değerler girilmeden
başlatılmamalıdır.

| Değişken | Ne konacak | Nasıl üretilir |
|---|---|---|
| `VERITABANI_URL` | **Tam URL**: `postgresql+psycopg://vardiya:<PAROLA>@localhost:5432/vardiya` — yalnız `<PAROLA>` değişir | Parolayı siz belirleyip hem `CREATE USER` komutunda hem burada kullanın |

**Doldurulması gereken tek sır budur.** Kimlik doğrulama turuyla birlikte
`CALISAN_PANELI_BAGLANTI_ANAHTARI` **kaldırıldı** (bölüm 12): parolalar
veritabanında Argon2id özeti olarak durur, oturum belirteci her girişte
rastgele üretilir; ikisi de bir ortam değişkenine dayanmaz.

**Sık yapılan hata:** `VERITABANI_URL` satırına yalnız parolayı yazmak.
Uygulama o dizeyi URL olarak ayrıştıramaz ve `Could not parse SQLAlchemy
URL` ile düşer. Satır tam URL taşımalıdır. Doğruluğu şöyle kontrol edilir
(değer ekrana basılmaz):

```bash
val=$(grep '^VERITABANI_URL=' /opt/vardiya/.env | cut -d= -f2-)
case "$val" in postgresql+psycopg://*) echo "tam URL";; *) echo "EKSIK";; esac
```

Parola `@ : / ? #` gibi karakterler içeriyorsa URL kodlaması gerekir
(`@` → `%40`). Ayrıca systemd `EnvironmentFile` bu dosyayı okur: değerler
tırnaksız yazılır ve `#` geçen bir değerin kalanı yorum sayılır.

## 4. Ön koşullar — YAPILDI

```bash
adduser --system --group --home /opt/vardiya --shell /usr/sbin/nologin vardiya
mkdir -p /opt/vardiya
```

PostgreSQL 18, Caddy ve Python 3.14 sunucuda zaten kuruluydu; `vardiya`
rolü ve `vardiya` veritabanı da önceden oluşturulmuştu.

**Node.js sunucuya KURULMADI.** Frontend yerelde derlenip `dist/` çıktısı
yüklenir (bölüm 6).

Kaynak kodun yüklenmesi (yerelden):

```bash
rsync -az --delete --exclude '.venv/' --exclude '__pycache__/' \
      --exclude '.pytest_cache/' --exclude '.ruff_cache/' --exclude '.env' \
      backend/ root@46.225.109.40:/opt/vardiya/backend/
rsync -az deploy/ root@46.225.109.40:/opt/vardiya/deploy/
scp .env.example root@46.225.109.40:/opt/vardiya/.env.example
```

Python ortamı:

```bash
cd /opt/vardiya/backend
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e ".[dev]"
chown -R vardiya:vardiya /opt/vardiya/backend
```

**Python 3.14 nedeniyle üç sabit sürüm yükseltildi.** Ubuntu 26.04'ün
deposunda tek Python sürümü 3.14 ve aynı makinedeki diğer projeler de onu
kullanıyor; aşağıdaki üç paketin derlenmiş uzantıları 3.14 için tekerlek
taşımıyordu (kaynaktan derleme Rust/C++ zinciri gerektirirdi). Her biri,
3.14 tekerleği bulunan **en düşük** sürüme çekildi:

| Paket | Önce | Sonra | Neden |
|---|---|---|---|
| `ortools` | 9.14.6206 | 9.15.6755 | 9.14'ün 3.14 tekerleği yok |
| `psycopg[binary]` | 3.2.3 | 3.2.10 | `psycopg-binary` tekerleği buradan itibaren |
| `pydantic` | 2.10.4 | 2.12.0 | 2.10.4, `pydantic-core==2.27.2`'yi tam sabitler; onun 3.14 tekerleği yok |

Yükseltmelerden sonra **163 testin tamamı** (çözücü-doğrulayıcı uyum testi
ve ağırlık kalibrasyonu dahil) ve **kabul ölçümü 5/5** yerelde yeniden
çalıştırıldı; sayılar değişmedi (K1 1,05 sn, K3 0,61).

## 5. Veritabanı — YAPILDI

- [x] `vardiya` rolü ve `vardiya` veritabanı (önceden hazırdı)
- [x] `.env` içindeki `VERITABANI_URL` dolduruldu
- [x] Göçler koşuldu

```bash
set -a; . /opt/vardiya/.env; set +a
cd /opt/vardiya/backend
sudo -u vardiya --preserve-env=VERITABANI_URL .venv/bin/alembic upgrade head
```

Üç göç de uygulandı (`b413bb80a4bd` → `a1c3f7e9b2d4` → `c8f2d1a45b73`);
17 tablo oluştu, zaman damgaları `timestamp with time zone`.

**Bir sürüm daha yükseltildi — SQLAlchemy 2.0.36 → 2.0.41.** 2.0.36 Python
3.14'te *kuruluyor* (saf Python tekerleği var) ama çalışma anında çöküyor:
`typing.Union.__getitem__` davranışı değişmiş. Kurulabilirlik kontrolü bunu
yakalayamaz; ancak kod çalıştırılınca ortaya çıkar. SQLAlchemy 3.14
sınıflandırıcısı yayınlamadığı için asgari sürüm ampirik bulundu
(2.0.37/.39/.40 hata, **2.0.41** çalışıyor). Bundan sonra sunucuda
**163 testin tamamı geçti** — başka yükseltme gerekmedi.

## 6. Frontend — YAPILDI

Yerelde derlenip yüklendi (sunucuda Node.js yok):

```bash
cd frontend && npm ci && npm run build
rsync -az --delete frontend/dist/ root@46.225.109.40:/opt/vardiya/web/
```

## 7. Servisler — YAPILDI

Unit dosyaları kuruldu ve doğrulandı:

```bash
cp /opt/vardiya/deploy/vardiya-api.service /etc/systemd/system/
cp /opt/vardiya/deploy/vardiya-cozucu.service /etc/systemd/system/
systemctl daemon-reload
systemd-analyze verify /etc/systemd/system/vardiya-api.service      # temiz
systemd-analyze verify /etc/systemd/system/vardiya-cozucu.service   # temiz
```

Sırlar doldurulduktan sonra başlatıldı:

```bash
systemctl enable --now vardiya-api.service vardiya-cozucu.service
systemctl reload caddy
```

**Doğrulama sonuçları:**

| Kontrol | Sonuç |
|---|---|
| `vardiya-api` / `vardiya-cozucu` | ikisi de `active` |
| API dinliyor | `127.0.0.1:8002` |
| `GET /api/donem` (doğrudan) | 200 |
| `GET /api/donem` (Caddy üzerinden, HTTPS) | 200 |
| Ana sayfa | 200 |
| Diğer siteler (rag / loadcast / emlak) | üçü de 200 — **etkilenmedi** |
| Uçtan uca çözüm | API kuyruğa yazdı → **işçi aldı** → `tamamlandı` (ceza 912) |

**`.env` dışarıdan erişilemiyor.** `/.env` isteği 200 döner ama gövde
`index.html`'dir — SPA geri dönüşü (`try_files ... /index.html`), dosyanın
kendisi değil. `.env` zaten web kökünün (`/opt/vardiya/web`) dışında,
`/opt/vardiya/.env` konumunda ve `0640 root:vardiya` izinli. `/api/.env`
404 döner. Aynı davranış `loadcast` bloğunda da vardır (aynı desen).
İnternet taramaları bu yolu ilk gün denedi; günlükte görülebilir.

### Caddy — blok eklendi, HENÜZ reload EDİLMEDİ

Değişiklikten önce yedek alındı ve `caddy validate` ile doğrulandı
(`Valid configuration`):

```bash
cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.yedek-20260808-071603
# blok dosyanın SONUNA eklendi; rag/loadcast/emlak blokları ve paylaşılan
# ayarlar değiştirilmedi
caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
```

Eklenen blok `loadcast` bloğuyla aynı deseni kullanır: statik SPA
(`/opt/vardiya/web`) + `/api/*` → `127.0.0.1:8002`. Aynı origin olduğu için
CORS başlığı yok.

`reload` bilerek ertelenmişti: servisler başlamadan reload edilirse site
yayına girer ama `/api` 502 dönerdi. Servisler ayağa kalktıktan sonra
reload edildi; diğer üç site etkilenmedi (hepsi 200).

**Çözüm işçisi hakkında.** SDD 3.4.4 gereği çözüm işi API sürecinde
çalışmaz: `CozumServisi.baslat` işi yalnızca `kuyrukta` durumunda yazar,
`cozum-isci.service` kuyruğu yoklayıp işleri yürütür. İki süreç arasında
doğrudan iletişim yoktur; tek sözleşme veritabanıdır.

Sonuçları:

- **API tek başına yeterli değildir.** İşçi çalışmazsa çözüm istekleri
  kuyrukta bekler ve hiçbir çizelge üretilmez. Her iki servis de
  `enable --now` edilmelidir.
- **Durdur butonu** API'den işin durumunu `IPTAL`'e çeker; işçi bunu çözüm
  geri çağırımında okuyup aramayı sonlandırır ve **hiçbir atama yazmadan**
  çıkar (SDD 6.3.2). Durum anında görünür, aramanın fiilen durması bir
  sonraki iyileşmiş çözüme ya da zaman limitine kadar sürebilir.
- **`systemctl stop` yarım sonuç bırakmaz:** işçi SIGTERM'de eldeki işi
  tamamlayıp çıkar. Unit'teki `TimeoutStopSec=180s` bu yüzden çözücü zaman
  limitinden (varsayılan 60 sn) geniş tutulmuştur.

## 8. Dağıtım sonrası kabul ölçümü — YAPILDI (09.08.2026)

Ölçüm, **gerçek kullanım başlamadan ve hesaplar açılmadan önce** alındı.

> ### ⛔ Sunucuda BİR DAHA yapılmayacaklar
>
> Aşağıdaki iki komut **sunucuda çalıştırılmamalıdır.** İkisi de tanım,
> girdi, kural ve sonuç tablolarını boşaltır; üstelik `personel` kaydına
> bağlı **hesapları da siler** (`kullanici.personel_id` yabancı anahtarı).
>
> | Komut | Sunucuda | Neden |
> |---|---|---|
> | `python -m pytest` | **HAYIR** | Senaryo kuran testler veritabanını boşaltır ve `HesapKapsami.HEPSI` ile **bütün hesapları** siler — yönetim hesabı dahil. O noktadan sonra sisteme giriş yolu kalmaz. |
> | `kabul_olcumu.py` | **HAYIR** | Ölçüm verisini kurmak için tabloları boşaltır; personele bağlı hesapları siler. |
> | `demo_veri_uret.py --reset` | **HAYIR** | Aynı temizlik sözleşmesi. |
>
> Bu satırlar 09.08.2026 kaydının düzeltmesidir: o gün **tüm test takımı
> sunucuda çalıştırılmıştı** ve o sırada henüz hiç hesap yoktu, dolayısıyla
> zararsız kaldı. Bugün aynı komut çalıştırılırsa yönetim hesabı da gider.
>
> **Koruma kod tarafında da var** (11.08.2026): her üçü de
> `VERI_TEMIZLIGINE_IZIN` ayarı olmadan çalışmayı reddeder
> (`app/veri_temizligi.py`). Ayar geliştirme makinesinin `backend/.env`
> dosyasındadır; **sunucuya eklenmemelidir** — kilit tam da ayarın
> yokluğunda devrededir.
>
> ### ✅ Sunucuda güvenle yapılabilecekler
>
> - `alembic upgrade head` / `alembic current` — şema göçleri
> - `yonetim_hesabi_olustur.py` — ilk yönetim hesabı (bölüm 12.5)
> - `systemctl status|restart vardiya-api vardiya-cozucu`
> - `journalctl -u vardiya-api` — kayıtlar
> - Bölüm 12.6'daki `curl` doğrulamaları (hepsi salt okunur)
>
> Ölçümü ve testleri **geliştirme makinesinde** çalıştırın. Sunucuda
> gerçekten gerekiyorsa (yeni bir referans donanım ölçümü gibi), önce
> veritabanını yedekleyin ve izni tek seferlik komutun önüne yazın:
> `VERI_TEMIZLIGINE_IZIN=true .venv/bin/python scripts/kabul_olcumu.py`

Ölçüm sırasında SDD 3.4.1/3.4.2 gereği diğer uygulamaların boşta olduğu bir
an seçildi (`vera-rag` ve `energy-api` %0,2 CPU).

- [x] `kabul_olcumu.py` → **K1–K5: 5/5 geçti**
- [x] `--json` çıktısı saklandı: `/opt/vardiya/olcum/kabul-20260809.json`
- [x] Tüm test takımı sunucuda: **163/163 geçti** (çözücü-doğrulayıcı uyum
      testinin 24 rastgele örneği dahil) — *o günkü kayıt; yukarıdaki
      uyarı gereği bir daha tekrarlanmayacak. Güncel sayı için geliştirme
      makinesindeki koşuya bakınız (11.08.2026: **304 backend / 135
      frontend**).*
- [x] K6: canlı site üzerinden **4 değişen atama**
- [x] `docs/PERFORMANS_NOTU.md` 2.0 — sunucu ölçümü **ikinci sütun** olarak
      eklendi, geliştirme makinesi sütunu korundu

**Referans donanımda 6/6 kriter geçti.** Süreler beklendiği gibi arttı
(K1 1,12 → 2,73 sn; K5 0,038 → 0,116 sn) ama eşiklerin çok altında kaldı;
kalite ölçütleri (K2, K3, K6) iki ortamda birebir aynı çıktı.

## 9. Çalışan paneli bağlantıları — KALDIRILDI

Bu bölüm kişiye özel bağlantı yöntemini anlatıyordu (`HMAC-SHA256(sunucu
sırrı, personel_id)`). Yöntem, betiği ve sunucu sırrıyla birlikte tümüyle
kaldırıldı; çalışan paneline artık kullanıcı adı ve parolayla girilir
(bölüm 12).

Kayıt olarak duruyor çünkü **dağıtılmış bağlantılar bir daha çalışmayacak**:
elinde eski bir bağlantı olan personel `/calisan/12?anahtar=…` adresine
gittiğinde giriş ekranını görür. Yeni dağıtımdan sonra herkese hesap
açılması gerekir (bölüm 12.4).

## 10. Bakım notları

**Yerel geliştirmede çözüm işçisi ayrıca çalıştırılmalıdır** (`python
scripts/cozum_iscisi.py`); çalışmazsa çözüm istekleri kuyrukta bekler.
Sunucuda bunu `vardiya-cozucu.service` yapar.

**Test veritabanı — yalnızca geliştirme makinesinde** (Ürün Backlog'u
B-20). Test takımı `vardiya` veritabanında değil, ayrı bir `vardiya_test`
veritabanında koşar; adresi `backend/.env` içindeki
`TEST_VERITABANI_URL`den okunur ve adında `test` geçmezse takım çalışmayı
reddeder. Sunucuda test koşturulmadığı için `/opt/vardiya/.env` bu satırı
**taşımaz**; taşısaydı, orada bulunmayan bir veritabanını gösteren ölü bir
ayar olurdu. `VERI_TEMIZLIGINE_IZIN` kilidi yerinde kalır — bu ikinci bir
kapıdır, onun yerine geçmez.

Test veritabanı geliştirme veritabanıyla **aynı göç zincirini** izler; yeni
bir göç eklendiğinde ikisine de uygulanır:

```bash
cd backend
VERITABANI_URL="$TEST_VERITABANI_URL" .venv/bin/alembic upgrade head
```

Günlükler:

```bash
journalctl -u vardiya-api -f
journalctl -u vardiya-cozucu -f
journalctl -u caddy -f | grep vardiya
```

Kod güncellemesi (yerelden):

```bash
cd frontend && npm ci && npm run build
rsync -az --delete frontend/dist/ root@46.225.109.40:/opt/vardiya/web/
rsync -az --delete --exclude '.venv/' --exclude '__pycache__/' \
      --exclude '.pytest_cache/' --exclude '.ruff_cache/' --exclude '.env' \
      backend/ root@46.225.109.40:/opt/vardiya/backend/
ssh $SSH_ANAHTARI root@46.225.109.40 'cd /opt/vardiya/backend && .venv/bin/pip install -q -e ".[dev]" \
    && chown -R vardiya:vardiya /opt/vardiya/backend \
    && systemctl restart vardiya-api vardiya-cozucu'
```

Şema değişikliği varsa `alembic upgrade head` yeniden başlatmadan **önce**
koşulur (bölüm 5'teki komut).

## 11. Arayüz turu güncellemesi (09.08.2026) — ÇIKTI

Bu tur sekiz madde getirdi (ayrıntı: PROGRESS.md, "Arayüz İyileştirme Turu").
Sunucuya çıkış için gereken üç şey var: **bir veritabanı göçü**, **yeniden
derlenmiş frontend** ve **servis yeniden başlatma**.

Yeni bağımlılık yok, yeni sır yok, `.env` değişmiyor. Frontend'e eklenen iki
paket (`@testing-library/react`, `jsdom`) yalnızca geliştirme
bağımlılığıdır; derleme yerelde yapıldığı için sunucuya hiç gitmez.

### Göçler: `d5e70a91c26f` → `e3b81f47a95c`

İki göç var, sırayla uygulanır. `alembic upgrade head` ikisini de yapar.

**`d5e70a91c26f`** — `yetkinlik`, `bina` ve `vardiya_tipi` tablolarına
`aktif BOOLEAN NOT NULL DEFAULT TRUE` ekler. Eklemeli ve geri alınabilir;
sunucu varsayılanı sayesinde mevcut satırlar tek adımda `aktif = TRUE`
olur, ayrı bir veri doldurma adımı **gerekmez**.

**`e3b81f47a95c`** — `kural` ve `gorev_noktasi` tablolarındaki mevcut
`aktif` sütunlarına aynı sunucu varsayılanını ekler. Bu ikisi ilk şemada
(b413bb80a4bd) varsayılansız oluşturulmuştu; beş tablo artık aynı
sözleşmede. Yalnızca varsayılanı değiştirir, **satırlara dokunmaz** —
pasifleştirilmiş bir kural veya görev noktası pasif kalır.

### Sıra

Göç, servisler yeniden başlatılmadan **önce** koşar. Ters sırada yeni kod
henüz var olmayan bir sütunu okur ve API açılışta çöker.

```bash
# 1) Yerelde derle ve testleri geçir (sunucuda Node yok)
cd frontend && npm ci && npm run build && npm test
cd ../backend && .venv/bin/python -m pytest -q   # 197 test

# 2) Kodu yükle
cd ..
rsync -az --delete frontend/dist/ root@46.225.109.40:/opt/vardiya/web/
rsync -az --delete --exclude '.venv/' --exclude '__pycache__/' \
      --exclude '.pytest_cache/' --exclude '.ruff_cache/' --exclude '.env' \
      backend/ root@46.225.109.40:/opt/vardiya/backend/

# 3) Göçü uygula, SONRA servisleri yeniden başlat
ssh $SSH_ANAHTARI root@46.225.109.40 'set -a; . /opt/vardiya/.env; set +a
  cd /opt/vardiya/backend
  sudo -u vardiya --preserve-env=VERITABANI_URL .venv/bin/alembic upgrade head
  sudo -u vardiya --preserve-env=VERITABANI_URL .venv/bin/alembic current
  chown -R vardiya:vardiya /opt/vardiya/backend
  systemctl restart vardiya-api vardiya-cozucu'
```

`alembic current` çıktısı `e3b81f47a95c (head)` olmalıdır.

### Doğrulama

```bash
ssh $SSH_ANAHTARI root@46.225.109.40 'systemctl is-active vardiya-api vardiya-cozucu'
curl -s https://vardiya.omerharmankaya.com/api/donem | head -c 120

# Yeni uç noktalar (tur boyunca eklenenler)
curl -s https://vardiya.omerharmankaya.com/api/kural | head -c 200        # ad + parametre_tanimlari taşımalı
curl -s https://vardiya.omerharmankaya.com/api/personel/1/kullanim        # kullanim dökümü
```

Arayüzde gözle bakılacaklar: Tanımlar sekmelerinde sağ üstteki
**Ekle · Değiştir · Sil**, Kural sekmesinde kural adları ve parametre
alanları (ham JSON kalmamalı), Çizelge ekranında yapışkan gün başlığı +
**Nokta Görünümü** + **CSV** / **Yazdır**, Sürümler ekranında arşiv
satırındaki **Taslak Olarak Kopyala**.

### Geri alma

Göç geri alınabilir (`downgrade` üç sütunu düşürür), ama önce eski kod
sürümüne dönülmelidir — yeni kod `aktif` sütunu olmadan çalışmaz:

```bash
ssh $SSH_ANAHTARI root@46.225.109.40 'cd /opt/vardiya/backend
  sudo -u vardiya --preserve-env=VERITABANI_URL .venv/bin/alembic downgrade c8f2d1a45b73'
```

Pasifleştirilmiş tanımlar varsa geri almada o bilgi kaybolur (sütun
düşer); kayıtların kendisi silinmez. `e3b81f47a95c`'nin geri alınması
zararsızdır — yalnızca varsayılanı kaldırır.

---

## 12. Kimlik doğrulama turu (09.08.2026) — ÇIKTI

Sistem canlıda çalışıyor; bu tur üzerine eklenen bir katmandır (SRS 5.10,
FR-10.1 – FR-10.10; SDD 4.2.1, 5.1b). Sunucuya çıkış için gereken beş şey
var: **`.env`'den bir satırın silinmesi**, **iki yeni Python paketi**, **bir
veritabanı göçü**, **yeniden derlenmiş frontend** ve **ilk yönetim
hesabının açılması**.

> **En kritik nokta baştan:** `.env` içindeki
> `CALISAN_PANELI_BAGLANTI_ANAHTARI` satırı **silinmezse uygulama
> açılmaz**. Uygulama açılışta kaldırılmış anahtarları açıkça arar ve
> bulursa hata verip çıkar (`app/config.py`,
> `_kaldirilmis_anahtarlari_dogrula`). Bu bilinçli — sessizce yok saymak,
> kaldırılmış bir sırrın hâlâ işe yaradığı izlenimi bırakırdı — ama sıra
> önemli: satırı servisleri yeniden başlatmadan **önce** silin.
>
> **Düzeltme (11.08.2026):** bu söz 09.08'de kısmen boştu. Koruma
> `Ayarlar`ın `extra='forbid'` ayarına dayanıyordu ve o, yalnızca DOTENV
> DOSYASINDAN okunan anahtarları reddeder; tanımadığı ORTAM
> DEĞİŞKENLERİNİ pydantic-settings sessizce yok sayar. Sunucuda ayarlar
> tam olarak ortam değişkeni olarak gelir (systemd `EnvironmentFile` +
> çalışma dizininde `.env` yok), dolayısıyla eski satır kalsa uygulama
> sorunsuz açılıyordu. Açıkça arayan kontrol bu yüzden eklendi; artık iki
> yol da aynı sonucu veriyor (`tests/test_kaldirilmis_ayar.py`).

### 12.1 `.env` değişiklikleri

**Silinecek satır** (tek satır, değeri önemsiz):

```bash
ssh $SSH_ANAHTARI root@46.225.109.40 "sed -i '/^CALISAN_PANELI_BAGLANTI_ANAHTARI=/d' /opt/vardiya/.env"
ssh $SSH_ANAHTARI root@46.225.109.40 "grep -c CALISAN_PANELI /opt/vardiya/.env"   # 0 dönmeli
```

**Eklenecek satırlar.** Hiçbiri sır değildir ve hepsinin kodda bir
varsayılanı vardır; `.env`'e yazılmaları yalnızca değerin sunucuda görünür
olması içindir. `OTURUM_CEREZI_SECURE` dışındakiler atlanabilir.

| Değişken | Değer | Anlamı |
|---|---|---|
| `OTURUM_HAREKETSIZLIK_DAKIKA` | `30` | Son istekten sonra oturumun düşme süresi |
| `OTURUM_AZAMI_SAAT` | `12` | Mutlak son kullanma; hareketsizlikten **ayrı** uygulanır |
| `GIRIS_KILIT_ESIGI` | `5` | Kaç ardışık başarısız denemeden sonra kilit (FR-10.8) |
| `GIRIS_KILIT_DAKIKA` | `15` | Kilit süresi |
| `OTURUM_CEREZI_SECURE` | `true` | **Sunucuda true kalmalı.** Site HTTPS'te; `false` yapmak oturum çerezini düz HTTP'de de göndermeye açar |

```bash
ssh $SSH_ANAHTARI root@46.225.109.40 "cat >> /opt/vardiya/.env <<'EOF'

# --- Kimlik dogrulama (SRS 5.10) ---
OTURUM_HAREKETSIZLIK_DAKIKA=30
OTURUM_AZAMI_SAAT=12
GIRIS_KILIT_ESIGI=5
GIRIS_KILIT_DAKIKA=15
OTURUM_CEREZI_SECURE=true
EOF"
```

### 12.2 Yeni bağımlılık: `argon2-cffi==25.1.0`

Parola özeti için (SDD 5.1b). `pip install -e ".[dev]"` yeterlidir —
**sürüm yükseltme dansı gerekmiyor**: bağımlılığın derlenmiş parçası
(`argon2-cffi-bindings`) kararlı ABI tekerleği yayınlıyor
(`cp39-abi3-manylinux_2_28_x86_64`), yani Python 3.14'te de hazır tekerlek
var. Bu, `ortools`/`psycopg`/`pydantic` üçlüsünde yaşanan durumun tersi;
yerelde `pip download --python-version 314 --abi cp314` ile doğrulandı.

### 12.3 Göç: `e3b81f47a95c` → `f7c1d9034ae6`

Tek göç, **yalnızca ekleme yapar**: `kullanici` ve `oturum` tabloları.
Mevcut hiçbir tablonun sütunu değişmez, hiçbir satır dönüştürülmez, veri
kaybı riski yoktur. Geri alınabilir (`downgrade` iki tabloyu ve `rol`
enum tipini düşürür); geri alınırsa yalnızca hesaplar kaybolur, çizelge
verisi etkilenmez.

İki CHECK kısıtı taşır: çalışan rolündeki hesap bir personel kaydına bağlı
olmak zorunda (FR-10.6) ve kullanıcı adı küçük harfle saklanır.

### 12.4 Sıra

Göç ve `.env` düzeltmesi, servisler yeniden başlatılmadan **önce** koşar.

```bash
# 1) Yerelde derle ve testleri geçir (sunucuda Node yok)
cd frontend && npm ci && npm run build && npm test   # 115 test
cd ../backend && .venv/bin/python -m pytest -q       # 279 test

# 2) .env'i düzelt — YENİDEN BAŞLATMADAN ÖNCE
ssh $SSH_ANAHTARI root@46.225.109.40 "sed -i '/^CALISAN_PANELI_BAGLANTI_ANAHTARI=/d' /opt/vardiya/.env"
# (12.1'deki yeni satırlar da burada eklenir)

# 3) Kodu yükle
cd ..
rsync -az --delete frontend/dist/ root@46.225.109.40:/opt/vardiya/web/
rsync -az --delete --exclude '.venv/' --exclude '__pycache__/' \
      --exclude '.pytest_cache/' --exclude '.ruff_cache/' --exclude '.env' \
      backend/ root@46.225.109.40:/opt/vardiya/backend/

# 4) Bağımlılık, göç, sonra yeniden başlatma
ssh $SSH_ANAHTARI root@46.225.109.40 'set -a; . /opt/vardiya/.env; set +a
  cd /opt/vardiya/backend
  .venv/bin/pip install -q -e ".[dev]"
  sudo -u vardiya --preserve-env=VERITABANI_URL .venv/bin/alembic upgrade head
  sudo -u vardiya --preserve-env=VERITABANI_URL .venv/bin/alembic current
  chown -R vardiya:vardiya /opt/vardiya/backend
  systemctl restart vardiya-api vardiya-cozucu'
```

`alembic current` çıktısı `f7c1d9034ae6 (head)` olmalıdır.

### 12.5 İlk yönetim hesabı (FR-10.10)

Bu adım atlanırsa **sisteme kimse giremez**: arayüzde hesap açan bir uç
nokta yoktur ve olmayacaktır. Hesap, sunucuda etkileşimli olarak açılır —
**parola argüman olarak verilemez** (kabuk geçmişine ve `ps` çıktısına
düşerdi), betik onu ekrana yazmadan sorar.

```bash
ssh -t $SSH_ANAHTARI root@46.225.109.40 'set -a; . /opt/vardiya/.env; set +a
  cd /opt/vardiya/backend
  sudo -u vardiya --preserve-env=VERITABANI_URL \
      .venv/bin/python scripts/yonetim_hesabi_olustur.py'
```

`ssh -t` gerekli: betik etkileşimli bir terminal ister ve bulamazsa 2 ile
çıkar. Betik, sistemde zaten aktif bir yönetim hesabı varsa hiçbir şey
yapmaz.

Bundan sonraki bütün hesaplar arayüzdeki **Kullanıcılar** ekranından
açılır. Çalışan rolündeki her hesap bir personel kaydına bağlanır
(FR-10.6) ve bir personelin ikinci hesabı açılamaz.

**Eski çalışan paneli bağlantıları artık çalışmıyor** (bölüm 9): panele
girmesi gereken her personel için hesap açılmalıdır.

### 12.6 Doğrulama

```bash
ssh $SSH_ANAHTARI root@46.225.109.40 'systemctl is-active vardiya-api vardiya-cozucu'

# Oturumsuz istek 401 dönmeli — 200 dönen bir uç nokta kalmamalı
curl -s -o /dev/null -w '%{http_code}\n' https://vardiya.omerharmankaya.com/api/donem     # 401
curl -s -o /dev/null -w '%{http_code}\n' https://vardiya.omerharmankaya.com/api/personel  # 401
curl -s -o /dev/null -w '%{http_code}\n' https://vardiya.omerharmankaya.com/health        # 200

# Eski bağlantı yolu artık veri vermiyor
curl -s -o /dev/null -w '%{http_code}\n' \
  'https://vardiya.omerharmankaya.com/api/calisan/vardiyalarim?personel_id=1&anahtar=x'   # 401
```

Arayüzde gözle bakılacaklar: kök adres giriş ekranını açar (kayıt bağlantısı
**yok**), yönetim hesabıyla girişte sol menüde **Kullanıcılar** görünür,
yönetici rolündeki bir hesapta **görünmez**. Yeni açılan bir hesapla ilk
girişte doğrudan parola değiştirme ekranı gelir ve değiştirilene kadar
başka bir ekrana geçilemez.

Kayıtlar (FR-10.9):

```bash
ssh $SSH_ANAHTARI root@46.225.109.40 "journalctl -u vardiya-api --since today | grep 'olay=giris'"
```

`olay=giris_basarili kullanici=… rol=…` ve `olay=giris_basarisiz …
neden=…` satırları görünmelidir. **Parola veya belirteç içeren bir satır
görünmemelidir**; görünürse bu bir hatadır.

### 12.7 Geri alma

Sırayla: eski koda dön, göçü geri al, `.env`'e eski sırrı geri koy.

```bash
ssh $SSH_ANAHTARI root@46.225.109.40 'cd /opt/vardiya/backend
  sudo -u vardiya --preserve-env=VERITABANI_URL .venv/bin/alembic downgrade e3b81f47a95c'
```

Geri alma **hesapları siler** (tablolar düşer); çizelge, tanım ve girdi
verisi etkilenmez. Eski kod `CALISAN_PANELI_BAGLANTI_ANAHTARI` olmadan
çalışan paneli bağlantılarını doğrulayamaz, o yüzden geri dönülüyorsa o
satırın da `.env`'e geri konması gerekir.

---

## 13. Kapanış denetimi turu (11.08.2026) — ÇIKTI

Bu tur bir denetimin bulgularını kapatır. **Yeni bağımlılık yok, yeni sır
yok.** Çıkış için gereken dört şey var: **`.env`'e bir satır EKLENMEMESİ**,
**bir veritabanı göçü**, **yeniden derlenmiş frontend** ve **servis yeniden
başlatma**.

### 13.0 Göç: `f7c1d9034ae6` → `a4d92c15e807`

Tek göç, **yalnızca ekleme yapar**: `fazla_kadro` tablosu. Mevcut hiçbir
tablonun sütunu değişmez, hiçbir satır dönüştürülmez, veri kaybı riski
yoktur. Geri alınabilir (`downgrade` tabloyu düşürür); geri alınırsa
yalnızca fazla kadro kayıtları kaybolur, çizelge verisi etkilenmez.

`alembic current` çıktısı `a4d92c15e807 (head)` olmalıdır.

### 13.1 `.env` — hiçbir şey eklenmeyecek

Bu turda `VERI_TEMIZLIGINE_IZIN` adında bir ayar eklendi
(`app/veri_temizligi.py`). **Sunucudaki `/opt/vardiya/.env` dosyasına
YAZILMAMALIDIR.** Varsayılanı `false` ve kilit tam da ayarın yokluğunda
devrede; yazılırsa sunucudaki koruma kalkar (bkz. bölüm 8'deki uyarı
kutusu).

Doğrulama:

```bash
ssh $SSH_ANAHTARI root@46.225.109.40 "grep -c VERI_TEMIZLIGINE_IZIN /opt/vardiya/.env"   # 0 dönmeli
```

### 13.2 Değişiklikler

| Bulgu | Ne değişti |
|---|---|
| B1 · B2 | Yıkıcı temizliğin tek tanımı: `app/veri_temizligi.py`. `TRUNCATE ... CASCADE` kaldırıldı; silinecek tablolar açık bir listede, hesapların akıbeti çağıranın açık seçimi (`HesapKapsami`). Betikler artık çökmüyor: personele bağlı hesapları siliyor, sayısını yazıyor, yönetim hesaplarına dokunmuyor. |
| B1d | Üretim kilidi: yıkıcı betikler ve fikstürler `VERI_TEMIZLIGINE_IZIN` olmadan reddediyor (yığın izi değil, tek satır mesaj + çıkış kodu 2). |
| B3 | Personel formundaki yetkinlik seçimi çoklu oldu. Önce tek seçim vardı ve iki yetkinlikli bir personeli değiştirmeden kaydetmek ikincisini **sessizce siliyordu**. |
| B4 | Kaldırılmış yapılandırma anahtarları açılışta açıkça aranıyor (bölüm 12.1'deki düzeltme notu). |
| B5 | `ozel_gun` için uç nokta ve arayüz (FR-1.10): `/api/ozel-gun` + Tanımlar'da **Özel Gün** sekmesi. Tablo ve çözücü tarafı zaten vardı, yalnız yazma yolu yoktu. |
| Madde 6 | Personel formu tamamlandı: sabit vardiya alanı, aktiflik tarihleri, sicil benzersizliği sunucuda (**409**, 500 değil), yanıltıcı "Aktif" kutusu kaldırıldı, yetkinlik çakışması için **uyarı** (engel değil). |
| B14 | Var olmayan `personel_id` ile hesap açmak 500 yerine anlaşılır 400 döndürüyor. |
| S1 üst sınırı | Manuel düzenlemede bir noktaya **talepten fazla** kişi yazmak sessizce kabul ediliyordu; `dogrula` yalnızca alt sınıra bakıyordu. Artık iki yarım da denetleniyor. Fazla kadro **engel değil uyarı** (ürün kararı) ve **ceza üretmez** — SRS 4.4'teki amaç fonksiyonunda karşılığı olmayan bir sayı uydurmamak için. |
| Ceza bildirimi | Panel tek bir **ham** sayı gösteriyordu (`+1.00`). Artık **ağırlıklı** toplam + kural bazında döküm (kimlik, ad, ham fark, ağırlık, ağırlıklı fark) + "nerede ne bozuldu" cümleleri. S1 mesajları kimlik yerine **ad** taşıyor (NFR-5). |
| Sapma kalıcılığı | Fazla kadro artık sürümde **kalıcı** (`fazla_kadro` tablosu): sürüm raporunda, Analiz'de, yazdırılabilir görünümde ve dışa aktarmada görünüyor. Aynı yolda bulunan bir hata da kapandı: **manuel düzenleme `kapsama_acigi` tablosunu hiç güncellemiyordu**, dolayısıyla elle düzenlenmiş her sürümde kapsama oranı, açık sayısı ve açık dosyası bayattı. |

### 13.3 Sıra

Bir göç var (13.0) ve **kod yüklendikten SONRA** uygulanır: `alembic`
sunucudaki depodan okunur, dolayısıyla göç dosyası önce oraya varmalıdır.

**SSH anahtarı — İKİ değişken birden.** `RSYNC_RSH` yalnızca rsync'i
etkiler; düz `ssh` çağrıları onu okumaz (bkz. 15.4).

```bash
export SSH_ANAHTARI="-o IdentitiesOnly=yes -i $HOME/.ssh/vera_hetzner"
export RSYNC_RSH="ssh $SSH_ANAHTARI"
```

```bash
# 1) Yerelde derle ve testleri geçir (sunucuda Node yok — ve pytest de yok)
cd frontend && npm ci && npm run build && npm test   # 135 test
cd ../backend && .venv/bin/python -m pytest -q       # 307 test

# 2) Kodu yükle
cd ..
rsync -az --delete frontend/dist/ root@46.225.109.40:/opt/vardiya/web/
rsync -az --delete --exclude '.venv/' --exclude '__pycache__/' \
      --exclude '.pytest_cache/' --exclude '.ruff_cache/' --exclude '.env' \
      backend/ root@46.225.109.40:/opt/vardiya/backend/

# 3) Göçü uygula, SONRA yeniden başlat
ssh $SSH_ANAHTARI root@46.225.109.40 'set -a; . /opt/vardiya/.env; set +a
  cd /opt/vardiya/backend
  sudo -u vardiya --preserve-env=VERITABANI_URL .venv/bin/alembic upgrade head
  sudo -u vardiya --preserve-env=VERITABANI_URL .venv/bin/alembic current
  chown -R vardiya:vardiya /opt/vardiya/backend
  systemctl restart vardiya-api vardiya-cozucu'
```

### 13.4 Doğrulama

```bash
ssh $SSH_ANAHTARI root@46.225.109.40 'systemctl is-active vardiya-api vardiya-cozucu'

# Yeni uç noktalar oturumsuz 401 dönmeli (açık kalan bir yol yok)
curl -s -o /dev/null -w '%{http_code}\n' https://vardiya.omerharmankaya.com/api/ozel-gun  # 401
curl -s -o /dev/null -w '%{http_code}\n' \
  https://vardiya.omerharmankaya.com/api/surum/1/fazla-kadro                              # 401

# Kilit sunucuda GERÇEKTEN kapalı mı — kapının kendisi çağrılır, kapıdan
# geçen betik DEĞİL. `demo_veri_uret.py --reset` çalıştırmak bu soruyu
# yanıtlamanın YANLIŞ yoludur: kilit beklenmedik biçimde açıksa cevabı
# 44 personelin, 17 sürümün ve 2.155 atamanın silinmesiyle öğrenirsiniz.
# `uretim_kilidini_dogrula` betiğin çağırdığı aynı kapıdır ve hiçbir şeye
# dokunmaz.
ssh $SSH_ANAHTARI root@46.225.109.40 'cd /opt/vardiya/backend
  set -a; . /opt/vardiya/.env; set +a
  sudo -u vardiya --preserve-env=VERITABANI_URL .venv/bin/python -c "
from app.veri_temizligi import uretim_kilidini_dogrula, UretimKilidiError
from app.config import ayarlar
print(\"veri_temizligine_izin =\", ayarlar.veri_temizligine_izin)
try:
    uretim_kilidini_dogrula()
except UretimKilidiError as h:
    print(\"KILIT DEVREDE ->\", h)
else:
    raise SystemExit(\"!!! KILIT ACIK — yikici betikler calisabilir\")
"'
# "KILIT DEVREDE -> ..." beklenir. Başka bir çıktı gelirse .env'e
# VERI_TEMIZLIGINE_IZIN sızmış demektir — hemen silin.
```

Arayüzde gözle bakılacaklar: Tanımlar'da **Özel Gün** sekmesi ve sağ üstteki
Ekle · Değiştir · Sil üçlüsü; Personel sekmesinde **Yetkinlikler** çoklu
seçimi, **Sabit Vardiya** ve iki aktiflik tarihi alanı; Müracaat Görevlisi
ile Güvenlik Görevi birlikte işaretlendiğinde çıkan uyarının kaydetmeyi
**engellemediği**.

Çizelge ekranında ayrıca: bir noktayı boşaltan bir hücre değişikliği
doğrulandığında panelde artık tek bir sayı değil, **hangi noktanın açıkta
kaldığını yazan bir cümle**, ağırlıklı ceza değişimi ve kural bazında
döküm tablosu görünmelidir. Bir noktaya talepten fazla kişi yazıldığında
"talepten N kişi fazla" uyarısı çıkar ama değişiklik **engellenmez**.

### 13.5 Geri alma

Önce eski kod sürümüne dönülür, sonra göç geri alınır:

```bash
ssh $SSH_ANAHTARI root@46.225.109.40 'cd /opt/vardiya/backend
  sudo -u vardiya --preserve-env=VERITABANI_URL .venv/bin/alembic downgrade f7c1d9034ae6'
```

Geri alma yalnızca `fazla_kadro` satırlarını düşürür; çizelge, tanım ve
girdi verisi etkilenmez.

### 13.6 Çıkış kaydı (11.08.2026, 15:58 TSİ)

| | |
|---|---|
| Kod sürümü | `fb10a74` (`fd9f99b` + yazdırılabilir başlık testi düzeltmesi) |
| Göç | `f7c1d9034ae6` → `a4d92c15e807`, `alembic current` = `a4d92c15e807 (head)` |
| Servisler | `vardiya-api`, `vardiya-cozucu` → yeniden başlatıldı, ikisi de `active` |
| Uyarı/hata günlüğü | yeniden başlatmadan sonra `-p warning` boş |
| `/api/ozel-gun`, `/api/surum/1/fazla-kadro`, `/api/personel` | oturumsuz **401** |
| Arayüz kökü | **200** |
| Üretim kilidi | `veri_temizligine_izin = False`, `uretim_kilidini_dogrula()` reddediyor; `/opt/vardiya/backend/.env` yok, `/opt/vardiya/.env` içinde `VERI_TEMIZLIGINE_IZIN` **yok** |
| Veri (dağıtım öncesi → sonrası) | 44 personel · 6 dönem · 17 sürüm · 2.155 atama · 4 hesap → **değişmedi** |
| `fazla_kadro` | tablo oluştu, 0 satır (mevcut sürümler yeniden çözülmediği için beklenen) |

**Mevcut sürümler geriye dönük fazla kadro taşımaz.** `fazla_kadro`
satırları `sapmalari_yenile` ile, yani bir çözüm veya elle düzenleme
sırasında yazılır; göç yalnızca tabloyu açar, geçmiş sürümleri taramaz.
Yayındaki 17 sürümde fazla kadro varsa Analiz'de ancak o sürüm yeniden
çözüldüğünde ya da elle düzenlendiğinde görünür.

Bölüm 13.4'teki arayüz turu **yapılmadı** — sunucuda oturum açmayı
gerektiriyor ve mevcut dört hesabın parolası bu makinede yok.

---

## 14. İkinci aşama, tur 1 + tur 2 (12.08.2026) — ÇIKIŞ HAZIR

İki tur birikti, tek çıkışta gidiyor. **Yeni bağımlılık yok, yeni sır
yok.** Gereken dört şey: **`.env`'e bir satır EKLENMEMESİ**, **iki
veritabanı göçü**, **yeniden derlenmiş frontend** ve **her iki servisin**
yeniden başlatılması.

### 14.0 Göçler: `a4d92c15e807` → `b6e2f81d3c07` → `c9a4b7e21f38`

| Göç | İçerik |
|---|---|
| `b6e2f81d3c07` | `cozum_isi.durum` ENUM'una `DURDURULDU`; `gecici_sonuc` JSONB; `devam_kaynagi_is_id` FK |
| `c9a4b7e21f38` | `cozum_isi.cozum_ipucu` JSONB |

**İkisi de yalnızca ekleme yapar.** Mevcut hiçbir sütun dönüştürülmez,
hiçbir satır taşınmaz, veri kaybı riski yoktur. `alembic current` çıktısı
`c9a4b7e21f38 (head)` olmalıdır.

`bitis_zamani` bu turda TIMESTAMPTZ'ye çevrilmedi çünkü **zaten öyleydi**
(göç `c8f2d1a45b73`, 08.08.2026). Olmayan bir farkı düzeltmek için ALTER
TYPE yazmak mevcut değerleri ikinci kez yorumlama riski doğururdu.

### 14.1 `.env` — hiçbir şey eklenmeyecek

Tur 2'de `TEST_VERITABANI_URL` adında bir ayar eklendi. **Sunucudaki
`/opt/vardiya/.env` dosyasına YAZILMAMALIDIR** — sunucuda test
koşturulmaz; yazılırsa orada bulunmayan bir veritabanını gösteren ölü bir
ayar olur. Uygulama bu değeri zaten hiç okumaz, yalnızca
`backend/conftest.py` okur.

`VERI_TEMIZLIGINE_IZIN` de eskisi gibi **yoktur** ve olmamalıdır.

```bash
ssh $SSH_ANAHTARI root@46.225.109.40 "grep -cE 'TEST_VERITABANI_URL|VERI_TEMIZLIGINE_IZIN' /opt/vardiya/.env"   # 0
```

### 14.2 Değişiklikler

| Tur | Ne değişti |
|---|---|
| 1 · İş 1 | Durdurma isteği artık ara çözüm geri çağırmasında beklemiyor: arama işçi sürecinde ayrı bir iş parçacığında yürüyor, ana döngü durumu yarım saniyede bir taze okuyup `stop_search()` çağırıyor. Ölçülen gecikme **0,35 s** (eski yolda en az 8,3 s, üst sınır zaman limitinin kendisi). |
| 1 · İş 2 | **Durdurma çözümü atmıyor.** Arama sonlanıyor, bulunan çözüm `gecici_sonuc`ta saklanıyor, kullanıcı karar veriyor: kullan / at / devam. `POST /api/cozum/{id}/iptal` **kaldırıldı**, yerine `/durdur` ve `/karar` geldi. |
| 1 · İş 3 | Çalışan iş göstergesi yönetici kabuğunun üst çubuğunda; yoklama ekran değişiminde ölmüyor. Yeni uç: `GET /api/cozum/aktif`. İş kimliği tarayıcıda tutulmuyor. |
| 1 · İş 4 | Yan menü sabit, içerik alanı kendi içinde kaydırılıyor. |
| 2 · İş 1 | Çözücü ipucu kendi sütununda (`cozum_ipucu`) ve **iş sonlandığında** boşalıyor. |
| 2 · İş 2 | Arama başlamadan gelen durdurma (`kuyrukta`/`on_kontrol`) **doğrudan iptal**; karar sorulmuyor. Geçiş tek koşullu UPDATE ile yarışsız. |
| 2 · İş 3 | Test takımı ayrı veritabanında (`vardiya_test`). **Sunucuyu ilgilendirmez**, yalnızca geliştirme makinesini. |

**Uç nokta sayısı 70 → 72** (`/iptal` gitti; `/durdur`, `/karar`, `/aktif`
geldi). Güncel liste `docs/EK_B_UC_NOKTALAR.md`'de.

### 14.3 Sıra

Göçler **kod yüklendikten SONRA** uygulanır: `alembic` sunucudaki depodan
okunur, dolayısıyla göç dosyaları önce oraya varmalıdır.

**SSH anahtarı — İKİ değişken birden.** `RSYNC_RSH` yalnızca rsync'i
etkiler; düz `ssh` çağrıları onu okumaz (bkz. 15.4).

```bash
export SSH_ANAHTARI="-o IdentitiesOnly=yes -i $HOME/.ssh/vera_hetzner"
export RSYNC_RSH="ssh $SSH_ANAHTARI"
```

```bash
# 1) Yerelde derle ve testleri geçir (sunucuda Node yok — ve pytest de yok)
cd frontend && npm ci && npm run build && npm test   # 140 test
cd ../backend && .venv/bin/python -m pytest -q       # 322 test

# 2) Kodu yükle
cd ..
rsync -az --delete frontend/dist/ root@46.225.109.40:/opt/vardiya/web/
rsync -az --delete --exclude '.venv/' --exclude '__pycache__/' \
      --exclude '.pytest_cache/' --exclude '.ruff_cache/' --exclude '.env' \
      backend/ root@46.225.109.40:/opt/vardiya/backend/

# 3) Göçleri uygula, SONRA yeniden başlat
ssh $SSH_ANAHTARI root@46.225.109.40 'set -a; . /opt/vardiya/.env; set +a
  cd /opt/vardiya/backend
  sudo -u vardiya --preserve-env=VERITABANI_URL .venv/bin/alembic upgrade head
  sudo -u vardiya --preserve-env=VERITABANI_URL .venv/bin/alembic current
  chown -R vardiya:vardiya /opt/vardiya/backend
  systemctl restart vardiya-api vardiya-cozucu'
```

**İki servis de yeniden başlatılmak zorunda.** Yeni uç noktalar API'de,
`durduruldu` durumu ile üç yeni sütun ise işçide kullanılıyor; yalnız
birini yeniden başlatmak, durdurma isteğini yazan tarafla okuyan tarafın
farklı sürümlerde kalması demektir.

**Rsync sırasında sunucudaki `backend/conftest.py` de yerine gider.** Zararı
yok: dosya yalnızca `pytest` çalıştırıldığında okunur ve sunucuda pytest
kurulu değil. Uygulamanın açılışına hiçbir etkisi yoktur.

### 14.4 Doğrulama

```bash
ssh $SSH_ANAHTARI root@46.225.109.40 'systemctl is-active vardiya-api vardiya-cozucu'
ssh $SSH_ANAHTARI root@46.225.109.40 'journalctl -u vardiya-api -u vardiya-cozucu --since "5 min ago" -p warning'

# Yeni uç noktalar oturumsuz 401 dönmeli (açık kalan bir yol yok)
for yol in /api/cozum/aktif /api/cozum/1/durdur /api/cozum/1/karar; do
  curl -s -o /dev/null -w "$yol -> %{http_code}\n" \
    -X POST https://vardiya.omerharmankaya.com$yol
done   # üçü de 401

# Kaldırılan uç nokta artık YOK: 404 ya da 405 dönmeli, 401 DEĞİL.
# 401 dönerse eski kod hâlâ ayakta demektir.
curl -s -o /dev/null -w '%{http_code}\n' \
  -X POST https://vardiya.omerharmankaya.com/api/cozum/1/iptal

# Göç uygulandı mı — üç sütun ve enum değeri
ssh $SSH_ANAHTARI root@46.225.109.40 'set -a; . /opt/vardiya/.env; set +a
  psql "$VERITABANI_URL" -tAc "
    select column_name from information_schema.columns
     where table_name = '"'"'cozum_isi'"'"'
       and column_name in ('"'"'gecici_sonuc'"'"','"'"'cozum_ipucu'"'"','"'"'devam_kaynagi_is_id'"'"')
     order by column_name;
    select enumlabel from pg_enum e join pg_type t on t.oid = e.enumtypid
     where t.typname = '"'"'cozumisidurumu'"'"' and enumlabel = '"'"'DURDURULDU'"'"';"'
```

Arayüzde gözle bakılacaklar (oturum açmayı gerektirir):

- Üst çubukta **çalışan iş göstergesi**: çözüm başlatıp Tanımlar'a geçince
  gösterge yerinde kalmalı, sayfa yenilendikten sonra da durmalı.
- Yan menü: uzun içerikli ekranlarda (Kural sekmesi, Analiz, Çizelge)
  sayfa kaydırılırken menü **yerinde kalmalı** ve alttaki Dönem bloğu
  görünür olmalı.
- **Durdur** → karar paneli: toplam ceza, hedef bazında döküm ve kapsama
  açığı sayısı görünmeli; üç eylem sunulmalı; ekranda "kaldığı yerden
  devam" ifadesi **geçmemeli**.
- Kuyruktaki bir işi durdurmak: panel **açılmamalı**, iş iptal edilmeli.

### 14.5 Geri alma

Önce eski kod sürümüne dönülür, sonra göçler geri alınır:

```bash
ssh $SSH_ANAHTARI root@46.225.109.40 'cd /opt/vardiya/backend
  sudo -u vardiya --preserve-env=VERITABANI_URL .venv/bin/alembic downgrade a4d92c15e807'
```

**Geri almadan önce karar bekleyen iş kalmadığından emin olun.** `durduruldu`
durumundaki bir iş, o durumu tanımayan eski kodun karşısına çıkarsa arayüz
onu okuyamaz:

```sql
select is_id, durum from cozum_isi where durum = 'DURDURULDU';   -- boş olmalı
```

Geri alma üç sütunu düşürür; kaybolan tek şey karar bekleyen işlerin
saklanmış çözümleridir — atama, kapsama açığı ve sürüm verisi etkilenmez.
**ENUM değeri geri alınmaz** (göç dosyasında gerekçesi yazılı): bir enum
değerini kaldırmak tipi baştan yaratıp bağımlı sütunları çevirmeyi
gerektirir ve o işlem veri kaybettirebilir. Kullanılmayan bir enum değeri
ise hiçbir şeye mal olmaz.

### 14.6 Çıkış kaydı

_Dağıtım yapıldığında doldurulacak._

| | |
|---|---|
| Kod sürümü | `d134f2c` |
| Göçler | `a4d92c15e807` → `b6e2f81d3c07` → `c9a4b7e21f38` |
| Servisler | — |
| Uyarı/hata günlüğü | — |
| Veri (öncesi → sonrası) | — |

---

## 15. Tur 3 — saatlik düzenin veri temeli (12.08.2026) — ÇIKIŞ HAZIR

**Bu, şimdiye kadarki en riskli çıkıştır ve tek farkla öncekilerden ayrılır:
göçlerden biri VERİ DÖNÜŞTÜRÜYOR.** Bölüm 14 (tur 1 + tur 2) hâlâ
sunucuya çıkmadıysa üç göç birlikte gider; 14'ün sırası bu bölümün
sırasıyla değiştirilir, 14.0'daki iki göç zincirin ilk iki halkasıdır.

**Yeni bağımlılık yok, yeni sır yok, `.env` değişmiyor.**

### 15.0 Önce: sunucu nerede

Kaç göç uygulanacağı sunucunun bulunduğu noktaya bağlı. Salt okunur:

```bash
ssh $SSH_ANAHTARI root@46.225.109.40 'set -a; . /opt/vardiya/.env; set +a
  cd /opt/vardiya/backend
  sudo -u vardiya --preserve-env=VERITABANI_URL .venv/bin/alembic current'
```

| Çıktı | Uygulanacak göç |
|---|---|
| `a4d92c15e807` | üçü birden: `b6e2f81d3c07` → `c9a4b7e21f38` → `d1f83a6c40b2` |
| `c9a4b7e21f38` | yalnız `d1f83a6c40b2` |
| `d1f83a6c40b2 (head)` | zaten çıkmış |

### 15.1 ⚠ `d1f83a6c40b2` veriyi dönüştürüyor — önce yedek

Bu göç üç şey yapıyor ve ilk ikisi geri döndürülemez veri işlemidir:

1. **`talep` satırları bloktan aralığa çevriliyor.** `vardiya_tipi_id`
   sütunu düşüyor, yerine `baslangic` / `bitis` (TIME) geliyor. Dönüşüm
   göç içinde yapılıyor ve **sayılarak doğrulanıyor**: satır sayısı ile
   toplam kişi-saat yükü dönüşümden önce ve sonra eşit değilse göç hata
   verip **duruyor**. Sessizce devam etseydi kaybolan bir talep satırı
   hiçbir yerde görünmezdi — talep düştüğü için kapsama açığı da doğmaz.
2. **`kapsama_acigi` ve `fazla_kadro` satırları SİLİNİYOR** (dönüştürülmüyor).
   Bu iki tablo bir çözümün çıktısıdır, kullanıcının girdiği veri değil;
   blok eksenli bir açık kaydını aralığa çevirmek, o kaydın üretildiği
   andaki talebi yeniden kurmayı gerektirir ve talep aynı göçte değişiyor.
   Yanlış dönüşmüş bir açık kaydı hiç olmamasından kötüdür: rapora doğru
   gibi girer.
3. `personel`e devir bakiyesi alanları, `cozum_isi`ye
   `on_kontrol_bulgulari` ekleniyor (yalnızca ekleme, risksiz).

> **Görünür sonuç: yayındaki sürümlerin kapsama açığı sayıları sıfırlanır.**
> Analiz ekranı, sürüm listesindeki açık sayıları ve açık dosyası, ilgili
> sürüm **yeniden çözülene ya da elle düzenlenene kadar** boş görünür.
> Atamalar, sürümler, tanımlar ve hesaplar etkilenmez. Bunu personele
> duyurmak gerekebilir.

Yedek — göçten önce, tek komut:

```bash
ssh $SSH_ANAHTARI root@46.225.109.40 'set -a; . /opt/vardiya/.env; set +a
  mkdir -p /opt/vardiya/yedek
  pg_dump "$VERITABANI_URL" -Fc -f /opt/vardiya/yedek/vardiya-$(date +%Y%m%d-%H%M).dump
  ls -lh /opt/vardiya/yedek/ | tail -3'
```

Dönüşümün ölçüsü (geliştirme veritabanı): **27 satır → 27 satır, 384
kişi-saat → 384 kişi-saat.** Sunucudaki sayı farklı olacaktır; önemli olan
göçün kendi kendini doğrulaması.

### 15.2 API sözleşmesi kırıldı — iki taraf BİRLİKTE gitmeli

`PUT /api/talep` **kaldırıldı**. Talep artık bir matris hücresi değil bir
zaman aralığı kaydı; yerine `POST /api/talep`, `PUT /api/talep/{id}` ve
`DELETE /api/talep/{id}` geldi (**uç nokta sayısı 72 → 74**).

Sonucu: **backend'i güncelleyip eski `dist/`i bırakmak Talep ekranını
çalışmaz hâle getirir** — ekran var olmayan bir uca yazar ve hiçbir talep
kaydedilemez. Frontend derlemesi ile backend aynı çıkışta gider.

### 15.3 Değişiklikler

| İş | Ne değişti |
|---|---|
| 1–4 | Talep, kapsama ve S1 kısıtı **saat eksenine** taşındı. Açık/fazla kadro kayıtları artık aralık; ardışık ve sayısı eşit saatler tek satırda birleşiyor (00…07'de 1 kişi eksik → tek `00.00–08.00 / 1` kaydı). |
| 5 | `personel.devir_fazla_calisma_saat` ve `kota_yili` — alanlar toplanıyor, **hiçbir kural okumuyor** (Tur 4'ün kota hesabı için). |
| 6 | Blok kataloğu kısıtları: aynı `(başlangıç, süre)` ikinci kez tanımlanamaz (**409**), süre günlük azamiyi (11 sa) aşamaz (**400**). |
| 7 | Talep ekranı aralık listesi oldu; saatler açılır liste, gün sonu **24.00**. |
| 8 | Ön kontrol bulguları çözümü **düşürmüyor**; `cozum_isi.on_kontrol_bulgulari`na yazılıp çözüme devam ediliyor. |
| 9 | Kapsama oranı artık **atama kayıtlarından** hesaplanıyor. |
| 10 | Bulgu metinleri veritabanı kimliği değil **ad** taşıyor. |

Kabul ölçümü (geliştirme makinesi, simetri gruplamasından sonra):
**K1 1,01 sn · K2 0 · K3 0,61 · K4 13 aralık · K5 0,035 sn — 5/5.**

### 15.4 Sıra

Göçler **kod yüklendikten SONRA** uygulanır: `alembic` sunucudaki depodan
okunur, dolayısıyla göç dosyaları önce oraya varmalıdır.

**SSH anahtarı — İKİ değişken birden gerekir.** Bağlantı
`~/.ssh/vera_hetzner` ile kurulur; makinedeki varsayılan `id_ed25519` bu
sunucuda tanımlı DEĞİLDİR. `RSYNC_RSH` **yalnızca rsync'i** etkiler;
düz `ssh` çağrıları onu okumaz ve `Permission denied (publickey)` alır.
Bu, 12.08.2026'da yarım bir dağıtıma yol açtı: rsync geçti, yedek ve göç
geçmedi, canlıda yeni arayüz eski backend'le kaldı.

```bash
export SSH_ANAHTARI="-o IdentitiesOnly=yes -i $HOME/.ssh/vera_hetzner"
export RSYNC_RSH="ssh $SSH_ANAHTARI"
```

Aşağıdaki komutların hepsi `$SSH_ANAHTARI` taşır; ikisini de aynı kabukta
tanımlayın.
```bash
# 1) Yerelde derle ve testleri geçir (sunucuda Node yok — ve pytest de yok)
cd frontend && npm ci && npm run build && npm test   # 155 test
cd ../backend && .venv/bin/python -m pytest -q       # 327 test

# 2) YEDEK — göçten önce (15.1)

# 3) Kodu yükle
cd ..
rsync -az --delete frontend/dist/ root@46.225.109.40:/opt/vardiya/web/
rsync -az --delete --exclude '.venv/' --exclude '__pycache__/' \
      --exclude '.pytest_cache/' --exclude '.ruff_cache/' --exclude '.env' \
      backend/ root@46.225.109.40:/opt/vardiya/backend/

# 4) Göçleri uygula, SONRA yeniden başlat
ssh $SSH_ANAHTARI root@46.225.109.40 'set -a; . /opt/vardiya/.env; set +a
  cd /opt/vardiya/backend
  sudo -u vardiya --preserve-env=VERITABANI_URL .venv/bin/alembic upgrade head
  sudo -u vardiya --preserve-env=VERITABANI_URL .venv/bin/alembic current
  chown -R vardiya:vardiya /opt/vardiya/backend
  systemctl restart vardiya-api vardiya-cozucu'
```

`alembic current` çıktısı **`d1f83a6c40b2 (head)`** olmalıdır. Göç kendi
doğrulamasında düşerse çıktıda `RuntimeError` görünür ve **işlem geri
alınır** — o durumda yedekten dönmeye gerek yoktur, ama sebep
araştırılmadan tekrar denenmemelidir.

**İki servis de yeniden başlatılmak zorunda.** Yeni uçlar API'de, saat
eksenli kapsama kısıtı ve yeni sütunlar işçide kullanılıyor; yalnız birini
yeniden başlatmak, talebi yazan tarafla okuyan tarafı farklı sürümlerde
bırakır.

### 15.5 Doğrulama

```bash
ssh $SSH_ANAHTARI root@46.225.109.40 'systemctl is-active vardiya-api vardiya-cozucu'
ssh $SSH_ANAHTARI root@46.225.109.40 'journalctl -u vardiya-api -u vardiya-cozucu --since "5 min ago" -p warning'

# Yeni uçlar oturumsuz 401 dönmeli
for yol in /api/talep /api/talep/1; do
  curl -s -o /dev/null -w "$yol -> %{http_code}\n" \
    -X POST https://vardiya.omerharmankaya.com$yol
done   # ikisi de 401

# Kaldırılan uç artık YOK: 404 ya da 405 dönmeli, 401 DEĞİL.
# 401 dönerse eski kod hâlâ ayakta demektir.
curl -s -o /dev/null -w 'PUT /api/talep -> %{http_code}\n' \
  -X PUT https://vardiya.omerharmankaya.com/api/talep

# Dönüşüm gerçekten oldu mu — talep artık aralık taşıyor
ssh $SSH_ANAHTARI root@46.225.109.40 'set -a; . /opt/vardiya/.env; set +a
  psql "$VERITABANI_URL" -tAc "
    select column_name from information_schema.columns
     where table_name = '"'"'talep'"'"'
       and column_name in ('"'"'baslangic'"'"','"'"'bitis'"'"','"'"'vardiya_tipi_id'"'"')
     order by column_name;
    select count(*) as talep_satiri from talep;
    select sum(gereken_sayi * ((extract(hour from bitis)::int
           - extract(hour from baslangic)::int + 24) % 24
           + case when extract(hour from bitis) = extract(hour from baslangic)
                  then 24 else 0 end)) as kisi_saat from talep;"'
```

`baslangic` ve `bitis` görünmeli, `vardiya_tipi_id` **görünmemelidir**.

Arayüzde gözle bakılacaklar (oturum açmayı gerektirir):

- **Tanımlar → Talep**: liste hâlinde aralıklar, gün sonu **24.00** olarak
  yazılı (`08.00–24.00`, `00.00–08.00`). Sağ üstte Ekle · Değiştir · Sil.
  Bir aralık eklenip düzenlenebilmeli ve silinebilmeli; aynı nokta ve gün
  tipi için çakışan bir aralık girildiğinde **hangi aralıkla çakıştığını
  söyleyen** bir hata çıkmalı.
- **Tanımlar → Vardiya Tipi**: var olan bir bloğun saatlerinin aynısıyla
  ikinci bir blok açmayı denediğinizde reddedilmeli; 12 saatlik bir blok
  "günlük azami 11 saat" diyerek reddedilmeli.
- **Tanımlar → Personel**: formda **Devir Fazla Çalışma (saat)** ve
  **Kota Yılı** alanları. Boş bırakılabilir.
- **Analiz / Sürümler**: açık sayıları **sıfırlanmış** olacak (15.1);
  bir sürümü yeniden çözünce açıklar aralık olarak geri gelmeli.

### 15.6 Geri alma

Önce eski kod sürümüne dönülür, sonra göç geri alınır:

```bash
ssh $SSH_ANAHTARI root@46.225.109.40 'cd /opt/vardiya/backend
  sudo -u vardiya --preserve-env=VERITABANI_URL .venv/bin/alembic downgrade c9a4b7e21f38'
```

**Geri alma her zaman başarılı olmaz ve bu bilinçlidir.** `downgrade`, her
talep aralığını **birebir eşleşen** bir çalışma bloğuna geri bağlar;
eşleşme bulunamayan bir satır varsa **durur**. Yani bu çıkıştan sonra
katalogla hizalanmayan bir aralık girilirse (örneğin `09.00–17.00`), geri
alma o satır silinene ya da uygun bir blok tanımlanana kadar mümkün
olmaz. Alternatif, satırı sessizce düşürmekti; o da talebi azaltır ve
hiçbir raporda görünmez.

`kapsama_acigi` / `fazla_kadro` satırları geri almada da boşaltılır (ileri
yönde zaten taşınmamışlardı). Atama, sürüm ve tanım verisi etkilenmez.

Yedekten tam dönüş gerekirse:

```bash
ssh $SSH_ANAHTARI root@46.225.109.40 'set -a; . /opt/vardiya/.env; set +a
  systemctl stop vardiya-api vardiya-cozucu
  pg_restore -c -d "$VERITABANI_URL" /opt/vardiya/yedek/vardiya-<ZAMAN>.dump
  systemctl start vardiya-api vardiya-cozucu'
```

### 15.7 Çıkış kaydı

_Dağıtım yapıldığında doldurulacak._

| | |
|---|---|
| Kod sürümü | `c149314` |
| Göçler | `→ d1f83a6c40b2` |
| Yedek dosyası | — |
| Talep satırı / kişi-saat (öncesi → sonrası) | — |
| Servisler | — |
| Uyarı/hata günlüğü | — |
| Silinen açık/fazla kadro satırı | — |

### 15.8 12.08.2026 — yarım dağıtım ve toparlanması

**Ne oldu.** `RSYNC_RSH` tanımlandı, `SSH_ANAHTARI` tanımlanmadı (o gün
runbook yalnızca birincisini yazıyordu). Sonuç: **rsync geçti, ssh
geçmedi.**

| Adım | Sonuç |
|---|---|
| Yedek | ❌ `Permission denied (publickey)` |
| `rsync` frontend + backend | ✅ yüklendi |
| `alembic upgrade head` | ❌ `Permission denied (publickey)` |
| `systemctl restart` | ❌ çalışmadı |

Yani **canlıda yeni arayüz, eski backend** kaldı. Yayındaki paket
(`index-CVUlCaag.js`) yeni ekranı taşıyordu ("talep aralıkları", "Devir
Fazla Çalışma"), API ise hâlâ eski sözleşmeyi konuşuyordu:
`PUT /api/talep` → 401 (uç duruyor), `POST /api/talep` → 405 (uç yok).

**İki somut sonucu vardı:**

1. **Talep ekranı canlıda kırıktı.** Yeni arayüz `POST /api/talep`e
   yazıyor, eski backend 405 dönüyordu.
2. **`vardiya-api` herhangi bir sebeple yeniden başlasaydı** (çökme,
   reboot) diskteki YENİ kod, göç edilmemiş ESKİ şemayla açılacaktı;
   talep sorguları var olmayan `baslangic` sütununu okuyup düşerdi.

**Ders — runbook'a işlendi.** `RSYNC_RSH` bir rsync değişkenidir ve düz
`ssh` onu okumaz. Runbook artık her `ssh` çağrısında `$SSH_ANAHTARI`
taşıyor ve iki değişkeni birlikte tanımlatıyor. Sessiz kısmi başarı en
kötü kip: komutlar `&&` ile zincirlenmediği için her biri kendi başına
düştü ve dağıtım yarıda kaldı.

**Toparlama sırası** — yedeksiz göç yok, ama pencere de hızla kapanmalı:

```bash
export SSH_ANAHTARI="-o IdentitiesOnly=yes -i $HOME/.ssh/vera_hetzner"
export RSYNC_RSH="ssh $SSH_ANAHTARI"

# Tek zincir: yedek başarısız olursa göç ÇALIŞMAZ.
ssh $SSH_ANAHTARI root@46.225.109.40 'set -a; . /opt/vardiya/.env; set +a
  mkdir -p /opt/vardiya/yedek
  pg_dump "$VERITABANI_URL" -Fc -f /opt/vardiya/yedek/vardiya-$(date +%Y%m%d-%H%M).dump
  ls -lh /opt/vardiya/yedek/ | tail -3
  cd /opt/vardiya/backend
  sudo -u vardiya --preserve-env=VERITABANI_URL .venv/bin/alembic upgrade head
  sudo -u vardiya --preserve-env=VERITABANI_URL .venv/bin/alembic current
  chown -R vardiya:vardiya /opt/vardiya/backend
  systemctl restart vardiya-api vardiya-cozucu'
```

Kod zaten sunucuda olduğu için rsync adımı tekrarlanmaz; tekrarlanması da
zararsızdır.
