import { useMemo } from 'react'
import type { Personel } from '@/api/types'
import type { CizelgeVerisi } from '@/lib/disaAktarma'
import { buyukHarf, kisalt } from '@/lib/metin'
import {
  donemAraligiBicimle,
  gunKisaltmasiVeNumarasi,
  gunlerListesi,
  haftaSonuMu,
  tarihBicimle,
} from '@/lib/tarih'
import { cn } from '@/lib/utils'

interface Props extends CizelgeVerisi {
  /** Başlıkta yazan üretim tarihi (ISO). Dışarıdan verilir; bileşen saat okumaz. */
  uretimTarihi: string
}

/**
 * Duvara asılan çizelge — personel × gün matrisi, yatay A4 baskı için
 * (madde 7b).
 *
 * CSV'nin uzun biçiminin aksine burada matris DOĞRU biçimdir: kâğıda bakan
 * kişi "bu kişi bu hafta ne zaman çalışıyor" ve "bugün kimler var" sorularını
 * göz gezdirerek yanıtlar; uzun biçim bunun için okunamaz.
 *
 * Genişlik yatay A4'e sığar; satırlar sayfaya sığmadığında bölünür ve gün
 * başlığı `thead` olduğu için her sayfada yeniden basılır. 36 personel tek
 * sayfaya sığmaz — sığdırmak için satır yüksekliğini okunmaz hâle getirmek
 * gerekirdi.
 *
 * Tarihler Türkçe biçimdedir (madde 5): bu çıktının okuyucusu insandır.
 * CSV'deki ISO ile ayrımı bilinçlidir ve iki biçim de lib/tarih.ts'ten gelir.
 */
export function YazdirilabilirCizelge({
  donem,
  surum,
  atamalar,
  kapsamaAcigi,
  personelMap,
  vardiyaMap,
  noktaMap,
  uretimTarihi,
}: Props) {
  const gunler = gunlerListesi(donem.baslangic_tarihi, donem.bitis_tarihi)

  const atamaIndeksi = useMemo(() => {
    const indeks = new Map<string, (typeof atamalar)[number]>()
    for (const a of atamalar) indeks.set(`${a.personel_id}|${a.tarih}`, a)
    return indeks
  }, [atamalar])

  const personeller = useMemo(() => {
    const idler = new Set(atamalar.map((a) => a.personel_id))
    return [...idler]
      .map((id) => personelMap.get(id))
      .filter((p): p is Personel => p !== undefined)
      .sort((a, b) => a.ad_soyad.localeCompare(b.ad_soyad, 'tr'))
  }, [atamalar, personelMap])

  const acikSatirlari = useMemo(
    () =>
      kapsamaAcigi
        .slice()
        .sort((a, b) => a.tarih.localeCompare(b.tarih) || a.nokta_id - b.nokta_id),
    [kapsamaAcigi],
  )
  const toplamEksik = acikSatirlari.reduce((toplam, k) => toplam + k.eksik_sayi, 0)

  return (
    <div className="yazdirma-alani bg-white text-black">
      {/* flex-wrap: iki parça yatay A4'ün yazım alanını tam dolduruyor
          (ölçüldü: 1062px'in 1062'si). Ay değiştiren bir dönem etiketi
          ("27 Tem – 23 Ağu 2026") bunu taşırırdı; sarmak, kırpmaya yeğdir. */}
      <header className="mb-3 flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 border-b border-black pb-2">
        <h1 className="m-0 text-base font-semibold">
          {buyukHarf('Vardiya Çizelgesi')} ·{' '}
          {donemAraligiBicimle(donem.baslangic_tarihi, donem.bitis_tarihi)}
        </h1>
        <p className="m-0 font-mono text-[10px]">
          Sürüm {surum.surum_no} · {gunler.length} gün · {personeller.length} personel ·{' '}
          {tarihBicimle(uretimTarihi)} tarihinde üretildi
        </p>
      </header>

      <table className="yazdirma-tablo w-full border-collapse">
        <thead>
          <tr>
            <th className="border border-neutral-400 px-1 py-0.5 text-left text-[8pt] font-semibold">
              Personel
            </th>
            {gunler.map((gun) => (
              <th
                key={gun}
                className={cn(
                  'border border-neutral-400 px-0.5 py-0.5 text-center font-mono text-[7pt] font-semibold',
                  haftaSonuMu(gun) && 'bg-neutral-200',
                )}
              >
                {gunKisaltmasiVeNumarasi(gun)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {personeller.map((p) => (
            <tr key={p.personel_id}>
              <td className="border border-neutral-400 px-1 py-0.5 text-[8pt] whitespace-nowrap">
                {p.ad_soyad}
              </td>
              {gunler.map((gun) => {
                const atama = atamaIndeksi.get(`${p.personel_id}|${gun}`)
                const vardiya = atama ? vardiyaMap.get(atama.vardiya_tipi_id) : undefined
                const nokta = atama ? noktaMap.get(atama.nokta_id) : undefined
                return (
                  <td
                    key={gun}
                    className={cn(
                      'border border-neutral-400 px-0.5 py-0.5 text-center font-mono text-[6.5pt] leading-tight',
                      haftaSonuMu(gun) && 'bg-neutral-100',
                      vardiya?.gece_mi && 'font-semibold',
                    )}
                  >
                    {atama && (
                      <>
                        {kisalt(vardiya?.ad ?? '')}
                        <br />
                        {kisalt(nokta?.ad ?? '')}
                      </>
                    )}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>

      <section className="mt-4 break-inside-avoid">
        <h2 className="m-0 mb-1 text-[9pt] font-semibold">Kapsama Açıkları</h2>
        {acikSatirlari.length === 0 ? (
          // Bölüm hiç açık olmadığında da basılır. Gizlenirse okuyucu,
          // çıktının açıkları hiç göstermediği bir sürüm mü yoksa açığı
          // olmayan bir çizelge mi olduğunu ayırt edemez.
          <p className="m-0 text-[8pt]">Bu sürümde kapsama açığı yok.</p>
        ) : (
          <>
            <p className="m-0 mb-1 text-[8pt]">
              {acikSatirlari.length} hücrede toplam {toplamEksik} kişi eksik.
            </p>
            <table className="w-auto border-collapse">
              <thead>
                <tr>
                  {['Tarih', 'Vardiya', 'Görev Noktası', 'Eksik'].map((b) => (
                    <th
                      key={b}
                      className="border border-neutral-400 px-2 py-0.5 text-left text-[8pt] font-semibold"
                    >
                      {b}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {acikSatirlari.map((k) => (
                  <tr key={k.acik_id}>
                    <td className="border border-neutral-400 px-2 py-0.5 text-[8pt]">
                      {tarihBicimle(k.tarih)}
                    </td>
                    <td className="border border-neutral-400 px-2 py-0.5 text-[8pt]">
                      {vardiyaMap.get(k.vardiya_tipi_id)?.ad ?? '—'}
                    </td>
                    <td className="border border-neutral-400 px-2 py-0.5 text-[8pt]">
                      {noktaMap.get(k.nokta_id)?.ad ?? '—'}
                    </td>
                    <td className="border border-neutral-400 px-2 py-0.5 text-right font-mono text-[8pt]">
                      {k.eksik_sayi}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </section>
    </div>
  )
}
