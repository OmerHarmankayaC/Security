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
  damga: 'd1',
  toplam_ceza: 912,
  kapsama_acigi_sayisi: 0,
  fazla_kadro_sayisi: 0,
  // Gorev 6/7: sozlesmeye eklendi, bu testler onu okumaz.
  atama_sayisi: 20,
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
    baslangic_zamani: `${tarih}T${String(bas).padStart(2, '0')}:00:00+03:00`,
    bitis_zamani: `${tarih}T${String((bas + 8) % 24).padStart(2, '0')}:00:00+03:00`,
    nokta_id: nokta,
    eksik_sayi: eksik,
  }
}

function ciz(atamalar: Atama[], acikSatirlari: KapsamaAcigi[] = []) {
  return render(
    <YazdirilabilirCizelge {...veriKur(atamalar, acikSatirlari)} uretimTarihi="2026-02-01" />,
  )
}

/**
 * Kapsama açığı tablosu, gün ızgaralarının SONUNDA durur ve sayısı döneme
 * göre değişir; sabit bir dizinle seçilmesi dönem uzunluğuna bağımlı bir test
 * üretirdi. Tablo kendi başlığından bulunur.
 */
function acikTablosunuBul(): HTMLElement {
  const tablo = screen
    .getAllByRole('table')
    .find((t) => within(t).queryByRole('columnheader', { name: 'Görev Noktası' }) !== null)
  if (!tablo) throw new Error('Kapsama açığı tablosu bulunamadı')
  return tablo
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

describe('YazdirilabilirCizelge — gün ızgarası (Tur 6 İş 5)', () => {
  it('dönemdeki her gün için ayrı bir ızgara basar', () => {
    const { container } = ciz(ATAMALAR)
    expect(container.querySelectorAll('.yazdirma-tablo')).toHaveLength(7)
    expect(screen.getByRole('heading', { name: /02 Şubat Pazartesi/ })).toBeDefined()
    expect(screen.getByRole('heading', { name: /08 Şubat Pazar · hafta sonu/ })).toBeDefined()
  })

  it('SAAT BAŞLIĞI taşır — gün başlığı değil', () => {
    ciz(ATAMALAR)
    const izgara = screen.getAllByRole('table')[0]!
    const basliklar = within(izgara).getAllByRole('columnheader')
    // Personel sütunu + yirmi dört saat.
    expect(basliklar).toHaveLength(25)
    expect(basliklar[1]?.textContent).toBe('00')
    expect(basliklar[24]?.textContent).toBe('23')
  })

  it('saat başlığı her günün tablosunun THEAD ında durur', () => {
    // Tablo sayfaya bölündüğünde tarayıcı `thead`i her sayfada yeniden
    // basar; başlık `tbody`ye konsaydı ikinci sayfadaki şeritler hangi
    // saate denk geldiğini kaybederdi.
    const { container } = ciz(ATAMALAR)
    const theadlar = container.querySelectorAll('.yazdirma-tablo thead')
    expect(theadlar).toHaveLength(7)
  })

  it('yalnızca ataması olan personeli satıra alır', () => {
    ciz([ATAMALAR[0]!])
    expect(screen.getAllByText(/Ayşe Şahin/).length).toBeGreaterThan(0)
    expect(screen.queryByText(/Mehmet Çınar/)).toBeNull()
  })

  it('şeridin üzerinde saat aralığı ve nokta kısaltması METİN olarak durur', () => {
    const { container } = ciz(ATAMALAR)
    // Renk tek başına bilgi taşımaz; tarayıcı arka plan basmayabilir
    // (SDD 6.3.3). Blok ADI diye bir şey yok (SRS TD-13), okunabilir tek
    // bilgi sürenin kendisi.
    expect(container.textContent).toContain('08.00–16.00')
    expect(container.textContent).toContain('00.00–08.00')
    expect(container.textContent).toContain('GÜV')
    expect(container.textContent).toContain('VŞ')
  })

  it('şerit, bloğun saatlerine denk gelen yerde ve genişlikte durur', () => {
    const { container } = ciz([ATAMALAR[0]!])
    const serit = [...container.querySelectorAll<HTMLElement>('td div[style*="left"]')].find(
      (d) => d.textContent?.includes('08.00–16.00'),
    )
    expect(serit?.style.left).toBe(`${(8 / 24) * 100}%`)
    expect(serit?.style.width).toBe(`${(8 / 24) * 100}%`)
  })

  it('gün toplamı bloğun BAŞLADIĞI güne yazılır (SRS TD-1)', () => {
    const { container } = ciz([ATAMALAR[0]!])
    // Sayı ayrı bir mono <span>'da durur (düz cümle asla Mono değildir), o
    // yüzden satırın tamamı textContent üzerinden okunur.
    const adHucreleri = [...container.querySelectorAll('.yazdirma-tablo tbody td:first-child')]
    const ayseninGunleri = adHucreleri
      .map((h) => h.textContent ?? '')
      .filter((m) => m.startsWith('Ayşe Şahin'))
    // Yedi günün yalnız BİRİNDE toplam yazar — blok başladığı güne sayılır.
    expect(ayseninGunleri.filter((m) => m.includes('8sa'))).toEqual(['Ayşe Şahin · 8sa'])
  })

  it('personeli ada göre sıralar', () => {
    ciz(ATAMALAR)
    const izgara = screen.getAllByRole('table')[0]!
    const adlar = within(izgara)
      .getAllByRole('row')
      .slice(1)
      // Ad hücresi günlük toplamı da taşır ("Ayşe Şahin · 8sa"); sıralamayı
      // ölçen test toplamdan etkilenmemeli.
      .map((satir) => satir.firstElementChild?.textContent?.split(' · ')[0])
    expect(adlar).toEqual(['Ayşe Şahin', 'Mehmet Çınar'])
  })

  it('ilk gün dışındaki her gün yeni sayfada başlar', () => {
    const { container } = ciz(ATAMALAR)
    // Yedi günden altısı + kapsama açığı bölümü.
    expect(container.querySelectorAll('.yazdirma-sayfa-basi')).toHaveLength(7)
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
    expect(screen.getByText('2 aralıkta toplam 3 kişi eksik.')).toBeDefined()

    const acikTablosu = acikTablosunuBul()
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
    const satirlar = within(acikTablosunuBul()).getAllByRole('row').slice(1)
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

  it('boş çizelgede bile çöker değil, ızgara iskeleti basılır', () => {
    ciz([])
    expect(screen.getAllByRole('table')[0]).toBeDefined()
    expect(screen.getByText('Bu sürümde kapsama açığı yok.')).toBeDefined()
  })
})

describe('YazdirilabilirCizelge — dar şeridin etiketi (baskı kusuru)', () => {
  function darBlok(bas: number, sure: number): Atama {
    const bit = (bas + sure) % 24
    const bitGun = bas + sure >= 24 ? '03' : '02'
    return {
      atama_id: 90,
      personel_id: 1,
      baslangic_zamani: `2026-02-02T${String(bas).padStart(2, '0')}:00:00+03:00`,
      bitis_zamani: `2026-02-${bitGun}T${String(bit).padStart(2, '0')}:00:00+03:00`,
      tarih: '2026-02-02',
      sure_saat: sure,
      nokta_id: 20,
      kilitli: false,
      kaynak: 'cozucu',
    }
  }

  /** Şeridin KENDİSİ (konumlandırılmış, gradientli kutu). */
  function seritKutusu(container: HTMLElement, metin: string): HTMLElement {
    const kutu = [...container.querySelectorAll<HTMLElement>('td div[style*="width"]')].find((d) =>
      d.style.backgroundImage.includes('linear-gradient'),
    )
    if (!kutu) throw new Error(`Şerit bulunamadı: ${metin}`)
    return kutu
  }

  it('geniş şeritte etiket şeridin İÇİNDE durur', () => {
    const { container } = ciz([darBlok(8, 8)])
    expect(seritKutusu(container, '08.00–16.00').textContent).toContain('08.00–16.00')
  })

  it('dar şeritte etiket şeridin DIŞINA çıkar — kırpılmaz', () => {
    // İki saatlik bir parça 6pt Mono ile "10.00–12.00 GÜV"ü taşıyamaz.
    const { container } = ciz([darBlok(10, 2)])
    expect(seritKutusu(container, '10.00–12.00').textContent).toBe('')
    // Metin kayıp DEĞİL: şeridin bittiği yerden itibaren yazılır.
    const etiket = [...container.querySelectorAll<HTMLElement>('span')].find((s) =>
      s.textContent?.includes('10.00–12.00'),
    )
    expect(etiket).toBeDefined()
    expect(etiket!.style.left).toBe(`${(12 / 24) * 100}%`)
    expect(etiket!.className).toContain('whitespace-nowrap')
  })

  it('gün sonuna dayanan dar şeritte etiket SOLA yazılır', () => {
    // 22.00–05.00: başladığı günde 22–24 arası iki saat kalır ve sağda yer
    // yoktur; etiket sağa yazılsaydı sayfa kenarında kırpılırdı.
    const { container } = ciz([darBlok(22, 7)])
    const etiket = [...container.querySelectorAll<HTMLElement>('span')].find((s) =>
      s.textContent?.includes('22.00–05.00'),
    )
    expect(etiket).toBeDefined()
    expect(etiket!.style.right).toBe(`${((24 - 22) / 24) * 100}%`)
    expect(etiket!.style.left).toBe('')
  })

  it('dar şeritte de gece yarısı işareti metne dahildir', () => {
    const { container } = ciz([darBlok(22, 7)])
    expect(container.textContent).toContain('22.00–05.00 GÜV›')
  })
})
