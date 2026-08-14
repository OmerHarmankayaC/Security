import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { Atama, GorevNoktasi, KapsamaAcigi, Personel } from '@/api/types'
import { gunlerListesi } from '@/lib/tarih'
import { HaftaSeridi } from './HaftaSeridi'

afterEach(cleanup)

/**
 * Hafta şeridi (Tur 6 İş 2).
 *
 * En önemli ölçü PERFORMANSTIR ve testle kilitlenir: mini şerit tek öğeyle
 * çizilmezse otuz personel × yedi gün × yirmi dört dilim beş binden fazla DOM
 * düğümü eder. Aşağıdaki test düğüm sayısını sayar; dilimler ayrı öğelere
 * bölünürse sayı bir anda büyür ve test düşer.
 */

const NOKTALAR = new Map<number, GorevNoktasi>([
  [1, { nokta_id: 1, ad: 'Güvenlik', bina_id: 1, onkosul_yetkinlik_id: 1, aktif: true }],
])

const GUNLER = gunlerListesi('2026-02-02', '2026-02-08')

function personel(id: number): Personel {
  return {
    personel_id: id,
    ad_soyad: `Personel ${String(id).padStart(2, '0')}`,
    sicil_no: `P-${String(id).padStart(3, '0')}`,
    haftalik_hedef_saat: 45,
    aktif_baslangic: '2026-01-01',
    aktif_bitis: null,
    yetkinlik_idleri: [1],
    devir_fazla_calisma_saat: '0',
    kota_yili: 2026,
  }
}

function blok(id: number, personelId: number, tarih: string, bas: number, sure: number): Atama {
  const bitGun = bas + sure >= 24 ? Number(tarih.slice(-2)) + 1 : Number(tarih.slice(-2))
  const bit = (bas + sure) % 24
  return {
    atama_id: id,
    personel_id: personelId,
    baslangic_zamani: `${tarih}T${String(bas).padStart(2, '0')}:00:00+03:00`,
    bitis_zamani: `${tarih.slice(0, 8)}${String(bitGun).padStart(2, '0')}T${String(bit).padStart(2, '0')}:00:00+03:00`,
    tarih,
    sure_saat: sure,
    nokta_id: 1,
    kilitli: false,
    kaynak: 'cozucu',
  }
}

const VARSAYILAN = {
  gunler: GUNLER,
  noktaMap: NOKTALAR,
  kapsamaAcigi: [] as KapsamaAcigi[],
  bugun: '2026-02-04',
  onGunSec: () => {},
}

describe('İş 2 kabul — yedi gün, otuz personel akıcı açılıyor', () => {
  it('mini şerit TEK ÖĞEDİR: hücre başına düşen düğüm sayısı dilim sayısından bağımsızdır', () => {
    const personeller = Array.from({ length: 30 }, (_, i) => personel(i + 1))
    const atamalar = personeller.flatMap((p, i) =>
      GUNLER.map((g, j) => blok(p.personel_id * 100 + j, p.personel_id, g, 6 + (i % 12), 8)),
    )

    const { container } = render(
      <HaftaSeridi {...VARSAYILAN} personeller={personeller} atamalar={atamalar} />,
    )

    const dugumSayisi = container.querySelectorAll('*').length
    // 30 × 7 = 210 hücre. Hücre başına düşen düğüm SABİTTİR: metin, ray ve
    // en çok iki çubuk. Her dilim ayrı düğüm olsaydı yalnız dilimler
    // 210 × 24 = 5.040 düğüm ederdi.
    //
    // Sınır Tur 7'de 1.000'den 2.000'e çıkarıldı: hücre artık tek bir
    // gradient öğesi değil, metin + ray + çubuk taşıyor (ölçülen ~1.400).
    // Testin koruduğu şey bugünkü sayı değil, sayının DİLİM SAYISINDAN
    // BAĞIMSIZ kalmasıdır; dilim başına düğüme dönülürse sınır aşılır.
    expect(dugumSayisi).toBeLessThan(2000)
    // Hücreler gerçekten çizilmiş olmalı — boş bir tablo da testi geçerdi.
    expect(container.querySelectorAll('td button')).toHaveLength(210)
  })

  it('bir gün hücresine tıklandığında o günün ızgarasına geçilir', () => {
    const onGunSec = vi.fn()
    render(
      <HaftaSeridi
        {...VARSAYILAN}
        personeller={[personel(1)]}
        atamalar={[blok(1, 1, '2026-02-03', 8, 8)]}
        onGunSec={onGunSec}
      />,
    )
    fireEvent.click(screen.getByLabelText(/3 Şubat 2026 08.00–16\.00 · Güvenlik/))
    expect(onGunSec).toHaveBeenCalledWith('2026-02-03')
  })

  it('gün başlığından da ızgaraya geçilir', () => {
    const onGunSec = vi.fn()
    render(
      <HaftaSeridi {...VARSAYILAN} personeller={[personel(1)]} atamalar={[]} onGunSec={onGunSec} />,
    )
    fireEvent.click(screen.getByTitle('4 Şubat 2026 — gün ızgarasına geç'))
    expect(onGunSec).toHaveBeenCalledWith('2026-02-04')
  })
})

