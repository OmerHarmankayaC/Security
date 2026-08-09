import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import type {
  Bina,
  GorevNoktasi,
  GunTipi,
  Kural,
  Personel,
  TalepHucresi,
  VardiyaTipi,
  Yetkinlik,
  YukGostergesi,
} from '../api/types'
import { AppShell, type NavOgesi } from '../components/AppShell'
import { Buton, Kart, KartEtiketi, Rozet, Sayi } from '../components/app-ui'
import { Input } from '@/components/ui/input'
import { cn } from '../lib/utils'
import { bugunIso } from '../lib/tarih'

interface Props {
  ekranSec: (ekran: NavOgesi) => void
}

const SEKMELER = [
  'Talep',
  'Personel',
  'Yetkinlik',
  'Bina',
  'Görev Noktası',
  'Vardiya Tipi',
  'Kural',
] as const
type Sekme = (typeof SEKMELER)[number]

const GUN_VARDIYA_SUTUNLARI: { baslik: string; gunTipi: GunTipi; vardiyaAdi: string }[] = [
  { baslik: 'GÜNDÜZ', gunTipi: 'hafta_ici', vardiyaAdi: 'Gündüz' },
  { baslik: 'AKŞAM', gunTipi: 'hafta_ici', vardiyaAdi: 'Akşam' },
  { baslik: 'GECE', gunTipi: 'hafta_ici', vardiyaAdi: 'Gece' },
  { baslik: 'H.SONU GÜNDÜZ', gunTipi: 'hafta_sonu', vardiyaAdi: 'Gündüz' },
  { baslik: 'H.SONU AKŞAM', gunTipi: 'hafta_sonu', vardiyaAdi: 'Akşam' },
  { baslik: 'H.SONU GECE', gunTipi: 'hafta_sonu', vardiyaAdi: 'Gece' },
]

const INPUT_SINIFI =
  'h-8 w-full rounded-sm border border-rule bg-surface px-2.5 font-mono text-sm text-ink outline-none focus-visible:border-accent focus-visible:ring-3 focus-visible:ring-accent/30'

