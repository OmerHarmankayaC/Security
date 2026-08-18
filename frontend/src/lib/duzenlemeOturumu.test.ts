import { describe, expect, it } from 'vitest'
import type { Atama } from '@/api/types'
import {
  BOS_OTURUM,
  adimEkle,
  adimlariEkle,
  atamalariUygula,
  bekleyenler,
  blokDegisikligi,
  geriAl,
  geriAlinabilirMi,
  kirliMi,
  tasimaAdimlari,
  yenidenUygula,
  yenidenUygulanabilirMi,
} from './duzenlemeOturumu'

/**
 * Taslak düzenleme oturumu (SRS TD-16, FR-6.7, FR-6.8).
 *
 * Turun kabul ölçütü buradan okunur: "on değişiklik yap, beşini geri al,
 * kaydetmeden çık → sürüm hiç değişmemiş". Sürümün değişmemesini sunucu
 * garanti eder (`test_duzenleme_oturumu.py`); burada ölçülen şey, sunucuya
 * GİDECEK listenin geri almadan sonra doğru olmasıdır.
 */

const GUN = '2026-03-02'

function aralik(bas: number, bit: number) {
  return { baslangic: bas, bitis: bit, noktaId: 7 }
}

function atama(id: number, personelId: number, tarih: string, bas: number, sure: number): Atama {
  const bit = (bas + sure) % 24
  return {
    atama_id: id,
    personel_id: personelId,
    baslangic_zamani: `${tarih}T${String(bas).padStart(2, '0')}:00:00`,
    bitis_zamani: `${tarih}T${String(bit).padStart(2, '0')}:00:00`,
    tarih,
    sure_saat: sure,
    nokta_id: 7,
    kilitli: false,
    kaynak: 'cozucu',
  }
}

describe('birikim ve imleç', () => {
  it('boş oturum kirli değildir', () => {
    expect(kirliMi(BOS_OTURUM)).toBe(false)
    expect(bekleyenler(BOS_OTURUM)).toEqual([])
    expect(geriAlinabilirMi(BOS_OTURUM)).toBe(false)
    expect(yenidenUygulanabilirMi(BOS_OTURUM)).toBe(false)
  })

  it('KABUL: on değişiklik yap, beşini geri al — sunucuya beşi gider', () => {
    let oturum = BOS_OTURUM
    for (let i = 0; i < 10; i += 1) {
      oturum = adimEkle(oturum, blokDegisikligi(i + 1, GUN, aralik(8, 16)))
    }
    expect(bekleyenler(oturum)).toHaveLength(10)

    for (let i = 0; i < 5; i += 1) oturum = geriAl(oturum)
    expect(bekleyenler(oturum)).toHaveLength(5)
    // Geri alınanlar SİLİNMEZ; yeniden uygulanabilir olmalı.
    expect(oturum.adimlar).toHaveLength(10)
    expect(yenidenUygulanabilirMi(oturum)).toBe(true)
    expect(bekleyenler(oturum).map((d) => d.personel_id)).toEqual([1, 2, 3, 4, 5])
  })

  it('yeniden uygulama birikimi geri getirir', () => {
    let oturum = adimlariEkle(BOS_OTURUM, [
      blokDegisikligi(1, GUN, aralik(8, 16)),
      blokDegisikligi(2, GUN, aralik(8, 16)),
    ])
    oturum = geriAl(geriAl(oturum))
    expect(kirliMi(oturum)).toBe(false)
    oturum = yenidenUygula(yenidenUygula(oturum))
    expect(bekleyenler(oturum)).toHaveLength(2)
  })

  it('geri alıp yeni bir adım eklemek ileri dalı ATAR', () => {
    let oturum = adimlariEkle(BOS_OTURUM, [
      blokDegisikligi(1, GUN, aralik(8, 16)),
      blokDegisikligi(2, GUN, aralik(8, 16)),
    ])
    oturum = geriAl(oturum)
    oturum = adimEkle(oturum, blokDegisikligi(3, GUN, aralik(0, 8)))
    // Yeniden uygula, kullanıcının HİÇ yapmadığı ikinci adımı geri
    // getirmemeli — tarayıcıların geri alma yığınıyla aynı davranış.
    expect(yenidenUygulanabilirMi(oturum)).toBe(false)
    expect(bekleyenler(oturum).map((d) => d.personel_id)).toEqual([1, 3])
  })

  it('sınırların dışına taşmaz', () => {
    expect(geriAl(BOS_OTURUM)).toEqual(BOS_OTURUM)
    const tek = adimEkle(BOS_OTURUM, blokDegisikligi(1, GUN, aralik(8, 16)))
    expect(yenidenUygula(tek)).toEqual(tek)
  })
})

