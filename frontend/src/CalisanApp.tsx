import { hataMetni } from './i18n/hata'
import { useMetin } from './i18n/DilBaglami'
import { useEffect, useState } from 'react'
import { api } from './api/client'
import type { Ben, Vardiyalarim } from './api/types'
import { CalisanShell, type CalisanSekmesi } from './components/CalisanShell'
import { OturumBaglami } from './components/OturumBaglami'
import { DonemOzetimEkrani } from './screens/calisan/DonemOzetimEkrani'
import { TercihlerimEkrani } from './screens/calisan/TercihlerimEkrani'
import { VardiyalarimEkrani } from './screens/calisan/VardiyalarimEkrani'

interface Props {
  ben: Ben
  cikis: () => void
  parolaDegistir: () => void
}

// Panel artık personel kimliği ALMAZ. Hangi personelin verisinin geleceğini
// sunucu oturumdan belirliyor (SRS FR-9.1); istemcinin kimliği taşıması,
// sunucu onu yok saysa bile "seçimi istemci yapıyor" izlenimi verirdi.
export function CalisanApp({ ben, cikis, parolaDegistir }: Props) {
  const m = useMetin()
  const [sekme, setSekme] = useState<CalisanSekmesi>('Vardiyalarım')
  const [veri, setVeri] = useState<Vardiyalarim | null>(null)
  const [hata, setHata] = useState<string | null>(null)

  useEffect(() => {
    api
      .calisanVardiyalarim()
      .then(setVeri)
      // 401 buraya düşmez: oturum düştüğünde kök bileşen giriş ekranına
      // döner (api/client.ts, `oturumDustugunde`). Kalan hatalar gerçek
      // hatadır ve kullanıcıya söylenir.
      .catch((e) => setHata(hataMetni(e, m)))
  }, [])

  if (hata) {
    return (
      <div className="flex min-h-svh items-center justify-center bg-canvas px-6 text-center">
        <p className="text-sm text-ink-muted">{hata}</p>
      </div>
    )
  }

  if (!veri) return null

  return (
    <OturumBaglami.Provider value={{ ben, cikis, parolaDegistir }}>
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
        {sekme === 'Tercihlerim' && <TercihlerimEkrani />}
      </CalisanShell>
    </OturumBaglami.Provider>
  )
}
