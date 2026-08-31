// Ekranın altında uçan, kendiliğinden kaybolan küçük uyarı.
//
// Gösterim ortamının yazma reddi (403 + `salt_okunur`) buradan duyurulur.
// Sayfa akışında bir hata satırı olarak değil ÜSTTE UÇARAK gösterilir:
// kaydet düğmesine basan kişi ekranın neresine bakıyorsa oraya yakın bir
// yerde görmeli, sayfanın en altına inip aramamalı.
//
// ON SANİYE SONRA KENDİLİĞİNDEN GİDER ama çarpı da vardır. İkisi birden
// gerekli: kalıcı bir uyarı ekranı kalıcı olarak daraltır, yalnızca
// kendiliğinden gidense okumaya vakit bulamayan kişiye geri getirilemez.
//
// AYNI UYARI YIĞILMAZ. Arka arkaya reddedilen üç istek üç kutu değil, bir
// kutu ve yeniden başlayan bir sayaç üretir; yığılsalardı ekranın yarısı
// aynı cümleyle dolardı.
import { useEffect, useState } from 'react'
import { yazmaReddedildiginde } from '../api/client'

const SURE_MS = 10_000

export function UcanUyari() {
  const [mesaj, setMesaj] = useState<string | null>(null)
  // Aynı mesaj tekrar geldiğinde sayacın yeniden başlaması için: `mesaj`
  // değişmediğinde effect yeniden kurulmaz, sayaç eski kalırdı.
  const [sayac, setSayac] = useState(0)

  useEffect(() => {
    yazmaReddedildiginde((m) => {
      setMesaj(m)
      setSayac((n) => n + 1)
    })
    return () => yazmaReddedildiginde(null)
  }, [])

  useEffect(() => {
    if (mesaj === null) return
    const zamanlayici = setTimeout(() => setMesaj(null), SURE_MS)
    return () => clearTimeout(zamanlayici)
  }, [mesaj, sayac])

  if (mesaj === null) return null

  return (
    <div
      // `pointer-events-none` sarmalayıcıda: uyarı ekranın altını kaplayan
      // görünmez bir şeritte duruyor ve o şerit altındaki düğmeleri
      // yutmamalı. Kutunun kendisi tıklanabilir kalır.
      className="pointer-events-none fixed inset-x-0 bottom-4 z-[60] flex justify-center px-4"
    >
      <div
        role="status"
        className="pointer-events-auto flex max-w-[420px] items-start gap-2 rounded-md border border-rule bg-surface py-2 pr-2 pl-3 shadow-lg"
      >
        <p className="m-0 text-xs leading-relaxed text-ink">{mesaj}</p>
        <button
          type="button"
          onClick={() => setMesaj(null)}
          aria-label="Uyarıyı kapat"
          className="-mt-0.5 shrink-0 rounded-sm px-1 text-sm leading-none text-ink-muted transition-colors hover:text-ink focus-visible:ring-3 focus-visible:ring-accent/30 focus-visible:outline-none"
        >
          ×
        </button>
      </div>
    </div>
  )
}
