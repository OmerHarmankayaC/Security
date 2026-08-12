import { describe, expect, it } from 'vitest'
import { araligiSure, araligiYaz, saatiCoz, saatiYaz } from './talepAraligi'

describe('talep aralığının saat kodlaması', () => {
  it('gün sonunu bitişte 24 okur, başlangıçta 0', () => {
    expect(saatiCoz('00:00:00', true)).toBe(24)
    expect(saatiCoz('00:00:00')).toBe(0)
  })

  it('24.00 gün sonunu 00:00 olarak yazar — depoda 24.00 diye bir değer yok', () => {
    expect(saatiYaz(24)).toBe('00:00:00')
    expect(saatiYaz(8)).toBe('08:00:00')
  })

  it('gün boyu aralığı 00.00–24.00 gösterir', () => {
    expect(araligiYaz('00:00:00', '00:00:00')).toBe('00.00–24.00')
  })

  it('gece yarısını aşan aralığı olduğu gibi gösterir', () => {
    expect(araligiYaz('20:00:00', '08:00:00')).toBe('20.00–08.00')
  })

  it('süreyi sunucudaki kuralla aynı hesaplar: fark sıfırsa gün boyudur', () => {
    expect(araligiSure(0, 24)).toBe(24)
    expect(araligiSure(8, 24)).toBe(16)
    expect(araligiSure(20, 8)).toBe(12)
  })
})
