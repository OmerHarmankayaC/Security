# Kabul Ölçümü — Ortam ve Bağlam (26.08.2026)

Bu dosya `kabul-20260826-*.json` çıktılarının yanına, ölçümün rapora
yazılabilmesi için gereken ve JSON'da bulunmayan bilgileri kaydeder.

## Ölçüm ortamı

| | |
|---|---|
| Sunucu | Adanmış bulut sunucu, Ubuntu 26.04 LTS, **4 çekirdek / 7 GB** |
| Çekirdek (kernel) | Linux 7.0.0-29-generic x86_64, glibc 2.43 |
| PostgreSQL | **18.6** |
| Python | **3.14.4** |
| OR-Tools | **9.15.6755** |
| Çözücü arama işçisi | **3** (SDD 3.4.3: çekirdek − 1) |
| Çözücü zaman limiti | Yayında **60 sn** (`/opt/vardiya/.env`); ölçüm 60 ve 300 sn ile ayrı ayrı alındı |
| Ölçüm tarihi | 26.08.2026 |
| Commit | **f5c75cd** — dağıtılan backend ağacı (107 .py dosyası) local HEAD ile hash bazında birebir doğrulandı |

Ölçüm üretim veritabanında DEĞİL, aynı sunucuda açılan ayrı bir
`vardiya_olcum` veritabanında alındı (göçler head `f4a8c1e60d92`).
Betik kendi referans örneğini kurduğu için sayılar üretim verisinden
bağımsızdır; üretim verisi (30 personel, 12 çizelge sürümü, 1364 atama)
korundu. Ölçüm öncesi yedek: `yedek/vardiya-20260826-0808-olcum-oncesi.dump`.

## Referans örnek

| | |
|---|---|
| Kadro | **40 personel** — 9 kişi (Vardiya Şefi + Güvenlik Görevi), 31 kişi (Güvenlik Görevi) |
| Planlama dönemi | **28 gün**, 02.02.2026 – 01.03.2026 |
| Toplam talep | **4.608 kişi-saat** (SRS 3.3.6: 1.152 kişi-saat/hafta × 4) |
| Gece talebi | **1.600 kişi-saat** (gece = 20:00–06:00, SRS TD-2) |
| Görev noktaları | Vardiya Şefliği (gün boyu 1 kişi), Güvenlik (08–24 arası 9, gece 3; hafta sonu/tatil 3) |

Gösterim verisinin 30 kişiye inmesi ölçümü etkilemez: `kabul_olcumu.py`
kendi kadrosunu kurar (`REFERANS_PERSONEL_SAYISI = 40`). Raporda referans
örnek **40 × 28** olarak sabitlenmelidir.

## Aktif kurallar

**Zorunlu (hepsi aktif):** H1 (asgari blok 4 sa), H2 (asgari dinlenme 16 sa),
H3 (azami ardışık gece 3, gece eşiği 4 sa), H4 (azami ardışık çalışma 6 gün),
H5 (haftalık mutlak tavan 66 sa), H6 (haftalık asgari izin 1 gün), H7, H8,
H9 (azami günlük 11 sa), H10 (fazla çalışma eşiği 45, yıllık kota 270).

**Esnek (hepsi aktif, kalibre ağırlıklarla):** S1=10000, S2=40, S3=35, S4=5,
S5=20, S6=10, S6b=10, S7=15, S8=15.

> Not: ölçümün kural kümesi üretimdekiyle birebir aynı değil — üretimde
> `S6b` pasif ve ayrıca `S1f` tanımlı. Ölçüm betiği kendi kataloğunu kurar.

## K4 çelişkisinin kurgusu

9 Vardiya Şefi'nin **7'si dönem boyunca yıllık izinli**. Kalan 2 kişi H5'in
66 saatlik tavanı altında haftada en çok 132 kişi-saat verebilir; Vardiya
Şefliği noktası kesintisiz dolu olmak için haftada 168 kişi-saat ister.
Açık aritmetiktir ve hiçbir blok bileşimiyle kapatılamaz.

## Ön kontroller (üretim veritabanı, salt-okunur)

1. **S1 aktif** (`S1 | ESNEK | t`). Sessiz toggle sorunu yok; K4 anlamlı.
2. **Göç c4f1a7d20b93 üretimde uygulanmış** — `alembic_version` = `f4a8c1e60d92`
   (head), c4f1a7d20b93 dört göç geride kaldı. `tercih` tablosunda kopya yok.
3. **Hesaplar korundu** — 3 yönetim + 1 personele bağlı hesap yerinde.
   `VERI_TEMIZLIGINE_IZIN` `.env`'e yazılmadı, koşum başına satır içi verildi;
   `backend/.env` sunucuda yok.

## Ölçümün kapsamadığı

**K6 aksama ölçmüyor.** `_k6` aynı dönemi aksama olmadan yeniden çözüp iki
sürümü karşılaştırır. Raporlanan sayı (60 sn'de 310, 300 sn'de 998) bir
aksamaya verilen tepki değil, iki koşum arasındaki çözücü belirlenimsizliğidir.
"Yayınlanmış çizelge küçük bir aksamayla yeniden çözüldüğünde değişen atama
sayısı" ölçülmek isteniyorsa betiğe aksama adımı (ör. bir kişiye 4 gün izin)
eklenmelidir.
