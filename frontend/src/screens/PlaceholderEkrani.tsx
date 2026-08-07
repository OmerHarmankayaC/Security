import { AppShell, type NavOgesi } from '../components/AppShell'
import { Kart, KartEtiketi } from '../components/app-ui'

interface Props {
  ekran: NavOgesi
  ekranSec: (ekran: NavOgesi) => void
}

// Sprint 2 Gün 10 kapsamı yalnızca Çizelge ve Çözüm ekranları; kalan altı
// nav öğesi, kabuk (sidebar/topbar) tutarlılığı için burada yer tutucu.
export function PlaceholderEkrani({ ekran, ekranSec }: Props) {
  return (
    <AppShell aktifEkran={ekran} ekranSec={ekranSec} baslik={ekran}>
      <Kart>
        <KartEtiketi>yakında</KartEtiketi>
        <p>Bu ekran henüz uygulanmadı.</p>
      </Kart>
    </AppShell>
  )
}
