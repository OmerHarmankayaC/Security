// Dil altyapısının sözleşmesi.
//
// Sözlüğün EKSİKSİZ olduğu burada sınanmıyor çünkü sınanamaz: `en`,
// `typeof tr` olarak tiplendiği için eksik anahtar derlemede hata verir ve
// test dosyasına hiç ulaşamaz. Çalışma anında sınanacak bir şey kalmadığında
// test yazmak, geçmesi garanti bir iddia yazmaktır.
//
// Burada sınanan, tipin yakalayamadıkları: seçimin kalıcılığı, tarayıcı
// dilinden düşüş, `<html lang>`, ve dile bağlı biçimlemenin gerçekten dile
// bağlı olduğu.
import { cleanup, fireEvent, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ciz } from '@/test/ciz'
import { DilSecici } from '@/components/DilSecici'
import { useDil } from './DilBaglami'
import { baslangicDili } from './diller'
import { buyukHarf } from '@/lib/metin'
import { sayiBicimle, sapmaBicimle, yereliAyarla, BOS } from '@/lib/sayi'

function Ornek() {
  const { dil, metin } = useDil()
  return (
    <>
      <span data-testid="dil">{dil}</span>
      <span data-testid="baslik">{metin.giris.baslik}</span>
    </>
  )
}

describe('dil seçimi', () => {
  beforeEach(() => {
    cleanup()
    localStorage.clear()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    yereliAyarla('tr')
  })

  it('sözlüğün etkin dalını verir', () => {
    ciz(<Ornek />, { dil: 'en' })

    expect(screen.getByTestId('baslik').textContent).toBe('Sign in')
  })

  it('seçici dili değiştirir', () => {
    ciz(
      <>
        <DilSecici />
        <Ornek />
      </>,
      { dil: 'tr' },
    )

    fireEvent.click(screen.getByText('English'))

    expect(screen.getByTestId('dil').textContent).toBe('en')
    expect(screen.getByTestId('baslik').textContent).toBe('Sign in')
  })

  it('seçim saklanır', () => {
    ciz(<DilSecici />, { dil: 'tr' })

    fireEvent.click(screen.getByText('English'))

    expect(localStorage.getItem('vardis.dil')).toBe('en')
  })

  it('<html lang> etkin dili taşır', () => {
    ciz(<Ornek />, { dil: 'en' })

    expect(document.documentElement.lang).toBe('en')
  })

  it('etkin dil aria-pressed ile duyurulur', () => {
    // Yalnızca renkle belirtmek görmeyene hiçbir şey söylemezdi.
    ciz(<DilSecici />, { dil: 'tr' })

    expect(screen.getByText('Türkçe').getAttribute('aria-pressed')).toBe('true')
    expect(screen.getByText('English').getAttribute('aria-pressed')).toBe('false')
  })
})

describe('başlangıç dili', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('saklanmış seçim tarayıcı dilini yener', () => {
    localStorage.setItem('vardis.dil', 'en')
    vi.stubGlobal('navigator', { language: 'tr-TR' })

    expect(baslangicDili()).toBe('en')
  })

  it('seçim yoksa tarayıcı Türkçeyse Türkçe açar', () => {
    vi.stubGlobal('navigator', { language: 'tr-TR' })

    expect(baslangicDili()).toBe('tr')
  })

  it('seçim yoksa ve tarayıcı Türkçe değilse İngilizce açar', () => {
    // Türkçe'ye düşmüyoruz: depo halka açık ve gelenlerin çoğu Türkçe
    // bilmiyor. Tarayıcısı Türkçe olan zaten üstteki daldan geçer.
    vi.stubGlobal('navigator', { language: 'de-DE' })

    expect(baslangicDili()).toBe('en')
  })

  it('saklanmış değer bozuksa yok sayılır', () => {
    localStorage.setItem('vardis.dil', 'klingon')
    vi.stubGlobal('navigator', { language: 'tr-TR' })

    expect(baslangicDili()).toBe('tr')
  })

  it('depolama erişimi hata verirse uygulama açılmaya devam eder', () => {
    // Gizli sekmede ya da site verisi kapalıyken `localStorage`a ERİŞMEK
    // yükselir, boş dönmez. Dil tercihi uğruna uygulamanın açılmaması saçma
    // olurdu.
    vi.stubGlobal('localStorage', {
      getItem() {
        throw new Error('erişim yok')
      },
    })
    vi.stubGlobal('navigator', { language: 'tr-TR' })

    expect(baslangicDili()).toBe('tr')
  })
})

describe('dile bağlı biçimleme', () => {
  afterEach(() => yereliAyarla('tr'))

  it('ondalık ayracı dile göre değişir', () => {
    yereliAyarla('tr')
    expect(sayiBicimle(3.39, 2)).toBe('3,39')

    yereliAyarla('en')
    expect(sayiBicimle(3.39, 2)).toBe('3.39')
  })

  it('dil değişince önbellekten eski biçimleyici dönmez', () => {
    // Önbellek anahtarı yereli içermeseydi ilk çağrı biçimleyiciyi kilitler
    // ve sayılar dil değiştikten sonra da virgülle yazılırdı.
    yereliAyarla('tr')
    sayiBicimle(1.5, 1)

    yereliAyarla('en')

    expect(sayiBicimle(1.5, 1)).toBe('1.5')
  })

  it('binlik ayracı iki dilde de yoktur', () => {
    // Tasarım Referansı v4: binlik ayracı YOKTUR. Dil bunu değiştirmez.
    yereliAyarla('en')
    expect(sayiBicimle(10000)).toBe('10000')

    yereliAyarla('tr')
    expect(sayiBicimle(10000)).toBe('10000')
  })

  it('sapma işareti dile göre biçimlenir', () => {
    yereliAyarla('en')
    expect(sapmaBicimle(3.4)).toBe('+3.4')
  })

  it('değersiz hücre uzun tire kullanmaz', () => {
    expect(BOS).toBe('-')
    expect(sayiBicimle(Number.NaN)).toBe(BOS)
  })
})

describe('büyük harf', () => {
  it('varsayılan Türkçedir çünkü çağrıların çoğu VERİYİ büyütür', () => {
    // Görev noktası adı, personel adı, ızgara kısaltması: hepsi kullanıcının
    // girdiği dilde. Arayüz İngilizce'ye alındı diye "İzin" bozulmamalı.
    expect(buyukHarf('izin')).toBe('İZİN')
  })

  it('İngilizce açıkça istenirse İngilizce büyütür', () => {
    expect(buyukHarf('sign in', 'en')).toBe('SIGN IN')
  })

  it('İngilizce metni Türkçe yereliyle büyütmek yanlış sonuç verir', () => {
    // Bu testin işi doğru davranışı değil, TUZAĞI kayda geçirmek: parametre
    // unutulursa çıkan sonuç budur.
    expect(buyukHarf('title')).toBe('TİTLE')
  })
})
