import { Buton } from '@/components/app-ui'
import { YazdirilabilirCizelge } from '@/components/YazdirilabilirCizelge'
import type { CizelgeVerisi } from '@/lib/disaAktarma'
import { bugunIso } from '@/lib/tarih'

interface Props {
  veri: CizelgeVerisi
  onKapat: () => void
}

/**
 * Yazdırılabilir görünümün ekran kabuğu.
 *
 * Çıktı önce ekranda gösterilir, doğrudan yazıcıya gönderilmez: kullanıcı
 * neyin basılacağını görmeden 36 satırlık bir çizelgeyi kâğıda göndermek
 * zorunda kalmaz. `window.print()` çağrıldığında baskı CSS'i (index.css)
 * gövdeyi gizleyip yalnızca `.yazdirma-alani`yı bırakır, yani ekrandaki
 * bileşenle basılan bileşen aynıdır.
 */
export function YazdirmaOnizlemesi({ veri, onKapat }: Props) {
  return (
    <div className="fixed inset-0 z-50 overflow-auto bg-white p-6">
      <div className="yazdirma-gizle mb-4 flex items-center gap-2">
        <Buton varyant="birincil" onClick={() => window.print()}>
          Yazdır
        </Buton>
        <Buton varyant="hayalet" onClick={onKapat}>
          Kapat
        </Buton>
        <span className="text-sm text-ink-muted">
          Yatay A4 · uzun dönemlerde satırlar sayfaya bölünür, gün başlığı her sayfada
          tekrarlanır.
        </span>
      </div>
      <YazdirilabilirCizelge {...veri} uretimTarihi={bugunIso()} />
    </div>
  )
}
