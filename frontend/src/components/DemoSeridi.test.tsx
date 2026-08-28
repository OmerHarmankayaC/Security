// Gösterim şeridinin sözleşmesi (Demo Senaryosu 10).
//
// Üç iddia, üçü de şeridin işini yapıp yapmadığına dair:
//
//   1. Ayar kapalıyken hiçbir şey çizilmez — gerçek bir kurulum kendini
//      gösterim ortamı ilan etmez.
//   2. Ayar açıkken şerit iki şeyi de söyler: verinin üretilmiş olduğunu
//      ve her gece kaybolduğunu.
//   3. Uç nokta hata verirse şerit ÇİZİLMEZ. "Emin olamadım" hâli, gerçek
//      bir kurulumda yanlış beyandır.
import { render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { DemoSeridi } from './DemoSeridi'
import { api } from '../api/client'

describe('DemoSeridi', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('ayar kapalıyken hiçbir şey çizmez', async () => {
    vi.spyOn(api, 'ortam').mockResolvedValue({ demo_kipi: false })

    const { container } = render(<DemoSeridi />)

    await waitFor(() => expect(api.ortam).toHaveBeenCalled())
    expect(container.innerHTML).toBe('')
  })

  it('ayar açıkken üç şeyi de söyler: üretilmişlik, gecelik sıfırlama, kullanımda olmayış', async () => {
    vi.spyOn(api, 'ortam').mockResolvedValue({ demo_kipi: true })

    render(<DemoSeridi />)

    const serit = await screen.findByRole('status')
    expect(serit.textContent).toContain('üretilmiştir')
    expect(serit.textContent).toContain('her gece sıfırlanır')
    expect(serit.textContent).toContain('kullanımda değildir')
  })

  it('uç nokta hata verdiğinde şerit çizilmez', async () => {
    vi.spyOn(api, 'ortam').mockRejectedValue(new Error('ağ hatası'))

    const { container } = render(<DemoSeridi />)

    await waitFor(() => expect(api.ortam).toHaveBeenCalled())
    expect(container.innerHTML).toBe('')
  })
})
