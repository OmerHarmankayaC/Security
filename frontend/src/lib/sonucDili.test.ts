import { describe, expect, it } from 'vitest'
import type { CezaKalemi, DogrulamaSonucu, Ihlal } from '@/api/types'
import { sonucuOzetle } from './sonucDili'

/**
 * Sonuç dili (SRS FR-6.4).
 *
 * Ölçülen şey: kullanıcı ilk satırda NE OLDUĞUNU okuyabiliyor mu. Eski ekran
 * "Ceza değişimi: −9999" yazıyordu ve yönünü bile söylemiyordu.
 */

function kalem(kimlik: string, hamFark: number, agirlik = 10): CezaKalemi {
  return {
    kural_kimlik: kimlik,
    ad: `${kimlik} adı`,
    ham_fark: hamFark,
    agirlik,
    agirlikli_fark: hamFark * agirlik,
  }
}

function ihlal(kimlik: string, aciklama = 'gerekçe'): Ihlal {
  return { kural_kimlik: kimlik, aciklama, personel_id: 1, tarih: '2026-03-02', ceza: 1 }
}

function sonuc(ek: Partial<DogrulamaSonucu> = {}): DogrulamaSonucu {
  return {
    kabul_edilebilir: true,
    zorunlu_ihlaller: [],
    ceza_degisimi: 0,
    agirlikli_ceza_degisimi: 0,
    ceza_dokumu: [],
    uyarilar: [],
    ...ek,
  }
}

describe('zorunlu ihlal — başka hiçbir şey söylenmez', () => {
  it('tek ihlalde değişikliğin uygulanmadığını söyler', () => {
    const ozet = sonucuOzetle(sonuc({ kabul_edilebilir: false, zorunlu_ihlaller: [ihlal('H2')] }))
    expect(ozet.tur).toBe('engellendi')
    expect(ozet.cumle).toBe('Bu değişiklik bir zorunlu kuralı bozuyor ve uygulanmadı.')
    expect(ozet.ihlaller).toHaveLength(1)
  })

  it('birden çok ihlalde kural kimliklerini sayar', () => {
    const ozet = sonucuOzetle(
      sonuc({ kabul_edilebilir: false, zorunlu_ihlaller: [ihlal('H2'), ihlal('H9')] }),
    )
    expect(ozet.cumle).toContain('2 zorunlu kuralı')
    expect(ozet.cumle).toContain('H2, H9')
  })

  it('ihlal varken ceza dökümü GÖSTERİLMEZ', () => {
    // Değişiklik uygulanmadığı için döküm gerçekleşmemiş bir durumu anlatır;
    // ikisini birlikte göstermek iki farklı gerçeklik sunardı.
    const ozet = sonucuOzetle(
      sonuc({
        kabul_edilebilir: false,
        zorunlu_ihlaller: [ihlal('H2')],
        ceza_dokumu: [kalem('S4', 3)],
      }),
    )
    expect(ozet.dokum).toEqual([])
  })
})

describe('esnek hedef değişimleri gündelik dille anlatılır', () => {
  it('kapsama açığının kapanmasını söyler', () => {
    const ozet = sonucuOzetle(sonuc({ ceza_dokumu: [kalem('S1', -2, 10000)] }))
    expect(ozet.tur).toBe('iyilesti')
    expect(ozet.cumle).toBe('Kapsama açığı 2 kişi azaldı.')
  })

  it('kapsama açığının açılmasını söyler', () => {
    const ozet = sonucuOzetle(sonuc({ ceza_dokumu: [kalem('S1', 1, 10000)] }))
    expect(ozet.tur).toBe('bozuldu')
    expect(ozet.cumle).toBe('Kapsama açığı 1 kişi arttı.')
  })

  it('adalet hedeflerinde bozuldu/iyileşti dilini kullanır', () => {
    expect(sonucuOzetle(sonuc({ ceza_dokumu: [kalem('S4', 1)] })).cumle).toBe(
      'Toplam saat dengesi 1 saat bozuldu.',
    )
    expect(sonucuOzetle(sonuc({ ceza_dokumu: [kalem('S2', -3)] })).cumle).toBe(
      'Gece adaleti 3 saat iyileşti.',
    )
  })

  it('turun örneğindeki iki yönlü cümleyi üretir', () => {
    // "Vardiya Şefliği'ndeki açık kapandı; toplam saat dengesi bir saat bozuldu"
    const ozet = sonucuOzetle(
      sonuc({ ceza_dokumu: [kalem('S1', -1, 10000), kalem('S4', 1, 1)] }),
    )
    expect(ozet.tur).toBe('karisik')
    expect(ozet.cumle).toBe('Kapsama açığı 1 kişi azaldı; toplam saat dengesi 1 saat bozuldu.')
  })

  it('en AĞIRLIKLI kalem başa gelir', () => {
    const ozet = sonucuOzetle(
      sonuc({ ceza_dokumu: [kalem('S6', 5, 4), kalem('S1', 1, 10000)] }),
    )
    expect(ozet.cumle.startsWith('Kapsama açığı')).toBe(true)
  })

  it('üçten fazla hedefte kalanı sayar', () => {
    const ozet = sonucuOzetle(
      sonuc({
        ceza_dokumu: [
          kalem('S1', 1, 10000),
          kalem('S2', 1, 100),
          kalem('S3', 1, 90),
          kalem('S4', 1, 80),
          kalem('S5', 1, 70),
        ],
      }),
    )
    expect(ozet.cumle).toContain('ve 2 hedef daha etkilendi.')
    // Döküm KIRPILMAZ; ayrıntı bağlantısının arkasında hepsi durur.
    expect(ozet.dokum).toHaveLength(5)
  })

  it('ondalık yalnızca gerektiğinde yazılır', () => {
    expect(sonucuOzetle(sonuc({ ceza_dokumu: [kalem('S4', 1.5)] })).cumle).toContain('1,5 saat')
    expect(sonucuOzetle(sonuc({ ceza_dokumu: [kalem('S4', 2)] })).cumle).toContain('2 saat')
  })

  it('sıfır farklı kalemler cümleye girmez', () => {
    const ozet = sonucuOzetle(sonuc({ ceza_dokumu: [kalem('S4', 0), kalem('S2', -1)] }))
    expect(ozet.cumle).toBe('Gece adaleti 1 saat iyileşti.')
    expect(ozet.dokum).toHaveLength(1)
  })
})

describe('etkisiz değişiklik', () => {
  it('hiçbir hedef etkilenmediğinde bunu açıkça söyler', () => {
    const ozet = sonucuOzetle(sonuc())
    expect(ozet.tur).toBe('degisiklik-yok')
    expect(ozet.cumle).toBe('Değişiklik hiçbir hedefi etkilemedi.')
  })
})

describe('uyarılar ayrı taşınır', () => {
  it('esnek bulgular cümleye karışmaz, kendi listesinde durur', () => {
    const ozet = sonucuOzetle(
      sonuc({ ceza_dokumu: [kalem('S1', 1, 10000)], uyarilar: [ihlal('S1', 'Şeflik açıkta')] }),
    )
    expect(ozet.uyarilar).toHaveLength(1)
    expect(ozet.cumle).not.toContain('Şeflik')
  })
})
