import { useEffect, useState } from 'react'
import { api, ApiHatasi } from './api/client'
import type { Vardiyalarim } from './api/types'
import { CalisanShell, type CalisanSekmesi } from './components/CalisanShell'
import { DonemOzetimEkrani } from './screens/calisan/DonemOzetimEkrani'
import { TercihlerimEkrani } from './screens/calisan/TercihlerimEkrani'
import { VardiyalarimEkrani } from './screens/calisan/VardiyalarimEkrani'

interface Props {
  personelId: number
  anahtar: string
}

export function CalisanApp({ personelId, anahtar }: Props) {
  const [sekme, setSekme] = useState<CalisanSekmesi>('Vardiyalarım')
  const [veri, setVeri] = useState<Vardiyalarim | null>(null)
  const [hata, setHata] = useState<string | null>(null)

  useEffect(() => {
    api
      .calisanVardiyalarim(personelId, anahtar)
      .then(setVeri)
      .catch((e) => {
        if (e instanceof ApiHatasi && e.status === 403) {
          setHata('Bu bağlantı geçersiz.')
        } else if (e instanceof ApiHatasi && e.status === 404) {
          setHata('Personel bulunamadı.')
        } else {
          setHata(e instanceof Error ? e.message : 'Veriler yüklenemedi')
        }
      })
  }, [personelId, anahtar])

  if (hata) {
    return (
      <div className="flex min-h-svh items-center justify-center bg-canvas px-6 text-center">
        <p className="text-sm text-ink-muted">{hata}</p>
      </div>
    )
  }

  if (!veri) return null

  return (
    <CalisanShell
      adSoyad={veri.ad_soyad}
      sicilNo={veri.sicil_no}
      yetkinlikler={veri.yetkinlikler}
      donemBaslangic={veri.donem_baslangic_tarihi}
      donemBitis={veri.donem_bitis_tarihi}
      aktifSekme={sekme}
      sekmeSec={setSekme}
    >
      {sekme === 'Vardiyalarım' && <VardiyalarimEkrani veri={veri} />}
      {sekme === 'Dönem Özetim' && <DonemOzetimEkrani veri={veri} />}
      {sekme === 'Tercihlerim' && <TercihlerimEkrani personelId={personelId} anahtar={anahtar} />}
    </CalisanShell>
  )
}
