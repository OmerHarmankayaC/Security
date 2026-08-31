import { useCallback, useMemo, useRef, useState } from 'react'
import type { Atama, GorevNoktasi, KapsamaAcigi, Personel } from '@/api/types'
import {
  blokErisilebilirEtiket,
  blokEtiketi,
  gununParcalari,
  saatEtiketi,
  sapmaGunu,
  sapmaSuresi,
  type GunParcasi,
} from '@/lib/blok'
import { sinirUyarisi, type BlokSinirlari } from '@/lib/kuralParametre'
import { gunEkle } from '@/lib/tarih'
import { kisalt } from '@/lib/metin'
import { sayiBicimle } from '@/lib/sayi'
import { ETIKET_ZEMINI, KILIT_DOKUSU, aralikGradyani, saatRengi } from '@/lib/saatRengi'
import { cn } from '@/lib/utils'
import { useMetin } from '@/i18n/DilBaglami'

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

/**
 * Sürükleme durumu.
 *
 * Dört kip: boş satırda YENİ blok, bloğun iki KENARI (uzat/kısalt) ve
 * GÖVDE (gün içinde kaydır ya da başka personele taşı). Gövde kipinde
 * `hedefPersonelId` imleç hangi satırdaysa oraya kayar; ötekilerde kaynakla
 * aynı kalır — bir bloğun kenarını çekerken satır değiştirmek anlamsızdır.
 */
type SuruklemeKipi = 'yeni' | 'sol-kenar' | 'sag-kenar' | 'govde'

interface Surukleme {
  kaynakPersonelId: number
  hedefPersonelId: number
  kip: SuruklemeKipi
  /** Basılan saat — çapa. Sürükleme geriye doğru da olabilir. */
  capa: number
  /** İmlecin bulunduğu saat. */
  imlec: number
  /** Gövde kipinde bloğun süresi (korunur) ve tutulan noktanın bloğa uzaklığı. */
  sure: number
  tutmaKaymasi: number
  /** Taşınan/boyutlandırılan bloğun görev noktası; yeni blokta null. */
  noktaId: number | null
}

/**
 * Sürüklemenin ürettiği saat aralığı — SINIRLARA DAYANINCA DURUR.
 *
 * Kullanıcı geçersiz bir seçim yapıp sonradan reddedilmek yerine sınırı
 * elinde hissetmeli (Tur 7 İş 1). Bu yüzden aralık uyarıyla işaretlenmez,
 * KIRPILIR: asgarinin altına inen sürükleme asgaride, azaminin üstüne çıkan
 * azamide durur. Değerler kural kataloğundan gelir; sınır tanımsızsa (kural
 * pasif) kırpma da yapılmaz.
 */
function araligaCevir(
  s: Surukleme,
  sinirlar: BlokSinirlari,
): { baslangic: number; bitis: number } {
  if (s.kip === 'govde') {
    // Süre KORUNUR; yalnızca başlangıç kayar. Tutulan noktanın bloğa
    // uzaklığı çıkarılır, yoksa blok imlecin altına zıplar.
    const bas = s.imlec - s.tutmaKaymasi
    return { baslangic: ((bas % 24) + 24) % 24, bitis: bas + s.sure }
  }

  const ham = { baslangic: Math.min(s.capa, s.imlec), bitis: Math.max(s.capa, s.imlec) + 1 }
  // Hangi uç SABİT: sol kenar çekilirken sağ uç, sağ kenar çekilirken sol uç.
  // Yeni blokta çapa sabittir ve imleç hangi yöne gittiyse o uç oynar.
  const sagaBuyuyor = s.kip === 'sol-kenar' ? false : s.imlec >= s.capa
  return kirp(ham, sagaBuyuyor, sinirlar)
}

