# Ek B — Uygulama Programlama Arayüzü Özeti (üretilmiş)

> Bu dosya `backend/app/main.py`'deki yönlendirme tablosundan ve
> yetkilendirme bağımlılıklarından **üretilmiştir**, elle yazılmamıştır.
> SDD Ek B'ye buradan aktarılacaktır (11.08.2026 kapanış denetimi).
>
> **Gereken Rol** sütunu, isteğin geçmek zorunda olduğu sunucu tarafı
> kapıdır (`backend/app/guvenlik.py`). Roller kapsayıcıdır: `yönetim`,
> `yönetici`nin yetkilerini içerir (SRS 5.10). `çalışan` rolü
> diğerlerinin alt kümesi DEĞİLDİR ve tersi de geçerlidir — yönetim
> rolü çalışan panelinden geçemez.

**Toplam 68 uç nokta.** SDD Ek B'nin önceki hâli 21 satır
listeliyordu ve kimlik doğrulama turunu hiç içermiyordu.

> Sayım ve **Gereken Rol** sütunu artık
> `backend/scripts/uc_noktalari_listele.py` ile uygulamadan okunuyor;
> `--denetle` bu dosyayı yönlendirme tablosuyla karşılaştırır ve fark
> varsa sıfırdan farklı bir kodla çıkar. İşlev sütunu düz metindir ve
> elle durur.

> 11.08.2026 — durdurma turu: `/api/cozum/{id}/iptal` **kaldırıldı**,
> yerine `/durdur` (sonlandırma, sonuç atılmaz), `/karar` (kullan / at /
> devam) ve `/cozum/aktif` (kabuktaki çalışan iş göstergesi) geldi.
> Uç nokta sayısı 70 → 72.
>
> 12.08.2026 — saatlik düzen turu: talep artık bir matris hücresi değil
> bir **zaman aralığı kaydıdır** (SDD 4.2.2). `PUT /api/talep`
> **kaldırıldı** — bir hücreyi yerinde güncelliyordu ve aralık
> kayıtlarında karşılığı yok; yerine `POST /api/talep`,
> `PUT /api/talep/{talep_id}` ve `DELETE /api/talep/{talep_id}` geldi.
> Üçü de listeyi ve yük göstergesini birlikte döner. Uç nokta sayısı
> 72 → 74.
>
> 13.08.2026 — gerçek saatlik model turu: blok kataloğu kalktı (SRS
> TD-13). `vardiya-tipi` uçlarının **altısı da kaldırıldı** —
> tanımlanacak bir vardiya tipi yok, blok uzunlukları çözümün
> çıktısıdır. Çalışan panelindeki `GET /api/calisan/vardiya-tipi` de
> düştü; tercih formu artık bir tip değil bir zaman aralığı alıyor
> (SRS FR-3.2). Uç nokta sayısı 74 → 68.

## Kimlik dogrulama (FR-10.1 - FR-10.3, FR-10.7)

| Uç Nokta | Yöntem | Gereken Rol | İşlev |
| --- | --- | --- | --- |
| `/api/ben` | GET | giris yapmis her rol | Oturumdaki kullanicinin kimligi ve rolu |
| `/api/cikis` | POST | giris yapmis her rol | Oturum kaydinin silinmesi (FR-10.3) |
| `/api/giris` | POST | **yok** (acik) | Kullanici adi ve parola ile giris (FR-10.1) |
| `/api/parola-degistir` | POST | giris yapmis her rol | Kullanicinin kendi parolasini degistirmesi (FR-10.7) |

## Hesap yonetimi (FR-10.5, FR-10.6)

| Uç Nokta | Yöntem | Gereken Rol | İşlev |
| --- | --- | --- | --- |
| `/api/kullanici` | GET | yonetim | Hesap listesi (FR-10.5) |
| `/api/kullanici` | POST | yonetim | Hesap olusturma; rol ve personel baglantisi (FR-10.5, FR-10.6) |
| `/api/kullanici/{kullanici_id}` | PUT | yonetim | Rol atama, devre disi birakma (FR-10.5) |
| `/api/kullanici/{kullanici_id}/parola-sifirla` | POST | yonetim | Parola sifirlama; acik oturumlari kapatir |

## Tanim yonetimi (FR-1.x)

