import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'

/**
 * Madde 5 nöbetçisi: tarih biçimlemesinin TEK yardımcıda kalmasını kaynak
 * dosyaları tarayarak doğrular.
 *
 * Gerekçe: "her yer buradan geçsin" bir yorum olarak yazıldığında bir sonraki
 * ekranda sessizce delinir — bu projede aynı sorun `new Date()` ile üç ayrı
 * yerde yaşandı (biri UTC'ye göre kestiği için Türkiye'de gece yarısından
 * 03:00'e kadar yanlış "bugün" veriyordu). Kural testle tutulur.
 *
 * `lib/tarih.ts` bu taramanın dışındadır; tek biçimlemenin yapıldığı yer orasıdır.
 */
const KAYNAK_KOKU = fileURLToPath(new URL('..', import.meta.url))
const MUAF_DOSYALAR = ['lib/tarih.ts']

const YASAKLI_KALIPLAR: { ad: string; desen: RegExp; neden: string }[] = [
  {
    ad: 'new Date(...) ile tarih ayrıştırma',
    desen: /new Date\(\s*[`'"]/,
    neden: 'isoAyristir veya utcTarihiAyristir kullanın',
  },
  {
    ad: 'toISOString ile "bugün" hesabı',
    desen: /toISOString\(\)\s*\.slice/,
    neden: 'bugunIso() kullanın — toISOString UTC’ye göre keser',
  },
  {
    ad: 'toLocaleDateString / toLocaleTimeString / tarihli toLocaleString',
    desen: /toLocale(Date|Time)String\(|toLocaleString\('tr-TR',\s*\{[^}]*(day|month|year|hour|minute)/,
    neden: 'lib/tarih.ts’teki biçimleyicileri kullanın',
  },
]

function kaynakDosyalari(dizin: string, kok = dizin): string[] {
  return readdirSync(dizin).flatMap((ad) => {
    const yol = join(dizin, ad)
    if (statSync(yol).isDirectory()) return kaynakDosyalari(yol, kok)
    if (!/\.tsx?$/.test(ad) || /\.test\.tsx?$/.test(ad)) return []
    return [yol.slice(kok.length)]
  })
}

describe('tarih biçimleme tek kaynakta', () => {
  const dosyalar = kaynakDosyalari(KAYNAK_KOKU).filter((d) => !MUAF_DOSYALAR.includes(d))

  it('taranacak kaynak dosya bulur', () => {
    // Tarama yolu bozulursa test sessizce "hiç ihlal yok" demesin.
    expect(dosyalar.length).toBeGreaterThan(10)
  })

  it.each(YASAKLI_KALIPLAR)('$ad hiçbir ekranda kullanılmaz', ({ desen, neden }) => {
    const ihlaller = dosyalar.filter((dosya) =>
      desen.test(readFileSync(join(KAYNAK_KOKU, dosya), 'utf8')),
    )
    expect(ihlaller, `${ihlaller.join(', ')} → ${neden}`).toEqual([])
  })
})
