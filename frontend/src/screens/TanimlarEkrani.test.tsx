import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { Ben, OzelGun, Personel, VardiyaTipi, Yetkinlik } from '@/api/types'
import { AktifIsSaglayici } from '@/components/AktifIsBaglami'
import { OturumBaglami } from '@/components/OturumBaglami'
import { TanimlarEkrani } from './TanimlarEkrani'

/**
 * Personel formunun sözleşmesi (bulgu B3 ve madde 6).
 *
 * Bu dosyanın kilitlediği asıl şey bir kayıp: form yalnızca ilk yetkinliği
 * taşıyor, kaydederken de tek elemanlı bir liste gönderiyordu. Sunucu
 * gönderilen kümeyi olduğu gibi yazdığı için, iki yetkinlikli bir personeli
 * AÇIP HİÇBİR ŞEY DEĞİŞTİRMEDEN Kaydet'e basmak ikinci yetkinliği siliyordu.
 * Sessizdi ve çözücü modelini (H8, uygun havuz) doğrudan değiştiriyordu.
 */

const BEN: Ben = {
  kullanici_adi: 'yonetim',
  rol: 'yonetim',
  parola_degistirmeli: false,
  personel_id: null,
  ad_soyad: null,
}

const YETKINLIKLER: Yetkinlik[] = [
  { yetkinlik_id: 1, ad: 'Güvenlik Görevi', aciklama: null, aktif: true },
  { yetkinlik_id: 2, ad: 'Vardiya Şefi', aciklama: null, aktif: true },
  { yetkinlik_id: 3, ad: 'Müracaat Görevlisi', aciklama: null, aktif: true },
]

const VARDIYA_TIPLERI: VardiyaTipi[] = [
  {
    vardiya_tipi_id: 10,
    ad: 'Gece',
    baslangic_saati: '00:00:00',
    bitis_saati: '08:00:00',
    sure_saat: '8.00',
    gece_mi: true,
    aktif: true,
  },
]

// SRS 3.3.2: Vardiya Şefi, Güvenlik Görevi yetkinliğini DE taşır. Kaybın
// gerçek hayattaki hâli tam olarak budur.
const SEF: Personel = {
  personel_id: 7,
  ad_soyad: 'Demo Şef',
  sicil_no: 'VS-001',
  haftalik_hedef_saat: 40,
  sabit_vardiya_tipi_id: null,
  aktif_baslangic: '2026-01-01',
  aktif_bitis: null,
  yetkinlik_idleri: [1, 2],
}

// FR-1.10. Kasten SIRASIZ verilir: sıralamanın depoda (sunucuda) yapıldığı
// ve arayüzün kendi sırasını uydurmadığı böyle görünür.
const OZEL_GUNLER: OzelGun[] = [
  { tarih: '2026-04-23', ad: 'Ulusal Egemenlik' },
  { tarih: '2026-10-29', ad: 'Cumhuriyet Bayramı' },
]

let gonderilenler: { yol: string; yontem: string; govde: unknown }[] = []

function fetchTaklidi() {
  return vi.fn(async (yol: string, secenekler?: RequestInit) => {
    const yontem = secenekler?.method ?? 'GET'
    if (yontem !== 'GET') {
      gonderilenler.push({
        yol,
        yontem,
        govde: secenekler?.body ? JSON.parse(String(secenekler.body)) : null,
      })
    }
    return {
      ok: true,
      status: 200,
      json: async () => {
        if (yol === '/api/personel') return yontem === 'GET' ? [SEF] : SEF
        if (yol === '/api/yetkinlik') return YETKINLIKLER
        if (yol === '/api/vardiya-tipi') return VARDIYA_TIPLERI
        if (yol === '/api/ozel-gun') return OZEL_GUNLER
        if (yol === '/api/talep') {
          return {
            hucreler: [],
            yuk_gostergesi: {
              haftalik_kisi_vardiya: 0,
              haftalik_kisi_saat: '0',
              asgari_kadro: 0,
            },
          }
        }
        return []
      },
    }
  })
}

function ekraniCiz() {
  gonderilenler = []
  vi.stubGlobal('fetch', fetchTaklidi())
  return render(
    <OturumBaglami.Provider value={{ ben: BEN, cikis: vi.fn(), parolaDegistir: vi.fn() }}>
      {/* Kabuk üst çubuğu çalışan iş göstergesini taşıyor; sağlayıcısı
          olmadan AppShell çizilemez (SDD 6.1). */}
      <AktifIsSaglayici>
        <TanimlarEkrani ekranSec={vi.fn()} />
      </AktifIsSaglayici>
    </OturumBaglami.Provider>,
  )
}

