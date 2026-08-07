import { useEffect, useMemo, useState } from 'react'
import { api, ApiHatasi } from '../api/client'
import type {
  Atama,
  CizelgeSurumu,
  Donem,
  DogrulamaSonucu,
  GorevNoktasi,
  KapsamaAcigi,
  Personel,
  VardiyaTipi,
} from '../api/types'
import { AppShell, type NavOgesi } from '../components/AppShell'
import { Buton, Kart, KartEtiketi } from '../components/app-ui'
import { cn } from '../lib/utils'
import { gunKisaltmasiVeNumarasi, gunlerListesi, zamanBicimle } from '../lib/tarih'

interface Props {
  ekranSec: (ekran: NavOgesi) => void
  donemId: number | null
  donemIdSec: (id: number | null) => void
  yenidenCozIste: (donemId: number) => void
}

const BOSALT_DEGERI = ''

const SURUM_DURUM_METNI: Record<string, string> = {
  taslak: 'Taslak',
  cozuldu: 'Çözüldü',
  yayinlandi: 'Yayınlandı',
  arsiv: 'Arşiv',
}

const SECIM_SINIFI =
  'h-8 rounded-md border border-input bg-transparent px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:opacity-50'

const HUCRE_DURUM_SINIFI: Record<string, string> = {
  bos: 'border-transparent bg-transparent',
  dolu: 'border-border bg-card',
  eksik: 'border-amber-700 bg-amber-100 font-medium text-amber-700',
  kilitli: 'border-primary bg-accent font-medium text-primary',
}

interface SeciliHucre {
  personelId: number
  tarih: string
}

