// Arayüz dili seçici.
//
// İKİ DÜĞME, AÇILIR LİSTE DEĞİL. İki seçenek varken açılır liste, seçimi
// görmek için bir tıklama daha ister ve o an hangi dilde olunduğunu gizler.
// Burada etkin dil her zaman görünür durur.
//
// Diller KENDİ adlarıyla yazılır ("Türkçe", "English"), çevrilmez: dilini
// arayan kişi karşılığını değil kendi dilinin adını arar.
import { DILLER, DIL_ADLARI } from '@/i18n/diller'
import { useDil } from '@/i18n/DilBaglami'
import { cn } from '@/lib/utils'

export function DilSecici({ className }: { className?: string }) {
  const { dil, metin, dilSec } = useDil()

  return (
    <div
      role="group"
      aria-label={metin.dil.secici}
      className={cn('inline-flex items-center gap-1', className)}
    >
      {DILLER.map((secenek) => {
        const etkin = secenek === dil
        return (
          <button
            key={secenek}
            type="button"
            onClick={() => dilSec(secenek)}
            // `aria-pressed`, ekran okuyucuya bunun bir aç/kapa olduğunu ve
            // hangisinin açık olduğunu söyler. Yalnızca renkle belirtmek,
            // görmeyene hiçbir şey söylemezdi.
            aria-pressed={etkin}
            lang={secenek}
            className={cn(
              'rounded-sm px-2 py-0.5 text-xs transition-colors',
              'focus-visible:ring-3 focus-visible:ring-accent/30 focus-visible:outline-none',
              etkin
                ? 'bg-accent/15 font-semibold text-ink'
                : 'text-ink-muted hover:text-ink',
            )}
          >
            {DIL_ADLARI[secenek]}
          </button>
        )
      })}
    </div>
  )
}
