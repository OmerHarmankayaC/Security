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
   * Çözüm ekranının sonuç özetini besler ve yeni bir iş başlayana kadar
   * durur — bildirimin kapatılması bunu SİLMEZ.
   */
  sonuclananIs: CozumIsi | null
  /** Kabuktaki göstergenin sonuçlanmış işi bildirip bildirmediği. */
  bildirimGorunur: boolean
  /**
   * İşin geçen süresi. Arama bittiğinde DONAR: ölçülen süre aramanın
   * süresidir, kullanıcının karar verme süresi değil (SDD 4.2.4).
   */
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

/**
 * İşin geçen süresi. Arama bittiyse SAYAÇ DONAR.
 *
 * `bitis_zamani` aramanın bittiği anı taşır (SDD 4.2.4) ve karar sonradan
 * verildiğinde değişmez. Sayacın karar beklerken işlemeye devam etmesi,
 * kullanıcının düşünme süresini aramanın süresine ekler; ekranda "24
 * saniyede bulundu" yazması gereken yerde dakikalar görünür.
 *
 * Sunucu zaman damgaları saat dilimi taşır (timestamptz); Date bunu
 * doğrudan ayrıştırır.
 */
function gecenSureSaniye(is: CozumIsi): number {
  const baslangic = new Date(is.baslangic_zamani).getTime()
  const bitis = is.bitis_zamani === null ? Date.now() : new Date(is.bitis_zamani).getTime()
  return Math.max(0, Math.floor((bitis - baslangic) / 1000))
}

export function AktifIsSaglayici({ children }: PropsWithChildren) {
  const [aktifIs, setAktifIs] = useState<CozumIsi | null>(null)
  const [sonuclananIs, setSonuclananIs] = useState<CozumIsi | null>(null)
  const [bildirimKapali, setBildirimKapali] = useState(false)
  const [gecenSure, setGecenSure] = useState(0)
  // Yalnızca "iş kayboldu" geçişini yakalamak için; okuma kaynağı değil.
  const oncekiIsId = useRef<number | null>(null)

  const yenile = useCallback(async () => {
    try {
      const guncel = await api.cozumAktif()
      setAktifIs(guncel)
      if (guncel !== null) {
        oncekiIsId.current = guncel.is_id
        setGecenSure(gecenSureSaniye(guncel))
        setSonuclananIs(null)
        setBildirimKapali(false)
        return
      }
      const bitenId = oncekiIsId.current
      oncekiIsId.current = null
      if (bitenId !== null) {
        // İş listeden düştü: son hâlini bir kez okuyup bildiriyoruz.
        // Kimlik burada bir kez KULLANILIYOR, saklanmıyor — sunucunun bir
        // önceki yanıtından geldi ve bu istekten sonra bırakılıyor.
        const biten = await api.cozumDurumu(bitenId)
        setSonuclananIs(biten)
        setGecenSure(gecenSureSaniye(biten))
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

  // Saat YALNIZCA arama sürerken işler. `durduruldu` durumundaki iş hâlâ
  // aktiftir (karar bekliyor) ama araması bitmiştir; sayacın orada da
  // işlemesi, karar verme süresini aramanın süresine ekliyordu.
  const aramaSuruyorMu = aktifIs !== null && aktifIs.bitis_zamani === null
  useEffect(() => {
    if (aktifIs === null || !aramaSuruyorMu) return
    const saat = setInterval(() => setGecenSure(gecenSureSaniye(aktifIs)), 1000)
    return () => clearInterval(saat)
  }, [aktifIs, aramaSuruyorMu])

  return (
    <AktifIsBaglami.Provider
      value={{
        aktifIs,
        // Bildirim kapatıldığında SON İŞ KAYBOLMAZ, yalnızca kabuktaki
        // gösterge gizlenir: göstergeye tıklamak Çözüm ekranını açıyor ve
        // aynı anda orada görülecek özeti silmek anlamsızdı.
        sonuclananIs,
        bildirimGorunur: sonuclananIs !== null && !bildirimKapali,
        gecenSure,
        yenile,
        sonucuKapat: () => setBildirimKapali(true),
      }}
    >
      {children}
    </AktifIsBaglami.Provider>
  )
}
