/**
 * Analiz ekranının yeni kartları (SDD 6.3.4).
 *
 * BU TESTLER GÖRSEL DOĞRULAMANIN YERİNE GEÇMEZ. Ekran giriş arkasında ve
 * parola giremediğim için kartları tarayıcıda kendi gözümle göremedim;
 * burada ölçülen şey DAVRANIŞ — hangi sayının nereden geldiği, sıralamanın
 * hangi ölçüye göre olduğu, boş hâlin ne dediği. Yerleşim, okunabilirlik ve
 * ufuk anahtarının görsel durumu insan gözü ister.
 */
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { Analiz, AnalizCezaKalemi, KotaDurumu, KumulatifDegisim } from '../api/types'

import { AnalizEkrani } from './AnalizEkrani'

// İstemci modül düzeyinde taklit edilir; yanıt testten teste değişsin diye
// değiştirilebilir bir değişkenden okunur.
let _cevap: Analiz
const analizGetir = vi.fn()

// AppShell oturum bağlamı ister ve bu testlerin konusu değil; çocuklarını
// döken bir kabukla değiştirilir. Ölçülen şey kartların davranışı.
vi.mock('../components/AppShell', () => ({
  AppShell: ({ children, aksiyonlar }: { children: unknown; aksiyonlar?: unknown }) => (
    <div>
      {aksiyonlar as never}
      {children as never}
    </div>
  ),
}))

vi.mock('../api/client', () => ({
  api: {
    donemler: () =>
      Promise.resolve([
        { donem_id: 1, baslangic_tarihi: '2026-08-17', bitis_tarihi: '2026-08-23' },
      ]),
    personelListele: () => Promise.resolve([]),
    surumler: () =>
      Promise.resolve([{ surum_id: 1, surum_no: 1, durum: 'YAYINLANDI', damga: 'x' }]),
    analizGetir: (...a: unknown[]) => {
      analizGetir(...a)
      return Promise.resolve(_cevap)
    },
  },
}))

// Testler arasi temizlik OTOMATIK DEGIL: onceki render DOM'da kalinca
// sorgular ayni metni iki kez buluyor.
afterEach(cleanup)

const KOTA: KotaDurumu[] = [
  { personel_id: 1, ad_soyad: 'Sınırdaki Kişi', fazla_calisma_saat: 240, kalan_kota_saat: 5 },
  { personel_id: 2, ad_soyad: 'Rahat Kişi', fazla_calisma_saat: 10, kalan_kota_saat: 200 },
]

const KALEMLER: AnalizCezaKalemi[] = [
  { kimlik: 'S1', ad: 'Talep karşılama', ham_deger: 36, agirlik: 10000, agirlikli_ceza: 360000 },
  { kimlik: 'S2', ad: 'Gece adaleti', ham_deger: 148, agirlik: 10, agirlikli_ceza: 1480 },
]

const DEGISIM: KumulatifDegisim = {
  onceki_surum_id: 7,
  onceki_ortalama_sapma: 12.5,
  simdiki_ortalama_sapma: 9.25,
}

function analiz(ek: Partial<Analiz> = {}): Analiz {
  return {
    surum_id: 1,
    kapsama_orani: 0.969,
    fazla_kadro: [],
    toplam_fazla_kadro: 0,
    kisi_basina_gece: [],
    kisi_basina_hafta_sonu: [],
    saat_dagilimi: [],
    en_dengesiz_personel_id: null,
    en_dengesiz_ad_soyad: null,
    tercih_karsilama_orani: null,
    bina_degisim_sayisi: [],
    ceza_dokumu: null,
    toplam_ceza: 361480,
    karsilanmayan_kisi_saat: 36,
    acik_aralik_sayisi: 10,
    kota_durumu: KOTA,
    ceza_kalemleri: KALEMLER,
    kumulatif_degisim: DEGISIM,
    ufuk: 'donem',
    ...ek,
  }
}

function ekraniKur(cevap: Analiz = analiz()) {
  _cevap = cevap
  analizGetir.mockClear()
  render(<AnalizEkrani ekranSec={vi.fn()} donemId={1} donemIdSec={vi.fn()} />)
}

describe('Analiz ekranı — üst şerit', () => {
  it('karşılanmayan KİŞİ-SAAT ile AÇIK ARALIK SAYISINI ayrı gösterir', async () => {
    // İkisi ayrı ölçülerdir: ardışık saatler tek kayıtta birleştiği için
    // satır sayısı yükü anlatmaz. Karıştırıldılar ve dışa aktarma
    // başlığında yanlış sayı gösterildi (SDD 6.3.4).
    ekraniKur()

    expect(await screen.findByText(/10 açık aralık/)).toBeDefined()
    expect(screen.getAllByText(/kişi-saat/).length).toBeGreaterThan(0)
  })
})

