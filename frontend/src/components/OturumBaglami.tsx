// Giriş yapan kullanıcı ve oturum eylemleri, kabuğun (AppShell /
// CalisanShell) okuduğu bağlam.
//
// Bağlam kullanılmasının nedeni yalnızca kolaylık: bu üçlü sekiz ekranın
// hiçbirini ilgilendirmiyor, yalnızca kabuğa ulaşması gerekiyor. Prop
// olarak geçirilseydi her ekran taşımadığı bir veriyi sırf iletmek için
// imzasına alırdı.
//
// Buradaki hiçbir şey YETKİ TAŞIMAZ: rol yalnızca menüde ne gösterileceğini
// belirler, uç noktaların kapısı sunucudadır (SRS FR-10.4).
import { createContext, useContext } from 'react'
import type { Ben } from '@/api/types'

export interface OturumDurumu {
  ben: Ben
  cikis: () => void
  parolaDegistir: () => void
}

export const OturumBaglami = createContext<OturumDurumu | null>(null)

export function useOturum(): OturumDurumu {
  const durum = useContext(OturumBaglami)
  if (durum === null) {
    // Sessizce boş dönmek yerine hata: kabuğun kullanıcıyı ve çıkış
    // düğmesini gösterememesi, fark edilmesi gereken bir kurulum hatasıdır.
    throw new Error('OturumBaglami saglayicisi yok')
  }
  return durum
}