describe('blokDegisikligi', () => {
  it('aralık verildiğinde saatleri sunucu biçiminde yazar', () => {
    expect(blokDegisikligi(3, GUN, aralik(8, 16))).toEqual({
      personel_id: 3,
      tarih: GUN,
      baslangic_saati: '08:00:00',
      bitis_saati: '16:00:00',
      nokta_id: 7,
    })
  })

  it('null aralık o günün bloğunu KALDIRIR — üçü de boş', () => {
    expect(blokDegisikligi(3, GUN, null)).toEqual({
      personel_id: 3,
      tarih: GUN,
      baslangic_saati: null,
      bitis_saati: null,
      nokta_id: null,
    })
  })

  it('gün sonu 24 saat başı 00 olarak yazılır', () => {
    expect(blokDegisikligi(3, GUN, aralik(16, 24)).bitis_saati).toBe('00:00:00')
  })
})

describe('taşıma İKİ değişikliktir', () => {
  it('kaynaktan kaldırma ve hedefe yazma üretir', () => {
    const adimlar = tasimaAdimlari(1, 2, GUN, aralik(8, 16))
    expect(adimlar).toHaveLength(2)
    expect(adimlar[0]).toMatchObject({ personel_id: 1, baslangic_saati: null })
    expect(adimlar[1]).toMatchObject({ personel_id: 2, baslangic_saati: '08:00:00' })
  })

  it('iki adım TEK TEK geri alınır', () => {
    let oturum = adimlariEkle(BOS_OTURUM, tasimaAdimlari(1, 2, GUN, aralik(8, 16)))
    expect(bekleyenler(oturum)).toHaveLength(2)
    oturum = geriAl(oturum)
    // Yarım geri alınmış taşıma: kaynaktan kaldırıldı, hedefe yazılmadı.
    // Bu geçerli bir ara durumdur ve ızgarada da öyle görünür.
    expect(bekleyenler(oturum)).toHaveLength(1)
    expect(bekleyenler(oturum)[0]!.personel_id).toBe(1)
  })
})

describe('atamalariUygula — ızgaranın gördüğü liste', () => {
  const mevcut = [atama(1, 1, GUN, 8, 8), atama(2, 2, GUN, 16, 8)]

  it('değişiklik yoksa listeyi olduğu gibi bırakır', () => {
    expect(atamalariUygula(mevcut, [])).toEqual(mevcut)
  })

  it('o günün bloğunu YERİNE KOYAR', () => {
    const sonuc = atamalariUygula(mevcut, [blokDegisikligi(1, GUN, aralik(0, 8))])
    expect(sonuc).toHaveLength(2)
    const yeni = sonuc.find((a) => a.personel_id === 1)!
    expect(yeni.sure_saat).toBe(8)
    expect(yeni.baslangic_zamani).toContain('T00:00:00')
    expect(yeni.kaynak).toBe('manuel')
  })

  it('boş değişiklik bloğu KALDIRIR', () => {
    const sonuc = atamalariUygula(mevcut, [blokDegisikligi(1, GUN, null)])
    expect(sonuc.map((a) => a.personel_id)).toEqual([2])
  })

  it('taşıma iki adımla bloğu diğer personele geçirir', () => {
    const sonuc = atamalariUygula(mevcut, tasimaAdimlari(1, 3, GUN, aralik(8, 16)))
    expect(sonuc.map((a) => a.personel_id).sort()).toEqual([2, 3])
  })

  it('gece yarısını aşan blokta bitiş ERTESİ güne düşer', () => {
    const sonuc = atamalariUygula([], [blokDegisikligi(1, GUN, aralik(20, 6))])
    expect(sonuc[0]!.sure_saat).toBe(10)
    expect(sonuc[0]!.baslangic_zamani).toBe('2026-03-02T20:00:00')
    expect(sonuc[0]!.bitis_zamani).toBe('2026-03-03T06:00:00')
    // Blok BAŞLADIĞI güne sayılır (SRS TD-1).
    expect(sonuc[0]!.tarih).toBe(GUN)
  })

  it('gece yarısını aşan DÜNKÜ blok, bugüne yapılan değişiklikten etkilenmez', () => {
    const dun = atama(9, 1, '2026-03-01', 20, 10)
    const sonuc = atamalariUygula([dun], [blokDegisikligi(1, GUN, aralik(8, 16))])
    // Filtre bloğun BAŞLADIĞI güne bakar; dünün bloğu el değmeden kalır.
    expect(sonuc).toHaveLength(2)
    expect(sonuc.some((a) => a.atama_id === 9)).toBe(true)
  })

  it('aynı hücrenin ikinci değişikliği birincinin yerine geçer', () => {
    const sonuc = atamalariUygula(mevcut, [
      blokDegisikligi(1, GUN, aralik(0, 8)),
      blokDegisikligi(1, GUN, aralik(12, 20)),
    ])
    const yeni = sonuc.filter((a) => a.personel_id === 1)
    expect(yeni).toHaveLength(1)
    expect(yeni[0]!.baslangic_zamani).toContain('T12:00:00')
  })

  it('kaydedilmemiş bloklar negatif kimlik taşır — gerçek satır değiller', () => {
    const sonuc = atamalariUygula([], [blokDegisikligi(1, GUN, aralik(8, 16))])
    expect(sonuc[0]!.atama_id).toBeLessThan(0)
  })
})
