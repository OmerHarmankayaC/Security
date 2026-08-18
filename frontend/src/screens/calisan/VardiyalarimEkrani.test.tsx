import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import type { Vardiyalarim } from '@/api/types'

import { VardiyalarimEkrani } from './VardiyalarimEkrani'

function vardiya(tarih: string, noktaAd: string) {
  return {
    tarih,
    baslangic_zamani: `${tarih}T08:00:00`,
    bitis_zamani: `${tarih}T16:00:00`,
    sure_saat: 8,
    gece_saati: 0,
    nokta_id: 1,
    nokta_ad: noktaAd,
    degisim_tipi: null,
  }
}

const VERI = {
  donem_id: 1,
  donem_baslangic_tarihi: '2026-08-17',
  donem_bitis_tarihi: '2026-08-18',
  yayinlanmis_surum_var: true,
  yayin_zamani: null,
  // Çakışan iki ad: ikisi de kisalt() ile "GÜV" verir (bkz. metin.test.ts).
  vardiyalar: [vardiya('2026-08-17', 'Güvenlik'), vardiya('2026-08-18', 'Güvence')],
  kaldirilan_gunler: [],
  siradaki: null,
} as unknown as Vardiyalarim

afterEach(cleanup)

describe('VardiyalarimEkrani', () => {
  it('aynı üç harfe düşen iki noktayı ızgarada ayrıştırır', () => {
    render(<VardiyalarimEkrani veri={VERI} />)
    // İkisi de "GÜV" görünseydi çalışan hangi noktaya gittiğini okuyamazdı.
    const hucreler = screen.getAllByText(/^GÜV/)
    expect(new Set(hucreler.map((h) => h.textContent)).size).toBe(2)
  })

  it('kaldırılan günü kendi satırı olarak gösterir', () => {
    const veri = {
      ...VERI,
      kaldirilan_gunler: [
        {
          tarih: '2026-08-18',
          onceki_baslangic_zamani: '2026-08-18T08:00:00',
          onceki_bitis_zamani: '2026-08-18T16:00:00',
          onceki_nokta_ad: 'Güvence',
        },
      ],
    } as unknown as Vardiyalarim
    render(<VardiyalarimEkrani veri={veri} />)
    // Rozet, çocuklarını buyukHarf() ile Türkçe büyütür (Kaldırıldı → KALDIRILDI);
    // sorgu gerçek DOM çıktısına göre — İ/ı bozulmasın diye .toUpperCase()
    // değil buyukHarf() kullanılıyor ve regex /i bunu doğru katlamıyor. Rozet
    // mobil/masaüstü için iki kopya render eder (CSS ile gizlenir), bu yüzden
    // getAllByText.
    expect(screen.getAllByText('KALDIRILDI').length).toBeGreaterThan(0)
  })
})
