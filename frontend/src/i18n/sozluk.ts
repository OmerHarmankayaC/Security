// Arayüz metinlerinin TEK kaynağı.
//
// NEDEN `t('giris.baslik')` DEĞİL DE NESNE: anahtar bir dizgi olsaydı eksik
// bir çeviri ancak o ekran o dilde açıldığında, çalışma anında ortaya
// çıkardı — yani büyük ihtimalle kullanıcıda. Burada `en`, `typeof tr`
// olarak tiplenmiştir: Türkçe'ye eklenip İngilizce'ye eklenmeyen her anahtar
// DERLEMEDE hata verir. Eksik çeviri diye bir durum kalmaz.
//
// TÜRKÇE KAYNAK DİLDİR. Ürün Türkçe tasarlandı, cümleler önce Türkçe
// yazılıyor; İngilizce onun karşılığı. Ters kurulsaydı `typeof` zinciri de
// ters dönerdi ve Türkçe metin eksik kalabilirdi.
//
// ARAYA DEĞER GİREN METİNLER FONKSİYONDUR, şablon dizgisi değil. Türkçe'de
// sayıya gelen ek sayının OKUNUŞUNA bağlıdır (`10'u` ama `12'si`) ve
// İngilizce'de böyle bir ek yoktur; iki dilin cümlesi aynı parçalardan
// kurulamaz. Fonksiyon her dile kendi cümlesini kurma hakkı verir.
//
// VERİ ÇEVRİLMEZ. Personel adı, görev noktası adı, izin açıklaması
// kullanıcının girdiği dilde kalır. Burada yalnızca uygulamanın kendi
// yazdığı metinler durur.
//
// UZUN TİRE (—) KULLANILMAZ, iki dilde de. Yerine iki nokta, virgül ya da
// ayrı bir cümle.
import { belirtmeHaliEki } from '@/lib/metin'

/**
 * Sunucunun döndürebileceği hata kodlarının TAMAMI.
 *
 * Açıkça yazılıyor, `typeof` ile türetilmiyor: bu bir API SÖZLEŞMESİ ve
 * `Record<HataKodu, HataMetni>` sayesinde iki dilden birinde eksik kalan
 * kod derlemede hata veriyor. Arka uçtaki listeyle birliği de sınanıyor
 * (`backend/tests/test_hata_kodlari.py`), yani sunucuya eklenip buraya
 * eklenmeyen bir kod takımı düşürüyor.
 */
export type HataKodu =
  | 'belge_cok_buyuk'
  | 'belge_tipi_kabul_edilmedi'
  | 'belge_yetkisi_yok'
  | 'belge_yok'
  | 'bina_yok'
  | 'cakisan_talep_araligi'
  | 'cozum_isi_yok'
  | 'damga_cakismasi'
  | 'donem_ya_da_surum_yok'
  | 'donem_yok'
  | 'durdurulamaz'
  | 'giris_basarisiz'
  | 'hesap_kilitli'
  | 'hesap_pasif'
  | 'hesap_yonetme_yetkisi_yok'
  | 'izin_yok'
  | 'kaldirilmis_ayar'
  | 'karar_uygulanamaz'
  | 'kendi_hesabi'
  | 'kopyalanamaz_surum_durumu'
  | 'kullanici_adi_gecersiz'
  | 'kullanici_adi_kullanimda'
  | 'kullanici_yok'
  | 'kural_parametresi'
  | 'kural_yok'
  | 'musaitlik_yok'
  | 'nokta_yok'
  | 'onceki_surum_yok'
  | 'oturum_gecersiz'
  | 'oturum_yok'
  | 'ozel_gun_yok'
  | 'parola_ayni'
  | 'parola_borcu'
  | 'parola_hatali'
  | 'parola_kurali'
  | 'personel_baglantisi_gerekli'
  | 'personel_baglantisi_yok'
  | 'personel_yok'
  | 'personel_zaten_bagli'
  | 'sicil_kullanimda'
  | 'sistem_yoneticisine_dokunulamaz'
  | 'son_sistem_yoneticisi'
  | 'surum_silinemez'
  | 'surum_taslak_degil'
  | 'surum_ya_da_atama_yok'
  | 'surum_yok'
  | 'surumler_ayni_donemde_degil'
  | 'talep_yok'
  | 'taslak_siniri_asildi'
  | 'tercih_donemi_yok'
  | 'tercih_kararlanmis'
  | 'tercih_var'
  | 'tercih_yok'
  | 'uretim_kilidi'
  | 'yetki_yok'
  | 'yetkinlik_yok'
  | 'zorunlu_ihlal'

