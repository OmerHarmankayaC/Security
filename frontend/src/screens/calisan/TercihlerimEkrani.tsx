import { useEffect, useState } from 'react'
import { ApiHatasi, api } from '@/api/client'
import type { AcikDonem, CalisanTercihListesi, KarsilanmaDurumu, TercihTipi } from '@/api/types'
import { Buton, Kart, KartEtiketi, Rozet } from '@/components/app-ui'
import { Input } from '@/components/ui/input'
import {
  BASLANGIC_SAATLERI,
  BITIS_SAATLERI,
  araligiSure,
  araligiYaz,
  saatEtiketi,
  saatiYaz,
} from '@/lib/talepAraligi'
import {
  bugunIso,
  donemAraligiBicimle,
  gunFarki,
  gunKisaltmasiVeNumarasi,
} from '@/lib/tarih'
import { buyukHarf } from '@/lib/metin'
import { cn } from '@/lib/utils'
import { useDil } from '@/i18n/DilBaglami'
import { hataMetni } from '@/i18n/hata'
import type { Metinler } from '@/i18n/sozluk'

// Rozet VARYANTI burada, ETİKETİ sözlükte: varyant bir görsel karar ve
// dile bağlı değil, etiket ise çevrilir. İkisini bir arada tutmak, sözlüğe
// renk sınıfı taşımak ya da bileşene metin taşımak demekti.
const DURUM_VARYANTI: Record<string, 'notr' | 'kilitli' | 'eksik'> = {
  beklemede: 'notr',
  onaylandi: 'kilitli',
  reddedildi: 'eksik',
}

const KARSILANMA_RENGI: Record<KarsilanmaDurumu, string> = {
  karsilandi: 'bg-accent',
  karsilanmadi: 'bg-signal',
  henuz_belirsiz: 'bg-ink-muted',
}

// Bulgu 5: alan sınırının (`min`) VE varsayılan değerin AYNI alt sınırdan
// beslenmesi zorunlu — tek fonksiyon, TEK YERDE. İki ayrı yerde elle
// hesaplanırsa (biri `min` için, biri varsayılan için) biri güncellenip
// diğeri unutulduğunda varsayılan `min`in altına düşebilir; tam bu turun
// bulgusu buydu.
function enErkenTarih(acikDonem: AcikDonem | null, bugun: string): string {
  if (!acikDonem) return ''
  return acikDonem.baslangic_tarihi > bugun ? acikDonem.baslangic_tarihi : bugun
}

function tercihAciklamasi(
  tip: TercihTipi,
  baslangic: string | null,
  bitis: string | null,
  m: Metinler,
): string {
  if (tip === 'calismama') return m.calisan.calismakIstemiyorum
  // Tercih artık bir vardiya TİPİ değil bir ZAMAN ARALIĞI (SRS FR-3.2).
  return baslangic && bitis
    ? m.calisan.araliktaCalismak(araligiYaz(baslangic, bitis))
    : m.calisan.belirliSaatlerde
}

