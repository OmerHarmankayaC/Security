/**
 * İzin belgesi düğmesi (Müsaitlik ekranı).
 *
 * Ölçülen şey düğmenin HANGİ HÂLDE çizildiği: belgesi olan kayıt indirtir,
 * olmayan yükletir. İçeriğin kendisi burada sınanmaz — o backend'in işi ve
 * `tests/test_girdi_api.py` gerçek baytlarla gidiş dönüş yapıyor.
 */
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { Musaitlik, Personel } from '@/api/types'

import { MusaitlikEkrani } from './MusaitlikEkrani'

let _kayitlar: Musaitlik[] = []

vi.mock('../components/AppShell', () => ({
  AppShell: ({ children }: { children: unknown }) => <div>{children as never}</div>,
}))

vi.mock('../api/client', () => ({
  ApiHatasi: class extends Error {
    status: number
    constructor(status: number) {
      super('hata')
      this.status = status
    }
  },
  api: {
    musaitlikListele: () => Promise.resolve(_kayitlar),
    personelListele: () =>
      Promise.resolve([
        { personel_id: 1, ad_soyad: 'Mehmet Aydın', sicil_no: 'VS-001' } as Personel,
      ]),
    izinBelgesiYolu: (id: number) => `/api/musaitlik/${id}/belge`,
  },
}))

function kayit(musaitlik_id: number, belge_var: boolean): Musaitlik {
  return {
    musaitlik_id,
    personel_id: 1,
    baslangic_tarihi: '2026-09-01',
    bitis_tarihi: '2026-09-02',
    dilim: 'tam_gun',
    tip: 'rapor',
    not_: null,
    belge_var,
  } as Musaitlik
}

afterEach(cleanup)

describe('izin belgesi düğmesi', () => {
  it('belgesi olan kayıtta İNDİR gösterir', async () => {
    _kayitlar = [kayit(1, true)]
    render(<MusaitlikEkrani ekranSec={vi.fn()} />)
    await waitFor(() => expect(screen.getByRole('button', { name: 'İndir' })).toBeTruthy())
  })

  it('belgesi olmayan kayıtta EKLE gösterir', async () => {
    _kayitlar = [kayit(2, false)]
    render(<MusaitlikEkrani ekranSec={vi.fn()} />)
    await waitFor(() => expect(screen.getByRole('button', { name: 'Ekle' })).toBeTruthy())
    expect(screen.queryByRole('button', { name: 'İndir' })).toBeNull()
  })

  it('yalnızca kabul edilen tipleri seçtirir', async () => {
    // Beyaz liste sunucuda da var (415 döner); arayüzün dosya seçicisi de
    // aynı listeyi taşımalı, yoksa kullanıcı reddedilecek bir dosyayı
    // seçebiliyor ve hatayı ancak yükledikten sonra görüyor.
    _kayitlar = [kayit(3, false)]
    const { container } = render(<MusaitlikEkrani ekranSec={vi.fn()} />)
    await waitFor(() => expect(screen.getByRole('button', { name: 'Ekle' })).toBeTruthy())
    const girdi = container.querySelector('input[type="file"]')
    expect(girdi?.getAttribute('accept')).toBe('image/png,image/jpeg,application/pdf')
  })
})
