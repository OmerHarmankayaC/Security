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
//   2. `i18n/etkinDil.ts` — saf yardımcılar (`lib/sayi`, `lib/tarih`) React
//      bağlamını okuyamaz ama çıktıları dile bağlıdır: ondalık ayracı, ay
//      adı, gün kısaltması. TEK yazan burasıdır.
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
import { etkinDiliAyarla } from './etkinDil'

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

  // ÇİZİM SIRASINDA, effect'te DEĞİL. Effect ilk çizimden SONRA koşar ve
  // `lib/sayi`/`lib/tarih` ilk çizimde hâlâ eski dili okurdu; üstelik bu
  // yazma bir durum değişikliği olmadığı için yeniden çizim de tetiklemez,
  // yani yanlış dildeki sayılar ekranda ÖYLECE KALIRDI. Çağrı etkisizdir
  // (aynı değeri yazar), o yüzden her çizimde koşması sorun değil.
  etkinDiliAyarla(dil)

  // `<html lang>` bir DOM yazması; o effect'te kalır.
  useEffect(() => {
    document.documentElement.lang = dil
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
