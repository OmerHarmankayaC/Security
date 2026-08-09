import { describe, expect, it } from 'vitest'
import type { Kural, KuralTipi, ParametreTanimi } from '@/api/types'
import { degisiklikleriBul, kirliMi, yazilacaklariBul } from './kuralDuzenleme'

function kural(
  kimlik: string,
  {
    agirlik = null as number | null,
    aktif = true,
    tip = 'esnek' as KuralTipi,
    parametreler = {} as Record<string, unknown>,
    tanimlar = [] as ParametreTanimi[],
  } = {},
): Kural {
  return {
    kural_id: 0,
    kimlik,
    tip,
    parametreler,
    agirlik,
    aktif,
    ad: `${kimlik} adı`,
    aciklama: '',
    parametre_tanimlari: tanimlar,
    silinebilir_mi: false,
  }
}

const DINLENME: ParametreTanimi = {
  anahtar: 'asgari_dinlenme_saati',
  etiket: 'Asgari dinlenme süresi',
  birim: 'saat',
  asgari: 1,
  azami: 72,
}

describe('degisiklikleriBul', () => {
  it('değişiklik yokken boş liste döner', () => {
    const kurallar = [kural('S1', { agirlik: 10000 }), kural('S2', { agirlik: 10 })]
    expect(degisiklikleriBul(kurallar, kurallar.map((k) => ({ ...k })))).toEqual([])
  })

  it('aktiflik değişimini kullanıcı diliyle yazar', () => {
    const once = [kural('S1', { agirlik: 10000 })]
    const sonra = [kural('S1', { agirlik: 10000, aktif: false })]
    expect(degisiklikleriBul(once, sonra)).toEqual([
      { kimlik: 'S1', ad: 'S1 adı', etiket: 'Aktiflik', onceki: 'Aktif', yeni: 'Pasif' },
    ])
  })

  it('ağırlık değişimini yazar', () => {
    const d = degisiklikleriBul([kural('S2', { agirlik: 10 })], [kural('S2', { agirlik: 4 })])
    expect(d).toHaveLength(1)
    expect(d[0]).toMatchObject({ etiket: 'Ağırlık', onceki: '10', yeni: '4' })
  })

  it('parametre değişimini etiketiyle yazar', () => {
    const once = [
      kural('H2', {
        tip: 'zorunlu',
        parametreler: { asgari_dinlenme_saati: 16 },
        tanimlar: [DINLENME],
      }),
    ]
    const sonra = [
      kural('H2', {
        tip: 'zorunlu',
        parametreler: { asgari_dinlenme_saati: 11 },
        tanimlar: [DINLENME],
      }),
    ]
    expect(degisiklikleriBul(once, sonra)).toEqual([
      {
        kimlik: 'H2',
        ad: 'H2 adı',
        etiket: 'Asgari dinlenme süresi',
        onceki: '16',
        yeni: '11',
      },
    ])
  })

  it('aynı değere dokunup bırakmayı değişiklik saymaz', () => {
    // Onay kutusu gerçekten değişeni göstermeli; yoksa kendi güvenilirliğini
    // kaybeder ve kullanıcı onu okumadan onaylamaya alışır.
    const once = [kural('S2', { agirlik: 10 })]
    const sonra = [kural('S2', { agirlik: 10 })]
    expect(degisiklikleriBul(once, sonra)).toEqual([])
  })

  it('birden fazla kuraldaki birden fazla alanı toplar', () => {
    const once = [kural('S1', { agirlik: 10000 }), kural('S2', { agirlik: 10 })]
    const sonra = [
      kural('S1', { agirlik: 500, aktif: false }),
      kural('S2', { agirlik: 10 }),
    ]
    const d = degisiklikleriBul(once, sonra)
    expect(d.map((x) => x.etiket)).toEqual(['Aktiflik', 'Ağırlık'])
    expect(d.every((x) => x.kimlik === 'S1')).toBe(true)
  })
})

describe('yazilacaklariBul', () => {
  it('değişiklik yokken hiçbir istek üretmez', () => {
    const kurallar = [kural('S1', { agirlik: 10000 })]
    expect(yazilacaklariBul(kurallar, [{ ...kurallar[0]! }])).toEqual([])
  })

  it('kural başına tek istek üretir, birden fazla alan değişse de', () => {
    const once = [kural('S1', { agirlik: 10000 })]
    const sonra = [kural('S1', { agirlik: 500, aktif: false })]
    expect(yazilacaklariBul(once, sonra)).toEqual([
      { kimlik: 'S1', govde: { aktif: false, agirlik: 500 } },
    ])
  })

  it('gövdeye yalnızca değişen alanı koyar', () => {
    const once = [kural('S2', { agirlik: 10 })]
    const sonra = [kural('S2', { agirlik: 4 })]
    const [yazma] = yazilacaklariBul(once, sonra)
    expect(Object.keys(yazma!.govde)).toEqual(['agirlik'])
  })

  it('parametreleri yalnızca değişen anahtarla gönderir', () => {
    const tanimlar = [
      DINLENME,
      { anahtar: 'baska', etiket: 'Başka', birim: null, asgari: 0, azami: 9 },
    ]
    const once = [
      kural('H2', {
        tip: 'zorunlu',
        parametreler: { asgari_dinlenme_saati: 16, baska: 3 },
        tanimlar,
      }),
    ]
    const sonra = [
      kural('H2', {
        tip: 'zorunlu',
        parametreler: { asgari_dinlenme_saati: 11, baska: 3 },
        tanimlar,
      }),
    ]
    expect(yazilacaklariBul(once, sonra)).toEqual([
      { kimlik: 'H2', govde: { parametreler: { asgari_dinlenme_saati: 11 } } },
    ])
  })

  it('değişmeyen kuralı hiç göndermez', () => {
    const once = [kural('S1', { agirlik: 10000 }), kural('S2', { agirlik: 10 })]
    const sonra = [kural('S1', { agirlik: 10000 }), kural('S2', { agirlik: 4 })]
    expect(yazilacaklariBul(once, sonra).map((y) => y.kimlik)).toEqual(['S2'])
  })
})

describe('kirliMi', () => {
  it('dokunulmamış taslak kirli değildir', () => {
    const kurallar = [kural('S1', { agirlik: 10000 })]
    expect(kirliMi(kurallar, [{ ...kurallar[0]! }])).toBe(false)
  })

  it('tek alan değişimi kirli sayar', () => {
    expect(kirliMi([kural('S1', { agirlik: 10000 })], [kural('S1', { agirlik: 9999 })])).toBe(
      true,
    )
  })
})
