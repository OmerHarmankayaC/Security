import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import type { CozumIsi, Donem, OnKontrolBulgu } from '../api/types'
import { AppShell, type NavOgesi } from '../components/AppShell'
import { Buton, BuyukRakam, Kart, KartEtiketi } from '../components/app-ui'
import { Input } from '@/components/ui/input'
import { utcTarihiAyristir } from '../lib/tarih'

interface Props {
  ekranSec: (ekran: NavOgesi) => void
  donemId: number | null
  donemIdSec: (id: number | null) => void
}

const CALISAN_DURUMLAR = new Set(['kuyrukta', 'on_kontrol', 'cozuluyor'])

const DURUM_METNI: Record<string, string> = {
  kuyrukta: 'Kuyrukta',
  on_kontrol: 'Ön Kontrol',
  cozuluyor: 'Çözülüyor',
  tamamlandi: 'Tamamlandı',
  uyarili: 'Uyarılı Tamamlandı',
  basarisiz: 'Başarısız',
  iptal: 'İptal Edildi',
}

const SECIM_SINIFI =
  'h-8 rounded-md border border-input bg-transparent px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:opacity-50'

function gecenSureSaniye(baslangicIso: string): number {
  return Math.max(0, Math.floor((Date.now() - utcTarihiAyristir(baslangicIso).getTime()) / 1000))
}

function sureBicimle(saniye: number): string {
  const dk = Math.floor(saniye / 60)
  const sn = saniye % 60
  return `${String(dk).padStart(2, '0')}:${String(sn).padStart(2, '0')}`
}

