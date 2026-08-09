import { describe, expect, it } from 'vitest'
import { buyukHarf, kisalt } from './metin'

describe('buyukHarf', () => {
  it('Türkçe i harfini noktalı İ yapar', () => {
    // Düz toUpperCase() burada "IZIN" verirdi.
    expect(buyukHarf('izin')).toBe('İZİN')
  })

  it('noktasız ı harfini I yapar', () => {
    expect(buyukHarf('ışık')).toBe('IŞIK')
  })
})

/**
 * Izgara kısaltmaları (SDD 6.3.3). Tanım adları arayüzden değiştirilebildiği
 * için kısaltma sabit bir tablodan değil addan türetilir; test, gösterim
 * verisindeki adların (SRS 3.3.1 ve 3.3.3) ayırt edici kısaltmalar ürettiğini
 * doğrular.
 */
describe('kisalt', () => {
  it('tek kelimeli adı ilk üç harfe indirir', () => {
    expect(kisalt('Güvenlik')).toBe('GÜV')
    expect(kisalt('Müracaat')).toBe('MÜR')
    expect(kisalt('Gündüz')).toBe('GÜN')
    expect(kisalt('Akşam')).toBe('AKŞ')
    expect(kisalt('Gece')).toBe('GEC')
  })

  it('çok kelimeli adı baş harflere indirir', () => {
    expect(kisalt('Vardiya Şefliği')).toBe('VŞ')
  })

  it('gösterim verisindeki üç görev noktası ayrı kısaltmalar üretir', () => {
    const kisaltmalar = ['Vardiya Şefliği', 'Güvenlik', 'Müracaat'].map(kisalt)
    expect(new Set(kisaltmalar).size).toBe(3)
  })

  it('gösterim verisindeki üç vardiya tipi ayrı kısaltmalar üretir', () => {
    const kisaltmalar = ['Gece', 'Gündüz', 'Akşam'].map(kisalt)
    expect(new Set(kisaltmalar).size).toBe(3)
  })

  it('fazladan boşlukları yok sayar ve boş adda boş döner', () => {
    expect(kisalt('  Vardiya   Şefliği  ')).toBe('VŞ')
    expect(kisalt('   ')).toBe('')
  })

  it('üçten fazla kelimede ilk üç baş harfi alır', () => {
    expect(kisalt('Kuzey Ana Kapı Nöbeti')).toBe('KAK')
  })
})
