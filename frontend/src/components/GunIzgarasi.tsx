import { useCallback, useMemo, useRef, useState } from 'react'
import type { Atama, GorevNoktasi, KapsamaAcigi, Personel } from '@/api/types'
import {
  blokErisilebilirEtiket,
  blokEtiketi,
  gununParcalari,
  saatEtiketi,
  type GunParcasi,
} from '@/lib/blok'
import { sinirUyarisi, type BlokSinirlari } from '@/lib/kuralParametre'
import { kisalt } from '@/lib/metin'
import { sayiBicimle } from '@/lib/sayi'
import { araligiSure } from '@/lib/talepAraligi'
import { ETIKET_ZEMINI, KILIT_DOKUSU, aralikGradyani, saatRengi } from '@/lib/saatRengi'
import { cn } from '@/lib/utils'

/**
 * Gün ızgarası — bu turun ANA GÖRÜNÜMÜ (SDD 6.3.3, Tur 6 İş 1).
 *
 * Satırlarda personel, sütunlarda seçili günün yirmi dört saati. Bir bloğun
 * kapladığı saatler KESİNTİSİZ TEK BİR ŞERİT olarak çizilir — hücre hücre
 * boyanmış bir dizi değil. Ayrım görsel değil anlamsal: blok tek bir karardır
 * (SRS TD-13) ve yirmi dört ayrı kutu, kataloglu sürümün "vardiya dizilimi"
 * görüntüsünü geri getirirdi.
 *
 * GECE YARISINI AŞAN BLOK. İki günün ızgarasında da görünür ama tek bloktur:
 * başladığı günde sağ kenara dayanır ve devam ettiği görünür, ertesi gün sol
 * kenardan başlar ve önceki günden geldiği görünür. Bloğun etiketi iki günde
 * de aralığın TAMAMINI yazar ("20.00–06.00"); o günkü parçasını yazmak
 * ("20.00–24.00" ve "00.00–06.00") tam olarak modelin yasakladığı iki-blok
 * görüntüsünü üretirdi (SRS TD-13). Geometri `blok.ts`ten gelir, burada
 * ikinci bir çözümleme yoktur.
 */

const SAATLER = Array.from({ length: 24 }, (_, i) => i)

// Ad sütunu gün ızgarasında da 220px (Tasarım Referansı sürüm 4); yirmi dört
// saat sütunu kalan genişliği eşit böler ve tablo kabı doldurur.
const AD_SUTUNU = 'w-[200px] min-w-[200px] max-w-[200px]'
const SATIR_YUKSEKLIGI = 'h-[42px]'

/** Sürükleme durumu: hangi satırda, nereden nereye. */
interface Surukleme {
  personelId: number
  /** Basılan saat — çapa. Sürükleme geriye doğru da olabilir. */
  capa: number
  /** İmlecin bulunduğu saat. */
  imlec: number
  /** Var olan bir bloğun kenarından tutulduysa bloğun sabit kalan ucu. */
  kip: 'yeni' | 'sol-kenar' | 'sag-kenar'
}

function araligaCevir(s: Surukleme): { baslangic: number; bitis: number } {
  const bas = Math.min(s.capa, s.imlec)
  const bit = Math.max(s.capa, s.imlec) + 1
  return { baslangic: bas, bitis: bit }
}

export interface GunIzgarasiProps {
  gun: string
  personeller: readonly Personel[]
  /** Dönemin TÜM atamaları — önceki günden taşan blok da çizileceği için. */
  atamalar: readonly Atama[]
  noktaMap: Map<number, GorevNoktasi>
  kapsamaAcigi: readonly KapsamaAcigi[]
  seritNoktalari: readonly GorevNoktasi[]
  sinirlar: BlokSinirlari
  duzenlenebilir: boolean
  seciliPersonelId: number | null
  onSatirSec: (personelId: number) => void
  /** Sürükleme bittiğinde: yarı açık [baslangic, bitis) saat aralığı. */
  onBlokTanimla: (personelId: number, baslangic: number, bitis: number) => void
}