| Uç Nokta | Yöntem | Gereken Rol | İşlev |
| --- | --- | --- | --- |
| `/api/bina` | GET | yonetici + yonetim | Bina tanimlari (FR-1.5) |
| `/api/bina` | POST | yonetici + yonetim | Bina olusturma (FR-1.5) |
| `/api/bina/{bina_id}` | PUT | yonetici + yonetim | Bina guncelleme (FR-1.5) |
| `/api/bina/{bina_id}` | DELETE | yonetici + yonetim | Silme veya pasiflestirme |
| `/api/bina/{bina_id}/kullanim` | GET | yonetici + yonetim | Silme oncesi kullanim dokumu |
| `/api/kural` | GET | yonetici + yonetim | Kural katalogu, parametre tanimlariyla (FR-1.11, FR-1.12) |
| `/api/kural/{kimlik}` | PUT | yonetici + yonetim | Parametre, agirlik ve aktiflik (FR-1.11 - FR-1.13) |
| `/api/nokta` | GET | yonetici + yonetim | Gorev noktasi tanimlari (FR-1.6) |
| `/api/nokta` | POST | yonetici + yonetim | Gorev noktasi olusturma (FR-1.6) |
| `/api/nokta/{nokta_id}` | PUT | yonetici + yonetim | Gorev noktasi guncelleme (FR-1.6) |
| `/api/nokta/{nokta_id}` | DELETE | yonetici + yonetim | Silme veya pasiflestirme |
| `/api/nokta/{nokta_id}/kullanim` | GET | yonetici + yonetim | Silme oncesi kullanim dokumu |
| `/api/ozel-gun` | GET | yonetici + yonetim | Resmi tatil takvimi (FR-1.10) |
| `/api/ozel-gun` | POST | yonetici + yonetim | Tarihi resmi tatil isaretleme (FR-1.10) |
| `/api/ozel-gun/{tarih}` | PUT | yonetici + yonetim | Tatil adinin degistirilmesi (FR-1.10) |
| `/api/ozel-gun/{tarih}` | DELETE | yonetici + yonetim | Isaretin kaldirilmasi (FR-1.10) |
| `/api/personel` | GET | yonetici + yonetim | Personel kayitlari (FR-1.1) |
| `/api/personel` | POST | yonetici + yonetim | Personel kaydi olusturma (FR-1.1); sicil cakismasinda 409 |
| `/api/personel/{personel_id}` | PUT | yonetici + yonetim | Personel kaydi guncelleme (FR-1.1); sicil cakismasinda 409 |
| `/api/personel/{personel_id}` | DELETE | yonetici + yonetim | Silme veya pasiflestirme (aktif_bitis) |
| `/api/personel/{personel_id}/kullanim` | GET | yonetici + yonetim | Silme oncesi kullanim dokumu |
| `/api/talep` | GET | yonetici + yonetim | Talep araliklari ve yuk gostergesi (FR-1.7, FR-1.9) |
| `/api/talep` | POST | yonetici + yonetim | Yeni talep araligi (FR-1.7); cakisan aralikta 409 |
| `/api/talep/{talep_id}` | PUT | yonetici + yonetim | Talep araliginin guncellenmesi (FR-1.8); cakisan aralikta 409 |
| `/api/talep/{talep_id}` | DELETE | yonetici + yonetim | Talep araliginin silinmesi (FR-1.8) |
| `/api/yetkinlik` | GET | yonetici + yonetim | Yetkinlik tanimlari (FR-1.2) |
| `/api/yetkinlik` | POST | yonetici + yonetim | Yetkinlik olusturma (FR-1.2) |
| `/api/yetkinlik/{yetkinlik_id}` | PUT | yonetici + yonetim | Yetkinlik guncelleme (FR-1.2) |
| `/api/yetkinlik/{yetkinlik_id}` | DELETE | yonetici + yonetim | Silme veya pasiflestirme |
| `/api/yetkinlik/{yetkinlik_id}/kullanim` | GET | yonetici + yonetim | Silme oncesi kullanim dokumu |

## Girdi yonetimi (FR-2.x, FR-3.x)

| Uç Nokta | Yöntem | Gereken Rol | İşlev |
| --- | --- | --- | --- |
| `/api/musaitlik` | GET | yonetici + yonetim | Musaitlik kayitlari (FR-2.1) |
| `/api/musaitlik` | POST | yonetici + yonetim | Musaitlik kaydi girisi (FR-2.1, FR-2.2) |
| `/api/musaitlik/{musaitlik_id}` | DELETE | yonetici + yonetim | Musaitlik kaydinin silinmesi |
| `/api/tercih` | GET | yonetici + yonetim | Tercih listesi; yonetici gorunumu (FR-3.x) |
| `/api/tercih` | POST | yonetici + yonetim | Yonetici tarafindan tercih girisi (FR-3.1, FR-3.2) |
| `/api/tercih/{tercih_id}` | PUT | yonetici + yonetim | Tercih onayi veya gerekceli reddi (FR-3.4) |

## Donem, surum ve yayin (FR-4.2, FR-7.x)

