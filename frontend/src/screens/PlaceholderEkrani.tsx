import { AppShell, type NavOgesi } from '../components/AppShell'
import { Kart, KartEtiketi } from '../components/app-ui'

interface Props {
  ekran: NavOgesi
  ekranSec: (ekran: NavOgesi) => void
}

// Analiz (Gün 12) ve Sürümler (Gün 15) — Sprint 3 Ara İş'in kapsamı dışında,
// yeni tasarım diliyle kendi günlerinde yapılacaklar (bkz. UYGULAMA_PLANI.md).
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
