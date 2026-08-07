// Tasarım Referansı sürüm 3 ("Kontrol Odası") üzerine kurulu paylaşılan
// bileşenler — shadcn primitiflerini (src/components/ui/) sarar. Ekran
// dosyalarının kullandığı Türkçe prop adları korunur.
import { Children, type ButtonHTMLAttributes, type PropsWithChildren, type ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { buyukHarf } from '@/lib/metin'
import { cn } from '@/lib/utils'

// JSX metin + ifade karisimi (orn. `sonuç özeti — {durum}`) React'e AYRI
// children olarak gelir; bunlari duz String(children) ile birlestirmek
// diziyi virgulle ayirir ("a,b"). Children.toArray + join('') doğru sonucu
// verir.
function duzMetneCevir(children: ReactNode): string {
  return Children.toArray(children).join('')
}

type ButonVaryanti = 'birincil' | 'ikincil' | 'hayalet'

const BUTON_VARYANT_ESLEME: Record<ButonVaryanti, 'default' | 'outline' | 'ghost'> = {
  birincil: 'default',
  ikincil: 'outline',
  hayalet: 'ghost',
}

export function Buton({
  varyant = 'ikincil',
  className,
  ...geri
}: { varyant?: ButonVaryanti } & ButtonHTMLAttributes<HTMLButtonElement>) {
  return <Button variant={BUTON_VARYANT_ESLEME[varyant]} className={className} {...geri} />
}

export function Kart({
  children,
  vurgulu,
  className,
}: PropsWithChildren<{ vurgulu?: boolean; className?: string }>) {
  return (
    <Card
      className={cn(
        '[--card-spacing:--spacing(6)] rounded-md border-rule bg-surface',
        vurgulu && 'border-accent bg-accent-soft',
        className,
      )}
    >
      <CardContent>{children}</CardContent>
    </Card>
  )
}

// Bolum etiketi (kart basligi) — kaynak metin kucuk harfle yazilir, gorsel
// olarak toLocaleUpperCase('tr-TR') ile buyutulur (duz toUpperCase DEGIL —
// Turkce İ/ı harflerini bozar, bkz. TASARIM_REFERANSI.md). Stil
// `etiket/caps`: IBM Plex Sans Condensed Medium 10px, %14 harf araligi.
export function KartEtiketi({
  children,
  renk,
}: PropsWithChildren<{ renk?: 'accent' | 'warn' }>) {
  return (
    <p
      className={cn(
        'mb-4 font-condensed text-[10px] font-medium tracking-[0.14em] text-ink-muted',
        renk === 'accent' && 'text-accent',
        renk === 'warn' && 'text-signal',
      )}
    >
      {buyukHarf(duzMetneCevir(children))}
    </p>
  )
}

type RozetVaryanti = 'dolu' | 'eksik' | 'kilitli' | 'notr'

const ROZET_VARYANT_SINIFI: Record<RozetVaryanti, string> = {
  dolu: 'bg-sunken text-ink-muted',
  eksik: 'bg-signal-soft text-signal',
  kilitli: 'bg-accent-soft text-accent',
  notr: 'bg-sunken text-ink-muted',
}

// Sabit genislik zorunlu: metne gore otomatik genisleyen bir rozet, yan yana
// gelen alanlari kaydirir (bkz. TASARIM_REFERANSI.md — "Genişleyen
// bileşenlere sabit genişlik" uyarısı, bu tasarımda daha önce iki kez
// yaşanmış).
export function Rozet({
  children,
  varyant,
  genislik = 96,
}: PropsWithChildren<{ varyant: RozetVaryanti; genislik?: number }>) {
  return (
    <Badge
      variant="secondary"
      className={cn('justify-center rounded-sm font-condensed tracking-[0.08em]', ROZET_VARYANT_SINIFI[varyant])}
      style={{ width: genislik }}
    >
      {buyukHarf(duzMetneCevir(children))}
    </Badge>
  )
}

// Sayı her yerde Mono: tarih, saat, ceza puanı, personel sayısı — rakamlar
// böylece sütun halinde hizalanır (bkz. TASARIM_REFERANSI.md, Tipografi).
export function Sayi({ children, className }: PropsWithChildren<{ className?: string }>) {
  return <span className={cn('font-mono tabular-nums', className)}>{children}</span>
}

export function BuyukRakam({ deger, etiket }: { deger: string; etiket: string }) {
  return (
    <div>
      <p className="m-0 font-mono text-3xl font-semibold text-ink">{deger}</p>
      <p className="mt-1 font-condensed text-[10px] tracking-[0.14em] text-ink-muted">
        {buyukHarf(etiket)}
      </p>
    </div>
  )
}
