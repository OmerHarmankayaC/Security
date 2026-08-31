// Gösterim ortamı şeridi (Demo Senaryosu 10).
//
// Şerit KAPATILAMAZ ve sayfayla birlikte kayar değil, en üstte durur.
// Kapatılabilir olsaydı ilk tıklamada kaybolur ve ekran görüntüsü alan
// kişi onu taşımayan bir görüntü üretirdi; oysa şeridin bütün işi, veriyi
// gören herkesin onun üretilmiş olduğunu bilmesi.
//
// Üç şey söyler ve üçü de gereklidir: veri üretilmiştir (kime ait olduğu
// sorusunu kapatır), her gece sıfırlanır (yapılan bir değişikliğin neden
// kaybolduğunu önceden açıklar) ve sistem hiçbir kurumda kullanımda değildir
// (ekran görüntüsünü gören birinin kuracağı ikinci varsayımı kapatır —
// birincisi "bu veri gerçek", ikincisi "bu sistem orada çalışıyor").
import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useMetin } from '@/i18n/DilBaglami'

export function DemoSeridi() {
  const m = useMetin()
  const [gorunur, setGorunur] = useState(false)

  useEffect(() => {
    // Hata YUTULUR ve şerit çizilmez: ortam uç noktasına ulaşılamaması
    // gösterim ortamında olunduğunun kanıtı değildir, ve şeridi "emin
    // olamadım" diye çizmek gerçek bir kurulumda yanlış beyan olurdu.
    api
      .ortam()
      .then((ortam) => setGorunur(ortam.demo_kipi))
      .catch(() => setGorunur(false))
  }, [])

  if (!gorunur) return null

  return (
    <div
      role="status"
      className="sticky top-0 z-50 w-full bg-amber-100 px-4 py-2 text-center text-sm text-amber-950"
    >
      <strong className="font-semibold">{m.demo.seritBasligi}</strong> {m.demo.seritGovdesi}
    </div>
  )
}
