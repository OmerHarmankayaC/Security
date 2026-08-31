/**
 * Sürümler ekranının davranış testleri (SDD 6.3.5, FR-7.x).
 *
 * Buradaki konu ATAMASIZ SÜRÜMÜN YAYINLANAMAMASI. Senaryo: dönemde v3
 * yayında ve dolu; yönetici boş taslak (v4) açıp vazgeçiyor; sonra v4'ün
 * Yayınla düğmesine basıyor. Onay metni "Sürüm 3 arşive alınacak" diyor ama
 * v4'ün SIFIR ataması olduğunu söylemiyor — sonuç, çalışan panelinde
 * herkesin vardiyasının kaybolması.
 */
import { cleanup, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { CizelgeSurumu, Donem } from '../api/types'
import { SurumlerEkrani } from './SurumlerEkrani'
import { ciz } from '@/test/ciz'
import { SOZLUK } from '@/i18n/sozluk'

// AppShell oturum bağlamı ister ve bu testlerin konusu değil; çocuklarını
// döken bir kabukla değiştirilir (bkz. OzetEkrani.test.tsx).
vi.mock('../components/AppShell', () => ({
  AppShell: ({ children, aksiyonlar }: { children: unknown; aksiyonlar?: unknown }) => (
    <div>
      {aksiyonlar as never}
      {children as never}
    </div>
  ),
}))

const DONEM: Donem = {
  donem_id: 1,
  baslangic_tarihi: '2026-08-17',
  bitis_tarihi: '2026-08-23',
  tercih_son_tarihi: '2026-08-10',
}

function surum(ek: Partial<CizelgeSurumu>): CizelgeSurumu {
  return {
    surum_id: 3,
    donem_id: 1,
    surum_no: 3,
    durum: 'taslak',
    onceki_surum_id: null,
    yayin_zamani: null,
    olusturma_zamani: '2026-08-16T10:00:00Z',
    guncelleme_zamani: '2026-08-16T10:00:00Z',
    damga: 'damga-3',
    toplam_ceza: null,
    kapsama_acigi_sayisi: 0,
    fazla_kadro_sayisi: 0,
    atama_sayisi: 40,
    ...ek,
  }
}

let _surumler: CizelgeSurumu[] = []

vi.mock('../api/client', () => ({
  ApiHatasi: class ApiHatasi extends Error {},
  api: {
    donemler: () => Promise.resolve([DONEM]),
    surumler: () => Promise.resolve(_surumler),
    surumYayinla: () => Promise.resolve(undefined),
    surumAtamalari: () => Promise.resolve([]),
    surumTaslakTuret: () => Promise.resolve(undefined),
    surumTaslakOlarakKopyala: () => Promise.resolve(undefined),
    surumKarsilastir: () => Promise.resolve(undefined),
  },
}))

afterEach(cleanup)

function ekraniKur(surumler: CizelgeSurumu[]) {
  _surumler = surumler
  ciz(<SurumlerEkrani ekranSec={vi.fn()} donemId={1} donemIdSec={vi.fn()} />)
}

describe('Yayınla düğmesi — atamasız sürüm koruması', () => {
  it('atamasız sürümde PASİFTİR ve nedeni ekranda yazar', async () => {
    ekraniKur([
      surum({ surum_id: 4, surum_no: 4, durum: 'taslak', atama_sayisi: 0 }),
      surum({ surum_id: 3, surum_no: 3, durum: 'yayinlandi', atama_sayisi: 40 }),
    ])

    const yayinla = (await screen.findByRole('button', {
      name: 'Yayınla',
    })) as HTMLButtonElement
    expect(yayinla.disabled).toBe(true)
    // Neden EKRANDA durur, yalnız ipucunda değil.
    expect(screen.getByText(SOZLUK.tr.surumler.atamaYokYayinlanamaz)).toBeDefined()
    expect(yayinla.title).toContain('hiç atama yok')
  })

  it('ataması olan taslakta ETKİNDİR', async () => {
    ekraniKur([surum({ surum_id: 4, surum_no: 4, durum: 'taslak', atama_sayisi: 12 })])

    const yayinla = (await screen.findByRole('button', {
      name: 'Yayınla',
    })) as HTMLButtonElement
    expect(yayinla.disabled).toBe(false)
    expect(screen.queryByText(SOZLUK.tr.surumler.atamaYokYayinlanamaz)).toBeNull()
  })

  it('pasif düğme onay şeridini açmaz', async () => {
    ekraniKur([
      surum({ surum_id: 4, surum_no: 4, durum: 'taslak', atama_sayisi: 0 }),
      surum({ surum_id: 3, surum_no: 3, durum: 'yayinlandi', atama_sayisi: 40 }),
    ])

    const yayinla = await screen.findByRole('button', { name: 'Yayınla' })
    yayinla.click()
    // "Sürüm 3 arşive alınacak" onayı — kullanıcının gördüğü ve yanıltan
    // metin buydu; hiç açılmamalı.
    expect(screen.queryByText(/arşive alınacak/)).toBeNull()
    expect(screen.queryByRole('button', { name: /Onayla ve Yayınla/ })).toBeNull()
  })
})
