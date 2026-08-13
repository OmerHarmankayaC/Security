/**
 * Talep aralıklarının saat kodlaması — TEK YER (SDD 4.2.2).
 *
 * Sunucu tarafında aralıklar TIME sütunlarında durur ve gün sonu `00:00`
 * ile yazılır: `bitis <= baslangic` ise aralık gün sonuna kadar sürer ya da
 * gece yarısını aşar. Depoda 24.00 diye bir değer YOKTUR — ne PostgreSQL
 * sürücüsü ne de Python'un `time` tipi onu geri okuyabiliyor (bkz.
 * PROGRESS_V2, "Tasarımdan sapmalar").
 *
 * Kullanıcı ise 24.00'ı görmek ister: "08.00–00.00" bir aralığın gün sonunda
 * bittiğini değil, sıfır uzunlukta olduğunu düşündürür. Çeviri bu dosyada
 * yapılır; ekran yalnızca 0–24 arası tam sayılarla çalışır.
 *
 * Aralıklar SAAT BAŞINDA başlar ve biter. Kapsama kısıtı saat ekseninde
 * yazıldığı için (SRS 4.3 S1) yarım saatlik bir sınır hiçbir saate denk
 * düşmez ve talep sessizce kaybolurdu; sunucu da bunu reddeder.
 */

import { saatEtiketi } from './blok'

/** "08:00:00" → 8. Bitiş alanında `00:00:00` gün sonudur, yani 24. */
export function saatiCoz(iso: string, bitisMi = false): number {
  const saat = Number(iso.slice(0, 2))
  return bitisMi && saat === 0 ? 24 : saat
}

/** 8 → "08:00:00", 24 → "00:00:00" (gün sonu). */
export function saatiYaz(saat: number): string {
  return `${String(saat % 24).padStart(2, '0')}:00:00`
}

/**
 * Saat metninin biçimi TEK YERDE, `blok.ts`te durur; burası yalnızca yeniden
 * dışa verir.
 *
 * Aynı biçimleyicinin üç kopyası (blok, talep aralığı, vardiya rengi) bir kez
 * hataya yol açtı: gün sonu bir kopyada 24, ötekinde 00 yazılıyordu ve aynı
 * çizelge iki ekranda farklı okunuyordu. Çağıranların içe aktarma yolu
 * değişmesin diye yeniden dışa verilir; tanım çoğalmaz.
 */
export { saatEtiketi }

/** Bir aralığın ekrandaki hâli: "08.00–24.00". */
export function araligiYaz(baslangic: string, bitis: string): string {
  return `${saatEtiketi(saatiCoz(baslangic))}–${saatEtiketi(saatiCoz(bitis, true))}`
}

/**
 * Aralığın saat cinsinden uzunluğu. Sunucudaki `aralik_sure_saat` ile AYNI
 * kural: fark sıfırsa aralık gün boyudur (24 saat), sıfır değil.
 */
export function araligiSure(baslangicSaati: number, bitisSaati: number): number {
  const fark = (bitisSaati - baslangicSaati + 24) % 24
  return fark === 0 ? 24 : fark
}

/** Başlangıç seçenekleri: 00.00–23.00. */
export const BASLANGIC_SAATLERI: number[] = Array.from({ length: 24 }, (_, i) => i)

/**
 * Bitiş seçenekleri: 01.00–24.00. 00.00 listede YOKTUR; 24.00 ile aynı
 * değeri kodlar ve iki ayrı seçenek olarak görünmesi kullanıcıyı yanıltır.
 */
export const BITIS_SAATLERI: number[] = Array.from({ length: 24 }, (_, i) => i + 1)
