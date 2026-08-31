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

  sayim: {
    gosteriliyor: (gosterilen: number, toplam: number) =>
      `Showing ${gosterilen} of ${toplam} records`,
  },
}

export const SOZLUK = { tr, en } as const
