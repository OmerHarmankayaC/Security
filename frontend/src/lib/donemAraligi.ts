import { gunFarki } from './tarih'
import type { Metinler } from '@/i18n/sozluk'

/**
 * Planlama dönemi uzunluk sınırı (madde 4).
 *
 * Backend'deki `AZAMI_DONEM_GUN` ile aynı değerdir (app/schemas/surum.py).
 * İki yerde durmasının nedeni iki farklı iş yapmaları: arayüz kullanıcıyı
 * istek gönderilmeden durdurup nedenini yazar, backend ise sözleşmeyi
 * uygular ve istemciden bağımsız olarak geçerlidir. İstemci tarafı denetim
 * tek başına bir güvence değildir; `test_donem_araligi.py` ikisinin aynı
 * sayıyı kullandığını backend tarafında sabitler.
 *
 * Sınır dört kanonik dokümanda tanımlı DEĞİLDİR. Kabul kriteri 28 günlük
 * referans örnekle ölçülür (NFR-1); 31 gün onu kapsar ve takvimsel olarak
 * "en uzun bir ay" karşılığıdır.
 */
export const AZAMI_DONEM_GUN = 31

/** Varsayılan dönem uzunluğu — Backlog karar günlüğü, 07.08.2026. */
export const VARSAYILAN_DONEM_GUN = 7

/** Seçilen aralığın gün sayısı (iki uç dahil). */
export function gunSayisi(baslangicIso: string, bitisIso: string): number {
  return gunFarki(baslangicIso, bitisIso) + 1
}

/**
 * Seçilen aralığın neden çözülemeyeceğini söyler; sorun yoksa null.
 *
 * Metin doğrudan kullanıcıya gösterilir: neden ve seçilen değer birlikte
 * yazılır, teknik terim geçmez (NFR-5).
 */
export function araligiDenetle(
  baslangicIso: string,
  bitisIso: string,
  m: Metinler,
): string | null {
  if (!baslangicIso || !bitisIso) return m.kuralUyarilari.tarihSecin
  const gun = gunSayisi(baslangicIso, bitisIso)
  if (gun < 1) return m.kuralUyarilari.bitisOnce
  if (gun > AZAMI_DONEM_GUN) {
    return m.kuralUyarilari.donemUzun(AZAMI_DONEM_GUN, gun)
  }
  return null
}