export function TercihlerimEkrani() {
  const { dil, metin: m } = useDil()
  const [liste, setListe] = useState<CalisanTercihListesi | null>(null)
  const [hata, setHata] = useState<string | null>(null)
  const [bilgi, setBilgi] = useState<string | null>(null)

  const [tip, setTip] = useState<TercihTipi>('calismama')
  const [baslangicSaati, setBaslangicSaati] = useState(8)
  const [bitisSaati, setBitisSaati] = useState(16)
  const [tarih, setTarih] = useState('')
  const [not, setNot] = useState('')
  const [gonderiliyor, setGonderiliyor] = useState(false)

  const yukle = () => {
    // Vardiya tipi listesi KALKTI: seçilecek bir blok yok, çalışan
    // doğrudan saat aralığını bildiriyor (SRS FR-3.2, TD-13).
    api
      .calisanTercihlerim()
      .then((t) => {
        setListe(t)
        // Bulgu 5: varsayılan `min` ile AYNI alt sınırdan (`enErkenTarih`)
        // gelir — dönem başlangıcından tek başına türetilirse, dönem zaten
        // başlamışken (bugün > başlangıç) varsayılan `min`in ALTINA düşer ve
        // alanı hiç değiştirmeden gönderen çalışan geçmiş bir güne tercih
        // bildirir.
        setTarih((mevcut) => mevcut || enErkenTarih(t.acik_donem, bugunIso()))
      })
      .catch((e) => setHata(hataMetni(e, m)))
  }

  useEffect(yukle, [])

  const gonder = async () => {
    if (!tarih) return
    setGonderiliyor(true)
    setHata(null)
    setBilgi(null)
    try {
      await api.calisanTercihBildir({
        tarih,
        tip,
        tercih_baslangic: tip === 'zaman_araligi_tercihi' ? saatiYaz(baslangicSaati) : null,
        tercih_bitis: tip === 'zaman_araligi_tercihi' ? saatiYaz(bitisSaati) : null,
        calisan_notu: not.trim() || null,
      })
      setNot('')
      setBilgi(m.calisan.tercihAlindi)
      yukle()
    } catch (e) {
      setBilgi(null)
      setHata(
        e instanceof ApiHatasi && e.status === 409
          ? m.calisan.tercihKararlanmis
          : e instanceof Error
            ? e.message
            : m.calisan.tercihGonderilemedi,
      )
    } finally {
      setGonderiliyor(false)
    }
  }

  if (!liste) return null

  const bugun = bugunIso()
  const acik = liste.acik_donem
  const kalanGun = acik ? gunFarki(bugun, acik.tercih_son_tarihi) : null
  // Alt sınır: dönem başlangıcı ile bugünün BÜYÜĞÜ — geçmiş bir güne tercih
  // bildirmenin anlamı yok, dönem gelecekteyse de başlangıçtan önce gün yok.
  // Varsayılan değer de (yukarıdaki `yukle`) AYNI fonksiyonu kullanır.
  const enErken = enErkenTarih(acik, bugun)
  const aralikSuresi = araligiSure(baslangicSaati, bitisSaati)

  const bildirdiklerimKarti = (
    <Kart>
      <KartEtiketi>{m.calisan.bildirdigimTercihler(liste.tercihler.length)}</KartEtiketi>
      {liste.tercihler.length === 0 ? (
        <p className="m-0 text-sm text-ink-muted">{m.calisan.tercihYok}</p>
      ) : (
        <ul className="m-0 flex list-none flex-col p-0">
          {liste.tercihler.map((t) => {
            const varyant = DURUM_VARYANTI[t.durum]
            const durumEtiketi =
              m.calisan.tercihDurumu[t.durum as keyof typeof m.calisan.tercihDurumu]
            // TD-12: karşılanma yalnızca onaylanmış tercihler için türetilir;
            // aksi hâlde null gelir ve satır hiç gösterilmez ("REDDEDİLDİ +
            // KARŞILANMADI" yan yana yazmak yanıltıcı olurdu).
            const karsilanmaRengi = t.karsilanma ? KARSILANMA_RENGI[t.karsilanma] : null
            const karsilanmaEtiketi = t.karsilanma
              ? m.calisan.tercihDurumu[t.karsilanma]
              : null
            return (
              <li key={t.tercih_id} className="flex flex-col gap-1 border-t border-rule py-3 first:border-none">
                <div className="flex items-center gap-3">
                  <span className="w-20 shrink-0 text-sm font-semibold text-ink">
                    {gunKisaltmasiVeNumarasi(t.tarih)}
                  </span>
                  <span className="flex-1 text-sm text-ink">{tercihAciklamasi(t.tip, t.tercih_baslangic, t.tercih_bitis, m)}</span>
                  {varyant && (
                    <Rozet varyant={varyant} genislik={104}>
                      {durumEtiketi}
                    </Rozet>
                  )}
                </div>
                {karsilanmaRengi && karsilanmaEtiketi && (
                  <div className="ml-[92px] flex items-center gap-1.5 text-xs">
                    <span className={cn('size-1.5 rounded-full', karsilanmaRengi)} />
                    <span className="etiket-caps text-ink-muted">
                      {buyukHarf(karsilanmaEtiketi, dil)}
                    </span>
                    {t.karsilanma === 'henuz_belirsiz' && (
                      <span className="text-ink-muted">{m.calisan.cizelgeYayinlanmadi}</span>
                    )}
                  </div>
                )}
                {t.durum === 'reddedildi' && t.ret_gerekcesi && (
                  <p className="ml-[92px] m-0 text-xs text-ink-muted">{m.calisan.gerekce(t.ret_gerekcesi)}</p>
                )}
              </li>
            )
          })}
        </ul>
      )}
    </Kart>
  )

  if (!acik) {
    return (
      <>
        <Kart>
          <p className="m-0 text-sm text-ink-muted">
            {m.calisan.acikDonemYok}
          </p>
        </Kart>
        {bildirdiklerimKarti}
      </>
    )
  }

  return (
    <>
      {hata && <p className="m-0 text-sm text-signal">{hata}</p>}
      {bilgi && <p className="m-0 text-sm text-accent">{bilgi}</p>}

      {kalanGun !== null && kalanGun >= 0 && (
        <div className="rounded-sm border-l-2 border-accent bg-accent-soft px-4 py-3">
          <p className="m-0 text-sm font-semibold text-accent">
            {m.calisan.tercihKapaniyor(gunKisaltmasiVeNumarasi(acik.tercih_son_tarihi))}
          </p>
          {/* DÖNEM ADIYLA SÖYLENİR. "Bir sonraki dönem" sabit bir ifadeydi
              ve yanlıştı: tercihe açık dönem, içinde bulunulan dönem de
              olabiliyor (son tarihi kendi bitiş gününe düşen bir dönemde
              öyle). Konuma dayalı bir ifade yerine aralığın kendisi
              yazılınca belirsizlik kalmıyor. */}
          <p className="m-0 mt-0.5 text-sm text-ink-muted">
            {m.calisan.kalanGun(
              donemAraligiBicimle(acik.baslangic_tarihi, acik.bitis_tarihi),
              kalanGun,
            )}
          </p>
        </div>
      )}

      <Kart>
        <KartEtiketi>{m.calisan.yeniTercihBildir}</KartEtiketi>
        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap items-end gap-6">
            <div className="flex flex-col gap-1">
              <label className="etiket-caps text-ink-muted">
                {buyukHarf(m.calisan.tercihTipi, dil)}
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
                  {m.calisan.calismakIstemiyorum}
                </button>
                <button
                  type="button"
                  onClick={() => setTip('zaman_araligi_tercihi')}
                  className={cn(
                    'rounded-sm border border-rule px-4 py-2 text-sm',
                    tip === 'zaman_araligi_tercihi'
                      ? 'border-accent bg-accent-soft font-medium text-accent'
                      : 'text-ink-muted',
                  )}
                >
                  {m.calisan.suSaatlerdeCalismak}
                </button>
              </div>
            </div>
            {tip === 'zaman_araligi_tercihi' && (
              <>
                <div className="flex flex-col gap-1">
                  <label htmlFor="tercih-baslangic" className="etiket-caps text-ink-muted">
                    {buyukHarf(m.calisan.baslangic, dil)}
                  </label>
                  <select
                    id="tercih-baslangic"
                    className="h-8 w-28 rounded-sm border border-rule bg-surface px-2.5 font-mono text-sm text-ink outline-none"
                    value={baslangicSaati}
                    onChange={(e) => setBaslangicSaati(Number(e.target.value))}
                  >
                    {BASLANGIC_SAATLERI.map((s) => (
                      <option key={s} value={s}>
                        {saatEtiketi(s)}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="flex flex-col gap-1">
                  <label htmlFor="tercih-bitis" className="etiket-caps text-ink-muted">
                    {buyukHarf(m.calisan.bitis, dil)}
                  </label>
                  <select
                    id="tercih-bitis"
                    className="h-8 w-28 rounded-sm border border-rule bg-surface px-2.5 font-mono text-sm text-ink outline-none"
                    value={bitisSaati}
                    onChange={(e) => setBitisSaati(Number(e.target.value))}
                  >
                    {BITIS_SAATLERI.map((s) => (
                      <option key={s} value={s}>
                        {saatEtiketi(s)}
                      </option>
                    ))}
                  </select>
                </div>
                {/* Başlangıç = bitiş TÜM GÜN demektir (zaman_araligi.py:
                    aralik_sure_saat); bunu yazmazsak 08→08 seçen kullanıcı 24
                    saat bildirdiğini bilmez. */}
                <span className="text-sm text-ink-muted">
                  {aralikSuresi === 24 ? m.calisan.tumGun : m.calisan.saatSuresi(aralikSuresi)}
                </span>
              </>
            )}
            <div className="flex flex-col gap-1">
              <label htmlFor="tercih-gun" className="etiket-caps text-ink-muted">
                {buyukHarf(m.calisan.gun, dil)}
              </label>
              <Input
                type="date"
                id="tercih-gun"
                min={enErken}
                max={acik.bitis_tarihi}
                value={tarih}
                onChange={(e) => setTarih(e.target.value)}
                className="w-44 rounded-sm border-rule font-mono"
              />
            </div>
          </div>

          <div className="flex flex-col gap-1">
            <label htmlFor="tercih-not" className="etiket-caps text-ink-muted">
              {buyukHarf(m.calisan.gerekceIsteğeBagli, dil)}
            </label>
            <textarea
              id="tercih-not"
              value={not}
              onChange={(e) => setNot(e.target.value)}
              rows={2}
              className="w-full rounded-sm border border-rule bg-surface px-2.5 py-2 text-sm text-ink outline-none focus-visible:border-accent focus-visible:ring-3 focus-visible:ring-accent/30"
            />
          </div>

          <div>
            <Buton
              varyant="birincil"
              disabled={gonderiliyor || !tarih}
              onClick={gonder}
            >
              {m.calisan.tercihiGonder}
            </Buton>
          </div>
        </div>
      </Kart>

      {bildirdiklerimKarti}
    </>
  )
}
