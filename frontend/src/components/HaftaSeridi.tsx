import { useMemo } from 'react'
import type { Atama, GorevNoktasi, KapsamaAcigi, Personel } from '@/api/types'
import { blokEtiketi, blokKisaEtiketi, gununParcalari, sapmaGunu } from '@/lib/blok'
import { kisalt } from '@/lib/metin'
import { sayiBicimle } from '@/lib/sayi'
import { gunBasligiParcalari, haftaSonuMu, tarihBicimle } from '@/lib/tarih'
import { cn } from '@/lib/utils'

/**
 * Hafta şeridi — İKİNCİL GÖRÜNÜM (SDD 6.3.3, Tur 6 İş 2).
 *
 * Satırlarda personel, sütunlarda günler. Yedi gün × yirmi dört saat yüz altmış
 * sekiz sütun eder ve tek ekrana sığmaz — iki görünüm bu yüzden vardır. Bir gün
 * hücresine tıklandığında o günün ızgarasına geçilir.
 *
 * HÜCRE ARTIK RENK BANDI DEĞİL, METİN (Tur 7 İş 6). Yirmi dört dilimlik
 * gradient kullanımda okunmadı: ekrana bakan kişi kimin ne zaman çalıştığını
 * göremiyor, yalnızca bulanık bantlar görüyordu. Hücre şimdi saat aralığını
 * yazıyor ("08–16 GÜV") ve altındaki üç piksellik DÜZ çubuk bloğun günün
 * neresinde durduğunu gösteriyor. Ayrıntı `MiniSerit`te.
 *
 * Yüz altmış sekiz sütunlu yatay kaydırma denenmedi ve denenmeyecek:
 * kullanılabilir olmaz.
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
      // Açık başladığı güne sayılır (SRS TD-1 ile aynı sözleşme).
      const gun = sapmaGunu(k)
      indeks.set(gun, (indeks.get(gun) ?? 0) + k.eksik_sayi)
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
 * Bir (personel, gün) hücresi: SAAT ARALIĞI METNİ + konum çubuğu.
 *
 * ÖNCEKİ HÂLİ OKUNMUYORDU. Hücre yirmi dört dilimlik bir renk bandıydı ve
 * ekrana bakan kişi kimin ne zaman çalıştığını göremiyordu — yalnızca
 * bulanık bantlar. Bilgiyi taşıyan şey rengin tonu değil, **sayının
 * kendisidir**; band en fazla onu destekler.
 *
 * ÇUBUK DÜZ, GRADIENT DEĞİL. Okunması gereken şey tam olarak bloğun
 * SINIRIDIR: nerede başlıyor, nerede bitiyor. Gradient sürekli olduğu için
 * sınırı belirsizleştirir — bandın erdemi olan süreklilik, burada tam
 * olarak kusurdur. Çubuk ayrıca saat rengini de taşımaz: gündüz tonları
 * (#E9E7D9) hücre zemininden (#E4E7E1) ayırt edilemiyor ve üç piksellik
 * bir çubukta o fark tümüyle kayboluyor. Rengin söyleyeceği "gece mi
 * gündüz mü" bilgisini metin zaten söylüyor.
 *
 * Düğüm sayısı hücre başına sabit ve KÜÇÜKTÜR: metin + ray + en çok iki
 * çubuk. Dilim başına düğüm üretilseydi otuz personel × yedi gün × yirmi
 * dört dilim beş binden fazla düğüm ederdi (Tur 6 İş 2'nin ölçümü); o sınır
 * hâlâ geçerli ve testle korunuyor.
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
  const { metin, noktaKisa, cubuklar, baslik, kilitli, dolu } = useMemo(() => {
    const parcalar = gununParcalari(bloklar, gun)
    const satirlar: string[] = []
    const barlar: { sol: number; genislik: number }[] = []
    const etiketler: string[] = []
    let kilit = false

    for (const { blok, parca } of parcalar) {
      barlar.push({
        sol: (parca.baslangic / 24) * 100,
        genislik: ((parca.bitis - parca.baslangic) / 24) * 100,
      })
      if (blok.kilitli) kilit = true
      const nokta = noktaMap.get(blok.nokta_id)?.ad ?? ''
      // Etiket bloğun TAMAMINI yazar, o günkü parçasını değil (SRS TD-13);
      // önceki günden gelen parçada `‹` ile nereden geldiği belirtilir.
      const kisa = blokKisaEtiketi(blok.baslangic_zamani, blok.bitis_zamani)
      etiketler.push(parca.oncekiGundenGeliyor ? `‹${kisa}` : kisa)
      const devam = parca.oncekiGundenGeliyor
        ? ' (önceki günden)'
        : parca.sonrakiGuneTasiyor
          ? ' (ertesi güne)'
          : ''
      satirlar.push(`${blokEtiketi(blok.baslangic_zamani, blok.bitis_zamani)} · ${nokta}${devam}`)
    }

    // Nokta kısaltması yalnızca TEK blok varken sığar; ikinci bir parça
    // (önceki günden taşan blok) varsa iki saat aralığı zaten satırı
    // doldurur ve nokta ayrıntı görünümünde kalır.
    const tekNokta =
      parcalar.length === 1 ? kisalt(noktaMap.get(parcalar[0]!.blok.nokta_id)?.ad ?? '') : ''

    return {
      metin: etiketler.join(' '),
      noktaKisa: tekNokta,
      cubuklar: barlar,
      baslik: satirlar.length
        ? `${adSoyad} · ${tarihBicimle(gun)}\n${satirlar.join('\n')}`
        : `${adSoyad} · ${tarihBicimle(gun)} · atama yok`,
      kilitli: kilit,
      dolu: satirlar.length > 0,
    }
  }, [bloklar, gun, noktaMap, adSoyad])

  return (
    <td
      className={cn('border-b border-rule p-0.5', HUCRE_YUKSEKLIGI, haftaSonuMu(gun) && 'bg-sunken')}
    >
      <button
        type="button"
        className="flex h-full w-full flex-col justify-center gap-1 rounded-xs px-1 hover:bg-accent-soft"
        title={baslik}
        aria-label={baslik}
        onClick={onSec}
      >
        <span
          className={cn(
            'block truncate text-center font-mono text-mono-kucuk leading-none',
            dolu ? 'text-ink' : 'text-ink-muted',
          )}
        >
          {dolu ? metin : '–'}
          {noktaKisa && <span className="ml-1 text-ink-muted">{noktaKisa}</span>}
        </span>
        {/* Ray günün tamamı, çubuk bloğun kapladığı bölüm. Üç piksel: göz
            bunu bir ölçek olarak okur, ikinci bir veri satırı olarak değil. */}
        <span className="relative block h-[3px] w-full rounded-xs bg-rule">
          {cubuklar.map((c, i) => (
            <span
              key={i}
              className={cn(
                'absolute inset-y-0 rounded-xs',
                kilitli ? 'bg-accent' : 'bg-ink',
              )}
              style={{ left: `${c.sol}%`, width: `${c.genislik}%` }}
            />
          ))}
        </span>
      </button>
    </td>
  )
}
