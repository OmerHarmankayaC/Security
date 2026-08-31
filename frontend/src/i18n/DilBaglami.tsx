// Etkin dilin bağlamı.
//
// Bileşenler `useMetin()` ile sözlüğün ETKİN DİLDEKİ dalını alır ve
// `m.giris.baslik` diye okur. Anahtar dizgi olmadığı için yazım hatası,
// eksik çeviri ve yeniden adlandırma derlemede yakalanır.
//
// Sağlayıcı ayrıca iki YAN ETKİYİ üstlenir; ikisi de bileşenlerin
// göremeyeceği yerlerde durur:
//
//   1. `<html lang>` — ekran okuyucu doğru sesletim için buna bakar,
//      tarayıcının "bu sayfayı çevir" önerisi de buna bakar.
//   2. `lib/sayi.ts` yereli — ondalık ayracı Türkçe'de virgül, İngilizce'de
//      noktadır. Biçimleyicilere dil parametresi geçirmek iki yüzden fazla
//      çağrı yerini değiştirmek demekti; yerel modül düzeyinde tutuluyor ve
//      TEK yazan burasıdır.
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from 'react'
import { baslangicDili, diliSakla, type Dil } from './diller'
import { SOZLUK, type Metinler } from './sozluk'
import { yereliAyarla } from '@/lib/sayi'

interface DilDurumu {
  dil: Dil
  metin: Metinler
  dilSec: (dil: Dil) => void
}

const Baglam = createContext<DilDurumu | null>(null)

export function DilSaglayici({ children }: PropsWithChildren) {
  const [dil, setDil] = useState<Dil>(baslangicDili)

  const dilSec = useCallback((yeni: Dil) => {
    setDil(yeni)
    diliSakla(yeni)
  }, [])

  useEffect(() => {
    document.documentElement.lang = dil
    yereliAyarla(dil)
  }, [dil])

  const deger = useMemo<DilDurumu>(
    () => ({ dil, metin: SOZLUK[dil], dilSec }),
    [dil, dilSec],
  )

  return <Baglam.Provider value={deger}>{children}</Baglam.Provider>
}

/**
 * Sağlayıcı YOKSA yükselir, sessizce Türkçe'ye düşmez.
 *
 * Düşseydi sağlayıcıyı sarmayı unutan bir ağaç, İngilizce arayüzde
 * Türkçe metin çizerdi ve bunu ancak o dilde bakan biri fark ederdi. Testler
 * de bunu yakalar: sağlayıcısız render eden bir test yüksek sesle düşer.
 */
export function useDil(): DilDurumu {
  const deger = useContext(Baglam)
  if (deger === null) {
    throw new Error('useDil, <DilSaglayici> içinde çağrılmalı')
  }
  return deger
}

/** Yalnızca metinler gerektiğinde; en sık kullanılan biçim. */
export function useMetin(): Metinler {
  return useDil().metin
}
