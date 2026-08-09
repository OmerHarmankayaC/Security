import { type PropsWithChildren, type ReactNode, useEffect, useState } from 'react'
import { api } from '@/api/client'
import type { Donem, VardiyaTipi } from '@/api/types'
import { cn } from '@/lib/utils'
import { buyukHarf } from '@/lib/metin'
import { bugunIso, donemAraligiBicimle, gunlerListesi } from '@/lib/tarih'
import { NAV_GRUPLARI, type NavOgesi } from './nav'

export type { NavOgesi }

interface AppShellProps {
  aktifEkran: NavOgesi
  ekranSec: (ekran: NavOgesi) => void
  baslik: string
  altBaslik?: ReactNode
  aksiyonlar?: ReactNode
  // Yan menüdeki "Planlama Dönemi" bloğunun göstereceği dönem. Dönem seçimi
  // olan ekranlar kendi seçimlerini geçirir; geçirmeyen ekranlarda blok
  // aşağıdaki geçerli-dönem kuralına düşer.
  donemId?: number | null
}

/**
 * Yan menüdeki dönem bloğunun hangi dönemi göstereceği.
 *
 * Ekran bir dönem seçmişse o gösterilir. Seçmemişse `/api/donem`'in dönüş
 * SIRASINA GÜVENİLMEZ (sorgu sırasızdır); bunun yerine backend'in çalışan
 * panelinde uyguladığı kuralın aynısı işletilir: bugünü içeren dönem, yoksa
 * en yakın gelecek dönem, o da yoksa en son geçmiş dönem.
 */
function donemSec(donemler: Donem[], donemId: number | null | undefined): Donem | undefined {
  if (donemId != null) {
    const secili = donemler.find((d) => d.donem_id === donemId)
    if (secili) return secili
  }
  const bugun = bugunIso()
  const sirali = [...donemler].sort((a, b) =>
    a.baslangic_tarihi.localeCompare(b.baslangic_tarihi),
  )
  return (
    sirali.find((d) => d.baslangic_tarihi <= bugun && d.bitis_tarihi >= bugun) ??
    sirali.find((d) => d.baslangic_tarihi > bugun) ??
    sirali[sirali.length - 1]
  )
}

export function AppShell({
  aktifEkran,
  ekranSec,
  baslik,
  altBaslik,
  aksiyonlar,
  donemId,
  children,
}: PropsWithChildren<AppShellProps>) {
  const [donemler, setDonemler] = useState<Donem[]>([])
  const [vardiyaTipleri, setVardiyaTipleri] = useState<VardiyaTipi[]>([])

  useEffect(() => {
    Promise.all([api.donemler(), api.vardiyaTipiListele()])
      .then(([d, v]) => {
        setDonemler(d)
        setVardiyaTipleri(v)
      })
      .catch(() => {
        // Dönem bloğu salt bilgilendirme amaçlı — sessizce boş bırakılır,
        // asıl ekranın kendi veri yükleme hatası zaten görünür olur.
      })
  }, [])

  const donem = donemSec(donemler, donemId)
  const ilkVardiya = vardiyaTipleri[0]
  const vardiyaOzeti = ilkVardiya
    ? `${vardiyaTipleri.length}×${Number(ilkVardiya.sure_saat)}`
    : null

  return (
    <div className="flex min-h-svh bg-canvas text-ink">
      <aside className="sticky top-0 flex h-svh w-[260px] shrink-0 flex-col justify-between overflow-y-auto bg-chrome-base px-[18px] pt-[26px] pb-[22px]">
        <div className="flex flex-col">
          <p className="m-0 text-base font-semibold tracking-wide text-chrome-ink">
            {buyukHarf('Vardiya Çizelgeleme')}
          </p>
          <p className="m-0 mt-[3px] text-xs text-chrome-ink-muted">karar destek aracı</p>

          <nav className="mt-6 flex flex-col">
            {NAV_GRUPLARI.map((grup, i) => (
              <div key={grup.baslik ?? `grup-${i}`} className={cn(i > 0 && 'mt-3.5')}>
                {grup.baslik && (
                  <p className="mb-1 font-condensed text-[10px] tracking-[0.14em] text-chrome-ink-muted">
                    {grup.baslik}
                  </p>
                )}
                <div className="flex flex-col gap-0.5">
                  {grup.ogeler.map((oge) => (
                    <button
                      key={oge}
                      type="button"
                      className={cn(
                        'h-[34px] rounded-sm px-2.5 text-left text-sm text-chrome-ink-muted transition-colors hover:text-chrome-ink',
                        oge === aktifEkran && 'bg-chrome-raised font-medium text-chrome-ink',
                      )}
                      onClick={() => ekranSec(oge)}
                    >
                      {oge}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </nav>
        </div>

        <div className="flex flex-col gap-[22px]">
          <div className="border-t border-chrome-line pt-3">
            <p className="m-0 font-condensed text-[10px] tracking-[0.14em] text-chrome-ink-muted">
              {buyukHarf('Planlama Dönemi')}
            </p>
            {donem ? (
              <>
                <p className="m-0 mt-1.5 font-mono text-sm font-semibold text-chrome-ink">
                  {buyukHarf(donemAraligiBicimle(donem.baslangic_tarihi, donem.bitis_tarihi))}
                </p>
                <p className="m-0 mt-0.5 font-mono text-[10px] text-chrome-ink-muted">
                  {gunlerListesi(donem.baslangic_tarihi, donem.bitis_tarihi).length} gün
                  {vardiyaOzeti ? ` · ${vardiyaOzeti} vardiya` : ''}
                </p>
              </>
            ) : (
              <p className="m-0 mt-1.5 text-sm text-chrome-ink-muted">—</p>
            )}
          </div>
        </div>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 shrink-0 items-center justify-between gap-6 border-b border-rule bg-canvas px-7">
          <div className="flex items-center gap-3">
            <h1 className="m-0 text-lg font-semibold text-ink">{baslik}</h1>
            {altBaslik}
          </div>
          {aksiyonlar && <div className="flex shrink-0 items-center gap-2">{aksiyonlar}</div>}
        </header>
        <main className="flex flex-col gap-5 px-8 py-7">{children}</main>
      </div>
    </div>
  )
}
