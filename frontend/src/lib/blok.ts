/**
 * Çalışma bloğunun okunması — TEK YER (SRS TD-13, SDD 4.2.1).
 *
 * Atama artık bir vardiya tipi taşımıyor; iki zaman damgası taşıyor
 * (`baslangic_zamani`, `bitis_zamani`). Ekranların hepsi aynı üç soruyu
 * soruyor — "kaçta başladı", "kaçta bitti", "ne kadar gece" — ve üçünün de
 * yanıtı burada. Kopyalandığında ayrışacak yer gün sınırıdır: gece yarısını
 * aşan blokta bitiş ertesi güne düşer ve `24` yazılması gerekir.
 *
 * Zaman damgaları sunucudan saat dilimi ofsetiyle gelir. Saat, dizeden
 * DOĞRUDAN okunur; `new Date(...)` kullanılsaydı tarayıcının yerel saat
 * dilimi devreye girer ve aynı çizelge iki makinede farklı saatlerde
 * görünürdü.
 */

/** "2026-02-02T08:00:00+03:00" → 8. */
export function baslangicSaati(zaman: string): number {
  return Number(zaman.slice(11, 13))
}

/** Bitiş saati; gün sonu `24` yazılır (00.00 bir aralığı sıfır uzunlukta gösterir). */
export function bitisSaati(zaman: string): number {
  const saat = Number(zaman.slice(11, 13))
  return saat === 0 ? 24 : saat
}

/** 8 → "08.00". Ondalık ayraç NOKTA (Tasarım Referansı). */
export function saatEtiketi(saat: number): string {
  return `${String(saat).padStart(2, '0')}.00`
}

/** Bloğun ekrandaki hâli: "08.00–16.00". */
export function blokEtiketi(baslangic: string, bitis: string): string {
  return `${saatEtiketi(baslangicSaati(baslangic))}–${saatEtiketi(bitisSaati(bitis))}`
}

/** Izgara hücresinin kısa hâli: "08–16". */
export function blokKisaEtiketi(baslangic: string, bitis: string): string {
  const bas = String(baslangicSaati(baslangic)).padStart(2, '0')
  const bit = String(bitisSaati(bitis)).padStart(2, '0')
  return `${bas}–${bit}`
}

// Gece dönemi (SRS TD-2): 20:00–06:00. Yarı açık aralık — 06 gece değildir.
const GECE_BASLANGIC = 20
const GECE_BITIS = 6

/**
 * Bloğun gece dönemiyle kesişiminin uzunluğu (SRS TD-2).
 *
 * GECE HESAPLANIR, İŞARETLENMEZ. Önceki sürümlerde vardiya tipi üzerinde bir
 * `gece_mi` bayrağı vardı; blok kataloğu kalktığı için işaretlenecek bir
 * nesne de kalmadı. Sunucudaki `gece_saat_sayisi` ile aynı hesap.
 */
export function geceSaati(baslangic: string, sureSaat: number): number {
  let sayac = 0
  for (let kayma = 0; kayma < sureSaat; kayma += 1) {
    const saat = (baslangicSaati(baslangic) + kayma) % 24
    if (saat >= GECE_BASLANGIC || saat < GECE_BITIS) sayac += 1
  }
  return sayac
}
