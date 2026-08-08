# Dağıtım Kaydı ve Yeniden Kurulum Rehberi

**Durum:** hazırlık aşaması — sunucuya **henüz çıkılmadı.**
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
| İşletim sistemi | Linux, systemd |
| Kurulum kökü | `/opt/vardiya` |
| Servis kullanıcısı | `vardiya` (sistem kullanıcısı, giriş kabuğu yok) |
| Uygulama sunucusu | uvicorn, `127.0.0.1:8000`, tek işçi |
| Ters vekil | Caddy — statik frontend + `/api` yönlendirmesi |
| Veritabanı | PostgreSQL, aynı makine |
| Çözücü paralelliği | `COZUCU_ARAMA_ISCISI_SAYISI=3` (SDD 3.4.3: çekirdek −1) |

**Neden tek uvicorn işçisi:** çözüm yükü ayrı serviste çalışır; API süreci
yalnızca istek işler. Birden fazla uvicorn işçisi açmak dört çekirdeğin bir
kısmını çözücüden alır ve SDD 3.4.3'teki çekirdek paylaşımı kararını bozar.

## 2. Paket içeriği (`deploy/`)

| Dosya | İşlev |
|---|---|
| `uygulama.service` | API (uvicorn) systemd unit'i |
| `cozum-isci.service` | Çözücü işçisi systemd unit'i |
| `DAGITIM.md` | bu dosya |
| `../.env.example` | tüm ortam değişkenleri, sır gerektirenler işaretli |

## 3. Doldurulması gereken sırlar

Aşağıdaki iki değer `.env` içinde **boş bırakılmıştır** ve uygulamayı kuran
kişi tarafından doldurulur. Servisler bu değerler girilmeden
başlatılmamalıdır.

| Değişken | Ne konacak | Nasıl üretilir |
|---|---|---|
| `VERITABANI_URL` | PostgreSQL `vardiya` kullanıcısının parolası (URL içindeki `PAROLA` yerine) | Parolayı siz belirleyip hem `CREATE USER` komutunda hem burada kullanın |
| `CALISAN_PANELI_BAGLANTI_ANAHTARI` | Uzun, rastgele bir dize | `python -c "import secrets; print(secrets.token_urlsafe(48))"` |

`CALISAN_PANELI_BAGLANTI_ANAHTARI` sonradan değiştirilirse **daha önce
dağıtılmış bütün çalışan paneli bağlantıları geçersiz olur**; yenileri
`python scripts/calisan_baglantisi_uret.py` ile üretilir.

## 4. Ön koşullar (sunucuda)

> Bu bölüm dağıtım yapıldıkça gerçekte çalıştırılan komutlarla doldurulacak.

- [ ] Sistem paketleri: Python 3.12+, `python3-venv`, PostgreSQL, Caddy, Node.js (frontend derlemesi için)
- [ ] `vardiya` sistem kullanıcısı
- [ ] `/opt/vardiya` dizini ve kaynak kodun yerleştirilmesi

## 5. Veritabanı

> Doldurulacak.

- [ ] `vardiya` rolü ve `vardiya` veritabanının oluşturulması (parola: bölüm 3)
- [ ] `.env` içindeki `VERITABANI_URL`'in doldurulması
- [ ] `alembic upgrade head`

## 6. Frontend

> Doldurulacak.

- [ ] `npm ci && npm run build`
- [ ] `dist/` çıktısının Caddy tarafından servis edilmesi, `/api` → `127.0.0.1:8000`

## 7. Servisler

> Doldurulacak.

- [ ] `uygulama.service` kurulumu, `enable --now`, günlük kontrolü
- [ ] `cozum-isci.service` kurulumu, `enable --now`, günlük kontrolü
- [ ] API'nin yanıt verdiğinin doğrulanması

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
