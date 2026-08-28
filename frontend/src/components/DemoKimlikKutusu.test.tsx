// Gösterim kimlik kutusunun sözleşmesi (Demo Senaryosu 7).
//
// Asıl iddia OLUMSUZ: gerçek bir kurulumda uç nokta yoktur (404) ve ekranda
// hiçbir kullanıcı adı, hiçbir parola görünmez. Bu testin düşmesi, demoya
// ait kimlik bilgisinin üretim ekranına sızdığı anlamına gelir.
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { DemoKimlikKutusu } from './DemoKimlikKutusu'
import { api } from '../api/client'
import type { DemoKimlik } from '../api/types'

const KIMLIK: DemoKimlik = {
  parola: 'gosterim-parolasi',
  hesaplar: [
    { kullanici_adi: 'demo_idare', rol: 'idare', aciklama: 'Çizelgeyi kuran rol' },
    { kullanici_adi: 'demo_hesap', rol: 'hesap_yoneticisi', aciklama: 'Hesapları yönetir' },
    { kullanici_adi: 'demo_d1010', rol: 'calisan', aciklama: 'Kotası dolmaya yakın' },
    { kullanici_adi: 'demo_d1020', rol: 'calisan', aciklama: 'Ortalama yüklü' },
  ],
}

describe('DemoKimlikKutusu', () => {
  beforeEach(() => {
    cleanup()
    vi.restoreAllMocks()
  })

  it('uç nokta 404 dönerse hiçbir kimlik bilgisi göstermez', async () => {
    vi.spyOn(api, 'demoKimlik').mockRejectedValue(new Error('404'))

    const { container } = render(<DemoKimlikKutusu doldur={() => {}} />)

    await waitFor(() => expect(api.demoKimlik).toHaveBeenCalled())
    expect(container.innerHTML).toBe('')
  })

  it('üç rolü de ayrı ayrı listeler', async () => {
    vi.spyOn(api, 'demoKimlik').mockResolvedValue(KIMLIK)

    render(<DemoKimlikKutusu doldur={() => {}} />)

    await screen.findByText('İdare')
    expect(screen.getByText('Hesap yöneticisi')).toBeTruthy()
    expect(screen.getByText('Çalışan')).toBeTruthy()
    // Sistem yöneticisi sunucudan HİÇ gelmez; ekranda da başlığı olmamalı.
    expect(screen.queryByText('Sistem yöneticisi')).toBeNull()
  })

  it('bir satıra tıklamak formu o hesapla doldurur', async () => {
    vi.spyOn(api, 'demoKimlik').mockResolvedValue(KIMLIK)
    const doldur = vi.fn()

    render(<DemoKimlikKutusu doldur={doldur} />)
    fireEvent.click(await screen.findByText('demo_d1010'))

    expect(doldur).toHaveBeenCalledWith('demo_d1010', 'gosterim-parolasi')
  })

  it('parola paketten değil yanıttan gelir', async () => {
    // Aynı bileşen farklı bir parolayla farklı bir değer göstermeli;
    // gömülü olsaydı yanıt değişse de ekran değişmezdi.
    vi.spyOn(api, 'demoKimlik').mockResolvedValue({ ...KIMLIK, parola: 'bambaska-parola' })

    render(<DemoKimlikKutusu doldur={() => {}} />)

    expect(await screen.findByText('bambaska-parola')).toBeTruthy()
  })
})
