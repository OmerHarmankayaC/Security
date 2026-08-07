import { useMemo } from 'react'
import type { Vardiyalarim, Vardiyam } from '@/api/types'
import { Kart, KartEtiketi, Rozet, Sayi } from '@/components/app-ui'
import { buyukHarf } from '@/lib/metin'
import {
  gunEtiketi,
  gunKisaltmasiVeNumarasi,
  gunlerListesi,
  isoBicimle,
  tarihUzunBicim,
  zamanBicimle,
} from '@/lib/tarih'
import { vardiyaHucreSinifi } from '@/lib/vardiyaRenk'
import { cn } from '@/lib/utils'

interface Props {
  veri: Vardiyalarim
}

function saatAraligi(v: Vardiyam): string {
  return `${v.baslangic_saati.slice(0, 5)}-${v.bitis_saati.slice(0, 5)}`
}

export function VardiyalarimEkrani({ veri }: Props) {
  const bugun = isoBicimle(new Date())
  const vardiyaMap = useMemo(
    () => new Map(veri.vardiyalar.map((v) => [v.tarih, v])),
    [veri.vardiyalar],
  )

  if (veri.donem_id === null) {
    return (
      <Kart>
        <p className="m-0 text-sm text-ink-muted">Aktif bir planlama dönemi yok.</p>
      </Kart>
    )
  }

  if (!veri.yayinlanmis_surum_var) {
    return (
      <Kart>
        <p className="m-0 text-sm text-ink-muted">
          Bu dönem için henüz yayınlanmış bir çizelge yok.
        </p>
      </Kart>
    )
  }

  const gunler = gunlerListesi(veri.donem_baslangic_tarihi!, veri.donem_bitis_tarihi!)
  const degisenGunSayisi = veri.vardiyalar.filter((v) => v.degisim_tipi !== null).length

  return (
    <>
      {veri.siradaki && (
        <Kart
          className={cn(
            'border-none',
            vardiyaHucreSinifi(veri.siradaki.gece_mi, veri.siradaki.baslangic_saati),
          )}
        >
          <p
            className={cn(
              'mb-4 font-condensed text-[10px] font-medium tracking-[0.14em]',
              veri.siradaki.gece_mi ? 'text-vardiya-gece-ink-muted' : 'text-ink-muted',
            )}
          >
            {buyukHarf('Sıradaki Vardiyan')}
          </p>
          <p className={cn('m-0 text-lg font-semibold', veri.siradaki.gece_mi ? 'text-vardiya-gece-ink' : 'text-ink')}>
            {gunEtiketi(veri.siradaki.tarih, bugun)} · {tarihUzunBicim(veri.siradaki.tarih)}
          </p>
          <div className="mt-2 flex items-center gap-2">
            <Sayi
              className={cn(
                'text-2xl font-semibold',
                veri.siradaki.gece_mi ? 'text-vardiya-gece-ink' : 'text-ink',
              )}
            >
              {saatAraligi(veri.siradaki)}
            </Sayi>
            <BeyazEtiket genislik={88}>
              {veri.siradaki.gece_mi
                ? 'Gece'
                : Number(veri.siradaki.baslangic_saati.slice(0, 2)) >= 14
                  ? 'Akşam'
                  : 'Gündüz'}
            </BeyazEtiket>
            <BeyazEtiket genislik={110}>{veri.siradaki.nokta_ad}</BeyazEtiket>
          </div>
        </Kart>
      )}

      <Kart>
        <KartEtiketi>Dönem Görünümü · {gunler.length} Gün</KartEtiketi>
        <div className="grid grid-cols-7 gap-px overflow-hidden rounded-sm border border-rule bg-rule">
          {gunler.map((g) => (
            <div key={`baslik-${g}`} className="bg-sunken py-1.5 text-center font-condensed text-[10px] tracking-[0.1em] text-ink-muted">
              {buyukHarf(gunKisaltmasiVeNumarasi(g).split(' ')[0] ?? '')}
            </div>
          ))}
          {gunler.map((g) => {
            const v = vardiyaMap.get(g)
            const bugunMu = g === bugun
            return (
              <div
                key={g}
                className={cn(
                  'flex flex-col items-center gap-0.5 py-3 text-sm',
                  v ? vardiyaHucreSinifi(v.gece_mi, v.baslangic_saati) : 'bg-surface text-ink-muted',
                  bugunMu && 'ring-2 ring-inset ring-accent',
                )}
              >
                <Sayi className="text-base font-semibold">{g.slice(-2)}</Sayi>
                <span className="font-condensed text-[10px] tracking-[0.08em]">
                  {v ? buyukHarf(v.nokta_ad.slice(0, 3)) : '–'}
                </span>
              </div>
            )
          })}
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-ink-muted">
          <LegendOgesi renk="bg-vardiya-gunduz border border-rule" etiket="Gündüz" />
          <LegendOgesi renk="bg-vardiya-aksam" etiket="Akşam" />
          <LegendOgesi renk="bg-vardiya-gece" etiket="Gece" />
          <LegendOgesi renk="bg-accent" etiket="Değişti" />
        </div>
      </Kart>

      <Kart>
        <KartEtiketi>Vardiya Listesi · {veri.vardiyalar.length} Vardiya</KartEtiketi>
        {veri.vardiyalar.length === 0 ? (
          <p className="m-0 text-sm text-ink-muted">Bu dönemde vardiyan yok.</p>
        ) : (
          <ul className="m-0 flex list-none flex-col p-0">
            {veri.vardiyalar.map((v) => (
              <li
                key={v.tarih}
                className={cn(
                  'flex items-center gap-4 border-t border-rule py-3 pl-3 first:border-none',
                  'border-l-2',
                  v.degisim_tipi ? 'border-l-accent' : 'border-l-transparent',
                )}
              >
                <Sayi className="w-16 shrink-0 text-sm font-semibold text-ink">
                  {gunKisaltmasiVeNumarasi(v.tarih)}
                </Sayi>
                <span className="w-16 shrink-0 text-sm text-ink-muted">{gunEtiketi(v.tarih, bugun)}</span>
                <Sayi className="w-24 shrink-0 text-sm text-ink">{saatAraligi(v)}</Sayi>
                <span className="font-condensed text-[10px] tracking-[0.08em] text-ink-muted">
                  {buyukHarf(v.gece_mi ? 'Gece' : Number(v.baslangic_saati.slice(0, 2)) >= 14 ? 'Akşam' : 'Gündüz')}
                </span>
                <span className="flex-1 text-sm text-ink">{v.nokta_ad}</span>
                {v.degisim_tipi && (
                  <Rozet varyant="kilitli" genislik={72}>
                    {v.degisim_tipi === 'eklendi' ? 'Eklendi' : 'Değişti'}
                  </Rozet>
                )}
              </li>
            ))}
          </ul>
        )}
      </Kart>

      {veri.yayin_zamani && (
        <p className="m-0 rounded-sm bg-sunken px-4 py-3 text-sm text-ink-muted">
          Bu çizelge {zamanBicimle(veri.yayin_zamani)} tarihinde yayınlandı.
          {degisenGunSayisi > 0
            ? ` ${degisenGunSayisi} günün bir önceki sürüme göre değişti.`
            : ''}
        </p>
      )}
    </>
  )
}

function LegendOgesi({ renk, etiket }: { renk: string; etiket: string }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className={cn('size-3 rounded-xs', renk)} />
      {etiket}
    </span>
  )
}

// "Sıradaki Vardiyan" kartı vardiyanın kendi renginde olduğundan (koyu/açık
// değişebilir), üzerindeki rozetler her zaman beyaz zeminle sabit kontrast
// sağlar — Rozet bileşeninin varyantları buradaki değişken zemine göre
// otomatik kontrast vermez.
function BeyazEtiket({ children, genislik }: { children: string; genislik: number }) {
  return (
    <span
      className="flex items-center justify-center rounded-sm bg-surface px-2.5 py-1 font-condensed text-[10px] tracking-[0.08em] text-ink"
      style={{ width: genislik }}
    >
      {buyukHarf(children)}
    </span>
  )
}
