import { useState } from 'react'
import type { NavOgesi } from './components/AppShell'
import { CizelgeEkrani } from './screens/CizelgeEkrani'
import { CozumEkrani } from './screens/CozumEkrani'
import { PlaceholderEkrani } from './screens/PlaceholderEkrani'

function App() {
  const [ekran, setEkran] = useState<NavOgesi>('Çizelge')
  const [donemId, setDonemId] = useState<number | null>(null)

  const yenidenCozIste = (id: number) => {
    setDonemId(id)
    setEkran('Çözüm')
  }

  switch (ekran) {
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
