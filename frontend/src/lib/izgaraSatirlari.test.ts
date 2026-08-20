import { describe, expect, it } from 'vitest'

import type { Atama, Personel } from '@/api/types'

import { izgaraSatirlari } from './izgaraSatirlari'

const DONEM_BAS = '2026-08-17'
const DONEM_BIT = '2026-08-23'

const personel = (
  id: number,
  adSoyad: string,
  aktifBaslangic: string,
  aktifBitis: string | null,
): Personel => ({
  personel_id: id,
  ad_soyad: adSoyad,
  sicil_no: `S${id}`,
  haftalik_hedef_saat: 40,
  aktif_baslangic: aktifBaslangic,
  aktif_bitis: aktifBitis,
  yetkinlik_idleri: [],
  devir_fazla_calisma_saat: '0',
  kota_yili: null,
})

const atama = (personelId: number): Atama => ({
  atama_id: personelId * 1000,
  personel_id: personelId,
  baslangic_zamani: `${DONEM_BAS}T08:00:00Z`,
  bitis_zamani: `${DONEM_BAS}T16:00:00Z`,
  tarih: DONEM_BAS,
  sure_saat: 8,
  nokta_id: 1,
  kilitli: false,
  kaynak: 'cozucu',
})

describe('izgaraSatirlari', () => {
  it('düzenlenebilir sürümde ataması olmayan personel de satır olur', () => {
    // Boş bir taslakta tıklanacak hücre kalmaması tam bu hatanın belirtisi.
    const atamasiz = personel(1, 'Ayşe Yılmaz', '2026-01-01', null)
    const sonuc = izgaraSatirlari({
      personeller: [atamasiz],
      atamalar: [],
      duzenlenebilir: true,
      donemBaslangic: DONEM_BAS,
      donemBitis: DONEM_BIT,
    })
    expect(sonuc.map((p) => p.personel_id)).toEqual([1])
  })

  it('salt okunur sürümde ataması olmayan personel satır OLMAZ', () => {
    const atamasiz = personel(1, 'Ayşe Yılmaz', '2026-01-01', null)
    const sonuc = izgaraSatirlari({
      personeller: [atamasiz],
      atamalar: [],
      duzenlenebilir: false,
      donemBaslangic: DONEM_BAS,
      donemBitis: DONEM_BIT,
    })
    expect(sonuc).toEqual([])
  })

  it('dönem bitmeden önce ayrılmış personel düzenlenebilir sürümde de satır olmaz', () => {
    // aktif_bitis, dönem başlamadan önce kalıyor — H7 bu güne atamayı zaten
    // reddeder, satırı göstermek asla kabul edilmeyecek bir tıklamaya davet ederdi.
    const ayrilmis = personel(2, 'Mehmet Kaya', '2026-01-01', '2026-08-01')
    const sonuc = izgaraSatirlari({
      personeller: [ayrilmis],
      atamalar: [],
      duzenlenebilir: true,
      donemBaslangic: DONEM_BAS,
      donemBitis: DONEM_BIT,
    })
    expect(sonuc).toEqual([])
  })

  it('dönem içinde işe başlayan personel satır olur — kısmi katılım geçerlidir', () => {
    const sonradanBaslayan = personel(3, 'Zeynep Demir', '2026-08-20', null)
    const sonuc = izgaraSatirlari({
      personeller: [sonradanBaslayan],
      atamalar: [],
      duzenlenebilir: true,
      donemBaslangic: DONEM_BAS,
      donemBitis: DONEM_BIT,
    })
    expect(sonuc.map((p) => p.personel_id)).toEqual([3])
  })

  it('salt okunur sürümde ataması olan ama aktiflik penceresi dışındaki personel yine satır olur', () => {
    // Geçmişte verilmiş bir karardır; gizlemek çizelgeyi eksik gösterirdi.
    const ayrilmisAmaAtanmis = personel(4, 'Can Öz', '2026-01-01', '2026-08-01')
    const sonuc = izgaraSatirlari({
      personeller: [ayrilmisAmaAtanmis],
      atamalar: [atama(4)],
      duzenlenebilir: false,
      donemBaslangic: DONEM_BAS,
      donemBitis: DONEM_BIT,
    })
    expect(sonuc.map((p) => p.personel_id)).toEqual([4])
  })

  it('sıralama ad_soyad üzerinden Türkçe locale ile yapılır', () => {
    const b = personel(1, 'Behice Ünal', '2026-01-01', null)
    const a = personel(2, 'Ayşe Yılmaz', '2026-01-01', null)
    const c = personel(3, 'İpek Çelik', '2026-01-01', null)
    const sonuc = izgaraSatirlari({
      personeller: [b, a, c],
      atamalar: [],
      duzenlenebilir: true,
      donemBaslangic: DONEM_BAS,
      donemBitis: DONEM_BIT,
    })
    expect(sonuc.map((p) => p.personel_id)).toEqual([2, 1, 3])
  })
})
