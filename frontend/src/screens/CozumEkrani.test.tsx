import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { CozumIsi } from '../api/types'
import { AktifIsSaglayici } from '../components/AktifIsBaglami'
import { OturumBaglami } from '../components/OturumBaglami'
import { CozumEkrani } from './CozumEkrani'

const DONEM = {
  donem_id: 1,
  baslangic_tarihi: '2026-04-06',
  bitis_tarihi: '2026-04-12',
  tercih_son_tarihi: '2026-03-30',
}

const DURDURULMUS: CozumIsi = {
  is_id: 7,
  surum_id: 3,
  durum: 'durduruldu',
  baslangic_zamani: '2026-04-01T10:00:00Z',
  bitis_zamani: '2026-04-01T10:02:00Z',
  sure_saniye: '120.000',
  zaman_limiti_saniye: 300,
  en_iyi_ceza: '912.00',
  ceza_dokumu: { S1: 0, S4: 12 },
  hata_mesaji: null,
  devam_kaynagi_is_id: null,
  kullanilabilir_sonuc_var: true,
  gecici_kapsama_acigi_sayisi: 2,
}

/** Ekranın ve kabuğun açılışta çektiği verileri karşılayan sahte fetch. */
function fetchSahtesi(aktifIs: CozumIsi | null) {
  return vi.fn(async (yol: string) => {
    const govde = yol.startsWith('/api/cozum/aktif')
      ? aktifIs
      : yol.startsWith('/api/donem')
        ? [DONEM]
        : []
    return { ok: true, status: 200, json: async () => govde }
  })
}

function ekraniAc(aktifIs: CozumIsi | null) {
  vi.stubGlobal('fetch', fetchSahtesi(aktifIs))
  return render(
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
        <CozumEkrani ekranSec={vi.fn()} donemId={1} donemIdSec={vi.fn()} />
      </AktifIsSaglayici>
    </OturumBaglami.Provider>,
  )
}