export function CozumEkrani({ ekranSec, donemId, donemIdSec }: Props) {
  const [donemler, setDonemler] = useState<Donem[]>([])
  const [zamanLimiti, setZamanLimiti] = useState(60)

  const [bulgular, setBulgular] = useState<OnKontrolBulgu[] | null>(null)
  const [onKontrolYukleniyor, setOnKontrolYukleniyor] = useState(false)

  const [isKaydi, setIsKaydi] = useState<CozumIsi | null>(null)
  const [kapsamaSayisi, setKapsamaSayisi] = useState<number | null>(null)
  const [hata, setHata] = useState<string | null>(null)
  const [gecenSure, setGecenSure] = useState(0)

  const anketAraligi = useRef<ReturnType<typeof setInterval> | null>(null)
  const saatAraligi = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    api
      .donemler()
      .then((d) => {
        setDonemler(d)
        if (donemId === null && d[0]) donemIdSec(d[0].donem_id)
      })
      .catch((e) => setHata(e instanceof Error ? e.message : 'Dönemler yüklenemedi'))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const anketiDurdur = () => {
    if (anketAraligi.current) clearInterval(anketAraligi.current)
    if (saatAraligi.current) clearInterval(saatAraligi.current)
  }

  useEffect(() => anketiDurdur, [])

  const isiIzle = (isId: number) => {
    anketiDurdur()
    saatAraligi.current = setInterval(() => {
      setIsKaydi((mevcut) => (mevcut ? { ...mevcut } : mevcut))
    }, 1000)
    anketAraligi.current = setInterval(async () => {
      try {
        const guncel = await api.cozumDurumu(isId)
        setIsKaydi(guncel)
        setGecenSure(gecenSureSaniye(guncel.baslangic_zamani))
        if (!CALISAN_DURUMLAR.has(guncel.durum)) {
          anketiDurdur()
          const kapsama = await api.surumKapsamaAcigi(guncel.surum_id)
          setKapsamaSayisi(kapsama.length)
        }
      } catch (e) {
        anketiDurdur()
        setHata(e instanceof Error ? e.message : 'Çözüm durumu alınamadı')
      }
    }, 1500)
  }

  const onKontrolCalistir = async () => {
    if (donemId === null) return
    setOnKontrolYukleniyor(true)
    setHata(null)
    try {
      const yanit = await api.onKontrolCalistir(donemId)
      setBulgular(yanit.bulgular)
    } catch (e) {
      setHata(e instanceof Error ? e.message : 'Ön kontrol başarısız')
    } finally {
      setOnKontrolYukleniyor(false)
    }
  }

  const cozumBaslat = async () => {
    if (donemId === null) return
    setHata(null)
    setKapsamaSayisi(null)
    try {
      const yeniIs = await api.cozumBaslat(donemId, zamanLimiti)
      setIsKaydi(yeniIs)
      setGecenSure(0)
      isiIzle(yeniIs.is_id)
    } catch (e) {
      setHata(e instanceof Error ? e.message : 'Çözüm başlatılamadı')
    }
  }

  const durdur = async () => {
    if (!isKaydi) return
    try {
      await api.cozumIptalEt(isKaydi.is_id)
    } catch (e) {
      setHata(e instanceof Error ? e.message : 'İptal isteği başarısız')
    }
  }

  const donem = donemler.find((d) => d.donem_id === donemId) ?? null
  const calisiyorMu = isKaydi !== null && CALISAN_DURUMLAR.has(isKaydi.durum)
  const sonuclandiMi = isKaydi !== null && !CALISAN_DURUMLAR.has(isKaydi.durum)

  return (
    <AppShell aktifEkran="Çözüm" ekranSec={ekranSec} baslik="Çözüm">
      <Kart>
        <KartEtiketi>çözüm ayarları</KartEtiketi>
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
            <label htmlFor="zaman-limiti" className="text-sm text-muted-foreground">
              Zaman Limiti (saniye)
            </label>
            <Input
              id="zaman-limiti"
              type="number"
              min={1}
              className="w-32"
              value={zamanLimiti}
              onChange={(e) => setZamanLimiti(Number(e.target.value))}
            />
          </div>
          <div className="flex gap-2">
            <Buton
              varyant="ikincil"
              onClick={onKontrolCalistir}
              disabled={donemId === null || onKontrolYukleniyor}
            >
              Ön Kontrol
            </Buton>
            <Buton
              varyant="birincil"
              onClick={cozumBaslat}
              disabled={donemId === null || calisiyorMu}
            >
              Çözümü Başlat
            </Buton>
          </div>
        </div>

        {bulgular && (
          <div className="mt-4">
            {bulgular.length === 0 ? (
              <p className="text-sm text-muted-foreground">Yapısal bir engel bulunamadı.</p>
            ) : (
              <ul className="m-0 flex list-none flex-col gap-1 p-0">
                {bulgular.map((b, i) => (
                  <li key={i} className="text-sm text-amber-700">
                    {b.aciklama}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </Kart>

      {hata && <p className="text-sm text-destructive">{hata}</p>}

      {isKaydi && calisiyorMu && (
        <Kart vurgulu>
          <KartEtiketi renk="accent">{DURUM_METNI[isKaydi.durum] ?? isKaydi.durum}</KartEtiketi>
          <div className="mb-4 flex gap-10">
            <BuyukRakam deger={sureBicimle(gecenSure)} etiket="Geçen Süre" />
            <BuyukRakam
              deger={isKaydi.en_iyi_ceza !== null ? isKaydi.en_iyi_ceza : '—'}
              etiket="En İyi Ceza"
            />
            <BuyukRakam deger="—" etiket="Kapsama Açığı" />
          </div>
          <Buton varyant="hayalet" onClick={durdur}>
            Durdur
          </Buton>
          <p className="mt-2 text-sm text-muted-foreground">
            Durdur, işi "iptal" olarak işaretler; ayrı süreçte fiilen çalışan arama en iyi çaba
            ile sonlanır, süre limitine kadar arka planda devam edebilir.
          </p>
        </Kart>
      )}

      {isKaydi && sonuclandiMi && (
        <Kart>
          <KartEtiketi renk={isKaydi.durum === 'tamamlandi' ? undefined : 'warn'}>
            sonuç özeti — {DURUM_METNI[isKaydi.durum] ?? isKaydi.durum}
          </KartEtiketi>
          {isKaydi.hata_mesaji && <p className="text-sm text-destructive">{isKaydi.hata_mesaji}</p>}
          {isKaydi.ceza_dokumu && (
            <ul className="m-0 flex list-none flex-col gap-2 p-0">
              {Object.entries(isKaydi.ceza_dokumu)
                .sort(([a], [b]) => a.localeCompare(b))
                .map(([kimlik, deger]) => (
                  <li
                    key={kimlik}
                    className="flex justify-between border-b border-border py-2 text-sm last:border-none"
                  >
                    <span>{kimlik}</span>
                    <span>{deger}</span>
                  </li>
                ))}
            </ul>
          )}
          {kapsamaSayisi !== null && kapsamaSayisi > 0 && (
            <p className="mt-2 text-sm text-muted-foreground">
              {kapsamaSayisi} kapsama açığı bulundu → Çizelge ekranında ilgili hücreler
              işaretlendi.
            </p>
          )}
          {donem && (
            <Buton varyant="hayalet" className="mt-4" onClick={() => ekranSec('Çizelge')}>
              Çizelgeyi Görüntüle
            </Buton>
          )}
        </Kart>
      )}
    </AppShell>
  )
}
