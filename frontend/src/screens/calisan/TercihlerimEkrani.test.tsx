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

  it('açık dönem yoksa formu hiç göstermez', async () => {
    _liste = { acik_donem: null, tercihler: [] }
    render(<TercihlerimEkrani />)
    expect(await screen.findByText(/tercihe açık bir dönem yok/i)).toBeTruthy()
    expect(screen.queryByRole('button', { name: /Tercihi Gönder/i })).toBeNull()
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
    render(<TercihlerimEkrani />)
    fireEvent.click(await screen.findByRole('button', { name: /Şu saatlerde/i }))
    const bitis = screen.getByLabelText(/bitiş/i)
    fireEvent.change(bitis, { target: { value: '8' } })
    expect(await screen.findByText(/tüm gün \(24 saat\)/i)).toBeTruthy()
  })
})
