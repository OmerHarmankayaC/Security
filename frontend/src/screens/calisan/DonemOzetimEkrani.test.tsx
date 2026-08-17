/**
 * Dönem Özetim ekranı (SDD 6.1, FR-9.5).
 *
 * BU TESTLER GÖRSEL DOĞRULAMANIN YERİNE GEÇMEZ; ölçülen şey davranış —
 * hangi ufkun çekildiği, kıyasın hangi sayıya göre yapıldığı, havuz dışı
 * metinlerin ne dediği.
 */
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { DonemOzeti, Vardiyalarim } from '@/api/types'

import { DonemOzetimEkrani } from './DonemOzetimEkrani'

let _ozet: DonemOzeti | null
const calisanOzetim = vi.fn()

vi.mock('@/api/client', () => ({
  api: {
    calisanOzetim: (...a: unknown[]) => {
      calisanOzetim(...a)
      return Promise.resolve(_ozet)
    },
  },
}))

const VERI = {
  donem_baslangic_tarihi: '2026-08-17',
  donem_bitis_tarihi: '2026-08-23',
} as Vardiyalarim

const OZET: DonemOzeti = {
  ufuk: 'donem',
  gece_saati: 24,
  ekip_ortalama_gece: 20,
  adil_pay_gece: 16,
  gece_havuzunda: true,
  hafta_sonu_saati: 8,
  ekip_ortalama_hafta_sonu: 8,
  adil_pay_hafta_sonu: 8,
  hafta_sonu_havuzunda: true,
  toplam_saat: 160,
  ekip_ortalama_saat: 158,
  hedef_saat: 160,
}

afterEach(() => {
  cleanup()
  calisanOzetim.mockClear()
})

describe('DonemOzetimEkrani', () => {
  it('açılışta dönem ufkunu çeker', async () => {
    _ozet = OZET
    render(<DonemOzetimEkrani veri={VERI} />)
    await waitFor(() => expect(calisanOzetim).toHaveBeenCalledWith('donem'))
  })

  it('ufuk değişince adalet ufkunu çeker', async () => {
    _ozet = OZET
    render(<DonemOzetimEkrani veri={VERI} />)
    await screen.findByText(/Gece Saati/i)
    fireEvent.click(screen.getByRole('button', { name: /90 gün/i }))
    await waitFor(() => expect(calisanOzetim).toHaveBeenCalledWith('adalet'))
  })

  it('kıyası adil paya göre kurar, ekip ortalamasına göre değil', async () => {
    // gece: sen 24, adil pay 16 -> 8 saat ÜSTÜNDE. Ekip ortalaması 20 olsaydı
    // fark 4 saat olurdu; hangi referansın kullanıldığı metinden okunur.
    _ozet = OZET
    render(<DonemOzetimEkrani veri={VERI} />)
    expect(await screen.findByText(/8,0 saat üzerindesin/)).toBeTruthy()
  })

  it('eşik göreli: adil payın %5 altındaki fark sapma sayılmaz', async () => {
    // toplam: sen 160, hedef 160 -> fark 0. Hafta sonu 8 vs 8 -> fark 0.
    // gece payı 100, sen 103 -> fark 3 < 5 (100 * %5) -> "yakınsın".
    _ozet = { ...OZET, gece_saati: 103, adil_pay_gece: 100 }
    render(<DonemOzetimEkrani veri={VERI} />)
    expect(await screen.findByText(/gece saatinde ortalamaya yakınsın/)).toBeTruthy()
  })

  it('özet yoksa çizelge olmadığını söyler', async () => {
    _ozet = null
    render(<DonemOzetimEkrani veri={VERI} />)
    expect(await screen.findByText(/henüz yayınlanmış bir çizelge yok/i)).toBeTruthy()
  })

  it('havuz dışındaki karşılaştırmayı hiç göstermez', async () => {
    _ozet = { ...OZET, gece_havuzunda: false, adil_pay_gece: null }
    render(<DonemOzetimEkrani veri={VERI} />)
    await screen.findByText(/Hafta Sonu/i)
    expect(screen.queryByText(/Gece Saati/i)).toBeNull()
    expect(screen.getByText(/gece vardiyası bulunmadığı için/i)).toBeTruthy()
  })
})
