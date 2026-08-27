// Gösterim ortamı şeridi (Demo Senaryosu 10).
//
// Şerit KAPATILAMAZ ve sayfayla birlikte kayar değil, en üstte durur.
// Kapatılabilir olsaydı ilk tıklamada kaybolur ve ekran görüntüsü alan
// kişi onu taşımayan bir görüntü üretirdi; oysa şeridin bütün işi, veriyi
// gören herkesin onun üretilmiş olduğunu bilmesi.
//
// İki cümle söyler ve ikisi de gereklidir: veri gerçek değildir (kime ait
// olduğu sorusunu kapatır) ve her gece yeniden kurulur (yapılan bir
// değişikliğin neden kaybolduğunu önceden açıklar).
import { useEffect, useState } from 'react'
import { api } from '../api/client'

export function DemoSeridi() {
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
      className="w-full bg-amber-100 px-4 py-2 text-center text-sm text-amber-950"
    >
      <strong className="font-semibold">Gösterim ortamı.</strong> Buradaki personel, izin ve
      çizelge kayıtlarının tamamı üretilmiştir; gerçek bir kurumu ya da kişiyi göstermez.
      Yaptığınız değişiklikler her gece veri yeniden kurulduğunda kaybolur.
    </div>
  )
}