describe('gece yarısını aşan blok şeritte de tek bloktur', () => {
  it('iki günün hücresinde de aynı aralığı yazar ve nereden geldiğini söyler', () => {
    render(
      <HaftaSeridi
        {...VARSAYILAN}
        personeller={[personel(1)]}
        atamalar={[blok(1, 1, '2026-02-03', 20, 10)]}
      />,
    )
    expect(screen.getByLabelText(/3 Şubat 2026 20.00–06\.00 · Güvenlik \(ertesi güne\)/)).toBeTruthy()
    expect(
      screen.getByLabelText(/4 Şubat 2026 20.00–06\.00 · Güvenlik \(önceki günden\)/),
    ).toBeTruthy()
  })
})

describe('kapsama açığı gün başlığında toplanır', () => {
  it('açık veren günün başlığında sayı ve şekil işareti bulunur', () => {
    render(
      <HaftaSeridi
        {...VARSAYILAN}
        personeller={[personel(1)]}
        atamalar={[]}
        kapsamaAcigi={[
          {
            acik_id: 1,
            tarih: '2026-02-05',
            baslangic: '06:00:00',
            bitis: '08:00:00',
            nokta_id: 1,
            eksik_sayi: 3,
          },
        ]}
      />,
    )
    expect(screen.getByText('▲3')).toBeTruthy()
  })
})

describe('satır toplamı', () => {
  it('dönem toplamı blokların süresidir — hücrelerin değil', () => {
    render(
      <HaftaSeridi
        {...VARSAYILAN}
        personeller={[personel(1)]}
        // 20.00–06.00 iki gün hücresini boyar ama TEK bloktur ve on saattir.
        atamalar={[blok(1, 1, '2026-02-03', 20, 10)]}
      />,
    )
    expect(screen.getByText(/P-001 · 10 sa/)).toBeTruthy()
  })
})

describe('İş 6 — hücre OKUNUR: saat aralığı metni + konum çubuğu', () => {
  it('saat aralığını ve nokta kısaltmasını METİN olarak yazar', () => {
    render(
      <HaftaSeridi
        {...VARSAYILAN}
        personeller={[personel(1)]}
        atamalar={[blok(1, 1, '2026-02-03', 8, 8)]}
      />,
    )
    // Gradient tek başına okunmuyordu; bilgiyi taşıyan şey sayının kendisi.
    expect(screen.getByText('08–16')).toBeTruthy()
    expect(screen.getByText('GÜV')).toBeTruthy()
  })

  it('çubuk bloğun günün neresinde durduğunu gösterir', () => {
    const { container } = render(
      <HaftaSeridi
        {...VARSAYILAN}
        personeller={[personel(1)]}
        atamalar={[blok(1, 1, '2026-02-03', 8, 8)]}
      />,
    )
    const cubuk = [...container.querySelectorAll<HTMLElement>('td span[style*="left"]')]
    expect(cubuk).toHaveLength(1)
    expect(cubuk[0]!.style.left).toBe(`${(8 / 24) * 100}%`)
    expect(cubuk[0]!.style.width).toBe(`${(8 / 24) * 100}%`)
  })

  it('gece yarısını aşan blokta iki günün çubukları kenarlara dayanır', () => {
    const { container } = render(
      <HaftaSeridi
        {...VARSAYILAN}
        personeller={[personel(1)]}
        atamalar={[blok(1, 1, '2026-02-03', 20, 10)]}
      />,
    )
    const cubuklar = [...container.querySelectorAll<HTMLElement>('td span[style*="left"]')]
    expect(cubuklar).toHaveLength(2)
    // Başladığı gün: 20.00'den gün sonuna. Ertesi gün: sol kenardan 06.00'ya.
    expect(cubuklar[0]!.style.left).toBe(`${(20 / 24) * 100}%`)
    expect(cubuklar[1]!.style.left).toBe('0%')
    expect(cubuklar[1]!.style.width).toBe(`${(6 / 24) * 100}%`)
  })

  it('önceki günden gelen parçanın metni ‹ ile işaretlenir', () => {
    render(
      <HaftaSeridi
        {...VARSAYILAN}
        personeller={[personel(1)]}
        atamalar={[blok(1, 1, '2026-02-03', 20, 10)]}
      />,
    )
    // İki günde de bloğun TAMAMI yazılır (SRS TD-13); ertesi günde nereden
    // geldiği `‹` ile belirtilir.
    expect(screen.getByText('20–06')).toBeTruthy()
    expect(screen.getByText('‹20–06')).toBeTruthy()
  })

  it('boş günde tire yazar ve çubuk çizmez', () => {
    const { container } = render(
      <HaftaSeridi {...VARSAYILAN} personeller={[personel(1)]} atamalar={[]} />,
    )
    expect(screen.getAllByText('–')).toHaveLength(7)
    expect(container.querySelectorAll('td span[style*="left"]')).toHaveLength(0)
  })
})