export function GunIzgarasi({
  gun,
  personeller,
  atamalar,
  noktaMap,
  kapsamaAcigi,
  seritNoktalari,
  sinirlar,
  duzenlenebilir,
  seciliPersonelId,
  onSatirSec,
  onBlokTanimla,
}: GunIzgarasiProps) {
  const [surukleme, setSurukleme] = useState<Surukleme | null>(null)
  // Sürükleme bırakıldığında kullanılacak son durum; `onPointerUp` state'in
  // güncellenmiş hâlini göremediği için ayrıca burada tutulur.
  const suruklemeRef = useRef<Surukleme | null>(null)

  const personelAtamalari = useMemo(() => {
    const indeks = new Map<number, Atama[]>()
    for (const a of atamalar) {
      const mevcut = indeks.get(a.personel_id)
      if (mevcut) mevcut.push(a)
      else indeks.set(a.personel_id, [a])
    }
    return indeks
  }, [atamalar])

  // Saat × nokta açık haritası. Kapsama açığı kaydı bir ARALIK taşır (SDD
  // 4.2.4); ızgaranın işareti SAAT düzeyindedir (SDD 6.3.3), o yüzden aralık
  // saatlere açılır.
  const acikSaatler = useMemo(() => {
    const indeks = new Map<number, Map<number, number>>()
    for (const k of kapsamaAcigi) {
      if (k.tarih !== gun) continue
      const bas = Number(k.baslangic.slice(0, 2))
      const sure = araligiSure(bas, Number(k.bitis.slice(0, 2)))
      for (let i = 0; i < sure; i += 1) {
        const saat = (bas + i) % 24
        let noktalar = indeks.get(saat)
        if (!noktalar) {
          noktalar = new Map()
          indeks.set(saat, noktalar)
        }
        noktalar.set(k.nokta_id, (noktalar.get(k.nokta_id) ?? 0) + k.eksik_sayi)
      }
    }
    return indeks
  }, [kapsamaAcigi, gun])

  const suruklemeyiBitir = useCallback(() => {
    const son = suruklemeRef.current
    suruklemeRef.current = null
    setSurukleme(null)
    if (!son) return
    // İMLEÇ HİÇ KIPIRDAMADIYSA BLOK TANIMLANMAZ. Tek tık, satırı seçmektir;
    // bir saatlik blok üretip ardından "asgari dört saat" diye reddetmek,
    // kullanıcının yapmadığı bir işlemi ona geri okumak olurdu. Kenardan
    // tutup bırakmak da aynı nedenle sessizce hiçbir şey yapmaz.
    if (son.imlec === son.capa) return
    const { baslangic, bitis } = araligaCevir(son)
    onBlokTanimla(son.personelId, baslangic, bitis)
  }, [onBlokTanimla])

  const saatBasla = (personelId: number, saat: number, kip: Surukleme['kip']) => {
    if (!duzenlenebilir) return
    const yeni: Surukleme = { personelId, capa: saat, imlec: saat, kip }
    suruklemeRef.current = yeni
    setSurukleme(yeni)
    onSatirSec(personelId)
  }

  const saatUzerinde = (personelId: number, saat: number) => {
    const mevcut = suruklemeRef.current
    if (!mevcut || mevcut.personelId !== personelId) return
    if (mevcut.imlec === saat) return
    const yeni = { ...mevcut, imlec: saat }
    suruklemeRef.current = yeni
    setSurukleme(yeni)
  }

  return (
    <div
      className="relative overflow-auto"
      // Sürükleme ızgaranın DIŞINDA bırakıldığında da bitmeli; aksi hâlde
      // imleç geri geldiğinde blok kullanıcı basmadan büyümeye devam eder.
      onPointerUp={suruklemeyiBitir}
      onPointerLeave={suruklemeyiBitir}
    >
      <table className="w-full min-w-[880px] table-fixed border-separate border-spacing-0 select-none">
        {/* Sabit yerleşim + colgroup: yirmi dört saat sütunu EŞİT olmak
            zorunda. Genişlik içeriğe bırakılsaydı yalnızca üçte birinde
            etiket bulunan başlık satırı sütunları farklı genişletir ve
            ayraç çizgileri şeridin saatleriyle hizalanmazdı. */}
        <colgroup>
          <col className={AD_SUTUNU} />
          {SAATLER.map((saat) => (
            <col key={saat} style={{ width: `${100 / 24}%` }} />
          ))}
        </colgroup>
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
            {SAATLER.map((saat) => (
              <th
                key={saat}
                colSpan={1}
                className={cn(
                  'sticky top-0 z-20 h-[34px] border-b border-rule bg-surface text-center font-mono text-mono-kucuk font-medium text-ink-muted',
                  // Üç saatte bir dikey ayraç: yirmi dört ince çizgi ızgarayı
                  // okunmaz eder, ayraçsız ızgarada da bir bloğun kaça kadar
                  // sürdüğü sayılamaz.
                  saat % 3 === 0 && 'border-l border-rule',
                )}
              >
                {saat % 3 === 0 ? String(saat).padStart(2, '0') : ''}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          <KapsamaSatiri
            acikSaatler={acikSaatler}
            seritNoktalari={seritNoktalari}
            adSutunu={AD_SUTUNU}
          />
          {personeller.map((p) => (
            <PersonelSatiri
              key={p.personel_id}
              gun={gun}
              personel={p}
              bloklar={personelAtamalari.get(p.personel_id) ?? []}
              noktaMap={noktaMap}
              secili={seciliPersonelId === p.personel_id}
              duzenlenebilir={duzenlenebilir}
              sinirlar={sinirlar}
              surukleme={surukleme?.personelId === p.personel_id ? surukleme : null}
              onSatirSec={onSatirSec}
              onSaatBasla={saatBasla}
              onSaatUzerinde={saatUzerinde}
            />
          ))}
        </tbody>
      </table>
    </div>
  )
}

/**
 * Kapsama satırı — açık SAAT düzeyinde işaretlenir (SDD 6.3.3).
 *
 * İşaret rengin yanında bir ÜÇGEN ve sayı taşır: renk körlüğünde ve
 * yazdırmada turuncu ile bandın koyu tonu ayrışmaz, üçgen ayrışır.
 */
function KapsamaSatiri({
  acikSaatler,
  seritNoktalari,
  adSutunu,
}: {
  acikSaatler: Map<number, Map<number, number>>
  seritNoktalari: readonly GorevNoktasi[]
  adSutunu: string
}) {
  if (seritNoktalari.length === 0) return null
  return (
    <tr>
      <td
        className={cn(
          'etiket-caps sticky left-0 z-10 h-[26px] border-r border-b border-rule bg-surface px-3 text-ink-muted',
          adSutunu,
        )}
        title={`Basamak sırası: ${seritNoktalari.map((n) => n.ad).join(' · ')}`}
      >
        KAPSAMA
      </td>
      {Array.from({ length: 24 }, (_, saat) => {
        const noktalar = acikSaatler.get(saat)
        const eksik = noktalar ? [...noktalar.values()].reduce((t, s) => t + s, 0) : 0
        const adlar = noktalar
          ? [...noktalar.entries()]
              .map(([id, s]) => `${seritNoktalari.find((n) => n.nokta_id === id)?.ad ?? id}: ${s}`)
              .join(' · ')
          : ''
        return (
          <td
            key={saat}
            className={cn(
              'h-[26px] border-b border-rule p-0 text-center',
              saat % 3 === 0 && 'border-l border-rule',
              eksik > 0 && 'bg-signal-soft',
            )}
            title={eksik > 0 ? `${saatEtiketi(saat)} — ${adlar}` : undefined}
          >
            {eksik > 0 && (
              <span className="font-mono text-[9px] leading-none font-semibold text-signal">
                ▲{eksik}
              </span>
            )}
          </td>
        )
      })}
    </tr>
  )
}

function PersonelSatiri({
  gun,
  personel,
  bloklar,
  noktaMap,
  secili,
  duzenlenebilir,
  sinirlar,
  surukleme,
  onSatirSec,
  onSaatBasla,
  onSaatUzerinde,
}: {
  gun: string
  personel: Personel
  bloklar: readonly Atama[]
  noktaMap: Map<number, GorevNoktasi>
  secili: boolean
  duzenlenebilir: boolean
  sinirlar: BlokSinirlari
  surukleme: Surukleme | null
  onSatirSec: (personelId: number) => void
  onSaatBasla: (personelId: number, saat: number, kip: Surukleme['kip']) => void
  onSaatUzerinde: (personelId: number, saat: number) => void
}) {
  const parcalar = useMemo(() => gununParcalari(bloklar, gun), [bloklar, gun])

  // Gün toplamı, o gün BAŞLAYAN bloğun tamamıdır (SRS TD-1): gece yarısını
  // aşan blok başladığı güne sayılır, ertesi günün toplamına girmez.
  const gunlukSaat = useMemo(
    () => bloklar.filter((b) => b.tarih === gun).reduce((t, b) => t + b.sure_saat, 0),
    [bloklar, gun],
  )

  const onizleme = surukleme ? araligaCevir(surukleme) : null
  const onizlemeSuresi = onizleme ? onizleme.bitis - onizleme.baslangic : 0
  const onizlemeUyarisi = onizleme ? sinirUyarisi(onizlemeSuresi, sinirlar) : null

  return (
    <tr>
      <td
        className={cn(
          'sticky left-0 z-10 border-r border-b border-rule bg-surface px-3 text-left',
          SATIR_YUKSEKLIGI,
          AD_SUTUNU,
          secili && 'ring-2 ring-inset ring-ink',
        )}
        title={`${personel.ad_soyad} · ${personel.sicil_no}`}
      >
        <button
          type="button"
          className="flex w-full flex-col items-start text-left"
          onClick={() => onSatirSec(personel.personel_id)}
        >
          <span className="block max-w-full truncate text-sm text-ink">{personel.ad_soyad}</span>
          <span className="block font-mono text-mono-kucuk text-ink-muted">
            {personel.sicil_no}
            {gunlukSaat > 0 && ` · ${sayiBicimle(gunlukSaat, 0)} sa`}
          </span>
        </button>
      </td>
      {/* Şerit, saat hücrelerinin ÜZERİNDE tek parça durur. Hücreler yalnızca
          ızgara çizgisi ve sürükleme hedefi; blok onların boyanmasıyla değil
          kendi öğesiyle çizilir. */}
      <td className={cn('relative border-b border-rule p-0', SATIR_YUKSEKLIGI)} colSpan={24}>
        <div className="absolute inset-0 flex">
          {Array.from({ length: 24 }, (_, saat) => (
            <div
              key={saat}
              data-saat={saat}
              className={cn(
                'h-full flex-1',
                saat % 3 === 0 && 'border-l border-rule',
                duzenlenebilir && 'cursor-crosshair',
              )}
              onPointerDown={(e) => {
                e.preventDefault()
                onSaatBasla(personel.personel_id, saat, 'yeni')
              }}
              onPointerEnter={() => onSaatUzerinde(personel.personel_id, saat)}
            />
          ))}
        </div>

        {parcalar.map(({ blok, parca }) => (
          <BlokSeridi
            key={blok.atama_id}
            blok={blok}
            parca={parca}
            noktaAdi={noktaMap.get(blok.nokta_id)?.ad ?? ''}
            duzenlenebilir={duzenlenebilir}
            onKenardanTut={(kip, saat) => onSaatBasla(personel.personel_id, saat, kip)}
            onSec={() => onSatirSec(personel.personel_id)}
          />
        ))}

        {onizleme && (
          <div
            className={cn(
              'pointer-events-none absolute inset-y-[3px] z-20 flex items-center justify-center rounded-xs border-2 border-dashed',
              onizlemeUyarisi ? 'border-signal bg-signal-soft/70' : 'border-ink bg-surface/60',
            )}
            style={{
              left: `${(onizleme.baslangic / 24) * 100}%`,
              width: `${(onizlemeSuresi / 24) * 100}%`,
            }}
          >
            <span
              className={cn(
                'truncate px-1 font-mono text-[10px] leading-none font-semibold',
                onizlemeUyarisi ? 'text-signal' : 'text-ink',
              )}
            >
              {onizlemeUyarisi ??
                `${saatEtiketi(onizleme.baslangic)}–${saatEtiketi(onizleme.bitis)}`}
            </span>
          </div>
        )}
      </td>
    </tr>
  )
}

/**
 * Bloğun bir gündeki şeridi.
 *
 * Arka plan, bloğun KENDİ saatlerinin bant gradientidir: gece saatleri koyu,
 * gündüz açık, geçiş sürekli (Tur 6 İş 3). Şerit tek bir öğedir; yirmi dört
 * ayrı hücre boyanmaz.
 */
function BlokSeridi({
  blok,
  parca,
  noktaAdi,
  duzenlenebilir,
  onKenardanTut,
  onSec,
}: {
  blok: Atama
  parca: GunParcasi
  noktaAdi: string
  duzenlenebilir: boolean
  onKenardanTut: (kip: 'sol-kenar' | 'sag-kenar', saat: number) => void
  onSec: () => void
}) {
  const uzunluk = parca.bitis - parca.baslangic
  // Bandın saatleri MUTLAK eksende okunur: ertesi güne düşen parçada 00–06
  // yerine 24–30 verilseydi gradient yanlış uçtan başlardı. `saatRengi` 24'e
  // göre sardığı için ikisi de aynı sonucu verir; okunurluk için parçanın
  // kendi saatleri kullanılır.
  const zemin = aralikGradyani(parca.baslangic, parca.bitis)
  const etiket = blokEtiketi(blok.baslangic_zamani, blok.bitis_zamani)

  return (
    <div
      className={cn(
        'absolute inset-y-[3px] z-10 flex items-center overflow-hidden border border-rule-strong',
        // Kenarın açık kalması gece yarısını aşan bloğun İKİ günde de tek
        // blok olduğunu söyler: kapalı köşe "burada bitti" demektir.
        parca.oncekiGundenGeliyor ? 'rounded-l-none border-l-0' : 'rounded-l-xs',
        parca.sonrakiGuneTasiyor ? 'rounded-r-none border-r-0' : 'rounded-r-xs',
        blok.kilitli && 'outline-2 outline-offset-[-2px] outline-accent',
      )}
      style={{
        left: `${(parca.baslangic / 24) * 100}%`,
        width: `${(uzunluk / 24) * 100}%`,
        backgroundImage: blok.kilitli ? `${KILIT_DOKUSU}, ${zemin}` : zemin,
      }}
      title={blokErisilebilirEtiket(blok, parca, noktaAdi)}
      aria-label={blokErisilebilirEtiket(blok, parca, noktaAdi)}
      onClick={onSec}
    >
      {/* Önceki günden geldiğinin İŞARETİ. Renk değil şekil: ‹ solda "bu şerit
          daha önce başladı" der ve yazdırmada da görünür. */}
      {parca.oncekiGundenGeliyor && (
        <span
          className="shrink-0 px-0.5 font-mono text-[11px] leading-none font-bold"
          style={{ color: saatRengi(parca.baslangic + 12) }}
          aria-hidden="true"
        >
          ‹
        </span>
      )}

      <span
        className="mx-auto flex min-w-0 items-center gap-1 rounded-xs px-1 py-px"
        style={{ background: ETIKET_ZEMINI }}
      >
        <span className="truncate font-mono text-[10px] leading-none font-semibold text-ink">
          {etiket}
        </span>
        {noktaAdi && (
          <span className="truncate font-mono text-[10px] leading-none text-ink-muted">
            {kisalt(noktaAdi)}
          </span>
        )}
      </span>

      {parca.sonrakiGuneTasiyor && (
        <span
          className="shrink-0 px-0.5 font-mono text-[11px] leading-none font-bold"
          style={{ color: saatRengi(parca.bitis + 12) }}
          aria-hidden="true"
        >
          ›
        </span>
      )}

      {/* Kenardan tutup uzatma/kısaltma. Tutamaklar şeridin İÇİNDE durur;
          dışarı taşsalardı komşu saat hücresinin sürükleme hedefini kapatır
          ve yeni blok tanımlamayı imkânsız kılarlardı. */}
      {duzenlenebilir && !parca.oncekiGundenGeliyor && (
        <span
          role="presentation"
          className="absolute inset-y-0 left-0 w-1.5 cursor-ew-resize"
          onPointerDown={(e) => {
            e.preventDefault()
            e.stopPropagation()
            onKenardanTut('sol-kenar', parca.bitis - 1)
          }}
        />
      )}
      {duzenlenebilir && !parca.sonrakiGuneTasiyor && (
        <span
          role="presentation"
          className="absolute inset-y-0 right-0 w-1.5 cursor-ew-resize"
          onPointerDown={(e) => {
            e.preventDefault()
            e.stopPropagation()
            onKenardanTut('sag-kenar', parca.baslangic)
          }}
        />
      )}
    </div>
  )
}
