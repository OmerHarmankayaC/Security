import { YEREL, type Dil } from '@/i18n/diller'

// Buyuk harfe cevirirken DAIMA bunu kullan, duz .toUpperCase() DEGIL:
// toUpperCase() "i" -> "I" cevirir (Turkce'de dogrusu "İ") ve İ/ı harflerini
// bozar (bkz. docs/tasarim/TASARIM_REFERANSI.md).
//
// VARSAYILAN TURKCE'DIR VE OYLE KALMALI. Bu fonksiyonun cagrilarinin cogu
// arayuz etiketini degil VERIYI buyutuyor: gorev noktasi adi, personel adi,
// izgara kisaltmasi. O veri kullanicinin girdigi dilde, yani Turkce'dir ve
// arayuz Ingilizce'ye alindi diye "İzin" -> "IZIN" olmamalidir.
//
// Arayuzun KENDI etiketlerini buyuten yerler etkin dili acikca gecirir
// (`buyukHarf(m.giris.baslik, dil)`); orada da tersi gecerlidir, Ingilizce
// bir etiketi Turkce yereliyle buyutmek "title" -> "TİTLE" verirdi.
export function buyukHarf(metin: string, dil: Dil = 'tr'): string {
  return metin.toLocaleUpperCase(YEREL[dil])
}

// Kucultmenin de yereli var ve ayni tuzagi tasir: `toLowerCase()` Turkce
// "I" harfini noktali "i" yapar (dogrusu noktasiz "ı"), Ingilizce metinde
// ise tersi olur. Varsayilan yine Turkce, ayni gerekceyle.
export function kucukHarf(metin: string, dil: Dil = 'tr'): string {
  return metin.toLocaleLowerCase(YEREL[dil])
}

/**
 * Tanım adının ızgara kısaltması (SDD 6.3.3: "vardiya tipini ve görev
 * noktasını KISALTMAYLA gösterir").
 *
 * Adlar kullanıcı tarafından değiştirilebildiği için kısaltma tablosu
 * tutulmaz, addan türetilir:
 *   çok kelimeli → kelime baş harfleri   "Vardiya Şefliği" → "VŞ"
 *   tek kelimeli → ilk üç harf           "Güvenlik" → "GÜV", "Gece" → "GEC"
 *
 * Büyütme her zaman Türkçe yereliyle yapılır; "İzin" düz toUpperCase ile
 * "IZIN" olurdu.
 */
/**
 * Sayıya gelen belirtme hâli eki: `36 personelin 10'U gösteriliyor`.
 *
 * Türkçede ek, sayının OKUNUŞUNUN son ünlüsüne göre değişir — "10'u" ama
 * "12'si", "3'ü", "6'sı". Rakamdan doğrudan türetilemez, bu yüzden okunuşun
 * son parçası tablodan bulunur. Ünlüyle biten okunuşlar (iki, altı, yedi,
 * yirmi, kırk…) araya kaynaştırma `s`si alır.
 *
 * Sayı bir metnin içinde eğilmeden yazılırsa cümle kulağa yanlış gelir ve
 * bunu düzeltmenin tek doğru yolu okunuşa bakmaktır.
 */
export function belirtmeHaliEki(sayi: number): string {
  // sıfırı · biri · ikisi · üçü · dördü · beşi · altısı · yedisi · sekizi · dokuzu
  const BIRLER = ["'ı", "'i", "'si", "'ü", "'ü", "'i", "'sı", "'si", "'i", "'u"]
  // onu · yirmisi · otuzu · kırkı · ellisi · altmışı · yetmişi · sekseni · doksanı
  const ONLAR = ["", "'u", "'si", "'u", "'ı", "'si", "'ı", "'i", "'i", "'ı"]
  const mutlak = Math.abs(Math.trunc(sayi))
  if (mutlak >= 100) {
    // Yüz ve üzeri: son iki basamak sıfırsa "yüz/bin" okunuşuna düşer.
    const kalan = mutlak % 100
    if (kalan !== 0) return belirtmeHaliEki(kalan)
    return mutlak % 1000 === 0 ? "'i" : "'ü"
  }
  const birler = mutlak % 10
  if (birler !== 0) return BIRLER[birler]!
  return ONLAR[Math.floor(mutlak / 10)]!
}

export function kisalt(ad: string): string {
  const kelimeler = ad.trim().split(/\s+/).filter(Boolean)
  if (kelimeler.length === 0) return ''
  const ham =
    kelimeler.length > 1
      ? kelimeler.slice(0, 3).map((k) => k.slice(0, 1)).join('')
      : kelimeler[0]!.slice(0, 3)
  return buyukHarf(ham)
}

/**
 * Bir ad kümesinin BENZERSİZ ızgara kısaltmaları.
 *
 * `kisalt()` tek başına çakışabilir: tek kelimeli adlarda ilk üç harf aynı
 * düşerse ("Güvenlik" ve "Güvence" ikisi de "GÜV" verir) ya da çok kelimeli
 * adlarda kelime baş harfleri aynı düşerse ("Ana Kapı" ve "Arka Kapı" ikisi
 * de "AK" verir) ızgarada iki farklı nokta aynı görünür ve çalışan hangi
 * noktaya gittiğini okuyamaz.
 *
 * Çakışanlara adın SONRAKİ ayırt edici harfi eklenir. Sonuç giriş sırasından
 * bağımsızdır: adlar önce sıralanır.
 */
export function benzersizKisaltma(adlar: string[]): Map<string, string> {
  const sirali = [...new Set(adlar)].sort((a, b) => a.localeCompare(b, 'tr'))
  const sonuc = new Map<string, string>()
  const kullanilan = new Set<string>()
  for (const ad of sirali) {
    let aday = kisalt(ad)
    const harfler = buyukHarf(ad).replace(/\s+/g, '')
    let i = aday.length
    while (kullanilan.has(aday) && i < harfler.length) {
      aday = kisalt(ad) + harfler[i]
      i += 1
    }
    // Harfler tükendiyse sayı ekle: iki ad birebir aynı olamaz (Set), ama
    // aynı harflerden oluşabilir.
    let sayac = 2
    while (kullanilan.has(aday)) {
      aday = `${kisalt(ad)}${sayac}`
      sayac += 1
    }
    kullanilan.add(aday)
    sonuc.set(ad, aday)
  }
  return sonuc
}
