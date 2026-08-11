// Çalışan Paneli kabuğu (SDD 6.1, Tasarım Referansı sürüm 4): tek sütun,
// mobil öncelikli — Kontrol
// Odası'nın koyu yan menüsünün aksine burada yan menü YOK, koyu şasi tek bir
// üst çubuğa ve altındaki üç sekmeye indirgenmiş (bkz. docs/tasarim/
// "Vardiyalarım/Dönem Özetim/Tercihlerim — Masaüstü (Çalışan).png"). Masaüstünde
// de ortalanmış tek sütun (~720px), iki sütunlu geniş düzen yok — bu yüzden
// mobil sürüm ayrı bir tasarım turu gerektirmiyor (NFR-7).
import type { PropsWithChildren } from 'react'
import { buyukHarf } from '@/lib/metin'
import { donemAraligiBicimle } from '@/lib/tarih'
import { cn } from '@/lib/utils'
import { useOturum } from './OturumBaglami'

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
  const { cikis, parolaDegistir } = useOturum()
  return (
    <div className="min-h-svh bg-canvas text-ink">
      <header className="bg-chrome-base">
        <div className="mx-auto flex max-w-[720px] items-start justify-between gap-6 px-6 py-6">
          <div>
            {/* Çalışan panelinde ekran adı yoktur; üst çubuğun taşıdığı ad
                bu iskeletin `başlık/ekran`ıdır. */}
            <p className="m-0 text-baslik-ekran font-semibold text-chrome-ink">{adSoyad}</p>
            {/* Yalnızca sicil mono: yetkinlik adları ("Güvenlik", "İlk Yardım")
                düz metindir (TASARIM_REFERANSI.md — "Düz cümle asla Mono
                değildir"). */}
            <p className="m-0 mt-0.5 text-mono-kucuk text-chrome-ink-muted">
              <span className="font-mono">{sicilNo}</span>
              {yetkinlikler.length > 0 ? ` · ${yetkinlikler.join(', ')}` : ''}
            </p>
          </div>
          <div className="shrink-0 text-right">
            <p className="etiket-caps m-0 text-chrome-ink-muted">{buyukHarf('Dönem')}</p>
            <p className="m-0 mt-1 font-mono text-sayi-orta font-semibold text-chrome-ink">
              {donemBaslangic && donemBitis
                ? buyukHarf(donemAraligiBicimle(donemBaslangic, donemBitis))
                : '—'}
            </p>
            {/* Oturum eylemleri üst çubukta, dönem bilgisinin altında:
                mobil öncelikli tek sütunda ayrı bir menü açmak, üç sekmelik
                bir panelde taşıdığından fazla yapı olurdu. */}
            <div className="mt-2 flex justify-end gap-3">
              <button
                type="button"
                onClick={parolaDegistir}
                className="text-xs text-chrome-ink-muted underline-offset-2 transition-colors hover:text-chrome-ink hover:underline"
              >
                Parola
              </button>
              <button
                type="button"
                onClick={cikis}
                className="text-xs text-chrome-ink-muted underline-offset-2 transition-colors hover:text-chrome-ink hover:underline"
              >
                Çıkış
              </button>
            </div>
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
