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
export function kisalt(ad: string): string {
  const kelimeler = ad.trim().split(/\s+/).filter(Boolean)
  if (kelimeler.length === 0) return ''
  const ham =
    kelimeler.length > 1
      ? kelimeler.slice(0, 3).map((k) => k.slice(0, 1)).join('')
      : kelimeler[0]!.slice(0, 3)
  return buyukHarf(ham)
}