/**
 * Bir hata kodunun metnini üretir.
 *
 * `detay` sunucunun kendi cümlesi. Ayrıntı taşıyan alan hataları Türkçe'de
 * onu olduğu gibi döndürüyor; ayrıntı taşımayanlar parametreyi hiç
 * kullanmıyor ve öyle de yazılıyorlar.
 */
export type HataMetni = (detay: string) => string


const TR_HATALAR: Record<HataKodu, HataMetni> = {
    belge_cok_buyuk: () => 'Dosya çok büyük; en fazla 5 MB.',
    belge_tipi_kabul_edilmedi: () => 'Bu dosya tipi kabul edilmiyor. PNG, JPEG ya da PDF yükleyin.',
    belge_yetkisi_yok: () => 'Bu belgeye erişim yetkiniz yok.',
    belge_yok: () => 'Bu izin kaydında belge yok.',
    bina_yok: () => 'Bina bulunamadı.',
    cakisan_talep_araligi: (detay) => detay,
    cozum_isi_yok: () => 'Çözüm işi bulunamadı.',
    damga_cakismasi: () => 'Bu kayıt siz bakarken değişti. Sayfayı yenileyip tekrar deneyin.',
    donem_ya_da_surum_yok: () => 'Dönem ya da önceki sürüm bulunamadı.',
    donem_yok: () => 'Dönem bulunamadı.',
    durdurulamaz: (detay) => detay,
    giris_basarisiz: () => 'Kullanıcı adı veya parola hatalı.',
    hesap_kilitli: (detay) => detay,
    hesap_pasif: () => 'Hesabınız devre dışı bırakılmış.',
    hesap_yonetme_yetkisi_yok: () => 'Hesapları yönetme yetkiniz yok.',
    izin_yok: () => 'İzin kaydı bulunamadı.',
    kaldirilmis_ayar: (detay) => detay,
    karar_uygulanamaz: (detay) => detay,
    kendi_hesabi: () => 'Kendi rolünüzü değiştiremez ve kendi hesabınızı devre dışı bırakamazsınız.',
    kopyalanamaz_surum_durumu: (detay) => detay,
    kullanici_adi_gecersiz: (detay) => detay,
    kullanici_adi_kullanimda: () => 'Bu kullanıcı adı zaten kullanımda.',
    kullanici_yok: () => 'Kullanıcı bulunamadı.',
    kural_parametresi: (detay) => detay,
    kural_yok: () => 'Kural bulunamadı.',
    musaitlik_yok: () => 'Müsaitlik kaydı bulunamadı.',
    nokta_yok: () => 'Görev noktası bulunamadı.',
    onceki_surum_yok: () => 'Önceki sürüm bulunamadı.',
    oturum_gecersiz: () => 'Oturumunuz geçersiz ya da süresi dolmuş. Tekrar giriş yapın.',
    oturum_yok: () => 'Oturumunuz açık değil. Lütfen tekrar giriş yapın.',
    ozel_gun_yok: () => 'Özel gün bulunamadı.',
    parola_ayni: () => 'Yeni parola mevcut parolayla aynı olamaz.',
    parola_borcu: () => 'Devam etmeden önce parolanızı değiştirmeniz gerekiyor.',
    parola_hatali: () => 'Mevcut parola hatalı.',
    parola_kurali: (detay) => detay,
    personel_baglantisi_gerekli: () => 'Bu rol bir personel kaydına bağlanmalı.',
    personel_baglantisi_yok: () => 'Hesabınız bir personel kaydına bağlı değil.',
    personel_yok: () => 'Personel bulunamadı.',
    personel_zaten_bagli: () => 'Bu personel zaten başka bir hesaba bağlı.',
    sicil_kullanimda: (detay) => detay,
    sistem_yoneticisine_dokunulamaz: () => 'Sistem yöneticisi hesabına dokunulamaz.',
    son_sistem_yoneticisi: () => 'Son sistem yöneticisi devre dışı bırakılamaz.',
    surum_silinemez: (detay) => detay,
    surum_taslak_degil: () => 'Bu sürüm taslak değil; üzerinde değişiklik yapılamaz.',
    surum_ya_da_atama_yok: () => 'Çizelge sürümü ya da atama bulunamadı.',
    surum_yok: () => 'Çizelge sürümü bulunamadı.',
    surumler_ayni_donemde_degil: () => 'Karşılaştırılan sürümler aynı döneme ait değil.',
    talep_yok: () => 'Talep kaydı bulunamadı.',
    taslak_siniri_asildi: (detay) => detay,
    tercih_donemi_yok: () => 'Bu tarih için tercih dönemi bulunamadı.',
    tercih_kararlanmis: () => 'Bu tercih karara bağlanmış; değiştirilemez.',
    tercih_var: () => 'Bu personelin bu tarih için zaten bir tercihi var.',
    tercih_yok: () => 'Tercih bulunamadı.',
    uretim_kilidi: (detay) => detay,
    yetki_yok: () => 'Bu işlem için yetkiniz yok.',
    yetkinlik_yok: () => 'Yetkinlik bulunamadı.',
    zorunlu_ihlal: () => 'Bu değişiklik zorunlu bir kuralı ihlal ediyor.',
  }

