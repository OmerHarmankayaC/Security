import { cleanup, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { GirisEkrani } from './GirisEkrani'
import { ciz } from '@/test/ciz'

function fetchYanit(durum: number, govde: unknown) {
  return vi.fn().mockResolvedValue({
    ok: durum >= 200 && durum < 300,
    status: durum,
    json: async () => govde,
  })
}

afterEach(() => {
  // `globals: true` ayarlı olmadığı için testing-library kendi kendine
  // temizlemiyor; temizlenmezse bir sonraki test önceki testin DOM'unu da
  // görür ve "birden fazla eşleşme" hatası verir.
  cleanup()
  vi.unstubAllGlobals()
})

describe('GirisEkrani', () => {
  it('kayıt bağlantısı İÇERMEZ (FR-10.1)', () => {
    // Sistem kurum içi bir araç; hesapları yönetim rolü açar (SRS 5.10).
    // Bir "Kayıt ol" bağlantısı kurumda karşılığı olmayan bir yetki vaat
    // ederdi. Test bunu metin üzerinden arar çünkü bağlantı yanlışlıkla
    // eklenirse en görünür hâli budur.
    const { container } = ciz(<GirisEkrani girisYapildi={vi.fn()} />)
    expect(container.textContent).not.toMatch(/kayıt ol|hesap oluştur|üye ol/i)
    expect(container.querySelectorAll('a')).toHaveLength(0)
  })

  it('kullanıcı adı ve parola alanlarını sunar', () => {
    ciz(<GirisEkrani girisYapildi={vi.fn()} />)
    expect(screen.getByLabelText('Kullanıcı adı')).toBeDefined()
    const parola = screen.getByLabelText('Parola') as HTMLInputElement
    // type=password: parola omuz üstünden okunmasın ve tarayıcı onu parola
    // olarak tanısın.
    expect(parola.type).toBe('password')
  })

  it('alanlar boşken gönderilemez', () => {
    ciz(<GirisEkrani girisYapildi={vi.fn()} />)
    const buton = screen.getByRole('button', { name: 'Giriş Yap' }) as HTMLButtonElement
    expect(buton.disabled).toBe(true)
  })

  it('sunucunun ret metnini olduğu gibi gösterir, yorum eklemez', async () => {
    // SDD 5.1b: yanıt kullanıcının var olup olmadığını ele vermemeli.
    // Sunucu tek bir metin döndürüyor; arayüzün "kullanıcı adı yanlış" gibi
    // bir yorum eklemesi o özeni tek satırda geçersiz kılardı.
    const metin = 'Kullanici adi veya parola hatali'
    vi.stubGlobal('fetch', fetchYanit(401, { detail: metin }))

    const { container } = ciz(<GirisEkrani girisYapildi={vi.fn()} />)
    const kullanici = screen.getByLabelText('Kullanıcı adı') as HTMLInputElement
    const parola = screen.getByLabelText('Parola') as HTMLInputElement

    kullanici.focus()
    const olayAyarla = (alan: HTMLInputElement, deger: string) => {
      const yazici = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype,
        'value',
      )?.set
      yazici?.call(alan, deger)
      alan.dispatchEvent(new Event('input', { bubbles: true }))
    }
    olayAyarla(kullanici, 'birisi')
    olayAyarla(parola, 'bir-parola')

    const form = container.querySelector('form')!
    form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))

    await waitFor(() => {
      expect(screen.getByRole('alert').textContent).toBe(metin)
    })
    // Kullanıcı adının var olup olmadığına dair hiçbir ek ifade yok.
    expect(container.textContent).not.toMatch(/böyle bir kullanıcı|kullanıcı bulunamadı/i)
  })
})
