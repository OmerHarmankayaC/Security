import { describe, expect, it } from 'vitest'
import type { KisiSayisi } from '@/api/types'
import { adaletSatirlari } from './adalet'

/**
 * Adalet ölçüsünün arayüzdeki karşılığı (Tur 6 İş 6).
 *
 * Bu testlerin kilitlediği şey ÇÖZÜCÜYLE AYNI SAYIYI ÜRETMEKTİR. Ekranda
 * daha hoş duran bir sapma ölçüsü kullanmak, aynı çizelge için ceza
 * dökümünde başka, adalet grafiğinde başka bir sayı gösterirdi; aynı bilginin
 * iki türetme yolu bu projede tekrarlayan bir hata.
 */

function kalem(id: number, sayi: number, pay: number | null): KisiSayisi {
  return { personel_id: id, ad_soyad: `P${id}`, sayi, pay }
}

describe('referans, HAVUZ ORTALAMASI değil kişiye düşen adil paydır', () => {
  it('payı satırın kendisinden alır — ortalamayı hesaplamaz', () => {
    // İki kişinin payı farklı: erişilebilirlikleri farklı (SRS S2). Tek bir
    // ortalama kullanılsaydı ikisi de aynı referansa vurulur ve kısıtlı
    // erişimi olan kalıcı olarak sapmalı görünürdü.
    const satirlar = adaletSatirlari([kalem(1, 40, 40), kalem(2, 8, 8)])
    expect(satirlar.map((s) => s.pay)).toEqual([40, 8])
    expect(satirlar.every((s) => s.sapma === 0)).toBe(true)
  })

  it('payı bulunmayan kalemde pay sıfır sayılır', () => {
    expect(adaletSatirlari([kalem(1, 3, null)])[0]!.pay).toBe(0)
  })
})

describe('sapma çözücünün formülüdür: max(saat − ⌊pay⌋, ⌈pay⌉ − saat, 0)', () => {
  it('tam sayı payda payı tutturan kişi cezasızdır', () => {
    expect(adaletSatirlari([kalem(1, 12, 12)])[0]!.sapma).toBe(0)
  })

  it('payın üstünde çalışan kişide sapma farktır', () => {
    expect(adaletSatirlari([kalem(1, 18, 12)])[0]!.sapma).toBe(6)
  })

  it('payın altında kalan kişide de sapma birikir', () => {
    expect(adaletSatirlari([kalem(1, 6, 12)])[0]!.sapma).toBe(6)
  })

  it('kesirli payda taban/tavan bandı uygulanır', () => {
    // pay = 7,4 → taban 7, tavan 8. Çözücünün ölçüsü işaretsizdir ve kesirli
    // payda en küçük değeri birdir; ekran onu OLDUĞU GİBİ gösterir, kendi
    // yuvarlamasını yapmaz.
    expect(adaletSatirlari([kalem(1, 7, 7.4)])[0]!.sapma).toBe(1)
    expect(adaletSatirlari([kalem(1, 8, 7.4)])[0]!.sapma).toBe(1)
    expect(adaletSatirlari([kalem(1, 10, 7.4)])[0]!.sapma).toBe(3)
    expect(adaletSatirlari([kalem(1, 4, 7.4)])[0]!.sapma).toBe(4)
  })

  it('sapma hiçbir zaman negatif olmaz', () => {
    for (const saat of [0, 1, 5, 7, 8, 20]) {
      expect(adaletSatirlari([kalem(1, saat, 7.4)])[0]!.sapma).toBeGreaterThanOrEqual(0)
    }
  })
})

describe('sıralama', () => {
  it('en sapmalı satır başa gelir', () => {
    const satirlar = adaletSatirlari([kalem(1, 12, 12), kalem(2, 30, 12), kalem(3, 16, 12)])
    expect(satirlar.map((s) => s.personel_id)).toEqual([2, 3, 1])
  })

  it('sapma eşitse çok çalışan öne alınır', () => {
    const satirlar = adaletSatirlari([kalem(1, 6, 12), kalem(2, 18, 12)])
    expect(satirlar.map((s) => s.personel_id)).toEqual([2, 1])
  })
})