const tr = {
  marka: {
    altBaslik: 'vardiya çizelgeleme karar destek aracı',
    altBaslikKisa: 'karar destek aracı',
  },

  giris: {
    baslik: 'Giriş',
    kullaniciAdi: 'Kullanıcı adı',
    parola: 'Parola',
    gonder: 'Giriş Yap',
    gonderiliyor: 'Giriş yapılıyor…',
    baglantiHatasi: 'Giriş yapılamadı. Bağlantınızı kontrol edin.',
    yardim: 'Hesabınız yoksa veya parolanızı unuttuysanız yönetime başvurun.',
  },

  roller: {
    sistem_yoneticisi: 'Sistem yöneticisi',
    hesap_yoneticisi: 'Hesap yöneticisi',
    idare: 'İdare',
    calisan: 'Çalışan',
  },

  demo: {
    seritBasligi: 'Gösterim ortamı.',
    seritGovdesi:
      'Buradaki personel, izin ve çizelge kayıtlarının tamamı gösterim amacıyla ' +
      'üretilmiştir; gerçek bir kurumu ya da kişiyi göstermez. Veri her gece ' +
      'sıfırlanır, yaptığınız değişiklikler kaybolur. Sistem herhangi bir kurumda ' +
      'kullanımda değildir.',
    hesaplarBasligi: 'Gösterim hesapları',
    hesaplarYardimi: 'bir satıra tıklayın, form dolsun.',
    saltOkunur:
      'Gösterim ortamı: değişiklikler kaydedilmez. Düzenleme araçlarını ' +
      'serbestçe deneyebilirsiniz.',
    uyariyiKapat: 'Uyarıyı kapat',
  },

  dil: {
    secici: 'Arayüz dili',
  },

  bilinmeyenHata: 'Beklenmeyen bir hata oluştu.',

  /**
   * MENÜ ETİKETLERİ, kimlikleri DEĞİL.
   *
   * `NavOgesi` ('Özet', 'Tanımlar'…) uygulamanın iç kimliği: hangi ekranın
   * açık olduğu, `App.tsx`teki `switch`, seçili öğe hep bu değerlerle
   * konuşuyor. Türkçe sözcükler olmaları tarihsel bir tesadüf; çevrilirlerse
   * kimlik kırılır. Bu yüzden kimlikler yerinde duruyor ve GÖRÜNEN ad
   * buradan geliyor.
   */
  menu: {
    'Özet': 'Özet',
    'Tanımlar': 'Tanımlar',
    'Müsaitlik': 'Müsaitlik',
    'Tercihler': 'Tercihler',
    'Çizelge': 'Çizelge',
    'Çözüm': 'Çözüm',
    'Analiz': 'Analiz',
    'Sürümler': 'Sürümler',
    'Kullanıcılar': 'Kullanıcılar',
    'Künye': 'Künye',
  },

  menuGruplari: {
    veri: 'VERİ',
    uretim: 'ÜRETİM',
    degerlendirme: 'DEĞERLENDİRME',
    yonetim: 'YÖNETİM',
  },

  /** Sekme başlığı. Ürün adı çevrilmez, yüzeyin adı çevrilir. */
  sekmeBasligi: {
    giris: 'VARDİS: Giriş',
    parola: 'VARDİS: Parola',
    calisan: 'VARDİS: Çalışan',
    idare: 'VARDİS: Yönetim',
  },

  /** Çözüm işinin durumu (üst çubuktaki iş kartı). */
  isDurumu: {
    kuyrukta: 'Kuyrukta',
    on_kontrol: 'Ön kontrol',
    cozuluyor: 'Çözülüyor',
    durduruldu: 'Karar bekliyor',
    tamamlandi: 'Tamamlandı',
    uyarili: 'Uyarılı tamamlandı',
    basarisiz: 'Başarısız',
    iptal: 'İptal edildi',
  },

  kabuk: {
    oturum: 'Oturum',
    parolaDegistir: 'Parola değiştir',
    cikis: 'Çıkış',
    cozumEkraniniAc: 'Çözüm ekranını aç',
    paneleDon: 'Panele dön',
    donem: 'Dönem',
    yapimAsamasinda: 'Bu ekran henüz uygulanmadı.',
    yakinda: 'yakında',
    verilerYuklenemedi: 'Veriler yüklenemedi.',
  },


  calisan: {
    donemYok: 'Aktif bir planlama dönemi yok.',
    cizelgeYok: 'Bu dönem için henüz yayınlanmış bir çizelge yok.',
    ozetYok: 'Bu dönem için henüz yayınlanmış bir çizelge yok, özet hesaplanamıyor.',
    siradakiVardiyan: 'Sıradaki Vardiyan',
    donemGorunumu: (gun: number) => `Dönem Görünümü · ${gun} Gün`,
    haftaGunleri: ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz'],
    vardiyanYok: 'Bu dönemde vardiyan yok.',
    saatBandi: 'saat bandı',
    degisenGun: 'Değişen gün',
    degisti: 'Değişti',
    kaldirildi: 'Kaldırıldı',
    gunKaldirildi: 'Bu günkü vardiyan kaldırıldı',
    gunEklendi: 'Bu güne yeni vardiya eklendi',
    gunDegisti: 'Bu günkü vardiyan değişti',
    yayinBilgisi: (zaman: string) => `Bu çizelge ${zaman} tarihinde yayınlandı.`,
    degisenGunSayisi: (sayi: number) => ` ${sayi} günün bir önceki sürüme göre değişti.`,
    ozetAlinamadi: 'Özet alınamadı.',
    olcumUfku: 'Ölçüm ufku',
    buDonem: 'Bu Dönem',
    son90Gun: 'Son 90 Gün',
    son90GunBaslik: 'SON 90 GÜN',
    donemBaslik: (aralik: string) => `${aralik} DÖNEMİ`,
    kapsamDonem: 'Sayılar yalnızca bu dönemi kapsar.',
    kapsamAdalet: 'Sayılar son doksan günü kapsar; geçmiş yayınlanmış çizelgeler dahil.',
    cumleBasiAdalet: 'Son 90 günde',
    cumleBasiDonem: 'Bu dönemde',
    adilPay: 'ADİL PAY',
    adilPayinUstunde: 'Adil Payın Üstünde',
    adilPayinAltinda: 'Adil Payın Altında',
    ekipOrtalamasi: (deger: string) => `ekip ortalaması ${deger} sa`,
    payinaYakinsin: 'adil payına yakınsın',
    payinUstundesin: (fark: string, birim: string) => `adil payının ${fark} ${birim} üzerindesin`,
    payinAltindasin: (fark: string, birim: string) => `adil payının ${fark} ${birim} altındasın`,
    haftaSonlarinda: (karsilastirma: string) => `hafta sonlarında ${karsilastirma}`,
    ikisiDeYok:
      'Görev noktanda gece ve hafta sonu vardiyası bulunmadığı için bu iki karşılaştırma gösterilmiyor.',
    geceYok: 'Görev noktanda gece vardiyası bulunmadığı için gece karşılaştırması gösterilmiyor.',
    haftaSonuYok:
      'Görev noktanda hafta sonu vardiyası bulunmadığı için hafta sonu karşılaştırması gösterilmiyor.',
    yayindanHesaplanir:
      'Sayılar yalnızca yayınlanmış çizelgeden hesaplanır. Yönetici üzerinde çalıştığı taslak buraya yansımaz.',
    sen: 'SEN',
    saat: 'saat',
    saatKisa: 'sa',
    geceSaatinde: (k: string) => `gece saatinde ${k}`,
    toplamSaatte: (k: string) => `toplam saatte ${k}`,
    geceSaati: 'Gece Saati',
    haftaSonu: 'Hafta Sonu',
    toplamSaat: 'Toplam Saat',
    tercihlerYuklenemedi: 'Tercihler yüklenemedi.',
    tercihAlindi: 'Tercihin alındı.',
    tercihKararlanmis: 'Bu gün için kararlanmış bir tercihin var; değiştirmek için yöneticine başvur.',
    tercihGonderilemedi: 'Tercih gönderilemedi.',
    bildirdigimTercihler: (sayi: number) => `Bildirdiğim Tercihler · ${sayi}`,
    tercihYok: 'Henüz tercih bildirmedin.',
    cizelgeYayinlanmadi: '· çizelge henüz yayınlanmadı',
    gerekce: (metin: string) => `Gerekçe: ${metin}`,
    acikDonemYok: 'Şu anda tercihe açık bir dönem yok. Yeni dönem açıldığında buradan bildirebilirsin.',
    kapaniyor: 'kapanıyor',
    kalanGun: (aralik: string, gun: number) => `${aralik} dönemi için ${gun} günün var.`,
    calismakIstemiyorum: 'Çalışmak istemiyorum',
    suSaatlerdeCalismak: 'Şu saatlerde çalışmak istiyorum',
    belirliSaatlerde: 'Belirli saatlerde çalışmak istiyorum',
    araliktaCalismak: (aralik: string) => `${aralik} arası çalışmak istiyorum`,
    baslangic: 'Başlangıç',
    bitis: 'Bitiş',
    gun: 'Gün',
    gerekceIsteğeBagli: 'Gerekçe (isteğe bağlı)',
    tercihiGonder: 'Tercihi Gönder',
    tumGun: 'tüm gün (24 saat)',
    saatSuresi: (saat: number) => `${saat} saat`,
    yeniTercihBildir: 'Yeni Tercih Bildir',
    tercihTipi: 'Tercih Tipi',
    vardiyaListesi: (sayi: number) => `Vardiya Listesi · ${sayi} Vardiya`,
    geceSaati2: (saat: string) => `${saat} sa gece`,
    tercihKapaniyor: (tarih: string) => `Tercih bildirimi ${tarih} tarihinde kapanıyor`,
    tercihDurumu: {
      beklemede: 'Beklemede',
      reddedildi: 'Reddedildi',
      onaylandi: 'Onaylandı',
      karsilandi: 'Karşılandı',
      karsilanmadi: 'Karşılanmadı',
      henuz_belirsiz: 'Henüz Belirsiz',
    },
  },

  calisanSekmeleri: {
    'Vardiyalarım': 'Vardiyalarım',
    'Dönem Özetim': 'Dönem Özetim',
    'Tercihlerim': 'Tercihlerim',
  },



  /**
   * SUNUCU HATALARININ METNİ, koda göre.
   *
   * Her girdi bir FONKSİYON ve sunucunun kendi metnini (`detay`) alıyor.
   * Sebebi: alan hatalarının bir kısmı ayrıntı taşıyor
   * (`"S3 kural kataloğunda tanımlı değil."`) ve sabit bir cümle o ayrıntıyı
   * atardı. Türkçe tarafta böyle girdiler `detay`ı olduğu gibi döndürüyor,
   * yani bugünkü davranış birebir korunuyor; İngilizce tarafta ayrıntı
   * çevrilemediği için genel cümle yazılıyor. Bu bilinçli ve sınırlı bir
   * kayıp: alternatifi, sunucudan yapılandırılmış parametre taşımaktı ve
   * bu tur onu kapsamıyor.
   */
  hatalar: TR_HATALAR,

  /**
   * "36 personelin 10'u gösteriliyor".
   *
   * Türkçe'de ek okunuşa bağlı (`belirtmeHaliEki`), İngilizce'de ek yok ama
   * cümlenin sırası da farklı. İki dilin ortak bir şablonu olamaz.
   */
  sayim: {
    gosteriliyor: (gosterilen: number, toplam: number) =>
      `${toplam} kaydın ${gosterilen}${belirtmeHaliEki(gosterilen)} gösteriliyor`,
  },
}

