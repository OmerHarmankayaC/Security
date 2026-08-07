// Gün 10'da elle yazılan Buton/Kart/KartEtiketi/Rozet/BuyukRakam
// bileşenlerinin shadcn/ui üzerine kurulu karşılıkları (Tasarım Referansı
// sürüm 2). Ekran dosyalarının JSX'i değişmeden kalsın diye aynı Türkçe
// prop adları korunuyor — yalnızca görsel katman shadcn primitiflerine
// taşındı (bkz. PROGRESS.md, Sprint 2 Gün 10 shadcn geçişi notu).
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
        '[--card-spacing:--spacing(8)]', // TASARIM_REFERANSI.md: kart ic bosluk 32px
        vurgulu && 'border-primary bg-accent',
        className,
      )}
    >
      <CardContent>{children}</CardContent>
    </Card>
  )
}

// Bolum etiketi (kart basligi) — kaynak metin kucuk harfle yazilir, gorsel
// olarak toLocaleUpperCase('tr-TR') ile buyutulur (duz toUpperCase DEGIL —
// Turkce İ/ı harflerini bozar, bkz. TASARIM_REFERANSI.md).
export function KartEtiketi({
  children,
  renk,
}: PropsWithChildren<{ renk?: 'accent' | 'warn' }>) {
  return (
    <p
      className={cn(
        'mb-4 text-xs font-medium tracking-wide text-muted-foreground',
        renk === 'accent' && 'text-primary',
        renk === 'warn' && 'text-amber-700',
      )}
    >
      {buyukHarf(duzMetneCevir(children))}
    </p>
  )
}

type RozetVaryanti = 'dolu' | 'eksik' | 'kilitli' | 'notr'

const ROZET_VARYANT_SINIFI: Record<RozetVaryanti, string> = {
  dolu: 'bg-green-50 text-green-700',
  eksik: 'bg-amber-100 text-amber-700',
  kilitli: 'bg-accent text-primary',
  notr: 'bg-gray-100 text-gray-500',
}

// Sabit genislik zorunlu: metne gore otomatik genisleyen bir rozet, yan yana
// gelen alanlari kaydirir (bkz. TASARIM_REFERANSI.md — Sürümler ekranindaki
// durum rozeti notu; shadcn Badge'e gecerken de gecerliligini koruyor).
export function Rozet({
  children,
  varyant,
  genislik = 96,
}: PropsWithChildren<{ varyant: RozetVaryanti; genislik?: number }>) {
  return (
    <Badge
      variant="secondary"
      className={cn('justify-center', ROZET_VARYANT_SINIFI[varyant])}
      style={{ width: genislik }}
    >
      {buyukHarf(duzMetneCevir(children))}
    </Badge>
  )
}

export function BuyukRakam({ deger, etiket }: { deger: string; etiket: string }) {
  return (
    <div>
      <p className="m-0 text-3xl font-semibold text-foreground">{deger}</p>
      <p className="mt-1 text-sm text-muted-foreground">{etiket}</p>
    </div>
  )
}
