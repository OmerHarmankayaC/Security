import { cleanup, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import type {
  Atama,
  CizelgeSurumu,
  Donem,
  GorevNoktasi,
  KapsamaAcigi,
  Personel,
} from '@/api/types'
import type { CizelgeVerisi } from '@/lib/disaAktarma'
import { YazdirilabilirCizelge } from './YazdirilabilirCizelge'

afterEach(cleanup)

// Bir haftalık dönem: 02–08 Şubat 2026 (pazartesi–pazar).
const DONEM: Donem = {
  donem_id: 1,
  baslangic_tarihi: '2026-02-02',
  bitis_tarihi: '2026-02-08',
  tercih_son_tarihi: '2026-01-26',
}

const SURUM: CizelgeSurumu = {
  surum_id: 9,
  donem_id: 1,
  surum_no: 3,
  durum: 'cozuldu',
  onceki_surum_id: null,
  yayin_zamani: null,
  olusturma_zamani: '2026-02-01T09:00:00Z',
  guncelleme_zamani: '2026-02-01T09:00:00Z',
  toplam_ceza: 912,
  kapsama_acigi_sayisi: 0,
  fazla_kadro_sayisi: 0,
}

const PERSONEL: Personel[] = [
  {
    personel_id: 1,
    ad_soyad: 'Ayşe Şahin',
    sicil_no: 'GG-001',
    haftalik_hedef_saat: 40,
    aktif_baslangic: '2026-01-01',
    aktif_bitis: null,
    yetkinlik_idleri: [],
  devir_fazla_calisma_saat: '0.00',
  kota_yili: null,
  },
  {
    personel_id: 2,
    ad_soyad: 'Mehmet Çınar',
    sicil_no: 'GG-002',
    haftalik_hedef_saat: 40,
    aktif_baslangic: '2026-01-01',
    aktif_bitis: null,
    yetkinlik_idleri: [],
  devir_fazla_calisma_saat: '0.00',
  kota_yili: null,
  },
]

const NOKTALAR: GorevNoktasi[] = [
  { nokta_id: 20, ad: 'Güvenlik', bina_id: null, onkosul_yetkinlik_id: null, aktif: true },
  { nokta_id: 21, ad: 'Vardiya Şefliği', bina_id: null, onkosul_yetkinlik_id: null, aktif: true },
]

function veriKur(atamalar: Atama[], kapsamaAcigi: KapsamaAcigi[] = []): CizelgeVerisi {
  return {
    donem: DONEM,
    surum: SURUM,
    atamalar,
    kapsamaAcigi,
    fazlaKadro: [],
    personelMap: new Map(PERSONEL.map((p) => [p.personel_id, p])),
    noktaMap: new Map(NOKTALAR.map((n) => [n.nokta_id, n])),
  }
}

function atama(id: number, personelId: number, tarih: string, bas: number, nokta: number): Atama {
  return {
    atama_id: id,
    personel_id: personelId,
    baslangic_zamani: `${tarih}T${String(bas).padStart(2, '0')}:00:00+03:00`,
    bitis_zamani: `${tarih}T${String((bas + 8) % 24).padStart(2, '0')}:00:00+03:00`,
    tarih,
    sure_saat: 8,
    nokta_id: nokta,
    kilitli: false,
    kaynak: 'cozucu',
  }
}

const ATAMALAR: Atama[] = [
  atama(1, 1, '2026-02-02', 8, 20),
  atama(2, 2, '2026-02-03', 0, 21),
]

function acik(id: number, tarih: string, bas: number, nokta: number, eksik: number): KapsamaAcigi {
  return {
    acik_id: id,
    tarih,
    baslangic: `${String(bas).padStart(2, '0')}:00:00`,
    bitis: `${String((bas + 8) % 24).padStart(2, '0')}:00:00`,
    nokta_id: nokta,
    eksik_sayi: eksik,
  }
}

function ciz(atamalar: Atama[], acikSatirlari: KapsamaAcigi[] = []) {
  return render(
    <YazdirilabilirCizelge {...veriKur(atamalar, acikSatirlari)} uretimTarihi="2026-02-01" />,
  )
}

describe('YazdirilabilirCizelge — başlık', () => {
  it('dönemi, sürüm numarasını ve üretim tarihini yazar', () => {
    ciz(ATAMALAR)
    expect(screen.getByRole('heading', { level: 1 })?.textContent).toContain('02 – 08 Şub 2026')
    // Özet satırındaki SAYILAR ayrı mono <span>'lardadır (TASARIM_REFERANSI.md
    // — "Düz cümle asla Mono değildir"), yani "Sürüm 3" tek bir metin
    // düğümünde DURMAZ. getByText düğüm bazında eşleştiği için satırın
    // tamamı textContent üzerinden okunur.
    const ozet = screen.getByText(/tarihinde üretildi/)
    expect(ozet.textContent).toContain('Sürüm 3')
    expect(ozet.textContent).toContain('1 Şubat 2026 tarihinde üretildi')
  })

  it('tarihleri Türkçe biçimde yazar — okuyucu insan (madde 5)', () => {
    const { container } = ciz(ATAMALAR)
    expect(container.textContent).not.toContain('2026-02-01')
  })
})

describe('YazdirilabilirCizelge — matris', () => {
  it('dönemdeki her gün için bir sütun başlığı üretir', () => {
    ciz(ATAMALAR)
    const izgara = screen.getAllByRole('table')[0]!
    const basliklar = within(izgara).getAllByRole('columnheader')
    // Personel sütunu + yedi gün.
    expect(basliklar).toHaveLength(8)
    expect(basliklar[1]?.textContent).toContain('PZT 2')
    expect(basliklar[7]?.textContent).toContain('PAZ 8')
  })

  it('yalnızca ataması olan personeli satıra alır', () => {
    ciz([ATAMALAR[0]!])
    expect(screen.getByText('Ayşe Şahin')).toBeDefined()
    expect(screen.queryByText('Mehmet Çınar')).toBeNull()
  })

  it('hücrede saat aralığını ve görev noktası kısaltmasını gösterir', () => {
    const { container } = ciz(ATAMALAR)
    // Blok ADI yerine SAAT ARALIĞI (SRS TD-13): blok adı diye bir şey yok,
    // tek okunabilir bilgi sürenin kendisi. Nokta kısaltması kalır — A4
    // genişliğine tam adlar sığmıyor (SDD 6.3.3).
    expect(container.textContent).toContain('08–16')
    expect(container.textContent).toContain('00–08')
    expect(container.textContent).toContain('GÜV')
    expect(container.textContent).toContain('VŞ')
  })

  it('personeli ada göre sıralar', () => {
    ciz(ATAMALAR)
    const izgara = screen.getAllByRole('table')[0]!
    const adlar = within(izgara)
      .getAllByRole('row')
      .slice(1)
      .map((satir) => satir.firstElementChild?.textContent)
    expect(adlar).toEqual(['Ayşe Şahin', 'Mehmet Çınar'])
  })
})

describe('YazdirilabilirCizelge — kapsama açıkları', () => {
  it('açık yokken bölümü gizlemez, açıkça yazar', () => {
    ciz(ATAMALAR, [])
    expect(screen.getByRole('heading', { name: 'Kapsama Açıkları' })).toBeDefined()
    expect(screen.getByText('Bu sürümde kapsama açığı yok.')).toBeDefined()
  })

  it('açıkları tabloda listeler ve toplamı yazar', () => {
    ciz(ATAMALAR, [
      acik(1, '2026-02-02', 0, 20, 2),
      acik(2, '2026-02-05', 8, 21, 1),
    ])
    expect(screen.getByText('2 hücrede toplam 3 kişi eksik.')).toBeDefined()

    const acikTablosu = screen.getAllByRole('table')[1]!
    const satirlar = within(acikTablosu).getAllByRole('row').slice(1)
    expect(satirlar).toHaveLength(2)
    expect(satirlar[0]?.textContent).toContain('2 Şubat 2026')
    // Blok adı yok; açık satırı SAAT ARALIĞINI yazar (SRS TD-13).
    expect(satirlar[0]?.textContent).toContain('00.00–08.00')
    expect(satirlar[0]?.textContent).toContain('Güvenlik')
  })

  it('açıkları tarihe göre sıralar', () => {
    ciz(ATAMALAR, [
      acik(1, '2026-02-06', 8, 20, 1),
      acik(2, '2026-02-02', 8, 20, 1),
    ])
    const satirlar = within(screen.getAllByRole('table')[1]!)
      .getAllByRole('row')
      .slice(1)
    expect(satirlar[0]?.textContent).toContain('2 Şubat 2026')
    expect(satirlar[1]?.textContent).toContain('6 Şubat 2026')
  })
})

describe('YazdirilabilirCizelge — baskı kancaları', () => {
  it('baskı CSS’inin hedeflediği sınıfları taşır', () => {
    const { container } = ciz(ATAMALAR)
    // index.css @media print bu iki sınıfa dayanır: biri gövde gizlenirken
    // görünür kalacak alanı, diğeri sayfa başına tekrarlanacak başlığı seçer.
    expect(container.querySelector('.yazdirma-alani')).not.toBeNull()
    expect(container.querySelector('.yazdirma-tablo thead')).not.toBeNull()
  })

  it('boş çizelgede bile çöker değil, matris iskeleti basılır', () => {
    ciz([])
    expect(screen.getAllByRole('table')[0]).toBeDefined()
    expect(screen.getByText('Bu sürümde kapsama açığı yok.')).toBeDefined()
  })
})
