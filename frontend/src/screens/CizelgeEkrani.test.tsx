import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { CizelgeSurumu, Donem, DogrulamaSonucu, GorevNoktasi, Personel } from '../api/types'
import { AktifIsSaglayici } from '../components/AktifIsBaglami'
import { OturumBaglami } from '../components/OturumBaglami'
import { CizelgeEkrani } from './CizelgeEkrani'

const DONEM: Donem = {
  donem_id: 1,
  baslangic_tarihi: '2026-04-06',
  bitis_tarihi: '2026-04-12',
  tercih_son_tarihi: '2026-03-30',
}

const PERSONEL: Personel = {
  personel_id: 5,
  ad_soyad: 'Ayşe Yılmaz',
  sicil_no: '1005',
  haftalik_hedef_saat: 40,
  aktif_baslangic: '2026-01-01',
  aktif_bitis: null,
  yetkinlik_idleri: [],
  devir_fazla_calisma_saat: '0',
  kota_yili: null,
}

function surum(surumId: number, surumNo: number, durum: CizelgeSurumu['durum']): CizelgeSurumu {
  return {
    surum_id: surumId,
    donem_id: 1,
    surum_no: surumNo,
    durum,
    onceki_surum_id: null,
    yayin_zamani: null,
    olusturma_zamani: '2026-04-01T00:00:00Z',
    guncelleme_zamani: '2026-04-01T00:00:00Z',
    damga: `damga-${surumId}`,
    toplam_ceza: null,
    kapsama_acigi_sayisi: 0,
    fazla_kadro_sayisi: 0,
  }
}

const NOKTA: GorevNoktasi = {
  nokta_id: 1,
  ad: 'Ana Kapı',
  bina_id: null,
  onkosul_yetkinlik_id: null,
  aktif: true,
}

const DOGRULAMA_BOS: DogrulamaSonucu = {
  kabul_edilebilir: true,
  zorunlu_ihlaller: [],
  ceza_degisimi: 0,
  agirlikli_ceza_degisimi: 0,
  ceza_dokumu: [],
  uyarilar: [],
}

/** Ekranın açılışta çektiği tüm tanım/sürüm verilerini karşılayan sahte fetch. */
function fetchSahtesi(surumler: CizelgeSurumu[], sonrakiSurum?: CizelgeSurumu) {
  return vi.fn(async (yol: string, secenekler?: RequestInit) => {
    const yontem = secenekler?.method ?? 'GET'

    if (yol.startsWith('/api/donem')) return yanit([DONEM])
    if (yol.startsWith('/api/personel')) return yanit([PERSONEL])
    if (yol.startsWith('/api/nokta')) return yanit([])
    if (yol.startsWith('/api/yetkinlik')) return yanit([])
    if (yol.startsWith('/api/kural')) return yanit([])
    if (yol.startsWith('/api/cozum/aktif')) return yanit(null)
    if (yol.startsWith('/api/analiz/')) return yanit(null)
    if (/^\/api\/surum\/\d+\/atama/.test(yol)) return yanit([])
    if (/^\/api\/surum\/\d+\/kapsama-acigi/.test(yol)) return yanit([])
    if (/^\/api\/surum\/\d+\/fazla-kadro/.test(yol)) return yanit([])
    if (yol === '/api/surum' && yontem === 'POST') {
      if (!sonrakiSurum) throw new Error('bosTaslakAc bu testte beklenmiyordu')
      return yanit(sonrakiSurum)
    }
    if (yol.startsWith('/api/surum?donem_id=')) return yanit(surumler)
    throw new Error(`fetchSahtesi: bilinmeyen yol ${yol}`)
  })
}

function yanit(govde: unknown) {
  return { ok: true, status: 200, json: async () => govde }
}

function ekraniAc(surumler: CizelgeSurumu[], donemId: number | null = 1, sonrakiSurum?: CizelgeSurumu) {
  const sahte = fetchSahtesi(surumler, sonrakiSurum)
  vi.stubGlobal('fetch', sahte)
  const donemIdSec = vi.fn()
  const sonuc = render(
    <OturumBaglami.Provider
      value={{
        ben: {
          kullanici_adi: 'idare',
          ad_soyad: 'Yönetici',
          rol: 'idare',
          personel_id: null,
          parola_degistirmeli: false,
        },
        cikis: vi.fn(),
        parolaDegistir: vi.fn(),
      }}
    >
      <AktifIsSaglayici>
        <CizelgeEkrani
          ekranSec={vi.fn()}
          donemId={donemId}
          donemIdSec={donemIdSec}
          yenidenCozIste={vi.fn()}
        />
      </AktifIsSaglayici>
    </OturumBaglami.Provider>,
  )
  return { ...sonuc, sahte, donemIdSec }
}

