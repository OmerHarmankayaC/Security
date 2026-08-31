import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import type { Personel, Tercih, TercihDurumu } from '../api/types'
import { AppShell, type NavOgesi } from '../components/AppShell'
import { Buton, Kart } from '../components/app-ui'
import { Input } from '@/components/ui/input'
import { cn } from '../lib/utils'
import { araligiYaz } from '../lib/talepAraligi'
import { gunKisaltmasiVeNumarasi } from '../lib/tarih'
import { useMetin } from '@/i18n/DilBaglami'
import { hataMetni } from '@/i18n/hata'
import type { Metinler } from '@/i18n/sozluk'
import { BOS } from '@/lib/sayi'

interface Props {
  ekranSec: (ekran: NavOgesi) => void
}

// Sekme KİMLİĞİ burada, başlığı sözlükte.
const SEKMELER: TercihDurumu[] = ['beklemede', 'onaylandi', 'reddedildi']

function tercihAciklamasi(t: Tercih, m: Metinler): string {
  if (t.tip === 'calismama') return m.tercihYonetimi.calismamaTercihi
  // Tercih artık bir vardiya TİPİ değil bir ZAMAN ARALIĞI (SRS FR-3.2).
  return t.tercih_baslangic && t.tercih_bitis
    ? m.tercihYonetimi.araligiTercihi(araligiYaz(t.tercih_baslangic, t.tercih_bitis))
    : m.tercihYonetimi.zamanAraligiTercihi
}

export function TercihlerEkrani({ ekranSec }: Props) {
  const m = useMetin()
  const [tercihler, setTercihler] = useState<Tercih[]>([])
  const [personelListesi, setPersonelListesi] = useState<Personel[]>([])
  const [sekme, setSekme] = useState<TercihDurumu>('beklemede')
  const [hata, setHata] = useState<string | null>(null)
  const [islenenId, setIslenenId] = useState<number | null>(null)
  const [retGerekceler, setRetGerekceler] = useState<Record<number, string>>({})

  const yukle = () => {
    Promise.all([api.tercihListele(), api.personelListele()])
      .then(([t, p]) => {
        setTercihler(t)
        setPersonelListesi(p)
      })
      .catch((e) => setHata(hataMetni(e, m)))
  }

  useEffect(yukle, [])

  const personelMap = useMemo(
    () => new Map(personelListesi.map((p) => [p.personel_id, p])),
    [personelListesi],
  )

  const durumGuncelle = async (tercihId: number, durum: TercihDurumu) => {
    setIslenenId(tercihId)
    setHata(null)
    try {
      await api.tercihDurumGuncelle(tercihId, durum, retGerekceler[tercihId]?.trim() || undefined)
      setRetGerekceler((r) => {
        const { [tercihId]: _silinen, ...kalan } = r
        return kalan
      })
      yukle()
    } catch (e) {
      setHata(hataMetni(e, m))
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
    <AppShell aktifEkran="Tercihler" ekranSec={ekranSec} baslik={m.menu['Tercihler']}>
      {hata && <p className="text-sm text-signal">{hata}</p>}

      <div className="flex gap-2">
        {SEKMELER.map((durum) => (
          <button
            key={durum}
            type="button"
            onClick={() => setSekme(durum)}
            className={cn(
              'flex items-center gap-2 rounded-sm border border-rule bg-surface px-4 py-2.5 text-sm text-ink-muted',
              durum === sekme && 'border-accent bg-surface font-medium text-ink',
            )}
          >
            {durum === 'beklemede'
              ? m.tercihYonetimi.bekleyen
              : durum === 'onaylandi'
                ? m.tercihYonetimi.onaylandi
                : m.tercihYonetimi.reddedildi}
            <span className="flex size-5 items-center justify-center rounded-full bg-accent-soft font-mono text-mono-kucuk text-accent">
              {sayilar[durum]}
            </span>
          </button>
        ))}
      </div>

      <Kart>
        {gosterilenler.length === 0 ? (
          <p className="text-sm text-ink-muted">{m.tercihYonetimi.buDurumdaYok}</p>
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
                    <p className="m-0 font-mono text-xs text-ink-muted">{personel?.sicil_no ?? BOS}</p>
                  </div>
                  <span className="w-20 shrink-0 font-mono text-sm font-semibold text-ink">
                    {gunKisaltmasiVeNumarasi(t.tarih).toUpperCase()}
                  </span>
                  <p className="m-0 flex-1 text-sm text-ink">{tercihAciklamasi(t, m)}</p>
                  {sekme === 'beklemede' && (
                    <div className="flex shrink-0 items-center gap-2">
                      <Input
                        placeholder={m.tercihYonetimi.retGerekcesi}
                        value={retGerekceler[t.tercih_id] ?? ''}
                        onChange={(e) =>
                          setRetGerekceler((r) => ({ ...r, [t.tercih_id]: e.target.value }))
                        }
                        className="h-8 w-48 rounded-sm border-rule text-sm"
                      />
                      <Buton
                        varyant="ikincil"
                        disabled={islenenId === t.tercih_id}
                        onClick={() => durumGuncelle(t.tercih_id, 'reddedildi')}
                      >
                        {m.tercihYonetimi.reddet}
                      </Buton>
                      <Buton
                        varyant="birincil"
                        disabled={islenenId === t.tercih_id}
                        onClick={() => durumGuncelle(t.tercih_id, 'onaylandi')}
                      >
                        {m.tercihYonetimi.onayla}
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
