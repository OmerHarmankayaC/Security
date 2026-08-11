# Veritabanı Şeması — canlı şemadan üretilmiştir

> `information_schema` ve `pg_catalog` sorgulanarak üretildi; modellerden
> ya da göç dosyalarından değil, **çalışan veritabanından** okundu.
> Göç başı: `a4d92c15e807`. PostgreSQL 18.

**19 uygulama tablosu** (+ `alembic_version`), **10 enum tipi**.

## Ortak sözleşme

`alembic_version` dışındaki her tabloda iki zaman damgası örtüktür ve
aşağıdaki tablolarda tekrar edilmemiştir:

| Alan | Tip | Not |
| --- | --- | --- |
| `olusturma_zamani` | TIMESTAMPTZ NOT NULL | `server_default now()` |
| `guncelleme_zamani` | TIMESTAMPTZ NOT NULL | `server_default now()` |

Tek istisna **`oturum`**: zaman damgası karışımını kullanmaz, kendi
`olusturma` / `son_erisim` / `gecerlilik_bitis` alanlarını taşır — hareketsizlik
ölçümü `son_erisim` üzerinden yapıldığı için `guncelleme_zamani` aynı olguyu
ikinci bir adla taşıyacaktı.

## Enum tipleri

| Tip | Değerler |
| --- | --- |
| `atamakaynagi` | `COZUCU`, `MANUEL` |
| `cizelgesurumudurumu` | `TASLAK`, `COZULDU`, `YAYINLANDI`, `ARSIV` |
| `cozumisidurumu` | `KUYRUKTA`, `ON_KONTROL`, `COZULUYOR`, `TAMAMLANDI`, `UYARILI`, `BASARISIZ`, `IPTAL` |
| `guntipi` | `HAFTA_ICI`, `HAFTA_SONU`, `RESMI_TATIL` |
| `kuraltipi` | `ZORUNLU`, `ESNEK` |
| `musaitlikdilimi` | `TAM_GUN`, `OGLEDEN_ONCE`, `OGLEDEN_SONRA` |
| `musaitliktipi` | `YILLIK_IZIN`, `RAPOR`, `EGITIM`, `MAZERET` |
| `rol` | `CALISAN`, `YONETICI`, `YONETIM` |
| `tercihdurumu` | `BEKLEMEDE`, `ONAYLANDI`, `REDDEDILDI` |
| `tercihtipi` | `CALISMAMA`, `VARDIYA_TIPI_TERCIHI` |

## Tanım varlıkları

### `personel`

| Sütun | Tip | Null | Varsayılan | Anahtar |
| --- | --- | --- | --- | --- |
| `personel_id` | INT | hayır | *(otomatik)* | **PK** |
| `ad_soyad` | VARCHAR | hayır | — | — |
| `sicil_no` | VARCHAR | hayır | — | UNIQUE |
| `haftalik_hedef_saat` | INT | hayır | — | — |
| `sabit_vardiya_tipi_id` | INT | evet | — | FK → `vardiya_tipi.vardiya_tipi_id` |
| `aktif_baslangic` | DATE | hayır | — | — |
| `aktif_bitis` | DATE | evet | — | — |

### `yetkinlik`

| Sütun | Tip | Null | Varsayılan | Anahtar |
| --- | --- | --- | --- | --- |
| `yetkinlik_id` | INT | hayır | *(otomatik)* | **PK** |
| `ad` | VARCHAR | hayır | — | UNIQUE |
| `aciklama` | VARCHAR | evet | — | — |
| `aktif` | BOOLEAN | hayır | `true` | — |

### `personel_yetkinlik`

| Sütun | Tip | Null | Varsayılan | Anahtar |
| --- | --- | --- | --- | --- |
| `personel_id` | INT | hayır | — | **PK** · FK → `personel.personel_id` |
| `yetkinlik_id` | INT | hayır | — | **PK** · FK → `yetkinlik.yetkinlik_id` |

### `bina`

| Sütun | Tip | Null | Varsayılan | Anahtar |
| --- | --- | --- | --- | --- |
| `bina_id` | INT | hayır | *(otomatik)* | **PK** |
| `ad` | VARCHAR | hayır | — | — |
| `aktif` | BOOLEAN | hayır | `true` | — |

### `gorev_noktasi`

| Sütun | Tip | Null | Varsayılan | Anahtar |
| --- | --- | --- | --- | --- |
| `nokta_id` | INT | hayır | *(otomatik)* | **PK** |
| `ad` | VARCHAR | hayır | — | — |
| `bina_id` | INT | evet | — | FK → `bina.bina_id` |
| `onkosul_yetkinlik_id` | INT | evet | — | FK → `yetkinlik.yetkinlik_id` |
| `aktif` | BOOLEAN | hayır | `true` | — |

