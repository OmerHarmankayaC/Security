// Çalışan veya karar bekleyen çözüm işinin, YÖNETİCİ KABUĞUNA bağlı hâli
// (SDD 6.1 "Çalışan İş Göstergesi", SRS FR-4.11).
//
// Yoklama daha önce Çözüm ekranı bileşeninin içinde yaşıyordu ve başka bir
// ekrana geçildiğinde unmount ile birlikte ölüyordu; iş kimliği de o
// bileşenin state'indeydi. Sonuç: backend'de gerçekten süren bir iş
// arayüzden kayboluyordu.
//
// İŞ KİMLİĞİ BURADA DA TUTULMAZ. Kabuk sunucuya "devam eden veya karar
// bekleyen bir iş var mı" diye sorar; kimlik yanıtın içinden gelir. İşin
// varlığı zaten veritabanında kayıtlı ve tek doğru kaynak orasıdır — aynı
// bilginin tarayıcı belleğinde ikinci bir kopyasının durması, sayfa
// yenilendiğinde veya başka bir cihazdan girildiğinde iki kaynağı
// ayrıştırır. Bu ayrışma, hatanın kendisiydi.
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type PropsWithChildren,
} from 'react'
import { api } from '@/api/client'
import type { CozumIsi } from '@/api/types'

// Bir iş sürerken sık, sürmezken seyrek yoklanır. Seyrek yoklama boşuna
// değil: iş başka bir sekmeden veya başka bir cihazdan da başlatılmış
// olabilir ve göstergenin onu da görmesi gerekir.
const CALISIRKEN_ARALIK_MS = 1500
const BOSTA_ARALIK_MS = 5000

export interface AktifIsDurumu {
  /** Devam eden ya da karar bekleyen iş; yoksa null. Kaynağı sunucudur. */
  aktifIs: CozumIsi | null
  /**
   * Az önce sonuçlanmış iş (tamamlandı / uyarılı / başarısız / iptal).
   * Gösterge sonucu bildirsin diye tutulur; kullanıcı kapatınca gider.
   */
  sonuclananIs: CozumIsi | null
  /** Aktif işin başlangıcından bu yana geçen saniye. */
  gecenSure: number
  /** Sunucuyu hemen yeniden sorar (çözüm başlatıldıktan sonra kullanılır). */
  yenile: () => Promise<void>
  sonucuKapat: () => void
}

const AktifIsBaglami = createContext<AktifIsDurumu | null>(null)

export function useAktifIs(): AktifIsDurumu {
  const durum = useContext(AktifIsBaglami)
  if (durum === null) {
    throw new Error('AktifIsBaglami saglayicisi yok')
  }
  return durum
}

function gecenSureSaniye(baslangicIso: string): number {
  // Sunucu zaman damgaları saat dilimi taşır (timestamptz); Date bunu
  // doğrudan ayrıştırır.
  return Math.max(0, Math.floor((Date.now() - new Date(baslangicIso).getTime()) / 1000))
}

export function AktifIsSaglayici({ children }: PropsWithChildren) {
  const [aktifIs, setAktifIs] = useState<CozumIsi | null>(null)
  const [sonuclananIs, setSonuclananIs] = useState<CozumIsi | null>(null)
  const [gecenSure, setGecenSure] = useState(0)
  // Yalnızca "iş kayboldu" geçişini yakalamak için; okuma kaynağı değil.
  const oncekiIsId = useRef<number | null>(null)

  const yenile = useCallback(async () => {
    try {
      const guncel = await api.cozumAktif()
      setAktifIs(guncel)
      if (guncel !== null) {
        oncekiIsId.current = guncel.is_id
        setGecenSure(gecenSureSaniye(guncel.baslangic_zamani))
        setSonuclananIs(null)
        return
      }
      const bitenId = oncekiIsId.current
      oncekiIsId.current = null
      if (bitenId !== null) {
        // İş listeden düştü: son hâlini bir kez okuyup bildiriyoruz.
        // Kimlik burada bir kez KULLANILIYOR, saklanmıyor — sunucunun bir
        // önceki yanıtından geldi ve bu istekten sonra bırakılıyor.
        setSonuclananIs(await api.cozumDurumu(bitenId))
      }
    } catch {
      // Gösterge ikincil bir bilgi alanıdır; ağ hatasında sessizce bekler
      // ve bir sonraki yoklamada yeniden dener. Ekranın kendi hata
      // bildirimi zaten görünür olur.
    }
  }, [])

  // Aralık, işin VARLIĞINA bakar; işin kendisine değil. Bağımlılık olarak
  // `aktifIs` verilseydi her yoklama yanıtı zamanlayıcıyı yeniden kurardı.
  const isVarMi = aktifIs !== null
  useEffect(() => {
    void yenile()
    const aralik = setInterval(() => void yenile(), isVarMi ? CALISIRKEN_ARALIK_MS : BOSTA_ARALIK_MS)
    return () => clearInterval(aralik)
  }, [yenile, isVarMi])

  useEffect(() => {
    if (aktifIs === null) return
    const saat = setInterval(() => setGecenSure(gecenSureSaniye(aktifIs.baslangic_zamani)), 1000)
    return () => clearInterval(saat)
  }, [aktifIs])

  return (
    <AktifIsBaglami.Provider
      value={{
        aktifIs,
        sonuclananIs,
        gecenSure,
        yenile,
        sonucuKapat: () => setSonuclananIs(null),
      }}
    >
      {children}
    </AktifIsBaglami.Provider>
  )
}
