// Vardiya kodlaması (TASARIM_REFERANSI.md, yalnızca vardiya bağlamındaki
// ızgara/kartlarda kullanılır).
//
// RENK BAŞLANGIÇ SAATİ BANDINDAN HESAPLANIR, blok kimliğinden değil. Sabit
// üç renk (gündüz/akşam/gece) yalnızca üç bloklu katalogda anlamlıydı;
// katalog yedi bloğa çıktığında (SRS 3.3.1) "Gündüz" adını taşıyan sekiz ve
// on iki saatlik bloklar aynı kutuya düşerdi. Bant, bloğun ne zaman
// başladığını söyler ve katalog büyüdükçe kendiliğinden çalışır.

/** Başlangıç saatinin düştüğü bant. Sınırlar SDD 6.3.3'ten. */
export function baslangicBandi(baslangicSaati: string): 'gece' | 'sabah' | 'gunduz' | 'aksam' {
  const saat = Number(baslangicSaati.slice(0, 2))
  if (saat >= 20 || saat < 5) return 'gece'
  if (saat < 8) return 'sabah'
  if (saat < 14) return 'gunduz'
  return 'aksam'
}

const _BANT_SINIFI: Record<ReturnType<typeof baslangicBandi>, string> = {
  gece: 'bg-vardiya-gece text-vardiya-gece-ink',
  // Erken başlayan uzun bloklar (06.00) gündüzden ayrılır: aynı rengi
  // taşısalardı ızgarada 06–16 ile 08–16 ayırt edilemezdi.
  sabah: 'bg-vardiya-gunduz text-ink opacity-90',
  gunduz: 'bg-vardiya-gunduz text-ink',
  aksam: 'bg-vardiya-aksam text-ink',
}

export function vardiyaHucreSinifi(_geceMi: boolean, baslangicSaati: string): string {
  return _BANT_SINIFI[baslangicBandi(baslangicSaati)]
}

/**
 * Hücrede görünen saat aralığı: `08–16`.
 *
 * Blok adının kısaltması yeterli değildir (SDD 6.3.3): karışık uzunluklu
 * katalogda "Gündüz" adını taşıyan sekiz saatlik blok ile on iki saatlik
 * blok aynı kısaltmaya sıkışır ve ızgara iki farklı çizelgeyi aynı
 * gösterir. Saat aralığı hem ayırt edicidir hem de sürenin kendisini
 * okunur kılar; blok adı ayrıntı görünümünde kalır.
 *
 * Gün sonu `24` yazılır — depoda `00:00` durur (SDD 4.2.2) ve `08–00` bir
 * aralığın sıfır uzunlukta olduğunu düşündürürdü.
 */
export function saatAraligiEtiketi(baslangicSaati: string, bitisSaati: string): string {
  const bas = baslangicSaati.slice(0, 2)
  const bit = bitisSaati.slice(0, 2)
  return `${bas}–${bit === '00' ? '24' : bit}`
}