### `vardiya_tipi`

| Sütun | Tip | Null | Varsayılan | Anahtar |
| --- | --- | --- | --- | --- |
| `vardiya_tipi_id` | INT | hayır | *(otomatik)* | **PK** |
| `ad` | VARCHAR | hayır | — | — |
| `baslangic_saati` | TIME | hayır | — | — |
| `bitis_saati` | TIME | hayır | — | — |
| `sure_saat` | NUMERIC(4,2) | hayır | — | — |
| `gece_mi` | BOOLEAN | hayır | — | — |
| `aktif` | BOOLEAN | hayır | `true` | — |

### `talep`

| Sütun | Tip | Null | Varsayılan | Anahtar |
| --- | --- | --- | --- | --- |
| `talep_id` | INT | hayır | *(otomatik)* | **PK** |
| `nokta_id` | INT | hayır | — | FK → `gorev_noktasi.nokta_id` |
| `vardiya_tipi_id` | INT | hayır | — | FK → `vardiya_tipi.vardiya_tipi_id` |
| `gun_tipi` | ENUM guntipi | hayır | — | — |
| `tarih` | DATE | evet | — | — |
| `gereken_sayi` | INT | hayır | — | — |

### `ozel_gun`

| Sütun | Tip | Null | Varsayılan | Anahtar |
| --- | --- | --- | --- | --- |
| `tarih` | DATE | hayır | — | **PK** |
| `ad` | VARCHAR | hayır | — | — |

## Kimlik varlıkları

### `kullanici`

| Sütun | Tip | Null | Varsayılan | Anahtar |
| --- | --- | --- | --- | --- |
| `kullanici_id` | INT | hayır | *(otomatik)* | **PK** |
| `kullanici_adi` | VARCHAR | hayır | — | UNIQUE |
| `parola_ozeti` | VARCHAR | hayır | — | — |
| `rol` | ENUM rol | hayır | — | — |
| `personel_id` | INT | evet | — | FK → `personel.personel_id` |
| `parola_degistirmeli` | BOOLEAN | hayır | `false` | — |
| `aktif` | BOOLEAN | hayır | `true` | — |
| `basarisiz_deneme` | INT | hayır | `0` | — |
| `kilit_bitis` | TIMESTAMPTZ | evet | — | — |

**CHECK** `ck_kullanici_adi_kucuk_harf`: `CHECK (((kullanici_adi)::text = lower((kullanici_adi)::text)))`
**CHECK** `ck_kullanici_calisan_personele_bagli`: `CHECK (((rol <> 'CALISAN'::rol) OR (personel_id IS NOT NULL)))`

### `oturum`

| Sütun | Tip | Null | Varsayılan | Anahtar |
| --- | --- | --- | --- | --- |
| `oturum_id` | VARCHAR(64) | hayır | — | **PK** |
| `kullanici_id` | INT | hayır | — | FK → `kullanici.kullanici_id` ON DELETE CASCADE |
| `olusturma` | TIMESTAMPTZ | hayır | — | — |
| `son_erisim` | TIMESTAMPTZ | hayır | — | — |
| `gecerlilik_bitis` | TIMESTAMPTZ | hayır | — | — |

## Girdi varlıkları

### `musaitlik`

| Sütun | Tip | Null | Varsayılan | Anahtar |
| --- | --- | --- | --- | --- |
| `musaitlik_id` | INT | hayır | *(otomatik)* | **PK** |
| `personel_id` | INT | hayır | — | FK → `personel.personel_id` |
| `baslangic_tarihi` | DATE | hayır | — | — |
| `bitis_tarihi` | DATE | hayır | — | — |
| `dilim` | ENUM musaitlikdilimi | hayır | — | — |
| `tip` | ENUM musaitliktipi | hayır | — | — |
| `not` | VARCHAR | evet | — | — |

### `tercih`

| Sütun | Tip | Null | Varsayılan | Anahtar |
| --- | --- | --- | --- | --- |
| `tercih_id` | INT | hayır | *(otomatik)* | **PK** |
| `personel_id` | INT | hayır | — | FK → `personel.personel_id` |
| `donem_id` | INT | hayır | — | FK → `donem.donem_id` |
| `tarih` | DATE | hayır | — | — |
| `tip` | ENUM tercihtipi | hayır | — | — |
| `vardiya_tipi_id` | INT | evet | — | FK → `vardiya_tipi.vardiya_tipi_id` |
| `durum` | ENUM tercihdurumu | hayır | — | — |
| `calisan_notu` | VARCHAR | evet | — | — |
| `ret_gerekcesi` | VARCHAR | evet | — | — |

