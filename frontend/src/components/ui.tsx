import type { ButtonHTMLAttributes, PropsWithChildren } from 'react'
import { buyukHarf } from '../lib/metin'
import './ui.css'

type ButonVaryanti = 'birincil' | 'ikincil' | 'hayalet'

export function Buton({
  varyant = 'ikincil',
  className,
  ...geri
}: { varyant?: ButonVaryanti } & ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button className={`btn btn--${varyant} ${className ?? ''}`} {...geri} />
}

export function Kart({
  children,
  vurgulu,
  className,
}: PropsWithChildren<{ vurgulu?: boolean; className?: string }>) {
  return (
    <section className={`card ${vurgulu ? 'card--accent' : ''} ${className ?? ''}`}>
      {children}
    </section>
  )
}

// Bolum etiketi (kart basligi) — kaynak metin kucuk harfle yazilir, gorsel
// olarak toLocaleUpperCase('tr-TR') ile buyutulur (duz toUpperCase DEGIL).
export function KartEtiketi({
  children,
  renk,
}: PropsWithChildren<{ renk?: 'accent' | 'warn' }>) {
  const className = `card__label ${renk ? `card__label--${renk}` : ''}`
  return <p className={className}>{buyukHarf(String(children))}</p>
}

type RozetVaryanti = 'dolu' | 'eksik' | 'kilitli' | 'notr'

// Sabit genislik zorunlu: metne gore otomatik genisleyen bir rozet, yan yana
// gelen alanlari kaydirir (bkz. docs/tasarim/TASARIM_REFERANSI.md — Sürümler
// ekranindaki durum rozeti notu).
export function Rozet({
  children,
  varyant,
  genislik = 96,
}: PropsWithChildren<{ varyant: RozetVaryanti; genislik?: number }>) {
  return (
    <span className={`rozet rozet--${varyant}`} style={{ width: genislik }}>
      {buyukHarf(String(children))}
    </span>
  )
}

export function BuyukRakam({ deger, etiket }: { deger: string; etiket: string }) {
  return (
    <div>
      <p className="buyuk-rakam">{deger}</p>
      <p className="buyuk-rakam__etiket">{etiket}</p>
    </div>
  )
}