export function CizelgeEkrani({ ekranSec, donemId, donemIdSec, yenidenCozIste }: Props) {
  const [donemler, setDonemler] = useState<Donem[]>([])
  const [surumler, setSurumler] = useState<CizelgeSurumu[]>([])
  const [surumId, setSurumId] = useState<number | null>(null)

  const [personelListesi, setPersonelListesi] = useState<Personel[]>([])
  const [vardiyaTipleri, setVardiyaTipleri] = useState<VardiyaTipi[]>([])
  const [noktalar, setNoktalar] = useState<GorevNoktasi[]>([])

  const [atamalar, setAtamalar] = useState<Atama[]>([])
  const [kapsamaAcigi, setKapsamaAcigi] = useState<KapsamaAcigi[]>([])
  const [yukleniyor, setYukleniyor] = useState(false)
  const [hata, setHata] = useState<string | null>(null)

  const [seciliHucre, setSeciliHucre] = useState<SeciliHucre | null>(null)
  const [seciliVardiyaTipiId, setSeciliVardiyaTipiId] = useState<string>(BOSALT_DEGERI)
  const [seciliNoktaId, setSeciliNoktaId] = useState<string>(BOSALT_DEGERI)
  const [dogrulamaSonucu, setDogrulamaSonucu] = useState<DogrulamaSonucu | null>(null)
  const [panelYukleniyor, setPanelYukleniyor] = useState(false)
  const [panelHata, setPanelHata] = useState<string | null>(null)

  // Tanim listeleri + donemler: bir kez yuklenir.
  useEffect(() => {
    Promise.all([
      api.donemler(),
      api.personelListele(),
      api.vardiyaTipiListele(),
      api.noktaListele(),
    ])
      .then(([d, p, v, n]) => {
        setDonemler(d)
        setPersonelListesi(p)
        setVardiyaTipleri(v)
        setNoktalar(n)
        if (donemId === null && d[0]) donemIdSec(d[0].donem_id)
      })
      .catch((e) => setHata(e instanceof Error ? e.message : 'Tanımlar yüklenemedi'))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Donem degisince surumleri yukle, en son surumu sec.
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

  const surumYukle = () => {
    if (surumId === null) {
      setAtamalar([])
      setKapsamaAcigi([])
      return
    }
    setYukleniyor(true)
    setHata(null)
    Promise.all([api.surumAtamalari(surumId), api.surumKapsamaAcigi(surumId)])
      .then(([a, k]) => {
        setAtamalar(a)
        setKapsamaAcigi(k)
      })
      .catch((e) => setHata(e instanceof Error ? e.message : 'Çizelge yüklenemedi'))
      .finally(() => setYukleniyor(false))
  }

  useEffect(surumYukle, [surumId])

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
  const noktaMap = useMemo(() => new Map(noktalar.map((n) => [n.nokta_id, n])), [noktalar])

  const gunler = donem ? gunlerListesi(donem.baslangic_tarihi, donem.bitis_tarihi) : []

  const izgaraPersonelleri = useMemo(() => {
    const idler = new Set(atamalar.map((a) => a.personel_id))
    return [...idler]
      .map((id) => personelMap.get(id))
      .filter((p): p is Personel => p !== undefined)
      .sort((a, b) => a.ad_soyad.localeCompare(b.ad_soyad, 'tr'))
  }, [atamalar, personelMap])

  const atamaBul = (personelId: number, tarih: string): Atama | undefined =>
    atamalar.find((a) => a.personel_id === personelId && a.tarih === tarih)

  const kapsamaBul = (atama: Atama): KapsamaAcigi | undefined =>
    kapsamaAcigi.find(
      (k) =>
        k.tarih === atama.tarih &&
        k.vardiya_tipi_id === atama.vardiya_tipi_id &&
        k.nokta_id === atama.nokta_id,
    )

  const hucreSec = (personelId: number, tarih: string) => {
    setSeciliHucre({ personelId, tarih })
    const mevcut = atamaBul(personelId, tarih)
    setSeciliVardiyaTipiId(mevcut ? String(mevcut.vardiya_tipi_id) : BOSALT_DEGERI)
    setSeciliNoktaId(mevcut ? String(mevcut.nokta_id) : BOSALT_DEGERI)
    setDogrulamaSonucu(null)
    setPanelHata(null)
  }

  const istekGovdesiOlustur = () => {
    if (!seciliHucre || surumId === null) return null
    return {
      surum_id: surumId,
      personel_id: seciliHucre.personelId,
      tarih: seciliHucre.tarih,
      vardiya_tipi_id: seciliVardiyaTipiId === BOSALT_DEGERI ? null : Number(seciliVardiyaTipiId),
      nokta_id: seciliNoktaId === BOSALT_DEGERI ? null : Number(seciliNoktaId),
    }
  }

  const dogrula = async () => {
    const govde = istekGovdesiOlustur()
    if (!govde) return
    setPanelYukleniyor(true)
    setPanelHata(null)
    try {
      const sonuc = await api.atamaDogrula(govde)
      setDogrulamaSonucu(sonuc)
    } catch (e) {
      setPanelHata(e instanceof Error ? e.message : 'Doğrulama başarısız')
    } finally {
      setPanelYukleniyor(false)
    }
  }

  const uygula = async () => {
    const govde = istekGovdesiOlustur()
    if (!govde) return
    setPanelYukleniyor(true)
    setPanelHata(null)
    try {
      const sonuc = await api.atamaGuncelle(govde)
      setDogrulamaSonucu(sonuc)
      surumYukle()
    } catch (e) {
      if (e instanceof ApiHatasi && e.detay && typeof e.detay === 'object') {
        setDogrulamaSonucu(e.detay as DogrulamaSonucu)
      } else {
        setPanelHata(e instanceof Error ? e.message : 'Değişiklik uygulanamadı')
      }
    } finally {
      setPanelYukleniyor(false)
    }
  }

  const kilidiDegistir = async () => {
    if (!seciliHucre || surumId === null) return
    const mevcut = atamaBul(seciliHucre.personelId, seciliHucre.tarih)
    if (!mevcut) return
    setPanelYukleniyor(true)
    setPanelHata(null)
    try {
      await api.atamaKilitAyarla(surumId, seciliHucre.personelId, seciliHucre.tarih, !mevcut.kilitli)
      surumYukle()
    } catch (e) {
      setPanelHata(e instanceof Error ? e.message : 'Kilit değiştirilemedi')
    } finally {
      setPanelYukleniyor(false)
    }
  }

  const seciliPersonel = seciliHucre ? personelMap.get(seciliHucre.personelId) : null
  const seciliMevcutAtama = seciliHucre ? atamaBul(seciliHucre.personelId, seciliHucre.tarih) : null

  return (
    <AppShell
      aktifEkran="Çizelge"
      ekranSec={ekranSec}
      baslik={surum ? `Çizelge — Sürüm ${surum.surum_no}` : 'Çizelge'}
      altBaslik={
        surum
          ? `${SURUM_DURUM_METNI[surum.durum] ?? surum.durum} · Son güncelleme ${zamanBicimle(surum.guncelleme_zamani)}`
          : undefined
      }
      aksiyonlar={
        <>
          <Buton varyant="hayalet" disabled title="Sprint 3'te eklenecek">
            Nokta Görünümü
          </Buton>
          <Buton
            varyant="birincil"
            disabled={donemId === null}
            onClick={() => donemId !== null && yenidenCozIste(donemId)}
          >
            Yeniden Çöz
          </Buton>
        </>
      }
    >
      <Kart>
        <KartEtiketi>seçim</KartEtiketi>
        <div className="flex flex-wrap items-end gap-6">
          <div className="flex flex-col gap-1">
            <label htmlFor="donem-sec" className="text-sm text-muted-foreground">
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
            <label htmlFor="surum-sec" className="text-sm text-muted-foreground">
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

      {hata && <p className="text-sm text-destructive">{hata}</p>}

      <Kart>
        {yukleniyor ? (
          <p>Yükleniyor…</p>
        ) : izgaraPersonelleri.length === 0 ? (
          <p>Bu sürümde henüz atama yok.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-max min-w-full border-collapse">
              <thead>
                <tr>
                  <th className="p-2" />
                  {gunler.map((gun) => (
                    <th
                      key={gun}
                      className="whitespace-nowrap p-2 text-center text-xs font-medium text-muted-foreground"
                    >
                      {gunKisaltmasiVeNumarasi(gun)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {izgaraPersonelleri.map((p) => (
                  <tr key={p.personel_id}>
                    <td className="whitespace-nowrap px-3 py-2 text-right text-sm text-foreground">
                      {p.ad_soyad}
                    </td>
                    {gunler.map((gun) => {
                      const atama = atamaBul(p.personel_id, gun)
                      const kapsama = atama ? kapsamaBul(atama) : undefined
                      const durum = !atama ? 'bos' : atama.kilitli ? 'kilitli' : kapsama ? 'eksik' : 'dolu'
                      const seciliMi =
                        seciliHucre?.personelId === p.personel_id && seciliHucre?.tarih === gun
                      return (
                        <td key={gun} className="p-0">
                          <button
                            type="button"
                            className={cn(
                              'box-border h-11 w-24 rounded-md border p-1 text-center text-xs',
                              HUCRE_DURUM_SINIFI[durum],
                              seciliMi && 'outline-2 outline-offset-[-2px] outline-foreground',
                            )}
                            onClick={() => hucreSec(p.personel_id, gun)}
                          >
                            {atama && (
                              <>
                                {vardiyaMap.get(atama.vardiya_tipi_id)?.ad}
                                <br />
                                {kapsama
                                  ? `${kapsama.eksik_sayi} eksik`
                                  : noktaMap.get(atama.nokta_id)?.ad}
                              </>
                            )}
                          </button>
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Kart>

      {seciliHucre && seciliPersonel && (
        <Kart>
          <KartEtiketi>atama düzenle</KartEtiketi>
          <div className="flex flex-col gap-4">
            <p className="text-sm text-foreground">
              {seciliPersonel.ad_soyad} — {gunKisaltmasiVeNumarasi(seciliHucre.tarih)}
            </p>
            <div className="flex flex-wrap items-end gap-4">
              <div className="flex flex-col gap-1">
                <label htmlFor="vardiya-sec" className="text-sm text-muted-foreground">
                  Vardiya
                </label>
                <select
                  id="vardiya-sec"
                  className={SECIM_SINIFI}
                  value={seciliVardiyaTipiId}
                  onChange={(e) => setSeciliVardiyaTipiId(e.target.value)}
                >
                  <option value={BOSALT_DEGERI}>— Boşalt —</option>
                  {vardiyaTipleri.map((v) => (
                    <option key={v.vardiya_tipi_id} value={v.vardiya_tipi_id}>
                      {v.ad}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <label htmlFor="nokta-sec" className="text-sm text-muted-foreground">
                  Görev Noktası
                </label>
                <select
                  id="nokta-sec"
                  className={SECIM_SINIFI}
                  value={seciliNoktaId}
                  onChange={(e) => setSeciliNoktaId(e.target.value)}
                  disabled={seciliVardiyaTipiId === BOSALT_DEGERI}
                >
                  <option value={BOSALT_DEGERI}>—</option>
                  {noktalar.map((n) => (
                    <option key={n.nokta_id} value={n.nokta_id}>
                      {n.ad}
                    </option>
                  ))}
                </select>
              </div>
              <Buton varyant="ikincil" onClick={dogrula} disabled={panelYukleniyor}>
                Doğrula
              </Buton>
              <Buton varyant="birincil" onClick={uygula} disabled={panelYukleniyor}>
                Uygula
              </Buton>
              {seciliMevcutAtama && (
                <Buton varyant="hayalet" onClick={kilidiDegistir} disabled={panelYukleniyor}>
                  {seciliMevcutAtama.kilitli ? 'Kilidi Aç' : 'Kilitle'}
                </Buton>
              )}
            </div>

            {panelHata && <p className="text-sm text-destructive">{panelHata}</p>}

            {dogrulamaSonucu && (
              <div>
                <p className="text-sm text-foreground">
                  {dogrulamaSonucu.kabul_edilebilir
                    ? 'Kabul edilebilir.'
                    : 'Zorunlu kısıt ihlali — reddedildi.'}{' '}
                  Esnek hedef ceza değişimi: {dogrulamaSonucu.ceza_degisimi.toFixed(2)}
                </p>
                {dogrulamaSonucu.zorunlu_ihlaller.length > 0 && (
                  <ul className="m-0 mt-1 flex list-none flex-col gap-1 p-0">
                    {dogrulamaSonucu.zorunlu_ihlaller.map((ihlal, i) => (
                      <li key={i} className="text-sm text-destructive">
                        {ihlal.kural_kimlik} — {ihlal.aciklama}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>
        </Kart>
      )}
    </AppShell>
  )
}