/**
 * Türkçe sözlüğün şekli. `en` bunu birebir karşılamak ZORUNDA: eksik anahtar
 * da fazla anahtar da derlemede hata verir.
 */
export type Metinler = typeof tr

const EN_HATALAR: Record<HataKodu, HataMetni> = {
    belge_cok_buyuk: () => 'The file is too large; 5 MB at most.',
    belge_tipi_kabul_edilmedi: () => 'This file type is not accepted. Upload a PNG, JPEG or PDF.',
    belge_yetkisi_yok: () => 'You do not have permission to access this document.',
    belge_yok: () => 'This leave record has no document.',
    bina_yok: () => 'Building not found.',
    cakisan_talep_araligi: () => 'This demand overlaps an existing record for the same duty point.',
    cozum_isi_yok: () => 'Solve job not found.',
    damga_cakismasi: () => 'This record changed while you were looking at it. Reload and try again.',
    donem_ya_da_surum_yok: () => 'Period or previous version not found.',
    donem_yok: () => 'Period not found.',
    durdurulamaz: () => 'This solve job cannot be stopped in its current state.',
    giris_basarisiz: () => 'Incorrect username or password.',
    hesap_kilitli: () => 'Your account is locked after too many failed attempts. Try again later.',
    hesap_pasif: () => 'Your account has been deactivated.',
    hesap_yonetme_yetkisi_yok: () => 'You do not have permission to manage accounts.',
    izin_yok: () => 'Leave record not found.',
    kaldirilmis_ayar: () => 'A setting this installation no longer supports is still configured.',
    karar_uygulanamaz: () => 'The solver decision cannot be applied in the current state.',
    kendi_hesabi: () => 'You cannot change your own role or deactivate your own account.',
    kopyalanamaz_surum_durumu: () => 'Only a published or archived version can be copied.',
    kullanici_adi_gecersiz: () => 'The username does not meet the required format.',
    kullanici_adi_kullanimda: () => 'That username is already taken.',
    kullanici_yok: () => 'User not found.',
    kural_parametresi: () => 'A rule parameter is invalid.',
    kural_yok: () => 'Rule not found.',
    musaitlik_yok: () => 'Availability record not found.',
    nokta_yok: () => 'Duty point not found.',
    onceki_surum_yok: () => 'Previous version not found.',
    oturum_gecersiz: () => 'Your session is invalid or has expired. Please sign in again.',
    oturum_yok: () => 'You are not signed in. Please sign in again.',
    ozel_gun_yok: () => 'Special day not found.',
    parola_ayni: () => 'The new password cannot be the same as the current one.',
    parola_borcu: () => 'You must change your password before continuing.',
    parola_hatali: () => 'Current password is incorrect.',
    parola_kurali: () => 'The password does not meet the required rules.',
    personel_baglantisi_gerekli: () => 'This role must be linked to a staff record.',
    personel_baglantisi_yok: () => 'Your account is not linked to a staff record.',
    personel_yok: () => 'Staff record not found.',
    personel_zaten_bagli: () => 'That staff record is already linked to another account.',
    sicil_kullanimda: () => 'That staff number is already in use.',
    sistem_yoneticisine_dokunulamaz: () => 'The system administrator account cannot be modified.',
    son_sistem_yoneticisi: () => 'The last system administrator cannot be deactivated.',
    surum_silinemez: () => 'This version cannot be deleted.',
    surum_taslak_degil: () => 'This version is not a draft and cannot be edited.',
    surum_ya_da_atama_yok: () => 'Schedule version or assignment not found.',
    surum_yok: () => 'Schedule version not found.',
    surumler_ayni_donemde_degil: () => 'The versions being compared belong to different periods.',
    talep_yok: () => 'Demand record not found.',
    taslak_siniri_asildi: () => 'This period has reached its limit of open versions. Delete one to make room.',
    tercih_donemi_yok: () => 'No preference period was found for this date.',
    tercih_kararlanmis: () => 'This preference has been decided and can no longer be changed.',
    tercih_var: () => 'This person already has a preference for this date.',
    tercih_yok: () => 'Preference not found.',
    uretim_kilidi: () => 'This operation is locked in a production installation.',
    yetki_yok: () => 'You do not have permission for this action.',
    yetkinlik_yok: () => 'Competency not found.',
    zorunlu_ihlal: () => 'This change violates a hard rule.',
  }

