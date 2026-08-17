import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { CalisanTercihListesi } from '@/api/types'

import { TercihlerimEkrani } from './TercihlerimEkrani'

let _liste: CalisanTercihListesi
let _hata: unknown = null
const bildir = vi.fn()

vi.mock('@/api/client', () => ({
  api: {
    calisanTercihlerim: () => Promise.resolve(_liste),
    calisanTercihBildir: (...a: unknown[]) => {
      bildir(...a)
      return _hata ? Promise.reject(_hata) : Promise.resolve({})
    },
  },
  ApiHatasi: class extends Error {
    status: number
    constructor(status: number, mesaj: string) {
      super(mesaj)
      this.status = status
    }
  },
}))

const ACIK: CalisanTercihListesi = {
  acik_donem: {
    donem_id: 1,
    baslangic_tarihi: '2099-01-05',
    bitis_tarihi: '2099-01-11',
    tercih_son_tarihi: '2099-01-01',
  },
  tercihler: [],
}

afterEach(() => {
  cleanup()
  bildir.mockClear()
  _hata = null
})

describe('TercihlerimEkrani', () => {
  it('tarih alanını açık dönemle sınırlar', async () => {
    _liste = ACIK
    render(<TercihlerimEkrani />)
    const alan = (await screen.findByLabelText(/gün/i)) as HTMLInputElement
    expect(alan.max).toBe('2099-01-11')
    // Alt sınır bugünden önce olamaz; dönem geleceğe düştüğü için başlangıç.
    expect(alan.min).toBe('2099-01-05')
  })

  it('açık dönem yoksa formu hiç göstermez ama geçmiş tercihleri gösterir', async () => {
    _liste = {
      acik_donem: null,
      tercihler: [
        {
          tercih_id: 1,
          tarih: '2026-01-05',
          tip: 'calismama',
          tercih_baslangic: null,
          tercih_bitis: null,
          calisan_notu: null,
          durum: 'beklemede',
          ret_gerekcesi: null,
          karsilanma: null,
        },
      ],
    }
    render(<TercihlerimEkrani />)
    expect(await screen.findByText(/tercihe açık bir dönem yok/i)).toBeTruthy()
    expect(screen.queryByRole('button', { name: /Tercihi Gönder/i })).toBeNull()
    // Brief'in adını koyarak uyardığı regresyon: erken dönüş "Bildirdiğim
    // Tercihler" kartını GİZLEMEMELİ. Kartın BAŞLIĞI `KartEtiketi` üzerinden
    // buyukHarf() ile geçtiği için (bkz. app-ui.tsx) ASCII case-insensitive
    // regex'le güvenle sorgulanamıyor — bunun yerine kartın İÇERİĞİNİN
    // (boş-durum mesajı değil, gerçek tercih satırı) göründüğü doğrulanıyor;
    // bu hem başlığın hem listenin render edildiğinin dolaylı kanıtıdır.
    expect(screen.queryByText(/henüz tercih bildirmedin/i)).toBeNull()
    expect(screen.getByText(/çalışmak istemiyorum/i)).toBeTruthy()
  })

  it('başarılı gönderimde onay gösterir', async () => {
    _liste = ACIK
    render(<TercihlerimEkrani />)
    fireEvent.click(await screen.findByRole('button', { name: /Tercihi Gönder/i }))
    expect(await screen.findByText(/tercihin alındı/i)).toBeTruthy()
  })

  it('409 gelince yöneticiye başvurmayı söyler', async () => {
    _liste = ACIK
    const { ApiHatasi } = await import('@/api/client')
    _hata = new ApiHatasi(409, 'kararlanmis')
    render(<TercihlerimEkrani />)
    fireEvent.click(await screen.findByRole('button', { name: /Tercihi Gönder/i }))
    expect(await screen.findByText(/yöneticine başvur/i)).toBeTruthy()
  })

  it('tüm gün seçimini açıkça yazar', async () => {
    _liste = ACIK
    const { container } = render(<TercihlerimEkrani />)
    fireEvent.click(await screen.findByRole('button', { name: /Şu saatlerde/i }))
    // `getByLabelText(/bitiş/i)` KULLANILMAZ: etiket `buyukHarf('Bitiş')` ile
    // "BİTİŞ" (noktalı büyük İ) yazar ve JS'in case-insensitive regex
    // katlaması Türkçe İ/ASCII I ayrımını bilmediği için ASCII `/bitiş/i`
    // bunu asla eşleştiremez. `id` üzerinden sorgulamak hangi alanın
    // bulunduğunu belirsiz bırakmıyor.
    const bitis = container.querySelector('#tercih-bitis') as HTMLSelectElement
    expect(bitis).toBeTruthy()
    fireEvent.change(bitis, { target: { value: '8' } })
    expect(await screen.findByText(/tüm gün \(24 saat\)/i)).toBeTruthy()
  })
})
