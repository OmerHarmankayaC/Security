import { AppShell, type NavOgesi } from '../components/AppShell'
import { Kart, KartEtiketi } from '../components/app-ui'
import { useMetin } from '@/i18n/DilBaglami'

interface Props {
  ekran: NavOgesi
  ekranSec: (ekran: NavOgesi) => void
}

// Analiz (Gün 12) ve Sürümler (Gün 15) — Sprint 3 Ara İş'in kapsamı dışında,
// yeni tasarım diliyle kendi günlerinde yapılacaklar (bkz. UYGULAMA_PLANI.md).
export function PlaceholderEkrani({ ekran, ekranSec }: Props) {
  const m = useMetin()
  return (
    <AppShell aktifEkran={ekran} ekranSec={ekranSec} baslik={m.menu[ekran]}>
      <Kart>
        <KartEtiketi>{m.kabuk.yakinda}</KartEtiketi>
        <p>{m.kabuk.yapimAsamasinda}</p>
      </Kart>
    </AppShell>
  )
}
