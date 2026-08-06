// Turkce buyuk harfe cevirirken DAIMA bunu kullan, duz .toUpperCase() DEGIL —
// toUpperCase() "i" -> "I" cevirir (Turkce'de dogrusu "İ"), İ/ı harflerini
// bozar (bkz. docs/tasarim/TASARIM_REFERANSI.md).
export function buyukHarf(metin: string): string {
  return metin.toLocaleUpperCase('tr-TR')
}
