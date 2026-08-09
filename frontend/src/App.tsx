import { useState } from 'react'
import type { Ben } from './api/types'
import type { NavOgesi } from './components/AppShell'
import { OturumBaglami } from './components/OturumBaglami'
import { AnalizEkrani } from './screens/AnalizEkrani'
import { CizelgeEkrani } from './screens/CizelgeEkrani'
import { CozumEkrani } from './screens/CozumEkrani'
import { KullanicilarEkrani } from './screens/KullanicilarEkrani'
import { MusaitlikEkrani } from './screens/MusaitlikEkrani'
import { OzetEkrani } from './screens/OzetEkrani'
import { PlaceholderEkrani } from './screens/PlaceholderEkrani'
import { SurumlerEkrani } from './screens/SurumlerEkrani'
import { TanimlarEkrani } from './screens/TanimlarEkrani'
import { TercihlerEkrani } from './screens/TercihlerEkrani'

interface Props {
  ben: Ben
  cikis: () => void
  parolaDegistir: () => void
}

function App({ ben, cikis, parolaDegistir }: Props) {
  const [ekran, setEkran] = useState<NavOgesi>('Özet')
  const [donemId, setDonemId] = useState<number | null>(null)

  const yenidenCozIste = (id: number) => {
    setDonemId(id)
    setEkran('Çözüm')
  }

  // Oturum bilgisi bağlam üzerinden AppShell'e ulaşır. Sekiz ekranın
  // hepsine üç ayrı prop geçirmek, ekranların taşımadıkları bir veriyi
  // sadece iletmek için imzalarına almasını gerektirirdi.
  return (
    <OturumBaglami.Provider value={{ ben, cikis, parolaDegistir }}>
      {(() => {
        switch (ekran) {
          case 'Özet':
            return <OzetEkrani ekranSec={setEkran} />
          case 'Tanımlar':
            return <TanimlarEkrani ekranSec={setEkran} />
          case 'Müsaitlik':
            return <MusaitlikEkrani ekranSec={setEkran} />
          case 'Tercihler':
            return <TercihlerEkrani ekranSec={setEkran} />
          case 'Çizelge':
            return (
              <CizelgeEkrani
                ekranSec={setEkran}
                donemId={donemId}
                donemIdSec={setDonemId}
                yenidenCozIste={yenidenCozIste}
              />
            )
          case 'Çözüm':
            return <CozumEkrani ekranSec={setEkran} donemId={donemId} donemIdSec={setDonemId} />
          case 'Analiz':
            return <AnalizEkrani ekranSec={setEkran} donemId={donemId} donemIdSec={setDonemId} />
          case 'Sürümler':
            return <SurumlerEkrani ekranSec={setEkran} donemId={donemId} donemIdSec={setDonemId} />
          case 'Kullanıcılar':
            return (
              <KullanicilarEkrani ekranSec={setEkran} kendiKullaniciAdi={ben.kullanici_adi} />
            )
          default:
            return <PlaceholderEkrani ekran={ekran} ekranSec={setEkran} />
        }
      })()}
    </OturumBaglami.Provider>
  )
}

export default App