const en: Metinler = {
  marka: {
    altBaslik: 'shift scheduling decision support tool',
    altBaslikKisa: 'decision support tool',
  },

  giris: {
    baslik: 'Sign in',
    kullaniciAdi: 'Username',
    parola: 'Password',
    gonder: 'Sign In',
    gonderiliyor: 'Signing in…',
    baglantiHatasi: 'Could not sign in. Check your connection.',
    yardim: 'If you have no account or forgot your password, contact an administrator.',
  },

  roller: {
    sistem_yoneticisi: 'System administrator',
    hesap_yoneticisi: 'Account manager',
    idare: 'Administration',
    calisan: 'Employee',
  },

  demo: {
    seritBasligi: 'Demonstration environment.',
    seritGovdesi:
      'Every staff, leave and schedule record here was generated for demonstration; ' +
      'none of it represents a real organisation or person. The data is rebuilt every ' +
      'night and any change you make is lost. The system is not in use at any ' +
      'organisation.',
    hesaplarBasligi: 'Demo accounts',
    hesaplarYardimi: 'click a row to fill the form.',
    saltOkunur:
      'Demonstration environment: changes are not saved. Feel free to try the ' +
      'editing tools.',
    uyariyiKapat: 'Dismiss notice',
  },

  dil: {
    secici: 'Interface language',
  },

  bilinmeyenHata: 'Something went wrong.',

  menu: {
    'Özet': 'Overview',
    'Tanımlar': 'Definitions',
    'Müsaitlik': 'Availability',
    'Tercihler': 'Preferences',
    'Çizelge': 'Schedule',
    'Çözüm': 'Solve',
    'Analiz': 'Analysis',
    'Sürümler': 'Versions',
    'Kullanıcılar': 'Users',
    'Künye': 'About',
  },

  menuGruplari: {
    veri: 'DATA',
    uretim: 'PRODUCTION',
    degerlendirme: 'EVALUATION',
    yonetim: 'ADMINISTRATION',
  },

  sekmeBasligi: {
    giris: 'VARDİS: Sign in',
    parola: 'VARDİS: Password',
    calisan: 'VARDİS: Employee',
    idare: 'VARDİS: Administration',
  },

  isDurumu: {
    kuyrukta: 'Queued',
    on_kontrol: 'Pre-check',
    cozuluyor: 'Solving',
    durduruldu: 'Awaiting decision',
    tamamlandi: 'Completed',
    uyarili: 'Completed with warnings',
    basarisiz: 'Failed',
    iptal: 'Cancelled',
  },

  kabuk: {
    oturum: 'Session',
    parolaDegistir: 'Change password',
    cikis: 'Sign out',
    cozumEkraniniAc: 'Open the solve screen',
    paneleDon: 'Back to the panel',
    donem: 'Period',
    yapimAsamasinda: 'This screen has not been built yet.',
    yakinda: 'coming soon',
    verilerYuklenemedi: 'Could not load the data.',
  },


  calisan: {
    donemYok: 'There is no active planning period.',
    cizelgeYok: 'No schedule has been published for this period yet.',
    ozetYok: 'No schedule has been published for this period yet, so no summary can be computed.',
    siradakiVardiyan: 'Your next shift',
    donemGorunumu: (gun: number) => `Period view · ${gun} days`,
    haftaGunleri: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    vardiyanYok: 'You have no shifts in this period.',
    saatBandi: 'hours worked',
    degisenGun: 'Changed day',
    degisti: 'Changed',
    kaldirildi: 'Removed',
    gunKaldirildi: 'Your shift on this day was removed',
    gunEklendi: 'A new shift was added on this day',
    gunDegisti: 'Your shift on this day changed',
    yayinBilgisi: (zaman: string) => `This schedule was published on ${zaman}.`,
    degisenGunSayisi: (sayi: number) =>
      sayi === 1 ? ' 1 day changed from the previous version.' : ` ${sayi} days changed from the previous version.`,
    ozetAlinamadi: 'Could not load the summary.',
    olcumUfku: 'Measurement horizon',
    buDonem: 'This period',
    son90Gun: 'Last 90 days',
    son90GunBaslik: 'LAST 90 DAYS',
    donemBaslik: (aralik: string) => `${aralik} PERIOD`,
    kapsamDonem: 'The figures cover this period only.',
    kapsamAdalet:
      'The figures cover the last ninety days, including previously published schedules.',
    cumleBasiAdalet: 'Over the last 90 days',
    cumleBasiDonem: 'In this period',
    adilPay: 'FAIR SHARE',
    adilPayinUstunde: 'Above your fair share',
    adilPayinAltinda: 'Below your fair share',
    ekipOrtalamasi: (deger: string) => `team average ${deger} h`,
    payinaYakinsin: 'you are close to your fair share',
    payinUstundesin: (fark: string, birim: string) => `you are ${fark} ${birim} above your fair share`,
    payinAltindasin: (fark: string, birim: string) => `you are ${fark} ${birim} below your fair share`,
    haftaSonlarinda: (karsilastirma: string) => `on weekends ${karsilastirma}`,
    ikisiDeYok:
      'Your duty point has no night or weekend shifts, so these two comparisons are not shown.',
    geceYok: 'Your duty point has no night shifts, so the night comparison is not shown.',
    haftaSonuYok:
      'Your duty point has no weekend shifts, so the weekend comparison is not shown.',
    yayindanHesaplanir:
      'The figures are computed from the published schedule only. A draft the administrator is working on does not appear here.',
    sen: 'YOU',
    saat: 'hours',
    saatKisa: 'h',
    geceSaatinde: (k: string) => `on night hours ${k}`,
    toplamSaatte: (k: string) => `on total hours ${k}`,
    geceSaati: 'Night hours',
    haftaSonu: 'Weekend',
    toplamSaat: 'Total hours',
    tercihlerYuklenemedi: 'Could not load your preferences.',
    tercihAlindi: 'Your preference was recorded.',
    tercihKararlanmis:
      'Your preference for this day has already been decided; contact your administrator to change it.',
    tercihGonderilemedi: 'Could not submit the preference.',
    bildirdigimTercihler: (sayi: number) => `My preferences · ${sayi}`,
    tercihYok: 'You have not submitted any preferences yet.',
    cizelgeYayinlanmadi: '· the schedule has not been published yet',
    gerekce: (metin: string) => `Reason: ${metin}`,
    acikDonemYok:
      'No period is open for preferences right now. You can submit here when a new period opens.',
    kapaniyor: 'closes',
    kalanGun: (aralik: string, gun: number) =>
      gun === 1 ? `You have 1 day left for the ${aralik} period.` : `You have ${gun} days left for the ${aralik} period.`,
    calismakIstemiyorum: 'I would rather not work',
    suSaatlerdeCalismak: 'I would like to work these hours',
    belirliSaatlerde: 'I would like to work particular hours',
    araliktaCalismak: (aralik: string) => `I would like to work ${aralik}`,
    baslangic: 'Start',
    bitis: 'End',
    gun: 'Day',
    gerekceIsteğeBagli: 'Reason (optional)',
    tercihiGonder: 'Submit preference',
    tumGun: 'all day (24 hours)',
    saatSuresi: (saat: number) => (saat === 1 ? '1 hour' : `${saat} hours`),
    yeniTercihBildir: 'New preference',
    tercihTipi: 'Preference type',
    vardiyaListesi: (sayi: number) =>
      sayi === 1 ? 'Shift list · 1 shift' : `Shift list · ${sayi} shifts`,
    geceSaati2: (saat: string) => `${saat} h night`,
    tercihKapaniyor: (tarih: string) => `Preferences close on ${tarih}`,
    tercihDurumu: {
      beklemede: 'Pending',
      reddedildi: 'Rejected',
      onaylandi: 'Approved',
      karsilandi: 'Met',
      karsilanmadi: 'Not met',
      henuz_belirsiz: 'Not yet known',
    },
  },

  calisanSekmeleri: {
    'Vardiyalarım': 'My shifts',
    'Dönem Özetim': 'My period summary',
    'Tercihlerim': 'My preferences',
  },



  hatalar: EN_HATALAR,

  sayim: {
    gosteriliyor: (gosterilen: number, toplam: number) =>
      `Showing ${gosterilen} of ${toplam} records`,
  },
}

export const SOZLUK = { tr, en } as const