function kirp(
  aralik: { baslangic: number; bitis: number },
  sagaBuyuyor: boolean,
  sinirlar: BlokSinirlari,
): { baslangic: number; bitis: number } {
  let { baslangic, bitis } = aralik
  const sure = bitis - baslangic
  if (sinirlar.asgariSaat !== null && sure < sinirlar.asgariSaat) {
    if (sagaBuyuyor) bitis = baslangic + sinirlar.asgariSaat
    else baslangic = bitis - sinirlar.asgariSaat
  }
  if (sinirlar.azamiSaat !== null && bitis - baslangic > sinirlar.azamiSaat) {
    if (sagaBuyuyor) bitis = baslangic + sinirlar.azamiSaat
    else baslangic = bitis - sinirlar.azamiSaat
  }
  // Kırpma günün dışına taşabilir; ızgara 0–24 arasıdır.
  if (baslangic < 0) {
    bitis -= baslangic
    baslangic = 0
  }
  if (bitis > 24) {
    baslangic -= bitis - 24
    bitis = 24
  }
  return { baslangic: Math.max(0, baslangic), bitis: Math.min(24, bitis) }
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
  /**
   * Blok taşındığında. Kaynak ve hedef AYNI olabilir — o zaman gün içinde
   * kaydırmadır. Ekran bunu iki değişikliğe çevirir (SDD 5.5).
   */
  onBlokTasi: (
    kaynakPersonelId: number,
    hedefPersonelId: number,
    baslangic: number,
    bitis: number,
  ) => void
  /** Blok menüsünün üç eylemi (SDD 6.3.3). */
  onNoktaDegistir: (personelId: number, noktaId: number) => void
  onKilitDegistir: (personelId: number, kilitli: boolean) => void
  onBlokSil: (personelId: number) => void
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
  onBlokTasi,
  onNoktaDegistir,
  onKilitDegistir,
  onBlokSil,
}: GunIzgarasiProps) {
  const [surukleme, setSurukleme] = useState<Surukleme | null>(null)
  // Açık blok menüsü — hangi personelin satırında (SDD 6.3.3).
  const [menuPersonelId, setMenuPersonelId] = useState<number | null>(null)
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
      // Aralık gün sınırını aşabilir (B-23): 22.00–02.00 tek kayıttır ve
      // İKİ günün ızgarasında da işaretlenmelidir. Bu yüzden filtre kaydın
      // gününe değil, açılan SAATLERİN gününe bakar.
      const bas = Number(k.baslangic_zamani.slice(11, 13))
      const sure = sapmaSuresi(k)
      for (let i = 0; i < sure; i += 1) {
        const mutlak = bas + i
        if (gunEkle(sapmaGunu(k), Math.floor(mutlak / 24)) !== gun) continue
        const saat = mutlak % 24
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

    if (son.kip === 'govde') {
      // Ne satır ne saat değiştiyse taşıma yoktur; tek tık MENÜYÜ açar.
      const kaymadi = son.imlec === son.capa && son.hedefPersonelId === son.kaynakPersonelId
      if (kaymadi) {
        setMenuPersonelId(son.kaynakPersonelId)
        return
      }
      const { baslangic, bitis } = araligaCevir(son, sinirlar)
      onBlokTasi(son.kaynakPersonelId, son.hedefPersonelId, baslangic, bitis)
      return
    }

    // İMLEÇ HİÇ KIPIRDAMADIYSA BLOK TANIMLANMAZ. Tek tık, satırı seçmektir;
    // bir saatlik blok üretip ardından "asgari dört saat" diye reddetmek,
    // kullanıcının yapmadığı bir işlemi ona geri okumak olurdu. Kenardan
    // tutup bırakmak da aynı nedenle sessizce hiçbir şey yapmaz.
    if (son.imlec === son.capa) return
    const { baslangic, bitis } = araligaCevir(son, sinirlar)
    onBlokTanimla(son.kaynakPersonelId, baslangic, bitis)
  }, [onBlokTanimla, onBlokTasi, sinirlar])

  const suruklemeBasla = (yeni: Surukleme) => {
    if (!duzenlenebilir) return
    setMenuPersonelId(null)
    suruklemeRef.current = yeni
    setSurukleme(yeni)
    onSatirSec(yeni.kaynakPersonelId)
  }

  const saatBasla = (personelId: number, saat: number, kip: SuruklemeKipi) => {
    suruklemeBasla({
      kaynakPersonelId: personelId,
      hedefPersonelId: personelId,
      kip,
      capa: saat,
      imlec: saat,
      sure: 0,
      tutmaKaymasi: 0,
      noktaId: null,
    })
  }

  /**
   * İmleç bir saat hücresine girdi.
   *
   * GÖVDE kipinde satır da güncellenir: kullanıcı bloğu başka bir personelin
   * satırına sürükleyebilir. Öteki kiplerde satır sabittir — bir bloğun
   * kenarını çekerken satır değiştirmek tanımsızdır.
   */
  const saatUzerinde = (personelId: number, saat: number) => {
    const mevcut = suruklemeRef.current
    if (!mevcut) return
    if (mevcut.kip !== 'govde' && mevcut.kaynakPersonelId !== personelId) return
    if (mevcut.imlec === saat && mevcut.hedefPersonelId === personelId) return
    const yeni = { ...mevcut, imlec: saat, hedefPersonelId: personelId }
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
              // Önizleme HEDEF satırda çizilir: kullanıcı bloğu nereye
              // bırakacağını orada görür. Kaynak satır ise sürükleme
              // boyunca soluklaşır (bkz. PersonelSatiri).
              surukleme={surukleme?.hedefPersonelId === p.personel_id ? surukleme : null}
              kaynakMi={surukleme?.kaynakPersonelId === p.personel_id}
              menuAcik={menuPersonelId === p.personel_id}
              noktalar={seritNoktalari}
              onSatirSec={onSatirSec}
              onSaatBasla={saatBasla}
              onGovdeBasla={suruklemeBasla}
              onSaatUzerinde={saatUzerinde}
              onMenuKapat={() => setMenuPersonelId(null)}
              onNoktaDegistir={onNoktaDegistir}
              onKilitDegistir={onKilitDegistir}
              onBlokSil={onBlokSil}
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
  const m = useMetin()
  if (seritNoktalari.length === 0) return null
  return (
    <tr>
      <td
        className={cn(
          'etiket-caps sticky left-0 z-10 h-[26px] border-r border-b border-rule bg-surface px-3 text-ink-muted',
          adSutunu,
        )}
        title={m.izgara.basamakSirasi(seritNoktalari.map((n) => n.ad).join(' · '))}
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
            title={eksik > 0 ? `${saatEtiketi(saat)} · ${adlar}` : undefined}
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
  kaynakMi,
  menuAcik,
  noktalar,
  onSatirSec,
  onSaatBasla,
  onGovdeBasla,
  onSaatUzerinde,
  onMenuKapat,
  onNoktaDegistir,
  onKilitDegistir,
  onBlokSil,
}: {
  gun: string
  personel: Personel
  bloklar: readonly Atama[]
  noktaMap: Map<number, GorevNoktasi>
  secili: boolean
  duzenlenebilir: boolean
  sinirlar: BlokSinirlari
  surukleme: Surukleme | null
  kaynakMi: boolean
  menuAcik: boolean
  noktalar: readonly GorevNoktasi[]
  onSatirSec: (personelId: number) => void
  onSaatBasla: (personelId: number, saat: number, kip: SuruklemeKipi) => void
  onGovdeBasla: (s: Surukleme) => void
  onSaatUzerinde: (personelId: number, saat: number) => void
  onMenuKapat: () => void
  onNoktaDegistir: (personelId: number, noktaId: number) => void
  onKilitDegistir: (personelId: number, kilitli: boolean) => void
  onBlokSil: (personelId: number) => void
}) {
  const m = useMetin()
  const parcalar = useMemo(() => gununParcalari(bloklar, gun), [bloklar, gun])

  // Gün toplamı, o gün BAŞLAYAN bloğun tamamıdır (SRS TD-1): gece yarısını
  // aşan blok başladığı güne sayılır, ertesi günün toplamına girmez.
  const gunlukSaat = useMemo(
    () => bloklar.filter((b) => b.tarih === gun).reduce((t, b) => t + b.sure_saat, 0),
    [bloklar, gun],
  )

  const onizleme = surukleme ? araligaCevir(surukleme, sinirlar) : null
  const onizlemeSuresi = onizleme ? onizleme.bitis - onizleme.baslangic : 0
  // Aralık artık KIRPILDIĞI için uyarı yalnızca sınıra DAYANILDIĞINI söyler;
  // engel değil, geri bildirimdir. Kullanıcı sınırı elinde hisseder.
  const sinirdaMi =
    onizleme !== null &&
    ((sinirlar.asgariSaat !== null && onizlemeSuresi === sinirlar.asgariSaat) ||
      (sinirlar.azamiSaat !== null && onizlemeSuresi === sinirlar.azamiSaat))
  const onizlemeUyarisi = sinirdaMi ? sinirUyarisi(onizlemeSuresi, sinirlar, m, true) : null

  // O gün BAŞLAYAN blok — menü ve gövde sürüklemesi onun üzerinde çalışır.
  const gununBlogu = bloklar.find((b) => b.tarih === gun) ?? null

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
            // Sürükleme sırasında KAYNAK şerit soluklaşır: blok artık orada
            // değil, imlecin altında.
            soluk={kaynakMi && surukleme?.kip === 'govde'}
            onKenardanTut={(kip, saat) => onSaatBasla(personel.personel_id, saat, kip)}
            onGovdedenTut={(saat) =>
              onGovdeBasla({
                kaynakPersonelId: personel.personel_id,
                hedefPersonelId: personel.personel_id,
                kip: 'govde',
                capa: saat,
                imlec: saat,
                sure: blok.sure_saat,
                // Bloğun neresinden tutulduğu korunur; yoksa blok imlecin
                // altına zıplar ve kullanıcı tuttuğu yeri kaybeder.
                tutmaKaymasi: saat - parca.baslangic,
                noktaId: blok.nokta_id,
              })
            }
            onSec={() => onSatirSec(personel.personel_id)}
          />
        ))}

        {menuAcik && gununBlogu && duzenlenebilir && (
          <BlokMenusu
            blok={gununBlogu}
            noktalar={noktalar}
            onNoktaDegistir={(noktaId: number) => {
              onNoktaDegistir(personel.personel_id, noktaId)
              onMenuKapat()
            }}
            onKilitDegistir={() => {
              onKilitDegistir(personel.personel_id, !gununBlogu.kilitli)
              onMenuKapat()
            }}
            onSil={() => {
              onBlokSil(personel.personel_id)
              onMenuKapat()
            }}
            onKapat={onMenuKapat}
          />
        )}

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
  soluk,
  onKenardanTut,
  onGovdedenTut,
  onSec,
}: {
  blok: Atama
  parca: GunParcasi
  noktaAdi: string
  duzenlenebilir: boolean
  soluk: boolean
  onKenardanTut: (kip: 'sol-kenar' | 'sag-kenar', saat: number) => void
  onGovdedenTut: (saat: number) => void
  onSec: () => void
}) {
  const m = useMetin()
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
        soluk && 'opacity-30',
        duzenlenebilir && 'cursor-grab',
      )}
      style={{
        left: `${(parca.baslangic / 24) * 100}%`,
        width: `${(uzunluk / 24) * 100}%`,
        backgroundImage: blok.kilitli ? `${KILIT_DOKUSU}, ${zemin}` : zemin,
      }}
      title={blokErisilebilirEtiket(blok, parca, noktaAdi, m)}
      aria-label={blokErisilebilirEtiket(blok, parca, noktaAdi, m)}
      data-blok={blok.atama_id}
      onClick={onSec}
      onPointerDown={(e) => {
        if (!duzenlenebilir) return
        // Kenar tutamakları kendi olaylarını durduruyor; buraya yalnızca
        // GÖVDEYE basılan olay ulaşır.
        e.preventDefault()
        const kap = e.currentTarget.parentElement
        if (!kap) return
        // İmlecin hangi saatin üzerinde olduğu, şeridin kabına göre oranla
        // bulunur — hücreler `pointerdown`ı görmüyor, şerit onların üstünde.
        // Genişlik sıfırsa (henüz yerleşmemiş kap) bölme NaN üretir ve
        // NaN === NaN false olduğu için "kıpırdamadı" kontrolü sessizce
        // çöker: tek tık taşımaya dönüşür. Sıfır genişlikte parçanın
        // başlangıcı kullanılır.
        const genislik = kap.clientWidth
        const oran = genislik > 0 ? (e.clientX - kap.getBoundingClientRect().left) / genislik : 0
        const saat = Math.floor(oran * 24)
        onGovdedenTut(Number.isFinite(saat) ? Math.max(0, Math.min(23, saat)) : parca.baslangic)
      }}
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