export function TanimlarEkrani({ ekranSec }: Props) {
  const [sekme, setSekme] = useState<Sekme>('Talep')
  const [ekleAcik, setEkleAcik] = useState(false)

  const [personelListesi, setPersonelListesi] = useState<Personel[]>([])
  const [yetkinlikler, setYetkinlikler] = useState<Yetkinlik[]>([])
  const [binalar, setBinalar] = useState<Bina[]>([])
  const [noktalar, setNoktalar] = useState<GorevNoktasi[]>([])
  const [vardiyaTipleri, setVardiyaTipleri] = useState<VardiyaTipi[]>([])
  const [talepHucreleri, setTalepHucreleri] = useState<TalepHucresi[]>([])
  const [yukGostergesi, setYukGostergesi] = useState<YukGostergesi | null>(null)
  const [kurallar, setKurallar] = useState<Kural[]>([])
  const [hata, setHata] = useState<string | null>(null)

  const hepsiniYukle = () => {
    Promise.all([
      api.personelListele(),
      api.yetkinlikListele(),
      api.binaListele(),
      api.noktaListele(),
      api.vardiyaTipiListele(),
      api.talepGetir(),
      api.kuralListele(),
    ])
      .then(([p, y, b, n, v, t, k]) => {
        setPersonelListesi(p)
        setYetkinlikler(y)
        setBinalar(b)
        setNoktalar(n)
        setVardiyaTipleri(v)
        setTalepHucreleri(t.hucreler)
        setYukGostergesi(t.yuk_gostergesi)
        setKurallar(k)
      })
      .catch((e) => setHata(e instanceof Error ? e.message : 'Tanımlar yüklenemedi'))
  }

  useEffect(hepsiniYukle, [])

  const yetkinlikMap = useMemo(
    () => new Map(yetkinlikler.map((y) => [y.yetkinlik_id, y])),
    [yetkinlikler],
  )
  const vardiyaAdIdMap = useMemo(
    () => new Map(vardiyaTipleri.map((v) => [v.ad, v.vardiya_tipi_id])),
    [vardiyaTipleri],
  )

  const talepHucreBul = (noktaId: number, gunTipi: GunTipi, vardiyaTipiId: number | undefined) =>
    talepHucreleri.find(
      (h) => h.nokta_id === noktaId && h.gun_tipi === gunTipi && h.vardiya_tipi_id === vardiyaTipiId,
    )

  const talepGuncelle = async (
    noktaId: number,
    gunTipi: GunTipi,
    vardiyaTipiId: number,
    gerekenSayi: number,
  ) => {
    try {
      const yanit = await api.talepHucresiGuncelle({
        nokta_id: noktaId,
        vardiya_tipi_id: vardiyaTipiId,
        gun_tipi: gunTipi,
        tarih: null,
        gereken_sayi: gerekenSayi,
      })
      setTalepHucreleri(yanit.hucreler)
      setYukGostergesi(yanit.yuk_gostergesi)
    } catch (e) {
      setHata(e instanceof Error ? e.message : 'Talep güncellenemedi')
    }
  }

  const kuralGuncelle = async (kimlik: string, alan: 'agirlik' | 'aktif', deger: number | boolean) => {
    try {
      const guncel = await api.kuralGuncelle(kimlik, { [alan]: deger })
      setKurallar((mevcut) => mevcut.map((k) => (k.kimlik === kimlik ? guncel : k)))
    } catch (e) {
      setHata(e instanceof Error ? e.message : 'Kural güncellenemedi')
    }
  }

  const eylemEtiketi: Partial<Record<Sekme, string>> = {
    Personel: 'Personel Ekle',
    Yetkinlik: 'Yetkinlik Ekle',
    Bina: 'Bina Ekle',
    'Görev Noktası': 'Görev Noktası Ekle',
    'Vardiya Tipi': 'Vardiya Tipi Ekle',
  }

  const zorunluKurallar = kurallar.filter((k) => k.tip === 'zorunlu')
  const esnekKurallar = kurallar.filter((k) => k.tip === 'esnek')

  return (
    <AppShell
      aktifEkran="Tanımlar"
      ekranSec={ekranSec}
      baslik="Tanımlar"
      aksiyonlar={
        eylemEtiketi[sekme] && (
          <Buton varyant="birincil" onClick={() => setEkleAcik(true)}>
            {eylemEtiketi[sekme]}
          </Buton>
        )
      }
    >
      {hata && <p className="text-sm text-signal">{hata}</p>}

      <div className="flex gap-0.5 border-b border-rule pb-0">
        {SEKMELER.map((s) => (
          <button
            key={s}
            type="button"
            className={cn(
              'rounded-t-sm px-4 py-2.5 text-sm text-ink-muted transition-colors',
              s === sekme && 'bg-chrome-base font-medium text-chrome-ink',
            )}
            onClick={() => {
              setSekme(s)
              setEkleAcik(false)
            }}
          >
            {s}
          </button>
        ))}
      </div>

      {ekleAcik && eylemEtiketi[sekme] && (
        <EkleFormu
          sekme={sekme}
          binalar={binalar}
          yetkinlikler={yetkinlikler}
          onIptal={() => setEkleAcik(false)}
          onKaydedildi={() => {
            setEkleAcik(false)
            hepsiniYukle()
          }}
          onHata={setHata}
        />
      )}

      {sekme === 'Talep' && (
        <>
          <Kart>
            <KartEtiketi>talep matrisi · görev noktası × gün tipi/vardiya</KartEtiketi>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[720px] border-collapse">
                <thead>
                  <tr className="bg-sunken">
                    <th className="whitespace-nowrap px-3 py-2 text-left font-condensed text-[10px] tracking-[0.1em] text-ink-muted">
                      GÖREV NOKTASI
                    </th>
                    {GUN_VARDIYA_SUTUNLARI.map((sutun) => (
                      <th
                        key={sutun.baslik}
                        className="whitespace-nowrap px-3 py-2 text-left font-condensed text-[10px] tracking-[0.1em] text-ink-muted"
                      >
                        {sutun.baslik}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {noktalar.map((n) => (
                    <tr key={n.nokta_id} className="border-t border-rule">
                      <td className="px-3 py-3 text-sm font-medium text-ink">{n.ad}</td>
                      {GUN_VARDIYA_SUTUNLARI.map((sutun) => {
                        const vardiyaTipiId = vardiyaAdIdMap.get(sutun.vardiyaAdi)
                        const hucre = talepHucreBul(n.nokta_id, sutun.gunTipi, vardiyaTipiId)
                        return (
                          <td key={sutun.baslik} className="px-3 py-2">
                            <input
                              type="number"
                              min={0}
                              className={cn(INPUT_SINIFI, 'w-16 bg-sunken text-center')}
                              defaultValue={hucre?.gereken_sayi ?? 0}
                              onBlur={(e) => {
                                if (vardiyaTipiId === undefined) return
                                const deger = Number(e.target.value)
                                if (deger !== (hucre?.gereken_sayi ?? 0)) {
                                  talepGuncelle(n.nokta_id, sutun.gunTipi, vardiyaTipiId, deger)
                                }
                              }}
                            />
                          </td>
                        )
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Kart>
          {yukGostergesi && (
            <Kart className="bg-sunken">
              <div className="flex gap-10">
                <div>
                  <p className="m-0 font-condensed text-[10px] tracking-[0.1em] text-ink-muted">
                    HAFTALIK KİŞİ-VARDİYA YÜKÜ
                  </p>
                  <Sayi className="text-xl font-semibold text-ink">
                    {yukGostergesi.haftalik_kisi_vardiya}
                  </Sayi>
                </div>
                <div>
                  <p className="m-0 font-condensed text-[10px] tracking-[0.1em] text-ink-muted">
                    ASGARİ KADRO (KURAL PARAMETRELERİNE GÖRE)
                  </p>
                  <Sayi className="text-xl font-semibold text-ink">{yukGostergesi.asgari_kadro}</Sayi>
                </div>
                <div>
                  <p className="m-0 font-condensed text-[10px] tracking-[0.1em] text-ink-muted">
                    MEVCUT PERSONEL
                  </p>
                  <Sayi className="text-xl font-semibold text-ink">{personelListesi.length}</Sayi>
                </div>
              </div>
            </Kart>
          )}
        </>
      )}

      {sekme === 'Personel' && (
        <Kart>
          <table className="w-full min-w-[720px] border-collapse">
            <thead>
              <tr className="bg-sunken">
                {['AD', 'SİCİL', 'YETKİNLİKLER', 'HEDEF SAAT', 'SABİT VARDİYA', 'DURUM'].map((b) => (
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
              {personelListesi.map((p) => {
                const aktifMi = !p.aktif_bitis || p.aktif_bitis >= bugunIso()
                return (
                  <tr key={p.personel_id} className="border-t border-rule">
                    <td className="px-3 py-3 text-sm font-medium text-ink">{p.ad_soyad}</td>
                    <td className="px-3 py-3 font-mono text-sm text-ink-muted">{p.sicil_no}</td>
                    <td className="px-3 py-3 text-sm text-ink-muted">
                      {p.yetkinlik_idleri.map((id) => yetkinlikMap.get(id)?.ad ?? id).join(', ') || '—'}
                    </td>
                    <td className="px-3 py-3 font-mono text-sm text-ink">
                      <Sayi>{p.haftalik_hedef_saat}</Sayi> sa
                    </td>
                    <td className="px-3 py-3 text-sm text-ink-muted">
                      {vardiyaTipleri.find((v) => v.vardiya_tipi_id === p.sabit_vardiya_tipi_id)?.ad ?? '—'}
                    </td>
                    <td className="px-3 py-3">
                      <Rozet varyant={aktifMi ? 'dolu' : 'notr'} genislik={64}>
                        {aktifMi ? 'Aktif' : 'İzinli'}
                      </Rozet>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </Kart>
      )}

      {sekme === 'Yetkinlik' && (
        <div className="flex flex-col gap-3">
          {yetkinlikler.map((y) => (
            <Kart key={y.yetkinlik_id}>
              <div className="flex items-start justify-between gap-6">
                <div>
                  <p className="m-0 text-base font-semibold text-ink">{y.ad}</p>
                  {y.aciklama && <p className="mt-1 text-sm text-ink-muted">{y.aciklama}</p>}
                </div>
                <div className="text-right">
                  <Sayi className="text-2xl font-semibold text-ink">
                    {personelListesi.filter((p) => p.yetkinlik_idleri.includes(y.yetkinlik_id)).length}
                  </Sayi>
                  <p className="m-0 font-condensed text-[10px] tracking-[0.1em] text-ink-muted">PERSONEL</p>
                </div>
              </div>
            </Kart>
          ))}
        </div>
      )}

      {sekme === 'Bina' && (
        <div className="flex flex-col gap-3">
          {binalar.length === 0 && (
            <p className="text-sm text-ink-muted">
              Bina tanımlı değil — mevcut uygulama alanında bütün noktalar tesis geneli (SRS 3.3.3).
            </p>
          )}
          {binalar.map((b) => (
            <Kart key={b.bina_id}>
              <p className="m-0 text-base font-semibold text-ink">{b.ad}</p>
            </Kart>
          ))}
        </div>
      )}

      {sekme === 'Görev Noktası' && (
        <div className="flex flex-col gap-3">
          {noktalar.map((n) => (
            <Kart key={n.nokta_id}>
              <div className="flex items-center justify-between gap-6">
                <div>
                  <p className="m-0 text-base font-semibold text-ink">{n.ad}</p>
                  <p className="mt-1 text-sm text-ink-muted">
                    {n.bina_id ? binalar.find((b) => b.bina_id === n.bina_id)?.ad : 'Tesis geneli'}
                    {' · '}
                    {n.onkosul_yetkinlik_id
                      ? (yetkinlikMap.get(n.onkosul_yetkinlik_id)?.ad ?? 'Ön koşul var')
                      : 'Ön koşul yok'}
                  </p>
                </div>
                <Rozet varyant={n.aktif ? 'dolu' : 'notr'} genislik={64}>
                  {n.aktif ? 'Aktif' : 'Pasif'}
                </Rozet>
              </div>
            </Kart>
          ))}
        </div>
      )}

      {sekme === 'Vardiya Tipi' && (
        <div className="flex flex-col gap-3">
          {vardiyaTipleri.map((v) => (
            <Kart key={v.vardiya_tipi_id}>
              <div className="flex items-center justify-between gap-6">
                <div>
                  <p className="m-0 text-base font-semibold text-ink">{v.ad}</p>
                  <p className="mt-1 font-mono text-sm text-ink-muted">
                    {v.baslangic_saati.slice(0, 5)} – {v.bitis_saati.slice(0, 5)} ·{' '}
                    <Sayi>{v.sure_saat}</Sayi> saat
                  </p>
                </div>
                {v.gece_mi && (
                  <Rozet varyant="kilitli" genislik={64}>
                    Gece
                  </Rozet>
                )}
              </div>
            </Kart>
          ))}
        </div>
      )}

      {sekme === 'Kural' && (
        <>
          <Kart>
            <KartEtiketi>H1–H8 · zorunlu kısıtlar</KartEtiketi>
            <ul className="m-0 flex list-none flex-col p-0">
              {zorunluKurallar.map((k) => (
                <li
                  key={k.kimlik}
                  className="flex items-center justify-between gap-4 border-t border-rule py-2.5 first:border-none"
                >
                  <span className="w-10 shrink-0 font-mono text-sm font-semibold text-ink">{k.kimlik}</span>
                  <span className="flex-1 text-sm text-ink">{JSON.stringify(k.parametreler)}</span>
                  <button
                    type="button"
                    onClick={() => kuralGuncelle(k.kimlik, 'aktif', !k.aktif)}
                    className="shrink-0"
                  >
                    <Rozet varyant={k.aktif ? 'dolu' : 'notr'} genislik={64}>
                      {k.aktif ? 'Aktif' : 'Pasif'}
                    </Rozet>
                  </button>
                </li>
              ))}
            </ul>
          </Kart>
          <Kart>
            <KartEtiketi>S1–S8 · esnek hedefler</KartEtiketi>
            <ul className="m-0 flex list-none flex-col p-0">
              {esnekKurallar.map((k) => (
                <li
                  key={k.kimlik}
                  className="flex items-center justify-between gap-4 border-t border-rule py-2.5 first:border-none"
                >
                  <span className="w-10 shrink-0 font-mono text-sm font-semibold text-accent">
                    {k.kimlik}
                  </span>
                  <span className="flex-1 text-sm text-ink" />
                  <Input
                    type="number"
                    className="w-20 rounded-sm border-rule font-mono text-right"
                    defaultValue={k.agirlik ?? 0}
                    onBlur={(e) => {
                      const deger = Number(e.target.value)
                      if (deger !== k.agirlik) kuralGuncelle(k.kimlik, 'agirlik', deger)
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => kuralGuncelle(k.kimlik, 'aktif', !k.aktif)}
                    className="shrink-0"
                  >
                    <Rozet varyant={k.aktif ? 'dolu' : 'notr'} genislik={64}>
                      {k.aktif ? 'Aktif' : 'Pasif'}
                    </Rozet>
                  </button>
                </li>
              ))}
            </ul>
          </Kart>
        </>
      )}
    </AppShell>
  )
}

interface EkleFormuProps {
  sekme: Sekme
  binalar: Bina[]
  yetkinlikler: Yetkinlik[]
  onIptal: () => void
  onKaydedildi: () => void
  onHata: (mesaj: string) => void
}

function EkleFormu({ sekme, binalar, yetkinlikler, onIptal, onKaydedildi, onHata }: EkleFormuProps) {
  const [ad, setAd] = useState('')
  const [ikinciAlan, setIkinciAlan] = useState('')
  const [ucuncuAlan, setUcuncuAlan] = useState('')
  const [binaId, setBinaId] = useState('')
  const [yetkinlikId, setYetkinlikId] = useState('')
  const [gonderiliyor, setGonderiliyor] = useState(false)

  const kaydet = async () => {
    setGonderiliyor(true)
    try {
      if (sekme === 'Personel') {
        await api.personelOlustur({
          ad_soyad: ad,
          sicil_no: ikinciAlan,
          haftalik_hedef_saat: Number(ucuncuAlan) || 40,
          aktif_baslangic: bugunIso(),
          yetkinlik_idleri: yetkinlikId ? [Number(yetkinlikId)] : [],
        })
      } else if (sekme === 'Yetkinlik') {
        await api.yetkinlikOlustur(ad, ikinciAlan || undefined)
      } else if (sekme === 'Bina') {
        await api.binaOlustur(ad)
      } else if (sekme === 'Görev Noktası') {
        await api.noktaOlustur(ad, binaId ? Number(binaId) : null, yetkinlikId ? Number(yetkinlikId) : null)
      } else if (sekme === 'Vardiya Tipi') {
        await api.vardiyaTipiOlustur(ad, ikinciAlan, ucuncuAlan)
      }
      onKaydedildi()
    } catch (e) {
      onHata(e instanceof Error ? e.message : 'Kayıt oluşturulamadı')
    } finally {
      setGonderiliyor(false)
    }
  }

  return (
    <Kart vurgulu>
      <KartEtiketi renk="accent">{sekme.toLocaleLowerCase('tr-TR')} ekle</KartEtiketi>
      <div className="flex flex-wrap items-end gap-4">
        <div className="flex flex-col gap-1">
          <label className="text-sm text-ink-muted">Ad</label>
          <Input value={ad} onChange={(e) => setAd(e.target.value)} className="w-52 rounded-sm border-rule" />
        </div>
        {sekme === 'Personel' && (
          <>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-ink-muted">Sicil No</label>
              <Input
                value={ikinciAlan}
                onChange={(e) => setIkinciAlan(e.target.value)}
                className="w-32 rounded-sm border-rule font-mono"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-ink-muted">Hedef Saat</label>
              <Input
                type="number"
                value={ucuncuAlan}
                onChange={(e) => setUcuncuAlan(e.target.value)}
                placeholder="40"
                className="w-24 rounded-sm border-rule font-mono"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-ink-muted">Yetkinlik</label>
              <select
                className={INPUT_SINIFI}
                value={yetkinlikId}
                onChange={(e) => setYetkinlikId(e.target.value)}
              >
                <option value="">—</option>
                {yetkinlikler.map((y) => (
                  <option key={y.yetkinlik_id} value={y.yetkinlik_id}>
                    {y.ad}
                  </option>
                ))}
              </select>
            </div>
          </>
        )}
        {sekme === 'Yetkinlik' && (
          <div className="flex flex-col gap-1">
            <label className="text-sm text-ink-muted">Açıklama</label>
            <Input
              value={ikinciAlan}
              onChange={(e) => setIkinciAlan(e.target.value)}
              className="w-64 rounded-sm border-rule"
            />
          </div>
        )}
        {sekme === 'Görev Noktası' && (
          <>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-ink-muted">Bina</label>
              <select className={INPUT_SINIFI} value={binaId} onChange={(e) => setBinaId(e.target.value)}>
                <option value="">Tesis geneli</option>
                {binalar.map((b) => (
                  <option key={b.bina_id} value={b.bina_id}>
                    {b.ad}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-ink-muted">Ön Koşul Yetkinlik</label>
              <select
                className={INPUT_SINIFI}
                value={yetkinlikId}
                onChange={(e) => setYetkinlikId(e.target.value)}
              >
                <option value="">—</option>
                {yetkinlikler.map((y) => (
                  <option key={y.yetkinlik_id} value={y.yetkinlik_id}>
                    {y.ad}
                  </option>
                ))}
              </select>
            </div>
          </>
        )}
        {sekme === 'Vardiya Tipi' && (
          <>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-ink-muted">Başlangıç</label>
              <Input
                type="time"
                value={ikinciAlan}
                onChange={(e) => setIkinciAlan(e.target.value)}
                className="w-28 rounded-sm border-rule font-mono"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-ink-muted">Bitiş</label>
              <Input
                type="time"
                value={ucuncuAlan}
                onChange={(e) => setUcuncuAlan(e.target.value)}
                className="w-28 rounded-sm border-rule font-mono"
              />
            </div>
          </>
        )}
        <Buton varyant="birincil" onClick={kaydet} disabled={gonderiliyor || !ad}>
          Kaydet
        </Buton>
        <Buton varyant="hayalet" onClick={onIptal}>
          İptal
        </Buton>
      </div>
    </Kart>
  )
}
