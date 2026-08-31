import { useEffect, useMemo, useRef, useState } from 'react'
import { ApiHatasi, api } from '../api/client'
import type { Musaitlik, MusaitlikDilimi, MusaitlikTipi, Personel } from '../api/types'
import { AppShell, type NavOgesi } from '../components/AppShell'
import { Buton, Kart, KartEtiketi, Rozet } from '../components/app-ui'
import { Input } from '@/components/ui/input'
import { gunKisaltmasiVeNumarasi } from '../lib/tarih'
import { useMetin } from '@/i18n/DilBaglami'
import { hataMetni } from '@/i18n/hata'

interface Props {
  ekranSec: (ekran: NavOgesi) => void
}

const INPUT_SINIFI =
  'h-8 w-full rounded-sm border border-rule bg-surface px-2.5 font-mono text-sm text-ink outline-none focus-visible:border-accent focus-visible:ring-3 focus-visible:ring-accent/30'

export function MusaitlikEkrani({ ekranSec }: Props) {
  const m = useMetin()
  const [kayitlar, setKayitlar] = useState<Musaitlik[]>([])
  const [personelListesi, setPersonelListesi] = useState<Personel[]>([])
  const [formAcik, setFormAcik] = useState(false)
  const [hata, setHata] = useState<string | null>(null)

  const [personelId, setPersonelId] = useState('')
  const [baslangic, setBaslangic] = useState('')
  const [bitis, setBitis] = useState('')
  const [dilim, setDilim] = useState<MusaitlikDilimi>('tam_gun')
  const [tip, setTip] = useState<MusaitlikTipi>('yillik_izin')
  const [gonderiliyor, setGonderiliyor] = useState(false)

  const yukle = () => {
    Promise.all([api.musaitlikListele(), api.personelListele()])
      .then(([m, p]) => {
        setKayitlar(m)
        setPersonelListesi(p)
      })
      .catch((e) => setHata(hataMetni(e, m)))
  }

  useEffect(yukle, [])

  const personelMap = useMemo(
    () => new Map(personelListesi.map((p) => [p.personel_id, p])),
    [personelListesi],
  )

  const kaydet = async () => {
    if (!personelId || !baslangic || !bitis) return
    setGonderiliyor(true)
    setHata(null)
    try {
      await api.musaitlikOlustur({
        personel_id: Number(personelId),
        baslangic_tarihi: baslangic,
        bitis_tarihi: bitis,
        dilim,
        tip,
      })
      setFormAcik(false)
      setPersonelId('')
      setBaslangic('')
      setBitis('')
      yukle()
    } catch (e) {
      setHata(hataMetni(e, m))
    } finally {
      setGonderiliyor(false)
    }
  }

  const sil = async (id: number) => {
    try {
      await api.musaitlikSil(id)
      yukle()
    } catch (e) {
      setHata(hataMetni(e, m))
    }
  }

  // Aynı hafta içinde çakışan izin/rapor kayıtları (bkz. TASARIM_REFERANSI.md
  // Müsaitlik ekranı — kapsama riski uyarısı); gerçek risk hesabı (nokta/
  // yetkinlik havuzu bazında) Analiz'e (Gün 12) bırakıldı, burada yalnızca
  // aynı haftaya denk gelen birden fazla kayıt uyarılır.
  const cakismaUyarisi = useMemo(() => {
    const izinler = kayitlar.filter((k) => k.tip === 'yillik_izin')
    for (let i = 0; i < izinler.length; i++) {
      for (let j = i + 1; j < izinler.length; j++) {
        const a = izinler[i]
        const b = izinler[j]
        if (!a || !b) continue
        if (a.baslangic_tarihi <= b.bitis_tarihi && b.baslangic_tarihi <= a.bitis_tarihi) {
          const adA = personelMap.get(a.personel_id)?.ad_soyad ?? `#${a.personel_id}`
          const adB = personelMap.get(b.personel_id)?.ad_soyad ?? `#${b.personel_id}`
          return m.musaitlik.kadroRiski(adA, adB)
        }
      }
    }
    return null
  }, [kayitlar, personelMap])

  return (
    <AppShell
      aktifEkran="Müsaitlik"
      ekranSec={ekranSec}
      baslik={m.menu['Müsaitlik']}
      aksiyonlar={
        <Buton varyant="birincil" onClick={() => setFormAcik((a) => !a)}>
          {m.musaitlik.kayitEkle}
        </Buton>
      }
    >
      {hata && <p className="text-sm text-signal">{hata}</p>}
      {cakismaUyarisi && (
        <div className="border-l-2 border-signal bg-signal-soft px-4 py-3 text-sm text-signal">
          {cakismaUyarisi}
        </div>
      )}

      {formAcik && (
        <Kart vurgulu>
          <KartEtiketi renk="accent">{m.musaitlik.yeniKayit}</KartEtiketi>
          <div className="flex flex-wrap items-end gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-sm text-ink-muted">{m.musaitlik.personelEtiketi}</label>
              <select
                className={INPUT_SINIFI}
                value={personelId}
                onChange={(e) => setPersonelId(e.target.value)}
              >
                <option value="">—</option>
                {personelListesi.map((p) => (
                  <option key={p.personel_id} value={p.personel_id}>
                    {p.ad_soyad}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-ink-muted">{m.musaitlik.baslangic}</label>
              <Input
                type="date"
                value={baslangic}
                onChange={(e) => setBaslangic(e.target.value)}
                className="w-40 rounded-sm border-rule font-mono"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-ink-muted">{m.musaitlik.bitis}</label>
              <Input
                type="date"
                value={bitis}
                onChange={(e) => setBitis(e.target.value)}
                className="w-40 rounded-sm border-rule font-mono"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-ink-muted">{m.musaitlik.dilimEtiketi}</label>
              <select
                className={INPUT_SINIFI}
                value={dilim}
                onChange={(e) => setDilim(e.target.value as MusaitlikDilimi)}
              >
                {Object.entries(m.musaitlik.dilim).map(([deger, etiket]) => (
                  <option key={deger} value={deger}>
                    {etiket}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-ink-muted">{m.musaitlik.tipEtiketi}</label>
              <select
                className={INPUT_SINIFI}
                value={tip}
                onChange={(e) => setTip(e.target.value as MusaitlikTipi)}
              >
                {Object.entries(m.musaitlik.tip).map(([deger, etiket]) => (
                  <option key={deger} value={deger}>
                    {etiket}
                  </option>
                ))}
              </select>
            </div>
            <Buton
              varyant="birincil"
              onClick={kaydet}
              disabled={gonderiliyor || !personelId || !baslangic || !bitis}
            >
              Kaydet
            </Buton>
            <Buton varyant="hayalet" onClick={() => setFormAcik(false)}>
              {m.musaitlik.iptal}
            </Buton>
          </div>
        </Kart>
      )}

      <Kart>
        <table className="w-full min-w-[640px] border-collapse">
          <thead>
            <tr className="bg-sunken">
              {m.musaitlik.sutunlar.map((b) => (
                <th
                  key={b}
                  className="mono-caps whitespace-nowrap px-3 py-2 text-left text-ink-muted"
                >
                  {b}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {kayitlar.map((k) => (
              <tr key={k.musaitlik_id} className="border-t border-rule">
                <td className="px-3 py-3 text-sm font-medium text-ink">
                  {personelMap.get(k.personel_id)?.ad_soyad ?? `#${k.personel_id}`}
                </td>
                <td className="px-3 py-3 font-mono text-sm text-ink-muted">
                  {gunKisaltmasiVeNumarasi(k.baslangic_tarihi)}
                </td>
                <td className="px-3 py-3 font-mono text-sm text-ink-muted">
                  {gunKisaltmasiVeNumarasi(k.bitis_tarihi)}
                </td>
                <td className="px-3 py-3 font-mono text-sm text-ink-muted">{m.musaitlik.dilim[k.dilim]}</td>
                <td className="px-3 py-3">
                  <Rozet varyant="notr" genislik={84}>
                    {m.musaitlik.tip[k.tip]}
                  </Rozet>
                </td>
                <td className="px-3 py-3">
                  <BelgeDugmesi kayit={k} yenile={yukle} />
                </td>
                <td className="px-3 py-3 text-right">
                  <Buton varyant="hayalet" onClick={() => sil(k.musaitlik_id)}>
                    {m.musaitlik.sil}
                  </Buton>
                </td>
              </tr>
            ))}
            {kayitlar.length === 0 && (
              <tr>
                <td colSpan={7} className="px-3 py-6 text-center text-sm text-ink-muted">
                  {m.musaitlik.kayitYok}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </Kart>
    </AppShell>
  )
}


/**
 * Bir izin kaydının belgesi: varsa indirir, yoksa yükletir.
 *
 * İNDİRME BAĞLANTI DEĞİL İSTEK. Belge uç noktası oturum çerezi ister ve
 * `<a href>` ile açılan sekme onu taşısa bile yanıtı `attachment` olarak
 * inen bir dosyaya çeviremiyoruz; içeriği alıp bir nesne URL'sine
 * dönüştürmek, hata durumunu da (401, 404) görünür kılar.
 */
function BelgeDugmesi({ kayit, yenile }: { kayit: Musaitlik; yenile: () => void }) {
  const m = useMetin()
  const dosyaGirdisi = useRef<HTMLInputElement>(null)
  const [calisiyor, setCalisiyor] = useState(false)
  const [hata, setHata] = useState<string | null>(null)

  const indir = async () => {
    setHata(null)
    try {
      const yanit = await fetch(api.izinBelgesiYolu(kayit.musaitlik_id))
      if (!yanit.ok) throw new Error(m.musaitlik.belgeAlinamadi)
      const veri = await yanit.blob()
      const url = URL.createObjectURL(veri)
      const bag = document.createElement('a')
      bag.href = url
      bag.download = 'izin-belgesi'
      bag.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      setHata(hataMetni(e, m))
    }
  }

  const yukle = async (dosya: File) => {
    setCalisiyor(true)
    setHata(null)
    try {
      await api.izinBelgesiYukle(kayit.musaitlik_id, dosya)
      yenile()
    } catch (e) {
      setHata(
        e instanceof ApiHatasi && e.status === 415
          ? m.musaitlik.belgeTipi
          : e instanceof ApiHatasi && e.status === 413
            ? m.musaitlik.belgeBuyuk
            : m.musaitlik.belgeYuklenemedi,
      )
    } finally {
      setCalisiyor(false)
    }
  }

  return (
    <span className="flex flex-col gap-1">
      <span className="flex items-center gap-2">
        {kayit.belge_var ? (
          <Buton varyant="hayalet" onClick={indir}>
            {m.musaitlik.indir}
          </Buton>
        ) : (
          <Buton
            varyant="hayalet"
            disabled={calisiyor}
            onClick={() => dosyaGirdisi.current?.click()}
          >
            {calisiyor ? m.musaitlik.yukleniyor : m.musaitlik.ekle}
          </Buton>
        )}
        <input
          ref={dosyaGirdisi}
          type="file"
          accept="image/png,image/jpeg,application/pdf"
          className="hidden"
          onChange={(e) => {
            const dosya = e.target.files?.[0]
            // Aynı dosya art arda seçilebilsin diye girdi sıfırlanır.
            e.target.value = ''
            if (dosya) void yukle(dosya)
          }}
        />
      </span>
      {hata && <span className="text-xs text-signal">{hata}</span>}
    </span>
  )
}
