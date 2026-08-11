// Turkce buyuk harfe cevirirken DAIMA bunu kullan, duz .toUpperCase() DEGIL —
// toUpperCase() "i" -> "I" cevirir (Turkce'de dogrusu "İ"), İ/ı harflerini
// bozar (bkz. docs/tasarim/TASARIM_REFERANSI.md).
export function buyukHarf(metin: string): string {
  return metin.toLocaleUpperCase('tr-TR')
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
