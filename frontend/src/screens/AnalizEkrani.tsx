import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import type { Analiz, Atama, CizelgeSurumu, Donem, Personel, VardiyaTipi } from '../api/types'
import { AppShell, type NavOgesi } from '../components/AppShell'
import { Buton, Kart, KartEtiketi, Sayi } from '../components/app-ui'
import { gunlerListesi } from '../lib/tarih'

interface Props {
  ekranSec: (ekran: NavOgesi) => void
  donemId: number | null
  donemIdSec: (id: number | null) => void
}

const SECIM_SINIFI =
  'h-8 rounded-sm border border-rule bg-surface px-2.5 font-mono text-sm text-ink outline-none focus-visible:border-accent focus-visible:ring-3 focus-visible:ring-accent/30 disabled:opacity-50'

const SURUM_DURUM_METNI: Record<string, string> = {
  taslak: 'Taslak',
  cozuldu: 'Çözüldü',
  yayinlandi: 'Yayınlandı',
  arsiv: 'Arşiv',
}

function yuzdeBicimle(oran: number | null): string {
  return oran === null ? '—' : `%${Math.round(oran * 100)}`
}

function sapmaBicimle(sapma: number): string {
  const isaret = sapma > 0 ? '+' : ''
  return `${isaret}${sapma.toFixed(1)} sa`
}

// SRS 7.2: çizelge dışa aktarma CSV biçimi, sicil/ad/tarih/vardiya_tipi/
// gece_mi/hafta_sonu_mu/sure_saat sütunlarıyla, UTF-8, ISO 8601 tarih.
function csvOlustur(
  atamalar: Atama[],
  personelMap: Map<number, Personel>,
  vardiyaMap: Map<number, VardiyaTipi>,
  haftaSonuMu: (tarih: string) => boolean,
): string {
  const basliklar = ['sicil', 'ad', 'tarih', 'vardiya_tipi', 'gece_mi', 'hafta_sonu_mu', 'sure_saat']
  const satirlar = atamalar
    .slice()
    .sort((a, b) => a.tarih.localeCompare(b.tarih) || a.personel_id - b.personel_id)
    .map((a) => {
      const personel = personelMap.get(a.personel_id)
      const vardiya = vardiyaMap.get(a.vardiya_tipi_id)
      return [
        personel?.sicil_no ?? '',
        personel?.ad_soyad ?? '',
        a.tarih,
        vardiya?.ad ?? '',
        vardiya?.gece_mi ? 'evet' : 'hayir',
        haftaSonuMu(a.tarih) ? 'evet' : 'hayir',
        vardiya?.sure_saat ?? '',
      ]
        .map((deger) => `"${String(deger).replaceAll('"', '""')}"`)
        .join(',')
    })
  return [basliklar.join(','), ...satirlar].join('\n')
}

