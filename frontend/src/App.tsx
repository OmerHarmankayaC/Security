import { useState } from 'react'
import type { NavOgesi } from './components/AppShell'
import { CizelgeEkrani } from './screens/CizelgeEkrani'
import { CozumEkrani } from './screens/CozumEkrani'
import { MusaitlikEkrani } from './screens/MusaitlikEkrani'
import { OzetEkrani } from './screens/OzetEkrani'
import { PlaceholderEkrani } from './screens/PlaceholderEkrani'
import { TanimlarEkrani } from './screens/TanimlarEkrani'
import { TercihlerEkrani } from './screens/TercihlerEkrani'

function App() {
  const [ekran, setEkran] = useState<NavOgesi>('Özet')
  const [donemId, setDonemId] = useState<number | null>(null)

  const yenidenCozIste = (id: number) => {
    setDonemId(id)
    setEkran('Çözüm')
  }

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
    default:
      return <PlaceholderEkrani ekran={ekran} ekranSec={setEkran} />
  }
}

export default App
