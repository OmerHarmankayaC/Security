import { describe, expect, it } from 'vitest'
import type { Kural } from '@/api/types'
import { blokSinirlariniOku, sinirUyarisi } from './kuralParametre'

function kural(kimlik: string, parametreler: Record<string, unknown>, aktif = true): Kural {
  return {
    kural_id: 1,
    kimlik,
    tip: 'zorunlu',
    parametreler,
    agirlik: null,
    aktif,
    ad: kimlik,
    aciklama: '',
    parametre_tanimlari: [],
    silinebilir_mi: false,
  }
}

const KATALOG: Kural[] = [
  kural('H1', { asgari_blok_saat: 4 }),
  kural('H9', { azami_gunluk_saat: 11 }),
]

describe('blokSinirlariniOku — değer koda gömülmez', () => {
  it('sınırları kural kataloğundan okur', () => {
    expect(blokSinirlariniOku(KATALOG)).toEqual({ asgariSaat: 4, azamiSaat: 11 })
  })

  it('kullanıcı parametreyi değiştirdiğinde ızgara yeni değeri görür', () => {
    const degismis = [kural('H1', { asgari_blok_saat: 6 }), kural('H9', { azami_gunluk_saat: 12 })]
    expect(blokSinirlariniOku(degismis)).toEqual({ asgariSaat: 6, azamiSaat: 12 })
  })

  it('PASİF kural sınır koymaz', () => {
    const pasif = [
      kural('H1', { asgari_blok_saat: 4 }, false),
      kural('H9', { azami_gunluk_saat: 11 }, false),
    ]
    expect(blokSinirlariniOku(pasif)).toEqual({ asgariSaat: null, azamiSaat: null })
  })

  it('kural hiç yoksa ya da parametre sayı değilse sınır yoktur', () => {
    expect(blokSinirlariniOku([])).toEqual({ asgariSaat: null, azamiSaat: null })
    expect(blokSinirlariniOku([kural('H1', { asgari_blok_saat: 'dört' })]).asgariSaat).toBeNull()
  })
})

describe('sinirUyarisi — sınır sürükleme SIRASINDA görünür', () => {
  const sinirlar = { asgariSaat: 4, azamiSaat: 11 }

  it('asgari süreden kısa seçim engellenir ve nedeni yazılır', () => {
    expect(sinirUyarisi(3, sinirlar)).toBe('Asgari blok 4 saat (H1)')
  })

  it('günlük tavanı aşan seçim engellenir', () => {
    expect(sinirUyarisi(12, sinirlar)).toBe('Günlük azami 11 saat (H9)')
  })

  it('sınırların içindeki seçim uyarı üretmez', () => {
    expect(sinirUyarisi(4, sinirlar)).toBeNull()
    expect(sinirUyarisi(11, sinirlar)).toBeNull()
    expect(sinirUyarisi(8, sinirlar)).toBeNull()
  })

  it('sınır tanımlı değilse hiçbir seçim engellenmez', () => {
    expect(sinirUyarisi(1, { asgariSaat: null, azamiSaat: null })).toBeNull()
    expect(sinirUyarisi(24, { asgariSaat: null, azamiSaat: null })).toBeNull()
  })
})
