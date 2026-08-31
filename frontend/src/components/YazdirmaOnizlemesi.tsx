import { createPortal } from 'react-dom'
import { Buton } from '@/components/app-ui'
import { YazdirilabilirCizelge } from '@/components/YazdirilabilirCizelge'
import type { CizelgeVerisi } from '@/lib/disaAktarma'
import { bugunIso } from '@/lib/tarih'
import { useMetin } from '@/i18n/DilBaglami'

interface Props {
  veri: CizelgeVerisi
  onKapat: () => void
}

/**
 * Yazdırılabilir görünümün ekran kabuğu.
 *
 * Çıktı önce ekranda gösterilir, doğrudan yazıcıya gönderilmez: kullanıcı
 * neyin basılacağını görmeden 36 satırlık bir çizelgeyi kâğıda göndermek
 * zorunda kalmaz. Ekrandaki bileşenle basılan bileşen AYNIDIR.
 *
 * GÖVDEYE PORTAL — sayfalama bunu gerektiriyor (Tur 7 İş 5).
 *
 * Önizleme uygulama ağacının içinde, `position: fixed` ve `overflow: auto`
 * taşıyan bir kabın altında duruyordu; baskı CSS'i de yazdırma alanına
 * `position: absolute` veriyordu. Üçü de aynı şeyi yapar: öğeyi normal
 * akıştan çıkarır. Akış dışındaki içerik SAYFALANMAZ — tarayıcı ilk
 * sayfadan sonrasını çizmez. Tek tablolu çıktıda görünmüyordu (zaten bir
 * sayfaya sığıyordu); gün başına ayrı ızgaraya geçilince yedi günlük bir
 * dönem tek sayfa basmaya başladı.
 *
 * Portal, önizlemeyi `#root`un KARDEŞİ yapar. Baskıda `#root` tümüyle
 * gizlenir (`display: none`) ve geriye kalan yazdırma kökü normal akışta
 * durur; sayfalama tarayıcının kendi işi olur. Görünürlük hilesi de
 * mutlak konumlandırma da böylece gereksizleşti ve ikisi de kaldırıldı.
 */
export function YazdirmaOnizlemesi({ veri, onKapat }: Props) {
  const m = useMetin()
  return createPortal(
    <div className="yazdirma-kok fixed inset-0 z-50 overflow-auto bg-white p-6">
      <div className="yazdirma-gizle mb-4 flex items-center gap-2">
        <Buton varyant="birincil" onClick={() => window.print()}>
          {m.yazdirma.yazdir}
        </Buton>
        <Buton varyant="hayalet" onClick={onKapat}>
          Kapat
        </Buton>
        <span className="text-sm text-ink-muted">
          {m.yazdirma.sayfaNotu}
        </span>
      </div>
      <YazdirilabilirCizelge {...veri} uretimTarihi={bugunIso()} />
    </div>,
    document.body,
  )
}