/**
 * Bloğa tıklandığında açılan küçük menü (SDD 6.3.3).
 *
 * Üç eylem: görev noktasını değiştir, kilitle, sil. SİLME BURADADIR ve
 * görünürdür — eski ekranda "hücreyi boşaltmak için başlangıcı '— Boşalt —'
 * yapın" diye bir açılır listenin içine saklanmıştı; bir işlemi başka bir
 * işlemin seçeneği hâline getirmek onu bulunmaz kılar.
 */
function BlokMenusu({
  blok,
  noktalar,
  onNoktaDegistir,
  onKilitDegistir,
  onSil,
  onKapat,
}: {
  blok: Atama
  noktalar: readonly GorevNoktasi[]
  onNoktaDegistir: (noktaId: number) => void
  onKilitDegistir: () => void
  onSil: () => void
  onKapat: () => void
}) {
  const m = useMetin()
  return (
    <>
      {/* Dışarı tıklama menüyü kapatır. Şeffaf katman ızgaranın tamamını
          kaplar; menünün kendisi onun üstünde durur. */}
      <span className="fixed inset-0 z-30" onPointerDown={onKapat} aria-hidden="true" />
      <div
        role="menu"
        aria-label={m.izgara.blokIslemleri}
        className="absolute top-full left-0 z-40 mt-1 flex w-56 flex-col gap-1 rounded-sm border border-rule bg-surface p-2 shadow-lg"
      >
        <label className="flex flex-col gap-1 text-sm text-ink-muted">
          {m.izgara.gorevNoktasi}
          <select
            className="h-8 rounded-sm border border-rule bg-surface px-2 font-mono text-sm text-ink"
            value={blok.nokta_id}
            onChange={(e) => onNoktaDegistir(Number(e.target.value))}
          >
            {noktalar.map((n) => (
              <option key={n.nokta_id} value={n.nokta_id}>
                {n.ad}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          role="menuitem"
          className="rounded-sm px-2 py-1.5 text-left text-sm text-ink hover:bg-sunken"
          onClick={onKilitDegistir}
        >
          {blok.kilitli ? m.izgara.kilidiAc : m.izgara.kilitle}
        </button>
        <button
          type="button"
          role="menuitem"
          className="rounded-sm px-2 py-1.5 text-left text-sm text-signal hover:bg-signal-soft"
          onClick={onSil}
        >
          {m.izgara.blogunuSil}
        </button>
      </div>
    </>
  )
}
