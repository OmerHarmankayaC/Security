import { useEffect, useState } from 'react'
import { api } from '@/api/client'
import type {
  CalisanTercihListesi,
  CalisanVardiyaTipi,
  KarsilanmaDurumu,
  TercihTipi,
} from '@/api/types'
import { Buton, Kart, KartEtiketi, Rozet } from '@/components/app-ui'
import { Input } from '@/components/ui/input'
import { bugunIso, gunFarki, gunKisaltmasiVeNumarasi } from '@/lib/tarih'
import { buyukHarf } from '@/lib/metin'
import { cn } from '@/lib/utils'

const DURUM_ROZET: Record<string, { varyant: 'notr' | 'kilitli' | 'eksik'; etiket: string }> = {
  beklemede: { varyant: 'notr', etiket: 'Beklemede' },
  onaylandi: { varyant: 'kilitli', etiket: 'Onaylandı' },
  reddedildi: { varyant: 'eksik', etiket: 'Reddedildi' },
}

const KARSILANMA_METNI: Record<KarsilanmaDurumu, { renk: string; etiket: string }> = {
  karsilandi: { renk: 'bg-accent', etiket: 'Karşılandı' },
  karsilanmadi: { renk: 'bg-signal', etiket: 'Karşılanmadı' },
  henuz_belirsiz: { renk: 'bg-ink-muted', etiket: 'Henüz Belirsiz' },
}

function tercihAciklamasi(tip: TercihTipi, vardiyaTipiAd: string | null): string {
  if (tip === 'calismama') return 'Çalışmak istemiyorum'
  return vardiyaTipiAd ? `${vardiyaTipiAd} istiyorum` : 'Vardiya tipi istiyorum'
}

