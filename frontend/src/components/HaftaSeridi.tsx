import { useMemo } from 'react'
import type { Atama, GorevNoktasi, KapsamaAcigi, Personel } from '@/api/types'
import { blokEtiketi, gununParcalari } from '@/lib/blok'
import { sayiBicimle } from '@/lib/sayi'
import { KILIT_DOKUSU, saatGradyani, saatRengi } from '@/lib/saatRengi'
import { gunBasligiParcalari, haftaSonuMu, tarihBicimle } from '@/lib/tarih'
import { cn } from '@/lib/utils'

/**
 * Hafta şeridi — İKİNCİL GÖRÜNÜM (SDD 6.3.3, Tur 6 İş 2).
 *
 * Satırlarda personel, sütunlarda günler; her gün hücresi yirmi dört dilimlik
 * bir mini şerittir ve dolu saatler boyalıdır. Yedi gün × yirmi dört saat yüz
 * altmış sekiz sütun eder ve tek ekrana sığmaz — iki görünüm bu yüzden vardır.
 * Bir gün hücresine tıklandığında o günün ızgarasına geçilir.
 *
 * MİNİ ŞERİT TEK ÖĞEDİR. Her dilim ayrı bir DOM düğümü yapılsaydı otuz
 * personel × yedi gün × yirmi dört dilim beş bin düğümden fazla ederdi ve
 * sayfa boğulurdu. Dilimler bir CSS gradientinin sert duraklarıyla çizilir
 * (`lib/saatRengi.ts`, `saatGradyani`): hücre başına düşen düğüm sayısı
 * DİLİM SAYISINDAN BAĞIMSIZ olarak birdir.
 */

const AD_SUTUNU = 'w-[200px] min-w-[200px] max-w-[200px]'
const HUCRE_YUKSEKLIGI = 'h-[38px]'

export interface HaftaSeridiProps {
  gunler: readonly string[]
  personeller: readonly Personel[]
  atamalar: readonly Atama[]
  noktaMap: Map<number, GorevNoktasi>
  kapsamaAcigi: readonly KapsamaAcigi[]
  bugun: string
  onGunSec: (gun: string) => void
}