| Uç Nokta | Yöntem | Gereken Rol | İşlev |
| --- | --- | --- | --- |
| `/api/donem` | GET | yonetici + yonetim | Planlama donemleri |
| `/api/donem` | POST | yonetici + yonetim | Planlama donemi olusturma (FR-4.2) |
| `/api/surum` | GET | yonetici + yonetim | Donemdeki cizelge surumleri (FR-7.1); acik ve fazla kadro sayilariyla |
| `/api/surum` | POST | yonetici + yonetim | Yayinlanmis surumden taslak turetme (FR-7.3) |
| `/api/surum/karsilastir` | GET | yonetici + yonetim | Iki surum arasindaki fark (FR-7.5) |
| `/api/surum/{surum_id}/atama` | GET | yonetici + yonetim | Surumun atamalari |
| `/api/surum/{surum_id}/fazla-kadro` | GET | yonetici + yonetim | Talepten fazla kadro yazilmis hucreler (SRS 4.3 S1 ust siniri) |
| `/api/surum/{surum_id}/kapsama-acigi` | GET | yonetici + yonetim | Surumun kapsama aciklari (FR-5.3) |
| `/api/surum/{surum_id}/kopyala` | POST | yonetici + yonetim | Arsivden taslak kopyalama (FR-7.6) |
| `/api/surum/{surum_id}/yayinla` | POST | yonetici + yonetim | Surumun yayinlanmasi (FR-7.2) |

## Cozum ve fizibilite (FR-4.x, FR-5.x)

| Uç Nokta | Yöntem | Gereken Rol | İşlev |
| --- | --- | --- | --- |
| `/api/cozum` | POST | yonetici + yonetim | Cozum isinin baslatilmasi; is kimligi dondurur (FR-4.1) |
| `/api/cozum/aktif` | GET | yonetici + yonetim | Devam eden ya da karar bekleyen is; kabuktaki gosterge bunu yoklar (FR-4.11) |
| `/api/cozum/{is_id}` | GET | yonetici + yonetim | Cozum isinin durumu ve ilerlemesi (FR-4.7) |
| `/api/cozum/{is_id}/durdur` | POST | yonetici + yonetim | Aramanin sonlandirilmasi (FR-4.9). Arama suruyorsa is karar bekleyen duruma gecer; henuz kuyrukta veya on kontroldeyse dogrudan iptal edilir (SDD 5.4.1). Durdurulamayacak bir durumdaki is icin **409** doner |
| `/api/cozum/{is_id}/karar` | POST | yonetici + yonetim | Durdurulan iste kullanici karari: kullan / at / devam (FR-4.10) |
| `/api/on-kontrol` | POST | yonetici + yonetim | Cozucu calistirmadan on kontrol (FR-5.1) |

## Manuel duzenleme (FR-6.x)

| Uç Nokta | Yöntem | Gereken Rol | İşlev |
| --- | --- | --- | --- |
| `/api/atama` | PUT | yonetici + yonetim | Dogrulanmis manuel degisikligin uygulanmasi (FR-6.1); sapma tablolarini tazeler |
| `/api/atama/dogrula` | POST | yonetici + yonetim | Manuel degisikligin kural dogrulamasi (FR-6.2); ceza dokumu ve uyarilarla |
| `/api/atama/kilit` | POST | yonetici + yonetim | Atamanin kilitlenmesi (FR-6.5) |

## Analiz (FR-8.x)

| Uç Nokta | Yöntem | Gereken Rol | İşlev |
| --- | --- | --- | --- |
| `/api/analiz/{surum_id}` | GET | yonetici + yonetim | Analiz metrikleri (FR-8.1 - FR-8.6); fazla kadro dahil |

## Calisan paneli (FR-9.x)

| Uç Nokta | Yöntem | Gereken Rol | İşlev |
| --- | --- | --- | --- |
| `/api/calisan/tercih` | GET | calisan | Calisanin tercihleri ve karsilanma durumu (FR-9.6, TD-12) |
| `/api/calisan/tercih` | POST | calisan | Calisanin tercih bildirimi (FR-3.1, FR-9.6) |
| `/api/calisan/vardiyalarim` | GET | calisan | Calisanin yayinlanmis cizelgedeki atamalari (FR-9.1 - FR-9.4) |

## Servis izleme

| Uç Nokta | Yöntem | Gereken Rol | İşlev |
| --- | --- | --- | --- |
| `/health` | GET | **yok** (acik) | Servis izleme; veri tasimaz |

## Özet

| Kapı | Uç nokta sayısı |
| --- | --- |
| yonetici + yonetim | 57 |
| calisan | 4 |
| yonetim | 4 |
| giris yapmis her rol | 3 |
| **yok** (acik) | 2 |

Kimlik doğrulaması gerektirmeyen iki uç nokta bilinçlidir: `/health`
veri taşımaz, `/api/giris` kapının kendisidir. Bu ayrım
`tests/test_yetkilendirme.py` içinde uygulamanın kendi yönlendirme
tablosundan türetilerek ölçülür; listeye elle eklenmeyen bir uç nokta
sessizce test dışı kalamaz.
