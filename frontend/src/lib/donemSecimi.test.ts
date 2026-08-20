import { describe, expect, it } from 'vitest'

import { donemSec, olculebilirSurum } from './donemSecimi'

const donem = (donem_id: number, bas: string, bit: string) =>
  ({ donem_id, baslangic_tarihi: bas, bitis_tarihi: bit }) as never

const DONEMLER = [
  donem(89, '2026-07-20', '2026-07-26'),
  donem(93, '2026-08-17', '2026-08-23'),
  donem(94, '2026-08-24', '2026-08-30'),
]

describe('donemSec', () => {
  it('bugünü içeren dönemi seçer — listenin ilk öğesini DEĞİL', () => {
    // ÖZET EKRANININ HATASI TAM BURADAYDI: `/api/donem` artan tarihe göre
    // sıralı döner, ekran `d[0]` alıyordu ve bu EN ESKİ dönemdi. Kenar
    // çubuğu güncel dönemi yazarken kartlar 20-26 Temmuz'un sayılarını
    // gösteriyordu.
    expect(donemSec(DONEMLER, '2026-08-19')?.donem_id).toBe(93)
  })

  it('bugün hiçbir döneme düşmüyorsa en yakın GELECEK dönemi seçer', () => {
    expect(donemSec(DONEMLER, '2026-08-01')?.donem_id).toBe(93)
  })

  it('gelecek dönem de yoksa en son geçmiş dönemi seçer', () => {
    expect(donemSec(DONEMLER, '2026-12-31')?.donem_id).toBe(94)
  })

  it('giriş sırası sonucu değiştirmez', () => {
    const ters = [...DONEMLER].reverse()
    expect(donemSec(ters, '2026-08-19')?.donem_id).toBe(93)
  })

  it('boş listede tanımsız döner', () => {
    expect(donemSec([], '2026-08-19')).toBeUndefined()
  })
})

describe('olculebilirSurum', () => {
  const S = (surum_id: number, durum: string, atama_sayisi: number) =>
    ({ surum_id, surum_no: 1, durum, atama_sayisi }) as never

  it('atamasız sürümü ATLAR, ölçülebilir en yeni sürümü verir', () => {
    // Ölçüt "taslak değil" İDİ ve "çözülmemiş taslağın ataması yoktur"
    // varsayımına dayanıyordu. Elle çizilen taslağın (Görev 1) ataması
    // vardır; bu yüzden ölçüt artık atama_sayisi'na bakar.
    const surumler = [S(76, 'taslak', 0), S(70, 'yayinlandi', 42)]
    expect(olculebilirSurum(surumler)?.surum_id).toBe(70)
  })

  it('hiç atama yoksa tanımsız döner — ekran ölçüm yerine durumu söyler', () => {
    expect(olculebilirSurum([S(76, 'taslak', 0)])).toBeUndefined()
  })

  it('ataması olan TASLAK da seçilir — eski ölçüt onu hiç görmüyordu', () => {
    // Elle çizilen boş taslak (Görev 1) çözülmeden ataması vardır. Eski
    // ölçüt ("taslak değil") tam bu sürümü atlıyordu ve Özet ekranı onu
    // hiç ölçmüyordu.
    const surumler = [S(80, 'taslak', 12)]
    expect(olculebilirSurum(surumler)?.surum_id).toBe(80)
  })

  it('atamasız sürüm ATLANIR, ataması olan bir sonraki sürüm seçilir', () => {
    const surumler = [S(81, 'cozuldu', 0), S(75, 'yayinlandi', 30)]
    expect(olculebilirSurum(surumler)?.surum_id).toBe(75)
  })
})
