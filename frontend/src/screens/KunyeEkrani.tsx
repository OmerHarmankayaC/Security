import { AppShell, type NavOgesi } from '../components/AppShell'
import { KunyeIcerigi } from '../components/KunyeIcerigi'
import { useMetin } from '@/i18n/DilBaglami'

interface Props {
  ekranSec: (ekran: NavOgesi) => void
}

/**
 * Künye — projenin ne olduğu, kimin geliştirdiği ve neyle kurulduğu.
 *
 * KURUMUN OPERASYONEL AYRINTISI YAZILMAZ. Proje bir staj kapsamında
 * geliştirildi ve bu yazılır; ama aracın hangi tesisin hangi güvenlik
 * düzenini çizelgelediği yazılmaz. Bir güvenlik kadrosunun nasıl
 * dizildiğini anlatan bir metin, aracın kendisinden daha hassastır.
 *
 * İçerik `components/KunyeIcerigi` içindedir: çalışan paneli de aynı metni
 * gösterir.
 */
export function KunyeEkrani({ ekranSec }: Props) {
  const m = useMetin()
  return (
    <AppShell aktifEkran="Künye" ekranSec={ekranSec} baslik={m.menu['Künye']}>
      <KunyeIcerigi />
    </AppShell>
  )
}
