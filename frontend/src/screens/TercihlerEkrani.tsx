import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import type { Personel, Tercih, TercihDurumu, VardiyaTipi } from '../api/types'
import { AppShell, type NavOgesi } from '../components/AppShell'
import { Buton, Kart } from '../components/app-ui'
import { cn } from '../lib/utils'
import { gunKisaltmasiVeNumarasi } from '../lib/tarih'

interface Props {
  ekranSec: (ekran: NavOgesi) => void
}

const SEKMELER: { durum: TercihDurumu; baslik: string }[] = [
  { durum: 'beklemede', baslik: 'Bekleyen' },
  { durum: 'onaylandi', baslik: 'Onaylandı' },
  { durum: 'reddedildi', baslik: 'Reddedildi' },
]

function tercihAciklamasi(t: Tercih, vardiyaMap: Map<number, VardiyaTipi>): string {
  if (t.tip === 'calismama') return 'Çalışmama tercihi'
  const vardiya = t.vardiya_tipi_id ? vardiyaMap.get(t.vardiya_tipi_id) : undefined
  return vardiya ? `${vardiya.ad} tercihi` : 'Vardiya tipi tercihi'
}

export function TercihlerEkrani({ ekranSec }: Props) {
  const [tercihler, setTercihler] = useState<Tercih[]>([])
  const [personelListesi, setPersonelListesi] = useState<Personel[]>([])
  const [vardiyaTipleri, setVardiyaTipleri] = useState<VardiyaTipi[]>([])
  const [sekme, setSekme] = useState<TercihDurumu>('beklemede')
  const [hata, setHata] = useState<string | null>(null)
  const [islenenId, setIslenenId] = useState<number | null>(null)

  const yukle = () => {
    Promise.all([api.tercihListele(), api.personelListele(), api.vardiyaTipiListele()])
      .then(([t, p, v]) => {
        setTercihler(t)
        setPersonelListesi(p)
        setVardiyaTipleri(v)
      })
      .catch((e) => setHata(e instanceof Error ? e.message : 'Tercihler yüklenemedi'))
  }

  useEffect(yukle, [])

  const personelMap = useMemo(
    () => new Map(personelListesi.map((p) => [p.personel_id, p])),
    [personelListesi],
  )
  const vardiyaMap = useMemo(
    () => new Map(vardiyaTipleri.map((v) => [v.vardiya_tipi_id, v])),
    [vardiyaTipleri],
  )

  const durumGuncelle = async (tercihId: number, durum: TercihDurumu) => {
    setIslenenId(tercihId)
    setHata(null)
    try {
      await api.tercihDurumGuncelle(tercihId, durum)
      yukle()
    } catch (e) {
      setHata(e instanceof Error ? e.message : 'Tercih güncellenemedi')
    } finally {
      setIslenenId(null)
    }
  }

  const sayilar: Record<TercihDurumu, number> = {
    beklemede: tercihler.filter((t) => t.durum === 'beklemede').length,
    onaylandi: tercihler.filter((t) => t.durum === 'onaylandi').length,
    reddedildi: tercihler.filter((t) => t.durum === 'reddedildi').length,
  }

  const gosterilenler = tercihler
    .filter((t) => t.durum === sekme)
    .sort((a, b) => a.tarih.localeCompare(b.tarih))

  return (
    <AppShell aktifEkran="Tercihler" ekranSec={ekranSec} baslik="Tercihler">
      {hata && <p className="text-sm text-signal">{hata}</p>}

      <div className="flex gap-2">
        {SEKMELER.map((s) => (
          <button
            key={s.durum}
            type="button"
            onClick={() => setSekme(s.durum)}
            className={cn(
              'flex items-center gap-2 rounded-sm border border-rule bg-surface px-4 py-2.5 text-sm text-ink-muted',
              s.durum === sekme && 'border-accent bg-surface font-medium text-ink',
            )}
          >
            {s.baslik}
            <span className="flex size-5 items-center justify-center rounded-full bg-accent-soft font-mono text-[11px] text-accent">
              {sayilar[s.durum]}
            </span>
          </button>
        ))}
      </div>

      <Kart>
        {gosterilenler.length === 0 ? (
          <p className="text-sm text-ink-muted">Bu durumda tercih yok.</p>
        ) : (
          <ul className="m-0 flex list-none flex-col p-0">
            {gosterilenler.map((t) => {
              const personel = personelMap.get(t.personel_id)
              return (
                <li
                  key={t.tercih_id}
                  className="flex items-center gap-6 border-t border-rule py-4 first:border-none"
                >
                  <div className="w-36 shrink-0">
                    <p className="m-0 text-sm font-semibold text-ink">
                      {personel?.ad_soyad ?? `#${t.personel_id}`}
                    </p>
                    <p className="m-0 font-mono text-xs text-ink-muted">{personel?.sicil_no ?? '—'}</p>
                  </div>
                  <span className="w-20 shrink-0 font-mono text-sm font-semibold text-ink">
                    {gunKisaltmasiVeNumarasi(t.tarih).toUpperCase()}
                  </span>
                  <p className="m-0 flex-1 text-sm text-ink">{tercihAciklamasi(t, vardiyaMap)}</p>
                  {sekme === 'beklemede' && (
                    <div className="flex shrink-0 gap-2">
                      <Buton
                        varyant="ikincil"
                        disabled={islenenId === t.tercih_id}
                        onClick={() => durumGuncelle(t.tercih_id, 'reddedildi')}
                      >
                        Reddet
                      </Buton>
                      <Buton
                        varyant="birincil"
                        disabled={islenenId === t.tercih_id}
                        onClick={() => durumGuncelle(t.tercih_id, 'onaylandi')}
                      >
                        Onayla
                      </Buton>
                    </div>
                  )}
                </li>
              )
            })}
          </ul>
        )}
      </Kart>
    </AppShell>
  )
}
