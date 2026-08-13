import { describe, expect, it } from 'vitest'
import {
  aralikAydinligi,
  aralikGradyani,
  saatAydinligi,
  saatGradyani,
  saatMurekkebi,
  saatRengi,
} from './saatRengi'

/**
 * Saat renk bandı (SDD 6.3.3, Tur 6 İş 3).
 *
 * Testin ölçtüğü şey SÜREKLİLİKTİR: kataloglu sürümün üç sabit tonu, saat
 * ekseninde karşılığı olmayan sıçramalar üretiyordu. Renk değerlerinin
 * kendisi tasarım kararıdır ve teste sabitlenmez; sabitlenen şey bandın
 * davranışıdır.
 */

describe('bandın biçimi', () => {
  it('gecenin ortası en koyu, günün ortası en açıktır', () => {
    expect(saatAydinligi(1)).toBeCloseTo(0, 6)
    expect(saatAydinligi(13)).toBeCloseTo(1, 6)
  })

  it('gece penceresinin iki kenarı aynı koyuluktadır', () => {
    // TD-2'ye göre gece 20.00–06.00; 20 ile 06 dip noktaya (01.00) eşit
    // uzaklıktadır ve band bir kategori sınırı çizmediği için eşit çıkar.
    expect(saatAydinligi(20)).toBeCloseTo(saatAydinligi(6), 6)
  })

  it('bandda sıçrama yok: komşu saatler arasındaki fark küçük ve düzgündür', () => {
    for (let saat = 0; saat < 24; saat += 1) {
      const fark = Math.abs(saatAydinligi(saat + 1) - saatAydinligi(saat))
      expect(fark).toBeLessThan(0.15)
    }
  })

  it('yirmi dört saatte bir kendini tekrarlar', () => {
    expect(saatRengi(25)).toBe(saatRengi(1))
    expect(saatRengi(-1)).toBe(saatRengi(23))
  })

  it('her saat geçerli bir onaltılık renk verir', () => {
    for (let saat = 0; saat < 24; saat += 1) {
      expect(saatRengi(saat)).toMatch(/^#[0-9a-f]{6}$/)
    }
  })
})

describe('mürekkep', () => {
  it('koyu gece saatinde açık, aydınlık gündüz saatinde koyu mürekkep verir', () => {
    expect(saatMurekkebi(1)).toBe('var(--vardiya-gece-ink)')
    expect(saatMurekkebi(13)).toBe('var(--ink)')
  })
})

describe('gradient — mini şerit TEK ÖĞEDİR', () => {
  it('dilim sayısı kadar sert durak üretir', () => {
    const gradyan = saatGradyani(['#000000', '#ffffff'])
    expect(gradyan).toBe(
      'linear-gradient(to right, #000000 0.0000% 50.0000%, #ffffff 50.0000% 100.0000%)',
    )
  })

  it('boş saatler saydam kalır — gri boyanmaz', () => {
    expect(saatGradyani([null, '#123456'])).toContain('transparent 0.0000% 50.0000%')
  })

  it('yirmi dört dilim tek bir gradient dizesine sığar', () => {
    const dilimler = Array.from({ length: 24 }, (_, s) => (s >= 8 && s < 16 ? saatRengi(s) : null))
    const gradyan = saatGradyani(dilimler)
    expect(gradyan.startsWith('linear-gradient(to right, ')).toBe(true)
    expect(gradyan.split(',').length - 1).toBe(24)
  })

  it('dilim yoksa gradient de yok', () => {
    expect(saatGradyani([])).toBe('none')
  })
})

describe('aralikGradyani — bloğun kendi saatleri', () => {
  it('aralığın uzunluğu kadar durak taşır', () => {
    expect(aralikGradyani(8, 16).split(',').length - 1).toBe(8)
  })

  it('gece yarısını aşan parçanın saatleri 24 e göre sarılır', () => {
    // Gün sonundan sonraki saatler ertesi günün aynı saatleridir; 24–26 ile
    // 00–02 aynı bandı vermelidir, yoksa taşan parça yanlış renkte çizilir.
    expect(aralikGradyani(24, 26)).toBe(aralikGradyani(0, 2))
    expect(saatGradyani([saatRengi(22), saatRengi(23), saatRengi(24), saatRengi(25)])).toBe(
      aralikGradyani(22, 26),
    )
  })

  it('boş aralık gradient üretmez', () => {
    expect(aralikGradyani(8, 8)).toBe('none')
  })
})

describe('aralikAydinligi', () => {
  it('gece bloğu gündüz bloğundan koyudur', () => {
    expect(aralikAydinligi(20, 30)).toBeLessThan(aralikAydinligi(8, 16))
  })
})
