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
import { sayiBicimle, sapmaBicimle, BOS } from '@/lib/sayi'
import {
  donemAraligiBicimle,
  gunBasligiParcalari,
  gunEtiketi,
  tarihBicimle,
  tarihUzunBicim,
} from '@/lib/tarih'
import { etkinDiliAyarla } from './etkinDil'

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
    etkinDiliAyarla('tr')
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
  afterEach(() => etkinDiliAyarla('tr'))

  it('ondalık ayracı dile göre değişir', () => {
    etkinDiliAyarla('tr')
    expect(sayiBicimle(3.39, 2)).toBe('3,39')

    etkinDiliAyarla('en')
    expect(sayiBicimle(3.39, 2)).toBe('3.39')
  })

  it('dil değişince önbellekten eski biçimleyici dönmez', () => {
    // Önbellek anahtarı yereli içermeseydi ilk çağrı biçimleyiciyi kilitler
    // ve sayılar dil değiştikten sonra da virgülle yazılırdı.
    etkinDiliAyarla('tr')
    sayiBicimle(1.5, 1)

    etkinDiliAyarla('en')

    expect(sayiBicimle(1.5, 1)).toBe('1.5')
  })

  it('binlik ayracı iki dilde de yoktur', () => {
    // Tasarım Referansı v4: binlik ayracı YOKTUR. Dil bunu değiştirmez.
    etkinDiliAyarla('en')
    expect(sayiBicimle(10000)).toBe('10000')

    etkinDiliAyarla('tr')
    expect(sayiBicimle(10000)).toBe('10000')
  })

  it('sapma işareti dile göre biçimlenir', () => {
    etkinDiliAyarla('en')
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

describe('dile bağlı tarih', () => {
  afterEach(() => etkinDiliAyarla('tr'))

  it('ay adı dile göre yazılır', () => {
    etkinDiliAyarla('tr')
    expect(tarihBicimle('2026-08-31')).toBe('31 Ağustos 2026')

    etkinDiliAyarla('en')
    expect(tarihBicimle('2026-08-31')).toBe('31 August 2026')
  })

  it('dönem aralığı kısaltmaları dile göre', () => {
    etkinDiliAyarla('en')
    expect(donemAraligiBicimle('2026-08-31', '2026-09-06')).toBe('31 Aug – 06 Sep 2026')
  })

  it('gün kısaltması ETKİN DİLİN yereliyle büyütülür', () => {
    // Türkçe yereliyle büyütülseydi "Fri" → "FRİ" olurdu: "i" harfi Türkçe'de
    // noktalı büyür ve İngilizce bir kısaltmada bu apaçık yanlıştır.
    etkinDiliAyarla('en')
    expect(gunBasligiParcalari('2026-09-04').kisaltma).toBe('FRI')

    etkinDiliAyarla('tr')
    expect(gunBasligiParcalari('2026-09-04').kisaltma).toBe('CUM')
  })

  it('uzun biçimde sözcük SIRASI dile göre değişir', () => {
    // Aynı şablonu iki dile dayatmak birinde tuhaf okunurdu.
    etkinDiliAyarla('tr')
    expect(tarihUzunBicim('2026-08-31')).toBe('31 Ağustos Pazartesi')

    etkinDiliAyarla('en')
    expect(tarihUzunBicim('2026-08-31')).toBe('Monday 31 August')
  })

  it('bugün ve yarın çevrilir', () => {
    etkinDiliAyarla('en')
    expect(gunEtiketi('2026-08-31', '2026-08-31')).toBe('Today')
    expect(gunEtiketi('2026-09-01', '2026-08-31')).toBe('Tomorrow')
    expect(gunEtiketi('2026-09-02', '2026-08-31')).toBe('Wednesday')
  })
})
