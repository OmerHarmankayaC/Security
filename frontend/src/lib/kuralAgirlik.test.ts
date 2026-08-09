import { describe, expect, it } from 'vitest'
import type { Kural, KuralTipi } from '@/api/types'
import {
  digerEsnekAgirlikToplami,
  s1BaskinligiKayboldu,
  s1PasifUyarisi,
} from './kuralAgirlik'

function kural(
  kimlik: string,
  agirlik: number | null,
  { aktif = true, tip = 'esnek' as KuralTipi } = {},
): Kural {
  return {
    kural_id: 0,
    kimlik,
    tip,
    parametreler: {},
    agirlik,
    aktif,
    ad: kimlik,
    aciklama: '',
    parametre_tanimlari: [],
    silinebilir_mi: false,
  }
}

describe('digerEsnekAgirlikToplami', () => {
  it('S1 dışındaki aktif esnek hedefleri toplar', () => {
    expect(
      digerEsnekAgirlikToplami([
        kural('S1', 1000),
        kural('S2', 30),
        kural('S3', 20),
        kural('S4', 10),
      ]),
    ).toBe(60)
  })

  it('pasif hedefi saymaz — amaç fonksiyonuna hiç eklenmez', () => {
    expect(
      digerEsnekAgirlikToplami([kural('S1', 1000), kural('S2', 30), kural('S6b', 6, { aktif: false })]),
    ).toBe(30)
  })

  it('zorunlu kısıtları saymaz — ağırlıkları yoktur', () => {
    expect(
      digerEsnekAgirlikToplami([
        kural('S2', 30),
        kural('H2', null, { tip: 'zorunlu' }),
        kural('H5', null, { tip: 'zorunlu' }),
      ]),
    ).toBe(30)
  })

  it('ağırlığı boş olan hedefi sıfır sayar', () => {
    expect(digerEsnekAgirlikToplami([kural('S2', null), kural('S3', 20)])).toBe(20)
  })
})

describe('s1BaskinligiKayboldu', () => {
  it('kalibre edilmiş ağırlıkta uyarı vermez', () => {
    // PROGRESS.md ağırlık kalibrasyonu turu: S1 belirgin biçimde baskın.
    expect(s1BaskinligiKayboldu(1000, 60)).toBe(false)
  })

  it('toplamın altına düşünce uyarır', () => {
    expect(s1BaskinligiKayboldu(50, 60)).toBe(true)
  })

  it('tam eşitlikte de uyarır — baskın değil, eşit', () => {
    expect(s1BaskinligiKayboldu(60, 60)).toBe(true)
  })

  it('S1 tanımlı değilse uyarmaz', () => {
    expect(s1BaskinligiKayboldu(null, 60)).toBe(false)
  })

  it('diğer hedeflerin hepsi pasifken sıfır toplamla uyarmaz', () => {
    expect(s1BaskinligiKayboldu(1, 0)).toBe(false)
  })
})

describe('s1PasifUyarisi', () => {
  it('S1 aktifken uyarmaz', () => {
    expect(s1PasifUyarisi([kural('S1', 10000), kural('S2', 10)])).toBeNull()
  })

  it('S1 pasifken uyarır', () => {
    expect(s1PasifUyarisi([kural('S1', 10000, { aktif: false })])).not.toBeNull()
  })

  it('S1 hiç yoksa uyarmaz — katalog eksikliği ayrı bir sorun', () => {
    expect(s1PasifUyarisi([kural('S2', 10)])).toBeNull()
  })

  it('başka bir hedefin pasifliği S1 uyarısı üretmez', () => {
    // S6b gösterim verisinde bilinçli olarak pasiftir.
    expect(s1PasifUyarisi([kural('S1', 10000), kural('S6b', 6, { aktif: false })])).toBeNull()
  })

  it('metin üç sonucu da söyler', () => {
    const metin = s1PasifUyarisi([kural('S1', 10000, { aktif: false })]) ?? ''
    expect(metin).toContain('boş bir çizelge')
    expect(metin).toContain('üzerinde')
    expect(metin).toContain('0 açık')
  })
})
