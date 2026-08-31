import { cleanup, fireEvent, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { Atama, GorevNoktasi, KapsamaAcigi, Personel } from '@/api/types'
import { GunIzgarasi } from './GunIzgarasi'
import { ciz } from '@/test/ciz'

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
  onBlokTasi: () => {},
  onNoktaDegistir: () => {},
  onKilitDegistir: () => {},
  onBlokSil: () => {},
}

describe('İş 1 kabul — gece yarısını aşan blok iki günde de görünür, TEK bloktur', () => {
  it('başladığı günün ızgarasında görünür ve ertesi güne taşıdığını söyler', () => {
    ciz(<GunIzgarasi {...VARSAYILAN} gun="2026-02-02" />)
    const serit = screen.getByLabelText('20.00–06.00 · Güvenlik · ertesi güne taşıyor')
    // Sağ kenara dayanır: 20.00'den gün sonuna, yani genişliğin 4/24'ü.
    expect(serit.style.left).toBe(`${(20 / 24) * 100}%`)
    expect(serit.style.width).toBe(`${(4 / 24) * 100}%`)
  })

  it('ertesi günün ızgarasında sol kenardan başlar ve önceki günden geldiğini söyler', () => {
    ciz(<GunIzgarasi {...VARSAYILAN} gun="2026-02-03" />)
    const serit = screen.getByLabelText('20.00–06.00 · Güvenlik · önceki günden devam ediyor')
    expect(serit.style.left).toBe('0%')
    expect(serit.style.width).toBe(`${(6 / 24) * 100}%`)
  })

  it('iki günde de AYNI aralığı yazar — iki ayrı blok gibi okunmaz', () => {
    const { unmount } = ciz(<GunIzgarasi {...VARSAYILAN} gun="2026-02-02" />)
    expect(screen.getByText('20.00–06.00')).toBeTruthy()
    unmount()
    ciz(<GunIzgarasi {...VARSAYILAN} gun="2026-02-03" />)
    // "20.00–24.00" ve "00.00–06.00" yazılsaydı model tam olarak yasakladığı
    // şeyi ekranda üretmiş olurdu (SRS TD-13).
    expect(screen.getByText('20.00–06.00')).toBeTruthy()
    expect(screen.queryByText('00.00–06.00')).toBeNull()
  })

  it('blok BAŞLADIĞI güne sayılır: toplam saat başlangıç gününde yazar', () => {
    const { unmount } = ciz(<GunIzgarasi {...VARSAYILAN} gun="2026-02-02" />)
    expect(screen.getByText(/P-001 · 10 sa/)).toBeTruthy()
    unmount()
    ciz(<GunIzgarasi {...VARSAYILAN} gun="2026-02-03" />)
    // Ertesi gün altı saat GÖRÜNÜR ama o günün toplamına yazılmaz (SRS TD-1).
    expect(screen.queryByText(/6 sa/)).toBeNull()
    expect(screen.getByText('P-001')).toBeTruthy()
  })

  it('üçüncü güne hiç değmez', () => {
    ciz(<GunIzgarasi {...VARSAYILAN} gun="2026-02-04" />)
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
    const { container } = ciz(
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
    const { container } = ciz(
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
    const { container } = ciz(
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
    ciz(<GunIzgarasi {...VARSAYILAN} atamalar={[]} gun="2026-02-02" />)
    fireEvent.pointerDown(saatHucresi(8))
    fireEvent.pointerEnter(saatHucresi(9))
    // İki saatlik seçim asgari dördün altında: önizleme sınırı ve NEDENİNİ
    // yazar, kullanıcı bırakıp sunucudan ret beklemez.
    expect(screen.getByText('Asgari blok 4 saat (H1)')).toBeTruthy()
  })

  it('günlük tavanı aşan seçim de sürükleme sırasında görünür', () => {
    ciz(<GunIzgarasi {...VARSAYILAN} atamalar={[]} gun="2026-02-02" />)
    fireEvent.pointerDown(saatHucresi(6))
    fireEvent.pointerEnter(saatHucresi(18))
    expect(screen.getByText('Günlük azami 11 saat (H9)')).toBeTruthy()
  })

  it('sınırların içindeki seçimde önizleme saat aralığını gösterir', () => {
    ciz(<GunIzgarasi {...VARSAYILAN} atamalar={[]} gun="2026-02-02" />)
    fireEvent.pointerDown(saatHucresi(8))
    fireEvent.pointerEnter(saatHucresi(15))
    expect(screen.getByText('08.00–16.00')).toBeTruthy()
  })

  it('düzenlenemeyen sürümde sürükleme hiç başlamaz', () => {
    const onBlokTanimla = vi.fn()
    const { container } = ciz(
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
    ciz(
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
      baslangic_zamani: '2026-02-02T06:00:00+03:00',
      bitis_zamani: '2026-02-02T08:00:00+03:00',
      nokta_id: 1,
      eksik_sayi: 2,
    },
  ]

  it('açık verilen saatlerde sayıyı ve şekil işaretini gösterir', () => {
    ciz(<GunIzgarasi {...VARSAYILAN} gun="2026-02-02" kapsamaAcigi={ACIK} />)
    // Aralık iki saat sürüyor: 06 ve 07 işaretlenir, 08 işaretlenmez.
    expect(screen.getAllByText('▲2')).toHaveLength(2)
  })
})

describe('İş 1 kabul — sınıra dayanınca sürükleme DURUR', () => {
  function saatHucresi(saat: number): Element {
    const hucre = document.querySelector(`[data-saat="${saat}"]`)
    if (!hucre) throw new Error(`Saat hücresi bulunamadı: ${saat}`)
    return hucre
  }

  it('asgari süreden kısa seçim yapılamaz — aralık asgariye ÇEKİLİR', () => {
    const onBlokTanimla = vi.fn()
    const { container } = ciz(
      <GunIzgarasi {...VARSAYILAN} atamalar={[]} gun="2026-02-02" onBlokTanimla={onBlokTanimla} />,
    )
    // 08'den 09'a: iki saat, asgari dördün altında.
    fireEvent.pointerDown(saatHucresi(8))
    fireEvent.pointerEnter(saatHucresi(9))
    fireEvent.pointerUp(container.firstChild!)
    // Reddedilmez; asgariye tamamlanır. Kullanıcı sınırı elinde hisseder.
    expect(onBlokTanimla).toHaveBeenCalledWith(1, 8, 12)
  })

  it('günlük tavanı aşan seçim azamide durur', () => {
    const onBlokTanimla = vi.fn()
    const { container } = ciz(
      <GunIzgarasi {...VARSAYILAN} atamalar={[]} gun="2026-02-02" onBlokTanimla={onBlokTanimla} />,
    )
    fireEvent.pointerDown(saatHucresi(6))
    fireEvent.pointerEnter(saatHucresi(22))
    fireEvent.pointerUp(container.firstChild!)
    // 06'dan 23'e on yedi saat; azami on bir.
    expect(onBlokTanimla).toHaveBeenCalledWith(1, 6, 17)
  })

  it('sınıra dayanıldığı önizlemede yazar', () => {
    ciz(<GunIzgarasi {...VARSAYILAN} atamalar={[]} gun="2026-02-02" />)
    fireEvent.pointerDown(saatHucresi(8))
    fireEvent.pointerEnter(saatHucresi(9))
    expect(screen.getByText('Asgari blok 4 saat (H1)')).toBeTruthy()
  })

  it('pasif kuralda kırpma da yapılmaz', () => {
    const onBlokTanimla = vi.fn()
    const { container } = ciz(
      <GunIzgarasi
        {...VARSAYILAN}
        atamalar={[]}
        gun="2026-02-02"
        sinirlar={{ asgariSaat: null, azamiSaat: null }}
        onBlokTanimla={onBlokTanimla}
      />,
    )
    fireEvent.pointerDown(saatHucresi(8))
    fireEvent.pointerEnter(saatHucresi(9))
    fireEvent.pointerUp(container.firstChild!)
    expect(onBlokTanimla).toHaveBeenCalledWith(1, 8, 10)
  })
})

describe('İş 1 kabul — blok taşıma ve menü', () => {
  const IKI_PERSONEL = [
    PERSONEL[0]!,
    { ...PERSONEL[0]!, personel_id: 2, ad_soyad: 'Mehmet Çınar', sicil_no: 'P-002' },
  ]
  const GUNDUZ = {
    ...GECE_BLOGU,
    atama_id: 20,
    baslangic_zamani: '2026-02-02T08:00:00+03:00',
    bitis_zamani: '2026-02-02T16:00:00+03:00',
    sure_saat: 8,
  }

  function serit(): HTMLElement {
    const el = document.querySelector<HTMLElement>('[data-blok="20"]')
    if (!el) throw new Error('Blok şeridi bulunamadı')
    return el
  }

  it('gövdeden tutup BAŞKA personelin satırına taşır', () => {
    const onBlokTasi = vi.fn()
    const { container } = ciz(
      <GunIzgarasi
        {...VARSAYILAN}
        personeller={IKI_PERSONEL}
        atamalar={[GUNDUZ]}
        gun="2026-02-02"
        onBlokTasi={onBlokTasi}
      />,
    )
    // jsdom düzen hesaplamaz: şeridin kabı sıfır genişliktedir ve oran hep
    // 0 çıkar, yani tutulan saat 0 sayılır. Testin ölçtüğü şey SATIR
    // DEĞİŞİKLİĞİDİR; saatin kendisi tarayıcıda gözle doğrulanmalı.
    fireEvent.pointerDown(serit())
    const hedefSatir = container.querySelectorAll('[data-saat="12"]')[1]!
    fireEvent.pointerEnter(hedefSatir)
    fireEvent.pointerUp(container.firstChild!)

    expect(onBlokTasi).toHaveBeenCalledTimes(1)
    const [kaynak, hedef] = onBlokTasi.mock.calls[0]!
    expect(kaynak).toBe(1)
    expect(hedef).toBe(2)
  })

  it('kıpırdamadan bırakmak taşıma DEĞİL menü açar', () => {
    const onBlokTasi = vi.fn()
    const { container } = ciz(
      <GunIzgarasi
        {...VARSAYILAN}
        personeller={IKI_PERSONEL}
        atamalar={[GUNDUZ]}
        gun="2026-02-02"
        onBlokTasi={onBlokTasi}
      />,
    )
    fireEvent.pointerDown(serit())
    fireEvent.pointerUp(container.firstChild!)
    expect(onBlokTasi).not.toHaveBeenCalled()
    expect(screen.getByRole('menu', { name: 'Blok işlemleri' })).toBeTruthy()
  })

  it('menüden silme TEK TIKLA yapılır', () => {
    const onBlokSil = vi.fn()
    const { container } = ciz(
      <GunIzgarasi {...VARSAYILAN} atamalar={[GUNDUZ]} gun="2026-02-02" onBlokSil={onBlokSil} />,
    )
    fireEvent.pointerDown(serit())
    fireEvent.pointerUp(container.firstChild!)
    // Eski ekranda silme bir açılır listenin "— Boşalt —" seçeneğinin
    // içine saklanmıştı; artık görünür bir eylem.
    fireEvent.click(screen.getByRole('menuitem', { name: 'Bloğu sil' }))
    expect(onBlokSil).toHaveBeenCalledWith(1)
  })

  it('menüden kilitleme ve görev noktası değiştirme çalışır', () => {
    const onKilitDegistir = vi.fn()
    const onNoktaDegistir = vi.fn()
    const noktaMap = new Map(NOKTALAR)
    noktaMap.set(2, {
      nokta_id: 2,
      ad: 'Vardiya Şefliği',
      bina_id: null,
      onkosul_yetkinlik_id: null,
      aktif: true,
    })
    const { container } = ciz(
      <GunIzgarasi
        {...VARSAYILAN}
        atamalar={[GUNDUZ]}
        gun="2026-02-02"
        noktaMap={noktaMap}
        seritNoktalari={[...noktaMap.values()]}
        onKilitDegistir={onKilitDegistir}
        onNoktaDegistir={onNoktaDegistir}
      />,
    )
    fireEvent.pointerDown(serit())
    fireEvent.pointerUp(container.firstChild!)

    fireEvent.change(screen.getByLabelText('Görev Noktası'), { target: { value: '2' } })
    expect(onNoktaDegistir).toHaveBeenCalledWith(1, 2)

    fireEvent.pointerDown(serit())
    fireEvent.pointerUp(container.firstChild!)
    fireEvent.click(screen.getByRole('menuitem', { name: 'Kilitle' }))
    expect(onKilitDegistir).toHaveBeenCalledWith(1, true)
  })

  it('düzenlenemeyen sürümde menü hiç açılmaz', () => {
    const { container } = ciz(
      <GunIzgarasi
        {...VARSAYILAN}
        atamalar={[GUNDUZ]}
        gun="2026-02-02"
        duzenlenebilir={false}
      />,
    )
    fireEvent.pointerDown(serit())
    fireEvent.pointerUp(container.firstChild!)
    expect(screen.queryByRole('menu')).toBeNull()
  })
})