beforeEach(() => {
  vi.stubGlobal('confirm', vi.fn(() => true))
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('CozumEkrani — karar paneli (SDD 6.3.2)', () => {
  it('durdurulan işte üç seçeneği de sunar', async () => {
    ekraniAc(DURDURULMUS)
    await waitFor(() => expect(screen.getByText('KARAR BEKLENİYOR')).toBeDefined())

    expect(screen.getByRole('button', { name: 'Sonucu kullan' })).toBeDefined()
    expect(screen.getByRole('button', { name: 'Sonucu at' })).toBeDefined()
    expect(screen.getByRole('button', { name: 'Bu çözümden devam et' })).toBeDefined()
  })

  it('çözüm tamamlanmış gibi tam ayrıntı gösterir', async () => {
    // Kullanıcı kararını buna bakarak veriyor; toplam ceza, hedef bazında
    // döküm ve kapsama açığı sayısı panelde olmak zorunda.
    const { container } = ekraniAc(DURDURULMUS)
    await waitFor(() => expect(screen.getByText('KARAR BEKLENİYOR')).toBeDefined())

    expect(container.textContent).toContain('912.00')
    expect(container.textContent).toContain('S4')
    expect(screen.getByText('KAPSAMA AÇIĞI')).toBeDefined()
  })

  it('hedefleri ADIYLA listeler, yalnız kimlikle değil', async () => {
    // "S1, S4" tek başına yalnız kural kataloğunu ezbere bilene bir şey
    // söylüyordu; kimlik yine durur, çünkü katalogla ve dışa aktarmayla
    // eşleşmesi gereken şey odur.
    const { container } = ekraniAc(DURDURULMUS)
    await waitFor(() => expect(screen.getByText('KARAR BEKLENİYOR')).toBeDefined())

    expect(container.textContent).toContain('kapsama açığı')
    expect(container.textContent).toContain('toplam saat dengesi')
  })

  it('"kaldığı yerden devam" DEMEZ', async () => {
    // Çözücü sonlandırıldıktan sonra iç arama durumu geri yüklenemez;
    // devam, yeni bir aramanın ipucuyla başlatılmasıdır (SDD 5.4.1).
    const { container } = ekraniAc(DURDURULMUS)
    await waitFor(() => expect(screen.getByText('KARAR BEKLENİYOR')).toBeDefined())

    expect(container.textContent).not.toMatch(/kaldığı yerden/i)
    expect(container.textContent).toMatch(/yeni bir arama/i)
    expect(container.textContent).toMatch(/süre sıfırdan işler/i)
  })

  it('çözüm bulunamadıysa "kullan" pasif ve nedeni yazılı', async () => {
    const { container } = ekraniAc({
      ...DURDURULMUS,
      en_iyi_ceza: null,
      ceza_dokumu: null,
      kullanilabilir_sonuc_var: false,
      gecici_kapsama_acigi_sayisi: null,
      hata_mesaji: 'Çözücü ilk uygun çizelgeye ulaşmadan durduruldu.',
    })
    await waitFor(() => expect(screen.getByText('KARAR BEKLENİYOR')).toBeDefined())

    const kullan = screen.getByRole('button', { name: 'Sonucu kullan' }) as HTMLButtonElement
    expect(kullan.disabled).toBe(true)
    expect(container.textContent).toContain('ulaşmadan durduruldu')
  })

  it('sayaç ARAMANIN süresinde donar, karar beklerken işlemez', async () => {
    // `bitis_zamani` aramanın bittiği anı taşır (SDD 4.2.4) ve karar
    // sonradan verildiğinde değişmez. Sayaç karar beklerken işlemeye devam
    // ederse kullanıcının düşünme süresi aramanın süresine eklenir.
    // Fikstür 10:00:00 → 10:02:00 arası, yani tam iki dakika; "şimdi"nin
    // ne olduğundan bağımsız olarak 02:00 görünmeli.
    ekraniAc(DURDURULMUS)
    await waitFor(() => expect(screen.getByText('KARAR BEKLENİYOR')).toBeDefined())

    // İki yerde birden görünür: karar panelindeki "Geçen Süre" ve üst
    // çubuktaki gösterge. İkisi de aynı kaynaktan beslendiği için ikisi de
    // donmuş olmalı.
    expect(screen.getAllByText('02:00').length).toBe(2)
  })

  it('karar beklerken yeni çözüm başlatılamaz', async () => {
    // Başlatılabilseydi, karar bekleyen iş göstergeden düşer ve kullanıcı
    // bir daha ona dönemezdi: iş kararı verilmeden askıda kalırdı.
    ekraniAc(DURDURULMUS)
    await waitFor(() => expect(screen.getByText('KARAR BEKLENİYOR')).toBeDefined())

    const baslat = screen.getByRole('button', { name: 'Çözümü Başlat' }) as HTMLButtonElement
    expect(baslat.disabled).toBe(true)
  })
})

describe('Çalışan iş göstergesi (SRS FR-4.11)', () => {
  it('iş kimliğini SUNUCUDAN alır, istemcide tutmaz', async () => {
    // Ekran hiçbir yerde iş kimliği taşımıyor: kabuk /api/cozum/aktif
    // soruyor ve kimlik yanıtın içinden geliyor. Bu yüzden ekran
    // değiştirmek, sayfayı yenilemek veya başka bir cihazdan girmek
    // göstergeyi kaybettirmiyor.
    const sahte = fetchSahtesi(DURDURULMUS)
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
          <CozumEkrani ekranSec={vi.fn()} donemId={1} donemIdSec={vi.fn()} />
        </AktifIsSaglayici>
      </OturumBaglami.Provider>,
    )

    await waitFor(() =>
      expect(sahte.mock.calls.some(([yol]) => String(yol) === '/api/cozum/aktif')).toBe(true),
    )
    // Kimliği adreste taşıyan bir istek YOK: kabuk işi adıyla değil,
    // "aktif iş var mı" sorusuyla buluyor.
    expect(sahte.mock.calls.every(([yol]) => !String(yol).startsWith('/api/cozum/7'))).toBe(true)

    // Gösterge üst çubukta: durum her ekranda görünür.
    await waitFor(() => expect(screen.getByTitle('Çözüm ekranını aç')).toBeDefined())
    expect(screen.getByTitle('Çözüm ekranını aç').textContent).toContain('Karar bekliyor')
  })
})