beforeEach(() => {
  vi.stubGlobal('confirm', vi.fn(() => true))
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('"Boş Taslak Aç" düğmesi (FR-7.3)', () => {
  it('dönem seçili değilse pasiftir', async () => {
    ekraniAc([], null)
    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'Boş Taslak Aç' })).toBeDefined(),
    )
    const dugme = screen.getByRole('button', { name: 'Boş Taslak Aç' }) as HTMLButtonElement
    expect(dugme.disabled).toBe(true)
  })

  it('dönemde sürüm varken basınca sayıyla confirm sorar', async () => {
    ekraniAc([surum(1, 1, 'yayinlandi')])
    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'Boş Taslak Aç' })).toBeDefined(),
    )

    const dugme = screen.getByRole('button', { name: 'Boş Taslak Aç' }) as HTMLButtonElement
    await waitFor(() => expect(dugme.disabled).toBe(false))
    dugme.click()

    expect(window.confirm).toHaveBeenCalledWith(
      'Dönemde 1 sürüm var; 2. sürüm boş bir taslak olarak açılacak.',
    )
  })

  it('onaylanınca /api/surum isteği donem_id gövdesiyle gider', async () => {
    const yeni = surum(9, 2, 'taslak')
    const { sahte } = ekraniAc([surum(1, 1, 'yayinlandi')], 1, yeni)
    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'Boş Taslak Aç' })).toBeDefined(),
    )
    const dugme = screen.getByRole('button', { name: 'Boş Taslak Aç' }) as HTMLButtonElement
    await waitFor(() => expect(dugme.disabled).toBe(false))
    dugme.click()

    await waitFor(() => {
      const istek = sahte.mock.calls.find(
        ([yol, secenekler]) =>
          String(yol) === '/api/surum' && (secenekler as RequestInit | undefined)?.method === 'POST',
      )
      expect(istek).toBeDefined()
      expect(JSON.parse(String((istek![1] as RequestInit).body))).toEqual({ donem_id: 1 })
    })
  })

  it('iptal edilince istek gitmez', async () => {
    vi.stubGlobal('confirm', vi.fn(() => false))
    const { sahte } = ekraniAc([surum(1, 1, 'yayinlandi')])
    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'Boş Taslak Aç' })).toBeDefined(),
    )
    const dugme = screen.getByRole('button', { name: 'Boş Taslak Aç' }) as HTMLButtonElement
    await waitFor(() => expect(dugme.disabled).toBe(false))
    dugme.click()

    expect(window.confirm).toHaveBeenCalled()
    expect(
      sahte.mock.calls.some(
        ([yol, secenekler]) =>
          String(yol) === '/api/surum' && (secenekler as RequestInit | undefined)?.method === 'POST',
      ),
    ).toBe(false)
  })

  it('dönemde sürüm yokken confirm sormadan doğrudan açar', async () => {
    const yeni = surum(9, 1, 'taslak')
    const { sahte } = ekraniAc([], 1, yeni)
    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'Boş Taslak Aç' })).toBeDefined(),
    )
    const dugme = screen.getByRole('button', { name: 'Boş Taslak Aç' }) as HTMLButtonElement
    await waitFor(() => expect(dugme.disabled).toBe(false))
    dugme.click()

    expect(window.confirm).not.toHaveBeenCalled()
    await waitFor(() => {
      const istek = sahte.mock.calls.find(
        ([yol, secenekler]) =>
          String(yol) === '/api/surum' && (secenekler as RequestInit | undefined)?.method === 'POST',
      )
      expect(istek).toBeDefined()
    })
  })

  it('kaydedilmemiş bir değişiklik varken pasiftir ve tıklama istek üretmez', async () => {
    // Ekranın diğer kontrolleri (dönem/sürüm seçici, "Yeniden Çöz") kirli bir
    // oturumda aynı desenle pasifleşiyor — bu düğme de aynı korumaya
    // ihtiyaç duyuyor: sürüm değişince oturum sessizce BOS_OTURUM'a döner ve
    // kaydedilmemiş değişiklik kaybolur.
    const sahte = vi.fn(async (yol: string, secenekler?: RequestInit) => {
      const yontem = secenekler?.method ?? 'GET'
      if (yol.startsWith('/api/donem')) return yanit([DONEM])
      if (yol.startsWith('/api/personel')) return yanit([PERSONEL])
      if (yol.startsWith('/api/nokta')) return yanit([NOKTA])
      if (yol.startsWith('/api/yetkinlik')) return yanit([])
      if (yol.startsWith('/api/kural')) return yanit([])
      if (yol.startsWith('/api/cozum/aktif')) return yanit(null)
      if (yol.startsWith('/api/analiz/')) return yanit(null)
      if (/^\/api\/surum\/\d+\/atama/.test(yol)) return yanit([])
      if (/^\/api\/surum\/\d+\/kapsama-acigi/.test(yol)) return yanit([])
      if (/^\/api\/surum\/\d+\/fazla-kadro/.test(yol)) return yanit([])
      if (yol === '/api/atama/dogrula' && yontem === 'POST') return yanit(DOGRULAMA_BOS)
      if (yol === '/api/surum' && yontem === 'POST') {
        throw new Error('bosTaslakAc bu testte beklenmiyordu — düğme pasif olmalı')
      }
      if (yol.startsWith('/api/surum?donem_id=')) return yanit([surum(1, 1, 'taslak')])
      throw new Error(`beklenmeyen yol ${yol}`)
    })
    vi.stubGlobal('fetch', sahte)
    render(
      <OturumBaglami.Provider
        value={{
          ben: {
            kullanici_adi: 'idare',
            ad_soyad: 'Yönetici',
            rol: 'idare',
            personel_id: null,
            parola_degistirmeli: false,
          },
          cikis: vi.fn(),
          parolaDegistir: vi.fn(),
        }}
      >
        <AktifIsSaglayici>
          <CizelgeEkrani
            ekranSec={vi.fn()}
            donemId={1}
            donemIdSec={vi.fn()}
            yenidenCozIste={vi.fn()}
          />
        </AktifIsSaglayici>
      </OturumBaglami.Provider>,
    )

    // Izgara (taslak sürüm, kadrolu personel) hücreleri kurulana kadar bekle.
    await waitFor(() => expect(document.querySelector('[data-saat="8"]')).not.toBeNull())
    const saatHucresi = (saat: number): Element => {
      const hucre = document.querySelector(`[data-saat="${saat}"]`)
      if (!hucre) throw new Error(`Saat hücresi bulunamadı: ${saat}`)
      return hucre
    }

    const dugme = screen.getByRole('button', { name: 'Boş Taslak Aç' }) as HTMLButtonElement
    await waitFor(() => expect(dugme.disabled).toBe(false))

    // 08.00–16.00 bloğu sürükleyerek çiz: oturum kirlenir.
    fireEvent.pointerDown(saatHucresi(8))
    fireEvent.pointerEnter(saatHucresi(15))
    fireEvent.pointerUp(saatHucresi(15))

    await waitFor(() => expect(screen.getByText(/KAYDEDİLMEMİŞ/)).toBeDefined())
    await waitFor(() => expect(dugme.disabled).toBe(true))
    expect(dugme.title).toBe('Önce değişiklikleri kaydedin ya da vazgeçin')

    const cagriSayisiOnce = sahte.mock.calls.length
    dugme.click()
    // Pasif düğme tıklamayı hiç üretmemeli — çağrı sayısı değişmez.
    expect(sahte.mock.calls.length).toBe(cagriSayisiOnce)
  })
})

