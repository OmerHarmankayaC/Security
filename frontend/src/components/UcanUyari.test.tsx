// Uçan uyarının sözleşmesi.
//
// Test SAHTE BİR DİNLEYİCİ KURMAZ; gerçek zinciri koşturur: `fetch` 403 +
// `salt_okunur` döndürür, api istemcisi dinleyiciyi çağırır, bileşen çizer.
// Dinleyiciyi doğrudan tetiklemek, kodun bu iki ucunu birbirine bağlayan
// kısmı — kod kontrolünü — sınamadan bırakırdı.
//
// Dört iddia: reddedilmeyen akışta bir şey çizilmez · reddedildiğinde
// sunucunun mesajı görünür · on saniye sonra kendiliğinden gider · çarpı
// sayacı beklemeden kapatır. Bir de aynı uyarının yığılmadığı.
import { act, cleanup, fireEvent, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { UcanUyari } from './UcanUyari'
import { api, ApiHatasi, SaltOkunurHatasi } from '../api/client'
import { ciz } from '@/test/ciz'

const MESAJ = 'Gösterim ortamı: değişiklikler kaydedilmez.'

function yanitVer(durum: number, govde: unknown) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => new Response(JSON.stringify(govde), { status: durum })),
  )
}

/** Bir yazma isteği atar ve reddedilmesini bekler. */
async function yazmayiDene() {
  await act(async () => {
    await api.cozumDurdur(1).catch(() => {})
  })
}

describe('UcanUyari', () => {
  beforeEach(() => {
    cleanup()
    vi.useFakeTimers({ shouldAdvanceTime: true })
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  it('reddetme gelmeden hiçbir şey çizmez', () => {
    const { container } = ciz(<UcanUyari />)

    expect(container.innerHTML).toBe('')
  })

  it('yazma reddedildiğinde sunucunun mesajını gösterir', async () => {
    yanitVer(403, { detail: MESAJ, kod: 'salt_okunur' })
    ciz(<UcanUyari />)

    await yazmayiDene()

    expect(screen.getByRole('status').textContent).toContain(MESAJ)
  })

  it('rol tabanlı 403 uyarı çıkarmaz', async () => {
    // Kod yok: bu ret gösterim ortamıyla ilgili değil, yetkiyle. Aynı
    // uyarıyı çıkarmak kullanıcıya yanlış nedeni gösterirdi.
    yanitVer(403, { detail: 'Bu işlem için yetkiniz yok.' })
    ciz(<UcanUyari />)

    await yazmayiDene()

    expect(screen.queryByRole('status')).toBeNull()
  })

  it('on saniye sonra kendiliğinden gider', async () => {
    yanitVer(403, { detail: MESAJ, kod: 'salt_okunur' })
    ciz(<UcanUyari />)
    await yazmayiDene()

    act(() => {
      vi.advanceTimersByTime(10_000)
    })

    expect(screen.queryByRole('status')).toBeNull()
  })

  it('çarpı sayacı beklemeden kapatır', async () => {
    yanitVer(403, { detail: MESAJ, kod: 'salt_okunur' })
    ciz(<UcanUyari />)
    await yazmayiDene()

    fireEvent.click(screen.getByLabelText('Uyarıyı kapat'))

    expect(screen.queryByRole('status')).toBeNull()
  })

  it('satır içi kopya çizilmesin diye hata mesajı boştur', async () => {
    // Ekranlar `e instanceof Error ? e.message : '…'` ile alıp
    // `{hata && <p>…}` ile çizer; boş mesaj o satırı atlatır ve açıklama
    // yalnızca uçan uyarıda kalır. Sunucunun metni `detay`da durur.
    yanitVer(403, { detail: MESAJ, kod: 'salt_okunur' })

    const hata = await api.cozumDurdur(1).catch((e) => e)

    expect(hata).toBeInstanceOf(SaltOkunurHatasi)
    expect(hata.message).toBe('')
    expect(hata.detay).toBe(MESAJ)
  })

  it('rol tabanlı 403 olağan hata olarak kalır', async () => {
    yanitVer(403, { detail: 'Bu işlem için yetkiniz yok.' })

    const hata = await api.cozumDurdur(1).catch((e) => e)

    expect(hata).toBeInstanceOf(ApiHatasi)
    expect(hata).not.toBeInstanceOf(SaltOkunurHatasi)
    expect(hata.message).toBe('Bu işlem için yetkiniz yok.')
  })

  it('arka arkaya gelen reddetmeler yığılmaz', async () => {
    yanitVer(403, { detail: MESAJ, kod: 'salt_okunur' })
    ciz(<UcanUyari />)

    await yazmayiDene()
    await yazmayiDene()
    await yazmayiDene()

    expect(screen.getAllByRole('status')).toHaveLength(1)
  })
})
