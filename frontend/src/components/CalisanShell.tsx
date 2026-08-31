// Çalışan Paneli kabuğu (SDD 6.1, Tasarım Referansı sürüm 4): tek sütun,
// mobil öncelikli — Kontrol
// Odası'nın koyu yan menüsünün aksine burada yan menü YOK, koyu şasi tek bir
// üst çubuğa ve altındaki üç sekmeye indirgenmiş (bkz. docs/tasarim/
// "Vardiyalarım/Dönem Özetim/Tercihlerim — Masaüstü (Çalışan).png"). Masaüstünde
// de ortalanmış tek sütun (~720px), iki sütunlu geniş düzen yok — bu yüzden
// mobil sürüm ayrı bir tasarım turu gerektirmiyor (NFR-7).
import { useState, type PropsWithChildren } from 'react'
import { buyukHarf } from '@/lib/metin'
import { donemAraligiBicimle } from '@/lib/tarih'
import { cn } from '@/lib/utils'
import { useOturum } from './OturumBaglami'
import { KunyeIcerigi } from './KunyeIcerigi'

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
  const [kunyeAcik, kunyeAc] = useState(false)
  return (
    // `min-h-svh` DEĞİL `flex-1`: gösterim şeridi eklendiğinde toplam
    // yükseklik şerit kadar taşıyor ve sayfa gereksiz yere kayıyordu.
    <div className="flex-1 bg-canvas text-ink">
      <header className="bg-chrome-base">
        <div className="mx-auto flex max-w-[720px] flex-col gap-4 px-6 py-6 sm:flex-row sm:items-start sm:justify-between sm:gap-6">
          <div className="min-w-0">
            {/* Çalışan panelinde ekran adı yoktur; üst çubuğun taşıdığı ad
                bu iskeletin `başlık/ekran`ıdır. */}
            <p className="m-0 text-baslik-ekran font-semibold text-chrome-ink">{adSoyad}</p>
            {/* Yalnızca sicil mono: yetkinlik adları ("Güvenlik", "İlk Yardım")
                düz metindir (TASARIM_REFERANSI.md — "Düz cümle asla Mono
                değildir"). min-w-0 + truncate: yetkinlik listesi uzadığında
                375px'te dönem bloğunu sıkıştırıyordu (NFR-7). */}
            <p className="m-0 mt-0.5 truncate text-mono-kucuk text-chrome-ink-muted">
              <span className="font-mono">{sicilNo}</span>
              {yetkinlikler.length > 0 ? ` · ${yetkinlikler.join(', ')}` : ''}
            </p>
          </div>
          {/* flex + justify-between: 375px'te bu satırın TAM İKİ çocuğu
              olmalı (bilgi grubu | eylem grubu) — üçüncü bir doğrudan çocuk
              justify-between'i üçe böler ve etiketi değerinden koparır,
              bu yüzden dönem etiketi + tarihi kendi sarmalayıcısına alındı. */}
          <div className="flex items-end justify-between gap-4 sm:block sm:shrink-0 sm:text-right">
            <div>
              <p className="etiket-caps m-0 text-chrome-ink-muted">{buyukHarf('Dönem')}</p>
              <p className="m-0 mt-1 font-mono text-sayi-orta font-semibold text-chrome-ink">
                {donemBaslangic && donemBitis
                  ? buyukHarf(donemAraligiBicimle(donemBaslangic, donemBitis))
                  : '—'}
              </p>
            </div>
            {/* Oturum eylemleri üst çubukta, dönem bilgisinin altında:
                mobil öncelikli tek sütunda ayrı bir menü açmak, üç sekmelik
                bir panelde taşıdığından fazla yapı olurdu. */}
            <div className="mt-2 flex justify-end gap-3">
              {/* KÜNYE SEKME DEĞİL BAĞLANTI: çalışanın kendi verisi değil,
                  ürünün bilgisi. Dördüncü bir sekme olsaydı üç sekmelik
                  panelin ritmini bozardı. */}
              <button
                type="button"
                onClick={() => kunyeAc(true)}
                className="text-xs text-chrome-ink-muted underline-offset-2 transition-colors hover:text-chrome-ink hover:underline"
              >
                Künye
              </button>
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
        {/* overflow-x-auto: taşan sekmeler kaydırılabilir olsun diye; yan etki
            olarak dikey eksen de 'auto' sayılır ve odak halkası kırpılabilir —
            burada kabul edilebilir (NFR-7, sekmelerin erişilebilirliği kritik). */}
        <nav className="mx-auto flex max-w-[720px] gap-6 overflow-x-auto px-6">
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
      <main className="mx-auto flex max-w-[720px] flex-col gap-5 px-6 py-7">
        {kunyeAcik ? (
          <>
            <button
              type="button"
              onClick={() => kunyeAc(false)}
              className="self-start text-sm text-accent underline-offset-2 hover:underline"
            >
              ← Panele dön
            </button>
            <KunyeIcerigi />
          </>
        ) : (
          children
        )}
      </main>
    </div>
  )
}