describe('boş hâl metni', () => {
  it('düzenlenebilir sürümde kadroda personel yoksa ayrı metin gösterir', async () => {
    // Taslak sürüm ama kadroda bu dönemde aktif personel yok: satır kaynağı
    // artık kadro olduğu için eski "atama yok" metni burada YANLIŞ olurdu.
    const sahte = vi.fn(async (yol: string) => {
      if (yol.startsWith('/api/donem')) return yanit([DONEM])
      if (yol.startsWith('/api/personel')) return yanit([])
      if (yol.startsWith('/api/nokta')) return yanit([])
      if (yol.startsWith('/api/yetkinlik')) return yanit([])
      if (yol.startsWith('/api/kural')) return yanit([])
      if (yol.startsWith('/api/cozum/aktif')) return yanit(null)
      if (yol.startsWith('/api/analiz/')) return yanit(null)
      if (/^\/api\/surum\/\d+\/atama/.test(yol)) return yanit([])
      if (/^\/api\/surum\/\d+\/kapsama-acigi/.test(yol)) return yanit([])
      if (/^\/api\/surum\/\d+\/fazla-kadro/.test(yol)) return yanit([])
      if (yol.startsWith('/api/surum?donem_id=')) return yanit([surum(1, 1, 'taslak')])
      throw new Error(`beklenmeyen yol ${yol}`)
    })
    vi.stubGlobal('fetch', sahte)
    render(
      <OturumBaglami.Provider
        value={{
          ben: {
            kullanici_adi: 'idare',
            ad_soyad: 'Yönetici',
            rol: 'idare',
            personel_id: null,
            parola_degistirmeli: false,
          },
          cikis: vi.fn(),
          parolaDegistir: vi.fn(),
        }}
      >
        <AktifIsSaglayici>
          <CizelgeEkrani
            ekranSec={vi.fn()}
            donemId={1}
            donemIdSec={vi.fn()}
            yenidenCozIste={vi.fn()}
          />
        </AktifIsSaglayici>
      </OturumBaglami.Provider>,
    )

    await waitFor(() =>
      expect(
        screen.getByText('Bu dönemde aktif personel yok; Tanımlar ekranından personel ekleyin.'),
      ).toBeDefined(),
    )
  })
})
