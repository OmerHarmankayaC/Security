import { describe, expect, it } from 'vitest'
import { baslangicBandi, saatAraligiEtiketi, vardiyaHucreSinifi } from './vardiyaRenk'

describe('çizelge hücresinin saat aralığı (SDD 6.3.3)', () => {
  it('gün sonunu 24 yazar — 00 sıfır uzunluk düşündürürdü', () => {
    expect(saatAraligiEtiketi('16:00:00', '00:00:00')).toBe('16–24')
    expect(saatAraligiEtiketi('08:00:00', '16:00:00')).toBe('08–16')
  })

  it('aynı adı taşıyan farklı uzunluktaki bloklar ayırt edilir', () => {
    // Kuralın varlık nedeni: karışık uzunluklu katalogda "Gündüz" adını
    // taşıyan sekiz ve on iki saatlik bloklar aynı kısaltmaya sıkışıyor ve
    // ızgara iki farklı çizelgeyi aynı gösteriyordu.
    expect(saatAraligiEtiketi('08:00:00', '16:00:00')).not.toBe(
      saatAraligiEtiketi('08:00:00', '20:00:00'),
    )
  })

  it('gece yarısını aşan bloğu olduğu gibi gösterir', () => {
    expect(saatAraligiEtiketi('20:00:00', '08:00:00')).toBe('20–08')
  })
})

describe('hücre rengi başlangıç saati bandından gelir', () => {
  it('yedi bloğun tamamı bir banda düşer', () => {
    expect(baslangicBandi('00:00:00')).toBe('gece')
    expect(baslangicBandi('20:00:00')).toBe('gece')
    expect(baslangicBandi('06:00:00')).toBe('sabah')
    expect(baslangicBandi('08:00:00')).toBe('gunduz')
    expect(baslangicBandi('14:00:00')).toBe('aksam')
    expect(baslangicBandi('16:00:00')).toBe('aksam')
  })

  it('renk yalnızca BAŞLANGIÇ SAATİNDEN gelir', () => {
    // 08.00'da başlayan bloklar aynı bandı paylaşır — süreleri farklı
    // olsa bile; ayrımı saat aralığı metni taşır, renk değil.
    expect(vardiyaHucreSinifi('08:00:00')).toBe(vardiyaHucreSinifi('08:00:00'))
    // 06.00'da başlayan uzun blok gündüzden AYRILIR: aynı renkte olsalardı
    // ızgarada 06–16 ile 08–16 ayırt edilemezdi.
    expect(vardiyaHucreSinifi('06:00:00')).not.toBe(vardiyaHucreSinifi('08:00:00'))
  })

  it('gece bandı da saatten okunur', () => {
    // `gece_mi` BAYRAĞI KALKTI (SRS TD-2): işaretlenecek bir nesne yok,
    // fonksiyon zaten yalnızca saate bakıyordu ve imzasından bayrak
    // düştüğünde davranışı değişmedi.
    expect(vardiyaHucreSinifi('20:00:00')).toBe(vardiyaHucreSinifi('22:00:00'))
    expect(vardiyaHucreSinifi('20:00:00')).not.toBe(vardiyaHucreSinifi('08:00:00'))
  })
})
