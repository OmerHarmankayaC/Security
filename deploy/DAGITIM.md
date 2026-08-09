# Dağıtım Kaydı ve Yeniden Kurulum Rehberi

**Durum:** kurulum tamamlandı, **servisler sırlar beklediği için
başlatılmadı.**
**Sunucu:** 46.225.109.40 (Hetzner), Ubuntu 26.04 LTS, 4 çekirdek / 7,6 GB
**Son güncelleme:** 08.08.2026

Bu dosya iki işi birden yapar: (a) yapılan her dağıtım adımının kaydı,
(b) sıfırdan yeniden kurulum rehberi. Dağıtım ilerledikçe her adım
gerçekte çalıştırılan komutla birlikte buraya işlenir; "şöyle yapılmalı"
değil "şöyle yapıldı" yazılır.

> **Sırlar bu dosyada yer almaz.** Veritabanı parolası, çalışan paneli
> HMAC sırrı ve benzeri hiçbir değer bu dosyaya, bir betiğe veya kaynak
> koda yazılmaz. Hepsi yalnızca sunucudaki `.env` içinde durur ve
> uygulamayı kuran kişi tarafından doldurulur (bölüm 3).

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
| `CALISAN_PANELI_BAGLANTI_ANAHTARI` | Uzun, rastgele bir dize | `python -c "import secrets; print(secrets.token_urlsafe(48))"` |

`CALISAN_PANELI_BAGLANTI_ANAHTARI` sonradan değiştirilirse **daha önce
dağıtılmış bütün çalışan paneli bağlantıları geçersiz olur**; yenileri
`python scripts/calisan_baglantisi_uret.py` ile üretilir.

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
      backend/ root@SUNUCU:/opt/vardiya/backend/
rsync -az deploy/ root@SUNUCU:/opt/vardiya/deploy/
scp .env.example root@SUNUCU:/opt/vardiya/.env.example
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

## 5. Veritabanı — SIR BEKLİYOR

- [x] `vardiya` rolü ve `vardiya` veritabanı (önceden hazırdı)
- [ ] `.env` içindeki `VERITABANI_URL` doldurulacak (bölüm 3)
- [ ] `sudo -u vardiya .venv/bin/alembic upgrade head` — **parola girilmeden
      çalıştırılamaz**, TIMESTAMPTZ göçü (`c8f2d1a45b73`) dahil

## 6. Frontend — YAPILDI

Yerelde derlenip yüklendi (sunucuda Node.js yok):

```bash
cd frontend && npm ci && npm run build
rsync -az --delete frontend/dist/ root@SUNUCU:/opt/vardiya/web/
```

## 7. Servisler — SIR BEKLİYOR

Unit dosyaları kuruldu ve doğrulandı, **başlatılmadı**:

```bash
cp /opt/vardiya/deploy/vardiya-api.service /etc/systemd/system/
cp /opt/vardiya/deploy/vardiya-cozucu.service /etc/systemd/system/
systemctl daemon-reload
systemd-analyze verify /etc/systemd/system/vardiya-api.service      # temiz
systemd-analyze verify /etc/systemd/system/vardiya-cozucu.service   # temiz
```

Sırlar doldurulduktan sonra:

```bash
systemctl enable --now vardiya-api.service vardiya-cozucu.service
systemctl reload caddy          # Caddy bloğu henüz devrede DEĞİL
journalctl -u vardiya-api -u vardiya-cozucu -n 50
curl -s https://vardiya.omerharmankaya.com/api/health
```

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

`reload` bilerek ertelendi: servisler başlamadan reload edilirse site
yayına girer ama `/api` 502 döner. Reload, servislerin başlatılmasıyla
birlikte yapılacak.

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

## 8. Dağıtım sonrası kabul ölçümü

> Doldurulacak (bkz. `docs/PERFORMANS_NOTU.md`).

**UYARI:** `scripts/kabul_olcumu.py` ve `scripts/demo_veri_uret.py --reset`
veritabanındaki tanım/girdi/kural/sonuç tablolarını **temizler**. Ölçüm bu
yüzden gerçek kullanım başlamadan önce yapılmalıdır.

- [ ] `python scripts/kabul_olcumu.py` (ve `--json` çıktısının saklanması)
- [ ] Tüm test takımı + çözücü-doğrulayıcı uyum testi
- [ ] K6: demo veri → çöz → yayınla → izin ekle → yeniden çöz → `GET /api/surum/karsilastir`
- [ ] Sonuçların `docs/PERFORMANS_NOTU.md`'ye **ikinci sütun** olarak işlenmesi (mevcut ölçüm makinesi sütunu silinmez)
