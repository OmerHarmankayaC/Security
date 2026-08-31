// Testler için dil sağlayıcısıyla saran render.
//
// `useDil()` sağlayıcı yoksa BİLEREK yükselir; sessizce Türkçe'ye düşseydi
// sağlayıcıyı sarmayı unutan bir ağaç İngilizce arayüzde Türkçe metin çizer
// ve bunu ancak o dilde bakan biri fark ederdi. O katılığın bedeli, her
// bileşen testinin sarmalayıcıyı elle kurması olurdu: kırk dosyada aynı üç
// satır, ve biri unutulduğunda anlaşılmaz bir yığın izi.
//
// Bu yardımcı bedeli tek yerde ödüyor. `dil` parametresi ayrıca testin
// metni HANGİ DİLDE beklediğini açıkça yazmasını sağlar; varsayılan Türkçe,
// çünkü sözlüğün kaynak dili odur.
import { render, type RenderOptions, type RenderResult } from '@testing-library/react'
import type { ReactElement, ReactNode } from 'react'
import { DilSaglayici } from '@/i18n/DilBaglami'
import type { Dil } from '@/i18n/diller'

const ANAHTAR = 'vardis.dil'

/**
 * Bileşeni dil sağlayıcısı içinde çizer.
 *
 * Dil `localStorage` üzerinden veriliyor çünkü `DilSaglayici` başlangıç
 * dilini oradan okuyor; sağlayıcıya doğrudan bir "dil" özelliği eklemek,
 * yalnızca testin ihtiyacı olan bir kapıyı üretim koduna açmak olurdu.
 */
export function ciz(
  ogel: ReactElement,
  { dil = 'tr', ...secenekler }: RenderOptions & { dil?: Dil } = {},
): RenderResult {
  try {
    localStorage.setItem(ANAHTAR, dil)
  } catch {
    // Depolama yoksa sağlayıcı tarayıcı diline düşer; jsdom'da o da 'en'
    // olabilir. Testler dili açıkça verdiğinde bu yol zaten kullanılmaz.
  }
  return render(ogel, {
    wrapper: ({ children }: { children: ReactNode }) => (
      <DilSaglayici>{children}</DilSaglayici>
    ),
    ...secenekler,
  })
}