/** Personel sekmesini açıp listeden şefi seçer ve Değiştir'e basar. */
async function sefiDuzenlemeyeAc() {
  ekraniCiz()
  fireEvent.click(await screen.findByRole('button', { name: 'Personel' }))
  fireEvent.click(await screen.findByRole('button', { name: /Demo Şef/ }))
  fireEvent.click(screen.getByRole('button', { name: 'Değiştir' }))
  await waitFor(() => expect(screen.getByLabelText('Güvenlik Görevi')).toBeDefined())
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('Personel formu — yetkinlik kümesi', () => {
  it('iki yetkinlikli personeli değiştirmeden kaydetmek kümeyi AYNEN bırakır', async () => {
    await sefiDuzenlemeyeAc()

    // Form açıldığında iki yetkinlik de işaretli olmalı; biri düşerse zaten
    // kayıp o anda başlıyor demektir.
    expect((screen.getByLabelText('Güvenlik Görevi') as HTMLInputElement).checked).toBe(true)
    expect((screen.getByLabelText('Vardiya Şefi') as HTMLInputElement).checked).toBe(true)
    expect((screen.getByLabelText('Müracaat Görevlisi') as HTMLInputElement).checked).toBe(false)

    fireEvent.click(screen.getByRole('button', { name: 'Kaydet' }))

    await waitFor(() => expect(gonderilenler.length).toBeGreaterThan(0))
    const istek = gonderilenler.find((g) => g.yontem === 'PUT')
    expect(istek).toBeDefined()
    const govde = istek!.govde as { yetkinlik_idleri: number[] }
    expect([...govde.yetkinlik_idleri].sort()).toEqual([1, 2])
  })

  it('yeni bir yetkinlik işaretlemek kümeye EKLER, diğerlerini düşürmez', async () => {
    await sefiDuzenlemeyeAc()
    fireEvent.click(screen.getByLabelText('Müracaat Görevlisi'))
    fireEvent.click(screen.getByRole('button', { name: 'Kaydet' }))

    await waitFor(() => expect(gonderilenler.some((g) => g.yontem === 'PUT')).toBe(true))
    const govde = gonderilenler.find((g) => g.yontem === 'PUT')!.govde as {
      yetkinlik_idleri: number[]
    }
    expect([...govde.yetkinlik_idleri].sort()).toEqual([1, 2, 3])
  })

  it('işareti kaldırmak kümeden ÇIKARIR', async () => {
    await sefiDuzenlemeyeAc()
    fireEvent.click(screen.getByLabelText('Vardiya Şefi'))
    fireEvent.click(screen.getByRole('button', { name: 'Kaydet' }))

    await waitFor(() => expect(gonderilenler.some((g) => g.yontem === 'PUT')).toBe(true))
    const govde = gonderilenler.find((g) => g.yontem === 'PUT')!.govde as {
      yetkinlik_idleri: number[]
    }
    expect(govde.yetkinlik_idleri).toEqual([1])
  })
})

describe('Personel formu — aktiflik ve sabit vardiya (madde 6)', () => {
  it('aktiflik tarihleri ve sabit vardiya gönderilir', async () => {
    await sefiDuzenlemeyeAc()

    // aktif_baslangic artık forma giriyor ve düzenlenebilir; eskiden ekleme
    // sırasında bugüne sabitleniyor, düzenlemede hiç gönderilmiyordu.
    const baslangic = screen.getByLabelText('Aktiflik Başlangıç') as HTMLInputElement
    expect(baslangic.value).toBe('2026-01-01')
    fireEvent.change(baslangic, { target: { value: '2026-02-01' } })

    fireEvent.change(screen.getByLabelText('Sabit Vardiya'), { target: { value: '10' } })
    fireEvent.click(screen.getByRole('button', { name: 'Kaydet' }))

    await waitFor(() => expect(gonderilenler.some((g) => g.yontem === 'PUT')).toBe(true))
    const govde = gonderilenler.find((g) => g.yontem === 'PUT')!.govde as Record<string, unknown>
    expect(govde.aktif_baslangic).toBe('2026-02-01')
    expect(govde.sabit_vardiya_tipi_id).toBe(10)
    expect(govde.aktif_bitis).toBeNull()
  })

  it('personelde yanıltıcı "Aktif" kutusu YOKTUR', async () => {
    // Kutu kaldırıldığında hiçbir şey yapmıyordu: aktif_bitis gönderilmiyor,
    // sunucu da exclude_unset ile alanı atlıyordu. Aktiflik burada bir bayrak
    // değil, iki tarih alanı (SDD 4.2.1).
    await sefiDuzenlemeyeAc()
    expect(screen.queryByLabelText('Aktif')).toBeNull()
    expect(screen.getByLabelText('Aktiflik Bitiş')).toBeDefined()
  })
})

describe('Personel formu — yetkinlik çakışma uyarısı', () => {
  it('uyarı ENGEL değildir: form yine de kaydedebilmelidir', async () => {
    await sefiDuzenlemeyeAc()
    fireEvent.click(screen.getByLabelText('Müracaat Görevlisi'))
    expect(screen.getByText(/karşılıklı dışlayıcı/)).toBeDefined()
    // TD-9: dışlayıcılık veri düzeni sözleşmesidir, kural değil — kaydetme
    // düğmesi bu yüzden açık kalır.
    expect((screen.getByRole('button', { name: 'Kaydet' }) as HTMLButtonElement).disabled).toBe(
      false,
    )
  })
})

describe('Özel Gün sekmesi (FR-1.10)', () => {
  /**
   * Bu sekmenin varlık nedeni bir boşluktu: `ozel_gun` tablosu ve çözücü
   * tarafı baştan beri vardı (baglam_kurucu dönemdeki özel günleri okur,
   * TD-3 onları hafta sonuyla aynı sayaca ekler), ama tabloya satır
   * ekleyecek hiçbir uç nokta ve hiçbir ekran yoktu — yani talep
   * matrisinin `resmi_tatil` sütunu hiçbir zaman tetiklenemiyordu.
   */
  async function sekmeyiAc() {
    ekraniCiz()
    fireEvent.click(await screen.findByRole('button', { name: 'Özel Gün' }))
    await waitFor(() => expect(screen.getByText('Cumhuriyet Bayramı')).toBeDefined())
  }

  it('işaretli günleri listeler', async () => {
    await sekmeyiAc()
    expect(screen.getByText('2026-04-23')).toBeDefined()
    expect(screen.getByText('Ulusal Egemenlik')).toBeDefined()
  })

  it('eylem çubuğu diğer sekmelerle aynı üçlüyü taşır', async () => {
    // SDD 6.3.1: "aynı konumda ve aynı sırada". Bu sekme ortak makineden
    // beslenmiyor (aktif bayrağı ve kullanım sayımı yok), ama kullanıcının
    // gördüğü düzen değişmemeli.
    await sekmeyiAc()
    expect(screen.getByRole('button', { name: 'Ekle' })).toBeDefined()
    expect(screen.getByRole('button', { name: 'Değiştir' })).toBeDefined()
    expect(screen.getByRole('button', { name: 'Sil' })).toBeDefined()
  })

  it('Değiştir ve Sil, seçim yapılmadan kapalıdır', async () => {
    await sekmeyiAc()
    expect((screen.getByRole('button', { name: 'Değiştir' }) as HTMLButtonElement).disabled).toBe(
      true,
    )
    expect((screen.getByRole('button', { name: 'Sil' }) as HTMLButtonElement).disabled).toBe(true)

    fireEvent.click(screen.getByRole('button', { name: /Cumhuriyet Bayramı/ }))
    expect((screen.getByRole('button', { name: 'Değiştir' }) as HTMLButtonElement).disabled).toBe(
      false,
    )
  })

  it('yeni bir tatil işaretlemek tarih ve adı gönderir', async () => {
    await sekmeyiAc()
    fireEvent.click(screen.getByRole('button', { name: 'Ekle' }))

    fireEvent.change(screen.getByLabelText('Tarih'), { target: { value: '2026-05-19' } })
    fireEvent.change(screen.getByLabelText('Tatil Adı'), { target: { value: '19 Mayıs' } })
    fireEvent.click(screen.getByRole('button', { name: 'Kaydet' }))

    await waitFor(() => expect(gonderilenler.some((g) => g.yol === '/api/ozel-gun')).toBe(true))
    const istek = gonderilenler.find((g) => g.yol === '/api/ozel-gun')!
    expect(istek.yontem).toBe('POST')
    expect(istek.govde).toEqual({ tarih: '2026-05-19', ad: '19 Mayıs' })
  })

  it('düzenleme kipinde TARİH salt okunurdur', async () => {
    // Tarih birincil anahtardır (SDD 4.2.1); değiştirmek yeni kayıt açmakla
    // aynı şey ve o yol zaten Ekle ile açık.
    await sekmeyiAc()
    fireEvent.click(screen.getByRole('button', { name: /Cumhuriyet Bayramı/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Değiştir' }))

    const tarihAlani = screen.getByLabelText('Tarih') as HTMLInputElement
    expect(tarihAlani.disabled).toBe(true)
    expect(tarihAlani.value).toBe('2026-10-29')
    expect((screen.getByLabelText('Tatil Adı') as HTMLInputElement).value).toBe(
      'Cumhuriyet Bayramı',
    )
  })

  it('silme, tarihi yol parçası olarak gönderir', async () => {
    await sekmeyiAc()
    fireEvent.click(screen.getByRole('button', { name: /Ulusal Egemenlik/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Sil' }))

    await waitFor(() => expect(gonderilenler.some((g) => g.yontem === 'DELETE')).toBe(true))
    expect(gonderilenler.find((g) => g.yontem === 'DELETE')!.yol).toBe('/api/ozel-gun/2026-04-23')
  })
})