export function AnalizEkrani({ ekranSec, donemId, donemIdSec }: Props) {
  const [donemler, setDonemler] = useState<Donem[]>([])
  const [surumler, setSurumler] = useState<CizelgeSurumu[]>([])
  const [surumId, setSurumId] = useState<number | null>(null)
  const [personelListesi, setPersonelListesi] = useState<Personel[]>([])
  const [vardiyaTipleri, setVardiyaTipleri] = useState<VardiyaTipi[]>([])
  const [analiz, setAnaliz] = useState<Analiz | null>(null)
  const [yukleniyor, setYukleniyor] = useState(false)
  const [hata, setHata] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([api.donemler(), api.personelListele(), api.vardiyaTipiListele()])
      .then(([d, p, v]) => {
        setDonemler(d)
        setPersonelListesi(p)
        setVardiyaTipleri(v)
        if (donemId === null && d[0]) donemIdSec(d[0].donem_id)
      })
      .catch((e) => setHata(e instanceof Error ? e.message : 'Tanımlar yüklenemedi'))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (donemId === null) {
      setSurumler([])
      setSurumId(null)
      return
    }
    api
      .surumler(donemId)
      .then((s) => {
        setSurumler(s)
        setSurumId(s[0] ? s[0].surum_id : null)
      })
      .catch((e) => setHata(e instanceof Error ? e.message : 'Sürümler yüklenemedi'))
  }, [donemId])

  useEffect(() => {
    if (surumId === null) {
      setAnaliz(null)
      return
    }
    setYukleniyor(true)
    setHata(null)
    api
      .analizGetir(surumId)
      .then(setAnaliz)
      .catch((e) => setHata(e instanceof Error ? e.message : 'Analiz yüklenemedi'))
      .finally(() => setYukleniyor(false))
  }, [surumId])

  const donem = donemler.find((d) => d.donem_id === donemId) ?? null
  const surum = surumler.find((s) => s.surum_id === surumId) ?? null

  const personelMap = useMemo(
    () => new Map(personelListesi.map((p) => [p.personel_id, p])),
    [personelListesi],
  )
  const vardiyaMap = useMemo(
    () => new Map(vardiyaTipleri.map((v) => [v.vardiya_tipi_id, v])),
    [vardiyaTipleri],
  )

  const adalet = useMemo(() => {
    if (!analiz) return []
    const hsMap = new Map(analiz.kisi_basina_hafta_sonu.map((k) => [k.personel_id, k.sayi]))
    return analiz.kisi_basina_gece
      .map((g) => ({
        personel_id: g.personel_id,
        ad_soyad: g.ad_soyad,
        gece: g.sayi,
        hafta_sonu: hsMap.get(g.personel_id) ?? 0,
      }))
      .filter((k) => k.gece > 0 || k.hafta_sonu > 0)
      .sort((a, b) => b.gece + b.hafta_sonu - (a.gece + a.hafta_sonu))
  }, [analiz])

  const azamiAdalet = adalet.reduce((m, k) => Math.max(m, k.gece + k.hafta_sonu), 0)
  const ortalamaGece = adalet.length
    ? adalet.reduce((t, k) => t + k.gece, 0) / adalet.length
    : 0
  const ortalamaHaftaSonu = adalet.length
    ? adalet.reduce((t, k) => t + k.hafta_sonu, 0) / adalet.length
    : 0

  const saatSapmasiOlanlar = (analiz?.saat_dagilimi ?? []).filter(
    (s) => Math.abs(s.sapma) > 1e-9,
  )

  const cezaGirdileri = analiz?.ceza_dokumu
    ? Object.entries(analiz.ceza_dokumu).sort(([a], [b]) => a.localeCompare(b))
    : []
  const azamiCeza = cezaGirdileri.reduce((m, [, deger]) => Math.max(m, deger), 0)

  const disaAktar = async () => {
    if (surumId === null || !donem) return
    try {
      const atamalar = await api.surumAtamalari(surumId)
      const gunler = new Set(gunlerListesi(donem.baslangic_tarihi, donem.bitis_tarihi))
      const haftaSonuMu = (tarih: string) => {
        if (!gunler.has(tarih)) return false
        const gun = new Date(`${tarih}T00:00:00`).getDay()
        return gun === 0 || gun === 6
      }
      const csv = csvOlustur(atamalar, personelMap, vardiyaMap, haftaSonuMu)
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
      const url = URL.createObjectURL(blob)
      const baglanti = document.createElement('a')
      baglanti.href = url
      baglanti.download = `cizelge-surum-${surum?.surum_no ?? surumId}.csv`
      baglanti.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      setHata(e instanceof Error ? e.message : 'Dışa aktarma başarısız')
    }
  }

  return (
    <AppShell
      aktifEkran="Analiz"
      ekranSec={ekranSec}
      baslik="Analiz"
      aksiyonlar={
        <Buton varyant="ikincil" onClick={disaAktar} disabled={surumId === null}>
          Dışa Aktar (CSV)
        </Buton>
      }
    >
      <Kart>
        <KartEtiketi>seçim</KartEtiketi>
        <div className="flex flex-wrap items-end gap-6">
          <div className="flex flex-col gap-1">
            <label htmlFor="donem-sec" className="text-sm text-ink-muted">
              Dönem
            </label>
            <select
              id="donem-sec"
              className={SECIM_SINIFI}
              value={donemId ?? ''}
              onChange={(e) => donemIdSec(e.target.value ? Number(e.target.value) : null)}
            >
              {donemler.map((d) => (
                <option key={d.donem_id} value={d.donem_id}>
                  {d.baslangic_tarihi} — {d.bitis_tarihi}
                </option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor="surum-sec" className="text-sm text-ink-muted">
              Sürüm
            </label>
            <select
              id="surum-sec"
              className={SECIM_SINIFI}
              value={surumId ?? ''}
              onChange={(e) => setSurumId(e.target.value ? Number(e.target.value) : null)}
            >
              {surumler.map((s) => (
                <option key={s.surum_id} value={s.surum_id}>
                  Sürüm {s.surum_no} ({SURUM_DURUM_METNI[s.durum] ?? s.durum})
                </option>
              ))}
            </select>
          </div>
        </div>
      </Kart>

      {hata && <p className="text-sm text-signal">{hata}</p>}
      {yukleniyor && <p className="text-sm text-ink-muted">Yükleniyor…</p>}

      {analiz && (
        <>
          <div className="grid grid-cols-4 gap-4">
            <Kart>
              <KartEtiketi>dönem kapsaması</KartEtiketi>
              <p className="m-0 font-mono text-2xl font-semibold text-accent">
                {yuzdeBicimle(analiz.kapsama_orani)}
              </p>
            </Kart>
            <Kart>
              <KartEtiketi>tercih karşılama</KartEtiketi>
              <p className="m-0 font-mono text-2xl font-semibold text-ink">
                {yuzdeBicimle(analiz.tercih_karsilama_orani)}
              </p>
            </Kart>
            <Kart>
              <KartEtiketi>en dengesiz</KartEtiketi>
              <p className="m-0 text-2xl font-semibold text-signal">
                {analiz.en_dengesiz_ad_soyad ?? '—'}
              </p>
            </Kart>
            <Kart>
              <KartEtiketi>toplam ceza</KartEtiketi>
              <Sayi className="text-2xl font-semibold text-ink">
                {analiz.toplam_ceza !== null ? analiz.toplam_ceza.toFixed(0) : '—'}
              </Sayi>
            </Kart>
          </div>

          <Kart>
            <KartEtiketi>gece ve hafta sonu dağılımı · kişi başına</KartEtiketi>
            {adalet.length === 0 ? (
              <p className="text-sm text-ink-muted">Bu sürümde gece veya hafta sonu ataması yok.</p>
            ) : (
              <ul className="m-0 flex list-none flex-col gap-2 p-0">
                {adalet.map((k) => (
                  <li key={k.personel_id} className="flex items-center gap-3 text-sm">
                    <span className="w-28 shrink-0 text-ink">{k.ad_soyad}</span>
                    <span className="flex h-2.5 flex-1 overflow-hidden rounded-sm bg-sunken">
                      <span
                        className="block h-full bg-vardiya-gece"
                        style={{ width: azamiAdalet > 0 ? `${(k.gece / azamiAdalet) * 100}%` : '0%' }}
                      />
                      <span
                        className="block h-full bg-accent"
                        style={{
                          width: azamiAdalet > 0 ? `${(k.hafta_sonu / azamiAdalet) * 100}%` : '0%',
                        }}
                      />
                    </span>
                    <Sayi className="w-16 shrink-0 text-right text-ink-muted">
                      {k.gece}g {k.hafta_sonu}h
                    </Sayi>
                  </li>
                ))}
              </ul>
            )}
            <div className="mt-4 flex items-center gap-4 text-xs text-ink-muted">
              <span className="flex items-center gap-1.5">
                <span className="size-2.5 rounded-sm bg-vardiya-gece" /> Gece
              </span>
              <span className="flex items-center gap-1.5">
                <span className="size-2.5 rounded-sm bg-accent" /> Hafta sonu
              </span>
              <span>
                ortalama: <Sayi>{ortalamaGece.toFixed(1)}</Sayi> gece /{' '}
                <Sayi>{ortalamaHaftaSonu.toFixed(1)}</Sayi> hafta sonu
              </span>
            </div>
          </Kart>

          <Kart>
            <KartEtiketi>saat dengesi · personel başına</KartEtiketi>
            {saatSapmasiOlanlar.length === 0 ? (
              <p className="text-sm text-ink-muted">Herkes kişisel hedef saatini tutturdu.</p>
            ) : (
              <table className="w-full min-w-[560px] border-collapse">
                <thead>
                  <tr className="bg-sunken">
                    {['PERSONEL', 'TOPLAM SAAT', 'HEDEF', 'SAPMA'].map((b) => (
                      <th
                        key={b}
                        className="whitespace-nowrap px-3 py-2 text-left font-condensed text-[10px] tracking-[0.1em] text-ink-muted"
                      >
                        {b}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {saatSapmasiOlanlar
                    .sort((a, b) => Math.abs(b.sapma) - Math.abs(a.sapma))
                    .map((s) => (
                      <tr key={s.personel_id} className="border-t border-rule">
                        <td className="px-3 py-3 text-sm font-medium text-ink">{s.ad_soyad}</td>
                        <td className="px-3 py-3 font-mono text-sm text-ink-muted">
                          {s.toplam_saat.toFixed(0)} sa
                        </td>
                        <td className="px-3 py-3 font-mono text-sm text-ink-muted">
                          {s.hedef_saat.toFixed(0)} sa
                        </td>
                        <td
                          className={`px-3 py-3 font-mono text-sm font-semibold ${
                            Math.abs(s.sapma) > s.hedef_saat * 0.1 ? 'text-signal' : 'text-ink'
                          }`}
                        >
                          {sapmaBicimle(s.sapma)}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            )}
          </Kart>

          {cezaGirdileri.length > 0 && (
            <Kart>
              <KartEtiketi>ceza dökümü</KartEtiketi>
              <ul className="m-0 flex list-none flex-col gap-2 p-0">
                {cezaGirdileri.map(([kimlik, deger]) => (
                  <li key={kimlik} className="flex items-center gap-3 py-1 text-sm">
                    <span className="w-28 shrink-0 text-ink-muted">{kimlik}</span>
                    <span className="h-2 flex-1 overflow-hidden rounded-sm bg-sunken">
                      <span
                        className={kimlik === 'S1' ? 'block h-full bg-signal' : 'block h-full bg-accent'}
                        style={{
                          width: azamiCeza > 0 ? `${Math.max(2, (deger / azamiCeza) * 100)}%` : '0%',
                        }}
                      />
                    </span>
                    <Sayi className="w-16 shrink-0 text-right text-ink">{deger}</Sayi>
                  </li>
                ))}
              </ul>
            </Kart>
          )}

          {analiz.bina_degisim_sayisi.length > 0 && (
            <Kart>
              <KartEtiketi renk="warn">bina değişim sayısı</KartEtiketi>
              <ul className="m-0 flex list-none flex-col p-0">
                {analiz.bina_degisim_sayisi.map((b) => (
                  <li
                    key={b.personel_id}
                    className="flex items-center justify-between border-t border-rule py-2 text-sm first:border-none"
                  >
                    <span className="text-ink">{b.ad_soyad}</span>
                    <Sayi className="text-ink-muted">{b.sayi}</Sayi>
                  </li>
                ))}
              </ul>
            </Kart>
          )}
        </>
      )}
    </AppShell>
  )
}
