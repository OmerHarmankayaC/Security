import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { Atama, GorevNoktasi, KapsamaAcigi, Personel } from '@/api/types'
import { GunIzgarasi } from './GunIzgarasi'

afterEach(cleanup)

/**
 * Gün ızgarası — turun İKİ KABUL KRİTERİ burada ölçülür (Tur 6, İş 1 ve İş 4).
 *
 * Ekran tarayıcıda açılamadığı için (5173 portu başka projede) davranışın
 * kanıtı bu testlerdir. TEST EDİLMEYEN DAVRANIŞ: fare ile gerçek sürükleme
 * jesti — jsdom `pointermove` sırasında düzen (layout) hesaplamadığından
 * imlecin hangi saatin üzerinde olduğu ancak `pointerenter` olayı elle
 * gönderilerek anlatılabiliyor. Aşağıdaki test hücrelere doğrudan olay
 * göndererek jestin MANTIĞINI doğrular; işaretçinin gerçekten o hücreye denk
 * gelip gelmediğini doğrulamaz.
 */

const PERSONEL: Personel[] = [
  {
    personel_id: 1,
    ad_soyad: 'Ayşe Yıldız',
    sicil_no: 'P-001',
    haftalik_hedef_saat: 45,
    aktif_baslangic: '2026-01-01',
    aktif_bitis: null,
    yetkinlik_idleri: [1],
    devir_fazla_calisma_saat: '0',
    kota_yili: 2026,
  },
]

const NOKTALAR = new Map<number, GorevNoktasi>([
  [1, { nokta_id: 1, ad: 'Güvenlik', bina_id: 1, onkosul_yetkinlik_id: 1, aktif: true }],
])

// 20.00'de başlayıp ertesi gün 06.00'da biten TEK blok — turun kabul örneği.
const GECE_BLOGU: Atama = {
  atama_id: 10,
  personel_id: 1,
  baslangic_zamani: '2026-02-02T20:00:00+03:00',
  bitis_zamani: '2026-02-03T06:00:00+03:00',
  tarih: '2026-02-02',
  sure_saat: 10,
  nokta_id: 1,
  kilitli: false,
  kaynak: 'cozucu',
}

const VARSAYILAN = {
  personeller: PERSONEL,
  atamalar: [GECE_BLOGU],
  noktaMap: NOKTALAR,
  kapsamaAcigi: [] as KapsamaAcigi[],
  seritNoktalari: [NOKTALAR.get(1)!],
  sinirlar: { asgariSaat: 4, azamiSaat: 11 },
  duzenlenebilir: true,
  seciliPersonelId: null,
  onSatirSec: () => {},
  onBlokTanimla: () => {},
}

describe('İş 1 kabul — gece yarısını aşan blok iki günde de görünür, TEK bloktur', () => {
  it('başladığı günün ızgarasında görünür ve ertesi güne taşıdığını söyler', () => {
    render(<GunIzgarasi {...VARSAYILAN} gun="2026-02-02" />)
    const serit = screen.getByLabelText('20.00–06.00 · Güvenlik · ertesi güne taşıyor')
    // Sağ kenara dayanır: 20.00'den gün sonuna, yani genişliğin 4/24'ü.
    expect(serit.style.left).toBe(`${(20 / 24) * 100}%`)
    expect(serit.style.width).toBe(`${(4 / 24) * 100}%`)
  })

  it('ertesi günün ızgarasında sol kenardan başlar ve önceki günden geldiğini söyler', () => {
    render(<GunIzgarasi {...VARSAYILAN} gun="2026-02-03" />)
    const serit = screen.getByLabelText('20.00–06.00 · Güvenlik · önceki günden devam ediyor')
    expect(serit.style.left).toBe('0%')
    expect(serit.style.width).toBe(`${(6 / 24) * 100}%`)
  })

  it('iki günde de AYNI aralığı yazar — iki ayrı blok gibi okunmaz', () => {
    const { unmount } = render(<GunIzgarasi {...VARSAYILAN} gun="2026-02-02" />)
    expect(screen.getByText('20.00–06.00')).toBeTruthy()
    unmount()
    render(<GunIzgarasi {...VARSAYILAN} gun="2026-02-03" />)
    // "20.00–24.00" ve "00.00–06.00" yazılsaydı model tam olarak yasakladığı
    // şeyi ekranda üretmiş olurdu (SRS TD-13).
    expect(screen.getByText('20.00–06.00')).toBeTruthy()
    expect(screen.queryByText('00.00–06.00')).toBeNull()
  })

  it('blok BAŞLADIĞI güne sayılır: toplam saat başlangıç gününde yazar', () => {
    const { unmount } = render(<GunIzgarasi {...VARSAYILAN} gun="2026-02-02" />)
    expect(screen.getByText(/P-001 · 10 sa/)).toBeTruthy()
    unmount()
    render(<GunIzgarasi {...VARSAYILAN} gun="2026-02-03" />)
    // Ertesi gün altı saat GÖRÜNÜR ama o günün toplamına yazılmaz (SRS TD-1).
    expect(screen.queryByText(/6 sa/)).toBeNull()
    expect(screen.getByText('P-001')).toBeTruthy()
  })

  it('üçüncü güne hiç değmez', () => {
    render(<GunIzgarasi {...VARSAYILAN} gun="2026-02-04" />)
    expect(screen.queryByText('20.00–06.00')).toBeNull()
  })
})

