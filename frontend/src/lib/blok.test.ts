import { describe, expect, it } from 'vitest'
import {
  blokErisilebilirEtiket,
  blokEtiketi,
  blokSuresi,
  geceSaati,
  gunParcasi,
  gununParcalari,
  saatEtiketi,
} from './blok'
import { SOZLUK } from '@/i18n/sozluk'

const TR = SOZLUK.tr

/**
 * Bloğun okunması ve gün ızgarasındaki geometrisi.
 *
 * Bu testlerin ağırlık merkezi GECE YARISINI AŞAN BLOKTUR: hem SRS TD-13'ün
 * "tek blok" kuralının hem de TD-1'in "başladığı güne sayılır" kuralının
 * ekrandaki karşılığı bu geometriden çıkar. Kopyalanmış bir çözümlemenin ilk
 * ayrışacağı yer de burasıdır.
 */

const gecelik = {
  tarih: '2026-02-02',
  baslangic_zamani: '2026-02-02T20:00:00+03:00',
  bitis_zamani: '2026-02-03T06:00:00+03:00',
  sure_saat: 10,
}

const gunduzluk = {
  tarih: '2026-02-02',
  baslangic_zamani: '2026-02-02T08:00:00+03:00',
  bitis_zamani: '2026-02-02T16:00:00+03:00',
  sure_saat: 8,
}

describe('saat metni — TEK biçimleyici', () => {
  it('gün sonunu 24 yazar, 00 değil', () => {
    expect(saatEtiketi(24)).toBe('24.00')
    expect(blokEtiketi('2026-02-02T16:00:00+03:00', '2026-02-03T00:00:00+03:00')).toBe(
      '16.00–24.00',
    )
  })
})

describe('blokSuresi', () => {
  it('gündüz bloğunun süresini verir', () => {
    expect(blokSuresi(gunduzluk.baslangic_zamani, gunduzluk.bitis_zamani)).toBe(8)
  })

  it('gece yarısını aşan blokta ertesi güne sarar', () => {
    expect(blokSuresi(gecelik.baslangic_zamani, gecelik.bitis_zamani)).toBe(10)
  })

  it('başlangıç ve bitiş aynıysa blok gün boyudur, sıfır değil', () => {
    expect(blokSuresi('2026-02-02T08:00:00+03:00', '2026-02-03T08:00:00+03:00')).toBe(24)
  })
})

describe('gunParcasi — gün ızgarasının geometrisi', () => {
  it('gün içinde kalan blok tek parçadır ve iki kenarı da kapalıdır', () => {
    expect(gunParcasi(gunduzluk, '2026-02-02')).toEqual({
      baslangic: 8,
      bitis: 16,
      oncekiGundenGeliyor: false,
      sonrakiGuneTasiyor: false,
    })
  })

  it('gece bloğu başladığı günde sağ kenara dayanır ve taşıdığını söyler', () => {
    expect(gunParcasi(gecelik, '2026-02-02')).toEqual({
      baslangic: 20,
      bitis: 24,
      oncekiGundenGeliyor: false,
      sonrakiGuneTasiyor: true,
    })
  })

  it('ertesi günün ızgarasında sol kenardan başlar ve geldiğini söyler', () => {
    expect(gunParcasi(gecelik, '2026-02-03')).toEqual({
      baslangic: 0,
      bitis: 6,
      oncekiGundenGeliyor: true,
      sonrakiGuneTasiyor: false,
    })
  })

  it('blok üçüncü bir güne hiç değmez', () => {
    expect(gunParcasi(gecelik, '2026-02-04')).toBeNull()
    expect(gunParcasi(gecelik, '2026-02-01')).toBeNull()
  })

  it('gün içinde kalan blok ertesi günün ızgarasında görünmez', () => {
    expect(gunParcasi(gunduzluk, '2026-02-03')).toBeNull()
  })

  it('ay sonunu aşan gece bloğu ertesi ayın ilk gününe düşer', () => {
    const ayDonumu = {
      tarih: '2026-02-28',
      baslangic_zamani: '2026-02-28T22:00:00+03:00',
      bitis_zamani: '2026-03-01T06:00:00+03:00',
      sure_saat: 8,
    }
    expect(gunParcasi(ayDonumu, '2026-03-01')?.oncekiGundenGeliyor).toBe(true)
  })
})

describe('gununParcalari', () => {
  it('bir günde hem taşan hem yeni başlayan bloğu sırayla verir', () => {
    const parcalar = gununParcalari([gecelik, { ...gunduzluk, tarih: '2026-02-03' }], '2026-02-03')
    expect(parcalar.map((p) => p.parca.baslangic)).toEqual([0, 8])
    // İKİSİ FARKLI BLOK: taşan parça önceki günün bloğudur.
    expect(parcalar[0]!.blok.tarih).toBe('2026-02-02')
    expect(parcalar[1]!.blok.tarih).toBe('2026-02-03')
  })

  it('boş günde hiçbir parça vermez', () => {
    expect(gununParcalari([gunduzluk], '2026-02-05')).toEqual([])
  })
})

describe('blokErisilebilirEtiket — renk tek başına bilgi taşımaz', () => {
  it('iki günde de bloğun TAMAMINI yazar, o günkü parçasını değil', () => {
    const bas = gunParcasi(gecelik, '2026-02-02')!
    const son = gunParcasi(gecelik, '2026-02-03')!
    expect(blokErisilebilirEtiket(gecelik, bas, 'Güvenlik', TR)).toBe(
      '20.00–06.00 · Güvenlik · ertesi güne taşıyor',
    )
    expect(blokErisilebilirEtiket(gecelik, son, 'Güvenlik', TR)).toBe(
      '20.00–06.00 · Güvenlik · önceki günden devam ediyor',
    )
  })

  it('gün içinde kalan blokta devam ibaresi bulunmaz', () => {
    const parca = gunParcasi(gunduzluk, '2026-02-02')!
    expect(blokErisilebilirEtiket(gunduzluk, parca, 'Kapı', TR)).toBe('08.00–16.00 · Kapı')
  })
})

describe('geceSaati — gece HESAPLANIR, işaretlenmez', () => {
  it('20.00–06.00 bloğunun tamamı gecedir', () => {
    expect(geceSaati(gecelik.baslangic_zamani, gecelik.sure_saat)).toBe(10)
  })

  it('gündüz bloğu hiç gece saati taşımaz', () => {
    expect(geceSaati(gunduzluk.baslangic_zamani, gunduzluk.sure_saat)).toBe(0)
  })
})
