import { describe, expect, it } from 'vitest'
import { utcTarihiAyristir } from './tarih'

/**
 * TIMESTAMPTZ göçünden (c8f2d1a45b73) sonra API zaman damgalarını ofsetle
 * döndürüyor ("2026-08-08T06:14:14.058150Z"); göç öncesinde ofsetsiz
 * dönüyordu. `utcTarihiAyristir` tek geçiş noktası olarak kalır ve iki
 * biçimi de doğru okumak zorundadır:
 *
 *   - Ofset YOKSA değer UTC kabul edilip 'Z' eklenir. Eklenmezse tarayıcı
 *     dizeyi YEREL saat sanar ve Türkiye'de üç saatlik bir kayma doğar.
 *   - Ofset VARSA ikinci kez eklenmez. Eklenirse dize geçersizleşir
 *     ("...Z Z") ve `Invalid Date` çıkar.
 */
describe('utcTarihiAyristir', () => {
  const beklenen = Date.UTC(2026, 7, 8, 6, 14, 14) // 8 Ağustos 2026, 06:14:14 UTC

  it('ofsetsiz dizeyi UTC olarak okur', () => {
    expect(utcTarihiAyristir('2026-08-08T06:14:14').getTime()).toBe(beklenen)
  })

  it('ofsetsiz, salise içeren dizeyi UTC olarak okur', () => {
    expect(utcTarihiAyristir('2026-08-08T06:14:14.058150').getTime()).toBe(beklenen + 58)
  })

  it("'Z' taşıyan dizeye ikinci kez ofset eklemez", () => {
    const sonuc = utcTarihiAyristir('2026-08-08T06:14:14Z')
    expect(Number.isNaN(sonuc.getTime())).toBe(false)
    expect(sonuc.getTime()).toBe(beklenen)
  })

  it('göçten sonra API’nin gerçekte döndürdüğü biçimi okur', () => {
    // Ölçülen gerçek çıktı (GET /api/surum): salise + 'Z'.
    const sonuc = utcTarihiAyristir('2026-08-08T06:14:14.058150Z')
    expect(Number.isNaN(sonuc.getTime())).toBe(false)
    expect(sonuc.getTime()).toBe(beklenen + 58)
  })

  it('+HH:MM ofsetini olduğu gibi kabul eder', () => {
    // 09:14:14+03:00 == 06:14:14 UTC
    expect(utcTarihiAyristir('2026-08-08T09:14:14+03:00').getTime()).toBe(beklenen)
  })

  it('iki nokta üst üste taşımayan +HHMM ofsetini de kabul eder', () => {
    expect(utcTarihiAyristir('2026-08-08T09:14:14+0300').getTime()).toBe(beklenen)
  })

  it('eksi ofseti kabul eder', () => {
    // 03:14:14-03:00 == 06:14:14 UTC
    expect(utcTarihiAyristir('2026-08-08T03:14:14-03:00').getTime()).toBe(beklenen)
  })

  it('tarih bölümündeki tireyi ofset sanmaz', () => {
    // "2026-08-08" sonu "-08" ile biter; eski regex bunu ofset sayabilirdi.
    // Yalnız tarih verilen bir dize JS tarafından zaten UTC gece yarısı
    // olarak okunur; önemli olan sonucun geçerli bir tarih olmasi.
    const sonuc = utcTarihiAyristir('2026-08-08')
    expect(Number.isNaN(sonuc.getTime())).toBe(false)
    expect(sonuc.getTime()).toBe(Date.UTC(2026, 7, 8))
  })
})
