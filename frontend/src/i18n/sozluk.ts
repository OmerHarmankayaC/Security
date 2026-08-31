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
