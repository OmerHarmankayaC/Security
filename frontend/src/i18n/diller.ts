// Arayüz dilinin tanımı, algılanması ve saklanması.
//
// İKİ DİL VAR VE İKİSİ DE ARAYÜZDÜR. Veri her zaman kullanıcının girdiği
// dilde kalır: görev noktası adı, personel adı, izin açıklaması çevrilmez.
// Çevrilen yalnızca uygulamanın kendi yazdığı metinlerdir.

export type Dil = 'tr' | 'en'

export const DILLER: readonly Dil[] = ['tr', 'en']

/** Seçicide görünen ad; her dil KENDİ adıyla yazılır, çevrilmez. */
export const DIL_ADLARI: Record<Dil, string> = {
  tr: 'Türkçe',
  en: 'English',
}

/**
 * `Intl` ve `toLocaleUpperCase` için yerel etiketi.
 *
 * Türkçe yereli yalnızca dil seçimi değil bir DOĞRULUK meselesidir: "i"
 * harfinin büyüğü Türkçe'de "İ"dir ve `en-US` yereli onu "I" yapar.
 */
export const YEREL: Record<Dil, string> = {
  tr: 'tr-TR',
  en: 'en-US',
}

const ANAHTAR = 'vardis.dil'

function gecerliMi(deger: unknown): deger is Dil {
  return deger === 'tr' || deger === 'en'
}

/**
 * Başlangıç dili: önce kullanıcının daha önceki seçimi, sonra tarayıcının
 * dili, sonra İngilizce.
 *
 * Türkçe'ye düşmüyoruz. Depo halka açık ve gösterim örneğine gelen kişilerin
 * çoğu Türkçe bilmiyor; tarayıcısı Türkçe olan zaten ilk daldan geçer.
 *
 * `localStorage` gizli sekmede ya da site verisi kapalıyken ERİŞİMİN
 * KENDİSİNDE hata verebilir, yalnızca boş dönmez — bu yüzden okuma da yazma
 * da sarmalanır. Dil tercihi uğruna uygulamanın açılmaması saçma olurdu.
 */
export function baslangicDili(): Dil {
  try {
    const kayitli = localStorage.getItem(ANAHTAR)
    if (gecerliMi(kayitli)) return kayitli
  } catch {
    // sessizce tarayıcı diline düş
  }
  const tarayici = typeof navigator === 'undefined' ? '' : navigator.language
  return tarayici.toLowerCase().startsWith('tr') ? 'tr' : 'en'
}

export function diliSakla(dil: Dil): void {
  try {
    localStorage.setItem(ANAHTAR, dil)
  } catch {
    // Saklanamıyorsa seçim yalnızca bu oturumda geçerli olur; kullanıcıya
    // hata göstermek, düzeltemeyeceği bir şeyi bildirmek olurdu.
  }
}
