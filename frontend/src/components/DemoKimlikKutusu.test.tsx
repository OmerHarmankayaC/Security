// Gösterim kimlik kutusunun sözleşmesi (Demo Senaryosu 7).
//
// Asıl iddia OLUMSUZ: gerçek bir kurulumda uç nokta yoktur (404) ve ekranda
// hiçbir kullanıcı adı, hiçbir parola görünmez. Bu testin düşmesi, demoya
// ait kimlik bilgisinin üretim ekranına sızdığı anlamına gelir.
import { cleanup, fireEvent, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { DemoKimlikKutusu } from './DemoKimlikKutusu'
import { api } from '../api/client'
import type { DemoKimlik } from '../api/types'
import { ciz } from '@/test/ciz'

// Parolalar hesap başına AYRI; testin tamamı bu ayrımın üstünde duruyor.
const KIMLIK: DemoKimlik = {
  hesaplar: [
    {
      kullanici_adi: 'demo_idare',
      rol: 'idare',
      aciklama: 'Çizelgeyi kuran rol',
      parola: 'aaa111bbb222',
    },
    {
      kullanici_adi: 'demo_hesap',
      rol: 'hesap_yoneticisi',
      aciklama: 'Hesapları yönetir',
      parola: 'ccc333ddd444',
    },
    {
      kullanici_adi: 'demo_d1010',
      rol: 'calisan',
      aciklama: 'Kotası dolmaya yakın',
      parola: 'eee555fff666',
    },
    {
      kullanici_adi: 'demo_d1020',
      rol: 'calisan',
      aciklama: 'Ortalama yüklü',
      parola: 'ggg777hhh888',
    },
  ],
}

describe('DemoKimlikKutusu', () => {
  beforeEach(() => {
    cleanup()
    vi.restoreAllMocks()
  })

  it('uç nokta 404 dönerse hiçbir kimlik bilgisi göstermez', async () => {
    vi.spyOn(api, 'demoKimlik').mockRejectedValue(new Error('404'))

    const { container } = ciz(<DemoKimlikKutusu doldur={() => {}} />)

    await waitFor(() => expect(api.demoKimlik).toHaveBeenCalled())
    expect(container.innerHTML).toBe('')
  })

  it('üç rolü de etiketler ve her hesabın kendi parolasını yazar', async () => {
    vi.spyOn(api, 'demoKimlik').mockResolvedValue(KIMLIK)

    ciz(<DemoKimlikKutusu doldur={() => {}} />)

    await screen.findByText('İdare')
    expect(screen.getByText('Hesap yöneticisi')).toBeTruthy()
    expect(screen.getAllByText('Çalışan')).toHaveLength(2)
    // Sistem yöneticisi sunucudan HİÇ gelmez; ekranda da etiketi olmamalı.
    expect(screen.queryByText('Sistem yöneticisi')).toBeNull()
    for (const hesap of KIMLIK.hesaplar) {
      expect(screen.getByText(hesap.parola)).toBeTruthy()
    }
  })

  it('bir satıra tıklamak formu O HESABIN kendi parolasıyla doldurur', async () => {
    vi.spyOn(api, 'demoKimlik').mockResolvedValue(KIMLIK)
    const doldur = vi.fn()

    ciz(<DemoKimlikKutusu doldur={doldur} />)
    fireEvent.click(await screen.findByText('demo_d1010'))

    // Ortak bir parola değil, o satırın parolası gitmeli.
    expect(doldur).toHaveBeenCalledWith('demo_d1010', 'eee555fff666')
  })

  it('parolalar paketten değil yanıttan gelir', async () => {
    // Gömülü olsalardı yanıt değişse de ekran değişmezdi.
    const baska = {
      hesaplar: KIMLIK.hesaplar.map((h) => ({ ...h, parola: `x${h.parola.slice(1)}` })),
    }
    vi.spyOn(api, 'demoKimlik').mockResolvedValue(baska)

    ciz(<DemoKimlikKutusu doldur={() => {}} />)

    expect(await screen.findByText('xaa111bbb222')).toBeTruthy()
  })
})