describe('Analiz ekranı — ufuk anahtarı', () => {
  it('seçilen ufku sunucuya iletir ve hangisinin seçili olduğunu gösterir', async () => {
    ekraniKur()

    const donemDugmesi = await screen.findByRole('button', { name: /Planlama dönemi/ })
    expect(donemDugmesi.getAttribute('aria-pressed')).toBe('true')

    fireEvent.click(screen.getByRole('button', { name: /Adalet ufku/ }))
    // İki ufkun sayıları farklıdır; istek yeniden gitmezse tablo eski
    // ufkun sayılarını yeni etiketle gösterirdi.
    await waitFor(() => expect(analizGetir).toHaveBeenCalledWith(1, 'adalet'))
  })
})

describe('Analiz ekranı — kota kartı', () => {
  it('sınıra dayananı ÜSTTE gösterir ve riski adlandırır', async () => {
    ekraniKur()

    // Kartın amacı listeyi değil riski göstermek: kotası dolmak üzere olan
    // kişi görünmeli, rahat olan filtrelenmeli.
    expect(await screen.findByText('Sınırdaki Kişi')).toBeDefined()
    expect(screen.queryByText('Rahat Kişi')).toBeNull()
    expect(screen.getByText(/kalan kotası 40 saatin altında/)).toBeDefined()
  })
})

describe('Analiz ekranı — ceza dökümü', () => {
  it('ham değer, ağırlık ve ağırlıklı cezayı AYRI sütunlarda verir', async () => {
    ekraniKur()

    // Hedefler ADLARIYLA listelenir; "S2" tek başına kimseye bir şey söylemez.
    expect((await screen.findAllByText('Gece adaleti')).length).toBeGreaterThan(0)
    expect(screen.getByText(/HAM DEĞER/)).toBeDefined()
    expect(screen.getByText(/AĞIRLIKLI CEZA/)).toBeDefined()
  })
})

describe('Analiz ekranı — kümülatif değişim', () => {
  it('sapma azalıyorsa bunu söyler', async () => {
    ekraniKur()
    expect((await screen.findAllByText(/azalıyor/)).length).toBeGreaterThan(0)
  })

  it('önceki dönem yoksa SIFIR yazmaz, yokluğu söyler', async () => {
    // "Değişim olmadı" ile "karşılaştırılacak dönem yok" aynı şey değildir.
    ekraniKur(
      analiz({
        kumulatif_degisim: {
          onceki_surum_id: null,
          onceki_ortalama_sapma: null,
          simdiki_ortalama_sapma: 9.25,
        },
      }),
    )
    expect(await screen.findByText(/önceki yayınlanmış dönem yok/)).toBeDefined()
  })
})
describe('Analiz ekranı — adalet grafiği', () => {
  const kisiler = [
    { personel_id: 1, ad_soyad: 'Osman Kurt', sayi: 26, pay: 11 },
    { personel_id: 2, ad_soyad: 'Ayşe Demir', sayi: 0, pay: 11 },
    { personel_id: 3, ad_soyad: 'Kemal Uçar', sayi: 11, pay: 11 },
  ]

  it('sapmanın YÖNÜNÜ işaretle gösterir', async () => {
    // Eskiden sayı işaretsizdi ve yön yalnızca çubuğun konumundan
    // okunuyordu: payının 15 saat ÜSTÜNDE olan ile 11 saat ALTINDA olan
    // ekranda aynı görünüyordu.
    ekraniKur(analiz({ kisi_basina_gece: kisiler as never }))

    expect(await screen.findByText('+15 sa')).toBeDefined()
    expect(screen.getByText('−11 sa')).toBeDefined()
  })

  it('payını tutturan satırda sapma yerine tire gösterir', async () => {
    ekraniKur(analiz({ kisi_basina_gece: kisiler as never }))

    await screen.findByText('+15 sa')
    // Kemal payını tam tutturdu: ne fazla ne eksik, çubuk hiç çizilmez.
    expect(screen.getAllByText('—').length).toBeGreaterThan(0)
  })

  it('sütun başlıkları yazılıdır', async () => {
    // Üç sayı (yük / adil pay / sapma) başlıksız durduğunda üçüncüsünün ne
    // olduğu ancak fareyle üstüne gelince anlaşılıyordu.
    ekraniKur(analiz({ kisi_basina_gece: kisiler as never }))

    await screen.findByText('+15 sa')
    expect(screen.getAllByText(/Adil pay/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/Yük/i).length).toBeGreaterThan(0)
  })
})
