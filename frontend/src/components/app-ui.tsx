// Tasarım Referansı sürüm 4 ("Kontrol Odası") üzerine kurulu paylaşılan
// bileşenler — shadcn primitiflerini (src/components/ui/) sarar. Ekran
// dosyalarının kullandığı Türkçe prop adları korunur.
import { Children, type ButtonHTMLAttributes, type PropsWithChildren, type ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { buyukHarf } from '@/lib/metin'
// ETKIN DILLE buyutulur, `buyukHarf`in Turkce varsayilaniyla DEGIL.
// Bu uc bilesenin cocuklari her zaman arayuzun kendi etiketidir (kart
// basligi, rozet metni, sayi altligi) ve Turkce yereliyle buyutulunce
// Ingilizce metin bozuluyordu: "Period view" -> "PERİOD VİEW", "Fri" ->
// "FRİ". Veriyi buyuten cagrilar (gorev noktasi adi, izgara kisaltmasi)
// varsayilanda kalir.
import { useDil } from '@/i18n/DilBaglami'
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
// `etiket/caps`: Public Sans Medium 11,5px, %14 harf araligi (surum 4'te
// Condensed kesim kalkti, bkz. index.css'teki `.etiket-caps`).
export function KartEtiketi({
  children,
  renk,
}: PropsWithChildren<{ renk?: 'accent' | 'warn' }>) {
  const { dil } = useDil()
  return (
    <p
      className={cn(
        'etiket-caps mb-4 text-ink-muted',
        renk === 'accent' && 'text-accent',
        renk === 'warn' && 'text-signal',
      )}
    >
      {buyukHarf(duzMetneCevir(children), dil)}
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
//
// Surum 4 notu: eski hal Condensed + %8 harf araligiydi; `etiket-caps`
// (Public Sans Medium 11,5px, %14) ayni metni ~%20 daha genis yazar. Bu
// yuzden asagidaki varsayilan ve butun cagri yerlerindeki `genislik`
// degerleri yeniden olculdu — h-5'lik rozete 11,5px yazi sigmadigi icin
// yukseklik de h-5,5'e cikti.
export function Rozet({
  children,
  varyant,
  genislik = 112,
}: PropsWithChildren<{ varyant: RozetVaryanti; genislik?: number }>) {
  const { dil } = useDil()
  return (
    <Badge
      variant="secondary"
      className={cn('etiket-caps h-5.5 justify-center rounded-sm', ROZET_VARYANT_SINIFI[varyant])}
      style={{ width: genislik }}
    >
      {buyukHarf(duzMetneCevir(children), dil)}
    </Badge>
  )
}

// Sayı her yerde Mono: tarih, saat, ceza puanı, personel sayısı — rakamlar
// böylece sütun halinde hizalanır (bkz. TASARIM_REFERANSI.md, Tipografi).
// `tabular-nums` YOK: Azeret Mono zaten sabit genişlikli, özelliği açmak
// hiçbir şeyi değiştirmez (Tasarım Referansı, "Uygulama notları").
export function Sayi({ children, className }: PropsWithChildren<{ className?: string }>) {
  return <span className={cn('font-mono', className)}>{children}</span>
}

// `sayı/büyük` — Azeret Mono SemiBold 26px.
export function BuyukRakam({ deger, etiket }: { deger: string; etiket: string }) {
  const { dil } = useDil()
  return (
    <div>
      <p className="m-0 font-mono text-sayi-buyuk font-semibold text-ink">{deger}</p>
      <p className="etiket-caps mt-1 text-ink-muted">{buyukHarf(etiket, dil)}</p>
    </div>
  )
}
