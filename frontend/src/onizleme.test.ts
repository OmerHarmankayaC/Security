// Paylaşım kartının ve robots.txt'in sözleşmesi.
//
// İkisi de STATİK DOSYA ve hiçbir bileşen onlara dokunmuyor; yani bir gün
// silinseler ne derleme, ne tip denetimi, ne de başka bir test bunu
// yakalardı. Kusur da sessizdir: uygulama açılır, çalışır, yalnızca
// paylaşılan bağlantı çıplak bir URL olarak görünür ve site aramada
// bulunmaz. Bu dosyanın tek işi o sessizliği bozmak.
//
// Dosyalar KAYNAKTAN okunuyor, `dist`ten değil: `dist` derleme çıktısıdır
// ve testin derlemeye bağlanması, testi "önce build koş" koşuluna bağlardı.
// Vite `public/` altını olduğu gibi kopyalar, `index.html`i de dönüştürmez.
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const kok = resolve(__dirname, '..')
const indexHtml = readFileSync(resolve(kok, 'index.html'), 'utf-8')
const robots = readFileSync(resolve(kok, 'public/robots.txt'), 'utf-8')

/**
 * `<meta property="og:x" content="...">` ya da `name="twitter:x"`.
 *
 * `\s+` satır sonunu da yutar, dolayısıyla uzun içerikler için üç satıra
 * yayılmış etiketler de aynı desenle yakalanır; ayrı bir "çok satırlı"
 * dalı yok, çünkü gereksiz olurdu.
 */
function etiket(ad: string): string | null {
  const desen = new RegExp(`<meta\\s+(?:property|name)="${ad}"\\s+content="([^"]*)"`, 's')
  return desen.exec(indexHtml)?.[1] ?? null
}

describe('önizleme kartı', () => {
  it.each([
    'og:title',
    'og:description',
    'og:image',
    'og:url',
    'og:type',
    'twitter:card',
  ])('%s etiketi var ve boş değil', (ad) => {
    expect(etiket(ad)).toBeTruthy()
  })

  it('twitter:card büyük görselli karttır', () => {
    // `summary` olsaydı görsel küçük bir kare olarak çıkar, ızgara okunmazdı.
    expect(etiket('twitter:card')).toBe('summary_large_image')
  })

  it('og:image ve og:url MUTLAK adrestir', () => {
    // Kazıyıcıların çoğu göreli yolu çözmez; göreli verilen bir görsel
    // kartı görselsiz bırakır ve bunu ancak paylaşan kişi fark eder.
    expect(etiket('og:image')).toMatch(/^https:\/\//)
    expect(etiket('og:url')).toMatch(/^https:\/\//)
  })

  it('açıklama verinin üretilmiş olduğunu söyler', () => {
    // Kart bağlamdan kopuk görülür; gösterim şeridi ancak sayfa açılınca
    // görünür, dolayısıyla bunu söyleyen tek yer burasıdır.
    expect(etiket('og:description')?.toLowerCase()).toContain('generated')
  })
})

describe('robots.txt', () => {
  it('bütün gezginlere izin verir', () => {
    expect(robots).toMatch(/^User-agent:\s*\*/m)
    expect(robots).toMatch(/^Allow:\s*\//m)
  })

  it('hiçbir şeyi yasaklamaz', () => {
    // `Disallow: /` dosyanın tamamını kapatır ve bunu geri getirmek tek
    // satırlık bir düzenlemedir; testin yakaladığı şey tam olarak odur.
    expect(robots).not.toMatch(/^Disallow:\s*\/\s*$/m)
  })
})
