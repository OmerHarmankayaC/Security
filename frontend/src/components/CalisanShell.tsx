// Çalışan Paneli kabuğu (SDD 6.1): tek sütun, mobil öncelikli — Kontrol
// Odası'nın koyu yan menüsünün aksine burada yan menü YOK, koyu şasi tek bir
// üst çubuğa ve altındaki üç sekmeye indirgenmiş (bkz. docs/tasarim/
// "Vardiyalarım/Dönem Özetim/Tercihlerim — Masaüstü (Çalışan).png"). Masaüstünde
// de ortalanmış tek sütun (~720px), iki sütunlu geniş düzen yok — bu yüzden
// mobil sürüm ayrı bir tasarım turu gerektirmiyor (NFR-7).
import type { PropsWithChildren } from 'react'
import { buyukHarf } from '@/lib/metin'
import { donemAraligiBicimle } from '@/lib/tarih'
import { cn } from '@/lib/utils'

export type CalisanSekmesi = 'Vardiyalarım' | 'Dönem Özetim' | 'Tercihlerim'

const SEKMELER: CalisanSekmesi[] = ['Vardiyalarım', 'Dönem Özetim', 'Tercihlerim']

interface Props {
  adSoyad: string
  sicilNo: string
  yetkinlikler: string[]
  donemBaslangic: string | null
  donemBitis: string | null
  aktifSekme: CalisanSekmesi
  sekmeSec: (sekme: CalisanSekmesi) => void
}

export function CalisanShell({
  adSoyad,
  sicilNo,
  yetkinlikler,
  donemBaslangic,
  donemBitis,
  aktifSekme,
  sekmeSec,
  children,
}: PropsWithChildren<Props>) {
  return (
    <div className="min-h-svh bg-canvas text-ink">
      <header className="bg-chrome-base">
        <div className="mx-auto flex max-w-[720px] items-start justify-between gap-6 px-6 py-6">
          <div>
            <p className="m-0 text-lg font-semibold text-chrome-ink">{adSoyad}</p>
            <p className="m-0 mt-0.5 font-mono text-xs text-chrome-ink-muted">
              {sicilNo}
              {yetkinlikler.length > 0 ? ` · ${yetkinlikler.join(', ')}` : ''}
            </p>
          </div>
          <div className="shrink-0 text-right">
            <p className="m-0 font-condensed text-[10px] tracking-[0.14em] text-chrome-ink-muted">
              {buyukHarf('Dönem')}
            </p>
            <p className="m-0 mt-1 font-mono text-sm font-semibold text-chrome-ink">
              {donemBaslangic && donemBitis
                ? buyukHarf(donemAraligiBicimle(donemBaslangic, donemBitis))
                : '—'}
            </p>
          </div>
        </div>
        <nav className="mx-auto flex max-w-[720px] gap-6 px-6">
          {SEKMELER.map((sekme) => (
            <button
              key={sekme}
              type="button"
              onClick={() => sekmeSec(sekme)}
              className={cn(
                'border-b-2 border-transparent px-1 py-3 text-sm text-chrome-ink-muted transition-colors hover:text-chrome-ink',
                sekme === aktifSekme && 'border-accent font-medium text-chrome-ink',
              )}
            >
              {sekme}
            </button>
          ))}
        </nav>
      </header>
      <main className="mx-auto flex max-w-[720px] flex-col gap-5 px-6 py-7">{children}</main>
    </div>
  )
}
