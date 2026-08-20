import type { GunlukKapsama } from '@/api/types'
import { gunKisaltmasiVeNumarasi, tarihUzunBicim } from '@/lib/tarih'
import { cn } from '@/lib/utils'

/**
 * Günlük açık şeridi — dönemin her günü için bir çubuk.
 *
 * Çubuğun yüksekliği o günün eksik kişi-saatiyle orantılıdır; açığı olmayan
 * gün soluk ve çubuksuz durur. Şerit KENDİ BAŞINA bir ölçü göstermez, aynı
 * kartın altındaki listenin süzgecidir: "hangi gün sorunlu" sorusunu
 * yanıtlar, "neden" sorusunu liste yanıtlar.
 */
export function GunlukKapsamaSeridi({
  gunler,
  seciliTarih,
  gunSec,
}: {
  gunler: readonly GunlukKapsama[]
  seciliTarih: string | null
  gunSec: (tarih: string | null) => void
}) {
  // Çubuk yüksekliği ŞERİDİN İÇİNDEKİ AZAMİYE göredir, sabit bir ölçeğe
  // göre değil — tek günlük hafif bir açık ile ağır bir açık aynı görsel
  // aralıkta ayırt edilebilir kalsın diye.
  const azami = gunler.reduce((m, g) => Math.max(m, g.karsilanmayan_kisi_saat), 0)

  return (
    <div className="flex items-end gap-1" role="group" aria-label="Günlük kapsama açığı">
      {gunler.map((g) => {
        const acikMi = g.karsilanmayan_kisi_saat > 0
        const secili = g.tarih === seciliTarih
        const yukseklikYuzde = azami > 0 ? Math.max(8, (g.karsilanmayan_kisi_saat / azami) * 100) : 0

        return (
          <button
            key={g.tarih}
            type="button"
            aria-pressed={secili}
            aria-label={`${tarihUzunBicim(g.tarih)} — ${g.karsilanmayan_kisi_saat} kişi-saat eksik`}
            // Seçili güne TEKRAR tıklamak süzgeci kaldırır (null); başka bir
            // güne tıklamak süzgeci o güne taşır.
            onClick={() => gunSec(secili ? null : g.tarih)}
            className={cn(
              'flex flex-1 flex-col items-center gap-1 rounded-sm py-1 outline-none',
              'focus-visible:ring-3 focus-visible:ring-accent/30',
              secili && 'bg-accent-soft',
            )}
          >
            <span className="flex h-12 w-full items-end justify-center">
              {acikMi && (
                <span
                  aria-hidden="true"
                  className={cn('w-full max-w-6 rounded-t-xs', secili ? 'bg-accent' : 'bg-signal')}
                  style={{ height: `${yukseklikYuzde}%` }}
                />
              )}
            </span>
            <span
              className={cn(
                'font-mono text-xs',
                acikMi ? 'text-ink-muted' : 'text-ink-muted/50',
              )}
            >
              {gunKisaltmasiVeNumarasi(g.tarih)}
            </span>
          </button>
        )
      })}
    </div>
  )
}
