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
  istekBasarisiz: (durum: number) => `İstek başarısız (HTTP ${durum}).`,

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


  /** Yüzde işareti Türkçe'de sayının ÖNÜNDE, İngilizce'de arkasındadır. */
  yuzde: (deger: number | string) => `%${deger}`,

  surumDurumu: {
    taslak: 'Taslak',
    cozuldu: 'Çözüldü',
    yayinlandi: 'Yayınlandı',
    arsiv: 'Arşiv',
  },

  /**
   * ÇÖZÜM SONUCUNUN GÜNDELİK DİLİ (SRS FR-6.4).
   *
   * Cümleler PARÇA BİRLEŞTİRMEYLE kurulmuyor, her dil kendi tam cümlesini
   * yazıyor. Türkçe'de ölçü adı özne olup yükleme bağlanıyor ("gece adaleti
   * 2 saat bozuldu"); İngilizce'de yüklem öne geçip miktar edatla geliyor
   * ("night fairness worsened by 2 hours"). Ortak bir şablon ikisinden
   * birini bozardı.
   */
  izgara: {
    blokIslemleri: 'Blok işlemleri',
    gorevNoktasi: 'Görev Noktası',
    kilidiAc: 'Kilidi aç',
    kilitle: 'Kilitle',
    blogunuSil: 'Bloğu sil',
    basamakSirasi: (noktalar: string) => `Basamak sırası: ${noktalar}`,
    gunIzgarasinaGec: (tarih: string) => `${tarih} · gün ızgarasına geç`,
    oncekiGunden: ' (önceki günden)',
    oncekiGundenDevam: 'önceki günden devam ediyor',
    ertesiGuneTasiyor: 'ertesi güne taşıyor',
    ertesiGune: ' (ertesi güne)',
    gunlukKapsamaAcigi: 'Günlük kapsama açığı',
    gunEksik: (tarih: string, saat: number) => `${tarih} · ${saat} kişi-saat eksik`,
  },

  yazdirma: {
    baslik: 'Vardiya Çizelgesi',
    gun: 'gün',
    uretildi: (tarih: string) => `${tarih} tarihinde üretildi`,
    kapsamaAciklari: 'Kapsama Açıkları',
    acikYok: 'Bu sürümde kapsama açığı yok.',
    acikOzeti: (aralik: number, kisi: number) => `${aralik} aralıkta toplam ${kisi} kişi eksik.`,
    acikSutunlari: ['Tarih', 'Saat Aralığı', 'Görev Noktası', 'Eksik'],
    fazlaOzeti: (aralik: number, kisi: number) =>
      `${aralik} aralıkta toplam ${kisi} kişi fazla. SRS 4.3 S1 bu sınırı esnek tanımlar; aşılması elle yapılmış bir düzenlemeden gelir.`,
    fazlaSutunlari: ['Tarih', 'Saat Aralığı', 'Görev Noktası', 'Fazla'],
    yazdir: 'Yazdır',
    sayfaNotu: 'Yatay A4 · her gün kendi sayfasında, saat başlığı her sayfada tekrarlanır.',
  },

  tanimYonetimi: {
    gizliPasif: (sayi: number) => `${sayi} pasif kayıt gizli.`,
    kullanimAlinamadi: 'Kullanım bilgisi alınamadı.',
    pasiflestirmeOnayi: 'pasifleştirme onayı',
    silmeOnayi: 'silme onayı',
    kontrolEdiliyor: 'Kullanım kontrol ediliyor…',
    kullaniliyorNotu:
      'kullanılıyor. Kayıt silinmeyecek, pasifleştirilecek: yeni çözümlerde kullanılmaz, mevcut çizelgelerde görünmeye devam eder.',
    kullanilmiyorNotu: ' hiçbir kayıtta kullanılmıyor. Kayıt kalıcı olarak silinecek.',
    pasiflestir: 'Pasifleştir',
    kaliciSil: 'Kalıcı Olarak Sil',
    vazgec: 'Vazgeç',
  },

  kuralUyarilari: {
    yetkinlikCakismasi: (a: string, b: string) =>
      `${a} ile ${b} birlikte seçildi. SRS 3.3.2 bu ikisini karşılıklı dışlayıcı tanımlar: müracaat görevlisi başka bir noktada, güvenlik görevlisi de müracaat noktasında çalışamaz. Kayıt engellenmiyor; bilerek yapıyorsanız devam edin.`,
    s1Pasif:
      'S1 pasif: talep kısıtı modele eklenmiyor. Hiçbir vardiyanın doldurulması zorunlu değil (sonuç boş bir çizelge olabilir), bir noktaya talebin üzerinde personel atanabilir ve kapsama açığı hiç hesaplanmadığı için Analiz ile Çizelge ekranları karşılanmamış talebi "0 açık" gösterir.',
    aktiflik: 'Aktiflik',
    aktif: 'Aktif',
    pasif: 'Pasif',
    agirlik: 'Ağırlık',
    asgariBlok: (saat: number) => `Asgari blok ${saat} saat (H1)`,
    gunlukAzami: (saat: number) => `Günlük azami ${saat} saat (H9)`,
    tarihSecin: 'Başlangıç ve bitiş tarihini seçin.',
    bitisOnce: 'Bitiş tarihi başlangıç tarihinden önce olamaz.',
    donemUzun: (azami: number, secilen: number) =>
      `Planlama dönemi en fazla ${azami} gün olabilir; seçilen aralık ${secilen} gün. Daha kısa bir bitiş tarihi seçin.`,
  },

  tanimlar: {
    sekmeler: {
      'Talep': 'Talep',
      'Personel': 'Personel',
      'Yetkinlik': 'Yetkinlik',
      'Bina': 'Bina',
      'Görev Noktası': 'Görev Noktası',
      'Özel Gün': 'Özel Gün',
      'Kural': 'Kural',
    },
    gunTipi: { hafta_ici: 'Hafta içi', hafta_sonu: 'Hafta sonu', resmi_tatil: 'Resmî tatil' },
    yuklenemedi: 'Tanımlar yüklenemedi.',
    ozelGunSilinemedi: 'Özel gün silinemedi.',
    talepSilinemedi: 'Talep aralığı silinemedi.',
    kuralGuncellenemedi: 'Kural güncellenemedi.',
    kayitKaydedilemedi: 'Kayıt kaydedilemedi.',
    talepKaydedilemedi: 'Talep aralığı kaydedilemedi.',
    ozelGunKaydedilemedi: 'Özel gün kaydedilemedi.',
    araligiCakisiyor: (mesaj: string) =>
      `Aralık çakışıyor: ${mesaj}. Aynı nokta ve gün tipi için saatler örtüşemez.`,
    noktaSayisi: (sayi: number) => `${sayi} görev noktası`,
    binaTanimliDegil:
      'Bina tanımlı değil; mevcut uygulama alanında bütün noktalar tesis geneli (SRS 3.3.3).',
    onkosulVar: 'Ön koşul var',
    onkosulYok: 'Ön koşul yok',
    degistir: 'Değiştir',
    degisiklikYok: 'Değişiklik yok',
    vazgec: 'Vazgeç',
    iptal: 'İptal',
    sil: 'Sil',
    onceNoktaTanimla: 'Önce bir görev noktası tanımlayın',
    onceAralikSec: 'Önce listeden bir aralık seçin',
    onceGunSec: 'Önce listeden bir gün seçin',
    onceKayitSec: 'Önce listeden bir kayıt seçin',
    pasifleriGoster: 'Pasifleri göster',
    talepBasligi: (sayi: number) => `talep aralıkları · ${sayi} kayıt`,
    talepYok:
      'Talep aralığı tanımlı değil. Aralık girilmeden çözüm hiç kimseyi istemez: kapsama kısıtı (SRS 4.3 S1) talep saatleri üzerinden yazılır ve boş talepte hiçbir açık doğmaz.',
    talepSutunlari: ['GÖREV NOKTASI', 'GÜN TİPİ', 'TARİH', 'ARALIK', 'SÜRE', 'GEREKEN'],
    talepNotu:
      "Aralıklar saat başında başlar ve biter; gün sonu 24.00'tır. Aynı nokta ve gün tipi için çakışan iki aralık kabul edilmez: çakışan kayıtlar aynı saat için iki farklı gereken sayı üretirdi. Tarih dolu bir satır yalnız o güne aittir ve o gün genel satırların yerine geçer.",
    haftalikYuk: 'HAFTALIK KİŞİ-SAAT YÜKÜ',
    asgariKadro: 'ASGARİ KADRO (FAZLA ÇALIŞMA EŞİĞİNE GÖRE)',
    tatilYok:
      'Resmî tatil işaretlenmemiş. İşaretlenen günler talep matrisinin resmî tatil sütunundan beslenir ve adalet hesaplarında hafta sonuyla aynı sayaca eklenir (SRS TD-3).',
    tatilTakvimi: (sayi: number) => `resmî tatil takvimi · ${sayi} gün`,
    degisiklikleriKaydet: 'değişiklikleri kaydet',
    kaydedilecek: (sayi: number) => `${sayi} değişiklik kaydedilecek`,
    ardindanSekme: (sekme: string) => `, ardından ${sekme} sekmesine geçilecek.`,
    s1Uyarisi: (s1: string, toplam: string) =>
      `S1 ağırlığı (${s1}) diğer aktif esnek hedeflerin toplamının (${toplam}) üzerinde değil; talep karşılama baskınlığını kaybeder.`,
    s1UyarisiUzun: (s1: string, toplam: string) =>
      `S1 ağırlığı (${s1}) diğer aktif esnek hedeflerin toplamının (${toplam}) üzerinde değil. Talep karşılama baskınlığını kaybeder: çözücü, adalet veya tercih gibi bir hedefi iyileştirmek için kapsama açığı bırakmayı tercih edebilir.`,
    duzenlemeyeDon: 'Düzenlemeye dön',
    zorunluKisitlar: 'H1–H8 · zorunlu kısıtlar',
    katalogNotu:
      'Katalog kuralları modelin yapısını oluşturur; silinemez, yalnızca devre dışı bırakılır ve parametreleri değiştirilir.',
    agirlik: 'Ağırlık',
    formBasligi: (sekme: string, yeni: boolean) => `${sekme} ${yeni ? 'ekle' : 'değiştir'}`,
    aktiflikBaslangic: 'Aktiflik Başlangıç',
    aktiflikBitis: 'Aktiflik Bitiş',
    devirFazlaCalisma: 'Devir Fazla Çalışma (saat)',
    kotaYili: 'Kota Yılı',
    aciklama: 'Açıklama',
    onkosulYetkinlik: 'Ön Koşul Yetkinlik',
    yetkinlikYok: 'Tanımlı yetkinlik yok; önce Yetkinlik sekmesinden ekleyin.',
    pasifNotu: 'Pasif kayıt yeni çözümlerde kullanılmaz; mevcut çizelgelerde görünmeye devam eder.',
    aktiflikNotu:
      'Aktiflik penceresi dışındaki günlerde personel müsait sayılmaz (H7). Bitiş boş bırakılırsa pencere süresizdir; bugüne kadar çalıştırmak için Sil eylemini kullanın, pencereyi bir önceki güne kapatır.',
    talepEkle: 'talep aralığı ekle',
    talepDegistir: 'talep aralığı değiştir',
    gorevNoktasi: 'Görev Noktası',
    gunTipiEtiketi: 'Gün Tipi',
    baslangic: 'Başlangıç',
    bitis: 'Bitiş',
    gerekenSayi: 'Gereken Sayı',
    aralikNotu: (sure: string, yuk: string) =>
      `Aralık ${sure} saat sürer ve gün başına ${yuk} kişi-saat yük getirir. Tarih boş bırakılırsa satır o gün tipinin tamamı için geçerlidir; doldurulursa yalnız o gün için geçerli bir istisna olur ve o gün genel satırların yerine geçer.`,
    tatilIsaretle: 'resmî tatil işaretle',
    tatilDegistir: 'resmî tatil değiştir',
    tatilAdi: 'Tatil Adı',
    tatilOrnegi: '29 Ekim Cumhuriyet Bayramı',
    tatilNotu:
      'İşaretlenen gün, talep matrisinin resmî tatil satırından beslenir ve adalet hesaplarında hafta sonuyla aynı sayaca eklenir (SRS TD-3). Yalnızca yeni çözümleri etkiler; üretilmiş çizelgeler değişmez.',
  },

  cizelge: {
    tanimlarYuklenemedi: 'Tanımlar yüklenemedi.',
    surumlerYuklenemedi: 'Sürümler yüklenemedi.',
    cizelgeYuklenemedi: 'Çizelge yüklenemedi.',
    dogrulamaBasarisiz: 'Doğrulama başarısız.',
    kilitDegistirilemedi: 'Kilit değiştirilemedi.',
    kaydedilemedi: 'Kaydedilemedi: değişiklikler zorunlu bir kuralı bozuyor.',
    bosTaslakOnayi: (mevcut: number, yeni: number) =>
      `Dönemde ${mevcut} sürüm var; ${yeni}. sürüm boş bir taslak olarak açılacak.`,
    bosTaslakAcilamadi: 'Boş taslak açılamadı.',
    gun: 'Gün',
    hafta: 'Hafta',
    excelIpucu: 'Çizelge + özet + ham veri, biçimlenmiş çalışma kitabı',
    excelIndirilemedi: 'Excel dosyası indirilemedi.',
    indiriliyor: 'İndiriliyor…',
    excel: 'Excel',
    csvIpucu: 'Uzun biçim CSV + talep sapması dosyası (ham veri)',
    yazdirIpucu: 'Personel × saat ızgarası, yatay A4',
    yazdir: 'Yazdır',
    kaydedilmemis: (sayi: number) => `${sayi} KAYDEDİLMEMİŞ`,
    geriAlIpucu: 'Son değişikliği geri al',
    yenidenUygulaIpucu: 'Geri alınan değişikliği yeniden uygula',
    vazgec: 'Vazgeç',
    onceKaydet: 'Önce değişiklikleri kaydedin ya da vazgeçin',
    yenidenCoz: 'Yeniden Çöz',
    yenidenCozKilitsiz: (no: number) =>
      `Sürüm ${no} taban alınarak yeniden çözülür; bu sürümde kilitli atama yok.`,
    yenidenCozKilitli: (no: number, sayi: number) =>
      `Sürüm ${no} taban alınarak yeniden çözülür; ${sayi} kilitli atama korunur.`,
    secim: 'seçim',
    donem: 'Dönem',
    surum: 'Sürüm',
    surumSecenegi: (no: number, durum: string) => `Sürüm ${no} (${durum})`,
    surumRozeti: (durum: string, no: number) => `${durum} · SÜRÜM ${no}`,
    bosTaslakAc: 'Boş Taslak Aç',
    duzenlenemezNotu1: 'Değişiklik için Sürümler ekranında bu sürümün',
    duzenlenemezKopyala: '“Düzenlemek İçin Kopyala”',
    duzenlenemezNotu2:
      'düğmesini kullanın: çizelge olduğu gibi yeni taslağa taşınır. “Boş Taslak Aç” ise atamasız bir sürüm üretir; onu bu ekranda elle doldurabilir ya da çözücüye bırakabilirsiniz (FR-7.3).',
    suzgec: 'Süzgeç',
    tumYetkinlikler: 'Tüm yetkinlikler',
    tumNoktalar: 'Tüm noktalar',
    yalnizAcikGunler: 'Yalnızca açık verilen günler',
    kapsama: 'Kapsama',
    acik: 'Açık',
    toplamCeza: 'Toplam Ceza',
    yukleniyor: 'Yükleniyor…',
    atamaYok: 'Bu sürümde henüz atama yok.',
    personelYok: 'Bu dönemde aktif personel yok; Tanımlar ekranından personel ekleyin.',
    acikGunYok: 'Bu dönemde açık verilen gün yok. Süzgeci kaldırarak tüm günleri görebilirsiniz.',
    suzgecteYok: 'Seçili süzgeçlerde bu sürüme atanmış personel yok.',
    gunSecimi: 'Gün seçimi',
    saatBandi: 'saat bandı',
    kilitli: 'Kilitli',
    kapsamaAcigi: 'Kapsama açığı',
    sonuc: 'sonuç',
    degerlendiriliyor: 'Değerlendiriliyor…',
    baslangic: 'Başlangıç',
    bitis: 'Bitiş',
    gorevNoktasi: 'Görev Noktası',
    dokumGizle: 'Ceza dökümünü gizle',
    dokumGoster: 'Ceza dökümünü göster',
    agirlik: 'Ağırlık',
    agirlikli: 'Ağırlıklı',
    /**
     * "36 personelin 10'u gösteriliyor".
     *
     * ÜÇÜNCÜ PARAMETRE yalnız Türkçe'de kullanılıyor: sayıya gelen belirtme
     * eki sayının okunuşuna bağlı (`belirtmeHaliEki`). İngilizce karşılığı
     * onu hiç almıyor ve TypeScript buna izin veriyor: daha az parametreli
     * bir fonksiyon, daha çok parametreli bir tipe atanabilir. Çağrı yeri
     * eki her zaman hesaplar, İngilizce dal görmezden gelir.
     */
    personelGosterimi: (toplam: string, gosterilen: string, ek: string) =>
      `${toplam} personelin ${gosterilen}${ek} gösteriliyor`,
  },

  analiz: {
    tanimlarYuklenemedi: 'Tanımlar yüklenemedi.',
    surumlerYuklenemedi: 'Sürümler yüklenemedi.',
    analizYuklenemedi: 'Analiz yüklenemedi.',
    disaAktarmaBasarisiz: 'Dışa aktarma başarısız.',
    excelIndirilemedi: 'Excel dosyası indirilemedi.',
    indiriliyor: 'İndiriliyor…',
    excel: 'Excel',
    secim: 'seçim',
    donem: 'Dönem',
    surum: 'Sürüm',
    surumSecenegi: (no: number, durum: string) => `Sürüm ${no} (${durum})`,
    yukleniyor: 'Yükleniyor…',
    donemKapsamasi: 'dönem kapsaması',
    taleptenFazla: 'talepten fazla',
    enDengesiz: 'en dengesiz',
    toplamCezaBasligi: 'toplam ceza',
    personel: 'Personel',
    adilPayKisa: 'Adil pay',
    sapma: 'Sapma',
    saatKisa: 'sa',
    karsilanmayan: 'karşılanmayan',
    kisiSaat: 'kişi-saat',
    acikAralik: (sayi: number) => `${sayi} açık aralık`,
    tercihKarsilama: 'tercih karşılama',
    olcumUfku: 'ölçüm ufku',
    planlamaDonemi: 'Planlama dönemi',
    adaletUfku: 'Adalet ufku · 90 gün',
    ufukDonem: 'Yük ve pay yalnızca bu dönemi kapsar (kabul kriteri, Charter 5).',
    ufukAdalet:
      'Yük ve pay son doksan günü kapsar; geçmiş yayınlanmış sürümler dahil (SRS TD-6).',
    geceDagilimi: 'gece saati dağılımı · kişi başına',
    geceBos: 'Bu sürümde gece ataması yok.',
    geceHavuz: 'Ölçü, gece talebine erişebilen personeli kapsar (SRS S2, P_gece).',
    haftaSonuDagilimi: 'hafta sonu saati dağılımı · kişi başına',
    haftaSonuBos: 'Bu sürümde hafta sonu ataması yok.',
    haftaSonuHavuz: 'Ölçü, hafta sonu talebine erişebilen personeli kapsar (SRS S3, P_hs).',
    saatDengesi: 'toplam saat dengesi · personel başına',
    herkesTutturdu: 'Herkes kendi adil payını tutturdu.',
    saatSutunlari: ['PERSONEL', 'TOPLAM SAAT', 'ADİL PAY', 'SAPMA'],
    ortakKayma: (yon: string, ortanca: string) =>
      `Bu dönemde herkesin toplamı payının ${yon}: talep, hedeflerin toplamıyla örtüşmüyor. Anlamlı olan kişiler arası fark; renk ortancadan (${ortanca}) uzaklığa göre.`,
    altinda: 'altında',
    ustunde: 'üstünde',
    ortancaAciklamasi: 'Renk, ortancadan on beş saatten fazla uzaklaşan kişileri işaretler.',
    enUzaktakiler: (sayi: number) => ` En uzaktaki ${sayi} kişi gösteriliyor.`,
    cezaDokumu: 'ceza dökümü',
    binaDegisimi: 'bina değişim sayısı',
    adilPayaGore: 'Adil paya göre konum',
    yuk: 'Yük',
    bandIcinde: 'Adil payın taban/tavan bandı içinde, cezasız',
    cezalandirilanSapma: (saat: string) => `Çözücünün cezalandırdığı sapma: ${saat} saat`,
    payinAltinda: '← payının altında',
    payinUstunde: 'payının üstünde →',
    dahaGoster: (sayi: number) => `${sayi} kişi daha göster`,
    yalnizEnUzaktaki: (sayi: number) => `Yalnız en uzaktaki ${sayi} kişi`,
    referansAciklamasi: 'kişiye düşen adil pay (referans)',
    kotaBasligi: 'yıllık fazla çalışma kotası',
    kotaSutunlari: ['PERSONEL', 'DEVİR', 'BU DÖNEM', 'KALAN KOTA'],
    kotaNotu:
      '"Bu dönem", haftalık eşiği aşan saattir: sıfır olması kişinin bu dönemde eşiği aşmadığı anlamına gelir, kotasının boş olduğu anlamına değil.',
    kotaRiskli: (sayi: number, esik: number) =>
      `${sayi} kişinin kalan kotası ${esik} saatin altında.`,
    kotaGuvenli: (sayi: number) =>
      `Kimse sınıra yakın değil; en az kalanı olan ${sayi} kişi gösteriliyor.`,
    dokumSutunlari: ['HEDEF', 'HAM DEĞER', 'AĞIRLIK', 'AĞIRLIKLI CEZA'],
    dokumNotu:
      'Ham değer kuralın kendi biriminde ölçülür (kişi-saat, saat, gün); ağırlıklı ceza amaç fonksiyonuna giren sayıdır.',
    dokumCozucu: ' Döküm çözüm işinden geliyor.',
    dokumKurallardan:
      ' Bu sürümde çözücü çalışmadı ya da çizelge sonradan elle değişti; döküm kural motorundan hesaplandı.',
    geceAdaleti: 'gece yükü adaleti · önceki yayınlanmış döneme göre',
    olcumeGirenYok: 'Ölçüme giren personel yok.',
    oncekiDonemYok: 'Karşılaştırılacak önceki yayınlanmış dönem yok. Bu dönemin ortalama gece sapması',
    onceki: 'önceki',
    simdi: 'şimdi',
    degismedi: 'değişmedi',
    azaliyor: '↓ azalıyor',
    artiyor: '↑ artıyor',
    geceOlcuAciklamasi:
      'Ölçü, kişi başına gece saatinin adil paydan ortalama sapmasıdır: 0 sa, herkesin gece yükünün payına eşit olması demektir. Her dönem kendi içinde ölçülür; sayının dönemden döneme küçülmesi, gece yükünün zamanla eşitlendiği anlamına gelir. Kümülatif adaletin vaadi sapmanın küçük olması değil, ZAMANLA küçülmesidir.',
  },

  surumler: {
    donemlerYuklenemedi: 'Dönemler yüklenemedi.',
    surumlerYuklenemedi: 'Sürümler yüklenemedi.',
    yayinlanamadi: 'Sürüm yayınlanamadı.',
    turetilemedi: 'Taslak türetilemedi.',
    kopyalanamadi: 'Sürüm kopyalanamadı.',
    silinemedi: 'Sürüm silinemedi.',
    karsilastirilamadi: 'Karşılaştırma yapılamadı.',
    karsilastir: 'Karşılaştır',
    donemEtiketi: 'Dönem:',
    surumSayisi: (sayi: number) => `${sayi} sürüm`,
    karsilastirBasligi: 'sürüm karşılaştır',
    oncekiSurum: 'Önceki sürüm',
    yeniSurum: 'Yeni sürüm',
    surumSecenegi: (no: number, durum: string) => `Sürüm ${no} (${durum})`,
    karsilastiriliyor: 'Karşılaştırılıyor…',
    farklariGetir: 'Farkları Getir',
    surumYok: 'Bu dönemde henüz sürüm yok.',
    surumNo: (no: number) => `Sürüm ${no}`,
    acik: 'Açık',
    kopyalaIpucu: 'Bu sürümün çizelgesini olduğu gibi taşıyan bir taslak açar; kaynak sürüm değişmez',
    kopyala: 'Düzenlemek İçin Kopyala',
    bosTaslakIpucu:
      'Atamasız bir taslak açar; Çizelge ekranından elle doldurabilir ya da çözücüye bırakabilirsiniz',
    bosTaslakAc: 'Boş Taslak Aç',
    atamaYokYayinlanamaz: 'Atama yok, yayınlanamaz',
    bosYayinUyarisi:
      'Bu sürümde hiç atama yok; yayınlanırsa çalışan panelinde çizelge boş görünür. Önce Çizelge ekranından doldurun ya da çözücüyü çalıştırın.',
    yayinla: 'Yayınla',
    silIpucu: 'Bu sürümü ve atamalarını siler; denenip vazgeçilmiş taslaklar birikmesin diye',
    sil: 'Sil',
    silmeOnayi: (no: number, atamalar: string) => `Sürüm ${no} ve ${atamalar} silinecek.`,
    atamaSayisi: (sayi: number) => `${sayi} ataması`,
    atamalari: 'atamaları',
    silmeNotu:
      'Geri alınamaz. Yayınlanmış ve arşivlenmiş sürümler silinemez; bu sürüm ikisi de değil.',
    vazgec: 'Vazgeç',
    kopyaOnayi: (no: number, atamalar: string) =>
      `Sürüm ${no}, ${atamalar} yeni bir taslak sürüme kopyalanacak.`,
    kopyaAtamaSayisi: (sayi: number) => `${sayi} atamasıyla birlikte`,
    kopyaAtamalari: 'atamalarıyla birlikte',
    kopyaNotu: (no: number) =>
      `Sürüm ${no} olduğu gibi kalır: durumu değişmez, atamalarına dokunulmaz. Düzenleme yeni taslak üzerinde yapılır.`,
    kopyalaniyor: 'Kopyalanıyor…',
    onaylaKopyala: 'Onayla ve Kopyala',
    yayinOnayiArsiv: (yeni: number, eski: number) =>
      `Sürüm ${yeni} yayınlanacak, Sürüm ${eski} arşive alınacak.`,
    yayinOnayi: (no: number) => `Sürüm ${no} yayınlanacak.`,
    yayinNotu: 'Yayınlanan sürüm salt okunur olur, üzerinde elle düzenleme yapılamaz.',
    yayinlaniyor: 'Yayınlanıyor…',
    onaylaYayinla: 'Onayla ve Yayınla',
    farkBasligi: (onceki: number, yeni: number, degisen: number) =>
      `Sürüm ${onceki} → Sürüm ${yeni} · ${degisen} değişen atama`,
    fark: { eklendi: 'Eklendi', kaldirildi: 'Kaldırıldı', degisti: 'Değişti' },
    farkYok: 'İki sürüm arasında farklı atama yok.',
    farkSutunlari: ['PERSONEL', 'GÜN', 'TÜR', 'ÖNCEKİ', 'YENİ'],
  },

  sonuc: {
    hedefler: {
      S1: { konu: 'kapsama açığı', birim: 'kişi' },
      S1f: { konu: 'talepten fazla kadro', birim: 'kişi' },
      S2: { konu: 'gece adaleti', birim: 'saat' },
      S3: { konu: 'hafta sonu adaleti', birim: 'saat' },
      S4: { konu: 'toplam saat dengesi', birim: 'saat' },
      S5: { konu: 'tercih karşılama', birim: 'tercih' },
      S6: { konu: 'çalışma deseni', birim: 'gün' },
      S6b: { konu: 'bina tutarlılığı', birim: 'gün' },
      S7: { konu: 'izole çalışma günü', birim: 'gün' },
      S8: { konu: 'önceki sürümden sapma', birim: 'atama' },
    } as Record<string, { konu: string; birim: string }>,
    acikArtti: (miktar: string) => `kapsama açığı ${miktar} arttı`,
    acikAzaldi: (miktar: string) => `kapsama açığı ${miktar} azaldı`,
    fazlaAtandi: (miktar: string) => `talepten ${miktar} fazla atandı`,
    fazlaAzaldi: (miktar: string) => `talepten fazla kadro ${miktar} azaldı`,
    bozuldu: (konu: string, miktar: string) => `${konu} ${miktar} bozuldu`,
    iyilesti: (konu: string, miktar: string) => `${konu} ${miktar} iyileşti`,
    tekIhlal: 'Bu değişiklik bir zorunlu kuralı bozuyor ve uygulanmadı.',
    cokIhlal: (sayi: number, kurallar: string) =>
      `Bu değişiklik ${sayi} zorunlu kuralı bozuyor ve uygulanmadı (${kurallar}).`,
    etkiYok: 'Değişiklik hiçbir hedefi etkilemedi.',
    kalanHedef: (sayi: number) => ` ve ${sayi} hedef daha etkilendi.`,
  },

  cozum: {
    durum: {
      kuyrukta: 'Kuyrukta',
      on_kontrol: 'Ön Kontrol',
      cozuluyor: 'Çözülüyor',
      durduruldu: 'Karar Bekleniyor',
      tamamlandi: 'Tamamlandı',
      uyarili: 'Uyarılı Tamamlandı',
      basarisiz: 'Başarısız',
      iptal: 'İptal Edildi',
    },
    donemlerYuklenemedi: 'Dönemler yüklenemedi.',
    onKontrolBasarisiz: 'Ön kontrol başarısız.',
    baslatilamadi: 'Çözüm başlatılamadı.',
    durdurmaBasarisiz: 'Durdurma isteği başarısız.',
    kararUygulanamadi: 'Karar uygulanamadı.',
    donemOlusturulamadi: 'Dönem oluşturulamadı.',
    atOnayi: 'Bulunan çözüm silinecek. Bu işlem geri alınamaz.',
    ayarlar: 'çözüm ayarları',
    donem: 'Dönem',
    yeniDonem: 'Yeni Dönem',
    onKontrol: 'Ön Kontrol',
    baslat: 'Çözümü Başlat',
    yenidenCozIpucu: 'Seçili sürümden yeniden çözer; kilitli atamalar olduğu gibi korunur',
    sifirdanIpucu: 'Dönem için sıfırdan çözer',
    yenidenCozumBasligi: 'Yeniden çözüm.',
    yenidenCozumGovde:
      'Çizelge ekranından seçtiğiniz sürüm taban alınır: kilitli atamalar korunur, kalanını çözücü yeniden yazar. Başka bir dönem seçmek tabanı kaldırır ve çözüm sıfırdan başlar.',
    tabanNotu:
      'sürüm taban alınır: kilitli atamalar korunur, kalanını çözücü yeniden yazar. Başka bir dönem seçmek tabanı kaldırır ve çözüm sıfırdan başlar.',
    yeniPlanlamaDonemi: 'yeni planlama dönemi',
    baslangic: 'Başlangıç',
    bitis: 'Bitiş',
    donemiOlustur: 'Dönemi Oluştur',
    iptal: 'İptal',
    gunSayisi: 'Seçilen aralık',
    gunSayisiSonek: (azami: number) => `gün · en fazla ${azami} gün`,
    engelYok: 'Yapısal bir engel bulunamadı.',
    engel: 'Engel',
    uyari: 'Uyarı',
    gecenSure: 'Geçen Süre',
    enIyiCeza: 'En İyi Ceza',
    toplamCeza: 'Toplam Ceza',
    kapsamaAcigi: 'Kapsama Açığı',
    durdurAramaVar:
      'Durdur, aramayı sonlandırır; o ana kadar bulunmuş çözüm atılmaz, kararınız için saklanır.',
    durdurAramaYok:
      'Arama henüz başlamadı. Durdur, işi doğrudan iptal eder; saklanacak bir sonuç olmadığı için karar sorulmaz.',
    aramaSonlandi:
      'Arama sonlandırıldı. Bulunan çözüm henüz çizelgeye yazılmadı; sürüm durdurma öncesindeki hâlinde duruyor.',
    uygunSonucYok:
      'Çözücü ilk uygun çizelgeye ulaşmadan durduruldu; kullanılabilir bir sonuç yok.',
    sonucKullanilamaz: 'Bu nedenle "Sonucu kullan" seçilemiyor.',
    sonucuKullan: 'Sonucu kullan',
    sonucuAt: 'Sonucu at',
    bundanDevam: 'Bu çözümden devam et',
    yeniZamanLimiti: 'Yeni zaman limiti (saniye)',
    devamNotu:
      '"Devam et", bulunan çözümü başlangıç ipucu olarak veren yeni bir arama başlatır; süre sıfırdan işler ve sonuç bu çözümden kötü olmaz.',
    sonucOzeti: (durum: string) => `sonuç özeti · ${durum}`,
    isIptal: 'İş iptal edildi. Çizelge sürümü değişmedi.',
    kapsamaBulundu: (sayi: number) =>
      `${sayi} kapsama açığı bulundu; Çizelge ekranında ilgili hücreler işaretlendi.`,
    cizelgeyiGoruntule: 'Çizelgeyi Görüntüle',
  },

  ozet: {
    veriYuklenemedi: 'Özet verisi yüklenemedi.',
    surumYuklenemedi: 'Sürüm verisi yüklenemedi.',
    bosTaslak:
      'Bu dönemin son sürümü henüz boş bir taslak. Çizelge ekranından elle çizebilir ya da Çözüm ekranını kullanabilirsin.',
    donemIcin: (aralik: string) => `${aralik} dönemi için`,
    kapsama: 'kapsama',
    eksikHucre: 'eksik hücre',
    toplamCeza: 'toplam ceza',
    bekleyenTercih: 'bekleyen tercih',
    surumDurumuBasligi: 'sürüm durumu',
    kisi: (sayi: number) => `${sayi} kişi`,
    kayit: 'kayıt',
    cezaKaynagi: {
      cozucu: 'çözüm işinden · S8 dahil',
      kurallardan: 'kurallardan hesaplandı · S8 hariç',
      yok: '',
    },
    cezaKaynagiCozucu:
      'Döküm çözüm işinden geliyor; sayı amaç fonksiyonunun tamamıdır, önceki sürümden sapma (S8) dahil.',
    cezaKaynagiKurallardan:
      'Bu sürümde çözücü çalışmadı ya da çizelge sonradan elle değişti; döküm kural motorundan hesaplandı. Önceki sürümden sapma (S8) bu hesaba GİRMEZ: kaynak değişince sayının kapsamı da değişir, iki kaynağın toplamı doğrudan karşılaştırılamaz.',
    gunlukKapsama: 'günlük kapsama',
    gunlukKapsamaAralik: (aralik: string) => `günlük kapsama · ${aralik}`,
    kapsamaVerisiYok: 'Bu sürüm için günlük kapsama verisi yok.',
    gunAcikKayitlari: (gun: string) => `${gun} günü açık kayıtları`,
    donemAcikKayitlari: 'Dönemin açık kayıtları',
    acikKayitYok: 'Açık kayıt yok.',
    kisiBasinaSaat: 'kişi başına saat',
    kisiBasinaSaatAralik: (aralik: string) => `kişi başına saat · ${aralik}`,
    saatSapmasiYok: 'Bu sürümde saat sapması yok.',
    tumunuAnalizde: 'Tümünü Analiz ekranında görüntüle',
    musaitOlmayanlar: 'bu dönem müsait olmayanlar',
    musaitOlmayanlarAralik: (aralik: string) => `bu dönem müsait olmayanlar · ${aralik}`,
    musaitOlmayanYok: 'Bu dönemde müsait olmayan yok.',
    yaklasanKayitlar: 'yaklaşan müsaitlik kayıtları · bugünden itibaren',
    yaklasanYok: 'Yaklaşan kayıt yok.',
  },

  musaitlik: {
    dilim: { tam_gun: 'TAM', ogleden_once: 'ÖÖ', ogleden_sonra: 'ÖS' },
    tip: { yillik_izin: 'İzin', rapor: 'Rapor', egitim: 'Eğitim', mazeret: 'Mazeret' },
    yuklenemedi: 'Müsaitlik kayıtları yüklenemedi.',
    olusturulamadi: 'Kayıt oluşturulamadı.',
    silinemedi: 'Kayıt silinemedi.',
    kadroRiski: (a: string, b: string) => `${a} ve ${b} aynı dönemde izinli; kadro riski oluşabilir.`,
    kayitEkle: 'Kayıt Ekle',
    yeniKayit: 'yeni müsaitlik kaydı',
    dilimEtiketi: 'Dilim',
    tipEtiketi: 'Tip',
    personelEtiketi: 'Personel',
    baslangic: 'Başlangıç',
    bitis: 'Bitiş',
    iptal: 'İptal',
    sil: 'Sil',
    kayitYok: 'Henüz müsaitlik kaydı yok.',
    sutunlar: ['PERSONEL', 'BAŞLANGIÇ', 'BİTİŞ', 'DİLİM', 'TİP', 'BELGE', ''],
    belgeAlinamadi: 'Belge alınamadı.',
    belgeTipi: 'Yalnızca PNG, JPEG ya da PDF yüklenebilir.',
    belgeBuyuk: 'Dosya çok büyük (azami 5 MB).',
    belgeYuklenemedi: 'Belge yüklenemedi.',
    indir: 'İndir',
    yukleniyor: 'Yükleniyor…',
    ekle: 'Ekle',
  },

  kullanicilar: {
    roller: [
      { deger: 'calisan', etiket: 'Çalışan', aciklama: 'Yalnız kendi çizelgesi, özeti ve tercihleri' },
      { deger: 'idare', etiket: 'Yönetici', aciklama: 'Vardiya yöneticisinin bütün işlevleri' },
      { deger: 'hesap_yoneticisi', etiket: 'Yönetim', aciklama: 'Yöneticinin yetkileri ve hesap yönetimi' },
    ],
    yuklenemedi: 'Hesaplar yüklenemedi.',
    hesapYok: 'Henüz hesap yok.',
    parolaBekliyor: 'Parola bekliyor',
    rolEtiketi: 'Rol',
    degistir: 'Değiştir',
    parolaSifirla: 'Parola Sıfırla',
    onceSec: 'Önce listeden bir hesap seçin',
    pasifleriGoster: 'Pasifleri göster',
    hesabiDegistir: 'hesabı değiştir',
    yeniHesap: 'yeni hesap',
    kullaniciAdi: 'Kullanıcı adı',
    kullaniciAdiKurali: 'Küçük harf, rakam, nokta, tire; 3–50 karakter.',
    baslangicParolasi: 'Başlangıç parolası',
    parolaKurali: 'En az 12 karakter. Kullanıcı ilk girişte değiştirmek zorunda.',
    kendiRolun: 'Kendi rolünüzü değiştiremezsiniz.',
    personelKaydi: 'Personel kaydı',
    bagliDegil: 'bağlı değil',
    calisanBaglanmali: 'Çalışan hesabı bir personel kaydına bağlanmak zorunda.',
    bosBirakilabilir: 'Yönetici ve yönetim rollerinde boş bırakılabilir.',
    kendiHesabin: 'Kendi hesabınızı kapatamazsınız.',
    kapatmaNotu: 'Kapatıldığında hesap silinmez; girişi durur ve açık oturumları kapanır.',
    vazgec: 'Vazgeç',
    sifirlanamadi: 'Sıfırlanamadı.',
    sifirlamaBasligi: 'parola sıfırlama',
    sifirlamaUyarisi: (kullanici: string) =>
      `${kullanici} hesabına yeni bir başlangıç parolası atanacak. Kullanıcı ilk girişte parolayı değiştirmek zorunda kalacak ve açık oturumlarının hepsi kapanacak.`,
    yeniBaslangicParolasi: 'Yeni başlangıç parolası',
    parolayiSifirla: 'Parolayı Sıfırla',
  },

  parolaEkrani: {
    urunAdi: 'Vardiya Çizelgeleme',
    baslik: 'Parola Değiştir',
    zorunluAciklama:
      'Parolanız yönetim tarafından atandı. Devam etmeden önce kendi parolanızı belirlemeniz gerekiyor.',
    mevcut: 'Mevcut parola',
    yeni: 'Yeni parola',
    tekrar: 'Yeni parola (tekrar)',
    asgariUzunluk: (n: number) => `Yeni parola en az ${n} karakter olmalı.`,
    ayniDegil: 'İki parola aynı değil.',
    kaydediliyor: 'Kaydediliyor…',
    kaydet: 'Parolayı Değiştir',
    vazgec: 'Vazgeç',
    degistirilemedi: 'Parola değiştirilemedi.',
  },

  tercihYonetimi: {
    bekleyen: 'Bekleyen',
    onaylandi: 'Onaylandı',
    reddedildi: 'Reddedildi',
    calismamaTercihi: 'Çalışmama tercihi',
    zamanAraligiTercihi: 'Zaman aralığı tercihi',
    araligiTercihi: (aralik: string) => `${aralik} tercihi`,
    buDurumdaYok: 'Bu durumda tercih yok.',
    retGerekcesi: 'Ret gerekçesi (isteğe bağlı)',
    reddet: 'Reddet',
    onayla: 'Onayla',
    yuklenemedi: 'Tercihler yüklenemedi.',
    guncellenemedi: 'Tercih güncellenemedi.',
  },

  kunye: {
    altBaslik: 'Vardiya çizelgeleme karar destek aracı',
    tanitim1:
      'VARDİS, vardiya çizelgesini elle kurmak yerine kısıt programlama ile üreten bir karar destek aracıdır. Personeli saatlik talebe atarken dinlenme süresi, haftalık saat tavanı ve yetkinlik gibi zorunlu kuralları ihlal etmez; gece saati, hafta sonu ve toplam yük gibi esnek hedefleri ise adil dağıtmaya çalışır.',
    tanitim2:
      'Aracın verdiği şey bir emir değil bir öneridir: üretilen her çizelge açıklanabilir. Hangi kuralın ne kadar cezalandırıldığı, kimin payından ne kadar saptığı ve talebin nerede karşılanamadığı ekranda görünür. Karar yöneticidedir; araç yalnızca kararın bedelini görünür kılar.',
    projeBasligi: 'proje',
    gelistirmeBasligi: 'geliştirme',
    sunucu: 'Sunucu',
    mimari: 'Mimari',
    gelistiren: 'Geliştiren',
    rol: 'Sistem analisti ve geliştirici, projenin yürütücüsü',
    rolEtiketi: 'Rol',
    kapsam: 'Kapsam',
    kapsamMetni: 'Bir yaz stajı çalışması kapsamında geliştirildi; hiçbir kurumun verisini içermez.',
    demoNotu:
      'Uygulamadaki personel, görev noktası ve talep kayıtları üretilmiş demo verisidir; gerçek bir kadroyu ya da çalışma düzenini yansıtmaz.',
    teknikBaslik: 'teknik künye',
    cozucu: 'Çözücü',
    arayuz: 'Arayüz',
    veritabani: 'Veritabanı',
    surecNotu:
      'Çözücü ayrı bir süreçte koşar; uygulama sunucusu iş kaydı oluşturur, işçi kuyruktan alır. İki süreç arasındaki tek sözleşme veritabanıdır.',
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
  istekBasarisiz: (durum: number) => `The request failed (HTTP ${durum}).`,

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


  yuzde: (deger: number | string) => `${deger}%`,

  surumDurumu: {
    taslak: 'Draft',
    cozuldu: 'Solved',
    yayinlandi: 'Published',
    arsiv: 'Archived',
  },

  izgara: {
    blokIslemleri: 'Block actions',
    gorevNoktasi: 'Duty point',
    kilidiAc: 'Unlock',
    kilitle: 'Lock',
    blogunuSil: 'Delete block',
    basamakSirasi: (noktalar: string) => `Step order: ${noktalar}`,
    gunIzgarasinaGec: (tarih: string) => `${tarih} · go to the day grid`,
    oncekiGunden: ' (from the previous day)',
    oncekiGundenDevam: 'continues from the previous day',
    ertesiGuneTasiyor: 'carries into the next day',
    ertesiGune: ' (into the next day)',
    gunlukKapsamaAcigi: 'Daily coverage gap',
    gunEksik: (tarih: string, saat: number) => `${tarih} · ${saat} person-hours short`,
  },

  yazdirma: {
    baslik: 'Shift Schedule',
    gun: 'days',
    uretildi: (tarih: string) => `produced on ${tarih}`,
    kapsamaAciklari: 'Coverage gaps',
    acikYok: 'No coverage gaps in this version.',
    acikOzeti: (aralik: number, kisi: number) =>
      `${kisi} people short across ${aralik} ranges in total.`,
    acikSutunlari: ['Date', 'Hours', 'Duty point', 'Short'],
    fazlaOzeti: (aralik: number, kisi: number) =>
      `${kisi} people above demand across ${aralik} ranges in total. SRS 4.3 S1 defines this limit as soft; exceeding it comes from a manual edit.`,
    fazlaSutunlari: ['Date', 'Hours', 'Duty point', 'Above'],
    yazdir: 'Print',
    sayfaNotu: 'Landscape A4 · each day on its own page, the hour header repeated on every page.',
  },

  tanimYonetimi: {
    gizliPasif: (sayi: number) =>
      sayi === 1 ? '1 inactive record hidden.' : `${sayi} inactive records hidden.`,
    kullanimAlinamadi: 'Could not fetch usage information.',
    pasiflestirmeOnayi: 'confirm deactivation',
    silmeOnayi: 'confirm deletion',
    kontrolEdiliyor: 'Checking usage…',
    kullaniliyorNotu:
      'uses it. The record will not be deleted but deactivated: it is not used in new solves and keeps appearing in existing schedules.',
    kullanilmiyorNotu: ' is not used in any record. It will be deleted permanently.',
    pasiflestir: 'Deactivate',
    kaliciSil: 'Delete permanently',
    vazgec: 'Cancel',
  },

  kuralUyarilari: {
    yetkinlikCakismasi: (a: string, b: string) =>
      `${a} and ${b} were selected together. SRS 3.3.2 defines these two as mutually exclusive: a reception officer cannot work at another point, and a security officer cannot work at the reception point. The record is not blocked; carry on if this is deliberate.`,
    s1Pasif:
      'S1 is inactive: the demand constraint is not added to the model. No shift has to be filled (the result may be an empty schedule), a duty point may be staffed above its demand, and because no coverage gap is computed at all, the Analysis and Schedule screens report unmet demand as "0 gaps".',
    aktiflik: 'Active',
    aktif: 'Active',
    pasif: 'Inactive',
    agirlik: 'Weight',
    asgariBlok: (saat: number) => `Minimum block ${saat} hours (H1)`,
    gunlukAzami: (saat: number) => `${saat} hours per day at most (H9)`,
    tarihSecin: 'Choose a start and an end date.',
    bitisOnce: 'The end date cannot be before the start date.',
    donemUzun: (azami: number, secilen: number) =>
      `A planning period can be ${azami} days at most; the selected range is ${secilen} days. Choose an earlier end date.`,
  },

  tanimlar: {
    sekmeler: {
      'Talep': 'Demand',
      'Personel': 'Staff',
      'Yetkinlik': 'Competencies',
      'Bina': 'Buildings',
      'Görev Noktası': 'Duty points',
      'Özel Gün': 'Special days',
      'Kural': 'Rules',
    },
    gunTipi: { hafta_ici: 'Weekday', hafta_sonu: 'Weekend', resmi_tatil: 'Public holiday' },
    yuklenemedi: 'Could not load the definitions.',
    ozelGunSilinemedi: 'Could not delete the special day.',
    talepSilinemedi: 'Could not delete the demand range.',
    kuralGuncellenemedi: 'Could not update the rule.',
    kayitKaydedilemedi: 'Could not save the record.',
    talepKaydedilemedi: 'Could not save the demand range.',
    ozelGunKaydedilemedi: 'Could not save the special day.',
    araligiCakisiyor: (mesaj: string) =>
      `The range overlaps: ${mesaj}. Hours cannot overlap for the same duty point and day type.`,
    noktaSayisi: (sayi: number) => (sayi === 1 ? '1 duty point' : `${sayi} duty points`),
    binaTanimliDegil:
      'No buildings are defined; in the current application area every duty point is site-wide (SRS 3.3.3).',
    onkosulVar: 'Has a prerequisite',
    onkosulYok: 'No prerequisite',
    degistir: 'Edit',
    degisiklikYok: 'No changes',
    vazgec: 'Discard',
    iptal: 'Cancel',
    sil: 'Delete',
    onceNoktaTanimla: 'Define a duty point first',
    onceAralikSec: 'Select a range from the list first',
    onceGunSec: 'Select a day from the list first',
    onceKayitSec: 'Select a record from the list first',
    pasifleriGoster: 'Show inactive',
    talepBasligi: (sayi: number) =>
      sayi === 1 ? 'demand ranges · 1 record' : `demand ranges · ${sayi} records`,
    talepYok:
      'No demand range is defined. With no range entered the solve asks for nobody: the coverage constraint (SRS 4.3 S1) is written over demand hours, and empty demand produces no gaps at all.',
    talepSutunlari: ['DUTY POINT', 'DAY TYPE', 'DATE', 'RANGE', 'LENGTH', 'REQUIRED'],
    talepNotu:
      'Ranges start and end on the hour; the end of the day is 24.00. Two overlapping ranges are not accepted for the same duty point and day type: overlapping records would give two different required counts for the same hour. A row with a date belongs to that day only and replaces the general rows for it.',
    haftalikYuk: 'WEEKLY PERSON-HOUR LOAD',
    asgariKadro: 'MINIMUM HEADCOUNT (BY THE OVERTIME THRESHOLD)',
    tatilYok:
      'No public holiday is marked. Marked days are fed from the public holiday column of the demand matrix and count towards the same fairness counter as weekends (SRS TD-3).',
    tatilTakvimi: (sayi: number) =>
      sayi === 1 ? 'public holiday calendar · 1 day' : `public holiday calendar · ${sayi} days`,
    degisiklikleriKaydet: 'save the changes',
    kaydedilecek: (sayi: number) =>
      sayi === 1 ? '1 change will be saved' : `${sayi} changes will be saved`,
    ardindanSekme: (sekme: string) => `, then the ${sekme} tab will open.`,
    s1Uyarisi: (s1: string, toplam: string) =>
      `The S1 weight (${s1}) is not above the sum of the other active soft goals (${toplam}); it loses its dominance over meeting demand.`,
    s1UyarisiUzun: (s1: string, toplam: string) =>
      `The S1 weight (${s1}) is not above the sum of the other active soft goals (${toplam}). It loses its dominance over meeting demand: the solver may prefer to leave a coverage gap in order to improve a goal such as fairness or preferences.`,
    duzenlemeyeDon: 'Back to editing',
    zorunluKisitlar: 'H1–H8 · hard constraints',
    katalogNotu:
      'Catalogue rules form the structure of the model; they cannot be deleted, only disabled, and their parameters changed.',
    agirlik: 'Weight',
    formBasligi: (sekme: string, yeni: boolean) => `${yeni ? 'add' : 'edit'} ${sekme}`,
    aktiflikBaslangic: 'Active from',
    aktiflikBitis: 'Active until',
    devirFazlaCalisma: 'Carried-over overtime (hours)',
    kotaYili: 'Quota year',
    aciklama: 'Description',
    onkosulYetkinlik: 'Prerequisite competency',
    yetkinlikYok: 'No competencies defined; add one from the Competencies tab first.',
    pasifNotu:
      'An inactive record is not used in new solves; it keeps appearing in existing schedules.',
    aktiflikNotu:
      'On days outside the active window a person is not considered available (H7). Leaving the end empty makes the window open-ended; to run it up to today use the Delete action, which closes the window on the previous day.',
    talepEkle: 'add demand range',
    talepDegistir: 'edit demand range',
    gorevNoktasi: 'Duty point',
    gunTipiEtiketi: 'Day type',
    baslangic: 'Start',
    bitis: 'End',
    gerekenSayi: 'Required count',
    aralikNotu: (sure: string, yuk: string) =>
      `The range lasts ${sure} hours and brings ${yuk} person-hours of load per day. Leaving the date empty makes the row apply to that whole day type; filling it makes it an exception valid for that day only, replacing the general rows.`,
    tatilIsaretle: 'mark public holiday',
    tatilDegistir: 'edit public holiday',
    tatilAdi: 'Holiday name',
    tatilOrnegi: '29 October Republic Day',
    tatilNotu:
      'A marked day is fed from the public holiday row of the demand matrix and counts towards the same fairness counter as weekends (SRS TD-3). It affects new solves only; schedules already produced do not change.',
  },

  cizelge: {
    tanimlarYuklenemedi: 'Could not load the definitions.',
    surumlerYuklenemedi: 'Could not load the versions.',
    cizelgeYuklenemedi: 'Could not load the schedule.',
    dogrulamaBasarisiz: 'Validation failed.',
    kilitDegistirilemedi: 'Could not change the lock.',
    kaydedilemedi: 'Not saved: the changes break a hard rule.',
    bosTaslakOnayi: (mevcut: number, yeni: number) =>
      `The period has ${mevcut} versions; version ${yeni} will open as an empty draft.`,
    bosTaslakAcilamadi: 'Could not open an empty draft.',
    gun: 'Day',
    hafta: 'Week',
    excelIpucu: 'Schedule, summary and raw data in a formatted workbook',
    excelIndirilemedi: 'Could not download the Excel file.',
    indiriliyor: 'Downloading…',
    excel: 'Excel',
    csvIpucu: 'Long-form CSV plus the demand deviation file (raw data)',
    yazdirIpucu: 'Staff × hour grid, landscape A4',
    yazdir: 'Print',
    kaydedilmemis: (sayi: number) => `${sayi} UNSAVED`,
    geriAlIpucu: 'Undo the last change',
    yenidenUygulaIpucu: 'Redo the undone change',
    vazgec: 'Discard',
    onceKaydet: 'Save or discard your changes first',
    yenidenCoz: 'Re-solve',
    yenidenCozKilitsiz: (no: number) =>
      `Re-solves with version ${no} as the base; this version has no locked assignments.`,
    yenidenCozKilitli: (no: number, sayi: number) =>
      sayi === 1
        ? `Re-solves with version ${no} as the base; 1 locked assignment is kept.`
        : `Re-solves with version ${no} as the base; ${sayi} locked assignments are kept.`,
    secim: 'selection',
    donem: 'Period',
    surum: 'Version',
    surumSecenegi: (no: number, durum: string) => `Version ${no} (${durum})`,
    surumRozeti: (durum: string, no: number) => `${durum} · VERSION ${no}`,
    bosTaslakAc: 'Open empty draft',
    duzenlenemezNotu1: 'To make changes, use this version\'s',
    duzenlenemezKopyala: '“Copy to edit”',
    duzenlenemezNotu2:
      'button on the Versions screen: the schedule moves into the new draft as it is. “Open empty draft” instead creates a version with no assignments; you can fill it by hand here or leave it to the solver (FR-7.3).',
    suzgec: 'Filter',
    tumYetkinlikler: 'All competencies',
    tumNoktalar: 'All duty points',
    yalnizAcikGunler: 'Only days with gaps',
    kapsama: 'Coverage',
    acik: 'Gaps',
    toplamCeza: 'Total penalty',
    yukleniyor: 'Loading…',
    atamaYok: 'No assignments in this version yet.',
    personelYok: 'No active staff in this period; add staff on the Definitions screen.',
    acikGunYok: 'No day has a gap in this period. Remove the filter to see all days.',
    suzgecteYok: 'No staff assigned to this version match the selected filters.',
    gunSecimi: 'Day selection',
    saatBandi: 'hours worked',
    kilitli: 'Locked',
    kapsamaAcigi: 'Coverage gap',
    sonuc: 'result',
    degerlendiriliyor: 'Evaluating…',
    baslangic: 'Start',
    bitis: 'End',
    gorevNoktasi: 'Duty point',
    dokumGizle: 'Hide the penalty breakdown',
    dokumGoster: 'Show the penalty breakdown',
    agirlik: 'Weight',
    agirlikli: 'Weighted',
    personelGosterimi: (toplam: string, gosterilen: string) =>
      `Showing ${gosterilen} of ${toplam} staff`,
  },

  analiz: {
    tanimlarYuklenemedi: 'Could not load the definitions.',
    surumlerYuklenemedi: 'Could not load the versions.',
    analizYuklenemedi: 'Could not load the analysis.',
    disaAktarmaBasarisiz: 'The export failed.',
    excelIndirilemedi: 'Could not download the Excel file.',
    indiriliyor: 'Downloading…',
    excel: 'Excel',
    secim: 'selection',
    donem: 'Period',
    surum: 'Version',
    surumSecenegi: (no: number, durum: string) => `Version ${no} (${durum})`,
    yukleniyor: 'Loading…',
    donemKapsamasi: 'period coverage',
    taleptenFazla: 'above demand',
    enDengesiz: 'most unbalanced',
    toplamCezaBasligi: 'total penalty',
    personel: 'Staff',
    adilPayKisa: 'Fair share',
    sapma: 'Deviation',
    saatKisa: 'h',
    karsilanmayan: 'unmet',
    kisiSaat: 'person-hours',
    acikAralik: (sayi: number) => (sayi === 1 ? '1 open range' : `${sayi} open ranges`),
    tercihKarsilama: 'preference fulfilment',
    olcumUfku: 'measurement horizon',
    planlamaDonemi: 'Planning period',
    adaletUfku: 'Fairness horizon · 90 days',
    ufukDonem: 'Load and share cover this period only (acceptance criterion, Charter 5).',
    ufukAdalet:
      'Load and share cover the last ninety days, including previously published versions (SRS TD-6).',
    geceDagilimi: 'night hours distribution · per person',
    geceBos: 'No night assignments in this version.',
    geceHavuz: 'The measure covers staff who can reach night demand (SRS S2, P_night).',
    haftaSonuDagilimi: 'weekend hours distribution · per person',
    haftaSonuBos: 'No weekend assignments in this version.',
    haftaSonuHavuz: 'The measure covers staff who can reach weekend demand (SRS S3, P_we).',
    saatDengesi: 'total hour balance · per person',
    herkesTutturdu: 'Everyone met their own fair share.',
    saatSutunlari: ['STAFF', 'TOTAL HOURS', 'FAIR SHARE', 'DEVIATION'],
    ortakKayma: (yon: string, ortanca: string) =>
      `Everyone's total is ${yon} their share in this period: demand does not match the sum of the targets. What matters is the difference between people; colour is based on distance from the median (${ortanca}).`,
    altinda: 'below',
    ustunde: 'above',
    ortancaAciklamasi: 'Colour marks people more than fifteen hours away from the median.',
    enUzaktakiler: (sayi: number) => ` Showing the ${sayi} furthest.`,
    cezaDokumu: 'penalty breakdown',
    binaDegisimi: 'building changes',
    adilPayaGore: 'Position against the fair share',
    yuk: 'Load',
    bandIcinde: 'Within the floor/ceiling band of the fair share, no penalty',
    cezalandirilanSapma: (saat: string) => `Deviation penalised by the solver: ${saat} hours`,
    payinAltinda: '← below their share',
    payinUstunde: 'above their share →',
    dahaGoster: (sayi: number) => (sayi === 1 ? 'Show 1 more person' : `Show ${sayi} more people`),
    yalnizEnUzaktaki: (sayi: number) => `Only the ${sayi} furthest`,
    referansAciklamasi: 'fair share per person (reference)',
    kotaBasligi: 'annual overtime quota',
    kotaSutunlari: ['STAFF', 'CARRIED OVER', 'THIS PERIOD', 'QUOTA LEFT'],
    kotaNotu:
      '"This period" is the hours above the weekly threshold: a zero means the person did not exceed the threshold in this period, not that their quota is empty.',
    kotaRiskli: (sayi: number, esik: number) =>
      sayi === 1
        ? `1 person has less than ${esik} hours of quota left.`
        : `${sayi} people have less than ${esik} hours of quota left.`,
    kotaGuvenli: (sayi: number) =>
      `Nobody is near the limit; showing the ${sayi} with the least left.`,
    dokumSutunlari: ['GOAL', 'RAW VALUE', 'WEIGHT', 'WEIGHTED PENALTY'],
    dokumNotu:
      'The raw value is measured in the rule\'s own unit (person-hours, hours, days); the weighted penalty is the figure that enters the objective function.',
    dokumCozucu: ' The breakdown comes from the solve job.',
    dokumKurallardan:
      ' The solver did not run for this version, or the schedule was edited by hand afterwards; the breakdown was computed from the rule engine.',
    geceAdaleti: 'night load fairness · against the previous published period',
    olcumeGirenYok: 'No staff enter the measurement.',
    oncekiDonemYok:
      'There is no previous published period to compare against. This period\'s average night deviation is',
    onceki: 'previously',
    simdi: 'now',
    degismedi: 'unchanged',
    azaliyor: '↓ falling',
    artiyor: '↑ rising',
    geceOlcuAciklamasi:
      'The measure is the average deviation of night hours per person from the fair share: 0 h means everyone\'s night load equals their share. Each period is measured on its own; the figure shrinking from period to period means night load is being equalised over time. What cumulative fairness promises is not that the deviation is small but that it shrinks OVER TIME.',
  },

  surumler: {
    donemlerYuklenemedi: 'Could not load the periods.',
    surumlerYuklenemedi: 'Could not load the versions.',
    yayinlanamadi: 'Could not publish the version.',
    turetilemedi: 'Could not create the draft.',
    kopyalanamadi: 'Could not copy the version.',
    silinemedi: 'Could not delete the version.',
    karsilastirilamadi: 'Could not compare the versions.',
    karsilastir: 'Compare',
    donemEtiketi: 'Period:',
    surumSayisi: (sayi: number) => (sayi === 1 ? '1 version' : `${sayi} versions`),
    karsilastirBasligi: 'compare versions',
    oncekiSurum: 'Previous version',
    yeniSurum: 'New version',
    surumSecenegi: (no: number, durum: string) => `Version ${no} (${durum})`,
    karsilastiriliyor: 'Comparing…',
    farklariGetir: 'Show differences',
    surumYok: 'No versions in this period yet.',
    surumNo: (no: number) => `Version ${no}`,
    acik: 'Gaps',
    kopyalaIpucu:
      'Opens a draft carrying this version\'s schedule as it is; the source version does not change',
    kopyala: 'Copy to edit',
    bosTaslakIpucu:
      'Opens a draft with no assignments; you can fill it by hand on the Schedule screen or leave it to the solver',
    bosTaslakAc: 'Open empty draft',
    atamaYokYayinlanamaz: 'No assignments, cannot publish',
    bosYayinUyarisi:
      'This version has no assignments; if published, the schedule will look empty in the employee panel. Fill it on the Schedule screen first, or run the solver.',
    yayinla: 'Publish',
    silIpucu:
      'Deletes this version and its assignments, so abandoned drafts do not pile up',
    sil: 'Delete',
    silmeOnayi: (no: number, atamalar: string) =>
      `Version ${no} and ${atamalar} will be deleted.`,
    atamaSayisi: (sayi: number) => (sayi === 1 ? 'its 1 assignment' : `its ${sayi} assignments`),
    atamalari: 'its assignments',
    silmeNotu:
      'This cannot be undone. Published and archived versions cannot be deleted; this version is neither.',
    vazgec: 'Cancel',
    kopyaOnayi: (no: number, atamalar: string) =>
      `Version ${no} will be copied into a new draft version, ${atamalar}.`,
    kopyaAtamaSayisi: (sayi: number) =>
      sayi === 1 ? 'along with its 1 assignment' : `along with its ${sayi} assignments`,
    kopyaAtamalari: 'along with its assignments',
    kopyaNotu: (no: number) =>
      `Version ${no} stays as it is: its status does not change and its assignments are untouched. Editing happens on the new draft.`,
    kopyalaniyor: 'Copying…',
    onaylaKopyala: 'Confirm and copy',
    yayinOnayiArsiv: (yeni: number, eski: number) =>
      `Version ${yeni} will be published and Version ${eski} archived.`,
    yayinOnayi: (no: number) => `Version ${no} will be published.`,
    yayinNotu: 'A published version becomes read only and cannot be edited by hand.',
    yayinlaniyor: 'Publishing…',
    onaylaYayinla: 'Confirm and publish',
    farkBasligi: (onceki: number, yeni: number, degisen: number) =>
      `Version ${onceki} → Version ${yeni} · ${degisen} changed assignments`,
    fark: { eklendi: 'Added', kaldirildi: 'Removed', degisti: 'Changed' },
    farkYok: 'No assignments differ between the two versions.',
    farkSutunlari: ['STAFF', 'DAY', 'KIND', 'PREVIOUS', 'NEW'],
  },

  sonuc: {
    hedefler: {
      S1: { konu: 'coverage gap', birim: 'people' },
      S1f: { konu: 'staffing above demand', birim: 'people' },
      S2: { konu: 'night fairness', birim: 'hours' },
      S3: { konu: 'weekend fairness', birim: 'hours' },
      S4: { konu: 'total hour balance', birim: 'hours' },
      S5: { konu: 'preference fulfilment', birim: 'preferences' },
      S6: { konu: 'work pattern', birim: 'days' },
      S6b: { konu: 'building consistency', birim: 'days' },
      S7: { konu: 'isolated working day', birim: 'days' },
      S8: { konu: 'deviation from the previous version', birim: 'assignments' },
    } as Record<string, { konu: string; birim: string }>,
    acikArtti: (miktar: string) => `the coverage gap grew by ${miktar}`,
    acikAzaldi: (miktar: string) => `the coverage gap shrank by ${miktar}`,
    fazlaAtandi: (miktar: string) => `${miktar} were assigned above demand`,
    fazlaAzaldi: (miktar: string) => `staffing above demand fell by ${miktar}`,
    bozuldu: (konu: string, miktar: string) => `${konu} worsened by ${miktar}`,
    iyilesti: (konu: string, miktar: string) => `${konu} improved by ${miktar}`,
    tekIhlal: 'This change breaks a hard rule and was not applied.',
    cokIhlal: (sayi: number, kurallar: string) =>
      `This change breaks ${sayi} hard rules and was not applied (${kurallar}).`,
    etkiYok: 'The change affected none of the goals.',
    kalanHedef: (sayi: number) =>
      sayi === 1 ? ' and 1 more goal was affected.' : ` and ${sayi} more goals were affected.`,
  },

  cozum: {
    durum: {
      kuyrukta: 'Queued',
      on_kontrol: 'Pre-check',
      cozuluyor: 'Solving',
      durduruldu: 'Awaiting decision',
      tamamlandi: 'Completed',
      uyarili: 'Completed with warnings',
      basarisiz: 'Failed',
      iptal: 'Cancelled',
    },
    donemlerYuklenemedi: 'Could not load the periods.',
    onKontrolBasarisiz: 'The pre-check failed.',
    baslatilamadi: 'Could not start the solve.',
    durdurmaBasarisiz: 'The stop request failed.',
    kararUygulanamadi: 'Could not apply the decision.',
    donemOlusturulamadi: 'Could not create the period.',
    atOnayi: 'The solution found will be deleted. This cannot be undone.',
    ayarlar: 'solve settings',
    donem: 'Period',
    yeniDonem: 'New period',
    onKontrol: 'Pre-check',
    baslat: 'Start solving',
    yenidenCozIpucu: 'Re-solves from the selected version; locked assignments are kept as they are',
    sifirdanIpucu: 'Solves the period from scratch',
    yenidenCozumBasligi: 'Re-solve.',
    yenidenCozumGovde:
      'The version you picked on the Schedule screen is taken as the base: locked assignments are kept and the solver rewrites the rest. Choosing another period removes the base and the solve starts from scratch.',
    tabanNotu:
      'is taken as the base: locked assignments are kept and the solver rewrites the rest. Choosing another period removes the base and the solve starts from scratch.',
    yeniPlanlamaDonemi: 'new planning period',
    baslangic: 'Start',
    bitis: 'End',
    donemiOlustur: 'Create period',
    iptal: 'Cancel',
    gunSayisi: 'The selected range is',
    gunSayisiSonek: (azami: number) => `days · ${azami} days at most`,
    engelYok: 'No structural obstacle was found.',
    engel: 'Obstacle',
    uyari: 'Warning',
    gecenSure: 'Elapsed',
    enIyiCeza: 'Best penalty',
    toplamCeza: 'Total penalty',
    kapsamaAcigi: 'Coverage gaps',
    durdurAramaVar:
      'Stop ends the search; the solution found so far is not discarded but kept for your decision.',
    durdurAramaYok:
      'The search has not started yet. Stop cancels the job outright; with no result to keep, no decision is asked.',
    aramaSonlandi:
      'The search was ended. The solution found has not been written to the schedule; the version is as it was before the stop.',
    uygunSonucYok:
      'The solver was stopped before it reached a first feasible schedule; there is no usable result.',
    sonucKullanilamaz: 'For that reason "Use the result" cannot be selected.',
    sonucuKullan: 'Use the result',
    sonucuAt: 'Discard the result',
    bundanDevam: 'Continue from this solution',
    yeniZamanLimiti: 'New time limit (seconds)',
    devamNotu:
      '"Continue" starts a new search seeded with the solution found; the clock restarts from zero and the result will not be worse than this solution.',
    sonucOzeti: (durum: string) => `result summary · ${durum}`,
    isIptal: 'The job was cancelled. The schedule version did not change.',
    kapsamaBulundu: (sayi: number) =>
      sayi === 1
        ? '1 coverage gap was found; the affected cells are marked on the Schedule screen.'
        : `${sayi} coverage gaps were found; the affected cells are marked on the Schedule screen.`,
    cizelgeyiGoruntule: 'View the schedule',
  },

  ozet: {
    veriYuklenemedi: 'Could not load the summary.',
    surumYuklenemedi: 'Could not load the version data.',
    bosTaslak:
      'The latest version of this period is still an empty draft. You can draw it by hand on the Schedule screen or use the Solve screen.',
    donemIcin: (aralik: string) => `for the ${aralik} period`,
    kapsama: 'coverage',
    eksikHucre: 'missing cells',
    toplamCeza: 'total penalty',
    bekleyenTercih: 'pending preferences',
    surumDurumuBasligi: 'version status',
    kisi: (sayi: number) => (sayi === 1 ? '1 person' : `${sayi} people`),
    kayit: 'records',
    cezaKaynagi: {
      cozucu: 'from the solve job · includes S8',
      kurallardan: 'computed from the rules · excludes S8',
      yok: '',
    },
    cezaKaynagiCozucu:
      'The breakdown comes from the solve job; the figure is the whole objective function, including deviation from the previous version (S8).',
    cezaKaynagiKurallardan:
      'The solver did not run for this version, or the schedule was edited by hand afterwards; the breakdown was computed from the rule engine. Deviation from the previous version (S8) is NOT part of this figure: when the source changes so does the scope, and totals from the two sources cannot be compared directly.',
    gunlukKapsama: 'daily coverage',
    gunlukKapsamaAralik: (aralik: string) => `daily coverage · ${aralik}`,
    kapsamaVerisiYok: 'No daily coverage data for this version.',
    gunAcikKayitlari: (gun: string) => `open records on ${gun}`,
    donemAcikKayitlari: 'Open records for the period',
    acikKayitYok: 'No open records.',
    kisiBasinaSaat: 'hours per person',
    kisiBasinaSaatAralik: (aralik: string) => `hours per person · ${aralik}`,
    saatSapmasiYok: 'No hour deviation in this version.',
    tumunuAnalizde: 'See them all on the Analysis screen',
    musaitOlmayanlar: 'unavailable this period',
    musaitOlmayanlarAralik: (aralik: string) => `unavailable this period · ${aralik}`,
    musaitOlmayanYok: 'Nobody is unavailable this period.',
    yaklasanKayitlar: 'upcoming availability records · from today',
    yaklasanYok: 'No upcoming records.',
  },

  musaitlik: {
    dilim: { tam_gun: 'FULL', ogleden_once: 'AM', ogleden_sonra: 'PM' },
    tip: { yillik_izin: 'Leave', rapor: 'Sick', egitim: 'Training', mazeret: 'Excused' },
    yuklenemedi: 'Could not load the availability records.',
    olusturulamadi: 'Could not create the record.',
    silinemedi: 'Could not delete the record.',
    kadroRiski: (a: string, b: string) =>
      `${a} and ${b} are away in the same period; staffing may be at risk.`,
    kayitEkle: 'Add record',
    yeniKayit: 'new availability record',
    dilimEtiketi: 'Part of day',
    tipEtiketi: 'Type',
    personelEtiketi: 'Staff member',
    baslangic: 'Start',
    bitis: 'End',
    iptal: 'Cancel',
    sil: 'Delete',
    kayitYok: 'No availability records yet.',
    sutunlar: ['STAFF', 'START', 'END', 'PART', 'TYPE', 'DOCUMENT', ''],
    belgeAlinamadi: 'Could not fetch the document.',
    belgeTipi: 'Only PNG, JPEG or PDF can be uploaded.',
    belgeBuyuk: 'The file is too large (5 MB at most).',
    belgeYuklenemedi: 'Could not upload the document.',
    indir: 'Download',
    yukleniyor: 'Uploading…',
    ekle: 'Add',
  },

  kullanicilar: {
    roller: [
      { deger: 'calisan', etiket: 'Employee', aciklama: 'Only their own schedule, summary and preferences' },
      { deger: 'idare', etiket: 'Administrator', aciklama: 'Every function of the shift administrator' },
      { deger: 'hesap_yoneticisi', etiket: 'Account manager', aciklama: 'The administrator rights plus account management' },
    ],
    yuklenemedi: 'Could not load the accounts.',
    hesapYok: 'No accounts yet.',
    parolaBekliyor: 'Password pending',
    rolEtiketi: 'Role',
    degistir: 'Edit',
    parolaSifirla: 'Reset password',
    onceSec: 'Select an account from the list first',
    pasifleriGoster: 'Show inactive',
    hesabiDegistir: 'edit account',
    yeniHesap: 'new account',
    kullaniciAdi: 'Username',
    kullaniciAdiKurali: 'Lower case, digits, dot, hyphen; 3–50 characters.',
    baslangicParolasi: 'Initial password',
    parolaKurali: 'At least 12 characters. The user must change it at first sign-in.',
    kendiRolun: 'You cannot change your own role.',
    personelKaydi: 'Staff record',
    bagliDegil: 'not linked',
    calisanBaglanmali: 'An employee account must be linked to a staff record.',
    bosBirakilabilir: 'It may be left empty for administrator and management roles.',
    kendiHesabin: 'You cannot deactivate your own account.',
    kapatmaNotu:
      'Deactivating does not delete the account; sign-in stops and open sessions are closed.',
    vazgec: 'Cancel',
    sifirlanamadi: 'Could not reset the password.',
    sifirlamaBasligi: 'password reset',
    sifirlamaUyarisi: (kullanici: string) =>
      `A new initial password will be assigned to ${kullanici}. The user will have to change it at first sign-in and all their open sessions will be closed.`,
    yeniBaslangicParolasi: 'New initial password',
    parolayiSifirla: 'Reset password',
  },

  parolaEkrani: {
    urunAdi: 'Shift Scheduling',
    baslik: 'Change password',
    zorunluAciklama:
      'Your password was assigned by an administrator. You must set your own password before continuing.',
    mevcut: 'Current password',
    yeni: 'New password',
    tekrar: 'New password (again)',
    asgariUzunluk: (n: number) => `The new password must be at least ${n} characters.`,
    ayniDegil: 'The two passwords do not match.',
    kaydediliyor: 'Saving…',
    kaydet: 'Change password',
    vazgec: 'Cancel',
    degistirilemedi: 'Could not change the password.',
  },

  tercihYonetimi: {
    bekleyen: 'Pending',
    onaylandi: 'Approved',
    reddedildi: 'Rejected',
    calismamaTercihi: 'Prefers not to work',
    zamanAraligiTercihi: 'Time range preference',
    araligiTercihi: (aralik: string) => `prefers ${aralik}`,
    buDurumdaYok: 'No preferences in this state.',
    retGerekcesi: 'Reason for rejection (optional)',
    reddet: 'Reject',
    onayla: 'Approve',
    yuklenemedi: 'Could not load the preferences.',
    guncellenemedi: 'Could not update the preference.',
  },

  kunye: {
    altBaslik: 'Shift scheduling decision support tool',
    tanitim1:
      'VARDİS builds shift schedules with constraint programming instead of by hand. Assigning staff to hourly demand, it never violates the hard rules such as rest periods, weekly hour caps and competencies, and it tries to distribute the soft goals such as night hours, weekend hours and total load fairly.',
    tanitim2:
      'What the tool produces is a proposal, not an instruction: every schedule it builds can be explained. Which rule was penalised and by how much, who deviated from their share and by how much, and where demand could not be met are all visible on screen. The decision belongs to the administrator; the tool only makes its cost visible.',
    projeBasligi: 'the project',
    gelistirmeBasligi: 'development',
    sunucu: 'Server',
    mimari: 'Architecture',
    gelistiren: 'Developed by',
    rol: 'Systems analyst and developer, project lead',
    rolEtiketi: 'Role',
    kapsam: 'Scope',
    kapsamMetni:
      'Built as a summer internship project; it contains no data from any organisation.',
    demoNotu:
      'The staff, duty point and demand records in this application are generated demonstration data; they do not reflect a real roster or working arrangement.',
    teknikBaslik: 'technical details',
    cozucu: 'Solver',
    arayuz: 'Interface',
    veritabani: 'Database',
    surecNotu:
      'The solver runs in a separate process; the application server creates a job record and the worker picks it up from the queue. The only contract between the two processes is the database.',
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
