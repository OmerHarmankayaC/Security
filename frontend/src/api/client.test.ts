/**
 * İkili dosya indirme yolu (FR-8.5, FR-8.9).
 *
 * Excel çıktısı `istek` üzerinden geçemez — o gövdeyi JSON diye çözer.
 * Ayrı bir yol açmak, 401 ele alışının ve dosya adının o yolda unutulması
 * riskini doğurur; bu dosya ikisini de kilitler.
 */
import { afterEach, describe, expect, it, vi } from 'vitest'
import { api, oturumDustugunde } from './client'

function yanitKur(
  govde: { durum?: number; bildirim?: string | null } = {},
): { tiklananAd: () => string } {
  const { durum = 200, bildirim = null } = govde
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: durum >= 200 && durum < 300,
      status: durum,
      headers: { get: (ad: string) => (ad === 'Content-Disposition' ? bildirim : null) },
      blob: async () => new Blob(['xx']),
    }),
  )
  vi.stubGlobal('URL', {
    createObjectURL: () => 'blob:sahte',
    revokeObjectURL: () => undefined,
  })
  let ad = ''
  vi.spyOn(document, 'createElement').mockReturnValue({
    set download(v: string) {
      ad = v
    },
    href: '',
    click: () => undefined,
  } as unknown as HTMLAnchorElement)
  return { tiklananAd: () => ad }
}

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
  oturumDustugunde(null)
})

describe('Excel indirme', () => {
  it('dosya adını SUNUCUNUN başlığından alır', async () => {
    // Ad iki yerde tanımlanmamalı: sunucu `dosya_adi()` ile kuruyor.
    const { tiklananAd } = yanitKur({
      bildirim: 'attachment; filename="cizelge_surum7.xlsx"',
    })
    await api.cizelgeExcelIndir(42, 7)
    expect(tiklananAd()).toBe('cizelge_surum7.xlsx')
  })

  it('başlık yoksa yedek ada düşer, indirme yine de olur', async () => {
    const { tiklananAd } = yanitKur({ bildirim: null })
    await api.analizExcelIndir(42, 3)
    expect(tiklananAd()).toBe('analiz_surum3.xlsx')
  })

  it('401 oturum düştü dinleyicisini tetikler', async () => {
    // Bu atlanırsa kullanıcı, oturumu kapandığı hâlde sessizce inmeyen bir
    // dosyayla baş başa kalır ve nedenini göremez.
    yanitKur({ durum: 401 })
    const dinleyici = vi.fn()
    oturumDustugunde(dinleyici)
    await expect(api.cizelgeExcelIndir(1, 1)).rejects.toThrow()
    expect(dinleyici).toHaveBeenCalledOnce()
  })
})
