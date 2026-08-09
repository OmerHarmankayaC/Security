import type { Kural } from '@/api/types'

/**
 * S1'in baskın ağırlığının ölçüsü (madde 2d).
 *
 * SRS S1: "Ağırlık w1, diğer tüm ağırlıkların toplamından belirgin biçimde
 * büyük seçilir; böylece çözücü hiçbir zaman başka bir hedefi iyileştirmek
 * için kapsama açığı bırakmaz." Uyarı bu cümlenin sayısal karşılığıdır.
 *
 * Toplama yalnızca AKTİF esnek hedefler girer: pasif bir hedef amaç
 * fonksiyonuna hiç eklenmez (SDD 5.1 yalnız aktif kuralları yükler), yani
 * S1 ile yarışmaz. Pasifleri de saymak, kullanıcıyı gerçekte var olmayan
 * bir baskınlık kaybı için uyarırdı.
 */
export function digerEsnekAgirlikToplami(kurallar: Kural[]): number {
  return kurallar
    .filter((k) => k.tip === 'esnek' && k.kimlik !== 'S1' && k.aktif)
    .reduce((toplam, k) => toplam + (k.agirlik ?? 0), 0)
}

/** S1 ağırlığı diğer aktif esnek hedeflerin toplamını geçmiyorsa true. */
export function s1BaskinligiKayboldu(
  s1Agirligi: number | null,
  digerToplam: number,
): boolean {
  if (s1Agirligi === null) return false
  return s1Agirligi <= digerToplam
}
