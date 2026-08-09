import { describe, expect, it } from 'vitest'
import {
  AZAMI_DONEM_GUN,
  VARSAYILAN_DONEM_GUN,
  araligiDenetle,
  gunSayisi,
} from './donemAraligi'

describe('gunSayisi', () => {
  it('iki ucu da sayar', () => {
    expect(gunSayisi('2026-08-03', '2026-08-09')).toBe(7)
    expect(gunSayisi('2026-08-03', '2026-08-03')).toBe(1)
  })

  it('ay ve yıl sınırını geçer', () => {
    expect(gunSayisi('2026-12-28', '2027-01-03')).toBe(7)
  })
})

describe('araligiDenetle', () => {
  it('varsayılan bir haftalık aralığı kabul eder (Backlog 07.08.2026)', () => {
    expect(VARSAYILAN_DONEM_GUN).toBe(7)
    expect(araligiDenetle('2026-08-03', '2026-08-09')).toBeNull()
  })

  it('kabul kriterinin 28 günlük dönemini kabul eder (NFR-1)', () => {
    expect(gunSayisi('2026-08-03', '2026-08-30')).toBe(28)
    expect(araligiDenetle('2026-08-03', '2026-08-30')).toBeNull()
  })

  it('tam sınırdaki aralığı kabul eder', () => {
    expect(gunSayisi('2026-08-01', '2026-08-31')).toBe(AZAMI_DONEM_GUN)
    expect(araligiDenetle('2026-08-01', '2026-08-31')).toBeNull()
  })

  it('sınırı bir gün aşan aralığı reddeder', () => {
    const hata = araligiDenetle('2026-08-01', '2026-09-01')
    expect(hata).not.toBeNull()
    expect(hata).toContain('31')
    expect(hata).toContain('32 gün')
  })

  it('ters aralığı reddeder', () => {
    expect(araligiDenetle('2026-08-09', '2026-08-03')).toContain('önce olamaz')
  })

  it('eksik tarihi reddeder', () => {
    expect(araligiDenetle('', '2026-08-09')).not.toBeNull()
    expect(araligiDenetle('2026-08-03', '')).not.toBeNull()
  })

  it('hata metni teknik terim içermez (NFR-5)', () => {
    const hata = araligiDenetle('2026-08-01', '2026-09-30') ?? ''
    for (const terim of ['null', 'undefined', 'ISO', 'baslangic', 'Error']) {
      expect(hata).not.toContain(terim)
    }
    // Kullanıcının ne yapacağını da söylemeli, yalnızca reddetmemeli.
    expect(hata).toContain('seçin')
  })
})