## Kural varlığı

### `kural`

| Sütun | Tip | Null | Varsayılan | Anahtar |
| --- | --- | --- | --- | --- |
| `kural_id` | INT | hayır | *(otomatik)* | **PK** |
| `kimlik` | VARCHAR | hayır | — | UNIQUE |
| `tip` | ENUM kuraltipi | hayır | — | — |
| `parametreler` | JSONB | hayır | — | — |
| `agirlik` | INT | evet | — | — |
| `aktif` | BOOLEAN | hayır | `true` | — |

## Sonuç varlıkları

### `donem`

| Sütun | Tip | Null | Varsayılan | Anahtar |
| --- | --- | --- | --- | --- |
| `donem_id` | INT | hayır | *(otomatik)* | **PK** |
| `baslangic_tarihi` | DATE | hayır | — | — |
| `bitis_tarihi` | DATE | hayır | — | — |
| `tercih_son_tarihi` | DATE | hayır | — | — |

### `cizelge_surumu`

| Sütun | Tip | Null | Varsayılan | Anahtar |
| --- | --- | --- | --- | --- |
| `surum_id` | INT | hayır | *(otomatik)* | **PK** |
| `donem_id` | INT | hayır | — | FK → `donem.donem_id` |
| `surum_no` | INT | hayır | — | — |
| `durum` | ENUM cizelgesurumudurumu | hayır | — | — |
| `onceki_surum_id` | INT | evet | — | FK → `cizelge_surumu.surum_id` |
| `yayin_zamani` | TIMESTAMPTZ | evet | — | — |

### `atama`

| Sütun | Tip | Null | Varsayılan | Anahtar |
| --- | --- | --- | --- | --- |
| `atama_id` | INT | hayır | *(otomatik)* | **PK** |
| `surum_id` | INT | hayır | — | FK → `cizelge_surumu.surum_id` · UNIQUE |
| `personel_id` | INT | hayır | — | FK → `personel.personel_id` · UNIQUE |
| `tarih` | DATE | hayır | — | UNIQUE |
| `vardiya_tipi_id` | INT | hayır | — | FK → `vardiya_tipi.vardiya_tipi_id` |
| `nokta_id` | INT | hayır | — | FK → `gorev_noktasi.nokta_id` |
| `kilitli` | BOOLEAN | hayır | — | — |
| `kaynak` | ENUM atamakaynagi | hayır | — | — |

**Bileşik UNIQUE** `uq_atama_surum_personel_tarih`: (surum_id, personel_id, tarih)

### `cozum_isi`

| Sütun | Tip | Null | Varsayılan | Anahtar |
| --- | --- | --- | --- | --- |
| `is_id` | INT | hayır | *(otomatik)* | **PK** |
| `surum_id` | INT | hayır | — | FK → `cizelge_surumu.surum_id` |
| `durum` | ENUM cozumisidurumu | hayır | — | — |
| `baslangic_zamani` | TIMESTAMPTZ | hayır | — | — |
| `bitis_zamani` | TIMESTAMPTZ | evet | — | — |
| `sure_saniye` | NUMERIC(10,3) | evet | — | — |
| `zaman_limiti_saniye` | INT | hayır | — | — |
| `en_iyi_ceza` | NUMERIC(12,2) | evet | — | — |
| `ceza_dokumu` | JSONB | evet | — | — |
| `kural_anlik_goruntu` | JSONB | hayır | — | — |
| `hata_mesaji` | VARCHAR | evet | — | — |

### `kapsama_acigi`

| Sütun | Tip | Null | Varsayılan | Anahtar |
| --- | --- | --- | --- | --- |
| `acik_id` | INT | hayır | *(otomatik)* | **PK** |
| `surum_id` | INT | hayır | — | FK → `cizelge_surumu.surum_id` |
| `tarih` | DATE | hayır | — | — |
| `vardiya_tipi_id` | INT | hayır | — | FK → `vardiya_tipi.vardiya_tipi_id` |
| `nokta_id` | INT | hayır | — | FK → `gorev_noktasi.nokta_id` |
| `eksik_sayi` | INT | hayır | — | — |

### `fazla_kadro`

