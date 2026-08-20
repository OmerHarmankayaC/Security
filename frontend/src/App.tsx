import { useCallback, useState } from 'react'
import type { Ben } from './api/types'
import type { NavOgesi } from './components/AppShell'
import { AktifIsSaglayici } from './components/AktifIsBaglami'
import { OturumBaglami } from './components/OturumBaglami'
import { AnalizEkrani } from './screens/AnalizEkrani'
import { CizelgeEkrani } from './screens/CizelgeEkrani'
import { CozumEkrani } from './screens/CozumEkrani'
import { KullanicilarEkrani } from './screens/KullanicilarEkrani'
import { MusaitlikEkrani } from './screens/MusaitlikEkrani'
import { KunyeEkrani } from './screens/KunyeEkrani'
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
  // Çizelge ekranından "Yeniden Çöz" ile gelinen SÜRÜM. Çözüm ekranı bunu
  // `onceki_surum_id` olarak gönderir; sürümün KİLİTLİ atamaları böylece
  // korunur (SDD 5.6). Alan boşken çözüm dönem için sıfırdan başlar.
  const [yenidenCozulecekSurumId, setYenidenCozulecekSurumId] = useState<number | null>(null)

  // Dönem değişince taban sürüm ANLAMSIZ kalır — başka bir dönemin sürümünü
  // taban almak çözümü sessizce yanlış çizelgeye bağlardı. Ekranların
  // hepsi dönem seçimini bu sarmalayıcıdan geçirir.
  //
  // `useCallback` ŞART: Sürümler ekranı bu işlevi bir useEffect bağımlılığı
  // olarak taşıyor (SurumlerEkrani.tsx). Her render'da yeni bir kimlik
  // üretilseydi efekt sonsuz döngüye girer ve ekran durmadan istek atardı.
  const donemIdSec = useCallback((id: number | null) => {
    setDonemId(id)
    setYenidenCozulecekSurumId(null)
  }, [])

  const yenidenCozIste = (id: number, surumId: number | null) => {
    setDonemId(id)
    setYenidenCozulecekSurumId(surumId)
    setEkran('Çözüm')
  }

  // Oturum bilgisi bağlam üzerinden AppShell'e ulaşır. Sekiz ekranın
  // hepsine üç ayrı prop geçirmek, ekranların taşımadıkları bir veriyi
  // sadece iletmek için imzalarına almasını gerektirirdi.
  // Çalışan işin yoklaması KABUKTA yaşar, Çözüm ekranında değil (SDD 6.1):
  // ekran değiştirmek bileşeni unmount ediyor ve yoklamayı öldürüyordu.
  // Sağlayıcı ekran anahtarının dışında durduğu için gezinme onu etkilemez.
  return (
    <OturumBaglami.Provider value={{ ben, cikis, parolaDegistir }}>
      <AktifIsSaglayici>
      {(() => {
        switch (ekran) {
          case 'Künye':
            return <KunyeEkrani ekranSec={setEkran} />
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
                donemIdSec={donemIdSec}
                yenidenCozIste={yenidenCozIste}
              />
            )
          case 'Çözüm':
            return (
              <CozumEkrani
                ekranSec={setEkran}
                donemId={donemId}
                donemIdSec={donemIdSec}
                oncekiSurumId={yenidenCozulecekSurumId}
              />
            )
          case 'Analiz':
            return <AnalizEkrani ekranSec={setEkran} donemId={donemId} donemIdSec={donemIdSec} />
          case 'Sürümler':
            return <SurumlerEkrani ekranSec={setEkran} donemId={donemId} donemIdSec={donemIdSec} />
          case 'Kullanıcılar':
            return (
              <KullanicilarEkrani ekranSec={setEkran} kendiKullaniciAdi={ben.kullanici_adi} />
            )
          default:
            return <PlaceholderEkrani ekran={ekran} ekranSec={setEkran} />
        }
      })()}
      </AktifIsSaglayici>
    </OturumBaglami.Provider>
  )
}

export default App
