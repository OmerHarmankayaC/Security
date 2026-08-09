import { describe, expect, it } from 'vitest'
import type { Ben, Rol } from '@/api/types'
import { navGruplari, yuzeyBasligi, yuzeySec } from './yetki'

function ben(rol: Rol, parolaDegistirmeli = false): Ben {
  return {
    kullanici_adi: 'test',
    rol,
    parola_degistirmeli: parolaDegistirmeli,
    personel_id: rol === 'calisan' ? 1 : null,
    ad_soyad: rol === 'calisan' ? 'Test Personel' : null,
  }
}

describe('yuzeySec', () => {
  it('oturum yokken giriş ekranını seçer', () => {
    expect(yuzeySec(null)).toBe('giris')
  })

  it('rolü kendi yüzeyine götürür (SRS 5.10)', () => {
    expect(yuzeySec(ben('calisan'))).toBe('calisan')
    expect(yuzeySec(ben('yonetici'))).toBe('yonetici')
    expect(yuzeySec(ben('yonetim'))).toBe('yonetici')
  })

  it('parola borcu her rolde diğer her şeyin önüne geçer (FR-10.7)', () => {
    // Sunucu da diğer uç noktaları kapatıyor; arayüz kullanıcıyı boş
    // ekranlarla baş başa bırakmasın diye doğrudan borcun ödeneceği yere
    // götürür. Üç rolde de aynı, çünkü borç role bağlı değil.
    for (const rol of ['calisan', 'yonetici', 'yonetim'] as const) {
      expect(yuzeySec(ben(rol, true))).toBe('parola')
    }
  })
})

describe('navGruplari', () => {
  it('Kullanıcılar menüsünü yalnız yönetim rolüne verir', () => {
    const kullanicilariIceriyor = (rol: Rol) =>
      navGruplari(rol).some((g) => g.ogeler.includes('Kullanıcılar'))

    expect(kullanicilariIceriyor('yonetim')).toBe(true)
    expect(kullanicilariIceriyor('yonetici')).toBe(false)
    expect(kullanicilariIceriyor('calisan')).toBe(false)
  })

  it('yöneticinin menüsü yönetiminkinin alt kümesidir (roller kapsayıcı)', () => {
    const yoneticininkiler = navGruplari('yonetici').flatMap((g) => g.ogeler)
    const yonetiminkiler = navGruplari('yonetim').flatMap((g) => g.ogeler)
    for (const oge of yoneticininkiler) {
      expect(yonetiminkiler).toContain(oge)
    }
  })

  it('menü listesini değiştirmez (paylaşılan sabit kirlenmemeli)', () => {
    // navGruplari yeni bir dizi döndürmeliydi; ortak NAV_GRUPLARI'na
    // eklemek, bir kez yönetim rolüyle çağrıldıktan sonra yöneticiye de
    // Kullanıcılar menüsünü gösterirdi.
    navGruplari('yonetim')
    expect(navGruplari('yonetici').some((g) => g.ogeler.includes('Kullanıcılar'))).toBe(false)
  })
})

describe('yuzeyBasligi', () => {
  it('her yüzeye ayrı bir sekme başlığı verir', () => {
    const basliklar = (['giris', 'parola', 'calisan', 'yonetici'] as const).map(yuzeyBasligi)
    expect(new Set(basliklar).size).toBe(basliklar.length)
    for (const baslik of basliklar) expect(baslik.startsWith('Vardiya')).toBe(true)
  })
})
