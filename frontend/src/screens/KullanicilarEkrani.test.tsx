import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { Ben, Kullanici, Personel } from '@/api/types'
import { OturumBaglami } from '@/components/OturumBaglami'
import { KullanicilarEkrani } from './KullanicilarEkrani'

const BEN: Ben = {
  kullanici_adi: 'yonetim',
  rol: 'yonetim',
  parola_degistirmeli: false,
  personel_id: null,
  ad_soyad: null,
}

const KULLANICILAR: Kullanici[] = [
  {
    kullanici_id: 1,
    kullanici_adi: 'yonetim',
    rol: 'yonetim',
    personel_id: null,
    ad_soyad: null,
    aktif: true,
    parola_degistirmeli: false,
    kilitli_mi: false,
  },
  {
    kullanici_id: 2,
    kullanici_adi: 'ahmet.yilmaz',
    rol: 'calisan',
    personel_id: 7,
    ad_soyad: 'Ahmet Yılmaz',
    aktif: true,
    parola_degistirmeli: true,
    kilitli_mi: false,
  },
  {
    kullanici_id: 3,
    kullanici_adi: 'eski.hesap',
    rol: 'yonetici',
    personel_id: null,
    ad_soyad: null,
    aktif: false,
    parola_degistirmeli: false,
    kilitli_mi: false,
  },
]

const PERSONELLER: Personel[] = []

function fetchTaklidi() {
  return vi.fn(async (yol: string) => ({
    ok: true,
    status: 200,
    json: async () => {
      if (yol === '/api/kullanici') return KULLANICILAR
      if (yol === '/api/personel') return PERSONELLER
      // AppShell'in yan menü dönem bloğu için sorduğu uçlar.
      return []
    },
  }))
}

function ekraniCiz() {
  vi.stubGlobal('fetch', fetchTaklidi())
  return render(
    <OturumBaglami.Provider
      value={{ ben: BEN, cikis: vi.fn(), parolaDegistir: vi.fn() }}
    >
      <KullanicilarEkrani ekranSec={vi.fn()} kendiKullaniciAdi="yonetim" />
    </OturumBaglami.Provider>,
  )
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('KullanicilarEkrani', () => {
  it('eylem çubuğu Tanımlar ekranındaki düzeni izler ve SİL İÇERMEZ', async () => {
    // FR-10.5: hesap silinmez, devre dışı bırakılır. Bir "Sil" düğmesi,
    // yapılmayan bir işi vaat ederdi; devre dışı bırakma düzenleme
    // kipindeki bir alandır (Tanımlar ekranındaki aktiflik alanıyla aynı).
    ekraniCiz()
    await waitFor(() => expect(screen.getByRole('button', { name: 'Ekle' })).toBeDefined())

    expect(screen.getByRole('button', { name: 'Değiştir' })).toBeDefined()
    expect(screen.getByRole('button', { name: 'Parola Sıfırla' })).toBeDefined()
    expect(screen.queryByRole('button', { name: 'Sil' })).toBeNull()
    expect(screen.queryByRole('button', { name: /kalıcı olarak sil/i })).toBeNull()
  })

  it('bir kayıt seçilene kadar Değiştir ve Parola Sıfırla pasiftir', async () => {
    ekraniCiz()
    await waitFor(() => expect(screen.getByRole('button', { name: 'Ekle' })).toBeDefined())

    expect((screen.getByRole('button', { name: 'Değiştir' }) as HTMLButtonElement).disabled).toBe(
      true,
    )
    expect(
      (screen.getByRole('button', { name: 'Parola Sıfırla' }) as HTMLButtonElement).disabled,
    ).toBe(true)
    // "Ekle" seçim istemez.
    expect((screen.getByRole('button', { name: 'Ekle' }) as HTMLButtonElement).disabled).toBe(
      false,
    )
  })

  it('hesapları rol ve durumlarıyla listeler', async () => {
    ekraniCiz()
    await waitFor(() => expect(screen.getByText('ahmet.yilmaz')).toBeDefined())

    // Çalışan hesabı bağlı olduğu personelle birlikte görünür (FR-10.6).
    expect(screen.getByText(/Çalışan · Ahmet Yılmaz/)).toBeDefined()
    // Parola borcu listede işaretlenir (FR-10.7).
    expect(screen.getByText('PAROLA BEKLİYOR')).toBeDefined()
    // Giriş yapılan hesap ayırt edilir: kendi hesabında bazı işlemler yasak.
    expect(screen.getByText(/bu hesapla girdiniz/)).toBeDefined()
  })

  it('pasif hesabı varsayılan olarak gizler, kaç tane gizlendiğini yazar', async () => {
    ekraniCiz()
    await waitFor(() => expect(screen.getByText('ahmet.yilmaz')).toBeDefined())

    expect(screen.queryByText('eski.hesap')).toBeNull()
    expect(screen.getByText('1 pasif kayıt gizli.')).toBeDefined()
  })
})