export function HaftaSeridi({
  gunler,
  personeller,
  atamalar,
  noktaMap,
  kapsamaAcigi,
  bugun,
  onGunSec,
}: HaftaSeridiProps) {
  const personelAtamalari = useMemo(() => {
    const indeks = new Map<number, Atama[]>()
    for (const a of atamalar) {
      const mevcut = indeks.get(a.personel_id)
      if (mevcut) mevcut.push(a)
      else indeks.set(a.personel_id, [a])
    }
    return indeks
  }, [atamalar])

  // Açık SAYISI gün başlığında toplanır (SDD 6.3.3): şeritte saat çözünürlüğü
  // zaten düşük, açığın hangi saatte olduğu gün ızgarasının işidir.
  const gunlukAcik = useMemo(() => {
    const indeks = new Map<string, number>()
    for (const k of kapsamaAcigi) {
      indeks.set(k.tarih, (indeks.get(k.tarih) ?? 0) + k.eksik_sayi)
    }
    return indeks
  }, [kapsamaAcigi])

  return (
    <div className="relative overflow-auto">
      <table className="w-full min-w-max border-separate border-spacing-0">
        <thead>
          <tr>
            <th
              className={cn(
                'mono-caps sticky top-0 left-0 z-30 border-r border-b border-rule bg-surface px-3 text-left text-ink-muted',
                AD_SUTUNU,
              )}
            >
              PERSONEL
            </th>
            {gunler.map((gun) => {
              const { kisaltma, numara } = gunBasligiParcalari(gun)
              const acik = gunlukAcik.get(gun) ?? 0
              return (
                <th
                  key={gun}
                  className={cn(
                    'sticky top-0 z-20 h-[48px] min-w-[92px] border-b border-rule bg-surface px-1 text-center font-mono text-mono-kucuk font-medium text-ink-muted',
                    haftaSonuMu(gun) && 'bg-sunken',
                  )}
                >
                  <button
                    type="button"
                    className="flex w-full flex-col items-center gap-0.5"
                    onClick={() => onGunSec(gun)}
                    title={`${tarihBicimle(gun)} — gün ızgarasına geç`}
                  >
                    <span>{kisaltma}</span>
                    <span
                      className={cn(
                        'flex size-6 items-center justify-center font-semibold',
                        gun === bugun ? 'rounded-full bg-accent text-chrome-ink' : 'text-ink',
                      )}
                    >
                      {numara}
                    </span>
                    {acik > 0 && (
                      <span className="text-[9px] leading-none font-semibold text-signal">
                        ▲{acik}
                      </span>
                    )}
                  </button>
                </th>
              )
            })}
          </tr>
        </thead>
        <tbody>
          {personeller.map((p) => {
            const bloklar = personelAtamalari.get(p.personel_id) ?? []
            // Dönem toplamı bloğun BAŞLADIĞI güne yazılır (SRS TD-1); satır
            // toplamı bu yüzden blokların süresidir, hücrelerin değil.
            const toplamSaat = bloklar.reduce((t, b) => t + b.sure_saat, 0)
            return (
              <tr key={p.personel_id}>
                <td
                  className={cn(
                    'sticky left-0 z-10 border-r border-b border-rule bg-surface px-3 text-left',
                    HUCRE_YUKSEKLIGI,
                    AD_SUTUNU,
                  )}
                  title={`${p.ad_soyad} · ${p.sicil_no}`}
                >
                  <span className="block truncate text-sm text-ink">{p.ad_soyad}</span>
                  <span className="block truncate font-mono text-mono-kucuk text-ink-muted">
                    {p.sicil_no} · {sayiBicimle(toplamSaat, 0)} sa
                  </span>
                </td>
                {gunler.map((gun) => (
                  <MiniSerit
                    key={gun}
                    gun={gun}
                    bloklar={bloklar}
                    noktaMap={noktaMap}
                    adSoyad={p.ad_soyad}
                    onSec={() => onGunSec(gun)}
                  />
                ))}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

/**
 * Bir (personel, gün) hücresi: yirmi dört dilimlik mini şerit, TEK ÖĞE.
 *
 * Düğüm sayısı: hücre başına bir `td` ve bir `button`. Dilimler `button`ın
 * arka planındaki gradientten gelir, ayrı düğüm üretmezler.
 */
function MiniSerit({
  gun,
  bloklar,
  noktaMap,
  adSoyad,
  onSec,
}: {
  gun: string
  bloklar: readonly Atama[]
  noktaMap: Map<number, GorevNoktasi>
  adSoyad: string
  onSec: () => void
}) {
  const { zemin, baslik, kilitli, dolu } = useMemo(() => {
    const parcalar = gununParcalari(bloklar, gun)
    const dilimler: (string | null)[] = Array.from({ length: 24 }, () => null)
    const satirlar: string[] = []
    let kilit = false
    for (const { blok, parca } of parcalar) {
      for (let saat = parca.baslangic; saat < parca.bitis; saat += 1) {
        dilimler[saat] = saatRengi(saat)
      }
      if (blok.kilitli) kilit = true
      const nokta = noktaMap.get(blok.nokta_id)?.ad ?? ''
      const devam = parca.oncekiGundenGeliyor
        ? ' (önceki günden)'
        : parca.sonrakiGuneTasiyor
          ? ' (ertesi güne)'
          : ''
      satirlar.push(
        `${blokEtiketi(blok.baslangic_zamani, blok.bitis_zamani)} · ${nokta}${devam}`,
      )
    }
    return {
      zemin: saatGradyani(dilimler),
      baslik: satirlar.length
        ? `${adSoyad} · ${tarihBicimle(gun)}\n${satirlar.join('\n')}`
        : `${adSoyad} · ${tarihBicimle(gun)} · atama yok`,
      kilitli: kilit,
      dolu: satirlar.length > 0,
    }
  }, [bloklar, gun, noktaMap, adSoyad])

  return (
    <td
      className={cn(
        'border-b border-rule p-1',
        HUCRE_YUKSEKLIGI,
        haftaSonuMu(gun) && 'bg-sunken',
      )}
    >
      <button
        type="button"
        className={cn(
          'block h-5 w-full rounded-xs border',
          dolu ? 'border-rule-strong' : 'border-rule bg-surface',
        )}
        style={{ backgroundImage: kilitli ? `${KILIT_DOKUSU}, ${zemin}` : zemin }}
        title={baslik}
        aria-label={baslik}
        onClick={onSec}
      />
    </td>
  )
}