export function TercihlerimEkrani() {
  const [liste, setListe] = useState<CalisanTercihListesi | null>(null)
  const [vardiyaTipleri, setVardiyaTipleri] = useState<CalisanVardiyaTipi[]>([])
  const [hata, setHata] = useState<string | null>(null)

  const [tip, setTip] = useState<TercihTipi>('calismama')
  const [vardiyaTipiId, setVardiyaTipiId] = useState('')
  const [tarih, setTarih] = useState('')
  const [not, setNot] = useState('')
  const [gonderiliyor, setGonderiliyor] = useState(false)

  const yukle = () => {
    // `/api/vardiya-tipi` (tanımlar) çalışan rolüne kapalı (SRS 5.10);
    // liste çalışan yüzeyinin kendi ucundan gelir.
    Promise.all([api.calisanTercihlerim(), api.calisanVardiyaTipleri()])
      .then(([t, v]) => {
        setListe(t)
        setVardiyaTipleri(v)
        setTarih((mevcut) => mevcut || t.acik_donem?.baslangic_tarihi || '')
      })
      .catch((e) => setHata(e instanceof Error ? e.message : 'Tercihler yüklenemedi'))
  }

  useEffect(yukle, [])

  const gonder = async () => {
    if (!tarih) return
    setGonderiliyor(true)
    setHata(null)
    try {
      await api.calisanTercihBildir({
        tarih,
        tip,
        vardiya_tipi_id: tip === 'vardiya_tipi_tercihi' ? Number(vardiyaTipiId) || null : null,
        calisan_notu: not.trim() || null,
      })
      setNot('')
      yukle()
    } catch (e) {
      setHata(e instanceof Error ? e.message : 'Tercih gönderilemedi')
    } finally {
      setGonderiliyor(false)
    }
  }

  if (!liste) return null

  const bugun = bugunIso()
  const kalanGun = liste.acik_donem ? gunFarki(bugun, liste.acik_donem.tercih_son_tarihi) : null

  return (
    <>
      {hata && <p className="m-0 text-sm text-signal">{hata}</p>}

      {liste.acik_donem && kalanGun !== null && kalanGun >= 0 && (
        <div className="rounded-sm border-l-2 border-accent bg-accent-soft px-4 py-3">
          <p className="m-0 text-sm font-semibold text-accent">
            Tercih bildirimi {gunKisaltmasiVeNumarasi(liste.acik_donem.tercih_son_tarihi)} tarihinde
            kapanıyor
          </p>
          <p className="m-0 mt-0.5 text-sm text-ink-muted">
            Bir sonraki dönem için {kalanGun} günün var.
          </p>
        </div>
      )}

      <Kart>
        <KartEtiketi>Yeni Tercih Bildir</KartEtiketi>
        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap items-end gap-6">
            <div className="flex flex-col gap-1">
              <label className="etiket-caps text-ink-muted">
                {buyukHarf('Tercih Tipi')}
              </label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setTip('calismama')}
                  className={cn(
                    'rounded-sm border border-rule px-4 py-2 text-sm',
                    tip === 'calismama' ? 'border-accent bg-accent-soft font-medium text-accent' : 'text-ink-muted',
                  )}
                >
                  Çalışmak istemiyorum
                </button>
                <button
                  type="button"
                  onClick={() => setTip('vardiya_tipi_tercihi')}
                  className={cn(
                    'rounded-sm border border-rule px-4 py-2 text-sm',
                    tip === 'vardiya_tipi_tercihi'
                      ? 'border-accent bg-accent-soft font-medium text-accent'
                      : 'text-ink-muted',
                  )}
                >
                  Vardiya tipi
                </button>
              </div>
            </div>
            {tip === 'vardiya_tipi_tercihi' && (
              <div className="flex flex-col gap-1">
                <label className="etiket-caps text-ink-muted">
                  {buyukHarf('Vardiya Tipi')}
                </label>
                <select
                  className="h-8 w-40 rounded-sm border border-rule bg-surface px-2.5 font-mono text-sm text-ink outline-none"
                  value={vardiyaTipiId}
                  onChange={(e) => setVardiyaTipiId(e.target.value)}
                >
                  <option value="">—</option>
                  {vardiyaTipleri.map((v) => (
                    <option key={v.vardiya_tipi_id} value={v.vardiya_tipi_id}>
                      {v.ad}
                    </option>
                  ))}
                </select>
              </div>
            )}
            <div className="flex flex-col gap-1">
              <label className="etiket-caps text-ink-muted">
                {buyukHarf('Gün')}
              </label>
              <Input
                type="date"
                value={tarih}
                onChange={(e) => setTarih(e.target.value)}
                className="w-44 rounded-sm border-rule font-mono"
              />
            </div>
          </div>

          <div className="flex flex-col gap-1">
            <label className="etiket-caps text-ink-muted">
              {buyukHarf('Gerekçe (isteğe bağlı)')}
            </label>
            <textarea
              value={not}
              onChange={(e) => setNot(e.target.value)}
              rows={2}
              className="w-full rounded-sm border border-rule bg-surface px-2.5 py-2 text-sm text-ink outline-none focus-visible:border-accent focus-visible:ring-3 focus-visible:ring-accent/30"
            />
          </div>

          <div>
            <Buton
              varyant="birincil"
              disabled={gonderiliyor || !tarih || (tip === 'vardiya_tipi_tercihi' && !vardiyaTipiId)}
              onClick={gonder}
            >
              Tercihi Gönder
            </Buton>
          </div>
        </div>
      </Kart>

      <Kart>
        <KartEtiketi>Bildirdiğim Tercihler · {liste.tercihler.length}</KartEtiketi>
        {liste.tercihler.length === 0 ? (
          <p className="m-0 text-sm text-ink-muted">Henüz tercih bildirmedin.</p>
        ) : (
          <ul className="m-0 flex list-none flex-col p-0">
            {liste.tercihler.map((t) => {
              const durum = DURUM_ROZET[t.durum]
              // TD-12: karşılanma yalnızca onaylanmış tercihler için türetilir;
              // aksi hâlde null gelir ve satır hiç gösterilmez ("REDDEDİLDİ +
              // KARŞILANMADI" yan yana yazmak yanıltıcı olurdu).
              const karsilanma = t.karsilanma ? KARSILANMA_METNI[t.karsilanma] : null
              return (
                <li key={t.tercih_id} className="flex flex-col gap-1 border-t border-rule py-3 first:border-none">
                  <div className="flex items-center gap-3">
                    <span className="w-20 shrink-0 text-sm font-semibold text-ink">
                      {gunKisaltmasiVeNumarasi(t.tarih)}
                    </span>
                    <span className="flex-1 text-sm text-ink">{tercihAciklamasi(t.tip, t.vardiya_tipi_ad)}</span>
                    {durum && (
                      <Rozet varyant={durum.varyant} genislik={92}>
                        {durum.etiket}
                      </Rozet>
                    )}
                  </div>
                  {karsilanma && (
                    <div className="ml-[92px] flex items-center gap-1.5 text-xs">
                      <span className={cn('size-1.5 rounded-full', karsilanma.renk)} />
                      <span className="etiket-caps text-ink-muted">
                        {buyukHarf(karsilanma.etiket)}
                      </span>
                      {t.karsilanma === 'henuz_belirsiz' && (
                        <span className="text-ink-muted">· çizelge henüz yayınlanmadı</span>
                      )}
                    </div>
                  )}
                  {t.durum === 'reddedildi' && t.ret_gerekcesi && (
                    <p className="ml-[92px] m-0 text-xs text-ink-muted">Gerekçe: {t.ret_gerekcesi}</p>
                  )}
                </li>
              )
            })}
          </ul>
        )}
      </Kart>
    </>
  )
}
