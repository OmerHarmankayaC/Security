import type { PropsWithChildren, ReactNode } from 'react'
import { NAV_OGELERI, type NavOgesi } from './nav'
import './AppShell.css'

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
    <div className="shell">
      <aside className="sidebar">
        <p className="sidebar__wordmark">Vardiya Çizelgeleme</p>
        <nav className="sidebar__nav">
          {NAV_OGELERI.map((oge) => (
            <button
              key={oge}
              type="button"
              className={`sidebar__item ${oge === aktifEkran ? 'sidebar__item--aktif' : ''}`}
              onClick={() => ekranSec(oge)}
            >
              {oge}
            </button>
          ))}
        </nav>
      </aside>
      <div className="shell__main">
        <header className="topbar">
          <div>
            <h1 className="topbar__baslik">{baslik}</h1>
            {altBaslik && <p className="topbar__altbaslik">{altBaslik}</p>}
          </div>
          {aksiyonlar && <div className="topbar__aksiyonlar">{aksiyonlar}</div>}
        </header>
        <main className="content">{children}</main>
      </div>
    </div>
  )
}