| Sütun | Tip | Null | Varsayılan | Anahtar |
| --- | --- | --- | --- | --- |
| `fazla_id` | INT | hayır | *(otomatik)* | **PK** |
| `surum_id` | INT | hayır | — | FK → `cizelge_surumu.surum_id` |
| `tarih` | DATE | hayır | — | — |
| `vardiya_tipi_id` | INT | hayır | — | FK → `vardiya_tipi.vardiya_tipi_id` |
| `nokta_id` | INT | hayır | — | FK → `gorev_noktasi.nokta_id` |
| `fazla_sayi` | INT | hayır | — | — |

## Altyapı

### `alembic_version`

| Sütun | Tip | Null | Varsayılan | Anahtar |
| --- | --- | --- | --- | --- |
| `version_num` | VARCHAR(32) | hayır | — | **PK** |

## Yabancı anahtar özeti (ER diyagramının ilişki listesi)

| Kaynak | Sütun | Hedef | ON DELETE |
| --- | --- | --- | --- |
| `atama` | `nokta_id` | `gorev_noktasi.nokta_id` | NO ACTION |
| `atama` | `personel_id` | `personel.personel_id` | NO ACTION |
| `atama` | `surum_id` | `cizelge_surumu.surum_id` | NO ACTION |
| `atama` | `vardiya_tipi_id` | `vardiya_tipi.vardiya_tipi_id` | NO ACTION |
| `cizelge_surumu` | `donem_id` | `donem.donem_id` | NO ACTION |
| `cizelge_surumu` | `onceki_surum_id` | `cizelge_surumu.surum_id` | NO ACTION |
| `cozum_isi` | `surum_id` | `cizelge_surumu.surum_id` | NO ACTION |
| `fazla_kadro` | `nokta_id` | `gorev_noktasi.nokta_id` | NO ACTION |
| `fazla_kadro` | `surum_id` | `cizelge_surumu.surum_id` | NO ACTION |
| `fazla_kadro` | `vardiya_tipi_id` | `vardiya_tipi.vardiya_tipi_id` | NO ACTION |
| `gorev_noktasi` | `bina_id` | `bina.bina_id` | NO ACTION |
| `gorev_noktasi` | `onkosul_yetkinlik_id` | `yetkinlik.yetkinlik_id` | NO ACTION |
| `kapsama_acigi` | `nokta_id` | `gorev_noktasi.nokta_id` | NO ACTION |
| `kapsama_acigi` | `surum_id` | `cizelge_surumu.surum_id` | NO ACTION |
| `kapsama_acigi` | `vardiya_tipi_id` | `vardiya_tipi.vardiya_tipi_id` | NO ACTION |
| `kullanici` | `personel_id` | `personel.personel_id` | NO ACTION |
| `musaitlik` | `personel_id` | `personel.personel_id` | NO ACTION |
| `oturum` | `kullanici_id` | `kullanici.kullanici_id` | CASCADE |
| `personel` | `sabit_vardiya_tipi_id` | `vardiya_tipi.vardiya_tipi_id` | NO ACTION |
| `personel_yetkinlik` | `personel_id` | `personel.personel_id` | NO ACTION |
| `personel_yetkinlik` | `yetkinlik_id` | `yetkinlik.yetkinlik_id` | NO ACTION |
| `talep` | `nokta_id` | `gorev_noktasi.nokta_id` | NO ACTION |
| `talep` | `vardiya_tipi_id` | `vardiya_tipi.vardiya_tipi_id` | NO ACTION |
| `tercih` | `donem_id` | `donem.donem_id` | NO ACTION |
| `tercih` | `personel_id` | `personel.personel_id` | NO ACTION |
| `tercih` | `vardiya_tipi_id` | `vardiya_tipi.vardiya_tipi_id` | NO ACTION |

## İndeksler (birincil anahtar dışı)

| Tablo | İndeks | Tanım |
| --- | --- | --- |
| `alembic_version` | `alembic_version_pkc` | `btree (version_num)` |
| `atama` | `uq_atama_surum_personel_tarih` | `btree (surum_id, personel_id, tarih)` |
| `fazla_kadro` | `ix_fazla_kadro_surum_id` | `btree (surum_id)` |
| `kullanici` | `kullanici_kullanici_adi_key` | `btree (kullanici_adi)` |
| `kural` | `kural_kimlik_key` | `btree (kimlik)` |
| `oturum` | `ix_oturum_kullanici_id` | `btree (kullanici_id)` |
| `personel` | `personel_sicil_no_key` | `btree (sicil_no)` |
| `yetkinlik` | `yetkinlik_ad_key` | `btree (ad)` |
