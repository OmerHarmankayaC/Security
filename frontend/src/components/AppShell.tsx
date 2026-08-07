import type { PropsWithChildren, ReactNode } from 'react'
import { cn } from '@/lib/utils'
import { NAV_OGELERI, type NavOgesi } from './nav'

export type { NavOgesi }

interface AppShellProps {
  aktifEkran: NavOgesi
  ekranSec: (ekran: NavOgesi) => void
  baslik: string
  altBaslik?: string
  aksiyonlar?: ReactNode
}

export function AppShell({
  aktifEkran,
  ekranSec,
  baslik,
  altBaslik,
  aksiyonlar,
  children,
}: PropsWithChildren<AppShellProps>) {
  return (
    <div className="flex min-h-svh bg-background">
      <aside className="w-[260px] shrink-0 border-r border-border bg-card p-6">
        <p className="mb-6 text-base font-semibold text-foreground">Vardiya Çizelgeleme</p>
        <nav className="flex flex-col gap-1">
          {NAV_OGELERI.map((oge) => (
            <button
              key={oge}
              type="button"
              className={cn(
                'rounded-md px-3 py-2 text-left text-sm text-muted-foreground transition-colors hover:bg-muted',
                oge === aktifEkran && 'bg-accent font-medium text-primary hover:bg-accent',
              )}
              onClick={() => ekranSec(oge)}
            >
              {oge}
            </button>
          ))}
        </nav>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-[88px] shrink-0 items-center justify-between gap-6 border-b border-border bg-card px-10">
          <div>
            <h1 className="m-0 text-xl font-semibold text-foreground">{baslik}</h1>
            {altBaslik && <p className="mt-1 text-sm text-muted-foreground">{altBaslik}</p>}
          </div>
          {aksiyonlar && <div className="flex shrink-0 gap-2">{aksiyonlar}</div>}
        </header>
        <main className="flex flex-col gap-6 px-10 py-8">{children}</main>
      </div>
    </div>
  )
}