describe('İş 4 kabul — sürükleyerek blok tanımlama', () => {
  function saatHucresi(saat: number): Element {
    const hucre = document.querySelector(`[data-saat="${saat}"]`)
    if (!hucre) throw new Error(`Saat hücresi bulunamadı: ${saat}`)
    return hucre
  }

  it('sürükleme bittiğinde yarı açık saat aralığını bildirir', () => {
    const onBlokTanimla = vi.fn()
    const { container } = render(
      <GunIzgarasi {...VARSAYILAN} atamalar={[]} gun="2026-02-02" onBlokTanimla={onBlokTanimla} />,
    )
    fireEvent.pointerDown(saatHucresi(8))
    fireEvent.pointerEnter(saatHucresi(15))
    fireEvent.pointerUp(container.firstChild!)
    // 08'den 15'e sürüklemek 08.00–16.00 bloğu tanımlar: bitiş DIŞLAYICIDIR.
    expect(onBlokTanimla).toHaveBeenCalledWith(1, 8, 16)
  })

  it('geriye doğru sürükleme de aynı aralığı verir', () => {
    const onBlokTanimla = vi.fn()
    const { container } = render(
      <GunIzgarasi {...VARSAYILAN} atamalar={[]} gun="2026-02-02" onBlokTanimla={onBlokTanimla} />,
    )
    fireEvent.pointerDown(saatHucresi(15))
    fireEvent.pointerEnter(saatHucresi(8))
    fireEvent.pointerUp(container.firstChild!)
    expect(onBlokTanimla).toHaveBeenCalledWith(1, 8, 16)
  })

  it('TEK TIK blok tanımlamaz — yalnızca satırı seçer', () => {
    const onBlokTanimla = vi.fn()
    const onSatirSec = vi.fn()
    const { container } = render(
      <GunIzgarasi
        {...VARSAYILAN}
        atamalar={[]}
        gun="2026-02-02"
        onBlokTanimla={onBlokTanimla}
        onSatirSec={onSatirSec}
      />,
    )
    fireEvent.pointerDown(saatHucresi(8))
    fireEvent.pointerUp(container.firstChild!)
    expect(onBlokTanimla).not.toHaveBeenCalled()
    expect(onSatirSec).toHaveBeenCalledWith(1)
  })

  it('asgari süreden kısa seçim sürükleme SIRASINDA anlaşılır biçimde engellenir', () => {
    render(<GunIzgarasi {...VARSAYILAN} atamalar={[]} gun="2026-02-02" />)
    fireEvent.pointerDown(saatHucresi(8))
    fireEvent.pointerEnter(saatHucresi(9))
    // İki saatlik seçim asgari dördün altında: önizleme sınırı ve NEDENİNİ
    // yazar, kullanıcı bırakıp sunucudan ret beklemez.
    expect(screen.getByText('Asgari blok 4 saat (H1)')).toBeTruthy()
  })

  it('günlük tavanı aşan seçim de sürükleme sırasında görünür', () => {
    render(<GunIzgarasi {...VARSAYILAN} atamalar={[]} gun="2026-02-02" />)
    fireEvent.pointerDown(saatHucresi(6))
    fireEvent.pointerEnter(saatHucresi(18))
    expect(screen.getByText('Günlük azami 11 saat (H9)')).toBeTruthy()
  })

  it('sınırların içindeki seçimde önizleme saat aralığını gösterir', () => {
    render(<GunIzgarasi {...VARSAYILAN} atamalar={[]} gun="2026-02-02" />)
    fireEvent.pointerDown(saatHucresi(8))
    fireEvent.pointerEnter(saatHucresi(15))
    expect(screen.getByText('08.00–16.00')).toBeTruthy()
  })

  it('düzenlenemeyen sürümde sürükleme hiç başlamaz', () => {
    const onBlokTanimla = vi.fn()
    const { container } = render(
      <GunIzgarasi
        {...VARSAYILAN}
        atamalar={[]}
        gun="2026-02-02"
        duzenlenebilir={false}
        onBlokTanimla={onBlokTanimla}
      />,
    )
    fireEvent.pointerDown(saatHucresi(8))
    fireEvent.pointerEnter(saatHucresi(15))
    fireEvent.pointerUp(container.firstChild!)
    expect(onBlokTanimla).not.toHaveBeenCalled()
  })

  it('pasif kural sınır koymaz: iki saatlik seçim uyarısız geçer', () => {
    render(
      <GunIzgarasi
        {...VARSAYILAN}
        atamalar={[]}
        gun="2026-02-02"
        sinirlar={{ asgariSaat: null, azamiSaat: null }}
      />,
    )
    fireEvent.pointerDown(saatHucresi(8))
    fireEvent.pointerEnter(saatHucresi(9))
    expect(screen.getByText('08.00–10.00')).toBeTruthy()
  })
})

describe('kapsama açığı — SAAT düzeyinde ve renkten bağımsız işaretli', () => {
  const ACIK: KapsamaAcigi[] = [
    {
      acik_id: 1,
      tarih: '2026-02-02',
      baslangic: '06:00:00',
      bitis: '08:00:00',
      nokta_id: 1,
      eksik_sayi: 2,
    },
  ]

  it('açık verilen saatlerde sayıyı ve şekil işaretini gösterir', () => {
    render(<GunIzgarasi {...VARSAYILAN} gun="2026-02-02" kapsamaAcigi={ACIK} />)
    // Aralık iki saat sürüyor: 06 ve 07 işaretlenir, 08 işaretlenmez.
    expect(screen.getAllByText('▲2')).toHaveLength(2)
  })
})
